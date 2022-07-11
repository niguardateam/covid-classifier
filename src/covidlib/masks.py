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

    def __init__(self, base_dir, maskname='mask_R231CW_3mm'):

        self.pre_paths = glob(base_dir + '/*')
        self.iso_nii_paths = glob(base_dir + '/*' + '/CT_3mm.nii')
        self.maskname = maskname


    def run(self):
        """Execute main method of MaskCreator class."""

        print("Creating masks....")
        model = mask.get_model('unet', 'R231CovidWeb')

        for pre_path, isoct_path in zip(self.pre_paths, self.iso_nii_paths):
            image = sitk.ReadImage(isoct_path)
            segm = mask.apply(image, model)
            segm *= 10
            result_out = sitk.GetImageFromArray(segm)
            sitk.WriteImage(result_out, os.path.join(pre_path, self.maskname + '.nii'))
            segm_one = 10*np.sign(segm)
            result_out_one = sitk.GetImageFromArray(segm_one)
            sitk.WriteImage(result_out_one, os.path.join(pre_path, self.maskname + "_bilat.nii"))

            print(f'{os.path.join(pre_path, self.maskname)}' + '.nii file created')
