"""Module to define geomtry and graphics
of a pdf report built with pyFPDF"""

import os
import pathlib
import datetime
import numpy as np
import fpdf

from PIL import Image, ImageEnhance
import SimpleITK as sitk
import imageio


def make_nii_slices(ct_scan, mask):
    """
    Takes .nii paths for ct and mask, return a slice in the middle
    """
    image, mask = sitk.ReadImage(ct_scan, sitk.sitkInt32), sitk.ReadImage(mask, sitk.sitkInt32)

    mask_rgb       = sitk.ScalarToRGBColormap(mask)
    image_rgb         = sitk.ScalarToRGBColormap(image)
    image_rgb_array   = sitk.GetArrayFromImage(image_rgb)
    mask_rgb_array = sitk.GetArrayFromImage(mask_rgb)

    red_only = mask_rgb_array[:,:,:,0]
    empty_channel = np.zeros(red_only.shape)
    red_only_rgb = np.stack([red_only, empty_channel, empty_channel], axis=3)

    tot_array = image_rgb_array//2 + red_only_rgb//4
    tot_array[tot_array > 255] = 255 #clamping
    n_slices = len(tot_array)
    step = n_slices//12

    sample_slices = tot_array[10:-1:step,:,:,:].astype(np.uint8)

    for i in range(min(len(sample_slices), 12)):
        imageio.imwrite(f"./slice_{i}.png", np.fliplr(np.flipud(sample_slices[i])))
        img = Image.open(f"./slice_{i}.png")

        enhancer = ImageEnhance.Brightness(img)
        factor = 2
        im_output = enhancer.enhance(factor)
        im_output.save(f"./slice_{i}.png")

    return len(sample_slices)


