import os
from version import version
from setuptools import setup, find_packages

project_path = os.path.dirname(os.path.realpath(__file__))
requirements_file = '{}/requirements.txt'.format(project_path)

with open(requirements_file) as f:
    content = f.readlines()
install_requires = [x.strip() for x in content]

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='osm-incline',
    version=version,
    author='Sujata Misra',
    author_email='sujatam@gaussiansolutions.com',
    description='Python package to calculates the Incline of given edges ',
    long_description=long_description,
    project_urls={
        'Documentation': 'https://github.com/TaskarCenterAtUW/TDEI-python-lib-osw-inclination/blob/main/README.md',
        'GitHub': 'https://github.com/TaskarCenterAtUW/TDEI-python-lib-osw-inclination',
        'Changelog': 'https://github.com/TaskarCenterAtUW/TDEI-python-lib-osw-inclination/blob/main/CHANGELOG.md'
    },
    long_description_content_type='text/markdown',
    url='https://github.com/TaskarCenterAtUW/TDEI-python-lib-osw-inclination',
    install_requires=[
        'pyproj',
        'networkx',
        'shapely',
        'rasterio',
        'numpy',
        'scipy'
    ],
    packages=find_packages(where='src'),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
    package_dir={'': 'src'},
)