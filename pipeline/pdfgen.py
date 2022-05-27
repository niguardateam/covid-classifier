from ctlibrary import dcmtagreader
import fpdf
from glob import glob
import pandas as pd
import numpy as np
from datetime import datetime
from tqdm import tqdm
import os
import pydicom
from PIL import Image


def one_dicom_slice(dcm_path, k=0.33):
    """
    Reads a directory full of DICOM slices and saves one converted sample image

    :param: dcm_path: path to the directory containing the DICOM slices
    :param: k:  height of the selected slice
    """

    number_of_files = len(os.listdir(dcm_path))
    sample = os.listdir(dcm_path)[int(number_of_files * k)]

    ds = pydicom.dcmread(os.path.join(dcm_path, sample))
    new_image = ds.pixel_array.astype(float)
    scaled_image = (np.maximum(new_image, 0) / new_image.max()) * 255.0
    scaled_image = np.uint8(scaled_image)
    final_image = Image.fromarray(scaled_image)
    final_image.save("sample_temp.png")
    return 



class PDF(fpdf.FPDF):

    def header(self):
        # Logo
        self.image(name='/Users/andreasala/Desktop/Tesi/pipeline/images/logo_nig.jpg', x=None, y=12, w=110,)

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

        self.ln(1)
        self.set_font('Arial', 'B', 15)
        self.cell(180, 70, 'REPORT FISICO', 0, 0, 'C')
        self.ln(1)
        self.cell(190, 80, 'ACQUISIZIONE ED ELABORAZIONE IMMAGINI', 0, 0, 'C')
        self.ln(30)

    def footer(self):
        self.set_y(-40)
        self.cell(50, 10, 'Data', border=1, align='C')
        self.cell(80, 10, 'Esperto in Fisica Medica', border=1, align='C')
        self.cell(50, 10, 'N. Matricola', border=1, align='C')

        self.ln(10)

        self.cell(50, 10, '01/01/01', border=1, align='C')
        self.cell(80, 10, '**NOME ESPERTO**', border=1, align='C')
        self.cell(50, 10, '12345', border=1, align='C')

    def run_single(self, dcm_path, **dcm_args):

        self.add_page()
        self.alias_nb_pages()
        self.set_font('Times', 'B', 12)
        self.ln(1)

        self.cell(0, 40, 'DATI DEL PAZIENTE', )
        self.ln(24)
        self.set_font('Times', '', 12)
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

        self.set_font('Times', 'B', 12)
        self.cell(0, 40, 'DATI DELLO STUDIO', )
        self.ln(24)
        self.set_font('Times', '', 12)
        self.cell(w=70, h=20, txt="Accession number:", border='LT', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['accnumber']}", border='LTR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Struttura richiedente:', border='LR', align='L')
        self.cell(w=100, h=20, txt='Nessuna (uso interno)', border='LR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Data della TAC:', border='BRL', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['ctdate']}", border='BLR', align='L')
        self.ln(8)
        self.set_font('Times', 'B', 12)
        self.cell(0, 40, 'RISULTATI', )
        self.ln(24)
        self.set_font('Times', '', 12)
        self.cell(w=70, h=20, txt="Probabilità COVID:", border='LT', align='L')
        self.cell(w=100, h=20, txt=f"{(100*dcm_args['covid_prob']):.1f}%", border='LTR', align='L')
        self.ln(7)
        self.cell(w=70, h=20, txt='Accuracy algoritmo:', border='BLR', align='L')
        self.cell(w=100, h=20, txt= '**INSERIRE ACCURACY**', border='BLR', align='L')
        output_name = '/Users/andreasala/Desktop/Tesi/pipeline/results/' + dcm_args['accnumber'] + 'COVID_CT.pdf'
       

        # second page with WAVE, dicom slice, other stuff?
        # self.add_page()
        #print(f"File {output_name} written")

        # getting an image in the middle 
        self.add_page()
        one_dicom_slice(dcm_path)
        self.image('sample_temp.png')
        os.remove("sample_temp.png")

        self.output(output_name, 'F')


class PDFHandler():
    def __init__(self, base_dir, dcm_dir, data_ref: pd.DataFrame):
        self.base_dir = base_dir
        self.dcm_dir = dcm_dir
        self.data_ref = data_ref
        self.patient_paths = glob(base_dir + '/*/')
        self.dcm_paths = glob(base_dir + '/*/' + dcm_dir)
    

    def run(self):

        for dcm_path in tqdm(self.dcm_paths, desc="Saving PDF files", colour='BLUE'):
            searchtag = dcmtagreader(dcm_path)

            name = str(searchtag[0x0010, 0x0010].value)
            age  = str(searchtag[0x0010, 0x1010].value)[1:-1]
            sex = searchtag[0x0010, 0x0040].value
            accnumber = searchtag[0x0008, 0x0050].value
            bdate = str(searchtag[0x0010, 0x0030].value)

            ctdate_raw = str(searchtag[0x0008, 0x0022].value)
            ctdate = ctdate_raw[-2:] + '/' + ctdate_raw[4:6] + '/' + ctdate_raw[0:4]

            covid_prob = self.data_ref[self.data_ref['AccessionNumber']==int(accnumber)]['CovidProbability'].values[0]
            
            dicom_args = {
                'name': name,
                'age': age,
                'sex': sex,
                'accnumber': accnumber,
                'bdate': bdate,
                'ctdate': ctdate,
                'covid_prob': covid_prob,
            }

            single_handler = PDF() #this line must stay here to allow header and footer to be created 
            single_handler.run_single(dcm_path, **dicom_args) #this outputs a PDF file


if __name__=='__main__':
    pdf = PDFHandler(base_dir='/Users/andreasala/Desktop/Tesi/data/COVID-NOCOVID',
              dcm_dir='CT/', data_ref=pd.read_csv("/Users/andreasala/Desktop/Tesi/pipeline/results/evaluation_results.csv", sep='\t'))
    pdf.run()