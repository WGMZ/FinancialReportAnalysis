# US Financials Ahead of the Q3 2026 Earnings Season: Who Is Bullish, Who Is Bearish

> Data as of the 2026-10-01 close; written on 2026-10-02. Bank reporting window: 10/13 (JPM, C, WFC, GS), 10/14 (BAC, MS), 10/15 (PNC, SCHW, USB), around 10/16 (TFC, MTB, CFG, HBAN, BNY, RF), 10/19 (FITB), 10/20 (KEY), 10/22 (COF). The FOMC meets on 10/27-28, in the middle of the season.
>
> This is a scenario analysis built on public information, not personalised investment advice. Every "probability of beating" is a model output under the assumptions stated in the text, not a historical frequency. Section 10 lists the methodological limits; please read it first.
>
> Reproduction: scripts under `research/scripts/`; tables in `research/output/*.csv`; consensus and sources in `research/data/consensus_q3_2026.csv`.

---

## 0. Bottom line first

1. **Three axes, not one, drive the dispersion this quarter.**
   - (a) Direction of capital-markets exposure. Q2 was a record quarter and Q3 cooled across the board; how far IB and trading fall quarter on quarter differs a lot by bank.
   - (b) Timing mismatch of the rate shock between the income statement and the balance sheet. The long end rose about 85bp in Q3, but the policy rate averaged only +4bp. Fixed-rate assets reprice faster than liabilities, which is an NII tailwind, but it will not be fully realised until Q4 and 2027. The AOCI loss on AFS securities, however, has already happened this quarter.
   - (c) One-offs in the Q2 base (the Visa B-2 exchange gain, M&A accounting) decide how much of the "quarter-on-quarter decline" is not real.
