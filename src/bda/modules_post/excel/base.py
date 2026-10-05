"""IExcelCheckModule — base class for individual Excel-backed check modules.

Design
------
- No auto-registration. The owning ``IModulePost`` subclass declares its
  ``EXCEL_MODULES`` tuple explicitly. This makes dependencies visible and
  eliminates the import-order surprises of auto-registration.
- ``data_requirements()`` is a classmethod (no instance or group arg).
  It parses result_path strings from ``SPEC_SI`` and ``SPEC_IMP`` and
  returns a ``DataRequest``. The CoordinationModule merges all of these
  before calling the importer.
- ``execute()`` receives a ``ResultSetView`` scoped to one structural group,
  the ``RunFolder`` for this check domain, and a ``component_id`` string.
  It returns a ``CheckResult``.

Lifecycle (per structural group)
---------------------------------
::

    for module_cls in coordination_module.EXCEL_MODULES:
        mod = module_cls()
        result = mod.execute(view, run_folder=grp_folder, component_id=group.id)
"""
from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple

import xlwings as xw

from bda.domain.results.result_set import ResultSetView
from bda.domain.results.data_request import DataRequest
from bda.infrastructure.utils.units import Q_
from bda.modules_post.excel.models import (
    CheckResult,
    ExcelCheckSpec,
    ExcelFileSpec,
    InputMapping,
    OutputMapping,
    TableColumnInputMapping,
    TableOutputMapping,
    UnitSystemSpec,
)
from bda.modules_post.excel.result_path import resolve
from bda.modules_post.excel.run_folder import RunFolder

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Patterns for unit-reference detection (see _resolve_unit_ref).
_CELL_ADDR_RE    = re.compile(r'^[A-Za-z]{1,3}\d+$')
_RELATIVE_REF_RE = re.compile(r'^(right|left|above|below)_(\d+)$', re.IGNORECASE)


def _resolve_unit_ref(
    ws: "xw.Sheet",
    cell_addr: str,
    unit_spec: Optional[str],
) -> Optional[str]:
    """Resolve a unit specification that may reference a cell in the workbook.

    Three forms are accepted:

    - **Pint string** (default): ``"MPa"``, ``"kN*m"`` — returned unchanged.
    - **Absolute cell reference**: ``"C1"``, ``"B20"`` — the unit label is
      read from that cell in *ws* at call time.
    - **Relative reference**: ``"right_1"``, ``"left_2"``, ``"above_1"``,
      ``"below_1"`` — the unit label is read from a cell offset relative to
      *cell_addr* (the cell being written).

    ``None`` is returned unchanged.

    Args:
        ws:        The active xlwings worksheet (already open).
        cell_addr: A1 address of the cell being written (anchor for relative refs).
        unit_spec: Raw unit specification from the spec.

    Returns:
        Resolved unit string suitable for pint, or ``None``.
    """
    if unit_spec is None:
        return None

    # Absolute cell address — read label from that cell.
    if _CELL_ADDR_RE.match(unit_spec):
        try:
            val = ws.range(unit_spec).value
            return str(val).strip() if val is not None else None
        except Exception:
            logger.debug(
                "_resolve_unit_ref: could not read unit from cell %r — "
                "treating as pint string.", unit_spec
            )
            return unit_spec

    # Relative reference — read label from offset cell.
    m = _RELATIVE_REF_RE.match(unit_spec)
    if m:
        direction = m.group(1).lower()
        n = int(m.group(2))
        offsets = {
            "right": (0,  n),
            "left":  (0, -n),
            "above": (-n, 0),
            "below": ( n, 0),
        }
        row_off, col_off = offsets[direction]
        try:
            val = ws.range(cell_addr).offset(row_off, col_off).value
            return str(val).strip() if val is not None else None
        except Exception:
            logger.debug(
                "_resolve_unit_ref: could not read unit from %r offset "
                "(%d, %d) — treating as None.", cell_addr, row_off, col_off
            )
            return None

    # Plain pint unit string — return unchanged.
    return unit_spec


def _read_named_range(wb: "xw.Book", ws: "xw.Sheet", name: str) -> Any:
    """Read a named range or cell address from an open xlwings workbook.

    Prefer ``wb.names[name].refers_to_range`` over ``ws.range(name)`` because:

    - Named ranges often point to the "Calculation" or "Outputs" sheet, not
      "Inputs". Calling ``ws.range(name)`` from the wrong sheet raises a COM
      error even for workbook-scoped names in some Excel/xlwings versions.
    - Formula-based dynamic ranges (OFFSET/INDEX) have no static cell address
      and can only be resolved via ``refers_to_range``, which asks Excel to
      evaluate the formula at the time of the call.

    Falls back to ``ws.range(name)`` for plain cell addresses (e.g. ``"B5"``)
    that are not in the workbook's name manager.
    """
    try:
        return wb.names[name].refers_to_range.value
    except Exception:
        # Not a named range — treat as a direct cell address on the current sheet.
        return ws.range(name).value


