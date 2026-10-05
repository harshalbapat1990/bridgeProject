from __future__ import annotations

from typing import Literal

from bda.contracts.paramodel.loadings.enums import LoadContextEnum
from bda.contracts.paramodel.loadings.load_model_base_para_models import LoadModelBaseParaModel


class DesignLoadModelBase(LoadModelBaseParaModel):
    load_context: Literal[LoadContextEnum.DESIGN] = LoadContextEnum.DESIGN
