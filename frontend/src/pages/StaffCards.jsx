import { useEffect, useState } from "react";
import { errMsg } from "../api";
import { fapi } from "../fastapi";
import { Alert, Button, PageHeader, Panel } from "../components/ui.jsx";
import { useRole } from "../utils/roleGuard.jsx";

export default function StaffCards() {
  const { role, can, loading: roleLoading } = useRole();
  const [cards, setCards] = useState([]);
  const [limits, setLimits] = useState({});
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [busy, setBusy] = useState(null);

  const load = () =>
    fapi.get("/admin/cards")
      .then((r) => { setCards(r.data); setError(""); })
      .catch((e) => setError(errMsg(e)));

  useEffect(() => { load(); }, []);

  const act = async (id, path, body, message) => {
    setBusy(id);
    setError("");
    setOk("");
    try {
      await fapi.post(`/admin/cards/${id}/${path}`, body);
      setOk(message);
      await load();
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setBusy(null);
    }
  };

  const toggleBlock = (c) => {
    const verb = c.is_blocked ? "unblock" : "block";
    if (!window.confirm(`Are you sure you want to ${verb} card ${c.masked_number}? This is recorded in the audit log.`)) return;
    act(c.id, verb, undefined, `Card ${c.masked_number} ${verb}ed`);
  };

  const saveLimit = (c) => {
    const value = limits[c.id];
    if (!value) return;
    act(c.id, "limit", { credit_limit: String(value) }, `Limit for ${c.masked_number} set to ${value}`);
  };

  const input = "w-32 rounded border border-slate-300 bg-transparent px-2 py-1 text-sm dark:border-slate-600";

  return (
    <>
      <PageHeader
        title="Card management"
        subtitle={roleLoading ? "Checking your role..." : role ? `Signed in with the ${role} role. Buttons depend on your permissions.` : "You do not have a staff role."}
      />
      <Alert>{error}</Alert>
      <Alert kind="ok">{ok}</Alert>

      <Panel>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase opacity-70">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">User</th>
                <th className="px-3 py-2">Card</th>
                <th className="px-3 py-2">Limit</th>
                <th className="px-3 py-2">Spent</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {cards.map((c) => (
                <tr key={c.id} className="border-t border-slate-200 dark:border-slate-700">
                  <td className="px-3 py-2">{c.id}</td>
                  <td className="px-3 py-2">{c.user_id}</td>
                  <td className="px-3 py-2 font-mono">{c.masked_number}</td>
                  <td className="px-3 py-2">
                    {can("card:limit") ? (
                      <div className="flex gap-2">
                        <input
                          type="number"
                          min="1"
                          className={input}
                          placeholder={String(c.credit_limit)}
                          value={limits[c.id] ?? ""}
                          onChange={(e) => setLimits({ ...limits, [c.id]: e.target.value })}
                        />
                        <Button type="button" variant="ghost" disabled={busy === c.id || !limits[c.id]} onClick={() => saveLimit(c)}>
                          Save
                        </Button>
                      </div>
                    ) : (
                      c.credit_limit.toLocaleString()
                    )}
                  </td>
                  <td className="px-3 py-2">{c.spent.toLocaleString()}</td>
                  <td className={`px-3 py-2 ${c.is_blocked ? "font-semibold text-red-600" : ""}`}>
                    {c.is_blocked ? "BLOCKED" : "ACTIVE"}
                  </td>
                  <td className="px-3 py-2">
                    {can("card:block") ? (
                      <Button type="button" variant={c.is_blocked ? "ghost" : "danger"} disabled={busy === c.id} onClick={() => toggleBlock(c)}>
                        {c.is_blocked ? "Unblock" : "Block"}
                      </Button>
                    ) : (
                      <span className="opacity-60">View only</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}