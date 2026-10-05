from __future__ import annotations

from typing import Annotated, Union

from pydantic import Field

from bda.contracts.paramodel.loadings.design.aashto.construction_loads import (
    _ConstructionLoad,
)
from bda.contracts.paramodel.loadings.design.aashto.structural_loads import (
    _NonStructuralLoad,
    _StructuralLoad,
)
from bda.contracts.paramodel.loadings.design.aashto.environment_loads import (
    _EnvironmentLoad,
)
from bda.contracts.paramodel.loadings.design.aashto.live_loads import (
    _LiveLoadInService,
)

# Level 3: LIVE_LOAD branch — discriminator: load_service_state
_LiveLoad = Annotated[
    Union[
        _LiveLoadInService,
    ],
    Field(discriminator="load_service_state"),
]

# Level 2: load_application_domain
_AashtoLoad = Annotated[
    Union[
        _StructuralLoad,
        _NonStructuralLoad,
        _LiveLoad,
        _ConstructionLoad,
        _EnvironmentLoad,
    ],
    Field(discriminator="load_application_domain"),
]
