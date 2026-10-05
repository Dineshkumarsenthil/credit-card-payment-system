import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, payApi, errMsg } from "../api";
import { Alert, Button, Field, PageHeader, Panel, Select, StatusBadge } from "../components/ui.jsx";
import { dateTime, money } from "../utils";

export default function MakePayment() {
  const [cards, setCards] = useState([]);
  const [cardId, setCardId] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    api.get("/api/cards/").then((r) => {
      setCards(r.data);
      if (r.data[0]) setCardId(String(r.data[0].id));
    }).catch((e) => setError(errMsg(e)));
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setResult(null); setBusy(true);
    try {
      const { data } = await payApi.post("/payments", {
        card_id: Number(cardId),
        amount: String(amount),
        currency: "INR",
        description,
      });
      setResult(data);
      setAmount(""); setDescription("");
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  if (cards.length === 0 && !error) {
    return (
      <>
        <PageHeader title="Make a payment" />
        <Panel><p className="text-sm">You need a saved card first. <Link to="/cards" className="font-medium text-brand underline">Add a card</Link>.</p></Panel>
      </>
    );
  }

  return (
    <>
      <PageHeader title="Make a payment" subtitle="Payments are simulated. The result is randomly success or failed." />
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Payment details">
          <form onSubmit={submit} className="space-y-4">
            <Alert>{error}</Alert>
            <Select label="Pay with" value={cardId} onChange={(e) => setCardId(e.target.value)} required>
              {cards.map((c) => <option key={c.id} value={c.id}>{c.brand} {c.masked_number}</option>)}
            </Select>
            <Field label="Amount (INR)" type="number" min="0.01" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required />
            <Field label="Description" value={description} onChange={(e) => setDescription(e.target.value)} maxLength={255} placeholder="What is this payment for?" />
            <Button type="submit" disabled={busy}>{busy ? "Processing..." : "Pay now"}</Button>
          </form>
        </Panel>

        <Panel title="Result">
          {busy && <p className="text-sm text-muted">Status: <StatusBadge status="PENDING" /> Waiting for the payment to settle...</p>}
          {!busy && !result && <p className="text-sm text-muted">Submit a payment to see its final status here.</p>}
          {result && (
            <div className="space-y-2 text-sm">
              <div><StatusBadge status={result.status} /></div>
              <div className="text-2xl font-semibold">{money(result.amount, result.currency)}</div>
              {result.failure_reason && <div className="text-bad">{result.failure_reason}</div>}
              <div className="text-muted">Reference {result.reference}</div>
              <div className="text-muted">{dateTime(result.created_at)}</div>
              <Link to="/transactions" className="inline-block font-medium text-brand underline">View transaction history</Link>
            </div>
          )}
        </Panel>
      </div>
    </>
  );
}
