# =============================================================================
# Chapter 5: Design Checks
# Presentation only — values are read from the stored design results,
# formatting comes from styles.py via tables.py / figures.py / charts.py.
# DO NOT add business logic here.
# =============================================================================
from __future__ import annotations

from typing import List, Optional

from osdagbridge.core.utils.common import (
    KEY_DD_AS_BOT,
    KEY_DD_AS_LONG,
    KEY_DD_AS_MIN,
    KEY_DD_AS_REQ_BOT,
    KEY_DD_AS_REQ_TOP,
    KEY_DD_AS_TOP,
    KEY_DD_COVER_OK,
    KEY_DD_DIA_BOT,
    KEY_DD_D_BOT,
    KEY_DD_FY,
    KEY_DD_GAMMA_DL,
    KEY_DD_GAMMA_LL,
    KEY_DD_HAS_OVERHANG,
    KEY_DD_IMPACT_FACTOR,
    KEY_DD_MIN_COVER,
    KEY_DD_MU_BOT,
    KEY_DD_MU_OH,
    KEY_DD_MU_TOP,
    KEY_DD_M_BARRIER,
    KEY_DD_M_DL,
    KEY_DD_M_DL_OH,
    KEY_DD_M_LL,
    KEY_DD_M_LL_OH,
    KEY_DD_M_ULS_HOG,
    KEY_DD_M_ULS_OH,
    KEY_DD_M_ULS_SAG,
    KEY_DD_PUNCH_C1,
    KEY_DD_PUNCH_C2,
    KEY_DD_PUNCH_OK,
    KEY_DD_PUNCH_U1,
    KEY_DD_PUNCH_VED,
    KEY_DD_PUNCH_VED_KN,
    KEY_DD_SHEAR_OK,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_SPACING_MAX,
    KEY_DD_SPAN,
    KEY_DD_SPC_BOT,
    KEY_DD_TYRE_LENGTH,
    KEY_DD_TYRE_WIDTH,
    KEY_DD_VEHICLE,
    KEY_DD_VRD_C_MPA,
    KEY_DD_WDL,
    KEY_DD_WHEEL_LOAD,
    KEY_DD_WK_BOT,
    KEY_DD_WK_LIMIT,
    KEY_DD_WK_OH,
    KEY_DD_WK_TOP,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DS_BOTTOM_CLEAR_COVER,
    KEY_DS_REINF_MATERIAL,
    KEY_DS_STUD_DIAMETER,
    KEY_DS_TOP_CLEAR_COVER,
    KEY_MATERIAL_DECK_FCK,
    KEY_MATERIAL_DECK_FCTM,
    KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_WIDTH,
    KEY_SD_BS_FCD,
    KEY_SD_BS_FCDW_LC,
    KEY_SD_BS_FCDW_WB,
    KEY_SD_BS_FPSD,
    KEY_SD_BS_R,
    KEY_SD_CLASS_FLANGE,
    KEY_SD_CLASS_WEB,
    KEY_SD_COMPOSITE_IZ,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
    KEY_SD_EFFECTIVE_SLAB_WIDTH,
    KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_FLANGE_SLENDERNESS,
    KEY_SD_HIGH_SHEAR,
    KEY_SD_IS_FQ,
    KEY_SD_IS_FQD,
    KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV,
    KEY_SD_LTB_CHI,
    KEY_SD_LTB_LAMBDA,
    KEY_SD_LTB_MB,
    KEY_SD_LTB_MCR,
    KEY_SD_MDV,
    KEY_SD_MD_CAPACITY,
    KEY_SD_MN_AXIAL,
    KEY_SD_MN_MOMENT,
    KEY_SD_MN_RATIO,
    KEY_SD_MU_APPLIED,
    KEY_SD_PANEL_CD,
    KEY_SD_PNA_DEPTH,
    KEY_SD_SC_D_LIMIT,
    KEY_SD_SC_EDGE_DIST,
    KEY_SD_SC_Qr_kN,
    KEY_SD_SC_Qu_kN,
    KEY_SD_SC_REQ_EDGE_DIST,
    KEY_SD_SC_SL1,
    KEY_SD_SC_SL2,
    KEY_SD_SC_SR,
    KEY_SD_SECTION_CLASS,
    KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IZ,
    KEY_SD_SECTION_PROP_ZUZ,
    KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SHEAR_AV,
    KEY_SD_SHEAR_KV,
    KEY_SD_SHEAR_LAMBDA_W,
    KEY_SD_SHEAR_TAU_B,
    KEY_SD_SHEAR_VCR,
    KEY_SD_SHEAR_VU,
    KEY_SD_STIFF_END_COUNT,
    KEY_SD_STIFF_END_THICK,
    KEY_SD_STIFF_INT_SPACING,
    KEY_SD_STIFF_INT_THICK,
    KEY_SD_STIFF_LONG,
    KEY_SD_STIFF_METHOD,
    KEY_SD_STRESS_STEEL,
    KEY_SD_STRESS_STEEL_ALLOWABLE,
    KEY_SD_TOP_FLANGE_THICKNESS,
    KEY_SD_TOP_FLANGE_WIDTH,
    KEY_SD_TOTAL_DEPTH,
    KEY_SD_TS_VL,
    KEY_SD_TS_VRD,
    KEY_SD_ULS_PER_GIRDER,
    KEY_SD_WEB_CLASS_LIMIT,
    KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_THICKNESS,
    KEY_SPAN,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_UTIL_FLEXURE,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LTB,
    KEY_UTIL_SHEAR,
)

from . import charts
from . import design_summary as DS
from . import figures as F
from . import styles as S
from . import tables as T
from .data_bridge import BracingResults, ReportDataBridge
from .report_utils import _render_value, _tex, fmt_num, girder_entries_or_default

U = S.UNITS
NA = S.TEXT.not_applicable
DASH = S.TABLE.empty_cell

# Plain unit strings written by the design engine → report notation.
_UNIT_TEX = {
    "kNm": U.kNm, "kN-m": U.kNm, "kNm/m": U.kNm_per_m, "kN/m": U.kN_per_m, "kN": U.kN,
    "MPa": U.MPa, "mm": U.mm, "mm⁴": U.mm4, "mm4": U.mm4, "mm²": U.mm2, "mm2": U.mm2,
    "–": "", "-": "", "—": "",
}


# ---------------------------------------------------------------------------
# Small formatting helpers
# ---------------------------------------------------------------------------

def _unit(unit) -> str:
    text = str(unit or "").strip()
    return _UNIT_TEX.get(text, _tex(text))


def _q(value, unit="", nd=2) -> str:
    """``'12.34 kN'``; empty when the value is missing."""
    text = fmt_num(value, nd)
    if not text:
        return ""
    unit = _unit(unit) if unit else ""
    return f"{text} {unit}" if unit else text


