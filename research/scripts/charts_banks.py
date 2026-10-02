"""Bank-level charts: revenue lines + Q3E, EPS, P/E, market dashboard, AFS/HTM, stress test."""

import os

import numpy as np
import pandas as pd

import chart_data as cd
from cstyle import *  # noqa: F403

D = os.path.join(cd.OUT, "data")
BANKS = cd.BIG6
QLAB = lambda q: q[2:4] + "Q" + q[5] + ("E" if q.endswith("E") else "")  # noqa: E731


def seg():
    return pd.read_csv(os.path.join(D, "segment_panel.csv"))


def fig_segments(L):
    d = seg()
    names = {"nii": L("净利息收入", "Net interest income"), "ib": L("投行费用", "IB fees"),
             "trading": L("交易/做市", "Trading / market-making"), "other": L("其他非息收入", "Other non-interest")}
    cols = {"nii": C_NII, "ib": C_IB, "trading": C_TRD, "other": C_OTH}
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.2))
    for ax, t in zip(axes.flat, BANKS):
        s = d[d.ticker == t].reset_index(drop=True)
        x = np.arange(len(s))
        bottom = np.zeros(len(s))
        for k in ("nii", "trading", "ib", "other"):
            v = s[k].values.astype(float)
            if k == "other":
                v = v - s["oneoff"].values
            ax.bar(x, v, bottom=bottom, color=cols[k], width=0.75, label=names[k],
                   hatch=None, edgecolor="white", linewidth=0.4)
            bottom += v
        if (s.oneoff > 0).any():
            i = s.index[s.oneoff > 0][0]
            ax.bar(i, s.oneoff[i], bottom=bottom[i], color="none", edgecolor="#555", hatch="////", width=0.75,
                   label=L("Visa 一次性收益", "Visa one-off gain"))
        iE = len(s) - 1
        ax.bar(iE, bottom[iE], color="none", edgecolor=C_FC, linewidth=1.6, width=0.75, linestyle="--")
        for xi, tot, rev in zip(x, bottom, s.total.values):
            ax.text(xi, tot + 0.4 + (s.oneoff.iloc[xi] if s.oneoff.iloc[xi] > 0 else 0), f"{tot:.1f}", ha="center", fontsize=7)
        ax.set_xticks(x, [QLAB(q) for q in s.q], rotation=0, fontsize=7.5)
        ax.get_xticklabels()[-1].set_color(C_FC)
        ax.get_xticklabels()[-1].set_fontweight("bold")
        ax.set_title(t, color=BANK_COL[t])
        ax.set_ylabel(L("十亿美元", "$ bn"))
    h, l = axes.flat[0].get_legend_handles_labels()
    h2, l2 = axes.flat[0].get_legend_handles_labels()
    seen = {}
    for ax in axes.flat:
        for hh, ll in zip(*ax.get_legend_handles_labels()):
            seen.setdefault(ll, hh)
    fig.legend(seen.values(), seen.keys(), loc="upper center", ncol=6, bbox_to_anchor=(0.5, 1.02))
    fig.suptitle(L("大行/投行收入结构:近 8 个季度 + Q3 预测 (E, 紫色虚线框)", "Revenue mix, last 8 quarters + Q3 estimate (E, dashed purple)"),
                 y=1.07, fontsize=13, fontweight="bold")
    footer(fig, L("数据:SEC XBRL 与 10-Q/10-K 表格;Q4 = 全年 − 前三季。BAC/WFC 的 IB 费来自附注;GS 的做市收入仅为附注口径(不含做市 NII)。\n"
                  "Q3E = Q2 + 本报告 EPS bridge 的收入项变动;JPM 的 Q2 已扣除 Visa 一次性收益(斜线);BAC/MS/GS 的 S&T 变动记入'交易/做市'(含其 NII 部分,为近似)。",
                  "Source: SEC XBRL and 10-Q/10-K tables; Q4 = FY − 9M. IB fees for BAC/WFC come from fee notes; GS market-making is the note definition (excl. its NII).\n"
                  "Q3E = Q2 + revenue lines of this report's EPS bridge; JPM Q2 excludes the Visa one-off (hatched); S&T changes for BAC/MS/GS are booked to Trading (includes the NII part, approximate)."),
           y=0.0)
    fig.tight_layout()
    return save(fig, L, "f05_segments")


