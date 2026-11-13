# =============================================================================
# Chapter 7: Material Take-off & Quantity Summary
# Presentation only — quantities come from core/boq/boq_generator.py,
# formatting from styles.py via tables.py / figures.py / charts.py.
# =============================================================================
"""Bill of materials, quantity summary and the material-quantity bar charts."""

from typing import Optional

from . import charts
from . import figures as F
from . import styles as S
from . import tables as T
from .report_utils import fmt_num

U = S.UNITS
NA = S.TEXT.not_applicable

# (serial no., description, key prefix in the BOQ dictionary)
_BOM_ITEMS = (
    ("1",    "Structural Steel (IS 2062) for Girders",   "steel_girders"),
    ("2(a)", "Cross Bracing --- Top Chord",              "bracing_top"),
    ("2(b)", "Cross Bracing --- Bottom Chord",           "bracing_bot"),
    ("2(c)", "Cross Bracing --- Diagonals",              "bracing_diag"),
    ("3",    "End Diaphragms (frames at both supports)", "end_diaphragm"),
    ("4",    "Concrete for Deck Slab",                   "concrete_deck"),
    ("5",    "Reinforcement Steel for Deck Slab",        "rebar_deck"),
    ("6",    "Shear Stud Connectors",                    "shear_studs"),
    ("7",    "Crash Barrier",                            "crash_barrier"),
)

_FIELDS = ("vol_formula", "qty", "vol_total", "wt_single", "wt_total")


def _number(value) -> Optional[float]:
    """Quantity string from the BOQ generator → float (``N.A.`` → ``None``)."""
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _cell(input_dict, prefix: str, name: str) -> str:
    value = input_dict.get(f"{prefix}_{name}")
    if value in (None, "", "N.A.", "N.A"):
        return NA
    return str(value)


def _sum(*values) -> Optional[float]:
    present = [v for v in values if v is not None]
    return sum(present) if present else None


def _bom_table(input_dict) -> str:
    rows = [
        (sn, description) + tuple(_cell(input_dict, prefix, f) for f in _FIELDS)
        for sn, description, prefix in _BOM_ITEMS
    ]
    return T.table(
        "Bill of Materials (Steel, Concrete and Reinforcement Quantities)",
        "bill_of_materials",
        ("S.N.", "Item Description", "Volume of One Item",
         "Qty.", "Total Volume (" + U.m3 + ")", "Weight of One (" + U.MT + ")",
         "Total Weight (" + U.MT + ")"),
        rows,
        note=("Unit weights: structural and reinforcement steel 7.85 " + U.MT + "/" + U.m3
              + ", concrete 2.50 " + U.MT + "/" + U.m3 + ". Quantities are net (no allowance for "
              "wastage, splices, laps or connection plates)."),
        label="tab:bill-of-materials",
    )


def _summary_table(q) -> str:
    def row(label, value, unit, share_of=None):
        share = ""
        if value is not None and share_of:
            share = fmt_num(100.0 * value / share_of, 1) + r"\,\%"
        return (label, fmt_num(value, 2) if value is not None else NA, unit, share or S.TABLE.empty_cell)

    steel = q["steel_total"]
    return T.table(
        "Quantity Summary by Material",
        "quantity_summary",
        ("Material / Component", "Quantity", "Unit", "Share of Structural Steel"),
        [
            T.Band("Structural steel"),
            row("Plate Girders", q["girders"], U.MT, steel),
            row("Cross Bracing (chords + diagonals)", q["bracing"], U.MT, steel),
            row("End Diaphragms", q["diaphragms"], U.MT, steel),
            row(r"\rptstrong{Total Structural Steel}", steel, U.MT, steel),
            T.Band("Deck slab"),
            row("Concrete Volume", q["concrete_m3"], U.m3),
            row("Reinforcement Steel", q["rebar"], U.MT),
            ("Reinforcement Content",
             fmt_num(q["rebar"] * 1000.0 / q["concrete_m3"], 0) if q["rebar"] and q["concrete_m3"] else NA,
             "kg/" + U.m3, S.TABLE.empty_cell),
        ],
        label="tab:quantity-summary",
    )


def collect_quantities(input_dict) -> dict:
    """Numeric totals used by the summary table and the charts."""
    wt = lambda prefix: _number(input_dict.get(f"{prefix}_wt_total"))
    girders = wt("steel_girders")
    bracing = _sum(wt("bracing_top"), wt("bracing_bot"), wt("bracing_diag"))
    diaphragms = wt("end_diaphragm")
    return {
        "girders": girders,
        "bracing": bracing,
        "diaphragms": diaphragms,
        "steel_total": _sum(girders, bracing, diaphragms),
        "concrete_m3": _number(input_dict.get("concrete_deck_vol_total")),
        "rebar": wt("rebar_deck"),
    }


def ch7_quantities(input_dict, asset_dir=None):
    """Chapter 7. ``asset_dir`` is the temporary image directory of the build;
    the two charts are written there and embedded as figures."""
    q = collect_quantities(input_dict)

    steel_chart = concrete_chart = None
    if asset_dir:
        steel_chart = charts.steel_tonnage_chart(
            {"Girders": q["girders"], "Cross Bracing": q["bracing"], "End Diaphragms": q["diaphragms"]},
            asset_dir,
        )
        concrete_chart = charts.concrete_vs_rebar_chart(q["concrete_m3"], q["rebar"], asset_dir)

    parts = [
        r"\chapter{Material Take-off \& Quantity Summary}",
        r"\label{ch:material-takeoff}",
        "",
        "This chapter lists the quantities of structural steel, concrete and reinforcement of the "
        "superstructure. The bill of materials is followed by a summary per material and by charts "
        "that show how the quantities are distributed.",
        "",
        r"\section{Bill of Materials}",
        r"\label{sec:bill-of-materials}",
        _bom_table(input_dict),
        _summary_table(q),
        r"\section{Material Quantity Charts}",
        r"\label{sec:quantity-charts}",
        "The charts below are generated from the quantities of the bill of materials.",
        F.figure(F.asset_path(steel_chart, asset_dir),
                 "Structural steel tonnage by component (girders, cross bracing, end diaphragms)",
                 width="chart", label="fig:steel-tonnage"),
        F.figure(F.asset_path(concrete_chart, asset_dir),
                 "Deck slab: concrete volume (" + U.m3 + ") compared with reinforcement steel weight ("
                 + U.MT + ")",
                 width="chart", label="fig:concrete-rebar"),
    ]
    return "\n".join(parts) + "\n"

