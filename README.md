# Bridge Automation & Optimisation

## Description
Bridge Automation & Optimisation modernises traditional bridge design workflows to deliver more sustainable and cost-effective infrastructure outcomes. The initiative integrates structural analysis, engineering design, and BIM-oriented data exchange into a single digital process that improves data consistency and tool interoperability.

The platform follows a two-stage analytical workflow: processing (model generation and setup) and post-processing (engineering validation and interpretation). Its modular, data-driven architecture enables rapid analytical model generation, region-specific customisation, and integration with Jacobs structural analysis platforms while reducing manual modelling effort and avoidable errors.

The core objective is to streamline creation of analytical bridge models through parametric design principles, scripting environments (Python and Grasshopper), and interoperable data layers. The workflow also supports generation of formal input calculation reports to improve compliance checks, metadata traceability, and assumption transparency.

### Metadata
<!--
Required fields. Bolding the key is optional but only use a colon `:` as the delimiter for now. Links can be the simple or Markdown format.  

- **Is Production** : true | false - is the app in production or not
- **Production Branch** : production - what is the production branch
- **Project Management** : URL to the DevOps Board site or GitHub Projects
- **Website** : Primary website if any
- **Availability** : A float percentage with or without the % sign on the expected uptime of your app in production. Consult an Uptime Calculator.
-->

- **Is Production** : false
- **Production Branch** : main
- **Development Branch** : dev
- **Project Management** : 
  - Preprocessing - https://dev.azure.com/Focus2023/Bridge%20Automation/_workitems/edit/26950
  - Postprocessing - https://dev.azure.com/Focus2023/Bridge%20Automation/_workitems/edit/26951
- **Website** : -
- **Availability** : <10%

### Other Repos
<!-- If you have more than ONE repo (not recommended) designate one as the primary (this one) and list the other repo URLs in this section
the repo name is after the last / in the address
-->
* ---

### Use Case
Bridge projects typically require repeated analytical model creation across multiple typologies, regions, software ecosystems, and code requirements. In traditional workflows, this is time-consuming, error-prone, and difficult to audit.

This repository addresses that by implementing a modular analytical processor that can activate specific modules based on bridge typology, assessment type (new design, load rating, assessment), and regional requirements. The result is faster model setup, better cross-discipline collaboration, and stronger traceability for compliance and engineering governance.

### Size

Describe the current usage size in terms of total users, daily users and simultaneous users.

Describe your projected or ideal growth of the app usage.

## Installation

The project uses `pyproject.toml` as the source of truth for dependencies.

### 1) Create virtual environment

```powershell
python -m venv .venv
```

### 2) Activate virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3) Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### 4) Install project (editable mode)

```powershell
pip install -e .
```

### 5) Install test dependencies

```powershell
pip install -e .[test]
```

### 6) Run tests

```powershell
python -m pytest tests/unit -q
```

## Running the application

The application entry point is `bda.__main__.main()`.

Configuration can be supplied in three layers, in this priority order:

1. explicit parameters passed directly to `main()` from Python,
2. JSON stored in the `BDA_CONFIG` environment variable,
3. built-in defaults from `src/bda/__main__.py`.

If you just want to start the application with defaults:

```powershell
python -m bda
```

If the project was installed in editable mode and the console script is available:

```powershell
bda
```

### Running with `BDA_CONFIG` from PowerShell

`BDA_CONFIG` must contain a JSON object. Example payload:

```json
{
  "config_json_path": "C:/Path/To/appsettings.json",
  "use_file_data_provider": true,
  "data_path": "C:/Users/YourName/input-json-data",
  "speckle_model_url": "https://ldd-emea.jacobs.com/projects/your-project-id",
  "speckle_authentication_token": "YOUR_SPECKLE_TOKEN"
}
```

Supported keys:

- `config_json_path`
- `use_file_data_provider`
- `data_path`
- `speckle_model_url`
- `speckle_authentication_token`

### PowerShell example 1 — inline JSON, `python -m bda`

```powershell
$env:BDA_CONFIG = '{"config_json_path":"C:/Path/To/appsettings.json","use_file_data_provider":true,"data_path":"C:/Users/TS040198/GitHub/DesignAutomation.BridgeAutomationAndOptimisation/tests/unit/fixtures","speckle_model_url":"https://ldd-emea.jacobs.com/projects/example","speckle_authentication_token":"TOKEN"}'
python -m bda
```

### PowerShell example 2 — inline JSON, console script `bda`

```powershell
$env:BDA_CONFIG = '{"config_json_path":"C:/Path/To/appsettings.json","use_file_data_provider":true,"data_path":"C:/Users/TS040198/GitHub/DesignAutomation.BridgeAutomationAndOptimisation/tests/unit/fixtures","speckle_model_url":"https://ldd-emea.jacobs.com/projects/example","speckle_authentication_token":"TOKEN"}'
bda
```

### PowerShell example 3 — omit `data_path` and use the internal default

If `use_file_data_provider` is set to `false`, data_path is not required.

```powershell
$env:BDA_CONFIG = '{"config_json_path":"C:/Path/To/appsettings.json","use_file_data_provider":false,"data_path":"","speckle_model_url":"https://ldd-emea.jacobs.com/projects/example","speckle_authentication_token":"TOKEN"}'
python -m bda
```

### PowerShell example 4 — build JSON more safely from a hashtable

This is often easier to maintain than manually escaping a JSON string.

