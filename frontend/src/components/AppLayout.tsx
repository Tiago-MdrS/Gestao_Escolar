import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  BookOpen,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  NotebookTabs,
  Settings,
  ShieldCheck,
  Users,
  UserRound,
  Clock3,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";

type MenuItem = {
  label: string;
  to: string;
  icon: typeof LayoutDashboard;
};

const commonItems: MenuItem[] = [
  { label: "Visão geral", to: "/", icon: LayoutDashboard },
  { label: "Calendário escolar", to: "/calendarios", icon: CalendarDays },
];

const managerItems: MenuItem[] = [
  { label: "Alunos", to: "/alunos", icon: Users },
  { label: "Responsáveis", to: "/responsaveis", icon: UserRound },
  { label: "Professores", to: "/professores", icon: GraduationCap },
  { label: "Turmas", to: "/turmas", icon: BookOpen },
  { label: "Disciplinas", to: "/disciplinas", icon: NotebookTabs },
  { label: "Matrículas", to: "/matriculas", icon: ClipboardCheck },
  { label: "Horários", to: "/horarios", icon: Clock3 },
  { label: "Usuários e perfis", to: "/usuarios", icon: ShieldCheck },
];

const teacherItems: MenuItem[] = [
  { label: "Meus horários", to: "/horarios", icon: Clock3 },
  { label: "Frequências", to: "/frequencias", icon: ClipboardCheck },
  { label: "Avaliações", to: "/avaliacoes", icon: NotebookTabs },
  { label: "Notas", to: "/notas", icon: BookOpen },
  { label: "Recuperações", to: "/recuperacoes", icon: GraduationCap },
];

const secretaryItems: MenuItem[] = [
  { label: "Alunos", to: "/alunos", icon: Users },
  { label: "Responsáveis", to: "/responsaveis", icon: UserRound },
  { label: "Matrículas", to: "/matriculas", icon: ClipboardCheck },
  { label: "Calendários", to: "/calendarios", icon: CalendarDays },
];

export default function AppLayout() {
  const { user, signOut } = useAuth();
  const [expanded, setExpanded] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();

  const profile = user?.perfil.nome ?? "Usuário";
  const normalized = profile.toLocaleLowerCase("pt-BR");

  const isTeacher = normalized.includes("professor");
  const isSecretary = normalized.includes("secretaria");
  const isManager =
    normalized.includes("gestor") ||
    normalized.includes("administrador");

  const roleItems = isTeacher
    ? teacherItems
    : isSecretary
      ? secretaryItems
      : managerItems;

  const items = isManager
    ? [...commonItems, ...managerItems]
    : [...commonItems, ...roleItems];

  const link = (item: MenuItem) => {
    const Icon = item.icon;

    return (
      <NavLink
        key={item.to}
        to={item.to}
        end={item.to === "/"}
        className={({ isActive }) =>
          `menu-link${isActive ? " active" : ""}`
        }
        title={!expanded ? item.label : undefined}
      >
        <Icon size={19} strokeWidth={1.9} />
        {expanded && <span>{item.label}</span>}
      </NavLink>
    );
  };

  return (
    <div className={`app-shell${expanded ? "" : " sidebar-collapsed"}`}>
      <aside className="sidebar">
        <button
          className="sidebar-brand"
          onClick={() => setExpanded((value) => !value)}
          aria-label="Recolher ou expandir menu"
        >
          <span className="brand-mark">
            <GraduationCap size={23} />
          </span>

          {expanded && (
            <span className="brand-name">
              Gestão Escolar
              <small>C.B.B.P.</small>
            </span>
          )}

          {expanded ? (
            <ChevronLeft className="collapse-icon" size={18} />
          ) : (
            <ChevronRight size={18} />
          )}
        </button>

        <div className="sidebar-user">
          <div className="avatar">
            {profile.slice(0, 1).toUpperCase()}
          </div>

          {expanded && (
            <div className="user-meta">
              <strong>{user?.nome_completo}</strong>
              <span>{profile}</span>
            </div>
          )}
        </div>

        <nav className="sidebar-nav">
          {expanded && (
            <span className="nav-caption">MENU PRINCIPAL</span>
          )}

          {items.map(link)}

          {expanded && (
            <span className="nav-caption">SISTEMA</span>
          )}

          <NavLink
            to="/configuracoes"
            className={({ isActive }) =>
              `menu-link${isActive ? " active" : ""}`
            }
            title={!expanded ? "Configurações" : undefined}
          >
            <Settings size={19} strokeWidth={1.9} />
            {expanded && <span>Configurações</span>}
          </NavLink>
        </nav>

        <button
          className="logout-link"
          onClick={() => {
            signOut();
            navigate("/login");
          }}
        >
          <LogOut size={19} strokeWidth={1.9} />
          {expanded && <span>Sair</span>}
        </button>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-title">
            <button
              className="mobile-menu"
              onClick={() => setExpanded((value) => !value)}
              aria-label="Alternar menu"
            >
              <Menu size={20} />
            </button>

            <div>
              <span className="breadcrumb">
                C.B.B.P. /{" "}
                {location.pathname.split("/").filter(Boolean).at(-1) ??
                  "Início"}
              </span>
              <h1>Gestão Escolar</h1>
            </div>
          </div>

          <div className="topbar-profile">
            <span className="status-dot" />
            {profile}
          </div>
        </header>

        <section className="page-content">
          <Outlet />
        </section>
      </main>
    </div>
  );
}
