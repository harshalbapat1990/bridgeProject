from __future__ import annotations
from pathlib import Path
import sys

from bda.contracts.speckle_contracts.base_objects import BridgeDataObject, Parameter, UnitlessParameter, EnumParameter, UnitParameter, ParameterGroup, BridgeDataObjectProperties, DataObjectSpeckleType
from bda.contracts.speckle_contracts.bda_analytical.materials.general_material_parameters import GeneralMaterialParameters
from bda.contracts.paramodel.sections.sections_para_models import SectionFamilyParaModel, SectionOffsetParaModel, SectionTypeParaModel
from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_enums import DesignCodesEnum
from typing import Literal, Optional
from pydantic import BaseModel, Field, StrictFloat
import json


# Dimesnion Abstract Class

class LengthDimensionParameter(UnitParameter[float]):
    # Allowed user units
    provided_unit: Literal["m", "in"]
    base_unit: Literal["m"] = "m"

class GeneralSectionDataObjectType(DataObjectSpeckleType):
    provided_value: Literal["Objects.Data.DataObject:BDA_General_Section"]="Objects.Data.DataObject:BDA_General_Section"

# Material Type

class SectionDescription(UnitlessParameter[str]):
    name: Literal["Section Description"] = "Section Description"
    symbol: None = None
    description: Literal["Description of the section"] = "Description of the section"

    provided_value: Optional[str] = None

class SectionFamily(EnumParameter[SectionFamilyParaModel]):
    name: Literal["Section Family"] = "Section Family"
    symbol: None = None
    description: Literal["Family of the section (e.g., Standard Shape, Composite, PSC)"] = "Family of the section (e.g., Standard Shape, Composite, PSC)"

class SectionType(EnumParameter[SectionTypeParaModel]):
    name: Literal["Section Type"] = "Section Type"
    symbol: None = None
    description: Literal["Type of the section (e.g., I-Section, T-Section, Box Section)"] = "Type of the section (e.g., I-Section, T-Section, Box Section)"

# NOTE: Omitted from Input Schema at MVP as not user defined property
# class SectionOffset(EnumParameter[SectionOffsetParaModel]):
#     name: Literal["Section Offset"] = "Section Offset"
#     symbol: None = None
#     description: Literal["Reference point for section properties (e.g., center-top, left-top, right-top, center-center, left-center, right-center, center-bottom, left-bottom, right-bottom)"] = "Reference point for section properties (e.g., center-top, left-top, right-top, center-center, left-center, right-center, center-bottom, left-bottom, right-bottom)"


class SectionDimensionParameterGroup(ParameterGroup):
    name: Literal["Section Dimensions"] = "Section Dimensions"
    description: Literal["Dimensions of the section"] = \
        "Dimensions of the section"

    group_parameters: dict[str, Parameter]

class GeneralSectionDataObject_Properties(BridgeDataObjectProperties):
    bda_speckle_type:GeneralSectionDataObjectType
    section_description: SectionDescription = Field(alias="Section Description")
    section_family: SectionFamily = Field(alias="Section Family")
    section_type: SectionType = Field(alias="Section Type")
    # section_offset: SectionOffset = Field(alias="Section Offset") # NOTE: Omitted from Input Schema at MVP as not user defined property
    section_dimensions: SectionDimensionParameterGroup= Field(alias="Section Dimensions")

class GeneralSectionDataObject(BridgeDataObject):
    properties: GeneralSectionDataObject_Properties
    displayValue: list = []

if __name__ == "__main__":
    # Example usage
    print("\n=== General Section Properties json schema ===")
    ui_schema = GeneralSectionDataObject.model_json_schema()
    print(json.dumps(ui_schema, indent=2))  


