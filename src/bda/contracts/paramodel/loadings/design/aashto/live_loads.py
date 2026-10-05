from __future__ import annotations

from typing import Literal, Annotated, Union

from pydantic import Field

from bda.contracts.paramodel.loadings.design.aashto.enums import AashtoLoadNatureEnum
from bda.contracts.paramodel.loadings.enums import (
    LoadApplicationDomainEnum,
    LoadServiceStateEnum,
    TrafficLoadTypeEnum, DefinitionTypeEnum,
)
from bda.contracts.paramodel.loadings.design.aashto.enums import PrimaryTrafficTypeEnum, \
    TrafficLoadModelEnum
from bda.contracts.paramodel.loadings.design.aashto.aashto_load_model_base import AashtoLoadModelBase
from bda.contracts.paramodel.shared.base_model_para_model import BaseModelParaModel
from bda.contracts.shared import QuantityParaModel


class LiveLoadBase(AashtoLoadModelBase):
    load_application_domain: Literal[
        LoadApplicationDomainEnum.LIVE_LOAD
    ] = LoadApplicationDomainEnum.LIVE_LOAD


class LiveLoadInServiceBase(LiveLoadBase):
    load_service_state: Literal[
        LoadServiceStateEnum.IN_SERVICE
    ] = LoadServiceStateEnum.IN_SERVICE

    primary_traffic_type: PrimaryTrafficTypeEnum


class RoadLiveLoadBase(LiveLoadInServiceBase):
    primary_traffic_type: Literal[
        PrimaryTrafficTypeEnum.ROAD
    ] = PrimaryTrafficTypeEnum.ROAD

    vehicle_def_type: DefinitionTypeEnum

class RoadStandardVehiclesLoadBase(
    RoadLiveLoadBase
):
    vehicle_def_type: Literal[
        DefinitionTypeEnum.STANDARD
    ] = DefinitionTypeEnum.STANDARD

    traffic_load_model: TrafficLoadModelEnum


class HL93ModelLoadBase(RoadStandardVehiclesLoadBase):
    traffic_load_model: Literal[
        TrafficLoadModelEnum.HL93
    ] = TrafficLoadModelEnum.HL93

    traffic_load_type: TrafficLoadTypeEnum


class HL93ModelVerticalDirectLoad(HL93ModelLoadBase):
    traffic_load_type: Literal[
        TrafficLoadTypeEnum.VERTICAL_TRAFFIC_DIRECT
    ] = TrafficLoadTypeEnum.VERTICAL_TRAFFIC_DIRECT

    load_nature: Literal[
        AashtoLoadNatureEnum.LL
    ] = AashtoLoadNatureEnum.LL

    include_truck_model: bool
    include_tandem_model: bool
    include_fatigue_model: bool
    lane_parameters: _LaneParameters


class LaneParametersBase(BaseModelParaModel):
    lane_definition_type: DefinitionTypeEnum


class CustomLaneParameters(LaneParametersBase):
    lane_definition_type: Literal[
        DefinitionTypeEnum.CUSTOM
    ] = DefinitionTypeEnum.CUSTOM

    lane_width: QuantityParaModel


class StandardLaneParameters(LaneParametersBase):
    lane_definition_type: Literal[
        DefinitionTypeEnum.STANDARD
    ] = DefinitionTypeEnum.STANDARD


_LaneParameters = Annotated[
    Union[
        CustomLaneParameters,
        StandardLaneParameters,
    ],
    Field(discriminator="lane_definition_type"),
]

class PedestrianStandardLoad(RoadStandardVehiclesLoadBase):
    traffic_load_model: Literal[
        TrafficLoadModelEnum.Pedestrian
    ] = TrafficLoadModelEnum.Pedestrian

    load_nature: Literal[
        AashtoLoadNatureEnum.PL
    ] = AashtoLoadNatureEnum.PL


class HL93ModelBrakingLoad(
    HL93ModelLoadBase
):
    traffic_load_type: Literal[
        TrafficLoadTypeEnum.BRAKING
    ] = TrafficLoadTypeEnum.BRAKING

    load_nature: Literal[
        AashtoLoadNatureEnum.BR
    ] = AashtoLoadNatureEnum.BR

    max_traffic_lanes_in_one_direction: int = Field(ge=1)


# discriminator: traffic_load_type
_HL93ModelLoad = Annotated[
    Union[
        HL93ModelBrakingLoad,
        HL93ModelVerticalDirectLoad
    ],
    Field(discriminator="traffic_load_type"),
]

# discriminator: traffic_load_model
_RoadStandardVehiclesLoad = Annotated[
    Union[
        _HL93ModelLoad,
        PedestrianStandardLoad,
    ],
    Field(discriminator="traffic_load_model"),
]

# discriminator: vehicle_def_type
_RoadLiveLoad = Annotated[
    Union[
        _RoadStandardVehiclesLoad,
    ],
    Field(discriminator="vehicle_def_type"),
]

# discriminator: primary_traffic_type
_LiveLoadInService = Annotated[
    Union[
        _RoadLiveLoad,
    ],
    Field(discriminator="primary_traffic_type"),
]