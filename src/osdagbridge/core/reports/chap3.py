# =============================================================================
# Chapter 3: Loads and Load Combinations
# Presentation only — data comes from the input dictionary / live_loads.py,
# formatting from styles.py via tables.py.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from . import styles as S
from . import tables as T
from .live_loads import associated_effects, footpath_load, selected_vehicle_rows
from .report_utils import _tex, _render_value, fmt_num

U = S.UNITS
NA = S.TEXT.not_applicable

# Short labels used in the load-combination expressions.
_LOAD_LABELS = {
    'dead_load':         'DL',
    'surfacing':         'SIDL',
    'live_load':         'LL',
    'wind_load':         'WL',
    'thermal_load':      'TL',
    'vehicle_collision': 'VC',
    'barge_impact':      'BI',
    'floating_bodies':   'FB',
    'seismic':           'EQ',
}


# ---------------------------------------------------------------------------
# 3.1 Permanent loads
# ---------------------------------------------------------------------------

def _dead_load_tables(input_dict) -> str:
    self_weight = T.unit_table(
        "Dead Load --- Self Weight (DL)",
        [
            ("Unit Weight of Structural Steel", _render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY),
             U.kN_per_m3, "IRC 6 Cl. 203"),
            ("Unit Weight of Deck Concrete", _render_value(input_dict, KEY_MATERIAL_DECK_DENSITY),
             U.kN_per_m3, "IRC 6 Cl. 203"),
            ("Self-Weight Factor", _render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR),
             U.none, "Multiplier on the computed self weight"),
        ],
    )
    railing = _render_value(input_dict, KEY_RL_LOAD_VALUE)
    surfacing = T.unit_table(
        "Superimposed Dead Load --- Surfacing and Barriers (DW)",
        [
            ("Wearing Course Material", _render_value(input_dict, KEY_WC_MATERIAL), U.none, "Additional Inputs"),
            ("Wearing Course Thickness", _render_value(input_dict, KEY_WC_THICKNESS), U.mm, "Additional Inputs"),
            ("Crash Barrier Load", _render_value(input_dict, KEY_CB_LOAD), U.kN_per_m, "Per barrier (SIDL)"),
            ("Railing Load", (railing + r"\sdstar{}") if railing else "", U.kN_per_m, "IRC 6 Cl. 206.5"),
        ],
    )
    return self_weight + surfacing


# ---------------------------------------------------------------------------
# 3.2 Live loads — vehicles and footpath in separate tables
# ---------------------------------------------------------------------------

def _vehicle_live_load_table(rows) -> str:
    header = (
        "Vehicle",
        "Total Load (kN)",
        "Impact Factor",
        T.Span("Braking Load", ("Considered?", "Value (kN)", "Eccentricity (m)")),
    )
    if rows:
        body = [
            (
                _tex(r.vehicle),
                fmt_num(r.total_load_kN, 1),
                fmt_num(r.impact_factor, 3),
                "Yes" if r.braking_considered else "No",
                fmt_num(r.braking_value_kN, 1) if r.braking_considered else "",
                fmt_num(r.braking_eccentricity_m, 2) if r.braking_considered else "",
            )
            for r in rows
        ]
    else:
        body = [(T.Merged("No IRC vehicle is selected in the Loading tab", 6, align="|c"),)]
    return T.table(
        "Vehicle Live Loads (LL) --- IRC 6",
        "vehicle_live_load",
        header,
        body,
        note=(r"Vehicles are those selected under Additional Inputs $\rightarrow$ Loading $\rightarrow$ Live Load. "
              r"Total load is that of one vehicle / train (IRC 6 Cl. 204). "
              r"Impact factor $= 1 + I$ for steel bridges (IRC 6 Cl. 208): Class A and fatigue vehicle "
              r"$I = 9/(13.5 + L)$; tracked vehicles $I = 0.10$; wheeled Class AA / 70R $I = 0.25$ up to 23 m span, "
              r"$9/(13.5 + L)$ beyond; no impact for Class SV (Cl. 204.5). "
              r"Braking value $= 20\%$ of the vehicle load (first train, IRC 6 Cl. 211.2), acting at the stated "
              r"eccentricity above the top of the deck."),
        label="tab:vehicle-live-loads",
    )


