import { useCallback, useEffect, useState } from "react";
import { errMsg } from "../api";
import { fapi } from "../fastapi";
import { Alert, Button, Empty, PageHeader, Panel } from "../components/ui.jsx";
import { useRole } from "../utils/roleGuard.jsx";

const fmtUptime = (s) => {
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  return d ? `${d}d ${h}h ${m}m` : `${h}h ${m}m`;
};

const codeStyle = (c) =>
  c >= 500 ? "bg-bad/10 text-bad" : "bg-warn/10 text-warn";

const th = "px-3 py-2 text-xs font-medium uppercase tracking-wide text-muted";
const td = "px-3 py-2.5";
const row = "border-t border-line/60";

function Pill({ className = "", children }) {
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${className}`}>
      {children}
    </span>
  );
}

function Stat({ label, value, hint, bad = false }) {
  return (
    <div className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-muted">{label}</p>
      <p className={`mt-2 text-2xl font-bold ${bad ? "text-bad" : ""}`}>{value}</p>
      {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
    </div>
  );
}

function Skeleton() {
  return (
    <div className="animate-pulse space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => <div key={i} className="h-24 rounded-2xl bg-line/60" />)}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="h-64 rounded-2xl bg-line/60" />
        <div className="h-64 rounded-2xl bg-line/60" />
      </div>
    </div>
  );
}

function DataTable({ head, children, empty, count }) {
  if (count === 0) return <Empty>{empty}</Empty>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr>{head.map((h) => <th key={h} className={th}>{h}</th>)}</tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

const TABS = [
  { id: "errors", label: "Recent errors" },
  { id: "audit", label: "Audit log" },
  { id: "fraud", label: "Fraud log" },
];

export default function AdminHealth() {
  const { can, loading: roleLoading } = useRole();
  const [health, setHealth] = useState(null);
  const [audit, setAudit] = useState([]);
  const [fraud, setFraud] = useState([]);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("errors");
  const [auto, setAuto] = useState(true);
  const [updated, setUpdated] = useState(null);

  const allowed = can("health:view");

  const load = useCallback(() => {
    Promise.all([
      fapi.get("/admin/health"),
      fapi.get("/admin/audit-logs", { params: { limit: 10 } }),
      fapi.get("/admin/fraud-logs", { params: { limit: 10 } }),
    ])
      .then(([h, a, f]) => {
        setHealth(h.data);
        setAudit(a.data);
        setFraud(f.data);
        setError("");
        setUpdated(new Date());
      })
      .catch((e) => setError(errMsg(e)));
  }, []);

  useEffect(() => {
    if (roleLoading || !allowed) return undefined;
    load();
    if (!auto) return undefined;
    const id = setInterval(load, 10000);
    return () => clearInterval(id);
  }, [roleLoading, allowed, auto, load]);

  if (roleLoading) return <Skeleton />;

  if (!allowed) {
    return (
      <>
        <PageHeader title="System health" />
        <Panel>
          <div className="py-10 text-center">
            <h2 className="text-lg font-semibold">Access denied</h2>
            <p className="mx-auto mt-1 max-w-md text-sm text-muted">
              System health, audit logs and fraud logs are available to administrators only.
              Your role does not have the <code>health:view</code> permission.
            </p>
          </div>
        </Panel>
      </>
    );
  }

  const l = health?.last_24h;
  const healthy = health && health.status === "healthy" && health.database === "up";
  const maxMs = health ? Math.max(...health.slowest_endpoints.map((s) => s.avg_ms), 1) : 1;
  const counts = { errors: health?.recent_errors.length ?? 0, audit: audit.length, fraud: fraud.length };

  return (
    <>
      <PageHeader
        title="System health"
        subtitle="API monitoring, audit logs and fraud logs (admin only)."
      >
        <div className="flex flex-wrap items-center gap-2">
          {health && (
            <span
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-medium ${
                healthy ? "border-ok/30 bg-ok/10 text-ok" : "border-bad/30 bg-bad/10 text-bad"
              }`}
            >
              <span className={`h-2 w-2 rounded-full ${healthy ? "bg-ok" : "bg-bad"}`} />
              {healthy ? "Operational" : "Degraded"}
            </span>
          )}
          {updated && <span className="text-xs text-muted">Updated {updated.toLocaleTimeString()}</span>}
          <Button type="button" variant="ghost" onClick={() => setAuto(!auto)}>
            {auto ? "Pause" : "Resume"}
          </Button>
          <Button type="button" onClick={load}>Refresh</Button>
        </div>
      </PageHeader>

      <Alert>{error}</Alert>
      {!health && !error && <Skeleton />}

      {health && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat label="API status" value={health.status.toUpperCase()} bad={health.status !== "healthy"} />
            <Stat label="Database" value={health.database.toUpperCase()} bad={health.database !== "up"} />
            <Stat label="Uptime" value={fmtUptime(health.uptime_seconds)} />
            <Stat label="Requests (24h)" value={l.total_requests.toLocaleString()} />
            <Stat
              label="Avg response"
              value={`${l.avg_response_ms} ms`}
              hint={l.avg_response_ms > 500 ? "Slower than 500 ms" : "Within target"}
              bad={l.avg_response_ms > 500}
            />
            <Stat label="Server errors (5xx)" value={l.server_errors} bad={l.server_errors > 0} />
            <Stat label="Client errors (4xx)" value={l.client_errors} />
            <div className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-muted">Error rate</p>
              <p className={`mt-2 text-2xl font-bold ${l.error_rate_percent > 5 ? "text-bad" : ""}`}>
                {l.error_rate_percent}%
              </p>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-line">
                <div
                  className={`h-full rounded-full ${l.error_rate_percent > 5 ? "bg-bad" : "bg-ok"}`}
                  style={{ width: `${Math.min(l.error_rate_percent, 100)}%` }}
                />
              </div>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-5">
            <Panel title="Slowest endpoints" className="lg:col-span-2">
              {health.slowest_endpoints.length === 0 ? (
                <Empty>No traffic recorded yet.</Empty>
              ) : (
                <ul className="space-y-4">
                  {health.slowest_endpoints.map((s) => (
                    <li key={s.endpoint}>
                      <div className="mb-1 flex justify-between gap-3 text-sm">
                        <span className="truncate font-mono text-xs">{s.endpoint}</span>
                        <span className="shrink-0 text-xs text-muted">{s.avg_ms} ms · {s.hits} hits</span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-line">
                        <div
                          className="h-full rounded-full bg-brand"
                          style={{ width: `${(s.avg_ms / maxMs) * 100}%` }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>

            <Panel className="lg:col-span-3">
              <div className="mb-4 flex gap-1 rounded-xl bg-paper p-1">
                {TABS.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setTab(t.id)}
                    className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                      tab === t.id ? "bg-surface text-ink shadow-sm" : "text-muted hover:text-ink"
                    }`}
                  >
                    {t.label}
                    <span className="ml-2 rounded-full bg-line px-2 py-0.5 text-xs">{counts[t.id]}</span>
                  </button>
                ))}
              </div>

              {tab === "errors" && (
                <DataTable head={["Endpoint", "Status", "Time"]} count={health.recent_errors.length} empty="No errors recorded.">
                  {health.recent_errors.map((e, i) => (
                    <tr key={i} className={row}>
                      <td className={`${td} font-mono text-xs`}>{e.method} {e.endpoint}</td>
                      <td className={td}><Pill className={codeStyle(e.status_code)}>{e.status_code}</Pill></td>
                      <td className={`${td} whitespace-nowrap text-muted`}>{new Date(e.created_at).toLocaleTimeString()}</td>
                    </tr>
                  ))}
                </DataTable>
              )}

              {tab === "audit" && (
                <DataTable head={["User", "Action", "Card", "Old", "New"]} count={audit.length} empty="No admin actions logged yet.">
                  {audit.map((a) => (
                    <tr key={a.id} className={row}>
                      <td className={td}>{a.user_id}</td>
                      <td className={td}><Pill className="bg-brand/10 text-brand">{a.action}</Pill></td>
                      <td className={td}>{a.card_id ?? "-"}</td>
                      <td className={`${td} text-muted`}>{a.old_value}</td>
                      <td className={`${td} font-medium`}>{a.new_value}</td>
                    </tr>
                  ))}
                </DataTable>
              )}

              {tab === "fraud" && (
                <DataTable head={["Txn", "Rule", "Email"]} count={fraud.length} empty="No fraud detected.">
                  {fraud.map((f) => (
                    <tr key={f.id} className={row}>
                      <td className={td}>#{f.transaction_id}</td>
                      <td className={td}><Pill className="bg-bad/10 text-bad">{f.rule_triggered}</Pill></td>
                      <td className={td}>
                        <Pill className={f.email_sent ? "bg-ok/10 text-ok" : "bg-line text-muted"}>
                          {f.email_sent ? "Sent" : "Not sent"}
                        </Pill>
                      </td>
                    </tr>
                  ))}
                </DataTable>
              )}
            </Panel>
          </div>
        </div>
      )}
    </>
  );
}