"""Shared Speckle collection and AASHTO/UAE load object contracts."""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal, Union

from pydantic import Field, model_validator

from bda.contracts.paramodel.loadings.design.aashto.enums import AashtoLoadNatureEnum
from bda.contracts.paramodel.loadings.enums import (
    LoadApplicationDomainEnum,
    LoadContextEnum,
    LoadServiceStateEnum,
    MainCodeEnum,
    SecondaryCodeEnum,
)
from bda.contracts.speckle_contracts.base_objects import (
    BridgeCollection,
    BridgeDataObject,
    BridgeDataObjectProperties,
    EnumParameter,
    Parameter,
    ParameterGroup,
)
from bda.contracts.speckle_contracts.speckle_enums import SpeckleTypes


class LoadContextParameter(EnumParameter[LoadContextEnum]):
    name: Literal["Load Context"] = "Load Context"
    provided_value: LoadContextEnum


class MainCodeParameter(EnumParameter[MainCodeEnum]):
    name: Literal["Main Code"] = "Main Code"
    provided_value: MainCodeEnum


class SecondaryCodeParameter(EnumParameter[SecondaryCodeEnum]):
    name: Literal["Secondary Code"] = "Secondary Code"
    provided_value: SecondaryCodeEnum


class LoadDomainParameter(EnumParameter[LoadApplicationDomainEnum]):
    name: Literal["Load Application Domain"] = "Load Application Domain"
    provided_value: LoadApplicationDomainEnum


class LoadServiceStateParameter(EnumParameter[LoadServiceStateEnum]):
    name: Literal["Load Service State"] = "Load Service State"
    provided_value: LoadServiceStateEnum


class AashtoLoadNatureParameter(EnumParameter[AashtoLoadNatureEnum]):
    name: Literal["Load Nature"] = "Load Nature"
    provided_value: AashtoLoadNatureEnum


class LoadingCodeProperties(BridgeDataObjectProperties):
    main_code: MainCodeParameter = Field(alias="Main Code")
    secondary_code: SecondaryCodeParameter = Field(alias="Secondary Code")


class LoadingCodeDataObject(BridgeDataObject):
    name: Literal["Design Code & Secondary Code"] = "Design Code & Secondary Code"
    speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_LOAD_CODE_CONFIGURATION.value
    ] = SpeckleTypes.DATA_OBJECT_BDA_LOAD_CODE_CONFIGURATION.value
    bda_speckle_type: Literal[
        SpeckleTypes.DATA_OBJECT_BDA_LOAD_CODE_CONFIGURATION.value
    ] = Field(SpeckleTypes.DATA_OBJECT_BDA_LOAD_CODE_CONFIGURATION.value, frozen=True)
    properties: LoadingCodeProperties

    APPLICATION_ID: ClassVar[str] = "LOAD-CODE-CONFIG"

    @classmethod
    def create(
        cls,
        main_code: MainCodeEnum = MainCodeEnum.AASHTO,
        secondary_code: SecondaryCodeEnum = SecondaryCodeEnum.UAE,
    ) -> "LoadingCodeDataObject":
        return cls(
            applicationId=cls.APPLICATION_ID,
            properties=LoadingCodeProperties(
                **{
                    "Main Code": MainCodeParameter(
                        isUser=True, provided_value=main_code
                    ),
                    "Secondary Code": SecondaryCodeParameter(
                        isUser=True, provided_value=secondary_code
                    ),
                }
            ),
        )


class LoadCollectionBase(BridgeCollection):
    """Shared base for every code-neutral collection in the loading tree."""

    # Avoid inheriting BridgeCollection's recursive BridgeElement union here:
    # each concrete collection below declares its own typed child union.
    elements: list = Field(default_factory=list)
    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection"
    ] = Field("Speckle.Core.Models.Collections.Collection", frozen=True)


class LoadParameters(ParameterGroup):
    name: Literal["Load Parameters"] = "Load Parameters"


class LoadDataObjectProperties(BridgeDataObjectProperties):
    load_context: LoadContextParameter = Field(alias="Load Context")
    main_code: MainCodeParameter = Field(alias="Main Code")
    secondary_code: SecondaryCodeParameter = Field(alias="Secondary Code")
    load_application_domain: LoadDomainParameter = Field(
        alias="Load Application Domain"
    )
    load_service_state: LoadServiceStateParameter = Field(
        alias="Load Service State"
    )
    load_nature: AashtoLoadNatureParameter = Field(alias="Load Nature")
    load_parameters: LoadParameters = Field(alias="Load Parameters")


