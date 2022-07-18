"""File to execute the whole pipeline. It contains the useful
main() function which is the library command"""

import argparse
import os
import logging
import pandas as pd
from covidlib.niftiz import Niftizator
from covidlib.pacs import DicomLoader
from covidlib.pdfgen import PDFHandler
from covidlib.rescale import Rescaler
from covidlib.masks import MaskCreator
from covidlib.extract import FeaturesExtractor
from covidlib.evaluate import ModelEvaluator
from covidlib.qct import QCT
#from covidlib.download_from_node import DicomDownloader


# default params
BASE_DIR = '/Users/andreasala/Desktop/Tesi/data2/COVID-NOCOVID'
TARGET_SUB_DIR_NAME = 'CT'
MASK_NAME_3 = 'mask_R231CW_3mm'
MASK_NAME_ISO = "mask_R231CW_ISO_1.15"
OUTPUT_DIR = './results/'
MODEL_JSON_PATH = 'model/model.json'
MODEL_WEIGHTS_PATH = 'model/model.h5'
EVAL_FILE_NAME = 'evaluation_results.csv'
ISO_VOX_DIM = 1.15


#add pacs functionality

def main():
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
    """Execute the whole pipeline."""

    parser = argparse.ArgumentParser("clearlung")
    parser.add_argument('-n','--skipnifti', action="store_true", default=False, help='Use pre-existing nii images')
    parser.add_argument('-r3','--skiprescaling3mm', action="store_true", default=False, help='Use pre-existing 3mm rescaled nii images and masks')
    parser.add_argument('-ri','--skiprescalingiso', action="store_true", default=False, help='Use pre-existing ISO rescaled nii images and masks')
    parser.add_argument('-e','--skipextractor', action="store_true", default=False, help='Use pre-existing features')
    parser.add_argument('-k','--skipmask', action="store_true", default=False, help='Use pre-existing masks')
    parser.add_argument('-q','--skipqct', action="store_true", default=False, help='Use pre-existing qct')
    parser.add_argument('-lr', action='store_true', default=False, help='Perform analysis on left-right lung')
    parser.add_argument('-ul', action='store_true', default=False, help='Perform analysis on upper-lower lung')
    parser.add_argument('-vd', action='store_true', default=False, help='Perform analysis on ventral-dorsal lung')
    parser.add_argument('--base_dir', type=str, default=BASE_DIR, help='path to folder containing patient data')
    parser.add_argument('--target_dir', type=str, default=TARGET_SUB_DIR_NAME, help='Name of the subfolder with the DICOM series')
    parser.add_argument('--output_dir', type=str, default=OUTPUT_DIR, help='Path to output features')
    parser.add_argument('--iso_ct_name', type=str, default=f'CT_ISO_{ISO_VOX_DIM}.nii', help='Isotropic CT name')
    parser.add_argument('--model', type=str, default="./model/", help='Path to pre-trained model')

    parser.add_argument("--from_pacs", action="store_true")
    parser.add_argument("--to_pacs", action="store_true")
    parser.add_argument('--ip', type=str, help='IP address of central pacs node', default='10.1.150.22')
    parser.add_argument('--port', type=int, help='Port of central pacs node', default=104)
    parser.add_argument('--aetitle', type=str, help='AE Title of central PACS node', default='EINIG')
    parser.add_argument('--patientID', type=str, help='Patient ID (download from pacs', default='0')
    parser.add_argument('--seriesUID', type=str, help='Series UID (download from pacs', default='0')
    parser.add_argument('--studyUID', type=str, help='Study UID (download from pacs', default='0')
    # pacs output path = base_dir
    
    args = parser.parse_args()

    print("Args parsed")

    if args.from_pacs or args.to_pacs:
        loader = DicomLoader(ip_add=args.ip, port=args.port, aetitle=args.aetitle,
                                patient_id=args.patientID, study_id=args.studyUID, 
                                series_id=args.seriesUID, output_path=args.base_dir)
       
    if args.from_pacs:
        loader.download()
        print("DICOM series correctly downloaded")
    

    parts = ['bilat']

    if args.lr:
        parts += ['left', 'right']
    if args.ul:
         parts += ['upper', 'lower']
    if args.vd:
        parts += ['ventral', 'dorsal']

    if not os.path.isdir(args.output_dir):
        os.mkdir(args.output_dir)

    if not args.skipnifti:
        nif = Niftizator(base_dir=args.base_dir, target_dir_name=args.target_dir)
        nif.run()

    rescale = Rescaler(base_dir=args.base_dir, iso_vox_dim=ISO_VOX_DIM)    
    if not args.skiprescaling3mm:
        rescale.run_3mm()
    
   
    if not args.skipmask:
        mask = MaskCreator(base_dir=args.base_dir, maskname=MASK_NAME_3)
        mask.run()
    else:
        print(f"Loading pre-existing {MASK_NAME_3}")

    if not args.skiprescalingiso:
        rescale.run_iso()
    if 'upper' in parts:
        rescale.make_upper_mask()
    if 'ventral' in parts:
        rescale.make_ventral_mask()

    extractor = FeaturesExtractor(
                    base_dir=args.base_dir, output_dir=args.output_dir,
                    maskname= MASK_NAME_ISO + '_bilat')

    if not args.skipextractor:
        extractor.run()

    print("Evaluating COVID probability...")
    model_ev = ModelEvaluator(features_df= pd.read_csv(
                            os.path.join(args.output_dir, 'radiomics_features.csv'), sep='\t'),
                          model_path= args.model,
                          out_path=os.path.join(args.output_dir, EVAL_FILE_NAME))

    model_ev.preprocess()
    model_ev.run()

    qct = QCT(base_dir=args.base_dir, parts=parts, out_dir=args.output_dir)
    if not args.skipqct:
        qct.run()

    pdf = PDFHandler(base_dir=args.base_dir, dcm_dir=args.target_dir,
                     data_ref=pd.read_csv(os.path.join(args.output_dir, EVAL_FILE_NAME), sep='\t'),
                     data_clinical=pd.read_csv(os.path.join(args.output_dir, 'clinical_features.csv'), sep='\t'),
                     out_dir=args.output_dir, parts=parts)
                    
    pdf.run()
    encapsulated_today = pdf.encapsulate()

    if args.to_pacs:
        loader.upload(encapsulated_today)
        print("Report uploaded on PACS")

    print("Goodbye!")


if __name__ == '__main__':
    #main()
    print("Hello world. Please use the command line :]")
