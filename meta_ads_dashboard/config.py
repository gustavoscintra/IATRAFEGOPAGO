"""Configuração central do dashboard Meta Ads da Scaland."""

# Fixo para toda a sessão de conversa com o MCP (20 chars alfanuméricos).
CLIENT_CONVERSATION_ID = "scalanddashboard2026"

# Filtros de conta consultável (não mexer sem revalidar com ads_get_ad_accounts).
ACCOUNT_FILTERS = {
    "is_queryable": True,
    "is_ads_mcp_enabled": True,
    "account_status": "ACTIVE",
}

# Presets de janela de data disponíveis para o usuário escolher ao rodar.
# chave -> date_preset do Meta (usado direto em ads_get_ad_entities).
DATE_PRESETS = {
    "diario": "yesterday",
    "7_dias": "last_7d",
    "30_dias": "last_30d",
    "mes_atual": "this_month",
    "mes_passado": "last_month",
    "3_meses": "last_90d",
    "anual": "this_year",
}

DEFAULT_DATE_PRESET_KEY = "7_dias"

# Thresholds do semáforo de fadiga / atenção.
THRESHOLDS = {
    "frequency_alert": 3.0,       # frequência > 3 em 7d = alerta (ajustar para janelas maiores manualmente)
    "ctr_drop_pct": 20.0,         # queda relativa de CTR vs período anterior
    "cpm_spike_pct": 20.0,        # alta relativa de CPM vs período anterior
}

FIELDS_ACCOUNT_LEVEL = [
    "amount_spent", "impressions", "clicks", "ctr", "cpm",
    "reach", "frequency", "link_click",
]

FIELDS_CAMPAIGN_LEVEL = [
    "name", "objective", "effective_status", "daily_budget",
    "amount_spent", "impressions", "clicks", "ctr", "cpm",
    "reach", "frequency", "link_click", "cost_per_result", "results",
]

DATA_DIR = "data/snapshots"
OUTPUT_DIR = "output"
