
import {
  Fragment,
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
  UserRound,
  Users,
  X,
  ChevronLeft,
  ChevronRight,
  UserX,
  RefreshCw,
  GraduationCap,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { api } from "../services/api";

type StatusAluno = "ativo" | "inativo" | "transferido";

interface Aluno {
  id: number;
  nome_completo: string;
  data_nascimento: string;
  matricula: string;
  cpf: string | null;
  sexo: string | null;
  telefone: string | null;
  email: string | null;
  cep: string | null;
  endereco: string | null;
  numero: string | null;
  bairro: string | null;
  cidade: string | null;
  estado: string | null;
  turma_id: number | null;
  status: StatusAluno;
  data_cadastro: string;
}

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

interface AlunoForm {
  nome_completo: string;
  data_nascimento: string;
  matricula: string;
  cpf: string;
  sexo: string;
  telefone: string;
  email: string;
  cep: string;
  endereco: string;
  numero: string;
  bairro: string;
  cidade: string;
  estado: string;
  turma_id: string;
  status: StatusAluno;
}

const emptyForm: AlunoForm = {
  nome_completo: "",
  data_nascimento: "",
  matricula: "",
  cpf: "",
  sexo: "",
  telefone: "",
  email: "",
  cep: "",
  endereco: "",
  numero: "",
  bairro: "",
  cidade: "",
  estado: "",
  turma_id: "",
  status: "ativo",
};

const PAGE_SIZE = 10;

function formatDate(value: string) {
  if (!value) return "—";

  const [year, month, day] = value.substring(0, 10).split("-");
  return `${day}/${month}/${year}`;
}

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

export default function AlunosPage() {
  const { user } = useAuth();

  const permissoes = user?.permissoes ?? [];

  const podeListar = permissoes.includes("alunos.listar");
  const podeCriar = permissoes.includes("alunos.criar");
  const podeEditar = permissoes.includes("alunos.editar");
  const podeInativar = permissoes.includes("alunos.desativar");
  const podeListarTurmas = permissoes.includes("turmas.listar");

  const [alunos, setAlunos] = useState<Aluno[]>([]);
  const [turmas, setTurmas] = useState<Turma[]>([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [search, setSearch] = useState("");
  const [turmaFiltro, setTurmaFiltro] = useState("todas");
  const [currentPage, setCurrentPage] = useState(1);

  const [modal, setModal] = useState<"create" | "edit" | "view" | null>(
    null,
  );

  const [selectedAluno, setSelectedAluno] = useState<Aluno | null>(null);
  const [form, setForm] = useState<AlunoForm>(emptyForm);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Carrega os alunos.
  const carregarAlunos = useCallback(async () => {
    if (!podeListar) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await api.get<Aluno[]>("/alunos/", {
        params: { offset: 0, limit: 100 },
      });

      setAlunos(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [podeListar]);

  // Carrega as turmas disponíveis para agrupamento e seleção.
  const carregarTurmas = useCallback(async () => {
    if (!podeListarTurmas) return;

    try {
      const response = await api.get<Turma[]>("/turmas/", {
        params: { offset: 0, limit: 100 },
      });

      setTurmas(response.data);
    } catch {
      setTurmas([]);
    }
  }, [podeListarTurmas]);

  useEffect(() => {
    void carregarAlunos();
    void carregarTurmas();
  }, [carregarAlunos, carregarTurmas]);

  // Retorna o nome da turma de um aluno.
  const obterNomeTurma = useCallback(
    (turmaId: number | null) => {
      if (!turmaId) return "Sem turma vinculada";

      const turma = turmas.find((item) => item.id === turmaId);

      if (!turma) return `Turma #${turmaId}`;

      return `${turma.nome} — ${turma.serie} — ${turma.turno}`;
    },
    [turmas],
  );

  // Filtra os alunos por pesquisa e turma.
  const alunosFiltrados = useMemo(() => {
    const termo = search.trim().toLocaleLowerCase("pt-BR");

    return alunos
      .filter((aluno) => {
        const correspondeTurma =
          turmaFiltro === "todas" ||
          (turmaFiltro === "sem-turma" && aluno.turma_id === null) ||
          aluno.turma_id?.toString() === turmaFiltro;

        if (!correspondeTurma) return false;

        if (!termo) return true;

        return [
          aluno.nome_completo,
          aluno.matricula,
          aluno.cpf ?? "",
          aluno.email ?? "",
          obterNomeTurma(aluno.turma_id),
        ].some((valor) =>
          valor.toLocaleLowerCase("pt-BR").includes(termo),
        );
      })
      .sort((a, b) => {
        const turmaA = obterNomeTurma(a.turma_id);
        const turmaB = obterNomeTurma(b.turma_id);

        const comparacao = turmaA.localeCompare(turmaB, "pt-BR");

        if (comparacao !== 0) return comparacao;

        return a.nome_completo.localeCompare(b.nome_completo, "pt-BR");
      });
  }, [alunos, search, turmaFiltro, obterNomeTurma]);

  const totalPages = Math.max(
    1,
    Math.ceil(alunosFiltrados.length / PAGE_SIZE),
  );

  const alunosPagina = alunosFiltrados.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE,
  );

  // Agrupa os alunos da página atual por turma.
  const gruposPagina = useMemo(() => {
    const grupos = new Map<string, Aluno[]>();

    alunosPagina.forEach((aluno) => {
      const nomeTurma = obterNomeTurma(aluno.turma_id);

      if (!grupos.has(nomeTurma)) {
        grupos.set(nomeTurma, []);
      }

      grupos.get(nomeTurma)!.push(aluno);
    });

    return Array.from(grupos.entries());
  }, [alunosPagina, obterNomeTurma]);

  useEffect(() => {
    setCurrentPage(1);
  }, [search, turmaFiltro]);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const abrirCadastro = () => {
    setSelectedAluno(null);
    setForm(emptyForm);
    setError("");
    setModal("create");
  };

  const abrirEdicao = (aluno: Aluno) => {
    setSelectedAluno(aluno);

    setForm({
      nome_completo: aluno.nome_completo,
      data_nascimento: aluno.data_nascimento.substring(0, 10),
      matricula: aluno.matricula,
      cpf: aluno.cpf ?? "",
      sexo: aluno.sexo ?? "",
      telefone: aluno.telefone ?? "",
      email: aluno.email ?? "",
      cep: aluno.cep ?? "",
      endereco: aluno.endereco ?? "",
      numero: aluno.numero ?? "",
      bairro: aluno.bairro ?? "",
      cidade: aluno.cidade ?? "",
      estado: aluno.estado ?? "",
      turma_id: aluno.turma_id?.toString() ?? "",
      status: aluno.status,
    });

    setError("");
    setModal("edit");
  };

  const abrirDetalhes = (aluno: Aluno) => {
    setSelectedAluno(aluno);
    setModal("view");
  };

  const fecharModal = () => {
    if (saving) return;

    setModal(null);
    setSelectedAluno(null);
    setError("");
  };

  const atualizarCampo = (
    campo: keyof AlunoForm,
    valor: string,
  ) => {
    setForm((anterior) => ({
      ...anterior,
      [campo]: valor,
    }));
  };

  const salvarAluno = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (modal === "create" && !podeCriar) return;
    if (modal === "edit" && !podeEditar) return;

    const dados = {
      nome_completo: form.nome_completo.trim(),
      data_nascimento: form.data_nascimento,
      matricula: form.matricula.trim(),
      cpf: form.cpf.replace(/\D/g, "") || null,
      sexo: form.sexo || null,
      telefone: form.telefone || null,
      email: form.email.trim() || null,
      cep: form.cep.replace(/\D/g, "") || null,
      endereco: form.endereco.trim() || null,
      numero: form.numero.trim() || null,
      bairro: form.bairro.trim() || null,
      cidade: form.cidade.trim() || null,
      estado: form.estado.trim().toUpperCase() || null,
      turma_id: form.turma_id ? Number(form.turma_id) : null,
      status: form.status,
    };

    if (dados.cpf && dados.cpf.length !== 11) {
      setError("O CPF deve possuir exatamente 11 números.");
      return;
    }

    if (dados.cep && dados.cep.length !== 8) {
      setError("O CEP deve possuir exatamente 8 números.");
      return;
    }

    setSaving(true);

    try {
      if (modal === "create") {
        await api.post("/alunos/", dados);
        setSuccess("Aluno cadastrado com sucesso!");
      } else if (modal === "edit" && selectedAluno) {
        await api.put(`/alunos/${selectedAluno.id}`, dados);
        setSuccess("Dados do aluno atualizados com sucesso!");
      }

      setModal(null);
      setSelectedAluno(null);

      await carregarAlunos();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const inativarAluno = async (aluno: Aluno) => {
    if (!podeInativar) return;

    const confirmar = window.confirm(
      `Deseja realmente inativar o cadastro de ${aluno.nome_completo}?\n\nO histórico do aluno será preservado.`,
    );

    if (!confirmar) return;

    setError("");
    setSuccess("");

    try {
      await api.delete(`/alunos/${aluno.id}`);

      setSuccess("Aluno inativado com sucesso.");
      await carregarAlunos();
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
            <h2>Alunos</h2>
          </div>
        </div>

        <div className="card-surface empty-state">
          <UserX size={36} />
          <h3>Acesso não autorizado</h3>
          <p>
            Seu perfil não possui permissão para consultar os alunos.
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
          <h2>Alunos</h2>
          <p className="muted">
            Consulte e gerencie os cadastros dos alunos da instituição.
          </p>
        </div>

        {podeCriar && (
          <button
            className="primary-button students-add"
            onClick={abrirCadastro}
          >
            <Plus size={18} />
            Novo aluno
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
            <span>Total de alunos carregados</span>
            <strong>{alunos.length}</strong>
          </div>
        </div>

        <div className="card-surface students-stat">
          <div className="students-stat-icon active-stat-icon">
            <UserRound size={21} />
          </div>
          <div>
            <span>Alunos ativos</span>
            <strong>
              {alunos.filter((aluno) => aluno.status === "ativo").length}
            </strong>
          </div>
        </div>

        <div className="card-surface students-stat">
          <div className="students-stat-icon inactive-stat-icon">
            <UserX size={21} />
          </div>
          <div>
            <span>Inativos ou transferidos</span>
            <strong>
              {alunos.filter((aluno) => aluno.status !== "ativo").length}
            </strong>
          </div>
        </div>
      </div>

      <div className="card-surface students-table-card">
        <div className="students-toolbar">
          <div>
            <h3>Lista de alunos</h3>
            <p className="muted">
              {alunosFiltrados.length} registro(s) encontrado(s)
            </p>
          </div>

          {podeListarTurmas && (
            <select
              className="students-class-filter"
              value={turmaFiltro}
              onChange={(event) => setTurmaFiltro(event.target.value)}
              aria-label="Filtrar alunos por turma"
            >
              <option value="todas">Todas as turmas</option>

              {turmas.map((turma) => (
                <option key={turma.id} value={turma.id.toString()}>
                  {turma.nome} — {turma.serie} — {turma.turno}
                </option>
              ))}

              <option value="sem-turma">Sem turma vinculada</option>
            </select>
          )}

          <div className="students-search">
            <Search size={18} />
            <input
              type="search"
              placeholder="Pesquisar por nome, matrícula ou CPF..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>

          <button
            className="icon-button"
            onClick={() => {
              void carregarAlunos();
              void carregarTurmas();
            }}
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
            <span>Carregando alunos...</span>
          </div>
        ) : alunosPagina.length === 0 ? (
          <div className="empty-state students-empty">
            <div className="empty-icon">
              <Users size={25} />
            </div>
            <h3>
              {search || turmaFiltro !== "todas"
                ? "Nenhum resultado encontrado"
                : "Nenhum aluno cadastrado"}
            </h3>
            <p>
              {search || turmaFiltro !== "todas"
                ? "Tente alterar a pesquisa ou selecionar outra turma."
                : "Os alunos cadastrados aparecerão nesta lista."}
            </p>
          </div>
        ) : (
          <>
            <div className="students-table-wrapper">
              <table className="students-table">
                <thead>
                  <tr>
                    <th>Aluno</th>
                    <th>Matrícula</th>
                    <th>CPF</th>
                    <th>Data de nascimento</th>
                    <th>Status</th>
                    <th className="actions-column">Ações</th>
                  </tr>
                </thead>

                <tbody>
                  {gruposPagina.map(([nomeTurma, alunosDoGrupo]) => (
                    <Fragment key={`grupo-${nomeTurma}`}>
                      <tr className="student-group-row">
                        <td colSpan={6}>
                          <div className="student-group-heading">
                            <GraduationCap size={17} />
                            <strong>{nomeTurma}</strong>
                            <span>
                              {alunosDoGrupo.length} aluno(s)
                            </span>
                          </div>
                        </td>
                      </tr>

                      {alunosDoGrupo.map((aluno) => (
                        <tr key={aluno.id}>
                          <td>
                            <div className="student-name-cell">
                              <div className="student-avatar">
                                {aluno.nome_completo.charAt(0).toUpperCase()}
                              </div>
                              <div>
                                <strong>{aluno.nome_completo}</strong>
                                <span>
                                  {aluno.email || "Sem e-mail cadastrado"}
                                </span>
                              </div>
                            </div>
                          </td>

                          <td>{aluno.matricula}</td>
                          <td>{aluno.cpf || "—"}</td>
                          <td>{formatDate(aluno.data_nascimento)}</td>

                          <td>
                            <span
                              className={`status-badge status-${aluno.status}`}
                            >
                              {aluno.status === "ativo"
                                ? "Ativo"
                                : aluno.status === "inativo"
                                  ? "Inativo"
                                  : "Transferido"}
                            </span>
                          </td>

                          <td>
                            <div className="student-actions">
                              <button
                                className="icon-button"
                                onClick={() => abrirDetalhes(aluno)}
                                title="Visualizar aluno"
                                aria-label="Visualizar aluno"
                              >
                                <Eye size={17} />
                              </button>

                              {podeEditar && (
                                <button
                                  className="icon-button"
                                  onClick={() => abrirEdicao(aluno)}
                                  title="Editar aluno"
                                  aria-label="Editar aluno"
                                >
                                  <Pencil size={17} />
                                </button>
                              )}

                              {podeInativar && aluno.status === "ativo" && (
                                <button
                                  className="icon-button danger-icon"
                                  onClick={() => void inativarAluno(aluno)}
                                  title="Inativar aluno"
                                  aria-label="Inativar aluno"
                                >
                                  <UserX size={17} />
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </Fragment>
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
            aria-labelledby="student-modal-title"
          >
            <div className="students-modal-header">
              <div>
                <p className="eyebrow">
                  {modal === "view" ? "CONSULTA" : "GESTÃO ACADÊMICA"}
                </p>
                <h3 id="student-modal-title">
                  {modal === "create"
                    ? "Cadastrar aluno"
                    : modal === "edit"
                      ? "Editar aluno"
                      : "Detalhes do aluno"}
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

            {modal === "view" && selectedAluno ? (
              <div className="student-details">
                <div className="student-details-heading">
                  <div className="student-avatar large-avatar">
                    {selectedAluno.nome_completo.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h4>{selectedAluno.nome_completo}</h4>
                    <span
                      className={`status-badge status-${selectedAluno.status}`}
                    >
                      {selectedAluno.status}
                    </span>
                  </div>
                </div>

                <div className="student-details-grid">
                  <Detail
                    label="Matrícula"
                    value={selectedAluno.matricula}
                  />
                  <Detail label="CPF" value={selectedAluno.cpf} />
                  <Detail
                    label="Nascimento"
                    value={formatDate(selectedAluno.data_nascimento)}
                  />
                  <Detail label="Sexo" value={selectedAluno.sexo} />
                  <Detail label="Telefone" value={selectedAluno.telefone} />
                  <Detail label="E-mail" value={selectedAluno.email} />
                  <Detail label="CEP" value={selectedAluno.cep} />
                  <Detail label="Endereço" value={selectedAluno.endereco} />
                  <Detail label="Número" value={selectedAluno.numero} />
                  <Detail label="Bairro" value={selectedAluno.bairro} />
                  <Detail label="Cidade" value={selectedAluno.cidade} />
                  <Detail label="Estado" value={selectedAluno.estado} />
                  <Detail
                    label="Turma"
                    value={obterNomeTurma(selectedAluno.turma_id)}
                  />
                  <Detail
                    label="Data do cadastro"
                    value={formatDate(selectedAluno.data_cadastro)}
                  />
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
                      onClick={() => abrirEdicao(selectedAluno)}
                    >
                      <Pencil size={16} />
                      Editar cadastro
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <form onSubmit={salvarAluno}>
                {error && <div className="form-error">{error}</div>}

                <div className="students-form-grid">
                  <Field label="Nome completo *" full>
                    <input
                      required
                      minLength={3}
                      maxLength={150}
                      value={form.nome_completo}
                      onChange={(e) =>
                        atualizarCampo("nome_completo", e.target.value)
                      }
                      placeholder="Nome completo do aluno"
                    />
                  </Field>

                  <Field label="Matrícula *">
                    <input
                      required
                      maxLength={30}
                      value={form.matricula}
                      onChange={(e) =>
                        atualizarCampo("matricula", e.target.value)
                      }
                      placeholder="Número de matrícula"
                    />
                  </Field>

                  <Field label="Data de nascimento *">
                    <input
                      required
                      type="date"
                      value={form.data_nascimento}
                      onChange={(e) =>
                        atualizarCampo("data_nascimento", e.target.value)
                      }
                    />
                  </Field>

                  <Field label="CPF">
                    <input
                      maxLength={14}
                      value={form.cpf}
                      onChange={(e) =>
                        atualizarCampo("cpf", e.target.value)
                      }
                      placeholder="Somente números"
                    />
                  </Field>

                  <Field label="Sexo">
                    <select
                      value={form.sexo}
                      onChange={(e) =>
                        atualizarCampo("sexo", e.target.value)
                      }
                    >
                      <option value="">Não informado</option>
                      <option value="Masculino">Masculino</option>
                      <option value="Feminino">Feminino</option>
                      <option value="Outro">Outro</option>
                    </select>
                  </Field>

                  <Field label="Telefone">
                    <input
                      maxLength={20}
                      value={form.telefone}
                      onChange={(e) =>
                        atualizarCampo("telefone", e.target.value)
                      }
                      placeholder="(99) 99999-9999"
                    />
                  </Field>

                  <Field label="E-mail">
                    <input
                      type="email"
                      maxLength={255}
                      value={form.email}
                      onChange={(e) =>
                        atualizarCampo("email", e.target.value)
                      }
                      placeholder="email@exemplo.com"
                    />
                  </Field>

                  <Field label="CEP">
                    <input
                      maxLength={8}
                      value={form.cep}
                      onChange={(e) =>
                        atualizarCampo("cep", e.target.value)
                      }
                      placeholder="00000000"
                    />
                  </Field>

                  <Field label="Endereço">
                    <input
                      maxLength={150}
                      value={form.endereco}
                      onChange={(e) =>
                        atualizarCampo("endereco", e.target.value)
                      }
                      placeholder="Rua, avenida..."
                    />
                  </Field>

                  <Field label="Número">
                    <input
                      maxLength={20}
                      value={form.numero}
                      onChange={(e) =>
                        atualizarCampo("numero", e.target.value)
                      }
                    />
                  </Field>

                  <Field label="Bairro">
                    <input
                      maxLength={100}
                      value={form.bairro}
                      onChange={(e) =>
                        atualizarCampo("bairro", e.target.value)
                      }
                    />
                  </Field>

                  <Field label="Cidade">
                    <input
                      maxLength={100}
                      value={form.cidade}
                      onChange={(e) =>
                        atualizarCampo("cidade", e.target.value)
                      }
                    />
                  </Field>

                  <Field label="Estado (UF)">
                    <input
                      maxLength={2}
                      value={form.estado}
                      onChange={(e) =>
                        atualizarCampo("estado", e.target.value)
                      }
                      placeholder="MA"
                    />
                  </Field>

                  <Field label="Turma">
                    {podeListarTurmas ? (
                      <select
                        value={form.turma_id}
                        onChange={(e) =>
                          atualizarCampo("turma_id", e.target.value)
                        }
                      >
                        <option value="">Sem turma vinculada</option>

                        {turmas
                          .filter((turma) => turma.ativa)
                          .map((turma) => (
                            <option
                              key={turma.id}
                              value={turma.id.toString()}
                            >
                              {turma.nome} — {turma.serie} — {turma.turno}
                            </option>
                          ))}
                      </select>
                    ) : (
                      <input
                        type="number"
                        min={1}
                        value={form.turma_id}
                        onChange={(e) =>
                          atualizarCampo("turma_id", e.target.value)
                        }
                        placeholder="ID da turma"
                      />
                    )}
                  </Field>

                  <Field label="Situação">
                    <select
                      value={form.status}
                      onChange={(e) =>
                        atualizarCampo("status", e.target.value)
                      }
                    >
                      <option value="ativo">Ativo</option>
                      <option value="inativo">Inativo</option>
                      <option value="transferido">Transferido</option>
                    </select>
                  </Field>
                </div>

                <p className="students-form-note">
                  * Campos obrigatórios. A turma é opcional.
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
