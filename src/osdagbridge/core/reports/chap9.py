# =============================================================================
# References
# =============================================================================

_REFERENCES = (
    r"IRC 5 (2024) --- \rptcite{Standard Specifications and Code of Practice for Road Bridges, Section I: General Features of Design.}",
    r"IRC 6 (2017) --- \rptcite{Standard Specifications and Code of Practice for Road Bridges, Section II: Loads and Load Combinations.}",
    r"IRC 22 (2014) --- \rptcite{Standard Specifications and Code of Practice for Road Bridges, Section VI: Composite Construction (Limit State Design).}",
    r"IRC 24 (2010) --- \rptcite{Standard Specifications and Code of Practice for Road Bridges, Section V: Steel Road Bridges (Limit State Method).}",
    r"IRC 112 (2011) --- \rptcite{Code of Practice for Concrete Road Bridges.}",
    r"IRC SP 114 (2018) --- \rptcite{Guidelines for Seismic Design of Road Bridges.}",
    r"IS 800 (2007) --- \rptcite{Indian Standard: General Construction in Steel --- Code of Practice.}",
    r"IS 2062 (2011) --- \rptcite{Hot Rolled Medium and High Tensile Structural Steel --- Specification.}",
    r"Subramanian, N. (2008). \rptcite{Design of Steel Structures.} Oxford University Press.",
    r"Steel-INSDAG Teaching Resource Materials. \url{https://www.steel-insdag.org}",
)


def references():
    items = "\n\n".join(r"\item " + ref for ref in _REFERENCES)
    return r"""
\rptfrontchapter{References}

\begin{enumerate}
""" + items + r"""
\end{enumerate}
"""
