"""
Mapper: SectionParaModel  →  SectionBase domain objects.

Usage
-----
::

    from bda.contracts.sections import SectionParaModelAdapter
    from bda.application.mapping.sections.section_mapper import SectionMapper

    adapter = SectionParaModelAdapter.model_validate(raw_data)
    domain_objects = SectionMapper.to_domain_list(adapter.sections)
"""

from __future__ import annotations

from typing import Callable

from bda.contracts.paramodel.sections import (
    SectionBaseParaModel,
)
from bda.contracts.paramodel.sections.dimensions_para_models import Point2DParaModel, PolygonParaModel
from bda.contracts.paramodel.sections.sections_para_models import *
from bda.contracts.shared import QuantityParaModel
from bda.domain.enums import OffsetReference, SectionType, TaperVariation
from bda.domain.models.submodels import SectionBase
from bda.application.mapping.base import to_pint, to_uuid
from bda.domain.models.submodels.section_base import Offset
from bda.domain.models.submodels.sections import *
from bda.domain.models.submodels.sections import SectionStandardPipe, DimensionsPipe


# ---------------------------------------------------------------------------
# SectionRegistry class
# ---------------------------------------------------------------------------

SectionKey = tuple[SectionFamilyParaModel, SectionTypeParaModel | None]
SectionMapperFunc = Callable[[SectionBaseParaModel], SectionBase]

class _RegistryMappingFunctions:
    """
    Registry for section mapping functions.

    This class maintains a mapping between `(SectionFamilyParaModel, SectionTypeParaModel)`
    keys and corresponding mapper functions. Each mapper function converts a
    `SectionBaseParaModel` instance into a domain-level `SectionBase` object.

    Mappers are registered using the `register` decorator and retrieved
    automatically at runtime via the `map` method.

    Example:
        @_SectionRegistry.register(
            SectionFamilyParaModel.STANDARD,
            SectionTypeParaModel.ANGLE,
        )
        def _map_standard_angle(sec: SectionBaseParaModel) -> SectionBase:
            ...

        result = _SectionRegistry.map(sec)

    Notes:
        - Each (section_family, section_type) pair can have only one mapper.
        - Attempting to register a duplicate mapper raises a RuntimeError.
        - Calling `map` with an unregistered key raises NotImplementedError.
    """

    _registry: dict[SectionKey, SectionMapperFunc] = {}

    @classmethod
    def register(
            cls,
            section_family: SectionFamilyParaModel,
            section_type: SectionTypeParaModel | None,
            ) -> Callable[[SectionMapperFunc], SectionMapperFunc]:
        """
        Register a section-mapping function for the given section family and type.

        This method is used as a decorator that associates a mapping function
        with a specific `(section_family, section_type)` pair.

        Args:
            section_family (SectionFamilyParaModel): Section family identifier.
            section_type (SectionTypeParaModel): Section type identifier.

        Returns:
            Callable: A decorator that registers the mapping function.

        Raises:
            RuntimeError: If a mapper for the given key is already registered.

        Example:
            @_SectionRegistry.register(
                SectionFamilyParaModel.STANDARD,
                SectionTypeParaModel.ANGLE)
            def _map_standard_angle(sec: SectionBaseParaModel) -> SectionBase:
                ...
        """

        def decorator(func: SectionMapperFunc) -> SectionMapperFunc:
            key = (section_family, section_type)

            if key in cls._registry:
                raise RuntimeError(f"Duplicate mapper for {key}")

            cls._registry[key] = func
            return func

        return decorator

    @classmethod
    def map(cls, sec: SectionBaseParaModel) -> SectionBase:
        """
            Map a parameter model section to its corresponding domain section.

            This method looks up a registered mapper based on the
            `(section_family, section_type)` attributes of the given
            `SectionBaseParaModel` instance and applies it to produce
            a `SectionBase` domain object.

            Args:
                sec (SectionBaseParaModel): Input section model to be mapped.

            Returns:
                SectionBase: Mapped domain section object.

            Raises:
                NotImplementedError: If no mapper is registered for the given
                    `(section_family, section_type)` pair.
            """

        key = (sec.section_family, sec.section_type)

        mapper = cls._registry.get(key)

        # fallback for (family, None)
        if mapper is None:
            fallback_key = (sec.section_family, None)
            mapper = cls._registry.get(fallback_key)

        if mapper is None:
            raise NotImplementedError(
                f"No mapper registered for type: {sec.section_type}, from family: {sec.section_family}."
            )

        return mapper(sec)

