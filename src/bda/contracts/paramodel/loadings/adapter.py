from __future__ import annotations

from typing import Annotated, Any, List, Union

from pydantic import Field, TypeAdapter

from bda.contracts.paramodel.loadings.design.design_load_models import (
    _DesignLoad,
)
from bda.contracts.paramodel.loadings.load_model_base_para_models import (
    LoadModelBaseParaModel,
)

# Discriminator evaluation order:
# Level 0: load_context
# Level 1: main_code
# Level 2: load_application_domain
# Level 3: load_service_state
# Level 4: env_load_type
#
# Type resolution follows the hierarchy above, progressively narrowing the
# selection until the final load model is identified. The tree can be extended
# at any level by introducing new discriminator values, branches, or concrete
# load types while preserving the hierarchical structure.

# Level 0: load_context
LoadModelParaModel = Annotated[
    Union[
        _DesignLoad,
    ],
    Field(discriminator="load_context"),
]

_ADAPTER = TypeAdapter(List[LoadModelParaModel])


class LoadParaModelAdapter:

    @staticmethod
    def parse(data: dict[str, Any]) -> LoadModelBaseParaModel:
        return TypeAdapter(LoadModelParaModel).validate_python(data)

    @staticmethod
    def parse_list(raw_list: list[dict[str, Any]]) -> list[LoadModelBaseParaModel]:
        return _ADAPTER.validate_python(raw_list)
