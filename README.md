# Gestão Escolar C.B.B.P.

Sistema de Gestão Escolar desenvolvido para o **Colégio Batista Bob Pierce (C.B.B.P.)**, com o objetivo de centralizar e modernizar os processos administrativos e acadêmicos da instituição.

O projeto utiliza uma API REST em Python com FastAPI e uma aplicação web em React, com banco de dados PostgreSQL.

## Tecnologias utilizadas

### Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- Alembic
- JWT (JSON Web Token)
- Argon2
- Pytest

### Frontend
- React 19
- TypeScript
- Vite
- React Router
- Axios
- Lucide React

## Funcionalidades do backend

### Gestão acadêmica
- [x] Cadastro e gerenciamento de alunos.
- [x] Cadastro e gerenciamento de responsáveis.
- [x] Associação entre alunos e responsáveis.
- [x] Cadastro e gerenciamento de professores.
- [x] Cadastro e gerenciamento de turmas.
- [x] Cadastro e gerenciamento de disciplinas.
- [x] Associação de disciplinas às turmas e professores.
- [x] Controle de matrículas.
- [x] Validação de matrícula ativa e capacidade de turmas.

### Autenticação e autorização
- [x] Login com autenticação JWT.
- [x] Hash de senhas com Argon2.
- [x] Consulta do usuário autenticado.
- [x] Gerenciamento de usuários e perfis.
- [x] Controle de permissões por perfil.
- [x] Proteção de operações conforme permissões.

### Horários e frequência
- [x] Cadastro, consulta, atualização e inativação de horários.
- [x] Consulta dos horários do professor autenticado.
- [x] Validação de conflitos de horários de turmas e professores.
- [x] Registro e consulta de frequência.
- [x] Registro de presença, falta e falta justificada.
- [x] Validação de matrícula ativa e prevenção de registros duplicados.
- [x] Controle de acesso às frequências conforme perfil e permissões.

### Avaliações e resultados acadêmicos
- [x] Cadastro e gerenciamento de períodos letivos.
- [x] Cadastro e gerenciamento de avaliações.
- [x] Lançamento e consulta de notas.
- [x] Recuperações acadêmicas.
- [x] Cálculo de médias e resultados acadêmicos.
- [x] Regras para composição dos resultados por período e média anual.

### Calendário e relatórios
- [x] Gerenciamento de calendários escolares.
- [x] Cadastro e gerenciamento de eventos do calendário.
- [x] Relatórios acadêmicos.

## Frontend

O frontend está em sua etapa inicial de integração com a API.

Funcionalidades já preparadas:
- [x] Estrutura React com TypeScript e Vite.
- [x] Tela de login integrada ao endpoint de autenticação.
- [x] Recuperação da sessão por meio de `/auth/me`.
- [x] Armazenamento local do token de acesso.
- [x] Rotas protegidas para usuários autenticados.
- [x] Layout principal com menu lateral responsivo.
- [x] Organização inicial da navegação por perfil.
- [x] Tema visual alinhado ao protótipo do sistema.
- [x] Proxy de desenvolvimento do Vite para a API.

**Atenção:** as telas dos módulos acadêmicos ainda são provisórias e não representam CRUDs frontend concluídos. A integração de consultas, cadastros, atualizações e operações com a API será realizada progressivamente.

## Perfis de acesso

O backend possui os seguintes perfis:
- **Administrador:** gerenciamento geral do sistema.
- **Gestor:** funcionalidades administrativas autorizadas.
- **Secretaria:** operações escolares autorizadas.
- **Professor:** funcionalidades relacionadas às suas turmas, disciplinas, horários e frequências.

O acesso às operações é controlado pelas permissões cadastradas no backend. A integração completa dessas permissões com as ações da interface frontend ainda está em desenvolvimento.

## Estrutura do projeto

```text
gestao-escolar/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── database.py
│   │   └── main.py
│   ├── migrations/
│   │   └── versions/
│   ├── scripts/
│   ├── tests/
│   ├── .env.example
│   ├── alembic.ini
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── auth/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── styles/
│   ├── .env.example
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.ts
│
├── .gitignore
└── README.md
```

## Requisitos

- Python instalado.
- Node.js e npm instalados.
- PostgreSQL instalado e em execução.

## Como executar o backend

### 1. Clonar o repositório

```powershell
git clone https://github.com/Tiago-MdrS/Gestao_Escolar.git
cd Gestao_Escolar
```

### 2. Criar e ativar o ambiente virtual

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar as dependências

```powershell
python -m pip install -r requirements.txt
```

### 4. Configurar as variáveis de ambiente

```powershell
Copy-Item .env.example .env
```

Configure no arquivo `.env` a conexão com o PostgreSQL e as variáveis de segurança da aplicação.

**Nunca publique o arquivo `.env`, senhas, tokens ou chaves secretas no GitHub.**

### 5. Criar o banco e aplicar as migrações

Crie previamente o banco de dados PostgreSQL e configure sua conexão no `.env`.

Depois execute:

```powershell
python -m alembic upgrade head
```

### 6. Inicializar perfis e permissões

```powershell
python .\scripts\seed_perfis_permissoes.py
```

### 7. Executar a API

```powershell
python -m uvicorn app.main:app --reload
```

A API estará disponível em:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Como executar o frontend

Em outro terminal PowerShell:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

O Vite exibirá o endereço local para acessar a aplicação, normalmente:

http://localhost:5173

O frontend utiliza o proxy `/api` configurado no Vite para encaminhar as requisições ao backend em `http://127.0.0.1:8000`.

### Compilar o frontend

```powershell
npm run build
```

## Migrações do banco de dados

O projeto utiliza Alembic para controlar a evolução do esquema do banco.

Criar uma migração:

```powershell
python -m alembic revision --autogenerate -m "descricao_da_migracao"
```

Aplicar migrações:

```powershell
python -m alembic upgrade head
```

Consultar a revisão atual:

```powershell
python -m alembic current
```

## Testes

Os testes automatizados do backend utilizam Pytest:

```powershell
python -m pytest
```

A compilação do frontend pode ser verificada com:

```powershell
npm run build
```

## Próximas etapas

- [ ] Implementar os CRUDs frontend dos módulos acadêmicos.
- [ ] Integrar alunos, responsáveis e vínculos à API.
- [ ] Integrar turmas, disciplinas, professores e matrículas.
- [ ] Integrar horários e frequência.
- [ ] Integrar avaliações, notas e recuperações.
- [ ] Integrar calendário escolar e relatórios.
- [ ] Aplicar controle de permissões nas ações da interface.
- [ ] Ampliar testes de integração entre frontend e backend.

## Status do projeto

**Em desenvolvimento.**

O backend já possui módulos administrativos e acadêmicos implementados. O frontend está estruturado, com autenticação integrada e navegação inicial, e seguirá em expansão até contemplar os fluxos completos do sistema.
