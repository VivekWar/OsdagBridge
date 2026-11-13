"""Unit tests for the report layout system (styles / tables / figures / charts).

They check the properties the report refactoring guarantees, without running
LaTeX: repeated table headers, keep-together row groups, the single source of
formatting, the live-load tables and the generated bar charts.
"""
import os
import re

import pytest

from osdagbridge.core.reports import charts, design_summary as DS
from osdagbridge.core.reports import figures as F
from osdagbridge.core.reports import styles as S
from osdagbridge.core.reports import tables as T
from osdagbridge.core.reports.data_bridge import ReportDataBridge
from osdagbridge.core.reports.live_loads import (
    VEHICLE_CLASSES, footpath_load, impact_factor, selected_vehicle_rows,
)
from osdagbridge.core.reports.report_utils import _tex, dimension_mm, fmt_num
from osdagbridge.core.utils.common import (
    KEY_FOOTPATH, KEY_LL_IRC_70R_WHEELED, KEY_LL_IRC_CLASS_A, KEY_SPAN,
)

REPORTS_DIR = os.path.dirname(os.path.abspath(S.__file__))
CHAPTER_FILES = sorted(
    f for f in os.listdir(REPORTS_DIR)
    if re.fullmatch(r"chap\d+\.py|executive_summary\.py", f)
)


# --------------------------------------------------------------------------
# 1. Repeated table headers (LongTable)
# --------------------------------------------------------------------------

def _simple_table(**kwargs):
    return T.table("Sample", "key_value", ("Parameter", "Value"),
                   [("a", "1"), ("b", "2"), ("c", "3")], **kwargs)


def test_table_is_a_longtable_with_repeated_header():
    tex = _simple_table()
    assert r"\begin{longtable}" in tex and r"\end{longtable}" in tex
    # first-page header, header for every following page, and the footers
    for marker in (r"\endfirsthead", r"\endhead", r"\endfoot", r"\endlastfoot"):
        assert tex.count(marker) == 1
    first, rest = tex.split(r"\endfirsthead")
    repeated = rest.split(r"\endhead")[0]
    header_row = r"\rpthead{Parameter} & \rpthead{Value}"
    assert header_row in first and header_row in repeated
    # the repeated caption is marked and does not create a second number
    assert r"\caption[]{Sample" + S.TABLE.continued_caption_suffix + "}" in repeated
    assert r"\rptcontinued{2}" in tex            # "Continued on next page" foot


def test_two_level_header_is_repeated_too():
    tex = T.table("Vehicles", "vehicle_live_load",
                  ("Vehicle", "Total Load (kN)", "Impact Factor",
                   T.Span("Braking Load", ("Considered?", "Value (kN)", "Eccentricity (m)"))),
                  [("Class A", "543.5", "1.207", "Yes", "108.7", "1.20")])
    assert tex.count(r"\multicolumn{3}{c|}{\rpthead{Braking Load}}") == 2
    assert tex.count(r"\rpthead{Eccentricity (m)}") == 2


# --------------------------------------------------------------------------
# 2. Layout: groups stay together, notes stay with the table
# --------------------------------------------------------------------------

def test_group_rows_cannot_be_separated_by_a_page_break():
    rows = [T.Group("G4", [("Depth", "1670"), ("Width", "510"), ("Web", "10")])]
    tex = T.table("Girder", "group_property_value", ("Girder", "Property", "Value", "Unit"),
                  [T.Group(g.label, [r + ("mm",) for r in g.rows]) for g in rows])
    body = tex.split(r"\endlastfoot")[1]
    lines = [ln.rstrip("%") for ln in body.splitlines() if ln.strip()]
    data = [ln for ln in lines if "&" in ln]
    assert len(data) == 3
    # every row of the group except the last forbids a break after it ...
    assert all(ln.endswith(r"\\*") for ln in data[:-1])
    # ... and so do the partial rules between them (no \hline / \cline inside)
    inner = body.split(data[0])[1].split(data[-1])[0]
    assert r"\hline" not in inner and r"\cline" not in inner
    assert inner.count(r"\noalign{\nobreak}") == 2
    assert r"\multirow{3}{=}" in data[0]