# ---------------------------------------------------------------------------
# Mapping functions: STANDARD
# ---------------------------------------------------------------------------

@_RegistryMappingFunctions.register(SectionFamilyParaModel.STANDARD_SHAPE, SectionTypeParaModel.ANGLE)
def _map_standard_angle(sec: SectionBaseParaModel) -> SectionBase:
    if not isinstance(sec, SectionStandardAngleParaModel):
        raise TypeError(
            f"Expected SectionStandardAngleParaModel, got {type(sec).__name__}"
        )
    s: SectionStandardAngleParaModel = sec
    map_offset = _SectionOffsetMapper.to_domain
    return SectionStandardAngle(
        guid= to_uuid(s.section_id),
        source_id=s.section_id,
        name=s.name,
        offset=map_offset(s.offset),
        dimensions=DimensionsAngle(
            height=to_pint(s.dimensions.height_h),
            width=to_pint(s.dimensions.width_b),
            thickness_web=to_pint(s.dimensions.thickness_web_tw),
            thickness_flange=to_pint(s.dimensions.thickness_flange_tf),
        ),
    )

@_RegistryMappingFunctions.register(SectionFamilyParaModel.STANDARD_SHAPE, SectionTypeParaModel.I_SECTION)
def _map_standard_Isection(sec: SectionBaseParaModel) -> SectionBase:
    if not isinstance(sec, SectionStandardISectionParaModel):
        raise TypeError(
            f"Expected SectionStandardISectionParaModel, got {type(sec).__name__}"
        )
    s: SectionStandardISectionParaModel = sec
    map_offset = _SectionOffsetMapper.to_domain
    return SectionStandardISection(
        guid=to_uuid(s.section_id),
        source_id=s.section_id,
        name= s.name,
        offset= map_offset(s.offset),
        dimensions= DimensionsISection(
            total_height_h= to_pint(s.dimensions.total_height_h),
            top_flange_width_b1= to_pint(s.dimensions.top_flange_width_b1),
            bottom_flange_width_b2= to_pint(s.dimensions.bottom_flange_width_b2),
            web_thickness_tw= to_pint(s.dimensions.web_thickness_tw),
            top_flange_thickness_tf1= to_pint(s.dimensions.top_flange_thickness_tf1),
            bottom_flange_thickness_tf2= to_pint(s.dimensions.bottom_flange_thickness_tf2),
            web_inner_radius_r1= to_pint(s.dimensions.web_inner_radius_r1),
            flange_end_radius_r2= to_pint(s.dimensions.flange_end_radius_r2)
        )
    )

@_RegistryMappingFunctions.register(SectionFamilyParaModel.STANDARD_SHAPE, SectionTypeParaModel.BOX)
def _map_standard_box(sec: SectionBaseParaModel) -> SectionBase:
    if not isinstance(sec, SectionStandardBoxParaModel):
        raise TypeError(
            f"Expected SectionStandardBoxParaModel, got {type(sec).__name__}"
        )
    s: SectionStandardBoxParaModel = sec
    map_offset = _SectionOffsetMapper.to_domain
    return SectionStandardBox(
        guid=to_uuid(s.section_id),
        source_id=s.section_id,
        name= s.name,
        offset= map_offset(s.offset),
        dimensions= DimensionsBox(
            height_h= to_pint(s.dimensions.height_h),
            top_flange_width_b= to_pint(s.dimensions.flange_width_b),
            web_thickness_tw= to_pint(s.dimensions.web_thickness_tw),
            top_flange_thickness_tf1= to_pint(s.dimensions.flange_thickness_tf)
            )
    )

