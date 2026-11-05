import getpass
import re
import sys

from pathlib import Path

# Permite executar o script diretamente a partir da pasta backend.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.database import SessionLocal
from app.core.security import hash_senha
from app.models.perfil import Perfil
from app.models.usuario import Usuario


def criar_administrador():
    db = SessionLocal()

    try:
        perfil_admin = db.scalar(
            select(Perfil).where(Perfil.nome == "Administrador")
        )

        if perfil_admin is None:
            print(
                "ERRO: perfil Administrador não encontrado. "
                "Execute primeiro o seed de perfis e permissões."
            )
            return

        administrador_existente = db.scalar(
            select(Usuario.id)
            .where(Usuario.perfil_id == perfil_admin.id)
            .limit(1)
        )

        if administrador_existente is not None:
            print(
                "ERRO: já existe uma conta com o perfil Administrador. "
                "O cadastro inicial foi bloqueado."
            )
            return

        print("\n========== CRIAR PRIMEIRO ADMINISTRADOR ==========")

        nome = input("Nome completo: ").strip()
        email = input("E-mail: ").strip().lower()

        if len(nome) < 3:
            print("ERRO: informe um nome completo válido.")
            return

        if len(nome) > 150:
            print("ERRO: o nome deve ter no máximo 150 caracteres.")
            return

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            print("ERRO: informe um endereço de e-mail válido.")
            return

        if len(email) > 150:
            print("ERRO: o e-mail deve ter no máximo 150 caracteres.")
            return

        email_existente = db.scalar(
            select(Usuario.id).where(Usuario.email == email)
        )

        if email_existente is not None:
            print("ERRO: já existe uma conta cadastrada com esse e-mail.")
            return

        senha = getpass.getpass("Senha (mínimo 12 caracteres): ")
        confirmacao = getpass.getpass("Confirme a senha: ")

        if len(senha) < 12:
            print("ERRO: a senha deve possuir pelo menos 12 caracteres.")
            return

        if senha != confirmacao:
            print("ERRO: as senhas não coincidem.")
            return

        usuario = Usuario(
            nome_completo=nome,
            email=email,
            senha_hash=hash_senha(senha),
            perfil_id=perfil_admin.id,
            ativo=True
        )

        db.add(usuario)
        db.commit()

        print("\nAdministrador criado com sucesso.")
        print(f"E-mail: {email}")
        print(f"Perfil: {perfil_admin.nome}")
        print("A senha não foi exibida nem armazenada em texto puro.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    criar_administrador()