def test_note_is_the_last_row_and_is_kept_with_the_table():
    tex = _simple_table(note="Some note.")
    body = tex.split(r"\endlastfoot")[1].split(r"\end{longtable}")[0]
    lines = [ln.rstrip("%") for ln in body.splitlines() if ln.strip()]
    assert r"\tablenote{Some note.}" in lines[-1]
    last_data = [ln for ln in lines if ln.startswith("c &")][0]
    assert last_data.endswith(r"\\*")
    assert r"\tablenote" not in tex.split(r"\end{longtable}")[1]


def test_short_tables_are_kept_whole_and_long_tables_may_break():
    short = _simple_table()
    assert re.search(r"\\rptneedspace\{\d+pt\}", short)
    long_rows = [(f"row {i}", str(i)) for i in range(80)]
    long = T.table("Long", "key_value", ("Parameter", "Value"), long_rows)
    assert not re.search(r"\\rptneedspace\{\d+pt\}", long)


def test_every_table_spans_the_text_width():
    for name, layout in S.TABLE_LAYOUTS.items():
        spec = T._column_spec(layout)
        fractions = [float(x) for x in re.findall(r"\{([0-9.]+)\\rptTableWidth\}", spec)]
        assert len(fractions) == layout.n_cols, name
        assert abs(sum(fractions) - 1.0) < 1e-3, name


def test_page_geometry_keeps_the_footer_clear_of_the_text():
    mm = lambda v: float(v.replace("mm", ""))
    # the footer baseline sits inside the bottom margin, below the text area
    assert mm(S.PAGE.foot_skip) < mm(S.PAGE.margin_bottom)
    assert mm(S.PAGE.margin_bottom) >= 25
    preamble = S.preamble_tex()
    assert r"\vspace{-" not in preamble.split("running header / footer")[1]   # no negative skips
    assert r"\newcommand{\rptneedspace}" in preamble


# --------------------------------------------------------------------------
# 6. Centralised style module is the single source of formatting
# --------------------------------------------------------------------------

FORBIDDEN_IN_CHAPTERS = [
    r"\begin{longtable}", r"\begin{tabular}", r"\hline", r"\cline", r"\multirow",
    r"\textcolor", r"\color{", r"\definecolor", r"\includegraphics", r"\setlength",
    r"\vspace", r"\newpage", r"\footnotesize", r"\small", r"\Large", r"\bfseries",
    r"\textbf{", r"\textit{", r"\arraystretch", r"\tabcolsep", r"\captionsetup",
]


@pytest.mark.parametrize("filename", CHAPTER_FILES)
def test_chapter_files_contain_no_formatting_rules(filename):
    with open(os.path.join(REPORTS_DIR, filename), encoding="utf-8") as fh:
        source = fh.read()
    found = [token for token in FORBIDDEN_IN_CHAPTERS if token in source]
    assert not found, f"{filename} hard-codes formatting: {found}"
    # explicit lengths (cm / pt / mm column widths) do not belong in chapters either
    assert not re.search(r"\{\s*\d+(\.\d+)?\s*(cm|pt|mm|em)\s*\}", source), filename


def test_layout_names_used_by_chapters_exist():
    used = set()
    for filename in CHAPTER_FILES:
        with open(os.path.join(REPORTS_DIR, filename), encoding="utf-8") as fh:
            source = fh.read()
        used |= set(re.findall(r'T\.table\(\s*[^,]+?,\s*"([a-z_]+)"', source, flags=re.S))
        used |= set(re.findall(r'layout="([a-z_]+)"', source))
    assert used, "no layouts found"
    assert used <= set(S.TABLE_LAYOUTS), used - set(S.TABLE_LAYOUTS)


def test_preamble_defines_every_palette_colour_and_macro():
    preamble = S.preamble_tex("Project", "Job")
    for name, value in S.COLORS.as_dict().items():
        assert r"\definecolor{%s}{HTML}{%s}" % (name, value) in preamble
    for macro in ("rpthead", "rptband", "rptpass", "rptfail", "rptwarn", "rptover", "tablenote",
                  "rptcontinued", "sdstar", "rptfrontchapter", "rptfiguresection"):
        assert "{\\%s}" % macro in preamble, macro
    assert S.status_tex("PASS") == r"\rptpass{}" and S.status_tex("fail") == r"\rptfail{}"
    assert S.ratio_tex(1.87) == r"\rptover{1.87}" and S.ratio_tex(0.5) == "0.50"


