"""Rates charts: curve change, benchmark bars, Q3 daily path, deposit-vs-loan repricing."""

import numpy as np
import pandas as pd

import chart_data as cd
from cstyle import *  # noqa: F403

TENORS = [("DGS1MO", 1 / 12), ("DGS3MO", 0.25), ("DGS6MO", 0.5), ("DGS1", 1), ("DGS2", 2), ("DGS3", 3),
          ("DGS5", 5), ("DGS7", 7), ("DGS10", 10), ("DGS20", 20), ("DGS30", 30)]
LBL = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
DATES = ["2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30", "2026-09-30"]


def curve(date):
    return np.array([cd.fred_at(s, date) for s, _ in TENORS])


def fig_curve(L):
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.6), gridspec_kw={"width_ratios": [1.25, 1]})
    names = [L("2025-09-30", "30 Sep 2025"), L("2025-12-31", "31 Dec 2025"), L("2026-03-31 (Q1末)", "31 Mar 2026"),
             L("2026-06-30 (Q2末)", "30 Jun 2026"), L("2026-09-30 (Q3末)", "30 Sep 2026")]
    x = np.arange(len(LBL))
    for d, n, c in zip(DATES, names, CURVE_COL):
        ax[0].plot(x, curve(d), marker="o", ms=3.5, lw=2.4 if d == DATES[-1] else 1.6, color=c, label=n)
    ax[0].set_xticks(x, LBL)
    ax[0].set_ylabel("%")
    ax[0].set_title(L("美国国债收益率曲线:Q3 整体上移并变陡", "US Treasury curve: Q3 shifted up and steepened"))
    ax[0].legend(loc="upper left")
    d = (curve(DATES[-1]) - curve(DATES[-2])) * 100
    cols = [C_UP if v > 0 else C_DN for v in d]
    b = ax[1].bar(x, d, color=cols)
    for xi, v in zip(x, d):
        ax[1].text(xi, v + 1.5, f"{v:+.0f}", ha="center", fontsize=8)
    ax[1].set_xticks(x, LBL)
    ax[1].set_ylabel("bp")
    ax[1].set_title(L("Q3 各期限变动 (bp)", "Q3 change by tenor (bp)"))
    s210_a = (cd.fred_at("DGS10", DATES[-2]) - cd.fred_at("DGS2", DATES[-2])) * 100
    s210_b = (cd.fred_at("DGS10", DATES[-1]) - cd.fred_at("DGS2", DATES[-1])) * 100
    ax[1].text(0.02, 0.97, L(f"2s10s: {s210_a:.0f} → {s210_b:.0f} bp\n(5Y 附近上移最多,曲线变陡)",
                             f"2s10s: {s210_a:.0f} → {s210_b:.0f} bp\n(belly rose most; curve steepened)"),
               transform=ax[1].transAxes, va="top", fontsize=9,
               bbox=dict(boxstyle="round", fc="#f4f6f7", ec="#cccccc"))
    ax[1].set_ylim(0, max(d) * 1.25)
    footer(fig, L("数据:FRED(DGS 系列,日度收益率,取季末最后一个观测值)。", "Source: FRED DGS series, last observation on or before each date."))
    return save(fig, L, "f01_yield_curve")


