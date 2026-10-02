"""Third XBRL pass: preferred equity, share counts, loans, CET1 ratio -- tags missing from earlier passes."""

import json
import os
import re
import time

import pandas as pd
import requests

HDRS = {"User-Agent": "Independent Research equity-research@example.com", "Accept-Encoding": "gzip, deflate"}
BASE = os.path.join(os.path.dirname(__file__), "..", "data", "sec")
OUT = os.path.join(BASE, "facts3")
os.makedirs(OUT, exist_ok=True)

PAT = re.compile(
    r"^(PreferredStockValue|PreferredStockCarryingValue|PreferredStockIncludingAdditionalPaidInCapitalNetOfDiscount|"
    r"CommonStockSharesOutstanding|EntityCommonStockSharesOutstanding|"
    r"LoansAndLeasesReceivableNetReportedAmount|LoansAndLeasesReceivableGrossCarryingAmount|"
    r"FinancingReceivableExcludingAccruedInterestBeforeAllowanceForCreditLoss|"
    r"FinancingReceivableExcludingAccruedInterestAfterAllowanceForCreditLoss|"
    r"LoansReceivableNet|LoansAndLeasesReceivableNetOfDeferredIncome|"
    r"CommonEquityTierOneCapitalRatio|CommonEquityTierOneCapital|TierOneRiskBasedCapitalToRiskWeightedAssets|"
    r"RiskWeightedAssets|TierOneLeverageCapitalToAverageAssets|"
    r"InterestBearingDepositLiabilities|NoninterestBearingDepositLiabilities|DepositsDomestic|"
    r"DepositsSavingsDeposits|DepositsMoneyMarketDeposits|TimeDeposits|"
    r"Deposits|LongTermDebt|ShortTermBorrowings|FederalHomeLoanBankAdvances.*|"
    r"SecuritiesSoldUnderAgreementsToRepurchase|Cash.*|InterestBearingDepositsInBanks)$")


def get(url):
    for i in range(5):
        try:
            r = requests.get(url, headers=HDRS, timeout=120)
            if r.status_code == 200:
                return r
            if r.status_code == 404:
                return None
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1.5 * (i + 1))


def main():
    uni = json.load(open(os.path.join(BASE, "universe.json")))
    for t, cik in sorted(uni["cik"].items()):
        dest = os.path.join(OUT, f"{t}.csv")
        if os.path.exists(dest):
            continue
        r = get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        if r is None:
            print(t, "FAIL")
            continue
        rows = []
        for taxo, tags in r.json().get("facts", {}).items():
            for tag, body in tags.items():
                if not PAT.match(tag):
                    continue
                for unit, items in body.get("units", {}).items():
                    for it in items:
                        rows.append((taxo, tag, unit, it.get("start"), it.get("end"), it.get("val"), it.get("form"), it.get("filed")))
        pd.DataFrame(rows, columns=["taxo", "tag", "unit", "start", "end", "val", "form", "filed"]).to_csv(dest, index=False)
        print(t, len(rows))
        time.sleep(0.16)


if __name__ == "__main__":
    main()
