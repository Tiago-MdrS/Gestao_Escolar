import { useState, type FormEvent } from "react";
import { GraduationCap, LockKeyhole, Mail } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { useNavigate } from "react-router-dom";

export default function LoginPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await signIn(username, password);
      navigate("/", { replace: true });
    } catch {
      setError("Não foi possível entrar. Confira seu e-mail e sua senha.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-screen">
      <section className="login-card">
        <div className="login-logo"><GraduationCap size={30} /></div>
        <h1>Gestão Escolar</h1>
        <p className="muted">Colégio Batista Bob Pierce</p>
        <form onSubmit={handleSubmit} className="login-form">
          <label htmlFor="username">E-mail</label>
          <div className="input-with-icon"><Mail size={18} /><input id="username" type="email" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required placeholder="seu@email.com" /></div>
          <label htmlFor="password">Senha</label>
          <div className="input-with-icon"><LockKeyhole size={18} /><input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="Digite sua senha" /></div>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="primary-button login-button" disabled={submitting}>{submitting ? "Entrando..." : "Entrar"}</button>
        </form>
        <p className="login-footnote">Acesso restrito a usuários cadastrados.</p>
      </section>
    </main>
  );
}