def fig_segment_changes(L):
    d = seg()
    names = {"nii": L("净利息收入", "NII"), "ib": L("投行费用", "IB fees"), "trading": L("交易/做市", "Trading"),
             "other": L("其他非息", "Other")}
    cols = {"nii": C_NII, "ib": C_IB, "trading": C_TRD, "other": C_OTH}
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 8.2))
    for ax, (base_q, ttl) in zip(axes, [("2026Q2", L("Q3E 对比 Q2'26 (环比, $bn)", "Q3E vs Q2'26 (QoQ, $bn)")),
                                         ("2025Q3", L("Q3E 对比 Q3'25 (同比, $bn)", "Q3E vs Q3'25 (YoY, $bn)"))]):
        x = np.arange(len(BANKS))
        w = 0.19
        tot = []
        for i, k in enumerate(("nii", "ib", "trading", "other")):
            vals = []
            for t in BANKS:
                s = d[d.ticker == t].set_index("q")
                b = s.loc[base_q, k] - (s.loc[base_q, "oneoff"] if k == "other" else 0)
                vals.append(s.loc["2026Q3E", k] - b)
            ax.bar(x + (i - 1.5) * w, vals, w, color=cols[k], label=names[k])
        for xi, t in zip(x, BANKS):
            s = d[d.ticker == t].set_index("q")
            tt = s.loc["2026Q3E", "total"] - (s.loc[base_q, "total"] - s.loc[base_q, "oneoff"])
            pct = tt / (s.loc[base_q, "total"] - s.loc[base_q, "oneoff"]) * 100
            ax.text(xi, ax.get_ylim()[1] * 0.9, f"{L('合计', 'Total')} {tt:+.1f}\n({pct:+.1f}%)", ha="center", fontsize=8,
                    bbox=dict(boxstyle="round", fc="#f4f6f7", ec="#cccccc"))
        ax.axhline(0, color="#333", lw=0.8)
        ax.set_xticks(x, BANKS)
        ax.set_title(ttl)
        ax.set_ylabel(L("十亿美元", "$ bn"))
        ax.legend(ncol=4, loc="lower left")
        lo, hi = ax.get_ylim()
        ax.set_ylim(lo, hi * 1.25)
    footer(fig, L("同比对比的基数 Q3'25 无一次性项目;环比基数已扣除 JPM 的 Visa 收益。BAC 的 S&T 环比约 −$1.55bn 是本季最大的单项拖累。",
                  "The Q3'25 base has no one-offs; the QoQ base excludes JPM's Visa gain. BAC's ~−$1.55bn QoQ S&T move is the largest single drag."))
    fig.tight_layout()
    return save(fig, L, "f06_segment_changes")


def eps_table():
    return pd.read_csv(os.path.join(D, "eps_history.csv"))


def fig_eps(L):
    e = eps_table()
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    for ax, t in zip(axes.flat, BANKS):
        s = e[(e.ticker == t) & (e.kind == "actual")]
        s = s[s.q >= "2024Q1"]
        x = {q: i for i, q in enumerate(list(s.q) + ["2026Q3E"])}
        ax.plot([x[q] for q in s.q], s.eps, marker="o", color=BANK_COL[t], lw=2, label=L("实际 (GAAP 稀释)", "Actual (GAAP diluted)"))
        m = e[(e.ticker == t) & (e.kind == "model")].iloc[0]
        ix = x["2026Q3E"]
        ax.errorbar([ix], [m.eps], yerr=[[m.eps - m.p10], [m.p90 - m.eps]], fmt="D", color=C_FC, capsize=4,
                    label=L("本报告模型 (P10–P90)", "Model (P10–P90)"))
        ax.plot([ix], [m.cons], marker="x", ms=9, mew=2, color="#c0392b", ls="", label=L("卖方共识", "Consensus"))
        adj = e[(e.ticker == t) & (e.eps_adj.notna())]
        if len(adj):
            ax.plot([x["2026Q2"]], [adj.eps_adj.iloc[0]], marker="s", color="#7f8c8d", ls="", ms=7,
                    label=L("JPM Q2 调整后 (剔 Visa)", "JPM Q2 adjusted (ex Visa)"))
        ax.plot([x[s.q.iloc[-1]], ix], [s.eps.iloc[-1], m.eps], ls=":", color=C_FC)
        ax.set_xticks(list(x.values()), [QLAB(q) for q in x], rotation=60, fontsize=7)
        ax.set_title(f"{t}  Q3E ${m.eps:.2f} vs {L('共识', 'cons.')} ${m.cons:.2f}", color=BANK_COL[t], fontsize=11)
        ax.set_ylabel("$ / share")
    seen = {}
    for ax in axes.flat:
        for hh, ll in zip(*ax.get_legend_handles_labels()):
            seen.setdefault(ll, hh)
    fig.legend(seen.values(), seen.keys(), loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.03))
    footer(fig, L("数据:SEC XBRL(Q4 = 全年 − 前三季,EPS 为近似);C 的 26Q1/Q2 来自 10-Q 表格。Q2'26 的 JPM/WFC/GS/MS 含季度性高点,GS 为 $20.98。\n"
                  "共识来自多家聚合页,口径可能混用 GAAP 与调整后,详见 consensus_q3_2026.csv。", 
                  "Source: SEC XBRL (Q4 = FY − 9M, EPS approximated); C's 26Q1/Q2 from 10-Q tables. Consensus is aggregated from several pages and may mix GAAP/adjusted; see consensus_q3_2026.csv."))
    fig.tight_layout()
    return save(fig, L, "f07_eps")


