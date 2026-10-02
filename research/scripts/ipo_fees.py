"""IPO league table, fee estimates by bank, and Q4 pipeline. Writes CSVs and chart f14.

Fees: disclosed in the prospectus/424B4 where marked 'disclosed'; otherwise gross spread x proceeds
('est'). Per-bank split: weights by role (lead / global coordinator = 2, joint bookrunner = 1,
co-manager = 0.5); explicit dollar splits where press reported them. These are estimates, not bank disclosures.
"""

import os

import numpy as np
import pandas as pd

from cstyle import *  # noqa: F403

OUT = os.path.join(BASE, "output")
D = os.path.join(OUT, "data")
os.makedirs(D, exist_ok=True)
TRACK = ["GS", "MS", "JPM", "BAC", "C", "WFC"]

# name, date, sector, proceeds $M (base deal), fee $M or None, spread if est, roles {bank: weight}, "Other" weight under key 'OTH'
Q3 = [
    ("SK hynix", "2026-07-09", "Semis / ADR", 26507, 257.5, None, {"explicit": {"C": 70.0, "BAC": 55.0, "GS": 55.0, "JPM": 55.0}}),
    ("Jersey Mike's", "2026-07-29", "Consumer", 1000, 50.0, None, {"MS": 2, "JPM": 2, "BAC": 1, "GS": 1, "OTH": 9}),
    ("Csquare", "2026-07-16", "Telecom svcs", 1050, 40.0, None, {"MS": 2, "WFC": 1, "BAC": 1, "JPM": 1, "OTH": 7}),
    ("Accelevation", "2026-09-30", "Industrial", 540, None, 0.05, {"MS": 2, "JPM": 2, "GS": 2, "BAC": 1, "OTH": 4}),
    ("ADARx", "2026-09-24", "Biotech", 446.3, None, 0.07, {"JPM": 2, "MS": 2, "OTH": 4}),
    ("Braveheart Bio", "2026-08-05", "Biotech", 382.5, None, 0.07, {"GS": 2, "OTH": 5}),
    ("Electra", "2026-09-17", "Biotech", 350, None, 0.07, {"OTH": 6}),
    ("Latigo", "2026-08-06", "Biotech", 345.6, None, 0.07, {"GS": 2, "OTH": 4}),
    ("Lyntris", "2026-08-18", "Tech", 298, None, 0.07, {"C": 2, "BAC": 1, "OTH": 4}),
    ("Attovia", "2026-08-04", "Biotech", 289, 20.23, None, {"MS": 2, "C": 1, "OTH": 3}),
    ("Orion180", "2026-09-17", "Biotech", 240, None, 0.07, {"GS": 1, "OTH": 6}),
    ("Reformation", "2026-07-29", "Consumer", 211, None, 0.07, {"JPM": 2, "MS": 2, "C": 1, "OTH": 1}),
    ("Apnimed", "2026-07-30", "Biotech", 192, None, 0.07, {"BAC": 2, "OTH": 4}),
    ("Robinhood Ventures Fund II", "2026-09", "Closed-end fund", 200, None, 0.045, {"GS": 1, "C": 1, "JPM": 1, "WFC": 1, "OTH": 2}),
    ("Standard Nuclear", "2026-07-15", "Energy", 150, None, 0.07, {"BAC": 2, "GS": 2, "OTH": 1}),
    ("BlossomHill", "2026-08-06", "Biotech", 150, None, 0.07, {"JPM": 2, "OTH": 4}),
    ("American Savings Bank", "2026-09-15", "Bank (secondary)", 129, None, 0.06, {"OTH": 1}),
    ("River City Bank", "2026-08-05", "Bank (secondary)", 121.5, 5.913, None, {"OTH": 1}),
]
SPACEX = {"GS": 100.0, "MS": 100.0, "JPM": 75.0, "BAC": 75.0, "C": 75.0, "WFC": 0.0, "OTH": 75.0}
Q3_TOTAL_BN, Q3_EX_SKH_BN = 34.9, 8.4

