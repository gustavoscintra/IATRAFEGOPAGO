# Scaland · Sistema

App de gestão da agência (React + Vite + TypeScript + Supabase). Substitui o
protótipo `scaland-sistema.html` (que guardava tudo em `localStorage`) por um
sistema real: login, banco de dados que não some, multiusuário desde o início.

## Rodando localmente

1. Instale as dependências:
   ```bash
   npm install
   ```
2. Configure o Supabase (veja "Setup do Supabase" abaixo se ainda não fez).
3. Copie `.env.example` para `.env.local` e cole a URL e a `anon key` do seu
   projeto Supabase (Project Settings → API no painel do Supabase):
   ```bash
   cp .env.example .env.local
   ```
4. Rode o servidor de desenvolvimento:
   ```bash
   npm run dev
   ```
   Abre em `http://localhost:5173`.

`.env.local` nunca é commitado (está no `.gitignore`).

## Setup do Supabase (resumo — passo a passo completo foi dado no chat)

1. Criar conta em [supabase.com](https://supabase.com) e um novo projeto.
2. Rodar `supabase/schema.sql` inteiro no **SQL Editor** do painel.
3. Em **Authentication → Settings**, desativar "Allow new users to sign up"
   (o app não tem tela de cadastro público — usuários só entram pelo painel).
4. Criar seu usuário em **Authentication → Users → Add user** (marcar "Auto
   Confirm User"). O trigger do `schema.sql` cria automaticamente a linha
   correspondente na tabela `usuario`.
5. Copiar **Project URL** e **anon public key** em **Project Settings → API**
   pro `.env.local`. Nunca usar a `service_role key` no front-end.

## Estrutura

```
supabase/schema.sql       Única fonte de verdade do banco (tabelas + RLS)
src/lib/supabaseClient.ts Cliente Supabase (usa as env vars VITE_SUPABASE_*)
src/context/              Auth, Tema (claro/escuro), Toast
src/components/           Sidebar, AppLayout, Modal, PlaceholderPage, ProtectedRoute
src/pages/                Login + uma pasta por módulo (clientes, prospeccao, tarefas)
src/styles/tokens.css     Variáveis de cor/tema — extraído do protótipo, não mexer sem olhar lá
src/styles/layout.css     Todo o resto do CSS do protótipo (sidebar, tabelas, kanban, modal...)
src/types/database.ts     Tipos TS batendo com as tabelas do Supabase
```

## Status (Fase 1 do roadmap)

- [x] **1. Esqueleto + login** — Supabase Auth, rotas protegidas, sidebar,
      tema claro/escuro, visual idêntico ao protótipo.
- [ ] 2. Clientes — lista + ficha + CRUD + aba de tarefas.
- [ ] 3. Prospecção — kanban/lista, funil, streak/meta, conversão lead→cliente.
- [ ] 4. Tarefas — visão global.

Fase 2 (Financeiro, Indicadores) e o módulo de Tráfego Pago (dashboard Meta
Ads) ficam pra depois — aparecem no menu como "em breve" mas sem tela ainda.
