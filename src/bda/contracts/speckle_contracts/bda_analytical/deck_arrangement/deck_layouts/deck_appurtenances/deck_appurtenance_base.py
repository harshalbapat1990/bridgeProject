from __future__ import annotations

from typing import Annotated, ClassVar, Literal, Union

from pydantic import Field

from bda.contracts.speckle_contracts.base_objects import (
    BridgeDataObject,
    BridgeDataObjectProperties,
    EnumParameter,
    Parameter,
)
from bda.contracts.paramodel.deck_appurtenances.enums import (
    DeckAppurtenanceTypeParaModel,
    GeometryTypeParaModel,
    PositionDefEnumParaModel,
)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

class AppurtenanceIdParameter(Parameter[str]):
    name: Literal["Appurtenance ID"] = "Appurtenance ID"
    description: Literal["Unique identifier for the appurtenance"] = (
        "Unique identifier for the appurtenance"
    )
    provided_value: str


class ElementIndexParameter(Parameter[int]):
    name: Literal["Element Index"] = "Element Index"
    description: Literal["Zero-based index of the appurtenance element"] = (
        "Zero-based index of the appurtenance element"
    )
    provided_value: int = Field(ge=0)


class AppurtenanceTypeParameter(EnumParameter[DeckAppurtenanceTypeParaModel]):
    name: Literal["Appurtenance Type"] = "Appurtenance Type"
    description: Literal["Type classification of the deck appurtenance"] = (
        "Type classification of the deck appurtenance"
    )
    provided_value: DeckAppurtenanceTypeParaModel


class MaterialIdParameter(Parameter[str]):
    name: Literal["Material ID"] = "Material ID"
    description: Literal["Reference ID of the material assigned to this appurtenance"] = (
        "Reference ID of the material assigned to this appurtenance"
    )
    provided_value: str


class PositionedByParameter(EnumParameter[PositionDefEnumParaModel]):
    name: Literal["Positioned By"] = "Positioned By"
    description: Literal["Defines how the appurtenance is positioned on the deck"] = (
        "Defines how the appurtenance is positioned on the deck"
    )
    provided_value: PositionDefEnumParaModel


class PositionedByParameter_Fixed(PositionedByParameter):
    provided_value: Literal[PositionDefEnumParaModel.FIXED] = PositionDefEnumParaModel.FIXED


class PositionedByParameter_ByOffset(PositionedByParameter):
    provided_value: Literal[PositionDefEnumParaModel.BY_OFFSET] = PositionDefEnumParaModel.BY_OFFSET


class GeometryTypeParameter(EnumParameter[GeometryTypeParaModel]):
    name: Literal["Geometry Type"] = "Geometry Type"
    description: Literal["Geometry type of the appurtenance cross-section"] = (
        "Geometry type of the appurtenance cross-section"
    )
    provided_value: GeometryTypeParaModel


class GeometryTypeParameter_Linear(GeometryTypeParameter):
    provided_value: Literal[GeometryTypeParaModel.LINEAR] = GeometryTypeParaModel.LINEAR


class GeometryTypeParameter_Surface(GeometryTypeParameter):
    provided_value: Literal[GeometryTypeParaModel.SURFACE] = GeometryTypeParaModel.SURFACE


class WidthParameter(Parameter[float]):
    name: Literal["Width"] = "Width"
    description: Literal["Width of the appurtenance [Length]"] = (
        "Width of the appurtenance [Length]"
    )
    provided_value: float = Field(gt=0)


class HeightParameter(Parameter[float]):
    name: Literal["Height"] = "Height"
    description: Literal["Height of the linear appurtenance [Length]"] = (
        "Height of the linear appurtenance [Length]"
    )
    provided_value: float = Field(gt=0)


class OutlineParameter(Parameter[list]):
    """Flat list of [x, y] coordinate pairs describing the cross-section outline.
    None entries (serialised as null) act as sub-polygon separators."""
    name: Literal["Outline"] = "Outline"
    description: Literal["Cross-section outline as flat [x, y, ...] coordinate list [Length]"] = (
        "Cross-section outline as flat [x, y, ...] coordinate list [Length]"
    )
    provided_value: list[float | None]