def ttm_eps(t, asof):
    e = eps_table()
    s = e[(e.ticker == t) & (e.kind == "actual")].copy()
    s["eps_use"] = np.where(s.eps_adj.notna(), s.eps_adj, s.eps)
    s["qend"] = pd.PeriodIndex(s.q, freq="Q").end_time.normalize()
    s["avail"] = s.qend + pd.Timedelta(days=16)
    s = s[s.avail <= asof].sort_values("qend")
    if len(s) < 4:
        return np.nan
    return s.eps_use.iloc[-4:].sum()


def fig_pe(L):
    e = eps_table()
    dates = pd.date_range("2025-08-01", "2026-10-01", freq="W-FRI")
    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.6), gridspec_kw={"width_ratios": [1.7, 1]})
    last = {}
    for t in BANKS:
        px = cd.price_close(t)
        pe = []
        for d in dates:
            p = px.loc[:d].iloc[-1]
            te = ttm_eps(t, d)
            pe.append(p / te if te and te > 0 else np.nan)
        ax[0].plot(dates, pe, label=t, color=BANK_COL[t], lw=1.8)
        pnow = px.iloc[-1]
        te_now = ttm_eps(t, pd.Timestamp("2026-10-01"))
        m = e[(e.ticker == t) & (e.kind == "model")].iloc[0]
        q3_25 = e[(e.ticker == t) & (e.q == "2025Q3") & (e.kind == "actual")].eps.iloc[0]
        roll = te_now - q3_25 + m.eps
        last[t] = (pnow / te_now, pnow / roll)
    ax[0].set_title(L("滚动 12 个月 (TTM) 市盈率", "Trailing-12M P/E"))
    ax[0].set_ylabel("x")
    ax[0].legend(ncol=6, loc="upper left")
    ax[0].axvline(pd.Timestamp("2026-09-16"), color="#888", ls="--", lw=0.8)
    x = np.arange(len(BANKS))
    ax[1].bar(x - 0.2, [last[t][0] for t in BANKS], 0.4, color="#9aa5b1", label=L("TTM (至 Q2'26)", "TTM (to Q2'26)"))
    ax[1].bar(x + 0.2, [last[t][1] for t in BANKS], 0.4, color=C_FC, label=L("滚动含 Q3E", "Rolled incl. Q3E"))
    for xi, t in zip(x, BANKS):
        ax[1].text(xi - 0.2, last[t][0] + 0.15, f"{last[t][0]:.1f}", ha="center", fontsize=8)
        ax[1].text(xi + 0.2, last[t][1] + 0.15, f"{last[t][1]:.1f}", ha="center", fontsize=8)
    ax[1].set_xticks(x, BANKS)
    ax[1].set_title(L("10/1 收盘价的市盈率", "P/E at the 1 Oct close"))
    ax[1].legend()
    footer(fig, L("价格:Yahoo 收盘价(未复权);EPS:GAAP 稀释,季报披露后 16 天起计入;JPM 的 Q2'26 取剔除 Visa 的 $6.14。GS 的 EPS 波动大,P/E 区间随之变化。",
                  "Price: Yahoo close (unadjusted); EPS: GAAP diluted, counted 16 days after quarter-end; JPM Q2'26 uses $6.14 ex-Visa. GS EPS is volatile, so its P/E swings."))
    fig.tight_layout()
    return save(fig, L, "f08_pe")


