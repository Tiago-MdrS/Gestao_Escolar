
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import axios from "axios";
import {
  AlertCircle,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Eye,
  Link2,
  Pencil,
  Plus,
  RefreshCw,
  RotateCcw,
  Search,
  Trash2,
  Users,
  X,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { api } from "../services/api";
import "../styles/vinculos.css";

interface Vinculo {
  id: number;
  turma_id: number;
  disciplina_id: number;
  professor_id: number;
  carga_horaria_semanal: number;
  ativa: boolean;
  data_cadastro: string;
}

interface Turma {
  id: number;
  nome: string;
  ativa: boolean;
}

interface Disciplina {
  id: number;
  nome: string;
  ativa: boolean;
}

interface Professor {
  id: number;
  nome_completo: string;
  ativo: boolean;
}

type ModalMode = "create" | "edit" | "details" | null;
type StatusFilter = "todos" | "ativos" | "inativos";

interface FormData {
  turma_id: string;
  disciplina_id: string;
  professor_id: string;
  carga_horaria_semanal: string;
  ativa: boolean;
}

const INITIAL_FORM: FormData = {
  turma_id: "",
  disciplina_id: "",
  professor_id: "",
  carga_horaria_semanal: "1",
  ativa: true,
};

const PAGE_SIZE = 10;

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") return detail;

    if (Array.isArray(detail)) {
      return detail
        .map((item) => item.msg ?? "Erro de validação")
        .join(", ");
    }

    if (error.response?.status === 403) {
      return "Você não tem permissão para realizar esta operação.";
    }

    if (error.response?.status === 404) {
      return "O registro solicitado não foi encontrado.";
    }

    if (error.response?.status === 409) {
      return "Já existe um vínculo para esta combinação de turma e disciplina.";
    }

    return "Não foi possível concluir a operação. Verifique a conexão com o servidor.";
  }

  return "Ocorreu um erro inesperado.";
}

