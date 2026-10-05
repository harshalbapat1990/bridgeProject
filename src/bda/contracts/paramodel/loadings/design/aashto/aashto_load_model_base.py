from __future__ import annotations

from typing import Literal

from bda.contracts.paramodel.loadings.enums import MainCodeEnum
from bda.contracts.paramodel.loadings.design.aashto.enums import AashtoLoadNatureEnum
from bda.contracts.paramodel.loadings.design.design_load_model_base_para_model import DesignLoadModelBase


class AashtoLoadModelBase(DesignLoadModelBase):
    main_code: Literal[MainCodeEnum.AASHTO] = MainCodeEnum.AASHTO
    load_nature: AashtoLoadNatureEnum