@_RegistryMappingFunctions.register(SectionFamilyParaModel.STANDARD_SHAPE, SectionTypeParaModel.CHANNEL)
def _map_standard_channel(sec: SectionBaseParaModel) -> SectionBase:
    if not isinstance(sec, SectionStandardChannelParaModel):
        raise TypeError(
            f"Expected SectionStandardChannelParaModel, got {type(sec).__name__}"
        )
    s: SectionStandardChannelParaModel = sec
    map_offset = _SectionOffsetMapper.to_domain
    return SectionStandardChannel(
        guid=to_uuid(s.section_id),
        source_id=s.section_id,
        name= s.name,
        offset= map_offset(s.offset),
        dimensions= DimensionsChannel(
            height_h=to_pint(s.dimensions.height_h), #TODO - consider changing this to "total_height_h"
            top_flange_width_b1=to_pint(s.dimensions.top_flange_width_b1),
            bottom_flange_width_b2=to_pint(s.dimensions.bottom_flange_width_b2),
            web_thickness_tw=to_pint(s.dimensions.web_thickness_tw),
            top_flange_thickness_tf1=to_pint(s.dimensions.top_flange_thickness_tf1),
            bottom_flange_thickness_tf2=to_pint(s.dimensions.bottom_flange_thickness_tf2),
            web_inner_radius_r1=to_pint(s.dimensions.web_inner_radius_r1),
            flange_end_radius_r2=to_pint(s.dimensions.flange_end_radius_r2)
        )
    )

@_RegistryMappingFunctions.register(SectionFamilyParaModel.STANDARD_SHAPE, SectionTypeParaModel.SOLID_RECTANGLE)
def _map_standard_solid_rectangle(sec: SectionBaseParaModel) -> SectionBase:
    if not isinstance(sec, SectionStandardSolidRectangleParaModel):
        raise TypeError(
            f"Expected SectionStandardSolidRectangleParaModel, got {type(sec).__name__}"
        )
    s: SectionStandardSolidRectangleParaModel = sec
    map_offset = _SectionOffsetMapper.to_domain
    return SectionStandardSolidRectangle(
        guid=to_uuid(s.section_id),
        source_id=s.section_id,
        name=s.name,
        offset=map_offset(s.offset),
        dimensions=DimensionsSolidRectangle(
            height_h= to_pint(s.dimensions.height_h),
            width_b= to_pint(s.dimensions.width_b),
        )
    )

@_RegistryMappingFunctions.register(SectionFamilyParaModel.STANDARD_SHAPE, SectionTypeParaModel.SOLID_ROUND)
def _map_standard_solid_round(sec: SectionBaseParaModel) -> SectionBase:
    if not isinstance(sec, SectionStandardSolidRoundParaModel):
        raise TypeError(
            f"Expected SectionStandardSolidRoundParaModel, got {type(sec).__name__}"
        )
    s: SectionStandardSolidRoundParaModel = sec
    map_offset = _SectionOffsetMapper.to_domain
    return SectionStandardSolidRound(
        guid=to_uuid(s.section_id),
        source_id=s.section_id,
        name=s.name,
        offset=map_offset(s.offset),
        dimensions= DimensionsSolidRound(
            diameter_d= to_pint(s.dimensions.diameter_d),
        )
    )

@_RegistryMappingFunctions.register(SectionFamilyParaModel.STANDARD_SHAPE, SectionTypeParaModel.PIPE)
def _map_standard_pipe(sec: SectionBaseParaModel) -> SectionBase:
    if not isinstance(sec, SectionStandardPipeParaModel):
        raise TypeError(
            f"Expected SectionStandardPipeParaModel, got {type(sec).__name__}"
        )
    s: SectionStandardPipeParaModel = sec
    map_offset = _SectionOffsetMapper.to_domain
    return SectionStandardPipe(
        guid=to_uuid(s.section_id),
        source_id=s.section_id,
        name=sec.name,
        offset=map_offset(sec.offset),
        dimensions= DimensionsPipe(
            external_diameter_d= to_pint(sec.dimensions.external_diameter_d),
            wall_thickness_tw= to_pint(sec.dimensions.wall_thickness_tw),
        ),
    )

# ---------------------------------------------------------------------------
# Mapping functions: COMPOSITE
# ---------------------------------------------------------------------------

