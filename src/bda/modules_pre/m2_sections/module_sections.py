from bda.application.mapping.sections.section_mapper import SectionMapper
from bda.application.interfaces.module.i_module import IModule
from bda.domain.enums import SectionFamily, SectionType, OutputSoftware
from bda.domain.models.submodels.sections import SectionTapered, SectionCompositeBase


class SectionsModule(IModule):

    @property
    def module_name(self) -> str:
        return "Sections"

    def _run(self) -> bool:
        sections_dto = self.data_provider.get_sections_for_project()
        self.logger.info("Retrieved %d sections from data provider.", len(sections_dto))

        for section in sections_dto:
            try:
                self.logger.debug("Processing section: %s", section.name)
                sec = SectionMapper.to_domain(section) # type: ignore

                self.amm.add_initial_section(sec)
                self.logger.debug("Section: %s successfully added to MultiModel", section.name)
            except Exception as e:
                raise RuntimeError(f"Error processing section '{section.name}': {e}") from e

        sections = self.amm.get_all_sections()

        sections_by_guid = {sec.guid: sec for sec in sections}

        tapered_sections = [
            sec for sec in sections
            if sec.section_family == SectionFamily.TAPERED
        ]

        for tap_sec in tapered_sections:
            if not isinstance(tap_sec, SectionTapered):
                raise ValueError("Expected SectionTapered.")

            try:
                tap_sec.section_start = sections_by_guid[tap_sec.section_start_id]
                tap_sec.section_end = sections_by_guid[tap_sec.section_end_id]
            except KeyError as e:
                raise RuntimeError(
                    f"Missing referenced section {e} in tapered section {tap_sec.name}."
                ) from e

        # THIS IS A TEMPORARY MATERIAL ASSIGNED FOR TESTING PURPOSES
        # TODO: to be removed once the assignment is done in geometry module
        # materials = self.amm.get_materials()
        #
        # for sec in sections:
        #     sec.material_main = materials[0]
        #     if isinstance(sec, SectionCompositeBase):
        #         sec.material_composite = materials[1]

        # END OF TEMPORARY CODE

        return True