# =============================================================================
# OsdagBridge — Report Style System (single source of truth)
# =============================================================================
"""Centralised formatting and style configuration for the design report.

Every visual decision of the PDF report lives in this module: page geometry,
fonts, colours, table metrics, column layouts, header/footer theme, figure
widths, vertical spacing and the chart (matplotlib) theme.

The chapter generators (``chap1.py`` … ``chap9.py``, ``executive_summary.py``),
the table/figure builders (``tables.py``, ``figures.py``) and the chart module
(``charts.py``) import their formatting rules *exclusively* from here.  To
restyle the whole report — change a colour, widen the margins, increase the
table row padding, swap the chart palette — edit the values below; no chapter
file needs to be touched.

Layout of this module
---------------------
1.  ``PAGE``            page geometry + base typography (document level)
2.  ``COLORS``          colour palette (shared by LaTeX and matplotlib)
3.  ``FONTS``           font switches for headings, tables, captions, notes
4.  ``SPACING``         vertical rhythm and page-break thresholds
5.  ``TABLE``           table metrics (padding, rules, header look)
6.  ``TABLE_LAYOUTS``   named column layouts (alignment + relative widths)
7.  ``HEADER_FOOTER``   running header / footer theme
8.  ``FIGURE``          figure widths
9.  ``CHART``           matplotlib theme for the generated bar charts
10. ``UNITS`` / ``TEXT``  unit strings and fixed wording
11. LaTeX emitters      ``latex_packages()``, ``preamble_tex()`` … which turn
                        the values above into the document preamble.

Only the Python standard library is used here so the module can be imported
from anywhere (including unit tests) without side effects.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Dict, List, Optional, Tuple


# =============================================================================
# 1. PAGE GEOMETRY AND BASE TYPOGRAPHY
# =============================================================================

@dataclass(frozen=True)
class PageStyle:
    """Document-level settings (``\\documentclass`` and ``geometry``)."""

    document_class: str = "report"
    paper: str = "a4paper"
    font_size: str = "11pt"

    # Margins. The bottom margin is larger than the top one because the footer
    # carries two stacked elements (optional "software default" note + rule +
    # footer text) that must never touch the last line / table rule of a page.
    margin_left: str = "20mm"
    margin_right: str = "20mm"
    margin_top: str = "27mm"
    margin_bottom: str = "30mm"

    head_height: str = "15pt"      # >= 1 line of header text (avoids fancyhdr warnings)
    head_sep: str = "7mm"          # header rule  -> first text line
    foot_skip: str = "15mm"        # last text line -> footer baseline

    line_stretch: float = 1.12     # body line spacing (setspace)
    paragraph_skip: str = "0.5em"

    def geometry_options(self) -> Dict[str, str]:
        """Options passed to the ``geometry`` package (via PyLaTeX)."""
        return {
            "left": self.margin_left,
            "right": self.margin_right,
            "top": self.margin_top,
            "bottom": self.margin_bottom,
            "headheight": self.head_height,
            "headsep": self.head_sep,
            "footskip": self.foot_skip,
        }

    def class_options(self) -> List[str]:
        return [self.font_size, self.paper]

    # A4 paper size, used only for the size estimates of the table builder.
    paper_width_mm: float = 210.0
    paper_height_mm: float = 297.0

    @staticmethod
    def _mm(length: str) -> float:
        return float(length.replace("mm", "").strip())

    def text_width_pt(self) -> float:
        mm = self.paper_width_mm - self._mm(self.margin_left) - self._mm(self.margin_right)
        return mm * 72.27 / 25.4

    def text_height_pt(self) -> float:
        mm = self.paper_height_mm - self._mm(self.margin_top) - self._mm(self.margin_bottom)
        return mm * 72.27 / 25.4


PAGE = PageStyle()


# =============================================================================
# 2. COLOUR PALETTE
# =============================================================================

@dataclass(frozen=True)
class Colors:
    """Colour palette as 6-digit hex strings (no leading ``#``).

    Each attribute name is also the LaTeX colour name (``\\color{osdagGreen}``),
    so the same palette drives the PDF text/tables and the matplotlib charts.
    """

    # --- brand ---------------------------------------------------------------
    osdagGreen: str = "91B014"     # Osdag brand green (rules, accents)
    osdagDark: str = "55690C"      # darker brand tone (headings, captions)

    # --- text ----------------------------------------------------------------
    rptText: str = "1F1F1F"        # body text
    rptMuted: str = "5C5C5C"       # notes, secondary text
    rptPlaceholder: str = "8A8A8A"

    # --- tables --------------------------------------------------------------
    rptHeadBg: str = "E4ECC3"      # table header fill (brand tint)
    rptBandBg: str = "F2F5E3"      # sub-heading band rows inside a table
    rptRule: str = "4D4D4D"        # table grid lines

    # --- status --------------------------------------------------------------
    rptPass: str = "2E7D32"
    rptWarn: str = "B26A00"
    rptFail: str = "C62828"
    rptInfo: str = "1F5FA8"        # log: warnings in the design log

    # --- chart series (primary structural elements) ---------------------------
    chartGirder: str = "2F6690"    # steel plate girders
    chartDeck: str = "8D99AE"      # concrete deck slab
    chartBracing: str = "3A9D8F"   # cross bracing
    chartDiaphragm: str = "C17C2D" # end diaphragms
    chartRebar: str = "B5534B"     # reinforcement steel
    chartConcrete: str = "9AA3AD"  # concrete
    chartThreshold: str = "D32F2F" # UR = 1.0 reference line
    chartGrid: str = "D9D9D9"

    def as_dict(self) -> Dict[str, str]:
        return {f.name: getattr(self, f.name) for f in fields(self)}

    def mpl(self, name: str) -> str:
        """Colour in matplotlib notation (``#RRGGBB``)."""
        return "#" + getattr(self, name)


COLORS = Colors()


# =============================================================================
# 3. FONTS
# =============================================================================

@dataclass(frozen=True)
class FontStyle:
    """LaTeX font switches. Values are raw LaTeX declarations."""

    # Font encoding / family (set through PyLaTeX ``Document`` arguments).
    font_encoding: str = "T1"
    input_encoding: str = "utf8"
    use_latin_modern: bool = True

    # Headings are set in the sans-serif companion of the body font.
    heading_family: str = r"\sffamily"
    chapter: str = r"\sffamily\LARGE\bfseries"
    section: str = r"\sffamily\Large\bfseries"
    subsection: str = r"\sffamily\large\bfseries"
    title_main: str = r"\sffamily\Huge\bfseries"
    title_sub: str = r"\sffamily\large"
    title_kind: str = r"\sffamily\LARGE\bfseries"

    # Tables
    table_body: str = r"\small"
    table_compact: str = r"\footnotesize"     # wide, many-column tables
    table_header: str = r"\bfseries"
    table_band: str = r"\bfseries"

    # Captions / notes / running heads
    caption_label: str = "bf,sf"
    caption_text: str = "sf"
    caption_size: str = "small"
    note: str = r"\footnotesize\itshape"
    running_head: str = r"\sffamily\footnotesize"
    toc_title: str = r"\sffamily\LARGE\bfseries"


FONTS = FontStyle()


# =============================================================================
# 4. VERTICAL SPACING AND PAGE-BREAK THRESHOLDS
# =============================================================================

@dataclass(frozen=True)
class SpacingStyle:
    """Vertical rhythm. All page-break guards are defined here."""

    # Space above / below every table and figure block.
    block_before: str = "10pt"
    block_after: str = "12pt"
    note_gap: str = "3pt"               # table -> note line
    caption_gap: str = "5pt"            # caption <-> table/figure body

    # Page-bottom thresholds: a block only starts on the current page if at
    # least this much vertical space is left, otherwise LaTeX breaks first.
    table_min_start: str = r"9\baselineskip"     # caption + header + >= 2 rows
    figure_min_start: str = r"12\baselineskip"
    # A section heading only starts on the current page if the heading, a
    # short lead-in paragraph and the start of a table still fit below it.
    heading_min_start: str = r"14\baselineskip"
    subheading_min_start: str = r"8\baselineskip"
    # ... and a heading that is directly followed by a figure needs room for
    # the (unbreakable) figure as well.
    figure_heading_min_start: str = r"0.48\textheight"

    # Headings (titlesec): space before / after.
    chapter_before: str = "0pt"
    chapter_after: str = "14pt"
    section_before: str = "16pt"
    section_after: str = "8pt"
    subsection_before: str = "12pt"
    subsection_after: str = "6pt"

    # Lists
    list_item_sep: str = "2pt"
    list_top_sep: str = "4pt"

    # Title page
    title_top: str = "10mm"
    title_logo_gap: str = "14mm"
    title_block_gap: str = "12mm"


SPACING = SpacingStyle()


# =============================================================================
# 5. TABLE METRICS
# =============================================================================

@dataclass(frozen=True)
class TableStyle:
    """Geometry and look shared by every table of the report."""

    col_sep: str = "5pt"                # horizontal cell padding (\tabcolsep)
    col_sep_compact: str = "3pt"        # ... for compact (many-column) tables
    row_stretch: float = 1.32           # vertical cell padding (\arraystretch)
    row_stretch_compact: float = 1.25
    extra_row_height: str = "1pt"       # extra space above text in each row
    rule_width: str = "0.4pt"           # grid line thickness
    header_rule_width: str = "0.9pt"    # heavier rule closing the header

    # Rows kept together on one page. Groups (e.g. all rows of girder "G4")
    # are never split by a page break, so a row-spanning label can no longer
    # drift below the text area into the footer.
    keep_group_together: bool = True
    # Widow / orphan control for tables: at least this many body rows stay
    # together below the header and above the end of a table that is broken
    # across pages (no single row left alone at the top or bottom of a page).
    min_rows_at_start: int = 2
    min_rows_at_end: int = 2

    # Short tables are not split at all: a table whose estimated height is at
    # most this fraction of the text height is moved to the next page as a
    # whole when it does not fit on the current one. Longer tables break
    # between rows (with repeated headers).
    keep_whole_max_fraction: float = 0.55
    # Metrics used for that estimate (points). They only need to be roughly
    # right: an estimate that is too low merely lets the table break normally.
    est_char_width: float = 5.3         # average glyph width, body table font
    est_char_width_compact: float = 4.8
    est_row_height: float = 19.5        # one-line row incl. padding and rule
    est_row_height_compact: float = 17.0
    est_line_height: float = 13.5       # every further wrapped line in a row
    est_line_height_compact: float = 12.5
    est_caption_height: float = 34.0    # caption + gap above the table

    # Text shown when a table continues over a page break.
    continued_caption_suffix: str = " (continued)"
    continued_footer_text: str = "Continued on next page"

    # Header fill / band fill colour names (see ``COLORS``).
    header_bg: str = "rptHeadBg"
    band_bg: str = "rptBandBg"
    rule_color: str = "rptRule"

    empty_cell: str = "---"             # shown for missing values
    # Invisible strut giving a line with a display fraction enough height/depth.
    formula_strut: str = r"\rule[-2.3ex]{0pt}{5.6ex}"


TABLE = TableStyle()


@dataclass(frozen=True)
class TableLayout:
    """A named column layout.

    ``columns`` is a tuple of ``(alignment, weight)`` pairs. ``alignment`` is
    ``l`` / ``c`` / ``r``; the weights are *relative* widths — the table
    builder normalises them so every table spans exactly the text width,
    whatever the page margins are.
    """

    columns: Tuple[Tuple[str, float], ...]
    compact: bool = False               # use the compact font / padding

    @property
    def n_cols(self) -> int:
        return len(self.columns)


def _layout(*columns: Tuple[str, float], compact: bool = False) -> TableLayout:
    return TableLayout(columns=tuple(columns), compact=compact)


# =============================================================================
# 6. NAMED COLUMN LAYOUTS
# =============================================================================
# One entry per kind of table. Chapters refer to a layout by name, e.g.
# ``table(layout="key_value", ...)``; widths/alignments are tuned only here.

TABLE_LAYOUTS: Dict[str, TableLayout] = {
    # ---- generic ------------------------------------------------------------
    "key_value":            _layout(("l", 37), ("l", 63)),
    "key_value_wide_key":   _layout(("l", 47), ("l", 53)),
    "param_value_unit_ref": _layout(("l", 34), ("c", 20), ("c", 14), ("l", 32)),
    "title_block":          _layout(("l", 32), ("l", 68)),

    # ---- chapter 2: inputs --------------------------------------------------
    "girder_general":       _layout(("c", 12), ("c", 14), ("l", 22), ("l", 28), ("l", 24)),
    "girder_dimensions":    _layout(("c", 12), ("c", 18), ("c", 16), ("c", 27), ("c", 27)),
    "girder_restraints":    _layout(("c", 9), ("l", 16), ("l", 14), ("l", 23), ("l", 15), ("l", 23)),
    "bracing_details":      _layout(("c", 16), ("c", 16), ("l", 24), ("l", 28), ("c", 16)),
    "diaphragm_details":    _layout(("c", 18), ("c", 18), ("l", 30), ("l", 34)),

    # ---- chapter 3: loads ---------------------------------------------------
    "vehicle_live_load":    _layout(("l", 26), ("c", 15), ("c", 13), ("c", 15), ("c", 15), ("c", 16)),
    "load_combinations":    _layout(("c", 11), ("l", 31), ("l", 58)),

    # ---- chapter 4: analysis ------------------------------------------------
    "analysis_demands":     _layout(("l", 34), ("c", 13), ("c", 9), ("c", 11),
                                    ("c", 13), ("c", 9), ("c", 11), compact=True),
    "reactions":            _layout(("l", 46), ("c", 27), ("c", 27)),
    "deflection_summary":   _layout(("l", 36), ("c", 22), ("c", 24), ("c", 18)),

    # ---- chapter 5: design checks -------------------------------------------
    "group_property_value": _layout(("c", 12), ("l", 50), ("c", 22), ("c", 16)),
    "group_classification": _layout(("c", 12), ("l", 22), ("c", 22), ("c", 20), ("c", 24)),
    "group_check":          _layout(("c", 10), ("l", 30), ("c", 26), ("c", 21), ("c", 13)),
    "group_required":       _layout(("c", 10), ("l", 32), ("c", 22), ("c", 22), ("c", 14)),
    "girder_fatigue":       _layout(("c", 14), ("c", 24), ("c", 24), ("c", 22), ("c", 16)),
    "girder_summary":       _layout(("c", 8), ("l", 30), ("l", 18), ("c", 13), ("c", 13), ("c", 8), ("c", 10),
                                    compact=True),
    "param_formula_value_ref": _layout(("l", 24), ("c", 36), ("c", 16), ("l", 24)),
    "criterion_spacing":    _layout(("l", 30), ("c", 26), ("c", 28), ("c", 16)),
    "check_value_status":   _layout(("l", 38), ("l", 46), ("c", 16)),
    "location_check":       _layout(("c", 15), ("l", 27), ("c", 24), ("c", 21), ("c", 13)),
    "param_formula_value_status": _layout(("l", 33), ("c", 28), ("c", 26), ("c", 13)),
    "detailing":            _layout(("l", 36), ("c", 25), ("c", 26), ("c", 13)),
    "bracing_section":      _layout(("c", 13), ("l", 22), ("l", 17), ("c", 22), ("c", 13), ("c", 13)),
    "bracing_slenderness":  _layout(("c", 13), ("l", 20), ("c", 12), ("c", 19), ("c", 12), ("c", 12), ("c", 12)),
    "bracing_capacity":     _layout(("c", 10), ("l", 12), ("c", 15), ("l", 24), ("c", 11), ("c", 11), ("c", 7), ("c", 10),
                                    compact=True),
    "overall_summary":      _layout(("c", 14), ("l", 17), ("l", 26), ("c", 14), ("c", 14), ("c", 7), ("c", 8),
                                    compact=True),
    "element_outcome":      _layout(("l", 26), ("l", 34), ("c", 20), ("c", 20)),
    "girder_sections":      _layout(("c", 10), ("c", 14), ("l", 30), ("l", 24), ("c", 10), ("c", 12)),

    # ---- chapter 7: quantities ----------------------------------------------
    "bill_of_materials":    _layout(("c", 7), ("l", 23), ("c", 30), ("c", 8), ("c", 11), ("c", 10), ("c", 11),
                                    compact=True),
    "quantity_summary":     _layout(("l", 40), ("c", 20), ("c", 20), ("c", 20)),

    # ---- chapter 8: standards -----------------------------------------------
    "code_list":            _layout(("c", 16), ("c", 10), ("l", 74)),
}


# =============================================================================
# 7. RUNNING HEADER / FOOTER THEME
# =============================================================================

@dataclass(frozen=True)
class HeaderFooterStyle:
    rule_color: str = "osdagGreen"
    rule_width: str = "0.9pt"
    separator: str = r"\,\textbar\,"                # between header fields
    footer_left: str = (r"Osdag \,\textbar\, FOSSEE \,\textbar\, "
                        r"Indian Institute of Technology Bombay")
    footer_right: str = r"Page \thepage\ of \pageref{LastPage}"
    # Note printed above the footer rule on pages that contain a value marked
    # with the software-default asterisk (\sdstar).
    default_note: str = r"* Software default value"
    note_gap: str = "3pt"          # note -> footer rule
    rule_gap: str = "5pt"          # footer rule -> footer text
    head_rule_gap: str = "3pt"     # header text -> header rule


HEADER_FOOTER = HeaderFooterStyle()


# =============================================================================
# 8. FIGURES
# =============================================================================

@dataclass(frozen=True)
class FigureStyle:
    """Figure widths as fractions of the text width."""

    width_full: float = 0.92       # drawings, executive-summary views
    width_wide: float = 0.85       # chapter 6 CAD views
    width_medium: float = 0.75     # analysis diagrams
    width_chart: float = 0.94      # generated bar charts
    width_third: float = 0.31      # three images side by side
    max_height: str = r"0.42\textheight"   # keeps tall images on the page
    logo_left_width: float = 0.52  # title page logos (fraction of text width)
    logo_right_width: float = 0.30
    logo_right_height: str = "22mm"
    placement: str = "H"           # float placement ("here", via float pkg)

    def width(self, key: str) -> str:
        return f"{getattr(self, 'width_' + key):.2f}" + r"\textwidth"


FIGURE = FigureStyle()


# =============================================================================
# 9. CHART THEME (matplotlib)
# =============================================================================

@dataclass(frozen=True)
class ChartStyle:
    dpi: int = 200
    image_format: str = "png"
    # Figure sizes in inches (width, height). The width matches the text width
    # at ``FIGURE.width_chart`` so fonts are not rescaled in the PDF.
    size_wide: Tuple[float, float] = (6.6, 3.1)
    size_tall: Tuple[float, float] = (6.6, 4.3)
    size_half: Tuple[float, float] = (6.6, 2.9)

    font_family: str = "DejaVu Sans"
    font_size: float = 8.5
    title_size: float = 10.0
    label_size: float = 8.5
    tick_size: float = 8.0
    annotation_size: float = 7.5

    bar_width: float = 0.62
    pad_inches: float = 0.06            # white margin kept around a saved chart
    label_pad_alpha: float = 0.85       # opacity of the pad behind value labels
    bar_edge_color: str = "rptText"
    bar_edge_width: float = 0.4
    grid_color: str = "chartGrid"
    grid_width: float = 0.6

    # Utilization-ratio threshold (UR = 1.0): red dashed reference line.
    threshold_value: float = 1.0
    threshold_color: str = "chartThreshold"
    threshold_style: str = "--"
    threshold_width: float = 1.4
    threshold_label: str = "UR = 1.0 (limit)"
    fail_color: str = "rptFail"         # bars with UR > 1.0
    fail_hatch: str = "///"
    ur_axis_min_top: float = 1.25       # y-axis always shows the 1.0 line

    # Colour (name in ``COLORS``) of each primary structural element.
    element_colors: Dict[str, str] = field(default_factory=lambda: {
        "Steel Plate Girders": "chartGirder",
        "Concrete Deck Slab": "chartDeck",
        "Cross Bracing": "chartBracing",
        "End Diaphragms": "chartDiaphragm",
    })
    material_colors: Dict[str, str] = field(default_factory=lambda: {
        "Girders": "chartGirder",
        "Cross Bracing": "chartBracing",
        "End Diaphragms": "chartDiaphragm",
        "Concrete": "chartConcrete",
        "Reinforcement": "chartRebar",
    })


CHART = ChartStyle()


# =============================================================================
# 10. UNITS AND FIXED WORDING
# =============================================================================

@dataclass(frozen=True)
class Units:
    """Unit strings in LaTeX notation (kept here so they render identically)."""

    kN: str = "kN"
    kNm: str = "kN-m"
    kNm_per_m: str = "kN-m/m"
    kN_per_m: str = "kN/m"
    kN_per_m2: str = r"kN/m\textsuperscript{2}"
    kN_per_m3: str = r"kN/m\textsuperscript{3}"
    N_per_m2: str = r"N/m\textsuperscript{2}"
    mm: str = "mm"
    mm2: str = r"mm\textsuperscript{2}"
    mm2_per_m: str = r"mm\textsuperscript{2}/m"
    cm2_per_m: str = r"cm\textsuperscript{2}/m"
    mm4: str = r"mm\textsuperscript{4}"
    m: str = "m"
    m3: str = r"m\textsuperscript{3}"
    m_per_s: str = "m/s"
    MPa: str = "MPa"
    MT: str = "MT"
    degree: str = r"\textdegree"
    deg_c: str = r"\textdegree C"
    none: str = "---"


UNITS = Units()


@dataclass(frozen=True)
class Wording:
    """Fixed strings reused across chapters."""

    product: str = "OsdagBridge"
    tagline: str = "Open Source Software for Steel Girder Bridge Design"
    report_kind: str = "Design Report"
    status_pass: str = "PASS"
    status_fail: str = "FAIL"
    status_warn: str = "WARN"
    not_applicable: str = "N/A"
    parameter: str = "Parameter"
    value: str = "Value"
    unit: str = "Unit"
    reference: str = "Reference / Remarks"
    toc_title: str = "Table of Contents"
    pdf_subject: str = "Steel girder bridge design report"
    front_number_prefix: str = "ES"       # numbering of executive-summary tables / figures


TEXT = Wording()


# =============================================================================
# 11. LATEX EMITTERS
# =============================================================================
# The functions below translate the configuration above into LaTeX. They are
# consumed by ``report_generator.py`` (document preamble) only.

def latex_packages() -> List[Tuple[str, Optional[str]]]:
    """``(package, options)`` pairs required by the report, in load order.

    ``geometry``, ``fontenc``, ``inputenc``, ``lmodern``, ``textcomp`` and
    ``lastpage`` are added by PyLaTeX's ``Document`` itself (see
    ``document_arguments``).
    """
    return [
        ("graphicx", None),
        ("amsmath", None),
        ("amssymb", None),
        ("array", None),
        ("xcolor", "table"),          # loads colortbl for header fills
        ("longtable", None),
        ("multirow", None),
        ("hhline", None),
        ("float", None),
        ("caption", None),
        ("subcaption", None),
        ("fancyhdr", None),
        ("setspace", None),
        ("enumitem", None),
        ("titlesec", None),
        ("titletoc", None),
        ("etoolbox", None),
        ("hyperref", "hidelinks"),
    ]


def document_arguments() -> Dict[str, object]:
    """Keyword arguments for ``pylatex.Document`` derived from the styles."""
    return {
        "documentclass": PAGE.document_class,
        "document_options": PAGE.class_options(),
        "geometry_options": PAGE.geometry_options(),
        "fontenc": FONTS.font_encoding,
        "inputenc": FONTS.input_encoding,
        "lmodern": FONTS.use_latin_modern,
        "textcomp": True,
        "page_numbers": True,
        # Paragraph indentation is switched off in ``preamble_tex`` (\\parindent);
        # ``indent=False`` would make PyLaTeX load the ``parskip`` package, which
        # also changes list and heading spacing.
        "indent": True,
    }


def _color_definitions() -> str:
    return "\n".join(
        r"\definecolor{%s}{HTML}{%s}" % (name, value)
        for name, value in COLORS.as_dict().items()
    )


def _page_break_setup() -> str:
    """``\\rptneedspace{<length>}`` — the page-bottom threshold.

    Starts a new page when less than ``<length>`` of vertical space is left on
    the current one. Unlike ``\\needspace`` it leaves no negative penalty
    behind, so a long table that follows is still broken *between its rows*
    at the page bottom instead of being pushed to the next page as a whole.
    """
    return "\n".join([
        r"% --- page-bottom threshold ------------------------------------------",
        r"\makeatletter",
        r"\newcommand{\rptneedspace}[1]{\par\begingroup",
        r"  \dimen@\pagegoal \advance\dimen@-\pagetotal",
        r"  \ifdim\dimen@<\dimexpr#1\relax\ifdim\dimen@>\z@\vfil\break\fi\fi",
        r"  \endgroup}",
        r"\makeatother",
    ])


def _table_setup() -> str:
    t, s, f = TABLE, SPACING, FONTS
    return "\n".join([
        r"% --- tables ---------------------------------------------------------",
        r"\setlength{\tabcolsep}{%s}" % t.col_sep,
        r"\renewcommand{\arraystretch}{%s}" % t.row_stretch,
        r"\setlength{\extrarowheight}{%s}" % t.extra_row_height,
        r"\setlength{\arrayrulewidth}{%s}" % t.rule_width,
        r"\arrayrulecolor{%s}" % t.rule_color,
        r"\setlength{\LTpre}{%s}" % s.block_before,
        r"\setlength{\LTpost}{%s}" % s.block_after,
        r"\setlength{\LTleft}{0pt}",
        r"\setlength{\LTright}{0pt}",
        # (\\LTcapwidth is set per table by the table builder: the text width is
        #  not final in the preamble, geometry applies it at \\begin{document}.)
        # Width available for the cells of the table being built (set by the
        # table builder for every table from the number of columns).
        r"\newlength{\rptTableWidth}",
        # Column types: left / centre / right aligned paragraphs of given width.
        r"\newcolumntype{L}[1]{>{\raggedright\arraybackslash\hspace{0pt}}p{#1}}",
        r"\newcolumntype{C}[1]{>{\centering\arraybackslash\hspace{0pt}}p{#1}}",
        r"\newcolumntype{R}[1]{>{\raggedleft\arraybackslash\hspace{0pt}}p{#1}}",
        # Semantic cell macros.
        r"\newcommand{\rpthead}[1]{{%s #1}}" % f.table_header,
        r"\newcommand{\rptband}[1]{{%s #1}}" % f.table_band,
        r"\newcommand{\rptheadrule}{\noalign{\hrule height %s}}" % t.header_rule_width,
        r"\newcommand{\rptpass}{\textcolor{rptPass}{\textbf{%s}}}" % TEXT.status_pass,
        r"\newcommand{\rptfail}{\textcolor{rptFail}{\textbf{%s}}}" % TEXT.status_fail,
        r"\newcommand{\rptwarn}{\textcolor{rptWarn}{\textbf{%s}}}" % TEXT.status_warn,
        r"\newcommand{\rptover}[1]{\textcolor{rptFail}{\textbf{#1}}}",
        r"\newcommand{\rptcontinued}[1]{\multicolumn{#1}{r}{{%s\color{rptMuted} %s}}}"
        % (f.note, t.continued_footer_text),
        # Note below a table: typeset by the table builder as the last,
        # un-ruled row of the table (so it always stays with the table).
        r"\newcommand{\tablenote}[1]{\rule{0pt}{\dimexpr\ht\strutbox+%s\relax}"
        r"{%s\color{rptMuted} #1}}" % (s.note_gap, f.note),
        r"\newcommand{\rptnote}[1]{\par\noindent{%s\color{rptMuted} #1}\par}" % f.note,
        # Semantic text macros used by the chapters (no raw font / colour
        # commands in chapter files).
        r"\newcommand{\rptstrong}[1]{\textbf{#1}}",
        r"\newcommand{\rptcite}[1]{\textit{#1}}",
        r"\newcommand{\rptloginfo}[1]{\textcolor{rptInfo}{#1}}",
        r"\newcommand{\rptlogerror}[1]{\textcolor{rptFail}{#1}}",
        r"\newcommand{\rptlogok}[1]{\textcolor{osdagDark}{#1}}",
        r"\newcommand{\placeholder}[1]{\textcolor{rptPlaceholder}{\textit{\textless #1\textgreater}}}",
        # Page-bottom threshold: never start a table / figure in the last
        # few lines of a page (prevents orphaned captions and header rows).
        r"\BeforeBeginEnvironment{longtable}{\rptneedspace{%s}}" % s.table_min_start,
        r"\BeforeBeginEnvironment{figure}{\rptneedspace{%s}}" % s.figure_min_start,
    ])


def _caption_setup() -> str:
    f, s = FONTS, SPACING
    return "\n".join([
        r"% --- captions -------------------------------------------------------",
        r"\captionsetup{font={%s},labelfont={%s,color=osdagDark},textfont={%s},"
        r"labelsep=colon,justification=raggedright,singlelinecheck=false,"
        r"format=plain,skip=%s}" % (f.caption_size, f.caption_label, f.caption_text, s.caption_gap),
        r"\captionsetup[figure]{justification=centering,singlelinecheck=true}",
        r"\numberwithin{table}{chapter}",
        r"\numberwithin{figure}{chapter}",
        # Tables / figures of the un-numbered executive summary are labelled
        # "ES.1", "ES.2" ...; the chapters return to "<chapter>.<n>".
        r"\newcommand{\rptfrontnumbering}{%",
        r"  \renewcommand{\thetable}{%s.\arabic{table}}%%" % TEXT.front_number_prefix,
        r"  \renewcommand{\thefigure}{%s.\arabic{figure}}}" % TEXT.front_number_prefix,
        r"\newcommand{\rptmainnumbering}{%",
        r"  \renewcommand{\thetable}{\thechapter.\arabic{table}}%",
        r"  \renewcommand{\thefigure}{\thechapter.\arabic{figure}}}",
    ])


def _heading_setup() -> str:
    f, s = FONTS, SPACING
    return "\n".join([
        r"% --- headings -------------------------------------------------------",
        r"\titleformat{\chapter}[block]{\normalfont%s\color{rptText}}{\thechapter}{0.7em}{}"
        r"[\vspace{3pt}{\color{osdagGreen}\titlerule[1.2pt]}]" % f.chapter,
        r"\titlespacing*{\chapter}{0pt}{%s}{%s}" % (s.chapter_before, s.chapter_after),
        r"\titleformat{\section}{\normalfont%s\color{osdagDark}}{\thesection}{0.7em}{}" % f.section,
        r"\titlespacing*{\section}{0pt}{%s}{%s}" % (s.section_before, s.section_after),
        r"\titleformat{\subsection}{\normalfont%s\color{rptText}}{\thesubsection}{0.7em}{}" % f.subsection,
        r"\titlespacing*{\subsection}{0pt}{%s}{%s}" % (s.subsection_before, s.subsection_after),
        # Page-bottom thresholds of the headings (no heading is left alone
        # at the foot of a page).
        r"\pretocmd{\section}{\rptneedspace{%s}}{}{}" % s.heading_min_start,
        r"\pretocmd{\subsection}{\rptneedspace{%s}}{}{}" % s.subheading_min_start,
        # Section whose first content is a figure.
        r"\newcommand{\rptfiguresection}[1]{\rptneedspace{%s}\section{#1}}" % s.figure_heading_min_start,
        r"\setcounter{secnumdepth}{2}",
        r"\setcounter{tocdepth}{2}",
        # Un-numbered heading used by the executive summary (same look as a
        # chapter title, listed in the table of contents).
        r"\newcommand{\rptfrontchapter}[1]{\clearpage\phantomsection"
        r"\addcontentsline{toc}{chapter}{#1}"
        r"{\noindent%s\color{rptText} #1\par}\vspace{3pt}"
        r"{\color{osdagGreen}\hrule height 1.2pt}\vspace{%s}}" % (f.chapter, s.chapter_after),
        r"\newcommand{\rptfrontsection}[1]{\rptneedspace{%s}\vspace{%s}\phantomsection"
        r"\addcontentsline{toc}{section}{#1}"
        r"{\noindent%s\color{osdagDark} #1\par}\nopagebreak\vspace{%s}}"
        % (s.heading_min_start, s.section_before, f.section, s.section_after),
        r"\newcommand{\rptsubheading}[1]{\rptneedspace{%s}\vspace{%s}"
        r"{\noindent%s\color{rptText} #1\par}\nopagebreak\vspace{%s}}"
        % (s.subheading_min_start, s.subsection_before, f.subsection, s.subsection_after),
    ])


def _toc_setup() -> str:
    return "\n".join([
        r"% --- table of contents ---------------------------------------------",
        r"\titlecontents{chapter}[1.8em]{\normalfont\sffamily\bfseries\vspace{5pt}}"
        r"{\contentslabel{1.8em}}{\hspace*{-1.8em}}{\hfill\contentspage}",
        r"\titlecontents{section}[4.2em]{\normalfont\vspace{1pt}}"
        r"{\contentslabel{2.4em}}{\hspace*{-2.4em}}"
        r"{\titlerule*[0.6pc]{.}\contentspage}",
        r"\titlecontents{subsection}[7.4em]{\normalfont\small}"
        r"{\contentslabel{3.2em}}{\hspace*{-3.2em}}"
        r"{\titlerule*[0.6pc]{.}\contentspage}",
        r"\renewcommand{\contentsname}{%s}" % TEXT.toc_title,
    ])


def _list_setup() -> str:
    s = SPACING
    return "\n".join([
        r"% --- lists ----------------------------------------------------------",
        r"\setlist{itemsep=%s,topsep=%s,parsep=0pt,leftmargin=1.6em}" % (s.list_item_sep, s.list_top_sep),
    ])


def _software_default_marker() -> str:
    """``\\sdstar`` — asterisk marking a software-default value.

    Every use writes its page number to the ``.aux`` file at shipout time, so
    on the next LaTeX pass the footer knows *exactly* which pages carry a
    marked value (also inside multi-page tables) and prints the explanatory
    note only there.
    """
    return "\n".join([
        r"% --- software-default marker ----------------------------------------",
        r"\makeatletter",
        r"\newcommand{\rptSDpage}[1]{\global\@namedef{rptSD@#1}{1}}",
        r"\newcommand{\sdstar}{\textsuperscript{*}"
        r"\protected@write\@auxout{}{\string\rptSDpage{\arabic{page}}}}",
        r"\newcommand{\rptIfSDpage}[1]{\@ifundefined{rptSD@\arabic{page}}{}{#1}}",
        r"\makeatother",
    ])


def _header_footer_setup(header_left: str, header_right: str) -> str:
    h, f = HEADER_FOOTER, FONTS
    foot_rule = "\n".join([
        r"\renewcommand{\footrule}{%",
        r"  \rptIfSDpage{\hbox to\headwidth{{%s\color{rptMuted} %s}\hfil}\vskip %s}%%"
        % (f.note, h.default_note, h.note_gap),
        r"  {\color{%s}\hrule width\headwidth height %s}\vskip %s}"
        % (h.rule_color, h.rule_width, h.rule_gap),
    ])
    head_rule = (
        r"\renewcommand{\headrule}{\vskip %s{\color{%s}\hrule width\headwidth height %s}}"
        % (h.head_rule_gap, h.rule_color, h.rule_width)
    )
    foot_fields = "\n".join([
        r"  \fancyfoot[L]{%s %s}" % (f.running_head, h.footer_left),
        r"  \fancyfoot[R]{%s %s}" % (f.running_head, h.footer_right),
    ])
    head_fields = "\n".join([
        r"  \fancyhead[L]{%s %s}" % (f.running_head, header_left),
        r"  \fancyhead[R]{%s %s}" % (f.running_head, header_right),
    ])

    def _page_style(name: str, with_head: bool) -> str:
        body = [r"\fancypagestyle{%s}{" % name, r"  \fancyhf{}"]
        if with_head:
            body += [head_fields, "  " + head_rule]
        else:
            body += [r"  \renewcommand{\headrule}{}"]
        body += [foot_fields, "  " + foot_rule.replace("\n", "\n  "), "}"]
        return "\n".join(body)

    return "\n".join([
        r"% --- running header / footer ----------------------------------------",
        _page_style("main", with_head=True),
        _page_style("plain", with_head=True),      # chapter opening pages
        _page_style("firstpage", with_head=False),  # title page
        r"\pagestyle{main}",
    ])


def header_fields(project_name: str, job_number: str,
                  report_date: str, report_version: str) -> Tuple[str, str]:
    """Left / right running-header texts (arguments must be LaTeX-escaped)."""
    sep = HEADER_FOOTER.separator
    left = sep.join(p for p in (project_name, job_number) if p)
    right = sep.join(p for p in (report_date, report_version) if p)
    return left, right


def preamble_tex(header_left: str = "", header_right: str = "",
                 pdf_title: str = "", pdf_author: str = "") -> str:
    """Complete style preamble (everything after the ``\\usepackage`` lines)."""
    return "\n\n".join([
        r"% ====================================================================" "\n"
        r"% Generated from osdagbridge/core/reports/styles.py -- do not edit here" "\n"
        r"% ====================================================================",
        _color_definitions(),
        r"\color{rptText}" "\n"
        r"\setstretch{%s}" "\n"
        r"\setlength{\parskip}{%s}" "\n"
        r"\setlength{\parindent}{0pt}" "\n"
        r"\raggedbottom" % (PAGE.line_stretch, PAGE.paragraph_skip),
        _page_break_setup(),
        _table_setup(),
        _caption_setup(),
        _heading_setup(),
        _toc_setup(),
        _list_setup(),
        _software_default_marker(),
        _header_footer_setup(header_left, header_right),
        r"\hypersetup{pdftitle={%s},pdfauthor={%s},pdfsubject={%s},pdfcreator={%s}}"
        % (pdf_title, pdf_author, TEXT.pdf_subject, TEXT.product),
    ])


# ---------------------------------------------------------------------------
# Small semantic helpers used by the chapter generators
# ---------------------------------------------------------------------------

def status_tex(status: object) -> str:
    """Colour-coded status cell for ``PASS`` / ``FAIL`` / ``WARN`` strings.

    Anything else (``N/A``, ``---``, empty) is returned unchanged; an empty
    value becomes the table's empty-cell marker.
    """
    if status is None:
        return TABLE.empty_cell
    text = str(status).strip()
    if not text:
        return TABLE.empty_cell
    upper = text.upper()
    if "FAIL" in upper:
        return r"\rptfail{}"
    if "WARN" in upper:
        return r"\rptwarn{}"
    if "PASS" in upper or upper == "OK":
        return r"\rptpass{}"
    return text


def pass_fail(ok: Optional[bool]) -> str:
    """``True`` → PASS, ``False`` → FAIL, ``None`` → empty-cell marker."""
    if ok is None:
        return TABLE.empty_cell
    return r"\rptpass{}" if ok else r"\rptfail{}"


def ratio_tex(value: object, nd: int = 2, limit: float = 1.0) -> str:
    """Utilization ratio; values above ``limit`` are highlighted."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return TABLE.empty_cell
    text = f"{f:.{nd}f}"
    return (r"\rptover{" + text + "}") if f > limit else text


def vgap(size: Optional[str] = None) -> str:
    """Vertical gap between two blocks (defaults to the standard block gap)."""
    return r"\vspace{%s}" % (size or SPACING.block_before)
