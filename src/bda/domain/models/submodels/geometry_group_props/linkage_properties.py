from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import List, Union

from bda.domain.models.submodels.geometry_group import GroupPropertiesBase
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import (
    BearingConfigurationType,
    SpacingType,
)
from bda.domain.units.quantities import Length


# -------------------------
# DETAIL CLASSES
# -------------------------

@dataclass
class BearingConfigurationDetailsBase(ABC):
    bearing_configuration_type: BearingConfigurationType
    no_of_bearings: int


@dataclass
class SingleBearingConfigurationDetails(BearingConfigurationDetailsBase):
    bearing_configuration_type: BearingConfigurationType = field(
        init=False,
        default=BearingConfigurationType.SINGULAR)
    no_of_bearings: int = 1


@dataclass
class MultipleBearingConfigurationDetails(BearingConfigurationDetailsBase):
    bearing_configuration_type: BearingConfigurationType = field(
        init=False,
        default=BearingConfigurationType.MULTIPLE)
    bearing_spacing_type: SpacingType
    bearing_spacing: List[Length]


BearingConfigurationDetails = Union[SingleBearingConfigurationDetails, MultipleBearingConfigurationDetails]


# -------------------------
# PROPERTIES CLASSES
# -------------------------

@dataclass
class GroupPropertiesLinkageSupToSub(GroupPropertiesBase):
    support_index: int
    bearing_configuration_details: BearingConfigurationDetails


