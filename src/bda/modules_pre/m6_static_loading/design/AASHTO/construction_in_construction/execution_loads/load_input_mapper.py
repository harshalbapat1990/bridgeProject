from dataclasses import dataclass
from typing import Annotated

from pint import Quantity


@dataclass(kw_only=True)
class ExecutionLoadInputMapper:
    """Execution loads, named the way the workbook's input labels name them.

    A load that is ``None`` is not merely skipped: the workbook has an explicit
    Include/Exclude switch per load, so an absent load is reported as excluded
    and its value cell is blanked.

    Cell addresses, unit conversion and the Excel round trip belong to
    ``WorkbookBinding``, not here.
    """

    # No ``from __future__ import annotations`` in this file: it silently
    # disables validate_pint_fields for the whole module.

    fixed_material_loads_uniform_load: Annotated[Quantity, "[force] / [length]**2"] | None
    variable_material_loads_uniform_load: Annotated[Quantity, "[force] / [length]**2"] | None
    personnel_and_equipment_uniform_load: Annotated[Quantity, "[force] / [length]**2"] | None

    # load label -> the switch that says whether it is in play. Unannotated, so
    # the dataclass leaves it a plain class attribute rather than a field.
    _INCLUSION_SWITCHES = {
        "fixed_material_loads_uniform_load": "inclusion_of_fixed_material_loads",
        "variable_material_loads_uniform_load": "inclusion_of_variable_material_loads",
        "personnel_and_equipment_uniform_load": "inclusion_of_personnel_and_equipment_loads",
    }

    def to_workbook_values(self) -> dict[str, Quantity | str]:
        """Label -> value for every input cell this mapper is responsible for."""
        values: dict[str, Quantity | str] = {}
        for load_label, switch_label in self._INCLUSION_SWITCHES.items():
            load = getattr(self, load_label)
            values[switch_label] = "Include" if load is not None else "Exclude"
            values[load_label] = load if load is not None else ""
        return values
