import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function ProtectedRoute() {
  const { user, loading } = useAuth();

  if (loading) return <div className="screen-message">Carregando sessão...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}