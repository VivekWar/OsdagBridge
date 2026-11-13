# =============================================================================
# OsdagBridge — Live-load data for the report (Chapter 3)
# =============================================================================
"""Collects the live-load parameters shown in Chapter 3 of the report.

This module contains *data* only — which vehicles the user ticked in
*Additional Inputs → Loading → Live Load*, their total load, impact factor
and braking load (IRC 6:2017), and the footpath loading. The presentation
(tables, units columns) lives in ``chap3.py``.

The vehicle list follows the Loading tab of the desktop application one to
one: a vehicle appears in the report only when its check box is ticked.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from osdagbridge.core.utils.common import (
    KEY_BL_IRC_CLASS_SV,
    KEY_FOOTPATH,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_SPAN,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_WC_LD_LANE_TABLE_COUNT,
)

GRAVITY = 9.81                       # tonne -> kN (same constant as the IRC 6 module)
BRAKING_FIRST_TRAIN = 0.20           # IRC 6 Cl. 211.2(a): 20 % of the first train of load
BRAKING_EXTRA_LANE = 0.05            # IRC 6 Cl. 211.2(b): 5 % of the load on each lane beyond two
DEFAULT_BRAKING_HEIGHT_M = 1.2       # IRC 6 Cl. 211.3


@dataclass(frozen=True)
class VehicleClass:
    """One entry of the *IRC Vehicles* list of the Loading tab."""

    name: str                # label exactly as shown in the UI
    select_key: str          # input key of the vehicle check box
    braking_key: str         # input key deciding whether braking is considered
    total_tonne: float       # nominal total load of one vehicle / train (IRC 6 Cl. 204)
    impact_rule: str         # "class_a" | "wheeled" | "tracked" | "none"
    clause: str              # governing IRC 6 clause


# Order and labels mirror ui_fields_additional_input.py (Live Load sub-tab).
# For every class except SV, braking is considered whenever the vehicle is
# selected; Class SV has its own opt-in check box (KEY_BL_IRC_CLASS_SV).
VEHICLE_CLASSES = (
    VehicleClass("Class A",           KEY_LL_IRC_CLASS_A,       KEY_LL_IRC_CLASS_A,       55.4,  "class_a", "Cl. 204.1"),
    VehicleClass("Class AA Wheeled",  KEY_LL_IRC_AA_WHEELED,    KEY_LL_IRC_AA_WHEELED,    40.0,  "wheeled", "Cl. 204.1"),
    VehicleClass("Class AA Tracked",  KEY_LL_IRC_AA_TRACKED,    KEY_LL_IRC_AA_TRACKED,    70.0,  "tracked", "Cl. 204.1"),
    VehicleClass("Class 70R Wheeled", KEY_LL_IRC_70R_WHEELED,   KEY_LL_IRC_70R_WHEELED,   100.0, "wheeled", "Cl. 204.1"),
    VehicleClass("Class 70R Tracked", KEY_LL_IRC_70R_TRACKED,   KEY_LL_IRC_70R_TRACKED,   70.0,  "tracked", "Cl. 204.1"),
    VehicleClass("Class 70R Bogie",   KEY_LL_IRC_70R_BOGIE,     KEY_LL_IRC_70R_BOGIE,     40.0,  "wheeled", "Cl. 204.1"),
    VehicleClass("Class SV",          KEY_LL_IRC_CLASS_SV,      KEY_BL_IRC_CLASS_SV,      385.0, "none",    "Cl. 204.5"),
    VehicleClass("Class Fatigue",     KEY_LL_IRC_CLASS_FATIGUE, KEY_LL_IRC_CLASS_FATIGUE, 40.0,  "class_a", "Cl. 204.6"),
)


@dataclass
class VehicleRow:
    """One row of the vehicle live-load table."""

    vehicle: str
    total_load_kN: Optional[float]
    impact_factor: Optional[float]          # multiplier (1 + I); None when unknown
    braking_considered: bool
    braking_value_kN: Optional[float]       # None when braking is not considered
    braking_eccentricity_m: Optional[float]  # height above deck; None when not considered


@dataclass
class FootpathLoad:
    provided: bool
    configuration: str                # "None", "Single Sided", "Both" ...
    width_m: Optional[float]
    mode: str                         # "As per IRC 6" | "Custom"
    intensity_kN_m2: Optional[float]


@dataclass
class AssociatedEffects:
    design_lanes: Optional[int]
    governing_vehicle: str
    braking_first_train_kN: Optional[float]
    braking_extra_lanes_kN: Optional[float]
    braking_total_kN: Optional[float]
    braking_height_m: Optional[float]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_selected(value) -> bool:
    return value is True or str(value).strip().lower() in ("true", "yes", "1", "checked")


def _to_float(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def impact_factor(rule: str, span_m: Optional[float]) -> Optional[float]:
    """Impact multiplier ``1 + I`` for a steel bridge, IRC 6:2017 Cl. 208.

    * ``class_a`` — Cl. 208.2: ``I = 9 / (13.5 + L)`` (span limited to 3–45 m).
    * ``tracked`` — Cl. 208.3: 10 % for all spans.
    * ``wheeled`` — Cl. 208.3: 25 % up to 23 m, ``9 / (13.5 + L)`` beyond.
    * ``none``    — Cl. 204.5.3: the special vehicle moves at crawling speed,
      no impact is applied.
    """
    if rule == "none":
        return 1.0
    if span_m is None or span_m <= 0:
        return None
    curve = 9.0 / (13.5 + min(max(span_m, 3.0), 45.0))
    if rule == "class_a":
        return 1.0 + curve
    if rule == "tracked":
        return 1.10
    if rule == "wheeled":
        return 1.25 if span_m < 23.0 else 1.0 + curve
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def selected_vehicle_rows(input_dict: dict) -> List[VehicleRow]:
    """Rows for the vehicles ticked in the Loading tab (UI order)."""
    span_m = _to_float(input_dict.get(KEY_SPAN))
    eccentricity = _to_float(input_dict.get(KEY_LL_ECCENTRICITY))
    if eccentricity is None:
        eccentricity = DEFAULT_BRAKING_HEIGHT_M

    rows: List[VehicleRow] = []
    for vc in VEHICLE_CLASSES:
        if not _is_selected(input_dict.get(vc.select_key)):
            continue
        total_kN = vc.total_tonne * GRAVITY
        braking = _is_selected(input_dict.get(vc.braking_key))
        rows.append(VehicleRow(
            vehicle=vc.name,
            total_load_kN=total_kN,
            impact_factor=impact_factor(vc.impact_rule, span_m),
            braking_considered=braking,
            braking_value_kN=BRAKING_FIRST_TRAIN * total_kN if braking else None,
            braking_eccentricity_m=eccentricity if braking else None,
        ))

    # User-defined vehicles (the custom-vehicle editor stores name / total load).
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if isinstance(custom, (list, tuple)):
        for entry in custom:
            if isinstance(entry, dict) and entry.get("name"):
                total_kN = _to_float(entry.get("total_load_kN") or entry.get("total_load"))
                rows.append(VehicleRow(
                    vehicle=str(entry["name"]),
                    total_load_kN=total_kN,
                    impact_factor=_to_float(entry.get("impact_factor")),
                    braking_considered=total_kN is not None,
                    braking_value_kN=BRAKING_FIRST_TRAIN * total_kN if total_kN is not None else None,
                    braking_eccentricity_m=eccentricity if total_kN is not None else None,
                ))
            elif isinstance(entry, str) and entry.strip():
                rows.append(VehicleRow(entry.strip(), None, None, False, None, None))
    return rows


def associated_effects(input_dict: dict, rows: List[VehicleRow]) -> AssociatedEffects:
    """Governing braking force for the deck (IRC 6:2017 Cl. 211.2)."""
    lanes = None
    try:
        lanes = int(float(input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)))
    except (TypeError, ValueError):
        pass

    braking_rows = [r for r in rows if r.braking_considered and r.braking_value_kN is not None]
    if not braking_rows:
        return AssociatedEffects(lanes, "", None, None, None, None)

    governing = max(braking_rows, key=lambda r: r.braking_value_kN)
    first = governing.braking_value_kN
    extra = None
    if lanes is not None and lanes > 2:
        # Cl. 211.2(b): 5 % of the loads on the lanes in excess of two; those
        # lanes carry Class A trains (IRC 6 Table 6).
        class_a_kN = 55.4 * GRAVITY
        extra = BRAKING_EXTRA_LANE * class_a_kN * (lanes - 2)
    total = first + (extra or 0.0)
    return AssociatedEffects(lanes, governing.vehicle, first, extra, total,
                             governing.braking_eccentricity_m)


def footpath_load(input_dict: dict) -> FootpathLoad:
    """Footpath (pedestrian) live load, IRC 6:2017 Cl. 206.1."""
    configuration = str(input_dict.get(KEY_FOOTPATH, "") or "").strip()
    provided = configuration.lower() not in ("", "none", "no")
    mode = str(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "") or "").strip()
    intensity = None
    if mode.lower() in ("as per irc 6", "as per irc6", "automatic", ""):
        try:
            from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
            intensity = float(IRC6_2017.cl_206_1_footway_load())
        except Exception:
            intensity = None
        mode = mode or "As per IRC 6"
    else:
        intensity = _to_float(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE))
    return FootpathLoad(
        provided=provided,
        configuration=configuration or "None",
        width_m=_to_float(input_dict.get(KEY_TS_FOOTPATH_WIDTH)),
        mode=mode,
        intensity_kN_m2=intensity,
    )
