"""Perform clinical analysis on CT scan
on bilateral, left/right, upper/lower,
ventral/dorsal lungs."""

import glob
import os
import csv
import pathlib
import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import scipy
from scipy import stats
import pandas as pd
from scipy.optimize import curve_fit
from covidlib.ctlibrary import dcmtagreader
from datetime import datetime

# = ['bilat', 'left', 'right','upper', 'lower', 'ventral', 'dorsal']
#analysis_date_for_image = datetime.now().strftime("%Y%m%d_%H%M%S")

def prod(tup1: tuple, tup2:tuple)-> float :
    """
    Scalar product between two tuples
    """
    assert len(tup1) == len(tup2), "Two arrays must be of same size"
    return sum(p*q for p,q in zip(tup1, tup2))

def gauss(x, *p):
    """Gaussian fit function
    Arguments:
        x: np.array type for x axis
        *p: tuple for optimization of the fit/tuple of parameters of gaussian function A, mu, sigma
    Returns:
        Gaussian Function
    """
    norm_coeff, mea, sigma = p
    return norm_coeff*np.exp(-(x-mea)**2/(2.*sigma**2))


class QCT():
    """
    Object to perform QCT analysis with clinical features
    on a .nii {SLICE_THICKNESS}mm CT scan with mask
    """

    def __init__(self, base_dir, parts, out_dir, single_mode, st, ad):
        """
        Constructor for the QCT class.
        :param base_dir: path to patient base directory
        :param parts: List of lung ROIs to be analyzed
        :param out_dir: Path to results directory
        :param single_mode: Boolean flag to activate single mode
        :param st: Slice thickness
        :param ad: Analysis date and time
        """

        self.base_dir = base_dir
        self.out_dir = out_dir
        self.parts = parts
        self.st = st
        self.ad = ad

        if single_mode:
            self.ct3_paths = [os.path.join(base_dir, f"CT_{st:.0f}mm.nii")]
            self.dcmpaths = [os.path.join(base_dir, "CT")]
            self.patient_paths = [base_dir]
        else:
            self.ct3_paths = glob.glob(base_dir + f"/*/CT_{st:.0f}mm.nii")
            self.dcmpaths = glob.glob(base_dir + "/*/CT/")
            self.patient_paths = glob.glob(base_dir + "/*/")

        assert len(self.ct3_paths) == len(self.dcmpaths) == len (self.patient_paths) , "Wrong path length"


    def run(self,):
        """
        Extract clinical features from histogram of voxel intensity.
        Computed statistics are:
        - Lung volume
        - Mean, std, kurtosis, skewness
        - Percentiles
        - WAVE (Area of gaussian fit), WAVE.th
        """
        features_df = pd.DataFrame()
        with open(os.path.join(self.out_dir, 'clinical_features.csv'), 'w', encoding='utf-8') as fall:
            fall_wr = csv.writer(fall, delimiter='\t')
            plt.figure()

            pbar = tqdm(total=len(self.parts)*len(self.ct3_paths), desc='Clinical features  ', colour='cyan')
            for part in self.parts:
                for ct_3m, dcmpath, patient_path in zip(self.ct3_paths,self.dcmpaths, self.patient_paths):
                    plt.clf()
                    searchtag = dcmtagreader(dcmpath)
                    accnum = searchtag[0x008, 0x0050].value

                    if part=='bilat':
                        maskpath = os.path.join(patient_path, f'mask_R231CW_{self.st:.0f}mm_bilat.nii')
                    elif part in ('lower', 'upper'):
                        maskpath = os.path.join(patient_path, f'mask_R231CW_{self.st:.0f}mm_upper.nii')
                    elif part in ('left', 'right'):
                        maskpath = os.path.join(patient_path, f'mask_R231CW_{self.st:.0f}mm.nii')
                    elif part in ('ventral', 'dorsal'):
                        maskpath = os.path.join(patient_path, f'mask_R231CW_{self.st:.0f}mm_ventral.nii')
                    elif part in ['upper_ventral', 'upper_dorsal', 'lower_ventral', 'lower_dorsal']:
                        maskpath = os.path.join(patient_path, f'mask_R231CW_{self.st:.0f}mm_mixed.nii')
                    else:
                        raise Exception(f"Part {part} not implemented")

                    image, mask = sitk.ReadImage(ct_3m), sitk.ReadImage(maskpath)
                    image_arr, mask_arr = sitk.GetArrayFromImage(image), sitk.GetArrayFromImage(mask)

                    if part in ['bilat' ,'right', 'dorsal', 'lower' ]:
                        grey_pixels = image_arr[mask_arr==10]
                        mask_arr = mask_arr[mask_arr==10]
                        mask_arr = np.sign(mask_arr)
                    elif part in ['left', 'ventral', 'upper']:
                        grey_pixels = image_arr[mask_arr==20]
                        mask_arr = mask_arr[mask_arr==20]
                        mask_arr = np.sign(mask_arr)
                    elif part=='upper_ventral':
                        grey_pixels = image_arr[mask_arr==42]
                        mask_arr = mask_arr[mask_arr==42]
                        mask_arr = np.sign(mask_arr)
                    elif part=='upper_dorsal':
                        grey_pixels = image_arr[mask_arr==22]
                        mask_arr = mask_arr[mask_arr==22]
                        mask_arr = np.sign(mask_arr)
                    elif part=='lower_dorsal':
                        grey_pixels = image_arr[mask_arr==11]
                        mask_arr = mask_arr[mask_arr==11]
                        mask_arr = np.sign(mask_arr)
                    elif part=='lower_ventral':
                        grey_pixels = image_arr[mask_arr==21]
                        mask_arr = mask_arr[mask_arr==21]
                        mask_arr = np.sign(mask_arr)
                    else:
                        raise NotImplementedError(f"Part {part} not implemented")

                    ct_nii_path = os.path.join(pathlib.Path(ct_3m).parent.absolute(), "CT.nii")

                    ctn = sitk.ReadImage(ct_nii_path)
                    spacing = ctn.GetSpacing()
                    volume = spacing[0]*spacing[1]* float(self.st) * (np.sum(mask_arr))

                    grey_pixels = grey_pixels[grey_pixels<=180]
                    grey_pixels = grey_pixels[grey_pixels>=-1020]

                    ave = np.mean(grey_pixels)
                    std = np.std(grey_pixels)
                    skew, kurt = stats.skew(grey_pixels), stats.kurtosis(grey_pixels)

                    # GAUSSIAN FIT #
                    data = plt.hist(grey_pixels, bins=240, range=(-1020, 180), density=True, alpha=0.5)     
                    counts = np.array(data[0])
                    bins = np.array(data[1])

                    bins_med = bins[:-1] + 2.5
                    assert len(counts)==len(bins_med), "Something went wrong with the histogram"

                    # Filter on range

                    left_lim, right_lim = -950, -700
                    x_range = [x for x in bins_med if left_lim < x < right_lim]
                    y_range = [y for x,y in zip(bins_med, counts) if left_lim < x < right_lim]

                    assert len(x_range)==len(y_range), "Something went wrong with cutting the histogram"

                    i_max = np.argmax(y_range)
                    y_smooth = scipy.signal.medfilt(y_range, kernel_size=7)
                    grads = np.gradient(y_smooth)

                    i_max = 0

                    for i in range(len(grads)-1):
                        if grads[i]*grads[i+1] <= 0:
                            i_max = i
                            break

                    i_right = i_max + 7
                    y_tofit = y_range[0:i_right]
                    x_tofit = x_range[0:i_right]

                    params_0 = [0.001, -800, 120]

                    coeff, _ = curve_fit(gauss, x_tofit, y_tofit,
                        p0=params_0, maxfev=10000,
                        bounds=([0.00001, -1000, 5], [1, -600, 350]))

                    if coeff[1]<-950 or coeff[1]>-750 or coeff[2]<5 or coeff[2]>150:
                        wave = 'n.a.'
                        #ill_curve=counts
                        mean_ill, std_ill = ave, std

                    else:
                        gaussian_fit = gauss(x_tofit, *coeff)
                        gauss_tot = gauss(bins_med, *coeff)

                        plt.plot(x_tofit, gaussian_fit,linestyle= '--',color='orange',
                            label='data for Gaussian Fit', linewidth= 4.0)
                        plt.plot(bins_med, gauss_tot, color= 'crimson', label='Gaussian fit')

                        wave = np.sum(gauss_tot)/np.sum(counts)
                        wave = np.round(wave, 3)
                        ill_curve = scipy.signal.medfilt(abs(counts - gauss_tot), kernel_size=5)

                        mean_ill = np.sum([x*y for x,y in zip(bins_med, ill_curve)])/np.sum(ill_curve)
                        std_ill = np.sqrt(np.sum([(x-mean_ill)**2 * y for x,y in zip(
                            bins_med, ill_curve)])/np.sum(ill_curve))


                        data_ill = stats.rv_histogram(histogram=(ill_curve, bins))
                        plt.plot(bins_med, ill_curve, color='purple', label='ill curve')
                        #quant_ill = data_ill.ppf([.25, .5, .75, .9])
                    

                    waveth = np.sum([c for b,c in zip(bins_med,counts) if -950<=b<=-700])
                    waveth /= np.sum(counts)

                    lims = [(-1000, -900), (-900, -500), (-500,-100), (-100,100)]
                    vents = [np.sum([c for b,c in zip(bins_med, counts) if reg[0]<= b< reg[1]])/
                        np.sum(counts) for reg in lims]

                    plt.axvline(x=-950, color='green', linestyle='dotted')
                    plt.axvline(x=-700, color='green', label='WAVE th range', linestyle='dotted')                             

                    searchtag = dcmtagreader(dcmpath)
                    try:
                        seriesDescription = str(searchtag[0x0008, 0x103e].value)
                        seriesDescription = seriesDescription.replace(' ', '').replace(',', '').replace('(', '').replace(')', '')
                    except:
                        seriesDescription = 'NA'

                    result_all = {
                        'AccessionNumber':   accnum,
                        'Analysis date': self.ad,
                        'Series description': seriesDescription,
                        'Region': part,
                        'volume':   np.round(volume/1000, 3),
                        'mean':     np.round(ave, 3),
                        'stddev':   np.round(std, 3),
                        'skewness': np.round(skew, 3),
                        'kurtosis': np.round(kurt, 3),
                        'wave':     wave,
                        'waveth':   np.round(waveth, 3),
                        'mean_ill': np.round(mean_ill, 3),
                        'std_ill':  np.round(std_ill, 3),
                        'overinf'  :np.round(vents[0],3),
                        'norm_aer' :np.round(vents[1],3),
                        'non_aer'  :np.round(vents[2],3),
                        'cons'  :   np.round(vents[3],3),
                    }

                    pbar.update(1)

                    if features_df.empty:
                        features_df = pd.DataFrame({k: [v] for k, v in result_all.items()})
                    else:
                        new = pd.DataFrame({k: [v] for k, v in result_all.items()})
                        features_df = pd.concat([features_df, new], ignore_index=True)

                    if fall.tell()==0:
                        fall_wr.writerow(result_all.keys())
                    fall_wr.writerow(result_all.values())

                    plt.legend(loc='upper right')
                    plt.title(f"{part} lung [HU]")


                    if not os.path.isdir(os.path.join(self.out_dir, 'histograms')):
                        os.mkdir(os.path.join(self.out_dir, 'histograms'))

                    plt.savefig(os.path.join(self.out_dir, 'histograms', f"{accnum}_hist_{part}_{seriesDescription}_{self.ad}.png"))

