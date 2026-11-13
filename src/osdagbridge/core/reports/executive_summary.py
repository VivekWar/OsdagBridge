# =============================================================================
# Executive Summary
# Presentation only — formatting comes from styles.py via tables.py / figures.py.
# =============================================================================
from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SD_SECTION_DESIGNATION,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
)

from . import design_summary as DS
from . import figures as F
from . import styles as S
from . import tables as T
from .data_bridge import ReportDataBridge
from .report_utils import _render_value, _tex, girder_entries_or_default

NA = S.TEXT.not_applicable


def _girder_status(per_girder: dict):
    """(failing check names, governing check name) over all girders."""
    failing, governing_name, governing_dcr = [], "", None
    for name, data in (per_girder or {}).items():
        if str(name).startswith("EB"):          # edge-beam pseudo girders
            continue
        for chk in (data.get("checks") or []):
            try:
                dcr = float(chk.get("dcr")) if chk.get("dcr") is not None else None
            except (TypeError, ValueError):
                dcr = None
            check_name = str(chk.get("name", "")).strip()
            failed = ("FAIL" in str(chk.get("status", "")).upper()) or (dcr is not None and dcr > 1.0)
            if failed and check_name and check_name not in failing:
                failing.append(check_name)
            if dcr is not None and (governing_dcr is None or dcr > governing_dcr):
                governing_dcr, governing_name = dcr, check_name
    return failing, governing_name


def _overview_table(input_dict, per_girder, summary) -> str:
    failing, governing_name = _girder_status(per_girder)
    if not per_girder:
        status = ""
    elif failing:
        status = r"\rptfail{} --- " + _tex(", ".join(failing))
    else:
        status = r"\rptpass{}"

    evaluated = [(r.ur, element) for element, r in DS.governing(summary).items() if r is not None]
    if evaluated:
        max_ur, element = max(evaluated)
        overall_ur = S.ratio_tex(max_ur) + " (" + _tex(element) + ")"
    else:
        overall_ur = ""

    return T.key_value_table(
        "Project Overview",
        [
            ("Bridge Type", _render_value(input_dict, KEY_STRUCTURE_TYPE)),
            ("Design Standards", "IRC 5, IRC 6, IRC 22, IRC 24, IS 800"),
            ("Span", _render_value(input_dict, KEY_SPAN, " m")),
            ("Carriageway Width", _render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, " m")),
            ("No. of Girders", _render_value(input_dict, KEY_TS_NO_OF_GIRDERS)),
            ("Girder Spacing", _render_value(input_dict, KEY_TS_GIRDER_SPACING, " m")),
            ("Deck Thickness", _render_value(input_dict, KEY_TS_DECK_THICKNESS, " mm")),
            ("Overall Design Status (girders)", status),
            ("Governing Girder Check", _tex(governing_name)),
            ("Overall Utilization Ratio (max.)", overall_ur),
        ],
        layout="key_value_wide_key",
        label="tab:project-overview",
    )


def _girder_table(input_dict, output_dict, per_girder) -> str:
    section = _render_value(output_dict, KEY_SD_SECTION_DESIGNATION)
    rows = []
    for i, (label, member_id) in enumerate(girder_entries_or_default(input_dict), start=1):
        checks = (per_girder.get(f"G{i}", {}) or {}).get("checks") or []
        if checks:
            ctrl = max(checks, key=lambda c: c.get("dcr") or 0.0)
            ur = ctrl.get("dcr")
            rows.append((_tex(label), _tex(member_id), section, _tex(ctrl.get("name", "")),
                         S.ratio_tex(ur), S.status_tex(ctrl.get("status"))))
        else:
            rows.append((_tex(label), _tex(member_id), section, None, None, None))
    return T.table(
        "Final Girder Sections (after optimization)", "girder_sections",
        ("Girder", "Member ID", r"Section Designation\newline ($D \times b_{tf} \times t_{tf} \times b_{bf} \times t_{bf}$, mm)",
         "Governing Check", "UR", "Status"),
        rows,
        note=r"Utilization ratio (UR) = demand / capacity. A value $\leq 1.0$ indicates a passing check.",
        label="tab:final-girder-sections",
    )


def _outcome_table(summary) -> str:
    rows = []
    for element, r in DS.governing(summary).items():
        if r is None:
            rows.append((_tex(element), "Not evaluated", None, None))
        else:
            rows.append((_tex(element), _tex(r.check), S.ratio_tex(r.ur), S.pass_fail(r.passed)))
    return T.table(
        "Key Design Outcomes by Structural Element", "element_outcome",
        ("Structural Element", "Governing Check", "Utilization Ratio", "Status"),
        rows,
        note="Details of every check are given in Chapter 5; Section 5.5 shows the utilization-ratio charts.",
        label="tab:key-outcomes",
    )


def executive_summary(input_dict, output_dict, fig_paths) -> str:
    design_results = output_dict.get("design_results", {}) or {}
    per_girder = design_results.get("per_girder", {}) or {}
    summary = DS.collect(ReportDataBridge(output_dict, input_dict))

    return "\n".join([
        r"\rptfrontchapter{Executive Summary}",
        r"\rptfrontnumbering",
        "This section provides a concise summary of the bridge design, key inputs, governing loads, and "
        "final design outcomes.",
        r"\rptfrontsection{Project Overview}",
        r"\label{sec:project-overview}",
        _overview_table(input_dict, per_girder, summary),
        F.figure(fig_paths.get('girder_top'), "Overall bridge plan", width="full", label="fig:es-plan"),
        F.figure(fig_paths.get('cross_section'),
                 "Typical cross-section (girders, deck, barriers, footpath)", width="full",
                 label="fig:es-cross-section"),
        F.figure(fig_paths.get('final_geometry'), "3D view of the bridge superstructure", width="full",
                 label="fig:es-3d"),
        _girder_table(input_dict, output_dict, per_girder),
        r"\rptfrontsection{Key Design Outcomes Summary}",
        r"\label{sec:key-outcomes}",
        _outcome_table(summary),
        r"\rptfrontsection{Design Assumptions and Limitations}",
        r"\label{sec:es-assumptions}",
        r"\begin{itemize}",
        r"\item Additional inputs not provided by the user were assumed by software per IRC/IS code defaults "
        "or practical consideration.",
        r"\item Grillage analysis was performed using OSPGrillage assuming simply supported I-girders.",
        r"\item Substructure and foundation design are not included in this report.",
        r"\item Splice connections and bearings are not designed in this version.",
        r"\end{itemize}",
        r"\rptmainnumbering",
    ]) + "\n"
