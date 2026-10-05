"""Pydantic models for the JSON-driven (plug-and-play) module spec.

A ``JsonModuleSpec`` is embedded as a ``"spec"`` sub-object inside a module
block in ``run_spec.json`` (e.g. ``module_07.spec``).  It fully describes the
Excel I/O mapping for one check module — template files, worksheet, which cells
to write and read — without requiring a hand-coded Python subclass per module.

Unit specifications
-------------------
Every input and column entry carries an optional ``unit`` field.  Three forms
are accepted:

- **Pint string** (default): ``"MPa"``, ``"kN*m"``, ``"cm**2"`` — used directly
  for pint unit conversion when the value source is a ``ResultSet`` Quantity.
- **Absolute cell reference**: ``"C1"``, ``"B20"`` — the runner reads the unit
  label from that cell in the open workbook at execution time.  Useful when the
  template has a dedicated "Units" column.
- **Relative cell reference**: ``"right_1"``, ``"left_2"``, ``"above_1"``,
  ``"below_1"`` — reads the unit label from a cell offset relative to the input
  cell being written.  ``"right_1"`` means one column to the right; etc.

For ``source="constant"`` scalar inputs the unit is informational only (no
conversion takes place).  For ``source="result"`` inputs the resolved unit
string is passed to pint for magnitude extraction.

Example JSON
------------
::

    "module_07": {
        "spec": {
            "module_id": "girder_flexure",
            "template_si":  "pt_box/Module 07 PT Box Flexure v5_SI.xlsx",
            "template_imp": "pt_box/Module 07 PT Box Flexure v5_IMP.xlsx",
            "worksheet": "Inputs",
            "scalar_inputs": [
                {"cell": "B1", "key": "fpu", "unit": "MPa"},
                {"cell": "B12", "key": "project_name"}
            ],
            "table_columns": [
                {"start_cell": "A25", "component": "NODE_ID",  "source": "geometry"},
                {"start_cell": "C25", "component": "Mz",
                 "source": "result", "load_case_key": "force", "unit": "kN*m"},
                {"start_cell": "D25", "component": "Aps",
                 "source": "section", "unit": "cm**2"}
            ],
            "outputs": [
                {"cell": "RF_phi", "name": "RF_phi"}
            ],
            "table_outputs": [
                {"cell": "Table_DC", "name": "Table_DC", "columns": ["DC"]}
            ]
        },
        "scalar_inputs": { ... },
        "sections":      { ... }
    }
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class JsonScalarInputSpec(BaseModel):
    """One scalar input cell in a JSON-driven module spec.

    Maps a run-spec ``key`` (looked up from the resolved ``scalar_inputs`` dict
    at runtime) to an Excel ``cell`` (named range or A1 address).
    """

    cell: str
    """Target cell — named range (preferred) or A1 address (e.g. ``"B1"``)."""

    key: str
    """Key used to look up the value in the resolved scalar_inputs dict
    passed to ``execute()``.  Corresponds to a key in
    ``run_spec.module_XX.scalar_inputs`` after ``$ref`` resolution."""

    unit: Optional[str] = None
    """Unit specification.  Accepted forms:

    - ``None`` / omitted — no unit info; value written as-is.
    - Pint string: ``"MPa"``, ``"kN*m"`` — used for conversion when the value
      is a pint ``Quantity`` (``source='result'``).
    - Absolute cell address: ``"C3"`` — unit label read from that cell.
    - Relative reference: ``"right_1"`` — unit label read from 1 cell to
      the right of the current input cell (also ``left_N``, ``above_N``,
      ``below_N``).
    """


class JsonTableColumnSpec(BaseModel):
    """One per-node table column injected into the Excel template.

    At runtime the coordinator builds a list of values (one per node in the
    structural group) and writes them as a contiguous column starting at
    ``start_cell``.
    """

    start_cell: str
    """Top-left cell of the column (A1 address, e.g. ``"C25"``)."""

    component: str
    """Data component name.  Interpretation depends on ``source``:

    - ``geometry``: ``"NODE_ID"`` or ``"DISTANCE"``
    - ``result``:   force/moment component — ``"Mz"``, ``"Fy"``, etc.
    - ``section``:  section geometry key — ``"Aps"``, ``"bw"``, ``"dp"``, etc.
    """

    source: Literal["geometry", "result", "section"]
    """Where the per-node values come from:

    - ``"geometry"``  — computed from node coordinates (NODE_ID, DISTANCE).
    - ``"result"``    — FEM result component (uses ``load_case_key``).
    - ``"section"``   — cross-section geometry from ``run_spec.XX.sections``.
    """

    load_case_key: str = "force"
    """Key into the module's ``load_cases`` dict (e.g. ``"force"`` → ``"ULS"``).
    Only used when ``source="result"``; ignored otherwise."""

    unit: Optional[str] = None
    """Informational unit string for this column (documentation only;
    the coordinator always supplies values in canonical SI units)."""


class JsonOutputSpec(BaseModel):
    """One scalar output cell read after Excel recalculation."""

    cell: str
    """Named range or A1 address of the output cell."""

    name: str
    """Key used in ``CheckResult.outputs``."""

    unit: Optional[str] = None
    """Pint unit string of the raw value in the cell.  If set, the value is
    wrapped in a ``pint.Quantity``; otherwise stored as a raw float."""


class JsonTableOutputSpec(BaseModel):
    """One multi-row table range read after Excel recalculation."""

    cell: str
    """Named range covering the table body (no header row)."""

    name: str
    """Key used in ``CheckResult.table_outputs``."""

    columns: List[str] = Field(default_factory=list)
    """Column names in order, left to right."""


class JsonModuleSpec(BaseModel):
    """Complete JSON spec for one plug-and-play Excel check module.

    Embedded as ``module_XX.spec`` in ``run_spec.json``.  The ``run_spec_key``
    field is **not** present in the JSON — it is injected by
    ``JSONContext.module_spec_for()`` after parsing so the coordinator can
    trace back to the data block.
    """

    module_id: str
    """Short identifier matching the ``MODULE_KEY`` on the static Python class
    (e.g. ``"girder_flexure"``).  Used in ``module_load_cases`` lookup and as
    the generated class name."""

    run_spec_key: str = ""
    """The top-level run-spec key under which this spec lives (e.g.
    ``"module_07"``).  Set by ``JSONContext.module_spec_for()``; not in JSON."""

    template_si: str
    """Path to the SI template **relative to the ``excel_templates/`` directory**,
    including the bridge-type subfolder — e.g.
    ``"pt_box/Module 07 PT Box Flexure v5_SI.xlsx"``."""

    template_imp: str
    """Path to the Imperial template, same convention as ``template_si``."""

    worksheet: str
    """Name of the Excel worksheet where inputs are written and outputs read."""

    scalar_inputs: List[JsonScalarInputSpec] = Field(default_factory=list)
    """Ordered list of scalar input cells (written before recalculation)."""

    table_columns: List[JsonTableColumnSpec] = Field(default_factory=list)
    """Per-node column injections (one value per node, written as a contiguous
    column starting at ``start_cell``)."""

    outputs: List[JsonOutputSpec] = Field(default_factory=list)
    """Scalar output cells read after recalculation."""

    table_outputs: List[JsonTableOutputSpec] = Field(default_factory=list)
    """Multi-row table ranges read after recalculation."""
