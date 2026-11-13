# =============================================================================
# Chapter 4: Analysis Results
# Presentation only — values come from the analysis summary / output
# dictionary, formatting from styles.py via tables.py / figures.py.
# =============================================================================
import re

from osdagbridge.core.utils.common import (
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
)

from . import figures as F
from . import styles as S
from . import tables as T
from .report_utils import _tex, fmt_num

U = S.UNITS


def _is_moving(name: str) -> bool:
    """Per-position moving-load cases are not listed (only their envelopes)."""
    n = name.lower()
    return "moving" in n or " pos_" in n


def _natural_key(name: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def _grouped_cases(names):
    """Load cases in report order: basic cases, combinations, envelopes."""
    basic, combos, envelopes = [], [], []
    for name in names:
        if name.lower().startswith("envelope"):
            envelopes.append(name)
        elif ":" in name:
            combos.append(name)
        else:
            basic.append(name)
    return [
        ("Basic load cases", sorted(basic, key=_natural_key)),
        ("Load combinations (IRC 6)", sorted(combos, key=_natural_key)),
        ("Envelopes", sorted(envelopes, key=_natural_key)),
    ]


def _girder(value):
    text = str(value or "").strip()
    return None if text in ("", "-", "—", "–", "---") else _tex(text)


def _demand_table(load_cases: dict) -> str:
    rows = []
    for title, names in _grouped_cases(load_cases):
        if not names:
            continue
        rows.append(T.Band(title))
        for name in names:
            d = load_cases.get(name) or {}
            rows.append((
                _tex(name),
                fmt_num(d.get("max_bm"), 2), _girder(d.get("bm_girder")), fmt_num(d.get("bm_location"), 2),
                fmt_num(d.get("max_sf"), 2), _girder(d.get("sf_girder")), fmt_num(d.get("sf_location"), 2),
            ))
    if not rows:
        rows = [(T.Merged("No analysis results are available", 7, align="|c"),)]
    return T.table(
        "Summary of Maximum Demands", "analysis_demands",
        ("Load Case / Combination",
         T.Span("Bending Moment", ("Max (" + U.kNm + ")", "Girder", "Location (m)")),
         T.Span("Shear Force", ("Max (" + U.kN + ")", "Girder", "Location (m)"))),
        rows,
        note="Location is measured from the left support along the span.",
        label="tab:maximum-demands",
    )


def _reaction_table(reactions: dict) -> str:
    rows = []
    for title, names in _grouped_cases(reactions):
        if not names:
            continue
        rows.append(T.Band(title))
        for name in names:
            r = reactions.get(name) or {}
            rows.append((_tex(name), fmt_num(r.get("left_kN"), 2), fmt_num(r.get("right_kN"), 2)))
    if not rows:
        rows = [(T.Merged("No support reactions are available", 3, align="|c"),)]
    return T.table(
        "Reactions at Supports", "reactions",
        ("Load Case / Combination", "Left Support (" + U.kN + ")", "Right Support (" + U.kN + ")"),
        rows,
        note="Total vertical reaction of each support line, in the sign convention of the grillage model.",
        label="tab:support-reactions",
    )


def _deflection_table(bridge) -> str:
    span_m = float(bridge.input_dict.get(KEY_SPAN, 0) or 0)
    try:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1) or 1)
    except (TypeError, ValueError):
        n = 1

    def governing(key):
        values = []
        for i in range(1, n + 1):
            try:
                values.append(float(bridge.output_dict.get(f"{key}.G{i}")))
            except (TypeError, ValueError):
                continue
        return max(values) if values else None

    def row(label, value, divisor):
        allowable = span_m * 1000.0 / divisor if span_m else None
        return (label, fmt_num(value, 3),
                (f"L/{divisor} = " + fmt_num(allowable, 1)) if allowable else None,
                S.pass_fail(None if value is None or allowable is None else value <= allowable))

    return T.table(
        "Deflection Summary (Live Load and Total Load)", "deflection_summary",
        ("Deflection", "Computed (mm)", "Allowable (mm)", "Status"),
        [
            row(r"Due to Live Load, $\delta_{LL}$", governing(KEY_SD_DEFL_LIVE), 800),
            row(r"Due to Total Load, $\delta_{total}$", governing(KEY_SD_DEFL_TOTAL), 600),
        ],
        note="Governing (largest) deflection of all girders; limits per IRC 22 Cl. 604.3.2.",
    )


def ch4_analysis(asum, fig_paths, bridge, span_m=None):
    asum = asum or {}
    load_cases = {k: v for k, v in (asum.get('load_cases') or {}).items() if not _is_moving(k)}
    reactions = {k: v for k, v in (asum.get('reactions') or {}).items() if not _is_moving(k)}

    return "\n".join([
        r"\chapter{Analysis Results}",
        "",
        "A grillage model was used for structural analysis. The deck is idealized as a grid of elastic beam "
        "elements --- longitudinal members represent the composite steel girders with effective slab, and "
        "transverse members represent the slab or cross frames. This section summarizes the critical output "
        "from that analysis.",
        "",
        r"\section{Maximum Demands}",
        r"\label{sec:maximum-demands}",
        _demand_table(load_cases),
        r"\section{Support Reactions}",
        r"\label{sec:support-reactions}",
        _reaction_table(reactions),
        r"\section{Deflections}",
        r"\label{sec:deflections}",
        _deflection_table(bridge),
        r"\rptfiguresection{Analysis Diagrams}",
        r"\label{sec:analysis-diagrams}",
        F.figure(fig_paths.get('bm_envelope'),
                 "Bending moment envelope (Envelope ULS): maximum / minimum bending moment (kN-m) along the "
                 "span, measured from the left support (m)", width="medium", label="fig:bm-envelope"),
        F.figure(fig_paths.get('sf_envelope'),
                 "Shear force envelope (Envelope ULS): maximum / minimum shear force (kN) along the span, "
                 "measured from the left support (m)", width="medium", label="fig:sf-envelope"),
        F.figure(fig_paths.get('defl_ll'),
                 "Vertical deflection $D_y$ under live load (1.0 LL): deflected shape of the grillage, "
                 "isometric view", width="medium", label="fig:defl-ll"),
    ]) + "\n"
