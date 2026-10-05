"""Plug-and-play Excel check module driven by a JSON spec.

``make_dynamic_module_class`` is the public entry point.  Given a
``JsonModuleSpec`` (parsed from ``run_spec.json``) it manufactures a proper
``IExcelCheckModule`` subclass with class-level ``SPEC_SI`` / ``SPEC_IMP``
attributes — exactly as if the module had been hand-coded in Python.

The generated class:
- Works with the existing ``data_requirements()`` classmethod machinery
  (load-case extraction, DataRequest merging).
- Supports ``make_spec(load_cases, scalar_inputs)`` for runtime spec
  construction with actual values.
- Is a drop-in replacement for any static ``IExcelCheckModule`` subclass in
  ``PTBoxGirderCoordination.EXCEL_MODULES``.

Template resolution
-------------------
Template paths in ``JsonModuleSpec`` are relative to the ``excel_templates/``
directory that lives directly under ``modules_post/``::

    modules_post/
        excel/
            dynamic_module.py   <- this file
        excel_templates/
            pt_box/
                Module 07 PT Box Flexure v5_SI_test.xlsx

``template_si = "pt_box/Module 07 PT Box Flexure v5_SI_test.xlsx"`` is resolved
to an absolute path using ``_TEMPLATES_BASE`` defined at module level.

Usage
-----
::

    from bda.modules_post.excel.dynamic_module import make_dynamic_module_class
    from bda.modules_post.excel.json_module_spec import JsonModuleSpec

    spec = context.module_spec_for("module_07")          # JsonModuleSpec
    ModuleCls = make_dynamic_module_class(spec)
    instance  = ModuleCls()
    result    = instance.execute(view, run_folder=folder, component_id="Girder_1",
                                 load_cases={"force": "ULS"},
                                 scalar_inputs={"fpu": 1861.58, ...})
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Type

from bda.modules_post.excel.base import IExcelCheckModule
from bda.modules_post.excel.json_module_spec import JsonModuleSpec
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
from bda.domain.results.result_set import ResultSetView
from bda.modules_post.excel.run_folder import RunFolder

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default templates base directory — relative to this file's location.
# modules_post/excel/dynamic_module.py  ->  ../  ->  modules_post/
# ---------------------------------------------------------------------------
_TEMPLATES_BASE: Path = (Path(__file__).parent.parent / "excel_templates").resolve()


# ---------------------------------------------------------------------------
# Internal spec builder
# ---------------------------------------------------------------------------

def _build_excel_check_spec(
    json_spec: JsonModuleSpec,
    templates_base: Path,
    unit_system: UnitSystemSpec,
    load_cases: Dict[str, Any],
    scalar_input_values: Dict[str, Any],
) -> ExcelCheckSpec:
    """Convert a ``JsonModuleSpec`` + runtime values into an ``ExcelCheckSpec``.

    Args:
        json_spec:            Parsed JSON spec (template paths, cell mappings).
        templates_base:       Absolute path to the ``excel_templates/`` directory.
        unit_system:          ``SI`` or ``IMP`` — selects template variant.
        load_cases:           Module-level load case dict (e.g. ``{"force": "ULS"}``).
        scalar_input_values:  Resolved scalar values keyed by ``JsonScalarInputSpec.key``
                              (after ``$ref`` resolution and ``h_max`` computation).
                              Keys with ``None`` values are skipped — this allows
                              the placeholder specs built at class-definition time
                              (with empty scalar_input_values) to pass validation.
    """
    template_rel = (
        json_spec.template_si if unit_system == UnitSystemSpec.SI
        else json_spec.template_imp
    )
    template_path = (templates_base / template_rel).resolve()

    # ── Scalar inputs ─────────────────────────────────────────────────────────
    inputs: List[InputMapping] = []
    for si in json_spec.scalar_inputs:
        raw_value = scalar_input_values.get(si.key)
        # Skip inputs with no resolved value — this occurs when building the
        # default SPEC_SI/SPEC_IMP placeholders (empty scalar_input_values={}).
        # The placeholder specs are only used for load-case/column discovery;
        # actual execution always goes through make_spec() with real values.
        if raw_value is None:
            continue
        # Convert to float if numeric; keep as string for metadata fields.
        if isinstance(raw_value, (int, float)):
            value: Any = float(raw_value)
        else:
            value = str(raw_value)
        inputs.append(
            InputMapping(
                cell=si.cell,
                source="constant",
                constant=value,
                unit=si.unit,   # may be pint str, cell addr, or relative ref
            )
        )

    # ── Per-node table column inputs ───────────────────────────────────────────
    table_column_inputs: List[TableColumnInputMapping] = []
    for col in json_spec.table_columns:
        if col.source == "result":
            load_case = load_cases.get(col.load_case_key, "")
        else:
            load_case = ""
        table_column_inputs.append(
            TableColumnInputMapping(
                start_cell=col.start_cell,
                component=col.component,
                load_case=load_case,
                unit=col.unit,
            )
        )

    # ── Scalar outputs ─────────────────────────────────────────────────────────
    outputs: List[OutputMapping] = [
        OutputMapping(cell=o.cell, name=o.name, unit=o.unit)
        for o in json_spec.outputs
    ]

    # ── Table outputs ──────────────────────────────────────────────────────────
    table_outputs: List[TableOutputMapping] = [
        TableOutputMapping(cell=t.cell, name=t.name, columns=t.columns)
        for t in json_spec.table_outputs
    ]

    file_spec = ExcelFileSpec(
        template_path=template_path,
        worksheet=json_spec.worksheet,
        inputs=inputs,
        table_column_inputs=table_column_inputs,
        outputs=outputs,
        table_outputs=table_outputs,
        run_order=0,
    )

    return ExcelCheckSpec(
        name=json_spec.module_id,
        files=[file_spec],
        unit_system=unit_system,
    )


# ---------------------------------------------------------------------------
# Base class for all dynamically generated modules
# ---------------------------------------------------------------------------

class DynamicExcelModule(IExcelCheckModule):
    """Base class for JSON-spec-driven Excel check modules.

    Do not instantiate directly.  Use ``make_dynamic_module_class()`` to
    obtain a concrete subclass with ``_JSON_SPEC`` and ``_TEMPLATES_BASE``
    baked in as class attributes.
    """

    MODULE_KEY:       ClassVar[str]  = ""
    INPUTS_SPEC_KEY:  ClassVar[str]  = ""
    _JSON_SPEC:       ClassVar[JsonModuleSpec]
    _TEMPLATES_BASE:  ClassVar[Path]

    @classmethod
    def make_spec(
        cls,
        load_cases: Optional[Dict[str, Any]] = None,
        scalar_inputs: Optional[Dict[str, Any]] = None,
    ) -> tuple:
        """Build SI and IMP specs from runtime load cases and scalar values.

        Mirrors the ``make_spec`` classmethod on hand-coded module classes
        (e.g. ``GirderFlexureCheck``), so the coordinator's
        ``data_requirements(load_cases)`` path works unchanged.
        """
        lcs = load_cases or {}
        si  = scalar_inputs or {}
        return (
            _build_excel_check_spec(
                cls._JSON_SPEC, cls._TEMPLATES_BASE,
                UnitSystemSpec.SI, lcs, si,
            ),
            _build_excel_check_spec(
                cls._JSON_SPEC, cls._TEMPLATES_BASE,
                UnitSystemSpec.IMP, lcs, si,
            ),
        )

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

        Builds the appropriate ``ExcelCheckSpec`` (SI or IMP) from the JSON
        spec + runtime values, then delegates to ``_run_excel_file`` exactly as
        hand-coded modules do.
        """
        effective_system = self._resolve_unit_system(view, unit_system)
        lcs = load_cases or {}
        si  = scalar_inputs or {}

        spec_si, spec_imp = type(self).make_spec(lcs, si)
        spec = spec_si if effective_system == UnitSystemSpec.SI else spec_imp

        all_scalars:  Dict[str, Any] = {}
        all_tables:   Dict[str, List[Dict[str, Any]]] = {}
        all_pdfs:     List[Path] = []
        all_versions: Dict[str, str] = {}
        errors:       List[str] = []
        outputs_so_far: Dict[str, Any] = {}

        for file_spec in sorted(spec.files, key=lambda f: f.run_order):
            try:
                scalars, tables, pdfs, versions = self._run_excel_file(
                    file_spec, view, run_folder, outputs_so_far,
                    pre_computed=pre_computed,
                )
                all_scalars.update(scalars)
                all_tables.update(tables)
                all_pdfs.extend(pdfs)
                all_versions.update(versions)
                outputs_so_far.update(scalars)
            except Exception as exc:
                import traceback
                errors.append(f"{file_spec.template_path.name}: {exc}")
                errors.append(traceback.format_exc())

        return CheckResult(
            check_name=spec.name,
            component_id=component_id,
            outputs=all_scalars,
            table_outputs=all_tables,
            pdf_paths=all_pdfs,
            template_versions=all_versions,
            errors=errors,
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def make_dynamic_module_class(
    json_spec: JsonModuleSpec,
    templates_base: Path = _TEMPLATES_BASE,
) -> Type[DynamicExcelModule]:
    """Create a concrete ``DynamicExcelModule`` subclass from *json_spec*.

    The generated class has:
    - ``MODULE_KEY``      -> ``json_spec.module_id``  (used in load-case lookup)
    - ``INPUTS_SPEC_KEY`` -> ``json_spec.run_spec_key``  (used in scalar-input /
                           section-data lookup inside the coordinator)
    - ``SPEC_SI``  / ``SPEC_IMP`` -> built with empty load cases + empty scalar
                   values (correct defaults; ``make_spec`` is used at runtime).
                   Scalar inputs with no resolved value are skipped so the
                   placeholder specs pass InputMapping validation.
    - ``_JSON_SPEC`` / ``_TEMPLATES_BASE`` -> captured for ``make_spec``

    The class is a proper Python class (not a lambda or closure), so it behaves
    correctly with ``isinstance``, ``issubclass``, and ``__name__``.

    Args:
        json_spec:      Parsed JSON spec, typically returned by
                        ``JSONContext.module_spec_for(key)``.
        templates_base: Absolute path to ``excel_templates/`` directory.
                        Defaults to the directory relative to this file.

    Returns:
        A ``Type[DynamicExcelModule]`` that can be used anywhere a static
        ``IExcelCheckModule`` subclass is expected.
    """
    _default_spec_si = _build_excel_check_spec(
        json_spec, templates_base, UnitSystemSpec.SI, {}, {}
    )
    _default_spec_imp = _build_excel_check_spec(
        json_spec, templates_base, UnitSystemSpec.IMP, {}, {}
    )

    # Build a new class with all required class-level attributes set.
    # Defining it as a nested class (rather than via type()) gives clearer
    # tracebacks and correct __qualname__ for logging.
    class _Generated(DynamicExcelModule):
        MODULE_KEY      = json_spec.module_id
        INPUTS_SPEC_KEY = json_spec.run_spec_key
        SPEC_SI         = _default_spec_si
        SPEC_IMP        = _default_spec_imp
        _JSON_SPEC      = json_spec
        _TEMPLATES_BASE = templates_base

    _Generated.__name__     = f"Dynamic_{json_spec.module_id}"
    _Generated.__qualname__ = f"Dynamic_{json_spec.module_id}"

    logger.debug(
        "make_dynamic_module_class: created %s (INPUTS_SPEC_KEY=%r, "
        "template_si=%r)",
        _Generated.__name__,
        json_spec.run_spec_key,
        json_spec.template_si,
    )
    return _Generated
