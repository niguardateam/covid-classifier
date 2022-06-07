"""Perform clinical analysis on CT scan"""

import glob
import os
import csv
import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import pandas as pd
import scipy
from scipy.optimize import curve_fit
from tomlkit import integer
from covidlib.ctlibrary import dcmtagreader

# Il fit va eseguito non su tutto il range, ma in un range 
# Cercare il massimo della gaussiana e fare il fit su quel punto
# range -950, -650


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


class QCT(): # pylint: disable=too-few-public-methods
    """
    Object to perform QCT analysis with clinical features
    on a .nii 3mm CT scan with mask
    """

    def __init__(self, base_dir) -> None:
        self.base_dir = base_dir
        self.ct3_paths = glob.glob(base_dir + "/*/CT_3mm.nii")
        self.mask3bilatpaths = glob.glob(base_dir + "/*/mask_R231CW_3mm_bilat.nii")
        self.mask3paths = glob.glob(base_dir + "/*/mask_R231CW_3mm.nii")
        self.out_dir = "./results/"
        self.dcmpaths = glob.glob(base_dir + "/*/CT/")

    def run(self,): # pylint: disable=too-many-locals
        """
        Extract clinical features from histogram of voxel intensity.
        Computed statistics are:
        - Lung volume
        - Mean, std, kurtosis, skewness
        - Percentiles
        - WAVE (Area of gaussian fit)
        """

        features_df = pd.DataFrame()

        with open(os.path.join(self.out_dir, 'clinical_features.csv'),
            'w', encoding='utf-8') as fall:

            fall_wr = csv.writer(fall, delimiter='\t')

            for ct_3m,dcmpath,mask3bilat in zip(self.ct3_paths,self.dcmpaths,self.mask3bilatpaths):

                plt.figure()
                searchtag = dcmtagreader(dcmpath)
                #pname = searchtag[0x0010, 0x0010].value
                accnum = searchtag[0x008, 0x0050].value

                image, mask = sitk.ReadImage(ct_3m), sitk.ReadImage(mask3bilat)
                image_arr, mask_arr = sitk.GetArrayFromImage(image), sitk.GetArrayFromImage(mask)

                #volume = prod(image.GetSpacing(),image.GetSize()) * (np.sum(mask_arr)/mask_arr.size)
                vx, vy, vz = image.GetSpacing()
                volume = vx*vy*vz * (np.sum(mask_arr))
                # sistemare

                grey_pixels = image_arr[mask_arr>0]
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
                x_range = [x for x in bins_med if x > -950 and x < -650]
                y_range = [y for x,y in zip(bins_med, counts) if x > -950 and x < -650]

                p0 = [0.001, -800, 120]

                coeff, _ = curve_fit(gauss, x_range, y_range, p0=p0, maxfev=10000, bounds=([0.00001, -1000, 15], [1, -600, 350]))
                gaussian_fit = gauss(x_range, *coeff)
                plt.plot(x_range, gaussian_fit,linestyle= '--',color='yellow', label='data for Gaussian Fit', linewidth= 5.0)

                gauss_tot = gauss(bins_med, *coeff)

                wave = np.sum(gauss_tot)/np.sum(counts)
                plt.plot(bins_med, gauss_tot, color= 'crimson', label='Gaussian function obtained')


                #WAVE.th = integrale dell'istogramma tra -950,-750

                waveth = np.sum([c for b,c in zip(bins_med, counts) if b > -950 and b < -750])/np.sum(counts)

                # with open(os.path.join(self.out_dir, 'histo_prova.csv'), 'w', encoding='utf-8') as fhist:
                #     fhist_wr = csv.writer(fhist, delimiter='\t')
                #     for j in range(len(counts)):
                #         fhist_wr.writerow([bins[j], counts[j]])

                #wave =  np.trapz(best_fit_line, bins_medi, dx=1)
      
                result_all = {

                    'AccessionNumber':   accnum,
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
                plt.savefig('results/histograms/' + accnum + "_hist.png")


if __name__=='__main__':
    r = QCT(base_dir="/Users/andreasala/Desktop/Tesi/data/COVID-NOCOVID/")

    r.run()
