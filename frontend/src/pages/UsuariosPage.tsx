
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Search,
  Plus,
  Pencil,
  Eye,
  UserCheck,
  UserX,
  ShieldCheck,
  Users,
  KeyRound,
  X,
  Save,
  RefreshCw,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { api } from "../services/api";

// ==========================================================
// TIPOS
// ==========================================================

interface PerfilResumo {
  id: number;
  nome: string;
}

interface Usuario {
  id: number;
  nome_completo: string;
  email: string;
  perfil_id: number;
  perfil: PerfilResumo;
  professor_id: number | null;
  ativo: boolean;
  ultimo_acesso: string | null;
  data_cadastro: string;
}

interface Perfil {
  id: number;
  nome: string;
  descricao: string | null;
  ativo: boolean;
  data_cadastro: string;
  permissoes: Permissao[];
}

interface Permissao {
  id: number;
  codigo: string;
  nome: string;
  descricao: string | null;
  modulo: string;
  data_cadastro: string;
}

interface Professor {
  id: number;
  nome_completo: string;
  ativo: boolean;
}

type Aba = "usuarios" | "perfis";
type ModalUsuario = "criar" | "editar" | "visualizar" | null;

interface FormUsuario {
  nome_completo: string;
  email: string;
  senha: string;
  perfil_id: string;
  professor_id: string;
}

interface FormPerfil {
  nome: string;
  descricao: string;
  ativo: boolean;
}

const FORM_USUARIO_INICIAL: FormUsuario = {
  nome_completo: "",
  email: "",
  senha: "",
  perfil_id: "",
  professor_id: "",
};

const USUARIOS_POR_PAGINA = 10;
const USUARIOS_POR_REQUISICAO = 100;

// ==========================================================
// UTILITÁRIOS
// ==========================================================

function mensagemErro(error: unknown): string {
  const resposta = (
    error as {
      response?: {
        data?: {
          detail?: string | { msg?: string }[];
        };
      };
    }
  )?.response?.data?.detail;

  if (typeof resposta === "string") {
    return resposta;
  }

  if (Array.isArray(resposta)) {
    return resposta.map((item) => item.msg || "Dados inválidos").join("\n");
  }

  if ((error as { response?: unknown })?.response) {
    return "Não foi possível concluir a operação. Verifique os dados e tente novamente.";
  }

  return "Não foi possível conectar ao servidor.";
}

