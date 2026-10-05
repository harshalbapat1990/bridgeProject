"""ConcreteTemporaryStressesCheck — Module 09 PT Box temporary stress check via Excel.

Template
--------
``excel_templates/pt_box/Module 09 Concrete Temporary Stresses v3_SI.xlsx``  (SI)
``excel_templates/pt_box/Module 09 Concrete Temporary Stresses v3_IMP.xlsx`` (Imperial)

Inputs sheet — automation-written
----------------------------------
Column F, rows 5 onward:
    Stage 1 unfactored bending moments ``Mstage_I`` at each node station [kN·m].
    Corresponds to moments after Stage 1 of post-tensioning sequence.

Column G, rows 5 onward:
    Stage 2 unfactored bending moments ``Mstage_II`` at each node station [kN·m].
    Corresponds to moments after the full post-tensioning sequence is applied.

Columns H/I (Stage 1/2 effective prestress Pe) and column J (strand CG)
are **not** written by automation — they remain as template constants until
a reliable source for these values is established (TBD per project configuration).

Named range outputs (read after recalculation)
----------------------------------------------
``Table_Location_stage_1`` — Node stations for Stage 1 check [m]
``Table_σ_c1_top``         — Stage 1 concrete compression stress, top fibre [MPa]
``Table_σ_c1_bot``         — Stage 1 concrete compression stress, bottom fibre [MPa]
``Table_σ_c1_lim``         — Stage 1 compression limit [MPa]

Notes
-----
- Stage 2 named ranges (``Table_σ_c2_*``) all resolve to ``#REF!`` in the current
  template version and are omitted from outputs; they will be added once the
  template is repaired.
- Load case names for construction stages must match the FEM model labels.
  Update ``_FORCE_LC_STAGE1`` and ``_FORCE_LC_STAGE2`` when the project's
  staged-construction load case names are known.
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
# Default load case names
# ---------------------------------------------------------------------------
_FORCE_LC_STAGE1_DEFAULT = "CS_Stage1"   # moments after Stage 1 PT stressing
_FORCE_LC_STAGE2_DEFAULT = "CS_Stage2"   # moments after Stage 2 PT stressing

# ---------------------------------------------------------------------------
# Template paths
# ---------------------------------------------------------------------------
_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "excel_templates" / "pt_box"
_TEMPLATE_SI  = _TEMPLATES_DIR / "Module 09 Concrete Temporary Stresses v3_SI.xlsx"
_TEMPLATE_IMP = _TEMPLATES_DIR / "Module 09 Concrete Temporary Stresses v3_IMP.xlsx"

# First data row in column F/G of the Inputs sheet (node station table).
_TABLE_START_ROW = 5


def _make_file_spec(
    template_path: Path,
    lc_stage1: str = _FORCE_LC_STAGE1_DEFAULT,
    lc_stage2: str = _FORCE_LC_STAGE2_DEFAULT,
) -> ExcelFileSpec:
    return ExcelFileSpec(
        template_path=template_path,
        worksheet="Inputs",
        # ── per-node column injection ──────────────────────────────────────
        # Stage 1 governing Mz at each node → column F
        # Stage 2 governing Mz at each node → column G
        table_column_inputs=[
            TableColumnInputMapping(
                start_cell=f"F{_TABLE_START_ROW}",
                component="Mz",
                load_case=lc_stage1,
                unit="kN*m",
            ),
            TableColumnInputMapping(
                start_cell=f"G{_TABLE_START_ROW}",
                component="Mz",
                load_case=lc_stage2,
                unit="kN*m",
            ),
        ],
        # ── table outputs (named ranges, read after recalculation) ─────────
        # Stage 2 outputs are #REF! in current template — not included yet.
        table_outputs=[
            TableOutputMapping(
                cell="Table_Location_stage_1",
                name="Table_Location_stage_1",
                columns=["Location_m"],
            ),
            TableOutputMapping(
                cell="Table_σ_c1_top",
                name="Table_sigma_c1_top",
                columns=["sigma_c1_top_MPa"],
            ),
            TableOutputMapping(
                cell="Table_σ_c1_bot",
                name="Table_sigma_c1_bot",
                columns=["sigma_c1_bot_MPa"],
            ),
            TableOutputMapping(
                cell="Table_σ_c1_lim",
                name="Table_sigma_c1_lim",
                columns=["sigma_c1_lim_MPa"],
            ),
        ],
        run_order=0,
    )


SPEC_SI = ExcelCheckSpec(
    name="ConcreteTemporaryStressesCheck",
    files=[_make_file_spec(_TEMPLATE_SI)],
    unit_system=UnitSystemSpec.SI,
)

SPEC_IMP = ExcelCheckSpec(
    name="ConcreteTemporaryStressesCheck",
    files=[_make_file_spec(_TEMPLATE_IMP)],
    unit_system=UnitSystemSpec.IMP,
)


class ConcreteTemporaryStressesCheck(IExcelCheckModule):
    """PT Box girder temporary concrete stress check (Modules 09).

    Writes per-node governing Mz for two construction stages into
    columns F and G of the Inputs sheet, then reads computed stress
    tables (Stage 1 only — Stage 2 named ranges are currently broken).
    """

    MODULE_KEY = "girder_temp_stresses"
    SPEC_SI  = SPEC_SI
    SPEC_IMP = SPEC_IMP

    @classmethod
    def make_spec(cls, load_cases: Dict[str, Any]) -> tuple:
        """Build SI and IMP specs from run-spec load case names."""
        lc1 = load_cases.get("force_stage1", _FORCE_LC_STAGE1_DEFAULT)
        lc2 = load_cases.get("force_stage2", _FORCE_LC_STAGE2_DEFAULT)
        return (
            ExcelCheckSpec(name="ConcreteTemporaryStressesCheck", files=[_make_file_spec(_TEMPLATE_SI, lc1, lc2)], unit_system=UnitSystemSpec.SI),
            ExcelCheckSpec(name="ConcreteTemporaryStressesCheck", files=[_make_file_spec(_TEMPLATE_IMP, lc1, lc2)], unit_system=UnitSystemSpec.IMP),
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