class ThicknessLeftParameter(Parameter[float]):
    name: Literal["Thickness Left"] = "Thickness Left"
    description: Literal["Left-edge thickness of the surface appurtenance [Length]"] = (
        "Left-edge thickness of the surface appurtenance [Length]"
    )
    provided_value: float = Field(gt=0)


class ThicknessRightParameter(Parameter[float]):
    name: Literal["Thickness Right"] = "Thickness Right"
    description: Literal["Right-edge thickness of the surface appurtenance [Length]"] = (
        "Right-edge thickness of the surface appurtenance [Length]"
    )
    provided_value: float = Field(gt=0)


class OffsetParameter(Parameter[float]):
    name: Literal["Offset"] = "Offset"
    description: Literal[
        "Transverse offset from the bridge centreline [Length]; positive = left"
    ] = "Transverse offset from the bridge centreline [Length]; positive = left"
    provided_value: float


# ---------------------------------------------------------------------------
# Properties — base fields shared by every appurtenance
# ---------------------------------------------------------------------------

class DeckAppurtenanceBaseProperties(BridgeDataObjectProperties):
    """Properties common to all deck appurtenance types."""

    element_index: ElementIndexParameter = Field(alias="Element Index")
    appurtenance_type: AppurtenanceTypeParameter = Field(alias="Appurtenance Type")
    material_id: MaterialIdParameter = Field(alias="Material ID")
    width: WidthParameter = Field(alias="Width")


# ---------------------------------------------------------------------------
# Properties — concrete combinations (positioned_by × geometry_type)
# ---------------------------------------------------------------------------

class LinearFixedDeckAppurtenanceProperties(DeckAppurtenanceBaseProperties):
    positioned_by: PositionedByParameter_Fixed = Field(alias="Positioned By")
    geometry_type: GeometryTypeParameter_Linear = Field(alias="Geometry Type")
    height: HeightParameter = Field(alias="Height")
    outline: OutlineParameter = Field(alias="Outline")


class SurfaceFixedDeckAppurtenanceProperties(DeckAppurtenanceBaseProperties):
    positioned_by: PositionedByParameter_Fixed = Field(alias="Positioned By")
    geometry_type: GeometryTypeParameter_Surface = Field(alias="Geometry Type")
    thickness_left: ThicknessLeftParameter = Field(alias="Thickness Left")
    thickness_right: ThicknessRightParameter = Field(alias="Thickness Right")


class LinearByOffsetDeckAppurtenanceProperties(DeckAppurtenanceBaseProperties):
    positioned_by: PositionedByParameter_ByOffset = Field(alias="Positioned By")
    geometry_type: GeometryTypeParameter_Linear = Field(alias="Geometry Type")
    height: HeightParameter = Field(alias="Height")
    outline: OutlineParameter = Field(alias="Outline")
    offset: OffsetParameter = Field(alias="Offset")


class SurfaceByOffsetDeckAppurtenanceProperties(DeckAppurtenanceBaseProperties):
    positioned_by: PositionedByParameter_ByOffset = Field(alias="Positioned By")
    geometry_type: GeometryTypeParameter_Surface = Field(alias="Geometry Type")
    thickness_left: ThicknessLeftParameter = Field(alias="Thickness Left")
    thickness_right: ThicknessRightParameter = Field(alias="Thickness Right")
    offset: OffsetParameter = Field(alias="Offset")


# ---------------------------------------------------------------------------
# Data objects
# ---------------------------------------------------------------------------

_BDA_TYPE_LINEAR_FIXED = (
    "Objects.Data.DataObject:BDA_Linear_Fixed_Deck_Appurtenance"
)
_BDA_TYPE_SURFACE_FIXED = (
    "Objects.Data.DataObject:BDA_Surface_Fixed_Deck_Appurtenance"
)
_BDA_TYPE_LINEAR_BY_OFFSET = (
    "Objects.Data.DataObject:BDA_Linear_By_Offset_Deck_Appurtenance"
)
_BDA_TYPE_SURFACE_BY_OFFSET = (
    "Objects.Data.DataObject:BDA_Surface_By_Offset_Deck_Appurtenance"
)


