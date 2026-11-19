
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";
import axios from "axios";
import {
  Search,
  Plus,
  Pencil,
  Eye,
  BookOpen,
  Users,
  X,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  UserX,
  GraduationCap,
  CalendarDays,
  Clock3,
  RotateCcw,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { api } from "../services/api";

interface Turma {
  id: number;
  nome: string;
  etapa: string;
  serie: string;
  turno: string;
  ano_letivo: number;
  capacidade: number;
  ativa: boolean;
}

interface Aluno {
  id: number;
  turma_id: number | null;
  status: string;
}

interface TurmaForm {
  nome: string;
  etapa: string;
  serie: string;
  turno: string;
  ano_letivo: string;
  capacidade: string;
}

type ModalMode = "create" | "edit" | "details";

const PAGE_SIZE = 10;

const emptyForm: TurmaForm = {
  nome: "",
  etapa: "",
  serie: "",
  turno: "",
  ano_letivo: String(new Date().getFullYear()),
  capacidade: "30",
};

function normalizarTexto(valor: string): string {
  return valor
    .toLocaleLowerCase("pt-BR")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[°º]/g, "o")
    .replace(/\s+/g, " ")
    .trim();
}

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") return detail;

    if (Array.isArray(detail)) {
      return detail
        .map((item) => item.msg ?? "Erro de validação")
        .join(" | ");
    }

    if (error.response?.status === 403) {
      return "Você não tem permissão para realizar esta operação.";
    }

    if (error.response?.status === 404) {
      return "O registro solicitado não foi encontrado.";
    }

    if (!error.response) {
      return "Não foi possível conectar ao servidor.";
    }
  }

  return "Ocorreu um erro inesperado. Tente novamente.";
}

