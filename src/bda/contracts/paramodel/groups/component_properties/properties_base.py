from __future__ import annotations

from typing import Literal, Annotated, Union

from pydantic import BaseModel, Field

from bda.contracts.paramodel.groups.enums import CurvatureTypeEnumParaModel
from bda.contracts.paramodel.sections.sections_para_models import SectionOffsetParaModel
from bda.contracts.paramodel.shared.base_model_para_model import BaseModelParaModel
from bda.contracts.shared import QuantityParaModel

# -------------------------
# Abstract base classes
# -------------------------

class PropertiesBaseParaModel(BaseModel):
    """
    Abstract base class for properties.

    Implementation depends on StructuralComponentType.
    Discriminator is defined in ParaModelGeometryGroup.
    """

class SegmentDetailsParaModel(BaseModel):
    x_start: QuantityParaModel


class TendonGeometryBaseParaModel(BaseModel):
    # for MVP we assume that the datum point is always center-top, so we can hardcode it here
    datum_point: Literal[
        SectionOffsetParaModel.CENTER_TOP
    ] = SectionOffsetParaModel.CENTER_TOP
    curvature_type: CurvatureTypeEnumParaModel


class ControlPointParaModel(BaseModelParaModel):
    longitudinal_x: QuantityParaModel
    transverse_offset_y: QuantityParaModel
    vertical_offset_z: QuantityParaModel


class ControlPointWithRadiusParaModel(BaseModelParaModel):
    point: ControlPointParaModel
    radius: QuantityParaModel


class TendonGeometryCircularTypeParaModel(TendonGeometryBaseParaModel):
    curvature_type: Literal[
        CurvatureTypeEnumParaModel.CIRCULAR
    ] = CurvatureTypeEnumParaModel.CIRCULAR

    control_points: list[ControlPointWithRadiusParaModel]

_TendonGeometryParaModel = Annotated[
    Union[
        TendonGeometryCircularTypeParaModel,
    ],
    Field(discriminator="curvature_type"),
]

class PropertiesIndividualTendonParaModel(PropertiesBaseParaModel):
    tendon_index: int
    tendon_geometry: _TendonGeometryParaModel