# Q4 pipeline: name, timing, size $M (None = n/d), spread, leads, status
PIPE = [
    ("Anthropic", "Nov 2026 (after midterms)", 100000, 0.0067, "MS, GS (leads); JPM, Citi", "roadshow mid-Oct; no public S-1 yet"),
    ("Oura", "Postponed on 9/29", 2150, 0.05, "n/d", "planned 50M sh at $40-44; postponed"),
    ("Entrata", "Q4", 500, 0.06, "GS, JPM, Barclays", "NYSE: ENT; ~$500M target"),
    ("SB Energy", "Q4 (reportedly delayed)", None, None, "JPM, GS, MS, Citi + others", "S-1/A #2 on 9/21; NVIDIA $3B private placement"),
    ("Encore", "Q4", None, None, "BofA, GS, MS", "size n/d"),
    ("Aggreko", "Q4", None, None, "n/d", "F-1 filed, NYSE: AGKO"),
    ("Nscale", "Q4", None, None, "n/d", "NYSE filing"),
    ("Inspire Brands", "year-end / early 2027", None, None, "n/d", "timing may slip"),
    ("City Therapeutics", "Q4", None, None, "GS, Jefferies", "biotech; size n/d"),
    ("OpenAI", "2027", None, None, "n/d", "pushed to 2027"),
]


def q3_tables():
    rows, banks = [], []
    for nm, dt, sec, pr, fee, sp, roles in Q3:
        est = fee is None
        fee_m = pr * sp if est else fee
        if "explicit" in roles:
            alloc = dict(roles["explicit"])
            alloc["OTH"] = fee_m - sum(alloc.values())
        else:
            tot = sum(roles.values())
            alloc = {k: fee_m * w / tot for k, w in roles.items()}
        rows.append(dict(deal=nm, date=dt, sector=sec, proceeds_usd_m=pr, fee_usd_m=round(fee_m, 2),
                         fee_pct=round(fee_m / pr * 100, 2), fee_basis="estimate" if est else "disclosed"))
        for b, v in alloc.items():
            banks.append(dict(deal=nm, bank=b, fee_usd_m=round(v, 2)))
    deals = pd.DataFrame(rows)
    bank = pd.DataFrame(banks).pivot_table(index="deal", columns="bank", values="fee_usd_m", aggfunc="sum").fillna(0.0)
    bank = bank.reindex(deals.deal)
    for b in TRACK + ["OTH"]:
        if b not in bank:
            bank[b] = 0.0
    bank = bank[TRACK + ["OTH"]]
    return deals, bank


def q4_tables():
    p = pd.DataFrame(PIPE, columns=["deal", "timing", "size_usd_m", "spread", "leads", "status"])
    p["fee_est_usd_m"] = p.size_usd_m * p.spread
    return p


def anthropic_grid():
    rows = []
    for size in (60000, 100000):
        for sp in (0.005, 0.0067, 0.01):
            pool = size * sp
            rows.append(dict(size_bn=size / 1000, spread_pct=sp * 100, pool_usd_m=pool,
                             lead_each_usd_m=pool * 0.20, other_major_each_usd_m=pool * 0.15))
    return pd.DataFrame(rows)


