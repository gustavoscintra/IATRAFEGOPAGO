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
        return "<tr><td colspan='9' class='empty'>Nenhuma campanha com gasto &gt; 0 nesse período.</td></tr>"
    rows = []
    for c in campaigns:
        results_txt = fmt_num(c["results"]) if c["results"] is not None else "—"
        if c.get("result_label"):
            results_txt += f" <span class='muted'>({html.escape(c['result_label'])})</span>"
        rows.append(
            "<tr>"
            f"<td>{html.escape(c['name'] or '')}</td>"
            f"<td>{html.escape(c['objective'] or '—')}</td>"
            f"<td>{html.escape(c['effective_status'] or '—')}</td>"
            f"<td class='num'>{fmt_currency(c['daily_budget'])}</td>"
            f"<td class='num'>{fmt_currency(c['amount_spent'])}</td>"
            f"<td class='num'>{fmt_pct(c['ctr'])}</td>"
            f"<td class='num'>{fmt_currency(c['cpm'])}</td>"
            f"<td class='num'>{fmt_freq(c['frequency'])}</td>"
            f"<td class='num'>{fmt_currency(c['cost_per_result'])}</td>"
            f"<td class='num'>{results_txt}</td>"
            "</tr>"
        )
    return "".join(rows)


def account_row_html(row, idx):
    m = row["metrics"]
    alerts = row["alerts"]
    status = alerts["status"]
    flags_txt = ", ".join(FLAG_LABEL.get(f, f) for f in alerts["flags"]) or "—"

    spend = m.get("amount_spent") or 0
    ctr = m.get("ctr") or 0
    freq = m.get("frequency") or 0

    header = (
        f"<tr class='acct-row status-{status}' data-spend='{spend}' data-ctr='{ctr}' "
        f"data-freq='{freq}' data-status='{status}' data-target='detail-{idx}'>"
        f"<td class='semaforo'><span class='dot dot-{status}' title='{STATUS_LABEL[status]}'></span></td>"
        f"<td class='acct-name'>▸ {html.escape(row['ad_account_name'] or row['ad_account_id'])}"
        f"<div class='muted small'>{html.escape(row['ad_account_id'])}</div></td>"
        f"<td class='num'>{fmt_currency(spend, row['currency'])}</td>"
        f"<td class='num'>{fmt_pct(m.get('ctr'))}</td>"
        f"<td class='num'>{fmt_currency(m.get('cpm'), row['currency'])}</td>"
        f"<td class='num'>{fmt_freq(m.get('frequency'))}</td>"
        f"<td class='num'>{row['active_campaign_count']}</td>"
        f"<td class='flags'>{html.escape(flags_txt)}</td>"
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
:root{color-scheme:light dark;--bg:#0b0d10;--fg:#e7e9ec;--muted:#9aa3ad;--card:#15181c;
--border:#2a2f36;--green:#2ecc71;--yellow:#f1c40f;--red:#e74c3c;--accent:#5b9dff;}
@media (prefers-color-scheme: light){
:root{--bg:#f7f8fa;--fg:#1a1d21;--muted:#5b6470;--card:#ffffff;--border:#e2e5e9;}
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;padding:24px}
h1{font-size:20px;margin:0 0 2px}
.subtitle{color:var(--muted);font-size:13px;margin-bottom:18px}
.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:16px;
background:var(--card);border:1px solid var(--border);border-radius:10px;padding:12px 14px}
.controls label{display:flex;flex-direction:column;font-size:11px;color:var(--muted);gap:4px}
.controls input,.controls select{padding:6px 8px;border-radius:6px;border:1px solid var(--border);
background:var(--bg);color:var(--fg)}
.summary-cards{display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:12px 16px;min-width:140px}
.card .label{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
.card .value{font-size:20px;font-weight:600;margin-top:4px}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden}
th,td{padding:9px 10px;border-bottom:1px solid var(--border);text-align:left;font-size:13px}
th{cursor:pointer;color:var(--muted);font-weight:600;font-size:11px;text-transform:uppercase;user-select:none}
th:hover{color:var(--accent)}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.acct-row{cursor:pointer}
.acct-row:hover{background:rgba(91,157,255,.08)}
.status-red{background:rgba(231,76,60,.10)}
.status-yellow{background:rgba(241,196,15,.08)}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%}
.dot-green{background:var(--green)}
.dot-yellow{background:var(--yellow)}
.dot-red{background:var(--red)}
.muted{color:var(--muted)}
.small{font-size:11px}
.flags{color:var(--muted);font-size:12px}
.status-red .flags{color:var(--red);font-weight:600}
.status-yellow .flags{color:#c9930a;font-weight:600}
.campaign-table{width:100%;font-size:12px;background:transparent;border:none}
.campaign-table th{background:transparent}
.empty{color:var(--muted);font-style:italic;padding:10px}
footer{margin-top:18px;color:var(--muted);font-size:12px}
"""

JS = """
document.querySelectorAll('.acct-row').forEach(row=>{
  row.addEventListener('click', ()=>{
    const detail = document.getElementById(row.dataset.target);
    detail.style.display = detail.style.display === 'none' ? '' : 'none';
    row.querySelector('.acct-name').firstChild.textContent =
      (detail.style.display === 'none' ? '▸ ' : '▾ ');
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

document.querySelectorAll('#accounts-table th[data-sort]').forEach(th=>{
  th.addEventListener('click', ()=>{
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
<title>Dashboard Meta Ads — Scaland</title>
<style>{CSS}</style></head>
<body>
<h1>Dashboard Meta Ads — Scaland</h1>
<div class="subtitle">Gerado em {html.escape(str(meta.get('generated_at','')))} · Período: {html.escape(str(period_txt))} · {html.escape(compare_txt)}</div>

<div class="summary-cards">
  <div class="card"><div class="label">Contas ativas</div><div class="value">{len(rows)}</div></div>
  <div class="card"><div class="label">Gasto total</div><div class="value">{fmt_currency(total_spend, currency)}</div></div>
  <div class="card"><div class="label">Precisam de atenção</div><div class="value">{needing_attention}</div></div>
  <div class="card"><div class="label">Threshold frequência</div><div class="value">&gt; {THRESHOLDS['frequency_alert']}</div></div>
</div>

<div class="controls">
  <label>Gasto mínimo <input id="f-spend" type="number" value="0" step="10"></label>
  <label>CTR mínimo (%) <input id="f-ctr" type="number" value="0" step="0.1"></label>
  <label>Frequência mínima <input id="f-freq" type="number" value="0" step="0.1"></label>
  <label style="flex-direction:row;align-items:center;gap:6px">
    <input id="f-alerts" type="checkbox" style="width:auto"> Só contas com alerta
  </label>
</div>

<table id="accounts-table">
<thead><tr>
<th>Semáforo</th>
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

<footer>Clique numa linha de conta para ver as campanhas. Clique nos cabeçalhos com ▾ para ordenar.</footer>
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
