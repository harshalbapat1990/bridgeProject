from __future__ import annotations

from typing import Callable, List, Dict

from bda.application.mapping.base.quantity_mappers import to_pint
from bda.contracts.paramodel.foundations.enums import DofTypeEnumParaModel
from bda.contracts.paramodel.foundations.foundation_bc_para_model import (
    FoundationApplicationBaseParaModel,
    BearingBasedFoundationApplicationParaModel,
    SubstructureElementBasedFoundationApplicationParaModel,
    LumpedFoundationBCsParaModel,
    PileInteractionFoundationBCsParaModel,
    NodeSpringStiffnessParaModel,
    PileNodeSpringStiffnessParaModel,
    PileStiffnessUniformDatasetParaModel,
    TranslationalStiffnessParaModel,
    RotationalStiffnessParaModel,
)
from bda.domain.models.submodels.boundary_conditions.enums import DofTypeEnum
from bda.domain.models.submodels.boundary_conditions.foundations import (
    NodeSpringStiffness,
    PileNodeSpringStiffness,
    PileStiffnessUniformDataset,
    BearingBasedFoundationApplication,
    SubstructureElementBasedFoundationApplication,
    FoundationApplication,
    LumpedFoundationBCs,
    PileInteractionFoundationBCs,
    FoundationBCs,
)
from bda.domain.models.submodels.boundary_conditions.spring_stiffness import SpringStiffness, TranslationalStiffness, \
    RotationalStiffness
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation


#
#   DOF TYPE MAPPING
#
_DOF_TYPE_MAP: dict[DofTypeEnumParaModel, DofTypeEnum] = {
    DofTypeEnumParaModel.FREE: DofTypeEnum.FREE,
    DofTypeEnumParaModel.FIXED: DofTypeEnum.FIXED,
    DofTypeEnumParaModel.CUSTOM: DofTypeEnum.CUSTOM,
}


def _map_dof_type(para: DofTypeEnumParaModel) -> DofTypeEnum:
    try:
        return _DOF_TYPE_MAP[para]
    except KeyError:
        raise ValueError(f"Unsupported DOF type: {para}")


#
#   STIFFNESS MAPPING
#
def _map_translational_dof(para: TranslationalStiffnessParaModel) -> TranslationalStiffness:
    return TranslationalStiffness(
        dof_type=_map_dof_type(para.dof_type),
        stiffness=to_pint(para.stiffness) if para.stiffness is not None else None,
    )


def _map_rotational_dof(para: RotationalStiffnessParaModel) -> RotationalStiffness:
    return RotationalStiffness(
        dof_type=_map_dof_type(para.dof_type),
        stiffness=to_pint(para.stiffness) if para.stiffness is not None else None,
    )


def _map_node_spring_stiffness(para: NodeSpringStiffnessParaModel) -> NodeSpringStiffness:
    return NodeSpringStiffness(
        sdx=_map_translational_dof(para.sdx),
        sdy=_map_translational_dof(para.sdy),
        sdz=_map_translational_dof(para.sdz),
        srx=_map_rotational_dof(para.srx),
        sry=_map_rotational_dof(para.sry),
        srz=_map_rotational_dof(para.srz),
    )


def _map_pile_node_spring_stiffness(para: PileNodeSpringStiffnessParaModel) -> PileNodeSpringStiffness:
    return PileNodeSpringStiffness(
        sdx=_map_translational_dof(para.sdx),
        sdy=_map_translational_dof(para.sdy),
        sdz=_map_translational_dof(para.sdz),
    )


#
#   PILE DATASET MAPPING
#
def _map_pile_stiffness_uniform_dataset(
    para: PileStiffnessUniformDatasetParaModel,
) -> PileStiffnessUniformDataset:
    return PileStiffnessUniformDataset(
        pile_index=para.pile_index,
        top_node=_map_pile_node_spring_stiffness(para.top_node),
        bottom_node=_map_pile_node_spring_stiffness(para.bottom_node),
        intermediate_nodes=_map_pile_node_spring_stiffness(para.intermediate_nodes),
    )


#
#   APPLICATION MAPPING
#
def _map_application(para: FoundationApplicationBaseParaModel) -> FoundationApplication:
    if isinstance(para, BearingBasedFoundationApplicationParaModel):
        return BearingBasedFoundationApplication(
            vertical_offset=to_pint(para.vertical_offset),
        )
    if isinstance(para, SubstructureElementBasedFoundationApplicationParaModel):
        return SubstructureElementBasedFoundationApplication()
    raise ValueError(f"Unsupported foundation application type: {type(para).__name__}")


#
#   FOUNDATION BC MAPPING
#
def _map_lumped(para: LumpedFoundationBCsParaModel) -> LumpedFoundationBCs:
    if not isinstance(para, LumpedFoundationBCsParaModel):
        raise ValueError("Expected a LumpedFoundationBCsParaModel instance")

    return LumpedFoundationBCs(
        support_index=para.support_index,
        stiffness_definition=_map_node_spring_stiffness(para.stiffness_definition),
        orientation=ElementOrientation(para.orientation),
        application=_map_application(para.application),
    )


def _map_pile_interaction(para: PileInteractionFoundationBCsParaModel) -> PileInteractionFoundationBCs:
    if not isinstance(para, PileInteractionFoundationBCsParaModel):
        raise ValueError("Expected a PileInteractionFoundationBCsParaModel instance")

    return PileInteractionFoundationBCs(
        support_index=para.support_index,
        pile_springs=[_map_pile_stiffness_uniform_dataset(p) for p in para.pile_springs],
    )


#
#   MAPPING DISPATCH
#
_MAPPING_FUNCS: Dict[type, Callable] = {
    LumpedFoundationBCsParaModel: _map_lumped,
    PileInteractionFoundationBCsParaModel: _map_pile_interaction,
}


#
#   PUBLIC API
#
class FoundationMapper:
    @staticmethod
    def to_domain(
        para_models: List[LumpedFoundationBCsParaModel | PileInteractionFoundationBCsParaModel],
    ) -> List[FoundationBCs]:
        unsupported = [p for p in para_models if type(p) not in _MAPPING_FUNCS]
        if unsupported:
            raise ValueError(
                f"Unsupported foundation model type(s): "
                f"{[type(p).__name__ for p in unsupported]}"
            )

        return [_MAPPING_FUNCS[type(p)](p) for p in para_models]
