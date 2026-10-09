import time

from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware

from .database import get_db
from .models import ApiLog

SKIP_PREFIXES = ("/docs", "/openapi.json", "/redoc", "/favicon.ico", "/health")


def _save(endpoint, method, status_code, ms, error):
    gen = get_db()
    try:
        db = next(gen)
        db.add(
            ApiLog(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=ms,
                error_message=error,
            )
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001
        print(f"[monitoring] could not save log: {exc}")
    finally:
        gen.close()


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Logs response time and failures of every API call into api_logs."""

    async def dispatch(self, request, call_next):
        if request.url.path.startswith(SKIP_PREFIXES):
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500
        error = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            if status_code >= 400:
                error = f"HTTP {status_code}"
            return response
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"[:500]
            raise
        finally:
            ms = round((time.perf_counter() - start) * 1000, 2)
            route = request.scope.get("route")
            path = getattr(route, "path", None) or request.url.path
            await run_in_threadpool(_save, path[:200], request.method, status_code, ms, error)