"""Banks vs tech in rate-shock / oil-shock / bubble regimes.

Sources
  * Ken French 48-industry monthly value-weighted returns (1926-2026): Banks, Insur, Fin, Softw,
    Chips, Hardw, Oil, BusSv, Comps -- covers 1973-74 and 1999-2002.
  * FRED: FEDFUNDS, WTISPLC (monthly), DGS10, GS10, CPI.
  * Yahoo: ^BKX / ^SOX / ^IXIC (daily-from-monthly) for the 1990s onward.
"""

import io
import os

import numpy as np
import pandas as pd
import requests

BASE = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(BASE, "output")
DATA = os.path.join(BASE, "data")
os.makedirs(os.path.join(DATA, "hist"), exist_ok=True)


def french_vw_monthly() -> pd.DataFrame:
    path = "/tmp/48_Industry_Portfolios.csv"
    if not os.path.exists(path):
        import subprocess
        subprocess.run(["curl", "-s", "-o", "/tmp/ff.zip",
                        "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/48_Industry_Portfolios_CSV.zip"], check=True)
        subprocess.run(["unzip", "-o", "-q", "/tmp/ff.zip", "-d", "/tmp"], check=True)
    txt = open(path).read().split("\n")
    start = next(i for i, l in enumerate(txt) if "Average Value Weighted Returns -- Monthly" in l)
    hdr = start + 1
    cols = [c.strip() for c in txt[hdr].split(",")][1:]
    rows = []
    for l in txt[hdr + 1:]:
        if not l.strip():
            break
        parts = l.split(",")
        rows.append([parts[0].strip()] + [float(x) for x in parts[1:]])
    df = pd.DataFrame(rows, columns=["ym"] + cols)
    df["date"] = pd.to_datetime(df["ym"].astype(str), format="%Y%m")
    df = df.set_index("date").drop(columns="ym").replace([-99.99, -999], np.nan) / 100
    df.to_csv(os.path.join(DATA, "hist", "french48_vw_monthly.csv"))
    return df


def fred(sid: str) -> pd.Series:
    r = requests.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", timeout=60)
    d = pd.read_csv(io.StringIO(r.text))
    d.columns = ["date", sid]
    d["date"] = pd.to_datetime(d["date"])
    s = d.set_index("date")[sid]
    s = pd.to_numeric(s, errors="coerce").dropna()
    s.to_csv(os.path.join(DATA, "hist", f"{sid}.csv"))
    return s


def cum(r: pd.Series, a: str, b: str) -> float:
    x = r.loc[a:b].dropna()
    return float((1 + x).prod() - 1) if len(x) else np.nan


