-- Scaland Sistema — schema inicial (Fase 1 + tabelas de Fase 2 já criadas, sem UI ainda)
-- Rode este arquivo inteiro no SQL Editor do painel do Supabase (Project > SQL Editor > New query > Run).
-- Pode rodar de novo com segurança em um projeto novo; NÃO rode duas vezes no mesmo projeto sem
-- limpar antes (vai reclamar de tabela/policy já existente).

-- ============================================================
-- USUARIO — 1:1 com auth.users. Só existe depois que a pessoa
-- é criada em Authentication > Users no painel do Supabase.
-- ============================================================
create table public.usuario (
  id uuid primary key references auth.users(id) on delete cascade,
  nome text not null,
  papel text not null default 'dono' check (papel in ('dono','vendedor','gestor')),
  created_at timestamptz not null default now()
);

-- Cria automaticamente uma linha em usuario sempre que alguém novo é
-- adicionado em Authentication > Users — assim você nunca precisa rodar
-- SQL manual pra cadastrar um novo membro da equipe depois.
create function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.usuario (id, nome, papel)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'nome', split_part(new.email, '@', 1)),
    'dono'
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ============================================================
-- CLIENTE
-- ============================================================
create table public.cliente (
  id uuid primary key default gen_random_uuid(),
  dono_id uuid references public.usuario(id),
  nome text not null,
  nicho text,
  status text not null default 'ativo' check (status in ('ativo','pausado','encerrado')),
  plano text not null default 'Start' check (plano in ('Start','Growth','Pro')),
  contato text,
  telefone text,
  created_at timestamptz not null default now()
);

-- ============================================================
-- LEAD (prospecção)
-- ============================================================
create table public.lead (
  id uuid primary key default gen_random_uuid(),
  dono_id uuid references public.usuario(id),
  client_id uuid references public.cliente(id),
  nome text not null,
  negocio text,
  telefone text,
  email text,
  instagram text,
  canal text,
  etapa text not null default 'Novo'
    check (etapa in ('Novo','1º toque','Follow-up','Conversa','Reunião','Fechado','Perdido')),
  proxima_etapa date,
  anotacoes text,
  created_at timestamptz not null default now()
);

-- ============================================================
-- TAREFA
-- ============================================================
create table public.tarefa (
  id uuid primary key default gen_random_uuid(),
  cliente_id uuid references public.cliente(id) on delete cascade,
  responsavel_id uuid references public.usuario(id),
  titulo text not null,
  status text not null default 'A fazer' check (status in ('A fazer','Fazendo','Feito')),
  prazo date,
  created_at timestamptz not null default now()
);

-- ============================================================
-- CONTRATO — Fase 2. Tabela criada agora, sem tela no app ainda.
-- ============================================================
create table public.contrato (
  id uuid primary key default gen_random_uuid(),
  cliente_id uuid references public.cliente(id) on delete cascade,
  plano text check (plano in ('Start','Growth','Pro')),
  valor_mensal numeric(10,2),
  inicio date,
  fim date,
  created_at timestamptz not null default now()
);

-- ============================================================
-- RECEITA_MRR — Fase 2. Tabela criada agora, sem tela no app ainda.
-- ============================================================
create table public.receita_mrr (
  id uuid primary key default gen_random_uuid(),
  contrato_id uuid references public.contrato(id) on delete cascade,
  mes_ref date not null,
  valor numeric(10,2) not null,
  tipo text not null check (tipo in ('nova','upsell','churn')),
  created_at timestamptz not null default now()
);

-- ============================================================
-- ROW LEVEL SECURITY
-- Modelo escolhido: visão compartilhada da agência — qualquer usuário
-- autenticado (logado) enxerga e edita todos os registros. dono_id /
-- responsavel_id são só informativos (quem é o responsável), não
-- restringem visibilidade. Ninguém não-autenticado acessa nada.
-- ============================================================
alter table public.usuario enable row level security;
alter table public.cliente enable row level security;
alter table public.lead enable row level security;
alter table public.tarefa enable row level security;
alter table public.contrato enable row level security;
alter table public.receita_mrr enable row level security;

-- usuario: todo autenticado pode ler (precisa pra popular dropdowns de
-- responsável); cada um só edita a própria linha.
create policy "usuario_select_all" on public.usuario
  for select to authenticated using (true);
create policy "usuario_update_self" on public.usuario
  for update to authenticated using (auth.uid() = id);

-- cliente / lead / tarefa / contrato / receita_mrr: CRUD completo pra
-- qualquer usuário autenticado.
create policy "cliente_all" on public.cliente
  for all to authenticated using (true) with check (true);
create policy "lead_all" on public.lead
  for all to authenticated using (true) with check (true);
create policy "tarefa_all" on public.tarefa
  for all to authenticated using (true) with check (true);
create policy "contrato_all" on public.contrato
  for all to authenticated using (true) with check (true);
create policy "receita_mrr_all" on public.receita_mrr
  for all to authenticated using (true) with check (true);
