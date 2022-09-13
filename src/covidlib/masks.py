"""Module to calculate masks for lung segmentation.
This module requires the installation of lungmask
pip install git+https://github.com/JoHof/lungmask
"""

from glob import glob
import logging
import os
import numpy as np
from lungmask import mask
from tqdm import tqdm
import SimpleITK as sitk

logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)


class MaskCreator:
    """Class to handle mask creation and storage in local memory."""

    def __init__(self, base_dir, single_mode, st, ivd):
        """Constructor for the MaskCreator class.
        :param base_dir: Path to .nii CT
        :param single_mode: Flag to indicate if the code is running in single or multiple mode
        :param st: slice thickness. It is automatically casted to int
        :param ivd: Isotropic voxel dimension
        """

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
        """Execute main method of MaskCreator class.
        Produce masks and save them in local memory"""

        model = mask.get_model('unet', 'R231CovidWeb')

        for pre_path, isoct_path in tqdm(
            zip(self.pre_paths, self.nii_paths), total=len(self.pre_paths), colour='MAGENTA',
            desc="Creating masks     "):
            image = sitk.ReadImage(isoct_path)
            segm = mask.apply(image, model)
            segm *= 10
            result_out = sitk.GetImageFromArray(segm)
            sitk.WriteImage(result_out, os.path.join(pre_path, self.maskname + '.nii'))
            segm_one = 10*np.sign(segm)
            result_out_one = sitk.GetImageFromArray(segm_one)
            sitk.WriteImage(result_out_one, os.path.join(pre_path, self.maskname + "_bilat.nii"))
