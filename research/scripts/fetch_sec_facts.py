"""Download SEC XBRL companyfacts and distill them into tidy quarterly fact tables.

companyfacts returns every tag a filer has ever used; we keep only the ~45 tags that
matter for a bank/broker earnings model and write one tidy CSV per ticker.
"""

import json
import os
import time

import pandas as pd
import requests

HDRS = {"User-Agent": "Independent Research equity-research@example.com",
        "Accept-Encoding": "gzip, deflate"}

BASE = os.path.join(os.path.dirname(__file__), "..", "data", "sec")
RAW = os.path.join(BASE, "facts")
os.makedirs(RAW, exist_ok=True)

KEEP = {
    # income statement
    "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenuesNetOfInterestExpense",
    "InterestAndDividendIncomeOperating", "InterestIncomeExpenseNet",
    "InterestIncomeExpenseAfterProvisionForLoanLoss",
    "InterestExpense", "InterestExpenseDeposits", "InterestExpenseBorrowings",
    "NoninterestIncome", "NoninterestExpense",
    "ProvisionForLoanLeaseAndOtherLosses", "ProvisionForLoanAndLeaseLossesExpensed",
    "ProvisionForCreditLossesExpensed", "ProvisionForDoubtfulAccounts",
    "NetIncomeLoss", "NetIncomeLossAvailableToCommonStockholdersBasic",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "IncomeTaxExpenseBenefit",
    "EarningsPerShareDiluted", "EarningsPerShareBasic",
    "WeightedAverageNumberOfDilutedSharesOutstanding",
    "WeightedAverageNumberOfSharesOutstandingBasic",
    # fee lines that separate the business models
    "InvestmentBankingRevenue", "InvestmentBankingAdvisoryBrokerageAndUnderwritingFeesAndCommissions",
    "PrincipalTransactionsRevenue", "TradingGainsLosses",
    "FeesAndCommissions", "FeesAndCommissionsAssetManagementCustodyAndDepositAccounts",
    "AssetManagementFees1", "InvestmentAdvisoryManagementAndAdministrativeFees",
    "FeesAndCommissionsCreditCards", "FeesAndCommissionsMortgageBankingAndServicing",
    "FeesAndCommissionsDepositorAccounts",
    "BrokerageCommissionsRevenue",
    # balance sheet
    "Assets", "Liabilities", "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    "Deposits", "DepositsDomestic", "InterestBearingDepositLiabilities",
    "NoninterestBearingDepositLiabilities",
    "LoansAndLeasesReceivableNetReportedAmount",
    "NotesReceivableNet",
    "FinancingReceivableExcludingAccruedInterestBeforeAllowanceForCreditLoss",
    "AvailableForSaleSecuritiesDebtSecurities", "AvailableForSaleSecurities",
    "DebtSecuritiesAvailableForSaleAmortizedCost",
    "HeldToMaturitySecurities", "HeldToMaturitySecuritiesFairValue",
    "DebtSecuritiesHeldToMaturityAmortizedCostAfterAllowanceForCreditLoss",
    "AccumulatedOtherComprehensiveIncomeLossNetOfTax",
    "FinancingReceivableAllowanceForCreditLosses",
    "LongTermDebt", "LongTermDebtNoncurrent",
    "CommonStockSharesOutstanding",
    "PaymentsForRepurchaseOfCommonStock",
    "GoodwillAndIntangibleAssetsIntangibleAssetsNet", "Goodwill", "IntangibleAssetsNetExcludingGoodwill",
    "AssetsUnderManagementCarryingAmount",
}


def get(url: str, tries: int = 5):
    for i in range(tries):
        try:
            r = requests.get(url, headers=HDRS, timeout=90)
            if r.status_code == 200:
                return r
            if r.status_code == 404:
                return None
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1.5 * (i + 1))
    return None


def distill(facts: dict, ticker: str) -> pd.DataFrame:
    rows = []
    for taxo, tags in facts.get("facts", {}).items():
        for tag, body in tags.items():
            if tag not in KEEP:
                continue
            for unit, items in body.get("units", {}).items():
                for it in items:
                    rows.append({
                        "ticker": ticker, "taxonomy": taxo, "tag": tag, "unit": unit,
                        "start": it.get("start"), "end": it.get("end"),
                        "val": it.get("val"), "fy": it.get("fy"), "fp": it.get("fp"),
                        "form": it.get("form"), "filed": it.get("filed"),
                        "frame": it.get("frame"),
                    })
    return pd.DataFrame(rows)


def main() -> None:
    uni = json.load(open(os.path.join(BASE, "universe.json")))
    ciks = uni["cik"]
    summary = []
    for i, (tkr, cik) in enumerate(sorted(ciks.items()), 1):
        out = os.path.join(RAW, f"{tkr}.csv")
        if os.path.exists(out):
            print(f"[{i:3d}] {tkr:6s} cached")
            continue
        r = get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        if r is None:
            print(f"[{i:3d}] {tkr:6s} FAILED")
            summary.append((tkr, 0))
            time.sleep(0.2)
            continue
        df = distill(r.json(), tkr)
        df.to_csv(out, index=False)
        latest = df[df["end"] >= "2026-01-01"]["end"].max() if len(df) else None
        print(f"[{i:3d}] {tkr:6s} rows={len(df):7d}  latest_period_end={latest}")
        summary.append((tkr, len(df)))
        time.sleep(0.16)  # stay under SEC's 10 req/s
    print("\ndone", len(summary))


if __name__ == "__main__":
    main()
