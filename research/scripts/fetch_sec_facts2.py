"""Second XBRL pass: pull every tag matching the risk-analytics patterns we care about.

Pass 1 used a hand-written tag whitelist and missed the securities-portfolio and
regulatory-capital tags, whose names vary by filer. Regex selection is more robust.
Output is long-format so later scripts can pick whichever tag a given filer used.
"""

import os
import re
import time

import pandas as pd
import requests

HDRS = {"User-Agent": "Independent Research equity-research@example.com",
        "Accept-Encoding": "gzip, deflate"}

BASE = os.path.join(os.path.dirname(__file__), "..", "data", "sec")
OUT = os.path.join(BASE, "facts2")
os.makedirs(OUT, exist_ok=True)

PATTERNS = [
    r"DebtSecurities(AvailableForSale|HeldToMaturity)",
    r"AvailableForSaleSecurities",
    r"HeldToMaturitySecurities",
    r"AccumulatedOtherComprehensiveIncome",
    r"OtherComprehensiveIncome.*(Securities|Hedg|Tax)",
    r"TierOneRiskBasedCapital",
    r"^Tier(One|Two)",
    r"CommonEquityTierOne",
    r"RiskWeightedAssets",
    r"SupplementaryLeverage",
    r"NotionalAmountOf(Interest|Derivative)",
    r"DerivativeNotionalAmount",
    r"InterestRateSwap",
    r"CashFlowHedge",
    r"FinancingReceivable.*(AllowanceForCreditLoss|Recorded)",
    r"AllowanceForCreditLoss",
    r"(Loans|FinancingReceivable).*(Gross|BeforeAllowance|NetReported)",
    r"Deposits",
    r"InterestExpense",
    r"InterestAndDividendIncome",
    r"InterestIncomeExpense",
    r"Noninterest(Income|Expense)",
    r"ProvisionFor(Loan|Credit|Doubtful)",
    r"NetIncomeLoss$",
    r"EarningsPerShare",
    r"WeightedAverageNumberOf",
    r"^Assets$", r"^Liabilities$", r"StockholdersEquity",
    r"^Goodwill$", r"IntangibleAssets",
    r"^Revenues$", r"RevenuesNetOfInterestExpense",
    r"PrincipalTransactions", r"InvestmentBanking", r"Trading",
    r"(FeesAndCommissions|AssetManagement|InvestmentAdvisory)",
    r"ShareBasedCompensation",
    r"PaymentsForRepurchaseOfCommonStock",
    r"CommonStockDividends",
    r"AssetsUnderManagement",
    r"ChargeOff", r"NonaccrualLoan", r"NonperformingAsset",
    r"MortgageServicingRight", r"ServicingAsset",
]
PAT = re.compile("|".join(PATTERNS))


def get(url: str, tries: int = 5):
    for i in range(tries):
        try:
            r = requests.get(url, headers=HDRS, timeout=120)
            if r.status_code == 200:
                return r
            if r.status_code == 404:
                return None
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1.5 * (i + 1))
    return None


def main() -> None:
    import json
    uni = json.load(open(os.path.join(BASE, "universe.json")))
    for i, (tkr, cik) in enumerate(sorted(uni["cik"].items()), 1):
        dest = os.path.join(OUT, f"{tkr}.parquet")
        destc = os.path.join(OUT, f"{tkr}.csv")
        if os.path.exists(destc):
            print(f"[{i:3d}] {tkr:6s} cached"); continue
        r = get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        if r is None:
            print(f"[{i:3d}] {tkr:6s} FAIL"); continue
        rows = []
        for taxo, tags in r.json().get("facts", {}).items():
            for tag, body in tags.items():
                if not PAT.search(tag):
                    continue
                for unit, items in body.get("units", {}).items():
                    if unit not in {"USD", "USD/shares", "shares", "pure"}:
                        continue
                    for it in items:
                        rows.append((tag, unit, it.get("start"), it.get("end"),
                                     it.get("val"), it.get("form"), it.get("filed")))
        df = pd.DataFrame(rows, columns=["tag", "unit", "start", "end", "val", "form", "filed"])
        df.to_csv(destc, index=False)
        print(f"[{i:3d}] {tkr:6s} rows={len(df):7d} tags={df['tag'].nunique():4d} max_end={df['end'].max()}")
        time.sleep(0.16)


if __name__ == "__main__":
    main()
