from __future__ import annotations

from typing import Annotated, Literal, Union, List

from pydantic import Field, AliasChoices, AliasPath

from bda.contracts.paramodel.foundations.enums import FoundationModelTypeParaModel, SoilProfileTypeEnumParaModel, \
    DofTypeEnumParaModel, FoundationApplicationTypeEnumParaModel
from bda.contracts.paramodel.groups import ElementOrientationParaModel
from bda.contracts.paramodel.shared.base_model_para_model import BaseModelParaModel
from bda.contracts.shared import QuantityParaModel


class FoundationBCsBaseParaModel(BaseModelParaModel):
    foundation_model_type: FoundationModelTypeParaModel = Field(validation_alias=AliasChoices("foundation_model_type", AliasPath("properties", "Lumped Foundation Parameters", "group_parameters", "Foundation Model Type", "provided_value"), AliasPath("properties", "Foundation Model Type", "provided_value")))
    support_index: int = Field(validation_alias=AliasChoices("support_index", AliasPath("properties", "Lumped Foundation Parameters", "group_parameters", "Support Index", "provided_value"), AliasPath("properties", "Support Index", "provided_value")))


class SpringStiffnessBaseParaModel(BaseModelParaModel):
    dof_type: DofTypeEnumParaModel = Field(validation_alias=AliasChoices("dof_type", AliasPath("DOF Type", "provided_value"), "DOF Type"))


class TranslationalStiffnessParaModel(SpringStiffnessBaseParaModel):
    stiffness: QuantityParaModel | None = Field(default=None, validation_alias=AliasChoices("stiffness", "Stiffness"))


class RotationalStiffnessParaModel(SpringStiffnessBaseParaModel):
    stiffness: QuantityParaModel | None = Field(default=None, validation_alias=AliasChoices("stiffness", "Stiffness"))


class PileNodeSpringStiffnessParaModel(BaseModelParaModel):
    sdx: TranslationalStiffnessParaModel = Field(validation_alias=AliasChoices("sdx", AliasPath("SDX", "group_parameters")))
    sdy: TranslationalStiffnessParaModel = Field(validation_alias=AliasChoices("sdy", AliasPath("SDY", "group_parameters")))
    sdz: TranslationalStiffnessParaModel = Field(validation_alias=AliasChoices("sdz", AliasPath("SDZ", "group_parameters")))

# TODO: consider renaming to 'SpringStiffnessParaModel' as in domain classes
class NodeSpringStiffnessParaModel(BaseModelParaModel):
    sdx: TranslationalStiffnessParaModel = Field(validation_alias=AliasChoices("sdx", AliasPath("SDX", "group_parameters")))
    sdy: TranslationalStiffnessParaModel = Field(validation_alias=AliasChoices("sdy", AliasPath("SDY", "group_parameters")))
    sdz: TranslationalStiffnessParaModel = Field(validation_alias=AliasChoices("sdz", AliasPath("SDZ", "group_parameters")))
    srx: RotationalStiffnessParaModel = Field(validation_alias=AliasChoices("srx", AliasPath("SRX", "group_parameters")))
    sry: RotationalStiffnessParaModel = Field(validation_alias=AliasChoices("sry", AliasPath("SRY", "group_parameters")))
    srz: RotationalStiffnessParaModel = Field(validation_alias=AliasChoices("srz", AliasPath("SRZ", "group_parameters")))


class PileStiffnessDataBaseParaModel(BaseModelParaModel):
    soil_profile_type: SoilProfileTypeEnumParaModel = Field(validation_alias=AliasChoices("soil_profile_type", AliasPath("Soil Profile Type", "provided_value")))
    pile_index: int = Field(validation_alias=AliasChoices("pile_index", AliasPath("Pile Index", "provided_value")))
    top_node: PileNodeSpringStiffnessParaModel = Field(validation_alias=AliasChoices("top_node", AliasPath("Top Node Spring Definition", "group_parameters")))
    bottom_node: PileNodeSpringStiffnessParaModel = Field(validation_alias=AliasChoices("bottom_node", AliasPath("Bottom Node Spring Definition", "group_parameters")))


class PileStiffnessUniformDatasetParaModel(PileStiffnessDataBaseParaModel):
    soil_profile_type: Literal[SoilProfileTypeEnumParaModel.UNIFORM]
    intermediate_nodes: PileNodeSpringStiffnessParaModel = Field(validation_alias=AliasChoices("intermediate_nodes", AliasPath("Intermediate Node Spring Definition", "group_parameters")))


PileStiffnessDatasetParaModel = Annotated[
    Union[
        PileStiffnessUniformDatasetParaModel,
    ],
    Field(discriminator="soil_profile_type"),
]


class FoundationApplicationBaseParaModel(BaseModelParaModel):
    application_type: FoundationApplicationTypeEnumParaModel = Field(validation_alias=AliasChoices("application_type", AliasPath("Foundation Application Type", "provided_value")))


class BearingBasedFoundationApplicationParaModel(FoundationApplicationBaseParaModel):
    application_type: Literal[FoundationApplicationTypeEnumParaModel.BEARING_BASED]
    vertical_offset: QuantityParaModel = Field(default=QuantityParaModel(value=0.1, unit="m"), validation_alias=AliasChoices("vertical_offset", "Vertical Offset"))


class SubstructureElementBasedFoundationApplicationParaModel(FoundationApplicationBaseParaModel):
    application_type: Literal[FoundationApplicationTypeEnumParaModel.SUBSTRUCTURE_ELEMENT_BASED]


class PileInteractionFoundationBCsParaModel(FoundationBCsBaseParaModel):
    foundation_model_type: Literal[FoundationModelTypeParaModel.PILE_INTERACTION_MODEL]
    pile_springs: List[PileStiffnessDatasetParaModel] = Field(validation_alias=AliasChoices("pile_springs", AliasPath("properties", "Pile Definitions", "group_parameters")))


FoundationApplicationParaModel = Annotated[
    Union[
        BearingBasedFoundationApplicationParaModel,
        SubstructureElementBasedFoundationApplicationParaModel
    ],
    Field(discriminator="application_type"),
]


class LumpedFoundationBCsParaModel(FoundationBCsBaseParaModel):
    foundation_model_type: Literal[FoundationModelTypeParaModel.LUMPED_FOUNDATION_MODEL]
    stiffness_definition: NodeSpringStiffnessParaModel = Field(validation_alias=AliasChoices("stiffness_definition", AliasPath("properties", "Lumped Foundation Parameters", "group_parameters", "Foundation Spring Definition", "group_parameters")))
    orientation: ElementOrientationParaModel = Field(validation_alias=AliasChoices("orientation", AliasPath("properties", "Lumped Foundation Parameters", "group_parameters", "Lumped Foundation Orientation", "provided_value")))
    application: FoundationApplicationParaModel = Field(validation_alias=AliasChoices("application", AliasPath("properties", "Lumped Foundation Parameters", "group_parameters")))


FoundationBCsParaModel = Annotated[
    Union[
        LumpedFoundationBCsParaModel,
        PileInteractionFoundationBCsParaModel
    ],
    Field(discriminator="foundation_model_type")
]
