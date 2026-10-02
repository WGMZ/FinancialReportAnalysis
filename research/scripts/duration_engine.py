"""Estimate each bank's effective securities duration empirically, then price the Q3-2026 move.

Why regression instead of the disclosed maturity ladder: for agency MBS the *stated*
maturity (30y) is meaningless -- effective duration is 4-7y and moves with rates. But
the unrealized loss on the book is observable every quarter, and so is the yield curve.

    UL%_t  =  -D * y_t + c            (UL% = unrealized loss / amortized cost)
    d(UL%) =  -D * dy  +  roll

Regressing the quarterly change in UL% on the quarterly change in the benchmark yield
gives D directly; the intercept absorbs pull-to-par and portfolio turnover.
"""

import json
import os

import numpy as np
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..", "data")
F2 = os.path.join(BASE, "sec", "facts2")
FRED = os.path.join(BASE, "fred")

# ---------------------------------------------------------------- tag aliases
AFS_AC = [
    "DebtSecuritiesAvailableForSaleAmortizedCostExcludingAccruedInterestAfterAllowanceForCreditLoss",
    "DebtSecuritiesAvailableForSaleAmortizedCostExcludingAccruedInterestBeforeAllowanceForCreditLoss",
    "DebtSecuritiesAvailableForSaleAmortizedCostAfterAllowanceForCreditLoss",
    "DebtSecuritiesAvailableForSaleAmortizedCostBeforeAllowanceForCreditLoss",
    "DebtSecuritiesAvailableForSaleAmortizedCost",
    "AvailableForSaleSecuritiesAmortizedCost",
    "AvailableForSaleDebtSecuritiesAmortizedCostBasis",
]
AFS_FV = [
    "DebtSecuritiesAvailableForSaleExcludingAccruedInterest",
    "AvailableForSaleSecuritiesDebtSecurities",
    "DebtSecuritiesAvailableForSale",
    "AvailableForSaleSecurities",
]
AFS_UL = [
    "DebtSecuritiesAvailableForSaleAccumulatedGrossUnrealizedLossBeforeTax",
    "DebtSecuritiesAvailableForSaleUnrealizedLossPositionAccumulatedLoss",
    "AvailableForSaleSecuritiesGrossUnrealizedLosses",
    "AvailableForSaleSecuritiesGrossUnrealizedLoss",
]
AFS_UG = [
    "DebtSecuritiesAvailableForSaleAccumulatedGrossUnrealizedGainBeforeTax",
    "AvailableForSaleSecuritiesGrossUnrealizedGains",
    "AvailableForSaleSecuritiesGrossUnrealizedGain",
]
HTM_AC = [
    "DebtSecuritiesHeldToMaturityExcludingAccruedInterestAfterAllowanceForCreditLoss",
    "DebtSecuritiesHeldToMaturityExcludingAccruedInterestBeforeAllowanceForCreditLoss",
    "DebtSecuritiesHeldToMaturityAmortizedCostAfterAllowanceForCreditLoss",
    "DebtSecuritiesHeldToMaturityAmortizedCostBeforeAllowanceForCreditLoss",
    "HeldToMaturitySecurities",
]
HTM_FV = ["HeldToMaturitySecuritiesFairValue", "DebtSecuritiesHeldToMaturityFairValue"]
HTM_UL = [
    "HeldToMaturitySecuritiesAccumulatedUnrecognizedHoldingLoss",
    "DebtSecuritiesHeldToMaturityAccumulatedUnrecognizedHoldingLoss",
]
HTM_UG = [
    "HeldToMaturitySecuritiesAccumulatedUnrecognizedHoldingGain",
    "DebtSecuritiesHeldToMaturityAccumulatedUnrecognizedHoldingGain",
]
AOCI = ["AccumulatedOtherComprehensiveIncomeLossNetOfTax"]
AOCI_AFS = [
    "AccumulatedOtherComprehensiveIncomeLossAvailableForSaleSecuritiesAdjustmentNetOfTax",
    "AociAvailableForSaleSecuritiesAdjustmentNetOfTax",
]
AOCI_CFH = [
    "AccumulatedGainLossNetCashFlowHedgeParentNetOfTax",
    "AccumulatedOtherComprehensiveIncomeLossCumulativeChangesInNetGainLossFromCashFlowHedgesEffectNetOfTax",
]
EQUITY = ["StockholdersEquity"]
GOODWILL = ["Goodwill"]
INTANG = ["IntangibleAssetsNetExcludingGoodwill", "FiniteLivedIntangibleAssetsNet"]
ASSETS = ["Assets"]
DEPOSITS = ["Deposits"]


def load(tkr: str) -> pd.DataFrame:
    df = pd.read_csv(os.path.join(F2, f"{tkr}.csv"), low_memory=False)
    df["end"] = pd.to_datetime(df["end"], errors="coerce")
    df["filed"] = pd.to_datetime(df["filed"], errors="coerce")
    df = df.dropna(subset=["end", "val"])
    df = df[df["start"].isna()]  # instants only
    qe = df["end"].dt.to_period("Q").dt.end_time.dt.normalize()
    df = df[(df["end"] - qe).dt.days.abs() <= 7]
    df["q"] = df["end"].dt.to_period("Q")
    return df.sort_values("filed")


