"""Module to generate PDF reports with patient info and clinical results"""

from inspect import signature
import os
import logging
import pathlib
from glob import glob
import pandas as pd
import numpy as np
import datetime
import imageio
from PIL import Image
import SimpleITK as sitk
from tqdm import tqdm
import fpdf
import pydicom
import covidlib
from covidlib.ctlibrary import change_keys, dcmtagreader


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
        self.cell(10, 30, 'DIPARTIMENTO DEI SERVIZI', 0, 0, 'L')
        self.cell(170, 30, 'Piazza Ospedale Maggiore 3', 0, 0, 'R')
        self.ln(6)
        self.cell(10, 30, 'Struttura Complessa: Fisica Sanitaria', 0, 0, 'L')
        self.cell(170, 30, '20162 Milano (MI)', 0, 0, 'R')
        self.ln(6)
        self.cell(170, 30, 'email: fisica.diagnostica@ospedaleniguarda.it', 0, 0, 'L')


    def make_footer(self, signature: tuple):
<<<<<<< HEAD
        """Make PDF report footer.
        :param signature: tuple with (NOME, MATRICOLA)"""
=======
        """Make PDF report footer."""
        
>>>>>>> interface
        self.set_y(-50)
        self.cell(50, 10, 'Data', border=1, align='C')
        self.cell(80, 10, 'Esperto in Fisica Medica', border=1, align='C')
        self.cell(50, 10, 'N. Matricola', border=1, align='C')
        self.ln(10)
        self.cell(50, 10, datetime.date.today().strftime("%d/%m/%Y"), border=1, align='C')
        self.cell(80, 10, signature[0], border=1, align='C')
        self.cell(50, 10, signature[1], border=1, align='C')


    def make_table(self, part, dcm_args):
        self.ln(24)
        self.set_font('Arial', '', 12)
        self.cell(w=60, h=12, txt="Volume polmonare (cc):", border=1 , align='L')
        self.cell(w=30, h=12, txt=f"{dcm_args['volume_' + part]:.1f}", border=1, align='C')
        self.ln(12)
        self.cell(w=60, h=12, txt="Media (HU):", border=1 , align='L')
        self.cell(w=30, h=12, txt=f"{dcm_args['mean_' + part]:.1f}", border=1, align='C')
        self.cell(w=60, h=12, txt="Dev. standard (HU):", border=1 , align='L')
        self.cell(w=30, h=12, txt=f"{dcm_args['stddev_' + part]:.1f}", border=1, align='C')
        self.ln(12)
        self.cell(w=60, h=12, txt="25mo percentile (HU):", border=1 , align='L')
        self.cell(w=30, h=12, txt=f"{dcm_args['perc25_' + part]:.1f}", border=1, align='C')
        self.cell(w=60, h=12, txt="50mo percentile (HU):", border=1 , align='L')
        self.cell(w=30, h=12, txt=f"{dcm_args['perc50_' + part]:.1f}", border=1, align='C')
        self.ln(12)
        self.cell(w=60, h=12, txt="75mo percentile (HU):", border=1 , align='L')
        self.cell(w=30, h=12, txt=f"{dcm_args['perc75_' + part]:.1f}", border=1, align='C')
        self.cell(w=60, h=12, txt="90mo percentile (HU):", border=1 , align='L')
        self.cell(w=30, h=12, txt=f"{dcm_args['perc90_' + part]:.1f}", border=1, align='C')
        self.ln(12)
        self.cell(w=60, h=12, txt="WAVE fit:", border=1 , align='L')
        self.cell(w=30, h=12, txt=f"{dcm_args['wave_' + part]:.3f}", border=1, align='C')
        self.cell(w=60, h=12, txt="WAVE.th:", border=1 , align='L')
        self.cell(w=30, h=12, txt=f"{dcm_args['waveth_' + part]:.3f}", border=1, align='C')


<<<<<<< HEAD
    def run_single(self, nii, mask, out_name, signature, **dcm_args):
=======
    def run_single(self, nii, mask, out_name, out_dir, parts, **dcm_args):
>>>>>>> interface
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
        self.cell(180, 70, 'REPORT FISICA SANITARIA', 0, 0, 'C')
        self.ln(1)
        self.cell(190, 80, 'ANALISI QUANTITATIVA CT POLMONE', 0, 0, 'C')
        self.ln(30)

        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'DATI DEL PAZIENTE', )
        self.ln(24)
        self.set_font('Arial', '', 12)
        self.cell(w=80, h=20, txt="Accession number:", border='LT', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['accnumber']}", border='LTR', align='L')
        self.ln(7)
        self.cell(w=80, h=20, txt='Sesso:', border='LR', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['sex']}", border='LR', align='L')
        self.ln(7)
        self.cell(w=80, h=20, txt='Età:', border='RL', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['age']}", border='LR', align='L')
        self.ln(7)
        self.cell(w=80, h=20, txt='Data dello studio CT:', border='RL', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['ctdate']}", border='LR', align='L')
        self.ln(7)
        self.cell(w=80, h=20, txt="Data dell'analisi", border='RL', align='L')
        self.cell(w=100, h=20, txt=datetime.date.today().strftime("%d/%m/%Y"), border='LR', align='L')
        self.ln(7)
        self.cell(w=80, h=20, txt='Descrizione della serie CT:', border='BRL', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['study_dsc']}", border='BLR', align='L')

        self.ln(45)
        make_nii_slices(nii, mask)
        self.image('img_temp.png', 10, 170 , 80, 80)
        self.image('msk_temp.png', 110, 170 , 80, 80)

        self.set_y(-48)
        self.set_font('Arial', '', 10)
        self.cell(w=80, h=10, txt="Sample CT", align='C', border=0)
        self.cell(w=120, h=10, txt="Sample Maschera", align='C', border=0)
