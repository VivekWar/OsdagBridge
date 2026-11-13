# =============================================================================
# Chapter 2: Input Parameters
# Presentation only — formatting comes from styles.py via tables.py.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_CB_LOAD,
    KEY_CB_TYPE,
    KEY_CROSS_BRACING,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DO_GAMMA_C_BASIC,
    KEY_DO_GAMMA_FLT,
    KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_MF,
    KEY_DO_GAMMA_S,
    KEY_DO_GAMMA_V,
    KEY_END_DIAPHRAGM,
    KEY_FOOTPATH,
    KEY_GIRDER,
    KEY_INCLUDE_MEDIAN,
    KEY_MD_TYPE,
    KEY_MP_CB_BRACING_SECTION_DESIGNATION,
    KEY_MP_CB_MEMBER_ID,
    KEY_MP_CB_SELECT_GIRDERS,
    KEY_MP_CB_SPACING,
    KEY_MP_CB_TYPE,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    KEY_MP_ED_MEMBER_ID,
    KEY_MP_ED_SELECT_GIRDERS,
    KEY_MP_ED_TYPE,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_SYMMETRY,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
    KEY_MP_GIRDER_TYPE,
    KEY_MP_GIRDER_WARPING_RESTRAINT,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_WEB_TYPE,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_LONGITUDINAL,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_SPACING,
    KEY_RL_LOAD_VALUE,
    KEY_RL_TYPE,
    KEY_SD_SHEAR_DIAMETER,
    KEY_SD_SHEAR_HEIGHT,
    KEY_SD_SHEAR_STUDS_PER_SECTION,
    KEY_SD_SHEAR_ULTIMATE_STRENGTH,
    KEY_SD_SHEAR_YIELD_STRENGTH,
    KEY_SKEW_ANGLE,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_OVERALL_WIDTH,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS
)

from . import styles as S
from . import tables as T
from .report_utils import _render_value, _tex, dimension_mm, girder_entries_or_default

U = S.UNITS


def _yes(value) -> bool:
    return str(value or "").strip().lower() in ("yes", "true", "1")


# ---------------------------------------------------------------------------
# 2.1 Basic inputs
# ---------------------------------------------------------------------------

def _basic_input_tables(m, input_dict) -> str:
    lat, lon = _render_value(input_dict, 'latitude'), _render_value(input_dict, 'longitude')
    location = T.unit_table(
        "Project Location",
        [
            ("Project Location", _tex(m.project_location), U.none, "Basic Inputs"),
            ("Latitude / Longitude", (lat + ", " + lon) if (lat or lon) else "", U.degree, "From project location"),
            ("Seismic Zone", _render_value(input_dict, 'seismic_zone'), U.none, "IRC 6 Fig. 18"),
            ("Basic Wind Speed", _render_value(input_dict, 'wind_speed'), U.m_per_s, "IRC 6 Fig. 10"),
            ("Shade Air Temperature --- Maximum", _render_value(input_dict, 'shade_temp_max'), U.deg_c, "IRC 6 Fig. 15"),
            ("Shade Air Temperature --- Minimum", _render_value(input_dict, 'shade_temp_min'), U.deg_c, "IRC 6 Fig. 16"),
        ],
        label="subsec:project-location",
    )
    geometry = T.unit_table(
        "Bridge Geometry",
        [
            ("Type of Structure", _render_value(input_dict, KEY_STRUCTURE_TYPE), U.none, "Basic Inputs"),
            ("Span", _render_value(input_dict, KEY_SPAN), U.m, "Effective span, simply supported"),
            ("Carriageway Width", _render_value(input_dict, KEY_CARRIAGEWAY_WIDTH), U.m, "IRC 5 Cl. 104.3.1"),
            ("Include Median", _render_value(input_dict, KEY_INCLUDE_MEDIAN), U.none, "Basic Inputs"),
            ("Footpath", _render_value(input_dict, KEY_FOOTPATH), U.none, "Basic Inputs"),
            ("Skew Angle", _render_value(input_dict, KEY_SKEW_ANGLE), U.degree, r"IRC 24 Cl. 504.8 limit: $\pm$15\textdegree"),
        ],
        label="subsec:bridge-geometry",
    )
    material = T.key_value_table(
        "Material Selection",
        [
            ("Girder Steel Grade (IS 2062)", _render_value(input_dict, KEY_GIRDER)),
            ("Cross Bracing Steel Grade", _render_value(input_dict, KEY_CROSS_BRACING)),
            ("End Diaphragm Steel Grade", _render_value(input_dict, KEY_END_DIAPHRAGM)),
            ("Concrete Deck Grade (IRC 22)", _render_value(input_dict, KEY_DECK_CONCRETE_GRADE_BASIC)),
        ],
        layout="key_value_wide_key",
        label="subsec:material",
    )
    return location + geometry + material


