from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes
from typing import Annotated, ClassVar, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bda.contracts.paramodel.groups.enums import (
    ElementOrientationParaModel,
    StructuralComponentTypeParaModel,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.geometry_group_base import (
    GeometryGroupBase,
    GeometryGroupParameters,
    GeometryGroupProperties,
    GeometryGroupParameterProperties,
    StructureComponentGroupType,
)

from bda.contracts.speckle_contracts.base_objects import (
    ParameterGroup,
    UnitlessParameter,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.shared_parameters.geometry_group_taper_details import (
    TaperedDetailsParameterGroup,
)

from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_longitudinal_members import GeometryGroupLongitudinalMembers
from bda.contracts.speckle_contracts.bda_analytical.geometry.component_type_groups.geometry_group_transverse_members import GeometryGroupTransverseMembers
from bda.contracts.speckle_contracts.unit_parameters import LengthParameter

# =============================================================================
# DETAIL PARAMETERS
# =============================================================================

class SpliceSectionIdParameter(UnitlessParameter[str]):
    name: Literal["Section ID"] = "Section ID"

    description: Literal[
        "Section identifier for splice"
    ] = "Section identifier for splice"

    symbol: None = None

    provided_value: str




# =============================================================================
# CONSTRUCTION SEQUENCE PARAMETER GROUPS
# =============================================================================

class PouringOrientationParameter(
    UnitlessParameter[ElementOrientationParaModel]
):
    name: Literal[
        "Pouring Orientation"
    ] = "Pouring Orientation"

    description: Literal[
        "Pouring orientation of construction sequence"
    ] = "Pouring orientation of construction sequence"

    symbol: None = None

    provided_value: ElementOrientationParaModel


class ConstructionSequenceSegmentXStartParameter(LengthParameter):
    name: Literal[
        "Construction Sequence Segment X Start"
    ] = "Construction Sequence Segment X Start"

    description: Literal[
        "Start x-coordinate of construction sequence segment"
    ] = "Start x-coordinate of construction sequence segment"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class ConstructionSequenceSegmentXEndParameter(LengthParameter):
    name: Literal[
        "Construction Sequence Segment X End"
    ] = "Construction Sequence Segment X End"

    description: Literal[
        "End x-coordinate of construction sequence segment"
    ] = "End x-coordinate of construction sequence segment"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


# =============================================================================
# CONSTRUCTION SEQUENCE SEGMENT
# =============================================================================

class ConstructionSequenceSegmentDetailsGroupParameters(
    BaseModel
):
    x_start: ConstructionSequenceSegmentXStartParameter = (
        Field(
            alias="Construction Sequence Segment X Start"
        )
    )

    x_end: ConstructionSequenceSegmentXEndParameter = (
        Field(
            alias="Construction Sequence Segment X End"
        )
    )


class ConstructionSequenceSegmentDetailsParameterGroup(
    ParameterGroup
):
    name: Literal[
        "Construction Sequence Segment Details"
    ] = "Construction Sequence Segment Details"

    description: Literal[
        "Construction sequence segment details"
    ] = "Construction sequence segment details"

    symbol: None = None

    group_parameters: (
        ConstructionSequenceSegmentDetailsGroupParameters
    )

    @classmethod
    def create(
        cls,
        x_start: float,
        x_end: float,
        x_start_unit: Literal["m", "ft"] = "m",
        x_end_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "ConstructionSequenceSegmentDetailsParameterGroup":

        return cls(
            isUser=isUser,
            group_parameters=(
                ConstructionSequenceSegmentDetailsGroupParameters(
                    **{
                        "Construction Sequence Segment X Start":
                            ConstructionSequenceSegmentXStartParameter(
                                isUser=isUser,
                                provided_value=x_start,
                                provided_unit=x_start_unit,
                                base_value=x_start,
                            ),

                        "Construction Sequence Segment X End":
                            ConstructionSequenceSegmentXEndParameter(
                                isUser=isUser,
                                provided_value=x_end,
                                provided_unit=x_end_unit,
                                base_value=x_end,
                            ),
                    }
                )
            ),
        )


# =============================================================================
# CONSTRUCTION SEQUENCE DETAILS
# =============================================================================

class ConstructionSequenceDetailsGroupParameters(
    BaseModel
):
    pouring_orientation: (
        PouringOrientationParameter
    ) = Field(
        alias="Pouring Orientation"
    )

    construction_sequence_segments: dict[
        str,
        ConstructionSequenceSegmentDetailsParameterGroup,
    ] = Field(
        alias="Construction Sequence Segments",
        min_length=1,
    )


class ConstructionSequenceDetailsParameterGroup(
    ParameterGroup
):
    name: Literal[
        "Construction Sequence Details"
    ] = "Construction Sequence Details"

    description: Literal[
        "Construction sequence details"
    ] = "Construction sequence details"

    symbol: None = None

    group_parameters: (
        ConstructionSequenceDetailsGroupParameters
    )

    @classmethod
    def create(
        cls,
        segments: list[tuple[float, float]],
        pouring_orientation: (
            ElementOrientationParaModel
        ),
        segment_units: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "ConstructionSequenceDetailsParameterGroup":

        return cls(
            isUser=isUser,
            group_parameters=(
                ConstructionSequenceDetailsGroupParameters(
                    **{
                        "Pouring Orientation":
                            PouringOrientationParameter(
                                isUser=isUser,
                                provided_value=(
                                    pouring_orientation
                                ),
                            ),

                        "Construction Sequence Segments":
                            {
                                (
                                    f"Construction Sequence Segment "
                                    f"{i + 1}"
                                ):
                                    ConstructionSequenceSegmentDetailsParameterGroup.create(
                                        isUser=isUser,
                                        x_start=x_start,
                                        x_end=x_end,
                                        x_start_unit=segment_units,
                                        x_end_unit=segment_units,
                                    )
                                for i, (x_start, x_end)
                                in enumerate(segments)
                            },
                    }
                )
            ),
        )

# =============================================================================
# CRACKED EXTENT PARAMETER GROUPS
# =============================================================================

class CrackedExtentsXStartParameter(LengthParameter):
    name: Literal["Cracked Extent X Start"] = "Cracked Extent X Start"

    description: Literal[
        "Start x-coordinate of cracked extent"
    ] = "Start x-coordinate of cracked extent"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class CrackedExtentsXEndParameter(LengthParameter):
    name: Literal[
        "Cracked Extent X End"
    ] = "Cracked Extent X End"

    description: Literal[
        "End x-coordinate of cracked extent"
    ] = "End x-coordinate of cracked extent"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class CrackedExtentDetailsGroupParameters(BaseModel):
    x_start: CrackedExtentsXStartParameter = Field(
        alias="Cracked Extent X Start"
    )

    x_end: CrackedExtentsXEndParameter = Field(
        alias="Cracked Extent X End"
    )


class CrackedExtentDetailsParameterGroup(ParameterGroup):
    name: Literal[
        "Cracked Extent Details"
    ] = "Cracked Extent Details"

    description: Literal[
        "Cracked extent details"
    ] = "Cracked extent details"

    symbol: None = None

    group_parameters: CrackedExtentDetailsGroupParameters

    @classmethod
    def create(
        cls,
        x_start: float,
        x_end: float,
        x_start_unit: Literal["m", "ft"] = "m",
        x_end_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "CrackedExtentDetailsParameterGroup":

        return cls(
            isUser=isUser,
            group_parameters=CrackedExtentDetailsGroupParameters(
                **{
                    "Cracked Extent X Start":
                        CrackedExtentsXStartParameter(
                            isUser=isUser,
                            provided_value=x_start,
                            provided_unit=x_start_unit,
                            base_value=x_start,
                        ),

                    "Cracked Extent X End":
                        CrackedExtentsXEndParameter(
                            isUser=isUser,
                            provided_value=x_end,
                            provided_unit=x_end_unit,
                            base_value=x_end,
                        ),
                }
            )
        )


class CrackedExtentsParameterGroup(ParameterGroup):
    name: Literal["Cracked Extents"] = "Cracked Extents"

    description: Literal[
        "Cracked extents along the span"
    ] = "Cracked extents along the span"

    symbol: None = None

    group_parameters: dict[
        str,
        CrackedExtentDetailsParameterGroup,
    ] = Field(
        ...,
        min_length=1,
    )

    @classmethod
    def create(
        cls,
        extents: list[tuple[float, float]],
        extents_units: Literal["m", "ft"] = "m",
        isUser: bool = True
    ) -> "CrackedExtentsParameterGroup":

        return cls(
            isUser=isUser,
            group_parameters={
                f"Cracked Extent {i+1}":
                    CrackedExtentDetailsParameterGroup.create(
                        isUser=isUser,
                        x_start=x_start,
                        x_end=x_end,
                        x_end_unit=extents_units,
                        x_start_unit=extents_units
                    )
                for i, (x_start, x_end)
                in enumerate(extents)
            }
        )

# =============================================================================
# SPLICE PARAMETER GROUPS
# =============================================================================


class SpliceDetailsGroupParameters(BaseModel):
    x_start: CrackedExtentsXStartParameter = Field(
        alias="Segment X Start"
    )

    section_id: SpliceSectionIdParameter = Field(
        alias="Section ID"
    )


class SpliceDetailsParameterGroup(ParameterGroup):
    name: Literal["Splice Details"] = "Splice Details"

    description: Literal[
        "Splice detail"
    ] = "Splice detail"

    symbol: None = None

    group_parameters: SpliceDetailsGroupParameters

    @classmethod
    def create(
        cls,
        x_start: float,
        section_id: str,
        x_start_unit: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "SpliceDetailsParameterGroup":

        return cls(
            isUser=isUser,
            group_parameters=SpliceDetailsGroupParameters(
                **{
                    "Segment X Start":
                        CrackedExtentsXStartParameter(
                            isUser=isUser,
                            provided_value=x_start,
                            provided_unit=x_start_unit,
                            base_value=x_start,
                        ),

                    "Section ID":
                        SpliceSectionIdParameter(
                            isUser=isUser,
                            provided_value=section_id,
                        ),
                }
            )
        )


class SplicesParameterGroup(ParameterGroup):
    name: Literal["Splices"] = "Splices"

    description: Literal[
        "Splice locations along the span"
    ] = "Splice locations along the span"

    symbol: None = None

    group_parameters: dict[
        str,
        SpliceDetailsParameterGroup,
    ] = Field(
        ...,
        min_length=1,
    )

    @classmethod
    def create(
        cls,
        splices: list[tuple[float, str]],
        splice_units: Literal["m", "ft"] = "m",
        isUser: bool = True,
    ) -> "SplicesParameterGroup":

        return cls(
            isUser=isUser,
            group_parameters={
                f"Splice {i + 1}":
                    SpliceDetailsParameterGroup.create(
                        isUser=isUser,
                        x_start=x_start,
                        section_id=section_id,
                        x_start_unit=splice_units,
                    )
                for i, (x_start, section_id)
                in enumerate(splices)
            }
        )




# =============================================================================
# SPAN PARAMETERS
# =============================================================================


class SpanIndexParameter(UnitlessParameter[int]):
    name: Literal["Span Index"] = "Span Index"

    description: Literal[
        "Index of the span"
    ] = "Index of the span"

    symbol: None = None

    provided_value: int


class SpanLengthParameter(LengthParameter):
    name: Literal["Span Length"] = "Span Length"

    description: Literal[
        "Length of the span"
    ] = "Length of the span"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


class TopDeckLevelAtEndParameter(LengthParameter):
    name: Literal[
        "Top Deck Level At End"
    ] = "Top Deck Level At End"

    description: Literal[
        "Top deck level at the end of the span"
    ] = "Top deck level at the end of the span"

    symbol: None = None

    provided_unit: Literal["m", "ft"]

    base_unit: Literal["m"] = "m"


# =============================================================================
# SPAN PROPERTY SET
# =============================================================================


class SpanGroupPropertiesParameters(BaseModel):
    span_index: SpanIndexParameter = Field(
        alias="Span Index"
    )

    span_length: SpanLengthParameter = Field(
        alias="Span Length"
    )

    top_deck_level_at_end: TopDeckLevelAtEndParameter = Field(
        alias="Top Deck Level At End"
    )

    cracked_extents: CrackedExtentsParameterGroup | None = Field(
        default=None,
        alias="Cracked Extents",
    )

    tapered_details: TaperedDetailsParameterGroup | None = Field(
        default=None,
        alias="Tapered Details",
    )

    splices: SplicesParameterGroup | None = Field(
        default=None,
        alias="Splices",
    )

    construction_sequence_details: (
        ConstructionSequenceDetailsParameterGroup | None
    ) = Field(
        default=None,
        alias="Construction Sequence Details",
    )

class SpanGroupProperties(
    GeometryGroupParameterProperties
):
    group_parameters: (
        SpanGroupPropertiesParameters
    )

    @classmethod
    def create(
        cls,
        span_index: int,
        span_length: float,
        top_deck_level_at_end: float,
        span_length_unit: Literal["m", "ft"] = "m",
        top_deck_level_at_end_unit: Literal["m", "ft"] = "m",
        cracked_extents: CrackedExtentsParameterGroup | None = None,
        tapered_details: TaperedDetailsParameterGroup | None = None,
        splices: SplicesParameterGroup | None = None,
        construction_sequence_details: (
            ConstructionSequenceDetailsParameterGroup | None
        ) = None,
        isUser: bool = True,
    ) -> "SpanGroupProperties":

        group_parameters = {
            "Span Index":
                SpanIndexParameter(
                    isUser=isUser,
                    provided_value=span_index,
                ),

            "Span Length":
                SpanLengthParameter(
                    isUser=isUser,
                    provided_value=span_length,
                    provided_unit=span_length_unit,
                    base_value=span_length,
                ),

            "Top Deck Level At End":
                TopDeckLevelAtEndParameter(
                    isUser=isUser,
                    provided_value=top_deck_level_at_end,
                    provided_unit=top_deck_level_at_end_unit,
                    base_value=top_deck_level_at_end,
                ),
        }

        if cracked_extents is not None:
            group_parameters[
                "Cracked Extents"
            ] = cracked_extents

        if tapered_details is not None:
            group_parameters[
                "Tapered Details"
            ] = tapered_details

        if splices is not None:
            group_parameters[
                "Splices"
            ] = splices

        if construction_sequence_details is not None:
            group_parameters[
                "Construction Sequence Details"
            ] = construction_sequence_details

        return cls(
            isUser=isUser,
            group_parameters=(
                SpanGroupPropertiesParameters(
                    **group_parameters
                )
            ),
        )


# =============================================================================
# GROUP TYPE IDENTIFICATION
# =============================================================================


class SpanStructureComponentGroupType(
    StructureComponentGroupType
):
    provided_value: Literal[
        StructuralComponentTypeParaModel.SPAN
    ] = StructuralComponentTypeParaModel.SPAN


# =============================================================================
# COMMON SPAN METADATA
# =============================================================================


class GeometryGroupPropertiesSpan(
    GeometryGroupProperties
):
    structural_component_type: (
        SpanStructureComponentGroupType
    ) = Field(
        alias="Structural Component Type"
    )

    group_properties: SpanGroupProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParametersSpan(
    GeometryGroupParameters
):
    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_SPAN
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES_SPAN.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^GEOMGROUP-PROPS-\d{4}-SPAN$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    properties: GeometryGroupPropertiesSpan


# =============================================================================
# SPAN GROUP
# =============================================================================

SpanGroupElements = Annotated[
    Union[
        GeometryGroupParametersSpan,
        GeometryGroupLongitudinalMembers,
        GeometryGroupTransverseMembers,
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupSpan(
    GeometryGroupBase
):
    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_SPAN
    ] = Field(SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP_SPAN.value, frozen=True)

    APPLICATION_ID_PATTERN: ClassVar[str] = r"^COL-GEOMGROUP-\d{4}-SPAN$"
    applicationId: str = Field(pattern=APPLICATION_ID_PATTERN)

    elements: list[SpanGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    # Exactly one span properties object
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties_Span"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                },
                {
                    # Optional longitudinal members group
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Longitudinal_Members"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
                {
                    # Optional transverse members group
                    "contains": {
                        "type": "object",
                        "properties": {
                            "bda_speckle_type": {
                                "const": (
                                    "Speckle.Core.Models.Collections.Collection:"
                                    "BDA_Geometry_Group_Transverse_Members"
                                )
                            }
                        },
                        "required": ["bda_speckle_type"],
                    },
                    "minContains": 0,
                    "maxContains": 1,
                },
            ],
        },
    )

    @model_validator(mode="after")
    def validate_span_elements(self) -> "GeometryGroupSpan":

        span_properties_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type
            == (
                "Objects.Data.DataObject:"
                "BDA_Geometry_Group_Properties_Span"
            )
        )

        longitudinal_members_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type
            == (
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Longitudinal_Members"
            )
        )

        transverse_members_count = sum(
            1
            for element in self.elements
            if element.bda_speckle_type
            == (
                "Speckle.Core.Models.Collections.Collection:"
                "BDA_Geometry_Group_Transverse_Members"
            )
        )

        if span_properties_count != 1:
            raise ValueError(
                "GeometryGroupSpan.elements must contain exactly one "
                "BDA_Geometry_Group_Properties_Span object. "
                f"Found {span_properties_count}."
            )

        if longitudinal_members_count > 1:
            raise ValueError(
                "GeometryGroupSpan.elements may contain at most one "
                "BDA_Geometry_Group_Longitudinal_Members collection. "
                f"Found {longitudinal_members_count}."
            )

        if transverse_members_count > 1:
            raise ValueError(
                "GeometryGroupSpan.elements may contain at most one "
                "BDA_Geometry_Group_Transverse_Members collection. "
                f"Found {transverse_members_count}."
            )

        return self

    @classmethod
    def create(
        cls,
        span_index: int,
        span_length: float,
        top_deck_level_at_end: float,
        span_length_unit: Literal["m", "ft"] = "m",
        top_deck_level_at_end_unit: Literal["m", "ft"] = "m",
        longitudinal_members: (
            GeometryGroupLongitudinalMembers | None
        ) = None,
        transverse_members: (
            GeometryGroupTransverseMembers | None
        ) = None,
        cracked_extents: CrackedExtentsParameterGroup | None = None,
        tapered_details: TaperedDetailsParameterGroup | None = None,
        splices: SplicesParameterGroup | None = None,
        construction_sequence_details: (
            ConstructionSequenceDetailsParameterGroup | None
        ) = None,
        application_id: str = "COL-GEOMGROUP-0001-SPAN",
        name: str = "Span",
        isUser: bool = True,
    ) -> "GeometryGroupSpan":
        elements: list[SpanGroupElements] = [
            GeometryGroupParametersSpan(
                **{
                    "id": None,
                    "applicationId": application_id.replace(
                        "COL-GEOMGROUP-", "GEOMGROUP-PROPS-", 1
                    ),
                    "properties": GeometryGroupPropertiesSpan(
                        **{
                            "Structural Component Type":
                                SpanStructureComponentGroupType(),

                            "Geometry Group Properties":
                                SpanGroupProperties.create(
                                    span_index=span_index,
                                    span_length=span_length,
                                    top_deck_level_at_end=(
                                        top_deck_level_at_end
                                    ),
                                    span_length_unit=(
                                        span_length_unit
                                    ),
                                    top_deck_level_at_end_unit=(
                                        top_deck_level_at_end_unit
                                    ),
                                    cracked_extents=(
                                        cracked_extents
                                    ),
                                    tapered_details=(
                                        tapered_details
                                    ),
                                    splices=splices,
                                    construction_sequence_details=(
                                        construction_sequence_details
                                    ),
                                    isUser=isUser,
                                ),
                        }
                    ),
                }
            )
        ]

        if longitudinal_members is not None:
            elements.append(longitudinal_members)

        if transverse_members is not None:
            elements.append(transverse_members)

        return cls(
            id=None,
            applicationId=application_id,
            name=name,
            elements=elements,
        )
    
if __name__ == "__main__":

    tapered_details = (
        TaperedDetailsParameterGroup.create(
            tapers=[
                (
                    0.0,
                    12.0,
                    "SEC_1",
                ),
                (
                    12.0,
                    25.0,
                    "SEC_2",
                ),
                (
                    25.0,
                    40.0,
                    "SEC_3",
                ),
            ],
            taper_units="m",
        )
    )

    cracked_extents = (
        CrackedExtentsParameterGroup.create(
            extents=[
                (
                    5.0,
                    8.0,
                ),
                (
                    17.0,
                    21.0,
                ),
            ],
            extents_units="m",
        )
    )

    construction_sequence_details = (
        ConstructionSequenceDetailsParameterGroup.create(
            pouring_orientation=
            ElementOrientationParaModel.SKEWED,
            segments=[
                (
                    0.0,
                    10.0,
                ),
                (
                    10.0,
                    20.0,
                ),
                (
                    20.0,
                    30.0,
                ),
                (
                    30.0,
                    40.0,
                ),
            ],
            segment_units="m",
        )
    )

    span = GeometryGroupSpan.create(
        span_index=1,
        span_length=40.0,
        top_deck_level_at_end=10.0,

        tapered_details=
        tapered_details,

        cracked_extents=
        cracked_extents,

        construction_sequence_details=
        construction_sequence_details,

        application_id="COL-GEOMGROUP-0001-SPAN",
    )

    print(
        span.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )