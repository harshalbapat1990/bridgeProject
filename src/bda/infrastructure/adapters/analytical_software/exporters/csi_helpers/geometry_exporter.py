from typing import Set, Tuple, List

from bda.domain.enums import TaperVariation, OffsetReference
from bda.domain.models.submodels import GeometryGroup, Element1D, Node
from bda.domain.models.submodels.section_base import Section
from bda.domain.models.submodels.sections import SectionTapered
from bda.domain.units import ExportUnits, to_float
from bda.infrastructure.utils import AppLogger

logger = AppLogger()

class CsiGeometryExporter:
    def __init__(self, sapModel, eu: ExportUnits):
        self.sapModel = sapModel
        self._eu: ExportUnits = eu


    def _get_section_name(self, group: GeometryGroup) -> str:
        cur_sec = group.get_section()
        current_sec_name = 'unknown'

        if cur_sec is not None and cur_sec.name is not None:
            current_sec_name = cur_sec.name

        return current_sec_name


    def _set_rigid_link_property(self, property_name: str):
        sapModel = self.sapModel

        DOF = [True] * 6
        Fixed = [True] * 6
        Ke = [0] * 6
        Ce = [0] * 6

        sapModel.PropLink.SetLinear(
            Name=property_name,
            DOF=DOF,
            Fixed=Fixed,
            Ke=Ke,
            Ce=Ce,
            DJ2=0,
            DJ3=0,
        )


    def _get_taper_variation_type_code(self, taper_variation: TaperVariation) -> int:
        if taper_variation == TaperVariation.LINEAR:
            return 1
        elif taper_variation == TaperVariation.PARABOLIC:
            return 2
        elif taper_variation == TaperVariation.CUBIC:
            return 3
        else:
            raise NotImplementedError(f"Taper variation {taper_variation} not implemented")


    def _get_section_offset_code(self, section: Section) -> int:
        """Get the section offset code for a given section."""
        if section is None:
            raise ValueError("Section is None, cannot get offset code")

        offset_type = section.offset.offset_reference
        match offset_type:
            case OffsetReference.LEFT_BOTTOM: return 1
            case OffsetReference.CENTER_BOTTOM: return 2
            case OffsetReference.RIGHT_BOTTOM: return 3
            case OffsetReference.LEFT_CENTER: return 4
            case OffsetReference.CENTER_CENTER: return 5
            case OffsetReference.RIGHT_CENTER: return 6
            case OffsetReference.LEFT_TOP: return 7
            case OffsetReference.CENTER_TOP: return 8
            case OffsetReference.RIGHT_TOP: return 9
            case _: raise NotImplementedError(f"Offset type {offset_type} not implemented")


    def _calc_distance(self, node1: Node, node2: Node) -> float:
        """Calculate the distance between two nodes.
        Returns value in export units."""
        eu = self._eu
        dx = to_float(node2.X - node1.X, eu.length)
        dy = to_float(node2.Y - node1.Y, eu.length)
        dz = to_float(node2.Z - node1.Z, eu.length)
        return (dx**2 + dy**2 + dz**2) ** 0.5


    def _export_tapered_section(self, gr: GeometryGroup, current_sec_name: str) -> None:
        """Export tapered section configuration for a geometry group."""
        eu = self._eu
        sapModel = self.sapModel

        sec = gr.section
        if not isinstance(sec, SectionTapered):
            return

        # prepare ordered list of tuple (element_number, node start, node end) ordered by x_start then y_start
        elements: List[Tuple[int, Node, Node]] = [(e.element_id, e.node_start, e.node_end)
                   for e in gr.analytical_typology.elements if isinstance(e, Element1D)]

        tol = 0.001
        elements = sorted(elements,
                          key=lambda x:
                          (round(to_float(x[1].Y, eu.length) / tol),
                           round(to_float(x[1].X, eu.length) / tol)
                          ))

        # tapered segment start point
        p0 = elements[0][1]
        total_length = self._calc_distance(p0, elements[-1][2])

        for tap_element in elements:
            dist = self._calc_distance(p0, tap_element[1])
            ratio = dist / total_length

            sapModel.FrameObj.SetSection(
                Name=str(tap_element[0]),
                PropName=current_sec_name,
                ItemType=0, # itemType = Object,
                SVarRelStartLoc=ratio,
                SVarTotalLength=total_length
            )


    def _export_group_elements(
            self,
            gr: GeometryGroup,
            current_sec_name: str,
            cur_sec: Section|None,
            group_collection: Set[str]) -> None:
        """Export elements for a geometry group."""

        eu = self._eu
        sapModel = self.sapModel

        for element in gr.analytical_typology.elements:
            if not isinstance(element, Element1D):
                raise NotImplementedError("Elements other than Element1D (beam) are not yet supported")
            for n in [element.node_start, element.node_end]:
                sapModel.PointObj.AddCartesian(
                    X=to_float(n.X, eu.length),
                    Y=to_float(n.Y, eu.length),
                    Z=to_float(n.Z, eu.length),
                    Name=str(n.node_id),
                    UserName=str(n.node_id)
                )
            sapModel.FrameObj.AddByPoint(
                Point1=str(element.node_start.node_id),
                Point2=str(element.node_end.node_id),
                Name=str(element.element_id),
                PropName=current_sec_name,
                UserName=str(element.element_id)
            )
            if cur_sec is not None:
                of_ref = cur_sec.offset.offset_reference
                if of_ref in [OffsetReference.LEFT_TOP, OffsetReference.LEFT_CENTER, OffsetReference.LEFT_BOTTOM]:
                    h_off = -to_float(cur_sec.dimensions.total_width - cur_sec.offset.horizontal_value, eu.length) \
                        if not isinstance(cur_sec, SectionTapered) else 0
                elif of_ref in [OffsetReference.RIGHT_TOP, OffsetReference.RIGHT_CENTER, OffsetReference.RIGHT_BOTTOM]:
                    h_off = to_float(cur_sec.offset.horizontal_value, eu.length)
                else:
                    h_off = 0

                ret = sapModel.FrameObj.SetInsertionPoint_1(
                    Name=str(element.element_id),
                    CardinalPoint=self._get_section_offset_code(cur_sec),
                    Mirror2=False,
                    Mirror3=False,
                    StiffTransform=True,
                    Offset1=[
                        0,
                        to_float(cur_sec.offset.vertical_value, eu.length),
                        h_off
                    ],
                    Offset2=[
                        0,
                        to_float(cur_sec.offset.vertical_value, eu.length),
                        h_off
                    ]
                )

            for gc in group_collection:
                sapModel.FrameObj.SetGroupAssign(Name=str(element.element_id), GroupName=gc)


    def _export_group_links(self, gr: GeometryGroup, rigid_link_property_name: str, unknown_group_name: str) -> None:
        """Export links for a geometry group."""
        eu = self._eu
        sapModel = self.sapModel

        for link in gr.analytical_typology.links:
            for n in [link.node_start, link.node_end]:
                sapModel.PointObj.AddCartesian(
                    X=to_float(n.X, eu.length),
                    Y=to_float(n.Y, eu.length),
                    Z=to_float(n.Z, eu.length),
                    Name=str(n.node_id),
                    UserName=str(n.node_id)
                )
            sapModel.LinkObj.AddByPoint(
                Point1=str(link.node_start.node_id),
                Point2=str(link.node_end.node_id),
                Name=str(link.element_id),
                IsSingleJoint=False,
                PropName=rigid_link_property_name,
                UserName=str(link.element_id),
            )

            sapModel.LinkObj.SetGroupAssign(Name=str(link.element_id), GroupName=gr.name or unknown_group_name)


    def export_geometry_group(self, group: GeometryGroup) -> None:
        """Export a GeometryGroup to CSI Bridge."""

        sapModel = self.sapModel

        unknown_group_name = "unknown"

        rigid_link_property_name = 'Rigid'
        self._set_rigid_link_property(rigid_link_property_name)

        for gr in group.iter_groups():

            cur_sec = gr.get_section()
            current_sec_name = self._get_section_name(gr)

            group_collection: Set[str] = {gr.name} if gr.name is not None else {unknown_group_name}
            g=gr
            while g.parent_group is not None:
                group_collection.add(g.parent_group.name or unknown_group_name)
                g = g.parent_group

            for gc in group_collection:
                sapModel.GroupDef.SetGroup(Name=gc)

            self._export_group_elements(gr, current_sec_name, cur_sec, group_collection)

            self._export_group_links(gr, rigid_link_property_name, unknown_group_name)

            self._export_tapered_section(gr, current_sec_name)


