"""Helper for i/o with DICOM files."""

import glob
import pydicom

def dcmtagreader(folder_name: str):
    """CT image dicom reader.
    :param folder_name: path of dicom folder
    """
    files_with_dcm = glob.glob(f"{folder_name}/*")
    for inputfile in files_with_dcm:
        data = pydicom.dcmread(inputfile)

    return data
