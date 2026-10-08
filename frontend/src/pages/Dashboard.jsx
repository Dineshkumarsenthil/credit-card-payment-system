import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, payApi, errMsg } from "../api";

/* ---------- settings (check these against your project) ---------- */

const PAYMENT_PATH = "/pay";
const CARDS_PATH = "/cards";
const TRANSACTIONS_PATH = "/transactions";
const LOGIN_PATH = "/login";

// FastAPI endpoint required by the task. payApi should point at port 8001.
const SUMMARY_URL = "/dashboard/summary";

// Django endpoints (optional extras: card visual, welcome name, 7-day chart).
// If your api.js baseURL already ends with "/api", remove the "/api" prefix.
const CARDS_URL = "/api/cards/";
const ME_URL = "/api/auth/me/";
const TX_URL = "/api/transactions/";

/* ---------- helpers ---------- */

const toList = (data) => (Array.isArray(data) ? data : data?.results ?? []);

// FastAPI returns dates without a timezone (UTC). Add "Z" so they show in local time.
const parseDate = (iso) => {
  const s = String(iso || "");
  return new Date(/Z$|[+-]\d{2}:?\d{2}$/.test(s) ? s : `${s}Z`);
};

const inr = (n) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(n) || 0);

const inrCompact = (n) =>
  new Intl.NumberFormat("en-IN", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(Number(n) || 0);

const formatDateTime = (iso) =>
  parseDate(iso).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });

const dayKey = (d) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate()
  ).padStart(2, "0")}`;

// Theme colours (ok / bad / warn) switch automatically in dark mode
const STATUS_STYLES = {
  SUCCESS: "bg-ok/10 text-ok ring-ok/30",
  FAILED: "bg-bad/10 text-bad ring-bad/30",
  PENDING: "bg-warn/10 text-warn ring-warn/30",
};

function StatusPill({ status }) {
  const key = String(status || "").toUpperCase();
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ring-1 ring-inset ${
        STATUS_STYLES[key] || "bg-line text-muted ring-line"
      }`}
    >
      {key.toLowerCase()}
    </span>
  );
}

/* ---------- small building blocks ---------- */

function StatCard({ label, value, note }) {
  return (
    <div className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-ink">
        {value}
      </p>
      {note && <p className="mt-1 text-xs text-muted">{note}</p>}
    </div>
  );
}

function SpendingChart({ days }) {
  const max = Math.max(...days.map((d) => d.total), 1);
  return (
    <div>
      <div className="flex h-44 items-end gap-3">
        {days.map((d) => {
          const pct = d.total > 0 ? Math.max((d.total / max) * 100, 4) : 0;
          return (
            <div
              key={d.key}
              className="flex h-full flex-1 flex-col items-center justify-end gap-1"
            >
              <span className="text-[11px] text-muted">
                {d.total > 0 ? inrCompact(d.total) : ""}
              </span>
              <div
                className={`w-full rounded-t-md ${
                  d.total > 0 ? "bg-emerald-700" : "bg-line"
                }`}
                style={{ height: d.total > 0 ? `${pct}%` : "4px" }}
                title={`${d.label}: ${inr(d.total)}`}
              />
            </div>
          );
        })}
      </div>
      <div className="mt-2 flex gap-3 border-t border-line pt-2">
        {days.map((d) => (
          <span key={d.key} className="flex-1 text-center text-xs text-muted">
            {d.label}
          </span>
        ))}
      </div>
    </div>
  );
}

