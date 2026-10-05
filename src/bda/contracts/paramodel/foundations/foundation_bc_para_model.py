from __future__ import annotations

from typing import Annotated, Literal, Union, List

from pydantic import Field

from bda.contracts.paramodel.foundations.enums import FoundationModelTypeParaModel, SoilProfileTypeEnumParaModel, \
    DofTypeEnumParaModel, FoundationApplicationTypeEnumParaModel
from bda.contracts.paramodel.groups import ElementOrientationParaModel
from bda.contracts.paramodel.shared.base_model_para_model import BaseModelParaModel
from bda.contracts.shared import QuantityParaModel


class FoundationBCsBaseParaModel(BaseModelParaModel):
    foundation_model_type: FoundationModelTypeParaModel
    support_index: int


class SpringStiffnessBaseParaModel(BaseModelParaModel):
    dof_type: DofTypeEnumParaModel


class TranslationalStiffnessParaModel(SpringStiffnessBaseParaModel):
    stiffness: QuantityParaModel | None = None


class RotationalStiffnessParaModel(SpringStiffnessBaseParaModel):
    stiffness: QuantityParaModel | None = None


class PileNodeSpringStiffnessParaModel(BaseModelParaModel):
    sdx: TranslationalStiffnessParaModel
    sdy: TranslationalStiffnessParaModel
    sdz: TranslationalStiffnessParaModel

# TODO: consider renaming to 'SpringStiffnessParaModel' as in domain classes
class NodeSpringStiffnessParaModel(BaseModelParaModel):
    sdx: TranslationalStiffnessParaModel
    sdy: TranslationalStiffnessParaModel
    sdz: TranslationalStiffnessParaModel
    srx: RotationalStiffnessParaModel
    sry: RotationalStiffnessParaModel
    srz: RotationalStiffnessParaModel


class PileStiffnessDataBaseParaModel(BaseModelParaModel):
    soil_profile_type: SoilProfileTypeEnumParaModel
    pile_index: int
    top_node: PileNodeSpringStiffnessParaModel
    bottom_node: PileNodeSpringStiffnessParaModel


class PileStiffnessUniformDatasetParaModel(PileStiffnessDataBaseParaModel):
    soil_profile_type: Literal[SoilProfileTypeEnumParaModel.UNIFORM]
    intermediate_nodes: PileNodeSpringStiffnessParaModel


PileStiffnessDatasetParaModel = Annotated[
    Union[
        PileStiffnessUniformDatasetParaModel,
    ],
    Field(discriminator="soil_profile_type"),
]


class FoundationApplicationBaseParaModel(BaseModelParaModel):
    application_type: FoundationApplicationTypeEnumParaModel


class BearingBasedFoundationApplicationParaModel(FoundationApplicationBaseParaModel):
    application_type: Literal[FoundationApplicationTypeEnumParaModel.BEARING_BASED]
    vertical_offset: QuantityParaModel = QuantityParaModel(value=0.1, unit="m")


class SubstructureElementBasedFoundationApplicationParaModel(FoundationApplicationBaseParaModel):
    application_type: Literal[FoundationApplicationTypeEnumParaModel.SUBSTRUCTURE_ELEMENT_BASED]


class PileInteractionFoundationBCsParaModel(FoundationBCsBaseParaModel):
    foundation_model_type: Literal[FoundationModelTypeParaModel.PILE_INTERACTION_MODEL]
    pile_springs: List[PileStiffnessDatasetParaModel]


FoundationApplicationParaModel = Annotated[
    Union[
        BearingBasedFoundationApplicationParaModel,
        SubstructureElementBasedFoundationApplicationParaModel
    ],
    Field(discriminator="application_type"),
]


class LumpedFoundationBCsParaModel(FoundationBCsBaseParaModel):
    foundation_model_type: Literal[FoundationModelTypeParaModel.LUMPED_FOUNDATION_MODEL]
    stiffness_definition: NodeSpringStiffnessParaModel
    orientation: ElementOrientationParaModel
    application: FoundationApplicationParaModel


FoundationBCsParaModel = Annotated[
    Union[
        LumpedFoundationBCsParaModel,
        PileInteractionFoundationBCsParaModel
    ],
    Field(discriminator="foundation_model_type")
]