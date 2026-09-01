"""Gera o dashboard.html a partir de um snapshot JSON (e opcionalmente um
snapshot anterior, para calcular queda de CTR / alta de CPM).

Uso:
    python3 scripts/generate_dashboard.py --current data/snapshots/2026-08-31_7_dias.json
    python3 scripts/generate_dashboard.py --current <atual>.json --previous <anterior>.json
    python3 scripts/generate_dashboard.py   # usa o snapshot mais recente em data/snapshots/
"""
import argparse
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import DATA_DIR, OUTPUT_DIR, THRESHOLDS  # noqa: E402
from scripts.analyze import build_account_rows, find_latest_snapshot, load_snapshot  # noqa: E402

STATUS_LABEL = {"green": "OK", "yellow": "Atenção", "red": "Crítico"}
FLAG_LABEL = {
    "frequencia_alta": "Frequência alta",
    "ctr_caindo": "CTR caindo",
    "cpm_disparando": "CPM disparando",
}


def fmt_currency(value, currency="BRL"):
    if value is None:
        return "—"
    symbol = "R$" if currency == "BRL" else currency + " "
    return f"{symbol}{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_pct(value):
    return "—" if value is None else f"{value:,.2f}%".replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_num(value):
    if value is None:
        return "—"
    return f"{value:,.0f}".replace(",", ".")


def fmt_freq(value):
    return "—" if value is None else f"{value:.2f}".replace(".", ",")


def campaign_rows_html(campaigns):
    if not campaigns:
        return "<tr><td colspan='10' class='empty'>Nenhuma campanha com gasto &gt; 0 nesse período.</td></tr>"
    rows = []
    for c in campaigns:
        results_txt = fmt_num(c["results"]) if c["results"] is not None else "—"
        if c.get("result_label"):
            results_txt += f" <span class='muted'>({html.escape(c['result_label'])})</span>"
        rows.append(
            "<tr>"
            f"<td>{html.escape(c['name'] or '')}</td>"
            f"<td>{html.escape(c['objective'] or '—')}</td>"
            f"<td><span class='mini-chip'>{html.escape(c['effective_status'] or '—')}</span></td>"
            f"<td class='num mono'>{fmt_currency(c['daily_budget'])}</td>"
            f"<td class='num mono'>{fmt_currency(c['amount_spent'])}</td>"
            f"<td class='num mono'>{fmt_pct(c['ctr'])}</td>"
            f"<td class='num mono'>{fmt_currency(c['cpm'])}</td>"
            f"<td class='num mono'>{fmt_freq(c['frequency'])}</td>"
            f"<td class='num mono'>{fmt_currency(c['cost_per_result'])}</td>"
            f"<td class='num mono'>{results_txt}</td>"
            "</tr>"
        )
    return "".join(rows)


ACTION_VERB = {
    "pausar": "Pausar",
    "revisar_criativo": "Revisar criativo",
    "trocar_criativo": "Trocar criativo",
    "revisar_orcamento_segmentacao": "Revisar orçamento",
}


def actions_panel_html(rows):
    items = []
    for r in rows:
        for a in r.get("suggested_actions", []):
            hard = a["action"] in ("pausar", "trocar_criativo")
            verb_class = "verb" if hard else "verb soft"
            items.append(
                "<div class='action-item'>"
                f"<span class='{verb_class}'>{html.escape(ACTION_VERB.get(a['action'], a['action']))}</span>"
                f"<span class='acct'>{html.escape(r['ad_account_name'] or r['ad_account_id'])}</span>"
                f"<span class='msg'>{html.escape(a['message'])}</span>"
                "</div>"
            )
    body = "".join(items) if items else "<div class='actions-empty'>Nenhuma ação sugerida — carteira sem alertas nesta rodada.</div>"
    return (
        "<div class='actions-panel'><h2>Ações sugeridas</h2>"
        f"{body}"
        "<div class='actions-note'>Nenhuma ação é executada automaticamente — são só recomendações a partir dos alertas. Peça pra executar qualquer uma e ela é aplicada via Meta Ads com sua confirmação.</div>"
        "</div>"
    )