<<<<<<< HEAD

        self.add_page()
        self.ln(2)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'FEATURES CLINICHE - POLMONE BILATERALE')
        self.make_table('bilat', dcm_args) 
        self.image(os.path.join('./results' ,'histograms',  dcm_args['accnumber'] + '_hist_bilat.png'), 40, 135, 140, 105)

        self.add_page()
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'FEATURES CLINICHE - POLMONE SINISTRO')
        self.make_table('left', dcm_args)
        self.ln(2)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'FEATURES CLINICHE - POLMONE DESTRO')
        self.make_table('right', dcm_args)
        self.image(os.path.join('./results' ,'histograms',  dcm_args['accnumber'] + '_hist_left.png'),   10, 185, 90, 69)
        self.image(os.path.join('./results' ,'histograms',  dcm_args['accnumber'] + '_hist_right.png'), 110, 185, 90, 69)
        
        self.add_page()
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'FEATURES CLINICHE - POLMONE SUPERIORE')
        self.make_table('upper', dcm_args)
        self.ln(2)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'FEATURES CLINICHE - POLMONE INFERIORE')
        self.make_table('lower', dcm_args)
        self.image(os.path.join('./results' ,'histograms',  dcm_args['accnumber'] + '_hist_upper.png'), 10, 190 , 90, 69)
        self.image(os.path.join('./results' ,'histograms',  dcm_args['accnumber'] + '_hist_lower.png'), 110, 190, 90, 69)

        self.add_page()
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'FEATURES CLINICHE - POLMONE VENTRALE')
        self.make_table('ventral', dcm_args)
        self.ln(2)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'FEATURES CLINICHE - POLMONE DORSALE')
        self.make_table('dorsal', dcm_args)
        self.image(os.path.join('./results' ,'histograms',  dcm_args['accnumber'] + '_hist_ventral.png'), 10, 190 , 90, 69)
        self.image(os.path.join('./results' ,'histograms',  dcm_args['accnumber'] + '_hist_dorsal.png'), 110, 190, 90, 69)


        self.add_page()
        self.ln(8)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'ALTRI RISULTATI', )
        self.ln(32)
        self.set_font('Arial', '', 12)

=======

        self.add_page()
        self.ln(2)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'FEATURES CLINICHE - POLMONE BILATERALE')
        self.make_table('bilat', dcm_args) 
        self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_bilat.png'), 40, 135, 140, 105)

        if 'left' in parts:
            self.add_page()
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'FEATURES CLINICHE - POLMONE SINISTRO')
            self.make_table('left', dcm_args)
            self.ln(2)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'FEATURES CLINICHE - POLMONE DESTRO')
            self.make_table('right', dcm_args)
            self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_left.png'),   10, 185, 90, 69)
            self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_right.png'), 110, 185, 90, 69)

        if 'upper' in parts:
            self.add_page()
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'FEATURES CLINICHE - POLMONE SUPERIORE')
            self.make_table('upper', dcm_args)
            self.ln(2)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'FEATURES CLINICHE - POLMONE INFERIORE')
            self.make_table('lower', dcm_args)
            self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_upper.png'), 10, 190 , 90, 69)
            self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_lower.png'), 110, 190, 90, 69)

        if 'ventral' in parts:
            self.add_page()
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'FEATURES CLINICHE - POLMONE VENTRALE')
            self.make_table('ventral', dcm_args)
            self.ln(2)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'FEATURES CLINICHE - POLMONE DORSALE')
            self.make_table('dorsal', dcm_args)
            self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_ventral.png'), 10, 190 , 90, 69)
            self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_dorsal.png'), 110, 190, 90, 69)


        self.add_page()
        self.ln(8)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'ALTRI RISULTATI', )
        self.ln(32)
        self.set_font('Arial', '', 12)

>>>>>>> interface
        long_txt = f"""La TAC polmonare è stata sottoposta ad un'analisi quantitativa""" +\
        f""" di alcune features radiomiche tramite una rete neurale allenata per distinguere""" +\
        f""" i casi di polmonite da COVID-19 da altre polmoniti virali (versione {covidlib.__version__})."""+\
        f"""Tale classificatore ha indicato una probabilità del {100*dcm_args['covid_prob']:.1f}%""" +\
        f""" di polmonite originata da COVID-19. È opportuno notare che, in fase di allenamento,"""+\
        f""" l'algoritmo ha classificato correttamente circa l'80% delle TAC polmonari."""
        self.multi_cell(w=0, h=10, txt=long_txt, border=1, align='L')
