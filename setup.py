from setuptools import setup

from my_pip_package import __version__

setup(
    name='googlefinance-sheets',
    version=__version__,

    url='https://github.com/rolozanod/googlefinance-sheets',
    author='Rodrigo Lozano',
    author_email='rolozanod@gmail.com',

    py_modules=['google_sheets'],
)