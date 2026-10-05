import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, payApi, errMsg } from "../api";
import { Alert, Button, Field, PageHeader, Panel, Select } from "../components/ui.jsx";
import CardVisual from "../components/CardVisual.jsx";
import { dateTime, money } from "../utils";

const presets = [199, 499, 999, 2499];

function Row({ label, value }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-muted">{label}</dt>
      <dd className="text-right font-medium">{value}</dd>
    </div>
  );
}

export default function MakePayment() {
  const [cards, setCards] = useState([]);
  const [cardId, setCardId] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [step, setStep] = useState("form"); // form, confirm, processing, done
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    api.get("/api/cards/").then((r) => {
      setCards(r.data);
      if (r.data[0]) setCardId(String(r.data[0].id));
    }).catch((e) => setError(errMsg(e)));
  }, []);

  const card = cards.find((c) => String(c.id) === cardId);
  const expiry = card ? `${String(card.expiry_month).padStart(2, "0")}/${String(card.expiry_year).slice(-2)}` : "";

  const review = (e) => { e.preventDefault(); setError(""); setStep("confirm"); };

  const pay = async () => {
    setError(""); setResult(null); setStep("processing");
    try {
      const { data } = await payApi.post("/payments", {
        card_id: Number(cardId),
        amount: String(amount),
        currency: "INR",
        description,
      });
      setResult(data);
      setStep("done");
    } catch (err) {
      setError(errMsg(err));
      setStep("form");
    }
  };

  const reset = () => { setAmount(""); setDescription(""); setResult(null); setStep("form"); };

  if (cards.length === 0 && !error) {
    return (
      <>
        <PageHeader title="Make a payment" />
        <Panel><p className="text-sm">You need a saved card first. <Link to="/cards" className="font-medium text-brand underline">Add a card</Link>.</p></Panel>
      </>
    );
  }

  const ok = result?.status === "SUCCESS";

  return (
    <>
      <PageHeader title="Make a payment" subtitle="Simulated gateway: every payment starts as pending and settles as success or failed." />
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title={step === "confirm" ? "Review and confirm" : "Payment details"}>
          {step === "form" && (
            <form onSubmit={review} className="space-y-4">
              <Alert>{error}</Alert>
              <Select label="Pay with" value={cardId} onChange={(e) => setCardId(e.target.value)} required>
                {cards.map((c) => <option key={c.id} value={c.id}>{c.brand} {c.masked_number}</option>)}
              </Select>
              <Field label="Amount (INR)" type="number" min="0.01" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required />
              <div className="flex flex-wrap gap-2">
                {presets.map((p) => (
                  <button key={p} type="button" onClick={() => setAmount(String(p))}
                    className="rounded-full border border-line px-3 py-1 text-xs font-medium hover:border-brand hover:text-brand">
                    {money(p)}
                  </button>
                ))}
              </div>
              <Field label="Description" value={description} onChange={(e) => setDescription(e.target.value)} maxLength={255} placeholder="What is this payment for?" />
              <Button type="submit" className="w-full">Review payment</Button>
            </form>
          )}

          {step === "confirm" && (
            <div className="space-y-5">
              <Alert>{error}</Alert>
              <div className="rounded-xl bg-paper p-4 text-center">
                <div className="text-xs uppercase tracking-wide text-muted">You are paying</div>
                <div className="text-3xl font-semibold">{money(amount)}</div>
              </div>
              <dl className="space-y-2 text-sm">
                <Row label="Card" value={`${card?.brand} •••• ${card?.last4}`} />
                <Row label="For" value={description || "-"} />
                <Row label="Fee" value={money(0)} />
              </dl>
              <div className="flex gap-3">
                <Button variant="ghost" onClick={() => setStep("form")}>Back</Button>
                <Button onClick={pay} className="flex-1">Confirm and pay {money(amount)}</Button>
              </div>
            </div>
          )}

          {(step === "processing" || step === "done") && (
            <p className="text-sm text-muted">
              {step === "processing" ? "Your payment is being processed." : "Payment complete. See the receipt."}
            </p>
          )}
        </Panel>

        <div>
          {card && <CardVisual brand={card.brand} number={card.masked_number} holder={card.card_holder.toUpperCase()} expiry={expiry} />}

          {step === "processing" && (
            <div className="mt-5 rounded-2xl border border-line bg-white p-6 text-center shadow-sm">
              <div className="mx-auto mb-3 h-10 w-10 animate-spin rounded-full border-4 border-line border-t-brand" />
              <div className="font-medium text-warn">PENDING</div>
              <p className="mt-1 text-sm text-muted">Waiting for the payment to settle...</p>
            </div>
          )}

          {step === "done" && result && (
            <div className="mt-5 rounded-2xl border border-line bg-white p-6 text-center shadow-sm">
              <div className={`mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full text-2xl text-white ${ok ? "bg-ok" : "bg-bad"}`}>{ok ? "✓" : "✕"}</div>
              <div className="text-sm text-muted">{ok ? "Payment successful" : "Payment failed"}</div>
              <div className="mt-1 text-3xl font-semibold">{money(result.amount, result.currency)}</div>
              {result.failure_reason && <div className="mt-1 text-sm text-bad">{result.failure_reason}</div>}
              <dl className="mt-5 space-y-2 border-t border-dashed border-line pt-4 text-left text-sm">
                <Row label="Status" value={result.status} />
                <Row label="Reference" value={String(result.reference).slice(0, 18)} />
                <Row label="Date" value={dateTime(result.created_at)} />
              </dl>
              <div className="mt-5 flex justify-center gap-3">
                <Button variant="ghost" onClick={reset}>New payment</Button>
                <Link to="/transactions"><Button>View history</Button></Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
