import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { errMsg } from "../api";
import { Alert, AuthShell, Button, Field } from "../components/ui.jsx";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(username, password);
      nav("/");
    } catch (err) {
      setError(err.response?.status === 401 ? "Wrong username or password." : errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Log in" subtitle="Enter your username and password.">
      <form onSubmit={submit} className="space-y-4">
        {location.state?.registered && <Alert kind="ok">Account created. Log in to continue.</Alert>}
        <Alert>{error}</Alert>
        <Field label="Username" value={username} onChange={(e) => setUsername(e.target.value)} required autoComplete="username" />
        <Field label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
        <Button type="submit" disabled={busy} className="w-full">{busy ? "Logging in..." : "Log in"}</Button>
      </form>
      <p className="mt-5 text-sm text-muted">
        New here? <Link to="/register" className="font-medium text-brand underline">Create an account</Link>
      </p>
    </AuthShell>
  );
}
