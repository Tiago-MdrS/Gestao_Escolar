import { useAuth } from "../auth/AuthContext";

export default function DashboardPage() {
  const { user } = useAuth();
  return (
    <div className="page-stack">
      <div className="page-heading"><div><p className="eyebrow">PAINEL</p><h2>Bem-vindo(a), {user?.nome_completo?.split(" ")[0]}</h2><p className="muted">Acompanhe as atividades acadêmicas da instituição.</p></div></div>
      <div className="empty-state card-surface">
        <div className="empty-icon"> <span>CB</span> </div>
        <h3>Estrutura inicial pronta</h3>
        <p>O painel será conectado aos dados reais do sistema nos próximos módulos.</p>
      </div>
    </div>
  );
}