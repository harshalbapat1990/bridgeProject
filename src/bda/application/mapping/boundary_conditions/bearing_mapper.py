from typing import Callable

from bda.application.mapping.base import to_pint
from bda.contracts.paramodel.bearings.bearing_bc_para_model import BearingBCsSupportParaModel, \
    SingleBearingBCsParaModel, MultipleBearingsBCsParaModel, BearingItemParaModel
from bda.domain.models.submodels.boundary_conditions.bearings import SingleBearingBCs, BearingItem, \
    MultiBearingBCs, BearingBCsSupport
from bda.domain.models.submodels.boundary_conditions.enums import DofTypeEnum
from bda.domain.models.submodels.boundary_conditions.spring_stiffness import SpringStiffness, TranslationalStiffness, \
    RotationalStiffness
from bda.domain.models.submodels.geometry_group_props.geometry_groups_enums import ElementOrientation

#
#   MAPPING FUNCTIONS
#
def _map_bearing_item(bearing: BearingItemParaModel) -> BearingItem:
    sd = bearing.bearing_stiffness_definition

    return BearingItem(
            bearing_index= bearing.bearing_index,
            orientation= ElementOrientation(bearing.orientation),
            bearing_stiffness_definition=
            SpringStiffness(
                sdx= TranslationalStiffness(
                    dof_type= DofTypeEnum(sd.sdx.dof_type),
                    stiffness= to_pint(sd.sdx.stiffness) if sd.sdx.stiffness is not None else None
                ),
                sdy=TranslationalStiffness(
                    dof_type=DofTypeEnum(sd.sdy.dof_type),
                    stiffness=to_pint(sd.sdy.stiffness) if sd.sdy.stiffness is not None else None
                ),
                sdz=TranslationalStiffness(
                    dof_type=DofTypeEnum(sd.sdz.dof_type),
                    stiffness=to_pint(sd.sdz.stiffness) if sd.sdz.stiffness is not None else None
                ),
                srx=RotationalStiffness(
                    dof_type=DofTypeEnum(sd.srx.dof_type),
                    stiffness=to_pint(sd.srx.stiffness) if sd.srx.stiffness is not None else None
                ),
                sry=RotationalStiffness(
                    dof_type=DofTypeEnum(sd.sry.dof_type),
                    stiffness=to_pint(sd.sry.stiffness) if sd.sry.stiffness is not None else None
                ),
                srz=RotationalStiffness(
                    dof_type=DofTypeEnum(sd.srz.dof_type),
                    stiffness=to_pint(sd.srz.stiffness) if sd.srz.stiffness is not None else None
                )
            )
        )

def _map_bearing_singular(bearing: SingleBearingBCsParaModel) -> SingleBearingBCs:
    if not isinstance(bearing, SingleBearingBCsParaModel):
        raise  ValueError("Expected a SingleBearingBCsParaModel instance")

    return SingleBearingBCs(
        girder_index= bearing.girder_index,
        bearing_definition= _map_bearing_item(bearing.bearing_definition),
    )

def _map_bearing_multi(bearing: MultipleBearingsBCsParaModel) -> MultiBearingBCs:
    if not isinstance(bearing, MultipleBearingsBCsParaModel):
        raise ValueError("Expected a MultipleBearingsBCsParaModel instance")

    return MultiBearingBCs(
        girder_index= bearing.girder_index,
        bearing_definitions=[_map_bearing_item(b) for b in bearing.bearing_definitions],
    )
#
#   Mapping dict
#
_mapping_func: dict[type, Callable] = {
    SingleBearingBCsParaModel: _map_bearing_singular,
    MultipleBearingsBCsParaModel: _map_bearing_multi,
}

def _map_bearing_support(
        support: BearingBCsSupportParaModel,
) -> BearingBCsSupport:

    bearings_by_girders: list[SingleBearingBCs | MultiBearingBCs] = []

    for g in support.bearings_by_girder:
        mapper: Callable = _mapping_func[type(g)]
        bearings_by_girders.append(
            mapper(g)
        )

    return BearingBCsSupport(
        support_index= support.support_index,
        bearings_by_girder= bearings_by_girders,
    )


#
#   PUBLIC API
#
class BearingMapper:
    @staticmethod
    def to_domain(
            para_model: list[BearingBCsSupportParaModel]
    ) -> list[BearingBCsSupport]:

        if not all(
            isinstance(b, BearingBCsSupportParaModel)
            for b in para_model
        ):
            raise ValueError(
                f"Unsupported bearing model type: {type(para_model).__name__}"
            )

        return [_map_bearing_support(b) for b in para_model]