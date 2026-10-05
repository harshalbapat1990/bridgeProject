from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes
import re
from typing import Annotated, ClassVar, Literal, Union

from pydantic import Field, ConfigDict, field_validator

from bda.contracts.paramodel.groups.enums import StructuralComponentTypeParaModel
from bda.contracts.speckle_contracts.base_objects import (
    BridgeCollection,
    BridgeDataObject,
    BridgeDataObjectProperties,
    Geometry,
    ParameterGroup,
    UnitlessParameter,
)


# =============================================================================
# TODO: IMPLEMENT MODEL ELEMENTS AFTER MVP
# =============================================================================

# class GeometryElementBase(BridgeDataObject):
#     name: str = "Geometry Element"
#     speckle_type: Literal[
#         "Objects.Data.DataObject:BDA_Geometry_Element"
#     ] = "Objects.Data.DataObject:BDA_Geometry_Element"


# =============================================================================
# TYPES
# =============================================================================


# =============================================================================
# COMMON PARAMETERS
# =============================================================================


class StructureComponentGroupType(
    UnitlessParameter[StructuralComponentTypeParaModel]
):
    name: Literal["Structural Component Type"] = "Structural Component Type"

    description: Literal[
        "Type of structural component "
        "(e.g., Girder, Deck, Abutment, Pier, Bearing, etc.)"
    ] = (
        "Type of structural component "
        "(e.g., Girder, Deck, Abutment, Pier, Bearing, etc.)"
    )

    symbol: None = None
    isUser: bool = False

    provided_value: StructuralComponentTypeParaModel


from typing import Literal, TypeAlias, Union

from bda.contracts.speckle_contracts.base_objects import (
    UnitlessParameter,
)


# =============================================================================
# COMMON ID PARAMETERS
# =============================================================================


class MaterialIdNone(UnitlessParameter[None]):
    name: Literal["Material ID"] = "Material ID"

    description: Literal[
        "No material is assigned to this geometry group"
    ] = "No material is assigned to this geometry group"

    symbol: None = None

    provided_value: Literal[None] = None
    provided_unit: None = None
    base_unit: None = None
    base_value: None = None


class MaterialIdString(UnitlessParameter[str]):
    name: Literal["Material ID"] = "Material ID"

    description: Literal[
        "applicationId of assigned material"
    ] = "applicationId of assigned material"

    symbol: None = None

    isUser: bool = True

    provided_value: str
    provided_unit: None = None
    base_unit: None = None
    base_value: None = None


class SectionIdNone(UnitlessParameter[None]):
    name: Literal["Section ID"] = "Section ID"

    description: Literal[
        "No section is assigned to this geometry group"
    ] = "No section is assigned to this geometry group"

    symbol: None = None

    provided_value: Literal[None] = None
    provided_unit: None = None
    base_unit: None = None
    base_value: None = None


class SectionIdString(UnitlessParameter[str]):
    name: Literal["Section ID"] = "Section ID"

    description: Literal[
        "applicationId of assigned section"
    ] = "applicationId of assigned section"

    symbol: None = None

    isUser: bool = True

    provided_value: str
    provided_unit: None = None
    base_unit: None = None
    base_value: None = None


# =============================================================================
# MATERIAL / SECTION ID SCHEMA OPTIONS
# =============================================================================
#
# Use these aliases in geometry group property models depending on whether
# material / section assignment is required, optional, or not applicable.
#
# 1. Required:
#       material_id: MaterialIdRequired
#       section_id: SectionIdRequired
#
# 2. Optional:
#       material_id: MaterialIdOptional
#       section_id: SectionIdOptional
#
# 3. Not applicable:
#       material_id: MaterialIdNotRequired
#       section_id: SectionIdNotRequired
# =============================================================================


# -----------------------------------------------------------------------------
# 1. ALWAYS NEEDED
# -----------------------------------------------------------------------------