export default function TurmasPage() {
  const { user } = useAuth();

  const permissions = user?.permissoes ?? [];

  const canList = permissions.includes("turmas.listar");
  const canCreate = permissions.includes("turmas.criar");
  const canEdit = permissions.includes("turmas.editar");
  const canDeactivate = permissions.includes("turmas.desativar");
  const canListAlunos = permissions.includes("alunos.listar");

  const [turmas, setTurmas] = useState<Turma[]>([]);
  const [alunosPorTurma, setAlunosPorTurma] = useState<
    Record<number, number>
  >({});

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [filterYear, setFilterYear] = useState("todos");
  const [filterEtapa, setFilterEtapa] = useState("todas");
  const [filterTurno, setFilterTurno] = useState("todos");
  const [filterStatus, setFilterStatus] = useState("todas");
  const [currentPage, setCurrentPage] = useState(1);

  const [modalMode, setModalMode] = useState<ModalMode | null>(null);
  const [selectedTurma, setSelectedTurma] = useState<Turma | null>(null);
  const [form, setForm] = useState<TurmaForm>(emptyForm);
  const [formError, setFormError] = useState("");

  const loadAlunos = useCallback(async (items: Turma[]) => {
    const counts: Record<number, number> = {};

    items.forEach((turma) => {
      counts[turma.id] = 0;
    });

    let offset = 0;
    let page: Aluno[] = [];

    do {
      const response = await api.get<Aluno[]>("/alunos/", {
        params: {
          offset,
          limit: 100,
        },
      });

      page = response.data;

      page.forEach((aluno) => {
        if (
          aluno.turma_id !== null &&
          aluno.status === "ativo" &&
          counts[aluno.turma_id] !== undefined
        ) {
          counts[aluno.turma_id] += 1;
        }
      });

      offset += page.length;
    } while (page.length === 100);

    setAlunosPorTurma(counts);
  }, []);

  const loadTurmas = useCallback(async () => {
    if (!canList) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await api.get<Turma[]>("/turmas/", {
        params: {
          offset: 0,
          limit: 100,
        },
      });

      setTurmas(response.data);

      if (canListAlunos) {
        await loadAlunos(response.data);
      } else {
        setAlunosPorTurma({});
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [canList, canListAlunos, loadAlunos]);

  useEffect(() => {
    void loadTurmas();
  }, [loadTurmas]);

  const years = useMemo(
    () =>
      [...new Set(turmas.map((turma) => turma.ano_letivo))].sort(
        (a, b) => b - a,
      ),
    [turmas],
  );

  const etapas = useMemo(
    () => [...new Set(turmas.map((turma) => turma.etapa))].sort(),
    [turmas],
  );

  const turnos = useMemo(
    () => [...new Set(turmas.map((turma) => turma.turno))].sort(),
    [turmas],
  );

  const filteredTurmas = useMemo(() => {
    const normalizedSearch = normalizarTexto(search);

    return turmas.filter((turma) => {
      const matchesSearch =
        !normalizedSearch ||
        normalizarTexto(turma.nome).includes(normalizedSearch) ||
        normalizarTexto(turma.etapa).includes(normalizedSearch) ||
        normalizarTexto(turma.serie).includes(normalizedSearch);

      const matchesYear =
        filterYear === "todos" ||
        turma.ano_letivo === Number(filterYear);

      const matchesEtapa =
        filterEtapa === "todas" || turma.etapa === filterEtapa;

      const matchesTurno =
        filterTurno === "todos" || turma.turno === filterTurno;

      const matchesStatus =
        filterStatus === "todas" ||
        (filterStatus === "ativas" && turma.ativa) ||
        (filterStatus === "inativas" && !turma.ativa);

      return (
        matchesSearch &&
        matchesYear &&
        matchesEtapa &&
        matchesTurno &&
        matchesStatus
      );
    });
  }, [
    turmas,
    search,
    filterYear,
    filterEtapa,
    filterTurno,
    filterStatus,
  ]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredTurmas.length / PAGE_SIZE),
  );

  const paginatedTurmas = filteredTurmas.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE,
  );

  const activeCount = turmas.filter((turma) => turma.ativa).length;
  const inactiveCount = turmas.length - activeCount;

  const totalAlunosVinculados = canListAlunos
    ? turmas.reduce(
        (total, turma) => total + (alunosPorTurma[turma.id] ?? 0),
        0,
      )
    : null;

  function openCreate() {
    setSelectedTurma(null);
    setForm(emptyForm);
    setFormError("");
    setModalMode("create");
  }

  function openEdit(turma: Turma) {
    setSelectedTurma(turma);
    setForm({
      nome: turma.nome,
      etapa: turma.etapa,
      serie: turma.serie,
      turno: turma.turno,
      ano_letivo: String(turma.ano_letivo),
      capacidade: String(turma.capacidade),
    });
    setFormError("");
    setModalMode("edit");
  }

  function openDetails(turma: Turma) {
    setSelectedTurma(turma);
    setModalMode("details");
  }

  function closeModal() {
    if (saving) return;

    setModalMode(null);
    setSelectedTurma(null);
    setFormError("");
  }

  function updateField(field: keyof TurmaForm, value: string) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");

    const anoLetivo = Number(form.ano_letivo);
    const capacidade = Number(form.capacidade);

    if (
      form.nome.trim().length < 2 ||
      form.etapa.trim().length < 2 ||
      !form.serie.trim() ||
      form.turno.trim().length < 2
    ) {
      setFormError("Preencha todos os campos obrigatórios corretamente.");
      return;
    }

    if (
      !Number.isInteger(anoLetivo) ||
      anoLetivo < 2000 ||
      anoLetivo > 2100
    ) {
      setFormError("Informe um ano letivo válido entre 2000 e 2100.");
      return;
    }

    if (!Number.isInteger(capacidade) || capacidade <= 0) {
      setFormError("A capacidade deve ser um número inteiro positivo.");
      return;
    }

    const payload = {
      nome: form.nome.trim(),
      etapa: form.etapa.trim(),
      serie: form.serie.trim(),
      turno: form.turno.trim(),
      ano_letivo: anoLetivo,
      capacidade,
    };

    setSaving(true);

    try {
      if (modalMode === "create") {
        await api.post("/turmas/", payload);
      } else if (modalMode === "edit" && selectedTurma) {
        await api.put(`/turmas/${selectedTurma.id}`, payload);
      }

      closeModalAfterSave();
      await loadTurmas();
    } catch (err) {
      setFormError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  function closeModalAfterSave() {
    setModalMode(null);
    setSelectedTurma(null);
    setFormError("");
  }

  async function handleDeactivate(turma: Turma) {
    const confirmed = window.confirm(
      `Deseja realmente inativar a turma "${turma.nome}"?\n\nO registro será mantido no histórico do sistema.`,
    );

    if (!confirmed) return;

    setError("");

    try {
      await api.delete(`/turmas/${turma.id}`);
      await loadTurmas();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  async function handleReactivate(turma: Turma) {
    if (!canEdit || turma.ativa) return;

    const confirmed = window.confirm(
      `Deseja realmente reativar a turma "${turma.nome}"?`,
    );

    if (!confirmed) return;

    setError("");

    try {
      await api.put(`/turmas/${turma.id}`, {
        ativa: true,
      });

      if (modalMode === "details") {
        setModalMode(null);
        setSelectedTurma(null);
      }

      await loadTurmas();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  if (!canList) {
    return (
      <div className="classes-access-denied">
        <BookOpen size={36} />
        <h2>Acesso não autorizado</h2>
        <p>Você não possui permissão para visualizar as turmas.</p>
      </div>
    );
  }

  return (
    <div className="classes-page">
      <div className="classes-heading">
        <div>
          <span className="classes-eyebrow">GESTÃO ACADÊMICA</span>
          <h2>Turmas</h2>
          <p>Gerencie as turmas, seus turnos e a capacidade de alunos.</p>
        </div>

        {canCreate && (
          <button className="classes-add" onClick={openCreate}>
            <Plus size={18} />
            Nova turma
          </button>
        )}
      </div>

      {error && (
        <div className="classes-alert">
          <span>{error}</span>
          <button onClick={() => setError("")} aria-label="Fechar aviso">
            <X size={17} />
          </button>
        </div>
      )}

      <div className="classes-stats">
        <div className="classes-stat">
          <div className="classes-stat-icon orange">
            <BookOpen size={21} />
          </div>
          <div>
            <span>Total de turmas</span>
            <strong>{turmas.length}</strong>
          </div>
        </div>

        <div className="classes-stat">
          <div className="classes-stat-icon green">
            <GraduationCap size={21} />
          </div>
          <div>
            <span>Turmas ativas</span>
            <strong>{activeCount}</strong>
          </div>
        </div>

        <div className="classes-stat">
          <div className="classes-stat-icon gray">
            <UserX size={21} />
          </div>
          <div>
            <span>Turmas inativas</span>
            <strong>{inactiveCount}</strong>
          </div>
        </div>

        {canListAlunos && (
          <div className="classes-stat">
            <div className="classes-stat-icon blue">
              <Users size={21} />
            </div>
            <div>
              <span>Alunos vinculados</span>
              <strong>{totalAlunosVinculados ?? 0}</strong>
            </div>
          </div>
        )}
      </div>

      <section className="classes-table-card">
        <div className="classes-toolbar">
          <div>
            <h3>Lista de turmas</h3>
            <p>Consulte e gerencie as turmas cadastradas.</p>
          </div>

          <div className="classes-search">
            <Search size={18} />
            <input
              type="search"
              placeholder="Pesquisar turma..."
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setCurrentPage(1);
              }}
            />
          </div>

          <button
            className="classes-refresh"
            onClick={() => void loadTurmas()}
            disabled={loading}
            title="Atualizar lista"
          >
            <RefreshCw size={17} />
          </button>
        </div>

        <div className="classes-filters">
          <select
            value={filterYear}
            onChange={(event) => {
              setFilterYear(event.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="todos">Todos os anos</option>
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>

          <select
            value={filterEtapa}
            onChange={(event) => {
              setFilterEtapa(event.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="todas">Todas as etapas</option>
            {etapas.map((etapa) => (
              <option key={etapa} value={etapa}>
                {etapa}
              </option>
            ))}
          </select>

          <select
            value={filterTurno}
            onChange={(event) => {
              setFilterTurno(event.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="todos">Todos os turnos</option>
            {turnos.map((turno) => (
              <option key={turno} value={turno}>
                {turno}
              </option>
            ))}
          </select>

          <select
            value={filterStatus}
            onChange={(event) => {
              setFilterStatus(event.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="todas">Todas as situações</option>
            <option value="ativas">Ativas</option>
            <option value="inativas">Inativas</option>
          </select>
        </div>

        {loading ? (
          <div className="classes-loading">
            <RefreshCw size={22} />
            <span>Carregando turmas...</span>
          </div>
        ) : (
          <>
            <div className="classes-table-wrapper">
              <table className="classes-table">
                <thead>
                  <tr>
                    <th>Turma</th>
                    <th>Etapa / Série</th>
                    <th>Turno</th>
                    <th>Ano letivo</th>
                    {canListAlunos && <th>Ocupação</th>}
                    <th>Situação</th>
                    <th>Ações</th>
                  </tr>
                </thead>

                <tbody>
                  {paginatedTurmas.map((turma) => {
                    const alunosVinculados =
                      alunosPorTurma[turma.id];

                    const countAvailable =
                      canListAlunos &&
                      alunosVinculados !== undefined;

                    const occupancy = countAvailable
                      ? Math.min(
                          100,
                          (alunosVinculados / turma.capacidade) * 100,
                        )
                      : 0;

                    return (
                      <tr key={turma.id}>
                        <td>
                          <div className="classes-name">
                            <div className="classes-name-icon">
                              <BookOpen size={17} />
                            </div>
                            <div>
                              <strong>{turma.nome}</strong>
                              <span>
                                Capacidade: {turma.capacidade} alunos
                              </span>
                            </div>
                          </div>
                        </td>

                        <td>
                          <strong className="classes-cell-main">
                            {turma.etapa}
                          </strong>
                          <span className="classes-cell-sub">
                            {turma.serie}
                          </span>
                        </td>

                        <td>
                          <span className="classes-turno">
                            <Clock3 size={14} />
                            {turma.turno}
                          </span>
                        </td>

                        <td>
                          <span className="classes-year">
                            <CalendarDays size={14} />
                            {turma.ano_letivo}
                          </span>
                        </td>

                        {canListAlunos && (
                          <td>
                            {countAvailable ? (
                              <div className="classes-occupancy">
                                <div>
                                  <strong>{alunosVinculados}</strong>
                                  <span> / {turma.capacidade}</span>
                                </div>
                                <div className="classes-progress">
                                  <span
                                    style={{
                                      width: `${occupancy}%`,
                                    }}
                                  />
                                </div>
                              </div>
                            ) : (
                              <span className="classes-unavailable">
                                Indisponível
                              </span>
                            )}
                          </td>
                        )}

                        <td>
                          <span
                            className={`classes-status ${
                              turma.ativa ? "active" : "inactive"
                            }`}
                          >
                            {turma.ativa ? "Ativa" : "Inativa"}
                          </span>
                        </td>

                        <td>
                          <div className="classes-actions">
                            <button
                              onClick={() => openDetails(turma)}
                              title="Visualizar turma"
                            >
                              <Eye size={17} />
                            </button>

                            {canEdit && turma.ativa && (
                              <button
                                onClick={() => openEdit(turma)}
                                title="Editar turma"
                              >
                                <Pencil size={17} />
                              </button>
                            )}

                            {canDeactivate && turma.ativa && (
                              <button
                                className="danger"
                                onClick={() => void handleDeactivate(turma)}
                                title="Inativar turma"
                              >
                                <UserX size={17} />
                              </button>
                            )}

                            {canEdit && !turma.ativa && (
                              <button
                                onClick={() => void handleReactivate(turma)}
                                title="Reativar turma"
                              >
                                <RotateCcw size={17} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}

                  {paginatedTurmas.length === 0 && (
                    <tr>
                      <td
                        colSpan={canListAlunos ? 7 : 6}
                        className="classes-empty"
                      >
                        <BookOpen size={32} />
                        <strong>Nenhuma turma encontrada</strong>
                        <span>
                          Tente alterar os filtros ou cadastrar uma nova turma.
                        </span>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="classes-pagination">
              <span>
                Mostrando{" "}
                {filteredTurmas.length === 0
                  ? 0
                  : (currentPage - 1) * PAGE_SIZE + 1}
                {" a "}
                {Math.min(currentPage * PAGE_SIZE, filteredTurmas.length)}
                {" de "}
                {filteredTurmas.length} turmas
              </span>

              <div>
                <button
                  disabled={currentPage <= 1}
                  onClick={() =>
                    setCurrentPage((page) => Math.max(1, page - 1))
                  }
                  aria-label="Página anterior"
                >
                  <ChevronLeft size={18} />
                </button>

                <span>
                  {currentPage} / {totalPages}
                </span>

                <button
                  disabled={currentPage >= totalPages}
                  onClick={() =>
                    setCurrentPage((page) =>
                      Math.min(totalPages, page + 1),
                    )
                  }
                  aria-label="Próxima página"
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          </>
        )}
      </section>

      {modalMode && (
        <div
          className="classes-modal-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeModal();
          }}
        >
          <section className="classes-modal">
            <header className="classes-modal-header">
              <div>
                <span>GESTÃO ACADÊMICA</span>
                <h3>
                  {modalMode === "create"
                    ? "Cadastrar turma"
                    : modalMode === "edit"
                      ? "Editar turma"
                      : "Detalhes da turma"}
                </h3>
              </div>

              <button
                onClick={closeModal}
                disabled={saving}
                aria-label="Fechar"
              >
                <X size={20} />
              </button>
            </header>

            {modalMode === "details" && selectedTurma ? (
              <div className="classes-details">
                <div className="classes-details-title">
                  <div className="classes-name-icon large">
                    <BookOpen size={24} />
                  </div>
                  <div>
                    <h4>{selectedTurma.nome}</h4>
                    <span
                      className={`classes-status ${
                        selectedTurma.ativa ? "active" : "inactive"
                      }`}
                    >
                      {selectedTurma.ativa ? "Ativa" : "Inativa"}
                    </span>
                  </div>
                </div>

                <div className="classes-details-grid">
                  <div>
                    <span>Etapa de ensino</span>
                    <strong>{selectedTurma.etapa}</strong>
                  </div>
                  <div>
                    <span>Série</span>
                    <strong>{selectedTurma.serie}</strong>
                  </div>
                  <div>
                    <span>Turno</span>
                    <strong>{selectedTurma.turno}</strong>
                  </div>
                  <div>
                    <span>Ano letivo</span>
                    <strong>{selectedTurma.ano_letivo}</strong>
                  </div>
                  <div>
                    <span>Capacidade máxima</span>
                    <strong>{selectedTurma.capacidade} alunos</strong>
                  </div>
                  {canListAlunos && (
                    <div>
                      <span>Alunos vinculados</span>
                      <strong>
                        {alunosPorTurma[selectedTurma.id] ??
                          "Indisponível"}
                      </strong>
                    </div>
                  )}
                </div>

                <footer className="classes-modal-footer">
                  <button
                    className="classes-secondary-button"
                    onClick={closeModal}
                  >
                    Fechar
                  </button>

                  {canEdit && selectedTurma.ativa && (
                    <button
                      className="classes-primary-button"
                      onClick={() => openEdit(selectedTurma)}
                    >
                      <Pencil size={16} />
                      Editar turma
                    </button>
                  )}

                  {canEdit && !selectedTurma.ativa && (
                    <button
                      className="classes-primary-button"
                      onClick={() => void handleReactivate(selectedTurma)}
                    >
                      <RotateCcw size={16} />
                      Reativar turma
                    </button>
                  )}
                </footer>
              </div>
            ) : (
              <form onSubmit={handleSubmit}>
                <div className="classes-form-grid">
                  <label className="classes-field field-full">
                    Nome da turma *
                    <input
                      autoFocus
                      value={form.nome}
                      onChange={(event) =>
                        updateField("nome", event.target.value)
                      }
                      placeholder="Ex.: 1º Ano A"
                      minLength={2}
                      maxLength={100}
                      required
                    />
                  </label>

                  <label className="classes-field">
                    Etapa de ensino *
                    <input
                      value={form.etapa}
                      onChange={(event) =>
                        updateField("etapa", event.target.value)
                      }
                      placeholder="Ex.: Ensino Fundamental"
                      minLength={2}
                      maxLength={50}
                      required
                    />
                  </label>

                  <label className="classes-field">
                    Série *
                    <input
                      value={form.serie}
                      onChange={(event) =>
                        updateField("serie", event.target.value)
                      }
                      placeholder="Ex.: 1º Ano"
                      maxLength={30}
                      required
                    />
                  </label>

                  <label className="classes-field">
                    Turno *
                    <input
                      value={form.turno}
                      onChange={(event) =>
                        updateField("turno", event.target.value)
                      }
                      placeholder="Ex.: Manhã"
                      minLength={2}
                      maxLength={20}
                      required
                    />
                  </label>

                  <label className="classes-field">
                    Ano letivo *
                    <input
                      type="number"
                      value={form.ano_letivo}
                      onChange={(event) =>
                        updateField("ano_letivo", event.target.value)
                      }
                      min={2000}
                      max={2100}
                      required
                    />
                  </label>

                  <label className="classes-field">
                    Capacidade de alunos *
                    <input
                      type="number"
                      value={form.capacidade}
                      onChange={(event) =>
                        updateField("capacidade", event.target.value)
                      }
                      min={1}
                      step={1}
                      required
                    />
                  </label>
                </div>

                {modalMode === "edit" && (
                  <p className="classes-form-note">
                    A alteração do ano letivo será recusada pelo sistema caso
                    existam matrículas vinculadas à turma.
                  </p>
                )}

                {formError && (
                  <div className="classes-form-error">{formError}</div>
                )}

                <footer className="classes-modal-footer">
                  <button
                    type="button"
                    className="classes-secondary-button"
                    onClick={closeModal}
                    disabled={saving}
                  >
                    Cancelar
                  </button>

                  <button
                    type="submit"
                    className="classes-primary-button"
                    disabled={saving}
                  >
                    {saving
                      ? "Salvando..."
                      : modalMode === "create"
                        ? "Cadastrar turma"
                        : "Salvar alterações"}
                  </button>
                </footer>
              </form>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
