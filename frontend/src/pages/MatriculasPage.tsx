
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import axios from "axios";
import {
  Search,
  Plus,
  Eye,
  Pencil,
  X,
  RefreshCw,
  GraduationCap,
  CheckCircle2,
  XCircle,
  ArrowLeftRight,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
} from "lucide-react";
import { api } from "../services/api";
import { useAuth } from "../auth/AuthContext";

type SituacaoMatricula =
  | "ativa"
  | "cancelada"
  | "transferida"
  | "concluida";

interface Matricula {
  id: number;
  aluno_id: number;
  turma_id: number;
  ano_letivo: number;
  data_matricula: string;
  situacao: SituacaoMatricula;
  observacoes: string | null;
  data_cadastro: string;
}

interface Aluno {
  id: number;
  nome_completo: string;
  matricula: string;
  status: "ativo" | "inativo" | "transferido";
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

interface MatriculaForm {
  aluno_id: string;
  turma_id: string;
  ano_letivo: string;
  data_matricula: string;
  observacoes: string;
}

const ITENS_POR_PAGINA = 10;

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

function formatarData(data: string) {
  if (!data) return "—";

  const [ano, mes, dia] = data.slice(0, 10).split("-");
  return `${dia}/${mes}/${ano}`;
}

function dataAtual() {
  const hoje = new Date();
  const ano = hoje.getFullYear();
  const mes = String(hoje.getMonth() + 1).padStart(2, "0");
  const dia = String(hoje.getDate()).padStart(2, "0");

  return `${ano}-${mes}-${dia}`;
}

function nomeSituacao(situacao: SituacaoMatricula) {
  const nomes: Record<SituacaoMatricula, string> = {
    ativa: "Ativa",
    cancelada: "Cancelada",
    transferida: "Transferida",
    concluida: "Concluída",
  };

  return nomes[situacao];
}

function classeSituacao(situacao: SituacaoMatricula) {
  return `status-badge status-${situacao}`;
}

export default function MatriculasPage() {
  const { user } = useAuth();

  const permissoes = user?.permissoes ?? [];

  const podeListar = permissoes.includes("matriculas.listar");
  const podeCriar = permissoes.includes("matriculas.criar");
  const podeEditar = permissoes.includes("matriculas.editar");
  const podeCancelar = permissoes.includes("matriculas.cancelar");

  const podeListarAlunos = permissoes.includes("alunos.listar");
  const podeListarTurmas = permissoes.includes("turmas.listar");

  const [matriculas, setMatriculas] = useState<Matricula[]>([]);
  const [alunos, setAlunos] = useState<Aluno[]>([]);
  const [turmas, setTurmas] = useState<Turma[]>([]);

  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");

  const [busca, setBusca] = useState("");
  const [filtroSituacao, setFiltroSituacao] = useState("todas");
  const [filtroAno, setFiltroAno] = useState("todos");
  const [pagina, setPagina] = useState(1);

  const [modalAberto, setModalAberto] = useState(false);
  const [modalDetalhes, setModalDetalhes] = useState(false);
  const [matriculaSelecionada, setMatriculaSelecionada] =
    useState<Matricula | null>(null);

  const [modoEdicao, setModoEdicao] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erroModal, setErroModal] = useState("");

  const [formulario, setFormulario] = useState<MatriculaForm>({
    aluno_id: "",
    turma_id: "",
    ano_letivo: String(new Date().getFullYear()),
    data_matricula: dataAtual(),
    observacoes: "",
  });


const carregarDados = useCallback(async () => {
  setCarregando(true);
  setErro("");

  try {
    const requisicoes: Promise<unknown>[] = [
      api.get("/matriculas/", {
        params: { offset: 0, limit: 100 },
      }),
    ];

    if (podeListarAlunos) {
      requisicoes.push(
        api.get("/alunos/", {
          params: { offset: 0, limit: 100 },
        }),
      );
    }

    if (podeListarTurmas) {
      requisicoes.push(
        api.get("/turmas/", {
          params: { offset: 0, limit: 100 },
        }),
      );
    }

    const resultados = await Promise.all(requisicoes);

    // Matrículas
    const respostaMatriculas = resultados[0] as {
      data: Matricula[];
    };

    setMatriculas(respostaMatriculas.data);

    let indice = 1;

    // Alunos
    if (podeListarAlunos) {
      const respostaAlunos = resultados[indice] as {
        data: Aluno[];
      };

      setAlunos(respostaAlunos.data);

      // Diagnóstico: verifica todos os alunos recebidos da API.
      console.log(
        "TOTAL DE ALUNOS RECEBIDOS:",
        respostaAlunos.data.length,
      );

      console.table(
        respostaAlunos.data.map((aluno) => ({
          id: aluno.id,
          nome: aluno.nome_completo,
          matricula: aluno.matricula,
          status: aluno.status,
        })),
      );

      indice++;
    } else {
      setAlunos([]);
    }

    // Turmas
    if (podeListarTurmas) {
      const respostaTurmas = resultados[indice] as {
        data: Turma[];
      };

      setTurmas(respostaTurmas.data);
    } else {
      setTurmas([]);
    }
  } catch (error) {
    console.error("Erro ao carregar dados das matrículas:", error);
    setErro(getErrorMessage(error));
  } finally {
    setCarregando(false);
  }
}, [podeListarAlunos, podeListarTurmas]);


