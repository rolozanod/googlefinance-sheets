from setuptools import setup

from google_sheets import __version__

setup(
    name='googlefinance_sheets',
    version=__version__,

    url='https://github.com/rolozanod/googlefinance-sheets',
    author='Rodrigo Lozano',
    author_email='rolozanod@gmail.com',

    py_modules=['google_sheets','pandas','googleapiclient','google_auth_oauthlib','google','google','logging','pickle','time','datetime','math','dateutil'],
)