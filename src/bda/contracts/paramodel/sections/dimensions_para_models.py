"""
Dimension sub-models for section ParaModels.

Every geometric scalar is a ``QuantityParaModel`` (``{"value": ..., "unit": "m"}``).
List fields (PSC arrays) are ``List[QuantityParaModel]``.
Outline coordinate pairs are ``List[List[QuantityParaModel]]``.
Boolean fields (PSC joints) are plain ``bool``.
"""
from __future__ import annotations

from typing import List, Iterable

from pydantic import Field, AliasChoices, field_validator, AliasPath

from bda.contracts.paramodel.shared.base_model_para_model import BaseModelParaModel
from bda.contracts.shared import QuantityParaModel

Q = QuantityParaModel  # local alias for brevity


# ---------------------------------------------------------------------------
# User sections
# ---------------------------------------------------------------------------

class DimensionsAngleParaModel(BaseModelParaModel):
    height_h: Q = Field(validation_alias=AliasChoices(
        "height_h", "Height"))
    width_b: Q = Field(validation_alias=AliasChoices(
        "width_b", "Width"))
    thickness_web_tw: Q = Field(validation_alias=AliasChoices(
        "thickness_web_tw", "Web Thickness"))
    thickness_flange_tf: Q = Field(validation_alias=AliasChoices(
        "thickness_flange_tf","Flange Thickness"))


class DimensionsISectionParaModel(BaseModelParaModel):
    total_height_h: Q = Field(validation_alias=AliasChoices(
        "total_height_h","Total Height"))
    top_flange_width_b1: Q = Field(validation_alias=AliasChoices(
        "top_flange_width_b1","Top Flange Width"))
    bottom_flange_width_b2: Q = Field(validation_alias=AliasChoices(
        "bottom_flange_width_b2","Bottom Flange Width"))
    web_thickness_tw: Q = Field(validation_alias=AliasChoices(
        "web_thickness_tw","Web Thickness"))
    top_flange_thickness_tf1: Q = Field(validation_alias=AliasChoices(
        "top_flange_thickness_tf1","Top Flange Thickness"))
    bottom_flange_thickness_tf2: Q = Field(validation_alias=AliasChoices(
        "bottom_flange_thickness_tf2", "Bottom Flange Thickness"))
    web_inner_radius_r1: Q = Field(validation_alias=AliasChoices(
        "web_inner_radius_r1", "Web Inner Radius"))
    flange_end_radius_r2: Q = Field(validation_alias=AliasChoices(
        "flange_end_radius_r2", "Flange End Radius"))


class DimensionsBoxParaModel(BaseModelParaModel):
    height_h: Q = Field(validation_alias=AliasChoices(
        "height_h","Height"))
    flange_width_b: Q = Field(validation_alias=AliasChoices(
        "flange_width_b", "Flange Width"))
    web_thickness_tw: Q = Field(validation_alias=AliasChoices(
        "web_thickness_tw", "Web Thickness"))
    flange_thickness_tf: Q = Field(validation_alias=AliasChoices(
        "flange_thickness_tf","Flange Thickness"))


class DimensionsChannelParaModel(BaseModelParaModel):
     height_h: Q = Field(validation_alias=AliasChoices(
        "height_h","Height"))
     top_flange_width_b1: Q = Field(validation_alias=AliasChoices(
        "top_flange_width_b1", "Top Flange Width"))
     bottom_flange_width_b2: Q = Field(validation_alias=AliasChoices(
        "bottom_flange_width_b2", "Bottom Flange Width"))
     web_thickness_tw: Q = Field(validation_alias=AliasChoices(
        "web_thickness_tw", "Web Thickness"))
     top_flange_thickness_tf1: Q = Field(validation_alias=AliasChoices(
        "top_flange_thickness_tf1","Top Flange Thickness"))
     bottom_flange_thickness_tf2: Q = Field(validation_alias=AliasChoices(
        "bottom_flange_thickness_tf2", "Bottom Flange Thickness"))
     web_inner_radius_r1: Q = Field(validation_alias=AliasChoices(
        "web_inner_radius_r1", "Web Inner Radius"))
     flange_end_radius_r2: Q = Field(validation_alias=AliasChoices(
        "flange_end_radius_r2", "Flange End Radius"))


class DimensionsSolidRectangleParaModel(BaseModelParaModel):
    height_h: Q = Field(validation_alias=AliasChoices(
        "height_h", "Height"))
    width_b:  Q = Field(validation_alias=AliasChoices(
        "width_b", "Width"))


class DimensionsSolidRoundParaModel(BaseModelParaModel):
    diameter_d: Q = Field(validation_alias=AliasChoices(
        "diameter_d", "Diameter"))


class DimensionsPipeParaModel(BaseModelParaModel):
    external_diameter_d: Q = Field(validation_alias=AliasChoices(
        "external_diameter_d", "External Diameter"))
    wall_thickness_tw: Q = Field(validation_alias=AliasChoices(
        "wall_thickness_tw", "Wall Thickness"))

# ---------------------------------------------------------------------------
# Composite sections
# ---------------------------------------------------------------------------

