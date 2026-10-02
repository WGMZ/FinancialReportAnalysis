"""Driver-based Q3 2026 EPS model with Monte Carlo.

EPS_Q3 = ((PBT_Q2_clean + sum(delta_i)) * (1 - t3) - pref) / shares_Q3

Every delta_i is a $M change in pre-tax profit versus the clean Q2 base, taken from management
guidance (Sep-2026 Barclays conference, July-2026 earnings calls) or from the Q2 filings. Items carry a
standard deviation and an optional loading on a common factor:
    mkt    capital-markets activity (IB, trading, investment gains); one draw shared by all banks
    rate   net-interest-income surprise (curve / deposit beta / day count)
    credit provision surprise
Loading is signed: compensation savings load negatively on the capital-markets factor (revenue down,
bonus accrual down).  A 2.5% multiplicative model-risk term is added to every bank.
"""

import os

import numpy as np
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(BASE, "output")
RNG = np.random.default_rng(20261013)
N = 40000
RHO = 0.6

M, R, C = "mkt", "rate", "credit"

# name, mean ($M change in pre-tax profit), sd, (factor, signed loading) or None
BANKS = {
    "JPM": dict(eps2=6.14, sh2=2694, sh3=2675, pref=411, t2=.235, t3=.235, items=[
        ("NII ex-Markets (FY guide 105.5bn total)", 1000, 300, (R, 1)),
        ("Markets revenue 12.1bn -> ~10.4bn (+16.5% YoY guide)", -1700, 800, (M, 1)),
        ("IB fees 3.2bn -> ~3.0bn (+mid/high-teens YoY)", -160, 300, (M, 1)),
        ("Asset & wealth fees (avg S&P +4.8%)", 200, 100, None),
        ("Card/payments/other fees", 100, 150, None),
        ("Opex (variable comp; FY 107.5bn)", 350, 350, (M, -.5)),
        ("Provision (card NCO 3.2% guide)", -100, 400, (C, -1)),
    ]),
    "GS": dict(eps2=20.98, sh2=305, sh3=303, pref=229, t2=.226, t3=.225, items=[
        ("Investments line 'much more muted'", -1800, 700, (M, 1)),
        ("Equities (strong)", -300, 500, (M, 1)),
        ("FICC (softer)", -600, 450, (M, 1)),
        ("IB fees", -300, 300, (M, 1)),
        ("NII / mgmt fees", 200, 150, None),
        ("Compensation accrual falls with revenue", 840, 200, (M, -.5)),
        ("Non-comp expense +$0.5bn+ (guide)", -550, 120, None),
        ("Provision 'slightly higher'", -200, 120, (C, -1)),
    ]),
    "MS": dict(eps2=3.46, sh2=1569, sh3=1560, pref=152, t2=.24, t3=.23, items=[
        ("Equities (3Q is no 2Q)", -450, 450, (M, 1)),
        ("FICC", -250, 300, (M, 1)),
        ("IB (100+ sponsor mandates)", 100, 250, (M, 1)),
        ("Unrealized carry reversal (mgmt)", -200, 80, None),
        ("Wealth NII + fees", 150, 120, None),
        ("Compensation accrual", 250, 150, (M, -.5)),
        ("Other expense", -50, 80, None),
    ]),
    "BAC": dict(eps2=1.21, sh2=7294, sh3=7200, pref=248, t2=.215, t3=.205, items=[
        ("NII ex-Markets (upper end of +6-8%)", 300, 150, (R, 1)),
        ("Sales & trading 7.1bn -> ~5.5bn ('flat YoY' vs 5.4bn)", -1550, 350, (M, 1)),
        ("IB fees 2.1bn -> 1.6-1.8bn (guide)", -400, 120, (M, 1)),
        ("Asset management fees", 100, 80, None),
        ("Other fees", 50, 150, None),
        ("Opex (~18.6bn)", 150, 200, (M, -.4)),
        ("Provision", -50, 250, (C, -1)),
    ]),
    "C": dict(eps2=3.15, sh2=1735.6, sh3=1710, pref=364, t2=.25, t3=.245, items=[
        ("Markets (+mid-single-digit YoY guide)", -700, 400, (M, 1)),
        ("IB (+low-single-digit YoY guide)", -150, 150, (M, 1)),
        ("Services/Wealth/USPB revenue", 250, 200, None),
        ("Opex", 100, 250, None),
        ("Provision (card)", -100, 300, (C, -1)),
    ]),
    "WFC": dict(eps2=2.00, sh2=3074.6, sh3=3038, pref=258, t2=.174, t3=.19, items=[
        ("NII (FY ~50bn; NIM stabilises)", 200, 150, (R, 1)),
        ("Non-interest income after strong Q2", -450, 450, (M, 1)),
        ("Opex (FY ~55.7bn)", -190, 250, None),
        ("Provision", -90, 200, (C, -1)),
    ]),
    "USB": dict(eps2=1.35, sh2=1555, sh3=1548, pref=78, t2=.215, t3=.215, items=[
        ("NII (+4-6% YoY, high end)", 73, 50, (R, 1)),
        ("Fees (+12-14% YoY incl. BTIG)", 150, 120, (M, .3)),
        ("Opex (+8% YoY incl. BTIG)", -105, 60, None),
        ("Provision incl. Amazon reserve build $160m", -120, 80, (C, -1)),
    ]),
    "PNC": dict(eps2=4.85, sh2=403, sh3=401, pref=100, t2=.195, t3=.195, items=[
        ("NII +3-3.5% QoQ", 135, 40, (R, 1)),
        ("Fee income -5 to -5.5% QoQ", -120, 60, (M, 1)),
        ("Other non-interest income 150-200m vs 265m adj Q2", -90, 50, None),
        ("Adj. expense -2 to -3% QoQ", 96, 40, None),
        ("Provision (NCO ~225m)", 0, 60, (C, -1)),
    ]),
    "TFC": dict(eps2=1.23, sh2=1239, sh3=1215, pref=100, t2=.145, t3=.145, items=[
        ("NII +1.5% QoQ", 54, 30, (R, 1)),
        ("Non-interest income flat guide, but Q2 other income +106m QoQ may not repeat", -60, 80, (M, 1)),
        ("Expense +2% QoQ", -61, 40, None),
        ("Provision", -25, 60, (C, -1)),
    ]),
    "FITB": dict(eps2=0.83, sh2=916, sh3=912, pref=41, t2=.20, t3=.20, items=[
        ("NII +2-2.5% QoQ (CFO: upper end)", 55, 25, (R, 1)),
        ("Non-interest income +1-3% (CFO: upper end)", 31, 20, (M, 1)),
        ("Expense: 1.86bn x0.985 + merger ~200m (conversion qtr) + other 15m vs 2.11bn", 62, 100, None),
        ("Provision", -20, 50, (C, -1)),
    ]),
    "HBAN": dict(eps2=0.33, sh2=2048, sh3=2040, pref=41, t2=.184, t3=.19, items=[
        ("NII flat (FY growth cut to ~35%)", 0, 40, (R, 1)),
        ("Non-interest income", 20, 50, (M, 1)),
        ("Expense: merger costs fade", 60, 60, None),
        ("Provision", 0, 30, (C, -1)),
    ]),
    "CFG": dict(eps2=1.30, sh2=427, sh3=423, pref=32, t2=.21, t3=.21, items=[
        ("NII +2.5-3.5% QoQ", 49, 25, (R, 1)),
        ("Non-interest income +1%", 7, 30, (M, 1)),
        ("Expense flat/slightly up", -10, 25, None),
        ("Provision", 0, 30, (C, -1)),
    ]),
    "KEY": dict(eps2=0.44, sh2=1080, sh3=1075, pref=34, t2=.21, t3=.21, items=[
        ("NII (FY +9-11%; NIM exit 3.00-3.05%)", 45, 25, (R, 1)),
        ("Non-interest income (FY +4-5%)", 50, 40, (M, 1)),
        ("Adj. expense (FY ~+4%)", -43, 25, None),
        ("Provision", -3, 25, (C, -1)),
    ]),
    "MTB": dict(eps2=5.32, sh2=147, sh3=145.5, pref=36, t2=.24, t3=.24, items=[
        ("NII (lower half of 7.2-7.35bn)", 10, 25, (R, 1)),
        ("Fees: Q2 Bayview distribution not repeated", -40, 40, (M, 1)),
        ("Expense (high end of 5.5-5.6bn)", -57, 30, None),
        ("Provision", 0, 30, (C, -1)),
    ]),
    "SCHW": dict(eps2=1.62, sh2=1739, sh3=1732, pref=113, t2=.235, t3=.235, items=[
        ("Net interest revenue (NIM +5bp, IEA +1%)", 105, 80, (R, 1)),
        ("Asset mgmt & admin fees", 65, 40, None),
        ("Trading revenue (lower vol)", -60, 80, (M, 1)),
        ("Expense", -60, 40, None),
    ]),
}

