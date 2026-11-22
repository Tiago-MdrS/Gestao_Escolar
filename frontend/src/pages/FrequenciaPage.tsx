
import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  RefreshCw,
  Search,
  Save,
  XCircle,
} from "lucide-react";
import { api } from "../services/api";
import { useAuth } from "../auth/AuthContext";

type SituacaoFrequencia =
  | "presente"
  | "falta"
  | "falta_justificada";

interface Horario {
  id: number;
  turma_id: number;
  turma_nome: string;
  ano_letivo: number;
  disciplina_nome: string;
  professor_nome: string;
  dia_semana: number;
  hora_inicio: string;
  hora_fim: string;
  sala: string | null;
  ativo: boolean;
}

interface Frequencia {
  id: number;
  aluno_id: number;
  nome_completo: string;
  horario_id: number;
  data_aula: string;
  situacao: SituacaoFrequencia;
  observacao: string | null;
  registrado_por_id: number;
  data_registro: string;
}

interface AlunoChamada {
  aluno_id: number;
  nome_completo: string;
  frequencia_id: number | null;
  situacao: SituacaoFrequencia | null;
  observacao: string | null;
}

interface AlunoChamadaForm extends Omit<AlunoChamada, "situacao"> {
  situacao: SituacaoFrequencia | "";
}

interface FrequenciaForm {
  situacao: SituacaoFrequencia;
  observacao: string;
}

const PAGE_SIZE = 10;

function dataAtual() {
  const hoje = new Date();
  const ano = hoje.getFullYear();
  const mes = String(hoje.getMonth() + 1).padStart(2, "0");
  const dia = String(hoje.getDate()).padStart(2, "0");

  return `${ano}-${mes}-${dia}`;
}

function formatarData(data: string) {
  if (!data) return "—";

  const [ano, mes, dia] = data.slice(0, 10).split("-");
  return `${dia}/${mes}/${ano}`;
}

function formatarHora(hora: string) {
  return hora?.slice(0, 5) ?? "";
}

function nomeSituacao(situacao: SituacaoFrequencia) {
  const nomes: Record<SituacaoFrequencia, string> = {
    presente: "Presente",
    falta: "Falta",
    falta_justificada: "Falta justificada",
  };

  return nomes[situacao];
}

function classeSituacao(situacao: SituacaoFrequencia) {
  return `frequency-status frequency-status-${situacao}`;
}

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") return detail;

    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg ?? "Erro de validação").join(" | ");
    }

    if (error.response?.status === 403) {
      return "Você não possui permissão para realizar esta operação.";
    }

    if (error.response?.status === 404) {
      return "O registro solicitado não foi encontrado.";
    }

    if (error.response?.status === 409) {
      return "Este registro já existe ou existe um conflito nos dados.";
    }

    if (!error.response) {
      return "Não foi possível conectar ao servidor.";
    }
  }

  return "Ocorreu um erro inesperado. Tente novamente.";
}

