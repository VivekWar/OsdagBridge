# =============================================================================
# OsdagBridge — Report Generator (orchestration)
#
# Builds the design report as a PyLaTeX ``Document`` and compiles it to PDF:
#   • title page, table of contents, executive summary
#   • Chapter 1  Project Information
#   • Chapter 2  Input Parameters
#   • Chapter 3  Loads & Load Combinations
#   • Chapter 4  Analysis Results
#   • Chapter 5  Design Checks (incl. utilization-ratio charts, Section 5.5)
#   • Chapter 6  Drawings & Visualizations
#   • Chapter 7  Material Take-off & Quantity Summary (incl. quantity charts)
#   • Chapter 8  Design Log
#   • References
#
# Module map of this package
#   styles.py          single source of truth for ALL formatting
#   tables.py          table builder (PyLaTeX LongTable, repeated headers)
#   figures.py         figure builder (PyLaTeX Figure)
#   charts.py          matplotlib bar charts (UR and material quantities)
#   live_loads.py      live-load data for Chapter 3
#   design_summary.py  governing design checks for Section 5.5 / exec. summary
#   data_bridge.py     read-only access to the stored design results
#   chap1.py … chap9.py, executive_summary.py   content of each chapter
# =============================================================================

# =============================================================================
# GAPS REPORT — keys used in templates with no canonical KEY_ in common.py
# =============================================================================
# GAP | Template location         | Literal key used             | Notes
# ─────────────────────────────────────────────────────────────────────────────
# 1   | Table 2.1                 | 'latitude'                   | injected from weather_data; no KEY_ yet
# 2   | Table 2.1                 | 'longitude'                  | injected from weather_data; no KEY_ yet
# 3   | Table 2.4 / Exec Summary  | 'num_lanes'                  | design lane count; NOT the UI counter
#     |                           |                              | KEY_WC_LD_LANE_TABLE_COUNT; stays GAP
# 4   | Exec Summary (Proj Ovw)   | 'overall_design_status'      | output_dict value; no KEY_ needed
# 5   | Exec Summary (Proj Ovw)   | 'governing_check'            | output_dict value; no KEY_ needed
# 6   | Exec Summary (Proj Ovw)   | 'overall_utilization_ratio'  | output_dict value; no KEY_ needed
# 7   | Exec Summary (Table 1)    | 'section_designation'        | output_dict value; no KEY_ needed
# 8   | Table 2.7 / 2.8           | ''              | no. of bracing panels; no KEY_ yet
# 9   | Table 2.8                 | ''              | ED spacing; no KEY_ yet
# 10  | Table 4.1, 4.2            | ''             | Load Cases (DL only, Seismic (EL)); ADD_BACKEND_KEY
# 11  | Table 4.1, 5.22           | ''             | Load Combinations (LC-ULS-1, LC-SLS-1); ADD_BACKEND_KEY
# 12  | Table 5.12                | ''                | tau_fn (67 MPa); PLACEHOLDER
# 13  | Table 5.20b, 5.22         | ''                 | Slenderness limits (250, 400); PLACEHOLDER
# 14  | Table 3.4, 3.5, 3.6       | 'wind_speed', 'seismic_zone' | Weather inputs; no KEY_ yet
# 15  | Table 4.1 - 4.3           | ''             | Analysis solver demands (Max BM, SF, Defl)
# 16  | Table 5.7 - 5.9           | 'stiffener_by_member'        | Stiffener capacities; no KEY_ yet
# 17  | Table 5.14 - 5.17         | ''             | Deck slab / shear connector forces
# 18  | Table 5.20 - 5.21         | ''             | Cross-bracing / Diaphragm forces
# 19  | Table 7.1                 | 'steel_girders_mt' (etc)     | All BOM quantities; no KEY_ yet
# 20  | Chapter 8                 | ''             | Standards & References; no structural KEY_
# =============================================================================

# =============================================================================
# #  | KEY_ constant used                        | Template   | Backend action needed
# ─────────────────────────────────────────────────────────────────────────────
# (All missing data cases for Chapters 1-9 resolved or moved to GAPS)
# =============================================================================

