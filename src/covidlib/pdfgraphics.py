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

import covidlib


def make_nii_slices(ct_scan, mask):
    """
    Takes .nii paths for ct and mask, return a slice in the middle
    """
    image, mask = sitk.ReadImage(ct_scan, sitk.sitkInt32), sitk.ReadImage(mask, sitk.sitkInt32)
    img_arr = np.flip(sitk.GetArrayFromImage(image),axis=0)
    msk_arr = 240*np.flip(sitk.GetArrayFromImage(mask), axis=0)
    height = np.argmax([np.sum(sLice) for sLice in msk_arr])

    i_slice, m_slice = np.flipud(img_arr[height]), np.flipud(msk_arr[height])
    imageio.imwrite('./img_temp.png', i_slice)
    imageio.imwrite('./msk_temp.png', m_slice)

    contour = mask
    contour_rgb       = sitk.ScalarToRGBColormap(contour)
    image_rgb         = sitk.ScalarToRGBColormap(image)
    image_rgb_array   = sitk.GetArrayFromImage(image_rgb)
    contour_rgb_array = sitk.GetArrayFromImage(contour_rgb)

    red_only = contour_rgb_array[:,:,:,0]
    empty_channel = np.zeros(red_only.shape)
    red_only_rgb = np.stack([red_only, empty_channel, empty_channel], axis=3)

    tot_array = image_rgb_array//2 + red_only_rgb//4
    tot_array[tot_array > 255] = 255 #clamping
    sample_slices = tot_array[20:91:10,:,:,:].astype(np.uint8)

    for i, sample_slice in enumerate(sample_slices):
        imageio.imwrite(f"./slice_{i}.png", np.fliplr(np.flipud(sample_slice )))
        im = Image.open(f"./slice_{i}.png")

        enhancer = ImageEnhance.Brightness(im)
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

    def make_table(self, part, dcm_args):

        self.ln(24)
        self.set_font('Arial', '', 12)
        self.cell(w=62, h=12, txt="Volume polmonare (cc):", border=1 , align='L')
        self.cell(w=31, h=12, txt=f"{dcm_args['volume_' + part]:.1f}", border=1, align='C')
        self.ln(12)
        self.cell(w=62, h=12, txt="Media (HU):", border=1 , align='L')
        self.cell(w=31, h=12, txt=f"{dcm_args['mean_' + part]:.1f}", border=1, align='C')
        self.cell(w=62, h=12, txt="Dev. std (HU):", border=1 , align='L')
        self.cell(w=31, h=12, txt=f"{dcm_args['stddev_' + part]:.0f}", border=1, align='C')
        self.ln(12)
        self.cell(w=62, h=12, txt="Percentili 25º-50º-75º-90º (HU)", border=1, align='L')
        self.cell(w=31, h=12, txt=f"{dcm_args['perc25_' + part]:.1f}", border=1, align='C')
        self.cell(w=31, h=12, txt=f"{dcm_args['perc50_' + part]:.1f}", border=1, align='C')
        self.cell(w=31, h=12, txt=f"{dcm_args['perc75_' + part]:.1f}", border=1, align='C')
        self.cell(w=31, h=12, txt=f"{dcm_args['perc90_' + part]:.1f}", border=1, align='C')
        self.ln(12)
        self.cell(w=62, h=12, txt="WAVE fit:", border=1 , align='L')
        self.cell(w=31, h=12, txt=f"{dcm_args['wave_' + part]}", border=1, align='C')
        self.cell(w=62, h=12, txt="WAVE.th:", border=1 , align='L')
        self.cell(w=31, h=12, txt=f"{dcm_args['waveth_' + part]:.3f}", border=1, align='C')
        self.ln(12)
        self.cell(w=62, h=12, txt="Media ILL (HU):", border=1 , align='L')
        self.cell(w=31, h=12, txt=f"{dcm_args['mean_ill_' + part]:.3f}", border=1, align='C', )
        self.cell(w=62, h=12, txt="Dev. std ILL (HU):", border=1 , align='L')
        self.cell(w=31, h=12, txt=f"{dcm_args['std_ill_' + part]:.0f}", border=1, align='C')
        self.ln(12)
        self.cell(w=62, h=12, txt="Percentili ILL (HU):", border=1, align='L')
        self.cell(w=31, h=12, txt=f"{dcm_args['perc25_ill_' + part]:.1f}", border=1, align='C')
        self.cell(w=31, h=12, txt=f"{dcm_args['perc50_ill_' + part]:.1f}", border=1, align='C')
        self.cell(w=31, h=12, txt=f"{dcm_args['perc75_ill_' + part]:.1f}", border=1, align='C')
        self.cell(w=31, h=12, txt=f"{dcm_args['perc90_ill_' + part]:.1f}", border=1, align='C')


    def run_single(self, nii, mask, out_name, out_dir, parts, **dcm_args):

        """Make body for one PDF report"""
        try:
            date = dcm_args['bdate'] 
            dcm_args['bdate']  = date[6:] + '/' + date[4:6] + '/' + date[0:4]
        except IndexError:
            pass
        try:
            ctdate = dcm_args['ctdate'][6:] + '/' + dcm_args['ctdate'][4:6] + '/' + dcm_args['ctdate'][0:4]
            dcm_args['ctdate'] = ctdate
        except IndexError:
            pass

        analysis_date = datetime.date.today().strftime("%d/%m/%Y")

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
        self.cell(w=100, h=20, txt=analysis_date, border='LR', align='L')
        self.ln(7)
        self.cell(w=80, h=20, txt='Descrizione della serie CT:', border='BRL', align='L')
        self.cell(w=100, h=20, txt=f"{dcm_args['study_dsc']}", border='BLR', align='L')

        self.ln(45)
        slices_to_delete = make_nii_slices(nii, mask)
        self.image('img_temp.png', 10, 170 , 80, 80)
        self.image('msk_temp.png', 110, 170 , 80, 80)

        self.set_y(-48)
        self.set_font('Arial', '', 10)
        self.cell(w=80, h=10, txt="Sample CT", align='C', border=0)
        self.cell(w=120, h=10, txt="Sample Maschera", align='C', border=0)

        self.add_page()
        self.ln(0)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'FEATURES CLINICHE - POLMONE BILATERALE')
        self.make_table('bilat', dcm_args) 
        self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_bilat.png'), 40, 135, 140, 105)

        if 'left' in parts:
            self.add_page()
            self.ln(-15)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'FEATURES CLINICHE - POLMONE SINISTRO')
            self.make_table('left', dcm_args)
            self.ln(1)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'FEATURES CLINICHE - POLMONE DESTRO')
            self.make_table('right', dcm_args)
            self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_left.png'),   10, 195, 90, 69)
            self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_right.png'), 110, 195, 90, 69)

        if 'upper' in parts:
            self.add_page()
            self.ln(-5)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'FEATURES CLINICHE - POLMONE SUPERIORE')
            self.make_table('upper', dcm_args)
            self.ln(1)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'FEATURES CLINICHE - POLMONE INFERIORE')
            self.make_table('lower', dcm_args)
            self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_upper.png'), 10, 195 , 90, 69)
            self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_lower.png'), 110, 195, 90, 69)

        if 'ventral' in parts:
            self.add_page()
            self.ln(-5)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'FEATURES CLINICHE - POLMONE VENTRALE')
            self.make_table('ventral', dcm_args)
            self.ln(2)
            self.set_font('Arial', 'B', 12)
            self.cell(0, 40, 'FEATURES CLINICHE - POLMONE DORSALE')
            self.make_table('dorsal', dcm_args)
            self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_ventral.png'), 10, 195 , 90, 69)
            self.image(os.path.join(out_dir ,'histograms',  dcm_args['accnumber'] + '_hist_dorsal.png'), 110, 195, 90, 69)


        self.add_page()
        self.ln(8)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 40, 'ALTRI RISULTATI', )
        self.ln(32)
        self.set_font('Arial', '', 12)

        long_txt = f"""La TAC polmonare è stata sottoposta ad un'analisi quantitativa""" +\
        f""" di alcune features radiomiche tramite una rete neurale allenata per distinguere""" +\
        f""" i casi di polmonite da COVID-19 da altre polmoniti virali (versione {covidlib.__version__})."""+\
        f"""Tale classificatore ha indicato una probabilità del {100*dcm_args['covid_prob']:.1f}%""" +\
        f""" di polmonite originata da COVID-19. È opportuno notare che, in fase di allenamento,"""+\
        f""" l'algoritmo ha classificato correttamente circa l'80% delle TAC polmonari."""
        self.multi_cell(w=0, h=10, txt=long_txt, border=1, align='L')

        self.add_page()
        self.ln(-25)
        self.set_font('Arial', 'B', 15)
        self.cell(180, 70, 'VALUTAZIONE SEGMENTAZIONE AUTOMATICA', 0, 0, 'C')
        
        xpos = [35, 105] * 4
        y_pos = [35, 35, 100, 100, 165, 165, 230, 230]

        for i in range(min(slices_to_delete, 8)):
            self.image(f"./slice_{i}.png", xpos[i], y_pos[i], 60, 60)

        for i in range(slices_to_delete):
            os.remove(f'./slice_{i}.png')

        self.output(out_name, 'F')
        os.remove("img_temp.png")
        os.remove("msk_temp.png")