def fig_ipo(L, deals, bank, ib_q3):
    fig, ax = plt.subplots(1, 3, figsize=(15, 5.2), gridspec_kw={"width_ratios": [1.15, 1, 1.05]})
    pal = {"SK hynix": "#c0392b", "Jersey Mike's": "#e07b00", "Csquare": "#2e86c1", "Accelevation": "#117a65"}
    a = ax[0]
    x = np.arange(len(TRACK))
    w = 0.38
    q3 = bank[TRACK].sum()
    major = bank.loc[["SK hynix", "Jersey Mike's", "Csquare", "Accelevation"]][TRACK]
    rest = bank[TRACK].drop(index=major.index).sum()
    bot = np.zeros(len(TRACK))
    for nm in major.index:
        v = major.loc[nm].values
        a.bar(x + w / 2, v, w, bottom=bot, color=pal[nm], label=nm, edgecolor="white", lw=0.4)
        bot += v
    a.bar(x + w / 2, rest.values, w, bottom=bot, color=C_OTH, label=L("其余 Q3 交易", "Other Q3 deals"), edgecolor="white", lw=0.4)
    a.bar(x - w / 2, [SPACEX[b] for b in TRACK], w, color="#6c3483", label=L("Q2 SpaceX(参考)", "Q2 SpaceX (ref.)"))
    for i, b in enumerate(TRACK):
        a.text(i + w / 2, q3[b] + 3, f"{q3[b]:.0f}", ha="center", fontsize=8)
        a.text(i - w / 2, SPACEX[b] + 3, f"{SPACEX[b]:.0f}", ha="center", fontsize=8)
    a.set_xticks(x, TRACK)
    a.set_ylabel("$ M")
    a.set_title(L("IPO 承销费估算:Q3 vs Q2 SpaceX", "Estimated IPO fees: Q3 vs Q2 SpaceX"))
    a.legend(fontsize=7.5, loc="upper right")

    a = ax[1]
    share = [q3[b] / (ib_q3[b] * 1000) * 100 for b in TRACK]
    a.bar(TRACK, share, color=[BANK_COL[b] for b in TRACK])
    for i, v in enumerate(share):
        a.text(i, v + 0.3, f"{v:.1f}%", ha="center", fontsize=9)
    a.set_ylabel("%")
    a.set_title(L("Q3 IPO 费用(估) 占 Q3E 投行费用比重", "Est. Q3 IPO fees as % of Q3E IB fees"))

    a = ax[2]
    g = anthropic_grid()
    cats = [f"${r.size_bn:.0f}B\n{r.spread_pct:.2f}%" for r in g.itertuples()]
    a.bar(cats, g.pool_usd_m, color=["#d6eaf8"] * 3 + ["#85c1e9"] * 3)
    a.bar(cats, g.lead_each_usd_m, color="#6c3483", width=0.35, label=L("牵头行各得(20%)", "Each lead bank (20%)"))
    for i, r in enumerate(g.itertuples()):
        a.text(i, r.pool_usd_m + 10, f"{r.pool_usd_m:.0f}", ha="center", fontsize=8)
    a.set_ylabel("$ M")
    a.set_title(L("Q4 情景:Anthropic 费用池(规模 × 费率)", "Q4 scenario: Anthropic fee pool (size x spread)"))
    a.legend(fontsize=8)
    fig.tight_layout()
    footer(fig, L("费用:招股书披露(SK hynix、Jersey Mike's、Csquare、Attovia、River City)或 费率×规模估算;各行分成按牵头/联席角色加权,为估算而非银行披露。\n"
                  "SpaceX:费用池约 5 亿美元(GS/MS 各约 1 亿,BofA/Citi/JPM 各约 7500 万)。Anthropic 为情景推演,规模/费率/份额均为假设(份额沿用 SpaceX 的 20%/15%)。",
                  "Fees: disclosed in prospectuses (SK hynix, Jersey Mike's, Csquare, Attovia, River City) or spread x size; per-bank split weighted by role - estimates, not bank disclosures.\n"
                  "SpaceX fee pool ~$500M (GS/MS ~$100M each; BofA/Citi/JPM ~$75M each). Anthropic is a scenario: size, spread and shares are assumptions (shares follow SpaceX 20%/15%)."), y=-0.01)
    return save(fig, L, "f14_ipo_fees")


def main():
    deals, bank = q3_tables()
    deals.to_csv(os.path.join(D, "ipo_deals.csv"), index=False)
    bank.reset_index().to_csv(os.path.join(D, "ipo_fees_by_bank.csv"), index=False)
    q4_tables().to_csv(os.path.join(D, "ipo_pipeline.csv"), index=False)
    anthropic_grid().to_csv(os.path.join(D, "ipo_anthropic_scenarios.csv"), index=False)
    seg = pd.read_csv(os.path.join(D, "segment_panel.csv"))
    ib = seg[seg.q == "2026Q3E"].set_index("ticker").ib
    for code in ("zh", "en"):
        print(fig_ipo(Lang(code), deals, bank, ib))
    print(deals.fee_usd_m.sum(), bank.sum().round(1).to_dict())
    print((bank.sum()[TRACK] / (ib[TRACK] * 1000) * 100).round(1).to_dict())


if __name__ == "__main__":
    main()
