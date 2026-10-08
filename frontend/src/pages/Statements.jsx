import { useState } from "react";
import { api, errMsg } from "../api";
import { Alert, Button, Field, PageHeader, Panel } from "../components/ui.jsx";

const MONTH_RE = /^\d{4}-(0[1-9]|1[0-2])$/;

function currentMonth() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

// With responseType "blob", an error body arrives as a Blob, so read it first
async function readError(e) {
  const body = e?.response?.data;
  if (body instanceof Blob) {
    try {
      const json = JSON.parse(await body.text());
      if (json.detail) return json.detail;
    } catch {
      /* fall through */
    }
    return "Could not create the statement.";
  }
  return errMsg(e);
}

export default function Statements() {
  const [month, setMonth] = useState(currentMonth());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const download = async () => {
    setError("");
    setNotice("");
    if (!MONTH_RE.test(month)) {
      setError("Please choose a month.");
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.get("/api/statements/", {
        params: { month },
        responseType: "blob",
      });
      const url = URL.createObjectURL(data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `statement-${month}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      setNotice(`Statement for ${month} downloaded.`);
    } catch (e) {
      setError(await readError(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Statements"
        subtitle="Download a PDF of your payments for any month: transactions, total spending and available credit."
      />
      <div className="space-y-4">
        <Alert>{error}</Alert>
        <Alert kind="success">{notice}</Alert>
        <Panel title="Monthly statement" className="max-w-md">
          <div className="space-y-4">
            <Field
              label="Month"
              type="month"
              value={month}
              max={currentMonth()}
              onChange={(e) => setMonth(e.target.value)}
              hint="Your own statement only. Card numbers are masked."
            />
            <Button onClick={download} disabled={busy}>
              {busy ? "Preparing..." : "Download PDF"}
            </Button>
          </div>
        </Panel>
      </div>
    </>
  );
}