# author: @andreasala98

import SimpleITK as sitk
import numpy as np
import glob
import matplotlib.pyplot as plt
from scipy import stats
import os, csv
import pandas as pd

from covidlib.ctlibrary import dcmtagreader

def prod(tup1: tuple, tup2:tuple)-> float :
    """
    Scalar product between two tuples
    """
    assert len(tup1) == len(tup2), "Two arrays must be of same size"
    return sum(p*q for p,q in zip(tup1, tup2))

def gauss(x, x0, sigma):
    return  1 / (np.sqrt(2*np.pi)*sigma) *np.exp(-(x - x0) ** 2 / (2 * sigma ** 2))


class QCT():
    """
    Object to perform QCT analysis with clinical features
    on a .nii 3mm CT scan with mask
    """
    
    def __init__(self, base_dir) -> None:
        self.base_dir = base_dir
        self.CT3paths = glob.glob(base_dir + "/*/CT_3mm.nii")
        self.mask3bilatpaths = glob.glob(base_dir + "/*/mask_R231CW_3mm_bilat.nii")
        self.mask3paths = glob.glob(base_dir + "/*/mask_R231CW_3mm.nii")
        self.output_dir = "./results/"
        self.dcmpaths = glob.glob(base_dir + "/*/CT/")
        

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

        with open(os.path.join( self.output_dir  , 'clinical_features.csv'), 'w') as fall:

            fall_wr = csv.writer(fall, delimiter='\t')
 
            for CT3, dcmpath, mask3bilat in zip(self.CT3paths, self.dcmpaths, self.mask3bilatpaths):

                searchtag = dcmtagreader(dcmpath)
                pname = searchtag[0x0010, 0x0010].value
                accnum = searchtag[0x008, 0x0050].value

                image, mask = sitk.ReadImage(CT3), sitk.ReadImage(mask3bilat)
                image_arr, mask_arr = sitk.GetArrayFromImage(image), sitk.GetArrayFromImage(mask)

                volume =  prod(image.GetSpacing(), image.GetSize()) *  (np.sum(mask_arr) / mask_arr.size )

                grey_pixels = image_arr[mask_arr>0]
                grey_pixels = grey_pixels[grey_pixels<180]
                grey_pixels = grey_pixels[grey_pixels>-1024]

                ave = np.mean(grey_pixels)
                quant = np.quantile(grey_pixels, [.25, .5, .75, .9])
                std, skew, kurt = np.std(grey_pixels), stats.skew(grey_pixels), stats.kurtosis(grey_pixels)

                mu, sigma = stats.norm.fit(grey_pixels)
                
                #_, bins, points = plt.hist(grey_pixels, bins=100, density=True, label='data')
                counts, bins = np.histogram(grey_pixels, bins=100, density=True)
                best_fit_line = stats.norm.pdf(bins, mu, sigma)
                ill_curve = best_fit_line[:-1] - counts

                wave =  np.trapz(best_fit_line, bins, dx=1)

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
                    'wave':     np.round(wave, 3)
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
                plt.hist(grey_pixels, bins=100, density=True)
                plt.plot(bins, best_fit_line)
                plt.savefig('results/histograms/' + accnum + "_hist.png")

        
if __name__=='__main__':
    r = QCT(base_dir="/Users/andreasala/Desktop/Tesi/data/COVID-NOCOVID/")

    r.run()