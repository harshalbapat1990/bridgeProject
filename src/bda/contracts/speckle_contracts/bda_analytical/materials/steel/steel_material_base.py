from __future__ import annotations

from typing import Literal
from pydantic import Field

from bda.contracts.speckle_contracts.bda_analytical.materials.general_material_parameters import (
    MaterialType,
    GeneralMaterialParameters,
    GeneralMaterialParameterGroup,
    GeneralMaterialDataObject_Properties,
)

from bda.contracts.speckle_contracts.bda_analytical.materials.general_material_data_object import (
    GeneralMaterialDataObject,
)

from bda.contracts.paramodel.materials.materials_para_model import (
    MaterialTypeParaModel,
)


# ==========================================================
# Material Type (FIXED)
# ==========================================================

class MaterialType_Steel(MaterialType):
    """Steel-specialised Material Type"""

    provided_value: MaterialTypeParaModel = (
        MaterialTypeParaModel.STEEL
    )


# ==========================================================
# Steel General Material Properties Override
# ==========================================================

class SteelGeneralMaterialParameters(
    GeneralMaterialParameters
):
    material_type: MaterialType_Steel = Field(
        alias="Material Type"
    )


class SteelGeneralMaterialParameterGroup(
    GeneralMaterialParameterGroup
):
    group_parameters: SteelGeneralMaterialParameters


class SteelMaterialDataObject_Properties(
    GeneralMaterialDataObject_Properties
):
    general_material_properties: (
        SteelGeneralMaterialParameterGroup
    ) = Field(
        alias="General Material Properties"
    )


class SteelMaterialDataObject(
    GeneralMaterialDataObject
):
    properties: SteelMaterialDataObject_Properties