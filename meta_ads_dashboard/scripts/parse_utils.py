"""Parsers para os valores formatados (pt-BR) que o MCP da Meta devolve.

Exemplos reais observados:
  amount_spent: "R$226,83 BRL"
  ctr:          "3,18%"
  frequency:    "3.370647"   (esse já vem com ponto, não vírgula)
  daily_budget: "R$33,00 BRL"
  cost_per_result: {"value": "R$56,71 BRL (Website purchases)"}
  results:      {"indicator": "...", "values": [{"value": "4", ...}]}
"""
import re

_CURRENCY_RE = re.compile(r"-?[\d.,]+")


def parse_number(raw):
    """Converte string numérica pt-BR ou já-numérica em float. None/'Not available' -> None."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip()
    if not text or text.lower() in ("not available", "n/a", "-", "none"):
        return None
    match = _CURRENCY_RE.search(text)
    if not match:
        return None
    num = match.group(0)
    if "," in num and "." in num:
        # formato pt-BR: milhar com ponto, decimal com vírgula -> normaliza
        num = num.replace(".", "").replace(",", ".")
    elif "," in num:
        num = num.replace(",", ".")
    try:
        return float(num)
    except ValueError:
        return None


def parse_currency(raw):
    """'R$226,83 BRL' -> 226.83"""
    return parse_number(raw)


def parse_percent(raw):
    """'3,18%' -> 3.18 (percentual, não fração)"""
    return parse_number(raw)


def parse_cost_per_result(raw):
    """{'value': 'R$56,71 BRL (Website purchases)'} -> (56.83, 'Website purchases')"""
    if not raw:
        return None, None
    value_str = raw.get("value") if isinstance(raw, dict) else raw
    if not value_str:
        return None, None
    label_match = re.search(r"\(([^)]+)\)\s*$", value_str)
    label = label_match.group(1) if label_match else None
    return parse_number(value_str), label


def parse_results(raw):
    """{'indicator': '...', 'values': [{'value': '4'}]} -> (4.0, 'actions:offsite_conversion...')"""
    if not raw or not isinstance(raw, dict):
        return None, None
    indicator = raw.get("indicator")
    values = raw.get("values") or []
    if not values:
        return None, indicator
    total = 0.0
    found = False
    for entry in values:
        val = parse_number(entry.get("value"))
        if val is not None:
            total += val
            found = True
    return (total if found else None), indicator