def account_row_html(row, idx):
    m = row["metrics"]
    alerts = row["alerts"]
    status = alerts["status"]
    flag_pills = "".join(
        f"<span class='flag-pill flag-{status}'>{html.escape(FLAG_LABEL.get(f, f))}</span>"
        for f in alerts["flags"]
    ) or "<span class='muted'>—</span>"

    spend = m.get("amount_spent") or 0
    ctr = m.get("ctr") or 0
    freq = m.get("frequency") or 0

    header = (
        f"<tr class='acct-row status-{status}' data-spend='{spend}' data-ctr='{ctr}' "
        f"data-freq='{freq}' data-status='{status}' data-target='detail-{idx}' "
        f"tabindex='0' role='button' aria-expanded='false'>"
        f"<td class='status-cell'><span class='chip chip-{status}'>{STATUS_LABEL[status]}</span></td>"
        f"<td class='acct-name'><span class='caret'>▸</span> {html.escape(row['ad_account_name'] or row['ad_account_id'])}"
        f"<div class='muted small mono'>{html.escape(row['ad_account_id'])}</div></td>"
        f"<td class='num mono'>{fmt_currency(spend, row['currency'])}</td>"
        f"<td class='num mono'>{fmt_pct(m.get('ctr'))}</td>"
        f"<td class='num mono'>{fmt_currency(m.get('cpm'), row['currency'])}</td>"
        f"<td class='num mono'>{fmt_freq(m.get('frequency'))}</td>"
        f"<td class='num mono'>{row['active_campaign_count']}</td>"
        f"<td class='flags'>{flag_pills}</td>"
        "</tr>"
    )
    detail = (
        f"<tr class='detail-row' id='detail-{idx}' style='display:none'>"
        "<td colspan='8'><table class='campaign-table'><thead><tr>"
        "<th>Campanha</th><th>Objetivo</th><th>Status</th><th>Orç. diário</th>"
        "<th>Gasto</th><th>CTR</th><th>CPM</th><th>Freq.</th>"
        "<th>Custo/Resultado</th><th>Resultados</th>"
        f"</tr></thead><tbody>{campaign_rows_html(row['campaigns'])}</tbody></table></td></tr>"
    )
    return header + detail