#==============================================================================
#   FLOW OF REPORT GENERATION
# ─────────────────────────────────────────────────────────────────────────────
# USER CLICKS "Generate Report" button
#        │
#        ▼
#[output_dock.py] OutputDock._on_report_clicked()
#        │  traverses UI tree to locate `cad_generator` widget
#        └──► [template_page.py] CustomWindow.open_report_dialog(cad_generator)
#                    │
#                    ├── ReportOptionsDialog(parent=self).exec()
#                    │         [report_options.py — user fills form]
#                    │         └── returns request (ReportRequest dataclass)
#                    │
#                    ├── Spawns background thread: _ReportWorker(backend, request, cad_generator)
#                    │
#                    └──► [template_page.py] _ReportWorker.run()
#                                │
#                                └──► [plategirderbridge.py] PlateGirderBridge.generate_design_report(request, cad_generator)
#                                            │
#                                            ├── self.input_dict.copy() → report_inputs
#                                            ├── dict(self.output_dict) → output_dict
#                                            │
#                                            ├──► [report_generator.py] build_report_payload(request, report_inputs, output_dict)
#                                            │           └── returns ReportPayload dataclass
#                                            │
#                                            ├── self._export_cad_figures(cad_generator)
#                                            │    └── exports 4 headless views to ResourceFiles/Images
#                                            │    └── wires paths onto payload.figures (girder_3d, etc.)
#                                            │
#                                            ├── self.build_figure_grillage() → grillage_fig (matplotlib)
#                                            ├── self.figure_to_bytes(grillage_fig) → grillage_bytes
#                                            ├──► [report_generator.py] export_grillage_figure(grillage_bytes, output_dir, file_stem)
#                                            │           └── writes grillage.png → payload.figures.grillage = path
#                                            │
#                                            └──► [report_generator.py] generate_report(payload, request)
#                                                        │
#                                                        ├── OsdagLatexEnv() → discovers pdflatex binary
#                                                        ├── Creates output_dir/assets/
#                                                        ├── Copies logos & payload figures → assets/
#                                                        ├── Calls 10 chapter functions → full_tex string
#                                                        ├── Writes full_tex to tempdir/stem.tex
#                                                        ├── subprocess.run(pdflatex) × 2 passes
#                                                        ├── shutil.copy2(tmp_pdf → output_dir/stem.pdf)
#                                                        └── returns ReportResult(pdf_path, tex_path)
#                                                                  │
#                                                                  ▼
#                                                      [template_page.py] _on_report_finished()
#                                                          if dialog.is_preview → os.startfile(pdf_path)
#                                                          else → CustomMessageBox("Report Saved")
#==============================================================================

import os, shutil, logging, datetime, tempfile, subprocess
from dataclasses import dataclass, field
from typing import Optional, List

from pylatex import Document, Package
from pylatex.utils import NoEscape

from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE
)

from . import figures as F
from . import styles as S
from . import tables as T
from .data_bridge import ReportDataBridge
from .report_utils import _tex
from .executive_summary import executive_summary
from .chap1 import ch1_project_info
from .chap2 import ch2_input_parameters
from .chap3 import ch3_loads
from .chap4 import ch4_analysis
from .chap5 import ch5_design_checks
from .chap6 import ch6_drawings
from .chap7 import ch7_quantities
from .chap8 import ch8_design_log
from .chap9 import references

logger = logging.getLogger(__name__)

# Number of pdflatex passes: table of contents, "Page x of y", longtable
# column widths and the software-default footer marker all need the .aux file
# of the previous pass.
LATEX_PASSES = 3

# Sub-directories of the temporary build directory (paths in the document are
# relative to the build directory, so no absolute path ever reaches LaTeX).
IMAGE_DIR = "images"        # captured CAD / analysis figures and generated charts
ASSET_DIR = "assets"        # title-page logos


# =============================================================================
# Document assembly (PyLaTeX)
# =============================================================================
# All formatting comes from styles.py: the Document arguments (class, paper,
# margins, fonts), the package list and the style preamble are emitted there.

