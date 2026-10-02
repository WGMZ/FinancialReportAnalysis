"""Parse AFS/HTM portfolio economics out of the rendered XBRL securities notes.

The rendered tables are "label on one line, then one value per date column", so we
anchor on the label and take the first value (most recent balance-sheet date).
We also hunt for the weighted-average maturity / yield disclosures, which is what
lets us turn an unrealized loss into an implied duration.
"""

import json
import os
import re

import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..", "data", "sec")
REPORTS = os.path.join(BASE, "reports")

NUM = re.compile(r"^\$?\s*\(?-?[\d,]+(?:\.\d+)?\)?%?$")


def to_num(s: str) -> float | None:
    s = s.strip().replace("$", "").replace(",", "").replace("%", "").strip()
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    if not s or s in {"-", "--"}:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def first_value_after(lines: list[str], label_pat: str, window: int = 6) -> float | None:
    rex = re.compile(label_pat, re.I)
    for i, ln in enumerate(lines):
        if rex.fullmatch(ln.strip()):
            for j in range(i + 1, min(len(lines), i + 1 + window)):
                cand = lines[j].strip()
                if NUM.match(cand):
                    return to_num(cand)
                if cand.startswith("[") or cand == "":
                    continue
                break
    return None


def parse_duration_str(s: str) -> float | None:
    """'8 years 1 month 6 days' -> 8.1"""
    y = re.search(r"(\d+)\s*years?", s, re.I)
    m = re.search(r"(\d+)\s*months?", s, re.I)
    d = re.search(r"(\d+)\s*days?", s, re.I)
    if not (y or m or d):
        return None
    return ((int(y.group(1)) if y else 0)
            + (int(m.group(1)) if m else 0) / 12
            + (int(d.group(1)) if d else 0) / 365)


def scan_file(path: str) -> list[str]:
    with open(path) as fh:
        return fh.read().split("\n")


def units_scale(lines: list[str]) -> float:
    head = "\n".join(lines[:12]).lower()
    if "in millions" in head:
        return 1e6
    if "in thousands" in head:
        return 1e3
    if "in billions" in head:
        return 1e9
    return 1.0


def portfolio_block(lines: list[str], scale: float) -> dict:
    return {
        "amortized_cost": (first_value_after(lines, r"Amortized Cost") or 0) * scale or None,
        "unrealized_gains": (lambda v: v * scale if v is not None else None)(
            first_value_after(lines, r"(?:Gross )?Unrealized (?:Holding )?Gains?")),
        "unrealized_losses": (lambda v: v * scale if v is not None else None)(
            first_value_after(lines, r"(?:Gross )?Unrealized (?:Holding )?Loss(?:es)?")),
        "fair_value": (lambda v: v * scale if v is not None else None)(
            first_value_after(lines, r"Fair Value")),
    }


def find_wam_way(lines: list[str]) -> dict:
    out = {}
    txt = "\n".join(lines)
    for i, ln in enumerate(lines):
        low = ln.lower().strip()
        if re.search(r"weighted[- ]?\s*average maturity", low) and "yield" not in low:
            for j in range(i + 1, min(len(lines), i + 8)):
                dur = parse_duration_str(lines[j])
                if dur:
                    out.setdefault("wam_years", dur)
                    break
        if re.search(r"weighted[- ]?average yield", low):
            for j in range(i + 1, min(len(lines), i + 8)):
                v = to_num(lines[j])
                if v is not None and 0 < v < 15:
                    out.setdefault("wavg_yield_pct", v)
                    break
    # fallback: any 'N years M months' right after a 'Total' inside a maturity table
    if "wam_years" not in out:
        for m in re.finditer(r"(\d+)\s*years?\s*(?:(\d+)\s*months?)?", txt):
            dur = parse_duration_str(m.group(0))
            if dur and 0.5 < dur < 30:
                out["wam_years"] = dur
                break
    return out


def pick(files: list[str], *pats: str) -> str | None:
    for p in pats:
        for f in files:
            if re.search(p, f, re.I):
                return f
    return None


def main() -> None:
    uni = json.load(open(os.path.join(BASE, "universe.json")))
    rows = []
    for tkr in sorted(uni["cik"]):
        d = os.path.join(REPORTS, tkr, "10-Q_2026-06-30")
        if not os.path.isdir(d):
            # fall back to whatever latest period we have
            cand = sorted([x for x in os.listdir(os.path.join(REPORTS, tkr))
                           if x.startswith("10-")], reverse=True) if os.path.isdir(os.path.join(REPORTS, tkr)) else []
            if not cand:
                continue
            d = os.path.join(REPORTS, tkr, cand[0])
        files = os.listdir(d)
        rec = {"ticker": tkr, "period": os.path.basename(d)}

        afs_f = pick(files, r"available[_ ]for[_ ]sale.*detail", r"available[_ ]for[_ ]sale")
        htm_f = pick(files, r"held[_ ]to[_ ]maturity.*detail", r"held[_ ]to[_ ]maturity")
        mat_f = pick(files, r"maturity.*yield", r"contractual_maturity", r"by_maturity")

        if afs_f:
            ln = scan_file(os.path.join(d, afs_f))
            b = portfolio_block(ln, units_scale(ln))
            rec.update({f"afs_{k}": v for k, v in b.items()})
            rec["afs_src"] = afs_f
        if htm_f:
            ln = scan_file(os.path.join(d, htm_f))
            b = portfolio_block(ln, units_scale(ln))
            rec.update({f"htm_{k}": v for k, v in b.items()})
            rec["htm_src"] = htm_f
        if mat_f:
            ln = scan_file(os.path.join(d, mat_f))
            rec.update(find_wam_way(ln))
            rec["mat_src"] = mat_f
        rows.append(rec)

    df = pd.DataFrame(rows).set_index("ticker")
    df.to_csv(os.path.join(BASE, "securities_q2_2026.csv"))
    show = ["afs_amortized_cost", "afs_unrealized_losses", "afs_fair_value",
            "htm_amortized_cost", "htm_unrealized_losses", "htm_fair_value",
            "wam_years", "wavg_yield_pct"]
    out = df.reindex(columns=show).dropna(how="all")
    pd.set_option("display.width", 220)
    print((out / 1e9).round(2).to_string())
    print(f"\nwritten -> {os.path.join(BASE, 'securities_q2_2026.csv')}")


if __name__ == "__main__":
    main()
