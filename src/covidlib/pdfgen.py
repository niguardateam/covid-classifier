"""Module to generate PDF reports with patient info and clinical results"""

import os
import logging
import pathlib
from glob import glob
import pandas as pd
import numpy as np
import imageio
from PIL import Image
import SimpleITK as sitk
from tqdm import tqdm
import fpdf
import pydicom
import covidlib


logger = logging.getLogger('imageio')
logger.setLevel('ERROR')


def one_dicom_slice(dcm_path, k=0.33):
    """
    Reads a directory full of DICOM slices and saves one converted sample image

    :param: dcm_path: path to the directory containing the DICOM slices
    :param: k:  height of the selected slice
    """
    number_of_files = len(os.listdir(dcm_path))
    sample = os.listdir(dcm_path)[int(number_of_files * k)]

    new_image = pydicom.dcmread(os.path.join(dcm_path, sample)).pixel_array.astype(float)
    scaled_image = (np.maximum(new_image, 0) / new_image.max()) * 255.0
    scaled_image = np.uint8(scaled_image)
    final_image = Image.fromarray(scaled_image)
    final_image.save("sample_temp.png")


def make_nii_slices(ct_scan, mask):
    """
    Takes .nii paths for ct and mask, return a slice in the middle
    """
    image, mask = sitk.ReadImage(ct_scan), sitk.ReadImage(mask)
    img_arr, msk_arr = sitk.GetArrayFromImage(image), 240*sitk.GetArrayFromImage(mask)

    height = np.argmax([np.sum(sLice) for sLice in msk_arr])

    i_slice, m_slice = img_arr[height], msk_arr[height]
    imageio.imwrite('./img_temp.png', i_slice)
    imageio.imwrite('./msk_temp.png', m_slice)



