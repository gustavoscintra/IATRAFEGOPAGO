---
name: atualizar-dashboard-meta-ads
description: Roda a coleta semanal de métricas Meta Ads da carteira Scaland (via MCP) e gera o dashboard HTML + PDF consolidado. Use quando o usuário pedir para "atualizar o dashboard", "rodar a coleta da carteira" ou "/atualizar-dashboard-meta-ads".
---

# Atualizar dashboard Meta Ads — Scaland

Runbook pra Claude seguir quando o usuário pedir a atualização semanal do
dashboard consolidado de tráfego pago. Cada leitura MCP abaixo exige
aprovação manual do usuário — não tente contornar isso.

Todos os caminhos abaixo são relativos a `meta_ads_dashboard/`. Config
central (thresholds, client_conversation_id, campos) está em `config.py`.

## 1. Definir a janela de datas

Pergunte ao usuário (ou use o padrão "7 dias") qual preset ele quer, entre:
diário, 7 dias, 30 dias, mês atual, mês passado, 3 meses, anual (ver
`DATE_PRESETS` em `config.py`). Calcule:

- `current`: os N dias mais recentes terminando ontem.
- `previous`: os N dias imediatamente anteriores ao período atual (mesmo
  tamanho), usado só pra calcular queda de CTR / alta de CPM.

Use `time_range` (`{"since": "...", "until": "..."}`) explícito nas duas
chamadas em vez de `date_preset`, pra garantir que os dois períodos sejam
consistentes entre si.

## 2. Listar e filtrar as contas

Chame `ads_get_ad_accounts` (paginando com `cursor` até `next_cursor` vir
nulo). Filtre só as contas com:
- `is_queryable == true`
- `is_ads_mcp_enabled == true`
- `account_status == "ACTIVE"`
- `is_ads_mcp_disabled_reason == null`

## 3. Nível de conta (todas as contas filtradas, período atual)

Pra cada conta filtrada, chame `ads_get_ad_entities` com
`level="ad_account"`, `time_range` do período atual, e os campos de
`FIELDS_ACCOUNT_LEVEL` (`config.py`). Pode disparar em paralelo, em lotes
de ~8 chamadas por turno (cada uma pede aprovação separada).

Se a conta voltar **sem** o campo `amount_spent` (ou com métricas vazias),
trate como "sem anúncio rodando nesse período" — **não busque mais nada
pra ela** (nem período anterior, nem campanhas). Ainda assim inclua no
snapshot final com métricas vazias, pra manter visibilidade da carteira
completa.

## 4. Só pras contas com gasto > 0: período anterior + campanhas

Pra cada conta que voltou com gasto > 0 no passo 3:
- `ads_get_ad_entities` nível `ad_account`, `time_range` do período
  anterior, mesmos campos — pra comparação de CTR/CPM.
- `ads_get_ad_entities` nível `campaign`, `time_range` do período atual,
  campos de `FIELDS_CAMPAIGN_LEVEL`, com filtro
  `[{"field": "campaign.amount_spent", "operator": "GREATER_THAN", "value": ["0"]}]`.

Isso mantém o número de aprovações proporcional só às contas realmente
ativas (na carga inicial: 49 contas filtradas, 14 ativas → ~77 chamadas
em vez de ~190).

## 5. Montar os snapshots JSON

Salve dois arquivos em `data/snapshots/` (nomeados com a data e o preset,
ex. `2026-09-08_7dias_current.json` / `..._previous.json`), seguindo o
schema usado por `scripts/analyze.py`:

```json
{
  "meta": {"generated_at": "...", "time_range": {"since": "...", "until": "..."}, "client_conversation_id": "..."},
  "accounts": [
    {"ad_account_id": "...", "ad_account_name": "...", "currency": "BRL",
     "account_metrics_raw": { ...campos crus do MCP... },
     "campaigns_raw": [ { ...campos crus por campanha... } ]}
  ]
}
```

`account_metrics_raw` e os campos de `campaigns_raw` guardam exatamente o
que o MCP devolveu (strings formatadas em pt-BR tipo `"R$104,68 BRL"`,
`"3,18%"` — o parsing fica todo em `scripts/parse_utils.py`, não
pré-processe os números na mão).

## 6. Gerar os outputs

```bash
python3 scripts/generate_dashboard.py --current data/snapshots/<atual>.json --previous data/snapshots/<anterior>.json
python3 scripts/generate_pdf.py       --current data/snapshots/<atual>.json --previous data/snapshots/<anterior>.json
```

Gera `output/dashboard.html` e `output/dashboard.pdf`, já com a seção
"Ações sugeridas" (heurística em `scripts/analyze.py::suggest_actions`,
uma sugestão por flag de alerta, apontando pra campanha específica).
Publique o HTML como Artifact (atualizando o mesmo link de antes, se
houver — passe `url`) e envie o PDF como arquivo.

## 7. Ações sugeridas → execução

As sugestões nunca são executadas sozinhas. Depois de publicar, liste
pro usuário as ações do painel e pergunte se quer que alguma seja
aplicada de verdade. Se ele confirmar uma específica, use:

- **Pausar campanha**: `ads_update_entity` com `entity_type="campaign"`,
  `fields={"status": "PAUSED"}`.
- **Ajustar orçamento**: `ads_update_entity` com `fields={"daily_budget": <centavos>}`
  (valor em centavos da moeda da conta, ex. R$50,00 → `5000`).
- **Reativar**: `ads_activate_entity` (só some PAUSED→ACTIVE).

Sempre confirme qual campanha/valor exato antes de chamar — nunca execute
a partir só da sugestão sem o usuário validar a campanha e o valor.

## Coisas que já sabemos que quebram se você não tratar

- `cost_per_result` e `results` vêm como objetos, não números simples —
  já tratado em `parse_utils.parse_cost_per_result` / `parse_results`.
- `results` às vezes vem com `"value": "Not available"` (singular) em vez
  de `"values": [...]` (plural) — os parsers já tratam os dois formatos.
- `objective`, `effective_status` e `daily_budget` só existem em
  campaign/adset, não em ad_account.
- No nível de conta, `results`/`cost_per_result` não devem ser pedidos
  (a API não consolida tipos de resultado diferentes) — só peça esses
  campos no nível `campaign`.
