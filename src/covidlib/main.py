from covidlib.niftiz import Niftizator
from covidlib.pdfgen import PDFHandler
from covidlib.rescale import Rescaler
from covidlib.masks import MaskCreator
from covidlib.extract import FeaturesExtractor
from covidlib.evaluate import ModelEvaluator
from covidlib.download_from_node import DicomDownloader

import argparse, os
import pandas as pd


# default params
base_dir = '/Users/andreasala/Desktop/Tesi/data/COVID-NOCOVID'
target_sub_dir_name = 'CT'
mask_name_3 = 'mask_R231CW_3mm'
mask_name_iso = "mask_R231CW_ISO_1.15"
output_dir = './results/'
model_json_path = './model/model.json'
model_weights_path = './model/model.h5'
eval_file_name = 'evaluation_results.csv'

ISO_VOX_DIM = 1.15


def main():

    parser = argparse.ArgumentParser("COVID CT Pipeline handler")
    parser.add_argument('--skipmask', action="store_true", default=True, help='Use pre-existing masks instead of making new ones')
    parser.add_argument('--base_dir', type=str, default=base_dir, help='path to folder containing patient data')
    parser.add_argument('--target_dir', type=str, default=target_sub_dir_name, help='Name of the subfolder with the DICOM series')
    parser.add_argument('--output_dir', type=str, default=output_dir, help='Path to output features')
    parser.add_argument('--iso_ct_name', type=str, default=f'CT_ISO_{ISO_VOX_DIM}.nii', help='Isotropic CT name')
    parser.add_argument('--model_json_path', type=str, default=model_json_path, help='Path to pre-trained model')
    parser.add_argument('--model_weights_path', type=str, default=model_weights_path, help='Path to model weights')
    args = parser.parse_args()

    # This downloads a dicom series from a PACS NODE and saves it in local memory
    #dcm = DicomDownloader(ip, port, aetitle, patient_id, series_id, study_id, dcm_output_path)
    #dcm.run()

    #CHANGE THE ORDER!
    # Do masks at 3 mm and then rescale also the masks

    nif = Niftizator(base_dir=base_dir, target_dir_name=target_sub_dir_name)
    nif.run()

    rescale = Rescaler(base_dir=base_dir, iso_vox_dim=ISO_VOX_DIM)
    rescale.run_3mm()

    if not args.skipmask:
        mask = MaskCreator(base_dir=base_dir, maskname=mask_name_3)
        mask.run()
    else:
        print("Loading pre-existing {0}".format(mask_name_3))

    rescale.run_iso()

    extractor = FeaturesExtractor(
                    base_dir=args.base_dir, output_dir=args.output_dir,
                    maskname= mask_name_iso + '_bilat')
    extractor.run()

    #Here we must insert a chunk of code to do the QCT analysis

    eval = ModelEvaluator(features_df= pd.read_csv(os.path.join(args.output_dir, 'features_all.csv'), sep='\t'),
                          model_json_path=args.model_json_path,
                          model_weights_path=args.model_weights_path,
                          out_path=os.path.join(args.output_dir, eval_file_name))

    eval.preprocess()
    eval.run()

    #Maybe write a txt with the QCT analysis + save histogram plot and pass it to the pdf generator
    pdf = PDFHandler(base_dir=args.base_dir, dcm_dir=args.target_dir,
                     data_ref=pd.read_csv(os.path.join(args.output_dir, eval_file_name), sep='\t'))
    pdf.run()


if __name__ == '__main__':
    main()