def fig_market(L):
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 7.6))
    start = "2025-10-01"
    ax = axes[0, 0]
    for t in BANKS:
        p = cd.price(t).loc[start:]
        ax.plot(p.index, p / p.iloc[0] * 100, color=BANK_COL[t], lw=1.5, label=t)
    ax.set_title(L("大行股价 (起点=100)", "Big-bank prices (start = 100)"))
    ax.legend(ncol=3, fontsize=8)
    ax = axes[0, 1]
    for t, nm, c, ls in [("KBWB", L("KBWB 银行", "KBWB banks"), "#1f4e79", "-"), ("KRE", L("KRE 区域银行", "KRE regionals"), "#b03a2e", "-"),
                         ("SPY", "SPY", "#555", "-"), ("SMH", L("SMH 芯片", "SMH chips"), "#e07b00", "-"), ("TLT", L("TLT 长债", "TLT long bonds"), "#2e8b57", "--")]:
        p = cd.price(t).loc[start:]
        ax.plot(p.index, p / p.iloc[0] * 100, color=c, ls=ls, lw=1.6, label=nm)
    ax.set_title(L("银行 vs 区域银行 vs 大盘 vs 芯片 vs 长债", "Banks vs regionals vs market vs chips vs long bonds"))
    ax.legend(ncol=2, fontsize=8)
    ax = axes[1, 0]
    v = cd.price_close("idx_VIX").loc[start:]
    ax.plot(v.index, v.values, color="#c0392b", label="VIX")
    ax.set_ylabel("VIX")
    ax2 = ax.twinx()
    y10 = cd.fred("DGS10").loc[start:]
    ax2.plot(y10.index, y10.values, color="#1f4e79", label=L("10Y 收益率", "10Y yield"))
    ax2.set_ylabel(L("10Y (%)", "10Y (%)"))
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    ax.set_title(L("波动率与 10 年期收益率", "Volatility and the 10Y yield"))
    ax.legend(loc="upper left")
    ax2.legend(loc="upper right")
    ax = axes[1, 1]
    w = cd.fred("DCOILWTICO").loc[start:]
    ax.plot(w.index, w.values, color="#7b241c", label="WTI")
    ax.set_ylabel("WTI $/bbl")
    ax3 = ax.twinx()
    mt = cd.fred("MORTGAGE30US").loc[start:]
    ax3.plot(mt.index, mt.values, color="#e07b00", label=L("30Y 按揭利率", "30Y mortgage"))
    ax3.set_ylabel("%")
    ax3.grid(False)
    ax3.spines["right"].set_visible(True)
    ax.set_title(L("油价与按揭利率", "Oil and mortgage rates"))
    ax.legend(loc="upper left")
    ax3.legend(loc="upper right")
    for a in axes.flat:
        a.tick_params(axis="x", labelrotation=30)
    footer(fig, L("数据:Yahoo(复权收盘价)、FRED。", "Source: Yahoo (adjusted close), FRED."))
    fig.tight_layout()
    return save(fig, L, "f09_market")


def afs_htm():
    return pd.read_csv(os.path.join(D, "afs_htm_history.csv"))