class DimensionsCompositeSteelISymmetricParaModel(BaseModelParaModel):
    slab_width_bc: Q = Field(validation_alias=AliasChoices(
        "slab_width_bc", "Slab Width"))
    slab_thickness_tc: Q = Field(validation_alias=AliasChoices(
        "slab_thickness_tc", "Slab Thickness"))
    slab_girder_spacing_hh: Q = Field(validation_alias=AliasChoices(
        "slab_girder_spacing_hh", "Girder Spacing"))
    girder_top_flange_width_b1: Q = Field(validation_alias=AliasChoices(
        "girder_top_flange_width_b1", "Top Flange Width"))
    girder_top_flange_thickness_tf1: Q = Field(validation_alias=AliasChoices(
        "girder_top_flange_thickness_tf1", "Top Flange Thickness"))
    girder_bottom_flange_width_b2: Q = Field(validation_alias=AliasChoices(
        "girder_bottom_flange_width_b2", "Bottom Flange Width"))
    girder_bottom_flange_thickness_tf2: Q = Field(validation_alias=AliasChoices(
        "girder_bottom_flange_thickness_tf2", "Bottom Flange Thickness"))
    girder_web_thickness_tw: Q = Field(validation_alias=AliasChoices(
        "girder_web_thickness_tw", "Web Thickness"))
    girder_web_height_hw: Q = Field(validation_alias=AliasChoices(
        "girder_web_height_hw", "Web Height"))


class DimensionsCompositeSteelIAsymmetricParaModel(BaseModelParaModel):
    slab_distance_rf_sg: Q = Field(validation_alias=AliasChoices(
        "slab_distance_rf_sg", "Slab Reference Offset"))
    top_flange_distance_rf_top: Q = Field(validation_alias=AliasChoices(
        "top_flange_distance_rf_top", "Top Flange Reference Offset"))
    bottom_flange_distance_rf_bot: Q = Field(validation_alias=AliasChoices(
        "bottom_flange_distance_rf_bot", "Bottom Flange Reference Offset"))
    slab_width_bc: Q = Field(validation_alias=AliasChoices(
        "slab_width_bc", "Slab Width"))
    slab_thickness_tc: Q = Field(validation_alias=AliasChoices(
        "slab_thickness_tc", "Slab Thickness"))
    slab_girder_spacing_hh: Q = Field(validation_alias=AliasChoices(
        "slab_girder_spacing_hh", "Girder Spacing"))
    girder_top_flange_left_width_b1: Q = Field(validation_alias=AliasChoices(
        "girder_top_flange_left_width_b1", "Top Flange Left Width"))
    girder_top_flange_right_width_b2: Q = Field(validation_alias=AliasChoices(
        "girder_top_flange_right_width_b2", "Top Flange Right Width"))
    girder_top_flange_thickness_t1: Q = Field(validation_alias=AliasChoices(
        "girder_top_flange_thickness_t1", "Top Flange Thickness"))
    girder_bottom_flange_left_width_b3: Q = Field(validation_alias=AliasChoices(
        "girder_bottom_flange_left_width_b3", "Bottom Flange Left Width"))
    girder_bottom_flange_right_width_b4: Q = Field(validation_alias=AliasChoices(
        "girder_bottom_flange_right_width_b4", "Bottom Flange Right Width"))
    girder_bottom_flange_thickness_t2: Q = Field(validation_alias=AliasChoices(
        "girder_bottom_flange_thickness_t2", "Bottom Flange Thickness"))
    girder_web_thickness_tw: Q = Field(validation_alias=AliasChoices(
        "girder_web_thickness_tw", "Web Thickness"))
    girder_web_height_h: Q = Field(validation_alias=AliasChoices(
        "girder_web_height_h", "Web Height"))


# ---------------------------------------------------------------------------
# PSC sections
# ---------------------------------------------------------------------------

class Point2DParaModel(BaseModelParaModel):
    x: QuantityParaModel
    y: QuantityParaModel


class PolygonParaModel(BaseModelParaModel):
    vertices: List[Point2DParaModel]


class DimensionsPSCValueParaModel(BaseModelParaModel):
    # Each outline is a list of [x, y] coordinate pairs, each coord a QuantityParaModel
    outer_outline:  PolygonParaModel = Field(validation_alias=AliasPath(
            "External Section Polygon", "group_parameters", "2D Coordinates"))

    inner_outlines: List[PolygonParaModel] = Field(validation_alias=AliasPath(
            "Internal Section Polygons", "group_parameters"))

    @staticmethod
    def _coords_to_polygon(data: dict) -> PolygonParaModel:
        """
        Converts:
        {
            "provided_value": [[x1, y1], [x2, y2], ...],
            "provided_unit": "m"
        }
        ->
        PolygonParaModel(vertices=[Point2DParaModel(...), ...])
        """

        coords = data.get("provided_value") or data.get("value")
        unit = data.get("provided_unit") or data.get("unit")

        if not isinstance(coords, Iterable):
            if 'vertices' in data and isinstance(data['vertices'], Iterable):
                return PolygonParaModel(vertices=data['vertices'])
            return PolygonParaModel(vertices=[])

        vertices = [
            Point2DParaModel(
                x=QuantityParaModel(value=x, unit=unit),
                y=QuantityParaModel(value=y, unit=unit),
            )
            for x, y in coords
        ]

        return PolygonParaModel(vertices=vertices)

    @field_validator("outer_outline", mode="before")
    @classmethod
    def _validate_outer(cls, v):
        return cls._coords_to_polygon(v)

    @field_validator("inner_outlines", mode="before")
    @classmethod
    def _validate_inner(cls, v):
        """
        Structure:
        Internal Section Polygons
          -> group_parameters
              -> Void_0
                  -> group_parameters
                      -> 2D Coordinates
        """

        if not isinstance(v, dict):
            return v

        result = []

        for _, void_data in v.items():
            coords_data = (
                void_data
                .get("group_parameters", {})
                .get("2D Coordinates")
            )

            if coords_data:
                result.append(cls._coords_to_polygon(coords_data))

        return result


class DimensionsPSC1or2CellsParaModel(BaseModelParaModel):
    """Shared dimensions model for both psc-1cell and psc-2cell."""
    joints: List[bool]   # no unit – structural connectivity flags
    outer_height_ho: List[Q]
    outer_breadth_bo: List[Q]
    inner_height_hi: List[Q]
    inner_breadth_bi: List[Q]

