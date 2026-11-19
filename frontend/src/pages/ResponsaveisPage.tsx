
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import axios from "axios";
import {
  Search,
  Plus,
  Pencil,
  Eye,
  Users,
  UserRound,
  UserX,
  RefreshCw,
  X,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { api } from "../services/api";

interface Responsavel {
  id: number;
  nome_completo: string;
  cpf: string | null;
  telefone: string;
  email: string | null;
  ativo: boolean;
}

interface ResponsavelForm {
  nome_completo: string;
  cpf: string;
  telefone: string;
  email: string;
}

const emptyForm: ResponsavelForm = {
  nome_completo: "",
  cpf: "",
  telefone: "",
  email: "",
};

const PAGE_SIZE = 10;

function getErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") return detail;

    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg).join(", ");
    }

    if (error.response?.status === 403) {
      return "Você não possui permissão para realizar esta operação.";
    }

    if (!error.response) {
      return "Não foi possível conectar ao servidor.";
    }
  }

  return "Ocorreu um erro inesperado. Tente novamente.";
}

function formatCpf(value: string | null) {
  if (!value) return "—";

  const cpf = value.replace(/\D/g, "");

  if (cpf.length !== 11) return value;

  return cpf.replace(
    /(\d{3})(\d{3})(\d{3})(\d{2})/,
    "$1.$2.$3-$4",
  );
}

