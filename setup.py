from setuptools import setup, find_packages

from __init__ import __version__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

extra_sql=[
    'sqlalchemy'
]

extra_dev=[
    *extra_sql,
    'jupyter',
    'ipykernel',
    'click',
    'black',
    'lint',
    'pytest',
    'pytest-cov',
]

setup(
    name='googlefinance_sheets',
    version=__version__,

    description='Google Finance data package using Google Sheets and Google Cloud Platform',
    long_description=long_description,
    long_description_content_type="text/markdown",

    url='https://github.com/rolozanod/googlefinance-sheets',
    author='Rodrigo Lozano',
    author_email='rolozanod@gmail.com',

    packages=find_packages(),
    # packages=['gfs'],
    install_requires=[
        'pandas',
        'google-api-core',
        'google-api-python-client',
        'google-auth',
        'google-auth-httplib2',
        'google-auth-oauthlib',
        'google-cloud-bigquery',
        'google-cloud-bigquery-storage',
        'google-cloud-core',
        'google-cloud-storage'
        ],

    extras_require={
        'sql': extra_sql,

        'dev': extra_dev,
    },

    project_urls = {
        "Bug Tracker": "https://github.com/rolozanod/googlefinance-sheets/issues"
    },
    license='MIT',
)