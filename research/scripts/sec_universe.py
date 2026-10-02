"""Resolve the Finance-sector universe to SEC CIKs and cache each company's filing index."""

import json
import os
import time

import requests

HDRS = {"User-Agent": "Independent Research equity-research@example.com",
        "Accept-Encoding": "gzip, deflate"}

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "sec")
os.makedirs(OUT, exist_ok=True)

# Finance-sector universe, grouped by business model because that is what drives the
# Q3-2026 dispersion we are trying to forecast.
UNIVERSE = {
    "GSIB_universal": ["JPM", "BAC", "C", "WFC"],
    "GSIB_ibank": ["GS", "MS"],
    # FITB absorbed Comerica (closed 2026-02-02), HBAN absorbed Cadence (2026-02),
    # PNFP is the Pinnacle/Synovus merger of equals (2026-01-01), PNC bought FirstBank (2026-01).
    # Webster was taken out by Santander (2026-08) and no longer files.
    "supraregional": ["USB", "PNC", "TFC", "MTB", "FITB", "CFG", "KEY", "RF", "HBAN", "PNFP"],
    "regional": ["ZION", "WAL", "EWBC", "FHN", "PB", "CFR", "WTFC", "ONB", "BOKF"],
    "trust_custody": ["BNY", "STT", "NTRS"],
    "broker_wealth": ["SCHW", "RJF", "IBKR", "LPLA", "AMP", "SF"],
    "card_consumer": ["COF", "AXP", "SYF", "ALLY", "BFH", "OMF"],
    "exchanges_data": ["CME", "ICE", "NDAQ", "CBOE", "MKTX", "TW", "MCO", "SPGI"],
    "asset_mgmt": ["BLK", "TROW", "BEN", "IVZ", "AB", "JHG"],
    "alternatives": ["BX", "KKR", "APO", "ARES", "CG", "TPG", "OWL", "BAM"],
    "payments": ["V", "MA", "FIS", "FISV", "GPN"],
    "mortgage_misc": ["RKT", "UWMC", "COOP", "PFSI"],
}

ALL = sorted({t for v in UNIVERSE.values() for t in v})


def main() -> None:
    r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=HDRS, timeout=60)
    r.raise_for_status()
    book = r.json()
    tick2cik = {}
    for row in book.values():
        tick2cik.setdefault(row["ticker"].upper(), f"{int(row['cik_str']):010d}")

    resolved, missing = {}, []
    for t in ALL:
        if t in tick2cik:
            resolved[t] = tick2cik[t]
        else:
            missing.append(t)

    with open(os.path.join(OUT, "universe.json"), "w") as fh:
        json.dump({"groups": UNIVERSE, "cik": resolved, "missing": missing}, fh, indent=2)

    print(f"resolved {len(resolved)}/{len(ALL)}; missing={missing}")
    for t, c in sorted(resolved.items()):
        print(f"  {t:6s} {c}")


if __name__ == "__main__":
    main()
