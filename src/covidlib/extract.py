from glob import glob
from tqdm import tqdm
import pandas as pd


# pytest --pyargs src/covidlib

import csv, os

import numpy as np
from covidlib.ctlibrary import  dcmtagreader
import radiomics

import SimpleITK as sitk
import logging

logger = logging.getLogger("radiomics")
logger.setLevel(logging.ERROR)


def change_keys(d, a):
    if type(d) is dict:
        return dict([(k + '_' + a, change_keys(v, a)) for k, v in d.items()])
    else:
        return d


class FeaturesExtractor:

    #remember to add the option for a non-standard mask!
    def __init__(self, base_dir, output_dir, maskname='mask_R231CW_ISO_1.15_bilat',):

        self.base_dir = base_dir
        self.output_dir = output_dir
        self.base_paths = glob(base_dir + '/*')
        self.ct_paths = glob(base_dir + '/*/CT_ISO_1.15.nii')
        self.mask_paths = glob(base_dir + '/*/' + maskname + '.nii')


    def setup_round(self, ct_path):

        searchtag = dcmtagreader(ct_path)
        pzname = searchtag[0x0010, 0x0010].value
        acqdate = searchtag[0x0008,0x0022].value
        try:
            pzage = searchtag[0x0010, 0x1010].value
        except:
            pzage = '-99'
        try:
            pzsex = searchtag[0x0010, 0x0040].value
        except:
            pzsex = '-99'
        try:
            accnumber = searchtag[0x0008, 0x0050].value
        except:
            accnumber = '-99'

        covlabel = 1 if acqdate.startswith('2020') or acqdate.startswith('2021') else 0

        myDict =  {
        'AccessionNumber': accnumber,
        'PatientAge': pzage,
        'PatientSex':pzsex,
        'Acquisition Date': acqdate,
        'COVlabel': covlabel,
        'Voxel size ISO': 1.15 }

        return myDict


    def run(self):

        features_df = pd.DataFrame()

        with open(os.path.join( self.output_dir  , 'radiomics_features.csv'), 'w') as fall:

            fall_wr = csv.writer(fall, delimiter='\t')

            for base_path, ct_path, mask_path in tqdm(zip(self.base_paths, self.ct_paths, self.mask_paths),
                                                    total=len(self.base_paths), colour='cyan',
                                                    desc='Extracting features'):

                result_1 = self.setup_round(base_path + '/CT/')
                result_all = result_1

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

                #Second order

                #GLCM
                result_GLCM = {}

                for p in [5, 25, 50]:
                    j = int(1200/p)

                    settings = {
                        'label': 1,
                        'resegmentRange': [-1020, 180],
                        'binWidth': p,
                        'binCount': j
                    }

                    GLCMfeatures = radiomics.glcm.RadiomicsGLCM(
                        image, mask, **settings)
                    feat_GLCM = change_keys(GLCMfeatures.execute(), str(p))
                    result_GLCM.update(feat_GLCM)

                result_all.update(result_GLCM)

                #GLSZM
                result_GLSZM = {}

                for p in [25, 100, 200]:
                    j = int(1200/p)

                    settings = {
                        'label': 1  ,
                        'resegmentRange': [-1020, 180],
                        'binWidth': p,
                        'binCount': j
                    }

                    GLSZMfeatures = radiomics.glszm.RadiomicsGLSZM(
                        image, mask, **settings)

                    feat_GLSZM = change_keys(GLSZMfeatures.execute(), str(p))
                    result_GLSZM.update(feat_GLSZM)

                result_all.update(result_GLSZM)

                if features_df.empty:
                    features_df = pd.DataFrame({k: [v] for k, v in result_all.items()})
                else:
                    new = pd.DataFrame({k: [v] for k, v in result_all.items()})
                    features_df = pd.concat([features_df, new], ignore_index=True)

                if fall.tell()==0:
                    fall_wr.writerow(result_all.keys())
                fall_wr.writerow(result_all.values())


            fall.close()


        return features_df

if __name__=='__main__':
    FeaturesExtractor(base_dir='/Users/andreasala/Desktop/Tesi/data/COVID-NOCOVID/',
                    output_dir='/Users/andreasala/Desktop/Tesi/pipeline/results/')

