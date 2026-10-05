from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import List, Union

from pint.registry import Quantity

from bda.domain.base import MultiModelObjectBase
from bda.domain.models.submodels.boundary_conditions.enums import DofTypeEnum, SoilProfileType, \
    FoundationApplicationType, FoundationModelType
from bda.domain.models.submodels.boundary_conditions.spring_stiffness import SpringStiffness, TranslationalStiffness
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation


#
#   STIFFNESS DATACLASSES
#

@dataclass(kw_only=True)
class PileNodeSpringStiffness:
    sdx: TranslationalStiffness
    sdy: TranslationalStiffness
    sdz: TranslationalStiffness


@dataclass(kw_only=True)
class NodeSpringStiffness (SpringStiffness):
    pass


#
#   PILE DATASET DATACLASSES
#
@dataclass(kw_only=True)
class PileStiffnessDatasetBase(ABC):
    soil_profile_type: SoilProfileType
    pile_index: int
    top_node: PileNodeSpringStiffness
    bottom_node: PileNodeSpringStiffness


@dataclass(kw_only=True)
class PileStiffnessUniformDataset(PileStiffnessDatasetBase):
    soil_profile_type: SoilProfileType = field(default=SoilProfileType.UNIFORM, init=False)
    intermediate_nodes: PileNodeSpringStiffness


#
#   APPLICATION DATACLASSES
#
@dataclass(kw_only=True)
class FoundationApplicationBase(ABC):
    application_type: FoundationApplicationType


@dataclass(kw_only=True)
class BearingBasedFoundationApplication(FoundationApplicationBase):
    application_type: FoundationApplicationType = field(
        default=FoundationApplicationType.BEARING_BASED, init=False
    )
    vertical_offset: Quantity


@dataclass(kw_only=True)
class SubstructureElementBasedFoundationApplication(FoundationApplicationBase):
    application_type: FoundationApplicationType = field(
        default=FoundationApplicationType.SUBSTRUCTURE_ELEMENT_BASED, init=False
    )


FoundationApplication = Union[
    BearingBasedFoundationApplication,
    SubstructureElementBasedFoundationApplication,
]


#
#   BASE CLASS
#
@dataclass(kw_only=True)
class FoundationBCsBase(MultiModelObjectBase, ABC): ...


#
#   DOMAIN CLASSES
#
@dataclass(kw_only=True)
class FoundationBCsSupportBase(FoundationBCsBase):
    support_index: int
    foundation_model_type: FoundationModelType


@dataclass(kw_only=True)
class LumpedFoundationBCs(FoundationBCsSupportBase):
    """Defines lumped spring boundary conditions for a foundation support.

    Attributes:
        foundation_model_type (Literal[FoundationModelType.LUMPED_FOUNDATION_MODEL]):
            Identifies this as a lumped (point-spring) foundation model.
        stiffness_definition (NodeSpringStiffness):
            Full 6-DOF spring stiffness at the foundation node.
        orientation (ElementOrientation):
            Orientation of the foundation element (orthogonal or skewed).
        application (FoundationApplication):
            Defines how the foundation spring is applied — either bearing-based
            (with a vertical offset) or substructure-element-based.
    """

    foundation_model_type: FoundationModelType = field(
        default=FoundationModelType.LUMPED_FOUNDATION_MODEL, init=False
    )
    stiffness_definition: NodeSpringStiffness
    orientation: ElementOrientation
    application: FoundationApplication


@dataclass(kw_only=True)
class PileInteractionFoundationBCs(FoundationBCsSupportBase):
    """Defines pile-interaction boundary conditions for a foundation support.

    Attributes:
        foundation_model_type (Literal[FoundationModelType.PILE_INTERACTION_MODEL]):
            Identifies this as a pile-interaction foundation model.
        pile_springs (List[PileStiffnessUniformDataset]):
            Spring stiffness datasets for each individual pile, including
            top, bottom, and any intermediate nodes.
    """

    foundation_model_type: FoundationModelType = field(
        default=FoundationModelType.PILE_INTERACTION_MODEL, init=False
    )
    pile_springs: List[PileStiffnessUniformDataset]


FoundationBCs = Union[
    LumpedFoundationBCs,
    PileInteractionFoundationBCs,
]