class IExcelCheckModule(ABC):
    """Abstract base for all Excel-backed check modules.

    Subclasses must declare:
    - ``SPEC_SI``  — ``ExcelCheckSpec`` for SI unit system
    - ``SPEC_IMP`` — ``ExcelCheckSpec`` for Imperial unit system

    Both specs encode the complete Excel I/O mapping (named ranges,
    template path, worksheet name) as class-level constants.
    """

    SPEC_SI:  ClassVar[ExcelCheckSpec]
    SPEC_IMP: ClassVar[ExcelCheckSpec]

    # ── Data requirements ─────────────────────────────────────────────────────

    @classmethod
    def data_requirements(cls, load_cases: Optional[Dict[str, Any]] = None) -> DataRequest:
        """Parse result_path strings from both specs and return a ``DataRequest``.

        Called once per module class (not per group) by the CoordinationModule.
        The CoordinationModule merges all module data requirements and issues a
        single importer fetch for the whole check domain.

        Args:
            load_cases: Optional dict of load case names sourced from the run-spec
                        (e.g. ``{"force": "ULS"}``). When provided and the subclass
                        implements ``make_spec()``, specs are built dynamically with
                        the supplied names instead of the hardcoded module defaults.

        Returns:
            Union of data needs from ``SPEC_SI`` and ``SPEC_IMP``.
        """
        if load_cases and hasattr(cls, "make_spec"):
            spec_si, spec_imp = cls.make_spec(load_cases)
        else:
            spec_si, spec_imp = cls.SPEC_SI, cls.SPEC_IMP
        si_req  = cls._data_requirements_for_spec(spec_si)
        imp_req = cls._data_requirements_for_spec(spec_imp)
        return si_req.merge(imp_req)

    # ── Execution ─────────────────────────────────────────────────────────────

    @abstractmethod
    def execute(
        self,
        view: ResultSetView,
        *,
        run_folder: RunFolder,
        component_id: str,
        unit_system: UnitSystemSpec = UnitSystemSpec.AUTO,
        pre_computed: Optional[Dict[str, Any]] = None,
        load_cases: Optional[Dict[str, Any]] = None,
        scalar_inputs: Optional[Dict[str, Any]] = None,
    ) -> CheckResult:
        """Run this check for one structural group.

        Args:
            view:         ``ResultSetView`` filtered to the group's element/node IDs.
            run_folder:   Per-module working directory (already scoped by the
                          CoordinationModule via ``run_folder.sub_folder(...)``).
            component_id: Human-readable group identifier (e.g. ``"Girder_1"``).
            unit_system:  Override AUTO resolution when needed.
            pre_computed: Per-node governing values prepared by the CoordinationModule.
                          Keys follow the convention ``f"node_{component}_{load_case}"``
                          (e.g. ``"node_Mz_ULS_gr5"``). Values are ``list[float]``
                          ordered to match ``StructuralGroup.node_ids``.
                          Consumed by ``TableColumnInputMapping`` entries.

        Returns:
            ``CheckResult`` with scalar outputs, table outputs, PDF paths,
            template versions, and any non-fatal errors.
        """
        ...

    # ── Helpers shared by subclasses ──────────────────────────────────────────────

    @classmethod
    def _resolve_unit_system(
        cls, view: ResultSetView, override: UnitSystemSpec
    ) -> UnitSystemSpec:
        """Return the effective unit system (resolve AUTO from ``ResultSet.source``)."""
        if override != UnitSystemSpec.AUTO:
            return override
        source = getattr(view.parent, "source", "")
        imp_tags = {"imp", "imperial", "us_customary"}
        if any(tag in source.lower() for tag in imp_tags):
            return UnitSystemSpec.IMP
        return UnitSystemSpec.SI

    @classmethod
    def _data_requirements_for_spec(cls, spec: ExcelCheckSpec) -> DataRequest:
        """Parse result_path strings in one spec into a ``DataRequest``."""
        element_ids: set = set()
        node_ids: set = set()
        force_lcs: set = set()
        disp_lcs: set = set()

        for file_spec in spec.files:
            for inp in file_spec.inputs:
                if inp.source != "result" or not inp.result_path:
                    continue
                path = inp.result_path

                # forces.element[id].end.lc.component
                m = re.match(r"^forces\.element\[(\d+)\]\.([IJ])\.(\w+)\.\w+$", path)
                if m:
                    element_ids.add(int(m.group(1)))
                    force_lcs.add(m.group(3))
                    continue

                # forces.governing.end.lc.component — all elements needed
                m = re.match(r"^forces\.governing\.([IJ])\.(\w+)\.\w+$", path)
                if m:
                    force_lcs.add(m.group(2))
                    continue

                # displacements.node[id].lc.component
                m = re.match(r"^displacements\.node\[(\d+)\]\.(\w+)\.\w+$", path)
                if m:
                    node_ids.add(int(m.group(1)))
                    disp_lcs.add(m.group(2))
                    continue

            for tc_inp in file_spec.table_column_inputs:
                if tc_inp.load_case:
                    force_lcs.add(tc_inp.load_case)

        return DataRequest(
            element_ids=frozenset(element_ids),
            node_ids=frozenset(node_ids),
            force_loadcases=frozenset(force_lcs),
            disp_loadcases=frozenset(disp_lcs),
        )

    @staticmethod
    def _run_excel_file(
        file_spec: ExcelFileSpec,
        view: ResultSetView,
        run_folder: RunFolder,
        outputs_so_far: Dict[str, Any],
        pre_computed: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]], List[Path], Dict[str, str]]:
        """Copy template -> inject inputs -> recalculate -> extract outputs."""
        template_path = file_spec.template_path
        if not template_path.is_absolute():
            raise ValueError(
                f"template_path must be absolute: {template_path!r}. "
                "Resolve it in the subclass before creating the ExcelFileSpec."
            )

        copied_path = run_folder.copy_template(template_path)
        pc = pre_computed or {}

        scalar_outputs: Dict[str, Any] = {}
        table_outputs: Dict[str, List[Dict[str, Any]]] = {}
        pdf_paths: List[Path] = []
        template_versions: Dict[str, str] = {}

        app = xw.App(visible=False, add_book=False)
        try:
            wb = app.books.open(copied_path)
            ws = wb.sheets[file_spec.worksheet]

            # ── inject scalar inputs (named range / cell address) ──────────────
            for inp in file_spec.inputs:
                if inp.source == "result":
                    qty = resolve(inp.result_path, view, outputs_so_far)
                    unit = _resolve_unit_ref(ws, inp.cell, inp.unit)
                    raw = qty.to(unit).magnitude if unit else qty.magnitude
                    rng = ws.range(inp.cell)
                    rng.value = raw
                    rng.color = (255, 165, 0)
                elif inp.source == "constant":
                    rng = ws.range(inp.cell)
                    rng.value = inp.constant
                    rng.color = (255, 165, 0)

            # ── inject per-node column inputs ──────────────────────────────
            for tc_inp in file_spec.table_column_inputs:
                key = f"node_{tc_inp.component}_{tc_inp.load_case}"
                values = pc.get(key)
                if not values:
                    logger.warning(
                        "_run_excel_file: no pre_computed data for key %r "
                        "(start_cell=%r). Column will be left as-is in template.",
                        key, tc_inp.start_cell,
                    )
                    continue
                n = len(values)
                col_rng = ws.range(tc_inp.start_cell).resize(n, 1)
                col_rng.value = [[v] for v in values]
                col_rng.color = (255, 165, 0)

            # ── recalculate ────────────────────────────────────────────────────────────
            wb.app.calculate()

            # ── read scalar outputs ────────────────────────────────────────────────────
            for out in file_spec.outputs:
                raw_val = _read_named_range(wb, ws, out.cell)
                if out.unit and raw_val is not None:
                    scalar_outputs[out.name] = Q_(float(raw_val), out.unit)
                else:
                    scalar_outputs[out.name] = raw_val

            # ── read table outputs ─────────────────────────────────────────────────────
            for tbl in file_spec.table_outputs:
                raw_data = _read_named_range(wb, ws, tbl.cell)
                if raw_data is None:
                    table_outputs[tbl.name] = []
                elif not isinstance(raw_data, list):
                    table_outputs[tbl.name] = [{col: raw_data for col in tbl.columns}]
                elif isinstance(raw_data[0], list):
                    rows = raw_data
                    table_outputs[tbl.name] = [
                        {col: val for col, val in zip(tbl.columns, row)}
                        for row in rows
                    ]
                else:
                    table_outputs[tbl.name] = [
                        {col: val for col, val in zip(tbl.columns, raw_data)}
                    ]

            # ── read TEMPLATE_VERSION ──────────────────────────────────────────────────────
            try:
                version = _read_named_range(wb, ws, "TEMPLATE_VERSION")
                template_versions[template_path.name] = (
                    str(version) if version is not None else "unknown"
                )
            except Exception:
                template_versions[file_spec.template_path.stem] = "unknown"

            # ── save workbook ──────────────────────────────────────────────────────────────
            # xlwings with visible=False does NOT save on close — explicit save required.
            wb.save()

        finally:
            try:
                wb.close()
            except Exception:
                pass
            app.quit()

        return scalar_outputs, table_outputs, pdf_paths, template_versions
