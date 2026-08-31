"""Lê snapshot(s) JSON e monta as linhas já normalizadas (números + alertas)
usadas tanto pelo gerador de HTML quanto pelo de PDF.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import THRESHOLDS  # noqa: E402
from scripts.parse_utils import (  # noqa: E402
    parse_currency,
    parse_number,
    parse_percent,
    parse_cost_per_result,
    parse_results,
)


def load_snapshot(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _normalize_account_metrics(raw):
    return {
        "amount_spent": parse_currency(raw.get("amount_spent")),
        "impressions": parse_number(raw.get("impressions")),
        "clicks": parse_number(raw.get("clicks")),
        "ctr": parse_percent(raw.get("ctr")),
        "cpm": parse_currency(raw.get("cpm")),
        "reach": parse_number(raw.get("reach")),
        "frequency": parse_number(raw.get("frequency")),
        "link_click": parse_number(raw.get("link_click")),
    }


def _normalize_campaign(raw):
    cost_per_result, result_label = parse_cost_per_result(raw.get("cost_per_result"))
    results_value, results_indicator = parse_results(raw.get("results"))
    return {
        "id": raw.get("id"),
        "name": raw.get("name"),
        "objective": raw.get("objective"),
        "effective_status": raw.get("effective_status"),
        "daily_budget": parse_currency(raw.get("daily_budget")),
        "amount_spent": parse_currency(raw.get("amount_spent")),
        "impressions": parse_number(raw.get("impressions")),
        "clicks": parse_number(raw.get("clicks")),
        "ctr": parse_percent(raw.get("ctr")),
        "cpm": parse_currency(raw.get("cpm")),
        "reach": parse_number(raw.get("reach")),
        "frequency": parse_number(raw.get("frequency")),
        "link_click": parse_number(raw.get("link_click")),
        "cost_per_result": cost_per_result,
        "result_label": result_label,
        "results": results_value,
        "results_indicator": results_indicator,
    }


def _relative_change_pct(current, previous):
    """(previous -> current) variação relativa em %. None se não der pra calcular."""
    if current is None or previous is None or previous == 0:
        return None
    return (current - previous) / previous * 100.0


def _compute_alerts(metrics, prev_metrics):
    freq = metrics.get("frequency")
    ctr = metrics.get("ctr")
    cpm = metrics.get("cpm")
    prev_ctr = prev_metrics.get("ctr") if prev_metrics else None
    prev_cpm = prev_metrics.get("cpm") if prev_metrics else None

    ctr_drop_pct = None
    if ctr is not None and prev_ctr is not None:
        change = _relative_change_pct(ctr, prev_ctr)
        if change is not None and change < 0:
            ctr_drop_pct = -change

    cpm_spike_pct = None
    if cpm is not None and prev_cpm is not None:
        change = _relative_change_pct(cpm, prev_cpm)
        if change is not None and change > 0:
            cpm_spike_pct = change

    flags = []
    freq_alert = freq is not None and freq > THRESHOLDS["frequency_alert"]
    if freq_alert:
        flags.append("frequencia_alta")
    ctr_alert = ctr_drop_pct is not None and ctr_drop_pct >= THRESHOLDS["ctr_drop_pct"]
    if ctr_alert:
        flags.append("ctr_caindo")
    cpm_alert = cpm_spike_pct is not None and cpm_spike_pct >= THRESHOLDS["cpm_spike_pct"]
    if cpm_alert:
        flags.append("cpm_disparando")

    freq_severe = freq is not None and freq > THRESHOLDS["frequency_alert"] * 1.5
    if len(flags) >= 2 or freq_severe:
        status = "red"
    elif len(flags) == 1:
        status = "yellow"
    else:
        status = "green"

    return {
        "status": status,
        "flags": flags,
        "ctr_drop_pct": ctr_drop_pct,
        "cpm_spike_pct": cpm_spike_pct,
    }


def build_account_rows(current_snapshot, previous_snapshot=None):
    prev_by_id = {}
    if previous_snapshot:
        for acc in previous_snapshot.get("accounts", []):
            prev_by_id[acc["ad_account_id"]] = acc

    rows = []
    for acc in current_snapshot.get("accounts", []):
        metrics = _normalize_account_metrics(acc.get("account_metrics_raw", {}))
        prev_acc = prev_by_id.get(acc["ad_account_id"])
        prev_metrics = (
            _normalize_account_metrics(prev_acc.get("account_metrics_raw", {}))
            if prev_acc
            else None
        )

        campaigns = [_normalize_campaign(c) for c in acc.get("campaigns_raw", [])]
        active_campaigns = [
            c for c in campaigns if c.get("effective_status") == "ACTIVE" and (c.get("amount_spent") or 0) > 0
        ]

        alerts = _compute_alerts(metrics, prev_metrics)

        rows.append(
            {
                "ad_account_id": acc["ad_account_id"],
                "ad_account_name": acc.get("ad_account_name"),
                "currency": acc.get("currency", "BRL"),
                "metrics": metrics,
                "prev_metrics": prev_metrics,
                "campaigns": campaigns,
                "active_campaign_count": len(active_campaigns),
                "alerts": alerts,
            }
        )

    rows.sort(key=lambda r: (r["metrics"].get("amount_spent") or 0), reverse=True)
    return rows


def find_latest_snapshot(data_dir):
    snapshots = sorted(Path(data_dir).glob("*.json"))
    return snapshots[-1] if snapshots else None
