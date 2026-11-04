# Gestão Escolar C.B.B.P.

Sistema de Gestão Escolar desenvolvido para o **Colégio Batista Bob Pierce (C.B.B.P.)**, com o objetivo de centralizar e modernizar os processos administrativos e acadêmicos da instituição.

## Sobre o projeto

O sistema está sendo desenvolvido para oferecer uma plataforma de gerenciamento escolar, com foco em organização, segurança e facilidade de utilização.

## Tecnologias

### Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- Alembic

### Frontend
- React
- TypeScript
- Vite

## Funcionalidades planejadas

- [ ] Cadastro e gerenciamento de alunos
- [ ] Cadastro de responsáveis
- [ ] Gerenciamento de turmas
- [ ] Controle de matrículas
- [ ] Gestão de professores
- [ ] Controle de notas e frequência
- [ ] Gestão financeira
- [ ] Autenticação e controle de acesso
- [ ] Painel administrativo

## Estrutura do projeto

```text
gestao-escolar/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│
├── .gitignore
└── README.md
```

## Como executar o backend

### 1. Clonar o repositório

```bash
git clone URL_DO_REPOSITORIO
cd gestao-escolar/backend
```

### 2. Criar o ambiente virtual

```bash
python -m venv .venv
```

### 3. Ativar o ambiente virtual no Windows

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Instalar as dependências

```bash
python -m pip install -r requirements.txt
```

### 5. Configurar as variáveis de ambiente

Copie `.env.example` para `.env` e configure a conexão com seu PostgreSQL.

### 6. Executar a aplicação

```bash
python -m uvicorn app.main:app --reload
```

A API estará disponível em:

`http://127.0.0.1:8000`

Documentação interativa:

`http://127.0.0.1:8000/docs`

## Status

**Em desenvolvimento.**

Este projeto está em construção e suas funcionalidades serão implementadas progressivamente.