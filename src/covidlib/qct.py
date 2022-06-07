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

def gauss(_x, x_0, sigma):
    """Gaussian pdf with mean value x_0 and std dev sigma"""
    return  1 / (np.sqrt(2*np.pi)*sigma) *np.exp(-(_x - x_0) ** 2 / (2 * sigma ** 2))


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

                pixels_fit = grey_pixels[grey_pixels>=-900]
                pixels_fit = pixels_fit[pixels_fit<=-700]

                mu_gaus, sigma = stats.norm.fit(pixels_fit)

                #bin width= 5HU
                #range = -1020, 180
                #--> 240 bins

                #WAVE.th = integrale dell'istogramma tra -950,-750

                counts2, bins2 = np.histogram(grey_pixels, bins=240, density=False)
                bins_medi = bins2[:-1] + 2.5
                counts, bins = np.histogram(grey_pixels, bins=240, density=True)

                best_fit_line = gauss(bins_medi, mu_gaus, sigma)
                best_fit_line *= np.max(counts)/np.max(best_fit_line)



                waveth=0
                for k in range(len(bins_medi)):
                    if bins_medi[k]>=-950 and bins_medi[k]<=-750:
                        waveth+= counts2[k]
                waveth /= np.sum(counts2)     

                with open(os.path.join(self.out_dir, 'histo_prova.csv'), 'w', encoding='utf-8') as fhist:
                    fhist_wr = csv.writer(fhist, delimiter='\t')
                    for j in range(len(counts2)):
                        fhist_wr.writerow([bins2[j], counts2[j]])

                wave =  np.trapz(best_fit_line, bins_medi, dx=1)
                #wave = 0
                result_all = {

                    'AccessionNumber':   accnum,
                    'volume':   np.round(volume, 3),
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

                plt.figure()
                plt.hist(grey_pixels, bins=240, density=True)
                plt.plot(bins_medi, best_fit_line)
                plt.savefig('results/histograms/' + accnum + "_hist.png")


if __name__=='__main__':
    r = QCT(base_dir="/Users/andreasala/Desktop/Tesi/data/COVID-NOCOVID/")

    r.run()
