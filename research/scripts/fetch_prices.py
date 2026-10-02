"""Daily adjusted prices from Yahoo Finance chart API for the universe plus benchmarks.

Used for: Q3 price action, relative performance vs XLF/SPY/QQQ, realized vol,
drawdown from highs.
"""

import json
import os
import time

import pandas as pd
import requests

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "prices")
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0"}

BENCH = ["SPY", "QQQ", "XLF", "KRE", "KBE", "IAI", "XLK", "TLT", "^GSPC", "^IXIC", "^TNX", "^VIX", "KBWB", "SMH"]


def fetch(sym: str, rng: str = "5y") -> pd.DataFrame | None:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={rng}&interval=1d&events=div,split"
    for i in range(4):
        try:
            r = requests.get(url, headers=UA, timeout=40)
            if r.status_code == 200:
                res = r.json()["chart"]["result"][0]
                ts = res["timestamp"]
                q = res["indicators"]["quote"][0]
                adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose")
                df = pd.DataFrame({
                    "date": pd.to_datetime(ts, unit="s").normalize(),
                    "open": q["open"], "high": q["high"], "low": q["low"],
                    "close": q["close"], "volume": q["volume"],
                    "adjclose": adj if adj else q["close"],
                }).dropna(subset=["close"])
                return df
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1.5 * (i + 1))
    return None


def main() -> None:
    uni = json.load(open(os.path.join(os.path.dirname(__file__), "..", "data", "sec", "universe.json")))
    syms = sorted(uni["cik"]) + BENCH
    bad = []
    for s in syms:
        dest = os.path.join(OUT, f"{s.replace('^', 'idx_')}.csv")
        if os.path.exists(dest):
            continue
        df = fetch(s)
        if df is None or df.empty:
            bad.append(s)
            continue
        df.to_csv(dest, index=False)
        print(f"{s:7s} n={len(df):5d} last={df.date.iloc[-1].date()} close={df.close.iloc[-1]:>10,.2f}")
        time.sleep(0.15)
    print("failed:", bad)


if __name__ == "__main__":
    main()
