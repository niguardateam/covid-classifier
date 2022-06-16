"""Perform clinical analysis on CT scan
on bilateral, left/right, upper/lower,
ventral/dorsal lungs."""

import glob
import os
import csv
import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from scipy import stats
import pandas as pd
from scipy.optimize import curve_fit
from tomlkit import integer
from covidlib.ctlibrary import dcmtagreader

PARTS = ['bilat', 'left', 'right','upper', 'lower', 'ventral', 'dorsal']

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
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))


class QCT():
    """
    Object to perform QCT analysis with clinical features
    on a .nii 3mm CT scan with mask
    """

    def __init__(self, base_dir) -> None:
        self.base_dir = base_dir
        self.ct3_paths = glob.glob(base_dir + "/*/CT_3mm.nii")
        self.out_dir = "./results/"
        self.dcmpaths = glob.glob(base_dir + "/*/CT/")
        self.patient_paths = glob.glob(base_dir + "/*/")

    def run(self,):
        """
        Extract clinical features from histogram of voxel intensity.
        Computed statistics are:
        - Lung volume
        - Mean, std, kurtosis, skewness
        - Percentiles
        - WAVE (Area of gaussian fit)
        """
        features_df = pd.DataFrame()
        with open(os.path.join(self.out_dir, f'clinical_features.csv'),'w', encoding='utf-8') as fall:
            fall_wr = csv.writer(fall, delimiter='\t')
            plt.figure()

            for part in tqdm(PARTS, desc='Clinical features', colour='cyan'):

                for ct_3m, dcmpath, patient_path in zip(self.ct3_paths,self.dcmpaths, self.patient_paths):

                    plt.clf()
                    searchtag = dcmtagreader(dcmpath)
                    accnum = searchtag[0x008, 0x0050].value

                    if part=='bilat':
                        maskpath = os.path.join(patient_path, 'mask_R231CW_3mm_bilat.nii')
                    elif part=='lower' or part=='upper':
                        maskpath = os.path.join(patient_path, 'mask_R231CW_3mm_upper.nii')
                    elif part=='left' or part=='right':
                        maskpath = os.path.join(patient_path, 'mask_R231CW_3mm.nii')
                    elif part=='ventral' or part=='dorsal':
                        maskpath = os.path.join(patient_path, 'mask_R231CW_3mm_ventral.nii')
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
                    else:
                        raise Exception(f"Part {part} not implemented")

                    vx, vy, vz = image.GetSpacing()
                    volume = vx*vy*vz * (np.sum(mask_arr))

                    grey_pixels = grey_pixels[grey_pixels<=180]
                    grey_pixels = grey_pixels[grey_pixels>=-1020]

                    ave = np.mean(grey_pixels)
                    quant = np.quantile(grey_pixels, [.25, .5, .75, .9])
                    std = np.std(grey_pixels)
                    skew, kurt = stats.skew(grey_pixels), stats.kurtosis(grey_pixels)

                    # GAUSSIAN FIT #
                    data = plt.hist(grey_pixels, bins=240, range=(-1020, 180), density=True)
                    counts = np.array(data[0])
                    bins = np.array(data[1])

                    bins_med = bins[:-1] + 2.5
                    assert len(counts)==len(bins_med), "Something went wrong with the histogram"

                    # Filter on range
                    x_range = [x for x in bins_med if -950 < x < -650]
                    y_range = [y for x,y in zip(bins_med, counts) if -950 < x < -650]

                    p0 = [0.001, -800, 120]

                    coeff, _ = curve_fit(gauss, x_range, y_range, p0=p0, maxfev=10000,
                        bounds=([0.00001, -1000, 15], [1, -600, 350]))
                    gaussian_fit = gauss(x_range, *coeff)
                    plt.plot(x_range, gaussian_fit,linestyle= '--',color='yellow',
                        label='data for Gaussian Fit', linewidth= 5.0)

                    gauss_tot = gauss(bins_med, *coeff)

                    wave = np.sum(gauss_tot)/np.sum(counts)
                    plt.plot(bins_med, gauss_tot, color= 'crimson', label='Gaussian function obtained')

                    waveth = np.sum([c for b,c in zip(bins_med,counts) if -950<=b<=-750])
                    waveth /= np.sum(counts)

                    result_all = {

                        'AccessionNumber':   accnum,
                        'Region': part,
                        'volume':   np.round(volume/1000, 3),
                        'mean':     np.round(ave, 3),
                        'stddev':   np.round(std, 3),
                        'perc25':   np.round(quant[0],3),
                        'perc50':   np.round(quant[1],3),
                        'perc75':   np.round(quant[2],3),
                        'perc90':   np.round(quant[3], 3),
                        'skewness': np.round(skew, 3),
                        'kurtosis': np.round(kurt, 3),
                        'wave':     np.round(wave, 3),
                        'waveth':   np.round(waveth, 3)

                    }

                    if features_df.empty:
                        features_df = pd.DataFrame({k: [v] for k, v in result_all.items()})
                    else:
                        new = pd.DataFrame({k: [v] for k, v in result_all.items()})
                        features_df = pd.concat([features_df, new], ignore_index=True)

                    if fall.tell()==0:
                        fall_wr.writerow(result_all.keys())
                    fall_wr.writerow(result_all.values())

                    plt.legend()
                    plt.title(f"{part} lung [HU]")
                    plt.savefig(f'results/histograms/{accnum}_hist_{part}.png')