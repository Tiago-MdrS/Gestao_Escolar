from sqlalchemy import select

from app.database import SessionLocal
from app.models.perfil import Perfil
from app.models.permissao import Permissao


PERMISSOES = [
    # Usuários
    ("usuarios.listar", "Listar usuários", "Consultar contas de acesso.", "usuarios"),
    ("usuarios.criar", "Criar usuários", "Cadastrar novas contas.", "usuarios"),
    ("usuarios.editar", "Editar usuários", "Alterar dados das contas.", "usuarios"),
    ("usuarios.desativar", "Desativar usuários", "Desativar contas de acesso.", "usuarios"),

    # Perfis e permissões
    ("perfis.listar", "Listar perfis", "Consultar perfis de acesso.", "acessos"),
    ("perfis.gerenciar", "Gerenciar perfis", "Criar, editar e desativar perfis.", "acessos"),
    ("permissoes.listar", "Listar permissões", "Consultar permissões disponíveis.", "acessos"),
    ("permissoes.gerenciar", "Gerenciar permissões", "Associar e remover permissões dos perfis.", "acessos"),

    # Alunos
    ("alunos.listar", "Listar alunos", "Consultar alunos cadastrados.", "alunos"),
    ("alunos.criar", "Criar alunos", "Cadastrar alunos.", "alunos"),
    ("alunos.editar", "Editar alunos", "Alterar dados dos alunos.", "alunos"),
    ("alunos.desativar", "Desativar alunos", "Desativar cadastros de alunos.", "alunos"),

    # Responsáveis
    ("responsaveis.listar", "Listar responsáveis", "Consultar responsáveis cadastrados.", "responsaveis"),
    ("responsaveis.criar", "Criar responsáveis", "Cadastrar responsáveis.", "responsaveis"),
    ("responsaveis.editar", "Editar responsáveis", "Alterar dados dos responsáveis.", "responsaveis"),
    ("responsaveis.desativar", "Desativar responsáveis", "Desativar responsáveis.", "responsaveis"),

    # Matrículas
    ("matriculas.listar", "Listar matrículas", "Consultar matrículas.", "matriculas"),
    ("matriculas.criar", "Criar matrículas", "Registrar matrículas.", "matriculas"),
    ("matriculas.editar", "Editar matrículas", "Alterar dados das matrículas.", "matriculas"),
    ("matriculas.cancelar", "Cancelar matrículas", "Cancelar matrículas.", "matriculas"),

    # Professores
    ("professores.listar", "Listar professores", "Consultar professores.", "professores"),
    ("professores.criar", "Criar professores", "Cadastrar professores.", "professores"),
    ("professores.editar", "Editar professores", "Alterar dados dos professores.", "professores"),
    ("professores.desativar", "Desativar professores", "Desativar professores.", "professores"),

    # Turmas
    ("turmas.listar", "Listar turmas", "Consultar turmas.", "turmas"),
    ("turmas.criar", "Criar turmas", "Cadastrar turmas.", "turmas"),
    ("turmas.editar", "Editar turmas", "Alterar dados das turmas.", "turmas"),
    ("turmas.desativar", "Desativar turmas", "Desativar turmas.", "turmas"),

    # Disciplinas
    ("disciplinas.listar", "Listar disciplinas", "Consultar disciplinas.", "disciplinas"),
    ("disciplinas.criar", "Criar disciplinas", "Cadastrar disciplinas.", "disciplinas"),
    ("disciplinas.editar", "Editar disciplinas", "Alterar disciplinas.", "disciplinas"),
    ("disciplinas.desativar", "Desativar disciplinas", "Desativar disciplinas.", "disciplinas"),

    # Vínculos entre turmas, disciplinas e professores
    ("turma_disciplinas.listar", "Listar vínculos", "Consultar vínculos acadêmicos.", "turma_disciplinas"),
    ("turma_disciplinas.gerenciar", "Gerenciar vínculos", "Criar, editar e desativar vínculos acadêmicos.", "turma_disciplinas"),

    # Grade horária
    ("horarios.listar", "Consultar grade horária", "Consultar horários das turmas.", "horarios"),
    ("horarios.gerenciar", "Gerenciar grade horária", "Criar, editar e desativar horários.", "horarios"),
    ("horarios.consultar_proprios", "Consultar horários próprios", "Consultar a própria grade horária.", "horarios"),
    # Frequência escolar
    ("frequencia.listar", "Listar frequências", "Consultar registros de frequência dos alunos.", "frequencias"),
    ("frequencia.registrar", "Registrar frequência", "Registrar presença, falta e falta justificada.", "frequencias"),
    ("frequencia.editar", "Editar frequência", "Corrigir registros de frequência.", "frequencias"),
    ("frequencia.consultar_propria", "Consultar frequências próprias", "Consultar frequências das próprias turmas.", "frequencias"),

    # Per?odos letivos
    ("periodos.listar", "Listar per?odos letivos", "Consultar per?odos letivos cadastrados.", "academico"),
    ("periodos.gerenciar", "Gerenciar per?odos letivos", "Criar, editar e desativar per?odos letivos.", "academico"),

    # Avalia??es
    ("avaliacoes.listar", "Listar avalia??es", "Consultar avalia??es cadastradas.", "academico"),
    ("avaliacoes.gerenciar", "Gerenciar avalia??es", "Criar, editar e desativar avalia??es.", "academico"),

    # Notas
    ("notas.listar", "Listar notas", "Consultar notas dos alunos.", "academico"),
    ("notas.lancar", "Lan?ar notas", "Registrar notas das avalia??es.", "academico"),
    ("notas.editar", "Editar notas", "Corrigir notas lan?adas.", "academico"),
    ("notas.consultar_proprias", "Consultar notas pr?prias", "Consultar notas das pr?prias turmas.", "academico"),

    # Recupera??es
    ("recuperacoes.listar", "Listar recupera??es", "Consultar notas de recupera??o.", "academico"),
    ("recuperacoes.gerenciar", "Gerenciar recupera??es", "Registrar e editar notas de recupera??o.", "academico"),

    # Relat?rios acad?micos
    ("relatorios.desempenho", "Consultar desempenho acad?mico", "Consultar m?dias e desempenho dos alunos.", "relatorios"),

]