def proforma():
    rs = pd.read_csv(os.path.join(cd.OUT, "risk_scorecard.csv")).set_index("t")
    st = pd.read_csv(os.path.join(D, "stress_test.csv"))
    rows = {}
    for t in BANKS:
        earn_q = st[st.ticker == t].annual_earn.iloc[0] / 4
        if t == "C":
            tce = st[st.ticker == "C"].tce.iloc[0]
            aoci = -3.046 * 0.875
            htm = -4.5 * 0.0054 * 167.893
            rows[t] = dict(tce=tce, aoci=aoci, htm=htm * 0.76, earn_q=earn_q, htm_pre=htm,
                           note="AOCI 取 10-Q 披露的 +100bp 敏感度 × 0.875")
        else:
            r = rs.loc[t]
            rows[t] = dict(tce=r.tce_bn, aoci=r.q3_aoci_hit_bn, htm=r.q3_htm_mark_bn * 0.76, earn_q=earn_q,
                           htm_pre=r.q3_htm_mark_bn, note="")
    df = pd.DataFrame(rows).T
    df["aoci_pct_tce"] = 100 * df.aoci.astype(float) / df.tce.astype(float)
    df["htm_pct_tce"] = 100 * df.htm.astype(float) / df.tce.astype(float)
    df["aoci_x_q3e"] = -df.aoci.astype(float) / df.earn_q.astype(float)
    df["htm_x_q3e"] = -df.htm.astype(float) / df.earn_q.astype(float)
    return df


def fig_afs_htm_book(L):
    a = afs_htm()
    figs = []
    for kind, ttl in (("htm", L("HTM 持有至到期证券:摊余成本 vs 公允价值 ($bn)", "HTM securities: amortized cost vs fair value ($bn)")),
                      ("afs", L("AFS 可供出售证券:摊余成本 vs 公允价值 ($bn)", "AFS securities: amortized cost vs fair value ($bn)"))):
        fig, axes = plt.subplots(2, 3, figsize=(13, 7))
        for ax, t in zip(axes.flat, BANKS):
            s = a[(a.ticker == t) & (a.q >= "2024Q2")].sort_values("q")
            if s.empty:
                continue
            x = np.arange(len(s))
            ac, fv = s[f"{kind}_ac"].values, s[f"{kind}_fv"].values
            if np.isnan(ac).all():
                ax.bar(x, fv, 0.6, color="#2e86c1", label=L("公允价值", "Fair value"))
                ax.text(0.5, 0.92, L("摊余成本未能从 XBRL 取得", "Amortized cost not in XBRL"), transform=ax.transAxes, ha="center", fontsize=8, color="#777")
            else:
                ax.bar(x - 0.2, ac, 0.4, color="#9aa5b1", label=L("摊余成本", "Amortized cost"))
                ax.bar(x + 0.2, fv, 0.4, color="#2e86c1", label=L("公允价值", "Fair value"))
                gap = fv - ac
                ax2 = ax.twinx()
                ax2.plot(x, gap, color="#c0392b", marker="o", ms=3, lw=1.5, label=L("浮亏(右轴)", "Unrealized gain/loss (rhs)"))
                ax2.grid(False)
                ax2.spines["right"].set_visible(True)
                if t == "BAC" and kind == "htm":
                    ax2.annotate(f"{gap[-1]:.0f}", (x[-1], gap[-1]), textcoords="offset points", xytext=(0, -12), ha="center", fontsize=8, color="#c0392b")
                else:
                    ax2.annotate(f"{gap[-1]:.1f}", (x[-1], gap[-1]), textcoords="offset points", xytext=(0, -12), ha="center", fontsize=8, color="#c0392b")
            ax.set_xticks(x, [QLAB(q) for q in s.q], rotation=60, fontsize=7)
            ax.set_title(t, color=BANK_COL[t])
        h, l = axes.flat[0].get_legend_handles_labels()
        seen = {}
        for ax in fig.axes:
            for hh, ll in zip(*ax.get_legend_handles_labels()):
                seen.setdefault(ll, hh)
        fig.legend(seen.values(), seen.keys(), loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.03))
        fig.suptitle(ttl, y=1.08, fontsize=13, fontweight="bold")
        footer(fig, L("数据:SEC XBRL。C 仅有 2025Q4 与 2026Q2 两个时点(10-Q 表格)。WFC、GS 的 AFS 摊余成本在 XBRL 中缺失,只画公允价值。\n"
                      "JPM/BAC 的 AFS 因利率互换对冲,摊余成本含对冲调整,浮亏远小于未对冲的久期暗示。",
                      "Source: SEC XBRL. C has only 2025Q4 and 2026Q2 (10-Q tables). WFC/GS AFS amortized cost is not tagged, so only fair value is shown.\n"
                      "JPM/BAC AFS books are swap-hedged, so unrealized losses are much smaller than their unhedged duration implies."))
        fig.tight_layout()
        figs.append(save(fig, L, f"f10_{kind}_book"))
    return figs


