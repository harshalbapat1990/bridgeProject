from __future__ import annotations

from enum import Enum
from typing import Literal, ClassVar

from pydantic import ConfigDict, Field

from bda.contracts.paramodel.sections.sections_para_models import (
    SectionFamilyParaModel,
    SectionTypeParaModel,
    TaperVariationParaModel,
)

from bda.contracts.speckle_contracts.base_objects import (
    BridgeDataObject,
    BridgeDataObjectProperties,
    UnitlessParameter,
    EnumParameter,
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
    APPLICATION_ID_PATTERN: ClassVar[str] = r"^SECT-[0-9]{4}-TAPERED$"
    applicationId: str = Field(
        pattern=APPLICATION_ID_PATTERN,
    )
    speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Tapered"
    ] = "Objects.Data.DataObject:BDA_Section:Tapered"

    bda_speckle_type: Literal[
        "Objects.Data.DataObject:BDA_Section:Tapered"
    ] = Field(
        ...,
        frozen=True
    )

    properties: TaperedSectionDataObject_Properties

    @classmethod
    def create(
        cls,
        name: str,
        start_section_application_id: str,
        end_section_application_id: str,
        section_type: SectionTypeParaModel,
        taper_y_variation: TaperVariationParaModel,
        taper_z_variation: TaperVariationParaModel,
        application_id: str = "tapered_section_1",
        isUser: bool = True,
    ) -> "SectionDataObject_Tapered":

        return cls(
            id=None,
            name=name,
            applicationId=application_id,
            speckle_type=(
                "Objects.Data.DataObject:"
                "BDA_Section:Tapered"
            ),
            bda_speckle_type=(
                "Objects.Data.DataObject:"
                "BDA_Section:Tapered"
            ),
            properties=(
                TaperedSectionDataObject_Properties(
                    **{
                        "Section Family":
                            SectionFamilyParameter_Tapered(),

                        "Section Type":
                            SectionTypeParameter_Tapered(
                                provided_value=section_type,
                            ),

                        "Section Start ID":
                            SectionStartIdParameter(
                                isUser=isUser,
                                provided_value=start_section_application_id,
                            ),

                        "Section End ID":
                            SectionEndIdParameter(
                                isUser=isUser,
                                provided_value=end_section_application_id,
                            ),

                        "Taper Y Variation":
                            TaperYVariationParameter(
                                isUser=isUser,
                                provided_value=taper_y_variation,
                            ),

                        "Taper Z Variation":
                            TaperZVariationParameter(
                                isUser=isUser,
                                provided_value=taper_z_variation,
                            ),
                    }
                )
            ),
        )


if __name__ == "__main__":

    from bda.contracts.speckle_contracts.bda_analytical.sections.standard_shape_family.standard_shape_section_types.isection_type_data_object import SectionDataObject_ISection

    start_section = SectionDataObject_ISection.create(
        name="Girder Start",
        application_id="SECT-0001-STANDARD-ISECTION",
        total_height=1.5,
        top_flange_width=0.5,
        bottom_flange_width=0.5,
        web_thickness=0.02,
        top_flange_thickness=0.03,
        bottom_flange_thickness=0.03,
        web_inner_radius=0.02,
        flange_end_radius=0.01,
    )

    end_section = SectionDataObject_ISection.create(
        name="Girder End",
        application_id="SECT-0002-STANDARD-ISECTION",
        total_height=2.0,
        top_flange_width=0.7,
        bottom_flange_width=0.7,
        web_thickness=0.02,
        top_flange_thickness=0.03,
        bottom_flange_thickness=0.03,
        web_inner_radius=0.02,
        flange_end_radius=0.01,
    )

    tapered = SectionDataObject_Tapered.create(
        name="Tapered Girder",
        application_id="SECT-0003-TAPERED",
        start_section_application_id="SECT-0001-STANDARD-ISECTION",
        end_section_application_id="SECT-0002-STANDARD-ISECTION",
        section_type=SectionTypeParaModel.I_SECTION,
        taper_y_variation=TaperVariationParaModel.LINEAR,
        taper_z_variation=TaperVariationParaModel.LINEAR,
    )

    print(
        tapered.model_dump_json(
            indent=4,
            by_alias=True,
            exclude_none=True,
        )
    )
