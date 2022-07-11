# pylint: disable=too-many-instance-attributes
"""Module to rescale voxels in .nii CT scans"""

import glob
import os
import pathlib
import numpy as np
import SimpleITK as sitk
import skimage.transform as skTrans
from tqdm import tqdm


class Rescaler():
    """Class to handle voxel rescaling operations. It supports both Z-rescaling to 3mm
    and isotropic voxel rescaling."""

    def __init__(self, base_dir, iso_ct_name='CT_ISO_1.15.nii',
    mm3_ct_name='CT_3mm.nii' ,iso_vox_dim=1.15):
        self.base_dir = base_dir
        self.iso_vox_dim = iso_vox_dim
        self.iso_ct_name = iso_ct_name
        self.mm3_ct_name = mm3_ct_name

        self.pre_paths = glob.glob(self.base_dir + '/*')
        self.nii_paths = glob.glob(self.base_dir + '/*/CT.nii')
        self.mask_paths = glob.glob(self.base_dir + '/*/mask_R231CW_3mm.nii')
        self.mask_bilat_paths = glob.glob(self.base_dir + '/*/mask_R231CW_3mm_bilat.nii')

        assert len(self.nii_paths) == len(self.mask_paths) == \
        len(self.mask_bilat_paths) == len(self.pre_paths), \
        f"Different lengths! [{len(self.nii_paths), len(self.mask_paths), len(self.mask_bilat_paths), len(self.pre_paths)}]"

    def run_3mm(self,):
        """
        Take native CT.nii and rescale it only along the z axis to make 3mm slices.
        """
        for image_path, pre_path in tqdm(zip(self.nii_paths, self.pre_paths),
         total=len(self.nii_paths), colour='green', desc='Rescaling to 3mm'):

            image_itk = sitk.ReadImage(image_path)
            img_array = sitk.GetArrayFromImage(image_itk)
            _, _, sp_z = image_itk.GetSpacing()

            if sp_z!=3.0:
                #if they are not 3mm, rescale them on Z
                n_x = image_itk.GetWidth()
                n_y = image_itk.GetHeight()
                n_z = image_itk.GetDepth() * sp_z / 3.0

                img_array= skTrans.resize(img_array, (n_z,n_y,n_x), order=1, preserve_range=True)
                image_itk = sitk.GetImageFromArray(img_array)

            sitk.WriteImage(image_itk, os.path.join(pre_path, self.mm3_ct_name))


    def run_iso(self,):
        """
        Take 3mm CT.nii and rescale to 1.15mm isotropic CT.nii.
        Also take 3mm mask.nii and rescale to 1.15mm isotropic mask.nii.
        """

        for image_path, mask_path, mask_bilat_path, pre_path in tqdm(zip(self.nii_paths,
        self.mask_paths, self.mask_bilat_paths, self.pre_paths),
        total=len(self.nii_paths), colour='green', desc='Rescaling to ISO'):

            image_itk =sitk.ReadImage(image_path)
            mask_itk = sitk.ReadImage(mask_path)
            mask_bilat =sitk.ReadImage(mask_bilat_path)

            img_array = sitk.GetArrayFromImage(image_itk)
            mask_array = sitk.GetArrayFromImage(mask_itk)
            mask_bilat_array = sitk.GetArrayFromImage(mask_bilat)

            n_x = image_itk.GetWidth() * image_itk.GetSpacing()[0] / self.iso_vox_dim
            n_y = image_itk.GetHeight() * image_itk.GetSpacing()[1] / self.iso_vox_dim
            n_z = image_itk.GetDepth() * image_itk.GetSpacing()[2] / self.iso_vox_dim

            img_array = skTrans.resize(img_array, (n_z,n_y,n_x), order=1, preserve_range=True)
            mask_array = skTrans.resize(mask_array, (n_z,n_y,n_x), order=1, preserve_range=True)
            mask_bilat_array = np.sign(skTrans.resize(mask_bilat_array,
            (n_z,n_y,n_x), order=1, preserve_range=True))

            sitk.WriteImage(sitk.GetImageFromArray(img_array),
                os.path.join(pre_path, "CT_ISO_1.15.nii"))
            sitk.WriteImage(sitk.GetImageFromArray(mask_array),
                os.path.join(pre_path, "mask_R231CW_ISO_1.15.nii"))
            sitk.WriteImage(sitk.GetImageFromArray(mask_bilat_array),
                os.path.join(pre_path, 'mask_R231CW_ISO_1.15_bilat.nii'))


    def make_upper_mask(self,):
        """
        Create a mask for the upper and lower lungs.
        We simply use the midpoint slice between the two external nonzero slices
        - Upper lung voxel value: 20
        - Lower lung voxel value: 10
        """

        for bilat_mask in self.mask_bilat_paths:
            mask = sitk.ReadImage(bilat_mask)
            mask_array = sitk.GetArrayFromImage(mask)
            n_vox = [np.sum(lung_slice) for lung_slice in mask_array]

            # 0 0 0 0 1 4 6 8 10 35 23 11 6 2 0 0 0 
            # left--> ^           right --> ^

            left  = next((i for i, val in enumerate(n_vox) if val != 0), None)
            right = len(n_vox)-1-next((i for i, v in enumerate(reversed(n_vox)) if v!=0),None)
            mid = (left + right)//2

<<<<<<< HEAD

=======
>>>>>>> interface
            for i in range(mid, len(n_vox)):
                mask_array[i,:,:] *= 2

            new_mask = sitk.GetImageFromArray(mask_array)
            out_path =  pathlib.Path(bilat_mask).parent
            sitk.WriteImage(new_mask, os.path.join(out_path, 'mask_R231CW_3mm_upper.nii'))

    def make_ventral_mask(self,):
        """
        Create a mask for the frontal and dorsal lungs.
        For each slice, we calculate the average y coordinate of the nonzero voxels.
        - Ventral lung voxel value: 20
        - Dorsal lung voxel value: 10
        """

        for bilat_mask in self.mask_bilat_paths:
            
            mask = sitk.ReadImage(bilat_mask)
            mask_array = sitk.GetArrayFromImage(mask)
           
            for i,lung_slice in enumerate(mask_array):

                row_totals = [np.sum(row) for row in lung_slice] 
                
                left  = next((i for i, val in enumerate(row_totals) if val != 0), 0)
                right = len(row_totals)-1-next((k for k, v in enumerate(reversed(row_totals)) if v!=0), 0)
                mid = (left + right)//2
                
                for y in range(mid, len(row_totals)):
                    mask_array[i,y,:] *= 2
        
            new_mask = sitk.GetImageFromArray(mask_array)
            out_path =  pathlib.Path(bilat_mask).parent
            sitk.WriteImage(new_mask, os.path.join(out_path, 'mask_R231CW_3mm_ventral.nii'))
