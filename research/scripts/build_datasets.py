"""Assemble the datasets behind the charts: revenue lines + Q3E, EPS history, AFS/HTM, stress test.

Outputs go to output/data/*.csv so the charts and the Word builder read the same numbers.
"""

import os
import re

import numpy as np
import pandas as pd

import chart_data as cd
import duration_engine as de

OUT = os.path.join(cd.OUT, "data")
os.makedirs(OUT, exist_ok=True)

Q_RANGE = ["2024Q3", "2024Q4", "2025Q1", "2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2"]
TAX = 0.24


def _seg_lines() -> pd.DataFrame:
    return pd.read_csv(os.path.join(cd.OUT, "seg_lines.csv"))


def segment_history() -> pd.DataFrame:
    sl = _seg_lines()

    def sl_get(t, line):
        s = sl[(sl.ticker == t) & (sl.line == line)].set_index("quarter")["usd_bn"]
        return s

    rows = []
    for t in cd.BIG6:
        p = cd.segment_panel(t, "2024Q3")
        p = p.reindex(Q_RANGE)
        if t in ("BAC", "WFC", "C"):
            p["ib"] = sl_get(t, "ib").reindex(Q_RANGE)
        if t == "GS":
            p["trading"] = sl_get(t, "mm").reindex(Q_RANGE)
        if t == "C":
            for col, line in (("nii", "nii"), ("trading", "trd"), ("total", "rev")):
                v = sl_get(t, line).reindex(Q_RANGE)
                p[col] = v.combine_first(p[col])
        p["ib"] = p["ib"].fillna(0)
        p["trading"] = p["trading"].fillna(0)
        if t != "C":
            p["total"] = p["nii"] + p["ib"] + p["trading"] + p["other"]
            if t in ("BAC", "WFC", "GS"):
                base = cd.segment_panel(t, "2024Q3").reindex(Q_RANGE)
                p["total"] = base["total"]
                p["other"] = p["total"] - p["nii"] - p["ib"] - p["trading"]
        else:
            p["other"] = p["total"] - p["nii"] - p["ib"] - p["trading"]
        p["ticker"] = t
        p["q"] = p.index
        rows.append(p.reset_index(drop=True))
    return pd.concat(rows, ignore_index=True)


LINE_RULES = [
    (re.compile(r"Opex|expense|Provision|Compensation|Non-comp", re.I), None),
    (re.compile(r"^NII \(|^NII ex-Markets", re.I), "nii"),
    (re.compile(r"Markets|Equities|FICC|Sales & trading", re.I), "trading"),
    (re.compile(r"^IB\b", re.I), "ib"),
]


def line_of(item: str):
    for rx, line in LINE_RULES:
        if rx.search(item):
            return line
    return "other"


def add_forecast(hist: pd.DataFrame) -> pd.DataFrame:
    import q3_model as qm

    br = pd.read_csv(os.path.join(cd.OUT, "q3_model_bridge.csv"))
    rows = []
    for t in cd.BIG6:
        q2 = hist[(hist.ticker == t) & (hist.q == "2026Q2")].iloc[0]
        e = dict(q2[["nii", "ib", "trading", "other"]])
        oneoff = 0.0
        if t == "JPM":
            cfg = qm.BANKS["JPM"]
            clean_pbt = (cfg["eps2"] * cfg["sh2"] + cfg["pref"]) / (1 - cfg["t2"]) / 1e3
            gaap = pd.read_csv(os.path.join(cd.DATA, "sec", "quarterly", "JPM.csv")).set_index("q")
            gaap_pbt = gaap.loc["2026Q2", "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"] / 1e9
            oneoff = max(gaap_pbt - clean_pbt, 0)
            e["other"] -= oneoff
        for _, r in br[br.t == t].iterrows():
            ln = line_of(r["item"])
            if ln:
                e[ln] += r["d_pbt_musd"] / 1e3
        e["total"] = sum(e.values())
        rows.append({"ticker": t, "q": "2026Q3E", **e})
        hist.loc[(hist.ticker == t) & (hist.q == "2026Q2"), "oneoff"] = oneoff
    out = pd.concat([hist, pd.DataFrame(rows)], ignore_index=True)
    out["oneoff"] = out["oneoff"].fillna(0.0)
    return out


def eps_history() -> pd.DataFrame:
    m = pd.read_csv(os.path.join(cd.OUT, "q3_model.csv")).set_index("t")
    rows = []
    for t in cd.BIG6:
        s = cd.eps_series(t, "2024Q1").to_dict()
        if t == "C":
            s["2026Q1"], s["2026Q2"] = 3.06, 3.15
        for q, v in s.items():
            rows.append({"ticker": t, "q": q, "eps": v, "kind": "actual"})
        rows.append({"ticker": t, "q": "2026Q3E", "eps": m.loc[t, "mean"], "kind": "model",
                     "p10": m.loc[t, "p10"], "p90": m.loc[t, "p90"], "cons": m.loc[t, "cons_eps"]})
    d = pd.DataFrame(rows)
    d.loc[(d.ticker == "JPM") & (d.q == "2026Q2"), "eps_adj"] = 6.14
    return d


