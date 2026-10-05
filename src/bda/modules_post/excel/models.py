"""Pydantic models for the declarative Excel check specification.

These models describe, at the class level, what a check module does:
which Excel file to open, which named ranges to write (inputs) and read
(outputs), and in which unit system to operate. Concrete ``IExcelCheckModule``
subclasses declare their specs as class variables ``SPEC_SI`` and ``SPEC_IMP``.

Input sources
-------------
There are two allowed input sources:

- ``"result"``   — resolved from ``ResultSetView`` via a dotted result_path
                   string (e.g. ``"forces.governing.J.ULS_gr5.My_max"``).
- ``"constant"`` — a literal float value declared directly in this spec.
                   Use when a module needs a fixed parameter that is the
                   same for every run (e.g. a code-defined threshold).

Constants that may vary per project (e.g. material strength ``fpc``) should
be embedded directly in the Excel template, not injected as inputs. This
keeps the spec self-contained and auditable.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class InputMapping(BaseModel):
    """One input cell written by the runner before Excel recalculation."""

    cell: str
    """Named range in the Excel template, e.g. ``'My_max'``.
    Cell addresses (e.g. ``'B12'``) are forbidden — only named ranges."""

    source: Literal["result", "constant"] = "result"
    """
    ``'result'``   — value resolved from ``ResultSetView`` via ``result_path``.
    ``'constant'`` — literal ``constant`` value injected directly.
    """

    result_path: Optional[str] = None
    """Dotted result-path string (required when ``source='result'``).

    Supported patterns::

        forces.element[{id}].{I|J}.{lc}.{axis}_{max|min}
        forces.governing.{I|J}.{lc}.{axis}_{max|min}
        displacements.node[{id}].{lc}.{axis}_{max|min}
        previous_outputs.{name}
    """

    constant: Optional[Any] = None
    """Literal value to inject (required when ``source='constant'``).
    Usually a float, but may be a string for metadata fields (project name,
    initials, dates) or an int (revision number)."""

    unit: Optional[str] = None
    """pint unit string of the value *before* injection into Excel.
    If set, the resolved quantity is converted to this unit and its
    magnitude is written to the cell (e.g. ``'kN*m'``, ``'MPa'``).
    If ``None``, the raw magnitude is written unchanged."""

    @model_validator(mode="after")
    def _validate_source_fields(self) -> "InputMapping":
        if self.source == "result" and not self.result_path:
            raise ValueError(
                f"InputMapping(cell={self.cell!r}): "
                "result_path is required when source='result'."
            )
        if self.source == "constant" and self.constant is None:
            raise ValueError(
                f"InputMapping(cell={self.cell!r}): "
                "constant is required when source='constant'."
            )
        return self


class OutputMapping(BaseModel):
    """One scalar output cell read by the runner after Excel recalculation."""

    cell: str
    """Named range in the Excel template."""

    name: str
    """Key used in ``CheckResult.outputs``, e.g. ``'DC_stress_top_max'``."""

    unit: Optional[str] = None
    """pint unit string that the extracted raw float represents.
    If set, the raw value is wrapped in a ``pint.Quantity``.
    If ``None``, the raw float is stored as-is."""


class TableOutputMapping(BaseModel):
    """One multi-row table range read by the runner after Excel recalculation.

    The named range covers the body rows (no header). Each row becomes a
    ``dict`` keyed by ``columns``. Stored in ``CheckResult.table_outputs``.

    Example::

        TableOutputMapping(
            cell="results_table",
            name="results",
            columns=["Node", "Nu_kN", "Mu_kNm", "DCR"],
        )
    """

    cell: str
    """Named range covering the table body (no header row)."""

    name: str
    """Key used in ``CheckResult.table_outputs``."""

    columns: List[str]
    """Column names in order, matching left-to-right columns of the range."""


class TableColumnInputMapping(BaseModel):
    """Write an ordered list of per-node governing values into a column range.

    The CoordinationModule pre-computes governing force/moment values at each
    node in the structural group (taking the max absolute value from the
    neighboring element I/J ends) and stores them in a ``pre_computed`` dict.
    This mapping writes that list into the template's Inputs sheet as a
    contiguous column, starting at ``start_cell`` and extending downward for
    as many rows as there are nodes.

    Key convention in ``pre_computed``::

        f"node_{component}_{load_case}"   e.g. "node_Mz_ULS_gr5"

    Example::

        TableColumnInputMapping(
            start_cell="C25",
            component="Mz",
            load_case="ULS_gr5",
            unit="kN*m",
        )
    """

    start_cell: str
    """Top-left cell of the column to write (e.g. ``"C25"``)."""

    component: str
    """Force/moment component name matching ``ElementForceEnvelope`` fields
    (``Fx``, ``Fy``, ``Fz``, ``Mx``, ``My``, ``Mz``) **or** a geometry key
    such as ``"NODE_ID"``, ``"DISTANCE"``, ``"Aps"``, ``"bw"``, ``"dp"``,
    ``"bot_As"``, ``"bot_ds"``, ``"bot_hf"``, ``"top_As"``, ``"top_ds"``,
    ``"top_hf"``, ``"top_b"`` for non-FEM per-node columns.
    """

    load_case: str = ""
    """Load case name as it appears in the importer (e.g. ``"ULS_gr5"``).
    Leave empty (default) for geometry/static columns that are not sourced
    from FEM results."""

    unit: Optional[str] = None
    """Expected unit string (for documentation only; the CoordinationModule
    always supplies values already in canonical SI — kN, m, kN·m)."""


class ExcelFileSpec(BaseModel):
    """One Excel file processed within a single check module execution."""

    template_path: Path
    """Absolute path to the Excel template file.
    Resolved at class definition time in the module subclass."""

    worksheet: str
    """Sheet name where inputs are written and outputs are read."""

    inputs: List[InputMapping] = Field(default_factory=list)
    table_column_inputs: List[TableColumnInputMapping] = Field(default_factory=list)
    """Per-node column writes (one value per node, written as a contiguous
    column into the Inputs sheet). Populated by the CoordinationModule via
    the ``pre_computed`` dict passed to ``execute()``."""
    outputs: List[OutputMapping] = Field(default_factory=list)
    table_outputs: List[TableOutputMapping] = Field(default_factory=list)

    run_order: int = 0
    """Files with lower ``run_order`` are processed first.
    Enables multi-file chaining where file 2 reads outputs from file 1
    via ``previous_outputs.*`` result paths."""


class ExcelCheckSpec(BaseModel):
    """Complete declarative description of one check module's Excel execution.

    One spec per unit system (SI or IMP). Each ``IExcelCheckModule`` subclass
    declares ``SPEC_SI`` and ``SPEC_IMP`` as class variables.
    """

    name: str
    """Short check name, e.g. ``'GirderFlexureCheck'``. Used in reports."""

    files: List[ExcelFileSpec]
    """Ordered list of Excel files to process. Usually one, sometimes two
    for chained checks (e.g. section properties → stress check)."""

    unit_system: "UnitSystemSpec"
    """Identifies which unit system this spec targets."""


class CheckResult(BaseModel):
    """Result of one (check module, structural group) execution pair."""

    check_name: str
    """Name of the check, e.g. ``'GirderFlexureCheck'``."""

    component_id: str
    """Structural group ID this result belongs to, e.g. ``'Girder_1'``."""

    outputs: Dict[str, Any] = Field(default_factory=dict)
    """Scalar outputs keyed by ``OutputMapping.name``.
    Values are ``pint.Quantity`` when the mapping declares a ``unit``,
    otherwise raw floats."""

    table_outputs: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    """Table outputs keyed by ``TableOutputMapping.name``.
    Each value is a list of row dicts (one dict per row, keyed by column name)."""

    pdf_paths: List[Path] = Field(default_factory=list)
    """Paths to PDF printouts produced during this run (if any)."""

    template_versions: Dict[str, str] = Field(default_factory=dict)
    """Excel filename → ``TEMPLATE_VERSION`` named-range value.
    Used for provenance tracking in reports."""

    errors: List[str] = Field(default_factory=list)
    """Non-fatal errors or warnings captured during execution.
    A non-empty list means the check ran but flagged a problem."""

    @property
    def passed(self) -> bool:
        """``True`` if no errors were recorded."""
        return not self.errors


# ---------------------------------------------------------------------------
# Lightweight unit-system enum (avoids importing the domain enum here)
# ---------------------------------------------------------------------------

import enum


class UnitSystemSpec(str, enum.Enum):
    """Unit system declaration for ``ExcelCheckSpec``."""
    SI  = "SI"
    IMP = "IMP"
    AUTO = "AUTO"   # resolved from ``ResultSet.source`` at runtime