# ---------------------------------------------------------------------------
# 2.2 Additional inputs
# ---------------------------------------------------------------------------

def _section_tables(input_dict) -> str:
    typical = T.unit_table(
        "Typical Section Details",
        [
            ("Overall Bridge Width", _render_value(input_dict, KEY_TS_OVERALL_WIDTH), U.m, "Carriageway + barriers + footpaths"),
            ("No. of Girders", _render_value(input_dict, KEY_TS_NO_OF_GIRDERS), U.none, "Additional Inputs"),
            ("Girder Spacing", _render_value(input_dict, KEY_TS_GIRDER_SPACING), U.m, "Centre to centre"),
            ("Deck Overhang Width", _render_value(input_dict, KEY_TS_DECK_OVERHANG), U.m, "Beyond the outer girder"),
            ("Deck Thickness", _render_value(input_dict, KEY_TS_DECK_THICKNESS), U.mm, "Additional Inputs"),
            ("Footpath Width", _render_value(input_dict, KEY_TS_FOOTPATH_WIDTH), U.m, "IRC 5 Cl. 104.3.6 (min. 1.5 m)"),
            ("No. of Traffic Lanes", _render_value(input_dict, KEY_WC_LD_LANE_TABLE_COUNT), U.none, "IRC 5 Cl. 104.3.1"),
        ],
    )
    rows = [
        ("Crash Barrier Type", _render_value(input_dict, KEY_CB_TYPE), U.none, "IRC 5 Cl. 109"),
        ("Crash Barrier Load", _render_value(input_dict, KEY_CB_LOAD), U.kN_per_m, "Per barrier"),
    ]
    if _yes(input_dict.get(KEY_INCLUDE_MEDIAN)):       # only when a median is included
        rows.append(("Median Type", _render_value(input_dict, KEY_MD_TYPE), U.none, "Additional Inputs"))
    rows += [
        ("Railing Type", _render_value(input_dict, KEY_RL_TYPE), U.none, "Additional Inputs"),
        ("Railing Load", _render_value(input_dict, KEY_RL_LOAD_VALUE), U.kN_per_m, "IRC 6 Cl. 206.5"),
        ("Wearing Course Material", _render_value(input_dict, KEY_WC_MATERIAL), U.none, "Additional Inputs"),
        ("Wearing Course Thickness", _render_value(input_dict, KEY_WC_THICKNESS), U.mm, "Additional Inputs"),
    ]
    return typical + T.unit_table("Components Details", rows)


