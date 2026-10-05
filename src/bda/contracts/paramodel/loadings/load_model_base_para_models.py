from __future__ import annotations

from bda.contracts.paramodel.shared.base_model_para_model import (
    BaseModelParaModel,
)
from bda.contracts.paramodel.loadings.enums import (
    LoadApplicationDomainEnum,
    LoadContextEnum,
    LoadServiceStateEnum,
    MainCodeEnum,
    SecondaryCodeEnum,
)


class LoadModelBaseParaModel(BaseModelParaModel):
    load_context: LoadContextEnum
    main_code: MainCodeEnum
    secondary_code: SecondaryCodeEnum = SecondaryCodeEnum.NONE
    load_application_domain: LoadApplicationDomainEnum
    load_service_state: LoadServiceStateEnum