class AashtoLoadDataObject(BridgeDataObject):
    """Common typed metadata for AASHTO/UAE load data objects."""

    properties: LoadDataObjectProperties
    applicationId: str = Field(pattern=r"^LOAD-[A-Z0-9-]+$")
    EXPECTED_DOMAIN: ClassVar[LoadApplicationDomainEnum]
    EXPECTED_STATE: ClassVar[LoadServiceStateEnum]
    EXPECTED_NATURES: ClassVar[set[AashtoLoadNatureEnum]]
    REQUIRED_PARAMETERS: ClassVar[set[str]] = set()

    @model_validator(mode="after")
    def validate_load_discriminators_and_required_parameters(self):
        if self.properties.load_context.provided_value != LoadContextEnum.DESIGN:
            raise ValueError("MVP load objects must use design load context")
        if self.properties.main_code.provided_value != MainCodeEnum.AASHTO:
            raise ValueError("MVP load objects must use the AASHTO main code")
        if self.properties.secondary_code.provided_value not in {
            SecondaryCodeEnum.NONE,
            SecondaryCodeEnum.UAE,
        }:
            raise ValueError("MVP supports AASHTO with no secondary code or UAE")
        if self.properties.load_application_domain.provided_value != self.EXPECTED_DOMAIN:
            raise ValueError("Load application domain does not match this load type")
        if self.properties.load_service_state.provided_value != self.EXPECTED_STATE:
            raise ValueError("Load service state does not match this load type")
        if self.properties.load_nature.provided_value not in self.EXPECTED_NATURES:
            raise ValueError("Load nature does not match this load type")
        missing = self.REQUIRED_PARAMETERS - set(
            self.properties.load_parameters.group_parameters
        )
        if missing:
            raise ValueError(
                f"Missing required load parameter(s): {', '.join(sorted(missing))}"
            )
        # Keep this contract aligned with the public ParaModel validation rules.
        # The import stays local to avoid a module cycle during schema creation.
        from bda.contracts.paramodel.loadings.speckle_adapter import (
            LoadingSpeckleAdapter,
        )

        LoadingSpeckleAdapter.parse(self)
        return self


_LOAD_TYPE_BY_SUFFIX = {
    "Structural_Dead_Load": SpeckleTypes.DATA_OBJECT_BDA_LOAD_STRUCTURAL_DEAD,
    "Prestressing_Load": SpeckleTypes.DATA_OBJECT_BDA_LOAD_PRESTRESSING,
    "Ancillary_Dead_Load": SpeckleTypes.DATA_OBJECT_BDA_LOAD_ANCILLARY_DEAD,
    "Execution_Load": SpeckleTypes.DATA_OBJECT_BDA_LOAD_EXECUTION,
    "Wind_In_Service_Load": SpeckleTypes.DATA_OBJECT_BDA_LOAD_WIND_IN_SERVICE,
    "Wind_In_Construction_Load": SpeckleTypes.DATA_OBJECT_BDA_LOAD_WIND_IN_CONSTRUCTION,
    "Uniform_Temperature_Load": SpeckleTypes.DATA_OBJECT_BDA_LOAD_UNIFORM_TEMPERATURE,
    "Gradient_Temperature_Load": SpeckleTypes.DATA_OBJECT_BDA_LOAD_GRADIENT_TEMPERATURE,
    "Earthquake_Load": SpeckleTypes.DATA_OBJECT_BDA_LOAD_EARTHQUAKE,
    "HL93_Vertical_Direct_Load": SpeckleTypes.DATA_OBJECT_BDA_LOAD_HL93_VERTICAL_DIRECT,
    "HL93_Braking_Load": SpeckleTypes.DATA_OBJECT_BDA_LOAD_HL93_BRAKING,
    "Pedestrian_Load": SpeckleTypes.DATA_OBJECT_BDA_LOAD_PEDESTRIAN,
    "Settlement_Load": SpeckleTypes.DATA_OBJECT_BDA_LOAD_SETTLEMENT,
}


def _load_object(
    name: str,
    domain,
    state,
    natures,
    required,
    suffix: str,
    object_name: str | None = None,
):
    """Build concrete contract classes while keeping shared validation centralized."""
    speckle_type = _LOAD_TYPE_BY_SUFFIX[suffix].value
    object_name = object_name or name
    return type(
        name,
        (AashtoLoadDataObject,),
        {
            "__module__": __name__,
            "__annotations__": {
                "name": Literal[object_name],
                "speckle_type": Literal[speckle_type],
                "bda_speckle_type": Literal[speckle_type],
            },
            "name": object_name,
            "speckle_type": speckle_type,
            "bda_speckle_type": Field(speckle_type, frozen=True),
            "EXPECTED_DOMAIN": domain,
            "EXPECTED_STATE": state,
            "EXPECTED_NATURES": natures,
            "REQUIRED_PARAMETERS": required,
        },
    )


