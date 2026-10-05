import re
from bda.contracts.paramodel.sections import SectionParaModel, SectionParaModelAdapter
from bda.contracts.speckle_contracts.base_objects import BridgeCollection

from pydantic import Field, field_validator
from typing import Literal, ClassVar, Union, Annotated

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
    Field(discriminator="bda_speckle_type")
]


class SectionsCollection(BridgeCollection):
    COLLECTION_ID_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"^COL-SECTIONS$"
    )

    applicationId: str = Field(
        pattern=r"^COL-SECTIONS$",
    )

    name: Literal["Sections"] = "Sections"

    elements: list[SectionObjectUnion] = Field(
        default_factory=list
    )
    
    bda_speckle_type: Literal[
        "Speckle.Core.Models.Collections.Collection"
    ] = "Speckle.Core.Models.Collections.Collection"

    @classmethod
    def create(
        cls,
        sections: list[SectionObjectUnion] | None = None,
        application_id: str = "sections",
    ) -> "SectionsCollection":

        return cls(
            id=None,
            applicationId=application_id,
            elements=sections or [],
        )
    
    @field_validator("applicationId")
    @classmethod
    def validate_application_id(
        cls,
        value: str,
    ):

        if not cls.COLLECTION_ID_PATTERN.match(value):
            raise ValueError(
                "Sections collection applicationId must be COL-SECTIONS"
            )

        return value

if __name__ == "__main__":

    from bda.contracts.paramodel.sections.sections_para_models import (
        SectionTypeParaModel,
        TaperVariationParaModel,
    )

    # ------------------------------------------------------
    # Start Section
    # ------------------------------------------------------

    start_section = SectionDataObject_ISection.create(
        name="Girder Start",
        application_id="SECT-0001-STANDARD-ISECTION",

        total_height=1.5,
        top_flange_width=0.50,
        bottom_flange_width=0.50,

        web_thickness=0.020,

        top_flange_thickness=0.030,
        bottom_flange_thickness=0.030,

        web_inner_radius=0.020,
        flange_end_radius=0.010,
    )

    # ------------------------------------------------------
    # End Section
    # ------------------------------------------------------

    end_section = SectionDataObject_ISection.create(
        name="Girder End",
        application_id="SECT-0002-STANDARD-ISECTION",

        total_height=2.0,
        top_flange_width=0.70,
        bottom_flange_width=0.70,

        web_thickness=0.020,

        top_flange_thickness=0.030,
        bottom_flange_thickness=0.030,

        web_inner_radius=0.020,
        flange_end_radius=0.010,
    )

    # ------------------------------------------------------
    # Taper Definition
    # ------------------------------------------------------

    tapered_section = SectionDataObject_Tapered.create(
        name="Tapered Girder",

        application_id="SECT-0003-TAPERED",

        start_section_application_id="SECT-0001-STANDARD-ISECTION",
        end_section_application_id="SECT-0002-STANDARD-ISECTION",

        section_type=SectionTypeParaModel.I_SECTION,

        taper_y_variation=TaperVariationParaModel.LINEAR,
        taper_z_variation=TaperVariationParaModel.LINEAR,
    )

    # ------------------------------------------------------
    # Sections Collection
    # ------------------------------------------------------

    sections = SectionsCollection.create(
        sections=[
            start_section,
            end_section,
            tapered_section,
        ],
        application_id="COL-SECTIONS",
    )

    print(
        sections.model_dump_json(
            indent=4,
            by_alias=True
        )
    )
