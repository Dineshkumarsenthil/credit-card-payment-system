import { useEffect, useState } from "react";
import { errMsg } from "../api";
import { fapi } from "../fastapi";
import { Alert, Button, Field, Panel, Select } from "./ui.jsx";

const blank = { status: "", min_amount: "", max_amount: "", date_from: "", date_to: "", card: "" };

export default function TransactionSearch({ endpoint = "/transactions/search", showUser = false }) {
  const [form, setForm] = useState(blank);
  const [applied, setApplied] = useState(blank);
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState("created_at");
  const [order, setOrder] = useState("desc");
  const [data, setData] = useState({ items: [], total: 0, pages: 1 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  useEffect(() => {
    const params = { page, page_size: 10, sort_by: sortBy, order };
    Object.entries(applied).forEach(([k, v]) => { if (v !== "") params[k] = v; });
    setLoading(true);
    fapi.get(endpoint, { params })
      .then((r) => { setData(r.data); setError(""); })
      .catch((e) => setError(errMsg(e)))
      .finally(() => setLoading(false));
  }, [endpoint, applied, page, sortBy, order]);

  const apply = (e) => { e.preventDefault(); setPage(1); setApplied(form); };
  const reset = () => { setForm(blank); setApplied(blank); setPage(1); };
  const sort = (col) => {
    if (sortBy === col) setOrder(order === "asc" ? "desc" : "asc");
    else { setSortBy(col); setOrder("asc"); }
    setPage(1);
  };
  const arrow = (col) => (sortBy === col ? (order === "asc" ? " \u25B2" : " \u25BC") : "");
  const th = "px-3 py-2 font-medium";
  const sortable = `${th} cursor-pointer select-none`;

  return (
    <div className="space-y-4">
      <Panel>
        <form onSubmit={apply} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
          <Select label="Status" value={form.status} onChange={set("status")}>
            <option value="">All</option>
            <option value="SUCCESS">Success</option>
            <option value="FAILED">Failed</option>
            <option value="PENDING">Pending</option>
          </Select>
          <Field label="Min amount" type="number" min="0" step="0.01" value={form.min_amount} onChange={set("min_amount")} />
          <Field label="Max amount" type="number" min="0" step="0.01" value={form.max_amount} onChange={set("max_amount")} />
          <Field label="From date" type="date" value={form.date_from} onChange={set("date_from")} />
          <Field label="To date" type="date" value={form.date_to} onChange={set("date_to")} />
          <Field label="Card last 4 digits" inputMode="numeric" maxLength={4} value={form.card} onChange={set("card")} />
          <div className="flex gap-2 sm:col-span-2 lg:col-span-6">
            <Button type="submit">Search</Button>
            <Button type="button" variant="ghost" onClick={reset}>Clear</Button>
          </div>
        </form>
      </Panel>

      <Alert>{error}</Alert>

      <Panel>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase opacity-70">
              <tr>
                <th className={sortable} onClick={() => sort("id")}>ID{arrow("id")}</th>
                {showUser && <th className={th}>User</th>}
                <th className={th}>Card</th>
                <th className={sortable} onClick={() => sort("amount")}>Amount{arrow("amount")}</th>
                <th className={sortable} onClick={() => sort("category")}>Category{arrow("category")}</th>
                <th className={sortable} onClick={() => sort("status")}>Status{arrow("status")}</th>
                <th className={th}>Fraud</th>
                <th className={sortable} onClick={() => sort("created_at")}>Date{arrow("created_at")}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={8} className="px-3 py-6 text-center opacity-70">Loading...</td></tr>
              ) : data.items.length === 0 ? (
                <tr><td colSpan={8} className="px-3 py-6 text-center opacity-70">No transactions found</td></tr>
              ) : (
                data.items.map((t) => (
                  <tr key={t.id} className="border-t border-slate-200 dark:border-slate-700">
                    <td className="px-3 py-2">{t.id}</td>
                    {showUser && <td className="px-3 py-2">{t.user_id}</td>}
                    <td className="px-3 py-2 font-mono">{t.card}</td>
                    <td className="px-3 py-2">{t.amount.toLocaleString()} {t.currency}</td>
                    <td className="px-3 py-2">{t.category}</td>
                    <td className="px-3 py-2">{t.status}</td>
                    <td className={`px-3 py-2 ${t.fraud_status === "flagged" ? "font-semibold text-red-600" : ""}`}>
                      {t.fraud_status}
                    </td>
                    <td className="px-3 py-2">{new Date(t.created_at).toLocaleString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex items-center justify-between text-sm">
          <span className="opacity-70">{data.total} results &middot; page {data.page || page} of {data.pages || 1}</span>
          <div className="flex gap-2">
            <Button type="button" variant="ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>Prev</Button>
            <Button type="button" variant="ghost" disabled={page >= (data.pages || 1)} onClick={() => setPage(page + 1)}>Next</Button>
          </div>
        </div>
      </Panel>
    </div>
  );
}