  useEffect(() => {
    if (podeListar) {
      carregarDados();
    } else {
      setCarregando(false);
    }
  }, [carregarDados, podeListar]);

  const alunosAtivos = useMemo(
    () => alunos.filter((aluno) => aluno.status === "ativo"),
    [alunos],
  );

  const turmasAtivas = useMemo(
    () => turmas.filter((turma) => turma.ativa),
    [turmas],
  );

  const anosDisponiveis = useMemo(
    () =>
      [...new Set(matriculas.map((item) => item.ano_letivo))].sort(
        (a, b) => b - a,
      ),
    [matriculas],
  );

  const matriculasFiltradas = useMemo(() => {
    const termo = busca.trim().toLowerCase();

    return matriculas.filter((item) => {
      const aluno = alunos.find((a) => a.id === item.aluno_id);
      const turma = turmas.find((t) => t.id === item.turma_id);

      const correspondeBusca =
        !termo ||
        aluno?.nome_completo.toLowerCase().includes(termo) ||
        aluno?.matricula.toLowerCase().includes(termo) ||
        turma?.nome.toLowerCase().includes(termo) ||
        String(item.id).includes(termo);

      const correspondeSituacao =
        filtroSituacao === "todas" ||
        item.situacao === filtroSituacao;

      const correspondeAno =
        filtroAno === "todos" ||
        item.ano_letivo === Number(filtroAno);

      return (
        correspondeBusca &&
        correspondeSituacao &&
        correspondeAno
      );
    });
  }, [matriculas, alunos, turmas, busca, filtroSituacao, filtroAno]);

  const totalPaginas = Math.max(
    1,
    Math.ceil(matriculasFiltradas.length / ITENS_POR_PAGINA),
  );

  const matriculasPaginadas = matriculasFiltradas.slice(
    (pagina - 1) * ITENS_POR_PAGINA,
    pagina * ITENS_POR_PAGINA,
  );

  const totalAtivas = matriculas.filter(
    (item) => item.situacao === "ativa",
  ).length;

  const totalCanceladas = matriculas.filter(
    (item) => item.situacao === "cancelada",
  ).length;


  function nomeAluno(alunoId: number) {
    return (
      alunos.find((aluno) => aluno.id === alunoId)?.nome_completo ??
      `Aluno #${alunoId}`
    );
  }

  function nomeTurma(turmaId: number) {
    return (
      turmas.find((turma) => turma.id === turmaId)?.nome ??
      `Turma #${turmaId}`
    );
  }

  function abrirCadastro() {
    setFormulario({
      aluno_id: "",
      turma_id: "",
      ano_letivo: String(new Date().getFullYear()),
      data_matricula: dataAtual(),
      observacoes: "",
    });

    setMatriculaSelecionada(null);
    setModoEdicao(false);
    setErroModal("");
    setModalAberto(true);
  }

  function abrirEdicao(matricula: Matricula) {
    setMatriculaSelecionada(matricula);
    setFormulario({
      aluno_id: String(matricula.aluno_id),
      turma_id: String(matricula.turma_id),
      ano_letivo: String(matricula.ano_letivo),
      data_matricula: matricula.data_matricula,
      observacoes: matricula.observacoes ?? "",
    });

    setModoEdicao(true);
    setErroModal("");
    setModalDetalhes(false);
    setModalAberto(true);
  }

