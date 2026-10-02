"""Rebuild quarterly IB-fee / market-making lines that XBRL companyfacts leaves untagged.

Sources are the rendered 10-Q/10-K R pages in data/sec/reports. A 10-Q holds the current
quarter and the prior-year quarter (plus YTD); Q4 = FY - 9M.
Output: output/seg_lines.csv  (ticker, line, quarter, usd_bn)
"""
import os
import re

import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..")
REP = os.path.join(BASE, "data", "sec", "reports")
OUT = os.path.join(BASE, "output")

NUM = re.compile(r"^\$?\s*\(?-?[\d,]+(\.\d+)?\)?$")


def nums_after(path: str, label: re.Pattern, skip_first=0) -> list[float]:
    lines = open(path, errors="ignore").read().split("\n")
    seen = 0
    for i, ln in enumerate(lines):
        if label.search(ln):
            seen += 1
            if seen <= skip_first:
                continue
            vals: list[float] = []
            for ln2 in lines[i + 1:i + 14]:
                s = ln2.strip().replace("$", "").strip()
                if NUM.match(s):
                    neg = s.startswith("(")
                    v = float(re.sub(r"[^\d.]", "", s))
                    vals.append(-v if neg else v)
                elif vals:
                    break
            if len(vals) >= 2:
                return vals
    return []


CFG = {
    ("BAC", "ib"): ("business_segment_information_noninterest_income_by_business_segment_and_all_other_details_.txt",
                    re.compile(r"^Total investment banking fees$"), 0),
    ("WFC", "ib"): ("consolidated_statement_of_income.txt", re.compile(r"^Investment banking fees \[Member\]$"), 0),
    ("GS", "mm"): ("trading_assets_and_liabilities_summary_of_market_making_revenues_by_major_product_type_det.txt",
                   re.compile(r"^Market making$"), 0),
    ("C", "nii"): ("consolidated_statement_of_income_unaudited_.txt",
                   re.compile(r"^Net interest income( \(NII\))?$"), 0),
    ("C", "trd"): ("consolidated_statement_of_income_unaudited_.txt", re.compile(r"^Principal transactions$"), 0),
    ("C", "rev"): ("consolidated_statement_of_income_unaudited_.txt",
                   re.compile(r"^Total revenues, net of interest expense$"), 0),
    ("C", "ib"): ("commissions_and_fees_administration_and_other_fiduciary_fees_commissions_and_fees_revenue_.txt",
                  re.compile(r"^Investment Banking$", re.I), 0),
}


def get(tkr, line, folder):
    fn, lab, skip = CFG[(tkr, line)]
    p = os.path.join(REP, tkr, folder, fn)
    if not os.path.exists(p):
        return []
    return nums_after(p, lab, skip)


def main():
    rows = []
    for (tkr, line) in CFG:
        q2 = get(tkr, line, "10-Q_2026-06-30")   # Q2'26, Q2'25, 6M26, 6M25
        q1 = get(tkr, line, "10-Q_2026-03-31")   # Q1'26, Q1'25
        q3 = get(tkr, line, "10-Q_2025-09-30")   # Q3'25, Q3'24, 9M25, 9M24
        fy = get(tkr, line, "10-K_2025-12-31")   # FY25, FY24, FY23
        print(tkr, line, q2, q1, q3, fy)
        d = {}
        if len(q2) >= 2:
            d["2026Q2"], d["2025Q2"] = q2[0], q2[1]
        if len(q1) >= 2:
            d["2026Q1"], d["2025Q1"] = q1[0], q1[1]
        if len(q3) >= 4:
            d["2025Q3"], d["2024Q3"] = q3[0], q3[1]
            if len(fy) >= 2:
                d["2025Q4"] = fy[0] - q3[2]
                d["2024Q4"] = fy[1] - q3[3]
        for k, v in d.items():
            rows.append({"ticker": tkr, "line": line, "quarter": k, "usd_bn": v / 1e3})
    df = pd.DataFrame(rows).sort_values(["ticker", "line", "quarter"])
    df.to_csv(os.path.join(OUT, "seg_lines.csv"), index=False)
    print(df.pivot_table(index="quarter", columns=["ticker", "line"], values="usd_bn").round(2))


if __name__ == "__main__":
    main()
