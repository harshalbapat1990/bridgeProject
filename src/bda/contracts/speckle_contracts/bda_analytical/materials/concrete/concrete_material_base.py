from __future__ import annotations

from typing import Literal
from pydantic import Field

from bda.contracts.speckle_contracts.bda_analytical.materials.general_material_parameters import (
    MaterialType,
    GeneralMaterialParameters,
    GeneralMaterialParameterGroup,
    GeneralMaterialDataObject_Properties,
)

from bda.contracts.speckle_contracts.bda_analytical.materials.general_material_data_object import GeneralMaterialDataObject

from bda.contracts.paramodel.materials.materials_para_model import (
    MaterialTypeParaModel,
)


# ==========================================================
# Material Type (FIXED)
# ==========================================================

class MaterialType_Concrete(MaterialType):
    """Concrete-specialised Material Type"""
    provided_value: MaterialTypeParaModel = MaterialTypeParaModel.CONCRETE

# ==========================================================
# Concrete General Material Properties Override
# ==========================================================

class ConcreteGeneralMaterialParameters(GeneralMaterialParameters):
    material_type: MaterialType_Concrete = Field(alias="Material Type")


class ConcreteGeneralMaterialParameterGroup(
    GeneralMaterialParameterGroup
):
    group_parameters: ConcreteGeneralMaterialParameters

class ConcreteMaterialDataObject_Properties(GeneralMaterialDataObject_Properties):
    general_material_properties: ConcreteGeneralMaterialParameterGroup = Field(
        alias="General Material Properties"
    )

class ConcreteMaterialDataObject(GeneralMaterialDataObject):
    properties: ConcreteMaterialDataObject_Properties