# =============================================================================
# OsdagBridge — Report charts (matplotlib)
# =============================================================================
"""Bar charts generated while the report is being built.

* Utilization-ratio (UR = Demand / Capacity) summaries for Section 5.5.
* Material-quantity summaries for Chapter 7.

Each function writes one image into the temporary asset directory of the
report build and returns its path; the chapter embeds it with a PyLaTeX
``Figure`` (see :mod:`figures`). The image files disappear together with the
temporary build directory once the PDF has been compiled.

Colours, sizes, fonts and the threshold-line look are read from
``styles.CHART`` / ``styles.COLORS``.

The charts are drawn with matplotlib's object-oriented API on an Agg canvas
(no ``pyplot``, no global rcParams), so they are safe to create from the
background thread the desktop application uses for report generation.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from . import styles as S

C = S.CHART
_col = S.COLORS.mpl


@dataclass
class URItem:
    """Utilization ratio of one design check of one structural element."""

    element: str            # key of ``styles.CHART.element_colors``
    check: str              # short check name, e.g. "Moment"
    ur: Optional[float]     # None when the check was not evaluated


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _new_figure(size: Tuple[float, float]):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    fig = Figure(figsize=size, dpi=C.dpi)
    FigureCanvasAgg(fig)
    return fig, fig.add_subplot(111)


def _font(size: float, weight: str = "normal") -> Dict[str, object]:
    return {"fontfamily": C.font_family, "fontsize": size, "fontweight": weight}


def _value_label(ax, text: str, x: float, y: float) -> None:
    """Value printed above a bar, on a white pad so grid / limit lines do not cross it."""
    ax.annotate(text, (x, y), xytext=(0, 3), textcoords="offset points",
                ha="center", va="bottom", color=_col("rptText"), zorder=6,
                bbox={"boxstyle": "round,pad=0.12", "facecolor": "white", "edgecolor": "none",
                      "alpha": C.label_pad_alpha},
                **_font(C.annotation_size, "bold"))


def _style_axes(ax, y_label: str, title: Optional[str] = None) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(_col("rptRule"))
        ax.spines[side].set_linewidth(0.7)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=_col(C.grid_color), linewidth=C.grid_width)
    ax.tick_params(axis="both", labelsize=C.tick_size, colors=_col("rptText"), length=3)
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontfamily(C.font_family)
    ax.set_ylabel(y_label, color=_col("rptText"), **_font(C.label_size))
    if title:
        ax.set_title(title, color=_col("rptText"), pad=8, **_font(C.title_size, "bold"))


def _save(fig, out_dir: str, name: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{name}.{C.image_format}")
    fig.tight_layout()
    # A tight bounding box removes the empty band a legend placed below the
    # axes would otherwise leave between the chart and its caption.
    fig.savefig(path, dpi=C.dpi, facecolor="white", bbox_inches="tight", pad_inches=C.pad_inches)
    return path


def _valid(items: Sequence[URItem]) -> List[URItem]:
    out = []
    for it in items:
        try:
            if it.ur is not None:
                out.append(URItem(it.element, it.check, float(it.ur)))
        except (TypeError, ValueError):
            continue
    return out


def _draw_threshold(ax, top: float) -> None:
    """Red dashed UR = 1.0 line; the failing region above it is tinted."""
    ax.axhspan(C.threshold_value, top, color=_col(C.fail_color), alpha=0.05, linewidth=0)
    ax.axhline(C.threshold_value, color=_col(C.threshold_color),
               linestyle=C.threshold_style, linewidth=C.threshold_width, zorder=4)


def _ur_bars(ax, xs, values, colors) -> None:
    for x, v, color in zip(xs, values, colors):
        failing = v > C.threshold_value
        ax.bar(x, v, width=C.bar_width,
               color=_col(C.fail_color) if failing else color,
               hatch=C.fail_hatch if failing else None,
               edgecolor=_col(C.bar_edge_color), linewidth=C.bar_edge_width, zorder=3)
        _value_label(ax, f"{v:.2f}", x, v)


def _ur_legend(ax, elements: Sequence[str], any_fail: bool, **kwargs) -> None:
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    handles = [Patch(facecolor=_col(C.element_colors[e]), edgecolor=_col(C.bar_edge_color),
                     linewidth=C.bar_edge_width, label=e) for e in elements]
    if any_fail:
        handles.append(Patch(facecolor=_col(C.fail_color), hatch=C.fail_hatch,
                             edgecolor=_col(C.bar_edge_color), linewidth=C.bar_edge_width,
                             label="UR > 1.0 (fails)"))
    handles.append(Line2D([0], [0], color=_col(C.threshold_color), linestyle=C.threshold_style,
                          linewidth=C.threshold_width, label=C.threshold_label))
    ax.legend(handles=handles, frameon=False,
              prop={"family": C.font_family, "size": C.tick_size}, **kwargs)


# ---------------------------------------------------------------------------
# Section 5.5 — utilization ratio charts
# ---------------------------------------------------------------------------

def governing_by_element(items: Sequence[URItem]) -> Dict[str, Optional[URItem]]:
    """Governing (largest-UR) check of every primary element, in chart order."""
    valid = _valid(items)
    out: Dict[str, Optional[URItem]] = {}
    for element in C.element_colors:
        mine = [it for it in valid if it.element == element]
        out[element] = max(mine, key=lambda it: it.ur) if mine else None
    return out


def utilization_by_element_chart(items: Sequence[URItem], out_dir: str,
                                 name: str = "chart_ur_by_element") -> Optional[str]:
    """Governing UR of each primary element (girders, deck, bracing, diaphragms)."""
    governing = governing_by_element(items)
    if not any(governing.values()):
        return None

    fig, ax = _new_figure(C.size_wide)
    elements = list(governing)
    top = max([C.ur_axis_min_top] + [g.ur * 1.18 for g in governing.values() if g])
    _draw_threshold(ax, top)

    labels = []
    for x, element in enumerate(elements):
        item = governing[element]
        if item is None:
            ax.text(x, 0.04 * top, "not evaluated", ha="center", va="bottom",
                    color=_col("rptMuted"), fontstyle="italic", **_font(C.annotation_size))
            labels.append(element)
            continue
        _ur_bars(ax, [x], [item.ur], [_col(C.element_colors[element])])
        labels.append(f"{element}\n({item.check})")

    ax.set_xticks(range(len(elements)))
    ax.set_xticklabels(labels)
    ax.set_xlim(-0.6, len(elements) - 0.4)
    ax.set_ylim(0, top)
    _style_axes(ax, "Utilization Ratio (Demand / Capacity)",
                "Governing Utilization Ratio by Structural Element")
    any_fail = any(g and g.ur > C.threshold_value for g in governing.values())
    _ur_legend(ax, [], any_fail, loc="upper right", ncol=2)
    return _save(fig, out_dir, name)


def utilization_by_check_chart(items: Sequence[URItem], out_dir: str,
                               name: str = "chart_ur_by_check") -> Optional[str]:
    """UR of every design check, coloured by the element it belongs to."""
    valid = _valid(items)
    if not valid:
        return None

    fig, ax = _new_figure(C.size_tall)
    top = max([C.ur_axis_min_top] + [it.ur * 1.15 for it in valid])
    _draw_threshold(ax, top)

    xs = list(range(len(valid)))
    _ur_bars(ax, xs, [it.ur for it in valid],
             [_col(C.element_colors.get(it.element, "chartGirder")) for it in valid])

    ax.set_xticks(xs)
    ax.set_xticklabels([it.check for it in valid], rotation=38, ha="right",
                       rotation_mode="anchor")
    ax.set_xlim(-0.7, len(valid) - 0.3)
    ax.set_ylim(0, top)
    _style_axes(ax, "Utilization Ratio (Demand / Capacity)",
                "Utilization Ratio of All Design Checks")

    # Light separators between the element groups.
    for i in range(1, len(valid)):
        if valid[i].element != valid[i - 1].element:
            ax.axvline(i - 0.5, color=_col(C.grid_color), linewidth=0.8, zorder=1)

    present = [e for e in C.element_colors if any(it.element == e for it in valid)]
    any_fail = any(it.ur > C.threshold_value for it in valid)
    _ur_legend(ax, present, any_fail, loc="upper center",
               bbox_to_anchor=(0.5, -0.42), ncol=3)
    return _save(fig, out_dir, name)


# ---------------------------------------------------------------------------
# Chapter 7 — material quantity charts
# ---------------------------------------------------------------------------

def steel_tonnage_chart(tonnage: Dict[str, Optional[float]], out_dir: str,
                        name: str = "chart_steel_tonnage") -> Optional[str]:
    """Structural steel tonnage by component (girders, bracing, diaphragms)."""
    data = [(k, float(v)) for k, v in tonnage.items() if v is not None]
    if not data or not any(v > 0 for _, v in data):
        return None

    fig, ax = _new_figure(C.size_half)
    total = sum(v for _, v in data)
    for x, (label, value) in enumerate(data):
        ax.bar(x, value, width=C.bar_width,
               color=_col(C.material_colors.get(label, "chartGirder")),
               edgecolor=_col(C.bar_edge_color), linewidth=C.bar_edge_width, zorder=3)
        share = (100.0 * value / total) if total > 0 else 0.0
        _value_label(ax, f"{value:.2f} MT\n({share:.0f}%)", x, value)
    ax.set_xticks(range(len(data)))
    ax.set_xticklabels([k for k, _ in data])
    ax.set_xlim(-0.6, len(data) - 0.4)
    ax.set_ylim(0, max(v for _, v in data) * 1.28)
    _style_axes(ax, "Structural Steel Weight (MT)",
                f"Structural Steel Tonnage by Component (total {total:.2f} MT)")
    return _save(fig, out_dir, name)


def concrete_vs_rebar_chart(concrete_m3: Optional[float], rebar_mt: Optional[float],
                            out_dir: str,
                            name: str = "chart_concrete_rebar") -> Optional[str]:
    """Deck concrete volume (m³, left axis) against reinforcement weight (MT, right axis)."""
    if not concrete_m3 or not rebar_mt:
        return None
    concrete_m3, rebar_mt = float(concrete_m3), float(rebar_mt)

    fig, ax = _new_figure(C.size_half)
    ax2 = ax.twinx()
    c_conc = _col(C.material_colors["Concrete"])
    c_bar = _col(C.material_colors["Reinforcement"])

    ax.bar(0, concrete_m3, width=C.bar_width, color=c_conc,
           edgecolor=_col(C.bar_edge_color), linewidth=C.bar_edge_width, zorder=3)
    ax2.bar(1, rebar_mt, width=C.bar_width, color=c_bar,
            edgecolor=_col(C.bar_edge_color), linewidth=C.bar_edge_width, zorder=3)
    _value_label(ax, f"{concrete_m3:.2f} m³", 0, concrete_m3)
    _value_label(ax2, f"{rebar_mt:.2f} MT", 1, rebar_mt)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Concrete Volume (m³)", "Reinforcement Steel (MT)"])
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylim(0, concrete_m3 * 1.25)
    ax2.set_ylim(0, rebar_mt * 1.25)

    ratio = rebar_mt * 1000.0 / concrete_m3
    _style_axes(ax, "Concrete Volume (m³)",
                f"Deck Concrete vs. Reinforcement Steel ({ratio:.0f} kg of steel per m³)")
    ax.yaxis.label.set_color(c_conc)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_color(_col("rptRule"))
    ax2.spines["right"].set_linewidth(0.7)
    ax2.tick_params(axis="y", labelsize=C.tick_size, colors=_col("rptText"), length=3)
    for lbl in ax2.get_yticklabels():
        lbl.set_fontfamily(C.font_family)
    ax2.set_ylabel("Reinforcement Steel Weight (MT)", color=c_bar, **_font(C.label_size))
    return _save(fig, out_dir, name)