function normalizarTexto(valor: string) {
  return valor
    .toLocaleLowerCase("pt-BR")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

export default function FrequenciaPage() {
  const { user } = useAuth();
  const permissoes = user?.permissoes ?? [];

  const podeListar = permissoes.includes("frequencia.listar");
  const podeConsultarPropria = permissoes.includes(
    "frequencia.consultar_propria",
  );
  const podeRegistrar = permissoes.includes("frequencia.registrar");
  const podeEditar = permissoes.includes("frequencia.editar");

  const podeConsultar = podeListar || podeConsultarPropria;

  const podeListarHorarios = permissoes.includes("horarios.listar");
  const podeConsultarHorariosProprios = permissoes.includes(
    "horarios.consultar_proprios",
  );

  const podeConsultarHorarios =
    podeListarHorarios || podeConsultarHorariosProprios;

  const [horarios, setHorarios] = useState<Horario[]>([]);
  const [frequencias, setFrequencias] = useState<Frequencia[]>([]);

  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");
  const [sucesso, setSucesso] = useState("");

  const [abaAtiva, setAbaAtiva] = useState<"chamada" | "historico">(
    podeRegistrar ? "chamada" : "historico",
  );

  // Dados da chamada
  const [dataAula, setDataAula] = useState(dataAtual());
  const [horarioId, setHorarioId] = useState("");
  const [alunos, setAlunos] = useState<AlunoChamadaForm[]>([]);
  const [carregandoChamada, setCarregandoChamada] = useState(false);
  const [buscaAluno, setBuscaAluno] = useState("");

  // Filtros do histórico
  const [buscaHistorico, setBuscaHistorico] = useState("");
  const [filtroTurma, setFiltroTurma] = useState("todas");
  const [filtroSituacao, setFiltroSituacao] = useState("todas");
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [pagina, setPagina] = useState(1);

  // Edição do histórico
  const [edicoes, setEdicoes] = useState<Record<number, FrequenciaForm>>({});
  const [salvandoEdicao, setSalvandoEdicao] = useState<number | null>(null);

  const carregarDados = useCallback(async () => {
    setCarregando(true);
    setErro("");

    const requisicoes = await Promise.allSettled([
      podeConsultarHorarios
        ? api.get<Horario[]>(
            podeListarHorarios ? "/horarios/" : "/horarios/meus",
            {
              params: podeListarHorarios
                ? { offset: 0, limit: 500 }
                : undefined,
            },
          )
        : Promise.resolve(null),

      podeConsultar
        ? api.get<Frequencia[]>(
            podeListar ? "/frequencias/" : "/frequencias/minhas",
            { params: { offset: 0, limit: 500 } },
          )
        : Promise.resolve(null),
    ]);

    if (requisicoes[0].status === "fulfilled" && requisicoes[0].value) {
      setHorarios(requisicoes[0].value.data);
    } else if (podeConsultarHorarios) {
      setErro("Não foi possível carregar os horários.");
    }

    if (requisicoes[1].status === "fulfilled" && requisicoes[1].value) {
      setFrequencias(requisicoes[1].value.data);
    } else if (podeConsultar) {
      setErro("Não foi possível carregar o histórico de frequências.");
    }

    setCarregando(false);
  }, [
    podeConsultarHorarios,
    podeListarHorarios,
    podeConsultar,
    podeListar,
  ]);

  useEffect(() => {
    void carregarDados();
  }, [carregarDados]);

  const horariosAtivos = useMemo(
    () => horarios.filter((horario) => horario.ativo),
    [horarios],
  );

  const horarioSelecionado = horarios.find(
    (horario) => horario.id === Number(horarioId),
  );

  const horariosDaData = useMemo(() => {
    if (!dataAula) return [];

    const data = new Date(`${dataAula}T12:00:00`);
    const diaSemana = (data.getDay() + 6) % 7;

    return horariosAtivos.filter(
      (horario) => horario.dia_semana === diaSemana,
    );
  }, [horariosAtivos, dataAula]);

  const alunosFiltrados = useMemo(() => {
    const busca = normalizarTexto(buscaAluno);

    return alunos.filter((aluno) =>
      normalizarTexto(aluno.nome_completo).includes(busca),
    );
  }, [alunos, buscaAluno]);

  const historicoFiltrado = useMemo(() => {
    const busca = normalizarTexto(buscaHistorico);

    return frequencias.filter((frequencia) => {
      const horario = horarios.find(
        (item) => item.id === frequencia.horario_id,
      );

      const correspondeBusca =
        !busca ||
        normalizarTexto(
          [
            frequencia.nome_completo,
            horario?.turma_nome ?? "",
            horario?.disciplina_nome ?? "",
            horario?.professor_nome ?? "",
          ].join(" "),
        ).includes(busca);

      const correspondeTurma =
        filtroTurma === "todas" ||
        horario?.turma_id === Number(filtroTurma);

      const correspondeSituacao =
        filtroSituacao === "todas" ||
        frequencia.situacao === filtroSituacao;

      const correspondeInicio =
        !dataInicio || frequencia.data_aula >= dataInicio;

      const correspondeFim =
        !dataFim || frequencia.data_aula <= dataFim;

      return (
        correspondeBusca &&
        correspondeTurma &&
        correspondeSituacao &&
        correspondeInicio &&
        correspondeFim
      );
    });
  }, [
    frequencias,
    horarios,
    buscaHistorico,
    filtroTurma,
    filtroSituacao,
    dataInicio,
    dataFim,
  ]);

  const totalPresentes = frequencias.filter(
    (item) => item.situacao === "presente",
  ).length;

  const totalFaltas = frequencias.filter(
    (item) => item.situacao === "falta",
  ).length;

  const totalJustificadas = frequencias.filter(
    (item) => item.situacao === "falta_justificada",
  ).length;

  const totalPaginas = Math.max(
    1,
    Math.ceil(historicoFiltrado.length / PAGE_SIZE),
  );

  const historicoPaginado = historicoFiltrado.slice(
    (pagina - 1) * PAGE_SIZE,
    pagina * PAGE_SIZE,
  );

  useEffect(() => {
    setPagina(1);
  }, [buscaHistorico, filtroTurma, filtroSituacao, dataInicio, dataFim]);

  useEffect(() => {
    if (
      horarioId &&
      !horariosDaData.some((horario) => horario.id === Number(horarioId))
    ) {
      setHorarioId("");
      setAlunos([]);
    }
  }, [horariosDaData, horarioId]);

  const carregarChamada = async () => {
    if (!horarioId || !dataAula) {
      setErro("Selecione a data e o horário da aula.");
      return;
    }

    if (dataAula > dataAtual()) {
      setErro("Não é possível realizar chamada em uma data futura.");
      return;
    }

    setCarregandoChamada(true);
    setErro("");
    setSucesso("");
    setAlunos([]);

    try {
      const resposta = await api.get<AlunoChamada[]>(
        "/frequencias/chamada",
        {
          params: {
            horario_id: Number(horarioId),
            data_aula: dataAula,
          },
        },
      );

      setAlunos(
        resposta.data.map((aluno) => ({
          ...aluno,
          situacao: aluno.situacao ?? "",
        })),
      );

      if (resposta.data.length === 0) {
        setSucesso("Não há alunos com matrícula ativa para esta chamada.");
      }
    } catch (error) {
      setErro(getErrorMessage(error));
    } finally {
      setCarregandoChamada(false);
    }
  };

  const alterarSituacaoAluno = (
    alunoId: number,
    situacao: SituacaoFrequencia | "",
  ) => {
    setAlunos((atuais) =>
      atuais.map((aluno) =>
        aluno.aluno_id === alunoId ? { ...aluno, situacao } : aluno,
      ),
    );
  };

  const alterarObservacaoAluno = (alunoId: number, observacao: string) => {
    setAlunos((atuais) =>
      atuais.map((aluno) =>
        aluno.aluno_id === alunoId ? { ...aluno, observacao } : aluno,
      ),
    );
  };

  const marcarTodos = (situacao: SituacaoFrequencia) => {
    setAlunos((atuais) =>
      atuais.map((aluno) => ({ ...aluno, situacao })),
    );
  };

  const salvarChamada = async () => {
    if (!horarioId || !dataAula || alunos.length === 0) return;

    const pendentes = alunos.filter((aluno) => !aluno.situacao);

    if (pendentes.length > 0) {
      setErro(
        `Ainda existem ${pendentes.length} aluno(s) sem situação definida.`,
      );
      return;
    }

    const alterados = alunos.filter((aluno) => {
      if (!aluno.frequencia_id) return true;

      const original = frequencias.find(
        (item) => item.id === aluno.frequencia_id,
      );

      return (
        original?.situacao !== aluno.situacao ||
        (original?.observacao ?? "") !== (aluno.observacao ?? "")
      );
    });

    if (alterados.some((aluno) => aluno.frequencia_id) && !podeEditar) {
      setErro(
        "Existem registros já lançados que foram alterados. Você não possui permissão para editá-los.",
      );
      return;
    }

    if (alterados.length === 0) {
      setSucesso("A chamada já está salva e não possui alterações.");
      return;
    }

    setSalvando(true);
    setErro("");
    setSucesso("");

    let salvos = 0;
    let falhas = 0;

    for (const aluno of alterados) {
      try {
        if (aluno.frequencia_id) {
          await api.put(`/frequencias/${aluno.frequencia_id}`, {
            situacao: aluno.situacao,
            observacao: aluno.observacao || null,
          });
        } else {
          await api.post("/frequencias/", {
            aluno_id: aluno.aluno_id,
            horario_id: Number(horarioId),
            data_aula: dataAula,
            situacao: aluno.situacao,
            observacao: aluno.observacao || null,
          });
        }

        salvos++;
      } catch {
        falhas++;
      }
    }

    await carregarDados();
    await carregarChamada();

    if (falhas > 0) {
      setErro(
        `${salvos} registro(s) salvo(s) e ${falhas} não puderam ser salvos. Confira as permissões e os dados.`,
      );
    } else {
      setSucesso(`${salvos} registro(s) de frequência salvo(s) com sucesso.`);
    }

    setSalvando(false);
  };

  const iniciarEdicao = (frequencia: Frequencia) => {
    setEdicoes((atuais) => ({
      ...atuais,
      [frequencia.id]: {
        situacao: frequencia.situacao,
        observacao: frequencia.observacao ?? "",
      },
    }));
  };

  const alterarEdicao = (
    frequenciaId: number,
    campo: keyof FrequenciaForm,
    valor: string,
  ) => {
    setEdicoes((atuais) => ({
      ...atuais,
      [frequenciaId]: {
        ...atuais[frequenciaId],
        [campo]: valor,
      },
    }));
  };

  const salvarEdicao = async (frequenciaId: number) => {
    const edicao = edicoes[frequenciaId];
    if (!edicao) return;

    setSalvandoEdicao(frequenciaId);
    setErro("");
    setSucesso("");

    try {
      await api.put(`/frequencias/${frequenciaId}`, {
        situacao: edicao.situacao,
        observacao: edicao.observacao || null,
      });

      setEdicoes((atuais) => {
        const novas = { ...atuais };
        delete novas[frequenciaId];
        return novas;
      });

      await carregarDados();
      setSucesso("Registro de frequência atualizado com sucesso.");
    } catch (error) {
      setErro(getErrorMessage(error));
    } finally {
      setSalvandoEdicao(null);
    }
  };

  if (!podeRegistrar && !podeConsultar) {
    return (
      <div className="frequency-access-denied">
        <ClipboardCheck size={42} />
        <h2>Acesso não autorizado</h2>
        <p>Você não possui permissão para acessar as frequências.</p>
      </div>
    );
  }

  const mostrarChamada = podeRegistrar;
  const mostrarHistorico = podeConsultar;

  return (
    <div className="frequency-page">
      <div className="frequency-heading">
        <div>
          <span className="frequency-eyebrow">GESTÃO ACADÊMICA</span>
          <h2>Frequência escolar</h2>
          <p>
            Registre a presença dos alunos e acompanhe o histórico de
            frequência das aulas.
          </p>
        </div>

        <button
          className="frequency-refresh-button"
          onClick={() => void carregarDados()}
          disabled={carregando}
        >
          <RefreshCw size={16} />
          Atualizar
        </button>
      </div>

      {erro && (
        <div className="frequency-alert frequency-alert-error">
          <XCircle size={18} />
          <span>{erro}</span>
        </div>
      )}

      {sucesso && (
        <div className="frequency-alert frequency-alert-success">
          <CheckCircle2 size={18} />
          <span>{sucesso}</span>
        </div>
      )}

      {mostrarHistorico && (
        <div className="frequency-stats">
          <div className="frequency-stat">
            <div className="frequency-stat-icon frequency-icon-total">
              <ClipboardCheck size={20} />
            </div>
            <div>
              <span>Registros realizados</span>
              <strong>{frequencias.length}</strong>
            </div>
          </div>

          <div className="frequency-stat">
            <div className="frequency-stat-icon frequency-icon-present">
              <CheckCircle2 size={20} />
            </div>
            <div>
              <span>Presenças</span>
              <strong>{totalPresentes}</strong>
            </div>
          </div>

          <div className="frequency-stat">
            <div className="frequency-stat-icon frequency-icon-absent">
              <XCircle size={20} />
            </div>
            <div>
              <span>Faltas</span>
              <strong>{totalFaltas}</strong>
            </div>
          </div>

          <div className="frequency-stat">
            <div className="frequency-stat-icon frequency-icon-justified">
              <CalendarDays size={20} />
            </div>
            <div>
              <span>Faltas justificadas</span>
              <strong>{totalJustificadas}</strong>
            </div>
          </div>
        </div>
      )}

      {mostrarChamada && mostrarHistorico && (
        <div className="frequency-tabs">
          <button
            className={abaAtiva === "chamada" ? "active" : ""}
            onClick={() => {
              setAbaAtiva("chamada");
              setErro("");
              setSucesso("");
            }}
          >
            <ClipboardCheck size={17} />
            Realizar chamada
          </button>

          <button
            className={abaAtiva === "historico" ? "active" : ""}
            onClick={() => {
              setAbaAtiva("historico");
              setErro("");
              setSucesso("");
            }}
          >
            <CalendarDays size={17} />
            Histórico
          </button>
        </div>
      )}

      {mostrarChamada && (!mostrarHistorico || abaAtiva === "chamada") && (
        <section className="frequency-panel">
          <div className="frequency-panel-header">
            <div>
              <h3>Realizar chamada</h3>
              <p>Selecione uma aula para carregar os alunos matriculados.</p>
            </div>
            <ClipboardCheck size={23} />
          </div>

          {!podeConsultarHorarios && (
            <div className="frequency-empty">
              Você não possui permissão para consultar os horários das aulas.
            </div>
          )}

          {podeConsultarHorarios && (
            <>
              <div className="frequency-call-filters">
                <label className="frequency-field">
                  Data da aula
                  <input
                    type="date"
                    value={dataAula}
                    max={dataAtual()}
                    onChange={(event) => {
                      setDataAula(event.target.value);
                      setHorarioId("");
                      setAlunos([]);
                      setErro("");
                      setSucesso("");
                    }}
                  />
                </label>

                <label className="frequency-field">
                  Horário / disciplina
                  <select
                    value={horarioId}
                    onChange={(event) => {
                      setHorarioId(event.target.value);
                      setAlunos([]);
                      setErro("");
                      setSucesso("");
                    }}
                  >
                    <option value="">Selecione o horário</option>
                    {horariosDaData.map((horario) => (
                      <option key={horario.id} value={horario.id}>
                        {horario.turma_nome} — {horario.disciplina_nome} (
                        {formatarHora(horario.hora_inicio)} às{" "}
                        {formatarHora(horario.hora_fim)})
                      </option>
                    ))}
                  </select>
                </label>

                <button
                  className="frequency-primary-button"
                  onClick={() => void carregarChamada()}
                  disabled={!horarioId || carregandoChamada}
                >
                  <Search size={16} />
                  {carregandoChamada ? "Carregando..." : "Carregar alunos"}
                </button>
              </div>

              {horarioSelecionado && (
                <div className="frequency-class-info">
                  <div>
                    <span>Turma</span>
                    <strong>{horarioSelecionado.turma_nome}</strong>
                  </div>
                  <div>
                    <span>Disciplina</span>
                    <strong>{horarioSelecionado.disciplina_nome}</strong>
                  </div>
                  <div>
                    <span>Professor</span>
                    <strong>{horarioSelecionado.professor_nome}</strong>
                  </div>
                  <div>
                    <span>Horário</span>
                    <strong>
                      {formatarHora(horarioSelecionado.hora_inicio)} às{" "}
                      {formatarHora(horarioSelecionado.hora_fim)}
                    </strong>
                  </div>
                  <div>
                    <span>Sala</span>
                    <strong>{horarioSelecionado.sala || "Não informada"}</strong>
                  </div>
                </div>
              )}

              {alunos.length > 0 && (
                <>
                  <div className="frequency-list-toolbar">
                    <div>
                      <h4>Alunos da turma</h4>
                      <span>
                        {alunos.length} aluno(s) ·{" "}
                        {alunos.filter((aluno) => aluno.frequencia_id).length}{" "}
                        registro(s) já realizado(s)
                      </span>
                    </div>

                    <div className="frequency-bulk-actions">
                      <button onClick={() => marcarTodos("presente")}>
                        Marcar todos presentes
                      </button>
                      <button onClick={() => marcarTodos("falta")}>
                        Marcar todos ausentes
                      </button>
                    </div>
                  </div>

                  <div className="frequency-search">
                    <Search size={17} />
                    <input
                      value={buscaAluno}
                      onChange={(event) => setBuscaAluno(event.target.value)}
                      placeholder="Buscar aluno..."
                    />
                  </div>

                  <div className="frequency-table-wrapper">
                    <table className="frequency-table">
                      <thead>
                        <tr>
                          <th>Aluno</th>
                          <th>Situação</th>
                          <th>Observação</th>
                          <th>Registro</th>
                        </tr>
                      </thead>
                      <tbody>
                        {alunosFiltrados.map((aluno) => (
                          <tr key={aluno.aluno_id}>
                            <td>
                              <strong>{aluno.nome_completo}</strong>
                            </td>
                            <td>
                              <select
                                className="frequency-situation-select"
                                value={aluno.situacao}
                                onChange={(event) =>
                                  alterarSituacaoAluno(
                                    aluno.aluno_id,
                                    event.target.value as
                                      | SituacaoFrequencia
                                      | "",
                                  )
                                }
                              >
                                <option value="">Selecione</option>
                                <option value="presente">Presente</option>
                                <option value="falta">Falta</option>
                                <option value="falta_justificada">
                                  Falta justificada
                                </option>
                              </select>
                            </td>
                            <td>
                              <input
                                className="frequency-observation-input"
                                value={aluno.observacao ?? ""}
                                onChange={(event) =>
                                  alterarObservacaoAluno(
                                    aluno.aluno_id,
                                    event.target.value,
                                  )
                                }
                                maxLength={2000}
                                placeholder="Observação (opcional)"
                              />
                            </td>
                            <td>
                              {aluno.frequencia_id ? (
                                <span className="frequency-recorded">
                                  <CheckCircle2 size={15} />
                                  Registrado
                                </span>
                              ) : (
                                <span className="frequency-pending">
                                  Pendente
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="frequency-call-footer">
                    <span>
                      {alunos.filter((aluno) => aluno.situacao).length} de{" "}
                      {alunos.length} alunos com situação definida
                    </span>

                    <button
                      className="frequency-primary-button"
                      onClick={() => void salvarChamada()}
                      disabled={salvando || alunos.length === 0}
                    >
                      <Save size={16} />
                      {salvando ? "Salvando chamada..." : "Salvar chamada"}
                    </button>
                  </div>
                </>
              )}

              {!carregandoChamada &&
                horarioId &&
                alunos.length === 0 &&
                sucesso === "" && (
                  <div className="frequency-empty">
                    Clique em “Carregar alunos” para iniciar a chamada.
                  </div>
                )}

              {!carregandoChamada && horariosDaData.length === 0 && (
                <div className="frequency-empty">
                  Não há horários cadastrados para este dia da semana.
                </div>
              )}
            </>
          )}
        </section>
      )}

      {mostrarHistorico && (!mostrarChamada || abaAtiva === "historico") && (
        <section className="frequency-panel">
          <div className="frequency-panel-header">
            <div>
              <h3>Histórico de frequências</h3>
              <p>Consulte e filtre os registros de frequência.</p>
            </div>
            <CalendarDays size={23} />
          </div>

          <div className="frequency-history-filters">
            <label className="frequency-field frequency-search-field">
              Buscar
              <div className="frequency-search">
                <Search size={17} />
                <input
                  value={buscaHistorico}
                  onChange={(event) => setBuscaHistorico(event.target.value)}
                  placeholder="Aluno, turma, disciplina ou professor..."
                />
              </div>
            </label>

            <label className="frequency-field">
              Turma
              <select
                value={filtroTurma}
                onChange={(event) => setFiltroTurma(event.target.value)}
              >
                <option value="todas">Todas as turmas</option>
                {Array.from(
                  new Map(
                    horarios.map((horario) => [
                      horario.turma_id,
                      horario.turma_nome,
                    ]),
                  ),
                ).map(([id, nome]) => (
                  <option key={id} value={id}>
                    {nome}
                  </option>
                ))}
              </select>
            </label>

            <label className="frequency-field">
              Situação
              <select
                value={filtroSituacao}
                onChange={(event) => setFiltroSituacao(event.target.value)}
              >
                <option value="todas">Todas</option>
                <option value="presente">Presente</option>
                <option value="falta">Falta</option>
                <option value="falta_justificada">Falta justificada</option>
              </select>
            </label>

            <label className="frequency-field">
              Data inicial
              <input
                type="date"
                value={dataInicio}
                onChange={(event) => setDataInicio(event.target.value)}
              />
            </label>

            <label className="frequency-field">
              Data final
              <input
                type="date"
                value={dataFim}
                onChange={(event) => setDataFim(event.target.value)}
              />
            </label>
          </div>

          {dataInicio && dataFim && dataInicio > dataFim && (
            <div className="frequency-filter-error">
              A data inicial não pode ser posterior à data final.
            </div>
          )}

          <div className="frequency-table-wrapper">
            <table className="frequency-table">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Aluno</th>
                  <th>Turma / disciplina</th>
                  <th>Situação</th>
                  <th>Observação</th>
                  {podeEditar && <th>Ação</th>}
                </tr>
              </thead>
              <tbody>
                {carregando ? (
                  <tr>
                    <td colSpan={podeEditar ? 6 : 5} className="frequency-table-empty">
                      Carregando registros...
                    </td>
                  </tr>
                ) : historicoPaginado.length === 0 ? (
                  <tr>
                    <td colSpan={podeEditar ? 6 : 5} className="frequency-table-empty">
                      Nenhum registro de frequência encontrado.
                    </td>
                  </tr>
                ) : (
                  historicoPaginado.map((frequencia) => {
                    const horario = horarios.find(
                      (item) => item.id === frequencia.horario_id,
                    );

                    const edicao = edicoes[frequencia.id];

                    return (
                      <tr key={frequencia.id}>
                        <td>{formatarData(frequencia.data_aula)}</td>
                        <td>
                          <strong>{frequencia.nome_completo}</strong>
                        </td>
                        <td>
                          <strong>
                            {horario?.turma_nome ?? "Turma não disponível"}
                          </strong>
                          <small>
                            {horario?.disciplina_nome ??
                              `Horário #${frequencia.horario_id}`}
                          </small>
                        </td>
                        <td>
                          {edicao ? (
                            <select
                              className="frequency-situation-select"
                              value={edicao.situacao}
                              onChange={(event) =>
                                alterarEdicao(
                                  frequencia.id,
                                  "situacao",
                                  event.target.value,
                                )
                              }
                            >
                              <option value="presente">Presente</option>
                              <option value="falta">Falta</option>
                              <option value="falta_justificada">
                                Falta justificada
                              </option>
                            </select>
                          ) : (
                            <span className={classeSituacao(frequencia.situacao)}>
                              {nomeSituacao(frequencia.situacao)}
                            </span>
                          )}
                        </td>
                        <td>
                          {edicao ? (
                            <input
                              className="frequency-observation-input"
                              value={edicao.observacao}
                              onChange={(event) =>
                                alterarEdicao(
                                  frequencia.id,
                                  "observacao",
                                  event.target.value,
                                )
                              }
                              maxLength={2000}
                            />
                          ) : (
                            frequencia.observacao || "—"
                          )}
                        </td>
                        {podeEditar && (
                          <td>
                            {edicao ? (
                              <button
                                className="frequency-save-small"
                                onClick={() => void salvarEdicao(frequencia.id)}
                                disabled={salvandoEdicao === frequencia.id}
                              >
                                <Save size={14} />
                                {salvandoEdicao === frequencia.id
                                  ? "Salvando"
                                  : "Salvar"}
                              </button>
                            ) : (
                              <button
                                className="frequency-edit-small"
                                onClick={() => iniciarEdicao(frequencia)}
                              >
                                Editar
                              </button>
                            )}
                          </td>
                        )}
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <div className="frequency-pagination">
            <span>
              {historicoFiltrado.length} registro(s) encontrado(s)
            </span>

            <div>
              <button
                onClick={() => setPagina((atual) => Math.max(1, atual - 1))}
                disabled={pagina <= 1}
              >
                Anterior
              </button>
              <span>
                Página {pagina} de {totalPaginas}
              </span>
              <button
                onClick={() =>
                  setPagina((atual) => Math.min(totalPaginas, atual + 1))
                }
                disabled={pagina >= totalPaginas}
              >
                Próxima
              </button>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
