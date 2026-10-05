import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

const link = ({ isActive }) =>
  `block rounded-lg px-3 py-2 text-sm font-medium ${isActive ? "bg-white/15 text-white" : "text-white/70 hover:bg-white/10 hover:text-white"}`;

export default function Layout() {
  const { user, logout } = useAuth();
  const nav = useNavigate();

  const signOut = async () => {
    await logout();
    nav("/login");
  };

  return (
    <div className="min-h-screen md:flex">
      <aside className="bg-gradient-to-b from-brand-dark to-[#0f0d33] p-4 text-white md:sticky md:top-0 md:flex md:h-screen md:w-60 md:flex-col md:justify-between">
        <div>
          <div className="mb-4 px-3 text-lg font-semibold">SecurePay</div>
          <nav className="flex gap-1 overflow-x-auto md:flex-col">
            <NavLink to="/" end className={link}>Dashboard</NavLink>
            <NavLink to="/cards" className={link}>Cards</NavLink>
            <NavLink to="/pay" className={link}>Make payment</NavLink>
            <NavLink to="/transactions" className={link}>Transactions</NavLink>
            {user?.is_staff && <NavLink to="/admin" className={link}>Admin</NavLink>}
          </nav>
        </div>
        <div className="mt-4 border-t border-white/15 pt-4">
          <div className="px-3 text-sm">{user?.username}</div>
          <div className="mb-2 px-3 text-xs text-white/60">{user?.is_staff ? "Administrator" : "Customer"}</div>
          <button onClick={signOut} className="w-full rounded-lg px-3 py-2 text-left text-sm text-white/80 hover:bg-white/10">
            Log out
          </button>
        </div>
      </aside>
      <main className="flex-1 p-5 md:p-10">
        <div className="mx-auto max-w-5xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
