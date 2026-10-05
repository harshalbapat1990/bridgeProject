from __future__ import annotations

from typing import Dict, TYPE_CHECKING
from bda.domain.enums import StructuralComponentType
from bda.domain.models.submodels import GeometryGroup
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_collectors import collect_supports_data
from bda.modules_pre.m3_geometry.builders.steel_composite_builder.group_property_getters import \
    require_linkage_sup_to_sup_properties

if TYPE_CHECKING:
    from bda.modules_pre.m3_geometry.builders.steel_composite_builder.context import BuildContext


def run(ctx: BuildContext) -> None:
    _process_bearing_nodes(ctx)

def _process_bearing_nodes(ctx: BuildContext) -> None:

    linkage_sup_to_sub_groups = (ctx.amm.geometry_group.
    get_groups_by_component_type(
        StructuralComponentType.SUPERSTRUCTURE_TO_SUBSTRUCTURE_CONNECTIONS))

    linkage_by_sup_id: Dict[int, GeometryGroup] = {}

    for g in linkage_sup_to_sub_groups:
        props = require_linkage_sup_to_sup_properties(g)
        if props is not None:
            linkage_by_sup_id[props.support_index] = g

    support_data_by_sup_id = collect_supports_data(ctx)

    for sidx, g in linkage_by_sup_id.items():
        level_z = support_data_by_sup_id[sidx].bearing_underside_relative_level
        bearings = g.analytical_typology.bearing_nodes

        for bearing_key, bearing_nodes in bearings.items():
            top_node = bearing_nodes.node_top
            bottom_node = ctx.amm.get_or_create_node(
                top_node.X,
                top_node.Y,
                level_z
            )
            ctx.amm.update_bearing_nodes(g, 
                key=bearing_key,
                node_end=bottom_node,
            )