StructuralDeadLoadDataObject = _load_object(
    "StructuralDeadLoadDataObject",
    LoadApplicationDomainEnum.STRUCTURE,
    LoadServiceStateEnum.IN_SERVICE,
    {AashtoLoadNatureEnum.DC, AashtoLoadNatureEnum.DW},
    {"loading", "load_application"},
    "Structural_Dead_Load",
    "StructuralInServiceDeadLoad",
)
PrestressingLoadDataObject = _load_object(
    "PrestressingLoadDataObject",
    LoadApplicationDomainEnum.STRUCTURE,
    LoadServiceStateEnum.IN_SERVICE,
    {AashtoLoadNatureEnum.PS},
    {"loading", "load_application"},
    "Prestressing_Load",
    "PrestressingInServiceLoad",
)
AncillaryDeadLoadDataObject = _load_object(
    "AncillaryDeadLoadDataObject",
    LoadApplicationDomainEnum.ANCILLARY_WORKS,
    LoadServiceStateEnum.IN_SERVICE,
    {AashtoLoadNatureEnum.DC, AashtoLoadNatureEnum.DW},
    {"loading", "load_application"},
    "Ancillary_Dead_Load",
    "NonStructuralInServiceDeadLoad",
)
ExecutionLoadDataObject = _load_object(
    "ExecutionLoadDataObject",
    LoadApplicationDomainEnum.CONSTRUCTION,
    LoadServiceStateEnum.CONSTRUCTION,
    {AashtoLoadNatureEnum.CS},
    set(),
    "Execution_Load",
    "ExecutionLoad",
)
WindInServiceLoadDataObject = _load_object(
    "WindInServiceLoadDataObject",
    LoadApplicationDomainEnum.ENVIRONMENT,
    LoadServiceStateEnum.IN_SERVICE,
    {AashtoLoadNatureEnum.WS},
    {
        "exposure_category", "reference_superstructure_height",
        "wind_speed_3s_gust_strength_iii", "wind_speed_3s_gust_service_iv",
        "wind_speed_3s_gust_service_i", "wind_speed_3s_gust_strength_v",
    },
    "Wind_In_Service_Load",
    "WindInServiceLoad",
)
WindInConstructionLoadDataObject = _load_object(
    "WindInConstructionLoadDataObject",
    LoadApplicationDomainEnum.ENVIRONMENT,
    LoadServiceStateEnum.CONSTRUCTION,
    {AashtoLoadNatureEnum.CS},
    {
        "exposure_category", "wind_speed_3s_gust_active_work_zone",
        "wind_speed_3s_gust_inactive_work_zone",
        "wind_speed_reduction_factor_active_work_zone",
        "wind_speed_reduction_factor_inactive_work_zone",
        "avg_height_of_superstructure_for_active_work_zone",
        "avg_height_of_superstructure_for_inactive_work_zone",
        "superstructure_constr_duration_days",
    },
    "Wind_In_Construction_Load",
    "WindInConstructionLoad",
)
UniformTemperatureLoadDataObject = _load_object(
    "UniformTemperatureLoadDataObject",
    LoadApplicationDomainEnum.ENVIRONMENT,
    LoadServiceStateEnum.IN_SERVICE,
    {AashtoLoadNatureEnum.TU},
    {"uniform_temperature_params"},
    "Uniform_Temperature_Load",
    "UniformTemperatureLoad",
)
GradientTemperatureLoadDataObject = _load_object(
    "GradientTemperatureLoadDataObject",
    LoadApplicationDomainEnum.ENVIRONMENT,
    LoadServiceStateEnum.IN_SERVICE,
    {AashtoLoadNatureEnum.TG},
    {"gradient_temperature_params"},
    "Gradient_Temperature_Load",
    "GradientTemperatureLoad",
)
EarthquakeLoadDataObject = _load_object(
    "EarthquakeLoadDataObject",
    LoadApplicationDomainEnum.ENVIRONMENT,
    LoadServiceStateEnum.IN_SERVICE,
    {AashtoLoadNatureEnum.EQ},
    {"response_spectrum_params", "modal_analysis_params"},
    "Earthquake_Load",
    "EarthquakeLoad",
)