CSS = """
:root{
  color-scheme:light dark;
  --bg:#eef1f6; --surface:#ffffff; --surface-2:#f4f6fb; --border:#dde2ea;
  --ink:#171a21; --muted:#5c6577;
  --accent:#46399e; --accent-ink:#ffffff;
  --ok:#1f8f5f; --ok-bg:rgba(31,143,95,.10);
  --warn:#a8720d; --warn-bg:rgba(184,133,20,.14);
  --crit:#c43d34; --crit-bg:rgba(196,61,52,.11);
  --shadow:0 1px 2px rgba(23,26,33,.05), 0 8px 24px -16px rgba(23,26,33,.25);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#11131a; --surface:#181b24; --surface-2:#1f2330; --border:#2b2f3d;
    --ink:#e7e9f0; --muted:#9096a8;
    --accent:#9089e8; --accent-ink:#14121f;
    --ok:#3ecf8e; --ok-bg:rgba(62,207,142,.12);
    --warn:#e0a83f; --warn-bg:rgba(224,168,63,.14);
    --crit:#ea6459; --crit-bg:rgba(234,100,89,.14);
    --shadow:0 1px 2px rgba(0,0,0,.3), 0 8px 24px -16px rgba(0,0,0,.6);
  }
}
:root[data-theme="dark"]{
  --bg:#11131a; --surface:#181b24; --surface-2:#1f2330; --border:#2b2f3d;
  --ink:#e7e9f0; --muted:#9096a8;
  --accent:#9089e8; --accent-ink:#14121f;
  --ok:#3ecf8e; --ok-bg:rgba(62,207,142,.12);
  --warn:#e0a83f; --warn-bg:rgba(224,168,63,.14);
  --crit:#ea6459; --crit-bg:rgba(234,100,89,.14);
  --shadow:0 1px 2px rgba(0,0,0,.3), 0 8px 24px -16px rgba(0,0,0,.6);
}
@media (prefers-reduced-motion: reduce){ *{transition:none!important; animation:none!important} }

*{box-sizing:border-box}
body{
  margin:0; background:var(--bg); color:var(--ink); padding:28px 32px 48px;
  font:15px/1.5 "Manrope","Segoe UI",-apple-system,sans-serif;
}
.mono{font-family:"IBM Plex Mono","SFMono-Regular",Consolas,monospace}
h1{font-size:21px; font-weight:800; letter-spacing:-.01em; margin:0 0 3px; text-wrap:balance}
.subtitle{color:var(--muted); font-size:13px; margin-bottom:20px}
.subtitle .mono{font-size:12px}

.summary-cards{display:grid; grid-template-columns:repeat(4,minmax(140px,1fr)); gap:12px; margin-bottom:18px}
.card{
  background:var(--surface); border:1px solid var(--border); border-radius:12px;
  padding:14px 16px; box-shadow:var(--shadow);
}
.card .label{color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.06em; font-weight:600}
.card .value{font-family:"IBM Plex Mono",monospace; font-size:22px; font-weight:600; margin-top:6px; color:var(--ink)}
.card.attn .value{color:var(--crit)}

.controls{
  display:flex; gap:18px; flex-wrap:wrap; align-items:end; margin-bottom:16px;
  background:var(--surface); border:1px solid var(--border); border-radius:12px;
  padding:12px 16px; box-shadow:var(--shadow);
}
.controls label{display:flex; flex-direction:column; font-size:11px; color:var(--muted); gap:5px; font-weight:600; text-transform:uppercase; letter-spacing:.03em}
.controls input[type=number]{
  padding:7px 9px; border-radius:7px; border:1px solid var(--border); width:110px;
  background:var(--bg); color:var(--ink); font:14px/1 "IBM Plex Mono",monospace;
}
.controls .check-label{flex-direction:row; align-items:center; gap:7px; text-transform:none; font-weight:500}
.controls input[type=checkbox]{width:auto; accent-color:var(--accent)}
input:focus-visible, [tabindex]:focus-visible{outline:2px solid var(--accent); outline-offset:2px}

.table-wrap{overflow-x:auto; border-radius:12px; box-shadow:var(--shadow)}
table{width:100%; border-collapse:collapse; background:var(--surface); min-width:760px}
th,td{padding:11px 12px; border-bottom:1px solid var(--border); text-align:left; font-size:13.5px}
thead th{
  cursor:pointer; color:var(--muted); font-weight:700; font-size:10.5px;
  text-transform:uppercase; letter-spacing:.05em; user-select:none; background:var(--surface-2);
  border-bottom:1px solid var(--border);
}
thead th:hover, thead th:focus-visible{color:var(--accent)}
td.num{text-align:right}
.acct-row{cursor:pointer}
.acct-row:hover{background:var(--surface-2)}
.acct-row:focus-visible{outline:2px solid var(--accent); outline-offset:-2px}
.acct-row[aria-expanded="true"] .caret{transform:rotate(90deg)}
.caret{display:inline-block; color:var(--muted); transition:transform .15s ease; width:.8em}

.status-cell{border-left:4px solid transparent; padding-left:10px}
.status-yellow .status-cell{border-left-color:var(--warn); background:var(--warn-bg)}
.status-red .status-cell{border-left-color:var(--crit); background:var(--crit-bg)}
.status-green .status-cell{border-left-color:var(--ok)}

.chip{
  display:inline-block; font-size:11px; font-weight:700; padding:3px 9px; border-radius:99px;
  text-transform:uppercase; letter-spacing:.03em;
}
.chip-green{background:var(--ok-bg); color:var(--ok)}
.chip-yellow{background:var(--warn-bg); color:var(--warn)}
.chip-red{background:var(--crit-bg); color:var(--crit)}

.mini-chip{
  display:inline-block; font-size:11px; padding:2px 8px; border-radius:6px;
  background:var(--surface-2); color:var(--muted); border:1px solid var(--border);
}

.muted{color:var(--muted)}
.small{font-size:11.5px}
.flags{display:flex; flex-wrap:wrap; gap:5px}
.flag-pill{font-size:11px; padding:3px 8px; border-radius:6px; font-weight:600}
.flag-yellow{background:var(--warn-bg); color:var(--warn)}
.flag-red{background:var(--crit-bg); color:var(--crit)}

.actions-panel{
  background:var(--surface); border:1px solid var(--border); border-radius:12px;
  padding:14px 16px; margin-bottom:16px; box-shadow:var(--shadow);
}
.actions-panel h2{font-size:13px; margin:0 0 10px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted)}
.action-item{
  display:flex; gap:10px; align-items:baseline; padding:8px 0; border-top:1px solid var(--border);
}
.action-item:first-of-type{border-top:none}
.action-item .acct{font-weight:700; white-space:nowrap}
.action-item .msg{color:var(--ink); font-size:13.5px}
.action-item .verb{
  font-size:10.5px; font-weight:700; text-transform:uppercase; letter-spacing:.03em;
  padding:2px 7px; border-radius:5px; white-space:nowrap; background:var(--crit-bg); color:var(--crit);
}
.action-item .verb.soft{background:var(--warn-bg); color:var(--warn)}
.actions-empty{color:var(--muted); font-size:13px; font-style:italic}
.actions-note{color:var(--muted); font-size:11.5px; margin-top:10px}

.detail-row td{padding:0; background:var(--surface-2)}
.campaign-table{width:100%; font-size:12.5px; background:transparent; margin:2px 0 2px 20px; width:calc(100% - 20px);
  border-left:2px solid var(--border)}
.campaign-table th{background:transparent; padding:8px 12px; border-bottom:1px solid var(--border)}
.campaign-table td{padding:8px 12px}
.empty{color:var(--muted); font-style:italic; padding:12px}
footer{margin-top:16px; color:var(--muted); font-size:12px}
"""