def _float(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _le_status(actual, limit) -> str:
    """PASS when ``actual <= limit``."""
    a, b = _float(actual), _float(limit)
    return S.pass_fail(None if a is None or b is None else a <= b)


def _ge_status(provided, required) -> str:
    """PASS when ``provided >= required``."""
    a, b = _float(provided), _float(required)
    return S.pass_fail(None if a is None or b is None else a >= b)


def _band_status(ratio) -> str:
    """Design-engine bands: PASS < 0.90, WARN < 1.00, FAIL >= 1.00."""
    r = _float(ratio)
    if r is None:
        return DASH
    if r < 0.90:
        return S.status_tex("PASS")
    if r < 1.00:
        return S.status_tex("WARN")
    return S.status_tex("FAIL")


def _percent_ur(output_dict, key) -> Optional[float]:
    """Category utilization stored as a percentage → ratio."""
    value = _float(output_dict.get(key))
    return None if value is None else value / 100.0


def _per_girder(entries, rows_for) -> List[T.Group]:
    """One row group per girder; ``rows_for(index, label)`` returns its rows."""
    return [T.Group(_tex(label), rows_for(i, label)) for i, (label, _) in enumerate(entries, start=1)]


# ---------------------------------------------------------------------------
# 5.1 Plate girder design
# ---------------------------------------------------------------------------

def _girder_property_table(od, entries) -> str:
    def rows(_i, _label):
        v = lambda key: _render_value(od, key)
        return [
            (r"Depth, $D$", v(KEY_SD_TOTAL_DEPTH), U.mm),
            (r"Top Flange Width, $b_f$", v(KEY_SD_TOP_FLANGE_WIDTH), U.mm),
            (r"Bottom Flange Width, $b_f$", v(KEY_SD_BOTTOM_FLANGE_WIDTH), U.mm),
            (r"Top Flange Thickness, $t_f$", v(KEY_SD_TOP_FLANGE_THICKNESS), U.mm),
            (r"Bottom Flange Thickness, $t_f$", v(KEY_SD_BOTTOM_FLANGE_THICKNESS), U.mm),
            (r"Web Thickness, $t_w$", v(KEY_SD_WEB_THICKNESS), U.mm),
            (r"Gross Area, $A$", v(KEY_SD_SECTION_PROP_AREA), r"cm\textsuperscript{2}"),
            (r"Moment of Inertia, $I_z$", v(KEY_SD_SECTION_PROP_IZ), r"cm\textsuperscript{4}"),
            (r"Elastic Section Modulus, $Z_{ez}$", v(KEY_SD_SECTION_PROP_ZZ), r"cm\textsuperscript{3}"),
            (r"Plastic Section Modulus, $Z_{pz}$", v(KEY_SD_SECTION_PROP_ZUZ), r"cm\textsuperscript{3}"),
            (r"Effective Slab Width, $b_{eff}$", v(KEY_SD_EFFECTIVE_SLAB_WIDTH), U.mm),
            (r"Transformed Composite $I_z$", v(KEY_SD_COMPOSITE_IZ), r"cm\textsuperscript{4}"),
            ("Depth to Plastic Neutral Axis", v(KEY_SD_PNA_DEPTH), U.mm),
        ]
    return T.table("Girder Section Properties (Final Optimized / User-selected)",
                   "group_property_value", ("Girder", "Property", "Value", "Unit"),
                   _per_girder(entries, rows), label="tab:girder-section-properties")


def _classification_table(od, entries) -> str:
    def rows(_i, _label):
        v = lambda key: _render_value(od, key)
        return [
            ("Top Flange", v(KEY_SD_FLANGE_SLENDERNESS), v(KEY_SD_FLANGE_CLASS_LIMIT), v(KEY_SD_CLASS_FLANGE)),
            ("Web", v(KEY_SD_WEB_SLENDERNESS), v(KEY_SD_WEB_CLASS_LIMIT), v(KEY_SD_CLASS_WEB)),
            ("Overall Section", None, None, v(KEY_SD_SECTION_CLASS)),
        ]
    return T.table("Girder Section Classification", "group_classification",
                   ("Girder", "Element", "Slenderness Ratio", "Class Limit", "Classification"),
                   _per_girder(entries, rows), note="IS 800:2007 Table 2.")


_CHECK_HEADER = ("Girder", "Parameter", "Formula / Reference", "Value", "Status")


def _moment_table(od, entries) -> str:
    ur = _percent_ur(od, KEY_UTIL_FLEXURE)

    def rows(_i, _label):
        return [
            (r"Applied Moment, $M_u$", "Governing LC (ULS)", _render_value(od, KEY_SD_MU_APPLIED, " " + U.kNm), None),
            (r"Design Moment Capacity, $M_d$", "IRC 22 Cl. 603.3.1", _render_value(od, KEY_SD_MD_CAPACITY, " " + U.kNm), None),
            (r"Utilization Ratio, $M_u / M_d$", r"$M_u / M_d$", S.ratio_tex(ur),
             S.pass_fail(None if ur is None else ur <= 1.0)),
        ]
    return T.table("Moment Capacity Check", "group_check", _CHECK_HEADER, _per_girder(entries, rows),
                   note="IRC 22 Cl. 603.3.1, IS 800 Cl. 8.2.1.")


def _shear_table(od, entries) -> str:
    ur = _percent_ur(od, KEY_UTIL_SHEAR)

    def rows(_i, _label):
        return [
            (r"Applied Shear, $V_u$", "Governing LC (ULS)", _render_value(od, KEY_SD_SHEAR_VU, " " + U.kN), None),
            (r"Shear Area, $A_v$", r"$d_w \times t_w$", _render_value(od, KEY_SD_SHEAR_AV, " " + U.mm2), None),
            (r"Panel Aspect Ratio, $c/d$", None, _render_value(od, KEY_SD_PANEL_CD), None),
            (r"Shear Buckling Coefficient, $k_v$", "IS 800 Cl. 8.4.2.2", _render_value(od, KEY_SD_SHEAR_KV), None),
            (r"Web Slenderness, $\lambda_w$", r"$\sqrt{f_{yw}/(\sqrt{3}\,\tau_{cr})}$",
             _render_value(od, KEY_SD_SHEAR_LAMBDA_W), None),
            (r"Design Shear Stress, $\tau_b$", "IRC 22 Cl. 603.3.3.2", _render_value(od, KEY_SD_SHEAR_TAU_B, " " + U.MPa), None),
            (r"Shear Buckling Resistance, $V_{cr}$", r"$A_v \times \tau_b$", _render_value(od, KEY_SD_SHEAR_VCR, " " + U.kN), None),
            (r"Utilization Ratio, $V_u / V_d$", r"$V_u / V_d$", S.ratio_tex(ur),
             S.pass_fail(None if ur is None else ur <= 1.0)),
        ]
    return T.table("Shear Capacity Check", "group_check", _CHECK_HEADER, _per_girder(entries, rows),
                   note="IS 800 Cl. 8.4, IRC 22 Cl. 603.3.3.2.")


def _interaction_table(od, entries) -> str:
    mv = _percent_ur(od, KEY_UTIL_INTERACTION)
    ratio, axial, moment = (_float(od.get(k)) for k in (KEY_SD_MN_RATIO, KEY_SD_MN_AXIAL, KEY_SD_MN_MOMENT))
    if ratio is None or axial is None or moment is None:      # no axial force
        mn_condition = mn_value = mn_status = NA
    else:
        mn_condition = f"{axial:.2f} + {moment:.2f} = {ratio:.3f}"
        mn_value = S.ratio_tex(ratio, 3)
        mn_status = _band_status(ratio)

    def rows(_i, _label):
        return [
            ("High Shear Condition?", r"$V_u > 0.6\,V_d$", _render_value(od, KEY_SD_HIGH_SHEAR), None),
            (r"Reduced Moment Capacity, $M_{dv}$", "IRC 22 Cl. 603.3.3.3", _render_value(od, KEY_SD_MDV, " " + U.kNm), None),
            (r"Interaction: $M_u \leq M_{dv}$", r"$M_u / M_{dv}$", S.ratio_tex(mv), _band_status(mv)),
            (r"Interaction: $N_u/N_{Rd} + M_u/M_{dv} \leq 1.0$", mn_condition, mn_value, mn_status),
        ]
    return T.table("Interaction Checks (M-V and M-N)", "group_check",
                   ("Girder", "Check", "Condition", "Value", "Status"), _per_girder(entries, rows),
                   note="IRC 22 Cl. 603.3.3.3.")


def _ltb_table(od, entries) -> str:
    ur = _percent_ur(od, KEY_UTIL_LTB)

    def rows(_i, _label):
        return [
            (r"Elastic Critical Moment, $M_{cr}$", "IRC 22 Cl. 603.3.3.1", _render_value(od, KEY_SD_LTB_MCR, " " + U.kNm), None),
            (r"Non-dim. Slenderness, $\bar{\lambda}_{LT}$", r"$\sqrt{M_p / M_{cr}}$", _render_value(od, KEY_SD_LTB_LAMBDA), None),
            (r"LTB Reduction Factor, $\chi_{LT}$", "IS 800 Cl. 8.2.2", _render_value(od, KEY_SD_LTB_CHI), None),
            (r"LTB Resistance, $M_b$", r"$\chi_{LT}\,M_p / \gamma_{m0}$", _render_value(od, KEY_SD_LTB_MB, " " + U.kNm), None),
            (r"$M_u \leq M_b$", r"$M_u / M_b$", S.ratio_tex(ur), _band_status(ur)),
        ]
    return T.table("Lateral Torsional Buckling Check --- Construction Stage", "group_check",
                   _CHECK_HEADER, _per_girder(entries, rows),
                   note="IRC 22 Cl. 603.3.3.1, IS 800 Cl. 8.2.2.")


def _stiffener_summary_table(od, entries) -> str:
    def rows(_i, _label):
        v = lambda key: _render_value(od, key)
        return [
            ("Shear Buckling Design Method", v(KEY_SD_STIFF_METHOD), U.none),
            ("Intermediate Stiffener Thickness", v(KEY_SD_STIFF_INT_THICK), U.mm),
            ("Intermediate Stiffener Spacing", v(KEY_SD_STIFF_INT_SPACING), U.mm),
            ("End Panel Stiffener Thickness", v(KEY_SD_STIFF_END_THICK), U.mm),
            ("No. of End Panel Stiffeners", v(KEY_SD_STIFF_END_COUNT), U.none),
            ("Longitudinal Stiffeners", v(KEY_SD_STIFF_LONG), U.none),
        ]
    return T.table("Stiffener Design Summary", "group_property_value",
                   ("Girder", "Parameter", "Value", "Unit"), _per_girder(entries, rows))


_REQUIRED_HEADER = ("Girder", "Check", "Required", "Provided", "Status")


def _intermediate_stiffener_table(od, entries) -> str:
    """Verification table — only meaningful when the user supplied the
    stiffener sizes (Design Type = Custom); omitted for optimized designs."""
    def rows(_i, _label):
        return [
            (r"Min. Moment of Inertia, $I_s$", _render_value(od, KEY_SD_IS_IYS_MIN, " " + U.mm4),
             _render_value(od, KEY_SD_IS_IYS_PROV, " " + U.mm4),
             _ge_status(od.get(KEY_SD_IS_IYS_PROV), od.get(KEY_SD_IS_IYS_MIN))),
            (r"Buckling Resistance, $F_{qd} \geq F_q$", _render_value(od, KEY_SD_IS_FQ, " " + U.kN),
             _render_value(od, KEY_SD_IS_FQD, " " + U.kN),
             _ge_status(od.get(KEY_SD_IS_FQD), od.get(KEY_SD_IS_FQ))),
        ]
    return T.table("Intermediate Stiffener Checks", "group_required", _REQUIRED_HEADER,
                   _per_girder(entries, rows), note="IS 800 Cl. 8.7.1.2.")


def _bearing_stiffener_table(od, entries) -> str:
    reaction = _float(od.get(KEY_SD_BS_R))

    def check(label, key):
        provided = _float(od.get(key))
        # Resistance not computed (guidance-only mode) → N/A.
        if provided is None or provided <= 0.0 or reaction is None:
            return (label, NA, NA, NA)
        return (label, _q(reaction, "kN"), _q(provided, "kN"), _ge_status(provided, reaction))

    def rows(_i, _label):
        return [
            check("Web Buckling Resistance", KEY_SD_BS_FCDW_WB),
            check("Local Crushing Resistance", KEY_SD_BS_FCDW_LC),
            check("Bearing Capacity", KEY_SD_BS_FPSD),
            check("Column Buckling Resistance", KEY_SD_BS_FCD),
        ]
    return T.table("End Panel Stiffener Checks", "group_required", _REQUIRED_HEADER,
                   _per_girder(entries, rows), note="IS 800 Cl. 8.7.3; required value = support reaction.")


def _deflection_table(bridge, entries) -> str:
    od = bridge.output_dict
    span = _float(bridge.input_dict.get(KEY_SPAN))
    allow_live = span * 1000.0 / 800.0 if span else None
    allow_total = span * 1000.0 / 600.0 if span else None

    def rows(i, _label):
        live = od.get(f"{KEY_SD_DEFL_LIVE}.G{i}")
        total = od.get(f"{KEY_SD_DEFL_TOTAL}.G{i}")
        return [
            (r"Live Load Deflection, $\delta_{LL}$",
             ("L/800 = " + _q(allow_live, "mm", 1)) if allow_live else "", _q(live, "mm", 3),
             _le_status(live, allow_live)),
            (r"Total Load Deflection, $\delta_{total}$",
             ("L/600 = " + _q(allow_total, "mm", 1)) if allow_total else "", _q(total, "mm", 3),
             _le_status(total, allow_total)),
        ]
    return T.table("Serviceability --- Deflection Checks", "group_required",
                   ("Girder", "Check", "Allowable", "Actual", "Status"),
                   _per_girder(entries, rows), note="IRC 22 Cl. 604.3.2.")


def _stress_table(od, entries) -> str:
    results = od.get("design_results", {}) or {}
    stress, allowable = results.get(KEY_SD_STRESS_STEEL), results.get(KEY_SD_STRESS_STEEL_ALLOWABLE)
    rows = [(_tex(label), r"Structural Steel ($0.9\,f_y$)", _q(allowable, "MPa"), _q(stress, "MPa"),
             _le_status(stress, allowable)) for label, _ in entries]
    return T.table("Serviceability --- Maximum Stress Limitation", "group_required",
                   ("Girder", "Element", "Allowable Stress", "Actual Stress", "Status"), rows,
                   note="IRC 22 Cl. 604.3.1.")


def _fatigue_table(od, entries) -> str:
    fatigue = ((od.get("design_results", {}) or {}).get(KEY_SD_ULS_PER_GIRDER, {}) or {}).get("fatigue", {}) or {}
    rows = []
    for i, (label, _) in enumerate(entries, start=1):
        g = fatigue.get(f"G{i}", {}) or {}
        rows.append((_tex(label), fmt_num(g.get("demand"), 2), fmt_num(g.get("capacity"), 2),
                     S.ratio_tex(g.get("ur")), S.status_tex(g.get("status"))))
    return T.table("Serviceability --- Fatigue Assessment", "girder_fatigue",
                   ("Girder", r"Stress Range, $\Delta\sigma$ (MPa)", r"Fatigue Limit, $f_{fd}$ (MPa)",
                    "Utilization Ratio", "Status"), rows,
                   note=(r"IRC 22 Cl. 605 --- governing of normal and shear fatigue (worst by DCR). Capacity "
                         r"reduction factor $\mu_r$ applied where plate thickness $>$ 25 mm."))


def _girder_summary_table(od, entries) -> str:
    per_girder = (od.get("design_results", {}) or {}).get("per_girder", {}) or {}
    rows = []
    for i, (label, _) in enumerate(entries, start=1):
        data = per_girder.get(f"G{i}", {}) or {}
        checks = data.get("checks") or []
        if not checks:
            rows.append((_tex(label), None, None, None, None, None, None))
            continue
        ctrl = max(checks, key=lambda c: c.get("dcr") or 0.0)
        # Worst real load case for the controlling check (envelope pseudo cases skipped).
        ctrl_lc, best = None, None
        for lc_name, lc_data in (data.get("per_lc") or {}).items():
            if str(lc_name).lower().startswith("envelope"):
                continue
            for chk in lc_data.get("checks") or []:
                if chk.get("id") == ctrl.get("check_id"):
                    dcr = chk.get("dcr") or 0.0
                    if best is None or dcr > best:
                        best, ctrl_lc = dcr, lc_name
        if ctrl_lc is None:
            ctrl_lc = (data.get("demand") or {}).get("governing_combination") or ""
        rows.append((_tex(label), _tex(str(ctrl_lc)), _tex(str(ctrl.get("name", ""))),
                     _q(ctrl.get("demand"), ctrl.get("demand_unit")),
                     _q(ctrl.get("capacity"), ctrl.get("capacity_unit")),
                     S.ratio_tex(ctrl.get("dcr"), 3), S.status_tex(ctrl.get("status"))))
    return T.table("Girder Design Summary (DCR / Utilization Ratio)", "girder_summary",
                   ("Girder", "Controlling LC / Combination", "Controlling Check", "Demand", "Capacity",
                    "UR", "Status"), rows,
                   note=(r"UR = Demand / Capacity. A value $\leq 1.0$ indicates a passing check. The controlling "
                         "check is the criterion with the highest UR for each girder, with the real load "
                         "case / combination that drives it."),
                   label="tab:girder-design-summary")


def _shear_connector_tables(bridge) -> str:
    od = bridge.output_dict
    results = od.get("design_results", {}) or {}

    capacity = T.table(
        "Shear Connector Capacity", "param_formula_value_ref",
        ("Parameter", "Formula", "Value", "Reference"),
        [
            (r"Design Resistance, $Q_u$",
             T.stacked([
                 r"$Q_u=\min(Q_{u,s},\,Q_{u,c})$",
                 r"$Q_{u,s}=\dfrac{0.8\,f_u\,(\pi d^2/4)}{\gamma_v}$",
                 r"$Q_{u,c}=\dfrac{0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}}{\gamma_v}$",
             ], tall=True),
             _q(results.get(KEY_SD_SC_Qu_kN), "kN"), "IRC 22 Cl. 606.3.1 (Eq. 6.1)"),
            (r"Fatigue Shear Resistance, $Q_r$", r"IRC 22 Table 8 ($\phi d$, $N_{sc}$)",
             _q(results.get(KEY_SD_SC_Qr_kN), "kN"), "IRC 22 Cl. 606.3.2 (Table 8)"),
        ],
    )

    provided = results.get("stud_spacing_provided_mm")

    def spacing_row(criterion, required):
        return (criterion, _q(required, "mm", 1), _q(provided, "mm", 1), _le_status(provided, required))

    spacing = T.table(
        "Shear Connector Spacing", "criterion_spacing",
        ("Criterion", "Governing Spacing", "Actual Spacing Provided", "Status"),
        [
            spacing_row("ULS Shear (SL1)", results.get(KEY_SD_SC_SL1)),
            spacing_row("Full Composite (SL2)", results.get(KEY_SD_SC_SL2)),
            spacing_row("SLS Fatigue (SR)", results.get(KEY_SD_SC_SR)),
            spacing_row("Max Spacing Limit (IRC 22)", results.get("stud_spacing_max_mm")),
        ],
        note=r"IRC 22 Cl. 606.4, 606.9. Governing spacing $= \min(S_{L1}, S_{L2}, S_R)$.",
    )

    v_l, v_rd = _float(results.get(KEY_SD_TS_VL)), _float(results.get(KEY_SD_TS_VRD))
    ts_ratio = (v_l / v_rd) if (v_l is not None and v_rd and v_rd > 0) else None
    ts_ok = results.get("transverse_shear_ok")
    ast_required = results.get("Ast_required_cm2_per_m")
    # Provided transverse steel = the deck's main (bottom + top) bars, which
    # cross the shear plane; the value comes from the deck design results.
    deck = od.get("deck_design_results", {}) or {}
    try:
        ast_provided = (float(deck.get("rebar_bottom_area") or 0) + float(deck.get("rebar_top_area") or 0)) / 100.0
    except (TypeError, ValueError):
        ast_provided = None
    stud_d = bridge.input_dict.get(KEY_DS_STUD_DIAMETER)
    d_limit = results.get(KEY_SD_SC_D_LIMIT)
    edge, edge_required = results.get(KEY_SD_SC_EDGE_DIST), results.get(KEY_SD_SC_REQ_EDGE_DIST)
    cm2m = lambda v: (fmt_num(v, 2) + " " + U.cm2_per_m) if fmt_num(v, 2) else ""

    detailing = T.table(
        "Transverse Shear and Detailing Checks", "check_value_status",
        ("Check", "Value", "Status"),
        [
            (r"Longitudinal Shear per unit length, $V_L$", _q(v_l, "kN/m"), None),
            (r"Transverse Shear Capacity of Slab, $V_{Rd}$", _q(v_rd, "kN/m"), None),
            ("Transverse Shear Check", r"$V_L/V_{Rd}$ = " + S.ratio_tex(ts_ratio),
             S.pass_fail(None if ts_ok is None else bool(ts_ok))),
            (r"Min. Transverse Reinforcement, $A_{st,min}$",
             "Required " + cm2m(ast_required) + ", Provided " + cm2m(ast_provided),
             _le_status(ast_required, ast_provided)),
            (r"Stud Diameter $\leq 2\,t_f$",
             r"$d$ = " + _q(stud_d, "mm", 1) + r" $\leq 2t_f$ = " + _q(d_limit, "mm", 1),
             _le_status(stud_d, d_limit)),
            ("Stud Edge Distance",
             "Provided " + _q(edge, "mm", 1) + r" (req. $\geq$ " + _q(edge_required, "mm", 1) + ")",
             _le_status(edge_required, edge)),
        ],
        note="IRC 22 Cl. 606.6, 606.10.",
    )
    return capacity + spacing + detailing


# ---------------------------------------------------------------------------
# 5.2 Deck slab design
# ---------------------------------------------------------------------------

class _Deck:
    """Formatted access to ``output_dict['deck_report_values']`` (KEY_DD_*)."""

    def __init__(self, values: dict):
        self.values = values or {}
        self.available = bool(self.values)
        self.overhang = bool(self.values.get(KEY_DD_HAS_OVERHANG))

    def num(self, key, default=0.0) -> float:
        value = _float(self.values.get(key))
        return default if value is None else value

    def fmt(self, key, nd=2, scale=1.0, unit="") -> str:
        """Display string; the empty-cell marker when the deck design was not run."""
        value = self.values.get(key)
        if not self.available or value in (None, ""):
            return DASH
        number = _float(value)
        text = _tex(value) if number is None else f"{number * scale:.{nd}f}"
        return f"{text} {unit}" if unit else text

    def oh(self, key, nd=2, unit="") -> str:
        """Overhang value; ``N/A`` when the deck has no overhang."""
        if not self.available:
            return DASH
        return self.fmt(key, nd=nd, unit=unit) if self.overhang else NA

    def status(self, ok) -> str:
        return S.pass_fail(bool(ok)) if self.available else DASH

    def ratio(self, demand_key, capacity_key, nd=2) -> str:
        capacity = self.num(capacity_key)
        if not self.available or capacity <= 0:
            return DASH
        return S.ratio_tex(self.num(demand_key) / capacity, nd)


def _deck_tables(bridge) -> str:
    inp = bridge.input_dict
    dk = _Deck(bridge.output_dict.get("deck_report_values", {}) or {})
    combo = dk.fmt(KEY_DD_GAMMA_DL) + " DL + " + dk.fmt(KEY_DD_GAMMA_LL) + " LL"
    kNm_m = U.kNm_per_m
    mm2_m = U.mm2_per_m

    loading = T.unit_table(
        "Deck Slab --- Loading and Geometry",
        [
            (r"Effective Span of Deck Slab, $l_{eff}$", dk.fmt(KEY_DD_SPAN, nd=0, scale=1000.0), U.mm, "Girder spacing (c/c)"),
            (r"Deck Thickness, $t_s$", _render_value(inp, KEY_TS_DECK_THICKNESS), U.mm, "Additional Inputs"),
            ("Clear Cover", "Top " + _render_value(inp, KEY_DS_TOP_CLEAR_COVER) + " / Bottom "
             + _render_value(inp, KEY_DS_BOTTOM_CLEAR_COVER), U.mm, "IRC 112 Cl. 15.2"),
            ("Concrete Grade", _render_value(inp, KEY_DECK_CONCRETE_GRADE_BASIC), U.none,
             r"$f_{ck}$ = " + _render_value(inp, KEY_MATERIAL_DECK_FCK) + r" MPa, $f_{ctm}$ = "
             + _render_value(inp, KEY_MATERIAL_DECK_FCTM) + " MPa (IRC 112 Cl. 6.4)"),
            ("Reinforcement Grade", _render_value(inp, KEY_DS_REINF_MATERIAL), U.none,
             r"$f_y$ = " + dk.fmt(KEY_DD_FY, nd=0) + " MPa (IRC 112 Cl. 6.2)"),
            (r"Dead Load per Unit Area, $w_{DL}$", dk.fmt(KEY_DD_WDL), U.kN_per_m2, "Slab self-weight"),
            ("IRC 6 Wheel Load", dk.fmt(KEY_DD_WHEEL_LOAD, nd=1), U.kN, "Governing wheel, IRC 6 Cl. 204"),
            ("Tyre Contact Width", dk.fmt(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0), U.mm, "Transverse, IRC 6 Annex A"),
            ("Impact Factor", dk.fmt(KEY_DD_IMPACT_FACTOR, nd=3), U.none, "IRC 6 Cl. 208"),
            ("Governing Live Load Case", dk.fmt(KEY_DD_VEHICLE), U.none, "Vehicle giving the largest moment"),
        ],
    )

    flexure = T.table(
        "Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)", "location_check",
        ("Location", "Parameter", "Formula / Reference", "Value", "Status"),
        [
            T.Group(r"At Midspan\newline (Sagging)", [
                (r"Transverse BM (DL), $M_{T,DL}$", r"$w_{DL}\,l_{eff}^2/10$", dk.fmt(KEY_DD_M_DL, unit=kNm_m), None),
                (r"Transverse BM (LL), $M_{T,LL}$", "Effective width (IRC 112 B3.1)", dk.fmt(KEY_DD_M_LL, unit=kNm_m), None),
                (r"Total Design BM, $M_{u,sag}$", combo, dk.fmt(KEY_DD_M_ULS_SAG, unit=kNm_m), None),
                (r"Effective depth, $d$", r"$t_s - c_{nom} - \phi/2$", dk.fmt(KEY_DD_D_BOT, nd=1, unit=U.mm), None),
                (r"Moment Capacity, $M_{Rd}$", "IRC 112 Cl. 12.2", dk.fmt(KEY_DD_MU_BOT, unit=kNm_m),
                 dk.status(dk.num(KEY_DD_MU_BOT) >= dk.num(KEY_DD_M_ULS_SAG))),
            ]),
            T.Group(r"At Support\newline (Hogging)", [
                (r"Total Design BM, $M_{u,hog}$", combo + " (at support)", dk.fmt(KEY_DD_M_ULS_HOG, unit=kNm_m), None),
                (r"Required Top Steel, $A_{st,top}$", r"$M_u / (0.87\,f_y\,d)$", dk.fmt(KEY_DD_AS_REQ_TOP, nd=0, unit=mm2_m), None),
                (r"Moment Capacity, $M_{Rd}$", "IRC 112 Cl. 12.2", dk.fmt(KEY_DD_MU_TOP, unit=kNm_m),
                 dk.status(dk.num(KEY_DD_MU_TOP) >= dk.num(KEY_DD_M_ULS_HOG))),
            ]),
        ],
        note=(r"IRC 112 Cl. 12.2. Distribution (longitudinal) reinforcement designed for 20\% of main steel "
              "moment (IRC 21 Cl. 305.18)."),
    )

    if dk.overhang:
        oh_status = dk.status(dk.num(KEY_DD_MU_OH) >= dk.num(KEY_DD_M_ULS_OH))
    else:
        oh_status = NA if dk.available else DASH
    _pfvs = ("Parameter", "Formula / Reference", "Value", "Status")
    overhang = T.table(
        "Deck Slab --- Cantilever Overhang Flexure Check", "param_formula_value_status", _pfvs,
        [
            (r"Overhang Length, $l_{oh}$", None, _render_value(inp, KEY_TS_DECK_OVERHANG, " " + U.m), None),
            ("Crash Barrier Load Moment", "IRC 6 Cl. 206.4", dk.oh(KEY_DD_M_BARRIER, unit=kNm_m), None),
            ("Dead Load Moment", r"$w_{DL}\,l_{oh}^2/2$ + railing", dk.oh(KEY_DD_M_DL_OH, unit=kNm_m), None),
            ("Live Load Moment (eccentric wheel)", r"Wheel load $\times$ arm", dk.oh(KEY_DD_M_LL_OH, unit=kNm_m), None),
            (r"Total Hogging Moment, $M_{u,oh}$", dk.fmt(KEY_DD_GAMMA_DL) + " DL + " + dk.fmt(KEY_DD_GAMMA_LL)
             + " (LL + CB)", dk.oh(KEY_DD_M_ULS_OH, unit=kNm_m), None),
            (r"Moment Capacity (top steel), $M_{Rd,oh}$", "IRC 112 Cl. 12.2", dk.oh(KEY_DD_MU_OH, unit=kNm_m), oh_status),
        ],
        note="IRC 6 Cl. 206.4 crash barrier loads applied at kerb face; IRC 112 Cl. 12.2 flexure.",
    )

    punching = T.table(
        "Deck Slab --- Punching Shear Check (IRC 112 Cl. 10.4.6)", "param_formula_value_status", _pfvs,
        [
            (r"Design Wheel Load (ULS), $V_{Ed}$", r"$\gamma_Q\,(1+IF)\,P_w$", dk.fmt(KEY_DD_PUNCH_VED_KN, nd=1, unit=U.kN), None),
            ("Tyre Contact Area", r"$a \times b$ (IRC 6 Annex A)",
             dk.fmt(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + r" $\times$ " + dk.fmt(KEY_DD_TYRE_LENGTH, nd=0, unit=U.mm), None),
            (r"Loaded Area at mid-depth, $b_0$", r"$c_1 \times c_2$ (incl.\ WC dispersion)",
             dk.fmt(KEY_DD_PUNCH_C1, nd=0) + r" $\times$ " + dk.fmt(KEY_DD_PUNCH_C2, nd=0, unit=U.mm), None),
            (r"Control Perimeter, $u_1$", r"$2(c_1+c_2) + 4\pi d$", dk.fmt(KEY_DD_PUNCH_U1, nd=0, unit=U.mm), None),
            (r"Punching Shear Stress, $v_{Ed}$", r"$V_{Ed} / (u_1\,d)$", dk.fmt(KEY_DD_PUNCH_VED, nd=3, unit=U.MPa), None),
            (r"Punching Resistance, $v_{Rd,c}$", r"IRC 112 Eq.\ 10.1", dk.fmt(KEY_DD_VRD_C_MPA, nd=3, unit=U.MPa), None),
            ("Punching Shear Check", r"$v_{Ed} / v_{Rd,c} \leq 1.0$", dk.ratio(KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA),
             dk.status(dk.values.get(KEY_DD_PUNCH_OK))),
        ],
        note=(r"Punching shear reinforcement not typically required for deck slabs with $d \geq 200$ mm and "
              "adequate longitudinal reinforcement."),
    )

    crack_values = [dk.num(KEY_DD_WK_BOT), dk.num(KEY_DD_WK_TOP)] + ([dk.num(KEY_DD_WK_OH)] if dk.overhang else [])
    governing_crack = max(crack_values)
    crack_ok = dk.available and governing_crack <= dk.num(KEY_DD_WK_LIMIT)
    crack = T.unit_table(
        "Crack Width Check (Deck Slab)",
        [
            (r"Min. Reinforcement for Crack Control, $A_{s,min}$", dk.fmt(KEY_DD_AS_MIN, nd=0), mm2_m, "IRC 112 Cl. 16.5.1"),
            ("Provided Reinforcement (bottom)", dk.fmt(KEY_DD_AS_BOT, nd=0), mm2_m,
             r"$\phi$" + dk.fmt(KEY_DD_DIA_BOT, nd=0) + " @ " + dk.fmt(KEY_DD_SPC_BOT, nd=0) + " mm c/c"),
            ("Max. Permissible Crack Width", dk.fmt(KEY_DD_WK_LIMIT), U.mm, "IRC 112 Table 12.1"),
            (r"Calculated Crack Width, $w_k$ (governing)", f"{governing_crack:.4f}" if dk.available else DASH,
             U.mm, "Frequent SLS combination"),
            ("Crack Width Check", dk.status(crack_ok), U.none, r"$w_k \leq w_{k,max}$"),
        ],
    )

    d_bot = dk.num(KEY_DD_D_BOT)
    has_depth = dk.available and d_bot > 0
    one_way = T.table(
        "One-Way (Beam) Shear Check (Deck Slab)", "param_formula_value_status", _pfvs,
        [
            (r"Design Shear per unit width, $V_{Ed}$", r"$\gamma_{DL} V_{DL} + \gamma_{LL}(1{+}IF)V_{LL}$",
             dk.fmt(KEY_DD_SHEAR_VED, unit=U.kN_per_m), None),
            (r"Effective depth, $d$", r"$t_s - c_{nom} - \phi/2$", dk.fmt(KEY_DD_D_BOT, nd=1, unit=U.mm), None),
            (r"Size factor, $k$", r"$1 + \sqrt{200/d} \leq 2.0$",
             f"{min(1.0 + (200.0 / d_bot) ** 0.5, 2.0):.3f}" if has_depth else DASH, None),
            (r"Long.\ reinforcement ratio, $\rho_l$", r"$A_{sl}/(b_w\,d) \leq 0.02$",
             f"{min(dk.num(KEY_DD_AS_BOT) / (1000.0 * d_bot), 0.02):.4f}" if has_depth else DASH, None),
            (r"Shear resistance (no stirrups), $V_{Rd,c}$", r"$v_{Rd,c}\,b_w\,d$ (Cl.\ 10.3.2)",
             dk.fmt(KEY_DD_SHEAR_VRDC, unit=U.kN_per_m), None),
            ("One-Way Shear Check", r"$V_{Ed} / V_{Rd,c} \leq 1.0$", dk.ratio(KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC),
             dk.status(dk.values.get(KEY_DD_SHEAR_OK))),
        ],
        note=("IRC 112 Cl. 10.3.2. Shear reinforcement not provided in deck slabs; capacity relies on concrete "
              "and main reinforcement."),
    )

    detailing = T.table(
        "Reinforcement Detailing Summary (Deck Slab)", "detailing",
        ("Parameter", "Required / Limit", "Provided", "Status"),
        [
            T.Band("Main Reinforcement --- Bottom (Transverse)"),
            (r"Required Area, $A_{st,req}$", dk.fmt(KEY_DD_AS_REQ_BOT, nd=0, unit=mm2_m), dk.fmt(KEY_DD_AS_BOT, nd=0, unit=mm2_m),
             dk.status(dk.num(KEY_DD_AS_BOT) >= dk.num(KEY_DD_AS_REQ_BOT))),
            (r"Bar Diameter $\times$ Spacing", r"$\phi \geq 10$ mm (IRC 112)",
             r"$\phi$" + dk.fmt(KEY_DD_DIA_BOT, nd=0) + " @ " + dk.fmt(KEY_DD_SPC_BOT, nd=0) + " mm c/c", None),
            (r"Min.\ Reinforcement $A_{s,min}$ (IRC 112 Cl. 16.3.1)", dk.fmt(KEY_DD_AS_MIN, nd=0, unit=mm2_m),
             dk.fmt(KEY_DD_AS_BOT, nd=0, unit=mm2_m), dk.status(dk.num(KEY_DD_AS_BOT) >= dk.num(KEY_DD_AS_MIN))),
            (r"Max.\ Bar Spacing (IRC 112 Cl. 16.3.2)", dk.fmt(KEY_DD_SPACING_MAX, nd=0, unit=U.mm),
             dk.fmt(KEY_DD_SPC_BOT, nd=0, unit=U.mm),
             dk.status(0.0 < dk.num(KEY_DD_SPC_BOT) <= dk.num(KEY_DD_SPACING_MAX))),
            T.Band("Distribution Reinforcement --- Longitudinal"),
            (r"Required Area, $A_{st,dist}$", r"$\geq 20\%$ of main steel", dk.fmt(KEY_DD_AS_LONG, nd=0, unit=mm2_m),
             dk.status(dk.num(KEY_DD_AS_LONG) >= max(0.20 * dk.num(KEY_DD_AS_BOT), dk.num(KEY_DD_AS_MIN)))),
            T.Band("Top Reinforcement (Support / Cantilever Overhang)"),
            (r"Required Area, $A_{st,top}$", dk.fmt(KEY_DD_AS_REQ_TOP, nd=0, unit=mm2_m), dk.fmt(KEY_DD_AS_TOP, nd=0, unit=mm2_m),
             dk.status(dk.num(KEY_DD_AS_TOP) >= dk.num(KEY_DD_AS_REQ_TOP))),
            T.Band("Cover and Detailing"),
            ("Clear Cover (IRC 112 Cl. 15.2)", r"$\geq$ " + dk.fmt(KEY_DD_MIN_COVER, nd=0) + " mm (Table 14.2)",
             "Top " + _render_value(inp, KEY_DS_TOP_CLEAR_COVER) + " / Bottom "
             + _render_value(inp, KEY_DS_BOTTOM_CLEAR_COVER) + " mm", dk.status(dk.values.get(KEY_DD_COVER_OK))),
        ],
        note="IRC 112 Cl. 16.3, IS 456 Cl. 26.5.",
    )
    return loading + flexure + overhang + punching + crack + one_way + detailing


# ---------------------------------------------------------------------------
# 5.3 / 5.4 Cross bracing and end diaphragms (bracing frames)
# ---------------------------------------------------------------------------

def _section_property(od, kind: str, member: str, pair_id: str, name: str):
    """Area / radius of gyration of a bracing member from the stored properties."""
    base = f"transverse_member_design.{kind}.section_properties"
    if kind == "ed":
        return od.get(f"{base}.end_diaphragm.{pair_id}.{name}")
    if member == "diagonal":
        return od.get(f"{base}.bracing.{pair_id}.{name}")
    value = od.get(f"{base}.bottom_chord.{pair_id}.{name}")
    return value if value is not None else od.get(f"{base}.top_chord.{pair_id}.{name}")


def _bracing_tables(od, results: BracingResults, title: str, kind: str, note: Optional[str] = None) -> str:
    """The three member tables of a set of bracing frames.

    ``kind`` selects the stored section properties (``"cb"`` or ``"ed"``).
    """
    pairs = results.pairs()

    # --- connection and section properties -----------------------------------
    section_rows = []
    for pair in pairs:
        pair_id = pair.replace("-", "")
        rows = []
        for member, label in (("diagonal", "Diagonal"), ("chord", "Top / Bottom chord")):
            _force, force_type = results.governing_force(pair, member)
            area = _float(_section_property(od, kind, member, pair_id, "A"))      # cm²
            r_min = _float(_section_property(od, kind, member, pair_id, "rv"))    # cm
            rows.append((label, _tex(results.connection(pair, member, force_type)),
                         _tex(results.section(pair, member, force_type)),
                         fmt_num(area * 100.0, 1) if area is not None else None,
                         fmt_num(r_min * 10.0, 1) if r_min is not None else None))
        section_rows.append(T.Group(_tex(pair), rows))
    if not section_rows:
        section_rows = [(T.Merged("No bracing member results are available", 6, align="|c"),)]
    sections = T.table(
        f"{title} --- Connection and Section Properties", "bracing_section",
        ("Panel", "Member", "Connection", "Section", "$A_g$ (" + U.mm2 + ")", r"$r_{min}$ (mm)"),
        section_rows,
        note=r"$A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration." + (" " + note if note else ""),
    )

    # --- slenderness ----------------------------------------------------------
    top, bottom = results.chord_enabled("top_chord"), results.chord_enabled("bottom_chord")

    def slender_row(label, nature, member, limit, pair):
        length = results.effective_length_mm(member)
        value = results.slenderness(pair, member)
        return (label, nature, fmt_num(length, 0), fmt_num(value, 1), f"{limit:.0f}",
                S.pass_fail(None if value is None else value <= limit))

    slender_rows = []
    for pair in pairs:
        rows = [slender_row("Diagonal", "C", "diagonal", DS.SLENDERNESS_LIMIT_COMPRESSION, pair)]
        if top:
            rows.append(slender_row("Top chord", "C", "chord", DS.SLENDERNESS_LIMIT_COMPRESSION, pair))
        if bottom:
            rows.append(slender_row("Bottom chord", "T", "chord", DS.SLENDERNESS_LIMIT_TENSION, pair))
        slender_rows.append(T.Group(_tex(pair), rows))
    if not slender_rows:
        slender_rows = [(T.Merged("No bracing member results are available", 7, align="|c"),)]
    slenderness = T.table(
        f"{title} --- Slenderness Ratio Check (IS 800 Cl. 3.8)", "bracing_slenderness",
        ("Panel", "Member", "Nature", r"Eff.\ Length $KL$ (mm)", "$KL/r$", "Limit", "Status"),
        slender_rows,
        note=("Limit = 250 for compression members (C), 400 for tension members (T). "
              "$K = 1.0$ for members with both ends pinned."),
    )

    # --- capacity -------------------------------------------------------------
    capacity_rows = []
    for pair in pairs:
        rows = []
        for member, label in (("diagonal", "Diagonal"), ("chord", "Chord")):
            force, force_type = results.governing_force(pair, member)
            ur = results.efficiency(pair, member, force_type)
            rows.append((label, _tex(results.section(pair, member, force_type)),
                         _tex(results.governing_load_case(pair, member, force_type)),
                         fmt_num(force, 2), fmt_num(results.capacity(pair, member, force_type), 2),
                         S.ratio_tex(ur), S.pass_fail(None if ur is None else ur <= 1.0)))
        capacity_rows.append(T.Group(_tex(pair), rows))
    if not capacity_rows:
        capacity_rows = [(T.Merged("No bracing member results are available", 8, align="|c"),)]
    capacity = T.table(
        f"{title} Design --- Capacity Summary", "bracing_capacity",
        ("Panel", "Member", "Section", "Governing LC", "Demand (kN)", "Capacity (kN)", "UR", "Status"),
        capacity_rows,
        note=("Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension) with the Osdag member-design "
              "module." + (" " + note if note else "")),
    )
    return sections + slenderness + capacity


def _end_diaphragm_section(bridge) -> str:
    results = DS.end_diaphragm_results(bridge)
    if results is None:
        return (r"\rptnote{The end diaphragms are rolled / welded beam sections. Their moment and shear design "
                "is not available in this version of OsdagBridge; no member check is reported.}\n")
    if DS.end_diaphragm_uses_bracing_design(bridge):
        note = ("The end diaphragms are cross-bracing frames; the analysis reports no separate end-diaphragm "
                "member forces, so the governing cross-bracing member design is shown.")
        return _bracing_tables(bridge.output_dict, results, "End Diaphragm", "cb", note)
    return _bracing_tables(bridge.output_dict, results, "End Diaphragm", "ed")


# ---------------------------------------------------------------------------
# 5.5 Overall design check summary (table + utilization charts)
# ---------------------------------------------------------------------------

def _overall_summary_table(rows: List[DS.CheckSummary]) -> str:
    groups = []
    for element, items in DS.by_element(rows).items():
        body = []
        for r in items:
            if r.ur is None and r.message:
                body.append((_tex(r.check), T.Merged(_tex(r.message), 5, align="c")))
                continue
            body.append((
                _tex(r.check),
                _tex(r.combination) if r.combination else None,
                _q(r.demand, r.unit, r.decimals),
                _q(r.capacity, r.unit, r.decimals),
                S.ratio_tex(r.ur),
                S.pass_fail(r.passed),
            ))
        if body:
            groups.append(T.Group(_tex(element), body))
    return T.table(
        "Overall Design Check Summary --- All Members", "overall_summary",
        ("Element", "Check", "Governing Load Combination", "Demand", "Capacity", "UR", "Status"),
        groups,
        note=(r"UR = Demand / Capacity. All values $\leq 1.0$ indicate passing checks; values above 1.0 are "
              "highlighted. For each element the worst girder / panel / member is reported."),
        label="tab:overall-design-summary",
    )


def _overall_summary_section(bridge, asset_dir) -> str:
    rows = DS.collect(bridge)
    items = [charts.URItem(r.element, r.check, r.ur) for r in rows]

    by_element = by_check = None
    if asset_dir:
        by_element = charts.utilization_by_element_chart(items, asset_dir)
        by_check = charts.utilization_by_check_chart(items, asset_dir)

    governing = DS.governing(rows)
    failing = [e for e, r in governing.items() if r is not None and r.ur > DS.UR_LIMIT]
    if failing:
        verdict = (r"\rptstrong{" + ", ".join(_tex(e) for e in failing) + r"} exceed"
                   + ("s" if len(failing) == 1 else "") + " the limit and must be revised.")
    else:
        verdict = "All evaluated elements are within the limit."

    return "\n".join([
        "The table below collects the governing design checks of all primary structural elements. The "
        "bar charts that follow show the utilization ratio (UR = demand / capacity) of each element; "
        "the red dashed line marks the limit UR = 1.0. " + verdict,
        _overall_summary_table(rows),
        F.figure(F.asset_path(by_element, asset_dir),
                 "Governing utilization ratio of the primary structural elements (limit UR = 1.0)",
                 width="chart", label="fig:ur-by-element"),
        F.figure(F.asset_path(by_check, asset_dir),
                 "Utilization ratio of all summary design checks, grouped by structural element "
                 "(limit UR = 1.0)",
                 width="chart", label="fig:ur-by-check"),
    ])


# ---------------------------------------------------------------------------
# Chapter
# ---------------------------------------------------------------------------

def ch5_design_checks(checks_data, bridge: ReportDataBridge, asset_dir: Optional[str] = None) -> str:
    """Chapter 5 — Design Checks.

    Parameters
    ----------
    checks_data :
        Raw checks payload (unused; data is sourced from ``bridge``).
    bridge : ReportDataBridge
        Provides ``input_dict`` / ``output_dict`` and the bracing accessors.
    asset_dir :
        Temporary image directory of the report build; the utilization-ratio
        charts of Section 5.5 are written there.
    """
    od = bridge.output_dict
    entries = girder_entries_or_default(bridge.input_dict)
    is_custom = str(bridge.input_dict.get(KEY_DESIGN_MODE, "Optimized")).strip().lower() in {"custom", "customized"}

    parts = [
        r"\chapter{Design Checks}",
        "",
        "This section presents all structural design checks performed by OsdagBridge. For each member, the "
        "demand from the governing load combination, the code-based capacity, and the utilization ratio are "
        "tabulated. All checks reference IS 800:2007 and IRC 22:2014 unless stated otherwise.",
        "",
        r"\section{Plate Girder Design}",
        r"\label{sec:plate-girder}",
        _girder_property_table(od, entries),
        _classification_table(od, entries),
        _moment_table(od, entries),
        _shear_table(od, entries),
        _interaction_table(od, entries),
        _ltb_table(od, entries),
        _stiffener_summary_table(od, entries),
        _intermediate_stiffener_table(od, entries) if is_custom else "",
        _bearing_stiffener_table(od, entries),
        _deflection_table(bridge, entries),
        _stress_table(od, entries),
        _fatigue_table(od, entries),
        _girder_summary_table(od, entries),
        _shear_connector_tables(bridge),
        r"\section{Deck Slab Design}",
        r"\label{sec:deck-design}",
        "The reinforced concrete deck slab is designed per IRC~112:2011 (flexure, shear, crack width) and "
        "IRC~22:2014 (composite construction). Wheel loads are distributed using Pigeaud's method. The deck is "
        "checked for flexure in the transverse and longitudinal directions, punching shear, one-way (beam) "
        "shear, crack width, and reinforcement detailing.",
        _deck_tables(bridge),
        r"\section{Cross Bracing Design}",
        r"\label{sec:cross-bracing}",
        "Cross bracing between adjacent plate girders provides lateral stability during construction, resists "
        "transverse loads (wind, seismic, braking) in service, and prevents lateral torsional buckling of the "
        "girders. Members are designed per IS~800:2007 Cl.~7 (compression) and Cl.~6 (tension). Forces are "
        "derived from the grillage model under the governing load combination.",
        _bracing_tables(od, bridge.cross_bracing, "Cross Bracing", "cb"),
        r"\section{End Diaphragm Design}",
        r"\label{sec:end-diaphragm}",
        "End diaphragms at the supports transfer transverse loads to the bearings, restrain the bottom flanges "
        "against lateral displacement, and maintain the girder cross-section geometry during construction and "
        "in service. They are designed per IS~800:2007 and IRC~24:2010 Cl.~507.",
        _end_diaphragm_section(bridge),
        r"\section{Overall Design Check Summary}",
        r"\label{sec:overall-summary}",
        _overall_summary_section(bridge, asset_dir),
    ]
    return "\n".join(p for p in parts if p is not None) + "\n"
