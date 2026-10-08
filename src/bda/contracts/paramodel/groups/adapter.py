from typing import List

from pydantic import TypeAdapter

from bda.contracts.paramodel.groups import GeometryGroupParaModel
from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes


_GEOMETRY_GROUP_COLLECTION_TYPES = {
    speckle_type.value
    for speckle_type in SpeckleTypes
    if speckle_type.name.startswith("COLLECTION_BDA_GEOMETRY_GROUP")
}
_GEOMETRY_GROUP_PROPERTY_TYPES = {
    speckle_type.value
    for speckle_type in SpeckleTypes
    if speckle_type.name.startswith("DATA_OBJECT_BDA_GEOMETRY_GROUP_PROPERTIES")
}


class GroupsParaModelAdapter:

    @staticmethod
    def parse_list(raw_list: List) -> List[GeometryGroupParaModel]:
        if isinstance(raw_list, dict):
            if raw_list.get("bda_speckle_type") in _GEOMETRY_GROUP_COLLECTION_TYPES:
                raw_list = [raw_list]
            else:
                raw_list = raw_list.get("elements", [raw_list])
        if (
            raw_list
            and isinstance(raw_list[0], dict)
            and raw_list[0].get("bda_speckle_type")
            in _GEOMETRY_GROUP_COLLECTION_TYPES
        ):
            raw_list = [GroupsParaModelAdapter._from_speckle(group) for group in raw_list]
        adapter = TypeAdapter(List[GeometryGroupParaModel])
        return adapter.validate_python(raw_list)

    @staticmethod
    def _quantity_or_value(parameter: dict):
        value = parameter.get("provided_value")
        unit = parameter.get("provided_unit")
        if unit is not None:
            return {"value": value, "unit": unit}
        return value

    @staticmethod
    def _normalize_unit_lists(value):
        """Convert nested unit-bearing numeric lists to quantity objects."""
        if isinstance(value, dict):
            normalized = {
                key: GroupsParaModelAdapter._normalize_unit_lists(item)
                for key, item in value.items()
            }
            provided_values = normalized.get("provided_value")
            provided_unit = normalized.get("provided_unit")
            if isinstance(provided_values, list) and provided_unit is not None:
                normalized["provided_value"] = [
                    item
                    if isinstance(item, dict)
                    else {"value": item, "unit": provided_unit}
                    for item in provided_values
                ]
            return normalized

        if isinstance(value, list):
            return [
                GroupsParaModelAdapter._normalize_unit_lists(item)
                for item in value
            ]

        return value

    @staticmethod
    def _detail_records(group: dict, fields: dict[str, str]) -> list[dict]:
        records = []
        details = group.get("group_parameters", group)
        for detail in details.values():
            parameters = detail.get("group_parameters", {})
            records.append({
                field: GroupsParaModelAdapter._quantity_or_value(parameters[speckle_name])
                for field, speckle_name in fields.items()
            })
        return records

    @staticmethod
    def _from_speckle(group: dict) -> dict:
        """Expose the geometry group's contract fields in the ParaModel shape."""
        children = group.get("elements", [])
        property_objects = [
            element for element in children
            if element.get("bda_speckle_type") in _GEOMETRY_GROUP_PROPERTY_TYPES
        ]
        if len(property_objects) != 1:
            raise ValueError(f"Expected one geometry-group properties object in {group.get('name')!r}")
        contract_properties = property_objects[0].get("properties", {})
        component_type = contract_properties.get("Structural Component Type", {}).get("provided_value")
        properties = contract_properties.get("Geometry Group Properties", {}).get("group_parameters", {})
        detail_fields = {
            "Cracked Extents": {
                "x_start": "Cracked Extent X Start",
                "x_end": "Cracked Extent X End",
            },
            "Tapered Details": {
                "x_start": "Taper X Start",
                "x_end": "Taper X End",
                "section_id": "Section ID",
            },
            "Splices": {
                "x_start": "Segment X Start",
                "section_id": "Section ID",
            },
        }
        for group_name, fields in detail_fields.items():
            detail_group = properties.get(group_name)
            if isinstance(detail_group, dict) and isinstance(detail_group.get("group_parameters"), dict):
                properties[group_name] = {
                    "group_parameters": GroupsParaModelAdapter._detail_records(detail_group, fields)
                }
        construction = properties.get("Construction Sequence Details")
        if isinstance(construction, dict) and isinstance(construction.get("group_parameters"), dict):
            parameters = construction["group_parameters"]
            segments_group = parameters.get("Construction Sequence Segments", {})
            segments = GroupsParaModelAdapter._detail_records(
                segments_group,
                {
                    "x_start": "Construction Sequence Segment X Start",
                    "x_end": "Construction Sequence Segment X End",
                },
            )
            properties["Construction Sequence Details"] = {
                "group_parameters": {
                    "segments": segments,
                    "pouring_orientation": parameters.get("Pouring Orientation", {}).get("provided_value"),
                }
            }
        # Nested Speckle discriminator parameters are parameter objects inside
        # their own named groups. Mirror their tag into the existing union tag
        # key while retaining the contract-named values for field aliases.
        for group_name, parameter_name, field_name in (
            ("Geometry Details", "Diaphragm Type", "diaphragm_type"),
            ("Details", "Support Type", "support_type"),
            ("Foundation Details", "Foundation Type", "foundation_type"),
            ("Geometry Details", "Brace Type", "bracing_type"),
            ("Bearing Configuration Details", "Bearing Configuration Type", "bearing_configuration_type"),
        ):
            grouped = properties.get(group_name)
            if isinstance(grouped, dict) and isinstance(grouped.get("group_parameters"), dict):
                parameters = grouped["group_parameters"]
                tag = parameters.get(parameter_name, {}).get("provided_value")
                if tag is not None:
                    parameters[field_name] = tag
                    if field_name == "bearing_configuration_type":
                        parameters.pop(parameter_name, None)
        # Parameter contracts carry units alongside provided values. Convert
        # unit parameters to the existing QuantityParaModel input shape.
        properties = GroupsParaModelAdapter._normalize_unit_lists(properties)
        for parameter_name, parameter in list(properties.items()):
            if not isinstance(parameter, dict) or "provided_value" not in parameter:
                continue
            value = parameter["provided_value"]
            unit = parameter.get("provided_unit")
            if unit is not None:
                if isinstance(value, list):
                    # Nested and top-level unit-bearing lists were normalized
                    # recursively above, preserving the Speckle parameter shape.
                    continue
                else:
                    properties[parameter_name] = {"value": value, "unit": unit}
        nested = [
            GroupsParaModelAdapter._from_speckle(element)
            for element in children
            if element.get("bda_speckle_type") in _GEOMETRY_GROUP_COLLECTION_TYPES
        ]
        return {
            "group_id": group.get("applicationId"),
            "name": group.get("name"),
            "structural_component_type": component_type,
            "material_id": contract_properties.get("Material ID", {}).get("provided_value"),
            "section_id": contract_properties.get("Section ID", {}).get("provided_value"),
            "elements": [],
            "nested_groups": nested,
            "properties": properties,
        }
