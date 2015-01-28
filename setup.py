try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Importing Infona data to CKAN',
    'author': 'ePF Foundation',
    'url': 'https://github.com/DanePubliczneGovPl/infona-to-ckan',
    'author_email': 'webmaster@epf.org.pl',
    'version': '0.1',
    'install_requires': [
        'pymongo >=2.7.2, <2.8', 
        'ckanapi'], 
    # use python setup.py develop to check if installs correctly
    # dependency_links=['http://github.com/user/repo/tarball/master#egg=package-1.0']
    'packages': ['epforgpl.infona_to_ckan'], 
    'scripts': [],
    'name': 'infona-to-ckan'
    # TODO license GPLv3+
}

setup(**config)