def afs_htm_history() -> pd.DataFrame:
    rows = []
    for t in ["JPM", "BAC", "WFC", "GS", "MS"]:
        df = de.load(t)
        cols = {n: de.series(df, al) for n, al in
                [("afs_ac", de.AFS_AC), ("afs_fv", de.AFS_FV), ("htm_ac", de.HTM_AC), ("htm_fv", de.HTM_FV)]}
        d = pd.DataFrame(cols) / 1e9
        d = d[d.index >= pd.Period("2024Q2")]
        d["ticker"] = t
        d["q"] = d.index.astype(str)
        rows.append(d.reset_index(drop=True))
    c = pd.DataFrame([
        {"ticker": "C", "q": "2025Q4", "afs_ac": np.nan, "afs_fv": 246.72, "htm_ac": 189.83, "htm_fv": 179.52},
        {"ticker": "C", "q": "2026Q2", "afs_ac": np.nan, "afs_fv": 286.77, "htm_ac": 167.89, "htm_fv": 157.52},
    ])
    return pd.concat(rows + [c], ignore_index=True)


# ------------------------------------------------------------------ stress test
# 12-month NII sensitivity disclosed in the Q2-2026 10-Qs ($bn). NaN = not disclosed.
NII_DISC = {
    "JPM": dict(p100=1.8, p200=2.9, steep=1.1, flat=0.6, src="10-Q disclosed"),
    "BAC": dict(p100=1.0, p200=1.9, steep=0.2, flat=0.8, src="10-Q disclosed"),
    "C": dict(p100=1.234, p200=2.381, steep=0.321, flat=0.906, src="10-Q disclosed"),
    "WFC": dict(p100=1.3, p200=np.nan, steep=0.4, flat=0.9, src="+200 linear"),
    "GS": dict(p100=0.056, p200=0.098, steep=np.nan, flat=np.nan, src="earnings-at-risk (net revenue)"),
    "MS": dict(p100=0.202, p200=0.413, steep=np.nan, flat=np.nan, src="Wealth Mgmt only"),
}
C_AOCI = {"p100": -3.046, "p200": -6.342, "steep": -0.898, "flat": -2.226}  # after tax, 10-Q disclosed
C_BS = dict(tce=212.015 - 19.012 - 5.004 - 19.55, assets=2894.654, htm_ac=167.893, htm_D=4.5)

SCEN = [
    ("p50", 0.5, 0.5),
    ("p100", 1.0, 1.0),
    ("p200", 2.0, 2.0),
    ("steep", 0.0, 1.0),
    ("flat", 1.0, 0.0),
]  # name, short-end shift (pp), long-end shift (pp)


def annual_earnings() -> dict:
    import q3_model as qm
    m = pd.read_csv(os.path.join(cd.OUT, "q3_model.csv")).set_index("t")
    out = {}
    for t in cd.BIG6:
        cfg = qm.BANKS[t]
        out[t] = 4 * m.loc[t, "mean"] * cfg["sh3"] / 1e3
    return out


def stress() -> pd.DataFrame:
    rs = pd.read_csv(os.path.join(cd.OUT, "risk_scorecard.csv")).set_index("t")
    earn = annual_earnings()
    rows = []
    for t in cd.BIG6:
        n = NII_DISC[t]
        if t == "C":
            tce, htm_ac, htm_D, afs_ac, afs_D = C_BS["tce"], C_BS["htm_ac"], C_BS["htm_D"], np.nan, np.nan
        else:
            r = rs.loc[t]
            tce, htm_ac, htm_D, afs_ac, afs_D = r.tce_bn, r.htm_ac_bn, r.htm_D, r.afs_ac_bn, r.afs_D
        for name, sh, lg in SCEN:
            if name == "p50":
                nii = 0.5 * n["p100"]
            elif name == "p200" and np.isnan(n["p200"]):
                nii = 2 * n["p100"]
            else:
                nii = n[name]
            if t == "C":
                key = {"p50": "p100"}.get(name, name)
                aoci = C_AOCI[key] * (0.5 if name == "p50" else 1.0)
            else:
                aoci = -afs_D * lg / 100 * afs_ac * (1 - TAX)
            htm = -htm_D * lg / 100 * htm_ac
            nii_at = nii * (1 - TAX) if not np.isnan(nii) else np.nan
            rows.append({
                "ticker": t, "scenario": name, "short_pp": sh, "long_pp": lg,
                "nii_pre": nii, "nii_after_tax": nii_at, "aoci_hit": aoci, "htm_mark_pre": htm,
                "htm_mark_after_tax": htm * (1 - TAX),
                "net_cap_12m": nii_at + aoci if not np.isnan(nii_at) else np.nan,
                "net_econ_12m": nii_at + aoci + htm * (1 - TAX) if not np.isnan(nii_at) else np.nan,
                "tce": tce, "annual_earn": earn[t],
            })
    d = pd.DataFrame(rows)
    for c in ("nii_after_tax", "aoci_hit", "htm_mark_after_tax", "net_cap_12m", "net_econ_12m"):
        d[c + "_pct_tce"] = 100 * d[c] / d["tce"]
    d["aoci_hit_x_earn"] = -d["aoci_hit"] / d["annual_earn"]
    d["net_econ_pct_earn"] = 100 * d["net_econ_12m"] / d["annual_earn"]
    return d


def main():
    hist = segment_history()
    seg = add_forecast(hist)
    seg.to_csv(os.path.join(OUT, "segment_panel.csv"), index=False)
    eps_history().to_csv(os.path.join(OUT, "eps_history.csv"), index=False)
    afs_htm_history().to_csv(os.path.join(OUT, "afs_htm_history.csv"), index=False)
    st = stress()
    st.to_csv(os.path.join(OUT, "stress_test.csv"), index=False)
    pd.set_option("display.width", 220, "display.max_columns", 30)
    print(seg[seg.q.isin(["2025Q3", "2026Q2", "2026Q3E"])].round(2).to_string())
    print(st.round(2).to_string())


if __name__ == "__main__":
    main()
