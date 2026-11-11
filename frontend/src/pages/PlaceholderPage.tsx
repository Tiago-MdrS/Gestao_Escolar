import { useLocation } from "react-router-dom";

const titles: Record<string, string> = {
  alunos: "Alunos", responsaveis: "Responsáveis", professores: "Professores",
  turmas: "Turmas", disciplinas: "Disciplinas", matriculas: "Matrículas",
  horarios: "Horários", usuarios: "Usuários e perfis", calendarios: "Calendários escolares",
  frequencias: "Frequências", avaliacoes: "Avaliações", notas: "Notas",
  recuperacoes: "Recuperações", configuracoes: "Configurações",
};

export default function PlaceholderPage() {
  const { pathname } = useLocation();
  const key = pathname.split("/").filter(Boolean)[0] ?? "";
  const title = titles[key] ?? "Módulo";
  return (
    <div className="page-stack">
      <div className="page-heading"><div><p className="eyebrow">MÓDULO</p><h2>{title}</h2><p className="muted">Área preparada para integração com a API.</p></div></div>
      <div className="card-surface module-placeholder">
        <h3>{title}</h3>
        <p>Esta tela ainda não consulta nem altera dados. A integração será implementada módulo por módulo, respeitando os contratos do backend.</p>
      </div>
    </div>
  );
}