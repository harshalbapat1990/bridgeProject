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

class MaterialType_Tendon(MaterialType):
    """Tendon-specialised Material Type"""

    provided_value: MaterialTypeParaModel = (
        MaterialTypeParaModel.TENDON
    )


# ==========================================================
# Tendon General Material Properties Override
# ==========================================================

class TendonGeneralMaterialParameters(
    GeneralMaterialParameters
):
    material_type: MaterialType_Tendon = Field(
        alias="Material Type"
    )


class TendonGeneralMaterialParameterGroup(
    GeneralMaterialParameterGroup
):
    group_parameters: TendonGeneralMaterialParameters


class TendonMaterialDataObject_Properties(
    GeneralMaterialDataObject_Properties
):
    general_material_properties: (
        TendonGeneralMaterialParameterGroup
    ) = Field(
        alias="General Material Properties"
    )


class TendonMaterialDataObject(
    GeneralMaterialDataObject
):
    properties: TendonMaterialDataObject_Properties