@_RegistryMappingFunctions.register(SectionFamilyParaModel.COMPOSITE, SectionTypeParaModel.STEEL_I_SYMMETRIC)
def _map_composite_steel_I_symmetric(sec: SectionBaseParaModel) -> SectionBase:
    if not isinstance(sec, SectionCompositeSteelISymmetricParaModel):
        raise TypeError(
            f"Expected SectionCompositeSteelISymmetricParaModel, got {type(sec).__name__}"
        )
    s: SectionCompositeSteelISymmetricParaModel = sec
    map_offset = _SectionOffsetMapper.to_domain
    return SectionCompositeSteelISymmetric(
        guid=to_uuid(s.section_id),
        source_id=s.section_id,
        name= s.name,
        offset= map_offset(s.offset),
        dimensions= DimensionsCompositeSteelISymmetric(
            slab_width_bc= to_pint(s.dimensions.slab_width_bc),
            slab_thickness_tc= to_pint(s.dimensions.slab_thickness_tc),
            slab_girder_spacing_hh= to_pint(s.dimensions.slab_girder_spacing_hh),
            girder_top_flange_width_b1= to_pint(s.dimensions.girder_top_flange_width_b1),
            girder_top_flange_thickness_tf1= to_pint(s.dimensions.girder_top_flange_thickness_tf1),
            girder_bottom_flange_width_b2= to_pint(s.dimensions.girder_bottom_flange_width_b2),
            girder_bottom_flange_thickness_tf2= to_pint(s.dimensions.girder_bottom_flange_thickness_tf2),
            girder_web_thickness_tw= to_pint(s.dimensions.girder_web_thickness_tw),
            girder_web_height_hw= to_pint(s.dimensions.girder_web_height_hw),
        )
    )

@_RegistryMappingFunctions.register(SectionFamilyParaModel.COMPOSITE, SectionTypeParaModel.STEEL_I_ASYMMETRIC)
def _map_composite_steel_I_asymmetric(sec: SectionBaseParaModel) -> SectionBase:
    if not isinstance(sec, SectionCompositeSteelIAsymmetricParaModel):
        raise TypeError(
            f"Expected SectionCompositeSteelISymmetricParaModel, got {type(sec).__name__}"
        )
    s: SectionCompositeSteelIAsymmetricParaModel = sec
    map_offset = _SectionOffsetMapper.to_domain
    return SectionCompositeSteelIAsymmetric(
        guid=to_uuid(s.section_id),
        source_id=s.section_id,
        name=s.name,
        offset=map_offset(s.offset),
        dimensions=DimensionsCompositeSteelIAsymmetric(
            slab_distance_rf_sg= to_pint(s.dimensions.slab_distance_rf_sg),
            top_flange_distance_rf_top= to_pint(s.dimensions.top_flange_distance_rf_top),
            bottom_flange_distance_rf_bot= to_pint(s.dimensions.bottom_flange_distance_rf_bot),
            slab_width_bc= to_pint(s.dimensions.slab_width_bc),
            slab_thickness_tc= to_pint(s.dimensions.slab_thickness_tc),
            slab_girder_spacing_hh= to_pint(s.dimensions.slab_girder_spacing_hh),
            girder_top_flange_left_width_b1= to_pint(s.dimensions.girder_top_flange_left_width_b1),
            girder_top_flange_right_width_b2= to_pint(s.dimensions.girder_top_flange_right_width_b2),
            girder_top_flange_thickness_t1= to_pint(s.dimensions.girder_top_flange_thickness_t1),
            girder_bottom_flange_left_width_b3= to_pint(s.dimensions.girder_bottom_flange_left_width_b3),
            girder_bottom_flange_right_width_b4= to_pint(s.dimensions.girder_bottom_flange_right_width_b4),
            girder_bottom_flange_thickness_t2= to_pint(s.dimensions.girder_bottom_flange_thickness_t2),
            girder_web_thickness_tw= to_pint(s.dimensions.girder_web_thickness_tw),
            girder_web_height_h= to_pint(s.dimensions.girder_web_height_h)
        )
    )

# ---------------------------------------------------------------------------
# Mapping functions: PSC
# ---------------------------------------------------------------------------

@_RegistryMappingFunctions.register(SectionFamilyParaModel.PSC, SectionTypeParaModel.PSC_VALUE)
def _map_psc_value(sec: SectionBaseParaModel) -> SectionBase:

    if not isinstance(sec, SectionPSCValueParaModel):
        raise TypeError(
            f"Expected SectionPSCValueParaModel, got {type(sec).__name__}"
        )
    s: SectionPSCValueParaModel = sec
    map_offset = _SectionOffsetMapper.to_domain
    map_polygon = _HelperSectionPSCMapper._map_polygon
    map_polygons = _HelperSectionPSCMapper._map_polygons
    return SectionPSCValue(
        guid=to_uuid(s.section_id),
        source_id=s.section_id,
        name= s.name,
        offset=map_offset(s.offset),
        dimensions= DimensionsPSCValues(
            outer_outline= map_polygon(s.dimensions.outer_outline),
            inner_outlines= map_polygons(s.dimensions.inner_outlines),
        )
    )