PERFIS = {
    "Administrador": {
        "descricao": "Administra contas de acesso, perfis e permissões do sistema.",
        "permissoes": [
            "usuarios.listar",
            "usuarios.criar",
            "usuarios.editar",
            "usuarios.desativar",
            "perfis.listar",
            "perfis.gerenciar",
            "permissoes.listar",
            "permissoes.gerenciar",
            "alunos.listar",
            "alunos.criar",
            "alunos.editar",
            "alunos.desativar",
            "responsaveis.listar",
            "responsaveis.criar",
            "responsaveis.editar",
            "responsaveis.desativar",
            "matriculas.listar",
            "matriculas.criar",
            "matriculas.editar",
            "matriculas.cancelar",
            "professores.listar",
            "professores.criar",
            "professores.editar",
            "professores.desativar",
            "turmas.listar",
            "turmas.criar",
            "turmas.editar",
            "turmas.desativar",
            "disciplinas.listar",
            "disciplinas.criar",
            "disciplinas.editar",
            "disciplinas.desativar",
            "turma_disciplinas.listar",
            "turma_disciplinas.gerenciar",
            "horarios.listar",
            "horarios.gerenciar",
            "frequencia.listar",
            "frequencia.registrar",
            "frequencia.editar",
            "frequencia.consultar_propria",
            "periodos.listar",
            "periodos.gerenciar",
            "avaliacoes.listar",
            "avaliacoes.gerenciar",
            "notas.listar",
            "notas.lancar",
            "notas.editar",
            "notas.consultar_proprias",
            "recuperacoes.listar",
            "recuperacoes.gerenciar",
            "relatorios.desempenho",
        ],
    },
    "Gestor": {
        "descricao": "Gerencia as operações escolares e a organização acadêmica.",
        "permissoes": [
            "alunos.listar",
            "alunos.criar",
            "alunos.editar",
            "alunos.desativar",
            "responsaveis.listar",
            "responsaveis.criar",
            "responsaveis.editar",
            "responsaveis.desativar",
            "matriculas.listar",
            "matriculas.criar",
            "matriculas.editar",
            "matriculas.cancelar",
            "professores.listar",
            "professores.criar",
            "professores.editar",
            "professores.desativar",
            "turmas.listar",
            "turmas.criar",
            "turmas.editar",
            "turmas.desativar",
            "disciplinas.listar",
            "disciplinas.criar",
            "disciplinas.editar",
            "disciplinas.desativar",
            "turma_disciplinas.listar",
            "turma_disciplinas.gerenciar",
            "horarios.listar",
            "horarios.gerenciar",
            "frequencia.listar",
            "frequencia.registrar",
            "frequencia.editar",
            "frequencia.consultar_propria",
            "periodos.listar",
            "periodos.gerenciar",
            "avaliacoes.listar",
            "avaliacoes.gerenciar",
            "notas.listar",
            "notas.lancar",
            "notas.editar",
            "notas.consultar_proprias",
            "recuperacoes.listar",
            "recuperacoes.gerenciar",
            "relatorios.desempenho",
        ],
    },
    "Secretaria": {
        "descricao": "Executa atividades administrativas e acadêmicas autorizadas.",
        "permissoes": [
            "alunos.listar",
            "alunos.criar",
            "alunos.editar",
            "responsaveis.listar",
            "responsaveis.criar",
            "responsaveis.editar",
            "matriculas.listar",
            "matriculas.criar",
            "matriculas.editar",
            "matriculas.cancelar",
            "professores.listar",
            "turmas.listar",
            "disciplinas.listar",
            "turma_disciplinas.listar",
            "horarios.listar",
            "frequencia.listar",
            "frequencia.registrar",
            "frequencia.editar",
            "periodos.listar",
            "avaliacoes.listar",
            "notas.listar",
            "recuperacoes.listar",
            "relatorios.desempenho",
        ],
    },
    "Professor": {
        "descricao": "Consulta suas próprias informações acadêmicas e horários.",
        "permissoes": [
            "turmas.listar",
            "disciplinas.listar",
            "turma_disciplinas.listar",
            "horarios.consultar_proprios",
            "frequencia.registrar",
            "frequencia.consultar_propria",
            "periodos.listar",
            "avaliacoes.listar",
            "avaliacoes.gerenciar",
            "notas.lancar",
            "notas.editar",
            "notas.consultar_proprias",
            "recuperacoes.listar",
            "recuperacoes.gerenciar",
            "relatorios.desempenho",
        ],
    },
}