def test_document_arguments_come_from_the_page_style():
    args = S.document_arguments()
    assert args["geometry_options"]["bottom"] == S.PAGE.margin_bottom
    assert args["documentclass"] == S.PAGE.document_class
    assert set(S.CHART.element_colors) == set(DS.ELEMENTS)


# --------------------------------------------------------------------------
# 3. Live-load tables: only the vehicles ticked in the Loading tab
# --------------------------------------------------------------------------

def test_only_selected_vehicles_are_listed_in_ui_order():
    inputs = {KEY_SPAN: 30, KEY_LL_IRC_70R_WHEELED: True, KEY_LL_IRC_CLASS_A: True}
    rows = selected_vehicle_rows(inputs)
    assert [r.vehicle for r in rows] == ["Class A", "Class 70R Wheeled"]
    class_a = rows[0]
    assert class_a.total_load_kN == pytest.approx(55.4 * 9.81)
    assert class_a.impact_factor == pytest.approx(1 + 9 / (13.5 + 30))
    assert class_a.braking_considered and class_a.braking_value_kN == pytest.approx(0.2 * 55.4 * 9.81)
    assert selected_vehicle_rows({KEY_SPAN: 30}) == []
    assert len(VEHICLE_CLASSES) == 8


def test_impact_factor_rules_irc6_cl_208():
    assert impact_factor("tracked", 30) == pytest.approx(1.10)
    assert impact_factor("wheeled", 20) == pytest.approx(1.25)
    assert impact_factor("wheeled", 30) == pytest.approx(1 + 9 / 43.5)
    assert impact_factor("none", 30) == 1.0


def test_footpath_load_is_reported_separately():
    none = footpath_load({KEY_FOOTPATH: "None"})
    assert not none.provided
    both = footpath_load({KEY_FOOTPATH: "Both"})
    assert both.provided and both.intensity_kN_m2 and both.intensity_kN_m2 > 0

    from osdagbridge.core.reports.chap3 import ch3_loads
    tex = ch3_loads({KEY_SPAN: 30, KEY_LL_IRC_CLASS_A: True, KEY_FOOTPATH: "Both"})
    assert r"\caption{Vehicle Live Loads (LL) --- IRC 6}" in tex
    assert r"\caption{Footpath Live Load --- IRC 6}" in tex
    assert "Centrifugal Force" in tex and r"\rpthead{Unit}" in tex


# --------------------------------------------------------------------------
# 4 / 5. Bar charts
# --------------------------------------------------------------------------

def _items():
    return [
        charts.URItem(DS.GIRDERS, "Moment", 0.23), charts.URItem(DS.GIRDERS, "Fatigue", 1.87),
        charts.URItem(DS.DECK, "Flexure", 0.91), charts.URItem(DS.BRACING, "Compression", 0.93),
        charts.URItem(DS.DIAPHRAGMS, "Compression", None),
    ]


def test_ur_charts_are_written_as_images(tmp_path):
    out = str(tmp_path / "images")
    for build in (charts.utilization_by_element_chart, charts.utilization_by_check_chart):
        path = build(_items(), out)
        assert path and os.path.getsize(path) > 5000 and path.endswith("." + S.CHART.image_format)
    governing = charts.governing_by_element(_items())
    assert list(governing) == list(DS.ELEMENTS)
    assert governing[DS.GIRDERS].ur == pytest.approx(1.87) and governing[DS.DIAPHRAGMS] is None
    assert charts.utilization_by_element_chart([charts.URItem(DS.DECK, "x", None)], out) is None


def test_ur_threshold_is_a_red_dashed_line_at_one():
    fig, ax = charts._new_figure(S.CHART.size_wide)
    charts._draw_threshold(ax, 2.0)
    line = ax.get_lines()[0]
    assert list(line.get_ydata()) == [1.0, 1.0]
    assert line.get_linestyle() == "--"
    assert line.get_color().lower() == "#" + S.COLORS.chartThreshold.lower()