def new_document(metadata) -> Document:
    """Empty report document with the complete style preamble."""
    doc = Document(**S.document_arguments())
    for name, options in S.latex_packages():
        doc.packages.append(Package(name, options=options))

    header_left, header_right = S.header_fields(
        _tex(metadata.project_name), _tex(metadata.job_number),
        _tex(metadata.report_date), _tex(metadata.subtitle or 'Rev 0'))
    doc.preamble.append(NoEscape(S.preamble_tex(
        header_left, header_right,
        pdf_title=_tex(metadata.project_name) + " --- " + S.TEXT.report_kind,
        pdf_author=_tex(metadata.designer))))
    return doc


def title_page(m, osdag_logo, org_logo):
    """Title page: logos, product title and the project information block."""
    fig, sp, fonts, text = S.FIGURE, S.SPACING, S.FONTS, S.TEXT
    if osdag_logo:
        lhs = r"\includegraphics[width=\linewidth,keepaspectratio]{\detokenize{%s}}" % osdag_logo
    else:
        lhs = r"\placeholder{Osdag logo}"
    if org_logo:
        rhs = (r"\includegraphics[width=\linewidth,height=%s,keepaspectratio]{\detokenize{%s}}"
               % (fig.logo_right_height, org_logo))
    else:
        rhs = ""

    info = T.plain_block("title_block", [
        ("Project Name", _tex(m.project_name)),
        ("Project Location", _tex(m.project_location)),
        ("Author / Designer", _tex(m.designer)),
        ("Reviewer", _tex(m.reviewer)),
        ("Organization", _tex(m.company)),
        ("Client Name and Organization", _tex(m.client)),
        ("Job Number", _tex(m.job_number)),
        ("Date", _tex(m.report_date)),
        ("Report Version", _tex(m.subtitle) if m.subtitle else ''),
    ])
    return "\n".join([
        r"\begin{titlepage}",
        r"\thispagestyle{firstpage}",
        r"\centering",
        r"\vspace*{%s}" % sp.title_top,
        r"\noindent\begin{minipage}[c]{%.2f\textwidth}\raggedright" % fig.logo_left_width,
        lhs,
        r"\end{minipage}\hfill",
        r"\begin{minipage}[c]{%.2f\textwidth}\raggedleft" % fig.logo_right_width,
        rhs,
        r"\end{minipage}\par",
        r"\vspace{%s}" % sp.title_logo_gap,
        r"{%s\color{rptText} %s\par}" % (fonts.title_main, text.product),
        r"\vspace{4mm}",
        r"{%s\color{rptMuted} %s\par}" % (fonts.title_sub, text.tagline),
        r"\vspace{6mm}",
        r"{\color{osdagGreen}\rule{0.35\textwidth}{1.2pt}\par}",
        r"\vspace{6mm}",
        r"{%s\color{osdagDark} %s\par}" % (fonts.title_kind, text.report_kind),
        r"\vspace{%s}" % sp.title_block_gap,
        r"{%s" % fonts.table_body,
        info + r"}",
        r"\end{titlepage}",
        # The title page is page 1: keep "Page x of y" continuous with the PDF.
        r"\setcounter{page}{2}",
    ]) + "\n"


def toc_section():
    """Table of contents (its look is defined in styles.py)."""
    return "\n".join([
        r"\clearpage",
        r"\tableofcontents",
        r"\clearpage",
    ]) + "\n"


def build_document(payload, fig_paths, osdag_logo, org_logo, asset_dir) -> Document:
    """Assemble the complete report.

    ``fig_paths`` maps a figure name to its image path relative to the build
    directory; ``asset_dir`` is the directory the generated charts are written
    to (inside the build directory).
    """
    doc = new_document(payload.metadata)
    add = lambda tex: doc.append(NoEscape(tex))

    add(title_page(payload.metadata, osdag_logo, org_logo))
    if payload.options.include_toc:
        add(toc_section())

    # Chapter inclusion is driven by the canonical section keys selected in
    # the report-options dialog. The first three parts are locked in the UI,
    # so they are always present.
    secs = payload.options.sections
    bridge = ReportDataBridge(payload.output_dict, payload.inputs, payload)
    span_m = float(payload.inputs.get(KEY_SPAN, 0) or 0)

    add(executive_summary(payload.inputs, payload.output_dict, fig_paths))
    add(ch1_project_info(payload.metadata))
    add(ch2_input_parameters(payload.metadata, payload.inputs, payload.output_dict))
    if 'loads' in secs:
        add(ch3_loads(payload.inputs))
    if 'analysis' in secs:
        add(ch4_analysis(payload.analysis_summary, fig_paths, bridge, span_m))
    if 'design_checks' in secs:
        add(ch5_design_checks(payload.design_checks, bridge, asset_dir))
    if 'drawings' in secs and payload.options.include_figures:
        add(ch6_drawings(fig_paths))
    add(ch7_quantities(payload.inputs, asset_dir))
    add(ch8_design_log(payload.log_entries, payload.inputs))
    add(references())
    return doc