def _girder_tables(input_dict) -> str:
    entries = girder_entries_or_default(input_dict)

    def key(base, i):
        return f"{base}.G{i}.M1"

    def dim(base, i):
        return dimension_mm(input_dict.get(key(base, i)))

    def pair(width_key, thickness_key, i):
        width, thickness = dim(width_key, i), dim(thickness_key, i)
        return (width + r" $\times$ " + thickness) if (width and thickness) else ""

    general = T.table(
        "Girder General Information", "girder_general",
        ("Girder", "Member ID", "Design Mode", "Girder Type", "Girder Symmetry"),
        [(_tex(label), _tex(member_id), _render_value(input_dict, KEY_DESIGN_MODE),
          _render_value(input_dict, key(KEY_MP_GIRDER_TYPE, i)),
          _render_value(input_dict, key(KEY_MP_GIRDER_SYMMETRY, i)))
         for i, (label, member_id) in enumerate(entries, start=1)],
    )
    dimensions = T.table(
        "Girder Section Dimensions", "girder_dimensions",
        ("Girder", "Total Depth, $D$ (mm)", "Web, $t_w$ (mm)",
         r"Top Flange, $b_{tf} \times t_{tf}$ (mm)", r"Bottom Flange, $b_{bf} \times t_{bf}$ (mm)"),
        [(_tex(label), dim(KEY_MP_GIRDER_DEPTH, i), dim(KEY_MP_GIRDER_WEB_THICKNESS, i),
          pair(KEY_MP_GIRDER_TOP_FLANGE_WIDTH, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, i),
          pair(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, i))
         for i, (label, _) in enumerate(entries, start=1)],
    )

    def stiffener(yes_no, spacing, thickness):
        parts = [p for p in (yes_no,
                             ("Spacing: " + spacing + " mm") if spacing else "",
                             ("Thickness: " + thickness + " mm") if thickness else "") if p]
        return "; ".join(parts)

    restraint_rows = []
    for i, (label, _) in enumerate(entries, start=1):
        v = lambda base: _render_value(input_dict, key(base, i))
        number = v(KEY_MP_STIFFENER_NO_BEARING_STIFFENERS)
        restraint_rows.append((
            _tex(label),
            "; ".join(p for p in (v(KEY_MP_GIRDER_TORSIONAL_RESTRAINT), v(KEY_MP_GIRDER_WARPING_RESTRAINT)) if p),
            v(KEY_MP_GIRDER_WEB_TYPE),
            stiffener(v(KEY_MP_STIFFENER_INTERMEDIATE), v(KEY_MP_STIFFENER_INTERMEDIATE_SPACING),
                      v(KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS)),
            v(KEY_MP_STIFFENER_LONGITUDINAL),
            stiffener(("No.: " + number) if number else "", v(KEY_MP_STIFFENER_SPACING),
                      v(KEY_MP_STIFFENER_BEARING_THICKNESS)),
        ))
    restraints = T.table(
        "Girder Restraint and Stiffener Details", "girder_restraints",
        ("Girder", "Torsional / Warping Restraint", "Web Philosophy", "Intermediate Stiffeners",
         "Longitudinal Stiffeners", "Bearing Stiffeners"),
        restraint_rows,
    )
    return general + dimensions + restraints


def _bracing_tables(input_dict) -> str:
    n = max(len(girder_entries_or_default(input_dict)), 2)

    def cb(base, i):
        return _render_value(input_dict, f"{base}.G{i}G{i + 1}.B{i}M1")

    def ed(base, i):
        return _render_value(input_dict, f"{base}.G{i}G{i + 1}.E{i}M1")

    cross = T.table(
        "Member Properties: Cross Bracing Details", "bracing_details",
        ("Location", "Member IDs", "Type of Bracing", "Bracing Section", "Spacing (m)"),
        [(cb(KEY_MP_CB_SELECT_GIRDERS, i), cb(KEY_MP_CB_MEMBER_ID, i), cb(KEY_MP_CB_TYPE, i),
          cb(KEY_MP_CB_BRACING_SECTION_DESIGNATION, i), cb(KEY_MP_CB_SPACING, i)) for i in range(1, n)],
    )
    diaphragm = T.table(
        "Member Properties: End Diaphragm Details", "diaphragm_details",
        ("Location", "Member IDs", "Type of Diaphragm", "Section"),
        [(ed(KEY_MP_ED_SELECT_GIRDERS, i), ed(KEY_MP_ED_MEMBER_ID, i), ed(KEY_MP_ED_TYPE, i),
          ed(KEY_MP_ED_BRACING_SECTION_DESIGNATION, i)) for i in range(1, n)],
    )
    return cross + diaphragm


