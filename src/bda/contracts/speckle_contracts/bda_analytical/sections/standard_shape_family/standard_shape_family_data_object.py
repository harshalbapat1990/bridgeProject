from __future__ import annotations

from typing import Literal
from pydantic import Field

from bda.contracts.speckle_contracts.bda_analytical.sections.general_section_data_object_parameters import (
    SectionFamily,
    GeneralSectionDataObject_Properties,
    GeneralSectionDataObject,
)

from bda.contracts.paramodel.sections.sections_para_models import (
    SectionFamilyParaModel,
)


# ==========================================================
# SECTION FAMILY (FIXED)
# ==========================================================

class SectionFamily_StandardShape(SectionFamily):
    provided_value: SectionFamilyParaModel = SectionFamilyParaModel.STANDARD_SHAPE


# ==========================================================
# PROPERTIES
# ==========================================================

class StandardShapeDataObject_Properties(GeneralSectionDataObject_Properties):
    section_family: SectionFamily_StandardShape = Field(
        alias="Section Family"
    )


# ==========================================================
# FINAL DATA OBJECT
# ==========================================================

class StandardShapeDataObject(GeneralSectionDataObject):
    properties: StandardShapeDataObject_Properties
    displayValue: list = []