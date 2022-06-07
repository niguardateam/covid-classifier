"""File to execute the whole pipeline. It contains the useful
main() function which is the library command"""

import argparse
import os
import pandas as pd
from covidlib.niftiz import Niftizator
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


def main():
    """Execute the whole pipeline."""

    parser = argparse.ArgumentParser("covid-classifier")
    parser.add_argument('--skipmask', action="store_true",
        default=False, help='Use pre-existing masks instead of making new ones')
    parser.add_argument('--base_dir', type=str,
        default=BASE_DIR, help='path to folder containing patient data')
    parser.add_argument('--target_dir', type=str,
        default=TARGET_SUB_DIR_NAME, help='Name of the subfolder with the DICOM series')
    parser.add_argument('--output_dir', type=str,
        default=OUTPUT_DIR, help='Path to output features')
    parser.add_argument('--iso_ct_name', type=str,
        default=f'CT_ISO_{ISO_VOX_DIM}.nii', help='Isotropic CT name')
    parser.add_argument('--model_json_path', type=str,
        default=MODEL_JSON_PATH, help='Path to pre-trained model')
    parser.add_argument('--model_weights_path', type=str,
        default=MODEL_WEIGHTS_PATH, help='Path to model weights')
    args = parser.parse_args()

    # This downloads a dicom series from a PACS NODE and saves it in local memory
    #dcm = DicomDownloader(ip, port, aetitle, patient_id, series_id, study_id, dcm_output_path)
    #dcm.run()

    #nif = Niftizator(base_dir=BASE_DIR, target_dir_name=TARGET_SUB_DIR_NAME)
    #nif.run()

    #rescale = Rescaler(base_dir=BASE_DIR, iso_vox_dim=ISO_VOX_DIM)
    #rescale.run_3mm()

    if not args.skipmask:
        mask = MaskCreator(base_dir=BASE_DIR, maskname=MASK_NAME_3)
        mask.run()
    else:
        print(f"Loading pre-existing {MASK_NAME_3}")

    #rescale.run_iso()

    #extractor = FeaturesExtractor(
    #                base_dir=args.base_dir, output_dir=args.output_dir,
    #                maskname= MASK_NAME_ISO + '_bilat')
    #extractor.run()

    #Here we must insert a chunk of code to do the QCT analysis

    model_ev = ModelEvaluator(features_df= pd.read_csv(
                            os.path.join(args.output_dir, 'radiomics_features.csv'), sep='\t'),
                          model_json_path=args.model_json_path,
                          model_weights_path=args.model_weights_path,
                          out_path=os.path.join(args.output_dir, EVAL_FILE_NAME))

    model_ev.preprocess()
    model_ev.run()

    qct = QCT(base_dir=args.base_dir)
    qct.run()

    #Maybe write a txt with the QCT analysis + save histogram plot and pass it to the pdf generator
    pdf = PDFHandler(base_dir=args.base_dir, dcm_dir=args.target_dir,
                     data_ref=pd.read_csv(os.path.join(args.output_dir, EVAL_FILE_NAME), sep='\t'),
                     data_clinical=pd.read_csv(
                         os.path.join(args.output_dir, "clinical_features.csv"), sep='\t')
                    )
    pdf.run()


if __name__ == '__main__':
    #main()
    print("Hello world")