def executar_cadastro():
    db = SessionLocal()

    try:
        permissoes_por_codigo = {}

        # Cria as permissões que ainda não existem.
        for codigo, nome, descricao, modulo in PERMISSOES:
            permissao = db.scalar(
                select(Permissao).where(Permissao.codigo == codigo)
            )

            if permissao is None:
                permissao = Permissao(
                    codigo=codigo,
                    nome=nome,
                    descricao=descricao,
                    modulo=modulo,
                )
                db.add(permissao)
                print(f"Permissão criada: {codigo}")

            permissoes_por_codigo[codigo] = permissao

        db.flush()

        # Cria os perfis e associa suas permissões.
        for nome, configuracao in PERFIS.items():
            perfil = db.scalar(
                select(Perfil).where(Perfil.nome == nome)
            )

            if perfil is None:
                perfil = Perfil(
                    nome=nome,
                    descricao=configuracao["descricao"],
                )
                db.add(perfil)
                print(f"Perfil criado: {nome}")

            codigos_associados = {
                permissao.codigo for permissao in perfil.permissoes
            }

            for codigo in configuracao["permissoes"]:
                if codigo not in codigos_associados:
                    perfil.permissoes.append(
                        permissoes_por_codigo[codigo]
                    )

        db.commit()

        print("\n========== CADASTRO CONCLUÍDO ==========")

        for nome in PERFIS:
            perfil = db.scalar(
                select(Perfil).where(Perfil.nome == nome)
            )
            print(
                f"{perfil.nome}: "
                f"{len(perfil.permissoes)} permissões"
            )

        print(f"\nTotal de permissões disponíveis: {len(PERMISSOES)}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    executar_cadastro()
