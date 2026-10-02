"""Generate the bilingual front matter and Part II (charts + supplementary analysis) as Markdown.

Numbers in tables and key sentences are computed from output/data/*.csv and FRED so the text cannot drift from the charts.
Output: output/doc_src/{front,supp}_{zh,en}.md
"""

import os

import numpy as np
import pandas as pd

import chart_data as cd

OUT = cd.OUT
D = os.path.join(OUT, "data")
SRC = os.path.join(OUT, "doc_src")
os.makedirs(SRC, exist_ok=True)
BANKS = cd.BIG6
BN = {"JPM": "JPMorgan", "BAC": "Bank of America", "C": "Citigroup", "WFC": "Wells Fargo", "GS": "Goldman Sachs", "MS": "Morgan Stanley"}

LBL = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
SID = ["DGS1MO", "DGS3MO", "DGS6MO", "DGS1", "DGS2", "DGS3", "DGS5", "DGS7", "DGS10", "DGS20", "DGS30"]
Q3_DEAL_LEADS = {
    "SK hynix": "BofA / Citi / GS / JPM (global coordinators)", "Jersey Mike's": "MS / Jefferies / JPM (global coordinators); Barclays, Guggenheim",
    "Csquare": "MS, TD (reps); Wells, BofA, BMO, Scotia, JPM", "Accelevation": "MS, JPM, GS, Barclays, BofA",
    "ADARx": "JPM, MS, TD Cowen, UBS", "Braveheart Bio": "GS, Jefferies, TD Cowen, Stifel, Cantor", "Electra": "Jefferies, TD Cowen, Evercore, Cantor",
    "Latigo": "GS, Jefferies, Leerink, Guggenheim", "Lyntris": "Evercore, Citi, Guggenheim; BofA", "Attovia": "MS, Leerink, Citi, RBC",
    "Orion180": "RBC, UBS, Raymond James; GS", "Reformation": "JPM, MS; Citi, RBC", "Apnimed": "BofA, Evercore, Cantor, LifeSci",
    "Robinhood Ventures Fund II": "GS, Citi, JPM, UBS, Wells", "Standard Nuclear": "BofA, GS", "BlossomHill": "JPM, Leerink, Guggenheim",
    "American Savings Bank": "Piper Sandler", "River City Bank": "KBW",
}


def tbl(head, rows, align=None):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def U(v):
    return ("-" if v < 0 else "+") + f"${abs(v):.1f}B"


def f(x, n=1, plus=False):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    s = f"{x + 1e-9 * np.sign(x):,.{n}f}"
    return ("+" + s) if plus and x > 0 else s


def pct(x, n=1, plus=True):
    return f(x, n, plus) + "%"


def data():
    seg = pd.read_csv(os.path.join(D, "segment_panel.csv"))
    st = pd.read_csv(os.path.join(D, "stress_test.csv"))
    afs = pd.read_csv(os.path.join(D, "afs_htm_history.csv"))
    ipo = pd.read_csv(os.path.join(D, "ipo_deals.csv"))
    ipob = pd.read_csv(os.path.join(D, "ipo_fees_by_bank.csv")).set_index("deal")
    pipe = pd.read_csv(os.path.join(D, "ipo_pipeline.csv"))
    eps = pd.read_csv(os.path.join(D, "eps_history.csv"))
    return seg, st, afs, ipo, ipob, pipe, eps


def seg_compare(seg):
    rows = {}
    for t in BANKS:
        s = seg[seg.ticker == t].set_index("q")
        q2 = s.loc["2026Q2"].copy()
        q2["other"] -= q2.oneoff
        q2["total"] -= q2.oneoff
        rows[t] = dict(y=s.loc["2025Q3"], q=q2, e=s.loc["2026Q3E"])
    return rows


def pe_table(eps):
    import charts_banks as cb
    out = {}
    for t in BANKS:
        px = cd.price_close(t)
        pnow = px.iloc[-1]
        te = cb.ttm_eps(t, pd.Timestamp("2026-10-01"))
        m = eps[(eps.ticker == t) & (eps.kind == "model")].iloc[0]
        q325 = eps[(eps.ticker == t) & (eps.q == "2025Q3") & (eps.kind == "actual")].eps.iloc[0]
        roll = te - q325 + m.eps
        te_prev = cb.ttm_eps(t, pd.Timestamp("2025-10-01"))
        px_prev = px.loc[:"2025-10-01"].iloc[-1]
        out[t] = dict(price=pnow, ttm=te, pe=pnow / te, pe_roll=pnow / roll, pe_prev=px_prev / te_prev if te_prev else np.nan, roll=roll)
    return out


