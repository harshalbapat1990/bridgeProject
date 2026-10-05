from pathlib import Path
import datetime

from bda.contracts.speckle_contracts.bda_analytical.model_root import ModelRootCollection
from bda.contracts.speckle_contracts.bda_analytical.model_config_data.model_config_data_DataObject import (
    BDA_ModelDataDataObject,
    ModelUnitSystemEnum,
    OutputSoftwareEnum,
    DesignCodesEnum,
    StructureTypeEnum
)

from bda.contracts.speckle_contracts.bda_analytical.materials.materials_collection import (
    MaterialsCollection
)

from bda.contracts.speckle_contracts.bda_analytical.materials.concrete.concrete_material_aashto import (
    ConcreteAASHTOMaterialDataObject
)

from bda.contracts.speckle_contracts.bda_analytical.materials.steel.steel_material_aashto import (
    SteelAASHTOMaterialDataObject
)

from bda.contracts.speckle_contracts.bda_analytical.materials.reinforcement.reinforcement_material_aashto import (
    ReinforcementAASHTOMaterialDataObject
)

from bda.contracts.speckle_contracts.bda_analytical.materials.tendon.tendon_material_aashto import (
    TendonAASHTOMaterialDataObject
)

from bda.contracts.speckle_contracts.bda_analytical.sections.section_collection import (
    SectionsCollection,
    SectionDataObject_Angle,
    SectionDataObject_Box,
    SectionDataObject_Channel,
    SectionDataObject_CompositeIAsymmetric,
    SectionDataObject_CompositeISymmetric,
    SectionDataObject_ISection,
    SectionDataObject_Pipe,
    SectionDataObject_PSCValue,
    SectionDataObject_SolidCircle,
    SectionDataObject_SolidRectangle,
    SectionDataObject_Tapered
)
from bda.contracts.speckle_contracts.bda_analytical.sections.taper_section_group import TaperVariationParaModel, SectionTypeParaModel, TaperYVariationParameter, TaperZVariationParameter

from bda.infrastructure.data_providers.speckle_helpers.speckle_send_object import ingest_ui_json_and_commit

# Sections

section_collection = SectionsCollection.create(
    application_id="COL-SECTIONS",
    sections=[
        SectionDataObject_Angle.create(
            name="Example Angle",
            description="Unequal angle section",
            application_id="SECT-0001-STANDARD-ANGLE",
            height=0.20,
            width=0.15,
            web_thickness=0.015,
            flange_thickness=0.015,
            unit="m",
        ),
        SectionDataObject_Box.create(
            name="Example Box",
            description="Rectangular box section",
            application_id="SECT-0002-STANDARD-BOX",
            height=0.30,
            flange_width=0.20,
            web_thickness=0.012,
            flange_thickness=0.016,
            unit="m",
        ),
        SectionDataObject_Channel.create(
            name="Example Channel",
            description="Parallel flange channel section",
            application_id="SECT-0003-STANDARD-CHANNEL",

            height=0.30,
            top_flange_width=0.10,
            bottom_flange_width=0.10,

            web_thickness=0.010,

            top_flange_thickness=0.015,
            bottom_flange_thickness=0.015,

            web_inner_radius=0.008,
            flange_end_radius=0.004,

            unit="m",
        ),
        SectionDataObject_Pipe.create(
            name="Example Pipe",
            description="Circular hollow section",
            application_id="SECT-0004-STANDARD-PIPE",

            external_diameter=0.324,
            wall_thickness=0.012,

            unit="m",
        ),
        SectionDataObject_SolidCircle.create(
            name="Example Solid Circle",
            description="Solid circular section",
            application_id="SECT-0005-STANDARD-SOLID-CIRCLE",

            diameter=0.10,

            unit="m",
        ),
        SectionDataObject_SolidRectangle.create(
            name="Example Solid Rectangle",
            description="Example solid rectangle section",
            application_id="SECT-0006-STANDARD-SOLID-RECTANGLE",
            height=0.75,
            width=1
        ),
        SectionDataObject_ISection.create(
            name="Example I Section",
            description="Symmetrical I section",
            application_id="SECT-0007-STANDARD-ISECTION",

            total_height=0.60,
            top_flange_width=0.25,
            bottom_flange_width=0.25,

            web_thickness=0.012,

            top_flange_thickness=0.020,
            bottom_flange_thickness=0.020,

            web_inner_radius=0.012,
            flange_end_radius=0.006,

            unit="m",
        ),
        SectionDataObject_CompositeISymmetric.create(
            name="Example Composite I Section",
            description="Composite steel I-girder with concrete deck",
            application_id="SECT-0008-COMPOSITE-I-SYMMETRIC",

            slab_width=3.50,
            slab_thickness=0.25,
            slab_girder_spacing=3.00,

            girder_top_flange_width=0.40,
            girder_top_flange_thickness=0.025,

            girder_bottom_flange_width=0.50,
            girder_bottom_flange_thickness=0.035,

            girder_web_thickness=0.016,
            girder_web_height=1.80,

            unit="m",
        ),
        SectionDataObject_CompositeIAsymmetric.create(
            name="Example Composite I Asymmetric Section",
            description="Composite steel I-girder with asymmetric flange geometry",
            application_id="SECT-0009-COMPOSITE-I-ASYMMETRIC",

            slab_reference_offset=0.0,

            top_flange_reference_offset=1.55,
            bottom_flange_reference_offset=1.45,

            slab_width=3.50,
            slab_thickness=0.25,
            slab_girder_spacing=3.00,

            girder_top_flange_left_width=0.22,
            girder_top_flange_right_width=0.18,
            girder_top_flange_thickness=0.025,

            girder_bottom_flange_left_width=0.30,
            girder_bottom_flange_right_width=0.20,
            girder_bottom_flange_thickness=0.035,

            girder_web_thickness=0.016,
            girder_web_height=1.80,

            unit="m",
        ),
        SectionDataObject_PSCValue.create(
            name="Example PSC Box ",
            application_id="SECT-0010-PSC-VALUE",
            external_polygon=[
                (-6.0, 2.5),
                (6.0, 2.5),
                (6.0, 2.35),
                (2.75, 0.0),
                (-2.75, 0.0),
                (-6.0, 2.35),
            ],

            internal_polygons={
                "Void 1": [
                    (-0.25, 2.2),
                    (-1.8323, 2.2),
                    (-2.8323, 2.1),
                    (-2.3510, 0.6155),
                    (-0.25, 0.3),
                ],

                "Void 2": [
                    (0.25, 2.2),
                    (1.8323, 2.2),
                    (2.8323, 2.1),
                    (2.3510, 0.6155),
                    (0.25, 0.3),
                ],
            },

            description="PSC box girder section",
            unit="m",
        ),
        SectionDataObject_SolidCircle.create(
            name="Example Taper Start",
            description="Larger diameter at start of tapered circular member",
            application_id="SECT-0011-STANDARD-SOLID-CIRCLE",
            diameter=0.60,
            unit="m",
        ),
        SectionDataObject_SolidCircle.create(
            name="Example Taper End",
            description="Smaller diameter at end of tapered circular member",
            application_id="SECT-0012-STANDARD-SOLID-CIRCLE",
            diameter=0.40,
            unit="m",
        ),
        SectionDataObject_Tapered.create(
            name="Example Circular Taper",
            application_id="SECT-0013-TAPERED",

            start_section_application_id="SECT-0011-STANDARD-SOLID-CIRCLE",
            end_section_application_id="SECT-0012-STANDARD-SOLID-CIRCLE",

            section_type=SectionTypeParaModel.SOLID_ROUND,

            taper_y_variation=TaperVariationParaModel.LINEAR,

            taper_z_variation=TaperVariationParaModel.LINEAR
        )
    ],
)

