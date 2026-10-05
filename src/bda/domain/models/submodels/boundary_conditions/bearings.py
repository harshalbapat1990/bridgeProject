from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import List, Literal

from bda.domain.base import MultiModelObjectBase
from bda.domain.models.submodels.boundary_conditions.spring_stiffness import SpringStiffness
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation, \
    BearingConfigurationType


#
#   BASE CLASS
#
@dataclass(kw_only=True)
class BearingBase(MultiModelObjectBase, ABC): ...


#
#   DOMAIN CLASSES
#
@dataclass(kw_only=True)
class BearingItem(BearingBase):
    bearing_index: int
    orientation: ElementOrientation
    bearing_stiffness_definition: SpringStiffness

    def __repr__(self):
        return (f"BearingItem(bearing_index= {self.bearing_index}, "
                f"orientation= {self.orientation}, "
                f"bearing_stiffness_definition= {self.bearing_stiffness_definition})")


@dataclass(kw_only=True)
class BearingBCsGirderBase(BearingBase):
    girder_index: int
    bearing_configuration_type: BearingConfigurationType


@dataclass(kw_only=True)
class SingleBearingBCs(BearingBCsGirderBase):
    """Defines boundary conditions for a girder supported by a single bearing.

    This model represents a girder-support connection in which only one
    bearing is assigned to the girder. The bearing properties, orientation,
    and stiffness characteristics are stored in the bearing definition.

    Attributes:
        bearing_configuration_type (Literal[BearingConfigurationType.SINGULAR]):
            Identifies the bearing configuration as a single-bearing arrangement.
        bearing_definition (BearingItem):
            Definition of the bearing associated with the girder.
    """

    bearing_configuration_type: BearingConfigurationType = field(default=BearingConfigurationType.SINGULAR, init= False)
    bearing_definition: BearingItem


@dataclass(kw_only=True)
class MultiBearingBCs(BearingBCsGirderBase):
    """Defines boundary conditions for a girder supported by multiple bearings.

    This model represents a girder-support connection in which more than one
    bearing is assigned to the girder. Each bearing definition contains its
    own orientation and stiffness properties.

    Attributes:
        bearing_configuration_type (Literal[BearingConfigurationType.MULTIPLE]):
            Identifies the bearing configuration as a multiple-bearing arrangement.
        bearing_definitions (List[BearingItem]):
            Collection of bearing definitions associated with the girder.
    """
    bearing_configuration_type: BearingConfigurationType = field(default=BearingConfigurationType.MULTIPLE, init= False)
    bearing_definitions: List[BearingItem]


@dataclass(kw_only=True)
class BearingBCsSupport(BearingBase):
    """Defines bearing boundary conditions assigned to a support.

    Each support may provide bearing boundary condition definitions for
    multiple girders. For every girder, the bearing arrangement can be
    represented by either a single-bearing or multiple-bearing
    configuration.

    Attributes:
        support_index (int):
            Index of the support within the structure.

        bearings_by_girder (List[BearingBCsGirder]):
            Bearing boundary condition definitions assigned to individual
            girders at this support.
    """
    support_index: int
    bearings_by_girder: List[BearingBCsGirderBase]

