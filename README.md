# Gestão Escolar C.B.B.P.

Sistema de Gestão Escolar desenvolvido para o **Colégio Batista Bob Pierce (C.B.B.P.)**, com o objetivo de centralizar e modernizar os processos administrativos e acadêmicos da instituição.

O projeto utiliza uma API REST desenvolvida em Python com FastAPI, uma aplicação web em React e banco de dados PostgreSQL.

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
- [x] Validação de matrícula ativa e capacidade das turmas.

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

## Funcionalidades do frontend

O frontend possui autenticação integrada ao backend, navegação protegida e páginas próprias para os principais módulos administrativos e acadêmicos.

### Estrutura e autenticação
- [x] Estrutura React com TypeScript e Vite.
- [x] Tela de login integrada à API.
- [x] Autenticação por token JWT.
- [x] Recuperação da sessão por meio do endpoint `/auth/me`.
- [x] Armazenamento local do token de acesso.
- [x] Rotas protegidas para usuários autenticados.
- [x] Layout principal com menu lateral.
- [x] Navegação organizada conforme os perfis de acesso.
- [x] Tema visual baseado no protótipo do sistema.
- [x] Proxy de desenvolvimento do Vite para a API.

### Módulos administrativos e acadêmicos
- [x] Página de gerenciamento de alunos.
- [x] Página de gerenciamento de turmas.
- [x] Página de gerenciamento de responsáveis.
- [x] Página de gerenciamento de matrículas.
- [x] Página de gerenciamento de professores.
- [x] Página de gerenciamento de disciplinas.
- [x] Página de gerenciamento de horários.
- [x] Seleção de turma, disciplina e professor nos vínculos utilizados pela grade horária.

As páginas possuem interfaces próprias para consulta e gerenciamento dos respectivos módulos. A integração e validação dos fluxos com a API continuam em evolução.

### Integração e controle de acesso
- [x] Serviço centralizado para comunicação com a API.
- [x] Integração da autenticação com o backend.
- [x] Organização das rotas e páginas por módulo.
- [ ] Concluir a aplicação das permissões em todas as ações da interface.
- [ ] Ampliar a validação dos fluxos entre frontend e backend.

## Perfis de acesso

O backend possui os seguintes perfis:

- **Administrador:** gerenciamento geral do sistema.
- **Gestor:** funcionalidades administrativas autorizadas.
- **Secretaria:** operações escolares autorizadas.
- **Professor:** funcionalidades relacionadas às suas turmas, disciplinas, horários e frequências.

O acesso às operações é controlado pelas permissões cadastradas no backend. A aplicação dessas permissões em todas as funcionalidades da interface frontend está em desenvolvimento.

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

- [ ] Concluir e validar os fluxos de CRUD dos módulos frontend.
- [ ] Aprimorar a integração de alunos, responsáveis e vínculos.
- [ ] Aprimorar a integração de turmas, disciplinas, professores e matrículas.
- [ ] Concluir a integração de horários e frequência.
- [ ] Desenvolver a interface de avaliações, notas e recuperações.
- [ ] Desenvolver a interface do calendário escolar e relatórios.
- [ ] Aplicar e validar as permissões em todas as ações da interface.
- [ ] Ampliar os testes de integração entre frontend e backend.
- [ ] Realizar testes completos dos fluxos administrativos e acadêmicos.

## Status do projeto

**Em desenvolvimento.**

O backend já conta com módulos administrativos e acadêmicos, autenticação JWT, controle de permissões e regras de negócio. O frontend possui autenticação integrada, layout principal e páginas dedicadas aos principais módulos de gestão escolar.

O desenvolvimento continua concentrado na evolução das interfaces, integração dos fluxos com a API, aplicação das permissões e validação do funcionamento completo do sistema.