JS = """
function toggleRow(row){
  const detail = document.getElementById(row.dataset.target);
  const willShow = detail.style.display === 'none';
  detail.style.display = willShow ? '' : 'none';
  row.setAttribute('aria-expanded', willShow ? 'true' : 'false');
}
document.querySelectorAll('.acct-row').forEach(row=>{
  row.addEventListener('click', ()=>toggleRow(row));
  row.addEventListener('keydown', (e)=>{
    if (e.key === 'Enter' || e.key === ' '){ e.preventDefault(); toggleRow(row); }
  });
});

function applyFilters(){
  const minSpend = parseFloat(document.getElementById('f-spend').value) || 0;
  const minCtr = parseFloat(document.getElementById('f-ctr').value) || 0;
  const minFreq = parseFloat(document.getElementById('f-freq').value) || 0;
  const onlyAlerts = document.getElementById('f-alerts').checked;
  document.querySelectorAll('.acct-row').forEach(row=>{
    const spend = parseFloat(row.dataset.spend);
    const ctr = parseFloat(row.dataset.ctr);
    const freq = parseFloat(row.dataset.freq);
    const status = row.dataset.status;
    let show = spend >= minSpend && ctr >= minCtr && freq >= minFreq;
    if (onlyAlerts) show = show && status !== 'green';
    row.style.display = show ? '' : 'none';
    document.getElementById(row.dataset.target).style.display = 'none';
  });
}
['f-spend','f-ctr','f-freq'].forEach(id=>document.getElementById(id).addEventListener('input', applyFilters));
document.getElementById('f-alerts').addEventListener('change', applyFilters);

function sortByHeader(th){
  const key = th.dataset.sort;
  const tbody = document.querySelector('#accounts-table tbody');
  const rows = Array.from(tbody.querySelectorAll('.acct-row'));
  const dir = th.dataset.dir === 'desc' ? 'asc' : 'desc';
  document.querySelectorAll('#accounts-table th[data-sort]').forEach(t=>t.dataset.dir='');
  th.dataset.dir = dir;
  rows.sort((a,b)=>{
    const av = parseFloat(a.dataset[key]) || 0;
    const bv = parseFloat(b.dataset[key]) || 0;
    return dir === 'desc' ? bv - av : av - bv;
  });
  rows.forEach(r=>{
    tbody.appendChild(r);
    tbody.appendChild(document.getElementById(r.dataset.target));
  });
}
document.querySelectorAll('#accounts-table th[data-sort]').forEach(th=>{
  th.setAttribute('tabindex','0');
  th.addEventListener('click', ()=>sortByHeader(th));
  th.addEventListener('keydown', (e)=>{
    if (e.key === 'Enter' || e.key === ' '){ e.preventDefault(); sortByHeader(th); }
  });
});
"""