export default function ResponsaveisPage() {
  const { user } = useAuth();
  const permissoes = user?.permissoes ?? [];

  const podeListar = permissoes.includes("responsaveis.listar");
  const podeCriar = permissoes.includes("responsaveis.criar");
  const podeEditar = permissoes.includes("responsaveis.editar");
  const podeInativar = permissoes.includes("responsaveis.desativar");

  const [responsaveis, setResponsaveis] = useState<Responsavel[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [search, setSearch] = useState("");
  const [filtroStatus, setFiltroStatus] = useState("todos");
  const [currentPage, setCurrentPage] = useState(1);

  const [modal, setModal] = useState<
    "create" | "edit" | "view" | null
  >(null);

  const [selectedResponsavel, setSelectedResponsavel] =
    useState<Responsavel | null>(null);

  const [form, setForm] = useState<ResponsavelForm>(emptyForm);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const carregarResponsaveis = useCallback(async () => {
    if (!podeListar) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await api.get<Responsavel[]>("/responsaveis/", {
        params: { offset: 0, limit: 100 },
      });

      setResponsaveis(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [podeListar]);

  useEffect(() => {
    void carregarResponsaveis();
  }, [carregarResponsaveis]);

  const responsaveisFiltrados = useMemo(() => {
    const termo = search.trim().toLocaleLowerCase("pt-BR");

    return responsaveis
      .filter((responsavel) => {
        if (
          filtroStatus === "ativos" &&
          !responsavel.ativo
        ) {
          return false;
        }

        if (
          filtroStatus === "inativos" &&
          responsavel.ativo
        ) {
          return false;
        }

        if (!termo) return true;

        return [
          responsavel.nome_completo,
          responsavel.cpf ?? "",
          responsavel.telefone,
          responsavel.email ?? "",
        ].some((valor) =>
          valor.toLocaleLowerCase("pt-BR").includes(termo),
        );
      })
      .sort((a, b) =>
        a.nome_completo.localeCompare(b.nome_completo, "pt-BR"),
      );
  }, [responsaveis, search, filtroStatus]);

  const totalPages = Math.max(
    1,
    Math.ceil(responsaveisFiltrados.length / PAGE_SIZE),
  );

  const responsaveisPagina = responsaveisFiltrados.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE,
  );

  useEffect(() => {
    setCurrentPage(1);
  }, [search, filtroStatus]);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const abrirCadastro = () => {
    setSelectedResponsavel(null);
    setForm(emptyForm);
    setError("");
    setModal("create");
  };

  const abrirEdicao = (responsavel: Responsavel) => {
    setSelectedResponsavel(responsavel);

    setForm({
      nome_completo: responsavel.nome_completo,
      cpf: responsavel.cpf ?? "",
      telefone: responsavel.telefone,
      email: responsavel.email ?? "",
    });

    setError("");
    setModal("edit");
  };

  const abrirDetalhes = (responsavel: Responsavel) => {
    setSelectedResponsavel(responsavel);
    setModal("view");
  };

  const fecharModal = () => {
    if (saving) return;

    setModal(null);
    setSelectedResponsavel(null);
    setError("");
  };

  const atualizarCampo = (
    campo: keyof ResponsavelForm,
    valor: string,
  ) => {
    setForm((anterior) => ({
      ...anterior,
      [campo]: valor,
    }));
  };

  const salvarResponsavel = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (modal === "create" && !podeCriar) return;
    if (modal === "edit" && !podeEditar) return;

    const cpf = form.cpf.replace(/\D/g, "");

    if (cpf && cpf.length !== 11) {
      setError("O CPF deve possuir exatamente 11 números.");
      return;
    }

    const dados = {
      nome_completo: form.nome_completo.trim(),
      cpf: cpf || null,
      telefone: form.telefone.trim(),
      email: form.email.trim() || null,
    };

    setSaving(true);

    try {
      if (modal === "create") {
        await api.post("/responsaveis/", dados);
        setSuccess("Responsável cadastrado com sucesso!");
      } else if (modal === "edit" && selectedResponsavel) {
        await api.put(
          `/responsaveis/${selectedResponsavel.id}`,
          dados,
        );
        setSuccess("Responsável atualizado com sucesso!");
      }

      setModal(null);
      setSelectedResponsavel(null);

      await carregarResponsaveis();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const inativarResponsavel = async (
    responsavel: Responsavel,
  ) => {
    if (!podeInativar) return;

    const confirmar = window.confirm(
      `Deseja realmente inativar o cadastro de ${responsavel.nome_completo}?\n\nOs vínculos históricos serão preservados.`,
    );

    if (!confirmar) return;

    setError("");
    setSuccess("");

    try {
      await api.delete(`/responsaveis/${responsavel.id}`);

      setSuccess("Responsável inativado com sucesso.");
      await carregarResponsaveis();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const reativarResponsavel = async (
    responsavel: Responsavel,
  ) => {
    if (!podeEditar) return;

    const confirmar = window.confirm(
      `Deseja reativar o cadastro de ${responsavel.nome_completo}?`,
    );

    if (!confirmar) return;

    setError("");
    setSuccess("");

    try {
      await api.put(`/responsaveis/${responsavel.id}`, {
        ativo: true,
      });

      setSuccess("Responsável reativado com sucesso.");
      await carregarResponsaveis();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  if (!podeListar) {
    return (
      <div className="page-stack">
        <div className="page-heading">
          <div>
            <p className="eyebrow">GESTÃO ACADÊMICA</p>
            <h2>Responsáveis</h2>
          </div>
        </div>

        <div className="card-surface empty-state">
          <UserX size={36} />
          <h3>Acesso não autorizado</h3>
          <p>
            Seu perfil não possui permissão para consultar os responsáveis.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-stack">
      <div className="page-heading students-heading">
        <div>
          <p className="eyebrow">GESTÃO ACADÊMICA</p>
          <h2>Responsáveis</h2>
          <p className="muted">
            Consulte e gerencie os responsáveis cadastrados na instituição.
          </p>
        </div>

        {podeCriar && (
          <button
            className="primary-button students-add"
            onClick={abrirCadastro}
          >
            <Plus size={18} />
            Novo responsável
          </button>
        )}
      </div>

      {success && (
        <div className="students-alert success-alert">
          {success}
          <button
            onClick={() => setSuccess("")}
            aria-label="Fechar mensagem"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {error && !modal && (
        <div className="students-alert error-alert">
          {error}
          <button
            onClick={() => setError("")}
            aria-label="Fechar mensagem"
          >
            <X size={16} />
          </button>
        </div>
      )}

      <div className="students-stats">
        <div className="card-surface students-stat">
          <div className="students-stat-icon">
            <Users size={21} />
          </div>
          <div>
            <span>Total de responsáveis</span>
            <strong>{responsaveis.length}</strong>
          </div>
        </div>

        <div className="card-surface students-stat">
          <div className="students-stat-icon active-stat-icon">
            <UserRound size={21} />
          </div>
          <div>
            <span>Responsáveis ativos</span>
            <strong>
              {responsaveis.filter((item) => item.ativo).length}
            </strong>
          </div>
        </div>

        <div className="card-surface students-stat">
          <div className="students-stat-icon inactive-stat-icon">
            <UserX size={21} />
          </div>
          <div>
            <span>Responsáveis inativos</span>
            <strong>
              {responsaveis.filter((item) => !item.ativo).length}
            </strong>
          </div>
        </div>
      </div>

      <div className="card-surface students-table-card">
        <div className="students-toolbar">
          <div>
            <h3>Lista de responsáveis</h3>
            <p className="muted">
              {responsaveisFiltrados.length} registro(s) encontrado(s)
            </p>
          </div>

          <select
            className="students-class-filter"
            value={filtroStatus}
            onChange={(event) => setFiltroStatus(event.target.value)}
            aria-label="Filtrar responsáveis por situação"
          >
            <option value="todos">Todos</option>
            <option value="ativos">Ativos</option>
            <option value="inativos">Inativos</option>
          </select>

          <div className="students-search">
            <Search size={18} />
            <input
              type="search"
              placeholder="Pesquisar por nome, CPF ou telefone..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>

          <button
            className="icon-button"
            onClick={() => void carregarResponsaveis()}
            disabled={loading}
            title="Atualizar lista"
            aria-label="Atualizar lista"
          >
            <RefreshCw size={18} />
          </button>
        </div>

        {loading ? (
          <div className="students-loading">
            <RefreshCw size={22} className="spin-icon" />
            <span>Carregando responsáveis...</span>
          </div>
        ) : responsaveisPagina.length === 0 ? (
          <div className="empty-state students-empty">
            <div className="empty-icon">
              <Users size={25} />
            </div>
            <h3>
              {search || filtroStatus !== "todos"
                ? "Nenhum resultado encontrado"
                : "Nenhum responsável cadastrado"}
            </h3>
            <p>
              {search || filtroStatus !== "todos"
                ? "Tente alterar a pesquisa ou o filtro."
                : "Os responsáveis cadastrados aparecerão nesta lista."}
            </p>
          </div>
        ) : (
          <>
            <div className="students-table-wrapper">
              <table className="students-table">
                <thead>
                  <tr>
                    <th>Responsável</th>
                    <th>CPF</th>
                    <th>Telefone</th>
                    <th>E-mail</th>
                    <th>Status</th>
                    <th className="actions-column">Ações</th>
                  </tr>
                </thead>

                <tbody>
                  {responsaveisPagina.map((responsavel) => (
                    <tr key={responsavel.id}>
                      <td>
                        <div className="student-name-cell">
                          <div className="student-avatar">
                            {responsavel.nome_completo
                              .charAt(0)
                              .toUpperCase()}
                          </div>
                          <div>
                            <strong>{responsavel.nome_completo}</strong>
                            <span>ID #{responsavel.id}</span>
                          </div>
                        </div>
                      </td>

                      <td>{formatCpf(responsavel.cpf)}</td>
                      <td>{responsavel.telefone}</td>
                      <td>{responsavel.email || "—"}</td>

                      <td>
                        <span
                          className={`status-badge ${
                            responsavel.ativo
                              ? "status-ativo"
                              : "status-inativo"
                          }`}
                        >
                          {responsavel.ativo ? "Ativo" : "Inativo"}
                        </span>
                      </td>

                      <td>
                        <div className="student-actions">
                          <button
                            className="icon-button"
                            onClick={() => abrirDetalhes(responsavel)}
                            title="Visualizar responsável"
                            aria-label="Visualizar responsável"
                          >
                            <Eye size={17} />
                          </button>

                          {podeEditar && (
                            <button
                              className="icon-button"
                              onClick={() => abrirEdicao(responsavel)}
                              title="Editar responsável"
                              aria-label="Editar responsável"
                            >
                              <Pencil size={17} />
                            </button>
                          )}

                          {responsavel.ativo && podeInativar && (
                            <button
                              className="icon-button danger-icon"
                              onClick={() =>
                                void inativarResponsavel(responsavel)
                              }
                              title="Inativar responsável"
                              aria-label="Inativar responsável"
                            >
                              <UserX size={17} />
                            </button>
                          )}

                          {!responsavel.ativo && podeEditar && (
                            <button
                              className="icon-button"
                              onClick={() =>
                                void reativarResponsavel(responsavel)
                              }
                              title="Reativar responsável"
                              aria-label="Reativar responsável"
                            >
                              <RefreshCw size={17} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="students-pagination">
              <span>
                Página {currentPage} de {totalPages}
              </span>

              <div>
                <button
                  className="icon-button"
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage((page) => page - 1)}
                  aria-label="Página anterior"
                >
                  <ChevronLeft size={18} />
                </button>

                <button
                  className="icon-button"
                  disabled={currentPage >= totalPages}
                  onClick={() => setCurrentPage((page) => page + 1)}
                  aria-label="Próxima página"
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {modal && (
        <div
          className="students-modal-backdrop"
          onMouseDown={fecharModal}
        >
          <div
            className="students-modal"
            onMouseDown={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="responsavel-modal-title"
          >
            <div className="students-modal-header">
              <div>
                <p className="eyebrow">
                  {modal === "view" ? "CONSULTA" : "GESTÃO ACADÊMICA"}
                </p>
                <h3 id="responsavel-modal-title">
                  {modal === "create"
                    ? "Cadastrar responsável"
                    : modal === "edit"
                      ? "Editar responsável"
                      : "Detalhes do responsável"}
                </h3>
              </div>

              <button
                className="icon-button"
                onClick={fecharModal}
                disabled={saving}
                aria-label="Fechar"
              >
                <X size={20} />
              </button>
            </div>

            {modal === "view" && selectedResponsavel ? (
              <div className="student-details">
                <div className="student-details-heading">
                  <div className="student-avatar large-avatar">
                    {selectedResponsavel.nome_completo
                      .charAt(0)
                      .toUpperCase()}
                  </div>

                  <div>
                    <h4>{selectedResponsavel.nome_completo}</h4>
                    <span
                      className={`status-badge ${
                        selectedResponsavel.ativo
                          ? "status-ativo"
                          : "status-inativo"
                      }`}
                    >
                      {selectedResponsavel.ativo ? "Ativo" : "Inativo"}
                    </span>
                  </div>
                </div>

                <div className="student-details-grid">
                  <Detail
                    label="CPF"
                    value={formatCpf(selectedResponsavel.cpf)}
                  />
                  <Detail
                    label="Telefone"
                    value={selectedResponsavel.telefone}
                  />
                  <Detail
                    label="E-mail"
                    value={selectedResponsavel.email}
                  />
                  <Detail
                    label="Código do cadastro"
                    value={`#${selectedResponsavel.id}`}
                  />
                </div>

                <div className="students-form-note">
                  Os vínculos entre responsáveis e alunos são gerenciados
                  no cadastro de cada aluno.
                </div>

                <div className="students-modal-footer">
                  <button
                    className="secondary-button"
                    onClick={fecharModal}
                  >
                    Fechar
                  </button>

                  {podeEditar && (
                    <button
                      className="primary-button"
                      onClick={() => abrirEdicao(selectedResponsavel)}
                    >
                      <Pencil size={16} />
                      Editar cadastro
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <form onSubmit={salvarResponsavel}>
                {error && <div className="form-error">{error}</div>}

                <div className="students-form-grid">
                  <Field label="Nome completo *" full>
                    <input
                      required
                      minLength={3}
                      maxLength={150}
                      value={form.nome_completo}
                      onChange={(event) =>
                        atualizarCampo(
                          "nome_completo",
                          event.target.value,
                        )
                      }
                      placeholder="Nome completo do responsável"
                    />
                  </Field>

                  <Field label="CPF">
                    <input
                      maxLength={14}
                      value={form.cpf}
                      onChange={(event) =>
                        atualizarCampo("cpf", event.target.value)
                      }
                      placeholder="Somente números"
                    />
                  </Field>

                  <Field label="Telefone *">
                    <input
                      required
                      minLength={8}
                      maxLength={20}
                      value={form.telefone}
                      onChange={(event) =>
                        atualizarCampo("telefone", event.target.value)
                      }
                      placeholder="(99) 99999-9999"
                    />
                  </Field>

                  <Field label="E-mail" full>
                    <input
                      type="email"
                      maxLength={150}
                      value={form.email}
                      onChange={(event) =>
                        atualizarCampo("email", event.target.value)
                      }
                      placeholder="email@exemplo.com"
                    />
                  </Field>
                </div>

                <p className="students-form-note">
                  * Campos obrigatórios. O CPF e o e-mail são opcionais.
                </p>

                <div className="students-modal-footer">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={fecharModal}
                    disabled={saving}
                  >
                    Cancelar
                  </button>

                  <button
                    type="submit"
                    className="primary-button"
                    disabled={saving}
                  >
                    {saving ? "Salvando..." : "Salvar cadastro"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Field({
  label,
  children,
  full = false,
}: {
  label: string;
  children: ReactNode;
  full?: boolean;
}) {
  return (
    <label className={`students-field${full ? " field-full" : ""}`}>
      <span>{label}</span>
      {children}
    </label>
  );
}

function Detail({
  label,
  value,
}: {
  label: string;
  value: string | null | undefined;
}) {
  return (
    <div className="student-detail-item">
      <span>{label}</span>
      <strong>{value || "—"}</strong>
    </div>
  );
}