2. **The premise "the IPO market is hot" does not hold for Q3, at least not for fee revenue.**
   - Q2 was the IPO peak. Excluding mega deals, Q3 IPOs cooled noticeably, and announced M&A volume fell about 41% quarter on quarter.
   - Fee rates on mega IPOs are very low (SK hynix's underwriting spread is about 0.97%), so proceeds overstate fee revenue.
   - Management guidance also diverges: JPM says IB fees are up "mid-to-high teens" year on year, C says "low single digits", BAC says down 10%+ year on year ($1.6-1.8B), PNC says fee income is down 5% quarter on quarter.
3. **Model ranking (details in Sections 4 and 5):**
   - **EPS likely to beat consensus**: C, FITB, MS, JPM, TFC (low confidence), BNY (prior).
   - **Neutral**: USB, KEY, PNC, MTB, CFG, WFC, COF.
   - **EPS likely to miss consensus**: GS (-8%), BAC (-5%), HBAN (-8%); SCHW slightly weak.
4. **"EPS beats" and "the stock goes up" are two different things.** Especially this quarter, because:
   - The sector already sold off hard in September (XLF -7.1% in September, KBWB -8.1%) and sits 8-25% below its 52-week highs.
   - Names with low expectations and light positioning (C, MS, JPM, TFC) have better odds.
   - Names that have already outperformed on high valuations (STT +39% YTD, BNY +26%, BEN +41%) are prone to "sell the news".
5. **The biggest tail risk is not earnings but the rate path.** The 10Y is at 5.3%, the largest single-quarter rise in Treasury yields this century. If October CPI or the FOMC pushes the long end up further, the AOCI/TBV and credit-cost narrative will overwhelm Q3 EPS.

---

## 1. Macro backdrop (2026 Q3)

| Indicator | Data |
|---|---|
| Fed funds target | Hiked 25bp on 9/16 to 3.75-4.00% (Warsh as Chair); IORB 3.90% |
| SEP year-end median | 4.1%; PCE 3.7% |
| Oil | WTI about $96, Brent about $114 (Iran-war shock) |
| Treasury curve, Q3 change | 2Y +74bp, 5Y +90bp, 10Y +85bp, 30Y +73bp (bear steepening) |
| 10Y yield | 5.29% on 9/30, touched 5.34% on 10/1, the largest single-quarter rise this century |
| Q3 average policy-rate change | only +4bp |
| 2s10s | Narrowed to about 22bp at one point on 9/22 (about 54bp a year earlier) |
| Equities | SPY +2.4% in Q3, XLK +2.9%, SMH -7.1% (but +71.6% YTD), XLF ±0% in Q3, KRE -6.7%, TLT -9.0% |
| Credit | FDIC Q2: industry net charge-off rate 0.57% (-2bp QoQ), past-due + non-accrual 1.44%, still improving overall |

**Transmission chain (to bank earnings)**

- Asset side: yields on newly originated and reinvested fixed-rate assets (MBS, loans) are up about 75-120bp (RF discloses about $3B of maturing assets reinvestable at +75-100bp; PNC's securities restructuring bought at yields 120bp higher).
- Liability side: deposit betas lag. The Q3 average policy rate rose only 4bp, so deposit costs have not caught up yet.
- Result: a sequential rise in NII and NIM is clear, but its size is split up by "tougher deposit competition, cash stockpiles (e.g. FITB's Comerica transition cash), and day-count effects".
- At the same time: the fall in fair value of AFS securities hits AOCI/TBV directly; HTM losses do not enter capital, but they are a hidden loss in "economic TBV".
- Demand side: Moynihan said explicitly that "if rates rise further, loan demand will slow". IB's DCM, leveraged finance and the IPO window are very sensitive to a rising long end.

**12-month NII sensitivity disclosed in the 10-Qs (as of 6/30, +100bp parallel shift)**

| Bank | Effect of +100bp |
|---|---|
| JPM | NII +$1.8B (of which long end +$1.1B) |
| WFC | +$1.3B |
| BAC | +$1.0B (mostly from the short end) |
| C | Asset sensitive; initial AOCI about -$3B (disclosed text) |
| SCHW | NII +3.6% |
| CFG | +0.9% |
| FITB | +0.42% (year one, ramped). EVE is negative at ±100bp; deliberately moving toward asset sensitivity |
| MTB | -0.18% (slightly liability sensitive) |
| RF | +$62M |

These are static balance-sheet model values that depend on deposit-beta assumptions; they must not be read as a Q3 forecast.

---

## 2. Method and mathematical framework

### 2.1 The EPS bridge (used for the forecasts in Section 4)

$$EPS_{Q3}=\frac{\big(PBT^{clean}_{Q2}+\sum_i \Delta_i\big)(1-t_3)-Pref}{Shares_{Q3}}$$

- $PBT^{clean}_{Q2}$: pre-tax profit with Q2 one-offs removed. For JPM we back-solve from the "clean EPS" of 6.14; PNC uses adjusted EPS of 4.85; FITB stays on GAAP with merger costs modelled separately.
- $\Delta_i$: every item comes from management guidance or the Q2 report, carries a standard deviation, and can be tied to one of three common factors:
  - `mkt`: capital-markets activity, one shared draw for all banks.
  - `rate`: NII surprise.
  - `credit`: provisions.
- The compensation (bonus) offset loads negatively on `mkt`: when revenue falls, the bonus accrual falls too.
- A further 2.5% multiplicative model-risk term is added. We run 40,000 Monte Carlo draws.

### 2.2 Duration gap and AOCI/TBV

$$\Delta TCE_{AFS}=-D_{AFS}\cdot\Delta y\cdot AC_{AFS}\cdot(1-\tau)$$

- $D$ is not a disclosed value; it is an effective duration regressed from the quarterly series: $\Delta(UL\%)=-D\,\Delta y+\text{roll}$. UL% is unrealised loss as a share of amortised cost; AFS is regressed on a 5Y/10Y blended rate and HTM on the 30-year mortgage rate.
- Q3 $\Delta y$: the 5Y/10Y blend is about +87.5bp, the mortgage rate +54bp, and the tax rate is 24%.
- If the regression R² < 0.5 or the duration is implausible, a fixed fallback is used (AFS 3.0 years, HTM 4.5 years), flagged in the `afs_src` / `htm_src` columns of `risk_scorecard.csv`.
- **Check**: the same convention gives BAC a TCE of $206.0B, matching the $206B quoted by Barron's; BAC's HTM unrealised loss of $82.1B matches the $82B in its supplement.

### 2.3 Leverage

- Leverage multiple = total assets / TCE. TCE = equity - goodwill - intangibles - preferred.
- The higher the leverage, the larger the same AOCI shock is as a share of TCE. BNY is at 25.8x, STT 24.4x, SCHW and GS about 21x, while PNC is 12.2x and COF 11.2x.

---

## 3. Segment breakdown

### 3.1 Retail and commercial banking: deposit-loan spread and duration mismatch

The key is NII quarter on quarter, and whether it is "high-quality" NII.

| Bank | Q3 NII guidance / clue | Comment |
|---|---|---|
| USB | +4-6% YoY, toward the high end; NIM improves in Q3 and Q4 | Loans +3.0% QoQ, fixed-rate asset repricing; but Q3 takes a one-off reserve of about $160M for the Amazon small-business portfolio |
| PNC | NII +3-3.5% QoQ; loans +1-2% | FirstBank integration; fee income -5-5.5% QoQ |
| FITB | NII +2-2.5% QoQ, CFO says "toward the high end"; NIM in the mid-3.30s, strong deposit growth | Cautious deployment of securities duration; cash above $20B depresses NIM by about 1bp per $1B |
| CFG | NII +2.5-3.5% QoQ | Expenses flat |
| KEY | Full-year NII +9-11%, Q4 NIM exit rate 3.00-3.05% | Back-solves to Q3 NII of about $1.30B |
| RF | NII about +2% QoQ; NIM stable to slightly higher; 3.70% by year-end | One extra day |
| TFC | NII about +1.5% QoQ; full-year NII growth cut to 1-1.5% | Slightly higher deposit costs, narrower loan spreads (Q2 NIM -4bp) |
| HBAN | Full-year NII growth cut from 39-43% to about 35% | Back-solves to roughly flat Q3 NII (Q2 $2,052M); deposit competition, weak loan volume |
| MTB | Full-year NII in the lower half of $7.2-7.35B | H2 NIM in the mid-3.60s, slightly lower |
| WFC | About $50B for the year (of which Markets $2B) | H1 $24.4B, implying H2 of about $25.6B; NIM stable in Q3 and Q4 |
| JPM | Full-year total NII about $105.5B (raised) | H1 $50.9B, implying H2 of $54.6B |
| BAC | Full-year NII growth "toward the high end" (6-8%) | Yields rising; but Markets NII overlaps with S&T |

**Why rising rates split the banks**

- Banks that are asset sensitive, with a high share of fixed-rate assets maturing soon (USB, FITB, KEY, PNC, CFG), have a clear NII tailwind.
- Banks facing stronger deposit competition, or that added deals such as Cadence/Comerica, carry a lot of "purchase accounting" and "cash transition" noise in NII (HBAN, FITB).
- Banks with a large retail deposit base that are forced to pay more for deposits (TFC, MTB) see NII growth cut first.

### 3.2 Investment banking (IB)

**Checking the claim that "the IPO market is hot"**

- Q2 was the peak: JPM IB fees $3.2B (+30% YoY), BAC $2.1B (+50%), C +44%.
- Excluding mega deals, Q3 IPOs and announced M&A volume were both clearly below Q2.
- Fees are not proceeds: mega issues on the scale of SK hynix pay an underwriting spread of only about 0.97%, so "large proceeds" do not automatically become IB fees.

**Q3 IB guidance by bank (YoY / QoQ)**

| Bank | Guidance | Implied Q3 IB fees | QoQ |
|---|---|---|---|
| JPM | YoY "mid-to-high teens" (Q3'25 $2.6B) | About $3.0B | About -5% |
| C | YoY "low single digits + depends on the last few deals" | No absolute figure | Estimated to fall QoQ |
| BAC | YoY down 10%+, $1.6-1.8B (Q3'25 $2.0B) | $1.6-1.8B | About -20% |
| GS | "Investing lines sharply weaker"; MS Research says IB slightly lower | n/a | Small decline |
| MS | 100+ sell-side mandates in hand; IB fees could exceed $2B | n/a | Flat / slightly higher |
| PNC | Fee income -5 to -5.5%, mainly capital markets | n/a | n/a |
| USB | BTIG added, about $200M per quarter | n/a | Higher (acquisition-driven) |

**Explaining the divergence**: JPM's and MS's strength lies in ECM and M&A for large corporates and AI/tech financing; BAC itself admits it is "lightly positioned in the active businesses". This is a structural divergence, not noise.

### 3.3 Sales and trading (S&T): equities vs. fixed income

| Bank | Q3 guidance | Our assumption |
|---|---|---|
| JPM | Markets YoY "mid-to-high teens" (Q3'25 $8.9B) | About $10.4B; Q2 $12.1B was a record, so about -14% QoQ |
| BAC | S&T roughly flat YoY ($5.4B); equities up, fixed income down; Asia PB balances down | About $5.5B vs. Q2 $7.1B, about -22% QoQ |
| C | Markets YoY "mid single digits" | About -$0.7B QoQ |
| GS | Equities "still very strong", FICC "relatively softer" | Equities -$0.3B, FICC -$0.6B QoQ |
| MS | "3Q is no 2Q" | Equities -$0.45B, FICC -$0.25B |
| WFC | No explicit guidance | Non-interest income -$0.45B QoQ (Q2 was unusually strong) |

**Implications of equity/bond allocation and term structure**: the equity side (PB, derivatives, cash equities) remained strong in Q3, which favours GS/MS/C. The fixed-income side is affected by the rapid rise in long-end rates and spread volatility, though large swings are themselves revenue for market-making. Whether money is made ultimately depends on hedging: in one-way yield shocks, proprietary inventory positions are at higher risk, while client-flow-driven market-making benefits.

### 3.4 Brokerage, wealth management, asset management, ETFs

- **SCHW**
  - Q2 NIM +12bp QoQ to 3.00%; net interest revenue $3,357M (+19% YoY); client sweep cash $485.7B.
  - Fitch believes cash-sorting pressure has eased, but cash as a share of client assets is still below its historical level.
  - Its bank securities portfolio has a duration of about 3.5 years and about 4% floating rate, so higher rates plus repricing are a positive.
  - But consensus has already pushed EPS to $1.67 (from $1.57 three months ago), and AOCI is already -43% of TCE with 21x leverage. Our model gives $1.65, slightly below consensus.
- **MS wealth management**: Q2 net new assets were a record $148B, more than half from IPO-related employee-plan inflows. Q3 depends on how much converts into fee-paying assets.
- **BAC wealth (Merrill + Private Bank)**: AUM fees +10-15% YoY.
- **Market-linked asset-management fees**: the S&P 500 Q3 average was up about 4.8% QoQ (only +2% at period end). Firms that bill on beginning or average AUM (BLK, TROW, AMP, LPL) benefit from the higher average, but their share prices are more sensitive to the period-end level.
- **ETFs and asset-manager share prices**: in Q3, BLK +10.6%, IVZ +15.1%, BEN -2.5%, TROW -7.3%. BEN is +41% YTD and +48% over one year, so expectations are high.

### 3.5 Exchanges, alternative managers, payments, mortgage

These are outside our EPS-driver model and are covered only by price and qualitative judgement:

| Category | Q3 | YTD | Judgement |
|---|---|---|---|
| Exchanges CME / ICE / NDAQ / CBOE | +19% / +24% / +17% / +14% | ~0 / -5% / -5% / +11% | Driven by rate volatility and derivatives volume; the strength has already been realised |
| Alternative managers BX / KKR / APO / ARES / CG / OWL | -4% / 0% / -2% / +6% / -5% / +6% | -25% / -28% / -20% / -25% / -30% / -36% | 24-44% below highs; the market worries about private-credit valuations and the pace of IPO monetisation, and valuations have compressed |
| Mortgage UWMC / RKT / PFSI | -48% / -27% / -29% | -70% / -38% / -53% | Directly hit by higher mortgage rates |
| Payments / data V / MA / FIS / FISV / GPN | +5% / +8% / -14% / -8% / +13% | +3% / -3% / -49% / -32% / +5% | V/MA steady; FIS/FISV dragged by other factors |
| Cards / consumer AXP / ALLY / SYF | -10% / -18% / -6% | -18% / -15% / -13% | Worries about provisions and consumer-credit stress |

---

## 4. EPS forecast by name and probability of beating consensus

`q3_model.csv` (driver method = item-by-item bridge; prior method = prior). Consensus comes from several aggregator pages that disagree; sources are recorded in `consensus_q3_2026.csv`.

| Ticker | Q2 EPS | Consensus | Model mean | P10-P90 | vs. cons. | P(beat) | P(< -3%) | Method |
|---|---|---|---|---|---|---|---|---|
| FITB | 0.83 | 0.84 | 0.95 | 0.81-1.08 | +12.5% | 84% | 11% | driver |
| C | 3.15 | 2.64 | 2.96 | 2.58-3.34 | +11.9% | 86% | 9% | driver |
| MS | 3.46 | 3.09 | 3.30 | 2.81-3.80 | +6.9% | 71% | 22% | driver |
| TFC | 1.23 | 1.12 | 1.19 | 1.08-1.30 | +6.3% | 80% | 11% | driver (single-source consensus) |
| JPM | 6.14 | 5.86 | 6.10 | 5.66-6.54 | +4.0% | 75% | 12% | driver |
| BNY | 2.45 | 2.26 | 2.35 | 2.21-2.49 | +4.0% | 79% | 8% | prior |
| KEY | 0.44 | 0.46 | 0.48 | 0.42-0.54 | +3.9% | 65% | 24% | driver |
| USB | 1.35 | 1.32 | 1.36 | 1.24-1.47 | +2.6% | 64% | 21% | driver |
| COF | 4.73 | 5.35 | 5.41 | 4.86-5.96 | +1.0% | 56% | 30% | prior |
| PNC | 4.85 | 4.89 | 4.92 | 4.59-5.25 | +0.5% | 54% | 25% | driver (adjusted basis) |
| MTB | 5.32 | 4.91 | 4.92 | 4.47-5.38 | +0.2% | 51% | 33% | driver |
| CFG | 1.30 | 1.40 | 1.40 | 1.26-1.54 | -0.1% | 49% | 36% | driver |
| WFC | 2.00 | 1.85 | 1.84 | 1.64-2.04 | -0.5% | 47% | 39% | driver |
| SCHW | 1.62 | 1.67 | 1.65 | 1.56-1.74 | -1.3% | 38% | 34% | driver |
| BAC | 1.21 | 1.15 | 1.09 | 1.00-1.17 | -5.5% | 17% | 67% | driver |
| HBAN | 0.33 | 0.39 | 0.36 | 0.31-0.41 | -7.6% | 22% | 69% | driver |
| GS | 20.98 | 15.39 | 14.19 | 9.57-18.84 | -7.8% | 37% | 58% | driver |

### 4.1 Derivation of the key calls

**C (largest positive gap)**

- Q2 EPS was $3.15, while Q3 consensus is $2.64 (-16%).
- Q1 and Q2 actuals beat consensus by +15.4% and +15.0%, showing the sell side is anchored on the old 10-11% ROTCE guidance; in September management changed its tone to "above 11% for the full year".
- Our bridge: Markets -$0.7B, IB -$0.15B, Services/Wealth/USPB +$0.25B, expenses -$0.1B, provisions -$0.1B, for a total pre-tax -$0.6B, or about -0.19 EPS, plus a lower share count (1,736M to 1,710M).
- Risk: if Q2 contains non-recurring items we have not identified (we found no disclosure of a Visa gain), the base is too high.

**JPM**

- After the full-year guidance raise, H2 NII is about $27.3B per quarter. Markets falls from $12.1B to about $10.4B and IB falls about $0.16B; the bridge totals about -$0.31B pre-tax.
- The sell side's $5.86 is conservative (a 4-quarter average beat of +4.6%, +9.8% in Q2); our $6.10 is more consistent.
- Part of the upside is already priced in by the "whisper $6.09".

**MS**

- Management has explicitly lowered Q3 expectations (consensus $3.08-3.13 vs. Q2 $3.46). Our bridge is slightly above consensus, mainly because the bonus accrual falls with revenue and the tax rate goes from about 24% to 23%.
- A caveat: about $200M of unrealised carry reversal (about $0.05 of EPS) is already included.

**BAC (most worth worrying about)**

- On 9/14 Moynihan said Q3 IB fees would be $1.6-1.8B and S&T flat YoY ($5.4B).
- Q2 S&T was $7.1B and IB $2.1B, so these two lines alone are about -$1.95B of revenue quarter on quarter. The NII increment (about +$0.3B) and wealth fees (+$0.1B) offset only part of it.
- Expenses are anchored near $18.6B. The result is EPS of about $1.09 vs. consensus of $1.14-1.17.
- Reality check: consensus revenue is $30.9-31.2B vs. $31.56B in Q2, meaning the sell side cut only $0.4-0.6B, inconsistent with management's "-$1.6B+ quarter-on-quarter revenue".
- The biggest uncertainty in this call: the consensus basis may include FTE or treat the S&T / NII overlap differently; also one data page (earningscalls.dev) shows Q3 EPS of $1.45, which is clearly wrong and was excluded.
- The stock already fell more than 5% on 9/14 and is -12.9% over one month, so a good part of the miss is already expected.

**GS**

- Solomon said three things: investing lines are "sharply weaker"; non-compensation expenses are up $500M+ QoQ (trading costs, technology spending, charitable giving pulled forward); and provisions are slightly higher.
- MS Research cut Q3 EPS to $13.76 (19% below consensus at the time); the non-compensation expense revision alone cut consensus EPS by 12%.
- Our bridge gives $14.2, with a P10-P90 of $9.6-18.8, the widest range of any name. GS is also the most volatile (60-day volatility of 36%).

**HBAN**

- Full-year NII growth was cut to about 35% (from 39-43%), which back-solves to roughly flat Q3 NII. Q2 EPS was $0.33, and the $0.39 consensus requires a large improvement.
- Lower integration costs for the Cadence acquisition are the main positive but not enough to cover it. BAC and MS downgraded it in July.

**FITB**

- Q2 adjusted EPS was $1.02 (GAAP $0.83, including $203M of merger costs). YTD merger costs are about 65% of the full-year total, so roughly one-third remains for H2 and Q3 (the systems-conversion quarter) is about $200M.
- On 9/15 management said NII and fee income are at the high end of guidance and expenses at the low end.
- The $0.84 consensus looks GAAP-based and conservative. But the Q3 AOCI hit of -7% of TCE is a risk.

**TFC (low confidence)**

- Consensus of $1.12 is below Q2's $1.23, while guidance is revenue +1%, NII +1.5%, expenses +2%.
- Question mark: Q2 other income of $208M (Q1 $102M) may contain one-offs; we have already deducted $60M.
- Consensus has a single source (MarketBeat), so we only say "leaning toward a beat" and give it little weight.

### 4.2 Names without a driver model

- **BNY**: full-year revenue +10-11%, NII +12-13%, expenses +6-7%; the sell side's $2.25-2.27 is below Q2 because the Q2 base may contain non-recurring items. We lean +4%. But with 25.8x leverage, an AFS AOCI hit of -10.6% of TCE and +26% YTD, the stock is less sensitive to a "beat".
- **COF**: card NCO rate 3.23% (-22bp QoQ), Discover integration costs down to $298M, but Q3 NIM is seasonally weak; adjusted consensus is $5.34-5.37 and we are neutral.
- **STT / NTRS / RF / ZION**: Q2 included a Visa gain or one-offs (ZION disclosed about $252M of pre-tax non-recurring items), so the base is not clean and we give no point estimate.

---

## 5. Tiered list

**This is a composite score, not a trade instruction.** Composite = 0.5 x earnings score + 0.3 x price-momentum score + 0.2 x balance-sheet score (`summary_table.py`).

### 5.1 Leaning bullish (EPS likely better than consensus, with modest expectations)

| Ticker | Rationale | Main risk |
|---|---|---|
| **C** | Consensus systematically low (two straight quarters of 15%+ beats); management raised full-year ROTCE; -7% in Q3 and 12% below its high | Q2 base may contain unidentified one-offs |
| **JPM** | Guidance raised for NII and expenses, IB/Markets up mid-to-high teens YoY; provision guidance lowered (card NCO 3.2%) | Expenses keep being raised; the "whisper" is already above consensus |
| **MS** | Management has already lowered expectations; wealth management + 100+ sell-side mandates; stock -10.9% (1 month) | IPO-related flows in Q2 are not sustainable; UBS M&A rumour (9/24) is a distraction |
| **FITB** | All Q3 guidance for the Comerica integration is at the high end; conversion complete | Size of merger costs (consensus range $0.34-1.11 is very wide); AOCI hit about -7% of TCE |
| **USB** | NII at the high end, fee income +12-14%, NIM improving; consensus slightly low | $160M Amazon reserve; securities AOCI already -17% of TCE |
| **TFC** (low confidence) | Guidance and consensus disagree; leaning toward a beat | Single-source consensus |

### 5.2 Neutral (information mostly in the price, or drivers offset)

PNC, MTB, CFG, KEY, WFC, COF.

- **KEY**: EPS slightly better, but AFS duration of 4.4 years and a Q3 AOCI hit of -8.2% of TCE make it one of the most sensitive regionals; -12% in Q3.
- **WFC**: EPS roughly in line with consensus; but it is -12.5% YTD and -7.8% over one month, expectations are low, and with the asset cap lifted the market expects some upward revision to NII guidance (a positive surprise if it comes).
- **PNC**: full-year guidance is clear and EPS is almost identical to consensus. Note the adjusted basis (about $50M of integration costs in Q3).

### 5.3 Leaning bearish (EPS risk skewed down, or the narrative is against them)

| Ticker | Rationale |
|---|---|
| **GS** | Management has already spelled out three Q3 headwinds; the consensus range is wide and some estimates have not caught up; but the stock is already -10.5% (Q3) / -21.8% below its high, a sizeable cushion |
| **BAC** | Management's IB/S&T guidance is inconsistent with consensus; expenses are sticky; but this is "bad news already made public", NII is at the high end, and HTM losses do not enter capital |
| **HBAN** | NII growth cut while consensus requires improvement; downgraded by several firms |
| **SCHW** | Consensus is up 6% (3 months) while we are slightly below; AOCI/TCE -43%, 21x leverage |
| **Alternative managers / mortgage / some payments** | Price and qualitative judgement only; no driver model |

---

## 6. Expected market reaction

### 6.1 Price backdrop

- XLF ±0% in Q3, -7.1% in September, 8.4% below its 52-week high. KBWB -8.1% in September, KRE -6.7% in Q3 (regionals weaker than the large banks).
- Large banks over one month: GS -10.6%, MS -10.9%, BAC -12.9%, JPM -6.1%, C -4.2%, WFC -7.8%.
- Distance from 52-week high: C -12%, JPM -9%, MS -17%, GS -22%, BAC -17%, WFC -15%.
- Tech: SMH +71.6% YTD, QQQ only 0.7% below its high. XLF is about -1% YTD.

### 6.2 Heuristic one-day move (= 2 x 60-day volatility / sqrt(252))

| GS | MS | C | WFC | JPM | BAC | USB | PNC | SCHW | FITB |
|---|---|---|---|---|---|---|---|---|---|
| ±4.5% | ±3.4% | ±3.4% | ±3.0% | ±2.3% | ±2.6% | ±2.4% | ±2.1% | ±2.9% | ±2.5% |

This is a rough proxy, not option-implied; check actual option-implied volatility before trading.

### 6.3 Our reaction calls

- **"Buy the news" more likely**: C, JPM, MS. An EPS beat + solid guidance + a 4-11% decline over the past month make relative strength more likely. But JPM's whisper is already above consensus, so there is limited room.
- **Possible "bad news already priced"**: BAC, GS. If EPS misses but NII guidance or buyback/capital guidance is good, the reaction may be milder than expected (BAC already had a -5% one-day reaction).
- **"Sell the news" risk**: STT (+38.6% YTD), BNY (+25.6%), BEN (+40.8%), IBKR.
- **Regional banks**: reactions depend more on comments about AOCI/TBV, deposit costs, CRE and NDFI exposure than on EPS itself.

---

## 7. Balance-sheet risk (`risk_scorecard.csv`)

| Ticker | TCE / assets | Leverage (x) | AOCI / TCE | Q3 incremental AFS hit / TCE | Note |
|---|---|---|---|---|---|
| BNY | 3.9% | 25.8 | -17.0% | **-10.6%** | Fallback duration used |
| KEY | 7.6% | 13.2 | -16.2% | **-8.2%** | |
| ALLY | 6.7% | 15.0 | -20.4% | -7.8% | AFS duration about 6 years |
| FITB | 7.0% | 14.3 | -15.6% | **-7.0%** | |
| NTRS | 6.5% | 15.3 | -4.7% | -6.5% | Fallback duration |
| COF | 9.0% | 11.2 | -10.4% | -5.3% | |
| RF | 7.2% | 13.9 | -16.6% | -4.8% | AFS size is an estimate |
| SCHW | 4.7% | 21.2 | **-43.4%** | -4.2% | HTM unrealised loss $9.4B, plus an additional Q3 HTM loss |
| ZION | 8.6% | 11.7 | -24.5% | -4.2% | |
| PNC | 8.2% | 12.2 | -8.1% | -3.7% | |
| WFC | 6.1% | 16.3 | -5.9% | -3.6% | AFS uses fair value in place of amortised cost; fallback duration |
| TFC | 7.5% | 13.4 | -16.2% | -3.4% | AFS size is an estimate |
| CFG | 6.8% | 14.8 | -14.3% | -3.2% | AFS size is an estimate |
| STT | 4.1% | 24.4 | -6.9% | -3.1% | |
| JPM | 6.0% | 16.7 | -2.6% | -2.7% | |
| USB | 5.8% | 17.1 | -16.8% | -2.3% | |
| MS | 5.0% | 19.9 | -7.5% | -2.1% | |
| MTB | 7.8% | 12.9 | -0.5% | -1.9% | |
| GS | 4.7% | 21.2 | -2.8% | -1.8% | Short-duration T-bills |
| BAC | 5.9% | 17.0 | -5.8% | -1.2% | HTM unrealised loss of $82B (about 40% of TCE) does not enter capital |

How to read it:

- AOCI/TCE reflects cumulative damage; the Q3 incremental hit reflects the marginal pressure this quarter.
- BAC is the textbook case: AFS duration is only about 1 year, so capital is almost unaffected, but the $82B HTM unrealised loss (plus about $14B of new loss in Q3) is a worry for "economic TBV"; it enters capital only if forced sales or reclassification occur.
- The table is a model estimate, not regulatory capital. CET1 treatment of AOCI differs by bank category (Category I-II must include it; III-IV usually opt out).

**Credit**:

- FDIC data show a net charge-off rate of 0.57% and improving delinquencies.
- NDFI / private-credit loans are about $1.7T, around 12% of bank loans, with a default rate of about 0.1% (vs. 1.4% for C&I), concentrated in PNC, USB, TFC and others.
- CRE: KEY's and HBAN's NPA ratios are up 11-13bp; office and multifamily remain the tail.

---

## 8. Historical analogues: dot-com bubble, oil shocks, wars and rate hikes

From Ken French's 48-industry monthly value-weighted returns (`historical_analogs.csv`).

| Period | Banks | Brokers / asset mgrs (Fin) | Chips | Computers | Banks - tech (mean of chips / computers / business services) |
|---|---|---|---|---|---|
| 1973.10-74.12 oil embargo + stagflation | -43% | -41% | -51% | -38% | About +3pp |
| 1979-81 Volcker + oil shock | +41% | +69% | +60% | -3% | -10pp |
| 1990.7-10 Gulf War oil shock | -35% | -30% | -27% | -26% | -9pp |
| 1998.10-2000.3 dot-com run-up | +13% | +113% | +264% | +219% | **-187pp** |
| 2000.4-2002.9 bubble burst | +4% | -40% | -84% | -83% | **+84pp** |
| 1999 rate hikes (4.75 to 5.50) | -7% | +6% | +72% | +68% | -71pp |
| 2008.1-7 oil to $147 | -21% | -28% | -12% | -16% | -7pp |
| Full-year 2022 (hikes + Ukraine) | -16% | -15% | -29% | -20% | +12pp |
| 2025.1-2026.9 AI rally | +37% | +31% | +67% | +93% | -23pp |

**What can be said**

1. The current setup most resembles 1999: tech far ahead, banks lagging, with the Fed hiking. In the 1999 hiking period banks were -7% and chips +72%.
2. In the 1999-2000 "bubble phase" banks lagged by 187 percentage points, but after the bubble burst banks outperformed by 84pp. The direction is right, but it should not be used to bet on timing.
3. During oil and war shocks (1973-74, 1990, 2008) banks fell together with tech, showing banks have no defensive character in stagflation and oil shocks. The 1979-81 Volcker period is the counter-example: banks +41%, because of wider spreads plus inflation.
4. 2022 is the most recent "hikes + energy shock" case: banks -16%, chips -29%. Banks were relatively more resilient, but absolute returns were negative.

**What cannot be said**: each episode is essentially one sample, with much overlap (oil, hikes and valuations moving together); no significance tests were run; and the industry classification (French 48) differs from today's KBW bank index. This is a "regime illustration", not a forecast.

**Differences from today**: the current 10Y is 5.3%, vs. a monthly average of about 6.3% in December 1999 (FRED GS10); the 2026 NII tailwind comes from fixed-rate assets bought in the long low-rate era repricing at maturity; the AOCI/HTM burden is a legacy of 2022 onward.

---

## 9. Investment views (scenario-based, not personalised)

**Core logic**: earnings season is a game against expectations. The expectation gaps are concentrated in C/JPM/MS (positive) and BAC/GS/HBAN (negative), while regionals as a group depend more on the 10/27-28 FOMC and the path of long-end rates.

**Tactical positioning (1-2 weeks before earnings, through each report date)**

1. **Lean long**: C, JPM, MS.
   - C has the largest "EPS gap" and the highest hit rate in the model. JPM offers lower volatility (±2.3%) and higher certainty. MS's narrative has already been hammered by "3Q is no 2Q".
   - Sizing: no more than 3-5% of the portfolio per name; set stops using the ±3-4% one-day move.
2. **Selectively long**: FITB, USB.
   - Guidance quality is high, but AOCI and consensus-basis noise is large; halve the position size.
3. **Avoid or hedge**: BAC, GS, HBAN.
   - If held, consider XLF or KBWB puts, or a pair trade long C/JPM and short BAC/GS to hedge sector beta.
   - BAC's risk is the gap between EPS and consensus; but the stock has priced it in ahead of time, so be careful shorting; pairs are better than outright shorts.
4. **Do not chase**: STT, BNY, BEN (large gains, high leverage, AOCI sensitivity).
5. **Regional banks (KRE/KBE)**: as a group 6-7pp weaker than the large banks (Q3), but the NII tailwind is real, and on the day of earnings the focus is on guidance and deposit costs. If you want exposure, pick names with high-end NII guidance and small AOCI exposure (USB, PNC, FITB, CFG) and avoid KEY (AOCI/TCE -8%).
6. **Alternative managers / mortgage**: prices have already fallen a lot (24%-79% below highs), but the catalysts are rates and private-credit valuations, not Q3 EPS. Unless you have a clear view on falling rates, Q3 earnings are not a reason to enter.

**Event calendar and triggers**

- 10/13 JPM/C/WFC/GS: watch JPM's Q4 IB/Markets comments, C's ROTCE upgrade, whether WFC raises NII guidance, and the actual size of GS's non-compensation expenses.
- 10/14 BAC/MS: BAC's NII and expense guidance; MS's wealth-management net new assets and IB pipeline.
- 10/15-16 PNC/SCHW/USB/TFC/MTB/CFG/HBAN: whether NII guidance is raised, deposit beta, private-credit and CRE comments.
- Mid-October CPI and the 10/27-28 FOMC: if the 10Y breaks 5.4%, the AOCI/TBV narrative will override earnings.

**When these views would fail**

- Capital-markets activity (IPO, M&A) in the first week of October is significantly better than the September guidance basis (Citi has already said the "last few deals" have upside).
- A credit shock: a single large loss in C&I, CRE or NDFI.
- A rapid fall in long-end rates (negative for the NII tailwind, positive for AOCI and valuations).

---

## 10. Limits of method and data quality

1. **Mixed consensus sources**: MarketBeat, TickerLeague, Benzinga, Hudson Labs, Barchart, MarketWatch, with inconsistent basis (GAAP vs. adjusted) and update times. GS consensus ranges from $13.76 to $16.54, and BAC's revenue basis does not reconcile to SEC data. Ranges are kept in the CSV. TFC consensus is single-source.
2. **The model depends on management guidance and drivers I set by hand**; it is not a valuation model. The standard deviations are judgement values, not calibrated from history, so P(beat) is sensitive to assumptions, especially for BAC (the S&T / NII overlap) and GS (the actual size of the investing lines).
3. **Q2 base**: JPM's clean EPS uses the public $6.14; for C, MS, WFC and GS we assume no Q2 adjustment is needed (no disclosed one-offs were found); if there are any, the model is systematically too high.
4. **Duration regression**: based on 15-21 quarters regressed on a single benchmark rate; for some banks the AFS figures are estimates (flagged `est`/`fallback`), and HBAN and C are not in the capital table because XBRL data are missing.
5. **The heuristic volatility ranges** are not option-implied volatility.
6. **Historical analogues** are regime comparisons, not forecasts.
7. **Not included**: the sell side's detailed bridge for each line item, actual option skew, positioning data (13F, short interest), and non-public channel information, which are unavailable in this environment.
8. **A premise not re-verified this time**: "Q3 IPOs cooled excluding mega deals, announced M&A volume about -41% QoQ" comes from earlier searches; this time it was only cross-checked against management commentary from BAC/C/JPM/PNC.
9. **Timeliness**: all data are as of 2026-10-02. Some reporting dates are estimates (MarketBeat notes "based on past reporting schedules"); please rely on company announcements.

---

## Appendix: files

| File | Content |
|---|---|
| `research/scripts/fetch_macro.py`, `macro_analysis.py` | FRED macro series and quarterly analysis |
| `research/scripts/fetch_sec_facts*.py`, `build_quarterly.py`, `fetch_filing_reports.py`, `fetch_rate_sensitivity.py` | SEC EDGAR XBRL and 10-Q table/text extraction |
| `research/scripts/duration_engine.py` | Empirical duration regression |
| `research/scripts/fetch_prices.py`, `price_analysis.py` | Prices and statistics |
| `research/scripts/baseline_panel.py` | Q2 base panel |
| `research/scripts/q3_model.py` | EPS bridge + Monte Carlo |
| `research/scripts/risk_scorecard.py` | TCE, leverage, AOCI scenarios |
| `research/scripts/summary_table.py` | Composite ranking |
| `research/scripts/historical_analogs.py` | Historical analogues |
| `research/output/*.csv` | All outputs |
| `research/data/consensus_q3_2026.csv` | Consensus and sources |
