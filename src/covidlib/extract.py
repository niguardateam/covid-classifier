"""Module to extract first and second order radiomic feautres
from CT scans in .nii format"""

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
    """Class to handle feature extraction"""

    def __init__(self, base_dir, output_dir, maskname='mask_R231CW_ISO_1.15_bilat',):
        self.base_dir = base_dir
        self.output_dir = output_dir
        self.base_paths = glob(base_dir + '/*')
        self.ct_paths = glob(base_dir + '/*/CT_ISO_1.15.nii')
        self.mask_paths = glob(base_dir + '/*/' + maskname + '.nii')

    def setup_round(self, ct_path):
        """Define some boring settings"""

        searchtag = dcmtagreader(ct_path)
        #pzname = searchtag[0x0010, 0x0010].value
        acqdate = searchtag[0x0008,0x0022].value
        pzage = searchtag[0x0010, 0x1010].value
        pzsex = searchtag[0x0010, 0x0040].value
        accnumber = searchtag[0x0008, 0x0050].value

        covlabel = 1 if acqdate.startswith('2020') or acqdate.startswith('2021') else 0

        my_dict =  {
        'AccessionNumber': accnumber,
        'PatientAge': pzage,
        'PatientSex':pzsex,
        'Acquisition Date': acqdate,
        'COVlabel': covlabel,
        'Voxel size ISO': 1.15 }

        return my_dict


    def run(self):  
        """Execute main method of FeaturesExtractor class."""
        features_df = pd.DataFrame()

        with open(os.path.join( self.output_dir, 'radiomics_features.csv'),
            'w', encoding='utf-8') as fall:

            fall_wr = csv.writer(fall, delimiter='\t')

            for base_path, ct_path, mask_path in tqdm(
                zip(self.base_paths, self.ct_paths, self.mask_paths),
                total=len(self.base_paths), colour='cyan',desc='Radiomic features'):

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

                result_all.update(result_glcm)

                #GLSZM
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

                result_all.update(result_glszm)

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
