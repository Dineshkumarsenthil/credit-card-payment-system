import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, errMsg } from "../api";
import { Alert, AuthShell, Button, Field } from "../components/ui.jsx";

export default function Register() {
  const nav = useNavigate();
  const [f, setF] = useState({ username: "", email: "", password: "", password2: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (f.password !== f.password2) return setError("Passwords do not match.");
    setBusy(true);
    try {
      await api.post("/api/auth/register/", f);
      nav("/login", { state: { registered: true } });
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Create your account" subtitle="Use at least 8 characters with letters and numbers.">
      <form onSubmit={submit} className="space-y-4">
        <Alert>{error}</Alert>
        <Field label="Username" value={f.username} onChange={set("username")} required autoComplete="username" />
        <Field label="Email" type="email" value={f.email} onChange={set("email")} required autoComplete="email" />
        <Field label="Password" type="password" value={f.password} onChange={set("password")} required autoComplete="new-password" />
        <Field label="Confirm password" type="password" value={f.password2} onChange={set("password2")} required autoComplete="new-password" />
        <Button type="submit" disabled={busy} className="w-full">{busy ? "Creating account..." : "Create account"}</Button>
      </form>
      <p className="mt-5 text-sm text-muted">
        Already registered? <Link to="/login" className="font-medium text-brand underline">Log in</Link>
      </p>
    </AuthShell>
  );
}
