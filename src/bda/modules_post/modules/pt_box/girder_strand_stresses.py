"""StrandStressesCheck — Module 11 PT Box strand stress check via Excel.

Template
--------
``excel_templates/pt_box/Module 11 Strand Stresses v3_SI.xlsx``  (SI)
``excel_templates/pt_box/Module 11 Strand Stresses v3_IMP.xlsx`` (Imperial)

Inputs sheet — automation-written
----------------------------------
Column M, rows 5 onward:
    Service-level bending moments at each node station [kN·m].
    These are total unfactored service moments (DC + DW + LL+IM) used to
    compute the stress increment in the bonded post-tensioning strands at
    the service limit state per AASHTO Table 5.9.2.2-1.

    The remaining input columns (distances in column C, strand CG heights
    in column J) and all scalar inputs (fpu, fpy, I, Eps, Ec, fpe values)
    are embedded as constants in the template and are not touched by
    the automation.

Named range outputs (read after recalculation)
----------------------------------------------
``Table_L``              — Node station locations [m]
``Table_f.pe.service.L`` — Service-level strand stress at each node [MPa]
``Table_f.pu.service.lim``— Allowable service-level strand stress limit [MPa]

Notes
-----
- The service load case name must match the FEM model label.
  Update ``_FORCE_LC_SERVICE`` when the project's service combination
  load case name is confirmed.
- Named ranges ``M.b``, ``M.ws``, ``M.LL`` point to Calculation sheet
  scalar cells and are read-only outputs, not automation inputs.
- At service limit state, strand stress = effective prestress + stress
  increment due to service loads; the template computes this internally.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from bda.modules_post.excel.base import IExcelCheckModule
from bda.modules_post.excel.models import (
    CheckResult,
    ExcelCheckSpec,
    ExcelFileSpec,
    TableColumnInputMapping,
    TableOutputMapping,
    UnitSystemSpec,
)
from bda.modules_post.excel.run_folder import RunFolder
from bda.domain.results.result_set import ResultSetView

# ---------------------------------------------------------------------------
# Default load case name
# ---------------------------------------------------------------------------
_FORCE_LC_SERVICE_DEFAULT = "SLS_Service"   # unfactored service combination (DC+DW+LL+IM)

# ---------------------------------------------------------------------------
# Template paths
# ---------------------------------------------------------------------------
_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "excel_templates" / "pt_box"
_TEMPLATE_SI  = _TEMPLATES_DIR / "Module 11 Strand Stresses v3_SI.xlsx"
_TEMPLATE_IMP = _TEMPLATES_DIR / "Module 11 Strand Stresses v3_IMP.xlsx"

# First data row in column M of the Inputs sheet (node station table).
_TABLE_START_ROW = 5


def _make_file_spec(template_path: Path, force_lc: str = _FORCE_LC_SERVICE_DEFAULT) -> ExcelFileSpec:
    return ExcelFileSpec(
        template_path=template_path,
        worksheet="Inputs",
        # ── per-node column injection ──────────────────────────────────────
        # Total service moment (DC+DW+LL+IM) at each node → column M
        table_column_inputs=[
            TableColumnInputMapping(
                start_cell=f"M{_TABLE_START_ROW}",
                component="Mz",
                load_case=force_lc,
                unit="kN*m",
            ),
        ],
        # ── table outputs (named ranges, read after recalculation) ─────────
        table_outputs=[
            TableOutputMapping(
                cell="Table_Location",
                name="Table_Location",
                columns=["Location_m"],
            ),
            TableOutputMapping(
                cell="Table_SLS",
                name="Table_SLS",
                columns=["f_pe_service_MPa"],
            ),
            TableOutputMapping(
                cell="Table_SLS_D_C",
                name="Table_SLS_D_C",
                columns=["f_pu_service_DC"],
            ),
        ],
        run_order=0,
    )


SPEC_SI = ExcelCheckSpec(
    name="StrandStressesCheck",
    files=[_make_file_spec(_TEMPLATE_SI)],
    unit_system=UnitSystemSpec.SI,
)

SPEC_IMP = ExcelCheckSpec(
    name="StrandStressesCheck",
    files=[_make_file_spec(_TEMPLATE_IMP)],
    unit_system=UnitSystemSpec.IMP,
)


class StrandStressesCheck(IExcelCheckModule):
    """PT Box girder strand stress check at service limit state (Module 11).

    Writes per-node total service moments into column M of the Inputs
    sheet and reads computed service stress vs. limit tables after
    Excel recalculates.
    """

    MODULE_KEY = "girder_strand_stresses"
    SPEC_SI  = SPEC_SI
    SPEC_IMP = SPEC_IMP

    @classmethod
    def make_spec(cls, load_cases: Dict[str, Any]) -> tuple:
        """Build SI and IMP specs from run-spec load case names."""
        lc = load_cases.get("force", _FORCE_LC_SERVICE_DEFAULT)
        return (
            ExcelCheckSpec(name="StrandStressesCheck", files=[_make_file_spec(_TEMPLATE_SI, lc)], unit_system=UnitSystemSpec.SI),
            ExcelCheckSpec(name="StrandStressesCheck", files=[_make_file_spec(_TEMPLATE_IMP, lc)], unit_system=UnitSystemSpec.IMP),
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
                    file_spec, view, run_folder, outputs_so_far,
                    pre_computed=pre_computed,
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