  function abrirDetalhes(matricula: Matricula) {
    setMatriculaSelecionada(matricula);
    setModalDetalhes(true);
  }

  function atualizarCampo(
    campo: keyof MatriculaForm,
    valor: string,
  ) {
    setFormulario((anterior) => ({
      ...anterior,
      [campo]: valor,
    }));
  }

  function selecionarTurma(turmaId: string) {
    const turma = turmasAtivas.find(
      (item) => item.id === Number(turmaId),
    );

    setFormulario((anterior) => ({
      ...anterior,
      turma_id: turmaId,
      ano_letivo: turma
        ? String(turma.ano_letivo)
        : anterior.ano_letivo,
    }));
  }

  async function salvarMatricula(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErroModal("");
    setSalvando(true);

    try {
      if (modoEdicao && matriculaSelecionada) {
        await api.put(`/matriculas/${matriculaSelecionada.id}`, {
          observacoes: formulario.observacoes.trim() || null,
        });

        setSucesso("Matrícula atualizada com sucesso.");
      } else {
        await api.post("/matriculas/", {
          aluno_id: Number(formulario.aluno_id),
          turma_id: Number(formulario.turma_id),
          ano_letivo: Number(formulario.ano_letivo),
          data_matricula: formulario.data_matricula,
          observacoes: formulario.observacoes.trim() || null,
        });

        setSucesso("Matrícula cadastrada com sucesso.");
      }

      setModalAberto(false);
      await carregarDados();
    } catch (error) {
      setErroModal(getErrorMessage(error));
    } finally {
      setSalvando(false);
    }
  }

  async function alterarSituacao(
    matricula: Matricula,
    situacao: SituacaoMatricula,
  ) {
    const confirmacao =
      situacao === "cancelada"
        ? "Deseja realmente cancelar esta matrícula?"
        : `Deseja alterar a situação desta matrícula para "${nomeSituacao(situacao)}"?`;

    if (!window.confirm(confirmacao)) return;

    setErro("");
    setSucesso("");

    try {
      await api.put(`/matriculas/${matricula.id}`, {
        situacao,
      });

      setSucesso(
        `Matrícula ${nomeSituacao(situacao).toLowerCase()} com sucesso.`,
      );

      setModalDetalhes(false);
      await carregarDados();
    } catch (error) {
      setErro(getErrorMessage(error));
    }
  }

  if (!podeListar) {
    return (
      <div className="page-stack">
        <div className="students-alert error-alert">
          Você não possui permissão para visualizar as matrículas.
        </div>
      </div>
    );
  }