PRIOR_ONLY = {  # EPS prior relative to consensus: mean surprise, sd
    "BNY": (0.04, 0.05, "Q2 base contains notable items; FY revenue +10-11%, NII +12-13% guide; habitual beater"),
    "COF": (0.01, 0.08, "Card NCO 3.23% trending lower, Discover integration costs falling; Q3 seasonally weaker NIM"),
}


def simulate(cfg, factors):
    pbt2 = (cfg["eps2"] * cfg["sh2"] + cfg["pref"]) / (1 - cfg["t2"])
    delta = np.zeros(N)
    for _, mu, sd, f in cfg["items"]:
        e = RNG.standard_normal(N)
        if f is None:
            z = e
        else:
            name, load = f
            load = load * RHO
            z = load * factors[name] + np.sqrt(1 - load**2) * e
        delta += mu + sd * z
    ni = (pbt2 + delta) * (1 - cfg["t3"]) - cfg["pref"]
    eps = ni / cfg["sh3"] * (1 + 0.025 * RNG.standard_normal(N))
    eps_pt = ((pbt2 + sum(i[1] for i in cfg["items"])) * (1 - cfg["t3"]) - cfg["pref"]) / cfg["sh3"]
    return eps, eps_pt


def main():
    cons = pd.read_csv(os.path.join(BASE, "data", "consensus_q3_2026.csv")).set_index("t")
    factors = {k: RNG.standard_normal(N) for k in (M, R, C)}
    rows = []
    for t, cfg in BANKS.items():
        eps, pt = simulate(cfg, factors)
        c = cons.loc[t, "cons_eps"]
        rows.append({
            "t": t, "q2_eps": cfg["eps2"], "cons_eps": c, "model_pt": pt, "mean": eps.mean(),
            "p10": np.percentile(eps, 10), "p90": np.percentile(eps, 90),
            "surp_pct": 100 * (eps.mean() / c - 1), "p_beat": (eps > c).mean(), "p_beat3": (eps > c * 1.03).mean(),
            "p_miss3": (eps < c * 0.97).mean(), "method": "driver",
        })
    for t, (mu, sd, _) in PRIOR_ONLY.items():
        c = cons.loc[t, "cons_eps"]
        eps = c * (1 + mu + sd * RNG.standard_normal(N))
        rows.append({
            "t": t, "q2_eps": cons.loc[t, "q2_eps_ref"], "cons_eps": c, "model_pt": c * (1 + mu), "mean": eps.mean(),
            "p10": np.percentile(eps, 10), "p90": np.percentile(eps, 90), "surp_pct": 100 * mu,
            "p_beat": (eps > c).mean(), "p_beat3": (eps > c * 1.03).mean(), "p_miss3": (eps < c * 0.97).mean(),
            "method": "prior",
        })
    df = pd.DataFrame(rows).round(3).sort_values("surp_pct", ascending=False)
    df.to_csv(os.path.join(OUT, "q3_model.csv"), index=False)
    pd.set_option("display.width", 220)
    print(df.to_string(index=False))

    bridge = []
    for t, cfg in BANKS.items():
        for name, mu, sd, _ in cfg["items"]:
            bridge.append({"t": t, "item": name, "d_pbt_musd": mu, "sd": sd})
    pd.DataFrame(bridge).to_csv(os.path.join(OUT, "q3_model_bridge.csv"), index=False)


if __name__ == "__main__":
    main()
