"""Validate a DataRequest against a live analysis model before fetching.

Currently checks that every element ID, node ID, and load case name
in the request actually exists in the target model. Designed to be
extended with structural sanity checks in later phases:

    - Model identity verification (is this the right model?)
    - Extreme-value plausibility (bending within N% of a simple calc?)
    - Self-weight equilibrium (sum of element SW ≈ SW reaction?)

All future checks follow the same pattern: run the check, append
``ValidationFinding`` items to the report, let the caller decide
whether to abort or continue.

Usage::

    validator = RequestValidator(importer)
    report = validator.validate(merged_request)
    if not report.passed:
        for f in report.findings:
            print(f"{f.severity}: {f.message}")
        sys.exit(1)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Set

from bda.domain.results.data_request import DataRequest
from importer.i_result_importer import IResultImporter

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# Report data structures
# ─────────────────────────────────────────────────────────────────────


class Severity(Enum):
    """How serious a validation finding is."""
    ERROR = "ERROR"      # Hard fail — cannot proceed
    WARNING = "WARNING"  # Proceed with caution


@dataclass
class ValidationFinding:
    """A single validation issue."""
    severity: Severity
    check: str       # Which check produced this (e.g. "element_ids")
    message: str


@dataclass
class ValidationReport:
    """Collects all findings from a validation run."""
    findings: List[ValidationFinding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True if there are no ERROR-level findings."""
        return not any(f.severity == Severity.ERROR for f in self.findings)

    @property
    def errors(self) -> List[ValidationFinding]:
        return [f for f in self.findings if f.severity == Severity.ERROR]

    @property
    def warnings(self) -> List[ValidationFinding]:
        return [f for f in self.findings if f.severity == Severity.WARNING]

    def add(self, severity: Severity, check: str, message: str) -> None:
        self.findings.append(ValidationFinding(severity, check, message))

    def log_summary(self) -> None:
        """Write findings to the logger."""
        if self.passed and not self.warnings:
            logger.info("Validation passed — all IDs and load cases exist.")
            return
        for f in self.findings:
            if f.severity == Severity.ERROR:
                logger.error("[%s] %s: %s", f.severity.value, f.check, f.message)
            else:
                logger.warning("[%s] %s: %s", f.severity.value, f.check, f.message)


# ─────────────────────────────────────────────────────────────────────
# Validator
# ─────────────────────────────────────────────────────────────────────


class RequestValidator:
    """Validate a ``DataRequest`` against a live model via its importer.

    The validator queries the importer's sub-components (id mapper,
    load case resolver) to confirm that every requested ID and load case
    name exists in the running model. It does NOT fetch results — only
    metadata.

    Args:
        importer: A concrete ``IResultImporter`` that is already
            connected to the target model.
    """

    def __init__(self, importer: IResultImporter) -> None:
        self._importer = importer

    def validate(self, request: DataRequest) -> ValidationReport:
        """Run all validation checks and return a report.

        Checks (current):
            1. Every ``element_id`` exists in the model.
            2. Every ``node_id`` exists in the model.
            3. Every load case name exists in the model.

        Checks (planned — not yet implemented):
            4. Model identity / hash verification.
            5. Extreme-value plausibility.
            6. Self-weight equilibrium.
        """
        report = ValidationReport()

        # Collect the model's known IDs and load cases once.
        model_element_ids = self._get_model_element_ids()
        model_node_ids = self._get_model_node_ids()
        model_lc_names = self._get_model_load_case_names()

        # --- Check element IDs ---
        if request.element_ids:
            missing = request.element_ids - model_element_ids
            if missing:
                report.add(
                    Severity.ERROR,
                    "element_ids",
                    f"{len(missing)} element(s) not found in model: "
                    f"{sorted(missing)}",
                )
            else:
                logger.info(
                    "Validated %d element IDs — all present.",
                    len(request.element_ids),
                )

        # --- Check node IDs ---
        if request.node_ids:
            missing = request.node_ids - model_node_ids
            if missing:
                report.add(
                    Severity.ERROR,
                    "node_ids",
                    f"{len(missing)} node(s) not found in model: "
                    f"{sorted(missing)}",
                )
            else:
                logger.info(
                    "Validated %d node IDs — all present.",
                    len(request.node_ids),
                )

        # --- Check load case names ---
        all_requested_lcs = request.all_load_cases()
        if all_requested_lcs:
            missing = all_requested_lcs - model_lc_names
            if missing:
                report.add(
                    Severity.ERROR,
                    "load_cases",
                    f"{len(missing)} load case(s) not found in model: "
                    f"{sorted(missing)}. "
                    f"Available: {sorted(model_lc_names)}",
                )
            else:
                logger.info(
                    "Validated %d load case names — all present.",
                    len(all_requested_lcs),
                )

        # --- Empty request warning ---
        if request.is_empty():
            report.add(
                Severity.WARNING,
                "empty_request",
                "The merged DataRequest is empty — nothing to fetch.",
            )

        report.log_summary()
        return report

    # ─────────────────────────────────────────────────────────────────
    # Model introspection helpers
    # ─────────────────────────────────────────────────────────────────

    def _get_model_element_ids(self) -> Set[int]:
        """Extract the set of element IDs known to the model.

        Works for both CSI (via ``_id_mapper``) and Midas (same attr).
        """
        mapper = getattr(self._importer, "_id_mapper", None)
        if mapper is not None and hasattr(mapper, "element_ids"):
            return set(mapper.element_ids)
        logger.warning(
            "Cannot introspect element IDs — importer has no _id_mapper. "
            "Skipping element validation."
        )
        return set()

    def _get_model_node_ids(self) -> Set[int]:
        """Extract the set of node IDs known to the model."""
        mapper = getattr(self._importer, "_id_mapper", None)
        if mapper is not None and hasattr(mapper, "node_ids"):
            return set(mapper.node_ids)
        logger.warning(
            "Cannot introspect node IDs — importer has no _id_mapper. "
            "Skipping node validation."
        )
        return set()

    def _get_model_load_case_names(self) -> Set[str]:
        """Extract the set of load case names known to the model."""
        try:
            available = self._importer.available_load_cases()
            return {lc.name for lc in available}
        except Exception as exc:
            logger.warning(
                "Cannot introspect load cases: %s. Skipping LC validation.",
                exc,
            )
            return set()
