from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import Annotated, Any

from pint import Quantity


@dataclass(kw_only=True)
class ExecutionLoadOutputMapper:
    """The execution loads the workbook computed.

    Values arrive already carrying their units -- ``WorkbookBinding`` attaches
    those, because it is the thing that knows which unit system the run used.
    What is left here is naming and dimension, which is all a result object
    should carry.
    """

    # No ``from __future__ import annotations`` in this file: it silently
    # disables validate_pint_fields for the whole module.

    fixed_material_loads_uniform_load: Annotated[Quantity, "[force] / [length]**2"] | None = None
    variable_material_loads_uniform_load: Annotated[Quantity, "[force] / [length]**2"] | None = None
    personnel_and_equipment_uniform_load: Annotated[Quantity, "[force] / [length]**2"] | None = None

    @classmethod
    def from_workbook_outputs(cls, outputs: Mapping[str, Any]) -> "ExecutionLoadOutputMapper":
        """Pick the labels this mapper names; ignore anything else the spec reads."""
        known = {field.name for field in fields(cls)}
        return cls(**{label: value for label, value in outputs.items() if label in known})
