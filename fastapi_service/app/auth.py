import os

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(
    description="Paste the access token returned by the Django service "
                "(POST /api/auth/login/). Do not add the word 'Bearer'."
)


def get_current_user_id(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise HTTPException(status_code=500, detail="Server misconfigured")
    try:
        payload = jwt.decode(
            creds.credentials,
            secret,
            algorithms=["HS256"],
            options={"require": ["exp"]},
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload.get("token_type") != "access" or "user_id" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return int(payload["user_id"])