# ---------------------------------------------------------------------------
# Public data-classes 
# ---------------------------------------------------------------------------

@dataclass
class ReportMetadata:
    project_name: str
    project_location: str
    designer: str
    client: str
    company: str
    group_name: str = ''
    subtitle: str = ''
    job_number: str = ''
    additional_comments: str = ''
    logo_path: Optional[str] = None
    report_date: str = ''
    reviewer: str = ''

@dataclass
class ReportOptions:
    sections: List[str]
    include_figures: bool
    include_toc: bool
    include_pdf: bool

@dataclass
class ReportRequest:
    metadata: ReportMetadata
    options: ReportOptions
    output_dir: str
    file_stem: str

@dataclass
class ReportFigures:
    plan:            Optional[str] = None
    cross_section:   Optional[str] = None
    final_geometry:  Optional[str] = None
    longitudinal_elevation: Optional[str] = None
    girder_3d:       Optional[str] = None
    girder_front:    Optional[str] = None
    girder_top:      Optional[str] = None
    girder_end:      Optional[str] = None
    bm_envelope:     Optional[str] = None
    sf_envelope:     Optional[str] = None
    defl_ll:         Optional[str] = None
    shear_connector: Optional[str] = None
    cross_bracing:   Optional[str] = None

@dataclass
class ReportPayload:
    metadata:         ReportMetadata
    options:          ReportOptions
    inputs:           dict
    analysis_summary: dict
    design_checks:    list
    figures:          ReportFigures
    log_entries:      List[str] = field(default_factory=list)
    output_dict:      dict = field(default_factory=dict)
    figure_data:      dict = field(default_factory=dict)  # {attr: bytes} — cleared after writing to tmpdir


@dataclass
class ReportResult:
    pdf_path: Optional[str]
    tex_path: Optional[str]


def _format_project_location(pl_data):
    if not pl_data:
        return ''
    if isinstance(pl_data, str):
        try:
            import ast
            pl_dict = ast.literal_eval(pl_data)
        except Exception:
            return pl_data
    elif isinstance(pl_data, dict):
        pl_dict = pl_data
    else:
        return str(pl_data)
    
    method = pl_dict.get('method')
    data = pl_dict.get('data', {})
    
    if method == 'location_name':
        dist = data.get('district', '')
        state = data.get('state', '')
        if dist and state:
            return f"{dist}, {state}"
        return dist or state or r''
    elif method == 'map':
        lat = data.get('latitude', '')
        lon = data.get('longitude', '')
        if lat and lon:
            try:
                from osdagbridge.core.bridge_types.plate_girder.ui_fields_project_location import DB_PATH
                from osdagbridge.core.data.project_location.database import Database
                db = Database(DB_PATH)
                db.connect()
                nearest = db.get_nearest_station_temperature(float(lat), float(lon))
                db.close()
                if nearest:
                    return f"{nearest['station']}, {nearest['state']}"
            except Exception as e:
                logger.warning(f"Reverse geocode error: {e}")
            return f"Lat: {lat}°, Lon: {lon}°"
        return 'Map Location'
    elif method == 'custom_data':
        return 'Custom Location Data'
    
    return str(pl_data)

# ---------------------------------------------------------------------------
# Public builder helper (unchanged signature)
# ---------------------------------------------------------------------------

