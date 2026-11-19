
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
  BookMarked,
  UserX,
  X,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  RotateCcw,
  Clock3,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { api } from "../services/api";

interface Disciplina {
  id: number;
  nome: string;
  codigo: string | null;
  descricao: string | null;
  carga_horaria: number;
  area_conhecimento: string | null;
  ativa: boolean;
  data_cadastro: string;
}

interface DisciplinaForm {
  nome: string;
  codigo: string;
  descricao: string;
  carga_horaria: string;
  area_conhecimento: string;
}

type ModalMode = "create" | "edit" | "details";

const PAGE_SIZE = 10;

const emptyForm: DisciplinaForm = {
  nome: "",
  codigo: "",
  descricao: "",
  carga_horaria: "",
  area_conhecimento: "",
};

function normalizarTexto(valor: string): string {
  return valor
    .toLocaleLowerCase("pt-BR")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
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
      return "A disciplina solicitada não foi encontrada.";
    }

    if (error.response?.status === 409) {
      return "Já existe uma disciplina com este nome ou código.";
    }

    if (!error.response) {
      return "Não foi possível conectar ao servidor.";
    }
  }

  return "Ocorreu um erro inesperado. Tente novamente.";
}

export default function DisciplinasPage() {
  const { user } = useAuth();

  const permissions = user?.permissoes ?? [];

  const canList = permissions.includes("disciplinas.listar");
  const canCreate = permissions.includes("disciplinas.criar");
  const canEdit = permissions.includes("disciplinas.editar");
  const canDeactivate = permissions.includes("disciplinas.desativar");

  const [disciplinas, setDisciplinas] = useState<Disciplina[]>([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [filterArea, setFilterArea] = useState("todas");
  const [filterStatus, setFilterStatus] = useState("todas");
  const [currentPage, setCurrentPage] = useState(1);

  const [modalMode, setModalMode] = useState<ModalMode | null>(null);
  const [selectedDisciplina, setSelectedDisciplina] =
    useState<Disciplina | null>(null);
  const [form, setForm] = useState<DisciplinaForm>(emptyForm);
  const [formError, setFormError] = useState("");

  const loadDisciplinas = useCallback(async () => {
    if (!canList) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await api.get<Disciplina[]>("/disciplinas/", {
        params: {
          offset: 0,
          limit: 100,
        },
      });

      setDisciplinas(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [canList]);

  useEffect(() => {
    void loadDisciplinas();
  }, [loadDisciplinas]);

  const areas = useMemo(
    () =>
      [
        ...new Set(
          disciplinas
            .map((disciplina) => disciplina.area_conhecimento)
            .filter((area): area is string => Boolean(area)),
        ),
      ].sort((a, b) => a.localeCompare(b, "pt-BR")),
    [disciplinas],
  );

  const filteredDisciplinas = useMemo(() => {
    const normalizedSearch = normalizarTexto(search);

    return disciplinas.filter((disciplina) => {
      const matchesSearch =
        !normalizedSearch ||
        normalizarTexto(disciplina.nome).includes(normalizedSearch) ||
        normalizarTexto(disciplina.codigo ?? "").includes(normalizedSearch) ||
        normalizarTexto(disciplina.area_conhecimento ?? "").includes(
          normalizedSearch,
        );

      const matchesArea =
        filterArea === "todas" ||
        disciplina.area_conhecimento === filterArea;

      const matchesStatus =
        filterStatus === "todas" ||
        (filterStatus === "ativas" && disciplina.ativa) ||
        (filterStatus === "inativas" && !disciplina.ativa);

      return matchesSearch && matchesArea && matchesStatus;
    });
  }, [disciplinas, search, filterArea, filterStatus]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredDisciplinas.length / PAGE_SIZE),
  );

  const paginatedDisciplinas = filteredDisciplinas.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE,
  );

  const activeCount = disciplinas.filter(
    (disciplina) => disciplina.ativa,
  ).length;

  const inactiveCount = disciplinas.length - activeCount;

  function openCreate() {
    setSelectedDisciplina(null);
    setForm(emptyForm);
    setFormError("");
    setModalMode("create");
  }

  function openEdit(disciplina: Disciplina) {
    setSelectedDisciplina(disciplina);

    setForm({
      nome: disciplina.nome,
      codigo: disciplina.codigo ?? "",
      descricao: disciplina.descricao ?? "",
      carga_horaria: String(disciplina.carga_horaria),
      area_conhecimento: disciplina.area_conhecimento ?? "",
    });

    setFormError("");
    setModalMode("edit");
  }

  function openDetails(disciplina: Disciplina) {
    setSelectedDisciplina(disciplina);
    setModalMode("details");
  }

  function closeModal() {
    if (saving) return;

    setModalMode(null);
    setSelectedDisciplina(null);
    setFormError("");
  }

  function closeModalAfterSave() {
    setModalMode(null);
    setSelectedDisciplina(null);
    setFormError("");
  }

  function updateField(field: keyof DisciplinaForm, value: string) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");

    const nome = form.nome.trim();
    const codigo = form.codigo.trim();
    const descricao = form.descricao.trim();
    const areaConhecimento = form.area_conhecimento.trim();
    const cargaHoraria = Number(form.carga_horaria);

    if (nome.length < 2 || nome.length > 100) {
      setFormError("O nome deve ter entre 2 e 100 caracteres.");
      return;
    }

    if (codigo.length > 20) {
      setFormError("O código deve ter no máximo 20 caracteres.");
      return;
    }

    if (
      !Number.isInteger(cargaHoraria) ||
      cargaHoraria < 1 ||
      cargaHoraria > 2000
    ) {
      setFormError(
        "A carga horária deve ser um número inteiro entre 1 e 2.000.",
      );
      return;
    }

    if (areaConhecimento.length > 100) {
      setFormError("A área de conhecimento deve ter até 100 caracteres.");
      return;
    }

    const payload = {
      nome,
      codigo: codigo ? codigo.toUpperCase() : null,
      descricao: descricao || null,
      carga_horaria: cargaHoraria,
      area_conhecimento: areaConhecimento || null,
    };

    setSaving(true);

    try {
      if (modalMode === "create") {
        await api.post("/disciplinas/", payload);
      } else if (modalMode === "edit" && selectedDisciplina) {
        await api.put(
          `/disciplinas/${selectedDisciplina.id}`,
          payload,
        );
      }

      closeModalAfterSave();
      await loadDisciplinas();
    } catch (err) {
      setFormError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleDeactivate(disciplina: Disciplina) {
    const confirmed = window.confirm(
      `Deseja realmente inativar a disciplina "${disciplina.nome}"?\n\nO registro será mantido no histórico do sistema.`,
    );

    if (!confirmed) return;

    setError("");

    try {
      await api.delete(`/disciplinas/${disciplina.id}`);
      await loadDisciplinas();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  async function handleReactivate(disciplina: Disciplina) {
    if (!canEdit || disciplina.ativa) return;

    const confirmed = window.confirm(
      `Deseja realmente reativar a disciplina "${disciplina.nome}"?`,
    );

    if (!confirmed) return;

    setError("");

    try {
      await api.put(`/disciplinas/${disciplina.id}`, {
        ativa: true,
      });

      if (modalMode === "details") {
        setModalMode(null);
        setSelectedDisciplina(null);
      }

      await loadDisciplinas();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  if (!canList) {
    return (
      <div className="subjects-access-denied">
        <BookOpen size={36} />
        <h2>Acesso não autorizado</h2>
        <p>Você não possui permissão para visualizar as disciplinas.</p>
      </div>
    );
  }

  return (
    <div className="subjects-page">
      <div className="subjects-heading">
        <div>
          <span className="subjects-eyebrow">GESTÃO ACADÊMICA</span>
          <h2>Disciplinas</h2>
          <p>Gerencie as disciplinas e suas respectivas cargas horárias.</p>
        </div>

        {canCreate && (
          <button className="subjects-add" onClick={openCreate}>
            <Plus size={18} />
            Nova disciplina
          </button>
        )}
      </div>

      {error && (
        <div className="subjects-alert">
          <span>{error}</span>
          <button
            onClick={() => setError("")}
            aria-label="Fechar aviso"
          >
            <X size={17} />
          </button>
        </div>
      )}

      <div className="subjects-stats">
        <div className="subjects-stat">
          <div className="subjects-stat-icon orange">
            <BookOpen size={21} />
          </div>
          <div>
            <span>Total de disciplinas</span>
            <strong>{disciplinas.length}</strong>
          </div>
        </div>

        <div className="subjects-stat">
          <div className="subjects-stat-icon green">
            <BookMarked size={21} />
          </div>
          <div>
            <span>Disciplinas ativas</span>
            <strong>{activeCount}</strong>
          </div>
        </div>

        <div className="subjects-stat">
          <div className="subjects-stat-icon gray">
            <UserX size={21} />
          </div>
          <div>
            <span>Disciplinas inativas</span>
            <strong>{inactiveCount}</strong>
          </div>
        </div>
      </div>

      <section className="subjects-table-card">
        <div className="subjects-toolbar">
          <div>
            <h3>Lista de disciplinas</h3>
            <p>Consulte e gerencie as disciplinas cadastradas.</p>
          </div>

          <div className="subjects-search">
            <Search size={18} />
            <input
              type="search"
              placeholder="Pesquisar disciplina..."
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setCurrentPage(1);
              }}
            />
          </div>

          <button
            className="subjects-refresh"
            onClick={() => void loadDisciplinas()}
            disabled={loading}
            title="Atualizar lista"
          >
            <RefreshCw size={17} />
          </button>
        </div>

        <div className="subjects-filters">
          <select
            value={filterArea}
            onChange={(event) => {
              setFilterArea(event.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="todas">Todas as áreas</option>
            {areas.map((area) => (
              <option key={area} value={area}>
                {area}
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
          <div className="subjects-loading">
            <RefreshCw size={22} />
            <span>Carregando disciplinas...</span>
          </div>
        ) : (
          <>
            <div className="subjects-table-wrapper">
              <table className="subjects-table">
                <thead>
                  <tr>
                    <th>Disciplina</th>
                    <th>Código</th>
                    <th>Área de conhecimento</th>
                    <th>Carga horária</th>
                    <th>Situação</th>
                    <th>Ações</th>
                  </tr>
                </thead>

                <tbody>
                  {paginatedDisciplinas.map((disciplina) => (
                    <tr key={disciplina.id}>
                      <td>
                        <div className="subjects-name">
                          <div className="subjects-name-icon">
                            <BookOpen size={17} />
                          </div>
                          <div>
                            <strong>{disciplina.nome}</strong>
                            <span>
                              {disciplina.descricao
                                ? disciplina.descricao
                                : "Sem descrição cadastrada"}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td>
                        <span className="subjects-code">
                          {disciplina.codigo || "—"}
                        </span>
                      </td>

                      <td>
                        <span className="subjects-area">
                          {disciplina.area_conhecimento || "Não informada"}
                        </span>
                      </td>

                      <td>
                        <span className="subjects-hours">
                          <Clock3 size={14} />
                          {disciplina.carga_horaria}h
                        </span>
                      </td>

                      <td>
                        <span
                          className={`subjects-status ${
                            disciplina.ativa ? "active" : "inactive"
                          }`}
                        >
                          {disciplina.ativa ? "Ativa" : "Inativa"}
                        </span>
                      </td>

                      <td>
                        <div className="subjects-actions">
                          <button
                            onClick={() => openDetails(disciplina)}
                            title="Visualizar disciplina"
                          >
                            <Eye size={17} />
                          </button>

                          {canEdit && disciplina.ativa && (
                            <button
                              onClick={() => openEdit(disciplina)}
                              title="Editar disciplina"
                            >
                              <Pencil size={17} />
                            </button>
                          )}

                          {canDeactivate && disciplina.ativa && (
                            <button
                              className="danger"
                              onClick={() =>
                                void handleDeactivate(disciplina)
                              }
                              title="Inativar disciplina"
                            >
                              <UserX size={17} />
                            </button>
                          )}

                          {canEdit && !disciplina.ativa && (
                            <button
                              onClick={() =>
                                void handleReactivate(disciplina)
                              }
                              title="Reativar disciplina"
                            >
                              <RotateCcw size={17} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}

                  {paginatedDisciplinas.length === 0 && (
                    <tr>
                      <td colSpan={6} className="subjects-empty">
                        <BookOpen size={32} />
                        <strong>Nenhuma disciplina encontrada</strong>
                        <span>
                          Tente alterar os filtros ou cadastrar uma nova
                          disciplina.
                        </span>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="subjects-pagination">
              <span>
                Mostrando{" "}
                {filteredDisciplinas.length === 0
                  ? 0
                  : (currentPage - 1) * PAGE_SIZE + 1}
                {" a "}
                {Math.min(
                  currentPage * PAGE_SIZE,
                  filteredDisciplinas.length,
                )}
                {" de "}
                {filteredDisciplinas.length} disciplinas
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
          className="subjects-modal-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeModal();
          }}
        >
          <section className="subjects-modal">
            <header className="subjects-modal-header">
              <div>
                <span>GESTÃO ACADÊMICA</span>
                <h3>
                  {modalMode === "create"
                    ? "Cadastrar disciplina"
                    : modalMode === "edit"
                      ? "Editar disciplina"
                      : "Detalhes da disciplina"}
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

            {modalMode === "details" && selectedDisciplina ? (
              <div className="subjects-details">
                <div className="subjects-details-title">
                  <div className="subjects-name-icon large">
                    <BookOpen size={24} />
                  </div>

                  <div>
                    <h4>{selectedDisciplina.nome}</h4>
                    <span
                      className={`subjects-status ${
                        selectedDisciplina.ativa ? "active" : "inactive"
                      }`}
                    >
                      {selectedDisciplina.ativa ? "Ativa" : "Inativa"}
                    </span>
                  </div>
                </div>

                <div className="subjects-details-grid">
                  <div>
                    <span>Código</span>
                    <strong>{selectedDisciplina.codigo || "Não informado"}</strong>
                  </div>

                  <div>
                    <span>Área de conhecimento</span>
                    <strong>
                      {selectedDisciplina.area_conhecimento ||
                        "Não informada"}
                    </strong>
                  </div>

                  <div>
                    <span>Carga horária</span>
                    <strong>{selectedDisciplina.carga_horaria} horas</strong>
                  </div>

                  <div>
                    <span>Data de cadastro</span>
                    <strong>
                      {new Date(
                        selectedDisciplina.data_cadastro,
                      ).toLocaleDateString("pt-BR")}
                    </strong>
                  </div>

                  <div className="field-full">
                    <span>Descrição</span>
                    <strong>
                      {selectedDisciplina.descricao || "Sem descrição"}
                    </strong>
                  </div>
                </div>

                <footer className="subjects-modal-footer">
                  <button
                    className="subjects-secondary-button"
                    onClick={closeModal}
                  >
                    Fechar
                  </button>

                  {canEdit && selectedDisciplina.ativa && (
                    <button
                      className="subjects-primary-button"
                      onClick={() => openEdit(selectedDisciplina)}
                    >
                      <Pencil size={16} />
                      Editar disciplina
                    </button>
                  )}

                  {canEdit && !selectedDisciplina.ativa && (
                    <button
                      className="subjects-primary-button"
                      onClick={() =>
                        void handleReactivate(selectedDisciplina)
                      }
                    >
                      <RotateCcw size={16} />
                      Reativar disciplina
                    </button>
                  )}
                </footer>
              </div>
            ) : (
              <form onSubmit={handleSubmit}>
                <div className="subjects-form-grid">
                  <label className="subjects-field field-full">
                    Nome da disciplina *
                    <input
                      autoFocus
                      value={form.nome}
                      onChange={(event) =>
                        updateField("nome", event.target.value)
                      }
                      placeholder="Ex.: Matemática"
                      minLength={2}
                      maxLength={100}
                      required
                    />
                  </label>

                  <label className="subjects-field">
                    Código
                    <input
                      value={form.codigo}
                      onChange={(event) =>
                        updateField(
                          "codigo",
                          event.target.value.toUpperCase(),
                        )
                      }
                      placeholder="Ex.: MAT001"
                      maxLength={20}
                    />
                  </label>

                  <label className="subjects-field">
                    Carga horária (horas) *
                    <input
                      type="number"
                      value={form.carga_horaria}
                      onChange={(event) =>
                        updateField("carga_horaria", event.target.value)
                      }
                      placeholder="Ex.: 80"
                      min={1}
                      max={2000}
                      step={1}
                      required
                    />
                  </label>

                  <label className="subjects-field field-full">
                    Área de conhecimento
                    <input
                      value={form.area_conhecimento}
                      onChange={(event) =>
                        updateField(
                          "area_conhecimento",
                          event.target.value,
                        )
                      }
                      placeholder="Ex.: Ciências da Natureza"
                      maxLength={100}
                    />
                  </label>

                  <label className="subjects-field field-full">
                    Descrição
                    <textarea
                      value={form.descricao}
                      onChange={(event) =>
                        updateField("descricao", event.target.value)
                      }
                      placeholder="Descreva brevemente a disciplina..."
                      rows={4}
                    />
                  </label>
                </div>

                {formError && (
                  <div className="subjects-form-error">{formError}</div>
                )}

                <footer className="subjects-modal-footer">
                  <button
                    type="button"
                    className="subjects-secondary-button"
                    onClick={closeModal}
                    disabled={saving}
                  >
                    Cancelar
                  </button>

                  <button
                    type="submit"
                    className="subjects-primary-button"
                    disabled={saving}
                  >
                    {saving
                      ? "Salvando..."
                      : modalMode === "create"
                        ? "Cadastrar disciplina"
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
