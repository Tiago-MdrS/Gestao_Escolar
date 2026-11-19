
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
  Clock3,
  CalendarDays,
  UserX,
  X,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  RotateCcw,
  CalendarClock,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { api } from "../services/api";

interface Horario {
  id: number;
  turma_disciplina_id: number;
  dia_semana: number;
  hora_inicio: string;
  hora_fim: string;
  sala: string | null;
  ativo: boolean;
  data_cadastro: string;
}

interface HorarioForm {
  turma_id: string;
  disciplina_id: string;
  professor_id: string;
  dia_semana: string;
  hora_inicio: string;
  hora_fim: string;
  sala: string;
}

interface Turma {
  id: number;
  nome: string;
  etapa: string;
  serie: string;
  turno: string;
  ano_letivo: number;
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

interface TurmaDisciplina {
  id: number;
  turma_id: number;
  disciplina_id: number;
  professor_id: number;
  carga_horaria_semanal: number;
  ativa: boolean;
}

type ModalMode = "create" | "edit" | "details";

const PAGE_SIZE = 10;

const diasSemana = [
  "Segunda-feira",
  "Terça-feira",
  "Quarta-feira",
  "Quinta-feira",
  "Sexta-feira",
  "Sábado",
  "Domingo",
];

const emptyForm: HorarioForm = {
  turma_id: "",
  disciplina_id: "",
  professor_id: "",
  dia_semana: "0",
  hora_inicio: "",
  hora_fim: "",
  sala: "",
};

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
      return "O horário ou vínculo solicitado não foi encontrado.";
    }

    if (error.response?.status === 409) {
      return (
        typeof detail === "string"
          ? detail
          : "Conflito de horário: verifique a turma, o professor e a sala."
      );
    }

    if (!error.response) {
      return "Não foi possível conectar ao servidor.";
    }
  }

  return "Ocorreu um erro inesperado. Tente novamente.";
}

function formatarHora(hora: string): string {
  return hora.slice(0, 5);
}

