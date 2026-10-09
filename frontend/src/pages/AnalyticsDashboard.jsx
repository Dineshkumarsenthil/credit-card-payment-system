import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart,
  PolarAngleAxis, RadialBar, RadialBarChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { errMsg } from "../api";
import { fapi } from "../fastapi";
import { Alert, Button, Empty, PageHeader, Panel } from "../components/ui.jsx";
import ExportButtons from "../components/ExportButtons.jsx";

const COLORS = ["#6366f1", "#22d3ee", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#ef4444"];

const inr = (n) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n || 0);

const utilColor = (p) => (p >= 80 ? "#ef4444" : p >= 50 ? "#f59e0b" : "#10b981");
const utilLabel = (p) => (p >= 80 ? "High" : p >= 50 ? "Moderate" : "Healthy");

const BADGE = {
  up: "bg-warn/10 text-warn",
  down: "bg-ok/10 text-ok",
  ok: "bg-ok/10 text-ok",
  warn: "bg-warn/10 text-warn",
  bad: "bg-bad/10 text-bad",
  none: "bg-line text-muted",
};

const axis = { fill: "currentColor", fontSize: 12 };

function Tip({ active, payload, label, percent = false }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-line bg-surface px-3 py-2 text-sm shadow-lg">
      {label && <p className="mb-1 font-medium">{label}</p>}
      {payload.map((p) => (
        <p key={p.name} className="text-muted">
          {p.name}: <span className="font-semibold text-ink">{percent ? `${p.value}%` : inr(p.value)}</span>
        </p>
      ))}
    </div>
  );
}

function Kpi({ icon, label, value, badge, tone = "none", hint }) {
  return (
    <div className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand/10 text-base text-brand">{icon}</span>
        <p className="text-sm font-medium text-muted">{label}</p>
      </div>
      <p className="mt-4 text-3xl font-bold tracking-tight">{value}</p>
      <div className="mt-3 flex items-center gap-2 text-xs text-muted">
        {badge && <span className={`rounded-full px-2 py-0.5 font-semibold ${BADGE[tone]}`}>{badge}</span>}
        <span>{hint}</span>
      </div>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="animate-pulse space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => <div key={i} className="h-36 rounded-2xl bg-line/60" />)}
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="h-80 rounded-2xl bg-line/60 lg:col-span-2" />
        <div className="h-80 rounded-2xl bg-line/60" />
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        {[0, 1, 2].map((i) => <div key={i} className="h-72 rounded-2xl bg-line/60" />)}
      </div>
    </div>
  );
}