def main() -> None:
    ff = french_vw_monthly()
    ffr = fred("FEDFUNDS")
    wti = fred("WTISPLC")
    cpi = fred("CPIAUCSL")
    g10 = fred("GS10")

    mkt_cols = [c for c in ["Banks", "Insur", "Fin", "Chips", "Comps", "Oil", "BusSv"] if c in ff.columns]
    print("Industries available:", mkt_cols)

    EPISODES = {
        "A. 1973-74 oil embargo + stagflation  (Oct73-Dec74)": ("1973-10", "1974-12"),
        "A2. 1973 pre-embargo peak -> trough (Jan73-Sep74)": ("1973-01", "1974-09"),
        "B. 1979-81 Volcker/oil shock (Jan79-Sep81)": ("1979-01", "1981-09"),
        "C. 1990 Gulf War oil spike (Jul90-Oct90)": ("1990-07", "1990-10"),
        "D. dot-com run-up (Oct98-Mar00)": ("1998-10", "2000-03"),
        "D2. dot-com bust (Apr00-Sep02)": ("2000-04", "2002-09"),
        "D3. 1999 Fed hikes 4.75->5.50 (Jun99-Dec99)": ("1999-06", "1999-12"),
        "E. 2004-06 hiking cycle (Jun04-Jun06)": ("2004-06", "2006-06"),
        "F. 2008 oil to $147 (Jan08-Jul08)": ("2008-01", "2008-07"),
        "G. 2022 hiking + Ukraine oil (Jan22-Dec22)": ("2022-01", "2022-12"),
        "G2. 2022 H1 (Jan22-Jun22)": ("2022-01", "2022-06"),
        "H. 2023 SVB (Feb23-May23)": ("2023-02", "2023-05"),
        "I. 2025-26 AI boom (Jan25-Sep26)": ("2025-01", "2026-09"),
    }
    rows = []
    for name, (a, b) in EPISODES.items():
        rec = {"episode": name}
        for c in mkt_cols:
            rec[c] = cum(ff[c], a, b)
        rec["ffr_chg_bp"] = (ffr.loc[:b].iloc[-1] - ffr.loc[:a].iloc[-1]) * 100 if len(ffr.loc[:b]) else np.nan
        rec["10y_chg_bp"] = (g10.loc[:b].iloc[-1] - g10.loc[:a].iloc[-1]) * 100
        w0, w1 = wti.loc[:a].iloc[-1], wti.loc[:b].iloc[-1]
        rec["oil_chg_pct"] = (w1 / w0 - 1)
        rec["banks_minus_tech"] = rec["Banks"] - np.nanmean([rec.get("Chips", np.nan), rec.get("Comps", np.nan), rec.get("BusSv", np.nan)])
        rows.append(rec)
    res = pd.DataFrame(rows).set_index("episode")
    res.to_csv(os.path.join(OUT, "historical_analogs.csv"))
    disp = res.copy()
    for c in mkt_cols + ["oil_chg_pct", "banks_minus_tech"]:
        disp[c] = (disp[c] * 100).round(1)
    disp["ffr_chg_bp"] = disp["ffr_chg_bp"].round(0)
    disp["10y_chg_bp"] = disp["10y_chg_bp"].round(0)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 60)
    print(disp.to_string())

    # Conditional stats: months when 10y rose >50bp over trailing 3 months -> bank vs tech next-3m
    g10m = g10.resample("MS").last()
    d3 = g10m.diff(3) * 100
    both = pd.concat([d3.rename("d10y_3m"), ff["Banks"].rolling(3).apply(lambda x: (1 + x).prod() - 1).rename("bank_3m"),
                      ff[["Chips", "Comps", "BusSv"]].mean(axis=1).rolling(3).apply(lambda x: (1 + x).prod() - 1).rename("tech_3m"),
                      ff["Banks"].shift(-3).rolling(3).apply(lambda x: (1 + x).prod() - 1).shift(-0).rename("dummy")], axis=1)
    fwd_b = ff["Banks"].rolling(3).apply(lambda x: (1 + x).prod() - 1).shift(-3)
    fwd_t = ff[["Chips", "Comps", "BusSv"]].mean(axis=1).rolling(3).apply(lambda x: (1 + x).prod() - 1).shift(-3)
    both["fwd_bank_3m"], both["fwd_tech_3m"] = fwd_b, fwd_t
    both = both.dropna(subset=["d10y_3m", "bank_3m", "tech_3m"])
    for lo, label in [(50, "10y +50bp in 3m"), (75, "10y +75bp in 3m")]:
        s = both[both.d10y_3m >= lo]
        print(f"\n{label}: n={len(s)} months  (concurrent) bank_3m={s.bank_3m.mean():+.1%}  tech_3m={s.tech_3m.mean():+.1%}"
              f"  | next-3m bank={s.fwd_bank_3m.mean():+.1%} (hit {np.mean(s.fwd_bank_3m>0):.0%}) tech={s.fwd_tech_3m.mean():+.1%}")
        print("   dates:", ", ".join(d.strftime("%Y-%m") for d in s.index[:40]))
    s_all = both.dropna(subset=["fwd_bank_3m"])
    print(f"\nUnconditional next-3m bank={s_all.fwd_bank_3m.mean():+.1%}  tech={s_all.fwd_tech_3m.mean():+.1%}")


if __name__ == "__main__":
    main()
