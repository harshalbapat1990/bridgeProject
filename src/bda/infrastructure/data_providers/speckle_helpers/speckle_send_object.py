# json_schema_dump.py
import json
from typing import Type, TypeVar

from pydantic import TypeAdapter, ValidationError, BaseModel

from specklepy.api import operations

from bda.infrastructure.data_providers.speckle_helpers.speckle_connector import BridgeDataPlatformSpeckleConnector, parse_speckle_url
from bda.contracts.speckle_contracts.bda_analytical.model_root import ModelRootCollection



example_response = {
    "id": None,
    "applicationId": "Root",
    "speckle_type": "Speckle.Core.Models.Collections.Collection:BDA_ModelRoot_Collection",
    "name": "Model Root",
    "elements": [
      {
        "id": None,
        "applicationId": "Model Config",
        "name": "BDA Analytical Model Data",
        "speckle_type": "Objects.Data.DataObject:BDA_Model_Config",
        "properties": {
          "bda_speckle_type": {
            "name": "DataObject Speckle Type",
            "isUser": True,
            "provided_value": "Objects.Data.DataObject:BDA_Model_Config",
            "description": "Entity speckle type used for creation. This is used for round tripping of objects and persistance of custom speckle object variants that are not persisted in deserialisation of objects",
            "symbol": "string",
            "provided_unit": None,
            "base_unit": None,
            "base_value": None
          },
          "Structure Type": {
            "name": "Structure Type",
            "isUser": True,
            "provided_value": "Steel Composite",
            "description": "Bridge structure type. This dictates the parameters for the analysis",
            "symbol":  None,
            "provided_unit": None,
            "base_unit": None,
            "base_value": None
          },
          "Model Unit System": {
            "name": "Model Unit System",
            "isUser": True,
            "provided_value": "Metric",
            "description": "The preferred unit system used for the model. This will impact the output unit systems of any models",
            "symbol": None,
            "provided_unit": None,
            "base_unit": None,
            "base_value": None
          },
          "Output Software": {
            "name": "Output Software",
            "isUser": True,
            "provided_value": "MIDAS Civil",
            "description": "The software used for output generation",
            "symbol": None,
            "provided_unit": None,
            "base_unit": None,
            "base_value": None
          },
          "Design Code": {
            "name": "Design Code",
            "isUser": True,
            "provided_value": "AASHTO",
            "description": "Design Code of bridge project (e.g Eurocode, AASHTO)",
            "symbol": None,
            "provided_unit": None,
            "base_unit": None,
            "base_value": None
          }
        },
        "displayValue": []
      },
      {
        "id": None,
        "applicationId": "Materials",
        "speckle_type": "Speckle.Core.Models.Collections.Collection:BDA_Material_Collection",
        "name": "Materials",
        "elements": [
          {
            "id": None,
            "applicationId": "MAT-1",
            "name": "Concrete Material Example - AASHTO",
            "speckle_type": "Objects.Data.DataObject:BDA_Concrete_Material_AASHTO",
            "properties": {
              "bda_speckle_type": {
                "name": "DataObject Speckle Type",
                "isUser": True,
                "provided_value": "Objects.Data.DataObject:BDA_Concrete_Material_AASHTO",
                "description": "Entity speckle type used for creation. This is used for round tripping of objects and persistance of custom speckle object variants that are not persisted in deserialisation of objects",
                "symbol": "string",
                "provided_unit": None,
                "base_unit": None,
                "base_value": None
              },
              "General Material Properties": {
                "name": "General Material Properties",
                "isUser": True,
                "description": "General material properties",
                "group_parameters": {
                  "Material Design Code": {
                    "name": "Material Design Code",
                    "isUser": True,
                    "provided_value": "AASHTO",
                    "description": "Associated design code of material",
                    "symbol": None,
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Material Type": {
                    "name": "Material Type",
                    "isUser": True,
                    "provided_value": "Concrete",
                    "description": "Type of material (e.g., Concrete, Steel, Timber)",
                    "symbol": "MatType",
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Isotropy": {
                    "name": "Isotropy",
                    "isUser": True,
                    "provided_value": "Isotropic",
                    "description": "Whether the material is isotropic or orthotropic",
                    "symbol": None,
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Density": {
                    "name": "Density",
                    "isUser": True,
                    "provided_value": 2400.0,
                    "description": "Mass per unit volume of a material",
                    "symbol": "\u03c1",
                    "provided_unit": "kg/m\u00b3",
                    "base_unit": "kg/m\u00b3",
                    "base_value": 2400.0
                  },
                  "Modulus of Elasticity": {
                    "name": "Modulus of Elasticity",
                    "isUser": True,
                    "provided_value": 30000000000.0,
                    "description": "Ratio of stress to strain in a material",
                    "symbol": "E",
                    "provided_unit": "Pa",
                    "base_unit": "Pa",
                    "base_value": 30000000000.0
                  },
                  "Poisson's Ratio": {
                    "name": "Poisson's Ratio",
                    "isUser": True,
                    "provided_value": 0.2,
                    "description": "Ratio of transverse strain to axial strain in a material",
                    "symbol": "\u03bd",
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Coefficient of Thermal Expansion": {
                    "name": "Coefficient of Thermal Expansion",
                    "isUser": True,
                    "provided_value": 1.0e-05,
                    "description": "Change in length per unit length per degree of temperature change",
                    "symbol": "\u03b1",
                    "provided_unit": "1/\u00b0C",
                    "base_unit": "1/\u00b0C",
                    "base_value": 1.0e-05
                  }
                }
              },
              "Concrete Material Properties": {
                "name": "Concrete Material Properties",
                "isUser": True,
                "description": "Concrete material properties",
                "group_parameters": {
                  "Expected Concrete Strength": {
                    "name": "Expected Compressive Strength",
                    "isUser": True,
                    "provided_value": 40000.0,
                    "description": "Expected compressive strength of concrete at 28 days",
                    "symbol": "fc,exp",
                    "provided_unit": "kN/m\u00b2",
                    "base_unit": "Pa",
                    "base_value": 40000000.0
                  },
                  "Specified Concrete Strength": {
                    "name": "Specified Minimum Compressive Strength",
                    "isUser": True,
                    "provided_value": 32000.0,
                    "description": "Specified minimum compressive strength of concrete",
                    "symbol": "fc,min",
                    "provided_unit": "kN/m\u00b2",
                    "base_unit": "Pa",
                    "base_value": 32000000.0
                  }
                }
              }
            },
            "displayValue": []
          },
          {
            "id": None,
            "applicationId": "MAT-2",
            "name": "General Material Example - AASHTO",
            "speckle_type": "Objects.Data.DataObject:BDA_General_Material_AASHTO",
            "properties": {
              "bda_speckle_type": {
                "name": "DataObject Speckle Type",
                "isUser": True,
                "provided_value": "Objects.Data.DataObject:BDA_General_Material_AASHTO",
                "description": "Entity speckle type used for creation. This is used for round tripping of objects and persistance of custom speckle object variants that are not persisted in deserialisation of objects",
                "symbol": "string",
                "provided_unit": None,
                "base_unit": None,
                "base_value": None
              },
              "General Material Properties": {
                "name": "General Material Properties",
                "isUser": True,
                "description": "General material properties",
                "group_parameters": {
                  "Material Type": {
                    "name": "Material Type",
                    "isUser": True,
                    "provided_value": "Concrete",
                    "description": "Type of material (e.g., Concrete, Steel, Timber)",
                    "symbol": "MatType",
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Material Design Code": {
                    "name": "Material Design Code",
                    "isUser": True,
                    "provided_value": "AASHTO",
                    "description": "Associated design code of material",
                    "symbol": None,
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Isotropy": {
                    "name": "Isotropy",
                    "isUser": True,
                    "provided_value": "Isotropic",
                    "description": "Whether the material is isotropic or orthotropic",
                    "symbol": None,
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Density": {
                    "name": "Density",
                    "isUser": True,
                    "provided_value": 2400.0,
                    "description": "Mass per unit volume of a material",
                    "symbol": "\u03c1",
                    "provided_unit": "kg/m\u00b3",
                    "base_unit": "kg/m\u00b3",
                    "base_value": 2400.0
                  },
                  "Modulus of Elasticity": {
                    "name": "Modulus of Elasticity",
                    "isUser": True,
                    "provided_value": 30000000000.0,
                    "description": "Ratio of stress to strain in a material",
                    "symbol": "E",
                    "provided_unit": "Pa",
                    "base_unit": "Pa",
                    "base_value": 30000000000.0
                  },
                  "Poisson's Ratio": {
                    "name": "Poisson's Ratio",
                    "isUser": True,
                    "provided_value": 0.2,
                    "description": "Ratio of transverse strain to axial strain in a material",
                    "symbol": "\u03bd",
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Coefficient of Thermal Expansion": {
                    "name": "Coefficient of Thermal Expansion",
                    "isUser": True,
                    "provided_value": 1.0e-05,
                    "description": "Change in length per unit length per degree of temperature change",
                    "symbol": "\u03b1",
                    "provided_unit": "1/\u00b0C",
                    "base_unit": "1/\u00b0C",
                    "base_value": 1.0e-05
                  }
                }
              }
            },
            "displayValue": []
          },
          {
            "id": None,
            "applicationId": "MAT-3",
            "name": "Reinforcement Material Example - AASHTO",
            "speckle_type": "Objects.Data.DataObject:BDA_Reinforcement_Material_AASHTO",
            "properties": {
              "bda_speckle_type": {
                "name": "DataObject Speckle Type",
                "isUser": True,
                "provided_value": "Objects.Data.DataObject:BDA_Reinforcement_Material_AASHTO",
                "description": "Entity speckle type used for creation. This is used for round tripping of objects and persistance of custom speckle object variants that are not persisted in deserialisation of objects",
                "symbol": "string",
                "provided_unit": None,
                "base_unit": None,
                "base_value": None
              },
              "General Material Properties": {
                "name": "General Material Properties",
                "isUser": True,
                "description": "General material properties",
                "group_parameters": {
                  "Material Type": {
                    "name": "Material Type",
                    "isUser": True,
                    "provided_value": "Steel Reinforcement",
                    "description": "Type of material (e.g., Concrete, Steel, Timber)",
                    "symbol": "MatType",
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Material Design Code": {
                    "name": "Material Design Code",
                    "isUser": True,
                    "provided_value": "AASHTO",
                    "description": "Associated design code of material",
                    "symbol": None,
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Isotropy": {
                    "name": "Isotropy",
                    "isUser": True,
                    "provided_value": "Isotropic",
                    "description": "Whether the material is isotropic or orthotropic",
                    "symbol": None,
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Density": {
                    "name": "Density",
                    "isUser": True,
                    "provided_value": 7850.0,
                    "description": "Mass per unit volume of a material",
                    "symbol": "\u03c1",
                    "provided_unit": "kg/m\u00b3",
                    "base_unit": "kg/m\u00b3",
                    "base_value": 7850.0
                  },
                  "Modulus of Elasticity": {
                    "name": "Modulus of Elasticity",
                    "isUser": True,
                    "provided_value": 200000000000.0,
                    "description": "Ratio of stress to strain in a material",
                    "symbol": "E",
                    "provided_unit": "Pa",
                    "base_unit": "Pa",
                    "base_value": 200000000000.0
                  },
                  "Poisson's Ratio": {
                    "name": "Poisson's Ratio",
                    "isUser": True,
                    "provided_value": 0.3,
                    "description": "Ratio of transverse strain to axial strain in a material",
                    "symbol": "\u03bd",
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Coefficient of Thermal Expansion": {
                    "name": "Coefficient of Thermal Expansion",
                    "isUser": True,
                    "provided_value": 1.2e-05,
                    "description": "Change in length per unit length per degree of temperature change",
                    "symbol": "\u03b1",
                    "provided_unit": "1/\u00b0C",
                    "base_unit": "1/\u00b0C",
                    "base_value": 1.2e-05
                  }
                }
              },
              "Steel Material Properties": {
                "name": "Steel Material Properties",
                "isUser": True,
                "description": "Steel material properties",
                "group_parameters": {
                  "Expected Steel Yield Strength": {
                    "name": "Expected Steel Yield Strength",
                    "isUser": True,
                    "provided_value": 500000.0,
                    "description": "Expected yield strength of steel",
                    "symbol": "fy,exp",
                    "provided_unit": "kN/m\u00b2",
                    "base_unit": "Pa",
                    "base_value": 500000000.0
                  },
                  "Minimum Steel Yield Strength": {
                    "name": "Specified Minimum Steel Yield Strength",
                    "isUser": True,
                    "provided_value": 420000.0,
                    "description": "Specified Minimum yield strength of steel",
                    "symbol": "fy,min",
                    "provided_unit": "kN/m\u00b2",
                    "base_unit": "Pa",
                    "base_value": 420000000.0
                  },
                  "Expected Steel Tensile Strength": {
                    "name": "Expected Steel Tensile Strength",
                    "isUser": True,
                    "provided_value": 650000.0,
                    "description": "Expected tensile strength of steel",
                    "symbol": "fu,exp",
                    "provided_unit": "kN/m\u00b2",
                    "base_unit": "Pa",
                    "base_value": 650000000.0
                  },
                  "Minimum Steel Tensile Strength": {
                    "name": "Specified Minimum Steel Tensile Strength",
                    "isUser": True,
                    "provided_value": 550000.0,
                    "description": "Specified minimum tensile strength of steel",
                    "symbol": "fu,min",
                    "provided_unit": "kN/m\u00b2",
                    "base_unit": "Pa",
                    "base_value": 550000000.0
                  }
                }
              }
            },
            "displayValue": []
          },
          {
            "id": None,
            "applicationId": "MAT-4",
            "name": "Steel Material Example - AASHTO",
            "speckle_type": "Objects.Data.DataObject:BDA_Steel_Material_AASHTO",
            "properties": {
              "bda_speckle_type": {
                "name": "DataObject Speckle Type",
                "isUser": True,
                "provided_value": "Objects.Data.DataObject:BDA_Steel_Material_AASHTO",
                "description": "Entity speckle type used for creation. This is used for round tripping of objects and persistance of custom speckle object variants that are not persisted in deserialisation of objects",
                "symbol": "string",
                "provided_unit": None,
                "base_unit": None,
                "base_value": None
              },
              "General Material Properties": {
                "name": "General Material Properties",
                "isUser": True,
                "description": "General material properties",
                "group_parameters": {
                  "Material Type": {
                    "name": "Material Type",
                    "isUser": True,
                    "provided_value": "Steel",
                    "description": "Type of material (e.g., Concrete, Steel, Timber)",
                    "symbol": "MatType",
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Material Design Code": {
                    "name": "Material Design Code",
                    "isUser": True,
                    "provided_value": "AASHTO",
                    "description": "Associated design code of material",
                    "symbol": None,
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Isotropy": {
                    "name": "Isotropy",
                    "isUser": True,
                    "provided_value": "Isotropic",
                    "description": "Whether the material is isotropic or orthotropic",
                    "symbol": None,
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Density": {
                    "name": "Density",
                    "isUser": True,
                    "provided_value": 7850.0,
                    "description": "Mass per unit volume of a material",
                    "symbol": "\u03c1",
                    "provided_unit": "kg/m\u00b3",
                    "base_unit": "kg/m\u00b3",
                    "base_value": 7850.0
                  },
                  "Modulus of Elasticity": {
                    "name": "Modulus of Elasticity",
                    "isUser": True,
                    "provided_value": 210000000000.0,
                    "description": "Ratio of stress to strain in a material",
                    "symbol": "E",
                    "provided_unit": "Pa",
                    "base_unit": "Pa",
                    "base_value": 210000000000.0
                  },
                  "Poisson's Ratio": {
                    "name": "Poisson's Ratio",
                    "isUser": True,
                    "provided_value": 0.3,
                    "description": "Ratio of transverse strain to axial strain in a material",
                    "symbol": "\u03bd",
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Coefficient of Thermal Expansion": {
                    "name": "Coefficient of Thermal Expansion",
                    "isUser": True,
                    "provided_value": 1.2e-05,
                    "description": "Change in length per unit length per degree of temperature change",
                    "symbol": "\u03b1",
                    "provided_unit": "1/\u00b0C",
                    "base_unit": "1/\u00b0C",
                    "base_value": 1.2e-05
                  }
                }
              },
              "Steel Material Properties": {
                "name": "Steel Material Properties",
                "isUser": True,
                "description": "Steel material properties",
                "group_parameters": {
                  "Expected Steel Yield Strength": {
                    "name": "Expected Steel Yield Strength",
                    "isUser": True,
                    "provided_value": 345000.0,
                    "description": "Expected yield strength of steel",
                    "symbol": "fy,exp",
                    "provided_unit": "kN/m\u00b2",
                    "base_unit": "Pa",
                    "base_value": 345000000.0
                  },
                  "Minimum Steel Yield Strength": {
                    "name": "Specified Minimum Steel Yield Strength",
                    "isUser": True,
                    "provided_value": 250000.0,
                    "description": "Specified Minimum yield strength of steel",
                    "symbol": "fy,min",
                    "provided_unit": "kN/m\u00b2",
                    "base_unit": "Pa",
                    "base_value": 250000000.0
                  },
                  "Expected Steel Tensile Strength": {
                    "name": "Expected Steel Tensile Strength",
                    "isUser": True,
                    "provided_value": 460000.0,
                    "description": "Expected tensile strength of steel",
                    "symbol": "fu,exp",
                    "provided_unit": "kN/m\u00b2",
                    "base_unit": "Pa",
                    "base_value": 460000000.0
                  },
                  "Minimum Steel Tensile Strength": {
                    "name": "Specified Minimum Steel Tensile Strength",
                    "isUser": True,
                    "provided_value": 400000.0,
                    "description": "Specified minimum tensile strength of steel",
                    "symbol": "fu,min",
                    "provided_unit": "kN/m\u00b2",
                    "base_unit": "Pa",
                    "base_value": 400000000.0
                  }
                }
              }
            },
            "displayValue": []
          },
          {
            "id": None,
            "applicationId": "MAT-5",
            "name": "Tendon Material Example - AASHTO",
            "speckle_type": "Objects.Data.DataObject:BDA_Tendon_Material_AASHTO",
            "properties": {
              "bda_speckle_type": {
                "name": "DataObject Speckle Type",
                "isUser": True,
                "provided_value": "Objects.Data.DataObject:BDA_Tendon_Material_AASHTO",
                "description": "Entity speckle type used for creation. This is used for round tripping of objects and persistance of custom speckle object variants that are not persisted in deserialisation of objects",
                "symbol": "string",
                "provided_unit": None,
                "base_unit": None,
                "base_value": None
              },
              "General Material Properties": {
                "name": "General Material Properties",
                "isUser": True,
                "description": "General material properties",
                "group_parameters": {
                  "Material Type": {
                    "name": "Material Type",
                    "isUser": True,
                    "provided_value": "Tendon",
                    "description": "Type of material (e.g., Concrete, Steel, Timber)",
                    "symbol": "MatType",
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Material Design Code": {
                    "name": "Material Design Code",
                    "isUser": True,
                    "provided_value": "AASHTO",
                    "description": "Associated design code of material",
                    "symbol": None,
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Isotropy": {
                    "name": "Isotropy",
                    "isUser": True,
                    "provided_value": "Isotropic",
                    "description": "Whether the material is isotropic or orthotropic",
                    "symbol": None,
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Density": {
                    "name": "Density",
                    "isUser": True,
                    "provided_value": 7850.0,
                    "description": "Mass per unit volume of a material",
                    "symbol": "\u03c1",
                    "provided_unit": "kg/m\u00b3",
                    "base_unit": "kg/m\u00b3",
                    "base_value": 7850.0
                  },
                  "Modulus of Elasticity": {
                    "name": "Modulus of Elasticity",
                    "isUser": True,
                    "provided_value": 195000000000.0,
                    "description": "Ratio of stress to strain in a material",
                    "symbol": "E",
                    "provided_unit": "Pa",
                    "base_unit": "Pa",
                    "base_value": 195000000000.0
                  },
                  "Poisson's Ratio": {
                    "name": "Poisson's Ratio",
                    "isUser": True,
                    "provided_value": 0.3,
                    "description": "Ratio of transverse strain to axial strain in a material",
                    "symbol": "\u03bd",
                    "provided_unit": None,
                    "base_unit": None,
                    "base_value": None
                  },
                  "Coefficient of Thermal Expansion": {
                    "name": "Coefficient of Thermal Expansion",
                    "isUser": True,
                    "provided_value": 1.2e-05,
                    "description": "Change in length per unit length per degree of temperature change",
                    "symbol": "\u03b1",
                    "provided_unit": "1/\u00b0C",
                    "base_unit": "1/\u00b0C",
                    "base_value": 1.2e-05
                  }
                }
              },
              "Tendon Material Properties": {
                "name": "Tendon Material Properties",
                "isUser": True,
                "description": "Tendon material properties",
                "group_parameters": {
                  "Prestressing/Post-Tensioning Steel Yield Strength": {
                    "name": "Prestressing/Post-Tensioning Steel Yield Strength",
                    "isUser": True,
                    "provided_value": 1860000.0,
                    "description": "Yield strength of prestressing or post-tensioning steel",
                    "symbol": "fy,min",
                    "provided_unit": "kN/m\u00b2",
                    "base_unit": "Pa",
                    "base_value": 1860000000.0
                  },
                  "Prestressing/Post-Tensioning Steel Specified Minimum Tensile Strength": {
                    "name": "Prestressing/Post-Tensioning Steel Specified Minimum Tensile Strength",
                    "isUser": True,
                    "provided_value": 2000000.0,
                    "description": "Minimum tensile strength of tendon",
                    "symbol": "fu,min",
                    "provided_unit": "kN/m\u00b2",
                    "base_unit": "Pa",
                    "base_value": 2000000000.0
                  }
                }
              }
            },
            "displayValue": []
          }
        ]
      }
    ]
  }