  return (
    <div className="page-stack">
      <div className="page-heading">
        <div>
          <span className="eyebrow">GESTÃO ACADÊMICA</span>
          <h1>Matrículas</h1>
          <p className="muted">
            Gerencie as matrículas e acompanhe a situação dos alunos.
          </p>
        </div>

        <div className="students-heading">
          <button
            type="button"
            className="students-add"
            onClick={carregarDados}
            disabled={carregando}
            title="Atualizar dados"
          >
            <RefreshCw size={17} />
          </button>

          {podeCriar && (
            <button
              type="button"
              className="students-add"
              onClick={abrirCadastro}
            >
              <Plus size={18} />
              Nova matrícula
            </button>
          )}
        </div>
      </div>

      {erro && (
        <div className="students-alert error-alert">
          {erro}
        </div>
      )}

      {sucesso && (
        <div className="students-alert success-alert">
          {sucesso}
          <button
            type="button"
            onClick={() => setSucesso("")}
            aria-label="Fechar mensagem"
          >
            <X size={16} />
          </button>
        </div>
      )}

      <div className="students-stats">
        <div className="students-stat">
          <div className="students-stat-icon">
            <ClipboardList size={21} />
          </div>
          <div>
            <span className="muted">Total de matrículas</span>
            <strong>{matriculas.length}</strong>
          </div>
        </div>

        <div className="students-stat">
          <div className="students-stat-icon active-stat-icon">
            <CheckCircle2 size={21} />
          </div>
          <div>
            <span className="muted">Matrículas ativas</span>
            <strong>{totalAtivas}</strong>
          </div>
        </div>

        <div className="students-stat">
          <div className="students-stat-icon inactive-stat-icon">
            <XCircle size={21} />
          </div>
          <div>
            <span className="muted">Canceladas</span>
            <strong>{totalCanceladas}</strong>
          </div>
        </div>
      </div>

      <div className="students-table-card">
        <div className="students-toolbar">
          <div className="students-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Buscar aluno, turma ou matrícula..."
              value={busca}
              onChange={(event) => {
                setBusca(event.target.value);
                setPagina(1);
              }}
            />
          </div>

          <select
            value={filtroAno}
            onChange={(event) => {
              setFiltroAno(event.target.value);
              setPagina(1);
            }}
            aria-label="Filtrar por ano letivo"
          >
            <option value="todos">Todos os anos</option>
            {anosDisponiveis.map((ano) => (
              <option key={ano} value={ano}>
                {ano}
              </option>
            ))}
          </select>

          <select
            value={filtroSituacao}
            onChange={(event) => {
              setFiltroSituacao(event.target.value);
              setPagina(1);
            }}
            aria-label="Filtrar por situação"
          >
            <option value="todas">Todas as situações</option>
            <option value="ativa">Ativas</option>
            <option value="cancelada">Canceladas</option>
            <option value="transferida">Transferidas</option>
            <option value="concluida">Concluídas</option>
          </select>
        </div>

        {carregando ? (
          <div className="students-loading">
            Carregando matrículas...
          </div>
        ) : matriculasPaginadas.length === 0 ? (
          <div className="students-empty">
            <GraduationCap size={34} />
            <strong>Nenhuma matrícula encontrada</strong>
            <span>
              Não há matrículas correspondentes aos filtros selecionados.
            </span>
          </div>
        ) : (
          <>
            <div className="students-table-wrapper">
              <table className="students-table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Aluno</th>
                    <th>Turma</th>
                    <th>Ano letivo</th>
                    <th>Data</th>
                    <th>Situação</th>
                    <th>Ações</th>
                  </tr>
                </thead>

                <tbody>
                  {matriculasPaginadas.map((matricula) => (
                    <tr key={matricula.id}>
                      <td>#{matricula.id}</td>

                      <td>
                        <div className="student-name-cell">
                          <div className="student-avatar">
                            <GraduationCap size={17} />
                          </div>
                          <span>{nomeAluno(matricula.aluno_id)}</span>
                        </div>
                      </td>

                      <td>{nomeTurma(matricula.turma_id)}</td>
                      <td>{matricula.ano_letivo}</td>
                      <td>{formatarData(matricula.data_matricula)}</td>

                      <td>
                        <span className={classeSituacao(matricula.situacao)}>
                          {nomeSituacao(matricula.situacao)}
                        </span>
                      </td>

                      <td>
                        <div className="student-actions">
                          <button
                            type="button"
                            className="icon-button"
                            title="Visualizar matrícula"
                            onClick={() => abrirDetalhes(matricula)}
                          >
                            <Eye size={17} />
                          </button>

                          {podeEditar && (
                            <button
                              type="button"
                              className="icon-button"
                              title="Editar observações"
                              onClick={() => abrirEdicao(matricula)}
                            >
                              <Pencil size={17} />
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
                Exibindo {matriculasPaginadas.length} de{" "}
                {matriculasFiltradas.length} matrícula(s)
              </span>

              <div>
                <button
                  type="button"
                  className="icon-button"
                  disabled={pagina <= 1}
                  onClick={() => setPagina((anterior) => anterior - 1)}
                  aria-label="Página anterior"
                >
                  <ChevronLeft size={18} />
                </button>

                <span>
                  Página {pagina} de {totalPaginas}
                </span>

                <button
                  type="button"
                  className="icon-button"
                  disabled={pagina >= totalPaginas}
                  onClick={() => setPagina((anterior) => anterior + 1)}
                  aria-label="Próxima página"
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {modalAberto && (
        <div
          className="students-modal-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setModalAberto(false);
            }
          }}
        >
          <div className="students-modal">
            <div className="students-modal-header">
              <div>
                <h2>
                  {modoEdicao ? "Editar matrícula" : "Nova matrícula"}
                </h2>
                <p className="muted">
                  {modoEdicao
                    ? "Atualize as observações da matrícula."
                    : "Preencha os dados para registrar uma matrícula."}
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() => setModalAberto(false)}
                aria-label="Fechar"
              >
                <X size={19} />
              </button>
            </div>

            <form onSubmit={salvarMatricula}>
              {erroModal && (
                <div className="students-alert error-alert">
                  {erroModal}
                </div>
              )}

              {modoEdicao ? (
                <div className="student-details">
                  <div className="student-details-grid">
                    <div className="student-detail-item">
                      <span>Aluno</span>
                      <strong>
                        {matriculaSelecionada
                          ? nomeAluno(matriculaSelecionada.aluno_id)
                          : "—"}
                      </strong>
                    </div>

                    <div className="student-detail-item">
                      <span>Turma</span>
                      <strong>
                        {matriculaSelecionada
                          ? nomeTurma(matriculaSelecionada.turma_id)
                          : "—"}
                      </strong>
                    </div>

                    <div className="student-detail-item">
                      <span>Ano letivo</span>
                      <strong>
                        {matriculaSelecionada?.ano_letivo}
                      </strong>
                    </div>

                    <div className="student-detail-item">
                      <span>Situação atual</span>
                      <strong>
                        {matriculaSelecionada
                          ? nomeSituacao(matriculaSelecionada.situacao)
                          : "—"}
                      </strong>
                    </div>
                  </div>
                </div>
              ) : (
                <>
                  {!podeListarAlunos || !podeListarTurmas ? (
                    <div className="students-alert error-alert">
                      Para cadastrar uma matrícula, você precisa ter
                      permissão para listar alunos e turmas.
                    </div>
                  ) : (
                    <div className="students-form-grid">
                      <div className="students-field field-full">
                        <label htmlFor="matricula-aluno">Aluno *</label>
                        <select
                          id="matricula-aluno"
                          required
                          value={formulario.aluno_id}
                          onChange={(event) =>
                            atualizarCampo("aluno_id", event.target.value)
                          }
                        >
                          <option value="">Selecione um aluno</option>
                          {alunosAtivos.map((aluno) => (
                            <option key={aluno.id} value={aluno.id}>
                                {aluno.nome_completo} — {aluno.matricula}
                            </option>
                            ))}
                        </select>

                        {alunosAtivos.length === 0 && (
                          <small className="muted">
                            Nenhum aluno ativo disponível.
                          </small>
                        )}
                      </div>

                      <div className="students-field field-full">
                        <label htmlFor="matricula-turma">Turma *</label>
                        <select
                          id="matricula-turma"
                          required
                          value={formulario.turma_id}
                          onChange={(event) =>
                            selecionarTurma(event.target.value)
                          }
                        >
                          <option value="">Selecione uma turma</option>
                          {turmasAtivas.map((turma) => (
                            <option key={turma.id} value={turma.id}>
                              {turma.nome} — {turma.serie} / {turma.turno}
                              {" "}({turma.ano_letivo})
                            </option>
                          ))}
                        </select>

                        {turmasAtivas.length === 0 && (
                          <small className="muted">
                            Nenhuma turma ativa disponível.
                          </small>
                        )}
                      </div>

                      <div className="students-field">
                        <label htmlFor="matricula-ano">Ano letivo *</label>
                        <input
                          id="matricula-ano"
                          type="number"
                          min="2000"
                          max="2100"
                          required
                          value={formulario.ano_letivo}
                          readOnly={Boolean(formulario.turma_id)}
                          onChange={(event) =>
                            atualizarCampo("ano_letivo", event.target.value)
                          }
                        />
                      </div>

                      <div className="students-field">
                        <label htmlFor="matricula-data">
                          Data da matrícula *
                        </label>
                        <input
                          id="matricula-data"
                          type="date"
                          required
                          value={formulario.data_matricula}
                          onChange={(event) =>
                            atualizarCampo(
                              "data_matricula",
                              event.target.value,
                            )
                          }
                        />
                      </div>
                    </div>
                  )}
                </>
              )}

              <div className="students-field field-full">
                <label htmlFor="matricula-observacoes">Observações</label>
                <textarea
                  id="matricula-observacoes"
                  rows={3}
                  maxLength={2000}
                  placeholder="Informações adicionais sobre a matrícula..."
                  value={formulario.observacoes}
                  onChange={(event) =>
                    atualizarCampo("observacoes", event.target.value)
                  }
                />
              </div>

              <div className="students-modal-footer">
                <button
                  type="button"
                  className="students-cancel"
                  onClick={() => setModalAberto(false)}
                  disabled={salvando}
                >
                  Fechar
                </button>

                <button
                  type="submit"
                  className="students-add"
                  disabled={
                    salvando ||
                    (!modoEdicao &&
                      (!podeListarAlunos ||
                        !podeListarTurmas ||
                        !formulario.aluno_id ||
                        !formulario.turma_id))
                  }
                >
                  {salvando
                    ? "Salvando..."
                    : modoEdicao
                      ? "Salvar alterações"
                      : "Cadastrar matrícula"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {modalDetalhes && matriculaSelecionada && (
        <div
          className="students-modal-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setModalDetalhes(false);
            }
          }}
        >
          <div className="students-modal">
            <div className="students-modal-header">
              <div>
                <span className="eyebrow">REGISTRO #{matriculaSelecionada.id}</span>
                <h2>Detalhes da matrícula</h2>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={() => setModalDetalhes(false)}
                aria-label="Fechar"
              >
                <X size={19} />
              </button>
            </div>

            <div className="student-details">
              <div className="student-details-heading">
                <GraduationCap size={22} />
                <strong>Informações acadêmicas</strong>
              </div>

              <div className="student-details-grid">
                <div className="student-detail-item">
                  <span>Aluno</span>
                  <strong>{nomeAluno(matriculaSelecionada.aluno_id)}</strong>
                </div>

                <div className="student-detail-item">
                  <span>Turma</span>
                  <strong>{nomeTurma(matriculaSelecionada.turma_id)}</strong>
                </div>

                <div className="student-detail-item">
                  <span>Ano letivo</span>
                  <strong>{matriculaSelecionada.ano_letivo}</strong>
                </div>

                <div className="student-detail-item">
                  <span>Data da matrícula</span>
                  <strong>
                    {formatarData(matriculaSelecionada.data_matricula)}
                  </strong>
                </div>

                <div className="student-detail-item">
                  <span>Situação</span>
                  <strong>
                    <span className={classeSituacao(matriculaSelecionada.situacao)}>
                      {nomeSituacao(matriculaSelecionada.situacao)}
                    </span>
                  </strong>
                </div>

                <div className="student-detail-item">
                  <span>Data do cadastro</span>
                  <strong>
                    {formatarData(matriculaSelecionada.data_cadastro)}
                  </strong>
                </div>

                <div className="student-detail-item field-full">
                  <span>Observações</span>
                  <strong>
                    {matriculaSelecionada.observacoes || "Nenhuma observação."}
                  </strong>
                </div>
              </div>
            </div>

            <div className="students-modal-footer">
              <button
                type="button"
                className="students-cancel"
                onClick={() => setModalDetalhes(false)}
              >
                Fechar
              </button>

              {podeEditar && (
                <button
                  type="button"
                  className="students-add"
                  onClick={() => abrirEdicao(matriculaSelecionada)}
                >
                  <Pencil size={16} />
                  Editar
                </button>
              )}
            </div>

            {(matriculaSelecionada.situacao === "ativa" &&
              podeCancelar) && (
              <div className="students-modal-footer">
                <button
                  type="button"
                  className="students-cancel"
                  onClick={() =>
                    alterarSituacao(matriculaSelecionada, "cancelada")
                  }
                >
                  <XCircle size={16} />
                  Cancelar matrícula
                </button>
              </div>
            )}

            {matriculaSelecionada.situacao === "ativa" && podeEditar && (
              <div className="students-modal-footer">
                <button
                  type="button"
                  className="students-cancel"
                  onClick={() =>
                    alterarSituacao(matriculaSelecionada, "transferida")
                  }
                >
                  <ArrowLeftRight size={16} />
                  Registrar transferência
                </button>

                <button
                  type="button"
                  className="students-cancel"
                  onClick={() =>
                    alterarSituacao(matriculaSelecionada, "concluida")
                  }
                >
                  <CheckCircle2 size={16} />
                  Concluir matrícula
                </button>
              </div>
            )}

            {matriculaSelecionada.situacao !== "ativa" && podeEditar && (
              <div className="students-modal-footer">
                <button
                  type="button"
                  className="students-add"
                  onClick={() =>
                    alterarSituacao(matriculaSelecionada, "ativa")
                  }
                >
                  <RefreshCw size={16} />
                  Reativar matrícula
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
