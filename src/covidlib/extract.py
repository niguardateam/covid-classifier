"""Module to extract first and second order radiomic feautres
from CT scans in .nii format"""

from email.mime import base
import os
import csv
import logging
from glob import glob
from tqdm import tqdm
import SimpleITK as sitk
import pandas as pd
import radiomics
from covidlib.ctlibrary import dcmtagreader, change_keys

logger = logging.getLogger("radiomics")
logger.setLevel(logging.ERROR)

class FeaturesExtractor:
    """Class to handle radiomic feature extraction with pyradiomics"""

    def __init__(self, base_dir, single_mode, output_dir, maskname, ivd,
        ford_p, glcm_p, glszm_p, glrlm_p, ngtdm_p, gldm_p, shape3d_p,):
        """Constructor for the FeaturesExtractor class. 
        
        :param base_dir: base directory where the .nii files live
        :param single_mode: boolean flag to indicate if the pipeline is in single or multiple mode
        :param output_dir: path to results directory
        :param maskname: filename of the mask file (usually mask_R231CW)
        :param ivd: isotropic voxel dimension
        :param ford_p: params (left, right, bin_width) for first order radiomic features
        :param glcm_p: params (left, right, bin_width) for GLCM radiomic features
        :param glszm_p: params (left, right, bin_width) for GLSZM radiomic features
        :param glrlm_p: params (left, right, bin_width) for GLRLM radiomic features
        :param ngtdm_p: params (left, right, bin_width) for NGTDM radiomic features
        :param gldm_p: params (left, right, bin_width) for GLDM radiomic features
        :param shape3d_p: params (left, right, bin_width) for 3D shape radiomic features 
        """

        self.base_dir = base_dir
        self.output_dir = output_dir
        self.ivd = ivd

        if single_mode:
            self.base_paths = [base_dir]
            self.ct_paths = [os.path.join(base_dir, f"CT_ISO_{ivd:.2f}.nii")]
            self.mask_paths = [os.path.join(base_dir, maskname + '.nii')]
        else:
            self.base_paths = glob(base_dir + '/*')
            self.ct_paths = glob(base_dir + f'/*/CT_ISO_{ivd:.2f}.nii')
            self.mask_paths = glob(base_dir + '/*/' + maskname + '.nii')

        if len(self.ct_paths)==0:
            raise ValueError

        self.ford_p = ford_p
        self.glcm_p = glcm_p
        self.glszm_p = glszm_p
        self.glrlm_p = glrlm_p
        self.ngtdm_p = ngtdm_p
        self.gldm_p = gldm_p
        self.shape3d_p = shape3d_p
            

    def setup_round(self, ct_path):
        """Define some boring settings for the DICOM tag reader"""

        searchtag = dcmtagreader(ct_path)
        try:
            acqdate = searchtag[0x0008,0x0022].value
        except:
            acqdate = "N/D"
        try:
            pzage = searchtag[0x0010, 0x1010].value
        except:
            pzage = '-99'
        try:
            pzsex = searchtag[0x0010, 0x0040].value
        except:
            pzsex = 'N/D'
        try:
            accnumber = searchtag[0x0008, 0x0050].value
        except:
            accnumber = '-99999'
        covlabel = 1 if acqdate.startswith('2020') or acqdate.startswith('2021') else 0

        my_dict =  {
        'AccessionNumber': accnumber,
        'PatientAge': pzage,
        'PatientSex':pzsex,
        'Acquisition Date': acqdate,
        'PatientTag': covlabel,
        'Voxel size ISO': self.ivd }

        return my_dict


    def run(self):  
        """Execute main method of FeaturesExtractor class.
            Extract radiomic features from nifti file"""
        features_df = pd.DataFrame()
        total_df = pd.DataFrame()

        with open(os.path.join( self.output_dir, 'radiomic_total.csv'),'w', encoding='utf-8') as fall, open(
            os.path.join( self.output_dir, 'radiomic_features.csv'),'w', encoding='utf-8') as f_NN:

            fall_wr = csv.writer(fall, delimiter='\t')
            f_NN_wr = csv.writer(f_NN, delimiter='\t')

            p_bar = tqdm(total=len(self.base_paths)*9, colour='cyan',desc='Radiomic features  ')

            for base_path, ct_path, mask_path in zip(self.base_paths, self.ct_paths, self.mask_paths):

                result_1 = self.setup_round (os.path.join(base_path, 'CT'))
                result_all = result_1
                result_NN = self.setup_round(os.path.join(base_path, 'CT'))

                image = sitk.ReadImage(ct_path)
                mask = sitk.ReadImage(mask_path)
                p, j= 5, 240

                settings = {
                    'voxelArrayShift': 0,
                    'label': 1,
                    'resegmentRange': [-1020, 180],
                    'binWidth': p,
                    'binCount': j
                }

                extr_1ord = radiomics.firstorder.RadiomicsFirstOrder(image, mask, **settings)
                feat_1ord = change_keys(extr_1ord.execute(), str(p))

                result_all.update(feat_1ord)
                result_NN.update(feat_1ord)
                p_bar.update(1)

                ## SECOND ORDER - FOR NEURAL NETWORK

                # 1. GLCM
                result_glcm = {}

                for bin_width in [5, 25, 50]:
                    j = int(1200/bin_width)

                    settings = {
                        'label': 1,
                        'resegmentRange': [-1020, 180],
                        'binWidth': bin_width,
                        'binCount': j
                    }

                    glcm_features = radiomics.glcm.RadiomicsGLCM(
                        image, mask, **settings)
                    feat_glcm = change_keys(glcm_features.execute(), str(bin_width))
                    result_glcm.update(feat_glcm)

                result_NN.update(result_glcm)
                p_bar.update(1)

                # 2. GLSZM
                result_glszm = {}

                for bin_width in [25, 100, 200]:
                    j = int(1200/bin_width)

                    settings = {
                        'label': 1  ,
                        'resegmentRange': [-1020, 180],
                        'binWidth': bin_width,
                        'binCount': j
                    }

                    glszm_features = radiomics.glszm.RadiomicsGLSZM(
                        image, mask, **settings)

                    feat_glszm = change_keys(glszm_features.execute(), str(bin_width))
                    result_glszm.update(feat_glszm)

                result_NN.update(result_glszm)
                p_bar.update(1)

                result_all.update(result_NN)

                #FIRST AND SECOND SECOND ORDER - FOR CSV FILE
                #ONLY IF THE ARGUMENT IS CHECKED!

                # 0. FIRST ORDER

                result_1ord = {}
                on, l,r, bin_width = self.ford_p
                j = int((int(r)-int(l))/int(bin_width))

                if int(on)==1:
                    settings = {
                        'voxelArrayShift': 0,
                        'label': 1,
                        'resegmentRange': [l, r],
                        'binWidth': bin_width,
                        'binCount': j
                    }

                    res_1ord = radiomics.firstorder.RadiomicsFirstOrder(image, mask, **settings)
                    dict_1ord = change_keys(res_1ord.execute(), str(p))
                    dict_1ord = change_keys(dict_1ord, str(l))
                    dict_1ord = change_keys(dict_1ord, str(r))

                    result_1ord.update(dict_1ord)
                    result_all.update(result_1ord)

                # 1. GLCM
                result_glcm = {}
                on, l,r, bin_width = self.glcm_p
                j = int((int(r)-int(l))/int(bin_width))

                if int(on)==1:
                    settings = {
                        'label': 1,
                        'resegmentRange': [l, r],
                        'binWidth': bin_width,
                        'binCount': j
                    }
                    glcm_features = radiomics.glcm.RadiomicsGLCM(
                        image, mask, **settings)
                    feat_glcm = change_keys(glcm_features.execute(), str(bin_width))
                    feat_glcm = change_keys(feat_glcm, str(l))
                    feat_glcm = change_keys(feat_glcm, str(r))

                    result_glcm.update(feat_glcm)

                    result_all.update(result_glcm)
                p_bar.update(1)

                # 2. GLSZM
                result_glszm = {}
                on, l,r, bin_width = self.glszm_p
                j = int((int(r)-int(l))/int(bin_width))

                if int(on)==1:

                    settings = {
                        'label': 1  ,
                        'resegmentRange': [l, r],
                        'binWidth': bin_width,
                        'binCount': j
                    }

                    glszm_features = radiomics.glszm.RadiomicsGLSZM(
                        image, mask, **settings)

                    feat_glszm = change_keys(glszm_features.execute(), str(bin_width))
                    feat_glszm = change_keys(feat_glszm, str(l))
                    feat_glszm = change_keys(feat_glszm, str(r))
                    result_glszm.update(feat_glszm)

                    result_all.update(result_glszm)
                p_bar.update(1)

                # 3. GLRLM

                result_glrlm = {}
                on, l, r, bin_width = self.glrlm_p
                j = int((int(r)-int(l))/int(bin_width))

                if int(on)==1:

                    settings = {
                        'label': 1  ,
                        'resegmentRange': [l, r],
                        'binWidth': bin_width,
                        'binCount': j
                    }

                    glrlm_features = radiomics.glrlm.RadiomicsGLRLM(image, mask, **settings)
                    feat_glrlm = change_keys(glrlm_features.execute(), str(bin_width))
                    feat_glrlm = change_keys(feat_glrlm, str(l))
                    feat_glrlm = change_keys(feat_glrlm, str(r))
                    result_glrlm.update(feat_glrlm)

                    result_all.update(result_glrlm)
                p_bar.update(1)

                # 4. NGTDM

                result_ngtdm = {}
                on, l, r, bin_width = self.ngtdm_p
                j = int((int(r)-int(l))/int(bin_width))

                if int(on)==1:
                   
                    settings = {
                        'label': 1  ,
                        'resegmentRange': [l, r],
                        'binWidth': bin_width,
                        'binCount': j
                    }


                    ngtdm_features = radiomics.ngtdm.RadiomicsNGTDM(image, mask, **settings)
                    feat_ngtdm = change_keys(ngtdm_features.execute(), str(bin_width))
                    feat_ngtdm = change_keys(feat_ngtdm, str(l))
                    feat_ngtdm = change_keys(feat_ngtdm, str(r))
                    result_ngtdm.update(feat_ngtdm)

                    result_all.update(result_ngtdm)
                p_bar.update(1)

                # 5. GLDM

                result_gldm = {}
                on, l, r, bin_width = self.gldm_p
                j = int((int(r)-int(l))/int(bin_width))

                if int(on)==1:

                    settings = {
                        'label': 1  ,
                        'resegmentRange': [l, r],
                        'binWidth': bin_width,
                        'binCount': j
                    }

                    gldm_features = radiomics.gldm.RadiomicsGLDM(image, mask, **settings)
                    feat_gldm = change_keys(gldm_features.execute(), str(bin_width))
                    feat_gldm = change_keys(feat_gldm, str(l))
                    feat_gldm = change_keys(feat_gldm, str(r))
                    result_gldm.update(feat_gldm)

                    result_all.update(result_gldm)
                p_bar.update(1)

                # 6. SHAPE FEATURES (3D)
             
                result_sh3 = {}
                on, l, r, bin_width = self.shape3d_p
                j = int((int(r)-int(l))/int(bin_width))

                if int(on)==1:
                  
                    settings = {
                        'label': 1  ,
                        'resegmentRange': [l, r],
                        'binWidth': bin_width,
                        'binCount': j
                    }

                    sh3_features = radiomics.shape.RadiomicsShape(image, mask, **settings)
                    feat_sh3 = change_keys(sh3_features.execute(), str(bin_width))
                    feat_sh3 = change_keys(feat_sh3, str(l))
                    feat_sh3 = change_keys(feat_sh3, str(r))
                    result_sh3.update(feat_sh3)

                    result_all.update(result_sh3)
                p_bar.update(1)


                #writing to file
                if features_df.empty:
                    features_df = pd.DataFrame({k: [v] for k, v in result_NN.items()})
                else:
                    new = pd.DataFrame({k: [v] for k, v in result_NN.items()})
                    features_df = pd.concat([features_df, new], ignore_index=True)

                if total_df.empty:
                    total_df = pd.DataFrame({k: [v] for k, v in result_all.items()})
                else:
                    new = pd.DataFrame({k: [v] for k, v in result_all.items()})
                    total_df = pd.concat([total_df, new], ignore_index=True)

                if fall.tell()==0:
                    fall_wr.writerow(result_all.keys())
                fall_wr.writerow(result_all.values())

                if f_NN.tell()==0:
                    f_NN_wr.writerow(result_NN.keys())
                f_NN_wr.writerow(result_NN.values())

            fall.close()
            f_NN.close()

        return features_df