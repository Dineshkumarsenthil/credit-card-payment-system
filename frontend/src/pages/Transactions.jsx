import { useEffect, useState } from "react";
import { api, errMsg } from "../api";
import { Alert, Button, Field, PageHeader, Panel, Select, TxnTable } from "../components/ui.jsx";

const blank = { status: "", min_amount: "", max_amount: "", date_from: "", date_to: "" };

export function cleanParams(f) {
  return Object.fromEntries(Object.entries(f).filter(([, v]) => v !== ""));
}

export default function Transactions() {
  const [f, setF] = useState(blank);
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const load = (filters = f) =>
    api.get("/api/transactions/", { params: cleanParams(filters) })
      .then((r) => { setRows(r.data); setError(""); })
      .catch((e) => setError(errMsg(e)));

  useEffect(() => { load(blank); }, []);

  const apply = (e) => { e.preventDefault(); load(); };
  const reset = () => { setF(blank); load(blank); };

  return (
    <>
      <PageHeader title="Transactions" subtitle="Filter your payments by date, amount and status." />
      <Panel className="mb-6">
        <form onSubmit={apply} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Select label="Status" value={f.status} onChange={set("status")}>
            <option value="">All</option>
            <option value="SUCCESS">Success</option>
            <option value="FAILED">Failed</option>
            <option value="PENDING">Pending</option>
          </Select>
          <Field label="Min amount" type="number" min="0" step="0.01" value={f.min_amount} onChange={set("min_amount")} />
          <Field label="Max amount" type="number" min="0" step="0.01" value={f.max_amount} onChange={set("max_amount")} />
          <Field label="From date" type="date" value={f.date_from} onChange={set("date_from")} />
          <Field label="To date" type="date" value={f.date_to} onChange={set("date_to")} />
          <div className="flex gap-2 sm:col-span-2 lg:col-span-5">
            <Button type="submit">Apply filters</Button>
            <Button type="button" variant="ghost" onClick={reset}>Clear</Button>
          </div>
        </form>
      </Panel>
      <Alert>{error}</Alert>
      <Panel><TxnTable rows={rows} /></Panel>
    </>
  );
}
