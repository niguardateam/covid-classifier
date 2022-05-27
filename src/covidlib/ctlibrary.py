# -*- coding: utf-8 -*-
# @author: S. Carrazza
# continued by Sara Gelmini

import glob
import pydicom
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import csv 
from PIL import Image
import statistics
from scipy.optimize import curve_fit
from scipy.signal import argrelextrema
import nrrd
import nibabel as nib


def dcmtagreader(folder_name: str):
    """CT image dicom reader

    Arguments: 
        path of dicom folder
    
    Example of Usage: call it when you need to find dicom tags
    """
    files_with_dcm = glob.glob(f"{folder_name}/*")
    for inputfile in files_with_dcm:
        data = pydicom.dcmread(inputfile)
    
    return data

def dcmtagreader_bis(folder_name: str):
    """CT image dicom reader

    Arguments: 
        path of dicom folder
    
    Example of Usage: call it when you need to find dicom tags
    """
    files_with_dcm = glob.glob(f"{folder_name}/*")
    for inputfile in files_with_dcm:
        data = pydicom.dcmread(inputfile)
    
    return data

def Manual_Sorter(man_element: list, man_key: list):
    """Sorter for list.

    Arguments:
        man_element(list) the element to be sorted
        man_key(list) the key used for sorting

    Returns: 
        Ordered list

    """
    n = len(man_key)
    for i in range (n-1):
        for j in range (0, n-i-1):
            if man_key[j] > man_key[j+1]:
                man_element[j], man_element[j+1] = man_element[j+1], man_element[j]
                man_key[j], man_key[j+1] = man_key[j+1], man_key[j]


def load_ct_from_folder(folder_name: str) -> list:
    """Load CT images/pixel_array in a list.

    Arguments:
        folder_name (str)

    Returns:
        List of images.
    """
    files_with_dcm = glob.glob(f"{folder_name}/*")
    images = list()
    position = list()
    park = list()
    
    for inputfile in files_with_dcm:
        data = pydicom.dcmread(inputfile)
        #print (inputfile, int(data[0x0020,0x0013].value))
        images.append(data.pixel_array)
        position.append(int(data[0x0020,0x0013].value))
    Manual_Sorter(images, position)
    return images

def load_ct_from_folder_bis(folder_name: str) -> list:
    """Load CT images/pixel_array in a list.

    Arguments:
        folder_name (str)

    Returns:
        List of images.
    """
    files_with_dcm = glob.glob(f"{folder_name}/*")
    images = list()
    position = list()
    park = list()
    
    for inputfile in files_with_dcm:
        data = pydicom.dcmread(inputfile)
        #print (inputfile, int(data[0x0020,0x0013].value))
        images.append(data.pixel_array)
        position.append(int(data[0x0020,0x0013].value))
    Manual_Sorter(images, position)
    return images

def another_loader(folder_name: str) -> list:
    """
    CT loader provv for test
    """
    files_with_dcm = glob.glob(f"{folder_name}/*.dcm")
    images = list()
    for inputfile in files_with_dcm:
        data = pydicom.dcmread(inputfile)
        images.append(data.pixel_array)
    return images

def load_png_CT_fromfolder(folder_name:str) ->list:
    """Load CT images/pixel_array in a list.

    Arguments:
        folder_name (str)

    Returns:
        List of images.
    """
    files_with_png = glob.glob(f"{folder_name}/*.png")
    images = list()
    orderkey = list()
    for inputfile in files_with_png:
        data = Image.open(inputfile)
        images.append(np.array(data))
        orderkey.append(int(str(inputfile).replace(folder_name, '').replace('/','').replace('.png','')))
    Manual_Sorter(images, orderkey)
    return images


def load_mask_from_file(file_name: str) -> list:
    """Load Mask in a list
    
    Arguments:
        file_name (str) type .tif
        
    Returns:
        List of images.
    """
    Mask= list()
    img= Image.open(file_name)
    for i in range(img.n_frames):
        img.seek(i)
        Mask.append(np.array(img))
    return Mask

def load_NRRD_mask(file_name: str) -> list: 
    """Load Mask in a list
    DO NOT USE THIS FUNCTION
    
    Arguments:
        file_name (str) type .nrrd
        
    Returns:
        List of images.
    """
    Mask = list()
    img = nrrd.read(file_name)
    for i in img:
        Mask.append(i)
    return Mask

