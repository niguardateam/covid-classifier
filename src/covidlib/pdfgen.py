"""Module to generate PDF reports with patient info and clinical results"""

from ast import excepthandler
import csv
import os
import sys
import logging

from glob import glob
import pandas as pd
import numpy as np
import datetime

from tqdm import tqdm
import pydicom

from covidlib.ctlibrary import change_keys, dcmtagreader
from covidlib.pdfgraphics import PDF

logger = logging.getLogger('imageio')
logger.setLevel('ERROR')

class PDFHandler():
    """Handle multiple PDF reports generation by cycling over different patients."""

    def __init__(self, base_dir, dcm_dir, data_ref, out_dir,
                 data_clinical, data_rad_sel, data_rad, parts,
                single_mode, st, ivd, tag, history_path):

        self.base_dir = base_dir
        self.dcm_dir = dcm_dir
        self.out_dir = out_dir
        self.parts = parts
        self.data_rad = data_rad
        self.data_rad_sel = data_rad_sel
        self.tag = tag
        self.st = st
        self.ivd = ivd
        self.history_path = history_path

        if single_mode:
            self.patient_paths = [base_dir]
            self.dcm_paths = [os.path.join(base_dir, dcm_dir)]
            self.nii_paths = [os.path.join(base_dir, f'CT_{st:.0f}mm.nii')]
            self.mask_paths = [os.path.join(base_dir, f'mask_R231CW_{st:.0f}mm.nii')]
            self.mask_bilat_paths = [os.path.join(base_dir, f'mask_R231CW_{st:.0f}mm_bilat.nii')]
        else:
            self.patient_paths = glob(base_dir + '/*/')
            self.dcm_paths = glob(base_dir + '/*/' + self.dcm_dir + '/')
            self.nii_paths = glob(base_dir + f'/*/CT_{st:.0f}mm.nii')
            self.mask_bilat_paths = glob(base_dir + f'/*/mask_R231CW_{st:.0f}mm_bilat.nii')
            self.mask_paths = glob(base_dir + f'/*/mask_R231CW_{st:.0f}mm.nii')
        
        self.data_clinical = data_clinical
        self.data = pd.merge(data_ref, data_clinical, on='AccessionNumber', how='inner')
        self.out_pdf_names = []


    def run(self):
        """Execute the PDF generation"""
        
        pbar = tqdm(total=len(self.nii_paths)*len(self.parts),
            desc="Saving PDF files   ", colour='BLUE', leave=True, position=0)

        for dcm_path, niipath, maskbilat in zip(
            self.dcm_paths,self.nii_paths, self.mask_bilat_paths):

            # general features from DICOM file

            try:
                searchtag = dcmtagreader(dcm_path)
                name = str(searchtag[0x0010, 0x0010].value)
                age  = str(searchtag[0x0010, 0x1010].value)[1:-1]
                sex = searchtag[0x0010, 0x0040].value
                accnumber = searchtag[0x0008, 0x0050].value
                dob = str(searchtag[0x0010, 0x0030].value)
                study_dsc = str(searchtag[0x0008, 0x103e].value)
                slicethick = str(searchtag[0x0018, 0x0050].value)
            except:
                name = "Null"
                age = 0
                sex = 'ND'
                accnumber = '-9999'
                dob = 'ND'
                study_dsc = 'ND'
                slicethick = 'ND'
            try:
                body_part = str(searchtag[0x0018, 0x0015].value)
            except KeyError:
                body_part = 'N/A'
            try:
                ctdate_raw = str(searchtag[0x0008, 0x0022].value)
                ctdate = ctdate_raw[-2:] + '/' + ctdate_raw[4:6] + '/' + ctdate_raw[0:4]
            except:
                ctdate = '00/00/0000'
            try:
                dob = dob[-2:] + '/' + dob[4:6] + '/' + dob[0:4]
            except IndexError:
                pass
            
            analysis_date = datetime.date.today().strftime("%d/%m/%Y")

            dicom_args = { 'name': name, 'age': age, 'sex': sex, 'accnumber': accnumber,
                'dob': dob, 'ctdate': ctdate, 'study_dsc': study_dsc, 'analysis_date': analysis_date,
                'slice_thickness': slicethick, 'body_part_examined': body_part}

            # selected radiomic features

            row = self.data_rad[self.data_rad['AccessionNumber']==int(accnumber)]
            selected_rad_args = {col: row[col].values[0] for col in row.columns}
        

            # clinical features

            for part in self.parts:

                data_part = self.data[self.data['Region'] == part]

                #select only the interested row
                row = data_part[data_part['AccessionNumber']==int(accnumber)]

                covid_prob = row['CovidProbability'].values[0]
                volume = row['volume'].values[0]
                mean, std = row['mean'].values[0], row['stddev'].values[0]
                perc25, perc50 = row['perc25'].values[0], row['perc50'].values[0]
                perc75, perc90 = row['perc75'].values[0], row['perc90'].values[0]
                skew, kurt = row['skewness'].values[0], row['kurtosis'].values[0]
                wave, waveth = row['wave'].values[0], row['waveth'].values[0]
                mean_ill, std_ill = row['mean_ill'].values[0], row['std_ill'].values[0]
                perc25_ill, perc50_ill = row['perc25_ill'].values[0], row['perc50_ill'].values[0]
                perc75_ill, perc90_ill = row['perc75_ill'].values[0], row['perc90_ill'].values[0]

                dicom_args_tmp = change_keys( {
                'volume': volume, 'mean': mean, 'stddev': std,
                'perc25': perc25,'perc50': perc50,'perc75': perc75,'perc90': perc90,
                'skewness': skew,'kurtosis': kurt,'wave': wave,'waveth': waveth, 
                'mean_ill': mean_ill, 'std_ill': std_ill,
                'perc25_ill': perc25_ill,'perc50_ill': perc50_ill,
                'perc75_ill': perc75_ill,'perc90_ill': perc90_ill,
                 }, part)

                dicom_args.update(dicom_args_tmp)
                dicom_args.update({'covid_prob': covid_prob})

                pbar.update(1)
            
            out_name =  accnumber + 'COVID_CT.pdf'

            if not os.path.isdir(os.path.join(self.out_dir, 'reports')):
                os.mkdir(os.path.join(self.out_dir, 'reports'))

            out_name_total = os.path.join(self.out_dir,'reports' , out_name)

            self.out_pdf_names.append(out_name)
            rescale_params = (self.st, self.ivd)

            single_handler = PDF()
            single_handler.run_single(nii=niipath,
                                      mask=maskbilat,
                                      out_name=out_name_total,
                                      out_dir=self.out_dir,
                                      parts = self.parts,
                                      rsc_params = rescale_params,
                                      **dicom_args,
                                      )

            special_dcm_args = {key:value for (key,value) in dicom_args.items() if not key[-4:] in ['left', 'ight', 'ower', 'pper', 'rsal', 'tral', 'prob', 'name']}


            #history
            try:
                with open(os.path.join(self.history_path, 'clearlung-history.csv'), 'a') as fwa:
                    writer = csv.writer(fwa)
                    if fwa.tell()==0:
                        writer.writerow(special_dcm_args.keys())
                    writer.writerow(special_dcm_args.values())
                    fwa.close()

                dicom_args.update(selected_rad_args)

                today_raw = datetime.date.today().strftime("%Y%m%d")
                patient_history_dir = os.path.join(self.history_path, 'patients')
                if not os.path.isdir(patient_history_dir):
                    os.mkdir(patient_history_dir)


                with open(os.path.join(patient_history_dir, today_raw + '_' + accnumber + '.csv'), 'w') as csvf:
                    writer = csv.writer(csvf) 
                    writer.writerow(['key', 'value', 'tag'])   
                    for key,value in dicom_args.items():
                        writer.writerow([key, value, self.tag])
                    csvf.close()
            except:
                print("There was an error with history path. This anaylsis will not be written on clearlung-history")
    


    def encapsulate(self,):
        """Encapsulate dicom fields in a pdf file.
        Dicom fields are taken from the first file in the series dir.
        """

        encaps_today = []

        for dcm_path, pdf_name in zip(self.dcm_paths, self.out_pdf_names):

            dcm_ref = os.path.join(dcm_path ,os.listdir(dcm_path)[0])
            dcm_ref = (os.path.abspath(dcm_ref))
            ds = pydicom.dcmread(dcm_ref)

            if pdf_name[-4:]=='.pdf':
                pdf_name = pdf_name[:-4]

            try:
                series_uid = ds[0x0020, 0x000E].value
            except:
                series_uid = '0000000'
            try:
                accnum = ds[0x0008, 0x0050].value
            except:
                accnum = '-9999'
            try:
                study_desc = ds[0x0008, 0x1030].value
            except:
                study_desc = 'ND'
            try:
                patient_id = ds[0x0010,0x0020].value
            except:
                patient_id='0000000000'
            new_uid = series_uid[:-3] + str(np.random.randint(100,999))

            if not os.path.isdir(os.path.join(self.out_dir, 'encapsulated')):
                os.mkdir(os.path.join(self.out_dir, 'encapsulated'))

            cmd = f"""pdf2dcm {os.path.join(self.out_dir, 'reports' ,pdf_name)}.pdf """+\
                  f"""{os.path.join(self.out_dir, 'encapsulated', pdf_name)}.dcm +se {dcm_ref} """ +\
                  f"""-k "SeriesNumber=901" -k "SeriesDescription=Analisi Fisica" """ +\
                  f""" -k "SeriesInstanceUID={new_uid}" -k "AccessionNumber={accnum}" -k "PatientID={patient_id}" """ +\
                  f"""  -k "Modality=SC" -k "InstanceNumber=1" -k  "StudyDescription={study_desc}" """

            os.system(cmd)
            encaps_today.append(os.path.join(self.out_dir, 'encapsulated', pdf_name + '.dcm'))
        return encaps_today

