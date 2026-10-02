import os

import numpy as np
import pandas as pd

P = os.path.join(os.path.dirname(__file__), "..", "data", "prices")
OUT = os.path.join(os.path.dirname(__file__), "..", "output")
os.makedirs(OUT, exist_ok=True)


def px(t):
    d = pd.read_csv(os.path.join(P, f"{t.replace('^','idx_')}.csv"), parse_dates=["date"])
    return d.set_index("date")["adjclose"]


def ret(s, a, b):
    sa, sb = s.loc[:a], s.loc[:b]
    return sb.iloc[-1] / sa.iloc[-1] - 1


names = [f[:-4] for f in os.listdir(P) if f.endswith(".csv")]
spy = px("SPY")
xlf = px("XLF")
rows = []
for t in sorted(names):
    s = px(t)
    if len(s) < 300:
        continue
    r = s.pct_change().dropna()
    rows.append({
        "t": t,
        "last": s.iloc[-1],
        "Q3": ret(s, "2026-06-30", "2026-09-30"),
        "Sep": ret(s, "2026-08-31", "2026-09-30"),
        "Q2": ret(s, "2026-03-31", "2026-06-30"),
        "1m": s.iloc[-1] / s.iloc[-22] - 1,
        "3m": s.iloc[-1] / s.iloc[-64] - 1,
        "YTD": ret(s, "2025-12-31", "2026-10-01"),
        "1y": s.iloc[-1] / s.iloc[-253] - 1,
        "dd_from_52wk_hi": s.iloc[-1] / s.iloc[-252:].max() - 1,
        "vol_60d": r.iloc[-60:].std() * np.sqrt(252),
        "vs_xlf_Q3": ret(s, "2026-06-30", "2026-09-30") - ret(xlf, "2026-06-30", "2026-09-30"),
        "hi52": s.iloc[-252:].max(),
    })
d = pd.DataFrame(rows).set_index("t")
d.to_csv(os.path.join(OUT, "price_stats.csv"))
pd.set_option("display.width", 220)
pct = d.drop(columns=["last", "hi52"]).copy()
for c in pct.columns:
    pct[c] = (pct[c] * 100).round(1)
pct.insert(0, "last", d["last"].round(2))
print(pct.sort_values("Q3").to_string())
