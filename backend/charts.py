"""Local matplotlib chart renderers (Agg backend) for the Bazzar Terminal.

Dark terminal theme:
  background  #000000 (black)
  panel/grid  #111827 / #1f2937
  accents     #eab308 (gold)
  candles     up #22c55e (green) / down #ef4444 (red)

Charts are rendered to PNG under the chart cache dir (<data dir>/charts) and
served by backend.server. No TradingView / lightweight-charts anywhere.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

import matplotlib

matplotlib.use("Agg")  # headless rendering only

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from .db import get_data_dir

# --- theme -----------------------------------------------------------------
BG = "#000000"
PANEL = "#111827"
GRID = "#1f2937"
GOLD = "#eab308"
UP = "#22c55e"
DOWN = "#ef4444"
TEXT = "#d1d5db"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": PANEL,
    "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT,
    "text.color": TEXT,
    "xtick.color": TEXT,
    "ytick.color": TEXT,
    "grid.color": GRID,
    "font.size": 9,
    "savefig.facecolor": BG,
})


def chart_cache_dir() -> Path:
    """Chart cache directory under the data dir; created on demand."""
    path = get_data_dir() / "charts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _as_date(value: Any) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    return dt.date.fromisoformat(str(value)[:10])


def _style(ax, title: str) -> None:
    ax.set_title(title, color=GOLD, fontsize=11, loc="left", pad=8)
    ax.grid(True, linewidth=0.5, alpha=0.7)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(length=0)


def render_candles_png(rows: Iterable[dict], title: str, out_path: str) -> str:
    """Render daily OHLC rows to a candlestick PNG.

    rows: iterable of dicts with keys date, open, high, low, close
          (volume is used for a sub-panel when present).
    Returns the output PNG path.
    """
    bars = sorted(rows, key=lambda r: str(r["date"]))
    if not bars:
        raise ValueError("no rows to render")

    dates = [_as_date(b["date"]) for b in bars]
    opens = [float(b["open"]) for b in bars]
    highs = [float(b["high"]) for b in bars]
    lows = [float(b["low"]) for b in bars]
    closes = [float(b["close"]) for b in bars]
    volumes: list[Optional[float]] = [
        float(b["volume"]) if b.get("volume") is not None else None for b in bars
    ]
    has_volume = any(v is not None for v in volumes)

    if has_volume:
        fig, (ax, axv) = plt.subplots(
            2, 1, figsize=(10, 6), sharex=True,
            gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05},
        )
    else:
        fig, ax = plt.subplots(figsize=(10, 5.4))
        axv = None

    xs = list(range(len(bars)))
    width = 0.7
    for x, o, h, l, c in zip(xs, opens, highs, lows, closes):
        color = UP if c >= o else DOWN
        ax.vlines(x, l, h, color=color, linewidth=0.8, zorder=2)
        body_low, body_high = min(o, c), max(o, c)
        if body_high - body_low < 1e-12:
            body_high = body_low + max(abs(body_low), 1.0) * 1e-4
        ax.add_patch(Rectangle((x - width / 2, body_low), width,
                               body_high - body_low,
                               facecolor=color, edgecolor=color, zorder=3))
    _style(ax, title)
    ax.set_xlim(-1, len(bars))
    ax.margins(y=0.08)

    tick_step = max(1, len(bars) // 8)
    tick_pos = xs[::tick_step]
    tick_labels = [dates[i].isoformat() for i in tick_pos]

    if axv is not None:
        axv.bar(xs, [v or 0.0 for v in volumes], width=width,
                color=[UP if c >= o else DOWN for o, c in zip(opens, closes)],
                alpha=0.6)
        axv.grid(True, linewidth=0.5, alpha=0.7)
        axv.tick_params(length=0)
        for spine in axv.spines.values():
            spine.set_color(GRID)
        axv.set_xticks(tick_pos)
        axv.set_xticklabels(tick_labels, rotation=30, ha="right")
        ax.set_xticks([])
    else:
        ax.set_xticks(tick_pos)
        ax.set_xticklabels(tick_labels, rotation=30, ha="right")

    last = closes[-1]
    ax.axhline(last, color=GOLD, linewidth=0.7, alpha=0.6, linestyle="--")
    ax.annotate(f"{last:,.2f}", xy=(len(bars) - 1, last), color=GOLD,
                fontsize=8, xytext=(4, 0), textcoords="offset points", va="center")

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return str(out)


def render_line_png(points: Sequence[tuple], title: str, unit: str, out_path: str,
                    series_labels: Optional[Sequence[str]] = None) -> str:
    """Render one or more line series to a PNG.

    points: either [(date, value), ...] for a single series, or a list of
            series each being [(date, value), ...] when series_labels given.
    unit: y-axis unit label (e.g. "%", "USD bn").
    Returns the output PNG path.
    """
    if series_labels is not None:
        series_list = [sorted(s, key=lambda p: str(p[0])) for s in points]  # type: ignore[arg-type]
    else:
        series_list = [sorted(points, key=lambda p: str(p[0]))]
    if not any(series_list):
        raise ValueError("no points to render")

    fig, ax = plt.subplots(figsize=(10, 5.4))
    palette = [GOLD, UP, "#38bdf8", DOWN, "#a78bfa", "#f472b6"]
    for i, series in enumerate(series_list):
        if not series:
            continue
        xs = [mdates.date2num(_as_date(p[0])) for p in series]
        ys = [float(p[1]) for p in series]
        label = series_labels[i] if series_labels is not None else None
        ax.plot(xs, ys, color=palette[i % len(palette)], linewidth=1.4, label=label)
        ax.annotate(f"{ys[-1]:,.2f}", xy=(xs[-1], ys[-1]),
                    color=palette[i % len(palette)], fontsize=8,
                    xytext=(4, 0), textcoords="offset points", va="center")

    _style(ax, title)
    if unit:
        ax.set_ylabel(unit)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=8))
    fig.autofmt_xdate(rotation=30)
    if series_labels is not None:
        ax.legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT, fontsize=8)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return str(out)