def load_nii_mask(file_name: str) -> list:
    """Load Mask in a list
    
    Arguments:
        file_name (str) type .nii
        PAY ATTENTION TO MASK ORIENTATION
        
    Returns:
        List of images.
    """
    Mask = list()
    img = nib.load(file_name)
    data = img.get_fdata()
    #data = np.rot90(data)
    
    print ('data.shape= ', data.shape)
    """
    for slice_Number in range(data.shape[2]):
           plt.imshow(data[:,:,slice_Number ])
           plt.show()
    """
    for slice_Number in range(data.shape[2]-1,-1, -1):
           park = data[:,:,slice_Number]
           #park = np.flipud(park)
           Mask.append(park)
    
    return Mask

def load_nii_ct(file_name: str) -> list:
    """Load Mask in a list
    
    Arguments:
        file_name (str) type .nii
        PAY ATTENTION TO MASK ORIENTATION
        
    Returns:
        List of images.
    """
    niftiimage = list()
    img = nib.load(file_name)
    data = img.get_fdata()
    data = np.rot90(data)
    
    print ('data.shape= ', data.shape)
    """
    for slice_Number in range(data.shape[2]):
           plt.imshow(data[:,:,slice_Number ])
           plt.show()
    """
    for slice_Number in range(data.shape[2]-1,-1, -1):
           park = data[:,:,slice_Number]
           #park = np.flipud(park)
           niftiimage.append(park)
    
    return niftiimage

def BilateralMask(inputMask: list, eliminatevalue: int) ->list:
    Park = list()
    #NewMask = list()
    for inputMaski in inputMask:
        data =np.where(inputMaski==eliminatevalue, inputMaski/eliminatevalue, inputMaski*1)
        Park.append(data)
   
    return Park

def SegFunc(inputCT: list, inputMask: list, value: int) -> list:
    """
    Segmentation of CT lungs

    Arguments:
        CT image (list)
        inputMask (list)
        value: int, value of the mask to consider
    
    Returns:
        Segmented lungs
    """
    Park = list()
    for inputCTi, inputMaski in zip(inputCT, inputMask):
        data =np.where(inputMaski==value, inputCTi, inputCTi*0)
        Park.append(data)

    return Park

def SegFunc_bis(inputCT: list, inputMask: list, value: int) -> list:
    """
    Segmentation of CT lungs

    Arguments:
        CT image (list)
        inputMask (list)
        value: int, value of the mask to consider
    
    Returns:
        Segmented lungs
    """
    Park = list()
    for inputCTi, inputMaski in zip(inputCT, inputMask):
        data =np.where(inputMaski==value, inputCTi*0, inputCTi)
        Park.append(data)

    return Park

def SegFunc_SubRoi(inputCT: list, inputMask: list, value: int) -> list:
    """
    Segmentation of CT lungs

    Arguments:
        CT image (list)
        inputMask (list)
        value: int, value of the mask to consider
    
    Returns:
        Segmented lungs
    """    

    Park = list()
    for inputCTi, inputMaski in zip(inputCT, inputMask):
        data =np.where(inputMaski==value, inputCTi, inputCTi*0)
        data_1=np.where(data==value+1, inputCTi, inputCTi*0)

        Park.append(data_1)

    return Park


def cumulative_pixel_histogram(images: list, min: int = 500, max: int = 2000) -> np.array:
    """Compute accumulative pixel histogram from dicom
    pixel_array.

    Arguments:
        images (list): list with numpy matrices
        min (int): minimum pixel value of x axis -1 (because the extrema are excluded). Deafult 500
        max (int): maximum pixel value of x axis +1 (because the extrema are excluded). Default 2000

    Returns:
        Array with all pixel values.
    """
    flatten_data = np.array([], dtype=np.uint16) 
    for image in images:
        filter_image = image[np.logical_and(image>min, image<max)] #threshold and cut of the tail
        flatten_data = np.concatenate([flatten_data, filter_image])

    #print('VETTORE', flatten_data)
    return flatten_data

def ImageViewer(ID: int, Selecimage: list, n_columns: int, n_rows: int, Size_x: int, Size_y: int, titleGraph: str='CTimage'):
    """Uses matplot to plot CTs

    Arguments:
        ID (int): to identificate the window
        Selecimage (list): name of the list of the desired image
        n_columns (int): number of columns of the image display (influences numenr of images)
        n_rows (int): number of rows of the image display (influences numenr of images)
        Size_x and Size_y (int): size of the displayer
    
    Returns:
        Display of images
    """

    viewer = plt.figure(num= ID, figsize=(Size_x,Size_y))
    columns = n_columns 
    rows = n_rows
    plt.title(titleGraph)
    for i in range (1,columns*rows +1):
        viewer.add_subplot(rows, columns, i )
        plt.imshow(Selecimage[i], cmap = 'gray')

    #plt.savefig(titleGraph)
    




    

    
    