def fig_rate_bars(L):
    qe = ["2024-09-30", "2024-12-31", "2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30", "2026-09-30"]
    lab = ["24Q3", "24Q4", "25Q1", "25Q2", "25Q3", "25Q4", "26Q1", "26Q2", "26Q3"]
    series = [("DFF", L("联邦基金有效利率", "Fed funds (effective)"), "#7f8c8d"),
              ("DGS2", L("2 年期国债", "2Y Treasury"), "#2e86c1"),
              ("DGS10", L("10 年期国债", "10Y Treasury"), "#1f4e79"),
              ("MORTGAGE30US", L("30 年期按揭利率", "30Y mortgage rate"), "#e07b00")]
    fig, ax = plt.subplots(figsize=(11.5, 4.4))
    w = 0.2
    x = np.arange(len(qe))
    for i, (sid, nm, c) in enumerate(series):
        v = [cd.fred_at(sid, d) for d in qe]
        bars = ax.bar(x + (i - 1.5) * w, v, w, color=c, label=nm)
        if sid in ("DGS10",):
            for xi, vi in zip(x, v):
                ax.text(xi + (i - 1.5) * w, vi + 0.08, f"{vi:.2f}", ha="center", fontsize=7)
    ax.set_xticks(x, lab)
    ax.set_ylabel("%")
    ax.set_title(L("各季度末的政策利率与基准利率", "Policy and benchmark rates at each quarter-end"))
    ax.legend(ncol=4, loc="upper left")
    ax.set_ylim(0, 8.2)
    ax.axvspan(x[-1] - 0.5, x[-1] + 0.5, color="#fdebd0", alpha=0.5, zorder=0)
    footer(fig, L("数据:FRED。26Q3 为 9/30(按揭利率为周度,取最近一周)。数值标注为 10 年期。",
                  "Source: FRED. 26Q3 = 30 Sep (mortgage rate is weekly). Labels show the 10Y."))
    return save(fig, L, "f02_rate_bars")


def fig_q3_path(L):
    s = "2026-06-30"
    idx = pd.date_range("2026-07-01", "2026-09-30")
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.3))
    for sid, nm, c in [("DGS2", L("2Y", "2Y"), "#2e86c1"), ("DGS10", L("10Y", "10Y"), "#1f4e79"),
                       ("DFF", L("联邦基金", "Fed funds"), "#7f8c8d"), ("DGS30", "30Y", "#c0392b")]:
        v = cd.fred(sid).loc["2026-06-01":"2026-09-30"]
        ax[0].plot(v.index, v.values, label=nm, color=c, lw=1.8)
    ax[0].axvline(pd.Timestamp("2026-09-16"), color="#555", ls="--", lw=1)
    ax[0].text(pd.Timestamp("2026-09-15"), ax[0].get_ylim()[0] + 0.1, L("9/16 加息 25bp", "9/16 hike 25bp"), ha="right", fontsize=8)
    ax[0].set_title(L("Q3 日度走势:长端上行早于政策利率", "Q3 daily path: long end moved before the policy rate"))
    ax[0].set_ylabel("%")
    ax[0].legend(ncol=4, loc="upper left")
    spread = (cd.fred("DGS10") - cd.fred("DGS2")).loc["2026-01-01":"2026-09-30"] * 100
    ax[1].plot(spread.index, spread.values, color="#1f4e79")
    ax[1].fill_between(spread.index, spread.values, 0, alpha=0.15, color="#1f4e79")
    ax[1].set_title(L("2s10s 利差 (bp):2026 年初至今", "2s10s spread (bp), 2026 YTD"))
    ax[1].set_ylabel("bp")
    mn = spread.idxmin()
    ax[1].annotate(L(f"低点 {spread.min():.0f}bp", f"low {spread.min():.0f}bp"), (mn, spread.min()),
                   xytext=(mn, spread.min() + 20), arrowprops=dict(arrowstyle="->"), fontsize=8, ha="center")
    footer(fig, L("数据:FRED。", "Source: FRED."))
    return save(fig, L, "f03_q3_path")


