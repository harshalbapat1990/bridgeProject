from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from bda.contracts.paramodel.loadings.design.aashto.enums import AashtoLoadNatureEnum
from bda.contracts.paramodel.loadings.design.aashto.aashto_load_model_base import AashtoLoadModelBase
from bda.contracts.paramodel.shared.base_model_para_model import (
    BaseModelParaModel,
)
from bda.contracts.paramodel.shared.case_insensitive_enum import CaseInsensitiveEnum
from bda.contracts.shared.quantity_para_model import QuantityParaModel
from bda.contracts.paramodel.groups.enums import (
    StructuralComponentTypeParaModel,
)
from bda.contracts.paramodel.loadings.enums import (
    DeadLoadingMethodEnum,
    LoadApplicationDomainEnum,
    LoadApplicationTypeEnum,
    LoadServiceStateEnum,
    StructuralApplicationTypeEnum, StructuralLoadTypeEnum,
)


class DeadLoadingBase(BaseModelParaModel):
    method: DeadLoadingMethodEnum


class DeadLoadingByDensityEnhancement(DeadLoadingBase):
    method: Literal[DeadLoadingMethodEnum.DENSITY_ENHANCEMENT]
    enhancement_factor: float = Field(
        ge=-1.0
    )


class DeadLoadingByDirectValue(DeadLoadingBase):
    method: Literal[DeadLoadingMethodEnum.DIRECT_VALUE]
    linear_load_value: QuantityParaModel | None = None
    pressure_load_value: QuantityParaModel | None = None


DeadLoading = Annotated[
    Union[
        DeadLoadingByDensityEnhancement,
        DeadLoadingByDirectValue,
    ],
    Field(discriminator="method"),
]


class StructuralLoadApplicationBase(BaseModelParaModel):
    application_type: StructuralApplicationTypeEnum


class StructuralLoadApplicationByGroup(
    StructuralLoadApplicationBase
):
    application_type: Literal[
        StructuralApplicationTypeEnum.STRUCTURAL_GROUP_ID
    ]
    group_id: str


class StructuralLoadApplicationByComponentType(
    StructuralLoadApplicationBase
):
    application_type: Literal[
        StructuralApplicationTypeEnum.STRUCTURAL_COMPONENT_TYPE
    ]
    component_type: StructuralComponentTypeParaModel


_StructuralLoadApplication = Annotated[
    Union[
        StructuralLoadApplicationByGroup,
        StructuralLoadApplicationByComponentType,
    ],
    Field(discriminator="application_type"),
]


class StructuralLoadBase(AashtoLoadModelBase):
    load_application_domain: Literal[
        LoadApplicationDomainEnum.STRUCTURE
    ] = LoadApplicationDomainEnum.STRUCTURE


class StructuralInServiceLoadBase(
    StructuralLoadBase
):
    load_service_state: Literal[
        LoadServiceStateEnum.IN_SERVICE
    ] = LoadServiceStateEnum.IN_SERVICE
    structural_load_type: StructuralLoadTypeEnum


class StructuralInServiceDeadLoad(
    StructuralInServiceLoadBase
):
    structural_load_type: Literal[
        StructuralLoadTypeEnum.DEAD_LOAD
    ] = StructuralLoadTypeEnum.DEAD_LOAD
    loading: DeadLoading
    load_application: _StructuralLoadApplication
    load_nature: Literal[
        AashtoLoadNatureEnum.DC,
        AashtoLoadNatureEnum.DW
    ]


#### PRESTRESSING

class PrestressApplicationTypeEnum(CaseInsensitiveEnum):
    BY_STRESS = 'by stress'
    # BY_FORCE = 'by force'


class TendonJackingTypeEnum(CaseInsensitiveEnum):
    START_OF_TENDON = 'start of tendon'
    END_OF_TENDON = 'end of tendon'
    BOTH_ENDS = 'both ends'


class PrestressLoadBase(BaseModelParaModel):
    prestress_application_type: PrestressApplicationTypeEnum
    tendon_jacking_type: TendonJackingTypeEnum


class PrestressLoadByStress(PrestressLoadBase):
    prestress_application_type: Literal[
        PrestressApplicationTypeEnum.BY_STRESS
    ] = PrestressApplicationTypeEnum.BY_STRESS
    tendon_stress: QuantityParaModel

_PrestressLoad = Annotated[
    Union[
        PrestressLoadByStress
        ],
    Field(discriminator="prestress_application_type"),
]

class PrestressingInServiceLoad(StructuralInServiceLoadBase):
    structural_load_type: Literal[
        StructuralLoadTypeEnum.PRESTRESSING
    ] = StructuralLoadTypeEnum.PRESTRESSING
    load_nature: Literal[
        AashtoLoadNatureEnum.PS
    ] = AashtoLoadNatureEnum.PS
    load_application: list[_StructuralLoadApplication]
    loading: _PrestressLoad


_StructuralInService = Annotated[
    Union[
        StructuralInServiceDeadLoad,
        PrestressingInServiceLoad
    ],
    Field(discriminator="structural_load_type"),
]

#### PRESTRESSING ENDS

class NonStructuralDeadLoadApplicationBase(BaseModelParaModel):
    application_type: LoadApplicationTypeEnum


class NonStructuralDeadLoadApplicationByDeckAppurtenance(
    NonStructuralDeadLoadApplicationBase
):
    application_type: Literal[
        LoadApplicationTypeEnum.DECK_APPURTENANCE_ID
    ]
    appurtenance_id: str


NonStructuralDeadLoadApplication = Annotated[
    Union[
        NonStructuralDeadLoadApplicationByDeckAppurtenance,
    ],
    Field(discriminator="application_type"),
]


class NonStructuralLoadBase(AashtoLoadModelBase):
    load_application_domain: Literal[
        LoadApplicationDomainEnum.ANCILLARY_WORKS
    ] = LoadApplicationDomainEnum.ANCILLARY_WORKS


class NonStructuralInServiceDeadLoad(
    NonStructuralLoadBase
):
    load_service_state: Literal[
        LoadServiceStateEnum.IN_SERVICE
    ] = LoadServiceStateEnum.IN_SERVICE
    load_nature: Literal[
        AashtoLoadNatureEnum.DC,
        AashtoLoadNatureEnum.DW
    ]
    load_application: NonStructuralDeadLoadApplication
    loading: DeadLoading


# DISCRIMINATED UNIONS

# Level 5: structural dead loads — discriminator: load_service_state
_StructuralLoad = Annotated[
    Union[
        _StructuralInService,
    ],
    Field(discriminator="load_service_state"),
]

# Level 5: ancillary works dead loads — discriminator: load_service_state
_NonStructuralLoad = Annotated[
    Union[
        NonStructuralInServiceDeadLoad,
    ],
    Field(discriminator="load_service_state"),
]

# Level 4: all dead loads — discriminator: load_application_domain
_DeadLoad = Annotated[
    Union[
        _StructuralLoad,
        _NonStructuralLoad,
    ],
    Field(discriminator="load_application_domain"),
]