<<<<<<< HEAD
        # self.cell(w=100, h=20, txt="Indice di probabilità COVID vs altra polmonite virale:", border='LT', align='L')
        # self.cell(w=70, h=20, txt=f"{(100*dcm_args['covid_prob']):.1f}%", border='LTR', align='L')
        # self.ln(7)
        # self.cell(w=100, h=20, txt='Release:', border='BLR', align='L')
        # self.cell(w=70, h=20, txt= covidlib.__version__, border='BLR', align='L')
=======
>>>>>>> interface

        self.output(out_name, 'F')
        os.remove("img_temp.png")
        os.remove("msk_temp.png")


class PDFHandler():
    """Handle multiple PDF reports generation"""

    def __init__(self, base_dir, dcm_dir, data_ref, out_dir,
<<<<<<< HEAD
                 data_clinical: pd.DataFrame, signature=("NOME ESPERTO", "12345")):
=======
                 data_clinical: pd.DataFrame, parts):
>>>>>>> interface
        self.base_dir = base_dir
        self.dcm_dir = dcm_dir
        self.patient_paths = glob(base_dir + '/*/')
        self.dcm_paths = glob(base_dir + '/*/' + self.dcm_dir + '/')
        self.nii_paths = glob(base_dir + '/*/CT_3mm.nii')
        self.mask_bilat_paths = glob(base_dir + '/*/mask_R231CW_3mm_bilat.nii')
        self.mask_paths = glob(base_dir + '/*/mask_R231CW_3mm.nii')
        self.out_dir = out_dir
<<<<<<< HEAD
=======
        self.parts = parts
>>>>>>> interface
        self.signature = signature

        self.data_clinical = data_clinical
        self.data = pd.merge(data_ref, data_clinical, on='AccessionNumber', how='inner')
        self.out_pdf_names = []


    def run(self):
        """Execute the PDF generation"""

        for dcm_path, niipath, maskpath in tqdm(zip(
            self.dcm_paths,self.nii_paths, self.mask_paths),
            total=len(self.nii_paths),desc="Saving PDF files", colour='BLUE'):

            searchtag = dcmtagreader(dcm_path)

            name = str(searchtag[0x0010, 0x0010].value)
            age  = str(searchtag[0x0010, 0x1010].value)[1:-1]
            sex = searchtag[0x0010, 0x0040].value
            accnumber = searchtag[0x0008, 0x0050].value
            bdate = str(searchtag[0x0010, 0x0030].value)
            study_dsc = str(searchtag[0x0008, 0x103e].value)

            ctdate_raw = str(searchtag[0x0008, 0x0022].value)
            ctdate = ctdate_raw[-2:] + '/' + ctdate_raw[4:6] + '/' + ctdate_raw[0:4]

            dicom_args = { 'name': name, 'age': age, 'sex': sex, 'accnumber': accnumber,
                'bdate': bdate, 'ctdate': ctdate, 'study_dsc': study_dsc}
<<<<<<< HEAD

            for part in ['bilat', 'left', 'right', 'upper', 'lower', 'ventral', 'dorsal']:

=======

            for part in self.parts:

>>>>>>> interface
                data_part = self.data[self.data['Region'] == part]

                row = data_part[data_part['AccessionNumber']==int(accnumber)]

                covid_prob = row['CovidProbability'].values[0]
                volume = row['volume'].values[0]
                mean, std = row['mean'].values[0], row['stddev'].values[0]
                perc25, perc50 = row['perc25'].values[0], row['perc50'].values[0]
                perc75, perc90 = row['perc75'].values[0], row['perc90'].values[0]
                skew, kurt = row['skewness'].values[0], row['kurtosis'].values[0]
                wave, waveth = row['wave'].values[0], row['waveth'].values[0]

                dicom_args_tmp = change_keys( {
                'volume': volume, 'mean': mean, 'stddev': std,
                'perc25': perc25,'perc50': perc50,'perc75': perc75,'perc90': perc90,
                'skewness': skew,'kurtosis': kurt,'wave': wave,'waveth': waveth,
                 }, part)

                dicom_args.update(dicom_args_tmp)
                dicom_args.update({'covid_prob': covid_prob})
            
            out_name =  accnumber + 'COVID_CT.pdf'
<<<<<<< HEAD
            out_name_total = './results/reports/' + out_name
=======
            out_name_total = os.path.join(self.out_dir,'reports' , out_name)
>>>>>>> interface
            self.out_pdf_names.append(out_name)

            single_handler = PDF()
            single_handler.run_single(nii=niipath,
                                      mask=maskpath,
                                      out_name=out_name_total,
                                      signature=self.signature,
<<<<<<< HEAD
=======
                                      out_dir=self.out_dir,
                                      parts = self.parts,
>>>>>>> interface
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
