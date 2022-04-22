# googlefinance-sheets
Repo to retrieve historical financial data from Google Finance using a Google Cloud Computing account connection to the Sheets app.

# SETUP

# CREATING A PYTHON PIP MODULE
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
#### Test locally
python3 -c "import gfs"

# TODO: Continue on Step 6
https://github.com/MichaelKim0407/tutorial-pip-package