class LinearFixedDeckAppurtenance(BridgeDataObject):
    """Linear cross-section appurtenance whose position is fixed by the deck layout."""

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^DA-LF-\d{4}$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)
    name: str

    bda_speckle_type: Literal[_BDA_TYPE_LINEAR_FIXED] = Field(..., frozen=True)

    properties: LinearFixedDeckAppurtenanceProperties

    @classmethod
    def create(
        cls,
        name: str,
        application_id: str,
        appurtenance_id: str,
        element_index: int,
        appurtenance_type: DeckAppurtenanceTypeParaModel,
        material_id: str,
        width: float,
        height: float,
        outline: list[float | None],
    ) -> "LinearFixedDeckAppurtenance":
        return cls(
            applicationId=application_id,
            name=name,
            bda_speckle_type=_BDA_TYPE_LINEAR_FIXED,
            properties=LinearFixedDeckAppurtenanceProperties(
                **{
                    "Appurtenance ID": AppurtenanceIdParameter(isUser=True, provided_value=appurtenance_id),
                    "Element Index": ElementIndexParameter(isUser=True, provided_value=element_index),
                    "Appurtenance Type": AppurtenanceTypeParameter(isUser=True, provided_value=appurtenance_type),
                    "Material ID": MaterialIdParameter(isUser=True, provided_value=material_id),
                    "Width": WidthParameter(isUser=True, provided_value=width),
                    "Positioned By": PositionedByParameter_Fixed(isUser=True),
                    "Geometry Type": GeometryTypeParameter_Linear(isUser=True),
                    "Height": HeightParameter(isUser=True, provided_value=height),
                    "Outline": OutlineParameter(isUser=True, provided_value=outline),
                }
            ),
        )


class SurfaceFixedDeckAppurtenance(BridgeDataObject):
    """Surface cross-section appurtenance whose position is fixed by the deck layout."""

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^DA-SF-\d{4}$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)
    name: str

    bda_speckle_type: Literal[_BDA_TYPE_SURFACE_FIXED] = Field(..., frozen=True)

    properties: SurfaceFixedDeckAppurtenanceProperties

    @classmethod
    def create(
        cls,
        name: str,
        application_id: str,
        appurtenance_id: str,
        element_index: int,
        appurtenance_type: DeckAppurtenanceTypeParaModel,
        material_id: str,
        width: float,
        thickness_left: float,
        thickness_right: float,
    ) -> "SurfaceFixedDeckAppurtenance":
        return cls(
            applicationId=application_id,
            name=name,
            bda_speckle_type=_BDA_TYPE_SURFACE_FIXED,
            properties=SurfaceFixedDeckAppurtenanceProperties(
                **{
                    "Appurtenance ID": AppurtenanceIdParameter(isUser=True, provided_value=appurtenance_id),
                    "Element Index": ElementIndexParameter(isUser=True, provided_value=element_index),
                    "Appurtenance Type": AppurtenanceTypeParameter(isUser=True, provided_value=appurtenance_type),
                    "Material ID": MaterialIdParameter(isUser=True, provided_value=material_id),
                    "Width": WidthParameter(isUser=True, provided_value=width),
                    "Positioned By": PositionedByParameter_Fixed(isUser=True),
                    "Geometry Type": GeometryTypeParameter_Surface(isUser=True),
                    "Thickness Left": ThicknessLeftParameter(isUser=True, provided_value=thickness_left),
                    "Thickness Right": ThicknessRightParameter(isUser=True, provided_value=thickness_right),
                }
            ),
        )


