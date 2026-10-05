from typing import Callable, List, Tuple

from bda.domain.enums import SectionFamily, SectionType, TaperVariation
from bda.domain.models.submodels import SectionBase
from bda.domain.models.submodels.sections import (
    DimensionsCompositeSteelISymmetric,
    DimensionsCompositeSteelIAsymmetric,
    DimensionsPSC12Cell,
    SectionCompositeBase,
    SectionCompositeSteelISymmetric,
    SectionCompositeSteelIAsymmetric,
    SectionPSC12Cell,
    SectionPSCBase,
    SectionPSCValue,
    SectionTapered,
    SectionStandard,
    SectionStandardAngle,
    SectionStandardBox,
    SectionStandardChannel,
    SectionStandardISection,
    SectionStandardSolidRectangle,
    SectionStandardSolidRound,
    SectionStandardPipe
)
from bda.domain.units.export_units import ExportUnits, to_float


class CsiSectionExporter:
    def __init__(self, sapModel, eu: ExportUnits):
        self.sapModel = sapModel
        self._eu: ExportUnits = eu

        self.INNER_SHAPE_NAME = 'inner'
        self.OPENING_MAT_NAME = 'Opening'

    def export_section(self, section: SectionBase):
        export_func = self._get_section_exporter_by_section_family(section.section_family)
        if export_func is None:
            raise ValueError(f"Unsupported section family: {section.section_family} "
                             f"for section '{section.name}'")
        export_func(section)

    # REGISTRIES
    def _get_section_exporter_by_section_family(self, section_family: SectionFamily) \
            -> Callable[[SectionBase], None] | None:

        section_exporter_by_section_family = {
            SectionFamily.DB: None,
            SectionFamily.STANDARD_SHAPE: self._export_section_user,
            SectionFamily.COMPOSITE: self._export_composite,
            SectionFamily.PSC: self._export_psc,
            SectionFamily.TAPERED: self._export_tapered,
        }

        export_method = section_exporter_by_section_family.get(section_family, None)
        return export_method


    def _get_section_dbuser_exporter_by_section_type(self, section_type: SectionType) \
            -> Callable[[SectionBase], None] | None:

        section_exporter_by_section_type = {
            SectionType.ANGLE: self._export_angle,
            SectionType.BOX: self._export_box,
            SectionType.CHANNEL: self._export_channel,
            SectionType.SOLID_ROUND: self._export_solid_round,
            SectionType.SOLID_RECTANGLE: self._export_solid_rectangle,
            SectionType.I_SECTION: self._export_i_section,
            SectionType.PIPE: self._export_pipe
        }

        export_method = section_exporter_by_section_type.get(section_type, None)
        return export_method

    def _get_section_composite_exporter_by_section_type(self, section_type: SectionType) \
            -> Callable[[SectionBase], None] | None:

        section_exporter_by_section_type = {
            SectionType.STEEL_I_SYMMETRIC: self._export_composite_steel_I_type_1,
            SectionType.STEEL_I_ASYMMETRIC: self._export_composite_steel_I_type_2,
        }

        export_method = section_exporter_by_section_type.get(section_type, None)
        return export_method


    def _get_section_psc_exporter_by_section_type(self, section_type: SectionType) \
            -> Callable[[SectionBase], None] | None:

        section_exporter_by_section_type = {
            SectionType.PSC_1CELL: self._export_psc_12cell,
            SectionType.PSC_2CELL: self._export_psc_12cell,
            SectionType.PSC_VALUE: self._export_psc_value
        }

        export_method = section_exporter_by_section_type.get(section_type, None)
        return export_method

    # SPECIFIC EXPORT METHODS
    def _export_section_user(self, section: SectionStandard) -> None:
        if not isinstance(section, SectionStandard):
            raise ValueError(f"Invalid section family: {section.section_family} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        dbuser_export = self._get_section_dbuser_exporter_by_section_type(section.section_type)
        if dbuser_export is None:
            raise ValueError(f"Unsupported section type '{section.section_type}' "
                             f"for section family '{section.section_family}' for section '{section.name}'")

        dbuser_export(section)


    def _export_angle(self, section: SectionStandard) -> None:
        sapModel = self.sapModel

        if not isinstance(section, SectionStandardAngle):
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        s: SectionStandardAngle = section
        eu = self._eu
        sapModel.PropFrame.SetAngle_1(s.name, s.material_main.name,
                                      T3=to_float(s.dimensions.height, eu.length),
                                      T2=to_float(s.dimensions.width, eu.length),
                                      Tf=to_float(s.dimensions.thickness_flange, eu.length),
                                      Tw=to_float(s.dimensions.thickness_web, eu.length),
                                      FilletRadius=0)


    def _export_box(self, section: SectionStandard) -> None:
        sapModel = self.sapModel

        if not isinstance(section, SectionStandardBox):
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        s: SectionStandardBox = section
        eu = self._eu
        sapModel.PropFrame.SetTube_1(s.name, s.material_main.name,
                                     T3=to_float(s.dimensions.height_h, eu.length),
                                     T2=to_float(s.dimensions.top_flange_width_b, eu.length),
                                     Tf=to_float(s.dimensions.top_flange_thickness_tf1, eu.length),
                                     Tw=to_float(s.dimensions.web_thickness_tw, eu.length),
                                     Radius=0)


    def _export_channel(self, section: SectionStandard) -> None:
        sapModel = self.sapModel
        if not isinstance(section, SectionStandardChannel):
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        s: SectionStandardChannel = section
        eu = self._eu
        sapModel.PropFrame.SetChannel_2(s.name, s.material_main.name,
                                        T3=to_float(s.dimensions.height_h, eu.length),
                                        T2=to_float(s.dimensions.top_flange_width_b1, eu.length),
                                        Tf=to_float(s.dimensions.top_flange_thickness_tf1, eu.length),
                                        Tw=to_float(s.dimensions.web_thickness_tw, eu.length),
                                        FilletRadius=0,
                                        MirrorAbout2=True)


    def _export_solid_round(self, section: SectionStandard) -> None:
        sapModel = self.sapModel
        if not isinstance(section, SectionStandardSolidRound):
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        s: SectionStandardSolidRound = section
        eu = self._eu
        sapModel.PropFrame.SetCircle(s.name, s.material_main.name,
                                     T3=to_float(s.dimensions.diameter_d, eu.length))


    def _export_solid_rectangle(self, section: SectionStandardSolidRectangle) -> None:
        sapModel = self.sapModel
        if not isinstance(section, SectionStandardSolidRectangle):
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        s: SectionStandardSolidRectangle = section
        eu = self._eu
        sapModel.PropFrame.SetRectangle(s.name, s.material_main.name,
                                        T3=to_float(s.dimensions.height_h, eu.length),
                                        T2=to_float(s.dimensions.width_b, eu.length))


    def _export_i_section(self, section: SectionStandardISection) -> None:
        sapModel = self.sapModel
        if not isinstance(section, SectionStandardISection):
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        s: SectionStandardISection = section
        eu = self._eu
        sapModel.PropFrame.SetISection_1(s.name, s.material_main.name,
                                         T3=to_float(s.dimensions.total_height_h, eu.length),
                                         T2=to_float(s.dimensions.top_flange_width_b1, eu.length),
                                         Tf=to_float(s.dimensions.top_flange_thickness_tf1, eu.length),
                                         Tw=to_float(s.dimensions.web_thickness_tw, eu.length),
                                         T2b=to_float(s.dimensions.bottom_flange_width_b2, eu.length),
                                         Tfb=to_float(s.dimensions.bottom_flange_thickness_tf2, eu.length),
                                         FilletRadius=to_float(s.dimensions.web_inner_radius_r1, eu.length))


    def _export_pipe(self, section: SectionStandardPipe) -> None:
        sapModel = self.sapModel
        if not isinstance(section, SectionStandardPipe):
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        s: SectionStandardPipe = section
        eu = self._eu
        sapModel.PropFrame.SetPipe(s.name, s.material_main.name,
                                   T3=to_float(s.dimensions.external_diameter_d, eu.length),
                                   Tw=to_float(s.dimensions.wall_thickness_tw, eu.length))


    def _export_composite(self, section: SectionCompositeBase) -> None:
        if not isinstance(section, SectionCompositeBase):
            raise ValueError(f"Invalid section family: {section.section_family} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        composite_export = self._get_section_composite_exporter_by_section_type(section.section_type)
        if composite_export is None:
            raise ValueError(f"Unsupported section type '{section.section_type}' "
                             f"for section family '{section.section_family}' for section '{section.name}'")

        composite_export(section)


    def _export_composite_steel_I_type_1(self, section: SectionCompositeSteelISymmetric) -> None:
        sapModel = self.sapModel
        if not isinstance(section, SectionCompositeSteelISymmetric):
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        s: SectionCompositeSteelISymmetric = section
        dim: DimensionsCompositeSteelISymmetric = s.dimensions
        eu = self._eu

        ret = sapModel.PropFrame.SetSDSection(s.name, s.material_main.name, 1)

        ret = sapModel.PropFrame.SDShape.SetSolidRect(Name=s.name, ShapeName='deck', MatProp=s.material_composite.name,
                                                      SSOverwrite="", XCenter=0,
                                                      YCenter=to_float(-0.5 * dim.slab_thickness_tc, eu.length),
                                                      H=to_float(dim.slab_thickness_tc, eu.length),
                                                      W=to_float(dim.slab_width_bc, eu.length), Rotation=0)

        gir_h_total = (dim.girder_web_height_hw + dim.girder_top_flange_thickness_tf1
                       + dim.girder_bottom_flange_thickness_tf2)
        y_center = -1 * dim.slab_thickness_tc - dim.slab_girder_spacing_hh - 0.5 * gir_h_total

        ret = sapModel.PropFrame.SDShape.SetISection(Name=s.name, ShapeName='girder', MatProp=s.material_main.name,
                                                     PropName="", XCenter=0.0,
                                                     YCenter=to_float(y_center, eu.length),
                                                     Rotation=0, Color=-1,
                                                     H=to_float(gir_h_total, eu.length),
                                                     Bf=to_float(dim.girder_top_flange_width_b1, eu.length),
                                                     Tf=to_float(dim.girder_top_flange_thickness_tf1, eu.length),
                                                     Tw=to_float(dim.girder_web_thickness_tw, eu.length),
                                                     Bfb=to_float(dim.girder_bottom_flange_width_b2, eu.length),
                                                     Tfb=to_float(dim.girder_bottom_flange_thickness_tf2, eu.length))

    def _export_composite_steel_I_type_2(self, section: SectionCompositeSteelIAsymmetric) -> None:
        sapModel = self.sapModel
        if not isinstance(section, SectionCompositeSteelIAsymmetric):
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        s: SectionCompositeSteelIAsymmetric = section
        dim: DimensionsCompositeSteelIAsymmetric = s.dimensions
        eu = self._eu
        _f = lambda q: to_float(q, eu.length)

        ret = sapModel.PropFrame.SetSDSection(s.name, s.material_main.name, 1)

        ret = sapModel.PropFrame.SDShape.SetSolidRect(Name=s.name, ShapeName='deck', MatProp=s.material_composite.name,
                                                      SSOverwrite="",
                                                      XCenter=_f(0.5 * dim.slab_width_bc + dim.slab_distance_rf_sg),
                                                      YCenter=_f(-0.5 * dim.slab_thickness_tc),
                                                      H=_f(dim.slab_thickness_tc),
                                                      W=_f(dim.slab_width_bc), Rotation=0)

        # assemble the steel section from rectangles and polyline
        # top flange
        tf_width_tot = dim.girder_top_flange_left_width_b1 + dim.girder_top_flange_right_width_b2
        ver_offset_top = (dim.slab_thickness_tc + dim.slab_girder_spacing_hh
                          + 0.5 * dim.girder_top_flange_thickness_t1)

        ret = sapModel.PropFrame.SDShape.SetSolidRect(Name=s.name, ShapeName='top flange', MatProp=s.material_main.name,
                                                      SSOverwrite="",
                                                      XCenter=_f(0.5 * tf_width_tot + dim.top_flange_distance_rf_top),
                                                      YCenter=_f(-ver_offset_top),
                                                      H=_f(dim.girder_top_flange_thickness_t1),
                                                      W=_f(tf_width_tot), Rotation=0)

        # bottom flange
        bf_width_tot = dim.girder_bottom_flange_left_width_b3 + dim.girder_bottom_flange_right_width_b4
        ver_offset_bottom = (dim.slab_thickness_tc + dim.slab_girder_spacing_hh
                             + dim.girder_top_flange_thickness_t1 + dim.girder_web_height_h
                             + 0.5 * dim.girder_bottom_flange_thickness_t2)

        ret = sapModel.PropFrame.SDShape.SetSolidRect(Name=s.name, ShapeName='bottom flange',
                                                      MatProp=s.material_main.name,
                                                      SSOverwrite="",
                                                      XCenter=_f(0.5 * bf_width_tot + dim.bottom_flange_distance_rf_bot),
                                                      YCenter=_f(-ver_offset_bottom),
                                                      H=_f(dim.girder_bottom_flange_thickness_t2),
                                                      W=_f(bf_width_tot), Rotation=0)

        # web - may be skewed/inclined so polyline method is used
        tw_half = 0.5 * dim.girder_web_thickness_tw
        b1 = dim.girder_top_flange_left_width_b1
        b3 = dim.girder_bottom_flange_left_width_b3

        X_coords = [
            _f(dim.top_flange_distance_rf_top + b1 - tw_half),
            _f(dim.top_flange_distance_rf_top + b1 + tw_half),
            _f(dim.bottom_flange_distance_rf_bot + b3 + tw_half),
            _f(dim.bottom_flange_distance_rf_bot + b3 - tw_half),
        ]

        Y_coords = [
            _f(-ver_offset_top - 0.5 * dim.girder_top_flange_thickness_t1),
            _f(-ver_offset_top - 0.5 * dim.girder_top_flange_thickness_t1),
            _f(-ver_offset_bottom + 0.5 * dim.girder_bottom_flange_thickness_t2),
            _f(-ver_offset_bottom + 0.5 * dim.girder_bottom_flange_thickness_t2),
        ]

        radius = [0, 0, 0, 0]

        ret = sapModel.PropFrame.SDShape.SetPolygon(Name=s.name, ShapeName='web', MatProp=s.material_main.name,
                                                    SSOverwrite="", NumberPoints=4,
                                                    X=X_coords, Y=Y_coords, Radius=radius)

    def _export_psc(self, section: SectionPSCBase) -> None:
        if not isinstance(section, SectionPSCBase):
            raise ValueError(f"Invalid section family: {section.section_family} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        psc_export = self._get_section_psc_exporter_by_section_type(section.section_type)

        if psc_export is None:
            raise ValueError(f"Unsupported section type '{section.section_type}' "
                             f"for section family '{section.section_family}' for section '{section.name}'")

        psc_export(section)

    def _export_psc_12cell(self, section: SectionPSC12Cell) -> None:
        if not isinstance(section, SectionPSC12Cell):
            raise ValueError(f"Invalid section family: {section.section_family} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        s: SectionPSC12Cell = section
        eu = self._eu
        # create a SD section (design type 3 - Design as a concrete column; design the reinforcing)
        ret = self.sapModel.PropFrame.SetSDSection(s.name, s.material_main.name, 3)

        # create outline polyline
        o_vs = self._generate_outer_vertices_for_psc(s.dimensions)
        X_coords = [to_float(v[0], eu.length) for v in o_vs]
        Y_coords = [to_float(v[1], eu.length) for v in o_vs]
        radius = [0 for _ in o_vs]
        number = len(o_vs)
        ret = self.sapModel.PropFrame.SDShape.SetPolygon(Name=s.name, ShapeName='outer', MatProp=s.material_main.name,
                                                        SSOverwrite="", NumberPoints=number,
                                                        X=X_coords, Y=Y_coords, Radius=radius)

        # create inner polyline(s)
        if section.section_type == SectionType.PSC_1CELL:
            in_vs = self._generate_inner_vertices_for_psc_1cell(s.dimensions)
            X_coords = [to_float(v[0], eu.length) for v in in_vs]
            Y_coords = [to_float(v[1], eu.length) for v in in_vs]
            radius = [0 for _ in in_vs]
            number = len(in_vs)
            ret = self.sapModel.PropFrame.SDShape.SetPolygon(Name=s.name,
                                                             ShapeName=f'{self.INNER_SHAPE_NAME}',
                                                             MatProp=s.material_main.name,
                                                             SSOverwrite="", NumberPoints=number,
                                                             X=X_coords, Y=Y_coords, Radius=radius)
            self._replace_void_shape_with_opening(s.name)

        elif section.section_type == SectionType.PSC_2CELL:
            in_vss = self._generate_inner_vertices_for_psc_2cell(s.dimensions)
            i=0
            for in_vs in in_vss:
                i+=1
                X_coords = [to_float(v[0], eu.length) for v in in_vs]
                Y_coords = [to_float(v[1], eu.length) for v in in_vs]
                radius = [0 for _ in in_vs]
                number = len(in_vs)
                ret = self.sapModel.PropFrame.SDShape.SetPolygon(Name=s.name,
                                                                 ShapeName=f'{self.INNER_SHAPE_NAME}{i}',
                                                                 MatProp=s.material_main.name,
                                                                 SSOverwrite="", NumberPoints=number,
                                                                 X=X_coords, Y=Y_coords, Radius=radius)
            self._replace_void_shape_with_opening(s.name)

        else:
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"for section family '{section.section_family}' of section '{section.name}'")


    def _export_psc_value(self, section: SectionPSCValue) -> None:
        if not isinstance(section, SectionPSCValue):
            raise ValueError(f"Invalid section family: {section.section_family} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        s: SectionPSCValue = section
        eu = self._eu
        # create a SD section (design type 3 - Design as a concrete column; design the reinforcing)
        ret = self.sapModel.PropFrame.SetSDSection(s.name, s.material_main.name, 3)

        # create outline polyline
        o_vs = s.dimensions.outer_outline
        X_coords = [to_float(v.x, eu.length) for v in o_vs]
        Y_coords = [to_float(v.y, eu.length) for v in o_vs]
        radius = [0 for _ in o_vs]
        number = len(o_vs)
        ret = self.sapModel.PropFrame.SDShape.SetPolygon(Name=s.name, ShapeName='outer',
                                                         MatProp=s.material_main.name,
                                                         SSOverwrite="", NumberPoints=number,
                                                         X=X_coords, Y=Y_coords, Radius=radius)

        in_vss = s.dimensions.inner_outlines
        i = 0
        for in_vs in in_vss:
            i += 1
            X_coords = [to_float(v.x, eu.length) for v in in_vs]
            Y_coords = [to_float(v.y, eu.length) for v in in_vs]
            radius = [0 for _ in in_vs]
            number = len(in_vs)
            ret = self.sapModel.PropFrame.SDShape.SetPolygon(Name=s.name,
                                                             ShapeName=f'{self.INNER_SHAPE_NAME}{i}',
                                                             MatProp=s.material_main.name,
                                                             SSOverwrite="", NumberPoints=number,
                                                             X=X_coords, Y=Y_coords, Radius=radius)
        self._replace_void_shape_with_opening(s.name)


    def _export_tapered(self, section: SectionTapered) -> None:
        if not isinstance(section, SectionTapered):
            raise ValueError(f"Invalid section family: {section.section_family} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")
        sapModel = self.sapModel

        s: SectionTapered = section

        n_items = 1
        start_sec = [s.section_start.name]
        end_sec = [s.section_end.name]

        lengths = [1.0]
        types = [1] # Variable (relative length), 2-Absolute
        ei33 = [self._get_csi_variation_for_tapered(s.taper_z_variation)]
        ei22 = [self._get_csi_variation_for_tapered(s.taper_y_variation)]

        sapModel.PropFrame.SetNonPrismatic(s.name, n_items, start_sec, end_sec, lengths, types, ei33, ei22)


    @staticmethod
    def _generate_inner_vertices_for_psc_1cell(dimensions: DimensionsPSC12Cell) \
            -> List[Tuple[float, float]]:
        j = dimensions.joints
        ji1, ji2, ji3, ji4, ji5 = j.ji1, j.ji2, j.ji3, j.ji4, j.ji5
        hi = dimensions.inner_height_hi
        hi1, hi2, hi2_1, hi2_2, hi3, hi3_1, hi4, hi4_1, hi4_2, hi5 = (
            hi.hi1, hi.hi2, hi.hi2_1, hi.hi2_2, hi.hi3, hi.hi3_1,
            hi.hi4, hi.hi4_1, hi.hi4_2, hi.hi5)
        bi = dimensions.inner_breadth_bi
        bi1, bi1_1, bi1_2, bi2_1, bi3, bi3_1, bi3_2, bi4 = (
            bi.bi1, bi.bi1_1, bi.bi1_2, bi.bi2_1, bi.bi3, bi.bi3_1,
            bi.bi3_2, bi.bi4)
        ho = dimensions.outer_height_ho
        ho1, ho2, ho2_1, ho2_2, ho3, ho3_1 = (
            ho.ho1, ho.ho2, ho.ho2_1, ho.ho2_2, ho.ho3, ho.ho3_1)

        # assume top center as 0,0, direction -> clockwise
        h_tot = ho1+ho2+ho3
        hi_tot = hi1+hi2+hi3+hi4+hi5
        y_ref =-h_tot+hi_tot
        _zero = ho1 * 0  # zero with matching Quantity dimensionality

        vertices: List[Tuple[float, float]] = [
            (_zero, y_ref-hi1),
        ]

        if ji1: vertices.append((bi1_1, y_ref-hi1-hi2_1))
        if ji2: vertices.append((bi1_2, y_ref-hi1-hi2_2))

        vertices.append((bi1, y_ref-hi1-hi2))

        if ji3: vertices.append((bi2_1, y_ref-hi1-hi2-hi3_1))

        vertices.append((bi3, y_ref-hi1-hi2-hi3))

        if ji4: vertices.append((bi3_2, y_ref-hi1-hi2-hi3-hi4+hi4_2))
        if ji5: vertices.append((bi3_1, y_ref-hi1-hi2-hi3-hi4+hi4_1))

        vertices.append((_zero, y_ref-hi1-hi2-hi3-hi4+hi4_1))

        # rest of vertices are symmetrical:
        if ji5: vertices.append((-bi3_1, y_ref-hi1-hi2-hi3-hi4+hi4_1))
        if ji4: vertices.append((-bi3_2, y_ref-hi1-hi2-hi3-hi4+hi4_2))
        vertices.append((-bi3, y_ref-hi1-hi2-hi3))
        if ji3: vertices.append((-bi2_1, y_ref-hi1-hi2-hi3_1))
        vertices.append((-bi1, y_ref-hi1-hi2))
        if ji2: vertices.append((-bi1_2, y_ref-hi1-hi2_2))
        if ji1: vertices.append((-bi1_1, y_ref-hi1-hi2_1))

        return vertices

    @staticmethod
    def _generate_inner_vertices_for_psc_2cell(dimensions: DimensionsPSC12Cell) \
            -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        j = dimensions.joints
        ji1, ji2, ji3, ji4, ji5 = j.ji1, j.ji2, j.ji3, j.ji4, j.ji5
        hi = dimensions.inner_height_hi
        hi1, hi2, hi2_1, hi2_2, hi3, hi3_1, hi4, hi4_1, hi4_2, hi5 = (
            hi.hi1, hi.hi2, hi.hi2_1, hi.hi2_2, hi.hi3, hi.hi3_1,
            hi.hi4, hi.hi4_1, hi.hi4_2, hi.hi5)
        bi = dimensions.inner_breadth_bi
        bi1, bi1_1, bi1_2, bi2_1, bi3, bi3_1, bi3_2, bi4 = (
            bi.bi1, bi.bi1_1, bi.bi1_2, bi.bi2_1, bi.bi3, bi.bi3_1,
            bi.bi3_2, bi.bi4)
        ho = dimensions.outer_height_ho
        ho1, ho2, ho2_1, ho2_2, ho3, ho3_1 = (
            ho.ho1, ho.ho2, ho.ho2_1, ho.ho2_2, ho.ho3, ho.ho3_1)

        # assume top center as 0,0, direction -> clockwise

        # use vertices for psc 1cell and modify them
        vertices = CsiSectionExporter._generate_inner_vertices_for_psc_1cell(dimensions)
        no_of_vertices = len(vertices)

        h_tot = ho1 + ho2 + ho3
        hi_tot = hi1 + hi2 + hi3 + hi4 + hi5
        y_ref = -h_tot + hi_tot

        vertices_right: List[Tuple[float, float]] = vertices[:int(no_of_vertices/2)]
        vertices_right[0] = (bi4, y_ref-hi1)
        vertices_right.append((bi4, y_ref-hi_tot+hi5))

        vertices_left: List[Tuple[float, float]] = vertices[int(no_of_vertices/2):]
        vertices_left[0] = (-bi4, y_ref-hi_tot+hi5)
        vertices_left.append((-bi4, y_ref-hi1))

        return vertices_right, vertices_left


    @staticmethod
    def _generate_outer_vertices_for_psc(dimensions: DimensionsPSC12Cell) \
            -> List[Tuple[float, float]]:
        j = dimensions.joints
        jo1, jo2, jo3 = j.jo1, j.jo2, j.jo3
        hi = dimensions.inner_height_hi
        hi1, hi2, hi2_1, hi2_2, hi3, hi3_1, hi4, hi4_1, hi4_2, hi5 = (
            hi.hi1, hi.hi2, hi.hi2_1, hi.hi2_2, hi.hi3, hi.hi3_1,
            hi.hi4, hi.hi4_1, hi.hi4_2, hi.hi5)
        ho = dimensions.outer_height_ho
        ho1, ho2, ho2_1, ho2_2, ho3, ho3_1 = (
            ho.ho1, ho.ho2, ho.ho2_1, ho.ho2_2, ho.ho3, ho.ho3_1)
        bo = dimensions.outer_breadth_bo
        bo1, bo1_1, bo1_2, bo2, bo2_1, bo3 = (
            bo.bo1, bo.bo1_1, bo.bo1_2, bo.bo2, bo.bo2_1, bo.bo3)

        # assume top center as 0,0, direction -> clockwise

        # helpers
        tot_w = bo1+bo2+bo3
        tot_h = ho1+ho2+ho3
        hi_tot = hi1 + hi2 + hi3 + hi4 + hi5
        y_ref = -tot_h + hi_tot
        _zero = ho1 * 0  # zero with matching Quantity dimensionality

        vertices: List[Tuple[float, float]] = [
            (_zero, y_ref),
            (tot_w, _zero),
            (tot_w, -ho1),
        ]

        if jo1: vertices.append((tot_w-bo1_1, -ho1-ho2_1))
        if jo2: vertices.append((tot_w-bo1_2, -ho1-ho2_2))

        vertices.append((tot_w-bo1, -ho1-ho2))

        if jo3: vertices.append((tot_w-bo1-bo2+bo2_1, -tot_h+ho3_1))

        vertices.append((tot_w-bo1-bo2, -tot_h))

        # rest of vertices are symmetrical:
        vertices.append((-tot_w+bo1+bo2, -tot_h))
        if jo3: vertices.append((-tot_w+bo1+bo2-bo2_1, -tot_h+ho3_1))
        vertices.append((-tot_w+bo1, -ho1-ho2))
        if jo2: vertices.append((-tot_w+bo1_2, -ho1-ho2_2))
        if jo1: vertices.append((-tot_w+bo1_1, -ho1-ho2_1))
        vertices.append((-tot_w, -ho1))
        vertices.append((-tot_w, _zero))

        return vertices

    def _replace_void_shape_with_opening(self, sectionName: str):
        sapModel = self.sapModel
        SDKEY = 'Section Designer Properties 16 - Shape Polygon'.lower()
        nTables, tableKeys, tableNames, importTypes, ret = sapModel.DatabaseTables.GetAvailableTables()

        lookingKey = next((key for key in tableKeys if SDKEY in key.lower()), None)
        if lookingKey is None:
            raise ValueError(f"Failed to update voids in section {sectionName}")

        ver, fields, n_records, data, ret = sapModel.DatabaseTables.GetTableForEditingArray(lookingKey, 'group')
        n_fields = len(fields)

        data_list_2d = [list(data[i:i + n_fields]) for i in range(0, len(data), n_fields)]
        data_list1d = list(data)

        i = -1
        for row in data_list_2d:
            i += 1
            if (sectionName.lower() in row[0].lower()
                    and self.INNER_SHAPE_NAME.lower() in row[1].lower()
                    and len(row[5]) > 0):
                data_list1d[i*n_fields + 5] = self.OPENING_MAT_NAME

        ver, fields, data_rev, ret2 = sapModel.DatabaseTables.SetTableForEditingArray(lookingKey, ver, fields,
                                                                                      len(data_list1d), data_list1d)

        n_errors, n_err_msgs, n_warn_msgs, n_info_msgs, log, ret3 = sapModel.DatabaseTables.ApplyEditedTables(False)

    @staticmethod
    def _get_csi_variation_for_tapered(variation: TaperVariation) -> int:

        variations = {
            TaperVariation.LINEAR: 1,
            TaperVariation.PARABOLIC: 2,
            TaperVariation.CUBIC: 3
        }

        var = variations.get(variation, None)
        if var is None:
            raise ValueError(f"Section variation {variation} is not supported.")

        return var