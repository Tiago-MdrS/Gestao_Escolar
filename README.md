# Gestão Escolar C.B.B.P.

Sistema de Gestão Escolar desenvolvido para o **Colégio Batista Bob Pierce (C.B.B.P.)**, com o objetivo de centralizar, organizar e modernizar os processos administrativos e acadêmicos da instituição.

## Sobre o projeto

O Gestão Escolar C.B.B.P. é uma aplicação em desenvolvimento voltada ao gerenciamento das atividades escolares, incluindo alunos, responsáveis, professores, turmas, disciplinas, matrículas, horários e frequência.

O projeto utiliza uma arquitetura com API REST no backend e uma aplicação web no frontend, priorizando organização, segurança, integridade dos dados e controle de acesso por perfil de usuário.

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

- React
- TypeScript
- Vite

## Funcionalidades implementadas

### Gestão acadêmica

- [x] Cadastro, consulta, atualização e gerenciamento de alunos.
- [x] Cadastro e gerenciamento de responsáveis.
- [x] Associação entre alunos e responsáveis.
- [x] Cadastro e gerenciamento de turmas.
- [x] Controle de matrículas.
- [x] Cadastro e gerenciamento de professores.
- [x] Cadastro de disciplinas.
- [x] Associação de professores, disciplinas e turmas.

### Autenticação e controle de acesso

- [x] Autenticação de usuários.
- [x] Login utilizando JWT.
- [x] Criptografia de senhas com Argon2.
- [x] Consulta dos dados do usuário autenticado.
- [x] Gerenciamento de usuários.
- [x] Gerenciamento de perfis.
- [x] Controle de permissões por perfil.
- [x] Proteção de rotas conforme as permissões do usuário.

### Horários de aula

- [x] Cadastro de horários.
- [x] Consulta e filtragem de horários.
- [x] Atualização e inativação de horários.
- [x] Consulta dos horários do professor autenticado.
- [x] Validação de conflitos de horários para turmas e professores.
- [x] Verificação de vínculos entre turma, disciplina e professor.

### Frequência escolar

- [x] Registro de frequência dos alunos.
- [x] Consulta geral de frequências.
- [x] Consulta de frequência por aluno.
- [x] Consulta individual de registros.
- [x] Atualização de frequência.
- [x] Registro de presença, falta e falta justificada.
- [x] Validação de matrícula ativa.
- [x] Bloqueio de registros duplicados.
- [x] Identificação do usuário responsável pelo lançamento.
- [x] Consulta das frequências das próprias turmas pelo professor.
- [x] Restrição de acesso conforme as permissões do perfil.

## Perfis de acesso

O sistema possui perfis de usuários com permissões específicas:

- **Administrador:** gerenciamento geral do sistema.
- **Gestor:** acesso às funcionalidades administrativas autorizadas.
- **Secretaria:** acesso às operações escolares autorizadas.
- **Professor:** acesso às funcionalidades relacionadas às suas turmas, disciplinas, horários e frequências.

As permissões são controladas individualmente por meio dos perfis cadastrados no sistema.

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
│
├── .gitignore
├── alembic.ini
└── README.md


Como executar o backend
1. Clonar o repositório
git clone URL_DO_REPOSITORIO
cd gestao-escolar/backend


2. Criar o ambiente virtual
python -m venv .venv


3. Ativar o ambiente virtual
Windows PowerShell:
.\.venv\Scripts\Activate.ps1


Linux:
source .venv/bin/activate


4. Instalar as dependências
python -m pip install -r requirements.txt


5. Configurar as variáveis de ambiente
Copie o arquivo .env.example para .env:

Windows PowerShell:
Copy-Item .env.example .env


Configure as variáveis necessárias para a conexão com o PostgreSQL e para a segurança da aplicação.

Importante: não compartilhe nem envie o arquivo .env ao GitHub. Utilize chaves e credenciais próprias para cada ambiente.
6. Configurar o banco de dados
Crie o banco PostgreSQL e execute as migrações:
python -m alembic upgrade head


7. Inicializar perfis e permissões
Execute o script de inicialização:
python .\scripts\seed_perfis_permissoes.py


8. Executar a aplicação
python -m uvicorn app.main:app --reload


A API estará disponível em:

http://127.0.0.1:8000
Documentação da API
A aplicação utiliza a documentação automática disponibilizada pelo FastAPI.
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
A documentação permite consultar os endpoints, visualizar os schemas e realizar requisições de teste.
Migrações do banco de dados
O projeto utiliza Alembic para controlar a evolução do esquema do banco de dados.

Criar uma nova migração:
python -m alembic revision --autogenerate -m "descricao_da_migracao"


Aplicar as migrações:
python -m alembic upgrade head


Consultar a revisão atual:
python -m alembic current


Testes
Os testes automatizados são executados com Pytest:
python -m pytest


Os principais fluxos de autenticação, autorização, horários e frequência também foram verificados por meio de requisições à API.
Próximas funcionalidades
- [ ] Cadastro e gerenciamento de avaliações.
- [ ] Lançamento de notas.
- [ ] Cálculo de médias e resultados acadêmicos.
- [ ] Boletim escolar.
- [ ] Gestão financeira.
- [ ] Painel administrativo.
- [ ] Relatórios acadêmicos.
- [ ] Interface frontend integrada à API.
Status do projeto
Em desenvolvimento.

O sistema está sendo implementado progressivamente, com módulos acadêmicos e administrativos integrados ao backend e preparados para expansão.
