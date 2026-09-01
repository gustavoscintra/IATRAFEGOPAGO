# Dashboard Meta Ads — Scaland

Dashboard consolidado semanal da carteira de contas Meta Ads da agência,
alimentado pelo conector MCP da Meta.

## Estrutura

```
config.py                  Thresholds, presets de data, campos, client_conversation_id
scripts/
  parse_utils.py           Parsers dos valores formatados pt-BR que o MCP devolve
  analyze.py                Lê snapshot(s) JSON, normaliza e calcula alertas
  generate_dashboard.py     Gera output/dashboard.html
  generate_pdf.py           Gera output/dashboard.pdf
data/snapshots/             JSON brutos por rodada (git-ignorado — dados de cliente)
output/                     dashboard.html / dashboard.pdf (git-ignorado — gerado)
.claude/skills/atualizar-dashboard-meta-ads/SKILL.md
                            Runbook que o Claude segue pra coletar os dados via MCP
```

## Como rodar

**Via Claude Code:** peça "atualizar o dashboard Meta Ads" (ou invoque a
skill `atualizar-dashboard-meta-ads`). Ele lista as contas, filtra as
ativas/consultáveis, puxa as métricas (aprovando cada leitura MCP) e
gera o HTML + PDF automaticamente.

**Manualmente, a partir de um snapshot já salvo** (sem precisar do MCP —
útil pra ajustar thresholds/layout e regenerar rápido):

```bash
pip install -r requirements.txt   # só a 1ª vez (reportlab, pro PDF)
python3 scripts/generate_dashboard.py --current data/snapshots/<atual>.json --previous data/snapshots/<anterior>.json
python3 scripts/generate_pdf.py       --current data/snapshots/<atual>.json --previous data/snapshots/<anterior>.json
```

Sem `--current`/`--previous`, o script usa o snapshot mais recente em
`data/snapshots/` (sem comparação com período anterior).

## Semáforo de fadiga

Definido em `config.py` → `THRESHOLDS`:
- **Frequência alta**: frequência > 3 no período.
- **CTR caindo**: queda relativa de CTR ≥ 20% vs. o período anterior.
- **CPM disparando**: alta relativa de CPM ≥ 20% vs. o período anterior.

Conta "Crítico" (vermelho) quando tem 2+ alertas ao mesmo tempo, ou
frequência > 4,5. Ajuste os números em `THRESHOLDS` conforme calibrar.

## Filtro de contas

Só entram contas com `is_queryable=true`, `is_ads_mcp_enabled=true`,
`account_status=ACTIVE` e sem `is_ads_mcp_disabled_reason`. Contas sem
gasto no período aparecem no dashboard com métricas zeradas, mas não têm
campanhas nem período anterior buscados (economiza aprovações de leitura).
