# This file contains the code for creating a speckle connection object for Bridges DA toolset
import os

from dotenv import load_dotenv
from specklepy.api.client import SpeckleClient
from specklepy.core.api.enums import ProjectVisibility
from specklepy.transports.server import ServerTransport
from specklepy.api import operations

from specklepy.objects import Base

import re
from dataclasses import dataclass
from bda.infrastructure.utils import AppLogger

@dataclass
class SpeckleUrlComponents:
    server_url: str
    project_id: str
    model_id: str
    version_id: str | None


def parse_speckle_url(url: str) -> SpeckleUrlComponents:
    pattern = re.compile(
        r"(?P<server_url>https?://[^/]+)/projects/"
        r"(?P<project_id>[^/]+)/models/"
        r"(?P<model_id>[^@/]+)"
        r"(?:@(?P<version_id>[^/?#]+))?$"
    )

    match = pattern.fullmatch(url)

    if not match:
        raise ValueError(f"Invalid Speckle URL format: {url}")

    groups = match.groupdict()

    return SpeckleUrlComponents(
        server_url=groups["server_url"],
        project_id=groups["project_id"],
        model_id=groups["model_id"],
        version_id=groups.get("version_id"),
    )

class BridgeDataPlatformSpeckleConnector():
    """
    Manages connections and operations with a Speckle server for the Bridges DA toolset.

    This connector handles authentication, project/model/version management, and data operations
    with Speckle servers. It requires authentication credentials provided either as constructor
    arguments or via environment variables loaded from a .env file.

    .env File Requirements:
        The .env file in the repository root must contain the following variables:
        
        SPECKLE_TOKEN: str
            - The authentication token for Speckle server access
            - Obtain from your Speckle server account settings
            - Format: 32+ character hexadecimal string (e.g., 'b3e9109bcc41aeb627e6348a89a29a9d13a6ec751c')
            - Must have valid permissions/scopes for the target Speckle server
            - Note: Tokens can expire; refresh from server if authentication fails with 403 Forbidden
        
        SPECKLE_SERVER: str
            - The base URL of the Speckle server
            - Format: https://domain.com (no trailing slash)
            - Example: https://ldd-emea.jacobs.com or https://app.speckle.systems
            - Must match the server where the SPECKLE_TOKEN was issued
            - For self-hosted Speckle instances, provide the instance URL
    
    Example .env file:
        SPECKLE_TOKEN=b3e9109bcc41aeb627e6348a89a29a9d13a6ec751c
        SPECKLE_SERVER=https://ldd-emea.jacobs.com

    Raises:
        EnvironmentError: If SPECKLE_TOKEN or SPECKLE_SERVER are not provided and cannot be
            loaded from environment variables, or if authentication fails (typically due to
            invalid/expired token or server mismatch).
    """
    def __init__(self, speckle_url_components:SpeckleUrlComponents,token: str|None = None):
        
        # Read env token and speckle url if not provided as arguments

        if token is None:
            load_dotenv(".env")
            token = os.getenv("BDA_SPECKLE_TOKEN")
            if not token:
                raise EnvironmentError("SPECKLE_TOKEN environment variable is required")

        if speckle_url_components is None:
            load_dotenv(".env")
            speckle_url_components = os.getenv("BDA_SPECKLE_SERVER")
            if not speckle_url_components:
                raise EnvironmentError("BDA_SPECKLE_SERVER environment variable is required")


        # Authenticate with the speckle server and create a connection object
        self.speckle_url = speckle_url_components
        
        # Create Client and authenticate
        AppLogger().info(f"Connecting to Speckle Server:{self.speckle_url.server_url}...")
        self.client = SpeckleClient(
            host=self.speckle_url.server_url
            )

        try:
            self.client.authenticate_with_token(token)
            # account = Account.from_token(token, server_url=self.speckle_url.server_url)
            # account.serverInfo = account.serverInfo.model_copy(update={"url": self.speckle_url.server_url})
            # self.client.account = account
        except Exception as ex:
            AppLogger().error(
                f"Failed to authenticate with Speckle server at {self.speckle_url}. "
                f"Check that SPECKLE_TOKEN is valid and has access to this server.\n"
                f"Error: {type(ex).__name__}: {str(ex)}"
            )
            raise EnvironmentError("Authentication failed.") from ex
        
        AppLogger().info(f"✓ Successfully Authenticated as {self.client.account.userInfo.name} ({self.client.account.userInfo.email})")
    
    # Project management functions
    
    def create_project(self, project_name: str, description: str="New Speckle Project", visibility: ProjectVisibility=ProjectVisibility.PRIVATE)->str:
        """Creates a new project on the speckle server and returns the project id"""
        from specklepy.core.api.inputs.project_inputs import ProjectCreateInput
        
        new_project = self.client.project.create(ProjectCreateInput(
            name=project_name,
            description=description,
            visibility=visibility
        ))

        self.select_project(new_project.id)
        return new_project.id
    
    def select_project(self, project_id: str):
        """Selects a project to work with by its id"""
        AppLogger().info(f"Selecting Project {project_id}...")
        assert project_id in self.available_project_ids, f"Project ID {project_id} not found in available projects. Please select a valid project ID."
        self.active_project_id = project_id
        self.transport = ServerTransport(stream_id=self.active_project_id, client=self.client)
        AppLogger().info(f"Project {project_id} Successfully Selected")

    def delete_project(self, project_id: str):
        """Deletes a project by its id"""
        assert project_id in self.available_project_ids, f"Project ID {project_id} not found in available projects. Please select a valid project ID."
        self.client.project.delete(project_id)

        print(f"Project with ID {project_id} has been deleted.")

    @property
    def projects(self):
        return self.client.active_user.get_projects()
    
    @property
    def available_project_ids(self)->list[str]:
        """Returns a list of available project ids on speckle client"""
        return [p.id for p in self.projects.items]
    
    # Model Management functions

    def create_model(self, project_id:str, model_name: str, description: str="New Speckle Model", visibility: ProjectVisibility=ProjectVisibility.PRIVATE)->str:
        """Creates a new model on the speckle server and returns the model id"""
        from specklepy.core.api.inputs.model_inputs import CreateModelInput
        
        # Create a new model
        model_input = CreateModelInput(
            project_id=project_id,
            name=model_name,
            description=description
        )
        model = self.client.model.create(model_input)

        self.select_model(model_id=model.id)

        # Initialse Model
        self.initailise_model(name=f"Initial Version")

        return model.id
    
    def select_model(self, model_id: str):
        """Selects a model to work with by its id"""
        AppLogger().info(f"Selecting Model {model_id}...")
        assert model_id in self.get_available_project_model_ids(self.active_project_id), f"Model ID {model_id} not found in available models for project {self.active_project_id}. Please select a valid model ID."
        
        self.active_model_id = model_id

        # Set up transport for the selected model
        self.transport = ServerTransport(stream_id=self.active_project_id, client=self.client)
        AppLogger().info(f"Model {model_id} Successfully Selected")
    
    def delete_model(self, project_id: str, model_id: str):
        """Deletes a model by its id"""
        from specklepy.core.api.inputs.model_inputs import DeleteModelInput

        assert model_id in self.get_available_project_model_ids(project_id), f"Model ID {model_id} not found in available models for project {project_id}. Please select a valid model ID."
        self.client.model.delete(DeleteModelInput(id=model_id,project_id=project_id))
    
    def get_available_project_model_ids(self, project_id: str)->list[str]:
        """Returns a list of available model ids on speckle client"""
        return [m.id for m in self.client.model.get_models(project_id=project_id).items]
    

    # Version Management functions

    def commit_version(self, obj:Base,message:str|None=None)->str:
        from specklepy.core.api.inputs.version_inputs import CreateVersionInput
        obj_id = operations.send(obj, transports=[self.transport])
        version_input = CreateVersionInput(
            project_id=self.active_project_id,
            model_id=self.active_model_id,
            object_id=obj_id,
            message=message
        )
        self.active_version = self.client.version.create(version_input)
        AppLogger().info(f"Latest Version Available @ {self.active_version.preview_url}")
        return self.active_version.id

    def get_latest_version_id(self)->str:
        """Returns the latest version id for the active model"""
        versions = self.get_available_versions(self.active_project_id, self.active_model_id).items
        versions.sort(key=lambda v: v.created_at) # Sort versions by creation date
        if not versions:
            raise ValueError("No versions available for the active model")
        return versions[-1].id
    
    def get_available_versions(self, project_id: str, model_id: str):
        """Returns a list of available version ids for a given model on speckle client"""
        return self.client.version.get_versions(project_id=project_id, model_id=model_id)

    def get_available_version_ids(self, project_id: str, model_id: str)->list[str]:
        """Returns a list of available version ids for a given model on speckle client"""
        return [v.id for v in self.client.version.get_versions(project_id=project_id, model_id=model_id).items]

    def read_version_object(self, project_id: str,model_id: str, version_id: str|None)->Base:
        """Retrieves a version object by its id"""
        if version_id is None:
            version_id = self.get_latest_version_id()
            AppLogger().info(f"No version ID provided. Defaulting to latest version: {version_id}")
        assert version_id in self.get_available_version_ids(project_id, model_id), f"Version ID {version_id} not found in available versions for model {model_id}. Please select a valid version ID."
        target_version = self.client.version.get(version_id,project_id)
        object_id = target_version.referenced_object
        assert object_id is not None, f"Version with ID {version_id} does not reference an object. Cannot retrieve version object."
        transport = ServerTransport(stream_id=project_id, client=self.client)
        obj = operations.receive(obj_id=object_id, remote_transport=transport)
        return obj


    def initailise_model(self, name: str):
        """Initialises a model with the base data structure for the Bridges DA toolset"""
        # speckle_model = ModelRoot(name=name)
        # self.commit_version(obj=speckle_model, message="First Commit - Initialised Model with Base Data Structure")