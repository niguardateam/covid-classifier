"""Perform clinical analysis on CT scan
on bilateral, left/right, upper/lower,
ventral/dorsal lungs."""

# new 
import glob
import os
import csv
import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import scipy
from scipy import stats
import pandas as pd
from scipy.optimize import curve_fit
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

    def __init__(self, base_dir, parts, out_dir, single_mode):

        self.base_dir = base_dir
        self.out_dir = out_dir
        self.parts = parts

        if single_mode:
            self.ct3_paths = [os.path.join(base_dir, "CT_3mm.nii")]
            self.dcmpaths = [os.path.join(base_dir, "CT")]
            self.patient_paths = [base_dir]
        else:
            self.ct3_paths = glob.glob(base_dir + "/*/CT_3mm.nii")
            self.dcmpaths = glob.glob(base_dir + "/*/CT/")
            self.patient_paths = glob.glob(base_dir + "/*/")
        

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
        with open(os.path.join(self.out_dir, f'clinical_features.csv'),'w', encoding='utf-8') as fall:
            fall_wr = csv.writer(fall, delimiter='\t')
            plt.figure()

            #for part in tqdm(PARTS, desc='Clinical features', colour='cyan'):

            for part in self.parts:

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

                    left_lim, right_lim = -950, -700
                    x_range = [x for x in bins_med if left_lim < x < right_lim]
                    y_range = [y for x,y in zip(bins_med, counts) if left_lim < x < right_lim]

                    assert len(x_range)==len(y_range), "Something went wrong with cutting the histogram"

                    i_max = np.argmax(y_range)
                    x_max = x_range[i_max]

                    y_smooth = scipy.signal.medfilt(y_range, kernel_size=7)
                    grads = np.gradient(y_smooth)
                    #plt.plot(x_range, y_smooth, color='firebrick', label='Filtered')
                    
                    i_max = 0

                    for i in range(len(grads)-1):
                        if grads[i]*grads[i+1] <= 0:
                            i_max = i
                            break

                    # broken=False
                    # for i in range(i_max, i_max+5):
                    #     if grads[i]*grads[i+1] < 0 or x_range[i]>-750:
                    #         i_right = i
                    #         broken = True
                    #         break

                    # if not broken:
                    #     i_right = i_max + 7
                    #  

                    i_right = i_max + 7
                    
                    y_tofit = y_range[0:i_right]
                    x_tofit = x_range[0:i_right]

                    # Test on mu and sigma:
                    # - mu in (-950,-750)
                    # - sigma in (5, 150)
                    # If fit fails: no gauss (WAVE=0)

                    p0 = [0.001, -800, 120]

                    coeff, _ = curve_fit(gauss, x_tofit, y_tofit, p0=p0, maxfev=10000,
                        bounds=([0.00001, -1000, 5], [1, -600, 350]))

                    if coeff[1]<-950 or coeff[1]>-750 or coeff[2]<5 or coeff[2]>150:
                        wave = 0

                    else:
                        gaussian_fit = gauss(x_tofit, *coeff)
                        gauss_tot = gauss(bins_med, *coeff)

                        plt.plot(x_tofit, gaussian_fit,linestyle= '--',color='orange',
                            label='data for Gaussian Fit', linewidth= 5.0)
                        plt.plot(bins_med, gauss_tot, color= 'crimson', label='Gaussian fit')

                        wave = np.sum(gauss_tot)/np.sum(counts)

                    waveth = np.sum([c for b,c in zip(bins_med,counts) if -950<=b<=-750])
                    waveth /= np.sum(counts)

                    #ill_curve = abs(hist - fit)
                    # if NO GAUSS-> gauss = hist(-950, -750)

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

                    if not os.path.isdir(os.path.join(self.out_dir, 'histograms')):
                        os.mkdir(os.path.join(self.out_dir, 'histograms'))

                    plt.savefig(os.path.join(self.out_dir, 'histograms', f"{accnum}_hist_{part}.png"))

                    #ciao! 2
