
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
  GraduationCap,
  X,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  UserX,
  Users,

} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { api } from "../services/api";

interface Professor {
  id: number;
  nome_completo: string;
  cpf: string | null;
  data_nascimento: string | null;
  telefone: string;
  email: string | null;
  formacao_academica: string | null;
  especializacao: string | null;
  area_atuacao: string | null;
  data_admissao: string | null;
  ativo: boolean;
  data_cadastro: string;
}

interface ProfessorForm {
  nome_completo: string;
  cpf: string;
  data_nascimento: string;
  telefone: string;
  email: string;
  formacao_academica: string;
  especializacao: string;
  area_atuacao: string;
  data_admissao: string;
}

type ModalType = "create" | "edit" | "view" | null;

const PAGE_SIZE = 10;

const emptyForm: ProfessorForm = {
  nome_completo: "",
  cpf: "",
  data_nascimento: "",
  telefone: "",
  email: "",
  formacao_academica: "",
  especializacao: "",
  area_atuacao: "",
  data_admissao: "",
};

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

function formatDate(value: string | null) {
  if (!value) return "Não informado";

  const [year, month, day] = value.split("-");
  if (!year || !month || !day) return value;

  return `${day}/${month}/${year}`;
}

function formatCPF(value: string | null) {
  if (!value) return "Não informado";

  const cpf = value.replace(/\D/g, "");

  if (cpf.length !== 11) return value;

  return cpf.replace(
    /^(\d{3})(\d{3})(\d{3})(\d{2})$/,
    "$1.$2.$3-$4"
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
    <label className={`students-field ${full ? "field-full" : ""}`}>
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
  value: ReactNode;
}) {
  return (
    <div className="student-detail-item">
      <span>{label}</span>
      <strong>{value || "Não informado"}</strong>
    </div>
  );
}