function formatDate(value: string): string {
  if (!value) return "—";

  return new Date(value).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export default function VinculosPage() {
  const { user } = useAuth();

  const permissions = user?.permissoes ?? [];
  const canList = permissions.includes("turma_disciplinas.listar");
  const canManage = permissions.includes("turma_disciplinas.gerenciar");

  const [vinculos, setVinculos] = useState<Vinculo[]>([]);
  const [turmas, setTurmas] = useState<Turma[]>([]);
  const [disciplinas, setDisciplinas] = useState<Disciplina[]>([]);
  const [professores, setProfessores] = useState<Professor[]>([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [auxiliaryError, setAuxiliaryError] = useState("");

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("todos");
  const [currentPage, setCurrentPage] = useState(1);

  const [modal, setModal] = useState<ModalMode>(null);
  const [selectedVinculo, setSelectedVinculo] = useState<Vinculo | null>(null);
  const [form, setForm] = useState<FormData>(INITIAL_FORM);

  const loadData = useCallback(async () => {
    if (!canList) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");
    setAuxiliaryError("");

    try {
      const vinculosResponse = await api.get<Vinculo[]>("/turma-disciplinas/", {
        params: { offset: 0, limit: 100 },
      });

      setVinculos(vinculosResponse.data);

      const requests = await Promise.allSettled([
        permissions.includes("turmas.listar")
          ? api.get<Turma[]>("/turmas/", {
              params: { offset: 0, limit: 100 },
            })
          : Promise.reject(new Error("Sem permissão para listar turmas.")),

        permissions.includes("disciplinas.listar")
          ? api.get<Disciplina[]>("/disciplinas/", {
              params: { offset: 0, limit: 100 },
            })
          : Promise.reject(new Error("Sem permissão para listar disciplinas.")),

        permissions.includes("professores.listar")
          ? api.get<Professor[]>("/professores/", {
              params: { offset: 0, limit: 100 },
            })
          : Promise.reject(new Error("Sem permissão para listar professores.")),
      ]);

      const [turmasResult, disciplinasResult, professoresResult] = requests;
      const auxiliaryErrors: string[] = [];

      if (turmasResult.status === "fulfilled") {
        setTurmas(turmasResult.value.data);
      } else {
        setTurmas([]);
        auxiliaryErrors.push("turmas");
      }

      if (disciplinasResult.status === "fulfilled") {
        setDisciplinas(disciplinasResult.value.data);
      } else {
        setDisciplinas([]);
        auxiliaryErrors.push("disciplinas");
      }

      if (professoresResult.status === "fulfilled") {
        setProfessores(professoresResult.value.data);
      } else {
        setProfessores([]);
        auxiliaryErrors.push("professores");
      }

      if (auxiliaryErrors.length > 0) {
        setAuxiliaryError(
          `Não foi possível carregar: ${auxiliaryErrors.join(", ")}. Verifique suas permissões.`
        );
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [canList, permissions]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const getTurmaNome = (id: number) =>
    turmas.find((item) => item.id === id)?.nome ?? `Turma #${id}`;

  const getDisciplinaNome = (id: number) =>
    disciplinas.find((item) => item.id === id)?.nome ?? `Disciplina #${id}`;

  const getProfessorNome = (id: number) =>
    professores.find((item) => item.id === id)?.nome_completo ??
    `Professor #${id}`;

  const filteredVinculos = useMemo(() => {
    const normalizedSearch = search.trim().toLocaleLowerCase("pt-BR");

    return vinculos.filter((vinculo) => {
      const matchesStatus =
        statusFilter === "todos" ||
        (statusFilter === "ativos" && vinculo.ativa) ||
        (statusFilter === "inativos" && !vinculo.ativa);

      const searchableText = [
        getTurmaNome(vinculo.turma_id),
        getDisciplinaNome(vinculo.disciplina_id),
        getProfessorNome(vinculo.professor_id),
      ]
        .join(" ")
        .toLocaleLowerCase("pt-BR");

      return (
        matchesStatus &&
        (!normalizedSearch || searchableText.includes(normalizedSearch))
      );
    });
  }, [vinculos, search, statusFilter, turmas, disciplinas, professores]);

  const totalPages = Math.max(1, Math.ceil(filteredVinculos.length / PAGE_SIZE));

  const paginatedVinculos = filteredVinculos.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const totalAtivos = vinculos.filter((item) => item.ativa).length;
  const totalInativos = vinculos.length - totalAtivos;

  const turmasAtivas = turmas.filter((item) => item.ativa);
  const disciplinasAtivas = disciplinas.filter((item) => item.ativa);
  const professoresAtivos = professores.filter((item) => item.ativo);

  const combinationExists =
    form.turma_id !== "" &&
    form.disciplina_id !== "" &&
    vinculos.some(
      (item) =>
        item.turma_id === Number(form.turma_id) &&
        item.disciplina_id === Number(form.disciplina_id)
    );

  const openCreateModal = () => {
    setSelectedVinculo(null);
    setForm(INITIAL_FORM);
    setError("");
    setSuccess("");
    setModal("create");
  };

  const openEditModal = (vinculo: Vinculo) => {
    setSelectedVinculo(vinculo);
    setForm({
      ...INITIAL_FORM,
      carga_horaria_semanal: String(vinculo.carga_horaria_semanal),
      ativa: vinculo.ativa,
    });
    setError("");
    setSuccess("");
    setModal("edit");
  };

  const openDetailsModal = (vinculo: Vinculo) => {
    setSelectedVinculo(vinculo);
    setModal("details");
  };

  const closeModal = () => {
    if (saving) return;
    setModal(null);
    setSelectedVinculo(null);
    setForm(INITIAL_FORM);
    setError("");
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!canManage) return;

    const cargaHoraria = Number(form.carga_horaria_semanal);

    if (!Number.isInteger(cargaHoraria) || cargaHoraria < 1 || cargaHoraria > 60) {
      setError("A carga horária deve ser um número inteiro entre 1 e 60.");
      return;
    }

    if (modal === "create") {
      if (!form.turma_id || !form.disciplina_id || !form.professor_id) {
        setError("Selecione a turma, a disciplina e o professor.");
        return;
      }

      if (combinationExists) {
        setError(
          "Já existe um registro para esta turma e disciplina. A API não permite criar outro vínculo para a mesma combinação, mesmo que o anterior esteja inativo."
        );
        return;
      }
    }

    setSaving(true);
    setError("");

    try {
      if (modal === "create") {
        await api.post("/turma-disciplinas/", {
          turma_id: Number(form.turma_id),
          disciplina_id: Number(form.disciplina_id),
          professor_id: Number(form.professor_id),
          carga_horaria_semanal: cargaHoraria,
        });

        setSuccess("Vínculo cadastrado com sucesso.");
      } else if (modal === "edit" && selectedVinculo) {
        await api.put(`/turma-disciplinas/${selectedVinculo.id}`, {
          carga_horaria_semanal: cargaHoraria,
          ativa: form.ativa,
        });

        setSuccess("Vínculo atualizado com sucesso.");
      }

      setModal(null);
      setSelectedVinculo(null);
      setForm(INITIAL_FORM);
      await loadData();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (vinculo: Vinculo) => {
    if (!canManage) return;

    const confirmed = window.confirm(
      `Deseja inativar o vínculo entre ${getTurmaNome(vinculo.turma_id)} e ${getDisciplinaNome(vinculo.disciplina_id)}?`
    );

    if (!confirmed) return;

    setError("");
    setSuccess("");

    try {
      await api.delete(`/turma-disciplinas/${vinculo.id}`);
      setSuccess("Vínculo inativado com sucesso.");
      await loadData();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleReactivate = async (vinculo: Vinculo) => {
    if (!canManage) return;

    const confirmed = window.confirm(
      "Deseja reativar este vínculo?"
    );

    if (!confirmed) return;

    setError("");
    setSuccess("");

    try {
      await api.put(`/turma-disciplinas/${vinculo.id}`, {
        ativa: true,
      });

      setSuccess("Vínculo reativado com sucesso.");
      await loadData();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  useEffect(() => {
    setCurrentPage(1);
  }, [search, statusFilter]);

  if (!canList) {
    return (
      <div className="assignments-page">
        <div className="assignments-message assignments-message-error">
          <AlertCircle size={20} />
          Você não tem permissão para visualizar os vínculos entre turmas,
          disciplinas e professores.
        </div>
      </div>
    );
  }

  return (
    <main className="assignments-page">
      <header className="assignments-header">
        <div>
          <span className="assignments-eyebrow">GESTÃO ACADÊMICA</span>
          <h1>Vínculos</h1>
          <p>
            Relacione turmas, disciplinas e professores da instituição.
          </p>
        </div>

        {canManage && (
          <button
            type="button"
            className="assignments-primary-button"
            onClick={openCreateModal}
          >
            <Plus size={18} />
            Novo vínculo
          </button>
        )}
      </header>

      {error && !modal && (
        <div className="assignments-alert assignments-alert-error">
          <AlertCircle size={18} />
          <span>{error}</span>
          <button type="button" onClick={() => setError("")} aria-label="Fechar">
            <X size={17} />
          </button>
        </div>
      )}

      {success && (
        <div className="assignments-alert assignments-alert-success">
          <span>{success}</span>
          <button type="button" onClick={() => setSuccess("")} aria-label="Fechar">
            <X size={17} />
          </button>
        </div>
      )}

      {auxiliaryError && (
        <div className="assignments-alert assignments-alert-warning">
          <AlertCircle size={18} />
          <span>{auxiliaryError}</span>
        </div>
      )}

      <section className="assignments-stats">
        <article className="assignments-stat-card">
          <div className="assignments-stat-icon assignments-stat-icon-orange">
            <Link2 size={21} />
          </div>
          <div>
            <span>Total de vínculos</span>
            <strong>{vinculos.length}</strong>
          </div>
        </article>

        <article className="assignments-stat-card">
          <div className="assignments-stat-icon assignments-stat-icon-green">
            <BookOpen size={21} />
          </div>
          <div>
            <span>Vínculos ativos</span>
            <strong>{totalAtivos}</strong>
          </div>
        </article>

        <article className="assignments-stat-card">
          <div className="assignments-stat-icon assignments-stat-icon-gray">
            <Users size={21} />
          </div>
          <div>
            <span>Vínculos inativos</span>
            <strong>{totalInativos}</strong>
          </div>
        </article>
      </section>

      <section className="assignments-content">
        <div className="assignments-toolbar">
          <div className="assignments-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Buscar por turma, disciplina ou professor..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            {search && (
              <button
                type="button"
                onClick={() => setSearch("")}
                aria-label="Limpar pesquisa"
              >
                <X size={16} />
              </button>
            )}
          </div>

          <div className="assignments-toolbar-actions">
            <div className="assignments-filter-group">
              <button
                type="button"
                className={statusFilter === "todos" ? "active" : ""}
                onClick={() => setStatusFilter("todos")}
              >
                Todos
              </button>
              <button
                type="button"
                className={statusFilter === "ativos" ? "active" : ""}
                onClick={() => setStatusFilter("ativos")}
              >
                Ativos
              </button>
              <button
                type="button"
                className={statusFilter === "inativos" ? "active" : ""}
                onClick={() => setStatusFilter("inativos")}
              >
                Inativos
              </button>
            </div>

            <button
              type="button"
              className="assignments-refresh-button"
              onClick={() => void loadData()}
              disabled={loading}
              title="Atualizar"
            >
              <RefreshCw size={17} className={loading ? "assignments-spinning" : ""} />
            </button>
          </div>
        </div>

        <div className="assignments-table-wrapper">
          <table className="assignments-table">
            <thead>
              <tr>
                <th>Turma</th>
                <th>Disciplina</th>
                <th>Professor</th>
                <th>Carga horária</th>
                <th>Status</th>
                <th className="assignments-actions-heading">Ações</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="assignments-empty">
                    Carregando vínculos...
                  </td>
                </tr>
              ) : paginatedVinculos.length === 0 ? (
                <tr>
                  <td colSpan={6} className="assignments-empty">
                    <Link2 size={28} />
                    <strong>Nenhum vínculo encontrado</strong>
                    <span>
                      {search || statusFilter !== "todos"
                        ? "Tente alterar os filtros da pesquisa."
                        : "Cadastre o primeiro vínculo entre turma, disciplina e professor."}
                    </span>
                  </td>
                </tr>
              ) : (
                paginatedVinculos.map((vinculo) => (
                  <tr key={vinculo.id}>
                    <td>
                      <div className="assignments-main-cell">
                        <BookOpen size={17} />
                        <span>{getTurmaNome(vinculo.turma_id)}</span>
                      </div>
                    </td>
                    <td>{getDisciplinaNome(vinculo.disciplina_id)}</td>
                    <td>{getProfessorNome(vinculo.professor_id)}</td>
                    <td>
                      <span className="assignments-hours">
                        <Clock3 size={15} />
                        {vinculo.carga_horaria_semanal}h/semana
                      </span>
                    </td>
                    <td>
                      <span
                        className={`assignments-status ${
                          vinculo.ativa ? "is-active" : "is-inactive"
                        }`}
                      >
                        {vinculo.ativa ? "Ativo" : "Inativo"}
                      </span>
                    </td>
                    <td>
                      <div className="assignments-row-actions">
                        <button
                          type="button"
                          title="Visualizar"
                          onClick={() => openDetailsModal(vinculo)}
                        >
                          <Eye size={17} />
                        </button>

                        {canManage && (
                          <>
                            <button
                              type="button"
                              title="Editar"
                              onClick={() => openEditModal(vinculo)}
                            >
                              <Pencil size={17} />
                            </button>

                            {vinculo.ativa ? (
                              <button
                                type="button"
                                title="Inativar"
                                className="danger"
                                onClick={() => void handleDeactivate(vinculo)}
                              >
                                <Trash2 size={17} />
                              </button>
                            ) : (
                              <button
                                type="button"
                                title="Reativar"
                                className="reactivate"
                                onClick={() => void handleReactivate(vinculo)}
                              >
                                <RotateCcw size={17} />
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <footer className="assignments-pagination">
          <span>
            Exibindo {filteredVinculos.length === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1}
            {" a "}
            {Math.min(currentPage * PAGE_SIZE, filteredVinculos.length)}
            {" de "}
            {filteredVinculos.length} vínculo(s)
          </span>

          <div>
            <button
              type="button"
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
              aria-label="Página anterior"
            >
              <ChevronLeft size={18} />
            </button>
            <span>
              {currentPage} / {totalPages}
            </span>
            <button
              type="button"
              disabled={currentPage >= totalPages}
              onClick={() =>
                setCurrentPage((page) => Math.min(totalPages, page + 1))
              }
              aria-label="Próxima página"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </footer>
      </section>

      {modal && (
        <div
          className="assignments-modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeModal();
          }}
        >
          <section className="assignments-modal">
            <header className="assignments-modal-header">
              <div>
                <span className="assignments-eyebrow">GESTÃO ACADÊMICA</span>
                <h2>
                  {modal === "create"
                    ? "Novo vínculo"
                    : modal === "edit"
                      ? "Editar vínculo"
                      : "Detalhes do vínculo"}
                </h2>
              </div>
              <button
                type="button"
                onClick={closeModal}
                disabled={saving}
                aria-label="Fechar"
              >
                <X size={20} />
              </button>
            </header>

            {error && (
              <div className="assignments-alert assignments-alert-error">
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            {modal === "details" && selectedVinculo ? (
              <div className="assignments-details">
                <div>
                  <span>Turma</span>
                  <strong>{getTurmaNome(selectedVinculo.turma_id)}</strong>
                </div>
                <div>
                  <span>Disciplina</span>
                  <strong>
                    {getDisciplinaNome(selectedVinculo.disciplina_id)}
                  </strong>
                </div>
                <div>
                  <span>Professor</span>
                  <strong>
                    {getProfessorNome(selectedVinculo.professor_id)}
                  </strong>
                </div>
                <div>
                  <span>Carga horária semanal</span>
                  <strong>{selectedVinculo.carga_horaria_semanal} horas</strong>
                </div>
                <div>
                  <span>Status</span>
                  <strong>
                    {selectedVinculo.ativa ? "Ativo" : "Inativo"}
                  </strong>
                </div>
                <div>
                  <span>Data de cadastro</span>
                  <strong>{formatDate(selectedVinculo.data_cadastro)}</strong>
                </div>
                <footer>
                  <button
                    type="button"
                    className="assignments-secondary-button"
                    onClick={closeModal}
                  >
                    Fechar
                  </button>
                </footer>
              </div>
            ) : (
              <form className="assignments-form" onSubmit={handleSubmit}>
                {modal === "create" && (
                  <>
                    <label>
                      Turma <span>*</span>
                      <select
                        value={form.turma_id}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            turma_id: event.target.value,
                          }))
                        }
                        required
                      >
                        <option value="">Selecione uma turma</option>
                        {turmasAtivas.map((turma) => (
                          <option key={turma.id} value={turma.id}>
                            {turma.nome}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label>
                      Disciplina <span>*</span>
                      <select
                        value={form.disciplina_id}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            disciplina_id: event.target.value,
                          }))
                        }
                        required
                      >
                        <option value="">Selecione uma disciplina</option>
                        {disciplinasAtivas.map((disciplina) => (
                          <option key={disciplina.id} value={disciplina.id}>
                            {disciplina.nome}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label>
                      Professor <span>*</span>
                      <select
                        value={form.professor_id}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            professor_id: event.target.value,
                          }))
                        }
                        required
                      >
                        <option value="">Selecione um professor</option>
                        {professoresAtivos.map((professor) => (
                          <option key={professor.id} value={professor.id}>
                            {professor.nome_completo}
                          </option>
                        ))}
                      </select>
                    </label>

                    {combinationExists && (
                      <div className="assignments-inline-warning">
                        <AlertCircle size={18} />
                        <span>
                          Já existe um vínculo cadastrado para esta turma e
                          disciplina. Mesmo inativo, o registro impede um novo
                          cadastro dessa combinação.
                        </span>
                      </div>
                    )}
                  </>
                )}

                {modal === "edit" && selectedVinculo && (
                  <div className="assignments-edit-reference">
                    <div>
                      <span>Turma</span>
                      <strong>{getTurmaNome(selectedVinculo.turma_id)}</strong>
                    </div>
                    <div>
                      <span>Disciplina</span>
                      <strong>
                        {getDisciplinaNome(selectedVinculo.disciplina_id)}
                      </strong>
                    </div>
                    <div>
                      <span>Professor</span>
                      <strong>
                        {getProfessorNome(selectedVinculo.professor_id)}
                      </strong>
                    </div>
                    <p>
                      Para preservar o histórico, a turma, a disciplina e o
                      professor não podem ser alterados neste cadastro.
                    </p>
                  </div>
                )}

                <label>
                  Carga horária semanal <span>*</span>
                  <div className="assignments-input-suffix">
                    <input
                      type="number"
                      min="1"
                      max="60"
                      step="1"
                      value={form.carga_horaria_semanal}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          carga_horaria_semanal: event.target.value,
                        }))
                      }
                      required
                    />
                    <span>horas</span>
                  </div>
                </label>

                {modal === "edit" && (
                  <label>
                    Situação
                    <select
                      value={form.ativa ? "true" : "false"}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          ativa: event.target.value === "true",
                        }))
                      }
                    >
                      <option value="true">Ativo</option>
                      <option value="false">Inativo</option>
                    </select>
                  </label>
                )}

                {modal === "create" && (
                  <div className="assignments-form-note">
                    <AlertCircle size={17} />
                    <span>
                      Cada turma pode ter apenas um vínculo por disciplina.
                      Confira os dados antes de salvar.
                    </span>
                  </div>
                )}

                <footer className="assignments-modal-actions">
                  <button
                    type="button"
                    className="assignments-secondary-button"
                    onClick={closeModal}
                    disabled={saving}
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="assignments-primary-button"
                    disabled={
                      saving ||
                      !canManage ||
                      (modal === "create" && combinationExists)
                    }
                  >
                    {saving
                      ? "Salvando..."
                      : modal === "create"
                        ? "Cadastrar vínculo"
                        : "Salvar alterações"}
                  </button>
                </footer>
              </form>
            )}
          </section>
        </div>
      )}
    </main>
  );
}
