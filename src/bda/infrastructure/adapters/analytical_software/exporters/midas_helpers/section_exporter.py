from typing import Callable

from bda.domain.enums import OffsetReference, SectionFamily, SectionType, TaperVariation
from bda.domain.models.submodels import MaterialBase, SectionBase
from bda.domain.models.submodels.material import GeneralMaterialIsotropicProperties
from bda.domain.models.submodels.section_base import Offset as DomainOffset
from bda.domain.models.submodels.sections import *
from bda.domain.units.export_units import ExportUnits, to_float
from bda.infrastructure.utils import AppLogger


class MidasSectionExporter:

    def __init__(self, eu: ExportUnits):
        self.logger = AppLogger()
        self._eu = eu
        from midas_civil import Section, Offset
        self.MidasSection = Section
        self.MidasOffset = Offset

    # ------------------------------------------------------------------
    # REGISTRIES (instance – reference bound methods)
    # ------------------------------------------------------------------

    def _get_section_exporter_by_section_family(self, section_family: SectionFamily) \
            -> Callable[[SectionBase], None] | None:
        registry = {
            SectionFamily.DB: self._export_section_db,
            SectionFamily.STANDARD_SHAPE: self._export_section_standard_shape,
            SectionFamily.COMPOSITE: self._export_composite,
            SectionFamily.PSC: self._export_psc,
            SectionFamily.TAPERED: self._export_tapered,
        }
        return registry.get(section_family, None)

    @staticmethod
    def _get_section_shape_by_section_type(section_type: SectionType) -> str | None:
        return {
            SectionType.ANGLE: "L",
            SectionType.I_SECTION: "H",
            SectionType.BOX: "B",
            SectionType.CHANNEL: "C",
            SectionType.SOLID_RECTANGLE: "SB",
            SectionType.SOLID_ROUND: "SR",
            SectionType.PIPE: "P"
        }.get(section_type, None)

    @staticmethod
    def _get_section_cell_shape_by_section_type(section_type: SectionType) -> str | None:
        return {
            SectionType.PSC_1CELL: "1CEL",
            SectionType.PSC_2CELL: "2CEL",
        }.get(section_type, None)

    # ------------------------------------------------------------------
    # MAIN EXPORT METHOD
    # ------------------------------------------------------------------

    def export_section(self, section: SectionBase) -> None:
        self.logger.debug("Exporting section %s", section.name)
        section.name = self._normalize_name(section.name)
        export_func = self._get_section_exporter_by_section_family(section.section_family)
        if export_func is None:
            raise ValueError(f"Unsupported section family: {section.section_family} "
                             f"for section '{section.name}'")
        export_func(section)
        self.logger.debug("Section %s successfully exported", section.name)

    # ------------------------------------------------------------------
    # SPECIFIC EXPORT METHODS
    # ------------------------------------------------------------------

    def _export_section_db(self, section: SectionDB) -> None:
        # TODO: standard/profile mapping not included for MVP
        if not isinstance(section, SectionDB):
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        db_shape = self._get_section_shape_by_section_type(section.section_type)
        if db_shape is None:
            raise ValueError(f"Unsupported section type for DB export: {section.section_type} "
                             f"for section '{section.name}'")

        try:
            offset = self._get_section_offset(section.offset)
        except ValueError as e:
            raise ValueError(f"{e} for section '{section.name}'")

        self.MidasSection.DB(section.name,
                             Shape=db_shape,
                             DB_Name=section.standard,
                             Sect_Name=section.profile_name,
                             Offset=offset,
                             id=section.model_id)

    def _export_section_standard_shape(self, section: SectionStandard) -> None:
        eu = self._eu
        if not isinstance(section, SectionStandard):
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        db_shape = self._get_section_shape_by_section_type(section.section_type)
        if db_shape is None:
            raise ValueError(f"Unsupported section type for User export: {section.section_type} "
                             f"for section '{section.name}'")

        offset = self._get_section_offset(section.offset)

        parameters = self._get_section_parameters(section, eu)
        if parameters is None or len(parameters) == 0:
            raise ValueError(f"Unsupported section parameters for User export: {section.section_type} ")

        self.MidasSection.DBUSER(section.name,
                                 Shape=db_shape,
                                 parameters=parameters,
                                 Offset=offset,
                                 id=section.model_id)

    def _export_composite(self, section: SectionCompositeBase) -> None:
        eu = self._eu
        if not isinstance(section, SectionCompositeBase):
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        if section.material_main is None:
            raise ValueError(f"Material main for section '{section.name}' "
                             f"is missing. Export is not possible.")
        if section.material_composite is None:
            raise ValueError(f"Material composite for section '{section.name}' "
                             f"is missing. Export is not possible.")

        mat1: MaterialBase = section.material_main
        mat2: MaterialBase = section.material_composite

        if isinstance(mat1.general_properties, GeneralMaterialIsotropicProperties) and \
                isinstance(mat2.general_properties, GeneralMaterialIsotropicProperties):
            m1prop: GeneralMaterialIsotropicProperties = mat1.general_properties
            m2prop: GeneralMaterialIsotropicProperties = mat2.general_properties
        else:
            raise NotImplementedError("Non isotropic materials are not supported in composite sections")

        density_ratio = 0.0 if (
                (m1_weight := to_float(m2prop.unit_weight, eu.weight_density)) >
                10 ** -6 * (m2_weight := to_float(m1prop.unit_weight, eu.weight_density))
        ) else m1_weight / m2_weight


        match section.section_type:

            case SectionType.STEEL_I_SYMMETRIC:
                if not isinstance(section, SectionCompositeSteelISymmetric):
                    raise ValueError(f"Invalid section type: {section.section_type} "
                                     f"Unsupported type: {type(section)} for section '{section.name}'")
                s: SectionCompositeSteelISymmetric = section
                d: DimensionsCompositeSteelISymmetric = s.dimensions

                self.MidasSection.Composite.SteelI_Type1(
                    Name=s.name,
                    Bc=to_float(d.slab_width_bc, eu.length),
                    tc=to_float(d.slab_thickness_tc, eu.length),
                    Hh=to_float(d.slab_girder_spacing_hh, eu.length),
                    Hw=to_float(d.girder_web_height_hw, eu.length),
                    B1=to_float(d.girder_top_flange_width_b1, eu.length),
                    tf1=to_float(d.girder_top_flange_thickness_tf1, eu.length),
                    tw=to_float(d.girder_web_thickness_tw, eu.length),
                    B2=to_float(d.girder_bottom_flange_width_b2, eu.length),
                    tf2=to_float(d.girder_bottom_flange_thickness_tf2, eu.length),
                    EsEc=to_float(m1prop.modulus_of_elasticity, eu.pressure)
                         / to_float(m2prop.modulus_of_elasticity, eu.pressure),
                    DsDc=density_ratio,
                    Ps=m1prop.poissons_ratio,
                    Pc=m2prop.poissons_ratio,
                    TsTc=to_float(m1prop.thermal_coefficient, eu.temperature_coef)
                         / to_float(m2prop.thermal_coefficient, eu.temperature_coef),
                    Offset=self._get_section_offset(section.offset),
                    id=s.model_id,
                )


            case SectionType.STEEL_I_ASYMMETRIC:
                if not isinstance(section, SectionCompositeSteelIAsymmetric):
                    raise ValueError(f"Invalid section type: {section.section_type} "
                                     f"Unsupported type: {type(section)} for section '{section.name}'")
                s: SectionCompositeSteelIAsymmetric = section
                d: DimensionsCompositeSteelIAsymmetric = s.dimensions

                json_db = {
                            "SECTTYPE": "COMPOSITE",
                            "SECT_NAME": s.name,
                            "SECT_BEFORE": {
                                "OFFSET_PT": self._get_section_offset_string(section.offset.offset_reference),
                                "HORZ_OFFSET_OPT": 1,
                                "USERDEF_OFFSET_YI": to_float(section.offset.horizontal_value, eu.length),
                                "VERT_OFFSET_OPT": 1,
                                "USERDEF_OFFSET_ZI": to_float(section.offset.vertical_value, eu.length),
                                "USER_OFFSET_REF": 1,
                                "SHAPE": "GI",
                                "SECT_I": {
                                    "vSIZE": [
                                        to_float(d.girder_top_flange_left_width_b1, eu.length),
                                        to_float(d.girder_top_flange_right_width_b2, eu.length),
                                        to_float(d.girder_bottom_flange_left_width_b3, eu.length),
                                        to_float(d.girder_bottom_flange_right_width_b4, eu.length),
                                        to_float(d.girder_web_height_h, eu.length),
                                        to_float(d.girder_top_flange_thickness_t1, eu.length),
                                        to_float(d.girder_bottom_flange_thickness_t2, eu.length),
                                        to_float(d.girder_web_thickness_tw, eu.length),
                                    ],
                                },
                                "MATL_ELAST": to_float(m1prop.modulus_of_elasticity, eu.pressure)
                                              / to_float(m2prop.modulus_of_elasticity, eu.pressure),
                                "MATL_DENS": density_ratio,
                                "MATL_POIS_S": m1prop.poissons_ratio,
                                "MATL_POIS_C": m2prop.poissons_ratio,
                                "MATL_THERMAL": to_float(m1prop.thermal_coefficient, eu.temperature_coef)
                                                / to_float(m2prop.thermal_coefficient, eu.temperature_coef),
                            },
                            "SECT_AFTER": {
                                "SECT_I": {
                                    "vSIZE": [
                                        to_float(d.slab_distance_rf_sg, eu.length),
                                        to_float(d.top_flange_distance_rf_top, eu.length),
                                        to_float(d.bottom_flange_distance_rf_bot, eu.length),
                                    ]
                                },
                                "SLAB": [
                                    to_float(d.slab_width_bc, eu.length),
                                    to_float(d.slab_thickness_tc, eu.length),
                                    to_float(d.slab_girder_spacing_hh, eu.length),
                                ]
                            }
                }

                # A method provided by Midas Support to locally create a cross-section
                # that is not supported by the Midas Civil Python library, add it to the in-memory model,
                # and then export it together with all other model elements in a single operation
                # instead of sending it directly to Midas Civil NX every single time.
                from midas_civil._section import _SS_UNSUPP
                unSpecSec = _SS_UNSUPP(
                    s.model_id,
                    s.name,
                    json_db['SECTTYPE'],
                    json_db['SECT_BEFORE']['SHAPE'],
                    self._get_section_offset(s.offset),
                    True,
                    True,
                    json_db
                )

                self.MidasSection.sect.append(unSpecSec)
                self.MidasSection.ids.append(int(unSpecSec.ID))

                # # Previous code in case of any issues with the above method
                # section_id = s.model_id
                # from midas_civil import MidasAPI
                # MidasAPI(method="PUT", command="/db/SECT", body={"Assign": {section_id: json_db}})

            case _:
                raise ValueError(f"Invalid section type: {section.section_type} "
                                 f"for composite section '{section.name}'")

    def _export_psc(self, section: SectionPSCBase) -> None:
        eu = self._eu
        if not isinstance(section, SectionPSCBase):
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        match section.section_type:

            case SectionType.PSC_VALUE:
                if not isinstance(section, SectionPSCValue):
                    raise ValueError(f"Invalid section type: {section.section_type} "
                                     f"Unsupported type: {type(section)} for section '{section.name}'")
                s: SectionPSCValue = section
                d: DimensionsPSCValues = s.dimensions

                # Convert Point2D lists to (float, float) tuples
                outer_polygon = [(to_float(p.x, eu.length), to_float(p.y, eu.length))
                                 for p in d.outer_outline]
                inner_polygons = [[(to_float(p.x, eu.length), to_float(p.y, eu.length))
                                   for p in inner]
                                  for inner in d.inner_outlines]

                self.MidasSection.PSC.Value(
                    Name=s.name,
                    OuterPolygon=outer_polygon,
                    InnerPolygon=inner_polygons,
                    Offset=self._get_section_offset(section.offset),
                    id=s.model_id,
                )

            case SectionType.PSC_1CELL | SectionType.PSC_2CELL:
                if not isinstance(section, SectionPSC12Cell):
                    raise ValueError(f"Invalid section type: {section.section_type} "
                                     f"Unsupported type: {type(section)} for section '{section.name}'")

                cell_type = self._get_section_cell_shape_by_section_type(section.section_type)
                if cell_type is None:
                    raise ValueError(f"Invalid section type: {section.section_type} "
                                     f"Unsupported type: {type(section)} for section '{section.name}'")

                s: SectionPSC12Cell = section
                d: DimensionsPSC12Cell = s.dimensions
                ho = d.outer_height_ho
                bo = d.outer_breadth_bo
                hi = d.inner_height_hi
                bi = d.inner_breadth_bi

                self.MidasSection.PSC.CEL12(
                    Name=s.name,
                    Shape=cell_type,
                    Joint=[1 if x else 0 for x in d.joints.to_list()],
                    HO1=to_float(ho.ho1, eu.length),
                    HO2=to_float(ho.ho2, eu.length),
                    HO21=to_float(ho.ho2_1, eu.length),
                    HO22=to_float(ho.ho2_2, eu.length),
                    HO3=to_float(ho.ho3, eu.length),
                    HO31=to_float(ho.ho3_1, eu.length),
                    BO1=to_float(bo.bo1, eu.length),
                    BO11=to_float(bo.bo1_1, eu.length),
                    BO12=to_float(bo.bo1_2, eu.length),
                    BO2=to_float(bo.bo2, eu.length),
                    BO21=to_float(bo.bo2_1, eu.length),
                    BO3=to_float(bo.bo3, eu.length),
                    HI1=to_float(hi.hi1, eu.length),
                    HI2=to_float(hi.hi2, eu.length),
                    HI21=to_float(hi.hi2_1, eu.length),
                    HI22=to_float(hi.hi2_2, eu.length),
                    HI3=to_float(hi.hi3, eu.length),
                    HI31=to_float(hi.hi3_1, eu.length),
                    HI4=to_float(hi.hi4, eu.length),
                    HI41=to_float(hi.hi4_1, eu.length),
                    HI42=to_float(hi.hi4_2, eu.length),
                    HI5=to_float(hi.hi5, eu.length),
                    BI1=to_float(bi.bi1, eu.length),
                    BI11=to_float(bi.bi1_1, eu.length),
                    BI12=to_float(bi.bi1_2, eu.length),
                    BI21=to_float(bi.bi2_1, eu.length),
                    BI3=to_float(bi.bi3, eu.length),
                    BI31=to_float(bi.bi3_1, eu.length),
                    BI32=to_float(bi.bi3_2, eu.length),
                    BI4=to_float(bi.bi4, eu.length) if s.section_type == SectionType.PSC_2CELL else 0,
                    Offset=self._get_section_offset(section.offset),
                    id=s.model_id,
                )

            case _:
                raise ValueError(f"Invalid section type: {section.section_type} "
                                 f"Unsupported type: {type(section)} for section '{section.name}'")

    def _export_tapered(self, section: SectionTapered) -> None:
        if not isinstance(section, SectionTapered):
            raise ValueError(f"Invalid section type: {section.section_type} "
                             f"Unsupported type: {type(section)} for section '{section.name}'")

        if section.section_start.section_type != section.section_end.section_type \
                or section.section_start.section_family != section.section_end.section_family:
            raise ValueError(f"Invalid tapered section definition for section: {section.name} "
                             f"Start and end section type and section family must be the same.")
        section.section_type = section.section_start.section_type

        export_json = self.MidasSection.json()
        exported_sections = export_json.get("Assign", None)
        if exported_sections is None or len(exported_sections) < 2:
            raise ValueError(f"Failed to export tapered section for section: {section.name} "
                             f"Base sections for tapered section have not been found.")
        exported_sections: dict = dict(exported_sections)

        start_section = self._find_exported_base_section(
            exported_sections,
            section.section_start.model_id,
            section.section_start.name,
        )
        end_section = self._find_exported_base_section(
            exported_sections,
            section.section_end.model_id,
            section.section_end.name,
        )

        if start_section is None or end_section is None:
            raise ValueError(f"Invalid section definition for section: {section.name} "
                             f"Base sections for tapered section have not been found.")

        # Combine and modify json to define tapered section
        json_tapered: dict = dict(start_section)
        try:
            self._adjust_json_for_tapered_section(section,
                                                  section.section_start.section_family,
                                                  json_tapered,
                                                  end_section)


            # A method provided by Midas Support to locally create a cross-section
            # that is not supported by the Midas Civil Python library, add it to the in-memory model,
            # and then export it together with all other model elements in a single operation
            # instead of sending it directly to Midas Civil NX every single time.
            from midas_civil._section import _SS_UNSUPP
            unSpecSec = _SS_UNSUPP(
                section.model_id,
                section.name,
                json_tapered['SECTTYPE'],
                json_tapered['SECT_BEFORE']['SHAPE'],
                self._get_section_offset(section.offset),
                True,
                True,
                json_tapered
            )

            self.MidasSection.sect.append(unSpecSec)
            self.MidasSection.ids.append(int(unSpecSec.ID))

            # # Previous code in case of any issues with the above method
            # final_json = {'Assign': {str(section.model_id): json_tapered}}
            #
            # from midas_civil import MidasAPI
            # MidasAPI(method='PUT', command='/db/SECT', body=final_json)

        except Exception as e:
            raise Exception(f"Failed to export tapered section for section: {section.name} "
                            f"Error message: {e}")

    # ------------------------------------------------------------------
    # HELPERS FOR TAPERED SECTIONS
    # ------------------------------------------------------------------

    @staticmethod
    def _find_exported_base_section(exported_sections: dict, section_id: int, section_name: str) -> dict | None:
        section_json = exported_sections.get(str(section_id), None)
        if section_json is None:
            section_json = exported_sections.get(section_id, None)
        if not isinstance(section_json, dict):
            return None

        # Avoid false positives when the same id already exists in MIDAS with a different section.
        expected_name = MidasSectionExporter._normalize_name(section_name)
        if section_json.get('SECT_NAME', None) != expected_name:
            return None

        return section_json

    def _adjust_json_for_tapered_section(self, s_tap: SectionTapered, s_family: SectionFamily,
                                         s_tap_json: dict, s_end_json: dict) -> None:
        s_tap_json['SECTTYPE'] = 'TAPERED'
        s_tap_json['SECT_NAME'] = self._normalize_name(s_tap.name)

        taperVarY = self._get_taper_variation(s_tap.taper_y_variation)
        taperVarZ = self._get_taper_variation(s_tap.taper_z_variation)

        s_tap_json['SECT_BEFORE']['Y_VAR'] = taperVarY
        s_tap_json['SECT_BEFORE']['Z_VAR'] = taperVarZ

        try:
            adjust_method = self._get_json_adjuster_for_tapered_section(s_family)
            adjust_method(s_tap, s_tap_json, s_end_json)
        except Exception as e:
            raise Exception(f"Failed to adjust tapered section for section: {s_tap.name} "
                            f"Error message: {e}")

    def _get_json_adjuster_for_tapered_section(self, s_family: SectionFamily) -> Callable[[SectionTapered, dict, dict], None]:
        json_adjusters_by_section_type = {
            SectionFamily.DB: self._adjust_db_user_tapered_json,
            SectionFamily.STANDARD_SHAPE: self._adjust_db_user_tapered_json,
            SectionFamily.COMPOSITE: self._adjust_composite_steel_tapered_json,
            SectionFamily.PSC: self._adjust_psc_tapered_json,
        }
        adjuster = json_adjusters_by_section_type.get(s_family, None)
        if adjuster is None:
            raise ValueError(f"Failed to get json adjuster for taper section of type: {s_family} ")
        return adjuster

    @staticmethod
    def _adjust_db_user_tapered_json(s_tap: SectionTapered, s_tap_json: dict, s_end_json: dict) -> None:
        s_tap_json['SECT_BEFORE']['TYPE'] = s_tap_json['SECT_BEFORE']['DATATYPE']
        s_tap_json['SECT_BEFORE'].pop('DATATYPE', None)
        s_tap_json['SECT_BEFORE']['SECT_J'] = s_end_json['SECT_BEFORE']['SECT_I']

    @staticmethod
    def _adjust_composite_steel_tapered_json(s_tap: SectionTapered, s_tap_json: dict, s_end_json: dict) -> None:
        s_type = MidasSectionExporter._get_taper_type_code(s_tap.section_type, s_tap.section_family)
        s_shape = MidasSectionExporter._get_taper_shape_code(s_tap.section_type)
        s_tap_json['SECT_BEFORE']['TYPE'] = s_type
        s_tap_json['SECT_BEFORE']['SHAPE'] = s_shape
        s_tap_json['SECT_AFTER']['SECT_I'] = {'BUILT_FLAG': 1}
        s_tap_json['COMPOSITE_J'] = s_end_json['SECT_BEFORE']['SECT_I']

    @staticmethod
    def _adjust_psc_tapered_json(s_tap: SectionTapered, s_tap_json: dict, s_end_json: dict) -> None:
        s_shape = MidasSectionExporter._get_taper_shape_code(s_tap.section_type)
        s_tap_json['SECT_BEFORE']['SHAPE'] = s_shape
        s_tap_json['SECT_BEFORE']['SECT_J'] = s_end_json['SECT_BEFORE']['SECT_I']

        if s_tap.section_type in [SectionType.PSC_1CELL, SectionType.PSC_2CELL]:
            s_type = MidasSectionExporter._get_taper_type_code(s_tap.section_type, s_tap.section_family)
            s_tap_json['SECT_BEFORE']['TYPE'] = s_type
            s_tap_json['SECT_BEFORE'].pop('USE_AUTO_SHEAR_CHK_POS', None)
            s_tap_json['SECT_BEFORE'].pop('SHEAR_CHK', None)
            s_tap_json['SECT_BEFORE'].pop('SHEAR_CHK_POS', None)

    # ------------------------------------------------------------------
    # GENERAL HELPERS (pure logic – stay as @staticmethod)
    # ------------------------------------------------------------------

    def _get_section_offset(self, offset: DomainOffset):

        offset_point = self._get_section_offset_string(offset.offset_reference)
        if offset_point is None:
            raise ValueError(f"Unsupported section offset: {offset.offset_reference.value} ")

        hor_offset_value = to_float(offset.horizontal_value, self._eu.length)
        vert_offset_value = to_float(offset.vertical_value, self._eu.length)

        offset = self.MidasOffset(offset_point, 0, hor_offset_value, 1, vert_offset_value, 1, 1)
        return offset

    @staticmethod
    def _get_section_offset_string(offset: OffsetReference) -> str:
        midas_offset_by_offset_reference = {
            OffsetReference.CENTER_TOP: 'CT',
            OffsetReference.LEFT_TOP: 'LT',
            OffsetReference.RIGHT_TOP: 'RT',
            OffsetReference.CENTER_CENTER: 'CC',
            OffsetReference.LEFT_CENTER: 'LC',
            OffsetReference.RIGHT_CENTER: 'RC',
            OffsetReference.CENTER_BOTTOM: 'CB',
            OffsetReference.LEFT_BOTTOM: 'LB',
            OffsetReference.RIGHT_BOTTOM: 'RB',
        }
        offset_method = midas_offset_by_offset_reference.get(offset, None)
        if offset_method is None:
            raise ValueError(f"Unsupported section offset: {offset.value} ")
        return offset_method

    @staticmethod
    def _get_section_parameters(section: SectionStandard, eu: ExportUnits) -> list[float]:
        """Return the ordered list of plain-float dimension values for DBUSER sections."""
        match section.section_type:

            case SectionType.ANGLE:
                if not isinstance(section, SectionStandardAngle):
                    raise ValueError(f"Invalid section type: {section.section_type} ")
                d: DimensionsAngle = section.dimensions
                return [
                    to_float(d.height, eu.length),
                    to_float(d.width, eu.length),
                    to_float(d.thickness_web, eu.length),
                    to_float(d.thickness_flange, eu.length),
                ]

            case SectionType.BOX:
                if not isinstance(section, SectionStandardBox):
                    raise ValueError(f"Invalid section type: {section.section_type} ")
                d: DimensionsBox = section.dimensions
                return [
                    to_float(d.height_h, eu.length),
                    to_float(d.top_flange_width_b, eu.length),
                    to_float(d.web_thickness_tw, eu.length),
                    to_float(d.top_flange_thickness_tf1, eu.length),
                    0,
                    0,
                ]

            case SectionType.CHANNEL:
                if not isinstance(section, SectionStandardChannel):
                    raise ValueError(f"Invalid section type: {section.section_type} ")
                d: DimensionsChannel = section.dimensions
                return [
                    to_float(d.height_h, eu.length),
                    to_float(d.top_flange_width_b1, eu.length),
                    to_float(d.web_thickness_tw, eu.length),
                    to_float(d.top_flange_thickness_tf1, eu.length),
                    to_float(d.bottom_flange_width_b2, eu.length),
                    to_float(d.bottom_flange_thickness_tf2, eu.length),
                ]

            case SectionType.I_SECTION:
                if not isinstance(section, SectionStandardISection):
                    raise ValueError(f"Invalid section type: {section.section_type} ")
                d: DimensionsISection = section.dimensions
                return [
                    to_float(d.total_height_h, eu.length),
                    to_float(d.top_flange_width_b1, eu.length),
                    to_float(d.web_thickness_tw, eu.length),
                    to_float(d.top_flange_thickness_tf1, eu.length),
                    to_float(d.bottom_flange_width_b2, eu.length),
                    to_float(d.bottom_flange_thickness_tf2, eu.length),
                    to_float(d.web_inner_radius_r1, eu.length),
                    to_float(d.flange_end_radius_r2, eu.length),
                ]

            case SectionType.SOLID_RECTANGLE:
                if not isinstance(section, SectionStandardSolidRectangle):
                    raise ValueError(f"Invalid section type: {section.section_type} ")
                d: DimensionsSolidRectangle = section.dimensions
                return [
                    to_float(d.height_h, eu.length),
                    to_float(d.width_b, eu.length),
                ]

            case SectionType.SOLID_ROUND:
                if not isinstance(section, SectionStandardSolidRound):
                    raise ValueError(f"Invalid section type: {section.section_type} ")
                d: DimensionsSolidRound = section.dimensions
                return [to_float(d.diameter_d, eu.length)]

            case SectionType.PIPE:
                if not isinstance(section, SectionStandardPipe):
                    raise ValueError(f"Invalid section type: {section.section_type} ")
                d: DimensionsPipe = section.dimensions
                return [
                    to_float(d.external_diameter_d, eu.length),
                    to_float(d.wall_thickness_tw, eu.length),
                    ]

            case _:
                raise ValueError(f"Unsupported section type: {section.section_type} "
                                 f"for exporting as Section db user type")

    @staticmethod
    def _get_taper_variation(taper_variation: TaperVariation) -> int:
        value = {
            TaperVariation.LINEAR: 1,
            TaperVariation.PARABOLIC: 2,
            TaperVariation.CUBIC: 3,
        }.get(taper_variation, None)
        if value is None:
            raise ValueError(f"Unsupported taper variation: {taper_variation} ")
        return value

    @staticmethod
    def _get_taper_shape_code(section_type: SectionType) -> str:
        code = {
            SectionType.ANGLE: 'L',
            SectionType.BOX: 'B',
            SectionType.CHANNEL: 'C',
            SectionType.I_SECTION: 'H',
            SectionType.SOLID_RECTANGLE: 'SB',
            SectionType.SOLID_ROUND: 'SR',
            SectionType.STEEL_I_SYMMETRIC: "CP-I",
            SectionType.STEEL_I_ASYMMETRIC: "CSGI",
            SectionType.PSC_VALUE: "VALU",
            SectionType.PSC_1CELL: "1CEL",
            SectionType.PSC_2CELL: "2CEL",
        }.get(section_type, None)
        if code is None:
            raise ValueError(f"Unsupported section type: {section_type} of tapered section")
        return code

    @staticmethod
    def _get_taper_type_code(section_type: SectionType, section_family: SectionFamily) -> int:
        DBUSER = {SectionFamily.DB: 1, SectionFamily.STANDARD_SHAPE: 2}
        code = {
            SectionType.ANGLE: DBUSER.get(section_family),
            SectionType.BOX: DBUSER.get(section_family),
            SectionType.CHANNEL: DBUSER.get(section_family),
            SectionType.I_SECTION: DBUSER.get(section_family),
            SectionType.SOLID_RECTANGLE: DBUSER.get(section_family),
            SectionType.SOLID_ROUND: DBUSER.get(section_family),
            SectionType.STEEL_I_SYMMETRIC: 10,
            SectionType.STEEL_I_ASYMMETRIC: 20,
            SectionType.PSC_VALUE: None,
            SectionType.PSC_1CELL: 11,
            SectionType.PSC_2CELL: 11,
        }.get(section_type, None)
        if code is None:
            raise ValueError(f"Unsupported section type: {section_type} of tapered section")
        return code

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Trim to 28 chars (MIDAS Civil section name limit)."""
        return name[:28]
