"""GirderFlexureCheck — PT Box girder flexure/moment capacity check via Excel.

Template
--------
``excel_templates/pt_box/Module 07 PT Box Flexure v5_SI.xlsx``   (SI)
``excel_templates/pt_box/Module 07 PT Box Flexure v5_IMP.xlsx``  (Imperial)

Inputs sheet — automation-written
----------------------------------
Scalar inputs written to column B, rows 1-19:
    B1  fpu          [MPa]   Specified tensile strength of prestressing steel
    B2  fpe          [MPa]   Effective prestress after losses
    B3  fpy          [MPa]   PT yield strength
    B4  f'c          [MPa]   Concrete compressive strength
    B5  fy           [MPa]   Rebar yield strength
    B6  Es           [MPa]   Rebar modulus of elasticity
    B7  Ep           [MPa]   PT steel modulus of elasticity
    B8  S            [m]     Girder spacing
    B9  SOH          [m]     Overhang width
    B10 h            [m]     Overall depth (minimum section depth across span)
    B11 girder_location       "Interior" or "Exterior"
    B12 project_name
    B13 project_number
    B14 section_letter
    B15 originator
    B16 origination_date
    B17 checker
    B18 checked_date
    B19 revision

Per-node table columns written from row 25 onward (Inputs sheet):
    A   NODE_ID      Node numbers (integer IDs in span order)
    B   DISTANCE     Cumulative chord distance from first node [m]
    C   Mu           Factored ULS bending moment [kN·m] (governing per node)
    D   Aps          Area of prestressing steel [cm²]
    E   bw           Web width [m] (from section definition)
    F   dp           Depth to tendon CG from top of section [m]
    G   bot_As       Bottom flange rebar area [mm²]
    H   bot_ds       Bottom flange rebar depth from top [m]
    I   bot_hf       Bottom flange thickness [m]
    J   (formula)    Bottom flange effective width — DO NOT OVERWRITE
    K   top_As       Top flange rebar area [mm²]
    L   top_ds       Top flange rebar depth from top [m]
    M   top_hf       Top flange thickness [m]
    N   top_b        Top flange effective width [m]

Named range outputs (read after recalculation)
----------------------------------------------
``Table_DC``                — Demand/Capacity ratio table
``Table_Location``          — Station locations
``Table_Mr_neg``            — Negative moment resistance table
``Table_Mr_pos``            — Positive moment resistance table
``Table_Mu``                — Moment demand table
``Resistance_M.n.Negative`` — Governing negative resistance scalar [kN·m]
``RF_phi``                  — Resistance factor

Notes
-----
- Scalar inputs are sourced from ``run_spec.json → module_07.scalar_inputs``.
  ``h`` is taken as the minimum section depth across all sections declared in
  ``module_07.sections`` so that the template's conservative constant-depth
  assumption is honoured.
- Per-node geometry columns (A, B, D-I, K-N) are populated by
  ``PTBoxGirderCoordination._prepare_node_data()``.
- Column J contains a formula derived from girder spacing S — never overwrite.
- ``Mz`` is the primary in-plane bending moment (sagging under gravity → positive
  ``Mz`` at mid-span per the BDA convention).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from bda.modules_post.excel.base import IExcelCheckModule
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
from bda.modules_post.excel.run_folder import RunFolder
from bda.domain.results.result_set import ResultSetView

# ---------------------------------------------------------------------------
# Default load case name (used when no run-spec override is present)
# ---------------------------------------------------------------------------
_FORCE_LC_DEFAULT = "ULS"

# ---------------------------------------------------------------------------
# Template paths (SI and IMP are separate files)
# ---------------------------------------------------------------------------
_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "excel_templates" / "pt_box"
_TEMPLATE_SI  = _TEMPLATES_DIR / "Module 07 PT Box Flexure v5_SI.xlsx"
_TEMPLATE_IMP = _TEMPLATES_DIR / "Module 07 PT Box Flexure v5_IMP.xlsx"

# First data row in column A of the Inputs sheet (node station table).
_TABLE_START_ROW = 25

# ---------------------------------------------------------------------------
# Default scalar input values (template's built-in values; overridden by
# run_spec module_07.scalar_inputs when provided)
# ---------------------------------------------------------------------------
_SCALAR_DEFAULTS: Dict[str, Any] = {
    "fpu":              1861.58,
    "fpe":              1606.48,
    "fpy":              1675.43,
    "fck":              34.47,
    "fy":               413.69,
    "Es":               199948.0,
    "Ep":               196501.0,
    "S":                2.4384,
    "SOH":              1.0668,
    "h":                2.54,
    "girder_location":  "Interior",
    "project_name":     "",
    "project_number":   "",
    "section_letter":   "",
    "originator":       "",
    "origination_date": "",
    "checker":          "",
    "checked_date":     "",
    "revision":         1,
}


def _build_scalar_input_mappings(scalar_inputs: Dict[str, Any]) -> List[InputMapping]:
    """Return ``InputMapping`` list for cells B1-B19 from *scalar_inputs*.

    Each entry uses ``source="constant"`` so that the runner writes the value
    directly into the specified cell.  Cell addresses (not named ranges) are
    used because the Inputs sheet scalars in Module 07 do not have individual
    named ranges.
    """
    merged = {**_SCALAR_DEFAULTS, **scalar_inputs}
    # Map run-spec keys to (cell_address, conversion_hint)
    cell_map: List[tuple] = [
        ("B1",  merged.get("fpu",              _SCALAR_DEFAULTS["fpu"])),
        ("B2",  merged.get("fpe",              _SCALAR_DEFAULTS["fpe"])),
        ("B3",  merged.get("fpy",              _SCALAR_DEFAULTS["fpy"])),
        ("B4",  merged.get("fck",              _SCALAR_DEFAULTS["fck"])),
        ("B5",  merged.get("fy",               _SCALAR_DEFAULTS["fy"])),
        ("B6",  merged.get("Es",               _SCALAR_DEFAULTS["Es"])),
        ("B7",  merged.get("Ep",               _SCALAR_DEFAULTS["Ep"])),
        ("B8",  merged.get("S",                _SCALAR_DEFAULTS["S"])),
        ("B9",  merged.get("SOH",              _SCALAR_DEFAULTS["SOH"])),
        ("B10", merged.get("h",                _SCALAR_DEFAULTS["h"])),
        ("B11", merged.get("girder_location",  _SCALAR_DEFAULTS["girder_location"])),
        ("B12", merged.get("project_name",     _SCALAR_DEFAULTS["project_name"])),
        ("B13", merged.get("project_number",   _SCALAR_DEFAULTS["project_number"])),
        ("B14", merged.get("section_letter",   _SCALAR_DEFAULTS["section_letter"])),
        ("B15", merged.get("originator",       _SCALAR_DEFAULTS["originator"])),
        ("B16", merged.get("origination_date", _SCALAR_DEFAULTS["origination_date"])),
        ("B17", merged.get("checker",          _SCALAR_DEFAULTS["checker"])),
        ("B18", merged.get("checked_date",     _SCALAR_DEFAULTS["checked_date"])),
        ("B19", merged.get("revision",         _SCALAR_DEFAULTS["revision"])),
    ]
    return [
        InputMapping(cell=cell, source="constant", constant=_to_float_or_str(val))
        for cell, val in cell_map
    ]


def _to_float_or_str(value: Any) -> Any:
    """Return *value* as a float if numeric, otherwise as a string.

    ``InputMapping.constant`` is typed as ``Optional[float]`` but xlwings
    happily writes strings via ``ws.range(cell).value = val``.  We keep the
    type wide here so string fields (girder_location, project metadata) pass
    through cleanly.
    """
    if isinstance(value, (int, float)):
        return float(value)
    return str(value) if value is not None else ""


def _make_file_spec(
    template_path: Path,
    force_lc: str = _FORCE_LC_DEFAULT,
    scalar_inputs: Optional[Dict[str, Any]] = None,
) -> ExcelFileSpec:
    si = scalar_inputs or {}
    return ExcelFileSpec(
        template_path=template_path,
        worksheet="Inputs",
        # ── scalar inputs written to B1-B19 ───────────────────────────────
        inputs=_build_scalar_input_mappings(si),
        # ── per-node column injection (A, B, C, D-I, K-N) ─────────────────
        # Column J is a formula (bottom flange effective width) — do NOT include.
        table_column_inputs=[
            # A: Node ID (integer)
            TableColumnInputMapping(
                start_cell=f"A{_TABLE_START_ROW}",
                component="NODE_ID",
                load_case="",
            ),
            # B: Cumulative distance from first node [m]
            TableColumnInputMapping(
                start_cell=f"B{_TABLE_START_ROW}",
                component="DISTANCE",
                load_case="",
                unit="m",
            ),
            # C: Governing ULS bending moment [kN·m]
            TableColumnInputMapping(
                start_cell=f"C{_TABLE_START_ROW}",
                component="Mz",
                load_case=force_lc,
                unit="kN*m",
            ),
            # D: Area of prestressing steel [cm²]
            TableColumnInputMapping(
                start_cell=f"D{_TABLE_START_ROW}",
                component="Aps",
                load_case="",
                unit="cm**2",
            ),
            # E: Web width [m]
            TableColumnInputMapping(
                start_cell=f"E{_TABLE_START_ROW}",
                component="bw",
                load_case="",
                unit="m",
            ),
            # F: Depth to tendon CG from top [m]
            TableColumnInputMapping(
                start_cell=f"F{_TABLE_START_ROW}",
                component="dp",
                load_case="",
                unit="m",
            ),
            # G: Bottom flange rebar area [mm²]
            TableColumnInputMapping(
                start_cell=f"G{_TABLE_START_ROW}",
                component="bot_As",
                load_case="",
                unit="mm**2",
            ),
            # H: Bottom flange rebar depth [m]
            TableColumnInputMapping(
                start_cell=f"H{_TABLE_START_ROW}",
                component="bot_ds",
                load_case="",
                unit="m",
            ),
            # I: Bottom flange thickness [m]
            TableColumnInputMapping(
                start_cell=f"I{_TABLE_START_ROW}",
                component="bot_hf",
                load_case="",
                unit="m",
            ),
            # J: FORMULA — bottom flange effective width — NOT written by automation
            # K: Top flange rebar area [mm²]
            TableColumnInputMapping(
                start_cell=f"K{_TABLE_START_ROW}",
                component="top_As",
                load_case="",
                unit="mm**2",
            ),
            # L: Top flange rebar depth [m]
            TableColumnInputMapping(
                start_cell=f"L{_TABLE_START_ROW}",
                component="top_ds",
                load_case="",
                unit="m",
            ),
            # M: Top flange thickness [m]
            TableColumnInputMapping(
                start_cell=f"M{_TABLE_START_ROW}",
                component="top_hf",
                load_case="",
                unit="m",
            ),
            # N: Top flange effective width [m]
            TableColumnInputMapping(
                start_cell=f"N{_TABLE_START_ROW}",
                component="top_b",
                load_case="",
                unit="m",
            ),
        ],
        # ── scalar outputs (named ranges, read after recalculation) ────────
        outputs=[
            OutputMapping(cell="Resistance_M.n.Negative", name="Resistance_Mn_Negative"),
            OutputMapping(cell="RF_phi", name="RF_phi"),
        ],
        # ── table outputs (named ranges spanning multiple rows) ────────────
        table_outputs=[
            TableOutputMapping(
                cell="Table_DC",
                name="Table_DC",
                columns=["DC"],
            ),
            TableOutputMapping(
                cell="Table_Location",
                name="Table_Location",
                columns=["Location_m"],
            ),
            TableOutputMapping(
                cell="Table_Mr_neg",
                name="Table_Mr_neg",
                columns=["Mr_neg_kNm"],
            ),
            TableOutputMapping(
                cell="Table_Mr_pos",
                name="Table_Mr_pos",
                columns=["Mr_pos_kNm"],
            ),
            TableOutputMapping(
                cell="Table_Mu",
                name="Table_Mu",
                columns=["Mu_kNm"],
            ),
        ],
        run_order=0,
    )


# Default specs (no scalar overrides — used when no run-spec is available)
SPEC_SI = ExcelCheckSpec(
    name="GirderFlexureCheck",
    files=[_make_file_spec(_TEMPLATE_SI)],
    unit_system=UnitSystemSpec.SI,
)

SPEC_IMP = ExcelCheckSpec(
    name="GirderFlexureCheck",
    files=[_make_file_spec(_TEMPLATE_IMP)],
    unit_system=UnitSystemSpec.IMP,
)


class GirderFlexureCheck(IExcelCheckModule):
    """PT Box girder flexure and moment capacity check (Module 07).

    Populates the full Inputs sheet: scalar material/geometry cells B1-B19
    plus per-node table columns A-N (column J is a formula, not written).

    Scalar inputs come from ``run_spec.module_07.scalar_inputs``, passed
    through ``scalar_inputs`` kwarg on ``execute()``.

    Per-node geometry columns (NODE_ID, DISTANCE, Aps, bw, dp, flange data)
    come from ``pre_computed``, populated by
    ``PTBoxGirderCoordination._prepare_node_data()``.
    """

    MODULE_KEY = "girder_flexure"
    INPUTS_SPEC_KEY = "module_07"   # links to context.module_inputs_for("module_07")
    SPEC_SI  = SPEC_SI
    SPEC_IMP = SPEC_IMP

    @classmethod
    def make_spec(
        cls,
        load_cases: Dict[str, Any],
        scalar_inputs: Optional[Dict[str, Any]] = None,
    ) -> tuple:
        """Build SI and IMP specs from run-spec load case names and scalar inputs.

        Args:
            load_cases:    Dict with key ``"force"`` → load case name string.
            scalar_inputs: Dict from ``run_spec.module_07.scalar_inputs``.
                           ``h`` in this dict is the *minimum* section depth
                           and should already be computed by the caller.
        """
        lc = load_cases.get("force", _FORCE_LC_DEFAULT)
        si = scalar_inputs or {}
        return (
            ExcelCheckSpec(
                name="GirderFlexureCheck",
                files=[_make_file_spec(_TEMPLATE_SI, lc, si)],
                unit_system=UnitSystemSpec.SI,
            ),
            ExcelCheckSpec(
                name="GirderFlexureCheck",
                files=[_make_file_spec(_TEMPLATE_IMP, lc, si)],
                unit_system=UnitSystemSpec.IMP,
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
        effective_system = self._resolve_unit_system(view, unit_system)
        lcs = load_cases or {}
        si = scalar_inputs or {}

        spec_si, spec_imp = self.make_spec(lcs, si)
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