export default function AnalyticsDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState(6);

  const load = useCallback(() => {
    setLoading(true);
    fapi.get("/analytics/summary")
      .then((r) => { setData(r.data); setError(""); })
      .catch((e) => setError(errMsg(e)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  const s = useMemo(() => {
    if (!data) return null;
    const monthly = (data.monthly || []).map((m) => ({ ...m, total: Number(m.total) }));
    const categories = [...(data.categories || [])]
      .map((c) => ({ ...c, total: Number(c.total) }))
      .sort((a, b) => b.total - a.total);
    const total = monthly.reduce((a, m) => a + m.total, 0);
    const catTotal = categories.reduce((a, c) => a + c.total, 0);
    const current = monthly.length ? monthly[monthly.length - 1].total : 0;
    const prev = monthly.length > 1 ? monthly[monthly.length - 2].total : null;
    const change = prev ? ((current - prev) / prev) * 100 : null;
    return { monthly, categories, total, catTotal, current, change, top: categories[0] };
  }, [data]);

  const util = data?.utilization;
  const chartData = s ? (range ? s.monthly.slice(-range) : s.monthly) : [];

  return (
    <>
      <PageHeader title="Analytics Dashboard" subtitle="Card usage insights from your successful payments.">
        <div className="flex flex-wrap items-start gap-2">
          <Button type="button" variant="ghost" onClick={load} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
          <ExportButtons />
        </div>
      </PageHeader>

      <Alert>{error}</Alert>
      {loading && !data && <Skeleton />}

      {data && s && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Kpi icon="₹" label="Total spent" value={inr(s.total)} hint={`${s.monthly.length} month(s) of data`} />
            <Kpi
              icon="↗"
              label="This month"
              value={inr(s.current)}
              badge={s.change == null ? null : `${s.change >= 0 ? "▲" : "▼"} ${Math.abs(s.change).toFixed(1)}%`}
              tone={s.change != null && s.change < 0 ? "down" : "up"}
              hint={s.change == null ? "No previous month yet" : "vs last month"}
            />
            <Kpi
              icon="★"
              label="Top category"
              value={s.top?.category || "-"}
              badge={s.top && s.catTotal ? `${((s.top.total / s.catTotal) * 100).toFixed(0)}%` : null}
              tone="none"
              hint={s.top ? `${inr(s.top.total)} spent` : "No spending yet"}
            />
            <Kpi
              icon="◔"
              label="Credit utilization"
              value={`${util.overall_percent}%`}
              badge={utilLabel(util.overall_percent)}
              tone={util.overall_percent >= 80 ? "bad" : util.overall_percent >= 50 ? "warn" : "ok"}
              hint="across all cards"
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            <Panel className="lg:col-span-2">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold">Monthly spending trend</h2>
                  <p className="text-sm text-muted">Total of successful payments per month</p>
                </div>
                <select
                  value={range}
                  onChange={(e) => setRange(Number(e.target.value))}
                  className="rounded-lg border border-line bg-surface px-3 py-1.5 text-sm outline-none focus:border-brand"
                >
                  <option value={3}>Last 3 months</option>
                  <option value={6}>Last 6 months</option>
                  <option value={12}>Last 12 months</option>
                  <option value={0}>All time</option>
                </select>
              </div>
              {chartData.length === 0 ? (
                <Empty>No successful payments yet.</Empty>
              ) : (
                <div className="h-72 text-muted">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="spendFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#6366f1" stopOpacity={0.5} />
                          <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="currentColor" strokeOpacity={0.15} vertical={false} />
                      <XAxis dataKey="month" tick={axis} tickLine={false} axisLine={false} />
                      <YAxis tick={axis} tickLine={false} axisLine={false} tickFormatter={(v) => (v >= 1000 ? `${v / 1000}k` : v)} />
                      <Tooltip content={<Tip />} />
                      <Area type="monotone" dataKey="total" name="Spent" stroke="#6366f1" strokeWidth={3} fill="url(#spendFill)" dot={{ r: 5, fill: "#6366f1", strokeWidth: 0 }} activeDot={{ r: 7 }} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Panel>

            <Panel>
              <h2 className="text-base font-semibold">Category breakdown</h2>
              <p className="text-sm text-muted">Expenses by category</p>
              <div className="mt-4 flex items-center justify-between border-b border-line pb-3 text-sm">
                <span className="text-muted">Total</span>
                <span className="text-xl font-bold">{inr(s.catTotal)}</span>
              </div>
              {s.categories.length === 0 ? (
                <Empty>No categories yet.</Empty>
              ) : (
                <ul className="mt-4 space-y-4">
                  {s.categories.map((c, i) => {
                    const pct = s.catTotal ? (c.total / s.catTotal) * 100 : 0;
                    return (
                      <li key={c.category}>
                        <div className="mb-1 flex justify-between text-sm">
                          <span className="font-medium">{c.category}</span>
                          <span>{inr(c.total)}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="h-2 flex-1 overflow-hidden rounded-full bg-line">
                            <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: COLORS[i % COLORS.length] }} />
                          </div>
                          <span className="w-10 text-right text-xs text-muted">{pct.toFixed(0)}%</span>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </Panel>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            <Panel title="Utilization per card">
              {util.cards.length === 0 ? (
                <Empty>No cards yet.</Empty>
              ) : (
                <div className="h-64 text-muted">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={util.cards} margin={{ top: 10, right: 8, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="currentColor" strokeOpacity={0.15} vertical={false} />
                      <XAxis dataKey="card" tick={axis} tickLine={false} axisLine={false} />
                      <YAxis domain={[0, 100]} tick={axis} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} />
                      <Tooltip content={<Tip percent />} cursor={{ fill: "currentColor", fillOpacity: 0.06 }} />
                      <Bar dataKey="percent" name="Utilization" radius={[8, 8, 0, 0]} maxBarSize={48}>
                        {util.cards.map((c, i) => <Cell key={i} fill={utilColor(c.percent)} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Panel>

            <Panel title="Spending share">
              {s.categories.length === 0 ? (
                <Empty>No spending yet.</Empty>
              ) : (
                <div className="relative h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={s.categories} dataKey="total" nameKey="category" innerRadius={62} outerRadius={92} paddingAngle={3} stroke="none">
                        {s.categories.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Tooltip content={<Tip />} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-xs text-muted">Categories</span>
                    <span className="text-2xl font-bold">{s.categories.length}</span>
                  </div>
                </div>
              )}
            </Panel>

            <Panel title="Overall utilization">
              <div className="relative h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart
                    innerRadius="70%" outerRadius="100%" startAngle={90} endAngle={-270}
                    data={[{ name: "Utilization", value: util.overall_percent, fill: utilColor(util.overall_percent) }]}
                  >
                    <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                    <RadialBar dataKey="value" cornerRadius={12} background={{ fill: "rgba(148,163,184,0.2)" }} />
                  </RadialBarChart>
                </ResponsiveContainer>
                <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-bold">{util.overall_percent}%</span>
                  <span className="text-xs text-muted">{utilLabel(util.overall_percent)}</span>
                </div>
              </div>
            </Panel>
          </div>
        </div>
      )}
    </>
  );
}