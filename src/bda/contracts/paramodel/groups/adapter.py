from typing import List

from pydantic import TypeAdapter

from bda.contracts.paramodel.groups import GeometryGroupParaModel



class GroupsParaModelAdapter:

    @staticmethod
    def parse_list(raw_list: List) -> List[GeometryGroupParaModel]:
        adapter = TypeAdapter(List[GeometryGroupParaModel])
        return adapter.validate_python(raw_list)