export default function ProfessoresPage() {
  const { user } = useAuth();

  const permissoes = user?.permissoes ?? [];

  const podeListar = permissoes.includes("professores.listar");
  const podeCriar = permissoes.includes("professores.criar");
  const podeEditar = permissoes.includes("professores.editar");
  const podeInativar = permissoes.includes("professores.desativar");

  const [professores, setProfessores] = useState<Professor[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [search, setSearch] = useState("");
  const [statusFiltro, setStatusFiltro] = useState("todos");
  const [currentPage, setCurrentPage] = useState(1);

  const [modal, setModal] = useState<ModalType>(null);
  const [selectedProfessor, setSelectedProfessor] =
    useState<Professor | null>(null);

  const [form, setForm] = useState<ProfessorForm>(emptyForm);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const carregarProfessores = useCallback(async () => {
    if (!podeListar) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await api.get<Professor[]>("/professores/", {
        params: {
          offset: 0,
          limit: 100,
        },
      });

      setProfessores(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [podeListar]);

  useEffect(() => {
    carregarProfessores();
  }, [carregarProfessores]);

  const professoresFiltrados = useMemo(() => {
    const termo = search.trim().toLowerCase();

    return professores.filter((professor) => {
      const correspondeBusca =
        !termo ||
        professor.nome_completo.toLowerCase().includes(termo) ||
        (professor.cpf ?? "").includes(termo.replace(/\D/g, "")) ||
        professor.telefone.includes(termo) ||
        (professor.email ?? "").toLowerCase().includes(termo) ||
        (professor.area_atuacao ?? "").toLowerCase().includes(termo);

      const correspondeStatus =
        statusFiltro === "todos" ||
        (statusFiltro === "ativos" && professor.ativo) ||
        (statusFiltro === "inativos" && !professor.ativo);

      return correspondeBusca && correspondeStatus;
    });
  }, [professores, search, statusFiltro]);

  const totalPages = Math.max(
    1,
    Math.ceil(professoresFiltrados.length / PAGE_SIZE)
  );

  const professoresPaginados = professoresFiltrados.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const totalAtivos = professores.filter((p) => p.ativo).length;
  const totalInativos = professores.filter((p) => !p.ativo).length;

  function atualizarCampo(
    campo: keyof ProfessorForm,
    valor: string
  ) {
    setForm((atual) => ({
      ...atual,
      [campo]: valor,
    }));
  }

  function abrirCadastro() {
    setSelectedProfessor(null);
    setForm(emptyForm);
    setError("");
    setModal("create");
  }

  function abrirEdicao(professor: Professor) {
    setSelectedProfessor(professor);

    setForm({
      nome_completo: professor.nome_completo,
      cpf: professor.cpf ?? "",
      data_nascimento: professor.data_nascimento ?? "",
      telefone: professor.telefone,
      email: professor.email ?? "",
      formacao_academica: professor.formacao_academica ?? "",
      especializacao: professor.especializacao ?? "",
      area_atuacao: professor.area_atuacao ?? "",
      data_admissao: professor.data_admissao ?? "",
    });

    setError("");
    setModal("edit");
  }

  function abrirDetalhes(professor: Professor) {
    setSelectedProfessor(professor);
    setModal("view");
  }

  function fecharModal() {
    if (saving) return;

    setModal(null);
    setSelectedProfessor(null);
    setForm(emptyForm);
    setError("");
  }

  async function salvarProfessor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setSuccess("");

    const cpf = form.cpf.replace(/\D/g, "");

    if (cpf && cpf.length !== 11) {
      setError("O CPF deve conter exatamente 11 números.");
      return;
    }

    const telefone = form.telefone.trim();

    if (telefone.length < 8 || telefone.length > 20) {
      setError("O telefone deve conter entre 8 e 20 caracteres.");
      return;
    }

    const dados = {
      nome_completo: form.nome_completo.trim(),
      cpf: cpf || null,
      data_nascimento: form.data_nascimento || null,
      telefone,
      email: form.email.trim() || null,
      formacao_academica: form.formacao_academica.trim() || null,
      especializacao: form.especializacao.trim() || null,
      area_atuacao: form.area_atuacao.trim() || null,
      data_admissao: form.data_admissao || null,
    };

    setSaving(true);

    try {
      if (modal === "create") {
        await api.post("/professores/", dados);
        setSuccess("Professor cadastrado com sucesso!");
      } else if (modal === "edit" && selectedProfessor) {
        await api.put(
          `/professores/${selectedProfessor.id}`,
          dados
        );
        setSuccess("Professor atualizado com sucesso!");
      }

      setModal(null);
      setSelectedProfessor(null);
      setForm(emptyForm);

      await carregarProfessores();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function inativarProfessor(professor: Professor) {
    const confirmar = window.confirm(
      `Deseja realmente inativar ${professor.nome_completo}?`
    );

    if (!confirmar) return;

    setError("");
    setSuccess("");

    try {
      await api.delete(`/professores/${professor.id}`);

      setSuccess("Professor inativado com sucesso!");
      await carregarProfessores();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  async function reativarProfessor(professor: Professor) {
    const confirmar = window.confirm(
      `Deseja reativar ${professor.nome_completo}?`
    );

    if (!confirmar) return;

    setError("");
    setSuccess("");

    try {
      await api.put(`/professores/${professor.id}`, {
        ativo: true,
      });

      setSuccess("Professor reativado com sucesso!");
      await carregarProfessores();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  if (!podeListar) {
    return (
      <div className="page-stack">
        <div className="card-surface empty-state">
          <UserX size={34} />
          <h2>Acesso não permitido</h2>
          <p>Você não possui permissão para consultar os professores.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-stack">
      <div className="page-heading students-heading">
        <div>
          <span className="eyebrow">GESTÃO ACADÊMICA</span>
          <h1>Professores</h1>
          <p className="muted">
            Gerencie os professores cadastrados na instituição.
          </p>
        </div>

        {podeCriar && (
          <button
            className="primary-button students-add"
            onClick={abrirCadastro}
          >
            <Plus size={18} />
            Novo professor
          </button>
        )}
      </div>

      {error && !modal && (
        <div className="students-alert error-alert">
          {error}
        </div>
      )}

      {success && (
        <div className="students-alert success-alert">
          {success}
        </div>
      )}

      <div className="students-stats">
        <div className="card-surface students-stat">
          <div className="students-stat-icon">
            <Users size={22} />
          </div>
          <div>
            <span>Total de professores</span>
            <strong>{professores.length}</strong>
          </div>
        </div>

        <div className="card-surface students-stat">
          <div className="students-stat-icon active-stat-icon">
            <GraduationCap size={22} />
          </div>
          <div>
            <span>Professores ativos</span>
            <strong>{totalAtivos}</strong>
          </div>
        </div>

        <div className="card-surface students-stat">
          <div className="students-stat-icon inactive-stat-icon">
            <UserX size={22} />
          </div>
          <div>
            <span>Professores inativos</span>
            <strong>{totalInativos}</strong>
          </div>
        </div>
      </div>

      <div className="card-surface students-table-card">
        <div className="students-toolbar">
          <div className="students-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Buscar por nome, CPF, telefone ou área..."
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setCurrentPage(1);
              }}
            />
          </div>

          <select
            className="students-class-filter"
            value={statusFiltro}
            onChange={(event) => {
              setStatusFiltro(event.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="todos">Todos os status</option>
            <option value="ativos">Ativos</option>
            <option value="inativos">Inativos</option>
          </select>

          <button
            className="secondary-button"
            onClick={carregarProfessores}
            disabled={loading}
            title="Atualizar lista"
          >
            <RefreshCw size={16} />
          </button>
        </div>

        {loading ? (
          <div className="students-loading">
            <RefreshCw size={22} className="spin" />
            <span>Carregando professores...</span>
          </div>
        ) : professoresPaginados.length === 0 ? (
          <div className="students-empty">
            <GraduationCap size={36} />
            <h3>Nenhum professor encontrado</h3>
            <p>
              Não existem professores correspondentes à pesquisa.
            </p>
          </div>
        ) : (
          <>
            <div className="students-table-wrapper">
              <table className="students-table">
                <thead>
                  <tr>
                    <th>Professor</th>
                    <th>CPF</th>
                    <th>Telefone</th>
                    <th>Área de atuação</th>
                    <th>Status</th>
                    <th>Ações</th>
                  </tr>
                </thead>

                <tbody>
                  {professoresPaginados.map((professor) => (
                    <tr key={professor.id}>
                      <td>
                        <div className="student-name-cell">
                          <div className="student-avatar">
                            <GraduationCap size={19} />
                          </div>
                          <div>
                            <strong>{professor.nome_completo}</strong>
                            <span>
                              {professor.email || "E-mail não informado"}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td>{formatCPF(professor.cpf)}</td>
                      <td>{professor.telefone}</td>
                      <td>
                        {professor.area_atuacao || "Não informada"}
                      </td>

                      <td>
                        <span
                          className={`status-badge ${
                            professor.ativo ? "active" : "inactive"
                          }`}
                        >
                          {professor.ativo ? "Ativo" : "Inativo"}
                        </span>
                      </td>

                      <td>
                        <div className="student-actions">
                          <button
                            className="icon-button"
                            title="Visualizar"
                            onClick={() => abrirDetalhes(professor)}
                          >
                            <Eye size={17} />
                          </button>

                          {podeEditar && (
                            <button
                              className="icon-button"
                              title="Editar"
                              onClick={() => abrirEdicao(professor)}
                            >
                              <Pencil size={17} />
                            </button>
                          )}

                          {professor.ativo && podeInativar && (
                            <button
                              className="icon-button danger-icon"
                              title="Inativar"
                              onClick={() => inativarProfessor(professor)}
                            >
                              <UserX size={17} />
                            </button>
                          )}

                          {!professor.ativo && podeEditar && (
                            <button
                              className="icon-button"
                              title="Reativar"
                              onClick={() => reativarProfessor(professor)}
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
                Mostrando{" "}
                {professoresFiltrados.length === 0
                  ? 0
                  : (currentPage - 1) * PAGE_SIZE + 1}{" "}
                a{" "}
                {Math.min(
                  currentPage * PAGE_SIZE,
                  professoresFiltrados.length
                )}{" "}
                de {professoresFiltrados.length} professores
              </span>

              <div>
                <button
                  className="icon-button"
                  disabled={currentPage === 1}
                  onClick={() =>
                    setCurrentPage((page) => Math.max(1, page - 1))
                  }
                >
                  <ChevronLeft size={18} />
                </button>

                <span>
                  {currentPage} / {totalPages}
                </span>

                <button
                  className="icon-button"
                  disabled={currentPage >= totalPages}
                  onClick={() =>
                    setCurrentPage((page) =>
                      Math.min(totalPages, page + 1)
                    )
                  }
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
          >
            <div className="students-modal-header">
              <div>
                <span className="eyebrow">
                  {modal === "create"
                    ? "NOVO CADASTRO"
                    : modal === "edit"
                      ? "ATUALIZAÇÃO"
                      : "INFORMAÇÕES"}
                </span>

                <h2>
                  {modal === "create"
                    ? "Cadastrar professor"
                    : modal === "edit"
                      ? "Editar professor"
                      : "Detalhes do professor"}
                </h2>
              </div>

              <button
                className="icon-button"
                onClick={fecharModal}
                disabled={saving}
              >
                <X size={20} />
              </button>
            </div>

            {modal === "view" && selectedProfessor ? (
              <div className="student-details">
                <div className="student-details-heading">
                  <div className="student-avatar">
                    <GraduationCap size={24} />
                  </div>
                  <div>
                    <h3>{selectedProfessor.nome_completo}</h3>
                    <span
                      className={`status-badge ${
                        selectedProfessor.ativo ? "active" : "inactive"
                      }`}
                    >
                      {selectedProfessor.ativo ? "Ativo" : "Inativo"}
                    </span>
                  </div>
                </div>

                <div className="student-details-grid">
                  <Detail
                    label="CPF"
                    value={formatCPF(selectedProfessor.cpf)}
                  />
                  <Detail
                    label="Telefone"
                    value={selectedProfessor.telefone}
                  />
                  <Detail
                    label="E-mail"
                    value={selectedProfessor.email}
                  />
                  <Detail
                    label="Data de nascimento"
                    value={formatDate(selectedProfessor.data_nascimento)}
                  />
                  <Detail
                    label="Formação acadêmica"
                    value={selectedProfessor.formacao_academica}
                  />
                  <Detail
                    label="Especialização"
                    value={selectedProfessor.especializacao}
                  />
                  <Detail
                    label="Área de atuação"
                    value={selectedProfessor.area_atuacao}
                  />
                  <Detail
                    label="Data de admissão"
                    value={formatDate(selectedProfessor.data_admissao)}
                  />
                  <Detail
                    label="Data de cadastro"
                    value={formatDate(
                      selectedProfessor.data_cadastro?.slice(0, 10) ?? null
                    )}
                  />
                </div>
              </div>
            ) : (
              <form onSubmit={salvarProfessor}>
                <div className="students-form-grid">
                  <Field label="Nome completo *" full>
                    <input
                      required
                      minLength={3}
                      maxLength={150}
                      value={form.nome_completo}
                      onChange={(event) =>
                        atualizarCampo("nome_completo", event.target.value)
                      }
                      placeholder="Nome completo do professor"
                    />
                  </Field>

                  <Field label="CPF">
                    <input
                      value={form.cpf}
                      maxLength={14}
                      onChange={(event) =>
                        atualizarCampo("cpf", event.target.value)
                      }
                      placeholder="000.000.000-00"
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

                  <Field label="Data de nascimento">
                    <input
                      type="date"
                      max={new Date().toISOString().slice(0, 10)}
                      value={form.data_nascimento}
                      onChange={(event) =>
                        atualizarCampo("data_nascimento", event.target.value)
                      }
                    />
                  </Field>

                  <Field label="E-mail">
                    <input
                      type="email"
                      maxLength={150}
                      value={form.email}
                      onChange={(event) =>
                        atualizarCampo("email", event.target.value)
                      }
                      placeholder="professor@email.com"
                    />
                  </Field>

                  <Field label="Formação acadêmica">
                    <input
                      maxLength={150}
                      value={form.formacao_academica}
                      onChange={(event) =>
                        atualizarCampo("formacao_academica", event.target.value)
                      }
                      placeholder="Ex.: Licenciatura em Matemática"
                    />
                  </Field>

                  <Field label="Especialização">
                    <input
                      maxLength={150}
                      value={form.especializacao}
                      onChange={(event) =>
                        atualizarCampo("especializacao", event.target.value)
                      }
                      placeholder="Especialização do professor"
                    />
                  </Field>

                  <Field label="Área de atuação">
                    <input
                      maxLength={100}
                      value={form.area_atuacao}
                      onChange={(event) =>
                        atualizarCampo("area_atuacao", event.target.value)
                      }
                      placeholder="Ex.: Matemática"
                    />
                  </Field>

                  <Field label="Data de admissão">
                    <input
                      type="date"
                      value={form.data_admissao}
                      onChange={(event) =>
                        atualizarCampo("data_admissao", event.target.value)
                      }
                    />
                  </Field>
                </div>

                <p className="students-form-note">
                  Os campos marcados com * são obrigatórios.
                </p>

                {error && (
                  <div className="form-error">
                    {error}
                  </div>
                )}

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
                    {saving
                      ? "Salvando..."
                      : modal === "create"
                        ? "Cadastrar professor"
                        : "Salvar alterações"}
                  </button>
                </div>
              </form>
            )}

            {modal === "view" && (
              <div className="students-modal-footer">
                <button
                  className="secondary-button"
                  onClick={fecharModal}
                >
                  Fechar
                </button>

                {selectedProfessor &&
                  podeEditar &&
                  (
                    <button
                      className="primary-button"
                      onClick={() => abrirEdicao(selectedProfessor)}
                    >
                      <Pencil size={16} />
                      Editar professor
                    </button>
                  )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