def _associated_effects_table(input_dict, rows) -> str:
    eff = associated_effects(input_dict, rows)
    gov = (" (" + _tex(eff.governing_vehicle) + ")") if eff.governing_vehicle else ""
    return T.unit_table(
        "Live Load --- Braking and Centrifugal Forces",
        [
            ("No. of Design Traffic Lanes", "" if eff.design_lanes is None else str(eff.design_lanes),
             U.none, "IRC 6 Table 6"),
            ("Braking Force --- Governing Vehicle" + gov, fmt_num(eff.braking_first_train_kN, 1),
             U.kN, r"20\% of first train, IRC 6 Cl. 211.2(a)"),
            ("Braking Force --- Lanes in Excess of Two",
             fmt_num(eff.braking_extra_lanes_kN, 1) if eff.braking_extra_lanes_kN is not None else NA,
             U.kN, r"5\% of the load on those lanes, IRC 6 Cl. 211.2(b)"),
            ("Design Braking Force (longitudinal)", fmt_num(eff.braking_total_kN, 1),
             U.kN, "Applied along the roadway"),
            ("Braking Force --- Height above Deck", fmt_num(eff.braking_height_m, 2),
             U.m, "IRC 6 Cl. 211.3"),
            ("Centrifugal Force", NA, U.kN,
             r"IRC 6 Cl. 212: $C = W V^{2} / (127 R)$; not applicable to a straight alignment"),
        ],
    )


def _footpath_load_table(input_dict) -> str:
    fp = footpath_load(input_dict)
    if not fp.provided:
        rows = [
            ("Footpath Provided", "None", U.none, "Basic Inputs"),
            ("Footpath Live Load", NA, U.kN_per_m2, "No footpath on this bridge"),
        ]
    else:
        rows = [
            ("Footpath Provided", _tex(fp.configuration), U.none, "Basic Inputs"),
            ("Footpath Width", fmt_num(fp.width_m, 2), U.m, "IRC 5 Cl. 104.3.6 (min. 1.5 m)"),
            ("Loading Basis", _tex(fp.mode), U.none, "Additional Inputs, Loading tab"),
            ("Footpath Live Load Intensity", fmt_num(fp.intensity_kN_m2, 3), U.kN_per_m2, "IRC 6 Cl. 206.1"),
        ]
    return T.unit_table("Footpath Live Load --- IRC 6", rows, label="tab:footpath-live-load")


# ---------------------------------------------------------------------------
# 3.3 Environmental loads
# ---------------------------------------------------------------------------

def _wind_table(input_dict) -> str:
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    # Vz / Pz — prefer stored computed values; fall back to IRC 6 Table 12.
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _h = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            vz_val = vz_val or _res.get("Vz")
            pz_val = pz_val or _res.get("Pz")
        except Exception:
            pass

    return T.unit_table(
        "Wind Load (WL) --- IRC 6",
        [
            (r"Basic Wind Speed, $V_b$", _render_value(input_dict, 'wind_speed'), U.m_per_s, "From project location"),
            ("Terrain Type", _render_value(input_dict, KEY_WL_TERRAIN_TYPE), U.none, "IRC 6 Cl. 209.2"),
            (r"Average Exposed Height, $H$", _render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT), U.m, "Additional Inputs"),
            (r"Hourly Mean Wind Speed, $V_z$", fmt_num(vz_val, 2), U.m_per_s, "IRC 6 Table 12"),
            (r"Hourly Wind Pressure, $P_z$", fmt_num(pz_val, 2), U.N_per_m2, "IRC 6 Table 12"),
            ("Transverse Wind Force", _render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE), U.kN, "IRC 6 Cl. 209.3.3"),
            ("Longitudinal Wind Force", _render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE), U.kN, "IRC 6 Cl. 209.3.4"),
            ("Vertical Wind Force", _render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE), U.kN, "IRC 6 Cl. 209.3.5"),
        ],
    )


def _seismic_table(input_dict) -> str:
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    # Prefer stored computed values; fall back to IRC 6 Cl. 218.5.1.
    zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    spectral = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    ah = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    av = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not ah or not zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                                        damping_percent=float(_damp))
            zone_factor = zone_factor or _res.get("Z")
            spectral = spectral or _res.get("Sa_g_adjusted")
            ah = ah or _res.get("Ah")
            av = av or round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    return T.unit_table(
        "Earthquake Load (EL) --- IRC 6",
        [
            ("Seismic Zone", _render_value(input_dict, 'seismic_zone'), U.none, "From project location"),
            (r"Zone Factor, $Z$", fmt_num(zone_factor, 3, strip=True), U.none, "IRC 6 Table 16"),
            (r"Importance Factor, $I$", _render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR), U.none, "IRC 6 Table 19"),
            ("Type of Soil", _render_value(input_dict, KEY_SL_SOIL_TYPE), U.none, "IRC 6 Cl. 218.5"),
            (r"Spectral Acceleration Coefficient, $S_a/g$", fmt_num(spectral, 3, strip=True), U.none, "IRC 6 Cl. 218.5.1"),
            (r"Horizontal Seismic Coefficient, $A_h$", fmt_num(ah, 4), U.none, "IRC 6 Cl. 218.5.1"),
            (r"Vertical Seismic Coefficient, $A_v$", fmt_num(av, 4), U.none, r"$\tfrac{2}{3} A_h$, IRC 6 Cl. 218.3"),
        ],
    )