def fig_proforma(L):
    p = proforma()
    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.6))
    x = np.arange(len(BANKS))
    a = p.loc[BANKS, "aoci_pct_tce"].astype(float).values
    h = p.loc[BANKS, "htm_pct_tce"].astype(float).values
    ax[0].bar(x, a, 0.6, color="#c0392b", label=L("AFS → AOCI (进入资本)", "AFS → AOCI (hits capital)"))
    ax[0].bar(x, h, 0.6, bottom=a, color="#e59866", label=L("HTM 公允价值减值 (税后,不进资本)", "HTM mark (after tax, not in capital)"))
    for xi, aa, hh, t in zip(x, a, h, BANKS):
        ax[0].text(xi, aa + hh - 0.4, f"{aa + hh:.1f}%", ha="center", fontsize=8, va="top")
    ax[0].set_xticks(x, BANKS)
    ax[0].set_ylabel(L("占 TCE (%)", "% of TCE"))
    ax[0].set_title(L("Q3 利率上行对账面价值的冲击 (占 TCE)", "Q3 rate-rise hit to book value (% of TCE)"))
    ax[0].legend(loc="lower left")
    ax[0].set_ylim(min(a + h) * 1.3, 0.5)
    ae = p.loc[BANKS, "aoci_x_q3e"].astype(float).values
    he = p.loc[BANKS, "htm_x_q3e"].astype(float).values
    ax[1].bar(x, ae, 0.6, color="#c0392b", label="AFS")
    ax[1].bar(x, he, 0.6, bottom=ae, color="#e59866", label="HTM")
    for xi, aa, hh in zip(x, ae, he):
        ax[1].text(xi, aa + hh + 0.01, f"{aa + hh:.2f}x", ha="center", fontsize=8)
    ax[1].set_xticks(x, BANKS)
    ax[1].set_title(L("冲击相当于几个季度的 Q3E 净利润", "Hit measured in quarters of Q3E net income"))
    ax[1].set_ylabel(L("倍 (季度净利润)", "x quarterly net income"))
    ax[1].legend()
    footer(fig, L("方法:ΔTCE = −D×Δy×摊余成本×(1−24%);Q3 Δy:AFS 用 5Y/10Y 均值 +87.5bp,HTM 用按揭利率 +54bp;久期由季度回归得到(见第 2.2 节),WFC/GS 为兜底值。\nC 取 10-Q 披露的 +100bp AOCI 敏感度(−$3.05bn)× 0.875,HTM 用兜底久期 4.5。HTM 不进监管资本,是'经济账面价值'的隐性损失。",
                  "Method: ΔTCE = −D×Δy×amortized cost×(1−24%). Q3 Δy: AFS 5Y/10Y blend +87.5bp, HTM mortgage rate +54bp; D from the quarterly regression (§2.2), fallback for WFC/GS.\nC uses the disclosed +100bp AOCI sensitivity (−$3.05bn) × 0.875 and fallback HTM duration 4.5. HTM is outside regulatory capital but is a hidden 'economic book value' loss."))
    fig.tight_layout()
    return save(fig, L, "f11_proforma")


SC_NAME = lambda L: {"p50": L("+50bp 平行", "+50bp parallel"), "p100": L("+100bp 平行", "+100bp parallel"),  # noqa: E731
                     "p200": L("+200bp 平行", "+200bp parallel"), "steep": L("熊陡:长端 +100bp", "Bear steepener: long +100bp"),
                     "flat": L("熊平:短端 +100bp", "Bear flattener: short +100bp")}


