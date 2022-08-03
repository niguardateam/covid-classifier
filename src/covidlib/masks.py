"""Module to calculate masks for lung segmentation.
This module requires the installation of lungmask
pip install git+https://github.com/JoHof/lungmask
"""

from glob import glob
import logging
import os
import numpy as np
import SimpleITK as sitk
from lungmask import mask

logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)


class MaskCreator:
    """Class to handle mask creation and storage in local memory."""

    def __init__(self, base_dir, single_mode, st, ivd):

        self.base_dir = base_dir
        self.ivd = ivd
        self.st = st

        if single_mode:
            self.pre_paths = [base_dir]
            self.nii_paths = [os.path.join(base_dir, f'CT_{st:.0f}mm.nii')]
        else:
            self.pre_paths = glob(base_dir + '/*')
            self.nii_paths = glob(base_dir + '/*' + f'/CT_{st:.0f}mm.nii')
            
        self.maskname =f'mask_R231CW_{self.st:.0f}mm'


    def run(self):
        """Execute main method of MaskCreator class."""

        print("Creating masks....")
        model = mask.get_model('unet', 'R231CovidWeb')

        for pre_path, isoct_path in zip(self.pre_paths, self.nii_paths):
            image = sitk.ReadImage(isoct_path)
            segm = mask.apply(image, model)
            segm *= 10
            result_out = sitk.GetImageFromArray(segm)
            sitk.WriteImage(result_out, os.path.join(pre_path, self.maskname + '.nii'))
            segm_one = 10*np.sign(segm)
            result_out_one = sitk.GetImageFromArray(segm_one)
            sitk.WriteImage(result_out_one, os.path.join(pre_path, self.maskname + "_bilat.nii"))

            print(f'{os.path.join(pre_path, self.maskname)}' + '.nii file created')
