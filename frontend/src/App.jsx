import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import Register from "./pages/Register.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Cards from "./pages/Cards.jsx";
import MakePayment from "./pages/MakePayment.jsx";
import Transactions from "./pages/Transactions.jsx";
import Statements from "./pages/Statements.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import AnalyticsDashboard from "./pages/AnalyticsDashboard.jsx";
import AdminHealth from "./pages/AdminHealth.jsx";
import { ThemeProvider } from "./theme/ThemeContext.jsx";
import StaffCards from "./pages/StaffCards.jsx";

export default function App() {
  return (
    <ThemeProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cards" element={<Cards />} />
          <Route path="/pay" element={<MakePayment />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/statements" element={<Statements />} />
          <Route path="/analytics" element={<AnalyticsDashboard />} />
          <Route path="/system-health" element={<AdminHealth />} />
          <Route path="/admin" element={<ProtectedRoute adminOnly><AdminDashboard /></ProtectedRoute>} />
          <Route path="/staff-cards" element={<StaffCards />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ThemeProvider>
  );
}