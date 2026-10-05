"""FE-level loads and load cases of the analytical multimodel.

NOTE: modules in this package must not use ``from __future__ import annotations``;
it would silently disable pint dimension validation of ``Annotated`` fields.
"""

from bda.domain.models.submodels.loads.line_loads import BeamLineLoad
from bda.domain.models.submodels.loads.load_base import (
    AreaLoadElementBase,
    LineLoadElementBase,
    LoadElementBase,
    PointLoadElementBase,
)
from bda.domain.models.submodels.loads.load_case import LoadCase
from bda.domain.models.submodels.loads.load_components import (
    LineLoadComponents,
    LoadOffset,
    PointLoadComponents,
)
from bda.domain.models.submodels.loads.load_self_weight import SelfWeightFactors, SelfWeightLoad
from bda.domain.models.submodels.loads.load_thermal import (
    GradientDefinition,
    ThermalLoadElementBase,
    ThermalLoadGradient,
    ThermalLoadUniform,
)
from bda.domain.models.submodels.loads.loads import Loads
from bda.domain.models.submodels.loads.point_loads import BeamPointLoad, NodalPointLoad

__all__ = [
    "AreaLoadElementBase",
    "BeamLineLoad",
    "BeamPointLoad",
    "LineLoadElementBase",
    "LineLoadComponents",
    "LoadElementBase",
    "LoadCase",
    "LoadOffset",
    "NodalPointLoad",
    "PointLoadElementBase",
    "PointLoadComponents",
    #Self-weight loads
    "SelfWeightFactors",
    "SelfWeightLoad",
    #   thermal loads
    "GradientDefinition",
    "ThermalLoadElementBase",
    "ThermalLoadGradient",
    "ThermalLoadUniform",

    "Loads",
]