def build_report_payload(request, input_dict, output_dict):
    try:
        rd  = request.metadata.report_date or datetime.date.today().isoformat()
        lp  = request.metadata.logo_path
        raw_pl = request.metadata.project_location or input_dict.get('project.location') or ''
        pl = _format_project_location(raw_pl)

        md = ReportMetadata(
            project_name  = request.metadata.project_name,
            project_location = pl,
            designer      = request.metadata.designer,
            client        = request.metadata.client,
            company       = request.metadata.company,
            group_name    = request.metadata.group_name,
            subtitle      = request.metadata.subtitle,
            job_number    = request.metadata.job_number,
            additional_comments = request.metadata.additional_comments,
            logo_path     = lp,
            report_date   = rd,
            reviewer      = getattr(request.metadata, 'reviewer', ''))

        # Inject detailed project location and weather data into input_dict dict
        try:
            import ast
            if isinstance(raw_pl, str) and '{' in raw_pl:
                pl_dict = ast.literal_eval(raw_pl)
            elif isinstance(raw_pl, dict):
                pl_dict = raw_pl
            else:
                pl_dict = {}
                
            if pl_dict and isinstance(pl_dict, dict):
                data = pl_dict.get('data', {})
                weather = pl_dict.get('weather_data', {})
                
                # We prioritize manual inputs if they exist, else we use the DB/map coordinates
                lat_val = data.get('latitude') or weather.get('latitude')
                lon_val = data.get('longitude') or weather.get('longitude')
                
                if 'latitude' not in input_dict and lat_val:
                    input_dict['latitude'] = lat_val
                if 'longitude' not in input_dict and lon_val:
                    input_dict['longitude'] = lon_val
                    
                if 'seismic_zone' not in input_dict and weather.get('zone'):
                    input_dict['seismic_zone'] = weather.get('zone')
                if 'wind_speed' not in input_dict and weather.get('wind_speed'):
                    input_dict['wind_speed'] = weather.get('wind_speed')
                if 'shade_temp_max' not in input_dict and weather.get('max_temp'):
                    input_dict['shade_temp_max'] = weather.get('max_temp')
                if 'shade_temp_min' not in input_dict and weather.get('min_temp'):
                    input_dict['shade_temp_min'] = weather.get('min_temp')
        except Exception as e:
            logger.warning(f"Failed to parse project location data: {e}")

        # ── Table 3.6 rows 3 & 4: effective bridge temp range and rise/fall ────
        # The computed keys live in output_dict (which is a snapshot of input_dict
        # at design time). Merge them into input_dict if not already present.
        for _tkey in (KEY_TL_BRIDGE_TEMP_MIN, KEY_TL_BRIDGE_TEMP_MAX,
                      KEY_TL_TEMP_RISE, KEY_TL_TEMP_FALL):
            if not input_dict.get(_tkey) and output_dict.get(_tkey):
                input_dict[_tkey] = output_dict[_tkey]

        # If still missing, compute from whatever temperature inputs are available.
        if not input_dict.get(KEY_TL_BRIDGE_TEMP_MIN):
            try:
                max_str = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
                min_str = input_dict.get(KEY_TL_LOWEST_MIN_TEMP)  or input_dict.get('shade_temp_min')
                if max_str and min_str:
                    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
                    res   = IRC6_2017.cl_215_2_effective_bridge_temperature(
                                float(max_str), float(min_str), 'metallic', False)
                    t_min = res.get('T_min', 0)
                    t_max = res.get('T_max', 0)
                    mean  = (t_max + t_min) / 2.0
                    input_dict[KEY_TL_BRIDGE_TEMP_MIN] = f"{t_min:.2f}"
                    input_dict[KEY_TL_BRIDGE_TEMP_MAX] = f"{t_max:.2f}"
                    input_dict[KEY_TL_TEMP_RISE]       = f"{t_max - mean:.2f}"
                    input_dict[KEY_TL_TEMP_FALL]       = f"{mean - t_min:.2f}"
            except Exception as _te:
                logger.warning(f"Could not compute temperature values for report: {_te}")

        asum = {}
        if output_dict:
            asum = output_dict.get('analysis_summary', {})
   

        # 4) Grab Design Checks and Log
        dc = []
        le = []
        if output_dict:
            if 'design_checks' in output_dict:
                dc = output_dict['design_checks']
            if 'design_log' in output_dict:
                le = output_dict['design_log']

        # Design Log chapter content: the green (success) stage-completion lines
        # captured by the singleton logger during the most recent run.
        if not le:
            try:
                from osdagbridge.core.utils.logger import bridge_logger
                le = bridge_logger.get_success_log()
            except Exception as _le:
                logger.warning("Could not read design log from logger: %s", _le)

        return ReportPayload(metadata=md, options=request.options, inputs=input_dict,
                             analysis_summary=asum, design_checks=dc,
                             figures=ReportFigures(), log_entries=le,
                             output_dict=output_dict or {})

    except Exception as exc:
        logger.warning("build_report_payload error: %s", exc)
        return ReportPayload(
            metadata=request.metadata, options=request.options,
            inputs={}, analysis_summary={}, design_checks=[],
            figures=ReportFigures(), log_entries=[],
            output_dict={})