export default function HorariosPage() {
  const { user } = useAuth();

  const permissions = user?.permissoes ?? [];

  const canList = permissions.includes("horarios.listar");
  const canConsultOwn = permissions.includes("horarios.consultar_proprios");
  const canManage = permissions.includes("horarios.gerenciar");

  const canView = canList || canConsultOwn;

  const canLoadTurmas = permissions.includes("turmas.listar");
  const canLoadDisciplinas = permissions.includes("disciplinas.listar");
  const canLoadProfessores = permissions.includes("professores.listar");
  const canLoadAssignments = permissions.includes(
    "turma_disciplinas.listar",
  );

  const [horarios, setHorarios] = useState<Horario[]>([]);
  const [turmas, setTurmas] = useState<Turma[]>([]);
  const [disciplinas, setDisciplinas] = useState<Disciplina[]>([]);
  const [professores, setProfessores] = useState<Professor[]>([]);
  const [atribuicoes, setAtribuicoes] = useState<TurmaDisciplina[]>([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [filterTurma, setFilterTurma] = useState("todas");
  const [filterProfessor, setFilterProfessor] = useState("todos");
  const [filterDisciplina, setFilterDisciplina] = useState("todas");
  const [filterDia, setFilterDia] = useState("todos");
  const [filterStatus, setFilterStatus] = useState("todas");
  const [currentPage, setCurrentPage] = useState(1);

  const [modalMode, setModalMode] = useState<ModalMode | null>(null);
  const [selectedHorario, setSelectedHorario] =
    useState<Horario | null>(null);
  const [form, setForm] = useState<HorarioForm>(emptyForm);
  const [formError, setFormError] = useState("");

  const loadAuxiliaryData = useCallback(async () => {
    const requests = await Promise.allSettled([
      canLoadTurmas
        ? api.get<Turma[]>("/turmas/", {
            params: { offset: 0, limit: 100 },
          })
        : Promise.resolve(null),

      canLoadDisciplinas
        ? api.get<Disciplina[]>("/disciplinas/", {
            params: { offset: 0, limit: 100 },
          })
        : Promise.resolve(null),

      canLoadProfessores
        ? api.get<Professor[]>("/professores/", {
            params: { offset: 0, limit: 100, ativo: true },
          })
        : Promise.resolve(null),

      canLoadAssignments
        ? api.get<TurmaDisciplina[]>("/turma-disciplinas/", {
            params: { offset: 0, limit: 100, ativa: true },
          })
        : Promise.resolve(null),
    ]);

    if (requests[0].status === "fulfilled" && requests[0].value) {
      setTurmas(requests[0].value.data);
    }

    if (requests[1].status === "fulfilled" && requests[1].value) {
      setDisciplinas(requests[1].value.data);
    }

    if (requests[2].status === "fulfilled" && requests[2].value) {
      setProfessores(requests[2].value.data);
    }

    if (requests[3].status === "fulfilled" && requests[3].value) {
      setAtribuicoes(requests[3].value.data);
    }
  }, [
    canLoadTurmas,
    canLoadDisciplinas,
    canLoadProfessores,
    canLoadAssignments,
  ]);

  const loadHorarios = useCallback(async () => {
    if (!canView) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const endpoint = canList ? "/horarios/" : "/horarios/meus";

      const response = await api.get<Horario[]>(endpoint, {
        params: canList
          ? { offset: 0, limit: 100 }
          : undefined,
      });

      setHorarios(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [canList, canView]);

  const loadData = useCallback(async () => {
    await Promise.all([loadHorarios(), loadAuxiliaryData()]);
  }, [loadHorarios, loadAuxiliaryData]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const obterAtribuicao = useCallback(
    (horario: Horario) =>
      atribuicoes.find(
        (atribuicao) => atribuicao.id === horario.turma_disciplina_id,
      ),
    [atribuicoes],
  );

  const obterNomeTurma = useCallback(
    (turmaId: number) => {
      const turma = turmas.find((item) => item.id === turmaId);

      if (!turma) return `Turma #${turmaId}`;

      return turma.nome || `${turma.serie} ${turma.etapa}`;
    },
    [turmas],
  );

  const obterNomeDisciplina = useCallback(
    (disciplinaId: number) =>
      disciplinas.find((item) => item.id === disciplinaId)?.nome ??
      `Disciplina #${disciplinaId}`,
    [disciplinas],
  );

  const obterNomeProfessor = useCallback(
    (professorId: number) =>
      professores.find((item) => item.id === professorId)?.nome_completo ??
      `Professor #${professorId}`,
    [professores],
  );

  const activeCount = horarios.filter((horario) => horario.ativo).length;
  const inactiveCount = horarios.length - activeCount;

  const filteredHorarios = useMemo(() => {
    const normalizedSearch = search
      .toLocaleLowerCase("pt-BR")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();

    return horarios
      .filter((horario) => {
        const atribuicao = atribuicoes.find(
          (item) => item.id === horario.turma_disciplina_id,
        );

        const turmaNome = atribuicao
          ? obterNomeTurma(atribuicao.turma_id)
          : `Turma ${horario.turma_disciplina_id}`;

        const disciplinaNome = atribuicao
          ? obterNomeDisciplina(atribuicao.disciplina_id)
          : "";

        const professorNome = atribuicao
          ? obterNomeProfessor(atribuicao.professor_id)
          : "";

        const searchable = [
          turmaNome,
          disciplinaNome,
          professorNome,
          horario.sala ?? "",
          diasSemana[horario.dia_semana],
        ]
          .join(" ")
          .toLocaleLowerCase("pt-BR")
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "");

        const matchesSearch =
          !normalizedSearch || searchable.includes(normalizedSearch);

        const matchesTurma =
          filterTurma === "todas" ||
          atribuicao?.turma_id === Number(filterTurma);

        const matchesProfessor =
          filterProfessor === "todos" ||
          atribuicao?.professor_id === Number(filterProfessor);

        const matchesDisciplina =
          filterDisciplina === "todas" ||
          atribuicao?.disciplina_id === Number(filterDisciplina);

        const matchesDia =
          filterDia === "todos" ||
          horario.dia_semana === Number(filterDia);

        const matchesStatus =
          filterStatus === "todas" ||
          (filterStatus === "ativos" && horario.ativo) ||
          (filterStatus === "inativos" && !horario.ativo);

        return (
          matchesSearch &&
          matchesTurma &&
          matchesProfessor &&
          matchesDisciplina &&
          matchesDia &&
          matchesStatus
        );
      })
      .sort((a, b) => {
        if (a.dia_semana !== b.dia_semana) {
          return a.dia_semana - b.dia_semana;
        }

        return a.hora_inicio.localeCompare(b.hora_inicio);
      });
  }, [
    horarios,
    atribuicoes,
    search,
    filterTurma,
    filterProfessor,
    filterDisciplina,
    filterDia,
    filterStatus,
    obterNomeTurma,
    obterNomeDisciplina,
    obterNomeProfessor,
  ]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredHorarios.length / PAGE_SIZE),
  );

  const paginatedHorarios = filteredHorarios.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE,
  );

  const atribuicoesAtivas = atribuicoes.filter((item) => item.ativa);

  const turmasDisponiveis = turmas.filter(
    (turma) =>
      turma.ativa &&
      atribuicoesAtivas.some(
        (atribuicao) => atribuicao.turma_id === turma.id,
      ),
  );

  const disciplinasDisponiveis = disciplinas.filter(
    (disciplina) =>
      disciplina.ativa &&
      atribuicoesAtivas.some(
        (atribuicao) =>
          atribuicao.turma_id === Number(form.turma_id) &&
          atribuicao.disciplina_id === disciplina.id,
      ),
  );

  const professoresDisponiveis = professores.filter(
    (professor) =>
      professor.ativo &&
      atribuicoesAtivas.some(
        (atribuicao) =>
          atribuicao.turma_id === Number(form.turma_id) &&
          atribuicao.disciplina_id === Number(form.disciplina_id) &&
          atribuicao.professor_id === professor.id,
      ),
  );

  function openCreate() {
    setSelectedHorario(null);
    setForm(emptyForm);
    setFormError("");
    setModalMode("create");
  }

  function openEdit(horario: Horario) {
    const atribuicao = obterAtribuicao(horario);

    setSelectedHorario(horario);

    setForm({
      turma_id: atribuicao ? String(atribuicao.turma_id) : "",
      disciplina_id: atribuicao ? String(atribuicao.disciplina_id) : "",
      professor_id: atribuicao ? String(atribuicao.professor_id) : "",
      dia_semana: String(horario.dia_semana),
      hora_inicio: formatarHora(horario.hora_inicio),
      hora_fim: formatarHora(horario.hora_fim),
      sala: horario.sala ?? "",
    });

    setFormError("");
    setModalMode("edit");
  }

  function openDetails(horario: Horario) {
    setSelectedHorario(horario);
    setModalMode("details");
  }

  function closeModal() {
    if (saving) return;

    setModalMode(null);
    setSelectedHorario(null);
    setFormError("");
  }

  function closeModalAfterSave() {
    setModalMode(null);
    setSelectedHorario(null);
    setFormError("");
  }

  function updateField(field: keyof HorarioForm, value: string) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function handleTurmaChange(value: string) {
    setForm((current) => ({
      ...current,
      turma_id: value,
      disciplina_id: "",
      professor_id: "",
    }));
  }

  function handleDisciplinaChange(value: string) {
    setForm((current) => ({
      ...current,
      disciplina_id: value,
      professor_id: "",
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");

    if (!form.turma_id || !form.disciplina_id || !form.professor_id) {
      setFormError("Selecione a turma, a disciplina e o professor.");
      return;
    }

    const atribuicaoSelecionada = atribuicoesAtivas.find(
      (item) =>
        item.turma_id === Number(form.turma_id) &&
        item.disciplina_id === Number(form.disciplina_id) &&
        item.professor_id === Number(form.professor_id),
    );

    if (!atribuicaoSelecionada) {
      setFormError(
        "Não foi encontrada uma atribuição ativa para essa combinação.",
      );
      return;
    }

    if (!form.hora_inicio || !form.hora_fim) {
      setFormError("Informe o horário de início e término.");
      return;
    }

    if (form.hora_inicio >= form.hora_fim) {
      setFormError("A hora de início deve ser anterior à hora de término.");
      return;
    }

    const payload = {
      turma_disciplina_id: atribuicaoSelecionada.id,
      dia_semana: Number(form.dia_semana),
      hora_inicio: form.hora_inicio,
      hora_fim: form.hora_fim,
      sala: form.sala.trim() || null,
    };

    setSaving(true);

    try {
      if (modalMode === "create") {
        await api.post("/horarios/", {
          ...payload,
          ativo: true,
        });
      } else if (modalMode === "edit" && selectedHorario) {
        await api.put(`/horarios/${selectedHorario.id}`, payload);
      }

      closeModalAfterSave();
      await loadData();
    } catch (err) {
      setFormError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleDeactivate(horario: Horario) {
    const confirmed = window.confirm(
      "Deseja realmente inativar este horário?\n\nO registro será mantido no histórico do sistema.",
    );

    if (!confirmed) return;

    setError("");

    try {
      await api.delete(`/horarios/${horario.id}`);

      if (modalMode === "details") {
        setModalMode(null);
        setSelectedHorario(null);
      }

      await loadData();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  async function handleReactivate(horario: Horario) {
    if (!canManage || horario.ativo) return;

    const confirmed = window.confirm(
      "Deseja realmente reativar este horário?",
    );

    if (!confirmed) return;

    setError("");

    try {
      await api.put(`/horarios/${horario.id}`, {
        ativo: true,
      });

      if (modalMode === "details") {
        setModalMode(null);
        setSelectedHorario(null);
      }

      await loadData();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  if (!canView) {
    return (
      <div className="schedules-access-denied">
        <CalendarClock size={36} />
        <h2>Acesso não autorizado</h2>
        <p>Você não possui permissão para visualizar os horários.</p>
      </div>
    );
  }

  return (
    <div className="schedules-page">
      <div className="schedules-heading">
        <div>
          <span className="schedules-eyebrow">GESTÃO ACADÊMICA</span>
          <h2>Horários de aulas</h2>
          <p>Organize e consulte os horários das turmas e disciplinas.</p>
        </div>

        {canManage && (
          <button className="schedules-add" onClick={openCreate}>
            <Plus size={18} />
            Novo horário
          </button>
        )}
      </div>

      {error && (
        <div className="schedules-alert">
          <span>{error}</span>
          <button onClick={() => setError("")} aria-label="Fechar aviso">
            <X size={17} />
          </button>
        </div>
      )}

      <div className="schedules-stats">
        <div className="schedules-stat">
          <div className="schedules-stat-icon orange">
            <CalendarDays size={21} />
          </div>
          <div>
            <span>Total de horários</span>
            <strong>{horarios.length}</strong>
          </div>
        </div>

        <div className="schedules-stat">
          <div className="schedules-stat-icon green">
            <Clock3 size={21} />
          </div>
          <div>
            <span>Horários ativos</span>
            <strong>{activeCount}</strong>
          </div>
        </div>

        <div className="schedules-stat">
          <div className="schedules-stat-icon gray">
            <UserX size={21} />
          </div>
          <div>
            <span>Horários inativos</span>
            <strong>{inactiveCount}</strong>
          </div>
        </div>
      </div>

      <section className="schedules-table-card">
        <div className="schedules-toolbar">
          <div>
            <h3>Grade de horários</h3>
            <p>Consulte e gerencie os horários cadastrados.</p>
          </div>

          <div className="schedules-search">
            <Search size={18} />
            <input
              type="search"
              placeholder="Pesquisar horário..."
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setCurrentPage(1);
              }}
            />
          </div>

          <button
            className="schedules-refresh"
            onClick={() => void loadData()}
            disabled={loading}
            title="Atualizar lista"
          >
            <RefreshCw size={17} />
          </button>
        </div>

        <div className="schedules-filters">
          <select
            value={filterTurma}
            onChange={(event) => {
              setFilterTurma(event.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="todas">Todas as turmas</option>
            {turmas.map((turma) => (
              <option key={turma.id} value={turma.id}>
                {turma.nome}
              </option>
            ))}
          </select>

          <select
            value={filterProfessor}
            onChange={(event) => {
              setFilterProfessor(event.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="todos">Todos os professores</option>
            {professores.map((professor) => (
              <option key={professor.id} value={professor.id}>
                {professor.nome_completo}
              </option>
            ))}
          </select>

          <select
            value={filterDisciplina}
            onChange={(event) => {
              setFilterDisciplina(event.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="todas">Todas as disciplinas</option>
            {disciplinas.map((disciplina) => (
              <option key={disciplina.id} value={disciplina.id}>
                {disciplina.nome}
              </option>
            ))}
          </select>

          <select
            value={filterDia}
            onChange={(event) => {
              setFilterDia(event.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="todos">Todos os dias</option>
            {diasSemana.map((dia, index) => (
              <option key={dia} value={index}>
                {dia}
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
            <option value="ativos">Ativos</option>
            <option value="inativos">Inativos</option>
          </select>
        </div>

        {loading ? (
          <div className="schedules-loading">
            <RefreshCw size={22} />
            <span>Carregando horários...</span>
          </div>
        ) : (
          <>
            <div className="schedules-table-wrapper">
              <table className="schedules-table">
                <thead>
                  <tr>
                    <th>Turma</th>
                    <th>Disciplina</th>
                    <th>Professor</th>
                    <th>Dia</th>
                    <th>Horário</th>
                    <th>Sala</th>
                    <th>Situação</th>
                    <th>Ações</th>
                  </tr>
                </thead>

                <tbody>
                  {paginatedHorarios.map((horario) => {
                    const atribuicao = obterAtribuicao(horario);

                    return (
                      <tr key={horario.id}>
                        <td>
                          <strong>
                            {atribuicao
                              ? obterNomeTurma(atribuicao.turma_id)
                              : `Vínculo #${horario.turma_disciplina_id}`}
                          </strong>
                        </td>

                        <td>
                          {atribuicao
                            ? obterNomeDisciplina(atribuicao.disciplina_id)
                            : "Não disponível"}
                        </td>

                        <td>
                          {atribuicao
                            ? obterNomeProfessor(atribuicao.professor_id)
                            : "Não disponível"}
                        </td>

                        <td>
                          <span className="schedules-day">
                            {diasSemana[horario.dia_semana]}
                          </span>
                        </td>

                        <td>
                          <span className="schedules-hours">
                            <Clock3 size={14} />
                            {formatarHora(horario.hora_inicio)} –{" "}
                            {formatarHora(horario.hora_fim)}
                          </span>
                        </td>

                        <td>{horario.sala || "—"}</td>

                        <td>
                          <span
                            className={`schedules-status ${
                              horario.ativo ? "active" : "inactive"
                            }`}
                          >
                            {horario.ativo ? "Ativo" : "Inativo"}
                          </span>
                        </td>

                        <td>
                          <div className="schedules-actions">
                            <button
                              onClick={() => openDetails(horario)}
                              title="Visualizar horário"
                            >
                              <Eye size={17} />
                            </button>

                            {canManage && horario.ativo && (
                              <button
                                onClick={() => openEdit(horario)}
                                title="Editar horário"
                              >
                                <Pencil size={17} />
                              </button>
                            )}

                            {canManage && horario.ativo && (
                              <button
                                className="danger"
                                onClick={() =>
                                  void handleDeactivate(horario)
                                }
                                title="Inativar horário"
                              >
                                <UserX size={17} />
                              </button>
                            )}

                            {canManage && !horario.ativo && (
                              <button
                                onClick={() =>
                                  void handleReactivate(horario)
                                }
                                title="Reativar horário"
                              >
                                <RotateCcw size={17} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}

                  {paginatedHorarios.length === 0 && (
                    <tr>
                      <td colSpan={8} className="schedules-empty">
                        <CalendarClock size={32} />
                        <strong>Nenhum horário encontrado</strong>
                        <span>
                          Tente alterar os filtros ou cadastrar um novo
                          horário.
                        </span>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="schedules-pagination">
              <span>
                Mostrando{" "}
                {filteredHorarios.length === 0
                  ? 0
                  : (currentPage - 1) * PAGE_SIZE + 1}
                {" a "}
                {Math.min(
                  currentPage * PAGE_SIZE,
                  filteredHorarios.length,
                )}
                {" de "}
                {filteredHorarios.length} horários
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
          className="schedules-modal-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeModal();
          }}
        >
          <section className="schedules-modal">
            <header className="schedules-modal-header">
              <div>
                <span>GESTÃO ACADÊMICA</span>
                <h3>
                  {modalMode === "create"
                    ? "Cadastrar horário"
                    : modalMode === "edit"
                      ? "Editar horário"
                      : "Detalhes do horário"}
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

            {modalMode === "details" && selectedHorario ? (
              <div className="schedules-details">
                {(() => {
                  const atribuicao = obterAtribuicao(selectedHorario);

                  return (
                    <>
                      <div className="schedules-details-title">
                        <div className="schedules-name-icon">
                          <CalendarClock size={24} />
                        </div>

                        <div>
                          <h4>
                            {atribuicao
                              ? obterNomeTurma(atribuicao.turma_id)
                              : `Vínculo #${selectedHorario.turma_disciplina_id}`}
                          </h4>

                          <span
                            className={`schedules-status ${
                              selectedHorario.ativo ? "active" : "inactive"
                            }`}
                          >
                            {selectedHorario.ativo ? "Ativo" : "Inativo"}
                          </span>
                        </div>
                      </div>

                      <div className="schedules-details-grid">
                        <div>
                          <span>Disciplina</span>
                          <strong>
                            {atribuicao
                              ? obterNomeDisciplina(atribuicao.disciplina_id)
                              : "Não disponível"}
                          </strong>
                        </div>

                        <div>
                          <span>Professor</span>
                          <strong>
                            {atribuicao
                              ? obterNomeProfessor(atribuicao.professor_id)
                              : "Não disponível"}
                          </strong>
                        </div>

                        <div>
                          <span>Dia da semana</span>
                          <strong>
                            {diasSemana[selectedHorario.dia_semana]}
                          </strong>
                        </div>

                        <div>
                          <span>Horário</span>
                          <strong>
                            {formatarHora(selectedHorario.hora_inicio)} às{" "}
                            {formatarHora(selectedHorario.hora_fim)}
                          </strong>
                        </div>

                        <div>
                          <span>Sala</span>
                          <strong>
                            {selectedHorario.sala || "Não informada"}
                          </strong>
                        </div>

                        <div>
                          <span>Carga horária semanal</span>
                          <strong>
                            {atribuicao
                              ? `${atribuicao.carga_horaria_semanal}h`
                              : "Não disponível"}
                          </strong>
                        </div>

                        <div className="field-full">
                          <span>Data de cadastro</span>
                          <strong>
                            {new Date(
                              selectedHorario.data_cadastro,
                            ).toLocaleDateString("pt-BR")}
                          </strong>
                        </div>
                      </div>
                    </>
                  );
                })()}

                <footer className="schedules-modal-footer">
                  <button
                    className="schedules-secondary-button"
                    onClick={closeModal}
                  >
                    Fechar
                  </button>

                  {canManage && selectedHorario.ativo && (
                    <button
                      className="schedules-primary-button"
                      onClick={() => openEdit(selectedHorario)}
                    >
                      <Pencil size={16} />
                      Editar horário
                    </button>
                  )}

                  {canManage && !selectedHorario.ativo && (
                    <button
                      className="schedules-primary-button"
                      onClick={() =>
                        void handleReactivate(selectedHorario)
                      }
                    >
                      <RotateCcw size={16} />
                      Reativar horário
                    </button>
                  )}
                </footer>
              </div>
            ) : (
              <form onSubmit={handleSubmit}>
                <div className="schedules-form-grid">
                  <label className="schedules-field">
                    Turma *
                    <select
                      autoFocus
                      value={form.turma_id}
                      onChange={(event) =>
                        handleTurmaChange(event.target.value)
                      }
                      required
                    >
                      <option value="">Selecione uma turma</option>

                      {turmasDisponiveis.map((turma) => (
                        <option key={turma.id} value={turma.id}>
                          {turma.nome}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="schedules-field">
                    Disciplina *
                    <select
                      value={form.disciplina_id}
                      onChange={(event) =>
                        handleDisciplinaChange(event.target.value)
                      }
                      disabled={!form.turma_id}
                      required
                    >
                      <option value="">Selecione uma disciplina</option>

                      {disciplinasDisponiveis.map((disciplina) => (
                        <option
                          key={disciplina.id}
                          value={disciplina.id}
                        >
                          {disciplina.nome}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="schedules-field field-full">
                    Professor *
                    <select
                      value={form.professor_id}
                      onChange={(event) =>
                        updateField("professor_id", event.target.value)
                      }
                      disabled={!form.disciplina_id}
                      required
                    >
                      <option value="">Selecione um professor</option>

                      {professoresDisponiveis.map((professor) => (
                        <option
                          key={professor.id}
                          value={professor.id}
                        >
                          {professor.nome_completo}
                        </option>
                      ))}
                    </select>

                    {atribuicoesAtivas.length === 0 && (
                      <small>
                        Nenhuma atribuição ativa disponível. Cadastre o
                        vínculo entre turma, disciplina e professor antes
                        de criar um horário.
                      </small>
                    )}
                  </label>

                  <label className="schedules-field field-full">
                    Dia da semana *
                    <select
                      value={form.dia_semana}
                      onChange={(event) =>
                        updateField("dia_semana", event.target.value)
                      }
                      required
                    >
                      {diasSemana.map((dia, index) => (
                        <option key={dia} value={index}>
                          {dia}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="schedules-field">
                    Hora de início *
                    <input
                      type="time"
                      value={form.hora_inicio}
                      onChange={(event) =>
                        updateField("hora_inicio", event.target.value)
                      }
                      required
                    />
                  </label>

                  <label className="schedules-field">
                    Hora de término *
                    <input
                      type="time"
                      value={form.hora_fim}
                      onChange={(event) =>
                        updateField("hora_fim", event.target.value)
                      }
                      required
                    />
                  </label>

                  <label className="schedules-field field-full">
                    Sala
                    <input
                      value={form.sala}
                      onChange={(event) =>
                        updateField("sala", event.target.value)
                      }
                      placeholder="Ex.: Sala 02"
                      maxLength={50}
                    />
                  </label>
                </div>

                {formError && (
                  <div className="schedules-form-error">{formError}</div>
                )}

                <footer className="schedules-modal-footer">
                  <button
                    type="button"
                    className="schedules-secondary-button"
                    onClick={closeModal}
                    disabled={saving}
                  >
                    Cancelar
                  </button>

                  <button
                    type="submit"
                    className="schedules-primary-button"
                    disabled={saving || atribuicoesAtivas.length === 0}
                  >
                    {saving
                      ? "Salvando..."
                      : modalMode === "create"
                        ? "Cadastrar horário"
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
