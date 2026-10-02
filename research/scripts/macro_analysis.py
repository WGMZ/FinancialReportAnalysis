"""Turn the raw FRED pulls into the quarter-over-quarter deltas that drive bank P&L."""

import os

import pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "data", "fred")


def s(sid: str) -> pd.Series:
    df = pd.read_csv(os.path.join(D, f"{sid}.csv"), parse_dates=["date"])
    return df.set_index("date")[sid]


def qavg(ser: pd.Series, start: str, end: str) -> float:
    return ser.loc[start:end].mean()


def qend(ser: pd.Series, end: str) -> float:
    sub = ser.loc[:end]
    return sub.iloc[-1] if len(sub) else float("nan")


QUARTERS = {
    "Q3-25": ("2025-07-01", "2025-09-30"),
    "Q4-25": ("2025-10-01", "2025-12-31"),
    "Q1-26": ("2026-01-01", "2026-03-31"),
    "Q2-26": ("2026-04-01", "2026-06-30"),
    "Q3-26": ("2026-07-01", "2026-09-30"),
}

RATES = ["DFF", "SOFR", "DGS3MO", "DGS2", "DGS5", "DGS10", "DGS30",
         "T10Y2Y", "T10Y3M", "MORTGAGE30US", "BAMLH0A0HYM2", "BAMLC0A0CM",
         "VIXCLS", "DCOILWTICO", "DCOILBRENTEU", "SP500", "NASDAQCOM", "DFII10"]

print("=" * 108)
print("QUARTERLY AVERAGES  (the level that sets accrual income)")
print("=" * 108)
rows = {}
for sid in RATES:
    ser = s(sid)
    rows[sid] = {q: qavg(ser, a, b) for q, (a, b) in QUARTERS.items()}
avg = pd.DataFrame(rows).T
avg["Q3vQ2"] = avg["Q3-26"] - avg["Q2-26"]
avg["Q3vQ3_yoy"] = avg["Q3-26"] - avg["Q3-25"]
print(avg.round(2).to_string())

print()
print("=" * 108)
print("QUARTER-END LEVELS  (the level that sets AOCI / mark-to-market / balance-sheet optics)")
print("=" * 108)
rows = {}
for sid in RATES:
    ser = s(sid)
    rows[sid] = {q: qend(ser, b) for q, (a, b) in QUARTERS.items()}
eop = pd.DataFrame(rows).T
eop["Q3vQ2"] = eop["Q3-26"] - eop["Q2-26"]
print(eop.round(2).to_string())

print()
print("=" * 108)
print("THE CURVE: 2026-06-30 vs 2026-09-30  (parallel shift? twist? -> duration-gap P&L)")
print("=" * 108)
tenors = {"DGS1MO": 1 / 12, "DGS3MO": 0.25, "DGS6MO": 0.5, "DGS1": 1, "DGS2": 2,
          "DGS3": 3, "DGS5": 5, "DGS7": 7, "DGS10": 10, "DGS20": 20, "DGS30": 30}
curve = {}
for sid, yrs in tenors.items():
    ser = s(sid)
    curve[sid] = {
        "yrs": yrs,
        "2025-09-30": qend(ser, "2025-09-30"),
        "2026-03-31": qend(ser, "2026-03-31"),
        "2026-06-30": qend(ser, "2026-06-30"),
        "2026-09-30": qend(ser, "2026-09-30"),
    }
cv = pd.DataFrame(curve).T
cv["Q3_shift_bp"] = (cv["2026-09-30"] - cv["2026-06-30"]) * 100
cv["YTD_shift_bp"] = (cv["2026-09-30"] - cv["2025-09-30"]) * 100
print(cv.round(2).to_string())

print()
print("=" * 108)
print("FED PATH: where did the policy rate actually go?")
print("=" * 108)
dff = s("DFF")
m = dff.resample("MS").mean()
print(m.loc["2025-01-01":].round(3).to_string())

print()
print("=" * 108)
print("INFLATION (YoY %)")
print("=" * 108)
for sid in ["CPIAUCSL", "CPILFESL", "PCEPILFE"]:
    ser = s(sid)
    yoy = (ser / ser.shift(12) - 1) * 100
    print(f"\n{sid}:")
    print(yoy.loc["2025-09-01":].round(2).to_string())

print()
print("=" * 108)
print("BANK SYSTEM AGGREGATES (H.8, $bn) and growth")
print("=" * 108)
for sid in ["TOTLL", "DPSACBW027SBOG", "CCLACBW027SBOG", "TOTBKCR"]:
    ser = s(sid)
    now = ser.iloc[-1]
    q_ago = ser.loc[:"2026-06-30"].iloc[-1]
    y_ago = ser.loc[:"2025-09-30"].iloc[-1]
    print(f"{sid:18s} last={now:12,.1f}  QoQ={now/q_ago-1:+7.2%}  YoY={now/y_ago-1:+7.2%}")

# Loan/deposit ratio trajectory
loans, deps = s("TOTLL"), s("DPSACBW027SBOG")
ldr = (loans / deps.reindex(loans.index).ffill() * 100).dropna()
print("\nSystem loan/deposit ratio (%), quarter-ends:")
for q, (a, b) in QUARTERS.items():
    print(f"  {q}: {qend(ldr, b):.2f}")

print()
print("=" * 108)
print("CREDIT QUALITY (quarterly, FRED lags one quarter)")
print("=" * 108)
for sid in ["DRCCLACBS", "DRCLACBS", "DRBLACBS", "DRCRELEXFACBS", "DRALACBN"]:
    ser = s(sid)
    print(f"\n{sid}:")
    print(ser.loc["2024-01-01":].round(2).to_string())

print()
print("=" * 108)
print("EQUITY MARKET LEVELS — drives AUM-based fees (avg balance matters, not just EOP)")
print("=" * 108)
for sid in ["SP500", "NASDAQCOM"]:
    ser = s(sid)
    print(f"\n{sid}: Q2-26 avg={qavg(ser,'2026-04-01','2026-06-30'):,.0f}  "
          f"Q3-26 avg={qavg(ser,'2026-07-01','2026-09-30'):,.0f}  "
          f"QoQ avg={qavg(ser,'2026-07-01','2026-09-30')/qavg(ser,'2026-04-01','2026-06-30')-1:+.2%}  "
          f"Q2 EOP={qend(ser,'2026-06-30'):,.0f}  Q3 EOP={qend(ser,'2026-09-30'):,.0f}  "
          f"EOP QoQ={qend(ser,'2026-09-30')/qend(ser,'2026-06-30')-1:+.2%}")
