import { money, dateTime } from "../utils";

export function Field({ label, hint, ...props }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium">{label}</span>
      <input
        {...props}
        className="w-full rounded-lg border border-line bg-white px-3 py-2 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/25"
      />
      {hint && <span className="mt-1 block text-xs text-muted">{hint}</span>}
    </label>
  );
}

export function Select({ label, children, ...props }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium">{label}</span>
      <select
        {...props}
        className="w-full rounded-lg border border-line bg-white px-3 py-2 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/25"
      >
        {children}
      </select>
    </label>
  );
}

const variants = {
  primary: "bg-brand text-white shadow-sm hover:bg-brand-dark",
  ghost: "border border-line bg-white text-ink hover:bg-paper",
  danger: "border border-bad/40 bg-white text-bad hover:bg-bad/10",
};

export function Button({ variant = "primary", className = "", ...props }) {
  return (
    <button
      {...props}
      className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:opacity-60 ${variants[variant]} ${className}`}
    />
  );
}

export function Alert({ kind = "error", children }) {
  if (!children) return null;
  const styles = kind === "error"
    ? "border-bad/30 bg-bad/10 text-bad"
    : "border-ok/30 bg-ok/10 text-ok";
  return <div role="alert" className={`rounded-lg border px-3 py-2 text-sm ${styles}`}>{children}</div>;
}

export function StatusBadge({ status }) {
  const styles = {
    SUCCESS: "bg-ok/10 text-ok",
    FAILED: "bg-bad/10 text-bad",
    PENDING: "bg-warn/10 text-warn",
  }[status] || "bg-line text-muted";
  return <span className={`inline-block rounded px-2 py-0.5 text-xs font-semibold ${styles}`}>{status}</span>;
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold">{title}</h1>
        {subtitle && <p className="mt-1 max-w-prose text-sm text-muted">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

export function Panel({ title, children, className = "" }) {
  return (
    <section className={`rounded-2xl border border-line bg-white p-6 shadow-sm ${className}`}>
      {title && <h2 className="mb-4 text-base font-semibold">{title}</h2>}
      {children}
    </section>
  );
}

export function Empty({ children }) {
  return <p className="py-6 text-center text-sm text-muted">{children}</p>;
}

export function TxnTable({ rows, showUser = false }) {
  if (!rows.length) return <Empty>No transactions match. Make a payment to see it here.</Empty>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-line text-muted">
            <th className="py-2 pr-4 font-medium">Date</th>
            {showUser && <th className="py-2 pr-4 font-medium">User</th>}
            <th className="py-2 pr-4 font-medium">Card</th>
            <th className="py-2 pr-4 font-medium">Description</th>
            <th className="py-2 pr-4 text-right font-medium">Amount</th>
            <th className="py-2 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((t) => (
            <tr key={t.id} className="border-b border-line/60 last:border-0">
              <td className="py-2.5 pr-4 whitespace-nowrap">{dateTime(t.created_at)}</td>
              {showUser && <td className="py-2.5 pr-4">{t.username}</td>}
              <td className="py-2.5 pr-4">{t.card_last4 ? `•••• ${t.card_last4}` : "-"}</td>
              <td className="py-2.5 pr-4">{t.description || "-"}</td>
              <td className="py-2.5 pr-4 text-right">{money(t.amount, t.currency)}</td>
              <td className="py-2.5">
                <StatusBadge status={t.status} />
                {t.failure_reason && <div className="mt-0.5 text-xs text-muted">{t.failure_reason}</div>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AuthShell({ title, subtitle, children }) {
  return (
    <div className="min-h-screen md:grid md:grid-cols-2">
      <div className="flex flex-col justify-between bg-gradient-to-br from-brand-dark via-brand-dark to-brand p-8 text-white md:p-12">
        <div className="text-lg font-semibold">SecurePay</div>
        <div className="py-10">
          <p className="max-w-md text-3xl font-semibold leading-tight">
            Save a card, pay, and watch the payment settle.
          </p>
          <p className="mt-4 max-w-md text-sm text-white/70">
            Every payment starts as pending and ends as success or failed. Payments are simulated, so no real money moves and card numbers and CVVs are never stored.
          </p>
        </div>
        <div className="text-xs text-white/50">Full stack assignment build</div>
      </div>
      <div className="flex items-center justify-center p-6 md:p-12">
        <div className="w-full max-w-sm">
          <h1 className="text-2xl font-semibold">{title}</h1>
          <p className="mb-6 mt-1 text-sm text-muted">{subtitle}</p>
          {children}
        </div>
      </div>
    </div>
  );
}
