"""Collapse raw XBRL facts into a clean per-ticker quarterly panel.

Two traps this handles:
  1. A 10-Q tags both the 3-month and the year-to-date duration for the same tag.
     We keep only durations of 80-100 days.
  2. The same period gets re-filed (restatements, comparatives in later filings).
     We keep the value from the *latest* filing date.
"""

import os
import re

import numpy as np
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..", "data", "sec")
RAW = os.path.join(BASE, "facts")
OUT = os.path.join(BASE, "quarterly")
os.makedirs(OUT, exist_ok=True)

MONEY = {"USD"}
PERSHARE = {"USD/shares"}


def quarter_label(end: pd.Timestamp) -> str:
    return f"{end.year}Q{(end.month - 1) // 3 + 1}"


def build(tkr: str) -> pd.DataFrame | None:
    path = os.path.join(RAW, f"{tkr}.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, low_memory=False)
    if df.empty:
        return None
    df["end"] = pd.to_datetime(df["end"], errors="coerce")
    df["start"] = pd.to_datetime(df["start"], errors="coerce")
    df["filed"] = pd.to_datetime(df["filed"], errors="coerce")
    df = df.dropna(subset=["end", "val"])

    is_dur = df["start"].notna()
    days = (df["end"] - df["start"]).dt.days

    # flow items: strictly quarterly windows
    flows = df[is_dur & days.between(80, 100)].copy()
    # stock items: point-in-time
    stocks = df[~is_dur].copy()

    # only keep period-ends that sit on a fiscal quarter boundary (allow +/- 7 days
    # so that 52/53-week filers and Sep-30 fiscal years still line up)
    def on_boundary(ts: pd.Series) -> pd.Series:
        qe = ts.dt.to_period("Q").dt.end_time.dt.normalize()
        return (ts - qe).dt.days.abs() <= 7

    flows = flows[on_boundary(flows["end"])]
    stocks = stocks[on_boundary(stocks["end"])]

    frames = []
    for part in (flows, stocks):
        if part.empty:
            continue
        part = part[part["unit"].isin(MONEY | PERSHARE | {"shares", "pure"})]
        part = part.sort_values("filed")
        part["q"] = part["end"].map(quarter_label)
        # last filed wins
        part = part.drop_duplicates(subset=["tag", "unit", "q"], keep="last")
        frames.append(part[["q", "end", "tag", "unit", "val", "form", "filed"]])

    if not frames:
        return None
    allp = pd.concat(frames)
    wide = allp.pivot_table(index="q", columns="tag", values="val", aggfunc="last")
    wide = wide.reindex(sorted(wide.index, key=lambda x: (int(x[:4]), int(x[-1]))))
    wide.insert(0, "ticker", tkr)
    return wide


def main() -> None:
    import json
    uni = json.load(open(os.path.join(BASE, "universe.json")))
    report = []
    for tkr in sorted(uni["cik"]):
        w = build(tkr)
        if w is None:
            print(f"{tkr:6s} no data")
            continue
        w.to_csv(os.path.join(OUT, f"{tkr}.csv"))
        recent = w.loc[[q for q in w.index if q >= "2025Q1"]]
        have = recent.notna().sum(axis=1).to_dict()
        report.append((tkr, len(w), list(w.index)[-1], have.get("2026Q2", 0)))
        print(f"{tkr:6s} quarters={len(w):4d}  last={list(w.index)[-1]}  tags_in_2026Q2={have.get('2026Q2',0)}")
    print(f"\n{len(report)} tickers written to {OUT}")


if __name__ == "__main__":
    main()