def build(lang):
    zh = lang == "zh"
    T = (lambda a, b: a) if zh else (lambda a, b: b)
    seg, st, afs, ipo, ipob, pipe, eps = data()
    sc = seg_compare(seg)
    pe = pe_table(eps)
    chdir = f"../charts/{lang}"
    fig_no = [0]

    def fig(name, cap):
        fig_no[0] += 1
        return f"![{T('图', 'Figure ')}{fig_no[0]}{T(':', '. ')}{cap}]({chdir}/{name}.png)"

    # ---------- numbers ----------
    cv = {s: (cd.fred_at(s, "2026-06-30"), cd.fred_at(s, "2026-09-30"), cd.fred_at(s, "2025-09-30")) for s in SID + ["MORTGAGE30US", "DFF"]}
    chg = {s: (v[1] - v[0]) * 100 for s, v in cv.items()}
    s210 = [(cv["DGS10"][i] - cv["DGS2"][i]) * 100 for i in range(3)]
    dff = cd.fred("DFF")
    ff_avg = (dff.loc["2026-07-01":"2026-09-30"].mean() - dff.loc["2026-04-01":"2026-06-30"].mean()) * 100
    ff_exit = chg["DFF"]
    bal = 100e3
    a5, a10 = chg["DGS5"] / 1e4 * bal, chg["DGS10"] / 1e4 * bal
    d_avg, d_exit = 0.4 * ff_avg / 1e4 * bal, 0.4 * ff_exit / 1e4 * bal
    d_exit60 = 0.6 * ff_exit / 1e4 * bal

    S = st.set_index(["ticker", "scenario"])
    afs_q = afs.set_index(["ticker", "q"])
    ib_e = {t: sc[t]["e"].ib for t in BANKS}
    ipo_by_bank = ipob[BANKS + ["OTH"]].sum()
    ipo_total = ipo.fee_usd_m.sum()
    skh = ipo[ipo.deal == "SK hynix"].fee_usd_m.iloc[0]
    proceeds_tot = ipo.proceeds_usd_m.sum() / 1e3
    proceeds_ex = proceeds_tot - 26.507
    six = ipo_by_bank[BANKS].sum()

    # ---------- front ----------
    fr = []
    fr.append("# " + T("美股金融板块 2026 年 Q3 财报季前瞻(图文版)", "US Financials Ahead of the Q3 2026 Earnings Season (Illustrated Edition)"))
    fr.append(T("数据截止 2026-10-01 收盘;2026-10-02 撰写。本文档是研究报告正文加图表、压力测试、AFS/HTM 影响与 IPO 梳理的合订本。",
                "Data as of the 2026-10-01 close; written 2026-10-02. This document combines the research report with charts, a rate stress test, the AFS/HTM impact analysis and an IPO review."))
    fr.append("## " + T("阅读指南", "Reading guide"))
    fr.append(tbl([T("部分", "Part"), T("内容", "Content"), T("适合谁读", "Who it is for")], [
        [T("第一部分(第 0-10 节)", "Part I (Sections 0-10)"), T("研究报告正文:结论、宏观、方法、分部门、逐家 EPS 预测、分层名单、风险、历史类比、投资建议、局限",
                                                         "Research report: conclusions, macro, method, segments, EPS forecasts, tiers, risk, analogues, views, limits"),
         T("想要完整论证的读者", "Readers who want the full argument")],
        [T("第二部分(第 11-17 节)", "Part II (Sections 11-17)"), T("图表与补充分析:期限结构、存款成本与贷款收入、分部门收入、EPS/P/E、AFS/HTM、压力测试、IPO",
                                                          "Charts and supplementary analysis: term structure, deposit cost vs. loan income, segment revenue, EPS/P/E, AFS/HTM, stress test, IPO"),
         T("想要直观理解的读者", "Readers who want an intuitive view")],
    ]))
    fr.append(T("**建议阅读顺序**:先读第 0 节(结论),再翻第二部分的图 1-4(利率),然后图 5-9(收入、EPS、估值),最后图 10-15(AFS/HTM、压力测试、IPO)。需要论证细节时回到第一部分。",
                "**Suggested order**: read Section 0 (conclusions), then Figures 1-4 (rates), Figures 5-9 (revenue, EPS, valuation), and Figures 10-15 (AFS/HTM, stress test, IPO). Go back to Part I for the detailed argument."))
    fr.append("## " + T("口径与期间可比性约定", "Conventions and period comparability"))
    for z, e in [
        ("**期间**:`24Q3` 到 `26Q2` 为日历季度的实际值;`26Q3E` 是本报告的预测(紫色/带 E)。**同比**对比 Q3'25,**环比**对比 Q2'26。",
         "**Periods**: `24Q3` to `26Q2` are actual calendar quarters; `26Q3E` is this report's forecast (purple / marked E). **YoY** compares with Q3'25, **QoQ** with Q2'26."),
        ("**一次性项目**:JPM 的 Q2'26 含约 $5.4B 的 Visa 一次性收益,在环比比较和 EPS 趋势中单独标出或剔除(图 5 用斜线标出,图 6、图 7 已剔除)。",
         "**One-offs**: JPM's Q2'26 contains a one-off Visa gain of about $5.4B, shown separately or removed in QoQ comparisons and EPS trends (hatched in Figure 5, removed in Figures 6 and 7)."),
        ("**第四季度**:XBRL 不单独披露 Q4,用「全年 − 前三季」推出;因此 EPS 为近似值。",
         "**Q4 history**: XBRL does not report Q4 separately, so it is derived as FY minus 9M; EPS is therefore approximate."),
        ("**收入口径**:总收入 = 净利息收入 + 非息收入(GAAP,不含 FTE 调整)。交易线是损益表里的交易类收入,不含做市相关的净利息收入,因此低于管理层口径的 Markets 收入(例如 JPM Q2 的 Markets $12.1B 对应图中交易线 $9.0B)。",
         "**Revenue basis**: total revenue = net interest income + non-interest income (GAAP, no FTE adjustment). The trading line is the income-statement trading revenue and excludes market-making NII, so it is lower than management's Markets revenue (e.g. JPM's Q2 Markets of $12.1B vs. $9.0B in the chart)."),
        ("**颜色**:蓝=净利息收入,橙=投行费用,绿=交易/做市,灰=其他非息,紫=预测;红=负债端或不利,深蓝=资产端。每家银行在所有图里使用同一种颜色。",
         "**Colours**: blue = NII, orange = IB fees, green = trading, grey = other non-interest, purple = forecast; red = liability side or adverse, dark blue = asset side. Each bank keeps the same colour in every chart."),
        ("**单位**:除注明外为十亿美元($bn);bp = 基点(0.01%);`$M` = 百万美元。",
         "**Units**: $bn unless noted; bp = basis point (0.01%); `$M` = millions of dollars."),
        ("**估算与披露的区分**:IPO 费用中,招股书披露的标「披露」,其余标「估算」;各行分成按角色加权,是估算,不是银行披露。",
         "**Estimated vs. disclosed**: in the IPO tables, fees from prospectuses are marked 'disclosed', the rest 'est.'; per-bank splits are role-weighted estimates, not bank disclosures."),
    ]:
        fr.append("- " + T(z, e))
    fr.append("## " + T("关键发现速览", "Key findings at a glance"))
    p100 = {t: S.loc[(t, "p100")] for t in BANKS}
    kf = [
        (f"**曲线**:Q3 国债曲线整体上移 {f(chg['DGS1MO'],0)}-{f(chg['DGS5'],0)}bp,5Y 涨幅最大(+{f(chg['DGS5'],0)}bp),10Y 到 {cv['DGS10'][1]:.2f}%,2s10s 从 {s210[0]:.0f}bp 升到 {s210[1]:.0f}bp。政策利率季均只 +{ff_avg:.0f}bp,期末 +{ff_exit:.0f}bp。(图 1-3)",
         f"**Curve**: the Treasury curve shifted up {f(chg['DGS1MO'],0)}-{f(chg['DGS5'],0)}bp in Q3, with the 5Y up the most (+{f(chg['DGS5'],0)}bp); the 10Y reached {cv['DGS10'][1]:.2f}% and 2s10s widened from {s210[0]:.0f}bp to {s210[1]:.0f}bp. The policy rate averaged only +{ff_avg:.0f}bp, +{ff_exit:.0f}bp at quarter-end. (Figures 1-3)"),
        (f"**重定价**:每 $1000 亿重定价的资产,按 5Y 利率变动年化多收约 ${a5/1e3:.2f}B;存款成本在 β=40% 下,按季均多付约 ${d_avg:.0f}M、按期末利率多付约 ${d_exit:.0f}M。收入端先到,存款成本后追。(图 4)",
         f"**Repricing**: per $100bn of assets that reprice, the 5Y move adds about ${a5/1e3:.2f}B a year of income; deposit costs at beta 40% add about ${d_avg:.0f}M (Q3 average) or ${d_exit:.0f}M (exit rate). Income arrives first; deposit cost catches up later. (Figure 4)"),
        ("**收入**:" + "、".join(f"{t} {pct(100*(sc[t]['e'].total/sc[t]['q'].total-1))}" for t in BANKS) + " 是 Q3E 总收入相对 Q2'26(JPM 已剔除 Visa)的变化;同比则全部为正(" + f"{pct(100*min(sc[t]['e'].total/sc[t]['y'].total-1 for t in BANKS))} 到 {pct(100*max(sc[t]['e'].total/sc[t]['y'].total-1 for t in BANKS))})。环比下降主要来自交易和 IB。(图 5-6)",
         "**Revenue**: Q3E total revenue vs. Q2'26 (JPM ex-Visa): " + ", ".join(f"{t} {pct(100*(sc[t]['e'].total/sc[t]['q'].total-1))}" for t in BANKS) + f"; YoY all are positive ({pct(100*min(sc[t]['e'].total/sc[t]['y'].total-1 for t in BANKS))} to {pct(100*max(sc[t]['e'].total/sc[t]['y'].total-1 for t in BANKS))}). The QoQ decline comes mainly from trading and IB. (Figures 5-6)"),
        (f"**AFS/HTM**:BAC 的 HTM 未实现损失 ${-(afs_q.loc[('BAC','2026Q2'),'htm_fv']-afs_q.loc[('BAC','2026Q2'),'htm_ac']):.1f}B,WFC ${-(afs_q.loc[('WFC','2026Q2'),'htm_fv']-afs_q.loc[('WFC','2026Q2'),'htm_ac']):.1f}B,JPM ${-(afs_q.loc[('JPM','2026Q2'),'htm_fv']-afs_q.loc[('JPM','2026Q2'),'htm_ac']):.1f}B;这些不进监管资本,但是经济账面价值的隐性损失。(图 10-12)",
         f"**AFS/HTM**: BAC's HTM unrealised loss is ${-(afs_q.loc[('BAC','2026Q2'),'htm_fv']-afs_q.loc[('BAC','2026Q2'),'htm_ac']):.1f}B, WFC's ${-(afs_q.loc[('WFC','2026Q2'),'htm_fv']-afs_q.loc[('WFC','2026Q2'),'htm_ac']):.1f}B, JPM's ${-(afs_q.loc[('JPM','2026Q2'),'htm_fv']-afs_q.loc[('JPM','2026Q2'),'htm_ac']):.1f}B; these do not enter regulatory capital but are a hidden loss of economic book value. (Figures 10-12)"),
        ("**压力测试**:再加息 100bp(平行),含 HTM 经济损失的净影响为 " + "、".join(f"{t} {U(p100[t].net_econ_12m)}(占 TCE {p100[t].net_econ_12m_pct_tce:.1f}%)" for t in BANKS) + "。BAC 最敏感,几乎全部来自 HTM。(图 13-14)",
         "**Stress test**: a further +100bp parallel hike, including the HTM economic loss, gives " + ", ".join(f"{t} {U(p100[t].net_econ_12m)} ({p100[t].net_econ_12m_pct_tce:.1f}% of TCE)" for t in BANKS) + ". BAC is the most sensitive, almost entirely through HTM. (Figures 13-14)"),
        (f"**IPO**:我们梳理的 Q3 共 {len(ipo)} 单、募资约 ${proceeds_tot:.1f}B,估算承销费合计约 ${ipo_total:.0f}M,其中 SK hynix 约 ${skh:.0f}M;对六大行合计约 ${six:.0f}M,占各行 Q3E 投行费用的 {min(ipo_by_bank[t]/(ib_e[t]*1e3)*100 for t in BANKS):.1f}%-{max(ipo_by_bank[t]/(ib_e[t]*1e3)*100 for t in BANKS):.1f}%。Q4 的最大变量是 Anthropic(媒体报道,尚无公开 S-1)。(图 15)",
         f"**IPO**: we reviewed {len(ipo)} Q3 deals raising about ${proceeds_tot:.1f}B, with estimated underwriting fees of about ${ipo_total:.0f}M in total (SK hynix about ${skh:.0f}M); the six large banks together earn about ${six:.0f}M, equal to {min(ipo_by_bank[t]/(ib_e[t]*1e3)*100 for t in BANKS):.1f}%-{max(ipo_by_bank[t]/(ib_e[t]*1e3)*100 for t in BANKS):.1f}% of each bank's Q3E IB fees. The big Q4 variable is Anthropic (media reports; no public S-1). (Figure 15)"),
    ]
    for z, e in kf:
        fr.append("- " + T(z, e))
    fr.append("## " + T("术语表", "Glossary"))
    gl = [
        ("NII / NIM", "净利息收入 / 净息差", "Net interest income / net interest margin"),
        ("AFS / HTM", "可供出售证券(按公允价值入 AOCI)/ 持有至到期证券(按摊余成本,浮亏不入资本)", "Available-for-sale securities (fair value through AOCI) / held-to-maturity securities (amortised cost; unrealised losses do not enter capital)"),
        ("AOCI", "累计其他综合收益,AFS 浮盈浮亏的累计", "Accumulated other comprehensive income; cumulative AFS gains and losses"),
        ("TCE / TBV", "有形普通股权益 / 有形账面价值 = 权益 − 商誉 − 无形资产 − 优先股", "Tangible common equity / tangible book value = equity - goodwill - intangibles - preferred"),
        ("IB / S&T", "投行业务 / 销售与交易", "Investment banking / sales and trading"),
        ("2s10s", "10 年期减 2 年期国债收益率", "10-year minus 2-year Treasury yield"),
        ("熊陡 / 熊平" if zh else "Bear steepener / flattener", "利率上行且曲线变陡 / 变平", "Rates rise while the curve steepens / flattens"),
        ("β(存款 beta)" if zh else "Deposit beta", "存款利率变动 ÷ 政策利率变动", "Change in deposit rates ÷ change in the policy rate"),
        ("久期" if zh else "Duration", "利率每变动 1 个百分点,价格近似反向变动的百分比", "Approximate % price change for a 1-point move in rates"),
        ("P/E (TTM)", "股价 ÷ 过去 12 个月 EPS", "Price ÷ trailing-12-month EPS"),
    ]
    fr.append(tbl([T("术语", "Term"), T("含义", "Meaning")], [[a, T(b, c)] for a, b, c in gl]))
    fr.append("## " + T("图表索引", "Chart index"))
    idx = [
        ("1-3", "f01-f03", "国债收益率曲线形状与 Q3 各期限变动;各季度末的政策利率与基准利率;Q3 日度路径与 2s10s", "Treasury curve shape and Q3 change by tenor; policy and benchmark rates at quarter-ends; Q3 daily path and 2s10s", "11"),
        ("4", "f04", "不同期限利率变动对存款成本与贷款收入的传导", "Transmission of rate moves at different tenors to deposit cost and loan income", "12"),
        ("5-6", "f05-f06", "六大行近 9 个季度分部门收入(含 Q3E);Q3E 的环比与同比分部门变化", "Segment revenue of the six banks over 9 quarters (incl. Q3E); Q3E segment changes QoQ and YoY", "13"),
        ("7-9", "f07-f09", "EPS 历史与 Q3E;滚动 12 个月 P/E;股价、板块、波动率、10Y、油价与按揭利率", "EPS history and Q3E; trailing-12M P/E; prices, sectors, volatility, 10Y, oil and mortgage rate", "14"),
        ("10-12", "f10, f11", "HTM、AFS 的摊余成本与公允价值;Q3 利率上行对账面价值的冲击", "HTM and AFS amortised cost vs. fair value; Q3 rate-rise hit to book value", "15"),
        ("13-14", "f12, f13", "加息压力测试:构成柱状图与热力图", "Rate stress test: component bars and heat map", "16"),
        ("15", "f14", "IPO 承销费估算与 Q4 Anthropic 情景", "Estimated IPO underwriting fees and the Q4 Anthropic scenario", "17"),
    ]
    fr.append(tbl([T("图", "Figure"), T("文件", "File"), T("内容", "Shows"), T("章节", "Section")], [[a, b, T(c, d), e] for a, b, c, d, e in idx]))
    fr.append("# " + T("第一部分 研究报告正文", "Part I. Research report"))

    # ---------- supplement ----------
    s = []
    s.append("# " + T("第二部分 图表与补充分析", "Part II. Charts and supplementary analysis"))
    s.append(T("本部分的图表、表格都由 `research/scripts/` 下的脚本从 SEC XBRL、10-Q 表格、FRED 与价格数据生成,可复现。第 11-17 节与第一部分的第 1-9 节对应。",
               "All charts and tables in this part are generated by the scripts in `research/scripts/` from SEC XBRL, 10-Q tables, FRED and price data, and are reproducible. Sections 11-17 correspond to Sections 1-9 of Part I."))

    # 11
    s.append("## " + T("11. 利率期限结构:这个季度发生了什么", "11. The term structure: what happened this quarter"))
    s.append(fig("f01_yield_curve", T("国债收益率曲线:各季度末的形状(左),Q3 各期限变动(右)", "Treasury curve at each quarter-end (left) and Q3 change by tenor (right)")))
    rows = [[LBL[i], f(cv[SID[i]][2], 2), f(cv[SID[i]][0], 2), f(cv[SID[i]][1], 2), f(chg[SID[i]], 0, True), f((cv[SID[i]][1] - cv[SID[i]][2]) * 100, 0, True)] for i in range(len(SID))]
    rows.append([T("30Y 按揭利率", "30Y mortgage"), f(cv["MORTGAGE30US"][2], 2), f(cv["MORTGAGE30US"][0], 2), f(cv["MORTGAGE30US"][1], 2), f(chg["MORTGAGE30US"], 0, True), f((cv["MORTGAGE30US"][1] - cv["MORTGAGE30US"][2]) * 100, 0, True)])
    rows.append([T("联邦基金有效利率", "Fed funds (effective)"), f(cv["DFF"][2], 2), f(cv["DFF"][0], 2), f(cv["DFF"][1], 2), f(chg["DFF"], 0, True), f((cv["DFF"][1] - cv["DFF"][2]) * 100, 0, True)])
    rows.append(["2s10s (bp)", f(s210[2], 0), f(s210[0], 0), f(s210[1], 0), f(s210[1] - s210[0], 0, True), f(s210[1] - s210[2], 0, True)])
    s.append(tbl([T("期限", "Tenor"), "2025-09-30 (%)", "2026-06-30 (%)", "2026-09-30 (%)", T("Q3 变动 (bp)", "Q3 chg (bp)"), T("同比变动 (bp)", "YoY chg (bp)")], rows))
    s.append(T("*数据:FRED。2s10s 与变动单位为 bp,其余为 %。*", "*Source: FRED. 2s10s and changes are in bp; the rest in %.*"))
    s.append("### " + T("读图要点", "How to read it"))
    s.append("- " + T(f"**形状**:Q3 的上行不是平行移动。短端(1M-6M)只涨约 {min(chg['DGS1MO'],chg['DGS3MO'],chg['DGS6MO']):.0f}-{max(chg['DGS1MO'],chg['DGS3MO'],chg['DGS6MO']):.0f}bp,1Y 涨 {chg['DGS1']:.0f}bp,2Y 涨 {chg['DGS2']:.0f}bp,3Y-7Y 涨 {chg['DGS3']:.0f}-{chg['DGS5']:.0f}bp(5Y 最大),10Y 涨 {chg['DGS10']:.0f}bp,20Y-30Y 涨约 {chg['DGS30']:.0f}-{chg['DGS20']:.0f}bp。涨幅最大的是中段(5Y 附近),所以 3M 到 5Y 之间的斜率明显变陡。",
                f"**Shape**: the Q3 rise was not parallel. The short end (1M-6M) rose only about {min(chg['DGS1MO'],chg['DGS3MO'],chg['DGS6MO']):.0f}-{max(chg['DGS1MO'],chg['DGS3MO'],chg['DGS6MO']):.0f}bp, 1Y rose {chg['DGS1']:.0f}bp, 2Y {chg['DGS2']:.0f}bp, 3Y-7Y {chg['DGS3']:.0f}-{chg['DGS5']:.0f}bp (the 5Y was the largest), 10Y {chg['DGS10']:.0f}bp, and 20Y-30Y about {chg['DGS30']:.0f}-{chg['DGS20']:.0f}bp. The belly (around 5Y) moved the most, so the slope between 3M and 5Y steepened sharply."))
    s.append("- " + T(f"**2s10s**:季末为 {s210[1]:.0f}bp,季初为 {s210[0]:.0f}bp,只多 {s210[1]-s210[0]:.0f}bp,但路径不平:9/22 一度收窄到约 22bp(图 3 右)。",
                f"**2s10s**: {s210[1]:.0f}bp at quarter-end vs. {s210[0]:.0f}bp at the start, only {s210[1]-s210[0]:.0f}bp wider, but the path was uneven: it narrowed to about 22bp on 9/22 (Figure 3, right)."))
    s.append("- " + T(f"**同比对比(期间可比性)**:和一年前(2025-09-30)相比,2Y 高 {(cv['DGS2'][1]-cv['DGS2'][2])*100:.0f}bp,10Y 高 {(cv['DGS10'][1]-cv['DGS10'][2])*100:.0f}bp,而联邦基金有效利率反而低 {-(cv['DFF'][1]-cv['DFF'][2])*100:.0f}bp({cv['DFF'][2]:.2f}% 到 {cv['DFF'][1]:.2f}%)。也就是说,中长端的上行主要不是政策利率推动的。2s10s 同比反而更窄({s210[2]:.0f}bp 到 {s210[1]:.0f}bp)。",
                f"**Year-on-year (comparability)**: versus a year earlier (2025-09-30), the 2Y is {(cv['DGS2'][1]-cv['DGS2'][2])*100:.0f}bp higher and the 10Y {(cv['DGS10'][1]-cv['DGS10'][2])*100:.0f}bp higher, while the effective fed funds rate is actually {-(cv['DFF'][1]-cv['DFF'][2])*100:.0f}bp lower ({cv['DFF'][2]:.2f}% to {cv['DFF'][1]:.2f}%). The rise in the intermediate and long end was mainly not driven by the policy rate. 2s10s is narrower YoY ({s210[2]:.0f}bp to {s210[1]:.0f}bp)."))
    s.append("- " + T(f"**季均 vs 期末**:联邦基金有效利率 Q3 季均比 Q2 只高 {ff_avg:.0f}bp,因为 9/16 才加息;期末比 6/30 高 {ff_exit:.0f}bp。负债成本的上行主要在 Q4 兑现。",
                f"**Average vs. exit**: the effective fed funds rate averaged only {ff_avg:.0f}bp above Q2 in Q3, since the hike came on 9/16; it ended {ff_exit:.0f}bp above 6/30. Most of the rise in liability costs lands in Q4."))
    s.append(fig("f02_rate_bars", T("各季度末的政策利率与基准利率(柱状图)", "Policy and benchmark rates at each quarter-end (bar chart)")))
    s.append(fig("f03_q3_path", T("Q3 日度走势(左)与 2s10s 利差(右)", "Q3 daily path (left) and 2s10s spread (right)")))
    s.append(T("*图 2 的柱状图把 9 个季度并排放在一起:从 2025Q3 到 2026Q2 政策利率从 4.09% 降到 3.63%,而 10Y 从 4.16% 升到 4.44%,2026Q3 长端再大幅抬升;这就是 Q3 的「长端先动、政策利率后动」的背景。*",
               "*Figure 2 puts nine quarters side by side: from 2025Q3 to 2026Q2 the effective policy rate fell from 4.09% to 3.63% while the 10Y rose from 4.16% to 4.44%, and in 2026Q3 the long end rose sharply again. That is the background for Q3's 'long end first, policy rate later' pattern.*"))

    # 12
    s.append("## " + T("12. 期限结构变化如何传导到存款成本与贷款收入", "12. How the term-structure move feeds deposit cost and loan income"))
    s.append(fig("f04_transmission", T("各参考利率的变动(左)与每 $1000 亿重定价余额的年化影响(右)", "Change in reference rates (left) and annualised effect per $100bn that reprices (right)")))
    s.append(tbl([T("银行产品/资产", "Bank product / asset"), T("对应参考利率", "Reference rate"), T("Q3 变动 (bp)", "Q3 change (bp)"), T("方向", "Side")], [
        [T("活期/储蓄存款(季均)", "Core deposits (avg)"), T("联邦基金有效利率(季均)", "Fed funds (Q3 average)"), f(ff_avg, 0, True), T("负债", "Liability")],
        [T("活期/储蓄存款(期末)", "Core deposits (exit)"), T("联邦基金有效利率(期末)", "Fed funds (exit)"), f(ff_exit, 0, True), T("负债", "Liability")],
        [T("同业/大额存单", "Wholesale / CD"), "3M", f(chg["DGS3MO"], 0, True), T("负债", "Liability")],
        [T("1 年期定存", "1Y CD"), "1Y", f(chg["DGS1"], 0, True), T("负债", "Liability")],
        [T("短久期证券", "Short securities"), "2Y", f(chg["DGS2"], 0, True), T("资产", "Asset")],
        [T("商业贷款/汽车贷", "C&I / auto loans"), "5Y", f(chg["DGS5"], 0, True), T("资产", "Asset")],
        [T("MBS/商业地产", "MBS / CRE"), "10Y", f(chg["DGS10"], 0, True), T("资产", "Asset")],
        [T("住房抵押贷款", "Residential mortgages"), T("30Y 按揭利率", "30Y mortgage rate"), f(chg["MORTGAGE30US"], 0, True), T("资产", "Asset")],
    ]))
    s.append("### " + T("示意性测算(每 $1000 亿重定价余额)", "Illustrative calculation (per $100bn that reprices)"))
    s.append(tbl([T("项目", "Item"), T("年化金额 ($M)", "Annualised ($M)")], [
        [T("新增或再投资 5Y 资产的收入增量", "Income gain on new / reinvested 5Y assets"), f(a5, 0, True)],
        [T("新增或再投资 10Y 资产的收入增量", "Income gain on new / reinvested 10Y assets"), f(a10, 0, True)],
        [T("存款成本增量(季均口径,β=40%)", "Deposit cost increase (Q3 average, beta 40%)"), f(-d_avg, 0, True)],
        [T("存款成本增量(期末口径,β=40%)", "Deposit cost increase (exit rate, beta 40%)"), f(-d_exit, 0, True)],
        [T("存款成本增量(期末口径,β=60%)", "Deposit cost increase (exit rate, beta 60%)"), f(-d_exit60, 0, True)],
    ]))
    s.append("- " + T(f"**含义**:每 $1000 亿资产在新利率上重定价,年化多收约 ${a5:.0f}M(5Y 口径),而 Q3 季均的存款成本只多付约 ${d_avg:.0f}M。这就是第 0 节说的「资产重定价先于负债」的 NII 顺风。",
                f"**Meaning**: for every $100bn of assets repricing at the new rates, annual income rises about ${a5:.0f}M (5Y basis), while the Q3-average deposit cost rises only about ${d_avg:.0f}M. This is the 'assets reprice before liabilities' NII tailwind described in Section 0."))
    s.append("- " + T(f"**但顺风会收窄**:按期末利率、β=40% 算,存款成本多付 ${d_exit:.0f}M;β 升到 60% 则是 ${d_exit60:.0f}M。Q4 起存款成本才完整反映 9/16 的加息,所以顺风是逐季衰减的。",
                f"**The tailwind narrows**: at the exit rate and beta 40%, deposit cost rises ${d_exit:.0f}M; at beta 60% it is ${d_exit60:.0f}M. Deposit costs reflect the 9/16 hike fully only from Q4, so the tailwind fades quarter by quarter."))
    s.append("- " + T("**只有一部分资产会重定价**:实际 NII 只受当期到期和新增的那部分资产影响。因此图是上限的示意,不是 NII 预测。NII 的预测见第 3.1 节与第 4 节的 bridge。",
                "**Only part of the book reprices**: actual NII is affected only by assets that mature or are newly originated in the period. The chart is an upper-bound illustration, not an NII forecast. For NII forecasts see Sections 3.1 and 4."))
    s.append("- " + T("**假设**:100% 的 $1000 亿余额按「Q3 末利率 − Q2 末利率」重定价;存款 β=40% 是假设值,不是披露值。",
                "**Assumptions**: 100% of the $100bn reprices at the Q3-end minus Q2-end rate difference; deposit beta of 40% is an assumption, not a disclosure."))

    # 13
    s.append("## " + T("13. 六大行分部门收入:近两年走势与 Q3 预测", "13. Segment revenue of the six large banks: two-year trend and Q3 forecast"))
    s.append(fig("f05_segments", T("分部门收入(堆叠柱,$bn):24Q3-26Q2 实际与 26Q3E", "Revenue by segment (stacked, $bn): 24Q3-26Q2 actual and 26Q3E")))
    rows = []
    for t in BANKS:
        r = sc[t]
        rows.append([t, f(r["y"].total), f(r["q"].total), f(r["e"].total), pct(100 * (r["e"].total / r["q"].total - 1)), pct(100 * (r["e"].total / r["y"].total - 1))])
    s.append(tbl([T("银行", "Bank"), "Q3'25", T("Q2'26(JPM 已剔除 Visa)", "Q2'26 (JPM ex-Visa)"), "Q3'26E", T("环比", "QoQ"), T("同比", "YoY")], rows))
    s.append(T("*总收入,$bn,GAAP 口径(NII + 非息收入)。*", "*Total revenue, $bn, GAAP basis (NII + non-interest income).*"))
    rows = []
    for t in BANKS:
        r = sc[t]
        rows.append([t] + [f(r["e"][k], 2) for k in ("nii", "ib", "trading", "other", "total")])
    s.append("### " + T("Q3'26E 分部门收入 ($bn)", "Q3'26E revenue by segment ($bn)"))
    s.append(tbl([T("银行", "Bank"), T("净利息收入", "NII"), T("投行费用", "IB fees"), T("交易/做市", "Trading"), T("其他非息", "Other"), T("合计", "Total")], rows))
    s.append(fig("f06_segment_changes", T("Q3E 相对 Q2'26(上)与相对 Q3'25(下)的分部门变化 ($bn)", "Q3E change vs. Q2'26 (top) and vs. Q3'25 (bottom) by segment ($bn)")))
    rows = []
    for t in BANKS:
        r = sc[t]
        rows.append([t] + [f(r["e"][k] - r["q"][k], 2, True) for k in ("nii", "ib", "trading", "other", "total")])
    s.append("### " + T("Q3'26E 相对 Q2'26 的环比变化 ($bn)", "Q3'26E change vs. Q2'26 ($bn)"))
    s.append(tbl([T("银行", "Bank"), T("净利息收入", "NII"), T("投行费用", "IB fees"), T("交易/做市", "Trading"), T("其他非息", "Other"), T("合计", "Total")], rows))
    rows = []
    for t in BANKS:
        r = sc[t]
        rows.append([t] + [f(r["e"][k] - r["y"][k], 2, True) for k in ("nii", "ib", "trading", "other", "total")])
    s.append("### " + T("Q3'26E 相对 Q3'25 的同比变化 ($bn)", "Q3'26E change vs. Q3'25 ($bn)"))
    s.append(tbl([T("银行", "Bank"), T("净利息收入", "NII"), T("投行费用", "IB fees"), T("交易/做市", "Trading"), T("其他非息", "Other"), T("合计", "Total")], rows))
    bq = sc["BAC"]
    s.append("### " + T("读图要点", "How to read it"))
    s.append("- " + T("**环比:资本市场回落,NII 仍在涨。**六家的交易线都是下降或持平,投行线多数下降;NII 在 JPM、BAC、WFC 上升,C、GS、MS 的 NII 在我们的桥里没有新增项,按持平处理。",
                "**QoQ: capital markets fall, NII still rises.** The trading line falls or is flat at all six, and the IB line falls at most of them; NII rises at JPM, BAC and WFC, while for C, GS and MS our bridge has no NII item so NII is held flat."))
    s.append("- " + T(f"**BAC 的交易线** 环比 {bq['e'].trading-bq['q'].trading:+.2f}B(Q2 {bq['q'].trading:.2f}B 到 Q3E {bq['e'].trading:.2f}B),是六家里最大的单项收缩之一,这也是第 4.1 节里 BAC EPS 低于共识的核心原因。",
                f"**BAC's trading line** falls {bq['e'].trading-bq['q'].trading:+.2f}B QoQ (Q2 {bq['q'].trading:.2f}B to Q3E {bq['e'].trading:.2f}B), among the largest single contractions of the six, and the core reason BAC's EPS falls short of consensus in Section 4.1."))
    gs = sc["GS"]
    s.append("- " + T(f"**GS 的降幅最大**(总收入环比 {pct(100*(gs['e'].total/gs['q'].total-1))}),主要来自「其他非息」(投资线,{gs['e'].other-gs['q'].other:+.2f}B)和交易({gs['e'].trading-gs['q'].trading:+.2f}B)。同比仍是 {pct(100*(gs['e'].total/gs['y'].total-1))},因为 Q3'25 基数较低。",
                f"**GS has the largest decline** (total revenue {pct(100*(gs['e'].total/gs['q'].total-1))} QoQ), mainly from 'other non-interest' (the investing lines, {gs['e'].other-gs['q'].other:+.2f}B) and trading ({gs['e'].trading-gs['q'].trading:+.2f}B). It is still {pct(100*(gs['e'].total/gs['y'].total-1))} YoY because the Q3'25 base was low."))
    s.append("- " + T("**期间可比性**:JPM 的 Q2'26 里 Visa 一次性收益约 $5.4B 在图 5 中用斜线标出,表格和图 6 的环比已剔除;否则 JPM 的环比会被夸大成约 −10%。",
                "**Comparability**: JPM's roughly $5.4B Visa one-off in Q2'26 is hatched in Figure 5 and removed in the QoQ tables and Figure 6; otherwise JPM's QoQ would be overstated at about -10%."))
    s.append("- " + T("**局限**:C 的 NII 和 IB、交易线的 Q4 来自 XBRL 回补而非 10-K 表格;Q3E 是我们的桥(第 4 节),WFC 的 IB 和交易线没有指引,按持平处理。",
                "**Limits**: for C the Q4 NII, IB and trading lines come from XBRL fill-ins rather than the 10-K table; Q3E comes from our bridge (Section 4), and for WFC the IB and trading lines have no guidance and are held flat."))

    # 14
    s.append("## " + T("14. EPS、P/E 与市场指标", "14. EPS, P/E and market indicators"))
    s.append(fig("f07_eps", T("六大行 EPS:历史、Q3E(紫色菱形为模型均值,误差线为 P10-P90)与共识", "EPS of the six large banks: history, Q3E (purple diamond = model mean, bars = P10-P90) and consensus")))
    rows = []
    for t in BANKS:
        m = eps[(eps.ticker == t) & (eps.kind == "model")].iloc[0]
        a = eps[(eps.ticker == t) & (eps.q == "2026Q2") & (eps.kind == "actual")].iloc[0]
        y = eps[(eps.ticker == t) & (eps.q == "2025Q3") & (eps.kind == "actual")].iloc[0]
        q2e = a.eps_adj if not np.isnan(a.eps_adj) else a.eps
        rows.append([t, f(y.eps, 2), f(q2e, 2), f(m.cons, 2), f(m.eps, 2), f"{m.p10:.2f}-{m.p90:.2f}", pct(100 * (m.eps / m.cons - 1)), pct(100 * (m.eps / y.eps - 1))])
    s.append(tbl([T("银行", "Bank"), "Q3'25 EPS", T("Q2'26 EPS(JPM 为剔除 Visa)", "Q2'26 EPS (JPM ex-Visa)"), T("Q3E 共识", "Q3E consensus"), T("Q3E 模型", "Q3E model"), "P10-P90", T("对共识", "vs. cons."), T("同比", "YoY")], rows))
    s.append(fig("f08_pe", T("滚动 12 个月 P/E(左)与 10/1 收盘价的 P/E(右,灰=已披露 TTM,紫=滚动含 Q3E)", "Trailing-12M P/E (left) and P/E at the 1 Oct close (right; grey = reported TTM, purple = rolled incl. Q3E)")))
    rows = [[t, f(pe[t]["price"], 2), f(pe[t]["ttm"], 2), f(pe[t]["pe_prev"], 1) + "x", f(pe[t]["pe"], 1) + "x", f(pe[t]["roll"], 2), f(pe[t]["pe_roll"], 1) + "x"] for t in BANKS]
    s.append(tbl([T("银行", "Bank"), T("10/1 收盘价 ($)", "1 Oct close ($)"), T("TTM EPS ($)", "TTM EPS ($)"), T("一年前 P/E", "P/E a year ago"), T("现在 P/E", "P/E now"), T("滚动含 Q3E 的 EPS ($)", "EPS rolled incl. Q3E ($)"), T("P/E(含 Q3E)", "P/E (incl. Q3E)")], rows))
    s.append(T("*P/E = 未复权收盘价 ÷ TTM EPS(GAAP 稀释;JPM Q2'26 用剔除 Visa 的 $6.14;季报披露后 16 天起计入)。GS 的单季 EPS 波动大,P/E 随之大幅变化。*",
               "*P/E = unadjusted close ÷ TTM EPS (GAAP diluted; JPM Q2'26 uses $6.14 ex-Visa; a quarter counts 16 days after quarter-end). GS's quarterly EPS is volatile, so its P/E swings.*"))
    s.append(fig("f09_market", T("市场仪表盘:大行股价、板块对比、VIX 与 10Y、油价与按揭利率", "Market dashboard: large-bank prices, sector comparison, VIX and 10Y, oil and mortgage rate")))
    s.append("### " + T("读图要点", "How to read it"))
    hi = max(BANKS, key=lambda t: pe[t]["pe"])
    lo = min(BANKS, key=lambda t: pe[t]["pe"])
    s.append("- " + T(f"**估值**:按 TTM,{hi} 的 P/E 最高({pe[hi]['pe']:.1f}x),{lo} 最低({pe[lo]['pe']:.1f}x);滚动纳入 Q3E 后,所有银行的 P/E 都会变化,幅度取决于 Q3E 相对 Q3'25 的 EPS 变化。",
                f"**Valuation**: on TTM, {hi} has the highest P/E ({pe[hi]['pe']:.1f}x) and {lo} the lowest ({pe[lo]['pe']:.1f}x); once Q3E is rolled in, every P/E changes by an amount that depends on Q3E EPS vs. Q3'25."))
    s.append("- " + T("**EPS 与共识**:C、MS、JPM 的模型值高于共识,BAC、GS 低于共识,WFC 基本一致(见表与图 7 的标题)。Q2'26 是创纪录季度,所以 Q3E 对 Q2 环比普遍下降;同比大多仍是上升。",
                "**EPS vs. consensus**: the model is above consensus for C, MS and JPM, below for BAC and GS, and roughly in line for WFC (see the table and the Figure 7 titles). Q2'26 was a record quarter, so Q3E is down QoQ nearly everywhere, but mostly still up YoY."))
    s.append("- " + T("**市场**:图 9 显示 3 月的 VIX 冲高和股价回撤,之后大行修复;9 月起 10Y 与按揭利率同步上行,TLT 下跌,银行与区域银行 ETF 也在 9 月回撤(第 6.1 节)。SMH 的涨幅远高于银行,与第 8 节「最像 1999 年」的类比一致。",
                "**Market**: Figure 9 shows the March VIX spike and price drawdown, followed by a recovery in the large banks; from September the 10Y and mortgage rates rose together, TLT fell, and bank and regional-bank ETFs pulled back (Section 6.1). SMH has far outpaced banks, consistent with the 'most like 1999' analogue in Section 8."))

    # 15
    s.append("## " + T("15. AFS / HTM 账面价值的变化,以及对大行的影响", "15. AFS / HTM book values and what they mean for the large banks"))
    s.append(T("本节只分析六大行(JPM、BAC、C、WFC、GS、MS),区域银行见第 7 节的评分表。",
               "This section covers only the six large banks (JPM, BAC, C, WFC, GS, MS); regional banks are in the scorecard in Section 7."))
    s.append(fig("f10_htm_book", T("HTM 证券:摊余成本 vs 公允价值,与未实现损益(右轴)", "HTM securities: amortised cost vs. fair value, with unrealised gain/loss (right axis)")))
    s.append(fig("f10_afs_book", T("AFS 证券:摊余成本 vs 公允价值", "AFS securities: amortised cost vs. fair value")))
    rows = []
    for t in BANKS:
        def g(q, k):
            try:
                return afs_q.loc[(t, q), k]
            except KeyError:
                return np.nan
        ul = lambda q: g(q, "htm_fv") - g(q, "htm_ac")  # noqa: E731
        rows.append([t, f(g("2026Q2", "afs_fv"), 1), f(g("2026Q2", "htm_ac"), 1), f(g("2026Q2", "htm_fv"), 1), f(ul("2025Q2"), 1), f(ul("2025Q4"), 1), f(ul("2026Q2"), 1)])
    s.append(tbl([T("银行", "Bank"), T("AFS 公允价值 6/30/26", "AFS fair value 6/30/26"), T("HTM 摊余成本 6/30/26", "HTM amortised cost 6/30/26"), T("HTM 公允价值 6/30/26", "HTM fair value 6/30/26"),
                  T("HTM 未实现损益 6/30/25", "HTM unrealised G/L 6/30/25"), T("HTM 未实现损益 12/31/25", "HTM unrealised G/L 12/31/25"), T("HTM 未实现损益 6/30/26", "HTM unrealised G/L 6/30/26")], rows))
    s.append(T("*$bn,SEC XBRL;C 的 12/31/25 与 6/30/26 来自 10-Q 表格,6/30/25 缺失。GS 与 MS 的 HTM 规模小。*", "*$bn, SEC XBRL; C's 12/31/25 and 6/30/26 come from 10-Q tables and 6/30/25 is unavailable. GS and MS have small HTM books.*"))
    s.append("### " + T("Q3 的利率上行把账面价值推低了多少(pro forma)", "How much the Q3 rate rise lowers book value (pro forma)"))
    import charts_banks as cb
    p = cb.proforma()
    rows = []
    for t in BANKS:
        r = p.loc[t]
        rows.append([t, f(float(r.tce), 1), f(float(r.aoci), 2), pct(float(r.aoci_pct_tce), 1, False), f(float(r.htm), 2), pct(float(r.htm_pct_tce), 1, False), f(float(r.earn_q), 1), f(float(r.aoci_x_q3e) + float(r.htm_x_q3e), 2) + "x"])
    s.append(tbl([T("银行", "Bank"), "TCE ($bn)", T("AFS→AOCI ($bn)", "AFS→AOCI ($bn)"), T("占 TCE", "% of TCE"), T("HTM 减值,税后 ($bn)", "HTM mark, after tax ($bn)"), T("占 TCE", "% of TCE"),
                  T("Q3E 季度盈利 ($bn)", "Q3E quarterly earnings ($bn)"), T("合计 ÷ Q3E 盈利", "Total ÷ Q3E earnings")], rows))
    s.append(fig("f11_proforma", T("Q3 利率上行对账面价值的冲击:占 TCE(左)与相当于几个季度的盈利(右)", "Q3 rate-rise hit to book value: % of TCE (left) and in quarters of earnings (right)")))
    s.append("### " + T("读图要点", "How to read it"))
    bh = -(afs_q.loc[("BAC", "2026Q2"), "htm_fv"] - afs_q.loc[("BAC", "2026Q2"), "htm_ac"])
    tc = float(p.loc["BAC"].tce)
    s.append("- " + T(f"**BAC 最特别**:AFS 只有约 1 年久期、且有利率互换对冲,所以 AOCI 冲击很小({float(p.loc['BAC'].aoci_pct_tce):.1f}% TCE);但 HTM 有 ${afs_q.loc[('BAC','2026Q2'),'htm_ac']:.0f}B,未实现损失 ${bh:.1f}B(约占 TCE 的 {bh/tc*100:.0f}%),Q3 再增约 ${-float(p.loc['BAC'].htm_pre):.1f}B(税前)。它不进监管资本,但是「经济 TBV」的隐性损失。",
                f"**BAC is the special case**: its AFS has about a 1-year duration and is swap-hedged, so the AOCI hit is small ({float(p.loc['BAC'].aoci_pct_tce):.1f}% of TCE); but the HTM book is ${afs_q.loc[('BAC','2026Q2'),'htm_ac']:.0f}B with a ${bh:.1f}B unrealised loss (about {bh/tc*100:.0f}% of TCE), and Q3 adds about ${-float(p.loc['BAC'].htm_pre):.1f}B (pre-tax). It does not enter regulatory capital but is a hidden loss in economic TBV."))
    s.append("- " + T("**WFC**:AFS 加 HTM 两边都有风险,Q3 的合计冲击占 TCE 最高之一;它的 AFS 摊余成本在 XBRL 缺失,AFS 久期用兜底值,精度较低。",
                "**WFC**: both AFS and HTM carry risk and the Q3 total hit as a share of TCE is among the highest; its AFS amortised cost is missing in XBRL and a fallback duration is used, so precision is lower."))
    s.append("- " + T("**JPM**:HTM 浮亏 $18B 左右,AFS 浮亏仅 $2.6B(因为对冲);相对 TCE 和盈利规模,影响居中。",
                "**JPM**: an HTM unrealised loss of roughly $18B and an AFS loss of only $2.6B (because of hedging); relative to TCE and earnings the impact is mid-range."))
    s.append("- " + T("**GS 与 MS**:GS 的 HTM 摊余成本约等于公允价值(未实现损益接近 0),MS 浮亏 $7.5B;两者受 AOCI 冲击都小。GS 的 AFS 以短久期国库券为主。",
                "**GS and MS**: GS's HTM amortised cost is about equal to fair value (unrealised G/L near zero) and MS has a $7.5B loss; both have small AOCI hits. GS's AFS is mostly short-duration T-bills."))
    s.append("- " + T("**C**:AOCI 的口径用 10-Q 披露的 +100bp 敏感度(税后 −$3.0B)乘以 0.875 近似 Q3 的 87.5bp;HTM 的久期 4.5 年是假设值。",
                "**C**: AOCI uses the +100bp sensitivity disclosed in its 10-Q (-$3.0B after tax) scaled by 0.875 to approximate Q3's 87.5bp; the HTM duration of 4.5 years is an assumption."))
    s.append("- " + T("**方法**:AFS 冲击 = −D × Δy × 摊余成本 ×(1 − 24%),Δy = +87.5bp;HTM 减值 = −D × Δy × 摊余成本(Δy = 按揭利率 +54bp),表中按 24% 税率折算为税后。公式见第 2.2 节。",
                "**Method**: AFS hit = -D x Δy x amortised cost x (1 - 24%) with Δy = +87.5bp; HTM mark = -D x Δy x amortised cost (Δy = mortgage rate +54bp), converted to after-tax at 24% in the table. See Section 2.2 for the formula."))

    # 16
    s.append("## " + T("16. 利率压力测试:如果继续加息", "16. Rate stress test: if the Fed keeps hiking"))
    s.append(T("**设问**:在已经发生的 Q3 上行之外,如果收益率曲线再上移,六大行的一年内经济影响有多大?",
               "**Question**: on top of the Q3 rise that has already happened, how large is the first-year economic effect on the six large banks if the curve moves up again?"))
    s.append(tbl([T("情景", "Scenario"), T("短端冲击", "Short-end shock"), T("长端冲击", "Long-end shock"), T("含义", "Meaning")], [
        [T("+50bp 平行", "+50bp parallel"), "+50bp", "+50bp", T("再加息两次 25bp 且长端同步", "Two more 25bp hikes with the long end moving in step")],
        [T("+100bp 平行", "+100bp parallel"), "+100bp", "+100bp", T("基准压力情景", "Baseline stress")],
        [T("+200bp 平行", "+200bp parallel"), "+200bp", "+200bp", T("极端情景", "Severe scenario")],
        [T("熊陡:长端 +100bp", "Bear steepener: long end +100bp"), "0", "+100bp", T("期限溢价上行,政策利率不动", "Term premium rises, policy rate unchanged")],
        [T("熊平:短端 +100bp", "Bear flattener: short end +100bp"), "+100bp", "0", T("纯政策利率冲击,AFS/HTM 估值不变", "Pure policy-rate shock; AFS/HTM valuations unchanged")],
    ]))
    s.append("### " + T("方法", "Method"))
    s.append("- " + T("**NII**:取各行 10-Q 披露的 12 个月 NII 敏感度(+100bp、+200bp、长端 +100bp、短端 +100bp),税率 24%;+50bp = 0.5 × (+100bp)。",
                "**NII**: the 12-month NII sensitivities each bank discloses in its 10-Q (+100bp, +200bp, long end +100bp, short end +100bp), 24% tax; +50bp = 0.5 x (+100bp)."))
    s.append("- " + T("**AFS→AOCI**:久期模型 × 长端冲击(C 为 10-Q 披露的 AOCI 初始冲击),税后;立即发生。",
                "**AFS→AOCI**: duration model x long-end shock (for C, the initial AOCI impact disclosed in its 10-Q), after tax; occurs immediately."))
    s.append("- " + T("**HTM 减值**:久期 × 长端冲击 × 摊余成本,按 24% 折算为税后;不进监管资本,也不进利润表,只是经济价值的损失。",
                "**HTM mark**: duration x long-end shock x amortised cost, converted to after-tax at 24%; it does not enter regulatory capital or the income statement, only economic value."))
    s.append("- " + T("**净经济影响** = 12 个月 NII(税后)+ AOCI + HTM 减值(税后)。**净资本影响** = NII + AOCI(不含 HTM)。两者的占比分母是 6/30 的 TCE 与「4 × Q3E EPS × 股数」的年化盈利。",
                "**Net economic effect** = 12M NII (after tax) + AOCI + HTM mark (after tax). **Net capital effect** = NII + AOCI (no HTM). Ratios use 6/30 TCE and annualised earnings of '4 x Q3E EPS x shares'."))
    s.append(fig("f12_stress_bars", T("压力测试(+100bp、+200bp、熊陡):NII、AOCI、HTM 与净经济影响 ($bn)", "Stress test (+100bp, +200bp, bear steepener): NII, AOCI, HTM and net economic effect ($bn)")))
    names = {"p50": T("+50bp 平行", "+50bp parallel"), "p100": T("+100bp 平行", "+100bp parallel"), "p200": T("+200bp 平行", "+200bp parallel"), "steep": T("熊陡 长端+100", "Steepener long +100"), "flat": T("熊平 短端+100", "Flattener short +100")}
    s.append("### " + T("净经济影响 ($bn)", "Net economic effect ($bn)"))
    s.append(tbl([T("银行", "Bank")] + list(names.values()), [[t] + [f(S.loc[(t, k)].net_econ_12m, 1, True) for k in names] for t in BANKS]))
    s.append("### " + T("净经济影响占 TCE (%)", "Net economic effect as % of TCE"))
    s.append(tbl([T("银行", "Bank")] + list(names.values()), [[t] + [f(S.loc[(t, k)].net_econ_12m_pct_tce, 1, True) for k in names] for t in BANKS]))
    s.append("### " + T("净经济影响占年化 Q3E 盈利 (%)", "Net economic effect as % of annualised Q3E earnings"))
    s.append(tbl([T("银行", "Bank")] + list(names.values()), [[t] + [f(S.loc[(t, k)].net_econ_pct_earn, 0, True) for k in names] for t in BANKS]))
    s.append("### " + T("+100bp 平行情景的构成 ($bn)", "Composition of the +100bp parallel scenario ($bn)"))
    s.append(tbl([T("银行", "Bank"), T("12M NII(税后)", "12M NII (after tax)"), "AFS→AOCI", T("HTM 减值(税后)", "HTM mark (after tax)"), T("净资本影响", "Net capital effect"), T("净经济影响", "Net economic effect")],
                 [[t, f(S.loc[(t, "p100")].nii_after_tax, 2, True), f(S.loc[(t, "p100")].aoci_hit, 2, True), f(S.loc[(t, "p100")].htm_mark_after_tax, 2, True), f(S.loc[(t, "p100")].net_cap_12m, 2, True), f(S.loc[(t, "p100")].net_econ_12m, 2, True)] for t in BANKS]))
    s.append(fig("f13_stress_heat", T("压力测试热力图:净经济影响占 TCE(左)与占年化 Q3E 盈利(右)", "Stress-test heat map: net economic effect as % of TCE (left) and of annualised Q3E earnings (right)")))
    s.append("### " + T("读图要点", "How to read it"))
    b = S.loc[("BAC", "p100")]
    s.append("- " + T(f"**BAC 最脆弱,而且几乎全是 HTM**:+100bp 的净经济影响 {U(b.net_econ_12m)}(占 TCE {b.net_econ_12m_pct_tce:.1f}%,占年化盈利 {b.net_econ_pct_earn:.0f}%),其中 HTM {U(b.htm_mark_after_tax)};只看进入资本的部分(NII+AOCI)只有 {U(b.net_cap_12m)}。+200bp 时净经济影响超过一整年的盈利。",
                f"**BAC is the most fragile, almost entirely through HTM**: +100bp gives a net economic effect of {U(b.net_econ_12m)} ({b.net_econ_12m_pct_tce:.1f}% of TCE, {b.net_econ_pct_earn:.0f}% of annualised earnings), of which HTM is {U(b.htm_mark_after_tax)}; the part that enters capital (NII + AOCI) is only {U(b.net_cap_12m)}. At +200bp the net economic effect exceeds a full year of earnings."))
    w = S.loc[("WFC", "p100")]
    s.append("- " + T(f"**WFC 次之**:{U(w.net_econ_12m)}(占 TCE {w.net_econ_12m_pct_tce:.1f}%);与 BAC 不同,WFC 的 AFS 同样敏感(AOCI {U(w.aoci_hit)}),所以进入资本的部分也不小({U(w.net_cap_12m)})。",
                f"**WFC is next**: {U(w.net_econ_12m)} ({w.net_econ_12m_pct_tce:.1f}% of TCE); unlike BAC, WFC's AFS is also sensitive (AOCI {U(w.aoci_hit)}), so the part that enters capital is also sizeable ({U(w.net_cap_12m)})."))
    j = S.loc[("JPM", "p100")]
    s.append("- " + T(f"**JPM 的 NII 顺风最大**(+100bp 税后 {U(j.nii_after_tax)},为六家最高),抵消了一部分估值损失,净经济影响 {U(j.net_econ_12m)},占年化盈利 {-j.net_econ_pct_earn:.0f}%。",
                f"**JPM has the largest NII tailwind** ({U(j.nii_after_tax)} after tax at +100bp, the highest of the six), which offsets part of the valuation loss; net economic effect {U(j.net_econ_12m)}, {-j.net_econ_pct_earn:.0f}% of annualised earnings."))
    s.append("- " + T("**熊陡 vs 熊平**:长端冲击(熊陡)对四家商业大行都是净负,因为 AOCI 和 HTM 估值损失超过了新增 NII;短端冲击(熊平)对 JPM、BAC、WFC 是小幅净正(NII 增加、估值不变),对 C 是小幅净负(其披露的短端 AOCI 冲击较大)。这说明 **风险在长端,不在政策利率**。",
                "**Steepener vs. flattener**: a long-end shock (steepener) is net negative for all four commercial banks because the AOCI and HTM valuation losses exceed the added NII; a short-end shock (flattener) is slightly net positive for JPM, BAC and WFC (NII rises, valuations unchanged) and slightly negative for C (its disclosed short-end AOCI hit is larger). **The risk is in the long end, not in the policy rate.**"))
    s.append("- " + T("**GS 与 MS** 的 NII 敏感度口径不可比(GS 为对净收入的 EaR,MS 仅财富管理分部),所以它们的 NII 偏小、净影响被高估;熊陡/熊平没有披露(n/a)。",
                "**GS and MS** NII sensitivities are not comparable (GS reports earnings-at-risk on net revenue, MS covers Wealth Management only), so their NII is understated and net effects overstated; steepener/flattener sensitivities are not disclosed (n/a)."))
    s.append("### " + T("局限", "Limits"))
    for z, e in [
        ("线性久期,没有凸性;AFS/HTM 的久期是回归值或兜底值(AFS 3.0 年、HTM 4.5 年),不是披露值。", "Linear duration with no convexity; AFS/HTM durations are regression or fallback values (AFS 3.0 years, HTM 4.5 years), not disclosures."),
        ("基于 6/30 的资产负债表和 6/30 的 10-Q 敏感度,没有更新到 Q3 末;Q3 已发生的上行见第 15 节,与压力测试是叠加关系而不是包含关系。", "Based on the 6/30 balance sheet and 6/30 10-Q sensitivities, not updated to quarter-end; the Q3 rise that has already happened is in Section 15 and is additive to, not included in, the stress test."),
        ("不含信贷成本、贷款需求变化、存款流失与再投资策略的变化;这些在加息中通常是更大的不确定性。", "No credit costs, loan-demand changes, deposit outflows or changes in reinvestment strategy, which are usually the larger uncertainties in a hiking cycle."),
        ("净经济影响把一年内逐步实现的 NII 与即时的估值损失相加,只作排序参考,不是资本比率预测。HTM 损失只有在出售或重分类时才会实现。", "The net economic effect adds NII earned gradually over a year to instantaneous valuation losses and is a ranking aid, not a capital-ratio forecast. HTM losses are realised only on sale or reclassification."),
        ("WFC 的 +200bp NII 未披露,用线性外推。", "WFC's +200bp NII is not disclosed and is extrapolated linearly."),
    ]:
        s.append("- " + T(z, e))

    # 17
    s.append("## " + T("17. IPO:Q3 做了哪些项目,Q4 还会做哪些,每一单收入如何", "17. IPOs: what was done in Q3, what is still coming in Q4, and the fees"))
    s.append(T(f"**先看大局**:Q3 美国 IPO 约 31 单、募资约 $34.9B,其中 SK hynix 一单约 $26.5B,去掉它只有约 $8.4B。我们逐单梳理了 {len(ipo)} 单(合计约 ${proceeds_tot:.1f}B,去掉 SK hynix 约 ${proceeds_ex:.1f}B,约占去掉巨型交易后总募资的 {proceeds_ex/8.4*100:.0f}%)。费用是 **披露值** 或 **费率 × 规模的估算**,各行的分成按角色加权,是估算。",
               f"**The big picture**: Q3 US IPOs were about 31 deals raising about $34.9B, of which SK hynix alone was about $26.5B; excluding it, only about $8.4B. We reviewed {len(ipo)} deals one by one (about ${proceeds_tot:.1f}B in total, about ${proceeds_ex:.1f}B excluding SK hynix, roughly {proceeds_ex/8.4*100:.0f}% of the ex-mega total). Fees are **disclosed** or **spread x size estimates**; per-bank splits are role-weighted estimates."))
    s.append("### " + T("17.1 Q3 已定价的项目与承销费", "17.1 Q3 deals and underwriting fees"))
    rows = []
    for r in ipo.itertuples():
        rows.append([r.deal, r.date, r.sector, f(r.proceeds_usd_m, 0), f(r.fee_usd_m, 1), f(r.fee_pct, 2) + "%", T("披露", "disclosed") if r.fee_basis == "disclosed" else T("估算", "est."), Q3_DEAL_LEADS[r.deal]])
    rows.append([T("**合计**", "**Total**"), "", "", f(ipo.proceeds_usd_m.sum(), 0), f(ipo_total, 1), f(ipo_total / ipo.proceeds_usd_m.sum() * 100, 2) + "%", "", ""])
    s.append(tbl([T("项目", "Deal"), T("日期", "Date"), T("行业", "Sector"), T("募资 ($M)", "Proceeds ($M)"), T("承销费 ($M)", "Fee ($M)"), T("费率", "Spread"), T("依据", "Basis"), T("牵头/联席行(节选)", "Lead / joint banks (selected)")], rows))
    s.append(T("*日期为定价日。Accelevation 于 9/30 定价,交割在季末前后,费用确认季度取决于各行会计政策。SK hynix 为美国上市,承销费 $257.5M 来自披露(约 0.97%);Jersey Mike's $50.0M、Csquare $40.0M(Brookfield 引入的股份不收费)、Attovia $20.23M、River City Bank $5.913M 也为披露值。其余按美国惯例:募资不足 $5 亿约 7%,$5-10 亿约 5%,封闭式基金 4.5% 销售费用。*",
               "*Dates are pricing dates. Accelevation priced on 9/30 with settlement around quarter-end, so the quarter in which fees are recognised depends on each bank's accounting policy. SK hynix is US-listed and its $257.5M fee (about 0.97%) is disclosed; Jersey Mike's $50.0M, Csquare $40.0M (shares introduced by Brookfield carry no fee), Attovia $20.23M and River City Bank $5.913M are also disclosed. The rest follow US convention: about 7% below $500M, about 5% for $500M-1B, and a 4.5% load for the closed-end fund.*"))
    s.append("### " + T("17.2 六大行的 Q3 IPO 承销费(估算)", "17.2 Estimated Q3 IPO underwriting fees of the six large banks"))
    cols = BANKS + ["OTH"]
    rows = []
    for r in ipo.itertuples():
        rows.append([r.deal] + [f(ipob.loc[r.deal, c], 1) if ipob.loc[r.deal, c] > 0 else "-" for c in cols])
    rows.append([T("**合计**", "**Total**")] + [f(ipo_by_bank[c], 1) for c in cols])
    s.append(tbl([T("项目 ($M)", "Deal ($M)")] + BANKS + [T("其他承销商", "Other underwriters")], rows))
    rows = []
    for t in BANKS:
        n = int((ipob[t] > 0).sum())
        rows.append([t, str(n), f(ipo_by_bank[t], 1), f(ib_e[t] * 1e3, 0), f(ipo_by_bank[t] / (ib_e[t] * 1e3) * 100, 1) + "%"])
    s.append(tbl([T("银行", "Bank"), T("参与项目数", "Deals"), T("估算 IPO 费用 ($M)", "Est. IPO fees ($M)"), T("Q3E 投行费用 ($M)", "Q3E IB fees ($M)"), T("占比", "Share")], rows))
    s.append(fig("f14_ipo_fees", T("IPO 承销费:Q3 估算 vs Q2 SpaceX(左),占 Q3E 投行费用比重(中),Q4 Anthropic 情景(右)", "IPO underwriting fees: Q3 estimate vs. Q2 SpaceX (left), share of Q3E IB fees (middle), Q4 Anthropic scenario (right)")))
    s.append("### " + T("读图要点", "How to read it"))
    cmax = max(BANKS, key=lambda t: ipo_by_bank[t] / (ib_e[t] * 1e3))
    s.append("- " + T(f"**IPO 费用只是投行费用的一小块**:六大行里最高的是 {cmax},也只有约 {ipo_by_bank[cmax]/(ib_e[cmax]*1e3)*100:.1f}%;其余多为 1%-5%。投行费用更大的部分是并购顾问、债券和杠杆融资承销。这支持第 0 节「IPO 火热对 Q3 费用不成立」。",
                f"**IPO fees are a small slice of IB fees**: the highest of the six is {cmax} at only about {ipo_by_bank[cmax]/(ib_e[cmax]*1e3)*100:.1f}%; the rest are mostly 1%-5%. The bulk of IB fees comes from M&A advisory, debt and leveraged-finance underwriting. This supports Section 0's point that 'a hot IPO market does not hold up for Q3 fees'."))
    s.append("- " + T(f"**一单就决定排名**:SK hynix 费用 ${skh:.1f}M 占所有梳理项目费用的 {skh/ipo_total*100:.0f}%,Citi 估算约 $70M(报道称超过 $70M),BofA、GS、JPM 各约 $55M(估算);去掉它,各行的 IPO 费用都只有十几到几十百万美元。",
                f"**One deal decides the ranking**: SK hynix's ${skh:.1f}M fee is {skh/ipo_total*100:.0f}% of all fees in the reviewed deals; Citi is estimated at about $70M (reported as above $70M), and BofA, GS, JPM at about $55M each (estimates); without it each bank's IPO fees are only in the low tens of millions."))
    s.append("- " + T("**费率与规模成反比**:SK hynix 约 0.97%,SpaceX 约 0.67%(基础发行 $750 亿对应约 $5 亿),$10 亿级约 4%-5%,$3 亿以下生物科技约 7%。所以募资额大不等于费用大。",
                "**Spread falls with size**: SK hynix about 0.97%, SpaceX about 0.67% (about $500M on a $75B base deal), $1B-class deals about 4%-5%, and biotechs under $300M about 7%. A large raise does not mean large fees."))
    s.append("- " + T(f"**Q2 对照**:SpaceX 一单的费用池约 $500M(GS、MS 各约 $100M,BofA、Citi、JPM 各约 $75M),与我们梳理的 Q3 全部 18 单合计(约 ${ipo_total:.0f}M)相当。这是 Q2 投行费用创纪录的关键。",
                f"**Q2 comparison**: SpaceX alone had a fee pool of about $500M (GS and MS about $100M each, BofA, Citi and JPM about $75M each), comparable to the combined fees of all 18 Q3 IPOs we reviewed (about ${ipo_total:.0f}M). It was the key to the record Q2 IB fees."))
    s.append("### " + T("17.3 Q4 已知的 IPO 管线", "17.3 Known Q4 IPO pipeline"))
    rows = []
    for r in pipe.itertuples():
        size = "n/d" if pd.isna(r.size_usd_m) else f(r.size_usd_m, 0)
        fee = "n/d" if pd.isna(r.fee_est_usd_m) else f(r.fee_est_usd_m, 0)
        rows.append([r.deal, r.timing, size, ("-" if pd.isna(r.spread) else f(r.spread * 100, 2) + "%"), fee, r.leads, r.status])
    s.append(tbl([T("项目", "Deal"), T("时间", "Timing"), T("规模 ($M)", "Size ($M)"), T("费率假设", "Assumed spread"), T("费用估算 ($M)", "Fee est. ($M)"), T("牵头行", "Leads"), T("状态", "Status")], rows))
    s.append(T("*n/d = 未披露。除 Anthropic 外,规模来自媒体或备案文件,可能变化;费率为假设。Oura 已于 9/29 推迟。管线中的其他项目(Switch、Holtec Nuclear、Tailored Brands、CoVolt Power、Wella、Iambic、Retension、TRex Bio 等)规模多未披露,未估算。Renaissance 估计年底前 40-70 单较大的美国 IPO 可能募资超过 $1250 亿,取决于巨型交易是否成行。*",
               "*n/d = not disclosed. Apart from Anthropic, sizes come from media reports or filings and may change; spreads are assumptions. Oura was postponed on 9/29. Other pipeline names (Switch, Holtec Nuclear, Tailored Brands, CoVolt Power, Wella, Iambic, Retension, TRex Bio, etc.) mostly have undisclosed sizes and are not estimated. Renaissance estimates 40-70 sizeable US IPOs by year-end could raise more than $125B, depending on whether the mega deals happen.*"))
    s.append("### " + T("17.4 Anthropic 情景:Q4 最大的费用变量", "17.4 The Anthropic scenario: the biggest Q4 fee variable"))
    s.append(T("据媒体报道,Anthropic 目标 11 月、中期选举之后上市,募资规模最高约 $1000 亿、估值约 2 万亿美元,路演预计 10 月中旬,牵头行为 MS 和 GS,JPM 和 Citi 参与;截至本文日期尚无公开 S-1,所有信息未经证实。OpenAI 已推迟到 2027 年。下面的表是假设推演,不是预测。",
               "Media reports say Anthropic is targeting a November listing after the midterms, raising up to about $100B at a valuation of about $2T, with a roadshow expected in mid-October, MS and GS leading and JPM and Citi involved; there is no public S-1 as of this writing and none of this is confirmed. OpenAI has been pushed to 2027. The table below is an assumption-driven scenario, not a forecast."))
    g = pd.read_csv(os.path.join(D, "ipo_anthropic_scenarios.csv"))
    rows = [[f"${r.size_bn:.0f}B", f"{r.spread_pct:.2f}%", f(r.pool_usd_m, 0), f(r.lead_each_usd_m, 0), f(r.other_major_each_usd_m, 0)] for r in g.itertuples()]
    s.append(tbl([T("募资规模", "Size"), T("费率", "Spread"), T("费用池 ($M)", "Fee pool ($M)"), T("牵头行各得 20% ($M)", "Each lead bank, 20% ($M)"), T("其他主承销商各得 15% ($M)", "Each other major, 15% ($M)")], rows))
    base = g[(g.size_bn == 100) & (g.spread_pct.round(2) == 0.67)].iloc[0]
    rows = []
    for t, share in (("MS", 0.20), ("GS", 0.20), ("JPM", 0.15), ("C", 0.15)):
        amt = base.pool_usd_m * share
        rows.append([t, f"{share*100:.0f}%", f(amt, 0), f(ib_e[t] * 1e3, 0), f(amt / (ib_e[t] * 1e3) * 100, 1) + "%"])
    s.append(tbl([T("银行(基准:$1000 亿、0.67%)", "Bank (base case: $100B, 0.67%)"), T("份额假设", "Share assumption"), T("估算费用 ($M)", "Est. fee ($M)"), T("Q3E 投行费用 ($M)", "Q3E IB fees ($M)"), T("相当于一个季度投行费用的", "As % of a quarter's IB fees")], rows))
    s.append("- " + T("**假设来源**:费率 0.5%/0.67%/1.0% 涵盖了巨型交易的区间(SpaceX 约 0.67%,SK hynix 约 0.97%);份额沿用 SpaceX 的 20%(牵头)和 15%(其他主承销商)。",
                "**Where the assumptions come from**: spreads of 0.5% / 0.67% / 1.0% span the mega-deal range (SpaceX about 0.67%, SK hynix about 0.97%); shares follow SpaceX's 20% (lead) and 15% (other major)."))
    s.append("- " + T("**含义**:即使是史上最大的 IPO,在基准情景下对牵头行也只是约一个季度投行费用的 4%-5%,对 C 约 8%;关键是 **时点**:它若落在 11 月,就是 Q4 的增量,而不是 Q3 的。如果 AI 大额 IPO 推迟到 2027,Q4 的 IB 费用就更依赖并购与债券。",
                "**Implication**: even the largest IPO ever amounts, in the base case, to only about 4%-5% of a quarter's IB fees for the lead banks and about 8% for C; the point is **timing**: if it lands in November it is incremental to Q4, not Q3. If the large AI IPOs slip to 2027, Q4 IB fees rely more on M&A and debt."))
    s.append("### " + T("17.5 IPO 部分的局限", "17.5 Limits of the IPO section"))
    for z, e in [
        ("覆盖:18 单,约占去掉 SK hynix 后 Q3 募资的七成;其余约 12 单规模较小。", "Coverage: 18 deals, about 70% of Q3 proceeds excluding SK hynix; the remaining dozen or so deals are small."),
        ("各行分成:除 SK hynix 与 SpaceX 有报道外,均按「牵头/全球协调人 = 2,联席账簿管理人 = 1,其他 = 0.5-1」加权;「其他承销商」包括未单列的中小券商。", "Per-bank splits: apart from SK hynix and SpaceX, which have press reports, splits weight 'lead / global coordinator = 2, joint bookrunner = 1, other = 0.5-1'; 'Other underwriters' include smaller dealers not listed individually."),
        ("费用确认:IPO 费用通常在定价/交割时确认,跨季项目可能进入下一季度;各行披露的投行费用还包含并购、债券、杠杆融资,这里只拆 IPO。", "Recognition: IPO fees are generally recognised at pricing / settlement, so deals around quarter-end may fall into the next quarter; banks' reported IB fees also include M&A, debt and leveraged finance, while only IPOs are broken out here."),
        ("中国与香港的巨型 IPO(CXMT 约 $86 亿、中际旭创 $68-78 亿)由中资或国际银行承销,美国大行只在中际旭创里有 GS、MS 参与,未纳入上表。", "The large China / Hong Kong IPOs (CXMT about $8.6B, Zhongji Innolight $6.8-7.8B) are underwritten by Chinese or international banks; of the US banks only GS and MS take part (in Zhongji Innolight) and they are not in the table above."),
    ]:
        s.append("- " + T(z, e))
    return "\n\n".join(fr) + "\n", "\n\n".join(s) + "\n"


if __name__ == "__main__":
    for lang in ("zh", "en"):
        fr, su = build(lang)
        open(os.path.join(SRC, f"front_{lang}.md"), "w").write(fr)
        open(os.path.join(SRC, f"supp_{lang}.md"), "w").write(su)
        print(lang, len(fr), len(su))
