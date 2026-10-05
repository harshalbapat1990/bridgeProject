"""Resolve and enable CSI load cases for result output.

Calculators refer to load cases by name. Before any result call
(`Results.FrameForce`, `Results.JointDispl`, ...) the corresponding
case or combination must be marked for output via
`Results.Setup.SetCaseSelectedForOutput` or
`Results.Setup.SetComboSelectedForOutput`.

This helper:
    1. Validates that every requested name exists in CSI.
    2. Classifies each name as a single-valued case, combination, or
       envelope (so the fetchers know whether to expect one value pair
       or a full max/min envelope).
    3. Enables the right set of names for output and remembers them so
       it can restore the previous selection on close.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from bda.domain.enums.load_case_enums import LoadCaseType
from bda.domain.results.load_case import LoadCase

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResolvedLoadCase:
    """A load-case name that has been validated against CSI."""
    name: str
    kind: LoadCaseType


class CsiLoadCaseResolver:
    """Validate, classify and enable CSI load cases for output."""

    def __init__(self, sap_model: Any) -> None:
        """Probe CSI for all available cases and combinations."""
        self._sap_model = sap_model
        self._index: Dict[str, LoadCaseType] = {}
        self._enabled: List[str] = []
        self._previously_enabled_cases: List[str] = []
        self._previously_enabled_combos: List[str] = []
        self._case_names: tuple = ()
        self._combo_names: tuple = ()
        self._build_index()
        self._capture_initial_state()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build_index(self) -> None:
        """Populate `self._index` with every case/combo CSI knows.

        Implementation hints:
            - `LoadCases.GetNameList` returns single-valued analysis cases.
            - `RespCombo.GetNameList` returns combinations. For each combo,
              `RespCombo.GetTypeOAPI` tells if it's linear additive
              (SINGLE_VALUED for our purposes) or envelope (ENVELOPE).
        """
        # Load analysis cases (always SINGLE_VALUED)
        case_result = self._sap_model.LoadCases.GetNameList()
        case_count = case_result[0]
        self._case_names = case_result[1] if case_count > 0 else ()
        for name in self._case_names:
            self._index[name] = LoadCaseType.SINGLE_VALUED

        # Load response combinations
        combo_result = self._sap_model.RespCombo.GetNameList()
        combo_count = combo_result[0]
        self._combo_names = combo_result[1] if combo_count > 0 else ()
        for name in self._combo_names:
            # GetTypeOAPI returns a tuple; index [0] is the type code.
            # Type code 1 indicates envelope; others are linear additive.
            type_code_tuple = self._sap_model.RespCombo.GetTypeOAPI(name)
            type_code = type_code_tuple[0] if isinstance(type_code_tuple, tuple) else type_code_tuple
            if type_code == 1:
                # Type code 1 is envelope
                self._index[name] = LoadCaseType.ENVELOPE
            else:
                # Other type codes are linear additive combinations
                self._index[name] = LoadCaseType.COMBINATION

    def _capture_initial_state(self) -> None:
        """Capture which cases and combos are currently enabled for output.

        This allows restore() to revert only the selections we made.
        """
        for name in self._case_names:
            if self._sap_model.Results.Setup.GetCaseSelectedForOutput(name):
                self._previously_enabled_cases.append(name)

        for name in self._combo_names:
            if self._sap_model.Results.Setup.GetComboSelectedForOutput(name):
                self._previously_enabled_combos.append(name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def available(self) -> List[LoadCase]:
        """Return every case/combo CSI currently exposes."""
        return [LoadCase(name=name, load_case_type=kind) for name, kind in self._index.items()]

    def resolve(self, names: Iterable[str]) -> List[ResolvedLoadCase]:
        """Validate every requested name and return its classification.

        Raises:
            KeyError: If any name is unknown to CSI.
        """
        resolved: List[ResolvedLoadCase] = []
        for name in names:
            if name not in self._index:
                raise KeyError(f"Load case '{name}' not found in CSI model")
            resolved.append(ResolvedLoadCase(name=name, kind=self._index[name]))
        return resolved

    def enable_for_output(self, names: Iterable[str]) -> None:
        """Mark each name for result output in CSI.

        Uses `SetCaseSelectedForOutput` for single-valued cases and
        `SetComboSelectedForOutput` for combinations / envelopes.
        Remembers the enabled names so `restore()` can undo the changes.
        """
        for name in names:
            if name not in self._index:
                raise KeyError(f"Load case '{name}' not found in CSI model")

            kind = self._index[name]
            if kind == LoadCaseType.SINGLE_VALUED:
                # Check if this is actually a case (not a combo that was misclassified)
                if name in self._case_names:
                    self._sap_model.Results.Setup.SetCaseSelectedForOutput(name, True)
                else:
                    # It's a SINGLE_VALUED combo (linear additive)
                    self._sap_model.Results.Setup.SetComboSelectedForOutput(name, True)
            else:
                # ENVELOPE or COMBINATION type
                self._sap_model.Results.Setup.SetComboSelectedForOutput(name, True)

            self._enabled.append(name)

    def restore(self) -> None:
        """Undo any output-selection changes made by `enable_for_output`."""
        # First, deselect all cases and combos for output
        self._sap_model.Results.Setup.DeselectAllCasesAndCombosForOutput()

        # Then re-enable only those that were previously enabled
        for name in self._previously_enabled_cases:
            try:
                self._sap_model.Results.Setup.SetCaseSelectedForOutput(name, True)
            except Exception as e:
                logger.warning(f"Could not restore case '{name}' for output: {e}")

        for name in self._previously_enabled_combos:
            try:
                self._sap_model.Results.Setup.SetComboSelectedForOutput(name, True)
            except Exception as e:
                logger.warning(f"Could not restore combo '{name}' for output: {e}")