function CardFace({ card, used, limit }) {
  const usedPct = limit > 0 ? Math.min((used / limit) * 100, 100) : 0;
  return (
    <div className="relative overflow-hidden rounded-2xl bg-emerald-900 p-6 text-emerald-50 shadow-lg">
      <div
        className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-emerald-700/40"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute -bottom-24 -left-10 h-56 w-56 rounded-full bg-emerald-800/60"
        aria-hidden="true"
      />
      <div className="relative">
        <div className="flex items-start justify-between">
          <span className="text-sm font-medium text-emerald-200">
            {card ? card.brand : "No card yet"}
          </span>
          <span className="h-7 w-10 rounded-md bg-amber-300/90" aria-hidden="true" />
        </div>
        <p className="mt-8 font-mono text-xl tracking-widest">
          {card ? `•••• •••• •••• ${card.last4}` : "•••• •••• •••• ––––"}
        </p>
        <div className="mt-6 flex items-end justify-between text-sm">
          <div>
            <p className="text-xs text-emerald-300">Card holder</p>
            <p className="font-medium">{card ? card.card_holder : "Add a card"}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-emerald-300">Expires</p>
            <p className="font-medium">
              {card
                ? `${String(card.expiry_month).padStart(2, "0")}/${card.expiry_year}`
                : "––/––––"}
            </p>
          </div>
        </div>
        <div className="mt-6">
          <div className="flex justify-between text-xs text-emerald-200">
            <span>Credit used {inr(used)}</span>
            <span>of {inr(limit)}</span>
          </div>
          <div
            className="mt-2 h-1.5 overflow-hidden rounded-full bg-emerald-950/50"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(usedPct)}
            aria-label="Credit used"
          >
            <div
              className="h-full rounded-full bg-amber-300"
              style={{ width: `${usedPct}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading dashboard">
      <div className="h-10 w-64 animate-pulse rounded-lg bg-line" />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-28 animate-pulse rounded-2xl bg-line" />
        ))}
      </div>
      <div className="h-72 animate-pulse rounded-2xl bg-line" />
      <div className="h-64 animate-pulse rounded-2xl bg-line" />
    </div>
  );
}

/* ---------- page ---------- */

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [cards, setCards] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // { message, authFailed }

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        // The summary is required; everything else is an optional extra.
        const [sum, cd, me, tx] = await Promise.allSettled([
          payApi.get(SUMMARY_URL),
          api.get(CARDS_URL),
          api.get(ME_URL),
          api.get(TX_URL),
        ]);
        if (!active) return;
        if (sum.status === "rejected") throw sum.reason;
        setSummary(sum.value.data);
        if (cd.status === "fulfilled") setCards(toList(cd.value.data));
        if (me.status === "fulfilled") setUsername(me.value.data?.username || "");
        if (tx.status === "fulfilled") setTransactions(toList(tx.value.data));
      } catch (e) {
        if (!active) return;
        const status = e?.response?.status;
        setError({
          authFailed: status === 401 || status === 403,
          message: errMsg(e),
        });
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  // Seven-day chart from the transaction list (optional extra)
  const days = useMemo(() => {
    const byDay = {};
    transactions
      .filter((t) => t.status === "SUCCESS")
      .forEach((t) => {
        const k = dayKey(new Date(t.created_at));
        byDay[k] = (byDay[k] || 0) + Number(t.amount);
      });
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (6 - i));
      return {
        key: dayKey(d),
        label: d.toLocaleDateString("en-IN", { day: "numeric", month: "short" }),
        total: byDay[dayKey(d)] || 0,
      };
    });
  }, [transactions]);
  const weekTotal = days.reduce((s, d) => s + d.total, 0);

  if (loading) return <Skeleton />;

  if (error) {
    return (
      <div
        role="alert"
        className="rounded-2xl border border-bad/30 bg-bad/10 p-5 text-sm text-bad"
      >
        {error.authFailed ? (
          <>
            <p className="font-medium">Your session has expired or is invalid.</p>
            <p className="mt-1">Log in again to see your dashboard.</p>
            <Link
              to={LOGIN_PATH}
              className="mt-3 inline-block rounded-lg bg-rose-700 px-4 py-2 font-medium text-white hover:bg-rose-600"
            >
              Log in
            </Link>
          </>
        ) : (
          <>
            <p className="font-medium">The dashboard could not load.</p>
            <p className="mt-1">{error.message}</p>
            <p className="mt-2">
              Check that the FastAPI service is running on port 8001.
            </p>
          </>
        )}
      </div>
    );
  }

  const totalSpent = Number(summary.total_amount_spent);
  const monthSpent = Number(summary.current_month_spending);
  const available = Number(summary.available_credit_limit);
  const limit = totalSpent + available;
  const last5 = (summary.last_5_transactions || []).slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink">
            {username ? `Welcome, ${username}` : "Welcome"}
          </h1>
          <p className="mt-1 text-sm text-muted">
            Your spending, saved cards and latest payments.
          </p>
        </div>
        <Link
          to={PAYMENT_PATH}
          className="rounded-xl bg-emerald-800 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-emerald-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2"
        >
          Make a payment
        </Link>
      </div>

      {/* Stat cards (all four come from GET /dashboard/summary) */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Total spent"
          value={inr(totalSpent)}
          note="Successful payments only"
        />
        <StatCard
          label="Available credit"
          value={inr(available)}
          note={`Limit ${inr(limit)}`}
        />
        <StatCard
          label="Total transactions"
          value={summary.total_transactions}
          note="Includes failed and pending"
        />
        <StatCard
          label="Spent this month"
          value={inr(monthSpent)}
          note="Successful payments only"
        />
      </div>

      {/* Chart + card */}
      <div className="grid gap-6 lg:grid-cols-5">
        <section className="rounded-2xl border border-line bg-surface p-6 shadow-sm lg:col-span-3">
          <div className="flex items-baseline justify-between">
            <h2 className="text-base font-semibold text-ink">
              Spending in the last 7 days
            </h2>
            <p className="text-sm text-muted">{inr(weekTotal)}</p>
          </div>
          <div className="mt-6">
            {weekTotal === 0 ? (
              <p className="py-12 text-center text-sm text-muted">
                No successful payments this week. Make a payment to see it here.
              </p>
            ) : (
              <SpendingChart days={days} />
            )}
          </div>
        </section>

        <section className="lg:col-span-2">
          <CardFace card={cards[0]} used={totalSpent} limit={limit} />
          <p className="mt-3 text-sm text-muted">
            {cards.length === 0 ? (
              <>
                No cards yet.{" "}
                <Link className="font-medium text-brand underline" to={CARDS_PATH}>
                  Add your first card
                </Link>
                .
              </>
            ) : (
              <>
                {cards.length} saved {cards.length === 1 ? "card" : "cards"}.{" "}
                <Link className="font-medium text-brand underline" to={CARDS_PATH}>
                  Manage cards
                </Link>
              </>
            )}
          </p>
        </section>
      </div>

      {/* Last 5 transactions */}
      <section className="rounded-2xl border border-line bg-surface p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-ink">
            Last 5 transactions
          </h2>
          <Link
            to={TRANSACTIONS_PATH}
            className="text-sm font-medium text-brand hover:underline"
          >
            View all
          </Link>
        </div>

        {last5.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted">
            No transactions yet. Make a payment to see it here.
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead>
                <tr className="border-b border-line text-muted">
                  <th className="pb-3 pr-4 font-medium">Date</th>
                  <th className="pb-3 pr-4 font-medium">Card</th>
                  <th className="pb-3 pr-4 text-right font-medium">Amount</th>
                  <th className="pb-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {last5.map((t, i) => (
                  <tr key={`${t.date}-${i}`}>
                    <td className="py-3 pr-4 text-ink">
                      {formatDateTime(t.date)}
                    </td>
                    <td className="py-3 pr-4 font-mono text-ink">
                      {t.masked_card || "Removed card"}
                    </td>
                    <td className="py-3 pr-4 text-right font-medium tabular-nums text-ink">
                      {inr(t.amount)}
                    </td>
                    <td className="py-3">
                      <StatusPill status={t.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}