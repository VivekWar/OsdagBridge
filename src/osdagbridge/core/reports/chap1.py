# =============================================================================
# Chapter 1: Project Information
# Presentation only — formatting comes from styles.py via tables.py.
# =============================================================================
from . import tables as T
from .report_utils import _tex

_CODES = (
    "Indian Roads Congress (IRC) 5: General Features of Design",
    "Indian Roads Congress (IRC) 6: Loads and Load Combinations",
    "Indian Roads Congress (IRC) 22: Composite Construction (Limit State Design)",
    "Indian Roads Congress (IRC) 24: Steel Road Bridges (Limit State Method)",
    "Indian Roads Congress (IRC) 112: Concrete Road Bridges (deck design)",
    "Indian Roads Congress Special Publication (IRC SP) 114: Seismic Design of Road Bridges",
    "Indian Standard (IS) 800: General Construction in Steel",
    "Indian Standard (IS) 2062: Hot Rolled Structural Steel Specification",
    "Indian Standard (IS) 6006: Steel Bearings",
)


def ch1_project_info(m):
    details = T.key_value_table(
        "Project and Design Team Details",
        [
            ("Project Name", _tex(m.project_name)),
            ("Project Location", _tex(m.project_location)),
            ("Designer", _tex(m.designer)),
            ("Reviewer", _tex(m.reviewer)),
            ("Organization", _tex(m.company)),
            ("Client", _tex(m.client)),
            ("Job Number", _tex(m.job_number)),
            ("Report Date", _tex(m.report_date)),
            ("Software", "OsdagBridge"),
        ],
        header=("Item", "Details"),
        label="tab:project-details",
    )
    codes = "\n".join(r"\item " + c for c in _CODES)
    return r"""
\chapter{Project Information}

This section records all project metadata as entered by the designer.

\section{Project and Design Team Details}
\label{sec:project-details}

""" + details + r"""
\section{Applicable Codes and Standards}
\label{sec:codes}

\begin{itemize}
""" + codes + r"""
\end{itemize}
"""
