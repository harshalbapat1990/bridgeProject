from typing import Literal

from pydantic import Field, model_validator
from bda.contracts.speckle_contracts.base_objects import UnitlessParameter, EnumParameter
from bda.contracts.speckle_contracts.unit_parameters import LengthParameter
from bda.contracts.paramodel.groups.enums import (
    ElementOrientationParaModel
)
from bda.contracts.paramodel.foundations.enums import FoundationModelTypeParaModel, \
    FoundationApplicationTypeEnumParaModel, SoilProfileTypeEnumParaModel

from ...common_parameters import SupportIndexParameter

class FoundationModelTypeParameter(
    EnumParameter[FoundationModelTypeParaModel]
):
    #let me know if we should move to enum based parameters here
    name: Literal[
        "Foundation Model Type"
    ] = "Foundation Model Type"

    description: Literal[
        "Type of foundation model for the support"
    ] = (
        "Type of foundation model for the support"
    )

class LumpedFoundationFoundationModelTypeParameter(
    FoundationModelTypeParameter
):
    provided_value: Literal[
        FoundationModelTypeParaModel.LUMPED_FOUNDATION_MODEL
    ] = FoundationModelTypeParaModel.LUMPED_FOUNDATION_MODEL

class PileInteractionFoundationModelTypeParameter(
    FoundationModelTypeParameter
):
    provided_value: Literal[
        FoundationModelTypeParaModel.PILE_INTERACTION_MODEL
    ] = FoundationModelTypeParaModel.PILE_INTERACTION_MODEL


class FoundationApplicationTypeParameter(
    EnumParameter[FoundationApplicationTypeEnumParaModel]
):
    name: Literal[
        "Foundation Application Type"
    ] = "Foundation Application Type"

    description: Literal[
        "Type of foundation application for the support"
    ] = (
        "Type of foundation application for the support"
    )

class BearingBasedFoundationApplicationTypeParameter(
    FoundationApplicationTypeParameter
):
    provided_value: Literal[
        FoundationApplicationTypeEnumParaModel.BEARING_BASED
    ] = FoundationApplicationTypeEnumParaModel.BEARING_BASED

class SubstructureElementBasedFoundationApplicationTypeParameter(
    FoundationApplicationTypeParameter
):
    provided_value: Literal[
        FoundationApplicationTypeEnumParaModel.SUBSTRUCTURE_ELEMENT_BASED
    ] = FoundationApplicationTypeEnumParaModel.SUBSTRUCTURE_ELEMENT_BASED


class VerticalOffsetParameter(
    LengthParameter
):
    name: Literal[
        "Vertical Offset"
    ] = "Vertical Offset"

    # Keep the minimum in base units so the schema is unit-aware and does not
    # assume a single author-supplied unit string. Values are converted to m
    # before validation, and the published schema reflects the minimum on the
    # computed base_value field.
    base_value: float = Field(
        ge=0.1,
        description="Minimum vertical offset in metres.",
    )

    description: Literal[
        "Vertical offset of the foundation relative to the support"
    ] = (
        "Vertical offset of the foundation relative to the support"
    )


class PileIndexParameter(
    UnitlessParameter[int]
):
    name: Literal[
        "Pile Index"
    ] = "Pile Index"

    description: Literal[
        "Index of the pile within the foundation"
    ] = (
        "Index of the pile within the foundation"
    )


class SoilProfileTypeParameter(
    EnumParameter[SoilProfileTypeEnumParaModel]
):
    name: Literal[
        "Soil Profile Type"
    ] = "Soil Profile Type"

    description: Literal[
        "Type of soil profile for the foundation"
    ] = (
        "Type of soil profile for the foundation"
    )


class UniformSoilProfileTypeParameter(
    SoilProfileTypeParameter
):
    provided_value: Literal[
        SoilProfileTypeEnumParaModel.UNIFORM
    ] = SoilProfileTypeEnumParaModel.UNIFORM

class FoundationOrientationParameter(
    UnitlessParameter[
        ElementOrientationParaModel
    ]
):
    name: Literal[
        "Lumped Foundation Orientation"
    ] = (
        "Lumped Foundation Orientation"
    )
    description: Literal[
        "Orientation of the lumped foundation"
    ] = (
        "Orientation of the lumped foundation"
    )
