# =============================================================================
# OsdagBridge — Design-check summary data (Section 5.5 / Executive Summary)
# =============================================================================
"""Governing design checks of every primary structural element.

The list built here is the single source for

* the *Overall Design Check Summary* table (Section 5.5),
* the utilization-ratio bar charts (Section 5.5) and
* the *Key Design Outcomes* table of the executive summary,

so the three always agree. Only values already stored by the design run are
read; a utilization ratio is ``demand / capacity`` of the stored numbers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from osdagbridge.core.utils.common import (
    KEY_DD_GAMMA_DL,
    KEY_DD_GAMMA_LL,
    KEY_DD_HAS_OVERHANG,
    KEY_DD_MU_BOT,
    KEY_DD_MU_OH,
    KEY_DD_MU_TOP,
    KEY_DD_M_ULS_HOG,
    KEY_DD_M_ULS_OH,
    KEY_DD_M_ULS_SAG,
    KEY_DD_PUNCH_VED,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_VRD_C_MPA,
    KEY_DD_WK_BOT,
    KEY_DD_WK_LIMIT,
    KEY_DD_WK_OH,
    KEY_DD_WK_TOP,
    KEY_MP_ED_TYPE,
    KEY_SD_TS_VL,
    KEY_SD_TS_VRD,
)

from .data_bridge import BracingResults, ReportDataBridge

# Primary structural elements (also the keys of ``styles.CHART.element_colors``).
GIRDERS = "Steel Plate Girders"
DECK = "Concrete Deck Slab"
BRACING = "Cross Bracing"
DIAPHRAGMS = "End Diaphragms"
ELEMENTS = (GIRDERS, DECK, BRACING, DIAPHRAGMS)

SLENDERNESS_LIMIT_COMPRESSION = 250.0   # IS 800 Table 3
SLENDERNESS_LIMIT_TENSION = 400.0

UR_LIMIT = 1.0


@dataclass
class CheckSummary:
    """Governing result of one design check of one element."""

    element: str
    check: str
    combination: str = ""                 # governing load case / combination (plain text)
    demand: Optional[float] = None
    capacity: Optional[float] = None
    unit: str = ""                        # plain unit, e.g. "kNm", "MPa", "mm"
    ur: Optional[float] = None
    message: str = ""                     # shown instead of values when nothing was evaluated
    decimals: int = 2

    @property
    def passed(self) -> Optional[bool]:
        return None if self.ur is None else self.ur <= UR_LIMIT


def _to_float(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ratio(demand: Optional[float], capacity: Optional[float]) -> Optional[float]:
    if demand is None or capacity is None or capacity <= 0:
        return None
    return demand / capacity


# ---------------------------------------------------------------------------
# Steel plate girders — DCR engine results (design_results["per_girder"])
# ---------------------------------------------------------------------------

def _girders(per_girder: dict) -> Iterable:
    for name, data in (per_girder or {}).items():
        if str(name).startswith("EB") or not isinstance(data, dict):   # edge-beam pseudo girders
            continue
        yield name, data


def _governing_combination(girder_data: dict, check_ids) -> str:
    """Real load case driving the check (envelope pseudo cases are skipped)."""
    best = None
    for lc_name, lc_data in (girder_data.get("per_lc") or {}).items():
        if str(lc_name).lower().startswith("envelope"):
            continue
        for chk in (lc_data.get("checks") or []):
            if chk.get("id") in check_ids:
                dcr = chk.get("dcr") or 0.0
                if best is None or dcr > best[0]:
                    best = (dcr, lc_name)
    return str(best[1]).strip() if best else ""


def _girder_check(per_girder: dict, label: str, check_ids, fallback_unit: str = "") -> CheckSummary:
    """Worst girder (highest DCR) for the given check ids."""
    best = None
    for name, data in _girders(per_girder):
        for chk in (data.get("checks") or []):
            if chk.get("check_id") in check_ids:
                dcr = chk.get("dcr") or 0.0
                if best is None or dcr > best[0]:
                    best = (dcr, chk, data)
    if best is not None:
        dcr, chk, data = best
        return CheckSummary(GIRDERS, label, _governing_combination(data, check_ids),
                            _to_float(chk.get("demand")), _to_float(chk.get("capacity")),
                            str(chk.get("demand_unit") or fallback_unit), _to_float(dcr))

    # Checks that are evaluated per load case only (no envelope entry).
    best = None
    for name, data in _girders(per_girder):
        for lc_name, lc_data in (data.get("per_lc") or {}).items():
            if str(lc_name).lower().startswith("envelope"):
                continue
            for chk in (lc_data.get("checks") or []):
                if chk.get("id") in check_ids:
                    dcr = chk.get("dcr") or 0.0
                    if best is None or dcr > best[0]:
                        best = (dcr, chk, lc_name)
    if best is None:
        return CheckSummary(GIRDERS, label, message="Not evaluated")
    dcr, chk, lc_name = best
    return CheckSummary(GIRDERS, label, str(lc_name).strip(), _to_float(chk.get("demand")),
                        _to_float(chk.get("capacity")), fallback_unit, _to_float(dcr))


def _girder_rows(per_girder: dict) -> List[CheckSummary]:
    return [
        _girder_check(per_girder, "Moment", {1}),
        _girder_check(per_girder, "Shear", {2}),
        _girder_check(per_girder, "LTB (construction)", {5}),
        _girder_check(per_girder, "Deflection", {13, 14}, "mm"),
        _girder_check(per_girder, "Stress (SLS)", {11}, "MPa"),
        _girder_check(per_girder, "Fatigue", {8, 9}, "MPa"),
    ]


# ---------------------------------------------------------------------------
# Concrete deck slab — deck_report_values (KEY_DD_*)
# ---------------------------------------------------------------------------

def _frequent_sls_combination(per_girder: dict) -> str:
    best = None
    for name, data in _girders(per_girder):
        for lc_name, lc_data in (data.get("per_lc") or {}).items():
            if "frequent" not in str(lc_name).lower():
                continue
            dcr = lc_data.get("max_dcr") or 0.0
            if best is None or dcr > best[0]:
                best = (dcr, lc_name)
    return str(best[1]).strip() if best else "Frequent SLS"


def _deck_rows(output_dict: dict, per_girder: dict) -> List[CheckSummary]:
    deck = output_dict.get("deck_report_values", {}) or {}
    results = output_dict.get("design_results", {}) or {}

    def value(key) -> Optional[float]:
        return _to_float(deck.get(key))

    rows: List[CheckSummary] = []
    if not deck:
        for label in ("Flexure (sagging)", "Flexure (hogging)", "Cantilever overhang",
                      "Punching shear", "One-way shear", "Crack width"):
            rows.append(CheckSummary(DECK, label, message="Deck design not run"))
    else:
        g_dl, g_ll = value(KEY_DD_GAMMA_DL), value(KEY_DD_GAMMA_LL)
        combo = "Basic ULS"
        if g_dl is not None and g_ll is not None:
            combo = f"Basic ULS: {g_dl:g}DL + {g_ll:g}LL"

        def row(label, demand_key, capacity_key, unit, decimals=2) -> CheckSummary:
            demand, capacity = value(demand_key), value(capacity_key)
            return CheckSummary(DECK, label, combo, demand, capacity, unit,
                                _ratio(demand, capacity), decimals=decimals)

        rows.append(row("Flexure (sagging)", KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT, "kNm/m"))
        rows.append(row("Flexure (hogging)", KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP, "kNm/m"))
        if deck.get(KEY_DD_HAS_OVERHANG):
            rows.append(row("Cantilever overhang", KEY_DD_M_ULS_OH, KEY_DD_MU_OH, "kNm/m"))
        else:
            rows.append(CheckSummary(DECK, "Cantilever overhang", combo, message="No deck overhang"))
        rows.append(row("Punching shear", KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA, "MPa", decimals=3))
        rows.append(row("One-way shear", KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, "kN/m"))

        crack = [value(KEY_DD_WK_BOT), value(KEY_DD_WK_TOP)]
        if deck.get(KEY_DD_HAS_OVERHANG):
            crack.append(value(KEY_DD_WK_OH))
        crack = [c for c in crack if c is not None]
        governing = max(crack) if crack else None
        limit = value(KEY_DD_WK_LIMIT)
        rows.append(CheckSummary(DECK, "Crack width", _frequent_sls_combination(per_girder),
                                 governing, limit, "mm", _ratio(governing, limit), decimals=3))

    # Longitudinal shear in the slab at the shear connectors (IRC 22 Cl. 606.10).
    v_l, v_rd = _to_float(results.get(KEY_SD_TS_VL)), _to_float(results.get(KEY_SD_TS_VRD))
    if v_l is not None and v_rd is not None:
        rows.append(CheckSummary(DECK, "Transverse shear (slab)", "Envelope ULS", v_l, v_rd, "kN/m",
                                 _ratio(v_l, v_rd)))
    else:
        rows.append(CheckSummary(DECK, "Transverse shear (slab)", message="Not evaluated"))
    return rows


# ---------------------------------------------------------------------------
# Cross bracing / end diaphragms — Osdag member designs
# ---------------------------------------------------------------------------

def _bracing_axial(element: str, results: BracingResults, force_type: str) -> CheckSummary:
    """Worst pair / member by utilization for tension or compression."""
    label = force_type.capitalize()
    best = None
    for pair in results.pairs():
        for member in results.MEMBERS:
            ur = results.efficiency(pair, member, force_type)
            if ur is not None and (best is None or ur > best[0]):
                best = (ur, pair, member)
    if best is None:
        return CheckSummary(element, label, message="Not evaluated")
    ur, pair, member = best
    capacity = results.capacity(pair, member, force_type)
    demand = capacity * ur if capacity is not None else None
    return CheckSummary(element, label, results.governing_load_case(pair, member, force_type),
                        demand, capacity, "kN", ur)


def _bracing_slenderness(element: str, results: BracingResults) -> CheckSummary:
    best = None
    for pair in results.pairs():
        for member in results.MEMBERS:
            slenderness = results.slenderness(pair, member)
            if slenderness is None:
                continue
            limit = SLENDERNESS_LIMIT_TENSION if member == "chord" else SLENDERNESS_LIMIT_COMPRESSION
            ratio = slenderness / limit
            if best is None or ratio > best[0]:
                best = (ratio, slenderness, limit)
    if best is None:
        return CheckSummary(element, "Slenderness", message="Not evaluated")
    ratio, slenderness, limit = best
    return CheckSummary(element, "Slenderness", "", slenderness, limit, "", ratio, decimals=1)


def _bracing_rows(element: str, results: BracingResults) -> List[CheckSummary]:
    return [
        _bracing_axial(element, results, "compression"),
        _bracing_axial(element, results, "tension"),
        _bracing_slenderness(element, results),
    ]


def end_diaphragm_type(input_dict: dict) -> str:
    """Type of end diaphragm chosen in the member properties (first panel)."""
    for key, value in (input_dict or {}).items():
        if str(key).startswith(KEY_MP_ED_TYPE) and value:
            return str(value)
    return ""


def end_diaphragm_results(bridge: ReportDataBridge) -> Optional[BracingResults]:
    """Member designs to report for the end diaphragms.

    A separate end-diaphragm design is used when the design run stored one.
    Otherwise an end diaphragm configured as a *cross-bracing frame* is
    reported with the governing cross-bracing member design (the frames are
    designed with the same member-design module); beam-type diaphragms have
    no design module yet and return ``None``.
    """
    own = bridge.end_diaphragm
    if own.has_design():
        return own
    if "brac" in end_diaphragm_type(bridge.input_dict).strip().lower():
        return bridge.cross_bracing
    return None


def end_diaphragm_uses_bracing_design(bridge: ReportDataBridge) -> bool:
    """True when the end-diaphragm rows are taken from the cross-bracing design."""
    return (not bridge.end_diaphragm.has_design()) and end_diaphragm_results(bridge) is not None


def _diaphragm_rows(bridge: ReportDataBridge) -> List[CheckSummary]:
    results = end_diaphragm_results(bridge)
    if results is None:
        message = "Rolled / welded beam diaphragm: design not available"
        return [CheckSummary(DIAPHRAGMS, "Compression", message=message),
                CheckSummary(DIAPHRAGMS, "Tension", message=message)]
    return _bracing_rows(DIAPHRAGMS, results)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def collect(bridge: ReportDataBridge) -> List[CheckSummary]:
    """Governing checks of all primary elements, in report order."""
    output_dict = bridge.output_dict
    per_girder = (output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}
    return (_girder_rows(per_girder)
            + _deck_rows(output_dict, per_girder)
            + _bracing_rows(BRACING, bridge.cross_bracing)
            + _diaphragm_rows(bridge))


def by_element(rows: Iterable[CheckSummary]) -> Dict[str, List[CheckSummary]]:
    grouped: Dict[str, List[CheckSummary]] = {element: [] for element in ELEMENTS}
    for row in rows:
        grouped.setdefault(row.element, []).append(row)
    return grouped


def governing(rows: Iterable[CheckSummary]) -> Dict[str, Optional[CheckSummary]]:
    """Check with the highest utilization ratio of every element."""
    out: Dict[str, Optional[CheckSummary]] = {}
    for element, items in by_element(rows).items():
        evaluated = [r for r in items if r.ur is not None]
        out[element] = max(evaluated, key=lambda r: r.ur) if evaluated else None
    return out
