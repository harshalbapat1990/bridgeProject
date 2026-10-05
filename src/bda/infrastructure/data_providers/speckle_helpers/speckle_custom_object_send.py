from bda.infrastructure.data_providers.speckle_helpers.speckle_connector import BridgeDataPlatformSpeckleConnector, SpeckleUrlComponents, parse_speckle_url

# Data Object Import
from specklepy.objects.data_objects import DataObject
# Collection import
from specklepy.objects.models.collections.collection import Collection

from bda.contracts.speckle_contracts.bda_analytical.sections.general_section_data_object_parameters import (
    SectionDescription,
    SectionType,
    SectionOffset,
    SectionFamily,
)

# MODEL CONFIG

speckle_url = "https://ldd-emea.jacobs.com/projects/c05550b96c/models/75a088eee7"


section_collection = Collection(
    name="Sections",
    applicationId="BDA-SECTION-COLLECTION"
)

section_collection.elements.append(
    DataObject(
        applicationId="SEC-001",
        name="Test Section 1",
        properties={
            "Section Description": SectionDescription(
                isUser = True,
                provided_value = "Test I-Section for BDA"
            ),
            "Section Family": SectionFamily(
                isUser = True,
                provided_value = "Standard Shape"
                ),
            "Section Type": SectionType(
                isUser = True,
                provided_value = "I-Section"
            ),
            "Section Offset": SectionOffset(
                isUser = True,
                provided_value = "Center-Top"
            )
        },
        displayValue=[]
    )
)

speckle_connector = BridgeDataPlatformSpeckleConnector(
    speckle_url_components=parse_speckle_url(speckle_url),
    token=None
)
speckle_connector.select_project(speckle_connector.speckle_url.project_id)
speckle_connector.select_model(speckle_connector.speckle_url.model_id)
speckle_connector.commit_version(section_collection, message="Adding section collection with test section")