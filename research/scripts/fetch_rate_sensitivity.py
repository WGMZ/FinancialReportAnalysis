"""Extract interest-rate-risk disclosures from the body of each 10-Q.

The NII-sensitivity and economic-value-of-equity tables live in MD&A / Item 3, which
is not XBRL-tagged, so we fetch the primary document and slice out the neighbourhoods
around the phrases banks actually use.
"""

import json
import os
import re
import sys
import time

import requests

HDRS = {"User-Agent": "Independent Research equity-research@example.com",
        "Accept-Encoding": "gzip, deflate"}

BASE = os.path.join(os.path.dirname(__file__), "..", "data", "sec")
OUT = os.path.join(BASE, "raterisk")
os.makedirs(OUT, exist_ok=True)

ANCHORS = [
    r"net interest income sensitivit",
    r"interest rate sensitivit",
    r"sensitivity of net interest income",
    r"earnings at risk",
    r"economic value of equity",
    r"net (?:portfolio|interest income) value",
    r"asset[/ -]liability management",
    r"interest rate risk",
    r"simulated net interest income",
    r"rate shock",
    r"instantaneous (?:and )?(?:parallel )?(?:increase|shift|change)",
    r"gradual(?:ly)? (?:increase|change) in (?:interest )?rates",
    r"\+100 basis point",
    r"100 basis point (?:increase|parallel)",
    r"deposit beta",
    r"duration of equity",
    r"effective duration",
    r"weighted[- ]average (?:expected )?(?:life|duration)",
    r"repricing",
    r"asset[- ]sensitiv",
    r"liability[- ]sensitiv",
]
ANCHOR_RE = re.compile("|".join(ANCHORS), re.I)


def get(url: str, tries: int = 4):
    for i in range(tries):
        try:
            r = requests.get(url, headers=HDRS, timeout=180)
            if r.status_code == 200:
                return r
            if r.status_code == 404:
                return None
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1.5 * (i + 1))
    return None


def to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    html = re.sub(r"(?i)</t[dh]>", " | ", html)
    html = re.sub(r"(?i)</tr>", "\n", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</(p|div|h[1-6]|table)>", "\n", html)
    html = re.sub(r"(?s)<[^>]+>", "", html)
    for a, b in [("&nbsp;", " "), ("&#160;", " "), ("&amp;", "&"), ("&lt;", "<"),
                 ("&gt;", ">"), ("&#8217;", "'"), ("&#8220;", '"'), ("&#8221;", '"'),
                 ("&#8212;", "--"), ("&#8211;", "-"), ("&quot;", '"'), ("&#39;", "'"),
                 ("&#151;", "--"), ("&#150;", "-")]:
        html = html.replace(a, b)
    lines = []
    for ln in html.split("\n"):
        ln = re.sub(r"[ \t\u00a0]+", " ", ln).strip()
        ln = re.sub(r"(\s*\|\s*)+", " | ", ln).strip()
        ln = re.sub(r"^\|\s*", "", ln)
        if ln and ln not in {"|", "-"}:
            lines.append(ln)
    return "\n".join(lines)


def slice_sections(text: str, before: int = 12, after: int = 60) -> str:
    lines = text.split("\n")
    hits = [i for i, ln in enumerate(lines) if ANCHOR_RE.search(ln)]
    if not hits:
        return ""
    keep = set()
    for h in hits:
        keep.update(range(max(0, h - before), min(len(lines), h + after)))
    out, prev = [], -10
    for i in sorted(keep):
        if i - prev > 1:
            out.append(f"\n----- [line {i}] -----")
        out.append(lines[i])
        prev = i
    return "\n".join(out)


def main() -> None:
    uni = json.load(open(os.path.join(BASE, "universe.json")))
    ciks = uni["cik"]
    targets = sys.argv[1:] or sorted(ciks)
    for tkr in targets:
        cik = ciks.get(tkr)
        if not cik:
            continue
        dest = os.path.join(OUT, f"{tkr}.txt")
        if os.path.exists(dest):
            print(f"{tkr:6s} cached"); continue
        sub = get(f"https://data.sec.gov/submissions/CIK{cik}.json")
        if sub is None:
            print(f"{tkr:6s} no submissions"); continue
        rec = sub.json()["filings"]["recent"]
        pick = None
        for form, acc, rep, doc in zip(rec["form"], rec["accessionNumber"],
                                       rec["reportDate"], rec["primaryDocument"]):
            if form == "10-Q":
                pick = (acc.replace("-", ""), rep, doc)
                break
        if pick is None:
            print(f"{tkr:6s} no 10-Q"); continue
        acc, rep, doc = pick
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{doc}"
        r = get(url)
        if r is None:
            print(f"{tkr:6s} fetch failed {url}"); continue
        text = to_text(r.text)
        sec = slice_sections(text)
        with open(dest, "w") as fh:
            fh.write(f"# {tkr} 10-Q period={rep}\n# {url}\n# full_doc_chars={len(text)}\n\n{sec}\n")
        print(f"{tkr:6s} {rep} doc={len(text):8d} chars -> extracted {len(sec):7d} chars")
        time.sleep(0.25)


if __name__ == "__main__":
    main()
