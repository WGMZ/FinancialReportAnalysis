"""Per-bank quarterly P&L panel (Q3'25 .. Q2'26) from SEC XBRL, with derived ratios."""

import json
import os

import numpy as np
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..", "data", "sec")
Q = os.path.join(BASE, "quarterly")
OUT = os.path.join(os.path.dirname(__file__), "..", "output")

NII = ["InterestIncomeExpenseNet"]
NONII = ["NoninterestIncome"]
NONIE = ["NoninterestExpense"]
PROV = ["ProvisionForCreditLossesExpensed", "ProvisionForLoanLeaseAndOtherLosses",
        "ProvisionForLoanAndLeaseLossesExpensed"]
NI = ["NetIncomeLoss"]
NIC = ["NetIncomeLossAvailableToCommonStockholdersBasic"]
EPS = ["EarningsPerShareDiluted"]
SH = ["WeightedAverageNumberOfDilutedSharesOutstanding"]
REV = ["Revenues", "RevenuesNetOfInterestExpense"]
PTI = ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"]
TAX = ["IncomeTaxExpenseBenefit"]
IB = ["InvestmentBankingRevenue", "InvestmentBankingAdvisoryBrokerageAndUnderwritingFeesAndCommissions"]
TRD = ["PrincipalTransactionsRevenue", "TradingGainsLosses"]
AM = ["AssetManagementFees1", "InvestmentAdvisoryManagementAndAdministrativeFees",
      "FeesAndCommissionsAssetManagementCustodyAndDepositAccounts"]
ASSETS = ["Assets"]
EQ = ["StockholdersEquity"]
DEP = ["Deposits"]


def g(df, names, q):
    for n in names:
        if n in df.columns and q in df.index and pd.notna(df.loc[q, n]):
            return df.loc[q, n]
    return np.nan


def main():
    uni = json.load(open(os.path.join(BASE, "universe.json")))
    quarters = ["2025Q3", "2025Q4", "2026Q1", "2026Q2"]
    recs = []
    for t in sorted(uni["cik"]):
        p = os.path.join(Q, f"{t}.csv")
        if not os.path.exists(p):
            continue
        df = pd.read_csv(p, index_col=0)
        for q in quarters:
            recs.append({"t": t, "q": q,
                         "nii": g(df, NII, q), "nonii": g(df, NONII, q), "nonie": g(df, NONIE, q),
                         "prov": g(df, PROV, q), "ni": g(df, NI, q), "eps": g(df, EPS, q),
                         "sh": g(df, SH, q), "rev": g(df, REV, q), "pti": g(df, PTI, q),
                         "tax": g(df, TAX, q), "ib": g(df, IB, q), "trd": g(df, TRD, q),
                         "assets": g(df, ASSETS, q), "eq": g(df, EQ, q), "dep": g(df, DEP, q)})
    d = pd.DataFrame(recs)
    d.to_csv(os.path.join(OUT, "baseline_panel.csv"), index=False)
    return d


if __name__ == "__main__":
    d = main()
    pd.set_option("display.width", 250)
    banks = ["JPM", "BAC", "C", "WFC", "GS", "MS", "USB", "PNC", "TFC", "FITB", "HBAN", "CFG", "KEY",
             "RF", "MTB", "ZION", "BNY", "STT", "NTRS", "SCHW", "COF", "AXP"]
    for t in banks:
        s = d[d.t == t].set_index("q")[["nii", "nonii", "nonie", "prov", "ni", "eps", "sh", "ib", "trd"]].copy()
        for c in ["nii", "nonii", "nonie", "prov", "ni", "ib", "trd"]:
            s[c] = (s[c] / 1e6).round(0)
        s["sh"] = (s["sh"] / 1e6).round(0)
        print(f"--- {t} ($M, shares M)")
        print(s.to_string())
