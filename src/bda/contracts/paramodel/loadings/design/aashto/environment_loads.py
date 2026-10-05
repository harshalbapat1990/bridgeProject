from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from bda.contracts.paramodel.loadings.design.aashto.aashto_load_model_base import AashtoLoadModelBase
from bda.contracts.paramodel.shared.base_model_para_model import (
    BaseModelParaModel,
)
from bda.contracts.shared.quantity_para_model import QuantityParaModel
from bda.contracts.paramodel.loadings.enums import (
    EnvironmentLoadTypeEnum,
    LoadApplicationDomainEnum,
    LoadServiceStateEnum, TemperatureEffectTypeEnum, ModalAnalysisTypeEnum,
)
from bda.contracts.paramodel.loadings.design.aashto.enums import WindExposureCategoryEnum, \
    GradientDefinitionTypeEnum, DeckOverlayEnum, GradientZoneEnum, AashtoLoadNatureEnum


class EnvironmentEffectBase(
    BaseModelParaModel
):
    env_load_type: EnvironmentLoadTypeEnum

class EnvironmentLoadBase(
    AashtoLoadModelBase
):
    load_application_domain: Literal[
        LoadApplicationDomainEnum.ENVIRONMENT
    ] = LoadApplicationDomainEnum.ENVIRONMENT


class EnvironmentLoadInServiceBase(
    EnvironmentLoadBase
):
    load_service_state: Literal[
        LoadServiceStateEnum.IN_SERVICE
    ] = LoadServiceStateEnum.IN_SERVICE


class EnvironmentLoadInConstructionBase(
    EnvironmentLoadBase
):
    load_service_state: Literal[
        LoadServiceStateEnum.CONSTRUCTION
    ] = LoadServiceStateEnum.CONSTRUCTION


class WindInServiceLoad(
    EnvironmentLoadInServiceBase,
    EnvironmentEffectBase
):
    env_load_type: Literal[
        EnvironmentLoadTypeEnum.WIND
    ] = EnvironmentLoadTypeEnum.WIND

    load_nature: Literal[
        AashtoLoadNatureEnum.WS
    ] = AashtoLoadNatureEnum.WS

    exposure_category: WindExposureCategoryEnum
    reference_superstructure_height: QuantityParaModel
    wind_speed_3s_gust_strength_iii: QuantityParaModel
    wind_speed_3s_gust_service_iv: QuantityParaModel
    wind_speed_3s_gust_service_i: QuantityParaModel
    wind_speed_3s_gust_strength_v: QuantityParaModel


class WindInConstructionLoad(
    EnvironmentLoadInConstructionBase,
    EnvironmentEffectBase
):
    env_load_type: Literal[
        EnvironmentLoadTypeEnum.WIND
    ] = EnvironmentLoadTypeEnum.WIND

    load_nature: Literal[
        AashtoLoadNatureEnum.CS
    ] = AashtoLoadNatureEnum.CS

    exposure_category: WindExposureCategoryEnum
    wind_speed_3s_gust_active_work_zone: QuantityParaModel
    wind_speed_3s_gust_inactive_work_zone: QuantityParaModel
    wind_speed_reduction_factor_active_work_zone: float
    wind_speed_reduction_factor_inactive_work_zone: float
    avg_height_of_superstructure_for_active_work_zone: QuantityParaModel
    avg_height_of_superstructure_for_inactive_work_zone: QuantityParaModel
    superstructure_constr_duration_days: int


class UniformTemperatureParameters(BaseModelParaModel):
    temperature_min_design: QuantityParaModel
    temperature_ref_expansion: QuantityParaModel
    temperature_ref_contraction: QuantityParaModel
    temperature_max_design: QuantityParaModel


class GradientTempParamsBase(BaseModelParaModel):
    definition_type: GradientDefinitionTypeEnum
    deck_overlay: DeckOverlayEnum


class GradientTempParamsCustom(
    GradientTempParamsBase
):
    definition_type: Literal[GradientDefinitionTypeEnum.CUSTOM]
    cooling_t1: QuantityParaModel
    cooling_t2: QuantityParaModel
    cooling_t3: QuantityParaModel
    heating_t1: QuantityParaModel
    heating_t2: QuantityParaModel
    heating_t3: QuantityParaModel


class GradientTempParamsByZone(
    GradientTempParamsBase
):
    definition_type: Literal[GradientDefinitionTypeEnum.BY_ZONE]
    zone: GradientZoneEnum