# Traffic and settlement extend the shared AASHTO/UAE loading schema. Their
# ParaModel classes remain the authority for detailed field and value checks.
HL93VerticalDirectLoadDataObject = _load_object(
    "HL93VerticalDirectLoadDataObject",
    LoadApplicationDomainEnum.LIVE_LOAD,
    LoadServiceStateEnum.IN_SERVICE,
    {AashtoLoadNatureEnum.LL},
    {
        "include_truck_model", "include_tandem_model",
        "include_fatigue_model", "lane_parameters",
    },
    "HL93_Vertical_Direct_Load",
    "HL93ModelVerticalDirectLoad",
)
HL93BrakingLoadDataObject = _load_object(
    "HL93BrakingLoadDataObject",
    LoadApplicationDomainEnum.LIVE_LOAD,
    LoadServiceStateEnum.IN_SERVICE,
    {AashtoLoadNatureEnum.BR},
    {
        "max_traffic_lanes_in_one_direction",
    },
    "HL93_Braking_Load",
    "HL93ModelBrakingLoad",
)
PedestrianLoadDataObject = _load_object(
    "PedestrianLoadDataObject",
    LoadApplicationDomainEnum.LIVE_LOAD,
    LoadServiceStateEnum.IN_SERVICE,
    {AashtoLoadNatureEnum.PL},
    set(),
    "Pedestrian_Load",
    "PedestrianStandardLoad",
)
SettlementLoadDataObject = _load_object(
    "SettlementLoadDataObject",
    LoadApplicationDomainEnum.ENVIRONMENT,
    LoadServiceStateEnum.IN_SERVICE,
    {AashtoLoadNatureEnum.SE},
    {"diff_settlement_value"},
    "Settlement_Load",
    "SettlementLoad",
)

LoadDataObject = Annotated[
    Union[
        StructuralDeadLoadDataObject,
        PrestressingLoadDataObject,
        AncillaryDeadLoadDataObject,
        ExecutionLoadDataObject,
        WindInServiceLoadDataObject,
        WindInConstructionLoadDataObject,
        UniformTemperatureLoadDataObject,
        GradientTemperatureLoadDataObject,
        EarthquakeLoadDataObject,
        HL93VerticalDirectLoadDataObject,
        HL93BrakingLoadDataObject,
        PedestrianLoadDataObject,
        SettlementLoadDataObject,
    ],
    Field(discriminator="bda_speckle_type"),
]


class LoadServiceStateCollectionBase(LoadCollectionBase):
    elements: list[LoadDataObject] = Field(default_factory=list)
    EXPECTED_STATE: ClassVar[LoadServiceStateEnum]

    @model_validator(mode="after")
    def validate_child_load_state(self):
        for load in self.elements:
            if load.properties.load_service_state.provided_value != self.EXPECTED_STATE:
                raise ValueError(f"{load.name} is in the wrong {self.name} collection")
        return self


class InServiceLoadCollection(LoadServiceStateCollectionBase):
    name: Literal["In Service"] = "In Service"
    EXPECTED_STATE = LoadServiceStateEnum.IN_SERVICE


class ConstructionLoadCollection(LoadServiceStateCollectionBase):
    name: Literal["Construction"] = "Construction"
    EXPECTED_STATE = LoadServiceStateEnum.CONSTRUCTION


class AccidentalLoadCollection(LoadServiceStateCollectionBase):
    name: Literal["Accidental"] = "Accidental"
    EXPECTED_STATE = LoadServiceStateEnum.ACCIDENTAL


class TemporaryLoadCollection(LoadServiceStateCollectionBase):
    name: Literal["Temporary"] = "Temporary"
    EXPECTED_STATE = LoadServiceStateEnum.TEMPORARY


LoadServiceCollection = Annotated[
    Union[
        InServiceLoadCollection,
        ConstructionLoadCollection,
        AccidentalLoadCollection,
        TemporaryLoadCollection,
    ],
    Field(discriminator="name"),
]


class LoadDomainCollectionBase(LoadCollectionBase):
    elements: list[LoadServiceCollection] = Field(default_factory=list)
    EXPECTED_DOMAIN: ClassVar[LoadApplicationDomainEnum]

    @model_validator(mode="after")
    def validate_child_load_domains(self):
        for state_collection in self.elements:
            for load in state_collection.elements:
                if load.properties.load_application_domain.provided_value != self.EXPECTED_DOMAIN:
                    raise ValueError(
                        f"{load.name} is in the wrong {self.name} load collection"
                    )
        return self


