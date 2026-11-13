# =============================================================================
# OsdagBridge — Report utilities (escaping, value formatting, girder labels)
# =============================================================================
"""Content helpers shared by the chapter generators.

Only *content* helpers live here (LaTeX escaping, number formatting, lookup of
girder labels). Everything that concerns the look of the report is defined in
:mod:`styles` and applied by :mod:`tables` / :mod:`figures`.
"""
from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_TS_NO_OF_GIRDERS
)


# Glyphs that pdflatex (T1 / Latin Modern) cannot print directly. They occur in
# section designations ("∠ 100 ⅹ 100ⅹ 10") and in the check names / notes
# produced by the design engine ("Leg ≤ H_limit", "mm⁴").
_UNICODE_TO_LATEX = {
    '∠': 'L', 'ⅹ': 'x', '×': 'x', '–': '-', '—': '-', '−': '-',
    '’': "'", '‘': "'", '“': '"', '”': '"',
    '≤': r'$\leq$', '≥': r'$\geq$', '·': r'$\cdot$', '±': r'$\pm$', '√': r'$\surd$',
    '→': r'$\rightarrow$', '°': r'\textdegree{}',
    '²': r'\textsuperscript{2}', '³': r'\textsuperscript{3}', '⁴': r'\textsuperscript{4}',
    'α': r'$\alpha$', 'β': r'$\beta$', 'γ': r'$\gamma$', 'δ': r'$\delta$', 'Δ': r'$\Delta$',
    'ε': r'$\varepsilon$', 'λ': r'$\lambda$', 'μ': r'$\mu$', 'π': r'$\pi$', 'σ': r'$\sigma$',
    'τ': r'$\tau$', 'φ': r'$\phi$', 'χ': r'$\chi$',
}


def _tex(value):
    """Escape a Python value for safe LaTeX embedding."""
    s = str(value) if value is not None else ''
    if not s:
        return r''
    s = s.replace('\\', r'\textbackslash{}')
    for ch, esc in [('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                    ('{', r'\{'), ('}', r'\}'),
                    ('_', r'\_\allowbreak{}'),
                    ('~', r'\textasciitilde{}'), ('^', r'\^{}')]:
        s = s.replace(ch, esc)
    # \textbackslash{} was written before the braces were escaped: restore it.
    s = s.replace(r'\textbackslash\{\}', r'\textbackslash{}')
    s = s.replace(':', r':\allowbreak{}')
    for uni, latex in _UNICODE_TO_LATEX.items():
        s = s.replace(uni, latex)
    # Anything else outside Latin-1 has no glyph in the report font.
    return ''.join(ch if ord(ch) < 256 else '?' for ch in s)


def fmt_num(value, nd=2, strip=False):
    """Format a number with ``nd`` decimals; ``''`` when it is not numeric.

    ``strip=True`` removes trailing zeros (``11.40`` → ``11.4``).
    """
    try:
        text = f"{float(value):.{nd}f}"
    except (TypeError, ValueError):
        return ''
    if strip and '.' in text:
        text = text.rstrip('0').rstrip('.')
    if text.startswith('-') and not text.strip('-0.'):     # "-0.00" -> "0.00"
        text = text[1:]
    return text


def _clean_number(val):
    """Trim binary floating-point noise (``11.399999999999999`` → ``11.4``)."""
    if isinstance(val, bool):
        return val
    if isinstance(val, float) or type(val).__name__ in ('float64', 'float32'):
        return fmt_num(val, nd=4, strip=True)
    return val


def _render_value(source_dict, key, unit=""):
    val = source_dict.get(key)
    if val in ("", None):
        return ""
    return _tex(_clean_number(val)) + unit


def with_unit(value, unit, nd=2):
    """``'12.34 kN'`` — empty string when the value is missing."""
    text = fmt_num(value, nd)
    if not text:
        return ''
    return f"{text} {unit}" if unit else text


def dimension_mm(value, nd=0):
    """Plate dimension in millimetres.

    The girder section keys are entered in mm in the UI, but after an
    optimised design run the backend writes them back in metres (``1.67``
    for a 1670 mm deep girder). A plate dimension below 5 can only be a value
    in metres (the thinnest plate is 5 mm, the deepest girder < 5 m), so such
    values are converted; values already in mm pass through unchanged.
    """
    try:
        f = float(value)
    except (TypeError, ValueError):
        return ''
    if 0 < f < 5.0:
        f *= 1000.0
    return fmt_num(f, nd)


def get_girder_entries(input_dict):
    """
    Retrieve all girder labels and member IDs from backend keys.

    Usage Example:
    --------------------------
    girder_entries = get_girder_entries(bridge.input_dict)

    # 1. Fallback handling (if backend hasn't populated keys yet)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]

    # 2. Get total number of girders safely
    n_girders = len(girder_entries)

    # 3. Iterate over the girders to build table rows
    for lbl, mid in girder_entries:
        # lbl will be e.g., "G1", mid will be e.g., "G1M1"
        # Access girder specific keys dynamically:
        # val = input_dict.get(f"{KEY_MP_GIRDER_DEPTH}.{lbl}.{mid}")
        pass

    Returns:
        List[Tuple[str, str]]
    """
    try:
        n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 0) or 0)
    except (TypeError, ValueError):
        n = 0

    entries = []

    for i in range(1, n + 1):
        entries.append(
            (
                input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{i}", ""),
                input_dict.get(f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1", ""),
            )
        )

    return entries


def girder_entries_or_default(input_dict):
    """Girder ``(label, member id)`` pairs with a generic fallback."""
    entries = get_girder_entries(input_dict)
    if entries and any(lbl for lbl, _ in entries):
        return entries
    try:
        n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 1) or 1)
    except (TypeError, ValueError):
        n = 1
    return [(f"G{i}", "M1") for i in range(1, max(n, 1) + 1)]
