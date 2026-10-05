from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import ConfigDict, Field

from bda.contracts.speckle_contracts.base_objects import (
    Parameter,
    EnumParameter,
    UnitlessParameter,
    DataObjectSpeckleType,
    BridgeDataObject,
    BridgeDataObjectProperties,
    BridgeCollection,
    iter_bridges_objects,
)

from bda.contracts.paramodel.sections.sections_para_models import (
    SectionFamilyParaModel,
    SectionTypeParaModel,
    TaperVariationParaModel
    
)

# ==========================================================
# SECTION REFERENCE PARAMETERS
# ==========================================================

class SectionStartIdParameter(UnitlessParameter[str]):
    name: Literal["Section Start ID"] = "Section Start ID"
    description: Literal[
        "Reference to the start section object by applicationId"
    ] = "Reference to the start section object by applicationId"
    provided_value: str


class SectionEndIdParameter(UnitlessParameter[str]):
    name: Literal["Section End ID"] = "Section End ID"
    description: Literal[
        "Reference to the end section object by applicationId"
    ] = "Reference to the end section object by applicationId"
    provided_value: str


# ==========================================================
# TAPER VARIATION PARAMETERS
# ==========================================================

class TaperYVariationParameter(EnumParameter[TaperVariationParaModel]):
    name: Literal["Taper Y Variation"] = "Taper Y Variation"
    description: Literal[
        "Interpolation rule for tapering in local Y"
    ] = "Interpolation rule for tapering in local Y"
    provided_value: TaperVariationParaModel


class TaperZVariationParameter(EnumParameter[TaperVariationParaModel]):
    name: Literal["Taper Z Variation"] = "Taper Z Variation"
    description: Literal[
        "Interpolation rule for tapering in local Z"
    ] = "Interpolation rule for tapering in local Z"
    provided_value: TaperVariationParaModel


# ==========================================================
# Fixed Parameters TYPE
# ==========================================================

class TaperedSectionDataObjectSpeckleType(DataObjectSpeckleType):
    provided_value: Literal[
        "Objects.Data.DataObject:BDA_Section:Tapered"
    ] = "Objects.Data.DataObject:BDA_Section:Tapered"


# ==========================================================
# OPTIONAL DESCRIPTOR PARAMETERS
# ==========================================================

class SectionFamilyParameter_Tapered(UnitlessParameter[str]):
    name: Literal["Section Family"] = "Section Family"
    description: Literal[
        "Family of the section (e.g., Standard Shape, Composite, PSC)"
    ] = "Family of the section (e.g., Standard Shape, Composite, PSC)"
    isUser: bool = True
    provided_value: SectionFamilyParaModel = SectionFamilyParaModel.TAPERED


class SectionTypeParameter_Tapered(UnitlessParameter[str]):
    name: Literal["Section Type"] = "Section Type"
    description: Literal[
        "Type of the section (e.g., I-Section, T-Section, Box Section)"
    ] = "Type of the section (e.g., I-Section, T-Section, Box Section)"
    isUser: bool = True
    provided_value: SectionTypeParaModel


# ==========================================================
# PROPERTIES
# ==========================================================

class TaperedSectionDataObject_Properties(BridgeDataObjectProperties):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)
    bda_speckle_type: TaperedSectionDataObjectSpeckleType
    section_family: SectionFamilyParameter_Tapered = Field(alias="Section Family")
    section_type: SectionTypeParameter_Tapered = Field(alias="Section Type")
    section_start_id: SectionStartIdParameter = Field(alias="Section Start ID")
    section_end_id: SectionEndIdParameter = Field(alias="Section End ID")
    taper_y_variation: TaperYVariationParameter = Field(alias="Taper Y Variation")
    taper_z_variation: TaperZVariationParameter = Field(alias="Taper Z Variation")


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class SectionDataObject_Tapered(BridgeDataObject):
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Tapered"
    ] = "Objects.Data.DataObject:BDA_Section:Tapered"

    properties: TaperedSectionDataObject_Properties


# ==========================================================
# COLLECTION-LEVEL VALIDATION HELPER
# ==========================================================

def validate_tapered_section_references(collection: BridgeCollection) -> None:
    """
    Validate all tapered section objects inside a collection.

    Rules:
    - Section Start ID must reference an existing object.applicationId
    - Section End ID must reference an existing object.applicationId
    - Start and End referenced objects must have identical speckle_type
    """

    objects_by_application_id = {
        obj.applicationId: obj
        for obj in iter_bridges_objects(collection)
        if obj.applicationId is not None
    }

    for obj in objects_by_application_id.values():
        if not isinstance(obj, BridgeDataObject):
            continue

        if obj.speckle_type != "Objects.Data.DataObject:BDA_Section:Tapered":
            continue

        props = obj.properties
        start_id = props.section_start_id.provided_value
        end_id = props.section_end_id.provided_value

        if start_id not in objects_by_application_id:
            raise ValueError(
                "Tapered section validation failed.\n"
                f"Tapered object applicationId: {obj.applicationId}\n"
                f"Missing start section applicationId: {start_id}"
            )

        if end_id not in objects_by_application_id:
            raise ValueError(
                "Tapered section validation failed.\n"
                f"Tapered object applicationId: {obj.applicationId}\n"
                f"Missing end section applicationId: {end_id}"
            )

        start_obj = objects_by_application_id[start_id]
        end_obj = objects_by_application_id[end_id]

        if start_obj.speckle_type != end_obj.speckle_type:
            raise ValueError(
                "Tapered section validation failed.\n"
                f"Tapered object applicationId: {obj.applicationId}\n"
                f"Start section applicationId: {start_id}\n"
                f"End section applicationId: {end_id}\n"
                f"Start speckle_type: {start_obj.speckle_type}\n"
                f"End speckle_type: {end_obj.speckle_type}\n"
                "Start and End sections must have identical speckle_type."
            )
