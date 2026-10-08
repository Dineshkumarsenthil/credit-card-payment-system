import { useCallback, useEffect, useState } from "react";
import { api, errMsg } from "../api";
import { Alert, Button, Empty, Field, StatusBadge } from "./ui.jsx";
import { dateTime, money } from "../utils";

const pad = (m) => String(m).padStart(2, "0");

export default function CardManagement() {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busyId, setBusyId] = useState(null);
  const [editId, setEditId] = useState(null);
  const [limitValue, setLimitValue] = useState("");
  const [activity, setActivity] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/api/admin/cards/");
      setCards(data);
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const replaceCard = (updated) =>
    setCards((list) => list.map((c) => (c.id === updated.id ? updated : c)));

  // Runs one admin request, updates the row from the server response
  const run = async (card, request, message) => {
    setBusyId(card.id);
    setError("");
    setNotice("");
    try {
      const { data } = await request();
      replaceCard(data);
      setNotice(message);
      return true;
    } catch (e) {
      setError(errMsg(e));
      return false;
    } finally {
      setBusyId(null);
    }
  };

  const toggleBlock = (card) => {
    const verb = card.is_blocked ? "unblock" : "block";
    if (!window.confirm(`Are you sure you want to ${verb} the card ending ${card.last4}?`)) return;
    run(card, () => api.post(`/api/admin/cards/${card.id}/${verb}/`),
      `Card ending ${card.last4} was ${verb}ed.`);
  };

  const startEdit = (card) => {
    setEditId(card.id);
    setLimitValue(String(card.credit_limit));
  };

  const saveLimit = async (card) => {
    const ok = await run(card,
      () => api.patch(`/api/admin/cards/${card.id}/limit/`, { credit_limit: limitValue }),
      `Credit limit updated for the card ending ${card.last4}.`);
    if (ok) setEditId(null);
  };

  const openActivity = async (card) => {
    setError("");
    try {
      const { data } = await api.get(`/api/admin/cards/${card.id}/activity/`);
      setActivity({ card, ...data });
    } catch (e) {
      setError(errMsg(e));
    }
  };

  if (loading) return <p className="text-sm text-muted">Loading...</p>;

  return (
    <div className="space-y-4">
      <Alert>{error}</Alert>
      <Alert kind="success">{notice}</Alert>

      {!cards.length ? <Empty>No cards have been added yet.</Empty> : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead>
              <tr className="border-b border-line text-muted">
                <th className="py-2 pr-4 font-medium">User</th>
                <th className="py-2 pr-4 font-medium">Card</th>
                <th className="py-2 pr-4 font-medium">Expiry</th>
                <th className="py-2 pr-4 font-medium">Credit limit</th>
                <th className="py-2 pr-4 font-medium">Status</th>
                <th className="py-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {cards.map((c) => (
                <tr key={c.id} className="border-b border-line/60 align-top last:border-0">
                  <td className="py-2.5 pr-4">{c.username}</td>
                  <td className="py-2.5 pr-4">
                    {c.brand}
                    <div className="text-xs text-muted">{c.masked_number}</div>
                  </td>
                  <td className="py-2.5 pr-4">{pad(c.expiry_month)}/{c.expiry_year}</td>
                  <td className="py-2.5 pr-4">
                    {editId === c.id ? (
                      <div className="flex items-end gap-2">
                        <div className="w-36">
                          <Field
                            label="New limit"
                            type="number"
                            min="1"
                            step="0.01"
                            value={limitValue}
                            onChange={(e) => setLimitValue(e.target.value)}
                          />
                        </div>
                        <Button onClick={() => saveLimit(c)} disabled={busyId === c.id}>Save</Button>
                        <Button variant="ghost" onClick={() => setEditId(null)}>Cancel</Button>
                      </div>
                    ) : money(Number(c.credit_limit))}
                  </td>
                  <td className="py-2.5 pr-4">
                    <span
                      className={`inline-block rounded px-2 py-0.5 text-xs font-semibold ${
                        c.is_blocked ? "bg-bad/10 text-bad" : "bg-ok/10 text-ok"
                      }`}
                    >
                      {c.is_blocked ? "BLOCKED" : "ACTIVE"}
                    </span>
                  </td>
                  <td className="py-2.5">
                    <div className="flex flex-wrap gap-2">
                      <Button
                        variant={c.is_blocked ? "ghost" : "danger"}
                        disabled={busyId === c.id}
                        aria-label={`${c.is_blocked ? "Unblock" : "Block"} card ending ${c.last4}`}
                        onClick={() => toggleBlock(c)}
                      >
                        {c.is_blocked ? "Unblock" : "Block"}
                      </Button>
                      <Button
                        variant="ghost"
                        aria-label={`Edit limit of card ending ${c.last4}`}
                        onClick={() => startEdit(c)}
                      >
                        Edit limit
                      </Button>
                      <Button
                        variant="ghost"
                        aria-label={`View activity of card ending ${c.last4}`}
                        onClick={() => openActivity(c)}
                      >
                        Activity
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activity && (
        <section aria-label="Card activity" className="rounded-xl border border-line p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold">
              Recent activity: {activity.card.username}, {activity.card.masked_number}
            </h3>
            <Button variant="ghost" onClick={() => setActivity(null)}>Close</Button>
          </div>

          <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">Payments</h4>
          {!activity.transactions.length ? <Empty>No payments on this card yet.</Empty> : (
            <div className="overflow-x-auto">
              <table className="mb-4 w-full min-w-[520px] text-left text-sm">
                <tbody>
                  {activity.transactions.map((t) => (
                    <tr key={t.id} className="border-b border-line/60 last:border-0">
                      <td className="py-2 pr-4 whitespace-nowrap">{dateTime(t.created_at)}</td>
                      <td className="py-2 pr-4">{t.description || "-"}</td>
                      <td className="py-2 pr-4 text-right">{money(Number(t.amount), t.currency)}</td>
                      <td className="py-2"><StatusBadge status={t.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">Admin actions</h4>
          {!activity.logs.length ? <Empty>No admin actions on this card yet.</Empty> : (
            <ul className="space-y-1 text-sm">
              {activity.logs.map((l) => (
                <li key={l.id}>
                  <span className="text-muted">{dateTime(l.created_at)}</span>{" "}
                  {l.admin__username || "unknown"}: {l.details}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}