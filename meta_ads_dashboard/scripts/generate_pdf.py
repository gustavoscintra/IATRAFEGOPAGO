"""Gera um PDF resumo (pra mandar por e-mail/whatsapp pro time ou clientes)
a partir do mesmo snapshot usado pelo generate_dashboard.py.

Uso:
    python3 scripts/generate_pdf.py --current <atual>.json --previous <anterior>.json
"""
import argparse
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import DATA_DIR, OUTPUT_DIR, THRESHOLDS  # noqa: E402
from scripts.analyze import build_account_rows, find_latest_snapshot, load_snapshot  # noqa: E402
from scripts.generate_dashboard import fmt_currency, fmt_pct, fmt_freq, STATUS_LABEL, FLAG_LABEL, ACTION_VERB  # noqa: E402

STATUS_COLOR = {
    "green": colors.HexColor("#1f8f5f"),
    "yellow": colors.HexColor("#a8720d"),
    "red": colors.HexColor("#c43d34"),
}
STATUS_BG = {
    "green": colors.HexColor("#eaf6f0"),
    "yellow": colors.HexColor("#fcf1dc"),
    "red": colors.HexColor("#fbe9e7"),
}


def build_pdf(rows, meta, previous_meta, out_path):
    active = [r for r in rows if (r["metrics"].get("amount_spent") or 0) > 0]
    zero = [r for r in rows if not (r["metrics"].get("amount_spent") or 0) > 0]
    total_spend = sum((r["metrics"].get("amount_spent") or 0) for r in rows)
    currency = rows[0]["currency"] if rows else "BRL"
    needing_attention = sum(1 for r in active if r["alerts"]["status"] != "green")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontSize=18, spaceAfter=2)
    sub_style = ParagraphStyle("SubX", parent=styles["Normal"], textColor=colors.HexColor("#5c6577"), fontSize=9)
    h2_style = ParagraphStyle("H2X", parent=styles["Heading2"], fontSize=12, spaceBefore=14, spaceAfter=6)
    small_style = ParagraphStyle("SmallX", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#5c6577"))
    action_style = ParagraphStyle("ActionX", parent=styles["Normal"], fontSize=9, spaceAfter=4, leftIndent=4)

    def fmt_range(mt):
        if not mt:
            return None
        tr = mt.get("time_range")
        if isinstance(tr, dict) and tr.get("since"):
            return f"{tr['since']} a {tr['until']}"
        return mt.get("date_preset")

    period_txt = fmt_range(meta) or "—"
    prev_txt = fmt_range(previous_meta)
    compare_txt = f"vs. {prev_txt}" if prev_txt else "sem período anterior"

    doc = SimpleDocTemplate(
        str(out_path), pagesize=landscape(A4),
        leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
    )
    story = [
        Paragraph("Dashboard Meta Ads — Scaland", title_style),
        Paragraph(
            f"Período: {period_txt} ({compare_txt}) · Gerado em {meta.get('generated_at', '')}", sub_style
        ),
        Spacer(1, 10),
        Paragraph(
            f"{len(active)} contas ativas · Gasto total {fmt_currency(total_spend, currency)} · "
            f"{needing_attention} precisam de atenção · threshold frequência &gt; {THRESHOLDS['frequency_alert']:.0f}",
            sub_style,
        ),
    ]

    header = ["Status", "Conta", "Gasto", "CTR", "CPM", "Freq.", "Camp. ativas", "Alertas"]
    data = [header]
    row_colors = []
    for r in active:
        m = r["metrics"]
        alerts = r["alerts"]
        flags_txt = ", ".join(FLAG_LABEL.get(f, f) for f in alerts["flags"]) or "—"
        data.append([
            STATUS_LABEL[alerts["status"]],
            r["ad_account_name"] or r["ad_account_id"],
            fmt_currency(m.get("amount_spent"), r["currency"]),
            fmt_pct(m.get("ctr")),
            fmt_currency(m.get("cpm"), r["currency"]),
            fmt_freq(m.get("frequency")),
            str(r["active_campaign_count"]),
            flags_txt,
        ])
        row_colors.append(alerts["status"])

    action_items = [(r["ad_account_name"] or r["ad_account_id"], a) for r in active for a in r.get("suggested_actions", [])]
    if action_items:
        story.append(Paragraph("Ações sugeridas", h2_style))
        for acct_name, a in action_items:
            verb = ACTION_VERB.get(a["action"], a["action"])
            story.append(Paragraph(f"<b>[{verb}]</b> {acct_name} — {a['message']}", action_style))
        story.append(Paragraph(
            "Nenhuma ação é executada automaticamente — recomendações a partir dos alertas; peça pra executar e confirmamos antes de mudar algo na Meta.",
            small_style,
        ))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Contas com investimento no período", h2_style))
    table = Table(data, repeatRows=1, colWidths=[22 * mm, 62 * mm, 24 * mm, 20 * mm, 24 * mm, 18 * mm, 24 * mm, None])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1d21")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 0), (6, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dde2ea")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, status in enumerate(row_colors, start=1):
        style.append(("BACKGROUND", (0, i), (0, i), STATUS_BG[status]))
        style.append(("TEXTCOLOR", (0, i), (0, i), STATUS_COLOR[status]))
        style.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))
    table.setStyle(TableStyle(style))
    story.append(table)

    if zero:
        story.append(Paragraph(f"Sem investimento no período ({len(zero)} contas)", h2_style))
        names = ", ".join(r["ad_account_name"] or r["ad_account_id"] for r in zero)
        story.append(Paragraph(names, small_style))

    doc.build(story)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", type=str, default=None)
    parser.add_argument("--previous", type=str, default=None)
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()

    data_dir = ROOT / DATA_DIR
    current_path = Path(args.current) if args.current else find_latest_snapshot(data_dir)
    if not current_path or not current_path.exists():
        print(f"Nenhum snapshot encontrado em {data_dir}.", file=sys.stderr)
        sys.exit(1)

    current = load_snapshot(current_path)
    previous = load_snapshot(args.previous) if args.previous else None

    rows = build_account_rows(current, previous)
    out_path = Path(args.out) if args.out else ROOT / OUTPUT_DIR / "dashboard.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    build_pdf(rows, current.get("meta", {}), previous.get("meta") if previous else None, out_path)
    print(f"PDF gerado em {out_path}")


if __name__ == "__main__":
    main()
