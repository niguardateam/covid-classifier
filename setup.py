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
    entry_points={'console_scripts': ['covid-classifier = covidlib.main:main']},
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    install_requires=[
        "dicom2nifti",
        "fpdf",
        "keras",
        "matplotlib",
        "nibabel",
        "numpy",
        "pandas",
        "Pillow",
        "pydicom",
        "pynetdicom",
        "pynrrd",
        "pyradiomics",
        "scikit-image",
        "scikit-learn",
        "scipy",
        "SimpleITK",
        "tensorflow",
        "tqdm",
    ],
    python_requires=">=3.7.0",
    long_description=long_description,
    long_description_content_type='text/markdown',
)