def _temperature_table(input_dict) -> str:
    rise = _render_value(input_dict, KEY_TL_TEMP_RISE)
    fall = _render_value(input_dict, KEY_TL_TEMP_FALL)
    return T.unit_table(
        "Temperature Load (TL) --- IRC 6",
        [
            ("Maximum Shade Air Temperature", _render_value(input_dict, 'shade_temp_max'), U.deg_c, "From project location"),
            ("Minimum Shade Air Temperature", _render_value(input_dict, 'shade_temp_min'), U.deg_c, "From project location"),
            ("Effective Bridge Temperature --- Minimum", _render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN), U.deg_c, "IRC 6 Cl. 215.2"),
            ("Effective Bridge Temperature --- Maximum", _render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX), U.deg_c, "IRC 6 Cl. 215.2"),
            ("Design Temperature Rise", ("+" + rise) if rise else "", U.deg_c, "From mean bridge temperature"),
            ("Design Temperature Fall", (r"$-$" + fall) if fall else "", U.deg_c, "From mean bridge temperature"),
        ],
    )


# ---------------------------------------------------------------------------
# 3.4 Load combinations
# ---------------------------------------------------------------------------

def _format_factors(factors) -> str:
    """Compact load-combination expression, e.g. ``1.35 DL + 1.50 LL``."""
    parts = []
    for load, val in factors.items():
        label = _LOAD_LABELS.get(load, str(load).upper())
        if isinstance(val, dict):  # permanent load: adding / relieving effect
            add, rel = val.get('adding'), val.get('relieving')
            add_s = f"{add:.2f}" if add is not None else '--'
            rel_s = f"{rel:.2f}" if rel is not None else '--'
            parts.append(f"({add_s}/{rel_s})\\,{label}")
        elif val is not None:
            parts.append(f"{val:.2f}\\,{label}")
    return " + ".join(parts)


def _combination_name(combo) -> str:
    name = str(combo.get('name', '') or '')
    for key, label in _LOAD_LABELS.items():
        name = name.replace(key, label)
    return _tex(name)


def _load_combination_table() -> str:
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    rows = []
    for prefix, combos in (("ULS", IRC6_2017.uls_load_combinations()),
                           ("SLS", IRC6_2017.sls_load_combinations())):
        for i, combo in enumerate(combos, start=1):
            rows.append((f"{prefix}-{i:02d}", _combination_name(combo), _format_factors(combo['factors'])))
    return T.table(
        "Load Combinations",
        "load_combinations",
        ("ID", "Description", "Load Cases and Partial Factors"),
        rows,
        note=("All IRC 6 load combinations are auto-generated by OsdagBridge. For permanent loads the two "
              "factors are (adding / relieving) effect. User-defined custom combinations, if any, are appended."),
    )


# ---------------------------------------------------------------------------
# Chapter
# ---------------------------------------------------------------------------

def ch3_loads(input_dict):
    vehicle_rows = selected_vehicle_rows(input_dict)
    return "\n".join([
        r"\chapter{Loads and Load Combinations}",
        "",
        "This section summarizes all loads applied to the bridge and the load combinations "
        "considered for analysis and design.",
        "",
        r"\section{Permanent Loads}",
        r"\label{sec:permanent-loads}",
        _dead_load_tables(input_dict),
        r"\section{Live Loads}",
        r"\label{sec:live-loads}",
        "Vehicular live loads and the footpath (pedestrian) live load are reported separately. "
        "Only the IRC vehicles selected by the user in the Loading tab of the Additional Inputs "
        "are listed.",
        _vehicle_live_load_table(vehicle_rows),
        _associated_effects_table(input_dict, vehicle_rows),
        _footpath_load_table(input_dict),
        r"\section{Environmental Loads}",
        r"\label{sec:environmental-loads}",
        _wind_table(input_dict),
        _seismic_table(input_dict),
        _temperature_table(input_dict),
        r"\section{Load Combinations}",
        r"\label{sec:load-combinations}",
        _load_combination_table(),
    ]) + "\n"
