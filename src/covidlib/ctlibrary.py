"""Helper for i/o with DICOM files."""

import glob
import pydicom
import numpy as np

def dcmtagreader(folder_name: str):
    """CT image dicom reader.
    :param folder_name: path of dicom folder
    """
    files_with_dcm = glob.glob(f"{folder_name}/*")
    for inputfile in files_with_dcm:
        data = pydicom.dcmread(inputfile, force=True)
    if not data:
        raise UnboundLocalError
    else:
        return data

def dcmtagreaderCTDI(folder_name: str):
    """CT image dicom reader.
    :param folder_name: path of dicom folder
    """
    files_with_dcm = glob.glob(f"{folder_name}/*")
    ctdi_vec = []
    for inputfile in files_with_dcm:
        data = pydicom.dcmread(inputfile, force=True)
        try:
            ctdi = float(data[0x0018, 0x9345].value)
        except:
            ctdi = 'NaN'       
        ctdi_vec.append(ctdi)
    if not data:
        raise UnboundLocalError
    else:
        for i in range(len(ctdi_vec)):
            if ctdi_vec[i]=='NaN':
                ctdi_vec[i] = np.nan
        ctdi_def = np.nanmean(ctdi_vec)        
        return ctdi_def, data

def change_keys(dic: dict, suffix: str) -> dict:
    """Add suffix to all dictionary keys"""
    return {str(key) + '_' + suffix : val for key, val in dic.items()}

def change_keys_2(prefix: str, dic: dict) -> dict:
     """Add prefix to all dictionary keys"""
     return {prefix + '_' + str(key) : val for key, val in dic.items()}

class EmptyMaskError(Exception):
    """Raised when the mask produces essentially a empty output"""
    def __init__(self, nvox) -> None:
        self.nvox = nvox

class WrongModalityError(Exception):
    """Raised when the DICOM modality is not a CT"""
    def __init__(self,) -> None:
        super().__init__()