def test_material_charts(tmp_path):
    out = str(tmp_path)
    steel = charts.steel_tonnage_chart({"Girders": 41.1, "Cross Bracing": 0.7, "End Diaphragms": 1.2}, out)
    mix = charts.concrete_vs_rebar_chart(85.5, 10.26, out)
    assert steel and mix and os.path.exists(steel) and os.path.exists(mix)
    assert charts.steel_tonnage_chart({"Girders": None}, out) is None
    assert charts.concrete_vs_rebar_chart(None, 10.0, out) is None
    # embedded through a PyLaTeX Figure, with a path relative to the build directory
    tex = F.figure(F.asset_path(steel, out), "Steel tonnage", width="chart")
    assert r"\begin{figure}" in tex and r"\includegraphics" in tex and r"\caption{Steel tonnage}" in tex
    assert os.path.basename(out) + "/chart_steel_tonnage" in tex and str(tmp_path.parent) not in tex


# --------------------------------------------------------------------------
# Design summary + content helpers
# --------------------------------------------------------------------------

def test_design_summary_reads_stored_results_only():
    check = lambda cid, name, d, c, unit: {"check_id": cid, "name": name, "demand": d, "capacity": c,
                                           "demand_unit": unit, "dcr": d / c, "status": "PASS"}
    output = {"design_results": {"per_girder": {
        "G1": {"checks": [check(1, "ULS Flexure", 100.0, 400.0, "kNm"), check(8, "Fatigue", 150.0, 100.0, "MPa")]},
        "G2": {"checks": [check(1, "ULS Flexure", 200.0, 400.0, "kNm")]},
    }}}
    rows = DS.collect(ReportDataBridge(output, {}))
    moment = next(r for r in rows if r.element == DS.GIRDERS and r.check == "Moment")
    assert moment.ur == pytest.approx(0.5) and moment.demand == 200.0 and moment.passed
    governing = DS.governing(rows)
    assert governing[DS.GIRDERS].check == "Fatigue" and not governing[DS.GIRDERS].passed
    assert governing[DS.BRACING] is None        # nothing stored -> not evaluated
    assert set(DS.by_element(rows)) == set(DS.ELEMENTS)


def test_content_helpers():
    assert _tex("a_b & 50%") == r"a\_\allowbreak{}b \& 50\%"
    assert _tex("Leg ≤ H") == r"Leg $\leq$ H"
    assert fmt_num(-0.0001, 2) == "0.00" and fmt_num(11.399999, 4, strip=True) == "11.4"
    assert fmt_num(None) == ""
    assert dimension_mm(1.67) == "1670" and dimension_mm(510) == "510"


# --------------------------------------------------------------------------
# Whole document (assembled with PyLaTeX, not compiled here)
# --------------------------------------------------------------------------

def test_document_assembles_from_an_empty_design(tmp_path):
    from pylatex import Document
    from osdagbridge.core.reports.report_generator import (
        ReportFigures, ReportMetadata, ReportOptions, ReportPayload, build_document,
    )
    metadata = ReportMetadata("Test Bridge", "Pune, Maharashtra", "Designer", "Client", "Company",
                              job_number="J-1", report_date="2026-01-01")
    options = ReportOptions(sections=["loads", "analysis", "design_checks", "drawings"],
                            include_figures=True, include_toc=True, include_pdf=True)
    payload = ReportPayload(metadata, options, {KEY_SPAN: 30, KEY_LL_IRC_CLASS_A: True}, {}, [], ReportFigures())

    doc = build_document(payload, {}, None, None, str(tmp_path / "images"))
    assert isinstance(doc, Document)
    tex = doc.dumps()

    assert tex.startswith(r"\documentclass[" + ",".join(S.PAGE.class_options()) + "]{report}")
    assert r"\geometry{" in tex and "bottom=" + S.PAGE.margin_bottom in tex
    for chapter in ("Project Information", "Input Parameters", "Loads and Load Combinations",
                    "Analysis Results", "Design Checks", "Drawings and Visualizations",
                    r"Material Take-off \& Quantity Summary"):
        assert r"\chapter{%s}" % chapter in tex
    # every table is a longtable with a header for the first and the following pages
    n_tables = tex.count(r"\begin{longtable}")
    assert n_tables > 40
    assert tex.count(r"\endfirsthead") == n_tables and tex.count(r"\endhead") == n_tables
    assert r"\begin{tabular}" in tex.split(r"\end{titlepage}")[0]       # only the title block
    assert r"\begin{tabular}" not in tex.split(r"\end{titlepage}")[1]
    # Section 5.5 and chapter 7 carry their figures even when nothing could be charted
    assert tex.count(r"\begin{figure}") >= 4
    assert r"\label{fig:ur-by-element}" in tex and r"\label{fig:steel-tonnage}" in tex