# ---------------------------------------------------------------------------



from osdagbridge.core.boq.boq_generator import calculate_material_quantities

# ===========================================================================
# Public entry point
# ===========================================================================

_FIGURE_MAP = [
    ('plan',                  'plan.png'),
    ('cross_section',         'cross_section.png'),
    ('final_geometry',        'final_geometry.png'),
    ('longitudinal_elevation','longitudinal_elevation.png'),
    ('girder_3d',             'girder_3d.png'),
    ('girder_top',            'girder_top.png'),
    ('section_preview',       'section_preview.png'),
    ('stiffener_preview',     'stiffener_preview.png'),
    ('cb_diagram',            'cb_diagram.png'),
    ('cb_bracing',            'cb_bracing.png'),
    ('cb_top_chord',          'cb_top_chord.png'),
    ('cb_bottom_chord',       'cb_bottom_chord.png'),
    ('ed_diagram',            'ed_diagram.png'),
    ('ed_bracing',            'ed_bracing.png'),
    ('ed_top_chord',          'ed_top_chord.png'),
    ('ed_bottom_chord',       'ed_bottom_chord.png'),
    ('bm_envelope',           'bm_envelope.png'),
    ('sf_envelope',           'sf_envelope.png'),
    ('defl_ll',               'defl_ll.png'),
]

