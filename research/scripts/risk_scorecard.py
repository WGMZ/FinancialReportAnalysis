"""Balance-sheet risk scorecard and pro forma Q3 rate shock.

TCE        = equity - goodwill - intangibles - preferred
Leverage   = assets / TCE
Pro forma  = AFS: -D * dy * AFS amortized cost * (1 - tax) hits AOCI and TCE
             HTM: not in capital, reported as an economic mark (% of TCE)
D          = empirical effective duration from duration_engine; regression R2 < 0.5
             or missing -> fallback by portfolio type (flagged)
dy         = Q3 average move of the benchmark the regression was run against
             (AFS: 5Y/10Y blend +87.5bp, HTM: 30Y mortgage rate +54bp)
"""

import os

import numpy as np
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(BASE, "output")

DY_AFS = 0.00875
DY_HTM = 0.0054
TAX = 0.24
FALLBACK_AFS_D = 3.0
FALLBACK_HTM_D = 4.5

PREF_FALLBACK = {
    "JPM": 20.2, "BAC": 24.3, "C": 17.7, "WFC": 18.9, "GS": 10.0, "MS": 9.3, "USB": 6.3, "PNC": 5.0, "TFC": 5.2,
    "FITB": 1.7, "HBAN": 3.0, "CFG": 1.6, "KEY": 3.2, "MTB": 2.0, "RF": 1.4, "COF": 4.5, "SCHW": 4.5, "BNY": 3.6,
    "NTRS": 1.0, "STT": 3.0, "ZION": 0.4, "ALLY": 1.5,
}  # $bn, preferred stock carrying value (approx, used only when XBRL is missing)

# AFS amortized-cost proxies (fair value from XBRL, or estimate) where the regression engine had no AFS series.
AFS_OVERRIDE = {  # ticker: (AFS $bn, effective duration, source)
    "WFC": (250.3, 3.0, "xbrl-FV/fallbackD"),
    "GS": (155.6, 1.8, "xbrl-FV/short-bills"),
    "TFC": (60.0, 3.5, "est"),
    "CFG": (22.0, 3.5, "est"),
    "MTB": (14.2, 3.5, "xbrl-unrealized-loss-position"),
    "RF": (24.0, 3.5, "est"),
}

TICKERS = ["JPM", "BAC", "C", "WFC", "GS", "MS", "USB", "PNC", "TFC", "FITB", "HBAN", "CFG", "KEY", "MTB", "RF",
           "COF", "SCHW", "BNY", "NTRS", "STT", "ZION", "ALLY"]


def pref_from_facts3(t):
    p = os.path.join(BASE, "data", "sec", "facts3", f"{t}.csv")
    if not os.path.exists(p):
        return np.nan
    d = pd.read_csv(p)
    d = d[d.tag.isin(["PreferredStockValue", "PreferredStockIncludingAdditionalPaidInCapitalNetOfDiscount"])]
    d = d[d.end == "2026-06-30"]
    return d.val.max() / 1e9 if len(d) else np.nan


def main():
    de = pd.read_csv(os.path.join(BASE, "data", "sec", "duration_estimates.csv")).set_index("ticker")
    rows = []
    for t in TICKERS:
        if t not in de.index or t in ("C", "HBAN"):
            continue
        r = de.loc[t]
        eq = r.equity / 1e9
        gw = (r.goodwill if pd.notna(r.goodwill) else 0) / 1e9
        ia = (r.intang if pd.notna(r.intang) else 0) / 1e9
        pf = pref_from_facts3(t)
        pf_src = "xbrl"
        if pd.isna(pf):
            pf = PREF_FALLBACK.get(t, 0.0)
            pf_src = "approx"
        tce = eq - gw - ia - pf
        assets = r.assets / 1e9
        afs_ac = r.afs_ac / 1e9 if pd.notna(r.afs_ac) else np.nan
        htm_ac = r.htm_ac / 1e9 if pd.notna(r.htm_ac) else np.nan
        d_afs, flag_afs = r.afs_dur_emp, "emp"
        if pd.isna(d_afs) or pd.isna(r.afs_r2) or r.afs_r2 < 0.5 or d_afs < 0.5:
            d_afs, flag_afs = FALLBACK_AFS_D, "fallback"
        d_htm, flag_htm = r.htm_dur_emp, "emp"
        if pd.isna(d_htm) or pd.isna(r.htm_r2) or r.htm_r2 < 0.5 or d_htm < 1.0:
            d_htm, flag_htm = FALLBACK_HTM_D, "fallback"
        if t in AFS_OVERRIDE and pd.isna(afs_ac):
            afs_ac, d_afs, flag_afs = AFS_OVERRIDE[t][0], AFS_OVERRIDE[t][1], AFS_OVERRIDE[t][2]
        afs_hit_pre = d_afs * DY_AFS * afs_ac if pd.notna(afs_ac) else 0.0
        afs_hit = afs_hit_pre * (1 - TAX)
        htm_hit = d_htm * DY_HTM * htm_ac if pd.notna(htm_ac) else 0.0
        htm_ul_now = -r.htm_net_unreal / 1e9 if pd.notna(r.htm_net_unreal) else np.nan
        afs_ul_now = -r.afs_net_unreal / 1e9 if pd.notna(r.afs_net_unreal) else np.nan
        rows.append({
            "t": t, "assets_bn": assets, "tce_bn": tce, "pref_src": pf_src,
            "tce_ta_pct": 100 * tce / assets, "lev_x": assets / tce,
            "aoci_bn": r.aoci / 1e9, "aoci_pct_tce": 100 * r.aoci / 1e9 / tce,
            "afs_ac_bn": afs_ac, "afs_D": d_afs, "afs_src": flag_afs,
            "htm_ac_bn": htm_ac, "htm_D": d_htm, "htm_src": flag_htm,
            "htm_ul_q2_bn": htm_ul_now,
            "q3_aoci_hit_bn": -afs_hit,
            "q3_aoci_hit_pct_tce": -100 * afs_hit / tce,
            "q3_htm_mark_bn": -htm_hit,
            "q3_htm_mark_pct_tce": -100 * htm_hit / tce,
            "total_ul_pf_pct_tce": -100 * ((htm_ul_now if pd.notna(htm_ul_now) else 0) + (afs_ul_now if pd.notna(afs_ul_now) else 0) + afs_hit_pre + htm_hit) / tce,
        })
    df = pd.DataFrame(rows).round(2)
    df.to_csv(os.path.join(OUT, "risk_scorecard.csv"), index=False)
    pd.set_option("display.width", 250, "display.max_columns", 40)
    print(df.drop(columns=["pref_src"]).to_string(index=False))


if __name__ == "__main__":
    main()