@_RegistryMappingFunctions.register(SectionFamilyParaModel.PSC, SectionTypeParaModel.PSC_1CELL)
def _map_psc_1cell(sec: SectionBaseParaModel) -> SectionBase:
    if not isinstance(sec, SectionPSC1CellParaModel):
        raise TypeError(
            f"Expected SectionPSC1CellParaModel, got {type(sec).__name__}"
        )
    s: SectionPSC1CellParaModel = sec
    map_offset = _SectionOffsetMapper.to_domain
    map_fixed_bool = _HelperSectionPSCMapper._map_fixed_bool
    map_fixed_length = _HelperSectionPSCMapper._map_fixed_length

    return SectionPSC12Cell(
        guid=to_uuid(s.section_id),
        source_id=s.section_id,
        section_type=SectionType.PSC_1CELL,
        name= s.name,
        offset=map_offset(s.offset),
        dimensions= DimensionsPSC12Cell(
            joints= JointsPSC(*map_fixed_bool(s.dimensions.joints, 8, "joints")),
            outer_height_ho= OuterHeightHo(*map_fixed_length(s.dimensions.outer_height_ho, 6, "outer_height_ho")),
            outer_breadth_bo= OuterBreadthBo(*map_fixed_length(s.dimensions.outer_breadth_bo, 6, "outer_breadth_bo")),
            inner_height_hi= InnerHeightHi(*map_fixed_length(s.dimensions.inner_height_hi, 10, "inner_height_hi")),
            inner_breadth_bi= InnerBreadthBi(*map_fixed_length(s.dimensions.inner_breadth_bi, 7, "inner_breadth_bi"),
                                             None),
        )
    )

@_RegistryMappingFunctions.register(SectionFamilyParaModel.PSC, SectionTypeParaModel.PSC_2CELLS)
def _map_psc_2cells(sec: SectionBaseParaModel) -> SectionBase:
    if not isinstance(sec, SectionPSC2CellParaModel):
        raise TypeError(
            f"Expected SectionPSC2CellParaModel, got {type(sec).__name__}"
        )
    s: SectionPSC2CellParaModel = sec
    map_offset = _SectionOffsetMapper.to_domain
    map_fixed_bool = _HelperSectionPSCMapper._map_fixed_bool
    map_fixed_length = _HelperSectionPSCMapper._map_fixed_length
    return SectionPSC12Cell(
        guid=to_uuid(s.section_id),
        source_id=s.section_id,
        section_type=SectionType.PSC_2CELL, #TODO - PSC_2CELLS in SectionTypeParaModel, PSC_2CELL in SectionType. Inconsistent.
        name= s.name,
        offset=map_offset(s.offset),
        dimensions= DimensionsPSC12Cell(
            joints= JointsPSC(*map_fixed_bool(s.dimensions.joints, 8, "joints")),
            outer_height_ho= OuterHeightHo(*map_fixed_length(s.dimensions.outer_height_ho, 6, "outer_height_ho")),
            outer_breadth_bo= OuterBreadthBo(*map_fixed_length(s.dimensions.outer_breadth_bo, 6, "outer_breadth_bo")),
            inner_height_hi= InnerHeightHi(*map_fixed_length(s.dimensions.inner_height_hi, 10, "inner_height_hi")),
            inner_breadth_bi= InnerBreadthBi(*map_fixed_length(s.dimensions.inner_breadth_bi, 8, "inner_breadth_bi")),
        )
    )

# ---------------------------------------------------------------------------
# Mapping functions: Tapered
# ---------------------------------------------------------------------------

@_RegistryMappingFunctions.register(SectionFamilyParaModel.TAPERED, section_type= None)
def _map_tapered(sec: SectionBaseParaModel) -> SectionBase:
    if not isinstance(sec, SectionTaperedParaModel):
        raise TypeError(
            f"Expected SectionTaperedParaModel, got {type(sec).__name__}"
        )
    s: SectionTaperedParaModel = sec
    map_offset = _SectionOffsetMapper.to_domain
    map_taper_variation = _TaperVariationMapper.to_domain
    return SectionTapered(
        guid=to_uuid(s.section_id),
        source_id=s.section_id,
        name= s.name,
        offset= map_offset(s.offset),
        section_start_id= to_uuid(s.section_start_id),
        section_end_id= to_uuid(s.section_end_id),
        taper_y_variation= map_taper_variation(s.taper_y_variation),
        taper_z_variation= map_taper_variation(s.taper_z_variation),
    )

