"""Test all functions.
We still have to figure out whether to upload a sample image for testing purposes.
"""

import pytest
from covidlib.niftiz import Niftizator

def test_one():
    assert True


#Strategy --> load .nii (completely anonymized) and test the pipeline (without report generation)
# maybe just the rpesence of the report file and the dicom file and read back some dicom fields
#then remove everythin we've gernated