class StructureLoadsCollection(LoadDomainCollectionBase):
    name: Literal["Structure"] = "Structure"
    EXPECTED_DOMAIN = LoadApplicationDomainEnum.STRUCTURE


class AncillaryWorksCollection(LoadDomainCollectionBase):
    name: Literal["Ancillary Works"] = "Ancillary Works"
    EXPECTED_DOMAIN = LoadApplicationDomainEnum.ANCILLARY_WORKS


class LiveLoadsCollection(LoadDomainCollectionBase):
    name: Literal["Live Loads"] = "Live Loads"
    EXPECTED_DOMAIN = LoadApplicationDomainEnum.LIVE_LOAD


class ConstructionLoadsCollection(LoadDomainCollectionBase):
    name: Literal["Construction Loads"] = "Construction Loads"
    EXPECTED_DOMAIN = LoadApplicationDomainEnum.CONSTRUCTION


class EnvironmentalLoadsCollection(LoadDomainCollectionBase):
    name: Literal["Environmental Loads"] = "Environmental Loads"
    EXPECTED_DOMAIN = LoadApplicationDomainEnum.ENVIRONMENT


LoadDomainCollection = Annotated[
    Union[
        StructureLoadsCollection,
        AncillaryWorksCollection,
        LiveLoadsCollection,
        ConstructionLoadsCollection,
        EnvironmentalLoadsCollection,
    ],
    Field(discriminator="name"),
]

LoadingChildCollection = Annotated[
    Union[
        LoadingCodeDataObject,
        StructureLoadsCollection,
        AncillaryWorksCollection,
        LiveLoadsCollection,
        ConstructionLoadsCollection,
        EnvironmentalLoadsCollection,
    ],
    Field(discriminator="name"),
]


class LoadingCollection(LoadCollectionBase):
    COLLECTION_ID: ClassVar[str] = "COL-LOADING"
    name: Literal["Loading"] = "Loading"
    elements: list[LoadingChildCollection] = Field(
        default_factory=list,
        min_length=6,
        max_length=6,
    )

    @model_validator(mode="after")
    def validate_complete_loading_structure(self):
        expected = {
            "Design Code & Secondary Code",
            "Structure",
            "Ancillary Works",
            "Live Loads",
            "Construction Loads",
            "Environmental Loads",
        }
        names = [element.name for element in self.elements]
        if set(names) != expected or len(names) != len(expected):
            raise ValueError("Loading collection must contain each standard child collection exactly once")
        code_configuration = next(
            item for item in self.elements
            if isinstance(item, LoadingCodeDataObject)
        )
        code = code_configuration.properties
        if code.main_code.provided_value != MainCodeEnum.AASHTO:
            raise ValueError("The current loading hierarchy supports AASHTO only")
        if code.secondary_code.provided_value not in {
            SecondaryCodeEnum.NONE,
            SecondaryCodeEnum.UAE,
        }:
            raise ValueError("The current loading hierarchy supports UAE as the secondary code")
        for domain in self.elements:
            if not isinstance(domain, LoadDomainCollectionBase):
                continue
            for state in domain.elements:
                for load in state.elements:
                    properties = load.properties
                    if (
                        properties.main_code.provided_value != code.main_code.provided_value
                        or properties.secondary_code.provided_value != code.secondary_code.provided_value
                    ):
                        raise ValueError(
                            f"{load.name} code metadata must match the loading code configuration"
                        )
        return self

    @classmethod
    def create(
        cls,
        code_configuration: LoadingCodeDataObject,
        structure: StructureLoadsCollection | None = None,
        ancillary_works: AncillaryWorksCollection | None = None,
        live_loads: LiveLoadsCollection | None = None,
        construction_loads: ConstructionLoadsCollection | None = None,
        environmental_loads: EnvironmentalLoadsCollection | None = None,
    ) -> "LoadingCollection":
        return cls(
            applicationId=cls.COLLECTION_ID,
            elements=[
                code_configuration,
                structure or StructureLoadsCollection(
                    applicationId="COL-LOAD-STRUCTURE"
                ),
                ancillary_works or AncillaryWorksCollection(
                    applicationId="COL-LOAD-ANCILLARY-WORKS"
                ),
                live_loads or LiveLoadsCollection(
                    applicationId="COL-LOAD-LIVE-LOADS"
                ),
                construction_loads or ConstructionLoadsCollection(
                    applicationId="COL-LOAD-CONSTRUCTION-LOADS"
                ),
                environmental_loads or EnvironmentalLoadsCollection(
                    applicationId="COL-LOAD-ENVIRONMENTAL-LOADS"
                ),
            ],
        )
