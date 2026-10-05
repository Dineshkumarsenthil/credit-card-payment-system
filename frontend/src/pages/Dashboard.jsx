import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, errMsg } from "../api";
import { useAuth } from "../auth.jsx";
import { Alert, Empty, PageHeader, Panel, TxnTable } from "../components/ui.jsx";
import { money } from "../utils";

export default function Dashboard() {
  const { user } = useAuth();
  const [cards, setCards] = useState([]);
  const [txns, setTxns] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.get("/api/cards/"), api.get("/api/transactions/")])
      .then(([c, t]) => { setCards(c.data); setTxns(t.data); })
      .catch((e) => setError(errMsg(e)));
  }, []);

  const paid = txns.filter((t) => t.status === "SUCCESS").reduce((s, t) => s + Number(t.amount), 0);
  const failed = txns.filter((t) => t.status === "FAILED").length;

  return (
    <>
      <PageHeader title={`Welcome, ${user?.username}`} subtitle="Your saved cards and latest payments.">
        <Link to="/pay" className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark">
          Make a payment
        </Link>
      </PageHeader>
      <Alert>{error}</Alert>

      <div className="mb-6 grid grid-cols-1 divide-y divide-line rounded-lg border border-line bg-white sm:grid-cols-3 sm:divide-x sm:divide-y-0">
        <div className="p-5"><div className="text-sm text-muted">Paid successfully</div><div className="mt-1 text-2xl font-semibold">{money(paid)}</div></div>
        <div className="p-5"><div className="text-sm text-muted">Failed payments</div><div className="mt-1 text-2xl font-semibold">{failed}</div></div>
        <div className="p-5"><div className="text-sm text-muted">Saved cards</div><div className="mt-1 text-2xl font-semibold">{cards.length}</div></div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Panel title="Recent transactions" className="lg:col-span-2">
          <TxnTable rows={txns.slice(0, 5)} />
          {txns.length > 5 && <Link to="/transactions" className="mt-3 inline-block text-sm font-medium text-brand underline">See all transactions</Link>}
        </Panel>
        <Panel title="Your cards">
          {cards.length === 0 ? (
            <Empty>No cards yet. <Link to="/cards" className="text-brand underline">Add your first card</Link>.</Empty>
          ) : (
            <ul className="space-y-3">
              {cards.map((c) => (
                <li key={c.id} className="flex items-center justify-between text-sm">
                  <span>{c.brand} •••• {c.last4}</span>
                  <span className="text-muted">{String(c.expiry_month).padStart(2, "0")}/{c.expiry_year}</span>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </>
  );
}
