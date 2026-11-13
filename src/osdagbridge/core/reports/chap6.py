# =============================================================================
# Chapter 6: Drawings and Visualizations
# Presentation only — figure sizes come from styles.py via figures.py.
# =============================================================================
from . import figures as F


def ch6_drawings(fig_paths):
    """Chapter 6 – Drawings and Visualizations.

    Figure numbering (auto-incremented by LaTeX):
      6.1  Overall 3D Bridge Superstructure
      6.2  Typical Cross Section
      6.3  Top View
      6.4  3D View of Plate Girders
      6.5  Cross Section of Plate Girder
      6.6  Side View of Girder
      6.7  Cross Bracing Layout
      6.8  Cross Bracing -- Bracing Section
      6.9  Cross Bracing -- Top Chord Section
      6.10 Cross Bracing -- Bottom Chord Section
      6.11 End Diaphragm Layout
      6.12 End Diaphragm -- Bracing Section
      6.13 End Diaphragm -- Top Chord Section
      6.14 End Diaphragm -- Bottom Chord Section
    """
    get = fig_paths.get

    def fig(key, title, label):
        return F.figure(get(key), title, width="wide", label=label)

    cb_sections = F.figure_row([
        (get('cb_bracing'), 'Cross Bracing -- Bracing Section', 'fig:cb-bracing-sec'),
        (get('cb_top_chord'), 'Cross Bracing -- Top Chord Section', 'fig:cb-top-chord'),
        (get('cb_bottom_chord'), 'Cross Bracing -- Bottom Chord Section', 'fig:cb-bottom-chord'),
    ])
    ed_sections = F.figure_row([
        (get('ed_bracing'), 'End Diaphragm -- Bracing Section', 'fig:ed-bracing-sec'),
        (get('ed_top_chord'), 'End Diaphragm -- Top Chord Section', 'fig:ed-top-chord'),
        (get('ed_bottom_chord'), 'End Diaphragm -- Bottom Chord Section', 'fig:ed-bottom-chord'),
    ])

    return "\n".join([
        r"\chapter{Drawings and Visualizations}",
        r"\label{ch:drawings}",
        "",
        "This section presents CAD-generated views of the designed bridge and its "
        "components. All views are generated automatically by OsdagBridge using pythonOCC.",
        "",
        r"\section{Bridge Configuration and Layout}",
        r"\label{sec:bridge-layout}",
        fig('final_geometry', 'Overall 3D Bridge Superstructure', 'fig:bridge-3d'),
        fig('cross_section', 'Typical Cross Section', 'fig:cross-section'),
        fig('girder_top', 'Top View', 'fig:top-view'),
        r"\rptfiguresection{Plate Girder --- Detailed Views}",
        r"\label{sec:girder-views}",
        fig('girder_3d', '3D View of Plate Girders', 'fig:girder-3d'),
        fig('section_preview', 'Cross Section of Plate Girder', 'fig:girder-xsec'),
        fig('stiffener_preview', 'Side View of Girder', 'fig:girder-side'),
        r"\rptfiguresection{Cross Bracing Detail}",
        r"\label{sec:bracing-detail}",
        fig('cb_diagram', 'Cross Bracing Layout', 'fig:cb-layout'),
        cb_sections,
        r"\rptfiguresection{End Diaphragm Detail}",
        r"\label{sec:diaphragm-detail}",
        fig('ed_diagram', 'End Diaphragm Layout', 'fig:ed-layout'),
        ed_sections,
    ]) + "\n"
