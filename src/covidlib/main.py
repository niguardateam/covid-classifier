"""File to execute the whole pipeline. It contains the useful
main() function which is the library command"""

import argparse
import os
import time

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import pandas as pd
from covidlib.niftiz import Niftizator
from covidlib.pacs import DicomLoader
from covidlib.pdfgen import PDFHandler
from covidlib.rescale import Rescaler
from covidlib.masks import MaskCreator
from covidlib.extract import FeaturesExtractor
from covidlib.evaluate import ModelEvaluator
from covidlib.qct import QCT

from traits.trait_errors import TraitError

# default params
BASE_DIR = '/Users/andreasala/Desktop/Tesi/data2/COVID-NOCOVID'
TARGET_SUB_DIR_NAME = 'CT'
MASK_NAME_3 = 'mask_R231CW_3mm'
MASK_NAME_ISO = "mask_R231CW_ISO_1.15"
OUTPUT_DIR = './results/'
EVAL_FILE_NAME = 'evaluation_results.csv'
ISO_VOX_DIM = 1.15



#add pacs functionality

def main():
    """Execute the whole pipeline."""

    print_intro()
    start = time.time()

    parser = argparse.ArgumentParser("clearlung")

    parser.add_argument('--single', action="store_true", help="Activate single mode")
    parser.add_argument('--automatic', action="store_true", help='Pipeline starts on automatic')

    parser.add_argument('-n','--skipnifti', action="store_true", default=False, help='Use pre-existing nii images')
    parser.add_argument('-r3','--skiprescaling3mm', action="store_true", default=False, help='Use pre-existing 3mm rescaled nii images and masks')
    parser.add_argument('-ri','--skiprescalingiso', action="store_true", default=False, help='Use pre-existing ISO rescaled nii images and masks')
    parser.add_argument('-k','--skipmask', action="store_true", default=False, help='Use pre-existing masks')
    parser.add_argument('--radqct', action="store_true", default=False, help='Skip radiomics and qct')
    parser.add_argument('--skippdf', action="store_true", default=False, help='Skip pdf generation')
    
    parser.add_argument('--base_dir', type=str, help='path to folder containing patient data')
    parser.add_argument('--target_dir', type=str, default='CT', help='Name of the subfolder with the DICOM series')
    parser.add_argument('--output_dir', type=str, default=OUTPUT_DIR, help='Path to output features')
    parser.add_argument('--slice_thickness_qct', type=float, default=3, help='Slice thickness in mm for QCT', dest='st')
    parser.add_argument('--slice_thickness_iso', type=float, default=1.15, help='Voxel dimension for ISO rescaling', dest='ivd')

    parser.add_argument('--model', type=str, default="./model/", help='Path to pre-trained model')
    parser.add_argument('--tag', help='Tag to add to output files')
    parser.add_argument('--subroi', action="store_true", help='Execute QCT analysis on subROIs and write it on the final csv file')

    parser.add_argument("--from_pacs", action="store_true")
    parser.add_argument("--to_pacs", action="store_true")
    parser.add_argument('--ip', type=str, help='IP address of central pacs node', default='10.1.150.22')
    parser.add_argument('--port', type=int, help='Port of central pacs node', default=104)
    parser.add_argument('--aetitle', type=str, help='AE Title of central PACS node', default='EINIG')
    parser.add_argument('--patientID', type=str, help='Patient ID (download from pacs', default='0')
    parser.add_argument('--seriesUID', type=str, help='Series UID (download from pacs', default='0')
    parser.add_argument('--studyUID', type=str, help='Study UID (download from pacs', default='0')
    
    parser.add_argument('--GLCM_params', action='store', dest='GLCM', type=str, nargs=3, default=[-1020, 180, 25],
     help="Custom params for GLCM")
    parser.add_argument('--GLSZM_params', action='store', dest='GLSZM', type=str, nargs=3, default=[-1020, 180, 25],
     help="Custom params for GLSZM")
    parser.add_argument('--GLRLM_params', action='store', dest='GLRLM', type=str, nargs=3, default=[-1020, 180, 25],
     help="Custom params for GLRLM")
    parser.add_argument('--NGTDM_params', action='store', dest='NGTDM', type=str, nargs=3, default=[-1020, 180, 25],
     help="Custom params for NGTDM")
    parser.add_argument('--GLDM_params', action='store', dest='GLDM', type=str, nargs=3, default=[-1020, 180, 25],
     help="Custom params for GLDM")
    parser.add_argument('--shape3D_params', action='store', dest='shape3D', type=str, nargs=3, default=[-1020, 180, 25],
     help="Custom params for shape3D")
    args = parser.parse_args()

    print("Args parsed")

   
    loader = DicomLoader(ip_add=args.ip, port=args.port, aetitle=args.aetitle,
                                patient_id=args.patientID, study_id=args.studyUID, 
                                series_id=args.seriesUID, output_path=args.base_dir)
       
    if args.from_pacs:
        loader.download()
        print("DICOM series correctly downloaded")

        args.base_dir = os.path.join(args.base_dir, args.patientID)

    
    parts = ['bilat']
    parts += ['left', 'right', 'upper', 'lower', 'ventral', 'dorsal']

    if args.subroi:
        parts += ['upper_ventral', 'upper_dorsal', 'lower_ventral', 'lower_dorsal']

    if not os.path.isdir(args.output_dir):
        os.mkdir(args.output_dir)

    if not args.skipnifti:
        nif = Niftizator(base_dir=args.base_dir, target_dir_name=args.target_dir, single_mode=args.single)
        try:
            nif.run()
        except TraitError:
            print("###############################\n")
            print("You probably selected the wrong Single/Multiple mode!")
            print("Or maybe you inserted a wrong input path. Try again\n")
            print(f"path(s) to dcm files: {nif.ct_paths}")
            print(f"Base directory: {nif.base_dir}")
            print("###############################")

            return
    else:
        print("Loading pre existing CT.nii")


    rescale = Rescaler(base_dir=args.base_dir, single_mode=args.single,  iso_vox_dim=args.ivd, slice_thk=args.st)    
    if not args.skiprescaling3mm:
        rescale.run_Xmm(args.st)
    else:
        print(f"Loading pre existing *_{args.st}mm.nii")

    if not args.skipmask:
        mask = MaskCreator(base_dir=args.base_dir, single_mode=args.single, st=args.st, ivd=args.ivd)
        mask.run()
    else:
        print(f"Loading pre-existing mask_R231CW_{args.st:.0f}mm.nii")

    if not args.skiprescalingiso:
        try:
            rescale.run_iso()
        except FileNotFoundError as e:
            print(e)
            print("Terminating the program")
            return
    else:
        print(f"Loading pre esisting *_ISO_{args.ivd}.nii")
    
    try:
        print("Making subROI masks...")
        rescale.make_upper_mask()
        rescale.make_ventral_mask()
        rescale.make_mixed_mask()
    except FileNotFoundError as ex:
        print(ex)
        print("Some files were not found. Terminating the program")
        return

    extractor = FeaturesExtractor(
                    base_dir=args.base_dir, single_mode = args.single, output_dir=args.output_dir,
                    ivd = args.ivd, maskname= f"mask_R231CW_ISO_{args.ivd}_bilat",
                    glcm_p=args.GLCM, glszm_p=args.GLSZM,
                    glrlm_p=args.GLRLM, ngtdm_p=args.NGTDM,
                    gldm_p=args.GLDM, shape3d_p=args.shape3D)

    if not args.radqct:
        extractor.run()
        print("Evaluating COVID probability...")
        model_ev = ModelEvaluator(features_df= pd.read_csv(
                            os.path.join(args.output_dir, 'radiomic_features.csv'), sep='\t'),
                          model_path= args.model,
                          out_path=os.path.join(args.output_dir, EVAL_FILE_NAME))

        model_ev.preprocess()
        model_ev.run()

        qct = QCT(base_dir=args.base_dir, parts=parts, single_mode=args.single,
            out_dir=args.output_dir, st=args.st)
        qct.run()
    else:
        print("Skipping QCT and radiomic analysis")

    pdf = PDFHandler(base_dir=args.base_dir,
                     dcm_dir=args.target_dir,
                     data_ref=pd.read_csv(os.path.join(args.output_dir, 'evaluation_results.csv'), sep='\t'),
                     data_clinical=pd.read_csv(os.path.join(args.output_dir, 'clinical_features.csv'), sep='\t'),
                     out_dir=args.output_dir,
                     parts=parts,
                     st=args.st,
                     ivd=args.ivd,
                     single_mode=args.single,
                     data_rad=pd.read_csv(os.path.join(args.output_dir, 'radiomic_total.csv'), sep='\t'),
                     data_rad_sel=pd.read_csv(os.path.join(args.output_dir, 'radiomic_selected.csv'), sep=','),
                     tag = args.tag)

    if not args.skippdf:  
        pdf.run()
        encapsulated_today = pdf.encapsulate()

    if args.to_pacs:
        loader.upload(encapsulated_today)
        print("Report uploaded on PACS")

    if args.automatic:
        loader.move_to_analyzed()


    elapsed = time.time() - start
    elaps_fmt = time.strftime("%Mm %Ss", time.gmtime(elapsed))
    print(f"\nTime elapsed:  {elaps_fmt}")
    print("Goodbye!")


def print_intro():
    print()
    print("          # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # ")
    print("         #   ____  _       ______    ___   ____    _      _    _   _   _    ____           #")
    print("        #   / ___ | |     |  ___/   /   | |  _  \ | |    | |  | | | \ | |  / ____|          #")
    print("       #   | |    | |     | |__    / /| | | |_| | | |    | |  | | |  \| | | | ___            #")
    print("      #    | |    | |     |  _/   / / | | | |__ / | |    | |  | | | \   | | ||__ |            # ")
    print("     #     | |___ | |___  | |___ / ___  | | | \ \ | |___ | |__| | | |\  | | |__| |           #")
    print("      #     \____ |_____| |_____/_/  |__| |_|  \_||_____| \____/  |_| \_|  \_____|          #")
    print("       #                                                                                   #")
    print("        #             CLinical Extraction And Radiomics on LUNGs (CT)                     #")
    print("         #                                                                               #")
    print("          # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #\n")


if __name__ == '__main__':
    print("Hello world. Please use the command line :]")
