"""Resolve and classify Midas Civil NX load cases.

Mirrors ``CsiLoadCaseResolver`` but adapted for the Midas REST API.

Key differences from CSI:
    - No "output selection" step is needed. Midas's ``/post/table``
      endpoint accepts load case names directly in the request body.
    - Load case classification uses ``GET /db/STLD`` (static load
      cases) and ``GET /db/LCOM-GEN`` (load combinations).
      NOTE: ``/db/STCT`` is Construction Stage Analysis Control Data
      (NOT static load cases), and ``/db/LDCOMB`` does not exist.
    - Combination type codes in Midas differ from CSI. The resolver
      maps them to the shared ``LoadCaseType`` enum.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List

from bda.domain.enums.load_case_enums import LoadCaseType
from bda.domain.results.load_case import LoadCase
from bda.infrastructure.adapters.analytical_software.exporters.midas_helpers.MidasAPI import MidasAPI

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResolvedMidasLoadCase:
    """A load-case name validated against the Midas model."""
    name: str
    kind: LoadCaseType


class MidasLoadCaseResolver:
    """Validate and classify Midas Civil NX load cases.

    Built at construction time by querying ``/db/STLD`` (static load
    cases) and ``/db/LCOM-GEN`` (general load combinations). Unlike
    the CSI resolver, there is no output-selection ceremony — Midas
    accepts case names directly in the POST body.
    """

    def __init__(self, api: MidasAPI) -> None:
        """Probe Midas for all available cases and combinations."""
        self._api = api
        self._index: Dict[str, LoadCaseType] = {}
        self._build_index()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build_index(self) -> None:
        """Populate ``self._index`` with every case/combo Midas knows.

        Endpoints (from Midas API manual):
            - ``GET /db/STLD`` — Static Load Cases
            - ``GET /db/LCOM-GEN`` — Load Combinations (General)

        Note: ``/db/STCT`` is "Construction Stage Analysis Control Data"
        — **not** static load cases. This was a bug in the original
        implementation, now corrected.
        """
        # Static load cases: GET /db/STLD
        # Response: {"STLD": {"1": {...}, "2": {...}}}
        try:
            stld_resp = self._api.request("GET", "/db/STLD")
            stld_data = stld_resp.json()
            # Try known response keys — Midas may use "STLD" as the
            # top-level key. Fall back to iterating all keys if needed.
            cases = stld_data.get("STLD", {})
            if not cases and "message" not in stld_data:
                # Fallback: the first dict-valued key might be the data
                for k, v in stld_data.items():
                    if isinstance(v, dict) and k != "message":
                        cases = v
                        logger.info(
                            "MidasLoadCaseResolver: STLD response key "
                            "was '%s' (not 'STLD')", k
                        )
                        break
            for _key, props in cases.items():
                if isinstance(props, dict):
                    name = props.get("NAME", props.get("LCNAME", ""))
                elif isinstance(props, str):
                    # Some Midas versions return {"1": "Dead", "2": "Live"}
                    name = props
                else:
                    continue
                if name:
                    self._index[name] = LoadCaseType.SINGLE_VALUED
            logger.info(
                "MidasLoadCaseResolver: loaded %d static load cases",
                sum(1 for v in self._index.values()
                    if v == LoadCaseType.SINGLE_VALUED),
            )
        except Exception as e:
            logger.warning("Could not load static load cases: %s", e)

        # Load combinations: GET /db/LCOM-GEN
        # Response: {"LCOM-GEN": {"1": {"NAME": "...", "iTYPE": 0, ...}}}
        # iTYPE: 0 = linear add, 1 = envelope, 2 = ABS, 3 = SRSS, etc.
        try:
            comb_resp = self._api.request("GET", "/db/LCOM-GEN")
            comb_data = comb_resp.json()
            combos = comb_data.get("LCOM-GEN", {})
            if not combos and "message" not in comb_data:
                for k, v in comb_data.items():
                    if isinstance(v, dict) and k != "message":
                        combos = v
                        logger.info(
                            "MidasLoadCaseResolver: LCOM-GEN response "
                            "key was '%s' (not 'LCOM-GEN')", k
                        )
                        break
            for _key, props in combos.items():
                if not isinstance(props, dict):
                    continue
                name = props.get("NAME", "")
                if not name:
                    continue
                i_type = props.get("iTYPE", 0)
                if i_type == 1:
                    self._index[name] = LoadCaseType.ENVELOPE
                else:
                    # Linear add, ABS, SRSS — all produce CB:max/min rows
                    self._index[name] = LoadCaseType.COMBINATION
            logger.info(
                "MidasLoadCaseResolver: loaded %d combinations",
                sum(1 for v in self._index.values()
                    if v != LoadCaseType.SINGLE_VALUED),
            )
        except Exception as e:
            logger.warning("Could not load load combinations: %s", e)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def available(self) -> List[LoadCase]:
        """Return every case/combo the Midas model currently exposes."""
        return [
            LoadCase(name=name, load_case_type=kind)
            for name, kind in self._index.items()
        ]

    def resolve(self, names: Iterable[str]) -> List[ResolvedMidasLoadCase]:
        """Validate every requested name and return its classification.

        Raises:
            KeyError: If any name is unknown to Midas.
        """
        resolved: List[ResolvedMidasLoadCase] = []
        for name in names:
            if name not in self._index:
                raise KeyError(
                    f"Load case '{name}' not found in Midas model. "
                    f"Available: {sorted(self._index.keys())}"
                )
            resolved.append(
                ResolvedMidasLoadCase(name=name, kind=self._index[name])
            )
        return resolved

    def is_combination(self, name: str) -> bool:
        """True if the load case is a combination (produces CB:max/min)."""
        kind = self._index.get(name)
        return kind in (LoadCaseType.COMBINATION, LoadCaseType.ENVELOPE)

    def classify(self, name: str) -> LoadCaseType:
        """Return the classification of a load case by name."""
        if name not in self._index:
            raise KeyError(f"Load case '{name}' not found in Midas model")
        return self._index[name]