def generate_report(payload, request):
    # type: (ReportPayload, ReportRequest) -> ReportResult
    """Compile the full OsdagBridge Design Report to PDF (+ .tex source)."""
    tex_path = None
    try:
        # Use OsdagLatexEnv to discover the bundled pdflatex path
        compiler = 'pdflatex'
        try:
            import importlib
            module = importlib.import_module('osdag_latex_env.__main__')
            latex_env = getattr(module, 'OsdagLatexEnv')()
            if latex_env.pdflatex:
                compiler = str(latex_env.pdflatex)
                # Ensure the bin directory is in PATH so subprocess can find DLLs if needed
                if latex_env.bin_dir:
                    os.environ['PATH'] = str(latex_env.bin_dir) + os.pathsep + os.environ.get('PATH', '')
        except Exception as e:
            logger.info("osdag_latex_env not found or failed to load. (%s)", e)
            
        logger.info("Compiler: %s", compiler)

        os.makedirs(request.output_dir, exist_ok=True)

        # fig_paths is built inside TemporaryDirectory (see below) after bytes are written

        pdf_path = os.path.join(request.output_dir, request.file_stem + '.pdf')
        tex_path = os.path.join(request.output_dir, request.file_stem + '.tex')

        # Write to temp dir first, compile there, then copy back
        with tempfile.TemporaryDirectory() as tmp_dir:

            # ── Write figure bytes into tmp_dir/images/ then free RAM immediately ──
            # LaTeX sees the images through paths relative to the build
            # directory ("images/<name>.png"), never through absolute paths.
            tmp_images = os.path.join(tmp_dir, IMAGE_DIR)
            os.makedirs(tmp_images, exist_ok=True)
            fig_paths = {}
            for attr, img_bytes in list(payload.figure_data.items()):
                if img_bytes:
                    p = os.path.join(tmp_images, attr + '.png')
                    with open(p, 'wb') as fh:
                        fh.write(img_bytes)
                    fig_paths[attr] = F.latex_path(p, tmp_dir)
            payload.figure_data.clear()  # bytes no longer needed — free RAM now

            # ── Write title-page logos into tmp_dir/assets (auto-deleted) ──
            # Nothing is left next to the PDF. Latex paths are relative to tmp_dir.
            tmp_assets = os.path.join(tmp_dir, ASSET_DIR)
            os.makedirs(tmp_assets, exist_ok=True)

            osdag_logo_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'ResourceFiles', 'vectors', 'Osdag Logo.png')
            iit_logo_src   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'IIT Bombay Logo.png')

            osdag_logo_latex = None
            if os.path.exists(osdag_logo_src):
                shutil.copy2(osdag_logo_src, os.path.join(tmp_assets, 'osdag_logo.png'))
                osdag_logo_latex = ASSET_DIR + '/osdag_logo.png'

            org_logo_latex = None
            org_logo_src = payload.metadata.logo_path if (payload.metadata.logo_path and os.path.exists(payload.metadata.logo_path)) else (iit_logo_src if os.path.exists(iit_logo_src) else None)
            if org_logo_src:
                shutil.copy2(org_logo_src, os.path.join(tmp_assets, 'org_logo.png'))
                org_logo_latex = ASSET_DIR + '/org_logo.png'

            # Compute and inject quantities for Chapter 7
            quantities = calculate_material_quantities(payload.inputs, payload.output_dict)
            payload.inputs.update(quantities)

            # ── Assemble the PyLaTeX document ──
            # The bar charts (Section 5.5 and Chapter 7) are generated while
            # the chapters are built and saved into tmp_dir/images as well.
            doc = build_document(payload, fig_paths, osdag_logo_latex, org_logo_latex, tmp_images)
            full_tex = doc.dumps()

            tmp_tex = os.path.join(tmp_dir, request.file_stem + '.tex')
            tmp_pdf = os.path.join(tmp_dir, request.file_stem + '.pdf')

            with open(tmp_tex, 'w', encoding='utf-8') as f:
                f.write(full_tex)

            # Several passes: TOC, page references, longtable widths, footer marker
            for _ in range(LATEX_PASSES):
                try:
                    kwargs = {
                        'cwd': tmp_dir,
                        'stdout': subprocess.PIPE,
                        'stderr': subprocess.PIPE,
                        'check': False,
                        'env': os.environ.copy()
                    }
                    if os.name == 'nt':
                        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

                    res = subprocess.run(
                        [compiler, '-interaction=nonstopmode', request.file_stem + '.tex'],
                        **kwargs
                    )
                except Exception as exc:
                    logger.warning(f"pdflatex run failed: {exc}")

            # Keep the LaTeX log next to the .tex source when requested (debugging).
            tmp_log = os.path.join(tmp_dir, request.file_stem + '.log')
            if os.environ.get('OSDAGBRIDGE_REPORT_KEEP_LOG') and os.path.exists(tmp_log):
                shutil.copy2(tmp_log, os.path.join(request.output_dir, request.file_stem + '.log'))

            if os.path.exists(tmp_tex):
                shutil.copy2(tmp_tex, tex_path)
            if os.path.exists(tmp_pdf):
                shutil.copy2(tmp_pdf, pdf_path)

        if os.path.exists(pdf_path):
            logger.info("Report generated: %s", pdf_path)
            return ReportResult(pdf_path=pdf_path, tex_path=tex_path)

        logger.error("pdflatex ran but no PDF was produced.")
        if 'res' in locals():
            logger.error("pdflatex STDOUT:\n%s", res.stdout.decode('utf-8', 'ignore'))
            logger.error("pdflatex STDERR:\n%s", res.stderr.decode('utf-8', 'ignore'))
        return ReportResult(pdf_path=None, tex_path=tex_path)

    except Exception as exc:
        logger.error("generate_report failed: %s", exc, exc_info=True)
        if tex_path and os.path.exists(tex_path):
            return ReportResult(pdf_path=None, tex_path=tex_path)
        return ReportResult(pdf_path=None, tex_path=None)