def series(df: pd.DataFrame, aliases: list[str]) -> pd.Series:
    """Pick the first alias that has data; return quarterly series (latest filing wins)."""
    for a in aliases:
        s = df[df["tag"] == a]
        if len(s) >= 1:
            s = s.drop_duplicates(subset=["q"], keep="last")
            out = s.set_index("q")["val"].sort_index()
            if out.notna().sum() >= 1:
                return out
    return pd.Series(dtype=float)


def fred_q(sid: str) -> pd.Series:
    d = pd.read_csv(os.path.join(FRED, f"{sid}.csv"), parse_dates=["date"])
    d = d.set_index("date")[sid]
    # quarter-end observation (last available on/before quarter end)
    idx = pd.period_range("2015Q1", "2026Q3", freq="Q")
    vals = {}
    for p in idx:
        sub = d.loc[:p.end_time]
        if len(sub):
            vals[p] = sub.iloc[-1]
    return pd.Series(vals)


def regress_duration(ul_pct: pd.Series, y: pd.Series, min_obs: int = 8):
    """d(UL%) = -D*dy + roll ; returns (D, roll_per_q, r2, n)."""
    common = ul_pct.index.intersection(y.index)
    u, yy = ul_pct.reindex(common).astype(float), y.reindex(common).astype(float)
    du, dy = u.diff(), yy.diff()
    m = du.notna() & dy.notna() & (dy.abs() > 1e-9)
    du, dy = du[m], dy[m]
    if len(du) < min_obs:
        return (np.nan, np.nan, np.nan, len(du))
    X = np.column_stack([dy.values, np.ones(len(dy))])
    beta, *_ = np.linalg.lstsq(X, du.values, rcond=None)
    pred = X @ beta
    ss_res = float(((du.values - pred) ** 2).sum())
    ss_tot = float(((du.values - du.values.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return (-beta[0], beta[1], r2, len(du))


def main() -> None:
    uni = json.load(open(os.path.join(BASE, "sec", "universe.json")))
    y5, y10 = fred_q("DGS5"), fred_q("DGS10")
    mbs = fred_q("MORTGAGE30US")
    blend = (0.5 * y5 + 0.5 * y10)

    rows = []
    for tkr in sorted(uni["cik"]):
        try:
            df = load(tkr)
        except Exception:  # noqa: BLE001
            continue
        afs_ac, afs_fv = series(df, AFS_AC), series(df, AFS_FV)
        afs_ul, afs_ug = series(df, AFS_UL), series(df, AFS_UG)
        htm_ac, htm_fv = series(df, HTM_AC), series(df, HTM_FV)
        htm_ul, htm_ug = series(df, HTM_UL), series(df, HTM_UG)

        # net unrealized position; prefer FV-AC (cleanest), else gains-losses
        afs_net = (afs_fv - afs_ac).dropna()
        if afs_net.empty and not afs_ul.empty:
            afs_net = (afs_ug.reindex(afs_ul.index).fillna(0) - afs_ul).dropna()
        htm_net = (htm_fv - htm_ac).dropna()
        if htm_net.empty and not htm_ul.empty:
            htm_net = (htm_ug.reindex(htm_ul.index).fillna(0) - htm_ul).dropna()

        rec = {"ticker": tkr}
        for name, net, ac, bench in [("afs", afs_net, afs_ac, blend), ("htm", htm_net, htm_ac, mbs)]:
            if net.empty or ac.empty:
                continue
            pct = (net / ac.reindex(net.index)).dropna() * 100  # % of amortized cost
            D, roll, r2, n = regress_duration(pct, bench)
            rec[f"{name}_ac"] = ac.get(pd.Period("2026Q2"), np.nan)
            rec[f"{name}_net_unreal"] = net.get(pd.Period("2026Q2"), np.nan)
            rec[f"{name}_unreal_pct"] = pct.get(pd.Period("2026Q2"), np.nan)
            rec[f"{name}_dur_emp"] = D
            rec[f"{name}_roll_q"] = roll
            rec[f"{name}_r2"] = r2
            rec[f"{name}_n"] = n

        for nm, al in [("aoci", AOCI), ("aoci_afs", AOCI_AFS), ("aoci_cfh", AOCI_CFH),
                       ("equity", EQUITY), ("goodwill", GOODWILL), ("intang", INTANG),
                       ("assets", ASSETS), ("deposits", DEPOSITS)]:
            s = series(df, al)
            rec[nm] = s.get(pd.Period("2026Q2"), np.nan)
        rows.append(rec)

    out = pd.DataFrame(rows).set_index("ticker")
    out.to_csv(os.path.join(BASE, "sec", "duration_estimates.csv"))

    pd.set_option("display.width", 260)
    cols = ["afs_ac", "afs_unreal_pct", "afs_dur_emp", "afs_r2", "afs_n",
            "htm_ac", "htm_unreal_pct", "htm_dur_emp", "htm_r2", "htm_n"]
    v = out.reindex(columns=cols).copy()
    v["afs_ac"] /= 1e9
    v["htm_ac"] /= 1e9
    print(v.dropna(subset=["afs_ac", "htm_ac"], how="all").round(2).to_string())
    print("\n-> data/sec/duration_estimates.csv")


if __name__ == "__main__":
    main()
