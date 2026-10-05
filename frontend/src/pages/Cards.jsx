import { useEffect, useState } from "react";
import { api, errMsg } from "../api";
import { Alert, Button, Empty, Field, PageHeader, Panel } from "../components/ui.jsx";

const blank = { card_holder: "", card_number: "", cvv: "", expiry_month: "", expiry_year: "" };

export default function Cards() {
  const [cards, setCards] = useState([]);
  const [f, setF] = useState(blank);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const load = () => api.get("/api/cards/").then((r) => setCards(r.data)).catch((e) => setError(errMsg(e)));
  useEffect(() => { load(); }, []);

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setOk(""); setBusy(true);
    try {
      await api.post("/api/cards/", {
        ...f,
        expiry_month: Number(f.expiry_month),
        expiry_year: Number(f.expiry_year),
      });
      setF(blank); // the full number and CVV are cleared from the browser right away
      setOk("Card saved. Only the last 4 digits are kept.");
      load();
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Delete this card?")) return;
    try {
      await api.delete(`/api/cards/${id}/`);
      load();
    } catch (err) {
      setError(errMsg(err));
    }
  };

  return (
    <>
      <PageHeader title="Cards" subtitle="The full card number and CVV are checked, then discarded. Only the masked number is stored." />
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Add a card">
          <form onSubmit={submit} className="space-y-4">
            <Alert>{error}</Alert>
            <Alert kind="ok">{ok}</Alert>
            <Field label="Name on card" value={f.card_holder} onChange={set("card_holder")} required />
            <Field label="Card number" value={f.card_number} onChange={set("card_number")} inputMode="numeric" autoComplete="off" placeholder="4111 1111 1111 1111" required />
            <div className="grid grid-cols-3 gap-3">
              <Field label="Month" type="number" min="1" max="12" value={f.expiry_month} onChange={set("expiry_month")} required />
              <Field label="Year" type="number" min="2026" max="2100" value={f.expiry_year} onChange={set("expiry_year")} required />
              <Field label="CVV" type="password" inputMode="numeric" maxLength={4} value={f.cvv} onChange={set("cvv")} autoComplete="off" required />
            </div>
            <Button type="submit" disabled={busy}>{busy ? "Saving..." : "Save card"}</Button>
          </form>
        </Panel>

        <Panel title="Saved cards">
          {cards.length === 0 ? (
            <Empty>No saved cards yet. Add one to start paying.</Empty>
          ) : (
            <ul className="space-y-3">
              {cards.map((c) => (
                <li key={c.id} className="flex items-center justify-between rounded-md border border-line p-3">
                  <div>
                    <div className="text-sm font-medium">{c.brand} {c.masked_number}</div>
                    <div className="text-xs text-muted">{c.card_holder} · expires {String(c.expiry_month).padStart(2, "0")}/{c.expiry_year}</div>
                  </div>
                  <Button variant="danger" onClick={() => remove(c.id)}>Delete</Button>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </>
  );
}
