from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from bda.contracts.paramodel.loadings.design.aashto.enums import AashtoLoadNatureEnum
from bda.contracts.paramodel.loadings.design.aashto.aashto_load_model_base import AashtoLoadModelBase
from bda.contracts.shared.quantity_para_model import QuantityParaModel
from bda.contracts.paramodel.loadings.enums import (
    LoadApplicationDomainEnum,
    LoadServiceStateEnum,
)


class ConstructionLoadBase(AashtoLoadModelBase):
    load_application_domain: Literal[
        LoadApplicationDomainEnum.CONSTRUCTION
    ] = LoadApplicationDomainEnum.CONSTRUCTION


class ExecutionLoad(
    ConstructionLoadBase
):
    load_service_state: Literal[
        LoadServiceStateEnum.CONSTRUCTION
    ] = LoadServiceStateEnum.CONSTRUCTION

    load_nature: Literal[
        AashtoLoadNatureEnum.CS
    ] = AashtoLoadNatureEnum.CS

    load_fixed_material_udl: QuantityParaModel | None = None
    load_variable_material_udl: QuantityParaModel | None = None
    load_personel_and_eqp_udl: QuantityParaModel | None = None


# DISCRIMINATED UNIONS

# Level 4: construction domain loads — discriminator: load_service_state
_ConstructionLoad = Annotated[
    Union[
        ExecutionLoad,
    ],
    Field(discriminator="load_service_state"),
]
