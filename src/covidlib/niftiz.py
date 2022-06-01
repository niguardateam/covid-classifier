import dicom2nifti
import glob, os
import os
from tqdm import tqdm
import logging

logger = logging.getLogger("dicom2nifti")
logger.setLevel(logging.ERROR)


class Niftizator:
    """
    Converter from dicom series to nifti.
    """

    def __init__(self, base_dir, target_dir_name):
        self.base_dir = base_dir
        self.target_dir_name = target_dir_name
        out_paths = glob.glob(self.base_dir + '/*/CT.nii')
        ct_paths = glob.glob(self.base_dir + '/*/' + target_dir_name + '/')

        self.ct_paths = ct_paths
        self.out_paths = out_paths

        return
    
    def run(self,):
        for ct_path, out_path in tqdm(zip(self.ct_paths, self.out_paths),
         total=len(self.ct_paths), colour='yellow', desc='Converting to nifti'):
            dicom2nifti.dicom_series_to_nifti(ct_path, out_path, reorient_nifti=False)

if __name__ == '__main__':

    Nif = Niftizator(base_dir="/Users/andreasala/Desktop/Tesi/data/COVID-NOCOVID",
                    target_dir_name='CT')

    Nif.run(verbose=True)
