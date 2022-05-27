from glob import glob
import numpy as np
import os
import SimpleITK as sitk
import sys
from lungmask import mask
from tqdm import tqdm
import torch


class MaskCreator:

    def __init__(self, base_dir, maskname='mask_R231CW_ISO'):

        self.pre_paths = glob(base_dir + '/*')
        self.iso_nii_paths = glob(base_dir + '/*' + '/CT_ISO_1.15.nii')

        self.maskname = maskname

    def run(self):
        print("Creating masks....")
        model = mask.get_model('unet', 'R231CovidWeb')
        # for pre_path, isoct_path in tqdm(zip(self.pre_paths, self.iso_nii_paths), total=len(self.pre_paths), colour='cyan', desc='Creating lung masks'):
        for pre_path, isoct_path in zip(self.pre_paths, self.iso_nii_paths):
            image = sitk.ReadImage(isoct_path)
            segm = mask.apply(image, model)
            result_out = sitk.GetImageFromArray(segm)
            sitk.WriteImage(result_out, os.path.join(pre_path, self.maskname + '.nii'))
            segm_one = np.sign(segm)
            result_out_one = sitk.GetImageFromArray(segm_one)
            sitk.WriteImage(result_out_one, os.path.join(pre_path, self.maskname + "_bilat.nii"))

            print(f'{os.path.join(pre_path, self.maskname)}' + '.nii file created')