MaterialIdRequired: TypeAlias = MaterialIdString
SectionIdRequired: TypeAlias = SectionIdString


# -----------------------------------------------------------------------------
# 2. OPTIONAL
# -----------------------------------------------------------------------------

MaterialIdOptional: TypeAlias = Union[
    MaterialIdString,
    MaterialIdNone,
]

SectionIdOptional: TypeAlias = Union[
    SectionIdString,
    SectionIdNone,
]


# -----------------------------------------------------------------------------
# 3. NEVER NEEDED
# -----------------------------------------------------------------------------

MaterialIdNotRequired: TypeAlias = MaterialIdNone
SectionIdNotRequired: TypeAlias = SectionIdNone


# =============================================================================
# MATERIAL / SECTION ID FACTORY HELPERS
# =============================================================================


# -----------------------------------------------------------------------------
# 1. ALWAYS NEEDED
# -----------------------------------------------------------------------------


def create_required_material_id(
    material_id: str,
    isUser: bool = True,
) -> MaterialIdRequired:
    return MaterialIdString(
        isUser=isUser,
        provided_value=material_id,
    )


def create_required_section_id(
    section_id: str,
    isUser: bool = True,
) -> SectionIdRequired:
    return SectionIdString(
        isUser=isUser,
        provided_value=section_id,
    )


# -----------------------------------------------------------------------------
# 2. OPTIONAL
# -----------------------------------------------------------------------------


def create_optional_material_id(
    material_id: str | None,
    isUser: bool = True,
) -> MaterialIdOptional:
    if material_id is None:
        return MaterialIdNone(
            isUser=isUser,
            provided_value=None,
        )

    return MaterialIdString(
        isUser=isUser,
        provided_value=material_id,
    )


def create_optional_section_id(
    section_id: str | None,
    isUser: bool = True,
) -> SectionIdOptional:
    if section_id is None:
        return SectionIdNone(
            isUser=isUser,
            provided_value=None,
        )

    return SectionIdString(
        isUser=isUser,
        provided_value=section_id,
    )


# -----------------------------------------------------------------------------
# 3. NEVER NEEDED
# -----------------------------------------------------------------------------


def create_no_material_id(
    isUser: bool = False,
) -> MaterialIdNotRequired:
    return MaterialIdNone(
        isUser=isUser,
        provided_value=None,
    )


def create_no_section_id(
    isUser: bool = False,
) -> SectionIdNotRequired:
    return SectionIdNone(
        isUser=isUser,
        provided_value=None,
    )


# =============================================================================
# BACKWARDS-COMPATIBLE DEFAULT HELPERS
# =============================================================================
#
# These are retained so existing create methods that call
# default_material_id_none() / default_section_id_none() do not break.
# Prefer create_no_material_id() and create_no_section_id() for new code.
# =============================================================================


def default_material_id_none() -> MaterialIdNone:
    return create_no_material_id()


def default_section_id_none() -> SectionIdNone:
    return create_no_section_id()

# =============================================================================
# EXTENSION POINT FOR COMPONENT-SPECIFIC PROPERTIES
# =============================================================================


class GeometryGroupParameterProperties(ParameterGroup):
    """
    Base class for component-specific properties.

    Example implementations:

        GirderProperties(GeometryGroupParameterProperties)
        DeckProperties(GeometryGroupParameterProperties)
        PierProperties(GeometryGroupParameterProperties)
    """

    name: Literal["Geometry Group Properties"] = "Geometry Group Properties"

    description: Literal[
        "Properties of the geometry group"
    ] = "Properties of the geometry group"

    symbol: None = None


# =============================================================================
# COMMON GEOMETRY GROUP PROPERTIES
# =============================================================================


