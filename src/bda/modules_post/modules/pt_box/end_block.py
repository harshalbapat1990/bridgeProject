"""EndBlockCheck — Module 12 PT Box anchorage zone / end block check via Excel.

Template
--------
``excel_templates/pt_box/Module12_End_Block v2_SI.xlsx``  (SI)
``excel_templates/pt_box/Module12_End_Block v2_IMP.xlsx`` (Imperial)

Inputs sheet — automation-written
----------------------------------
Module 12 has **no FEM-derived inputs**. All inputs are section geometry,
material properties, and reinforcement layout constants that are pre-filled
in the template (reflecting the bridge design rather than analysis results).

Examples of template-constant inputs (Inputs sheet column B):
  - Number of internal webs (``N.web``)
  - Section dimensions: ``H.ts``, ``H.bs``, ``H.o``, ``L.CL1``, ``L.CL2``, etc.
  - Strand layout: ``No.str``, ``A.ps``, ``N.TT``, ``N.BT``
  - Material strengths: ``fpu``, ``fy``, ``fci``
  - Reinforcement: stirrup size/count for bursting and spalling

The automation copies the template, recalculates it, and reads the
output named ranges. No cells are written.

Named range outputs (read after recalculation)
----------------------------------------------
``Pu``    — Factored anchorage force (total, all tendons) [kN]
``P.uh``  — Required horizontal bursting force [kN]
``P.uv``  — Required vertical bursting force [kN]
``P.uh_t``— Top-face horizontal bursting force component [kN]
``P.uh_b``— Bottom-face horizontal bursting force component [kN]
``P.uv_t``— Top-face vertical bursting force component [kN]
``P.uv_b``— Bottom-face vertical bursting force component [kN]
``N.B``   — Number of bursting stirrups provided
``N.S``   — Number of spalling bars provided
``fci``   — Concrete strength at release [MPa]
``fpu``   — Tendon tensile strength [MPa]
``fy``    — Reinforcing steel yield strength [MPa]

Notes
-----
- Future versions may inject ``Pu`` from FEM reaction results once that
  data path is established (currently it is computed within the template
  from strand count × jacking stress × area).
- The ``TEMPLATE_VERSION`` named range resolves to ``Inputs!$P$1``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from bda.modules_post.excel.base import IExcelCheckModule
from bda.modules_post.excel.models import (
    CheckResult,
    ExcelCheckSpec,
    ExcelFileSpec,
    OutputMapping,
    UnitSystemSpec,
)
from bda.modules_post.excel.run_folder import RunFolder
from bda.domain.results.result_set import ResultSetView

# ---------------------------------------------------------------------------
# Template paths
# ---------------------------------------------------------------------------
_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "excel_templates" / "pt_box"
_TEMPLATE_SI  = _TEMPLATES_DIR / "Module12_End_Block v2_SI.xlsx"
_TEMPLATE_IMP = _TEMPLATES_DIR / "Module12_End_Block v2_IMP.xlsx"


def _make_file_spec(template_path: Path) -> ExcelFileSpec:
    return ExcelFileSpec(
        template_path=template_path,
        worksheet="Inputs",
        # No FEM inputs — template is self-contained with design constants.
        inputs=[],
        table_column_inputs=[],
        # ── scalar outputs (named ranges, read after recalculation) ────────
        outputs=[
            OutputMapping(cell="Pu",    name="Pu_kN"),
            OutputMapping(cell="P.uh",  name="P_uh_kN"),
            OutputMapping(cell="P.uv",  name="P_uv_kN"),
            OutputMapping(cell="P.uh_t", name="P_uh_t_kN"),
            OutputMapping(cell="P.uh_b", name="P_uh_b_kN"),
            OutputMapping(cell="P.uv_t", name="P_uv_t_kN"),
            OutputMapping(cell="P.uv_b", name="P_uv_b_kN"),
            OutputMapping(cell="N.B",   name="N_bursting"),
            OutputMapping(cell="N.S",   name="N_spalling"),
            OutputMapping(cell="fci",   name="fci_MPa"),
            OutputMapping(cell="fpu",   name="fpu_MPa"),
            OutputMapping(cell="fy",    name="fy_MPa"),
        ],
        run_order=0,
    )


SPEC_SI = ExcelCheckSpec(
    name="EndBlockCheck",
    files=[_make_file_spec(_TEMPLATE_SI)],
    unit_system=UnitSystemSpec.SI,
)

SPEC_IMP = ExcelCheckSpec(
    name="EndBlockCheck",
    files=[_make_file_spec(_TEMPLATE_IMP)],
    unit_system=UnitSystemSpec.IMP,
)


class EndBlockCheck(IExcelCheckModule):
    """PT Box girder anchorage zone / end block check (Module 12).

    No FEM-derived inputs — the template is run as-is with design constants.
    Reads anchorage force, bursting/spalling demands, and material strengths
    after Excel recalculation.
    """

    MODULE_KEY = "end_block"
    SPEC_SI  = SPEC_SI
    SPEC_IMP = SPEC_IMP

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
        spec = self.SPEC_SI if effective_system == UnitSystemSpec.SI else self.SPEC_IMP

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