def fig_transmission(L):
    q2 = ("2026-04-01", "2026-06-30")
    q3 = ("2026-07-01", "2026-09-30")
    ff_avg = (cd.fred("DFF").loc[q3[0]:q3[1]].mean() - cd.fred("DFF").loc[q2[0]:q2[1]].mean()) * 100
    ff_exit = (cd.fred_at("DFF", "2026-09-30") - cd.fred_at("DFF", "2026-06-30")) * 100
    ch = lambda sid: (cd.fred_at(sid, "2026-09-30") - cd.fred_at(sid, "2026-06-30")) * 100  # noqa: E731
    items = [
        (L("政策利率(季均)", "Policy rate (Q3 avg)"), ff_avg, "L"),
        (L("政策利率(期末)", "Policy rate (exit)"), ff_exit, "L"),
        (L("3M 国库券\n(同业/大额存单)", "3M T-bill\n(wholesale/CD)"), ch("DGS3MO"), "L"),
        (L("1Y 国债\n(1 年期 CD)", "1Y Treasury\n(1Y CD)"), ch("DGS1"), "L"),
        (L("2Y 国债\n(短久期证券)", "2Y Treasury\n(short securities)"), ch("DGS2"), "A"),
        (L("5Y 国债\n(商业贷款/汽车贷)", "5Y Treasury\n(C&I / auto)"), ch("DGS5"), "A"),
        (L("10Y 国债\n(MBS/CRE)", "10Y Treasury\n(MBS / CRE)"), ch("DGS10"), "A"),
        (L("30Y 按揭利率\n(住房抵押)", "30Y mortgage rate\n(residential)"), ch("MORTGAGE30US"), "A"),
    ]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.5, 1]})
    names = [i[0] for i in items]
    vals = [i[1] for i in items]
    cols = ["#c0392b" if i[2] == "L" else "#1f4e79" for i in items]
    y = np.arange(len(items))[::-1]
    ax[0].barh(y, vals, color=cols)
    for yi, v in zip(y, vals):
        ax[0].text(v + 1.5, yi, f"{v:+.0f}bp", va="center", fontsize=8)
    ax[0].set_yticks(y, names)
    ax[0].set_xlim(0, max(vals) * 1.2)
    ax[0].set_title(L("Q3 各参考利率的变动:负债端 (红) vs 资产端 (蓝)", "Q3 change in reference rates: liabilities (red) vs assets (blue)"))
    ax[0].set_xlabel("bp")

    bal = 100e3  # $M per $100bn
    beta = 0.4
    asset5 = ch("DGS5") / 1e4 * bal
    asset10 = ch("DGS10") / 1e4 * bal
    dep_avg = beta * ff_avg / 1e4 * bal
    dep_exit = beta * ff_exit / 1e4 * bal
    labs = [L("新增 5Y 资产\n年化收入增量", "New 5Y assets\nannual income"),
            L("新增 10Y 资产\n年化收入增量", "New 10Y assets\nannual income"),
            L("存款成本增量\n(季均, β=40%)", "Deposit cost\n(Q3 avg, β=40%)"),
            L("存款成本增量\n(期末, β=40%)", "Deposit cost\n(exit, β=40%)")]
    v2 = [asset5, asset10, -dep_avg, -dep_exit]
    c2 = ["#1f4e79", "#1f4e79", "#c0392b", "#c0392b"]
    ax[1].bar(range(4), v2, color=c2)
    for i, v in enumerate(v2):
        ax[1].text(i, v + (25 if v > 0 else -75), f"{v:+.0f}", ha="center", fontsize=8)
    ax[1].axhline(0, color="#333", lw=0.8)
    ax[1].set_xticks(range(4), labs, fontsize=7.5)
    ax[1].set_ylabel(L("百万美元 / 年 / 每 $1000 亿余额", "$M per year per $100bn"))
    ax[1].set_title(L("每 $1000 亿重定价余额的年化影响", "Annualised effect per $100bn that reprices"))
    footer(fig, L("示意性测算:假设 $1000 亿资产全部按 Q3 末利率与 Q2 末利率之差重定价;存款 beta 40% 为假设值,非披露值。\n"
                  "对实际 NII 而言,只有当期到期/新增的那部分资产才重定价,所以收入端的兑现是逐季的。",
                  "Illustrative: $100bn of assets fully repriced at the Q3-end vs Q2-end rate difference; the 40% deposit beta is an assumption, not a disclosure.\n"
                  "Only the portion that matures or is originated reprices, so the income benefit arrives gradually."),
           y=-0.01)
    return save(fig, L, "f04_transmission")


def run(L):
    return [fig_curve(L), fig_rate_bars(L), fig_q3_path(L), fig_transmission(L)]


if __name__ == "__main__":
    for code in ("zh", "en"):
        print(run(Lang(code)))
