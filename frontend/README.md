# Gestão Escolar C.B.B.P. — Frontend

Aplicação web do sistema Gestão Escolar C.B.B.P., desenvolvida com React, TypeScript e Vite.

## Requisitos

- Node.js
- npm
- Backend FastAPI em execução

## Configuração

No diretório `frontend`, instale as dependências:

```powershell
npm install
```

Crie o arquivo de ambiente:

```powershell
Copy-Item .env.example .env
```

A configuração padrão utiliza o proxy `/api` do Vite para encaminhar as requisições ao backend local.

## Executar em desenvolvimento

```powershell
npm run dev
```

Acesse o endereço exibido no terminal, normalmente `http://localhost:5173`.

Mantenha o terminal aberto enquanto utilizar a aplicação.

## Compilação

```powershell
npm run build
```

## Tecnologias

- React 19
- TypeScript
- Vite
- React Router
- Axios
- Lucide React

## Implementado

- Tela de login integrada ao backend.
- Autenticação JWT.
- Recuperação da sessão com `/auth/me`.
- Rotas protegidas.
- Layout principal responsivo.
- Menu lateral organizado inicialmente por perfil.
- Tema visual baseado no protótipo do sistema.
- Proxy de desenvolvimento para a API.

## Em desenvolvimento

As páginas dos módulos acadêmicos ainda são provisórias. A integração completa dos CRUDs com a API e o controle fino das permissões nas ações da interface serão implementados progressivamente.

O frontend não cria nem altera diretamente o banco de dados.

## Segurança

Não publique arquivos `.env`, tokens, senhas ou outras credenciais. Utilize `.env.example` apenas para documentar as variáveis necessárias, sem valores secretos.
