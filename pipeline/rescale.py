import SimpleITK as sitk
import numpy as np
import skimage.transform as skTrans
import os, glob
from tqdm import tqdm


class Rescaler():

    def __init__(self, base_dir, iso_ct_name='CT_ISO_1.15.nii', iso_vox_dim=1.15):
        self.base_dir = base_dir
        self.iso_vox_dim = iso_vox_dim
        self.iso_ct_name = iso_ct_name

        self.pre_paths = glob.glob(self.base_dir + '/*')
        self.nii_paths = glob.glob(self.base_dir + '/*/CT.nii')

        return


    def run(self,):

        for image_path, pre_path in  tqdm(zip(self.nii_paths, self.pre_paths), total=len(self.nii_paths), colour='green', desc='Rescaling images'):

            image_itk = sitk.ReadImage(image_path)
            sp_x, sp_y, sp_z = image_itk.GetSpacing()
            img_array = sitk.GetArrayFromImage(image_itk)

            n_x = image_itk.GetWidth() * sp_x / self.iso_vox_dim
            n_y = image_itk.GetHeight() * sp_y / self.iso_vox_dim
            n_z = image_itk.GetDepth() * sp_z / self.iso_vox_dim

            im_array_resized = skTrans.resize(img_array, (n_z,n_y,n_x), order=1, preserve_range=True)
            result_image = sitk.GetImageFromArray(im_array_resized)  
            sitk.WriteImage(result_image, os.path.join(pre_path, self.iso_ct_name))



if __name__ == '__main__':
    pass