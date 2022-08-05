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

    def __init__(self, base_dir, single_mode, slice_thk=3 ,iso_vox_dim=1.15):

        self.base_dir = base_dir
        self.iso_vox_dim = iso_vox_dim
        self.st = slice_thk
        self.iso_ct_name = f"CT_ISO_{iso_vox_dim:.2f}.nii"
        self.mm3_ct_name = f"CT_{slice_thk:.0f}mm.nii"

        self.single_mode = single_mode

        if single_mode:
            self.pre_paths = [self.base_dir]
            self.nii_paths = [os.path.join(self.base_dir, "CT.nii")]

        else:
            self.pre_paths = glob.glob(self.base_dir + '/*')
            self.nii_paths = glob.glob(self.base_dir + '/*/CT.nii')
            


    def run_Xmm(self, x=3.0):
        """
        Take native CT.nii and rescale it only along the z axis to make "x" mm slices.
        """
        for image_path, pre_path in tqdm(zip(self.nii_paths, self.pre_paths),
         total=len(self.nii_paths), colour='green', desc=f'Rescaling to {self.st:.0f}mm'):

            image_itk = sitk.ReadImage(image_path)
            img_array = sitk.GetArrayFromImage(image_itk)
            _, _, sp_z = image_itk.GetSpacing()

            if sp_z!=x:
                #if they are not x mm, rescale them on Z
                n_x = image_itk.GetWidth()
                n_y = image_itk.GetHeight()
                n_z = image_itk.GetDepth() * sp_z / x

                img_array= skTrans.resize(img_array, (n_z,n_y,n_x), order=1, preserve_range=True)
                image_itk = sitk.GetImageFromArray(img_array)

            sitk.WriteImage(image_itk, os.path.join(pre_path, self.mm3_ct_name))


    def run_iso(self,):
        """
        Take x mm CT.nii and rescale to isotropic CT.nii.
        Also take x mm mask.nii and rescale to isotropic mask.nii.
        """
        if self.single_mode:
            self.mask_paths = [os.path.join(self.base_dir , f'mask_R231CW_{self.st:.0f}mm.nii')]
            self.mask_bilat_paths = [os.path.join(self.base_dir , f'mask_R231CW_{self.st:.0f}mm_bilat.nii')]
        else:
            self.mask_paths = glob.glob(self.base_dir + f'/*/mask_R231CW_{self.st:.0f}mm.nii')
            self.mask_bilat_paths = glob.glob(self.base_dir + f'/*/mask_R231CW_{self.st:.0f}mm_bilat.nii')

        pbar = tqdm(total=len(self.nii_paths)*4, colour='green', desc='Rescaling to ISO')

        for image_path, mask_path, mask_bilat_path, pre_path in zip(self.nii_paths,
        self.mask_paths, self.mask_bilat_paths, self.pre_paths):

            image_itk =sitk.ReadImage(image_path)
            try:
                mask_itk = sitk.ReadImage(mask_path)
                mask_bilat =sitk.ReadImage(mask_bilat_path)
            except RuntimeError:
                raise FileNotFoundError(f"File not found: {mask_path} or {mask_bilat_path}")

            img_array = sitk.GetArrayFromImage(image_itk)
            mask_array = sitk.GetArrayFromImage(mask_itk)
            mask_bilat_array = sitk.GetArrayFromImage(mask_bilat)

            n_x = image_itk.GetWidth() * image_itk.GetSpacing()[0] / self.iso_vox_dim
            n_y = image_itk.GetHeight() * image_itk.GetSpacing()[1] / self.iso_vox_dim
            n_z = image_itk.GetDepth() * image_itk.GetSpacing()[2] / self.iso_vox_dim

            pbar.update(1)

            img_array = skTrans.resize(img_array, (n_z,n_y,n_x), order=1, preserve_range=True)
            pbar.update(1)
            mask_array = skTrans.resize(mask_array, (n_z,n_y,n_x), order=1, preserve_range=True)
            pbar.update(1)
            mask_bilat_array = np.sign(skTrans.resize(mask_bilat_array,
            (n_z,n_y,n_x), order=1, preserve_range=True))

            sitk.WriteImage(sitk.GetImageFromArray(img_array),
                os.path.join(pre_path, f"CT_ISO_{self.iso_vox_dim:.2f}.nii"))
            sitk.WriteImage(sitk.GetImageFromArray(mask_array),
                os.path.join(pre_path, f"mask_R231CW_ISO_{self.iso_vox_dim:.2f}.nii"))
            sitk.WriteImage(sitk.GetImageFromArray(mask_bilat_array),
                os.path.join(pre_path, f'mask_R231CW_ISO_{self.iso_vox_dim:.2f}_bilat.nii'))
            pbar.update(1)


    def make_upper_mask(self,):
        """
        Create a mask for the upper and lower lungs.
        We simply use the midpoint slice between the two external nonzero slices
        - Upper lung voxel value: 20
        - Lower lung voxel value: 10
        """
        if self.single_mode:
            self.mask_paths = [os.path.join(self.base_dir , f'mask_R231CW_{self.st:.0f}mm.nii')]
            self.mask_bilat_paths = [os.path.join(self.base_dir , f'mask_R231CW_{self.st:.0f}mm_bilat.nii')]
        else:
            self.mask_paths = glob.glob(self.base_dir + f'/*/mask_R231CW_{self.st}mm.nii')
            self.mask_bilat_paths = glob.glob(self.base_dir + f'/*/mask_R231CW_{self.st:.0f}mm_bilat.nii')

        for bilat_mask in self.mask_bilat_paths:
            mask = sitk.ReadImage(bilat_mask)
            mask_array = sitk.GetArrayFromImage(mask)
            n_vox = [np.sum(lung_slice) for lung_slice in mask_array]

            # 0 0 0 0 1 4 6 8 10 35 23 11 6 2 0 0 0 
            # left--> ^           right --> ^

            left  = next((i for i, val in enumerate(n_vox) if val != 0), None)
            right = len(n_vox)-1-next((i for i, v in enumerate(reversed(n_vox)) if v!=0),None)
            mid = (left + right)//2

            for i in range(mid, len(n_vox)):
                mask_array[i,:,:] *= 2

            new_mask = sitk.GetImageFromArray(mask_array)
            out_path =  pathlib.Path(bilat_mask).parent
            sitk.WriteImage(new_mask, os.path.join(out_path, f'mask_R231CW_{self.st:.0f}mm_upper.nii'))

    def make_ventral_mask(self,):
        """
        Create a mask for the frontal and dorsal lungs.
        For each slice, we calculate the average y coordinate of the nonzero voxels.
        - Ventral lung voxel value: 20
        - Dorsal lung voxel value: 10
        """
        if self.single_mode:
            self.mask_paths = [os.path.join(self.base_dir , f'mask_R231CW_{self.st:.0f}mm.nii')]
            self.mask_bilat_paths = [os.path.join(self.base_dir , f'mask_R231CW_{self.st:.0f}mm_bilat.nii')]
        else:
            self.mask_paths = glob.glob(self.base_dir +f'/*/mask_R231CW_{self.st:.0f}mm.nii')
            self.mask_bilat_paths = glob.glob(self.base_dir + f'/*/mask_R231CW_{self.st:.0f}mm_bilat.nii')

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
            sitk.WriteImage(new_mask, os.path.join(out_path, f'mask_R231CW_{self.st:.0f}mm_ventral.nii'))

    def make_mixed_mask(self,):
        """
        Create a mask for the intersection between UL and VD masks.
        The subROIs are labeled according to the following rule:
         - upper_dorsal = 22
         - upper_ventral = 42
         - lower_dorsal = 11
         - lower_ventral = 21
        """
        if self.single_mode:
            self.maskul_paths = [os.path.join(self.base_dir ,     f'mask_R231CW_{self.st:.0f}mm_upper.nii')]
            self.maskvd_paths = [os.path.join(self.base_dir ,     f'mask_R231CW_{self.st:.0f}mm_ventral.nii')]
            self.mask_mixed_paths = [os.path.join(self.base_dir , f'mask_R231CW_{self.st:.0f}mm_mixed.nii')]
        else:
            self.maskul_paths = glob.glob(self.base_dir +         f'/*/mask_R231CW_{self.st:.0f}mm_upper.nii')
            self.maskvd_paths = glob.glob(self.base_dir +         f'/*/mask_R231CW_{self.st:.0f}mm_ventral.nii')
            self.mask_mixed_paths = glob.glob(self.base_dir +     f'/*/mask_R231CW_{self.st:.0f}mm_mixed.nii')

        for ul_mask, vd_mask, mixed_mask in zip(self.maskul_paths, self.maskvd_paths, self.mask_mixed_paths):
        
            ulmask = sitk.ReadImage(ul_mask)
            vdmask = sitk.ReadImage(vd_mask)
            ulmask_array = 0.1 * sitk.GetArrayFromImage(ulmask) 
            vdmask_array = np.ones(shape=ulmask_array.shape) + sitk.GetArrayFromImage(vdmask)
    
            tot_array = np.multiply(ulmask_array, vdmask_array)
            new_mask = sitk.GetImageFromArray(tot_array)
            sitk.WriteImage(new_mask, mixed_mask)