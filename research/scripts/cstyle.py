"""Shared plotting style. Every chart is rendered once per language: pick text with L(zh, en)."""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager as fm  # noqa: E402

BASE = os.path.join(os.path.dirname(__file__), "..")
FIGDIR = os.path.join(BASE, "output", "charts")

for p in ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",):
    if os.path.exists(p):
        fm.fontManager.addfont(p)

plt.rcParams.update({
    "font.family": ["WenQuanYi Micro Hei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "text.parse_math": False,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.6,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "legend.frameon": False,
    "figure.dpi": 100,
    "savefig.dpi": 170,
    "savefig.bbox": "tight",
})

C_NII = "#1f4e79"
C_IB = "#e07b00"
C_TRD = "#2e8b57"
C_OTH = "#9aa5b1"
C_UP = "#c0392b"
C_DN = "#2e7d32"
C_FC = "#6c3483"
BANK_COL = {"JPM": "#1f4e79", "BAC": "#c0392b", "C": "#2e86c1", "WFC": "#b7950b", "GS": "#6c3483", "MS": "#117a65"}
CURVE_COL = ["#bdc3c7", "#95a5a6", "#7f8c8d", "#2e86c1", "#c0392b"]


class Lang:
    def __init__(self, code: str):
        self.code = code

    def __call__(self, zh: str, en: str) -> str:
        return zh if self.code == "zh" else en


def save(fig, lang: Lang, name: str) -> str:
    d = os.path.join(FIGDIR, lang.code)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{name}.png")
    fig.savefig(p)
    plt.close(fig)
    return p


def footer(fig, text: str, y=-0.02):
    fig.text(0.01, y, text, fontsize=7.5, color="#555555", ha="left", va="top", wrap=True)
