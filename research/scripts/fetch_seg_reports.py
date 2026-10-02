"""Pull the FY2025 10-K and Q3-2025 10-Q rendered tables for the big-bank revenue-line history.

The 10-Qs already on disk cover Q1/Q2 2025-26; the Q3-25 10-Q (Q3'25 and the 9M YTD) and the
FY25 10-K let us derive Q3'25 and Q4'25 for lines XBRL companyfacts leaves untagged.
"""
import json
import os
import sys

import fetch_filing_reports as f

uni = json.load(open(os.path.join(f.BASE, "universe.json")))["cik"]
WANT_DATES = {"2025-09-30": "10-Q", "2025-12-31": "10-K"}
for tkr in sys.argv[1:] or ["BAC", "C", "WFC", "GS"]:
    cik = uni[tkr]
    r = f.get(f"https://data.sec.gov/submissions/CIK{cik}.json")
    rec = r.json()["filings"]["recent"]
    for form, acc, rep in zip(rec["form"], rec["accessionNumber"], rec["reportDate"]):
        if WANT_DATES.get(rep) == form:
            n = f.pull(cik, tkr, {"form": form, "accession": acc.replace("-", ""), "report_date": rep})
            print(tkr, form, rep, n, flush=True)
