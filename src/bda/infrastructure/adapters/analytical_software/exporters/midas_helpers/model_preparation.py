from bda.domain import AnalyticalMultiModel
from bda.domain.enums import MaterialType
from bda.domain.models.submodels.sections import SectionCompositeBase
from bda.infrastructure.adapters.analytical_software.exporters.common.section_materials import (
    SectionMaterialsResolver,
)

SOFTWARE_NAME = "Midas Civil"


class MidasModelPreparator:

    @staticmethod
    def prepare_sections_for_export(amm: AnalyticalMultiModel) -> None:
        """
        Prepare sections for export by making sure that each of them has its materials assigned.

        Midas Civil takes the material of an element from the geometry group, but the materials
        of a composite section are read from the section itself, so every exported section needs
        them. Materials already assigned are never overwritten, so the assignments made by the
        geometry modules are kept.

        Parameters
        ----------
        amm: AnalyticalMultiModel

        Returns
        -------

        """

        MidasModelPreparator._assign_materials_to_sections(amm)
        SectionMaterialsResolver.fill_missing_section_materials(amm, SOFTWARE_NAME)

    @staticmethod
    def _assign_materials_to_sections(amm: AnalyticalMultiModel) -> None:

        # this step is only for testing purposes during development when geometry group does not exist
        # but there is a need to test section export
        if amm.geometry_group is not None:
            return

        sections = amm.get_all_sections()
        materials = amm.get_all_materials()
        if not materials:
            return
        # main material is the steel part of the section and composite material is its concrete
        # part, so materials of those types are preferred; when there is none, the first and the
        # second material are used as before
        material_main = next(
            (m for m in materials if m.material_type == MaterialType.STEEL),
            materials[0])
        material_composite = next(
            (m for m in materials if m.material_type == MaterialType.CONCRETE),
            materials[1] if len(materials) > 1 else materials[0])
        for section in sections:
            section.set_material_main(material_main)
            if isinstance(section, SectionCompositeBase):
                section.set_material_composite(material_composite)
