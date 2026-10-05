from typing import List

from pydantic import TypeAdapter

from bda.contracts.paramodel.bearings.bearing_bc_para_model import BearingBCsSupportParaModel


class BearingBCsParaModelAdapter:

    @staticmethod
    def parse_list(raw_list: List) -> List[BearingBCsSupportParaModel]:
        adapter = TypeAdapter(List[BearingBCsSupportParaModel])
        return adapter.validate_python(raw_list)