```powershell
$config = @{
    config_json_path = "C:/Path/To/appsettings.json"
    use_file_data_provider = true
    data_path = "C:/Users/TS040198/GitHub/DesignAutomation.BridgeAutomationAndOptimisation/tests/unit/fixtures"
    speckle_model_url = "https://ldd-emea.jacobs.com/projects/example"
    speckle_authentication_token = "TOKEN"
} | ConvertTo-Json -Compress

$env:BDA_CONFIG = $config
python -m bda
```

### PowerShell example 5 — multiline JSON with here-string

Useful when you want a more readable command in scripts.

```powershell
$env:BDA_CONFIG = @'
{
  "config_json_path": "C:/Path/To/appsettings.json",
  "use_file_data_provider": false,
  "speckle_model_url": "https://ldd-emea.jacobs.com/projects/example",
  "speckle_authentication_token": "TOKEN"
}
'@

python -m bda
```

### Removing `BDA_CONFIG` in the current PowerShell session

```powershell
Remove-Item Env:BDA_CONFIG
```

or:

```powershell
$env:BDA_CONFIG = ""
```

### Accepted values

#### `use_file_data_provider`

Accepted examples:

- TRUE
- FALSE
- true
- false

#### Notes

- data_path is used only when use_file_data_provider is set to TRUE. 
- speckle_model_url and speckle_authentication_token are required when using the Speckle data provider (use_file_data_provider = FALSE). 
- config_json_path should always point to a valid appsettings.json file.

### Invalid configuration handling

If `BDA_CONFIG` contains invalid JSON, for example:

```powershell
$env:BDA_CONFIG = '{bad json}'
python -m bda
```

the application will log an error and exit with code `1`.

If a parameter value is invalid, for example:

```powershell
$env:BDA_CONFIG = '{"config_json_path":"","use_file_data_provider":true,"data_path":"","speckle_model_url":"https://ldd-emea.jacobs.com/projects/example","speckle_authentication_token":"TOKEN"}'
python -m bda
```

the application will also log an error and exit with code `1`.

### Calling `main()` directly from another Python process

This can be useful for debugging or integration tests:

```powershell
python -c "from bda.__main__ import main; main({"config_json_path":"C:/Path/To/appsettings.json","use_file_data_provider":true,"data_path":"C:/Users/TS040198/GitHub/DesignAutomation.BridgeAutomationAndOptimisation/tests/unit/fixtures","speckle_model_url":"https://ldd-emea.jacobs.com/projects/example","speckle_authentication_token":"TOKEN"}')"
```

In that scenario, explicit parameters passed to `main()` override values coming from `BDA_CONFIG`.

## Team

| eMail                           | Role                           |
|---------------------------------|--------------------------------|
| Tomasz.Slusarczyk@jacobs.com    | Lead Developer - preprocessing |
| Grzegorz.Czerpak@jacobs.com     | Developer - preprocessing      |
| Stanislaw.Bolanowski@jacobs.com | Developer - postprocessing     |
| Matthew.Jones1@jacobs.com       | Developer - speckle            |
| Kiran.Walase@jacobs.com         | Tester                         |

## Contributing
All changes to the code base must be made in feature branches and reviewed by another team member.

The reviewer should merge the feature branch into main - you should never merge your own branch.

Never make commits directly to main or dev.

The process for making changes to the code base is as follows:

* Get a ticket in Azure DevOps e.g. `900 Make changes to something`
* Create the matching branch locally (make sure to always branch off *dev*): `git checkout -b 900-make-changes-to-something`. Note branch name should be lowercase with hyphens instead of spaces.
* Make the required changes to the codebase
* Commit the changes to Git locally: `git commit -a -m "The commit message"`
* Push the changes: `git push -u origin 900-make-changes-to-something`. For subsequent pushes you only need git push.
* In GitHub go to Pull requests and click on the New pull request button
* Set *compare* to your new branch and confirm that base is set to *dev*
* Click the *Create pull request* button
* Once the pull request is created, ask someone else to review it. They should check out your branch locally and confirm that it works as expected.
* The reviewer should leave any relevant comments on the pull request page in GitHub
* If changes are required to address any comments, make the changes locally and then push your branch to GitHub again. The pull request will update automatically.
Once the reviewer is happy with the feature branch they should merge it into the *dev* branch by clicking the green *Squash and merge* button on the pull request page.

## Documents
<!--
Use Markdown Links to supporting documentation
* [PingOne API](https://apidocs.pingidentity.com/pingone/main/v1/api/)
-->

* -


## Project Structure

This sections describes the structure of the code project files and solutions.

The root package namespace is `bda`.

Key modules:

- `bda.application`: interfaces, mapping.
- `bda.bootstrap`: orchestration/module coordination layer,
- `bda.config`: configuration management,
- `bda.contracts`: contract/data models used as input/output boundaries.
- `bda.domain`: core domain entities, enums, and unit/quantity logic.
- `bda.infrastructure`: adapters for exporters, schemas, and utilities (logger).
- `bda.modules_post`: post-processing importers, validators, result models, and checks.
- `bda.modules_pre`: pre-processing modules logic, bridge type profiles.
- `bda.__main__`: entry point, configuration parsing, and application startup.

## Tech Stack

Describe the primary tech stack being used:

* Python >= 3.14
* Pytest
* Speckle (integration workflows)
* External structural platforms: MIDAS Civil, CSI Bridge

The architecture is intentionally modular to support phased rollout, region-specific logic, and future extension without compromising core system integrity.
