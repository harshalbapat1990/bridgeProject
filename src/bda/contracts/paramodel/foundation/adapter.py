from typing import List

from pydantic import TypeAdapter

from bda.contracts.paramodel.foundation.foundation_bc_para_model import FoundationBCsParaModel


class FoundationBCsParaModelAdapter:

    @staticmethod
    def parse_list(raw_list: List) -> List[FoundationBCsParaModel]:
        adapter = TypeAdapter(List[FoundationBCsParaModel])
        return adapter.validate_python(raw_list)