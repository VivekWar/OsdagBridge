# =============================================================================
# OsdagBridge — Report figure helpers (PyLaTeX Figure)
# =============================================================================
"""Figure blocks shared by every chapter of the design report.

All images (CAD views, analysis diagrams and the generated bar charts) are
embedded through PyLaTeX's :class:`~pylatex.Figure`. Widths, the maximum
height and the float placement come from :mod:`styles` — chapters only pass
the image path, a caption and the *name* of a width.
"""
from __future__ import annotations

import os
from typing import Optional, Sequence, Tuple

from pylatex import Figure, StandAloneGraphic
from pylatex.utils import NoEscape

from . import styles as S


def latex_path(path: str, base_dir: Optional[str] = None) -> str:
    """Path as LaTeX should see it: forward slashes, relative to ``base_dir``.

    Relative paths keep the document independent of the temporary build
    directory (whose absolute path may contain spaces or ``~``).
    """
    if base_dir:
        try:
            path = os.path.relpath(path, base_dir)
        except ValueError:      # different drive on Windows
            pass
    return path.replace("\\", "/")


def asset_path(path: Optional[str], asset_dir: Optional[str]) -> Optional[str]:
    """LaTeX path of a generated asset (chart image).

    The assets are written to ``<build dir>/<asset dir>``; the document is
    compiled in the build directory, so the path is given relative to it.
    Returns ``None`` when the asset was not produced.
    """
    if not path:
        return None
    base = os.path.dirname(os.path.abspath(asset_dir)) if asset_dir else None
    return latex_path(os.path.abspath(path), base)


def _graphic(path: str, width: str, limit_height: bool) -> StandAloneGraphic:
    options = "width=" + S.FIGURE.width(width)
    if limit_height:
        options += ",height=" + S.FIGURE.max_height + ",keepaspectratio"
    # \detokenize keeps unusual characters in the file name intact.
    return StandAloneGraphic(
        image_options=NoEscape(options),
        filename=NoEscape(r"\detokenize{%s}" % path.replace("\\", "/")),
    )


def _placeholder(caption: str) -> str:
    return (r"\fbox{\parbox{0.95\linewidth}{\centering\vspace{6pt}"
            r"\placeholder{figure not available: %s}\vspace{6pt}}}" % caption)


def figure(path: Optional[str], caption: str, *, width: str = "full",
           label: Optional[str] = None, numbered: bool = True,
           limit_height: bool = True) -> str:
    """One centred figure; a framed placeholder is shown when ``path`` is empty.

    ``width`` names a width in ``styles.FIGURE`` (``full``, ``wide``,
    ``medium``, ``chart``).
    """
    fig = Figure(position=S.FIGURE.placement)
    fig.append(NoEscape(r"\centering"))
    if path:
        fig.append(_graphic(path, width, limit_height))
    else:
        fig.append(NoEscape(_placeholder(caption)))
    if numbered:
        fig.add_caption(NoEscape(caption))
    else:
        fig.append(NoEscape(r"\caption*{%s}" % caption))
    if label:
        fig.append(NoEscape(r"\label{%s}" % label))
    return fig.dumps() + "\n"


def figure_row(items: Sequence[Tuple[Optional[str], str, Optional[str]]]) -> str:
    """Several small figures side by side, each with its own number.

    ``items`` is a sequence of ``(path, caption, label)``.
    """
    cell_width = S.FIGURE.width("third")
    cells = []
    for path, caption, label in items:
        if path:
            body = (r"\includegraphics[width=\linewidth]{\detokenize{%s}}"
                    % path.replace("\\", "/"))
        else:
            body = _placeholder(caption)
        cells.append("\n".join([
            r"\begin{minipage}[t]{%s}" % cell_width,
            r"\centering",
            body,
            r"\captionof{figure}{%s}" % caption + ((r"\label{%s}" % label) if label else ""),
            r"\end{minipage}",
        ]))
    return "\n".join([
        r"\rptneedspace{%s}" % S.SPACING.figure_min_start,
        S.vgap(),
        r"\noindent" + "\n" + "\n\\hfill\n".join(cells),
        r"\par" + S.vgap(S.SPACING.block_after),
    ]) + "\n"
