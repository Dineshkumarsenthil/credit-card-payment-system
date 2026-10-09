import { useEffect, useState } from "react";
import { fapi } from "../fastapi";

export function useRole() {
  const [state, setState] = useState({ role: null, permissions: [], loading: true });

  useEffect(() => {
    fapi.get("/admin/me")
      .then((r) => setState({ role: r.data.role, permissions: r.data.permissions, loading: false }))
      .catch(() => setState({ role: null, permissions: [], loading: false }));
  }, []);

  return { ...state, can: (p) => state.permissions.includes(p) };
}

export function RoleGuard({ permission, children, fallback = null }) {
  const { can, loading } = useRole();
  if (loading) return null;
  return can(permission) ? children : fallback;
}