# Materials

materials_elements = [
    ConcreteAASHTOMaterialDataObject.create(
        name="Example AASHTO Concrete",
        application_id="MAT-0001-CONC-AASHTO",
        unit_weight=23.536,
        poissons_ratio=0.2,
        modulus_of_elasticity=30,
        elasticity_unit="GPa",
        coefficient_of_thermal_expansion=1.0e-05,
        expected_concrete_strength=40000,
        specified_concrete_strength=32000
    ),
    SteelAASHTOMaterialDataObject.create(
        name="Example AASHTO Steel",
        application_id="MAT-0002-STEEL-AASHTO",
        unit_weight=76.982,
        poissons_ratio=0.3,
        modulus_of_elasticity=200,
        elasticity_unit="GPa",
        coefficient_of_thermal_expansion=1.2e-05,
        minimum_steel_tensile_strength=550000,
        expected_steel_tensile_strength=650000,
        minimum_steel_yield_strength=420000,
        expected_steel_yield_strength=500000
    ),
    ReinforcementAASHTOMaterialDataObject.create(
        name="Example Reinforcing Steel",
        application_id="MAT-0003-REBAR-AASHTO",
        unit_weight=76.98,                     
        unit_weight_unit="kN/m³",
        modulus_of_elasticity=200,             
        elasticity_unit="GPa",
        poissons_ratio=0.30,
        coefficient_of_thermal_expansion=1.2e-05,
        thermal_coefficient_unit="1/Δ°C",

        minimum_reinforcement_yield_strength=420000,      
        expected_reinforcement_yield_strength=500000,     

        minimum_reinforcement_tensile_strength=620000,    
        expected_reinforcement_tensile_strength=690000,   

        strength_unit="kN/m²",
    ),
    TendonAASHTOMaterialDataObject.create(
        name="Example Prestressing Strand",
        application_id="MAT-0004-TENDON-AASHTO",

        unit_weight=76.98,
        modulus_of_elasticity=195,
        elasticity_unit="GPa",

        poissons_ratio=0.30,

        coefficient_of_thermal_expansion=1.2e-05,
        thermal_coefficient_unit="1/Δ°C",

        tendon_yield_strength=1580000,                    
        tendon_specified_minimum_tensile_strength=1860000 
        )
]

# Materials

materials_collection = MaterialsCollection.create(
    application_id="COL-MATERIALS",
    materials=materials_elements
)


# model_config
model_config = BDA_ModelDataDataObject.create(
    model_unit_system=ModelUnitSystemEnum.METRIC,
    output_software=OutputSoftwareEnum.CSI_BRIDGE,
    design_code=DesignCodesEnum.AASHTO,
    structure_type=StructureTypeEnum.STEEL_COMPOSITE
)

model = ModelRootCollection.create(
    model_config=model_config,
    materials=materials_collection,
    sections=section_collection,
)

# output_path = Path.home() / "Downloads" / "material_and_sections.json"
# output_path.write_text(
#     model.model_dump_json(
#         indent=4,
#         by_alias=True
#     ),
#     encoding="utf-8"
# )
# print(f"Model JSON written to: {output_path}")

ingest_ui_json_and_commit(
    json_data=model.model_dump(
        by_alias=True,
        mode="json"
    ),
    pydantic_model=ModelRootCollection,
    speckle_url="https://design.jacobs.com/projects/8f0d636aa6/models/0ed6df7cda",
    commit_message=(
        f"Material and Sections model w bda_speckle_type - "
        f"{datetime.datetime.now():%Y-%m-%d %H:%M}"
    )
)