class PDF(fpdf.FPDF):
    """Class to generate PDF reports with analysis results"""

    def make_header(self):
        """Make PDF report header"""
        # Logo
        image_path = os.path.join(pathlib.Path(__file__).parent.resolve(), 'images/logo_nig.jpg')
        self.image(name=image_path, x=None, y=12, w=110,)

        self.set_font('Arial', '', 10)
        self.ln(20)
        self.cell(10, 30, 'DIPARTIMENTO TECNOLOGIE AVANZATE', 0, 0, 'L')
        self.cell(170, 30, 'Piazza Ospedale Maggiore 3', 0, 0, 'R')
        self.ln(6)
        self.cell(10, 30, 'DIAGNOSTICO - TERAPEUTICHE', 0, 0, 'L')
        self.cell(170, 30, '20162 Milano (MI)', 0, 0, 'R')
        self.ln(6)
        self.cell(10, 30, 'Struttura Complessa: Fisica Sanitaria', 0, 0, 'L')
        self.cell(170, 30, 'email: segreteria.fisica@ospedaleniguarda.it', 0, 0, 'R')


    def make_footer(self):
        """Make PDF report footer"""
        self.set_y(-50)
        self.cell(50, 10, 'Data', border=1, align='C')
        self.cell(80, 10, 'Esperto in Fisica Medica', border=1, align='C')
        self.cell(50, 10, 'N. Matricola', border=1, align='C')
        self.ln(10)
        self.cell(50, 10, '01/01/01', border=1, align='C')
        self.cell(80, 10, '**NOME ESPERTO**', border=1, align='C')
        self.cell(50, 10, '12345', border=1, align='C')


    def run_single(self, nii, mask, **dcm_args):
        """Make body for one PDF report"""
        self.add_page()
        self.alias_nb_pages()
        self.make_header()
        self.ln(1)

        self.set_font('Arial', 'B', 15)
        self.cell(180, 70, 'REPORT FISICO', 0, 0, 'C')
        self.ln(1)
        self.cell(190, 80, 'ACQUISIZIONE ED ELABORAZIONE IMMAGINI', 0, 0, 'C')
        self.ln(30)

        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'DATI DEL PAZIENTE', )
        self.ln(24)
        self.set_font('Arial', '', 12)
        self.cell(w=70, h=20, txt="Cognome e nome:", border='LT', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['name']}", border='LTR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Sesso:', border='LR', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['sex']}", border='LR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Data di nascita:', border='RL', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['bdate']}", border='LR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Età:', border='BRL', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['age']}", border='BLR', align='L')
        self.ln(8)

        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'DATI DELLO STUDIO', )
        self.ln(24)
        self.set_font('Arial', '', 12)
        self.cell(w=70, h=20, txt="Accession number:", border='LT', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['accnumber']}", border='LTR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Struttura richiedente:', border='LR', align='L')
        self.cell(w=100, h=20, txt='Nessuna (uso interno)', border='LR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Data della TAC:', border='BRL', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['ctdate']}", border='BLR', align='L')
        self.ln(8)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'RISULTATI', )
        self.ln(24)
        self.set_font('Arial', '', 12)
        self.cell(w=70, h=20, txt="Probabilità COVID:", border='LT', align='L')
        self.cell(w=100, h=20, txt=f"{(100*dcm_args['covid_prob']):.1f}%", border='LTR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Release algoritmo:', border='BLR', align='L')
        self.cell(w=100, h=20, txt= covidlib.__version__, border='BLR', align='L')

        #self.add_page()

        self.ln(5)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'FEATURES CLINICHE')
        self.ln(24)
        self.set_font('Times', '', 12)
        self.cell(w=70, h=20, txt="Volume polmonare (cc):", border='LT', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['volume']:.1f}", border='LTR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Media e deviazione standard:', border='LR', align='L')
        self.cell(w=100, h=20, txt=f"""{dcm_args['mean']:.1f},
            {dcm_args['stddev']:.1f}""", border='LR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Percentili:', border='RL', align='L')
        self.cell(w=100, h=20, txt=f"""25%: {dcm_args['perc25']:.1f},  50%: {
            dcm_args['perc50']:.1f},   75%: {dcm_args['perc75']:.1f},  90%: {
            dcm_args['perc90']:.1f},""", border='LR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='WAVE,  WAVE.th:', border='BRL', align='L')
        self.cell(w=100, h=20, txt=f"""{dcm_args['wave']:.3f},
            {dcm_args['waveth']:.3f}""", border='LRB', align='L')
        self.ln(6)

        self.add_page()

        self.image('./results/histograms/' + dcm_args['accnumber'] + '_hist.png', 40, 10, 140, 90)
        make_nii_slices(nii, mask)
        self.image('img_temp.png', 10, 140 , 80, 80)
        self.image('msk_temp.png', 110, 140 , 80, 80)

        os.remove("img_temp.png")
        os.remove("msk_temp.png")


        self.make_footer()
        output_name = './results/' + dcm_args['accnumber'] + 'COVID_CT.pdf'
        self.output(output_name, 'F')


class PDFHandler(): # pylint: disable=too-few-public-methods
    """Handle multiple PDF reports generation"""

    def __init__(self, base_dir, dcm_dir, data_ref: pd.DataFrame, data_clinical: pd.DataFrame):
        self.base_dir = base_dir
        self.dcm_dir = dcm_dir
        self.patient_paths = glob(base_dir + '/*/')
        self.dcm_paths = glob(base_dir + '/*/' + dcm_dir)
        self.nii_paths = glob(base_dir + '/*/CT_3mm.nii')
        self.mask_paths = glob(base_dir + '/*/mask_R231CW_3mm_bilat.nii')

        self.data = pd.merge(data_ref, data_clinical, on='AccessionNumber', how='inner')


    def run(self): # pylint: disable=too-many-locals
        """Execute the PDF generation"""

        for dcm_path, niipath, maskpath in tqdm(zip(self.dcm_paths,
            self.nii_paths, self.mask_paths), total=len(self.nii_paths),
            desc="Saving PDF files", colour='BLUE'):

            searchtag = covidlib.ctlibrary.dcmtagreader(dcm_path)

            name = str(searchtag[0x0010, 0x0010].value)
            age  = str(searchtag[0x0010, 0x1010].value)[1:-1]
            sex = searchtag[0x0010, 0x0040].value
            accnumber = searchtag[0x0008, 0x0050].value
            bdate = str(searchtag[0x0010, 0x0030].value)

            ctdate_raw = str(searchtag[0x0008, 0x0022].value)
            ctdate = ctdate_raw[-2:] + '/' + ctdate_raw[4:6] + '/' + ctdate_raw[0:4]

            row = self.data[self.data['AccessionNumber']==int(accnumber)]
            covid_prob = row['CovidProbability'].values[0]
            volume = row['volume'].values[0]
            mean = row['mean'].values[0]
            std = row['stddev'].values[0]
            perc25 = row['perc25'].values[0]
            perc50 = row['perc50'].values[0]
            perc75 = row['perc75'].values[0]
            perc90 = row['perc90'].values[0]
            skew = row['skewness'].values[0]
            kurt = row['kurtosis'].values[0]
            wave = row['wave'].values[0]
            waveth = row['waveth'].values[0]


            dicom_args = {
                'name': name,
                'age': age,
                'sex': sex,
                'accnumber': accnumber,
                'bdate': bdate,
                'ctdate': ctdate,
                'covid_prob': covid_prob,
                'volume': volume,
                'mean': mean,
                'stddev': std,
                'perc25': perc25,
                'perc50': perc50,
                'perc75': perc75,
                'perc90': perc90,
                'skewness': skew,
                'kurtosis': kurt,
                'wave': wave,
                'waveth': waveth
            }

            single_handler = PDF()
            single_handler.run_single(nii=niipath,
                                      mask=maskpath,
                                      **dicom_args)

if __name__=='__main__':
    pdf = PDFHandler(
        base_dir='/Users/andreasala/Desktop/Tesi/data/COVID-NOCOVID',
        dcm_dir='CT/',
        data_ref = pd.read_csv("./results/evaluation_results.csv",sep='\t'),
        data_clinical = pd.read_csv("./results/clinical_features.csv", sep='\t'))

    pdf.run()
