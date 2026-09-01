// Tipos escritos à mão pra bater com supabase/schema.sql.
// Depois que o projeto Supabase existir, dá pra trocar por tipos gerados de
// verdade com `npx supabase gen types typescript --project-id SEU_ID` — mas
// não é obrigatório, este arquivo já cobre o que o app usa.

export type Papel = 'dono' | 'vendedor' | 'gestor'
export type ClienteStatus = 'ativo' | 'pausado' | 'encerrado'
export type Plano = 'Start' | 'Growth' | 'Pro'
export type LeadEtapa = 'Novo' | '1º toque' | 'Follow-up' | 'Conversa' | 'Reunião' | 'Fechado' | 'Perdido'
export type TarefaStatus = 'A fazer' | 'Fazendo' | 'Feito'
export type ReceitaTipo = 'nova' | 'upsell' | 'churn'

export interface Usuario {
  id: string
  nome: string
  papel: Papel
  created_at: string
}

export interface Cliente {
  id: string
  dono_id: string | null
  nome: string
  nicho: string | null
  status: ClienteStatus
  plano: Plano
  contato: string | null
  telefone: string | null
  created_at: string
}

export interface Lead {
  id: string
  dono_id: string | null
  client_id: string | null
  nome: string
  negocio: string | null
  telefone: string | null
  email: string | null
  instagram: string | null
  canal: string | null
  etapa: LeadEtapa
  proxima_etapa: string | null
  anotacoes: string | null
  created_at: string
}

export interface Tarefa {
  id: string
  cliente_id: string
  responsavel_id: string | null
  titulo: string
  status: TarefaStatus
  prazo: string | null
  created_at: string
}

export interface Contrato {
  id: string
  cliente_id: string
  plano: Plano | null
  valor_mensal: number | null
  inicio: string | null
  fim: string | null
  created_at: string
}

export interface ReceitaMrr {
  id: string
  contrato_id: string
  mes_ref: string
  valor: number
  tipo: ReceitaTipo
  created_at: string
}

export interface Database {
  public: {
    Tables: {
      usuario: { Row: Usuario; Insert: Partial<Usuario> & { id: string; nome: string }; Update: Partial<Usuario> }
      cliente: { Row: Cliente; Insert: Partial<Cliente> & { nome: string }; Update: Partial<Cliente> }
      lead: { Row: Lead; Insert: Partial<Lead> & { nome: string }; Update: Partial<Lead> }
      tarefa: { Row: Tarefa; Insert: Partial<Tarefa> & { cliente_id: string; titulo: string }; Update: Partial<Tarefa> }
      contrato: { Row: Contrato; Insert: Partial<Contrato> & { cliente_id: string }; Update: Partial<Contrato> }
      receita_mrr: { Row: ReceitaMrr; Insert: Partial<ReceitaMrr> & { contrato_id: string; mes_ref: string; valor: number; tipo: ReceitaTipo }; Update: Partial<ReceitaMrr> }
    }
  }
}
