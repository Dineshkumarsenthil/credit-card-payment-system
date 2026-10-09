import { useState } from "react";
import { errMsg } from "../api";
import { fapi } from "../fastapi";
import { Alert, Button } from "./ui.jsx";

export default function ExportButtons() {
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  const download = async (format) => {
    setBusy(format);
    setError("");
    try {
      const res = await fapi.get("/analytics/export", { params: { format }, responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `analytics_summary.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setBusy("");
    }
  };

  return (
    <div className="space-y-2">
      <Alert>{error}</Alert>
      <div className="flex gap-2">
        <Button type="button" disabled={!!busy} onClick={() => download("csv")}>
          {busy === "csv" ? "Exporting..." : "Export CSV"}
        </Button>
        <Button type="button" disabled={!!busy} onClick={() => download("pdf")}>
          {busy === "pdf" ? "Exporting..." : "Export PDF"}
        </Button>
      </div>
    </div>
  );
}