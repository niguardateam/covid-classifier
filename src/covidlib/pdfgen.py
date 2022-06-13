"""Module to generate PDF reports with patient info and clinical results"""

import os
import logging
import pathlib
from glob import glob
import pandas as pd
import numpy as np
import scipy
import imageio
from PIL import Image
import SimpleITK as sitk
from tqdm import tqdm
import fpdf
import pydicom
import covidlib


logger = logging.getLogger('imageio')
logger.setLevel('ERROR')



def make_nii_slices(ct_scan, mask):
    """
    Takes .nii paths for ct and mask, return a slice in the middle
    """
    image, mask = sitk.ReadImage(ct_scan), sitk.ReadImage(mask)
    img_arr = np.flip(sitk.GetArrayFromImage(image),axis=0)
    msk_arr = 240*np.flip(sitk.GetArrayFromImage(mask), axis=0)
    height = np.argmax([np.sum(sLice) for sLice in msk_arr])

    i_slice, m_slice = np.flipud(img_arr[height]), np.flipud(msk_arr[height])
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


    def run_single(self, nii, mask, out_name, **dcm_args,):
        """Make body for one PDF report"""

        try:
            date = dcm_args['bdate'] 
            fmt_date = date[6:] + '/' + date[4:6] + '/' + date[0:4]
        except IndexError:
            fmt_date = dcm_args['bdate']

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
        self.cell(w=100, h=20, txt=f"{fmt_date}", border='LR', align='L')
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
        self.cell(w=100, h=20, txt='**Inserire struttura**', border='LR', align='L')
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

        self.add_page()

        self.ln(5)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'FEATURES CLINICHE - POLMONE BILATERALE')
        self.ln(24)
        self.set_font('Arial', '', 12)
        self.cell(w=70, h=20, txt="Volume polmonare (cc):", border='LT', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['volume']:.1f}", border='LTR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Media e deviazione standard:', border='LR', align='L')
        self.cell(w=100, h=20, txt=f"""{dcm_args['mean']:.1f},
            {dcm_args['stddev']:.1f}""", border='LR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Percentili:', border='RL', align='L')
        self.cell(w=100, h=20, txt=f"""25: {dcm_args['perc25']:.1f},  50: {
            dcm_args['perc50']:.1f},   75: {dcm_args['perc75']:.1f},  90: {
            dcm_args['perc90']:.1f},""", border='LR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='WAVE,  WAVE.th:', border='BRL', align='L')
        self.cell(w=100, h=20, txt=f"""{dcm_args['wave']:.3f},
            {dcm_args['waveth']:.3f}""", border='LRB', align='L')
        self.ln(6)

        self.image(os.path.join('./results' ,'histograms',  dcm_args['accnumber'] + '_hist_bilat.png'), 40, 85, 120, 90)
        make_nii_slices(nii, mask)
        self.image('img_temp.png', 20, 180 , 80, 80)
        self.image('msk_temp.png', 110, 180 , 80, 80)

        self.add_page()

        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'FEATURES CLINICHE - POLMONE SINISTRO')
        self.ln(24)
        self.set_font('Arial', '', 12)
        self.cell(w=70, h=20, txt="Volume polmonare (cc):", border='LT', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['volumeL']:.1f}", border='LTR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Media e deviazione standard:', border='LR', align='L')
        self.cell(w=100, h=20, txt=f"""{dcm_args['meanL']:.1f},
            {dcm_args['stddevL']:.1f}""", border='LR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Percentili:', border='RL', align='L')
        self.cell(w=100, h=20, txt=f"""25: {dcm_args['perc25L']:.1f},  50: {
            dcm_args['perc50L']:.1f},   75: {dcm_args['perc75L']:.1f},  90: {
            dcm_args['perc90L']:.1f},""", border='LR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='WAVE,  WAVE.th:', border='BRL', align='L')
        self.cell(w=100, h=20, txt=f"""{dcm_args['waveL']:.3f},
            {dcm_args['wavethL']:.3f}""", border='LRB', align='L')
        self.ln(6)

        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'FEATURES CLINICHE - POLMONE DESTRO')
        self.ln(24)
        self.set_font('Arial', '', 12)
        self.cell(w=70, h=20, txt="Volume polmonare (cc):", border='LT', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['volumeR']:.1f}", border='LTR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Media e deviazione standard:', border='LR', align='L')
        self.cell(w=100, h=20, txt=f"""{dcm_args['meanR']:.1f},
            {dcm_args['stddevR']:.1f}""", border='LR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Percentili:', border='RL', align='L')
        self.cell(w=100, h=20, txt=f"""25: {dcm_args['perc25R']:.1f},  50: {
            dcm_args['perc50R']:.1f},   75: {dcm_args['perc75R']:.1f},  90: {
            dcm_args['perc90R']:.1f},""", border='LR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='WAVE,  WAVE.th:', border='BRL', align='L')
        self.cell(w=100, h=20, txt=f"""{dcm_args['waveR']:.3f},
            {dcm_args['wavethR']:.3f}""", border='LRB', align='L')
        self.ln(6)

        self.image(os.path.join('./results' ,'histograms',  dcm_args['accnumber'] + '_hist_left.png'), 15, 160, 90, 70)
        self.image(os.path.join('./results' ,'histograms',  dcm_args['accnumber'] + '_hist_right.png'), 112, 160, 00, 70)



        os.remove("img_temp.png")
        os.remove("msk_temp.png")

        self.make_footer()
        self.output(out_name, 'F')


class PDFHandler():
    """Handle multiple PDF reports generation"""

    def __init__(self, base_dir, dcm_dir, data_ref, data_bilat, data_left, data_right, out_dir):
        self.base_dir = base_dir
        self.dcm_dir = dcm_dir
        self.patient_paths = glob(base_dir + '/*/')
        self.dcm_paths = glob(base_dir + '/*/' + self.dcm_dir + '/')
        self.nii_paths = glob(base_dir + '/*/CT_3mm.nii')
        self.mask_bilat_paths = glob(base_dir + '/*/mask_R231CW_3mm_bilat.nii')
        self.mask_paths = glob(base_dir + '/*/mask_R231CW_3mm.nii')
        self.out_dir = out_dir

        self.data_bilat = pd.merge(data_ref, data_bilat, on='AccessionNumber', how='inner')
        self.data_left = pd.merge(data_ref, data_left, on='AccessionNumber', how='inner')
        self.data_right = pd.merge(data_ref, data_right, on='AccessionNumber', how='inner')
        self.out_pdf_names = []


    def run(self):
        """Execute the PDF generation"""

        for dcm_path, niipath, maskpath, maskbilat in tqdm(zip(self.dcm_paths,
            self.nii_paths, self.mask_paths, self.mask_bilat_paths),
            total=len(self.nii_paths),desc="Saving PDF files", colour='BLUE'):

            searchtag = covidlib.ctlibrary.dcmtagreader(dcm_path)

            name = str(searchtag[0x0010, 0x0010].value)
            age  = str(searchtag[0x0010, 0x1010].value)[1:-1]
            sex = searchtag[0x0010, 0x0040].value
            accnumber = searchtag[0x0008, 0x0050].value
            bdate = str(searchtag[0x0010, 0x0030].value)

            ctdate_raw = str(searchtag[0x0008, 0x0022].value)
            ctdate = ctdate_raw[-2:] + '/' + ctdate_raw[4:6] + '/' + ctdate_raw[0:4]

            row = self.data_bilat[self.data_bilat['AccessionNumber']==int(accnumber)]
            rowL = self.data_left[self.data_left['AccessionNumber']==int(accnumber)]
            rowR = self.data_right[self.data_right['AccessionNumber']==int(accnumber)]

            covid_prob = row['CovidProbability'].values[0]
            volume = row['volume'].values[0]
            mean, std = row['mean'].values[0], row['stddev'].values[0]
            perc25, perc50 = row['perc25'].values[0], row['perc50'].values[0]
            perc75, perc90 = row['perc75'].values[0], row['perc90'].values[0]
            skew, kurt = row['skewness'].values[0], row['kurtosis'].values[0]
            wave, waveth = row['wave'].values[0], row['waveth'].values[0]

            volumeL, meanL = rowL['volume'].values[0], rowL['mean'].values[0]
            stdL    = rowL['stddev'].values[0]
            perc25L, perc50L = rowL['perc25'].values[0], rowL['perc50'].values[0]
            perc75L, perc90L = rowL['perc75'].values[0], rowL['perc90'].values[0]
            skewL,   kurtL   = rowL['skewness'].values[0], rowL['kurtosis'].values[0]
            waveL,   wavethL = rowL['wave'].values[0], rowL['waveth'].values[0]

            volumeR = rowR['volume'].values[0]
            meanR   = rowR['mean'].values[0]
            stdR    = rowR['stddev'].values[0]
            perc25R = rowR['perc25'].values[0]
            perc50R = rowR['perc50'].values[0]
            perc75R = rowR['perc75'].values[0]
            perc90R = rowR['perc90'].values[0]
            skewR   = rowR['skewness'].values[0]
            kurtR   = rowR['kurtosis'].values[0]
            waveR   = rowR['wave'].values[0]
            wavethR = rowR['waveth'].values[0]

            dicom_args = {
                'name': name, 'age': age, 'sex': sex, 'accnumber': accnumber,
                'bdate': bdate, 'ctdate': ctdate, 'covid_prob': covid_prob,

                'volume': volume, 'mean': mean, 'stddev': std,
                'perc25': perc25,'perc50': perc50,'perc75': perc75,'perc90': perc90,
                'skewness': skew,'kurtosis': kurt,'wave': wave,'waveth': waveth,

                'volumeL': volumeL, 'meanL': meanL, 'stddevL': stdL,
                'perc25L': perc25L,'perc50L': perc50L,'perc75L': perc75L,'perc90L': perc90L,
                'skewnessL': skewL,'kurtosisL': kurtL,'waveL': waveL,'wavethL': wavethL,

                'volumeR': volumeR, 'meanR': meanR, 'stddevR': stdR,
                'perc25R': perc25R,'perc50R': perc50R,'perc75R': perc75R,'perc90R': perc90R,
                'skewnessR': skewR,'kurtosisR': kurtR,'waveR': waveR,'wavethR': wavethR
            }

            out_name =  accnumber + 'COVID_CT.pdf'
            out_name_total = './results/reports/' + out_name
            self.out_pdf_names.append(out_name)

            single_handler = PDF()
            single_handler.run_single(nii=niipath,
                                      mask=maskpath,
                                      out_name=out_name_total,
                                      **dicom_args,
                                      )


    def encapsulate(self,):
        """Encapsulate dicom fields in a pdf file.
        Dicom fileds are taken from the first file in the series dir.
        """
        for dcm_path, pdf_name in zip(self.dcm_paths, self.out_pdf_names):

            dcm_ref = os.path.join(dcm_path ,os.listdir(dcm_path)[0])
            dcm_ref = (os.path.abspath(dcm_ref))
            ds = pydicom.dcmread(dcm_ref)

            if pdf_name[-4:]=='.pdf':
                pdf_name = pdf_name[:-4]

            series_uid = ds[0x0020, 0x000E].value
            accnum = ds[0x0008, 0x0050].value
            study_desc = ds[0x0008, 0x1030].value

            new_uid = series_uid[:-3] + str(np.random.randint(100,999))

            if not os.path.isdir(os.path.join(self.out_dir, 'encapsulated')):
                os.mkdir(os.path.join(self.out_dir, 'encapsulated'))

            cmd = f"""pdf2dcm {os.path.join(self.out_dir, 'reports' ,pdf_name)}.pdf """+\
                  f"""{os.path.join(self.out_dir, 'encapsulated', pdf_name)}.dcm +se {dcm_ref} """ +\
                  f"""-k "SeriesNumber=901" -k "SeriesDescription=Analisi Fisica" """ +\
                  f""" -k "SeriesInstanceUID={new_uid}" -k "AccessionNumber={accnum}" """ +\
                  f"""  -k "Modality=SC" -k "InstanceNumber=1" -k  "StudyDescription={study_desc}" """
            os.system(cmd)


if __name__=='__main__':
    pdf = PDFHandler(
        base_dir='/Users/andreasala/Desktop/Tesi/data/COVID-NOCOVID',
        dcm_dir='CT/',
        data_ref = pd.read_csv("./results/evaluation_results.csv",sep='\t'),
        data_clinical = pd.read_csv("./results/clinical_features.csv", sep='\t'))

    pdf.run()
    pdf.encapsulate()