function formatarData(data: string | null): string {
  if (!data) return "Nunca acessou";

  return new Date(data).toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

// ==========================================================
// COMPONENTE
// ==========================================================

export default function UsuariosPage() {
  const { user } = useAuth();

  const permissoesUsuario = user?.permissoes ?? [];

  const pode = (codigo: string) => permissoesUsuario.includes(codigo);

  const podeListarUsuarios = pode("usuarios.listar");
  const podeListarPerfis = pode("perfis.listar");

  // Abas
  const [aba, setAba] = useState<Aba>("usuarios");

  // Dados
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [perfis, setPerfis] = useState<Perfil[]>([]);
  const [permissoes, setPermissoes] = useState<Permissao[]>([]);
  const [professores, setProfessores] = useState<Professor[]>([]);

  // Carregamento
  const [carregando, setCarregando] = useState(true);
  const [atualizando, setAtualizando] = useState(false);
  const [erro, setErro] = useState("");

  // Filtros
  const [busca, setBusca] = useState("");
  const [filtroStatus, setFiltroStatus] = useState("todos");
  const [filtroPerfil, setFiltroPerfil] = useState("todos");

  // Paginação
  const [paginaAtual, setPaginaAtual] = useState(1);

  // Modal de usuário
  const [modalUsuario, setModalUsuario] = useState<ModalUsuario>(null);
  const [usuarioSelecionado, setUsuarioSelecionado] =
    useState<Usuario | null>(null);
  const [formUsuario, setFormUsuario] = useState<FormUsuario>(
    FORM_USUARIO_INICIAL
  );
  const [salvandoUsuario, setSalvandoUsuario] = useState(false);

  // Modal de perfil
  const [perfilSelecionado, setPerfilSelecionado] = useState<Perfil | null>(
    null
  );
  const [formPerfil, setFormPerfil] = useState<FormPerfil>({
    nome: "",
    descricao: "",
    ativo: true,
  });
  const [permissoesSelecionadas, setPermissoesSelecionadas] = useState<number[]>(
    []
  );
  const [salvandoPerfil, setSalvandoPerfil] = useState(false);

  // ========================================================
  // CARREGAMENTO DOS DADOS
  // ========================================================

  const carregarDados = useCallback(async (silencioso = false) => {
    if (!silencioso) setCarregando(true);
    else setAtualizando(true);

    setErro("");

    try {
      const requisicoes: Promise<void>[] = [];

      if (pode("usuarios.listar")) {
        requisicoes.push(
          (async () => {
            let offset = 0;
            const todosUsuarios: Usuario[] = [];

            while (true) {
              const resposta = await api.get<Usuario[]>("/usuarios/", {
                params: {
                  offset,
                  limit: USUARIOS_POR_REQUISICAO,
                },
              });

              todosUsuarios.push(...resposta.data);

              if (resposta.data.length < USUARIOS_POR_REQUISICAO) {
                break;
              }

              offset += USUARIOS_POR_REQUISICAO;
            }

            setUsuarios(todosUsuarios);
          })()
        );
      }

      if (pode("perfis.listar")) {
        requisicoes.push(
          api
            .get<Perfil[]>("/perfis/")
            .then((resposta) => setPerfis(resposta.data))
        );
      }

      if (pode("permissoes.listar")) {
        requisicoes.push(
          api
            .get<Permissao[]>("/permissoes/")
            .then((resposta) => setPermissoes(resposta.data))
        );
      }

      if (pode("professores.listar")) {
        requisicoes.push(
          api
            .get<Professor[]>("/professores/", {
              params: {
                offset: 0,
                limit: 100,
                ativo: true,
              },
            })
            .then((resposta) => setProfessores(resposta.data))
        );
      }

      await Promise.all(requisicoes);
    } catch (error) {
      setErro(mensagemErro(error));
    } finally {
      setCarregando(false);
      setAtualizando(false);
    }
  }, [user]);

  useEffect(() => {
    carregarDados();
  }, [carregarDados]);

  // ========================================================
  // SELEÇÃO AUTOMÁTICA DA ABA
  // ========================================================

  useEffect(() => {
    if (!podeListarUsuarios && podeListarPerfis) {
      setAba("perfis");
    } else if (podeListarUsuarios && !podeListarPerfis) {
      setAba("usuarios");
    }
  }, [podeListarUsuarios, podeListarPerfis]);

  // ========================================================
  // USUÁRIOS: FILTROS E PAGINAÇÃO
  // ========================================================

  const usuariosFiltrados = useMemo(() => {
    const termo = busca.trim().toLowerCase();

    return usuarios.filter((usuario) => {
      const correspondeBusca =
        !termo ||
        usuario.nome_completo.toLowerCase().includes(termo) ||
        usuario.email.toLowerCase().includes(termo);

      const correspondeStatus =
        filtroStatus === "todos" ||
        (filtroStatus === "ativos" && usuario.ativo) ||
        (filtroStatus === "inativos" && !usuario.ativo);

      const correspondePerfil =
        filtroPerfil === "todos" ||
        usuario.perfil_id === Number(filtroPerfil);

      return (
        correspondeBusca &&
        correspondeStatus &&
        correspondePerfil
      );
    });
  }, [usuarios, busca, filtroStatus, filtroPerfil]);

  const totalAtivos = usuarios.filter((usuario) => usuario.ativo).length;
  const totalInativos = usuarios.length - totalAtivos;

  const totalPaginas = Math.max(
    1,
    Math.ceil(usuariosFiltrados.length / USUARIOS_POR_PAGINA)
  );

  const paginaLimitada = Math.min(paginaAtual, totalPaginas);

  const inicioPagina = (paginaLimitada - 1) * USUARIOS_POR_PAGINA;

  const usuariosPaginados = usuariosFiltrados.slice(
    inicioPagina,
    inicioPagina + USUARIOS_POR_PAGINA
  );

  const primeiroUsuario =
    usuariosFiltrados.length === 0 ? 0 : inicioPagina + 1;

  const ultimoUsuario = Math.min(
    inicioPagina + USUARIOS_POR_PAGINA,
    usuariosFiltrados.length
  );

  useEffect(() => {
    setPaginaAtual(1);
  }, [busca, filtroStatus, filtroPerfil]);

  useEffect(() => {
    if (paginaAtual > totalPaginas) {
      setPaginaAtual(totalPaginas);
    }
  }, [paginaAtual, totalPaginas]);

  // ========================================================
  // USUÁRIOS: MODAL
  // ========================================================

  function abrirCriacao() {
    setUsuarioSelecionado(null);
    setFormUsuario(FORM_USUARIO_INICIAL);
    setModalUsuario("criar");
  }

  function abrirEdicao(usuario: Usuario) {
    setUsuarioSelecionado(usuario);
    setFormUsuario({
      nome_completo: usuario.nome_completo,
      email: usuario.email,
      senha: "",
      perfil_id: String(usuario.perfil_id),
      professor_id: usuario.professor_id
        ? String(usuario.professor_id)
        : "",
    });
    setModalUsuario("editar");
  }

  function abrirVisualizacao(usuario: Usuario) {
    setUsuarioSelecionado(usuario);
    setModalUsuario("visualizar");
  }

  function fecharModalUsuario() {
    if (salvandoUsuario) return;

    setModalUsuario(null);
    setUsuarioSelecionado(null);
    setFormUsuario(FORM_USUARIO_INICIAL);
  }

  async function salvarUsuario(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (salvandoUsuario) return;

    setErro("");

    if (!formUsuario.perfil_id) {
      setErro("Selecione um perfil para o usuário.");
      return;
    }

    if (modalUsuario === "criar" && formUsuario.senha.length < 12) {
      setErro("A senha deve possuir pelo menos 12 caracteres.");
      return;
    }

    if (formUsuario.senha && formUsuario.senha.length < 12) {
      setErro("A senha deve possuir pelo menos 12 caracteres.");
      return;
    }

    const dados: Record<string, unknown> = {
      nome_completo: formUsuario.nome_completo.trim(),
      email: formUsuario.email.trim().toLowerCase(),
      perfil_id: Number(formUsuario.perfil_id),
    };

    if (pode("professores.listar")) {
      dados.professor_id = formUsuario.professor_id
        ? Number(formUsuario.professor_id)
        : null;
    }

    setSalvandoUsuario(true);

    try {
      if (modalUsuario === "criar") {
        await api.post("/usuarios/", {
          ...dados,
          senha: formUsuario.senha,
        });
      } else if (usuarioSelecionado) {
        await api.put(`/usuarios/${usuarioSelecionado.id}`, dados);
      }

      fecharModalUsuario();
      await carregarDados(true);
    } catch (error) {
      setErro(mensagemErro(error));
    } finally {
      setSalvandoUsuario(false);
    }
  }

  async function alterarStatusUsuario(usuario: Usuario) {
    if (usuario.id === user?.id && usuario.ativo) {
      window.alert("Você não pode desativar a própria conta.");
      return;
    }

    const acao = usuario.ativo ? "desativar" : "reativar";

    const confirmou = window.confirm(
      `Deseja realmente ${acao} a conta de ${usuario.nome_completo}?`
    );

    if (!confirmou) return;

    setErro("");

    try {
      if (usuario.ativo) {
        await api.delete(`/usuarios/${usuario.id}`);
      } else {
        await api.patch(`/usuarios/${usuario.id}/ativar`);
      }

      await carregarDados(true);
    } catch (error) {
      setErro(mensagemErro(error));
    }
  }

  // ========================================================
  // PERFIS: EDIÇÃO
  // ========================================================

  function abrirPerfil(perfil: Perfil) {
    setPerfilSelecionado(perfil);
    setFormPerfil({
      nome: perfil.nome,
      descricao: perfil.descricao || "",
      ativo: perfil.ativo,
    });
    setPermissoesSelecionadas(
      perfil.permissoes.map((permissao) => permissao.id)
    );
    setErro("");
  }

  function fecharPerfil() {
    if (salvandoPerfil) return;

    setPerfilSelecionado(null);
    setErro("");
  }

  function alternarPermissao(id: number) {
    setPermissoesSelecionadas((atuais) =>
      atuais.includes(id)
        ? atuais.filter((item) => item !== id)
        : [...atuais, id]
    );
  }

  const permissoesAgrupadas = useMemo(() => {
    return permissoes.reduce<Record<string, Permissao[]>>(
      (grupos, permissao) => {
        const modulo = permissao.modulo || "Outros";

        if (!grupos[modulo]) grupos[modulo] = [];

        grupos[modulo].push(permissao);
        return grupos;
      },
      {}
    );
  }, [permissoes]);

  async function salvarPerfil(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!perfilSelecionado || salvandoPerfil) return;

    setSalvandoPerfil(true);
    setErro("");

    try {
      if (pode("perfis.gerenciar")) {
        await api.put(`/perfis/${perfilSelecionado.id}`, {
          nome: formPerfil.nome.trim(),
          descricao: formPerfil.descricao.trim() || null,
          ativo: formPerfil.ativo,
        });
      }

      if (pode("permissoes.gerenciar")) {
        await api.put(
          `/perfis/${perfilSelecionado.id}/permissoes`,
          {
            permissao_ids: permissoesSelecionadas,
          }
        );
      }

      setPerfilSelecionado(null);
      await carregarDados(true);
    } catch (error) {
      setErro(mensagemErro(error));
    } finally {
      setSalvandoPerfil(false);
    }
  }

  // ========================================================
  // RENDERIZAÇÃO
  // ========================================================

  if (carregando) {
    return (
      <div className="students-loading">
        Carregando usuários e perfis...
      </div>
    );
  }

  if (!podeListarUsuarios && !podeListarPerfis) {
    return (
      <div className="page-stack">
        <div className="page-heading">
          <div>
            <span className="eyebrow">ADMINISTRAÇÃO DO SISTEMA</span>
            <h1>Usuários e perfis</h1>
          </div>
        </div>

        <div className="students-alert">
          Você não possui permissão para visualizar usuários ou perfis.
        </div>
      </div>
    );
  }

  return (
    <div className="page-stack">
      {/* CABEÇALHO */}
      <div className="page-heading students-heading">
        <div>
          <span className="eyebrow">ADMINISTRAÇÃO DO SISTEMA</span>
          <h1>Usuários e perfis</h1>
          <p className="muted">
            Gerencie as contas de acesso e as permissões do sistema.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={() => carregarDados(true)}
          disabled={atualizando}
        >
          <RefreshCw size={16} />
          {atualizando ? "Atualizando..." : "Atualizar"}
        </button>
      </div>

      {/* MENSAGEM DE ERRO */}
      {erro && !modalUsuario && !perfilSelecionado && (
        <div className="students-alert">{erro}</div>
      )}

      {/* ABAS */}
      <div className="students-toolbar">
        <div className="users-tabs">
          {podeListarUsuarios && (
            <button
              type="button"
              className={`users-tab ${aba === "usuarios" ? "active" : ""}`}
              onClick={() => {
                setAba("usuarios");
                setErro("");
              }}
            >
              <Users size={17} />
              Usuários
            </button>
          )}

          {podeListarPerfis && (
            <button
              type="button"
              className={`users-tab ${aba === "perfis" ? "active" : ""}`}
              onClick={() => {
                setAba("perfis");
                setErro("");
              }}
            >
              <ShieldCheck size={17} />
              Perfis e permissões
            </button>
          )}
        </div>
      </div>

      {/* ================================================== */}
      {/* ABA USUÁRIOS */}
      {/* ================================================== */}

      {aba === "usuarios" && podeListarUsuarios && (
        <>
          <div className="students-stats">
            <div className="students-stat">
              <div>
                <span className="muted">Total de usuários</span>
                <strong>{usuarios.length}</strong>
              </div>
              <Users size={22} />
            </div>

            <div className="students-stat">
              <div>
                <span className="muted">Contas ativas</span>
                <strong>{totalAtivos}</strong>
              </div>
              <UserCheck size={22} />
            </div>

            <div className="students-stat">
              <div>
                <span className="muted">Contas inativas</span>
                <strong>{totalInativos}</strong>
              </div>
              <UserX size={22} />
            </div>
          </div>

          <div className="students-table-card">
            <div className="students-toolbar">
              <div className="students-search">
                <Search size={17} />
                <input
                  type="search"
                  placeholder="Buscar por nome ou e-mail..."
                  value={busca}
                  onChange={(event) => setBusca(event.target.value)}
                />
              </div>

              <select
                className="students-class-filter"
                value={filtroPerfil}
                onChange={(event) => setFiltroPerfil(event.target.value)}
              >
                <option value="todos">Todos os perfis</option>
                {perfis.map((perfil) => (
                  <option key={perfil.id} value={perfil.id}>
                    {perfil.nome}
                  </option>
                ))}
              </select>

              <select
                className="students-class-filter"
                value={filtroStatus}
                onChange={(event) => setFiltroStatus(event.target.value)}
              >
                <option value="todos">Todas as situações</option>
                <option value="ativos">Ativos</option>
                <option value="inativos">Inativos</option>
              </select>

              {pode("usuarios.criar") && (
                <button
                  type="button"
                  className="primary-button"
                  onClick={abrirCriacao}
                >
                  <Plus size={17} />
                  Novo usuário
                </button>
              )}
            </div>

            <div className="students-table-wrapper">
              <table className="students-table">
                <thead>
                  <tr>
                    <th>Usuário</th>
                    <th>Perfil</th>
                    <th>Último acesso</th>
                    <th>Situação</th>
                    <th>Ações</th>
                  </tr>
                </thead>

                <tbody>
                  {usuariosPaginados.map((usuario) => (
                    <tr key={usuario.id}>
                      <td>
                        <div className="student-name-cell">
                          <div className="student-avatar">
                            {usuario.nome_completo.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <strong>{usuario.nome_completo}</strong>
                            <span>{usuario.email}</span>
                          </div>
                        </div>
                      </td>

                      <td>{usuario.perfil?.nome || "—"}</td>

                      <td>{formatarData(usuario.ultimo_acesso)}</td>

                      <td>
                        <span
                          className={`status-badge ${
                            usuario.ativo ? "active" : "inactive"
                          }`}
                        >
                          {usuario.ativo ? "Ativo" : "Inativo"}
                        </span>
                      </td>

                      <td>
                        <div className="student-actions">
                          <button
                            type="button"
                            className="icon-button"
                            title="Visualizar usuário"
                            onClick={() => abrirVisualizacao(usuario)}
                          >
                            <Eye size={17} />
                          </button>

                          {pode("usuarios.editar") && (
                            <button
                              type="button"
                              className="icon-button"
                              title="Editar usuário"
                              onClick={() => abrirEdicao(usuario)}
                            >
                              <Pencil size={17} />
                            </button>
                          )}

                          {usuario.id !== user?.id &&
                            (usuario.ativo
                              ? pode("usuarios.desativar")
                              : pode("usuarios.editar")) && (
                              <button
                                type="button"
                                className="icon-button"
                                title={
                                  usuario.ativo
                                    ? "Desativar usuário"
                                    : "Reativar usuário"
                                }
                                onClick={() =>
                                  alterarStatusUsuario(usuario)
                                }
                              >
                                {usuario.ativo ? (
                                  <UserX size={17} />
                                ) : (
                                  <UserCheck size={17} />
                                )}
                              </button>
                            )}
                        </div>
                      </td>
                    </tr>
                  ))}

                  {usuariosFiltrados.length === 0 && (
                    <tr>
                      <td colSpan={5}>
                        <div className="students-empty">
                          Nenhum usuário encontrado.
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="students-pagination">
              <span>
                Exibindo {primeiroUsuario}–{ultimoUsuario} de{" "}
                {usuariosFiltrados.length} usuário(s)
              </span>

              {totalPaginas > 1 && (
                <div className="student-actions">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      setPaginaAtual((pagina) => Math.max(1, pagina - 1))
                    }
                    disabled={paginaLimitada === 1}
                  >
                    Anterior
                  </button>

                  <span>
                    Página {paginaLimitada} de {totalPaginas}
                  </span>

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      setPaginaAtual((pagina) =>
                        Math.min(totalPaginas, pagina + 1)
                      )
                    }
                    disabled={paginaLimitada === totalPaginas}
                  >
                    Próxima
                  </button>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* ================================================== */}
      {/* ABA PERFIS */}
      {/* ================================================== */}

      {aba === "perfis" && podeListarPerfis && (
        <div className="users-profiles-grid">
          {perfis.map((perfil) => (
            <div className="card-surface users-profile-card" key={perfil.id}>
              <div className="users-profile-header">
                <div className="users-profile-icon">
                  <ShieldCheck size={22} />
                </div>

                <span
                  className={`status-badge ${
                    perfil.ativo ? "active" : "inactive"
                  }`}
                >
                  {perfil.ativo ? "Ativo" : "Inativo"}
                </span>
              </div>

              <h3>{perfil.nome}</h3>

              <p className="muted">
                {perfil.descricao || "Nenhuma descrição cadastrada."}
              </p>

              <div className="users-profile-info">
                <span>
                  <KeyRound size={15} />
                  {perfil.permissoes.length} permissões
                </span>
              </div>

              {(pode("perfis.gerenciar") ||
                pode("permissoes.gerenciar")) && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => abrirPerfil(perfil)}
                >
                  <Pencil size={16} />
                  Gerenciar perfil
                </button>
              )}
            </div>
          ))}

          {perfis.length === 0 && (
            <div className="students-empty">
              Nenhum perfil encontrado.
            </div>
          )}
        </div>
      )}

      {/* ================================================== */}
      {/* MODAL DE USUÁRIO */}
      {/* ================================================== */}

      {modalUsuario && (
        <div
          className="students-modal-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) fecharModalUsuario();
          }}
        >
          <div className="students-modal">
            <div className="students-modal-header">
              <div>
                <h2>
                  {modalUsuario === "criar"
                    ? "Novo usuário"
                    : modalUsuario === "editar"
                      ? "Editar usuário"
                      : "Detalhes do usuário"}
                </h2>
                <p className="muted">
                  {modalUsuario === "visualizar"
                    ? "Informações da conta de acesso."
                    : "Preencha os dados da conta de acesso."}
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={fecharModalUsuario}
                title="Fechar"
              >
                <X size={19} />
              </button>
            </div>

            {modalUsuario === "visualizar" && usuarioSelecionado ? (
              <div className="student-details">
                <div className="student-details-grid">
                  <div>
                    <span>Nome completo</span>
                    <strong>{usuarioSelecionado.nome_completo}</strong>
                  </div>

                  <div>
                    <span>E-mail</span>
                    <strong>{usuarioSelecionado.email}</strong>
                  </div>

                  <div>
                    <span>Perfil</span>
                    <strong>{usuarioSelecionado.perfil?.nome || "—"}</strong>
                  </div>

                  <div>
                    <span>Situação</span>
                    <strong>
                      {usuarioSelecionado.ativo ? "Ativo" : "Inativo"}
                    </strong>
                  </div>

                  <div>
                    <span>Último acesso</span>
                    <strong>
                      {formatarData(usuarioSelecionado.ultimo_acesso)}
                    </strong>
                  </div>

                  <div>
                    <span>Data de cadastro</span>
                    <strong>
                      {formatarData(usuarioSelecionado.data_cadastro)}
                    </strong>
                  </div>

                  <div>
                    <span>ID do professor vinculado</span>
                    <strong>
                      {usuarioSelecionado.professor_id || "Não vinculado"}
                    </strong>
                  </div>
                </div>

                <div className="students-modal-footer">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={fecharModalUsuario}
                  >
                    Fechar
                  </button>

                  {pode("usuarios.editar") && (
                    <button
                      type="button"
                      className="primary-button"
                      onClick={() => abrirEdicao(usuarioSelecionado)}
                    >
                      <Pencil size={16} />
                      Editar
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <form onSubmit={salvarUsuario}>
                {erro && <div className="students-alert">{erro}</div>}

                <div className="students-form-grid">
                  <div className="students-field">
                    <label htmlFor="usuario-nome">Nome completo</label>
                    <input
                      id="usuario-nome"
                      type="text"
                      minLength={3}
                      maxLength={150}
                      required
                      value={formUsuario.nome_completo}
                      onChange={(event) =>
                        setFormUsuario({
                          ...formUsuario,
                          nome_completo: event.target.value,
                        })
                      }
                      disabled={modalUsuario === "visualizar"}
                    />
                  </div>

                  <div className="students-field">
                    <label htmlFor="usuario-email">E-mail</label>
                    <input
                      id="usuario-email"
                      type="email"
                      maxLength={255}
                      required
                      value={formUsuario.email}
                      onChange={(event) =>
                        setFormUsuario({
                          ...formUsuario,
                          email: event.target.value,
                        })
                      }
                    />
                  </div>

                  <div className="students-field">
                    <label htmlFor="usuario-perfil">Perfil de acesso</label>
                    <select
                      id="usuario-perfil"
                      required
                      value={formUsuario.perfil_id}
                      onChange={(event) =>
                        setFormUsuario({
                          ...formUsuario,
                          perfil_id: event.target.value,
                        })
                      }
                    >
                      <option value="">Selecione um perfil</option>
                      {perfis
                        .filter((perfil) => perfil.ativo)
                        .map((perfil) => (
                          <option key={perfil.id} value={perfil.id}>
                            {perfil.nome}
                          </option>
                        ))}
                    </select>
                  </div>

                  {pode("professores.listar") && (
                    <div className="students-field">
                      <label htmlFor="usuario-professor">
                        Professor vinculado
                      </label>
                      <select
                        id="usuario-professor"
                        value={formUsuario.professor_id}
                        onChange={(event) =>
                          setFormUsuario({
                            ...formUsuario,
                            professor_id: event.target.value,
                          })
                        }
                      >
                        <option value="">Não vincular a professor</option>
                        {professores.map((professor) => (
                          <option key={professor.id} value={professor.id}>
                            {professor.nome_completo}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  <div className="students-field">
                    <label htmlFor="usuario-senha">
                      {modalUsuario === "criar"
                        ? "Senha inicial"
                        : "Nova senha"}
                    </label>
                    <input
                      id="usuario-senha"
                      type="password"
                      minLength={12}
                      maxLength={128}
                      required={modalUsuario === "criar"}
                      autoComplete="new-password"
                      placeholder={
                        modalUsuario === "editar"
                          ? "Deixe em branco para manter a atual"
                          : "Mínimo de 12 caracteres"
                      }
                      value={formUsuario.senha}
                      onChange={(event) =>
                        setFormUsuario({
                          ...formUsuario,
                          senha: event.target.value,
                        })
                      }
                    />
                    <small className="muted">
                      {modalUsuario === "editar"
                        ? "Preencha somente se desejar alterar a senha."
                        : "A senha deve possuir pelo menos 12 caracteres."}
                    </small>
                  </div>
                </div>

                <div className="students-modal-footer">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={fecharModalUsuario}
                    disabled={salvandoUsuario}
                  >
                    Cancelar
                  </button>

                  <button
                    type="submit"
                    className="primary-button"
                    disabled={salvandoUsuario}
                  >
                    <Save size={16} />
                    {salvandoUsuario ? "Salvando..." : "Salvar usuário"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* ================================================== */}
      {/* MODAL DE PERFIL E PERMISSÕES */}
      {/* ================================================== */}

      {perfilSelecionado && (
        <div
          className="students-modal-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) fecharPerfil();
          }}
        >
          <div className="students-modal users-profile-modal">
            <div className="students-modal-header">
              <div>
                <h2>Gerenciar perfil</h2>
                <p className="muted">
                  Configure os dados e as permissões de acesso.
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={fecharPerfil}
                title="Fechar"
              >
                <X size={19} />
              </button>
            </div>

            <form onSubmit={salvarPerfil}>
              {erro && <div className="students-alert">{erro}</div>}

              {pode("perfis.gerenciar") && (
                <div className="students-form-grid">
                  <div className="students-field">
                    <label htmlFor="perfil-nome">Nome do perfil</label>
                    <input
                      id="perfil-nome"
                      type="text"
                      minLength={3}
                      maxLength={100}
                      required
                      value={formPerfil.nome}
                      onChange={(event) =>
                        setFormPerfil({
                          ...formPerfil,
                          nome: event.target.value,
                        })
                      }
                    />
                  </div>

                  <div className="students-field">
                    <label htmlFor="perfil-descricao">Descrição</label>
                    <input
                      id="perfil-descricao"
                      type="text"
                      maxLength={255}
                      value={formPerfil.descricao}
                      onChange={(event) =>
                        setFormPerfil({
                          ...formPerfil,
                          descricao: event.target.value,
                        })
                      }
                    />
                  </div>

                  <div className="students-field">
                    <label htmlFor="perfil-status">Situação</label>
                    <select
                      id="perfil-status"
                      value={formPerfil.ativo ? "ativo" : "inativo"}
                      onChange={(event) =>
                        setFormPerfil({
                          ...formPerfil,
                          ativo: event.target.value === "ativo",
                        })
                      }
                    >
                      <option value="ativo">Ativo</option>
                      <option value="inativo">Inativo</option>
                    </select>
                  </div>
                </div>
              )}

              {pode("permissoes.gerenciar") && (
                <section className="users-permissions-section">
                  <div className="users-permissions-heading">
                    <div>
                      <h3>Permissões do perfil</h3>
                      <p className="muted">
                        Selecione as funcionalidades que este perfil poderá acessar.
                      </p>
                    </div>

                    <span className="users-permissions-count">
                      {permissoesSelecionadas.length} selecionada(s)
                    </span>
                  </div>

                  {Object.entries(permissoesAgrupadas).map(
                    ([modulo, lista]) => (
                      <div className="users-permission-group" key={modulo}>
                        <h4>{modulo}</h4>

                        <div className="users-permission-list">
                          {lista.map((permissao) => (
                            <label
                              className="users-permission-item"
                              key={permissao.id}
                            >
                              <input
                                type="checkbox"
                                checked={permissoesSelecionadas.includes(
                                  permissao.id
                                )}
                                onChange={() =>
                                  alternarPermissao(permissao.id)
                                }
                              />

                              <span>
                                <strong>{permissao.nome}</strong>
                                <small>
                                  {permissao.descricao || permissao.codigo}
                                </small>
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>
                    )
                  )}

                  {permissoes.length === 0 && (
                    <div className="students-empty">
                      Nenhuma permissão disponível para gerenciamento.
                    </div>
                  )}
                </section>
              )}

              <div className="students-modal-footer">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={fecharPerfil}
                  disabled={salvandoPerfil}
                >
                  Cancelar
                </button>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={salvandoPerfil}
                >
                  <Save size={16} />
                  {salvandoPerfil ? "Salvando..." : "Salvar alterações"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
