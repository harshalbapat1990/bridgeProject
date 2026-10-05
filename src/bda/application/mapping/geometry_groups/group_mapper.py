from bda.application.mapping.base import to_uuid
from bda.application.mapping.geometry_groups.properties_mapper import map_properties
from bda.contracts.paramodel.groups import GeometryGroupParaModel
from bda.domain.enums import StructuralComponentType

from bda.domain.models.submodels.geometry_group import GeometryGroup


class GeometryGroupMapper:

    @classmethod
    def map_group(
            cls,
            dto: GeometryGroupParaModel,
            parent: GeometryGroup | None = None) -> GeometryGroup:

        group = cls._map_geometry_group(dto)
        if parent is not None:
            parent.add_nested_group(group)

        # recursion for children
        for child_dto in dto.nested_groups:
            cls.map_group(child_dto, group)

        return group

    @classmethod
    def _map_geometry_group(cls, dto: GeometryGroupParaModel) -> GeometryGroup:
        return GeometryGroup(
            guid=to_uuid(dto.group_id),
            source_id=dto.group_id,
            section_uid=to_uuid(dto.section_id) if dto.section_id else None,
            material_uid=to_uuid(dto.material_id) if dto.material_id else None,
            component_type=StructuralComponentType(dto.structural_component_type.value),
            name=dto.name,
            properties=map_properties(dto.structural_component_type, dto.properties))
