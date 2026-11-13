# Report generator refactoring — deliverables

Screening task *"OsdagBridge LaTeX Report Generator Refactoring & Enhancements"*.

| File | Content |
|------|---------|
| `Report_Before.pdf` | Design report generated with upstream `dev` (commit `d74f56d`) |
| `Report_After.pdf` | The same design, generated with the refactored report generator |
| `Technical_Changes.pdf` | Technical Changes Document: key code / LaTeX changes, files altered, structure of the style module, rationale (source: `Technical_Changes.tex`) |
| `img/` | Before / after comparison pages used in the document |

Both reports were produced through the desktop application for the same design
(plate girder bridge, 30 m span, 10.5 m carriageway, Pune, all IRC vehicles selected).

## What changed (short)

1. Every table is a PyLaTeX `LongTable` built by `core/reports/tables.py` — caption and column
   headers repeat on every page a table runs onto.
2. Row groups can no longer be split by a page break and nothing reaches the footer
   (page geometry, keep-together rules, page-bottom thresholds).
3. Vehicle and footpath live loads are reported in separate tables with unit columns
   (`core/reports/live_loads.py`, `chap3.py`).
4. Utilization-ratio bar charts with a red dashed UR = 1.0 line in Section 5.5 (`charts.py`).
5. Material quantity charts in Chapter 7.
6. `core/reports/styles.py` is the single source of truth for all formatting.

## Reproduce

```bash
# full run through the GUI (location, span, Design, Generate Report)
python tools/report_demo.py --out out/Report_After.pdf --district Pune --payload out/payload.pkl

# re-render the stored design without GUI / analysis (seconds)
python tools/render_report.py out/payload.pkl --out out/Report_After.pdf

# layout tests
pytest tests/unit/test_report_layout.py
```

`pdflatex` must be available (Osdag's `osdag_latex_env` on Linux / Windows; any TeX
distribution with the packages listed in `styles.latex_packages()` otherwise).
