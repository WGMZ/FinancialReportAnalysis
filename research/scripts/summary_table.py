"""Combine the EPS model, price action and balance-sheet risk into one ranked table.

earn_score   = 2 * (P(beat) - 0.5)                         earnings versus consensus   (-1..+1)
setup_score  = clip(-(1m return + 0.5 * YTD vs XLF) / 0.25, -1, 1)
               a stock that has already sold off against the sector carries a lower bar; a stock that has run
               carries a higher one
struct_score = clip(-(|Q3 AOCI hit| % of TCE) / 8 + 0.5, -1, 1) - penalty for TCE/TA < 5%
composite    = 0.5 earn + 0.3 setup + 0.2 struct
implied move = 2.0 * 60d vol / sqrt(252)                   heuristic one-day earnings move
"""

import os

import numpy as np
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(BASE, "output")


def main():
    m = pd.read_csv(os.path.join(OUT, "q3_model.csv")).set_index("t")
    p = pd.read_csv(os.path.join(OUT, "price_stats.csv")).set_index("t")
    r = pd.read_csv(os.path.join(OUT, "risk_scorecard.csv")).set_index("t")
    xlf_ytd = p.loc["XLF", "YTD"]
    rows = []
    for t in m.index:
        pp = p.loc[t]
        earn = 2 * (m.loc[t, "p_beat"] - 0.5)
        rel_ytd = pp["YTD"] - xlf_ytd
        setup = float(np.clip(-(pp["1m"] + 0.5 * rel_ytd) / 0.25, -1, 1))
        if t in r.index:
            hit = abs(r.loc[t, "q3_aoci_hit_pct_tce"])
            struct = float(np.clip(-hit / 8 + 0.5, -1, 1))
            if r.loc[t, "tce_ta_pct"] < 5.0:
                struct -= 0.2
            tce_ta, lev, hit_pct = r.loc[t, "tce_ta_pct"], r.loc[t, "lev_x"], r.loc[t, "q3_aoci_hit_pct_tce"]
        else:
            struct, tce_ta, lev, hit_pct = 0.0, np.nan, np.nan, np.nan
        comp = 0.5 * earn + 0.3 * setup + 0.2 * struct
        rows.append({
            "t": t, "cons": m.loc[t, "cons_eps"], "model": m.loc[t, "mean"], "surp_pct": m.loc[t, "surp_pct"],
            "p_beat": m.loc[t, "p_beat"], "p_miss3": m.loc[t, "p_miss3"], "method": m.loc[t, "method"],
            "Q3_ret": 100 * pp["Q3"], "1m": 100 * pp["1m"], "ytd": 100 * pp["YTD"], "ytd_vs_xlf": 100 * rel_ytd,
            "dd_hi": 100 * pp["dd_from_52wk_hi"], "vol60": 100 * pp["vol_60d"],
            "implied_move_pct": 2.0 * 100 * pp["vol_60d"] / np.sqrt(252),
            "tce_ta": tce_ta, "lev": lev, "q3_aoci_hit_pct_tce": hit_pct,
            "earn": earn, "setup": setup, "struct": struct, "composite": comp,
        })
    df = pd.DataFrame(rows).sort_values("composite", ascending=False).round(2)
    df.to_csv(os.path.join(OUT, "summary_table.csv"), index=False)
    pd.set_option("display.width", 260, "display.max_columns", 40)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
