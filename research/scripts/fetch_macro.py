"""Pull FRED series needed for the Q3-2026 US financials earnings model.

FRED's fredgraph.csv endpoint is public and needs no API key.
Everything is cached to research/data/fred/ so later scripts never re-hit the network.
"""

import io
import os
import sys
import time

import pandas as pd
import requests

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "fred")
os.makedirs(OUT, exist_ok=True)

SERIES = {
    # ---- policy / money market ----
    "DFF": "Effective fed funds (daily)",
    "IORB": "Interest on reserve balances",
    "SOFR": "SOFR",
    "DGS1MO": "1M Treasury CMT",
    "DGS3MO": "3M Treasury CMT",
    "DGS6MO": "6M Treasury CMT",
    "DGS1": "1Y Treasury CMT",
    "DGS2": "2Y Treasury CMT",
    "DGS3": "3Y Treasury CMT",
    "DGS5": "5Y Treasury CMT",
    "DGS7": "7Y Treasury CMT",
    "DGS10": "10Y Treasury CMT",
    "DGS20": "20Y Treasury CMT",
    "DGS30": "30Y Treasury CMT",
    "T10Y2Y": "10Y-2Y spread",
    "T10Y3M": "10Y-3M spread",
    "T5YIE": "5Y breakeven inflation",
    "T10YIE": "10Y breakeven inflation",
    "DFII10": "10Y TIPS real yield",
    # ---- credit / risk ----
    "BAMLH0A0HYM2": "ICE BofA US High Yield OAS",
    "BAMLC0A0CM": "ICE BofA US Corporate IG OAS",
    "BAMLC0A4CBBB": "ICE BofA BBB OAS",
    "VIXCLS": "VIX",
    "NFCI": "Chicago Fed National Financial Conditions Index",
    "STLFSI4": "St Louis Fed Financial Stress Index",
    # ---- macro ----
    "CPIAUCSL": "CPI all items SA",
    "CPILFESL": "Core CPI SA",
    "PCEPILFE": "Core PCE price index",
    "UNRATE": "Unemployment rate",
    "PAYEMS": "Nonfarm payrolls",
    "GDPC1": "Real GDP",
    "DCOILWTICO": "WTI crude",
    "DCOILBRENTEU": "Brent crude",
    "MORTGAGE30US": "30Y fixed mortgage rate",
    # ---- banking system (H.8 / H.4.1) ----
    "TOTBKCR": "Bank credit, all commercial banks",
    "TOTLL": "Loans and leases, all commercial banks",
    "DPSACBW027SBOG": "Deposits, all commercial banks",
    "BUSLOANS": "C&I loans",
    "REALLN": "Real estate loans",
    "CONSUMER": "Consumer loans",
    "CCLACBW027SBOG": "Credit card & revolving loans",
    "H8B1058NCBCMG": "Loan growth",
    "WALCL": "Fed total assets",
    "TOTRESNS": "Reserve balances",
    "RRPONTSYD": "ON RRP",
    # ---- credit quality (quarterly, lagged) ----
    "DRCCLACBS": "Credit card charge-off rate",
    "DRCLACBS": "Consumer loan delinquency rate",
    "DRBLACBS": "Business loan delinquency rate",
    "DRCRELEXFACBS": "CRE delinquency rate",
    "DRALACBN": "All loans delinquency rate",
    "DALLCIACBEP": "Allowance ratio",
    # ---- equity ----
    "SP500": "S&P 500",
    "NASDAQCOM": "Nasdaq Composite",
    # ---- deposits pricing ----
    "DPCREDIT": "Discount window primary credit rate",
}


def fetch(sid: str) -> pd.DataFrame | None:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=40)
            if r.status_code == 200 and not r.text.lstrip().startswith("<"):
                df = pd.read_csv(io.StringIO(r.text))
                if df.shape[1] < 2:
                    return None
                df.columns = ["date", sid]
                df["date"] = pd.to_datetime(df["date"])
                df[sid] = pd.to_numeric(df[sid], errors="coerce")
                return df.dropna()
        except Exception as exc:  # noqa: BLE001
            print(f"  retry {sid}: {exc}", file=sys.stderr)
        time.sleep(2 * (attempt + 1))
    return None


def main() -> None:
    ok, bad = [], []
    for sid, label in SERIES.items():
        df = fetch(sid)
        if df is None or df.empty:
            bad.append(sid)
            print(f"FAIL {sid:16s} {label}")
            continue
        df.to_csv(os.path.join(OUT, f"{sid}.csv"), index=False)
        last = df.iloc[-1]
        ok.append(sid)
        print(f"OK   {sid:16s} n={len(df):6d}  last={last['date'].date()}  {last[sid]:>12,.4f}   {label}")
    print(f"\n{len(ok)} ok, {len(bad)} failed: {bad}")


if __name__ == "__main__":
    main()
