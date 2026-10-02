"""Pull the rendered XBRL report tables (R*.htm) out of each filer's recent filings.

FilingSummary.xml lists every statement/note the renderer produced. We keep the ones
that carry the economics we need: segment P&L, the securities portfolio (AFS/HTM
unrealized losses), the interest-rate-sensitivity tables, loans/allowance, deposits
and regulatory capital.
"""

import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

import requests

HDRS = {"User-Agent": "Independent Research equity-research@example.com",
        "Accept-Encoding": "gzip, deflate"}

BASE = os.path.join(os.path.dirname(__file__), "..", "data", "sec")
OUT = os.path.join(BASE, "reports")
os.makedirs(OUT, exist_ok=True)

WANT = [
    "segment", "business segment", "reportable segment",
    "interest rate sensitivity", "interest rate risk", "market risk",
    "net interest income sensitivity", "earnings at risk", "economic value",
    "available-for-sale", "available for sale", "held-to-maturity", "held to maturity",
    "investment securities", "debt securities", "securities portfolio",
    "amortized cost", "unrealized",
    "allowance for credit loss", "allowance for loan", "credit quality",
    "loans and leases", "loan portfolio", "deposits",
    "accumulated other comprehensive",
    "regulatory capital", "capital ratio",
    "consolidated statement of income", "consolidated balance sheet",
    "consolidated statements of income", "consolidated statements of financial condition",
    "net interest", "noninterest", "non-interest",
    "revenue", "trading", "derivative",
    "assets under management", "assets under custody",
]

SKIP = ["parenthetical", "policies", "(tables)", "policy"]


def get(url: str, tries: int = 4):
    for i in range(tries):
        try:
            r = requests.get(url, headers=HDRS, timeout=90)
            if r.status_code == 200:
                return r
            if r.status_code == 404:
                return None
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1.2 * (i + 1))
    return None


def html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    html = re.sub(r"(?i)</t[dh]>", " | ", html)
    html = re.sub(r"(?i)</tr>", "\n", html)
    html = re.sub(r"(?i)<br\s*/?>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", "", html)
    html = (html.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#160;", " ")
            .replace("&lt;", "<").replace("&gt;", ">").replace("&#8217;", "'")
            .replace("&#8212;", "-").replace("&#8211;", "-").replace("&quot;", '"'))
    lines = []
    for ln in html.split("\n"):
        ln = re.sub(r"[ \t]+", " ", ln).strip()
        ln = re.sub(r"(\s*\|\s*)+", " | ", ln).strip(" |")
        if ln:
            lines.append(ln)
    return "\n".join(lines)


def latest_filings(cik: str, forms=("10-Q", "10-K"), n: int = 2):
    r = get(f"https://data.sec.gov/submissions/CIK{cik}.json")
    if r is None:
        return []
    rec = r.json()["filings"]["recent"]
    out = []
    for form, acc, rep, fdate in zip(rec["form"], rec["accessionNumber"],
                                     rec["reportDate"], rec["filingDate"]):
        if form in forms:
            out.append({"form": form, "accession": acc.replace("-", ""),
                        "report_date": rep, "filed": fdate})
        if len(out) >= n:
            break
    return out


def pull(cik: str, tkr: str, filing: dict) -> int:
    acc = filing["accession"]
    root = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}"
    fs = get(f"{root}/FilingSummary.xml")
    if fs is None:
        print(f"    no FilingSummary for {tkr} {acc}")
        return 0
    try:
        tree = ET.fromstring(fs.content)
    except ET.ParseError:
        return 0

    dest = os.path.join(OUT, tkr, f"{filing['form']}_{filing['report_date']}")
    os.makedirs(dest, exist_ok=True)

    index = []
    saved = 0
    for rep in tree.iter("Report"):
        short = (rep.findtext("ShortName") or "").strip()
        fname = (rep.findtext("HtmlFileName") or rep.findtext("XmlFileName") or "").strip()
        if not fname or not short:
            continue
        low = short.lower()
        index.append(short)
        if any(sk in low for sk in SKIP):
            continue
        if not any(w in low for w in WANT):
            continue
        rr = get(f"{root}/{fname}")
        if rr is None:
            continue
        txt = html_to_text(rr.text)
        if len(txt) < 80:
            continue
        safe = re.sub(r"[^a-z0-9]+", "_", low)[:90]
        with open(os.path.join(dest, f"{safe}.txt"), "w") as fh:
            fh.write(f"# {short}\n# source: {root}/{fname}\n\n{txt}\n")
        saved += 1
        time.sleep(0.12)

    with open(os.path.join(dest, "_all_report_names.txt"), "w") as fh:
        fh.write("\n".join(index))
    return saved


def main() -> None:
    uni = json.load(open(os.path.join(BASE, "universe.json")))
    ciks = uni["cik"]
    targets = sys.argv[1:] or sorted(ciks)
    for tkr in targets:
        cik = ciks.get(tkr)
        if not cik:
            print(f"{tkr}: unknown"); continue
        done = os.path.join(OUT, tkr, ".done")
        if os.path.exists(done):
            print(f"{tkr:6s} cached"); continue
        n_tot = 0
        for f in latest_filings(cik, n=2):
            n = pull(cik, tkr, f)
            n_tot += n
            print(f"{tkr:6s} {f['form']} {f['report_date']} -> {n} tables")
        os.makedirs(os.path.join(OUT, tkr), exist_ok=True)
        open(done, "w").write("ok")
        time.sleep(0.2)


if __name__ == "__main__":
    main()
