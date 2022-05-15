# googlefinance-sheets
Repo to retrieve historical financial data from Google Finance using a Google Cloud Platform account connection to the Sheets app.

## USAGE
**The project needs to be configured on GCP to work, automated configuration is provided in Terraform scripts**

`from gfs import google_finance`

`google_finance.retrieve_stocks(*args)`

## REQUIREMENTS!
- A ***free tier*** **Google Cloud Platform account** is enough.

- A **project** enabled to **manipulate Google Sheets in Google Drive** needs to be created and configured.

- **BigQuery** and **Blob storage** need to be enabled. These are **free** up to XX TB of data.

- [Terraform on local](https://learn.hashicorp.com/tutorials/terraform/install-cli) ***OR*** run configuration files from the GCP console where Terraform is already available.

# SETUP GCP
## CREATE A GOOGLE CLOUD PLATFORM ACCOUNT
If you do not have a GCP account, [create one now](https://console.cloud.google.com/freetrial/ "Google Cloud Platform link").

## CREATE A PROJECT
GCP organizes resources into projects. [Create one now](https://console.cloud.google.com/projectcreate "Project creation link in GCP").

## CREATE A SERVICE ACCOUNT FOR TERRAFORM
This serivce account will enable Terraform create the architecture needed for the project

[Configure one now](https://console.cloud.google.com/apis/credentials/serviceaccountkey "Service account creation link in GCP") for the project you just created.

1. Under `+ Create credentials`, create a service account with the following roles:
    - "Editor": Terraform needs this role to create a bucket and an object to store the financial data
    - "BigQuery Job User": the package needs this role to process the data stored in the bucket
    - "Storage Object Viewer": the package needs this role to read data from buckets and bulk insert it into BigQuery
    - "Storage Object Creator": the package needs this role to save the stocks data
1. Skip user assignment
1. Create a new key
    - Under the service account key got to the "Keys" tab and select "Create new key" with JSON "Key Type".
1. Download the service account key.

Read more about service account keys in [Google's documentation](https://cloud.google.com/iam/docs/creating-managing-service-account-keys).

## CREATE AN OAUTH CLIENT ID FOR GFS (GOOGLE FINANCE SHEETS)
This client will enable Python access the Sheets, Drive and BigQuery resources in GCP needed for the package to work

[Configure one now](https://console.cloud.google.com/apis/credentials/oauthclient "OAuth client ID creation link in GCP") for the project you just created.

Before you can create your OAuth client credentials, you must have set up your OAuth consent screen. For more information, see [Setting up your OAuth Consent Screen](https://support.google.com/cloud/answer/10311615 "GCP Console Help: Setting up your OAuth consent screen").
1. Under `+ Create credentials`, create an OAuth Client ID
1. Configure consent screen for "External" users.
    - Fill the OAuth consent screen form
    - Skip the "Scopes" tab.
    - Add your gmail account under "Test Users"
    - "Save & continue" on the "Summary" tab.
1. Go back to "APIs & Services/Credentials".

1. Under `+ Create credentials`, create an OAuth Client ID with a Web application "Application Type".
    - Add `http://localhost:8080/` to the **Authorized redirect URIs**
1. Download the JSON file.

Read more about service account keys in [Google's documentation](https://cloud.google.com/iam/docs/creating-managing-service-account-keys).

## ENABLE GCP APIs FOR TERRAFORM
Go to [`APIs and Services`-`Enabled APIs and services`](https://console.cloud.google.com/apis/dashboard "APIs and services managements")

Under `+ ENABLE APIS AND SERVICES`, enable [**Cloud Resource Manager API**](https://console.cloud.google.com/apis/library/cloudresourcemanager.googleapis.com).

## LAST STEP! DEPLOY WITH TERRAFORM

[Install terraform on local](https://learn.hashicorp.com/tutorials/terraform/install-cli) or run it from the GCP console where it is already available.

Run the terraform_setup script in the project.

    google_finance.terraform_setup(
        project_id=<project_id>,
        project_env=<environment>,
        gcp_location=<gcp_location>, select a location from https://cloud.google.com/storage/docs/locations
        gcp_zone=<gcp_zone>, select a location from https://cloud.google.com/storage/docs/locations
        gcp_bucket_name=<gcp_bucket_name>,
        service_account_json=<path/to/service_account.json>
    )

* Type `yes` when prompted to accept the configuration

# COLABORATING
I used the following tutorials to make this project open source:
- https://packaging.python.org/en/latest/tutorials/packaging-projects/
- https://github.com/MichaelKim0407/tutorial-pip-package
- https://opensource.com/article/21/11/packaging-python-setuptools

#### Useful Terraform doc
https://learn.hashicorp.com/tutorials/terraform/google-cloud-platform-build

https://cloud.google.com/docs/terraform/get-started-with-terraform

https://cloud.google.com/docs/terraform

## CREATE A PYTHON PIP MODULE
### Create virtual environment
`python3 -m venv .VENV`
`source .VENV/bin/activate`

### Install base packages
`pip install -U pip setuptools, build`

### Install locally
- Using build with toml file and setup file (preferred)
`python3 -m build`
`python3 -m pip install dist/googlefinance_sheets-<version>.tar.gz`
* The `version` is defined in `__init__.py`
- Using setuptools with setup file
`pip install -e .[dev]`

### Test locally
`python3 -c "from gfs import google_finance; hasattr(google_finance, 'retrieve_stocks')"`


### Send to pypi or testpypi

Follow instrucitons on [packaging.python](https://packaging.python.org/en/latest/tutorials/packaging-projects/ "Packaging instructions")

**Install twine to send to pypi**
- `python3 -m pip install --upgrade twine`

**TEST PYPI**

- Send to test pypi
    - `python3 -m twine upload --repository testpypi dist/*`

- Install from test pypi
    - `python3 -m pip install -i https://test.pypi.org/simple/ googlefinance-sheets==<version>`

# CONTRIBUTORS
[Rodrigo Lozano](https://rolozanod.github.io/ "Developer personal webpage")

TODO:
- Comment the functions
- Send terraform command directly to GCP to avoid installing Terraform on local.