class PDF(fpdf.FPDF):
    """Class to generate PDF reports with analysis results"""

    def make_header(self):
        """Make PDF report header"""
        # Logo
        image_path = os.path.join(pathlib.Path(__file__).parent.resolve(), 'images/logo_nig.jpg')
        self.image(name=image_path, x=None, y=12, w=100,)

        logo_path = os.path.join(pathlib.Path(__file__).parent.resolve(), 'images/logo_sub.png')
        self.image(logo_path, x=120, y=12, w=80,)

        self.set_font('Arial', '', 10)
        self.ln(10)
        self.cell(10, 30, 'DIPARTIMENTO DEI SERVIZI', 0, 0, 'L')
        self.cell(170, 30, 'Piazza Ospedale Maggiore 3', 0, 0, 'R')
        self.ln(6)
        self.cell(10, 30, 'Struttura Complessa: Fisica Sanitaria', 0, 0, 'L')
        self.cell(170, 30, '20162 Milano (MI)', 0, 0, 'R')
        self.ln(6)
        self.cell(170, 30, 'email: fisica.diagnostica@ospedaleniguarda.it', 0, 0, 'L')


    def footer(self):
        # Go to 1.5 cm from bottom
        self.set_y(-15)
        # Select Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Print centered page number
        self.cell(0, 10, 'Page %s' % self.page_no(), 0, 0, 'C')


    def make_table(self, part, dcm_args):

        self.ln(24)
        self.set_font('Arial', '', 12)
        self.cell(w=62, h=12, txt="Lung volume (cc):", border=1 , align='L')
        self.cell(w=31, h=12, txt=f"{dcm_args['volume_' + part]:.0f}", border=1, align='C')
        self.ln(12)
        self.cell(w=62, h=12, txt="Mean HU:", border=1 , align='L')
        self.cell(w=31, h=12, txt=f"{dcm_args['mean_' + part]:.0f}", border=1, align='C')
        self.cell(w=66, h=12, txt="Std dev HU:", border=1 , align='L')
        self.cell(w=27, h=12, txt=f"{dcm_args['stddev_' + part]:.0f}", border=1, align='C')
        self.ln(12)
        self.cell(w=62, h=12, txt='Overinflated (-1000, -900) HU:', border=1, align='L')
        self.cell(w=31, h=12, txt=f"{(100*dcm_args['overinf_' + part]):.0f}%", border=1, align='C')
        self.cell(w=66, h=12, txt='Normally aerated (-900, -500) HU:', border=1, align='L')
        self.cell(w=27, h=12, txt=f"{(100*dcm_args['norm_aer_' + part]):.0f}%", border=1, align='C')
        self.ln(12)
        self.cell(w=62, h=12, txt='Non aerated (-500, -100) HU:', border=1, align='L')
        self.cell(w=31, h=12, txt=f"{(100*dcm_args['non_aer_' + part]):.0f}%", border=1, align='C')
        self.cell(w=66, h=12, txt='Consolidated (-100, 100) HU:', border=1, align='L')
        self.cell(w=27, h=12, txt=f"{(100*dcm_args['cons_' + part]):.0f}%", border=1, align='C')
        self.ln(12)
        self.cell(w=62, h=12, txt="WAVE fit:", border=1 , align='L')
        self.cell(w=31, h=12, txt=f"{(100*dcm_args['wave_' + part]):.0f}%", border=1, align='C')
        self.cell(w=66, h=12, txt="WAVE.th (-950, -700) HU:", border=1 , align='L')
        self.cell(w=27, h=12, txt=f"{(100*dcm_args['waveth_' + part]):.0f}%", border=1, align='C')
        self.ln(12)
        self.cell(w=62, h=12, txt="Mean ILL HU:", border=1 , align='L')
        self.cell(w=31, h=12, txt=f"{dcm_args['mean_ill_' + part]:.0f}", border=1, align='C', )
        self.cell(w=66, h=12, txt="Std dev ILL HU:", border=1 , align='L')
        self.cell(w=27, h=12, txt=f"{dcm_args['std_ill_' + part]:.0f}", border=1, align='C')
        self.ln(4)


    def run_single(self, nii, mask, out_name, out_dir,
        parts, rsc_params, **dcm_args):

        """Make body for one PDF report"""
        try:
            date = dcm_args['dob']
            dcm_args['dob']  = date[6:] + '/' + date[4:6] + '/' + date[0:4]
        except IndexError:
            pass

        analysis_date = datetime.date.today().strftime("%d/%m/%Y")

        self.add_page()
        self.alias_nb_pages()
        self.make_header()
        self.ln(1)

        self.set_font('Arial', 'B', 15)
        self.cell(180, 70, 'MEDICAL PHYSICS REPORT', 0, 0, 'C')
        self.ln(1)
        self.cell(190, 80, 'QUANTITATIVE ANALYSIS - LUNG CT', 0, 0, 'C')
        self.ln(30)

        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'PATIENT DATA', )
        self.ln(25)
        self.set_font('Arial', '', 12)
        self.cell(w=40,  h=15, txt="Accession number:", border='LT', align='R')
        self.cell(w=40, h=15, txt=f"{dcm_args['accnumber']}", border='TR', align='L')
        self.cell(w=50,  h=15, txt="Analysis date", border='LT', align='R')
        self.cell(w=50, h=15, txt=analysis_date, border='RT', align='L')
        self.ln(7)
        self.cell(w=40,  h=15, txt='Age:', border='L', align='R')
        self.cell(w=40, h=15, txt=f"{dcm_args['age']}", border='R', align='L')
        self.cell(w=50,  h=15, txt='CT study date:', border='L', align='R')
        self.cell(w=50, h=15, txt=f"{dcm_args['ctdate']}", border='R', align='L')
        self.ln(7)
        self.cell(w=40,  h=15, txt='Sex:', border='LB', align='R')
        self.cell(w=40, h=15, txt=f"{dcm_args['sex']}", border='RB', align='L')

        self.cell(w=50,  h=15, txt='CT series description:', border='BL', align='R')
        self.cell(w=50, h=15, txt=f"{dcm_args['series_dsc']}", border='BR', align='L')

        self.ln(20)
        self.set_font('Arial', 'B', 12)
        self.cell(w=60, h=15, txt="DISCLAIMERS", border=0)
        self.ln(20)
        self.set_font('Arial', '', 12)

        long_intro_eng = "This report is automatically generated by CLEARLUNG, a python software " \
            + "developed at the Medical Physics Department at Ospedale Niguarda. The pipeline performs "\
            + "both radiomic and clinical analysis on lung CT scans. Moreover, it is capable of receiving CTs "\
            + "from PACS in real time, and to send results in PDF format onto PACS after the analysis is finished."\
            + f" The clinical analysis was performed on CTs rescaled at {rsc_params[0]} mm, while the radiomic "\
            + f"analysis was performed on CTs rescaled at {rsc_params[1]} mm."

        self.multi_cell(w=0, h=10, txt=long_intro_eng, border=1, align='L')
        self.ln(5)

        long_txt_eng = "The lung CT was subjected to a quantitative analysis of radiomic features with a neural " \
        +"network model trained to distinguish COVID-19 pneumonia cases from other viral pneumonias " \
        +f"(model {dcm_args['model_name']}). The classifier indicated a {100*dcm_args['covid_prob']:.1f}% probability of pneumonia " \
        +"originating from COVID-19. It should be noted that, in the training phase, the algorithm " \
        +"correctly classified about 80% of lung CT scans."

        self.multi_cell(w=0, h=10, txt=long_txt_eng, border=1, align='L')

        self.add_page()
        self.ln(-25)
        self.set_font('Arial', 'B', 15)
        self.cell(180, 70, 'AUTOMATIC SEGMENTATION EVALUATION', 0, 0, 'C')

        slices_to_delete = make_nii_slices(nii, mask)

        xpos = [10, 75, 140] * 4
        y_pos = [35] * 3 + [100] * 3 + [165] * 3 + [230] * 3

        for i in range(min(slices_to_delete, 12)):
            self.image(f"./slice_{i}.png", xpos[i], y_pos[i], 60, 60)

        for i in range(min(slices_to_delete, 12)):
            os.remove(f'./slice_{i}.png')

        self.add_page()
        self.ln(0)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'CLINICAL FEATURES - BILATERAL LUNG')
        self.make_table('bilat', dcm_args)
        self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_bilat.png'), 40, 135, 140, 105)

        if 'left' in parts:
            self.add_page()
            self.ln(-15)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'CLINICAL FEATURES - LEFT LUNG')
            self.make_table('left', dcm_args)
            self.ln(1)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'CLINICAL FEATURES - RIGHT LUNG')
            self.make_table('right', dcm_args)
            self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_left.png'),   10, 195, 90, 69)
            self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_right.png'), 110, 195, 90, 69)

        if 'upper' in parts:
            self.add_page()
            self.ln(-5)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'CLINICAL FEATURES - UPPER LUNG')
            self.make_table('upper', dcm_args)
            self.ln(1)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'CLINICAL FEATURES - LOWER LUNG')
            self.make_table('lower', dcm_args)
            self.image(os.path.join(out_dir ,'histograms',
                dcm_args['accnumber'] + '_hist_upper.png'), 10, 195 , 90, 69)
            self.image(os.path.join(out_dir ,'histograms',
                dcm_args['accnumber'] + '_hist_lower.png'), 110, 195, 90, 69)

        if 'ventral' in parts:
            self.add_page()
            self.ln(-5)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'CLINICAL FEATURES - VENTRAL LUNG')
            self.make_table('ventral', dcm_args)
            self.ln(2)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'CLINICAL FEATURES - DORSAL LUNG')
            self.make_table('dorsal', dcm_args)
            self.image(os.path.join(out_dir ,'histograms',
                dcm_args['accnumber'] + '_hist_ventral.png'), 10, 195 , 90, 69)
            self.image(os.path.join(out_dir ,'histograms',
                dcm_args['accnumber'] + '_hist_dorsal.png'), 110, 195, 90, 69)

        if 'upper_ventral' in parts:
            self.add_page()
            self.ln(-5)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'CLINICAL FEATURES - UPPER VENTRAL LUNG')
            self.make_table('upper_ventral', dcm_args)
            self.ln(2)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'CLINICAL FEATURES - UPPER DORSAL LUNG')
            self.make_table('upper_dorsal', dcm_args)
            self.image(os.path.join(out_dir ,'histograms',
                dcm_args['accnumber'] + '_hist_upper_ventral.png'), 10, 195 , 90, 69)
            self.image(os.path.join(out_dir ,'histograms',
                dcm_args['accnumber'] + '_hist_upper_dorsal.png'), 110, 195, 90, 69)

            self.add_page()
            self.ln(-5)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'CLINICAL FEATURES - LOWER VENTRAL LUNG')
            self.make_table('lower_ventral', dcm_args)
            self.ln(2)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'CLINICAL FEATURES - LOWER DORSAL LUNG')
            self.make_table('lower_dorsal', dcm_args)
            self.image(os.path.join(out_dir ,'histograms',
                dcm_args['accnumber'] + '_hist_lower_ventral.png'), 10, 195 , 90, 69)
            self.image(os.path.join(out_dir ,'histograms',
                dcm_args['accnumber'] + '_hist_lower_dorsal.png'), 110, 195, 90, 69)

        self.output(out_name, 'F')