class LinearByOffsetDeckAppurtenance(BridgeDataObject):
    """Linear cross-section appurtenance placed by a transverse offset from centreline."""

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^DA-LO-\d{4}$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)
    name: str

    bda_speckle_type: Literal[_BDA_TYPE_LINEAR_BY_OFFSET] = Field(..., frozen=True)

    properties: LinearByOffsetDeckAppurtenanceProperties

    @classmethod
    def create(
        cls,
        name: str,
        application_id: str,
        appurtenance_id: str,
        element_index: int,
        appurtenance_type: DeckAppurtenanceTypeParaModel,
        material_id: str,
        width: float,
        height: float,
        outline: list[float | None],
        offset: float,
    ) -> "LinearByOffsetDeckAppurtenance":
        return cls(
            applicationId=application_id,
            name=name,
            bda_speckle_type=_BDA_TYPE_LINEAR_BY_OFFSET,
            properties=LinearByOffsetDeckAppurtenanceProperties(
                **{
                    "Appurtenance ID": AppurtenanceIdParameter(isUser=True, provided_value=appurtenance_id),
                    "Element Index": ElementIndexParameter(isUser=True, provided_value=element_index),
                    "Appurtenance Type": AppurtenanceTypeParameter(isUser=True, provided_value=appurtenance_type),
                    "Material ID": MaterialIdParameter(isUser=True, provided_value=material_id),
                    "Width": WidthParameter(isUser=True, provided_value=width),
                    "Positioned By": PositionedByParameter_ByOffset(isUser=True),
                    "Geometry Type": GeometryTypeParameter_Linear(isUser=True),
                    "Height": HeightParameter(isUser=True, provided_value=height),
                    "Outline": OutlineParameter(isUser=True, provided_value=outline),
                    "Offset": OffsetParameter(isUser=True, provided_value=offset),
                }
            ),
        )


class SurfaceByOffsetDeckAppurtenance(BridgeDataObject):
    """Surface cross-section appurtenance placed by a transverse offset from centreline."""

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^DA-SO-\d{4}$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)
    name: str

    bda_speckle_type: Literal[_BDA_TYPE_SURFACE_BY_OFFSET] = Field(..., frozen=True)

    properties: SurfaceByOffsetDeckAppurtenanceProperties

    @classmethod
    def create(
        cls,
        name: str,
        application_id: str,
        appurtenance_id: str,
        element_index: int,
        appurtenance_type: DeckAppurtenanceTypeParaModel,
        material_id: str,
        width: float,
        thickness_left: float,
        thickness_right: float,
        offset: float,
    ) -> "SurfaceByOffsetDeckAppurtenance":
        return cls(
            applicationId=application_id,
            name=name,
            bda_speckle_type=_BDA_TYPE_SURFACE_BY_OFFSET,
            properties=SurfaceByOffsetDeckAppurtenanceProperties(
                **{
                    "Appurtenance ID": AppurtenanceIdParameter(isUser=True, provided_value=appurtenance_id),
                    "Element Index": ElementIndexParameter(isUser=True, provided_value=element_index),
                    "Appurtenance Type": AppurtenanceTypeParameter(isUser=True, provided_value=appurtenance_type),
                    "Material ID": MaterialIdParameter(isUser=True, provided_value=material_id),
                    "Width": WidthParameter(isUser=True, provided_value=width),
                    "Positioned By": PositionedByParameter_ByOffset(isUser=True),
                    "Geometry Type": GeometryTypeParameter_Surface(isUser=True),
                    "Thickness Left": ThicknessLeftParameter(isUser=True, provided_value=thickness_left),
                    "Thickness Right": ThicknessRightParameter(isUser=True, provided_value=thickness_right),
                    "Offset": OffsetParameter(isUser=True, provided_value=offset),
                }
            ),
        )


# ---------------------------------------------------------------------------
# Discriminated union for use in collection elements
# ---------------------------------------------------------------------------

DeckAppurtenanceByOffest = Annotated[
    Union[
        LinearByOffsetDeckAppurtenance,
        SurfaceByOffsetDeckAppurtenance,
    ],
    Field(discriminator="bda_speckle_type"),
]

DeckAppurtenance = Annotated[
    Union[
        LinearFixedDeckAppurtenance,
        SurfaceFixedDeckAppurtenance,
        LinearByOffsetDeckAppurtenance,
        SurfaceByOffsetDeckAppurtenance,
    ],
    Field(discriminator="bda_speckle_type"),
]
