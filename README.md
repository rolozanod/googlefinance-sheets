# googlefinance-sheets
Repo to retrieve historical financial data from Google Finance using a Google Cloud Computing account connection to the Sheets app.

***REQUIREMENTS!*** A **Google Cloud Platform account** with a **project** enabled to **manipulate Google Sheets in Google Drive** is needed.

Developed by ![Rodrigo Lozano](https://rolozanod.github.io/)

TODO:
- Send the project to PyPi

# SETUP
### Create a Google Cloud Platform account

### Create a project

### Enable permissions

# Colaborating
I used the following tutorials to create this open source project
- https://github.com/MichaelKim0407/tutorial-pip-package
- https://opensource.com/article/21/11/packaging-python-setuptools

## CREATING A PYTHON PIP MODULE
### Create virtual environment
python3 -m venv .VENV
source .VENV/bin/activate

### Install base packages
pip install -U pip setuptools

### Install locally
-Using setuptools with setup file
pip install -e .[dev]
-Using build with toml file and setup file
python -m build
python3 -m pip install dist/googlefinance_sheets-0.0.1.tar.gz

### Test locally
python3 -c "from gfs import google_sheets; hasattr(google_sheets, 'retrieve_stocks')"