from bda.contracts.paramodel.sections import SectionParaModel, SectionParaModelAdapter
from bda.contracts.speckle_contracts.base_objects import BridgeCollection

from pydantic import Field, field_validator
from typing import Literal

import json

# Standard Section Type Imports
from bda.contracts.speckle_contracts.bda_analytical.sections.standard_shape_family.standard_shape_section_types.angle_type_data_object import SectionDataObject_Angle
from bda.contracts.speckle_contracts.bda_analytical.sections.standard_shape_family.standard_shape_section_types.isection_type_data_object import SectionDataObject_ISection
from bda.contracts.speckle_contracts.bda_analytical.sections.standard_shape_family.standard_shape_section_types.box_type_data_object import SectionDataObject_Box
from bda.contracts.speckle_contracts.bda_analytical.sections.standard_shape_family.standard_shape_section_types.channel_type_data_object import SectionDataObject_Channel
from bda.contracts.speckle_contracts.bda_analytical.sections.standard_shape_family.standard_shape_section_types.pipe_type_data_object import SectionDataObject_Pipe
from bda.contracts.speckle_contracts.bda_analytical.sections.standard_shape_family.standard_shape_section_types.solid_circle_data_object import SectionDataObject_SolidCircle
from bda.contracts.speckle_contracts.bda_analytical.sections.standard_shape_family.standard_shape_section_types.solid_rectangle_data_object import SectionDataObject_SolidRectangle

# Composite Section Type Imports
from bda.contracts.speckle_contracts.bda_analytical.sections.composite_family.composite_section_types.i_symmetrical_data_object import SectionDataObject_CompositeISymmetric
from bda.contracts.speckle_contracts.bda_analytical.sections.composite_family.composite_section_types.i_asymmetrical_data_object import SectionDataObject_CompositeIAsymmetric

# PSC Sections
from bda.contracts.speckle_contracts.bda_analytical.sections.psc_family.psc_section_types.psc_value_type_data_object import SectionDataObject_PSCValue

# Taper Groups
from bda.contracts.speckle_contracts.bda_analytical.sections.taper_section_group import SectionDataObject_Tapered




from pydantic import Field, model_validator
from typing import Literal

from typing import Union, Annotated
import json

SectionObjectUnion = Annotated[
    Union[
        # Sections
        SectionDataObject_Angle,
        SectionDataObject_ISection,
        SectionDataObject_Box,
        SectionDataObject_Channel,
        SectionDataObject_Pipe,
        SectionDataObject_SolidCircle,
        SectionDataObject_SolidRectangle,
        SectionDataObject_CompositeISymmetric,
        SectionDataObject_CompositeIAsymmetric,
        SectionDataObject_PSCValue,

        # Taper Groups
        SectionDataObject_Tapered
    ],
    Field(discriminator="speckle_type")
]



class SectionsCollection(BridgeCollection):
    name: Literal["Sections"] = "Sections"
    elements: list[SectionObjectUnion] = Field(default_factory=list)

if __name__ == "__main__":
    from bda.contracts.speckle_contracts.example_from_json import example_from_schema
    from bda.infrastructure.data_providers.speckle_helpers.speckle_send_object import ingest_ui_json_and_commit
    # Schema Check
    print("Section Collection Schema Generated")
    section_collection_schema = SectionsCollection.model_json_schema()
    print(json.dumps(section_collection_schema, indent=2))

    


