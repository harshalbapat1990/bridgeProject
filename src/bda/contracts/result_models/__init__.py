"""Result model DTOs — intermediate representation for POST-pipeline FEM data.

Analogous to the `paramodel` package for PRE, but for POST-processing:
raw FEM API responses are wrapped in these dataclasses before being
passed to mappers that produce domain objects.

    FEM API response → ...ResultModel → ResultMapper → domain object

Unlike ParaModel (Pydantic BaseModel, validated JSON contract),
ResultModel uses plain dataclasses — the FEM API values are trusted
numeric data, not user-supplied JSON.
"""

from bda.contracts.result_models.csi.displacement_result_model import CsiDisplacementResultModel
from bda.contracts.result_models.midas.displacement_result_model import MidasDisplacementResultModel
from bda.contracts.result_models.force_result_model import ForceResultModel
from bda.contracts.result_models.section_properties_result_model import SectionPropertiesResultModel
from bda.contracts.result_models.stress_result_model import StressResultModel

__all__ = [
    "ForceResultModel",
    "CsiDisplacementResultModel",
    "MidasDisplacementResultModel",
    "SectionPropertiesResultModel",
    "StressResultModel",
]
