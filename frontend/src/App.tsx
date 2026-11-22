
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./components/AppLayout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import AlunosPage from "./pages/AlunosPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import ResponsaveisPage from "./pages/ResponsaveisPage";
import ProfessoresPage from "./pages/ProfessoresPage";
import DisciplinasPage from "./pages/DisciplinasPage";
import MatriculasPage from "./pages/MatriculasPage";
import HorariosPage from "./pages/HorariosPage";
import VinculosPage from "./pages/VinculosPage";
import FrequenciaPage from "./pages/FrequenciaPage";
import UsuariosPage from "./pages/UsuariosPage";

import TurmasPage from "./pages/TurmasPage";

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="screen-message">Carregando aplicação...</div>;
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <LoginPage />}
      />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="alunos" element={<AlunosPage />} />
          <Route path="turmas" element={<TurmasPage />} />
          <Route path="responsaveis" element={<ResponsaveisPage />} />
          <Route path="professores" element={<ProfessoresPage />} />
          <Route path="matriculas" element={<MatriculasPage />} />
          <Route path="disciplinas" element={<DisciplinasPage />} />
          <Route path="horarios" element={<HorariosPage />} />
          <Route path="vinculos" element={<VinculosPage />} />
          <Route path="frequencias" element={<FrequenciaPage />} />
          <Route path="usuarios" element={<UsuariosPage />} />

          <Route path="*" element={<PlaceholderPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