class GeometryGroupProperties(BridgeDataObjectProperties):

    structural_component_type: StructureComponentGroupType = Field(
        alias="Structural Component Type"
    )

    material_id: MaterialIdNone = Field(
        default_factory=default_material_id_none,
        alias="Material ID",
    )

    section_id: SectionIdNone = Field(
        default_factory=default_section_id_none,
        alias="Section ID",
    )

    group_properties: GeometryGroupParameterProperties = Field(
        alias="Geometry Group Properties"
    )


class GeometryGroupParameters(BridgeDataObject):
    """
    Mandatory child object that stores all metadata
    associated with a GeometryGroup.
    """
    GEOMETRY_GROUP_PROPERTIES_ID_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"^GEOMGROUP-PROPS-\d{4}-[A-Z0-9]+(?:-[A-Z0-9]+)*$"
    )

    name: Literal[
        "Geometry Group Properties"
    ] = "Geometry Group Properties"

    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES.value, frozen=True)

    properties: GeometryGroupProperties

    displayValue: list[Geometry] = Field(
        default_factory=list,
        frozen=True,
        description="Always empty for properties objects",
        json_schema_extra={"const": []},
    )

    @field_validator("applicationId")
    @classmethod
    def validate_geometry_group_application_id(
        cls,
        value: str,
    ):

        if not cls.GEOMETRY_GROUP_PROPERTIES_ID_PATTERN.match(value):
            raise ValueError(
                "Geometry group applicationId must match GEOMGROUP-PROPS-<id>-<ComponentType>"
            )

        return value


# =============================================================================
# GROUP HIERARCHY
# =============================================================================


GeometryGroupElements = Annotated[
    Union[
        GeometryGroupParameters,
        "GeometryGroupBase",
    ],
    Field(discriminator="bda_speckle_type"),
]


class GeometryGroupBase(BridgeCollection):
    """
    Base geometry group collection.

    Represents a hierarchical grouping of bridge geometry components. Unlike
    individual DataObjects (Materials, Config), geometry groups form a tree
    structure where each group can contain properties and nested child groups.

    This class uses BridgeCollection (not BridgeDataObject) because:
    - Geometry is hierarchical (Bridge > Superstructure > Span > Girder)
    - Each level contains metadata (properties) and children (nested groups)
    - Visualization (displayValue) is needed at collection level for Speckle

    Structure:
    - Exactly one GeometryGroupParameters child (metadata/properties).
    - Zero or more nested GeometryGroupBase children (sub-components).
    - Future GeometryElementBase children for individual geometric elements.

    Examples:
    - GeometryGroupBridge: root level, contains Superstructure + Substructure
    - GeometryGroupSpan: under Superstructure, contains member groups
    - GeometryGroupGirder: under Span, represents individual girder data
    """

    GEOMETRY_GROUP_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"^COL-GEOMGROUP-\d{4}-[A-Z0-9]+(?:-[A-Z0-9]+)*$"
    )

    bda_speckle_type: Literal[
        SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP
    ] = Field(SpeckleTypes.COLLECTION_BDA_GEOMETRY_GROUP.value, frozen=True)

    name: str
    
    elements: list[GeometryGroupElements] = Field(
        default_factory=list,
        json_schema_extra={
            "minItems": 1,
            "allOf": [
                {
                    "contains": {
                        "type": "object",
                        "properties": {
                            "speckle_type": {
                                "const": (
                                    "Objects.Data.DataObject:"
                                    "BDA_Geometry_Group_Properties"
                                )
                            }
                        },
                        "required": ["speckle_type"],
                    },
                    "minContains": 1,
                    "maxContains": 1,
                }
            ],
        },
    )

    @field_validator("applicationId")
    @classmethod
    def validate_geometry_group_application_id(
        cls,
        value: str,
    ):

        if not cls.GEOMETRY_GROUP_PATTERN.match(value):
            raise ValueError(
                "Geometry group applicationId must match COL-GEOMGROUP-<ID>-<ComponentType>"
            )

        return value


# Resolve forward references
GeometryGroupBase.model_rebuild()