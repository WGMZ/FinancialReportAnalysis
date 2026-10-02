"""Data layer for the charts and the Word reports.

Quarterly flow series come from the raw SEC facts. A 10-K only tags the full year, so
Q4 is derived as FY minus the three 10-Q quarters (flagged `derived`).
"""

import os

import numpy as np
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "output")

BIG6 = ["JPM", "BAC", "C", "WFC", "GS", "MS"]

NII_TAGS = ["InterestIncomeExpenseNet", "InterestIncomeExpenseAfterProvisionForLoanLoss"]
IB_TAGS = ["InvestmentBankingRevenue", "InvestmentBankingAdvisoryBrokerageAndUnderwritingFeesAndCommissions"]
TRD_TAGS = ["PrincipalTransactionsRevenue", "TradingGainsLosses", "TradingGainsLosses1"]
NONINT_TAGS = ["NoninterestIncome", "NoninterestIncomeOperating"]
EPS_TAGS = ["EarningsPerShareDiluted"]
NI_TAGS = ["NetIncomeLoss"]
REV_TAGS = ["RevenuesNetOfInterestExpense", "Revenues"]


def _raw(tkr: str) -> pd.DataFrame:
    frames = []
    for sub in ("facts", "facts2"):
        p = os.path.join(DATA, "sec", sub, f"{tkr}.csv")
        if os.path.exists(p):
            d = pd.read_csv(p, low_memory=False)
            d = d[["tag", "start", "end", "val", "form", "filed"]].copy()
            frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    for c in ("start", "end", "filed"):
        df[c] = pd.to_datetime(df[c], errors="coerce")
    return df.dropna(subset=["start", "end", "val"])


def flow_series(tkr: str, tags: list[str], first="2024Q1") -> pd.Series:
    """Quarterly flow in native units; Q4 = FY - (Q1+Q2+Q3) when the quarters exist."""
    df = _raw(tkr)
    out: dict[pd.Period, float] = {}
    for tag in tags:
        d = df[df.tag == tag].copy()
        if d.empty:
            continue
        d["days"] = (d["end"] - d["start"]).dt.days
        d = d.sort_values("filed").drop_duplicates(subset=["start", "end"], keep="last")
        q = d[(d.days >= 80) & (d.days <= 100)]
        y = d[(d.days >= 350) & (d.days <= 380)]
        res: dict[pd.Period, float] = {}
        for _, r in q.iterrows():
            res[r["end"].to_period("Q")] = r["val"]
        for _, r in y.iterrows():
            q4 = r["end"].to_period("Q")
            if q4 in res:
                continue
            parts = [res.get(q4 - k) for k in (1, 2, 3)]
            if all(p is not None for p in parts):
                res[q4] = r["val"] - sum(parts)
        if res:
            out = {**res, **{k: v for k, v in out.items()}}
            break
    s = pd.Series(out).sort_index()
    s.index = s.index.astype(str)
    return s[s.index >= first]


def segment_panel(tkr: str, first="2024Q1") -> pd.DataFrame:
    """NII, IB fees, trading, other non-interest income, total, in $bn."""
    nii = flow_series(tkr, NII_TAGS, first)
    ib = flow_series(tkr, IB_TAGS, first)
    trd = flow_series(tkr, TRD_TAGS, first)
    nonint = flow_series(tkr, NONINT_TAGS, first)
    idx = sorted(set(nii.index) | set(nonint.index))
    d = pd.DataFrame(index=idx)
    d["nii"] = nii
    d["ib"] = ib
    d["trading"] = trd
    d["nonint"] = nonint
    d = d.dropna(subset=["nii", "nonint"])
    d["ib"] = d["ib"].fillna(0)
    d["trading"] = d["trading"].fillna(0)
    d["other"] = d["nonint"] - d["ib"] - d["trading"]
    d = d[["nii", "ib", "trading", "other"]] / 1e9
    d["total"] = d.sum(axis=1)
    return d


def eps_series(tkr: str, first="2024Q1") -> pd.Series:
    s = flow_series(tkr, EPS_TAGS, first)
    s = s[s != 0]
    return s


def fred(sid: str) -> pd.Series:
    d = pd.read_csv(os.path.join(DATA, "fred", f"{sid}.csv"), parse_dates=["date"]).set_index("date")[sid]
    return d.dropna()


def fred_at(sid: str, date: str) -> float:
    return float(fred(sid).loc[:date].iloc[-1])


def price(tkr: str) -> pd.Series:
    d = pd.read_csv(os.path.join(DATA, "prices", f"{tkr}.csv"), parse_dates=["date"]).set_index("date")
    return d["adjclose"].dropna()


def price_close(tkr: str) -> pd.Series:
    d = pd.read_csv(os.path.join(DATA, "prices", f"{tkr}.csv"), parse_dates=["date"]).set_index("date")
    return d["close"].dropna()


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    for t in BIG6:
        print(t)
        print(segment_panel(t).round(2).tail(10))
        print(eps_series(t).round(2).tail(10).to_dict())