from typing import Type, TypeVar
from pydantic import BaseModel, TypeAdapter, ValidationError

T = TypeVar("T", bound=BaseModel)


def validate_and_parse_model(
    json_data: dict | str,
    model: Type[T],
) -> T:
    adapter = TypeAdapter(model)

    if isinstance(json_data, str):
        return adapter.validate_json(json_data)

    return adapter.validate_python(json_data)


def ingest_ui_json_and_commit(
    json_data: dict,
    pydantic_model: Type[BaseModel],
    speckle_url: str,
    commit_message: str = "Version Created from Pydantic Model"
) -> str:
    """
    End-to-end ingestion for UI-provided JSON.
    """

    # 1️⃣ Validation
    try:
        validated_model = validate_and_parse_model(json_data, pydantic_model)
        print(f"✅ Successfully validated JSON against {pydantic_model.__name__}")
    except ValidationError as e:
        raise ValueError(
            {
                "message": "JSON failed validation",
                "errors": e.errors(),
            }
        ) from e

    # 2️⃣ Freeze
    validated_model = validated_model.model_copy(deep=True)

    # ✅ 3️⃣ IMPORTANT FIX — SERIALIZE TO JSON STRING
    payload_json = validated_model.model_dump_json(
        by_alias=True,
        exclude_none=True,
        exclude_defaults=False,
    )

    # ✅ Speckle expects JSON string here
    speckle_object = operations.deserialize(payload_json)

    # 4️⃣ Commit
    connector = BridgeDataPlatformSpeckleConnector(
        speckle_url_components=parse_speckle_url(speckle_url)
    )

    connector.select_project(project_id=connector.speckle_url.project_id)
    connector.select_model(model_id=connector.speckle_url.model_id)

    version_id = connector.commit_version(
        obj=speckle_object,
        message=commit_message,
    )

    return version_id



# --------------------------------------------------
# Example Execution
# --------------------------------------------------

# if __name__ == "__main__":
#     model_url = 

#     try:
#         version_id = ingest_ui_json_and_commit(
#             example_response,
#             project_id=PROJECT_ID,
#             model_id=MODEL_ID,
#         )
#         print(f"✅ Successfully committed version {version_id}")

#     except ValueError as exc:
#         print("❌ Ingestion failed")
#         print(json.dumps(exc.args[0], indent=2))