def _shear_connector_table(output_dict) -> str:
    # Stud properties are results of the design run (store_design_results).
    od = output_dict or {}
    return T.unit_table(
        "Shear Connector Details",
        [
            ("Stud Diameter", _render_value(od, KEY_SD_SHEAR_DIAMETER), U.mm, "IRC 22 Cl. 606.6"),
            ("Stud Height", _render_value(od, KEY_SD_SHEAR_HEIGHT), U.mm, "IRC 22 Cl. 606.6"),
            (r"Stud Yield Strength, $f_y$", _render_value(od, KEY_SD_SHEAR_YIELD_STRENGTH), U.MPa, "IRC 22 Cl. 606.3"),
            (r"Stud Ultimate Strength, $f_u$", _render_value(od, KEY_SD_SHEAR_ULTIMATE_STRENGTH), U.MPa, "IRC 22 Cl. 606.3"),
            ("No. of Studs per Section", _render_value(od, KEY_SD_SHEAR_STUDS_PER_SECTION), U.none, "Across the flange width"),
        ],
        label="subsec:shear-connectors",
    )


def _safety_factors_table(input_dict) -> str:
    return T.table(
        "Partial Safety Factors", "key_value_wide_key",
        ("Partial Safety Factor", S.TEXT.value),
        [
            (r"$\gamma_{M0}$ (Yielding / Buckling)", _render_value(input_dict, KEY_DO_GAMMA_M0)),
            (r"$\gamma_{M1}$ (Ultimate Stress)", _render_value(input_dict, KEY_DO_GAMMA_M1)),
            (r"$\gamma_C$ (Concrete, Basic)", _render_value(input_dict, KEY_DO_GAMMA_C_BASIC)),
            (r"$\gamma_s$ (Reinforcement)", _render_value(input_dict, KEY_DO_GAMMA_S)),
            (r"$\gamma_v$ (Shear Connectors)", _render_value(input_dict, KEY_DO_GAMMA_V)),
            (r"$\gamma_{fft}$ (Fatigue Load)", _render_value(input_dict, KEY_DO_GAMMA_FLT)),
            (r"$\gamma_{Mft}$ (Fatigue Strength)", _render_value(input_dict, KEY_DO_GAMMA_MF)),
        ],
        note="All values are per IRC 22 Table 1 unless user-modified.",
        label="subsec:safety-factors",
    )


# ---------------------------------------------------------------------------
# Chapter
# ---------------------------------------------------------------------------

def ch2_input_parameters(m, input_dict, output_dict=None):
    return "\n".join([
        r"\chapter{Input Parameters}",
        "",
        "This section documents all inputs provided to OsdagBridge. User-provided inputs are clearly "
        "distinguished from software-assumed defaults. Where the user did not supply a value, the software has "
        r"applied the IRC/IS code default or an empirical guideline; these are annotated with an asterisk (\sdstar{}).",
        "",
        r"\section{Basic Inputs (User-Defined)}",
        r"\label{sec:basic-inputs}",
        r"\rptnote{These inputs are mandatory and were provided by the user.}",
        _basic_input_tables(m, input_dict),
        r"\section{Additional Inputs}",
        r"\label{sec:additional-inputs}",
        "Where the user has modified additional inputs, those values are reported here. Where no modification "
        "was made, the software default is shown.",
        _section_tables(input_dict),
        _girder_tables(input_dict),
        _bracing_tables(input_dict),
        _shear_connector_table(output_dict),
        _safety_factors_table(input_dict),
    ]) + "\n"
