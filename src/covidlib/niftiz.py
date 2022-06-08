"""Module to convert a DICOM series into NIFTI (.nii) format."""

import glob
import logging
import os
from tqdm import tqdm
from nipype.interfaces.dcm2nii import Dcm2niix

logger = logging.getLogger('nipype.interface')
logger.setLevel(logging.CRITICAL)


class Niftizator:
    """
    Converter from dicom series to nifti.
    """

    def __init__(self, base_dir, target_dir_name):
        self.base_dir = base_dir
        self.target_dir_name = target_dir_name
        self.ct_paths = glob.glob(self.base_dir + '/*/' + target_dir_name + '/')
        self.out_paths = glob.glob(self.base_dir + '/*/CT.nii')
        self.out_dirs = glob.glob(self.base_dir + '/*/')

    def run(self,):
        """Execute main method of Niftizator class.
        It converts a DICOM series to NIFTI."""
        for ct_path, out_path, out_dir in tqdm(zip(
            self.ct_paths, self.out_paths, self.out_dirs),
            total=len(self.ct_paths), colour='yellow', desc='Converting to nifti'):

            nii_exists = os.path.exists(out_path)
            json_exists = os.path.exists(os.path.join(out_dir, 'CT.json'))

            if nii_exists:
                os.remove(out_path)
            if json_exists:
                os.remove(os.path.join(out_dir, 'CT.json'))

            converter = Dcm2niix()
            converter.inputs.source_dir = ct_path
            converter.inputs.compress = 'n'
            converter.inputs.out_filename = 'CT'
            converter.inputs.output_dir = out_dir
            converter.inputs.merge_imgs = True

            _ = converter.run()


if __name__ == '__main__':

    Nif = Niftizator(base_dir="/Users/andreasala/Desktop/Tesi/data/COVID-NOCOVID",
                    target_dir_name='CT')
    Nif.run()