# ---------------------------------------------------------------------------
# Private sub-mappers
# ---------------------------------------------------------------------------

class _TaperVariationMapper:
    _MAP = {
        TaperVariationParaModel.LINEAR: TaperVariation.LINEAR,
        TaperVariationParaModel.PARABOLIC: TaperVariation.PARABOLIC,
        TaperVariationParaModel.CUBIC: TaperVariation.CUBIC,
    }

    @staticmethod
    def to_domain(taper_variation: TaperVariationParaModel) -> TaperVariation:
        try:
            return _TaperVariationMapper._MAP[taper_variation]
        except NotImplementedError:
            raise NotImplementedError(
                f"Taper variation {taper_variation} not found in TaperVariationMapper"
            )

class _SectionOffsetMapper:
    _MAP = {
        SectionOffsetParaModel.CENTER_TOP: OffsetReference.CENTER_TOP,
        SectionOffsetParaModel.LEFT_TOP: OffsetReference.LEFT_TOP,
        SectionOffsetParaModel.RIGHT_TOP: OffsetReference.RIGHT_TOP,
        SectionOffsetParaModel.CENTER_CENTER: OffsetReference.CENTER_CENTER,
        SectionOffsetParaModel.LEFT_CENTER: OffsetReference.LEFT_CENTER,
        SectionOffsetParaModel.RIGHT_CENTER: OffsetReference.RIGHT_CENTER,
        SectionOffsetParaModel.CENTER_BOTTOM: OffsetReference.CENTER_BOTTOM,
        SectionOffsetParaModel.LEFT_BOTTOM: OffsetReference.LEFT_BOTTOM,
        SectionOffsetParaModel.RIGHT_BOTTOM: OffsetReference.RIGHT_BOTTOM,
    }

    @staticmethod
    def to_domain(offset: SectionOffsetParaModel) -> Offset:
        try:
            return Offset(_SectionOffsetMapper._MAP[offset])
        except KeyError:
            raise NotImplementedError(
                f"Section offset {offset} is not implemented. "
            )

class _HelperSectionPSCMapper:
    @staticmethod
    def _map_point(pm: Point2DParaModel) -> Point2D:
        return Point2D(
            x = to_pint(pm.x),
            y = to_pint(pm.y),
        )

    @staticmethod
    def _map_polygon(pm: PolygonParaModel) -> list[Point2D]:
        return [
            _HelperSectionPSCMapper._map_point(p)
            for p in pm.vertices
        ]

    @staticmethod
    def _map_polygons(data: list[PolygonParaModel]) -> list[list[Point2D]]:
        return [
            _HelperSectionPSCMapper._map_polygon(poly)
            for poly in data
        ]

    @staticmethod
    def _map_fixed_length(data, n: int, name: str):
        if len(data) != n:
            raise ValueError(f"{name} expected {n}, got {len(data)}")
        return [to_pint(x) for x in data]

    @staticmethod
    def _map_fixed_bool(data, n: int, name: str):
        if len(data) != n:
            raise ValueError(f"{name} expected {n}, got {len(data)}")
        return list(data)

    @staticmethod
    def _to_length(val):
        if isinstance(val, QuantityParaModel):
            return val
        return to_pint(val)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class SectionMapper:
    """Entry point for mapping ``SectionParaModel`` contracts to domain objects.

    Maps grouped ParaModel contracts to domain objects."""

    @staticmethod
    def to_domain(para_model: SectionParaModel) -> SectionBase:
        """Map a single ``SectionParaModel`` to its domain counterpart."""
        return _RegistryMappingFunctions.map(para_model)

    @staticmethod
    def to_domain_list(para_models: List[SectionParaModel]) -> List[SectionBase]:
        """Map a list of ParaModels to domain objects, preserving order.

        If a ParaModel carries a non-None ``id`` field it is forwarded to
        ``set_id()`` on the resulting domain object so that downstream
        consumers (e.g. group consistency checks) can resolve references.
        """
        result: List[SectionBase] = []
        for pm in para_models:
            domain_obj = SectionMapper.to_domain(pm)
            result.append(domain_obj)
        return result