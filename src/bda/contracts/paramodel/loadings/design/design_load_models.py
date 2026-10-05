from __future__ import annotations

from typing import Annotated, Union

from pydantic import Field

from bda.contracts.paramodel.loadings.design.aashto.aashto_load_models import (
    _AashtoLoad,
)

# Level 1: main_code
_DesignLoad = Annotated[
    Union[
        _AashtoLoad,
    ],
    Field(discriminator="main_code"),
]
