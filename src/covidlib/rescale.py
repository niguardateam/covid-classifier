import SimpleITK as sitk
import numpy as np
import skimage.transform as skTrans
import os, glob
from tqdm import tqdm


class Rescaler():

    def __init__(self, base_dir, iso_ct_name='CT_ISO_1.15.nii', mm3_ct_name='CT_3mm.nii' ,iso_vox_dim=1.15):
        self.base_dir = base_dir
        self.iso_vox_dim = iso_vox_dim
        self.iso_ct_name = iso_ct_name
        self.mm3_ct_name = mm3_ct_name

        self.pre_paths = glob.glob(self.base_dir + '/*')
        self.nii_paths = glob.glob(self.base_dir + '/*/CT.nii')
        self.mask_paths = glob.glob(self.base_dir + '/*/mask_R231CW_3mm.nii')
        self.mask_bilat_paths = glob.glob(self.base_dir + '/*/mask_R231CW_3mm_bilat.nii')

        return

    def resize_to_iso(self, image_itk):
        sp_x, sp_y, sp_z = image_itk.GetSpacing()
        img_array = sitk.GetArrayFromImage(image_itk)
        n_x = image_itk.GetWidth() * sp_x / self.iso_vox_dim
        n_y = image_itk.GetHeight() * sp_y / self.iso_vox_dim
        n_z = image_itk.GetDepth() * sp_z / self.iso_vox_dim
        im_array_resized = skTrans.resize(img_array, (n_z,n_y,n_x), order=1, preserve_range=True)
        result_image = sitk.GetImageFromArray(im_array_resized)  

        return result_image

    def run_3mm(self,):
        """
        Take native CT.nii and rescale it only along the z axis to make 3mm slices.
        """
        for image_path, pre_path in tqdm(zip(self.nii_paths, self.pre_paths), total=len(self.nii_paths), colour='green', desc='Rescaling to 3mm'):

            image_itk = sitk.ReadImage(image_path)
            img_array = sitk.GetArrayFromImage(image_itk)
            sp_x, sp_y, sp_z = image_itk.GetSpacing()

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

        for image_path, mask_path, mask_bilat_path, pre_path in  tqdm(zip(self.nii_paths, self.mask_paths, self.mask_bilat_paths, self.pre_paths), 
        total=len(self.nii_paths), colour='green', desc='Rescaling to ISO'):

            image_itk = self.resize_to_iso(sitk.ReadImage(image_path))
            mask_itk = self.resize_to_iso(sitk.ReadImage(mask_path))
            mask_bilat = self.resize_to_iso(sitk.ReadImage(mask_bilat_path))

            sitk.WriteImage(image_itk, os.path.join(pre_path, self.iso_ct_name))
            sitk.WriteImage(mask_itk, os.path.join(pre_path, "mask_R231CW_ISO_1.15.nii"))
            sitk.WriteImage(mask_bilat, os.path.join(pre_path, 'mask_R231CW_ISO_1.15_bilat.nii'))


if __name__ == '__main__':
    r = Rescaler(base_dir='/Users/andreasala/Desktop/Tesi/data/COVID-NOCOVID/',)
    r.run_iso()
    r.run_3mm()