def render_html(rows, meta, previous_meta):
    total_spend = sum((r["metrics"].get("amount_spent") or 0) for r in rows)
    currency = rows[0]["currency"] if rows else "BRL"
    needing_attention = sum(1 for r in rows if r["alerts"]["status"] != "green")

    period_txt = meta.get("date_preset") or meta.get("time_range") or "—"
    compare_txt = (
        f"Comparado com: {previous_meta.get('date_preset') or previous_meta.get('time_range')}"
        if previous_meta
        else "Sem período anterior carregado — alertas de CTR/CPM ficam desativados até rodar de novo."
    )

    body_rows = "".join(account_row_html(r, i) for i, r in enumerate(rows))

    return f"""<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dashboard Meta Ads — Scaland</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>{CSS}</style></head>
<body>
<h1>Dashboard Meta Ads — Scaland</h1>
<div class="subtitle">Gerado em <span class="mono">{html.escape(str(meta.get('generated_at','')))}</span> · Período: <span class="mono">{html.escape(str(period_txt))}</span> · {html.escape(compare_txt)}</div>

<div class="summary-cards">
  <div class="card"><div class="label">Contas ativas</div><div class="value">{len(rows)}</div></div>
  <div class="card"><div class="label">Gasto total</div><div class="value">{fmt_currency(total_spend, currency)}</div></div>
  <div class="card{' attn' if needing_attention else ''}"><div class="label">Precisam de atenção</div><div class="value">{needing_attention}</div></div>
  <div class="card"><div class="label">Threshold frequência</div><div class="value">&gt; {THRESHOLDS['frequency_alert']:.0f}</div></div>
</div>

{actions_panel_html(rows)}

<div class="controls">
  <label>Gasto mínimo <input id="f-spend" type="number" value="0" step="10"></label>
  <label>CTR mínimo (%) <input id="f-ctr" type="number" value="0" step="0.1"></label>
  <label>Frequência mínima <input id="f-freq" type="number" value="0" step="0.1"></label>
  <label class="check-label">
    <input id="f-alerts" type="checkbox"> Só contas com alerta
  </label>
</div>

<div class="table-wrap">
<table id="accounts-table">
<thead><tr>
<th>Status</th>
<th data-sort="spend">Conta ▾</th>
<th class="num" data-sort="spend">Gasto ▾</th>
<th class="num" data-sort="ctr">CTR ▾</th>
<th class="num">CPM</th>
<th class="num" data-sort="freq">Frequência ▾</th>
<th class="num">Campanhas ativas</th>
<th>Alertas</th>
</tr></thead>
<tbody>{body_rows}</tbody>
</table>
</div>

<footer>Clique numa linha de conta (ou Enter/Espaço com foco no teclado) para ver as campanhas. Clique nos cabeçalhos com ▾ para ordenar.</footer>
<script>{JS}</script>
</body></html>
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", type=str, default=None, help="Snapshot JSON atual")
    parser.add_argument("--previous", type=str, default=None, help="Snapshot JSON anterior (comparação)")
    parser.add_argument("--out", type=str, default=None, help="Caminho do HTML de saída")
    args = parser.parse_args()

    data_dir = ROOT / DATA_DIR
    current_path = Path(args.current) if args.current else find_latest_snapshot(data_dir)
    if not current_path or not current_path.exists():
        print(f"Nenhum snapshot encontrado em {data_dir}. Rode a coleta primeiro.", file=sys.stderr)
        sys.exit(1)

    current = load_snapshot(current_path)
    previous = load_snapshot(args.previous) if args.previous else None

    rows = build_account_rows(current, previous)
    out_path = Path(args.out) if args.out else ROOT / OUTPUT_DIR / "dashboard.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_html(rows, current.get("meta", {}), previous.get("meta") if previous else None),
        encoding="utf-8",
    )
    print(f"Dashboard gerado em {out_path} ({len(rows)} contas)")


if __name__ == "__main__":
    main()
