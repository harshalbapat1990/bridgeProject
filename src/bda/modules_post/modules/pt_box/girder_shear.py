"""GirderShearCheck — PT Box girder shear check via Excel.

Template
--------
``excel_templates/pt_box/Module_GirderShear.xlsx``

Named ranges (inputs written before recalculation)
--------------------------------------------------
``Fy_max_ULS``   — Maximum vertical shear force, ULS governing              [kN]
``Fy_min_ULS``   — Minimum vertical shear force, ULS governing              [kN]

Named ranges (outputs read after recalculation)
-----------------------------------------------
``DC_shear_max``  — Peak shear D/C ratio (maximum side)
``DC_shear_min``  — Peak shear D/C ratio (minimum side)

Notes
-----
- Shear uses ``Fy`` from end ``I`` (I-end of each element, where shear
  is typically worst for a continuous girder). Adjust end and component
  once the actual Excel template logic is confirmed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from bda.modules_post.excel.base import IExcelCheckModule
from bda.modules_post.excel.models import (
    CheckResult,
    ExcelCheckSpec,
    ExcelFileSpec,
    InputMapping,
    OutputMapping,
    UnitSystemSpec,
)
from bda.modules_post.excel.run_folder import RunFolder
from bda.domain.results.result_set import ResultSetView

# ---------------------------------------------------------------------------
# Default load case name
# ---------------------------------------------------------------------------
_FORCE_LC_DEFAULT = "ULS"

# ---------------------------------------------------------------------------
# Template path
# ---------------------------------------------------------------------------
_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "excel_templates" / "pt_box"
_TEMPLATE_PATH = _TEMPLATES_DIR / "Module_GirderShear.xlsx"


def _make_file_spec(template_path: Path, force_lc: str = _FORCE_LC_DEFAULT) -> ExcelFileSpec:
    return ExcelFileSpec(
        template_path=template_path,
        worksheet="Inputs",
        inputs=[
            InputMapping(
                cell="Fy_max_ULS",
                source="result",
                result_path=f"forces.governing.I.{force_lc}.Fy_max",
                unit="kN",
            ),
            InputMapping(
                cell="Fy_min_ULS",
                source="result",
                result_path=f"forces.governing.I.{force_lc}.Fy_min",
                unit="kN",
            ),
        ],
        outputs=[
            OutputMapping(cell="DC_shear_max", name="DC_shear_max"),
            OutputMapping(cell="DC_shear_min", name="DC_shear_min"),
        ],
        run_order=0,
    )


SPEC_SI = ExcelCheckSpec(
    name="GirderShearCheck",
    files=[_make_file_spec(_TEMPLATE_PATH)],
    unit_system=UnitSystemSpec.SI,
)

SPEC_IMP = ExcelCheckSpec(
    name="GirderShearCheck",
    files=[_make_file_spec(_TEMPLATE_PATH)],
    unit_system=UnitSystemSpec.IMP,
)


class GirderShearCheck(IExcelCheckModule):
    """PT Box girder shear demand/capacity check.

    Reads governing shear forces from the ``ResultSetView``, injects them
    into the Excel template, and reads D/C ratios after recalculation.
    """

    MODULE_KEY = "girder_shear"
    SPEC_SI  = SPEC_SI
    SPEC_IMP = SPEC_IMP

    @classmethod
    def make_spec(cls, load_cases: Dict[str, Any]) -> tuple:
        """Build SI and IMP specs from run-spec load case names."""
        lc = load_cases.get("force", _FORCE_LC_DEFAULT)
        return (
            ExcelCheckSpec(name="GirderShearCheck", files=[_make_file_spec(_TEMPLATE_PATH, lc)], unit_system=UnitSystemSpec.SI),
            ExcelCheckSpec(name="GirderShearCheck", files=[_make_file_spec(_TEMPLATE_PATH, lc)], unit_system=UnitSystemSpec.IMP),
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
        effective_system = self._resolve_unit_system(view, unit_system)
        if load_cases:
            spec_si, spec_imp = self.make_spec(load_cases)
        else:
            spec_si, spec_imp = self.SPEC_SI, self.SPEC_IMP
        spec = spec_si if effective_system == UnitSystemSpec.SI else spec_imp

        all_scalars: Dict[str, Any] = {}
        all_tables: Dict[str, List[Dict[str, Any]]] = {}
        all_pdf_paths = []
        all_versions: Dict[str, str] = {}
        errors: List[str] = []
        outputs_so_far: Dict[str, Any] = {}

        for file_spec in sorted(spec.files, key=lambda f: f.run_order):
            try:
                scalars, tables, pdfs, versions = self._run_excel_file(
                    file_spec, view, run_folder, outputs_so_far
                )
                all_scalars.update(scalars)
                all_tables.update(tables)
                all_pdf_paths.extend(pdfs)
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
            pdf_paths=all_pdf_paths,
            template_versions=all_versions,
            errors=errors,
        )
