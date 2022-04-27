# googlefinance-sheets
Repo to retrieve historical financial data from Google Finance using a Google Cloud Computing account connection to the Sheets app.

## REQUIREMENTS!
A ***free tier*** **Google Cloud Platform account** is enough.

A **project** enabled to **manipulate Google Sheets in Google Drive** needs to be created and configured.

**BigQuery** and **Blob storage** need to be enabled. These are **free** up to XX TB of data.

# SETUP GCP
## CREATE A GOOGLE CLOUD PLATFORM ACCOUNT
If you do not have a GCP account, [create one now](https://console.cloud.google.com/freetrial/ "Google Cloud Platform link").

## CREATE A PROJECT
GCP organizes resources into projects. [Create one now](https://console.cloud.google.com/projectcreate "Project creation link in GCP").

## CREATE A SERVICE ACCOUNT
[Configure one now](https://console.cloud.google.com/apis/credentials/serviceaccountkey "Service account creation link in GCP") for the project you just created.

This serivce account will enable
- Terraform create the architecture needed for the project
- Python access the resources in GCP needed for the package to work

## DEPLOY WITH TERRAFORM
https://learn.hashicorp.com/tutorials/terraform/google-cloud-platform-build

https://cloud.google.com/docs/terraform/get-started-with-terraform

https://cloud.google.com/docs/terraform

# COLABORATING
I used the following tutorials to make this project open source:
- https://github.com/MichaelKim0407/tutorial-pip-package
- https://opensource.com/article/21/11/packaging-python-setuptools

## CREATE A PYTHON PIP MODULE
### Create virtual environment
`python3 -m venv .VENV`
`source .VENV/bin/activate`

### Install base packages
`pip install -U pip setuptools, build`

### Install locally
- Using setuptools with setup file
`pip install -e .[dev]`
- Using build with toml file and setup file
`python -m build`
`python3 -m pip install dist/googlefinance_sheets-0.0.1.tar.gz`

### Test locally
`python3 -c "from gfs import google_sheets; hasattr(google_sheets, 'retrieve_stocks')"`

# CONTRIBUTORS
[Rodrigo Lozano](https://rolozanod.github.io/ "Developer personal webpage")

TODO:
- Comment the functions
- Document the SETUP section regarding the resources needed for the project to work
- Optional: Create a Terraform plan to automate the creation of resources in GCP
- Send the project to PyPi