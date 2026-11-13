# =============================================================================
# OsdagBridge — Report table builder (PyLaTeX LongTable)
# =============================================================================
"""Table builder shared by every chapter of the design report.

All report tables are produced by :func:`table`, which builds a PyLaTeX
:class:`~pylatex.LongTable` and therefore guarantees, for every table:

* the caption and the column-header row are repeated at the top of every page
  the table runs onto (``\\endfirsthead`` / ``\\endhead``), with a
  "Continued on next page" marker at the bottom of a broken page
  (``\\endfoot`` / ``\\endlastfoot``);
* rows that belong together (a :class:`Group`, e.g. all rows of girder "G4")
  are kept on one page, so a row-spanning label can never be pushed below the
  text area into the footer;
* the table spans exactly the text width — column widths are *relative*
  weights taken from a named layout in :mod:`styles`;
* cell padding, rules, header fill and fonts come from :mod:`styles` only.

Chapter modules pass content (already LaTeX-escaped strings) and the *name* of
a layout; they never write table markup or formatting values themselves.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Union

from pylatex import LongTable, MultiColumn, MultiRow
from pylatex.utils import NoEscape

from . import styles as S

Cell = Union[str, "NoEscape", None]


# ---------------------------------------------------------------------------
# Row / header descriptors used by the chapter modules
# ---------------------------------------------------------------------------

@dataclass
class Group:
    """Rows sharing a row-spanning label in the first column.

    ``rows`` hold the cells of the *remaining* columns. The whole group is
    kept on one page.
    """

    label: Cell
    rows: List[Sequence[Cell]]


@dataclass
class Band:
    """Full-width sub-heading row inside a table."""

    text: Cell


@dataclass
class Span:
    """Header cell spanning several columns with a second header line below."""

    title: Cell
    subheaders: Sequence[Cell]


@dataclass
class Merged:
    """Body cell spanning ``n`` columns (used for one-line messages)."""

    text: Cell
    n: int
    align: str = "c"


Row = Union[Sequence[Cell], Group, Band]


# ---------------------------------------------------------------------------
# PyLaTeX LongTable with the longtable features PyLaTeX does not expose
# ---------------------------------------------------------------------------

class ReportLongTable(LongTable):
    """``longtable`` environment with repeated headers and keep-together rows.

    PyLaTeX's :class:`LongTable` already offers ``end_table_header()``
    (``\\endhead``), ``end_table_footer()`` and ``end_table_last_footer()``.
    This subclass adds the first-page header (``\\endfirsthead``), captions
    placed inside the table, rows that forbid a page break after them
    (``\\\\*``) and partial rules that stay visible on filled header rows.
    """

    _latex_name = "longtable"

    def __init__(self, table_spec: str, n_cols: int, **kwargs):
        # ``width`` is given explicitly: the spec uses custom column types
        # (L/C/R with a width argument) that PyLaTeX cannot count itself.
        super().__init__(NoEscape(table_spec), width=n_cols, **kwargs)
        self.n_cols = n_cols

    # -- structure -----------------------------------------------------------
    def add_caption(self, caption: str, label: Optional[str] = None,
                    continued: bool = False) -> None:
        if continued:
            # Empty optional argument: no second entry in a list of tables.
            text = r"\caption[]{%s%s}" % (caption, S.TABLE.continued_caption_suffix)
        else:
            text = r"\caption{%s}" % caption
            if label:
                text += r"\label{%s}" % label
        self.append(NoEscape(text + r"\\"))

    def end_first_header(self) -> None:
        self.append(NoEscape(r"\endfirsthead"))

    def add_raw(self, tex: str) -> None:
        self.append(NoEscape(tex))

    # -- rows ----------------------------------------------------------------
    def add_cells(self, cells: Sequence[object], nobreak: bool = False) -> None:
        """Add one row. ``nobreak`` forbids a page break after the row."""
        parts = []
        for c in cells:
            parts.append(c.dumps() if hasattr(c, "dumps") else ("" if c is None else str(c)))
        self.append(NoEscape(" & ".join(parts) + (r" \\*" if nobreak else r" \\")))

    def add_rule(self, first_col: int = 1, nobreak: bool = False) -> None:
        """Horizontal rule from column ``first_col`` to the last column.

        ``\\hline`` deliberately contains a page-break opportunity and
        ``\\cline`` is followed by a breakable skip. Rules *inside* a block
        of rows that must stay together are therefore drawn with ``\\hhline``
        (a plain rule row) followed by an explicit ``\\nobreak``.
        """
        if first_col <= 1 and not nobreak:
            self.add_hline()
            return
        spec = "|" + "~|" * (first_col - 1) + "-|" * (self.n_cols - first_col + 1)
        self.append(NoEscape(r"\hhline{%s}" % spec + (r"\noalign{\nobreak}" if nobreak else "")))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cell(value: Cell) -> str:
    """Normalise a body cell: ``None`` / empty → the empty-cell marker."""
    if value is None:
        return S.TABLE.empty_cell
    text = str(value)
    return text if text.strip() else S.TABLE.empty_cell


def stacked(lines: Sequence[str], tall: bool = False) -> str:
    """Several lines in one cell. ``tall`` adds room for display fractions."""
    strut = S.TABLE.formula_strut if tall else ""
    return r"\newline ".join(strut + line for line in lines)


_TEX_NOISE = re.compile(r"\\[a-zA-Z]+\*?|[{}$^_~]|\\.")


def _text_lines(cell: object, width_pt: float, char_width: float) -> int:
    """Rough number of lines a cell wraps to (LaTeX commands are ignored)."""
    if isinstance(cell, Merged):
        cell = cell.text
    text = _TEX_NOISE.sub("", str(cell or ""))
    explicit = str(cell or "").count(r"\newline") + 1
    wrapped = math.ceil(len(text) * char_width / max(width_pt, 1.0)) if text else 1
    return max(explicit, wrapped, 1)


def _estimated_height(layout: S.TableLayout, header, rows: Sequence[Row], note: Optional[str]) -> float:
    """Approximate height of a complete table in points (see ``styles.TABLE``)."""
    t = S.TABLE
    compact = layout.compact
    char_w = t.est_char_width_compact if compact else t.est_char_width
    row_h = t.est_row_height_compact if compact else t.est_row_height
    line_h = t.est_line_height_compact if compact else t.est_line_height
    total = float(sum(w for _, w in layout.columns)) or 1.0
    usable = S.PAGE.text_width_pt() - 12.0 * layout.n_cols          # minus cell paddings
    widths = [usable * w / total for _, w in layout.columns]

    def row_height(cells: Sequence[object], cols: Sequence[float]) -> float:
        lines = max([_text_lines(c, w, char_w) for c, w in zip(cells, cols)] or [1])
        return row_h + (lines - 1) * line_h

    height = t.est_caption_height
    if header:
        flat = []
        for h in header:
            flat.extend(h.subheaders if isinstance(h, Span) else [h])
        height += row_height(flat, widths) * (2 if any(isinstance(h, Span) for h in header) else 1)
    for row in rows:
        if isinstance(row, Band):
            height += row_h
        elif isinstance(row, Group):
            for sub in row.rows:
                height += row_height(sub, widths[1:])
        else:
            height += row_height(row, widths)
    if note:
        height += line_h * (_text_lines(note, S.PAGE.text_width_pt(), char_w) + 0.5)
    return height


def _column_spec(layout: S.TableLayout) -> str:
    """Column specification with widths relative to ``\\rptTableWidth``."""
    total = float(sum(w for _, w in layout.columns)) or 1.0
    parts = []
    for align, weight in layout.columns:
        col_type = {"l": "L", "c": "C", "r": "R"}.get(align, "L")
        parts.append("%s{%.4f\\rptTableWidth}" % (col_type, weight / total))
    return "|" + "|".join(parts) + "|"


def _header_cell(text: Cell) -> str:
    return r"\rpthead{%s}" % ("" if text is None else str(text))


def _header_rows(header: Sequence[Union[Cell, Span]], n_cols: int) -> List[str]:
    """LaTeX lines of the (one- or two-level) column header."""
    bg = S.TABLE.header_bg
    fill = r"\rowcolor{%s}" % bg
    has_span = any(isinstance(h, Span) for h in header)

    if not has_span:
        cells = " & ".join(_header_cell(h) for h in header)
        return [fill + cells + r" \\", r"\hline"]

    # Two-level header. Single cells span both rows: they are written in the
    # *second* row with a negative \multirow so the row fill does not paint
    # over them; the rule between the two levels is drawn with \hhline so it
    # stays visible on the filled background.
    top, bottom, hh = [], [], []
    col = 1
    for h in header:
        if isinstance(h, Span):
            k = len(h.subheaders)
            right = "|"
            left = "|" if col == 1 else ""
            top.append(r"\multicolumn{%d}{%sc%s}{%s}" % (k, left, right, _header_cell(h.title)))
            bottom.extend(_header_cell(s) for s in h.subheaders)
            hh.append("|" + "|".join(["-"] * k) + "|" if col == 1 else "|".join(["-"] * k) + "|")
            col += k
        else:
            top.append("")
            bottom.append(r"\multirow{-2}{=}{%s}" % _header_cell(h))
            gap = r">{\arrayrulecolor{%s}}->{\arrayrulecolor{%s}}" % (bg, S.TABLE.rule_color)
            hh.append(("|" if col == 1 else "") + gap + "|")
            col += 1
    return [
        fill + " & ".join(top) + r" \\*",
        r"\hhline{%s}" % "".join(hh),
        fill + " & ".join(bottom) + r" \\",
        r"\hline",
    ]


def _body_rows(table: ReportLongTable, rows: Iterable[Row], n_cols: int,
               keep_last: bool = False) -> None:
    """Write the body rows.

    ``keep_last`` forbids a page break after the last row (used when a note
    row follows, so the note never ends up alone on the next page).
    """
    keep = S.TABLE.keep_group_together
    rows = list(rows)
    count = len(rows)
    # Position of every row among the data rows (bands are headings, not data).
    data_total = sum(1 for r in rows if not isinstance(r, Band))
    data_seen = 0
    for index, row in enumerate(rows):
        if not isinstance(row, Band):
            data_seen += 1
        # No page break after this row when ...
        hold = (
            (keep_last and index == count - 1)                       # ... a note row follows,
            or data_seen < S.TABLE.min_rows_at_start                 # ... it would leave too few rows
            or (data_total - data_seen < S.TABLE.min_rows_at_end     # at the start / end of a page.
                and index < count - 1)
        )
        if isinstance(row, Band):
            cell = MultiColumn(n_cols, align=NoEscape("|l|"),
                               data=NoEscape(r"\cellcolor{%s}\rptband{%s}" % (S.TABLE.band_bg, row.text)))
            # A band heads the rows that follow it: no page break after it.
            table.add_cells([cell], nobreak=True)
            table.add_rule(nobreak=True)
        elif isinstance(row, Group):
            sub_rows = [list(r) for r in row.rows] or [[None] * (n_cols - 1)]
            n = len(sub_rows)
            for i, sub in enumerate(sub_rows):
                last = i == n - 1
                if i == 0:
                    first = MultiRow(n, width="=", data=NoEscape(r"\centering " + _cell(row.label))) \
                        if n > 1 else NoEscape(_cell(row.label))
                else:
                    first = NoEscape("")
                stay = (keep and not last) or (last and hold)
                table.add_cells([first] + [_render(c) for c in sub], nobreak=stay)
                if last:
                    table.add_rule(nobreak=hold)
                else:
                    # rule under columns 2..n only; the group label spans the rows
                    table.add_rule(first_col=2, nobreak=keep)
        else:
            table.add_cells([_render(c) for c in row], nobreak=hold)
            table.add_rule(nobreak=hold)


def _render(cell: object) -> object:
    if isinstance(cell, Merged):
        return MultiColumn(cell.n, align=NoEscape(cell.align + "|"), data=NoEscape(_cell(cell.text)))
    return NoEscape(_cell(cell))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def table(caption: str,
          layout: Union[str, S.TableLayout],
          header: Optional[Sequence[Union[Cell, Span]]],
          rows: Iterable[Row],
          *,
          note: Optional[str] = None,
          label: Optional[str] = None) -> str:
    """Return the LaTeX source of one report table.

    Parameters
    ----------
    caption:
        Table title (LaTeX). Numbering is automatic.
    layout:
        Name of a layout in ``styles.TABLE_LAYOUTS`` (or a ``TableLayout``).
    header:
        Column titles; a :class:`Span` creates a two-level header.
    rows:
        Body rows — plain cell sequences, :class:`Group` or :class:`Band`.
    note:
        Optional note printed directly below the table. It is the last row of
        the table and cannot be separated from the row above it.
    label:
        Optional ``\\label`` for cross references.
    """
    lay = S.TABLE_LAYOUTS[layout] if isinstance(layout, str) else layout
    n = lay.n_cols
    t = S.TABLE
    rows = list(rows)

    tab = ReportLongTable(_column_spec(lay), n)

    header_lines = _header_rows(header, n) if header else []

    # --- first page: caption + header ---------------------------------------
    tab.add_caption(caption, label)
    tab.add_hline()
    for line in header_lines:
        tab.add_raw(line)
    tab.end_first_header()

    # --- following pages: "(continued)" caption + header ---------------------
    tab.add_caption(caption, continued=True)
    tab.add_hline()
    for line in header_lines:
        tab.add_raw(line)
    tab.end_table_header()

    # --- foot of a broken page / foot of the last page ------------------------
    tab.add_raw(r"\rptcontinued{%d} \\" % n)
    tab.end_table_footer()
    tab.end_table_last_footer()

    _body_rows(tab, rows, n, keep_last=bool(note))

    # --- note: last (un-ruled) row of the table, kept with the row above ------
    if note:
        tab.add_raw(r"\multicolumn{%d}{@{}p{\linewidth}@{}}{\tablenote{%s}} \\" % (n, note))

    # --- per-table set-up (font, padding, usable width) -----------------------
    col_sep = t.col_sep_compact if lay.compact else t.col_sep
    stretch = t.row_stretch_compact if lay.compact else t.row_stretch
    font = S.FONTS.table_compact if lay.compact else S.FONTS.table_body
    # Short tables are kept whole: start a new page first if the table would
    # not fit completely on the current one.
    estimate = _estimated_height(lay, header, rows, note)
    keep_whole = estimate <= t.keep_whole_max_fraction * S.PAGE.text_height_pt()
    setup = "\n".join(([r"\rptneedspace{%.0fpt}" % estimate] if keep_whole else []) + [
        r"\begingroup",
        font,
        r"\setlength{\tabcolsep}{%s}" % col_sep,
        r"\renewcommand{\arraystretch}{%s}" % stretch,
        # usable width = line width - cell paddings - vertical rules
        r"\setlength{\rptTableWidth}{\dimexpr\linewidth-%d\tabcolsep-%d\arrayrulewidth\relax}"
        % (2 * n, n + 1),
        r"\setlength{\LTcapwidth}{\linewidth}",     # caption as wide as the table
    ])
    return "\n".join([setup, tab.dumps(), r"\endgroup"]) + "\n"


def key_value_table(caption: str, rows: Iterable[Sequence[Cell]], *,
                    layout: str = "key_value",
                    header: Optional[Sequence[Cell]] = None,
                    note: Optional[str] = None,
                    label: Optional[str] = None) -> str:
    """Two-column *Parameter | Value* table."""
    if header is None:
        header = (S.TEXT.parameter, S.TEXT.value)
    return table(caption, layout, header, rows, note=note, label=label)


def unit_table(caption: str, rows: Iterable[Sequence[Cell]], *,
               note: Optional[str] = None, label: Optional[str] = None) -> str:
    """Four-column *Parameter | Value | Unit | Reference / Remarks* table."""
    header = (S.TEXT.parameter, S.TEXT.value, S.TEXT.unit, S.TEXT.reference)
    return table(caption, "param_value_unit_ref", header, rows, note=note, label=label)


def plain_block(layout: Union[str, S.TableLayout], rows: Iterable[Sequence[Cell]],
                bold_first: bool = True) -> str:
    """Un-captioned, non-floating grid (title page / information blocks)."""
    lay = S.TABLE_LAYOUTS[layout] if isinstance(layout, str) else layout
    n = lay.n_cols
    lines = [
        r"\begingroup",
        r"\setlength{\rptTableWidth}{\dimexpr\linewidth-%d\tabcolsep-%d\arrayrulewidth\relax}"
        % (2 * n, n + 1),
        r"\noindent\begin{tabular}{%s}" % _column_spec(lay),
        r"\hline",
    ]
    for row in rows:
        cells = [_cell(c) for c in row]
        if bold_first and cells:
            cells[0] = r"\cellcolor{%s}\rpthead{%s}" % (S.TABLE.header_bg, cells[0])
        lines.append(" & ".join(cells) + r" \\")
        lines.append(r"\hline")
    lines += [r"\end{tabular}", r"\endgroup"]
    return "\n".join(lines) + "\n"
