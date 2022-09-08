"""Helper for i/o with DICOM files."""

import glob
import pydicom

def dcmtagreader(folder_name: str):
    """CT image dicom reader.
    :param folder_name: path of dicom folder
    """
    files_with_dcm = glob.glob(f"{folder_name}/*")
    for inputfile in files_with_dcm:
        data = pydicom.dcmread(inputfile, force=True)

    if data:
        return data
    else:
        raise UnboundLocalError

def change_keys(dic: dict, suffix: str) -> dict:
    """Add suffix to all dictionary keys"""
    return {str(key) + '_' + suffix : val for key, val in dic.items()}

class EmptyMaskError(Exception):
    """Raised when the mask produces essentially a empty output"""
    def __init__(self, nvox) -> None:
        super().__init__()
        self.nvox = nvox