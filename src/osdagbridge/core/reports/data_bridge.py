# =============================================================================
# OsdagBridge — Report data bridge (read-only access to stored design results)
# =============================================================================
"""Read-only accessors for the results the chapters need.

Nothing is calculated here: the classes only look values up in the
``output_dict`` produced by the design run and return them as plain Python
values (numbers / strings). Formatting is done by the chapter modules through
:mod:`styles` and :mod:`tables`.
"""
from __future__ import annotations

from typing import Optional, Tuple


def _to_float(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class BracingResults:
    """Member forces and member designs of a set of bracing frames.

    Used for the intermediate cross bracing and, when the end diaphragm is a
    bracing frame, for the end diaphragms as well.

    ``forces_dict``  — ``{"pairs": {"G1-G2": {...}}, "geometry": {...}}``
    ``pair_designs`` — ``{"G1-G2": {"diagonal": {"tension": raw, ...}, ...}}``
    """

    MEMBERS = ("diagonal", "chord")
    FORCE_TYPES = ("compression", "tension")

    def __init__(self, forces_dict: Optional[dict], pair_designs: Optional[dict]):
        self.forces_dict = forces_dict if isinstance(forces_dict, dict) else {}
        self.pair_designs = pair_designs if isinstance(pair_designs, dict) else {}

    # -- structure -----------------------------------------------------------
    def pairs(self) -> list:
        """Sorted girder-pair keys, e.g. ``['G1-G2', 'G2-G3']``."""
        pairs = self.forces_dict.get("pairs")
        return sorted(pairs.keys()) if isinstance(pairs, dict) else []

    def geometry(self) -> dict:
        geometry = self.forces_dict.get("geometry")
        return geometry if isinstance(geometry, dict) else {}

    def chord_enabled(self, which: str) -> bool:
        """``which`` is ``"top_chord"`` or ``"bottom_chord"``."""
        return bool(self.forces_dict.get(which, True))

    def has_design(self) -> bool:
        """True when at least one member design (utilization) is stored."""
        return any(self.efficiency(p, m, f) is not None
                   for p in self.pairs() for m in self.MEMBERS for f in self.FORCE_TYPES)

    # -- raw look-ups ----------------------------------------------------------
    def _pair_forces(self, pair: str) -> dict:
        data = (self.forces_dict.get("pairs") or {}).get(pair)
        return data if isinstance(data, dict) else {}

    def _osdag(self, pair: str, member: str, force_type: str) -> dict:
        """Summary of the Osdag member design (section, capacity, efficiency …)."""
        from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
        try:
            raw = self.pair_designs[pair][member][force_type]
            return _extract_osdag_summary(raw or {})
        except (KeyError, TypeError, AttributeError):
            return {}

    @staticmethod
    def _force_key(member: str, force_type: str, suffix: str) -> str:
        return f"{'diag' if member == 'diagonal' else 'chord'}_{force_type}_{suffix}"

    # -- member forces ---------------------------------------------------------
    def force(self, pair: str, member: str, force_type: str) -> Optional[float]:
        return _to_float(self._pair_forces(pair).get(self._force_key(member, force_type, "kN")))

    def governing_force(self, pair: str, member: str) -> Tuple[Optional[float], str]:
        """``(force in kN, force type)`` of the larger of tension / compression."""
        tension = self.force(pair, member, "tension")
        compression = self.force(pair, member, "compression")
        if tension is not None and compression is not None:
            if abs(compression) >= abs(tension):
                return compression, "compression"
            return tension, "tension"
        if compression is not None:
            return compression, "compression"
        if tension is not None:
            return tension, "tension"
        return None, "compression"

    def governing_load_case(self, pair: str, member: str, force_type: str) -> str:
        value = self._pair_forces(pair).get(self._force_key(member, force_type, "gov_lc"))
        return str(value) if value else ""

    # -- member design ---------------------------------------------------------
    def section(self, pair: str, member: str, force_type: str) -> str:
        value = self._osdag(pair, member, force_type).get("section")
        return str(value) if value else ""

    def connection(self, pair: str, member: str, force_type: str) -> str:
        value = self._osdag(pair, member, force_type).get("connection")
        return str(value) if value else ""

    def capacity(self, pair: str, member: str, force_type: str) -> Optional[float]:
        return _to_float(self._osdag(pair, member, force_type).get("capacity_kN"))

    def efficiency(self, pair: str, member: str, force_type: str) -> Optional[float]:
        """Utilization ratio of the member design."""
        return _to_float(self._osdag(pair, member, force_type).get("efficiency"))

    def slenderness(self, pair: str, member: str) -> Optional[float]:
        """KL/r — geometry based, the compression design is preferred."""
        for force_type in self.FORCE_TYPES:
            value = _to_float(self._osdag(pair, member, force_type).get("slenderness"))
            if value is not None:
                return value
        return None

    def effective_length_mm(self, member: str) -> Optional[float]:
        geometry = self.geometry()
        key = "diagonal_length_m" if member == "diagonal" else "horiz_proj_m"
        length = _to_float(geometry.get(key))
        return None if length is None else length * 1000.0


class ReportDataBridge:
    """Centralised, read-only view on the data of one report."""

    def __init__(self, output_dict: dict, input_dict: dict, payload=None):
        self.output_dict = output_dict or {}
        self.input_dict = input_dict or {}
        self.payload = payload

    @property
    def cross_bracing(self) -> BracingResults:
        return BracingResults(self.output_dict.get("crossbracing_forces_dict"),
                              self.output_dict.get("crossbracing_design_results"))

    @property
    def end_diaphragm(self) -> BracingResults:
        return BracingResults(self.output_dict.get("end_diaphragm_forces_dict"),
                              self.output_dict.get("end_diaphragm_design_results"))