GradientTempParams = Annotated[
    Union[
        GradientTempParamsCustom,
        GradientTempParamsByZone,
    ],
    Field(discriminator="definition_type"),
]


class TemperatureLoadBase(
    EnvironmentLoadInServiceBase,
    EnvironmentEffectBase
):
    env_load_type: Literal[
        EnvironmentLoadTypeEnum.TEMPERATURE
    ] = EnvironmentLoadTypeEnum.TEMPERATURE

    temperature_effect_type: TemperatureEffectTypeEnum


class GradientTemperatureLoad(
    TemperatureLoadBase
):
    temperature_effect_type: Literal[
        TemperatureEffectTypeEnum.GRADIENT
    ] = TemperatureEffectTypeEnum.GRADIENT

    load_nature: Literal[
        AashtoLoadNatureEnum.TG
    ] = AashtoLoadNatureEnum.TG

    gradient_temperature_params: GradientTempParams


class UniformTemperatureLoad(
    TemperatureLoadBase
):
    temperature_effect_type: Literal[
        TemperatureEffectTypeEnum.UNIFORM
    ] = TemperatureEffectTypeEnum.UNIFORM

    load_nature: Literal[
        AashtoLoadNatureEnum.TU
    ] = AashtoLoadNatureEnum.TU

    uniform_temperature_params: UniformTemperatureParameters


#### Earthquake Loadings

class ResponseSpectrumPoint(BaseModelParaModel):
    period: QuantityParaModel
    acceleration: QuantityParaModel


class ResponseSpectrumParameters(BaseModelParaModel):
    damping_ratio: float= 0.05
    horizontal_response_spectrum: list[ResponseSpectrumPoint]
    consider_vertical_rs: bool
    use_horizontal_rs_as_vertical: bool | None = None
    vertical_response_spectrum: list[ResponseSpectrumPoint] | None = None


class IncludedLoad(BaseModelParaModel):
    load_nature: AashtoLoadNatureEnum
    mass_participation: float= 1.0


class ModalAnalysisParameters(BaseModelParaModel):
    modal_analysis_type: ModalAnalysisTypeEnum
    number_of_modes: int = Field(ge=1)
    included_load_types: list[IncludedLoad]


class EarthquakeLoad(
    EnvironmentLoadInServiceBase,
    EnvironmentEffectBase
):
    env_load_type: Literal[
        EnvironmentLoadTypeEnum.EARTHQUAKE
    ] = EnvironmentLoadTypeEnum.EARTHQUAKE

    load_nature: Literal[
        AashtoLoadNatureEnum.EQ
    ] = AashtoLoadNatureEnum.EQ

    response_spectrum_params: ResponseSpectrumParameters
    modal_analysis_params: ModalAnalysisParameters

#### Earthquake Loadings ENDS

#### Settlement loading

class SettlementLoad(
    EnvironmentLoadInServiceBase,
    EnvironmentEffectBase
):
    env_load_type: Literal[
        EnvironmentLoadTypeEnum.SETTLEMENT
    ] = EnvironmentLoadTypeEnum.SETTLEMENT

    load_nature: Literal[
        AashtoLoadNatureEnum.SE
    ] = AashtoLoadNatureEnum.SE

    diff_settlement_value: QuantityParaModel

#### Settlement loading ENDS


# DISCRIMINATED UNIONS


# Level 6: in-service temperature — discriminator: temperature_effect_type
_TemperatureLoadInService = Annotated[
    Union[
        GradientTemperatureLoad,
        UniformTemperatureLoad,
    ],
    Field(discriminator="temperature_effect_type"),
]

# Level 5: in-service environment — discriminator: env_load_type
_EnvironmentInServiceLoad = Annotated[
    Union[
        WindInServiceLoad,
        _TemperatureLoadInService,
        EarthquakeLoad,
        SettlementLoad
    ],
    Field(discriminator="env_load_type"),
]

# Level 5: in-construction environment — discriminator: env_load_type
_EnvironmentInConstructionLoad = Annotated[
    Union[
        WindInConstructionLoad
    ],
    Field(discriminator="env_load_type"),
]

# Level 4: all environmental loads — discriminator: load_service_state
_EnvironmentLoad = Annotated[
    Union[
        _EnvironmentInServiceLoad,
        _EnvironmentInConstructionLoad,
    ],
    Field(discriminator="load_service_state"),
]
