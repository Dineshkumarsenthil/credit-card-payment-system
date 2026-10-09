import { useEffect, useState } from "react";
import { api, errMsg } from "../api.js";
import { Alert, Button, Empty, PageHeader, Panel, Select, TxnTable } from "../components/ui.jsx";
import CardManagement from "../components/CardManagement.jsx";
import { dateTime, money } from "../utils";

const tabs = [
  { id: "summary", label: "Daily summary", url: "/api/admin/summary/" },
  { id: "users", label: "Users", url: "/api/admin/users/" },
  { id: "cards", label: "Cards", url: null },
  { id: "transactions", label: "Transactions", url: "/api/admin/transactions/" },
];

function Table({ head, rows }) {
  if (!rows.length) return <Empty>Nothing to show yet.</Empty>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead>
          <tr className="border-b border-line text-muted">
            {head.map((h) => <th key={h} className="py-2 pr-4 font-medium">{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-line/60 last:border-0">
              {r.map((c, j) => <td key={j} className="py-2.5 pr-4">{c}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function AdminDashboard() {
  const [tab, setTab] = useState("summary");
  const [data, setData] = useState([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const current = tabs.find((t) => t.id === tab);
    setError("");
    // The Cards tab loads its own data inside CardManagement
    if (!current.url) {
      setData([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    api.get(current.url, { params: tab === "transactions" && status ? { status } : {} })
      .then((r) => setData(r.data))
      .catch((e) => { setData([]); setError(errMsg(e)); })
      .finally(() => setLoading(false));
  }, [tab, status]);

  const exportCsv = async () => {
    try {
      const { data: blob } = await api.get("/api/admin/transactions/export/", { responseType: "blob" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "transactions.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(errMsg(e));
    }
  };

  return (
    <>
      <PageHeader title="Admin" subtitle="Manage users and cards, and review transactions and daily payment totals.">
        <Button onClick={exportCsv}>Export transactions to CSV</Button>
      </PageHeader>

      <div role="tablist" className="mb-4 flex flex-wrap gap-1 border-b border-line">
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${tab === t.id ? "border-brand text-brand" : "border-transparent text-muted hover:text-ink"}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <Alert>{error}</Alert>
      <Panel>
        {tab === "transactions" && (
          <div className="mb-4 max-w-xs">
            <Select label="Status" value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">All</option>
              <option value="SUCCESS">Success</option>
              <option value="FAILED">Failed</option>
              <option value="PENDING">Pending</option>
            </Select>
          </div>
        )}
        {tab === "cards" && <CardManagement />}
        {tab !== "cards" && (loading ? <p className="text-sm text-muted">Loading...</p> : (
          <>
            {tab === "summary" && (
              <Table
                head={["Date", "Total", "Success", "Failed", "Pending", "Amount collected"]}
                rows={data.map((d) => [d.day, d.total, d.success, d.failed, d.pending, money(d.success_amount || 0)])}
              />
            )}
            {tab === "users" && (
              <Table
                head={["ID", "Username", "Email", "Role", "Joined"]}
                rows={data.map((u) => [u.id, u.username, u.email, u.is_staff ? "Admin" : "Customer", dateTime(u.date_joined)])}
              />
            )}
            {tab === "transactions" && <TxnTable rows={data} showUser />}
          </>
        ))}
      </Panel>
    </>
  );
}