def fig_stress_bars(L):
    st = pd.read_csv(os.path.join(D, "stress_test.csv"))
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), sharey=False)
    for ax, sc in zip(axes, ["p100", "p200", "steep"]):
        s = st[st.scenario == sc].set_index("ticker").loc[BANKS]
        x = np.arange(len(BANKS))
        w = 0.2
        ax.bar(x - 1.5 * w, s.nii_after_tax.fillna(0), w, color=C_NII, label=L("12 个月 NII (税后)", "12M NII (after tax)"))
        ax.bar(x - 0.5 * w, s.aoci_hit, w, color="#c0392b", label=L("AFS→AOCI (税后)", "AFS→AOCI (after tax)"))
        ax.bar(x + 0.5 * w, s.htm_mark_after_tax, w, color="#e59866", label=L("HTM 减值 (税后)", "HTM mark (after tax)"))
        ax.scatter(x + 1.5 * w, s.net_econ_12m, marker="D", color="#111", zorder=5, label=L("净经济影响", "Net economic effect"))
        for xi, v in zip(x, s.net_econ_12m):
            if not np.isnan(v):
                ax.text(xi + 1.5 * w, v - 2.2, f"{v:.0f}", ha="center", fontsize=7)
        ax.axhline(0, color="#333", lw=0.8)
        ax.set_xticks(x, BANKS)
        ax.set_title(SC_NAME(L)[sc])
        ax.set_ylabel(L("十亿美元", "$ bn"))
    axes[0].legend(loc="lower left", fontsize=8)
    fig.suptitle(L("压力测试:继续加息的第一年影响 ($bn)", "Stress test: first-year effect of further hikes ($bn)"), y=1.03, fontsize=13, fontweight="bold")
    footer(fig, L("NII:10-Q 披露的 12 个月敏感度(静态资产负债表、含存款 beta 假设),税率 24%;+200 对 WFC 为线性外推。GS 为净收入 EaR,MS 仅财富管理分部,低估。\n"
                  "AOCI/HTM:同一久期模型 × 冲击幅度(长端 ≥3 年);C 的 AOCI 为披露值。NII 是 12 个月累计的缓慢收益,AOCI 是即时损失;两者不可直接相加解读为'资本变化',净经济影响含 HTM 减值,仅作排序参考。",
                  "NII: 12-month sensitivity from the 10-Qs (static balance sheet, deposit-beta assumptions), 24% tax; +200 for WFC is a linear extrapolation. GS is net-revenue EaR and MS covers Wealth Management only, so both understate.\n"
                  "AOCI/HTM: same duration model × shock (long end ≥3Y); C's AOCI is as disclosed. NII accrues over 12 months while AOCI is instantaneous; the net economic effect includes the HTM mark and is a ranking aid only."),
           y=-0.03)
    fig.tight_layout()
    return save(fig, L, "f12_stress_bars")


def fig_stress_heat(L):
    st = pd.read_csv(os.path.join(D, "stress_test.csv"))
    scs = ["p50", "p100", "p200", "steep", "flat"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.3))
    for ax, col, ttl in [(axes[0], "net_econ_12m_pct_tce", L("净经济影响 占 TCE (%)", "Net economic effect, % of TCE")),
                         (axes[1], "net_econ_pct_earn", L("净经济影响 占年化 Q3E 净利润 (%)", "Net economic effect, % of annualised Q3E earnings"))]:
        m = st.pivot(index="scenario", columns="ticker", values=col).loc[scs, BANKS]
        im = ax.imshow(m.values, cmap="RdYlGn", vmin=-m.abs().max().max() * 0.6, vmax=m.abs().max().max() * 0.6, aspect="auto")
        ax.set_xticks(range(len(BANKS)), BANKS)
        ax.set_yticks(range(len(scs)), [SC_NAME(L)[s] for s in scs])
        ax.grid(False)
        for i in range(len(scs)):
            for j in range(len(BANKS)):
                v = m.values[i, j]
                ax.text(j, i, "n/a" if np.isnan(v) else f"{v:.1f}", ha="center", va="center", fontsize=9)
        ax.set_title(ttl)
    footer(fig, L("n/a = 10-Q 未披露该情景的 NII 敏感度。负值 = 对经济账面价值/利润不利。含 HTM 减值,不含信用成本与需求变化。",
                  "n/a = NII sensitivity for this scenario is not disclosed. Negative = adverse to economic book value/earnings. Includes the HTM mark; excludes credit costs and demand effects."))
    fig.tight_layout()
    return save(fig, L, "f13_stress_heat")


def run(L):
    out = [fig_segments(L), fig_segment_changes(L), fig_eps(L), fig_pe(L), fig_market(L)]
    out += fig_afs_htm_book(L)
    out += [fig_proforma(L), fig_stress_bars(L), fig_stress_heat(L)]
    return out


if __name__ == "__main__":
    for code in ("zh", "en"):
        print(run(Lang(code)))
