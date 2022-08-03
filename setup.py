# Installation script for python
from setuptools import setup, find_packages
import os
import re

PACKAGE = "covidlib"


# Returns the version
def get_version():
    """ Gets the version from the package's __init__ file
    if there is some problem, let it happily fail """
    VERSIONFILE = os.path.join("src", PACKAGE, "__init__.py")
    initfile_lines = open(VERSIONFILE, "rt").readlines()
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    for line in initfile_lines:
        mo = re.search(VSRE, line, re.M)
        if mo:
            return mo.group(1)


# load long description from README
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name=PACKAGE,
    version=get_version(),
    description="Classifier for COVID CT",
    author="The Niguarda team",
    author_email="",
    url="https://github.com/niguardateam/covid-classifier",
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={"": ["*.h5", "*.json"]},
    entry_points={'console_scripts': ['clearlung = covidlib.main:main']},
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    install_requires=[
        "fastapi>=0.79.0",
        "fpdf>=1.7.2",
        "imageio>=2.21.0",
        "keras>=2.9.0",
        "matplotlib>=3.5.1",
        "nipype>=1.8.3",
        "numpy>=1.22.0",
        "pandas>=1.3.5",
        "Pillow>=9.2.0",
        "pydicom>=2.3.0",
        "pynetdicom>=2.0.2",
        "pyradiomics>=3.0.1",
        "pytest>=7.0.1",
        "radiomics>=0.1",
        "scipy>=1.7.3",
        "setuptools>=59.4.0",
        "SimpleITK>=2.1.1.2",
        "skimage>=0.0",
        "tensorflow>=2.9.1",
        "tqdm>=4.62.3",
        "traits>=6.3.2",
    ],
    python_requires=">=3.7.0",
    long_description=long_description,
    long_description_content_type='text/markdown',
)
