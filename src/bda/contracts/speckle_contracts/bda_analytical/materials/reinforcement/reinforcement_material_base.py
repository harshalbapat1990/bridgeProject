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

class MaterialType_Reinforcement(MaterialType):
    """Reinforcement-specialised Material Type"""

    provided_value: MaterialTypeParaModel = (
        MaterialTypeParaModel.REINFORCEMENT
    )


# ==========================================================
# Reinforcement General Material Properties Override
# ==========================================================

class ReinforcementGeneralMaterialParameters(
    GeneralMaterialParameters
):
    material_type: MaterialType_Reinforcement = Field(
        alias="Material Type"
    )


class ReinforcementGeneralMaterialParameterGroup(
    GeneralMaterialParameterGroup
):
    group_parameters: (
        ReinforcementGeneralMaterialParameters
    )


class ReinforcementMaterialDataObject_Properties(
    GeneralMaterialDataObject_Properties
):
    general_material_properties: (
        ReinforcementGeneralMaterialParameterGroup
    ) = Field(
        alias="General Material Properties"
    )


class ReinforcementMaterialDataObject(
    GeneralMaterialDataObject
):
    properties: (
        ReinforcementMaterialDataObject_Properties
    )