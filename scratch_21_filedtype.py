#
from microscopes import DM34
import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv

def load(path):
    img, _, _, _ = DM34.dm_load(path)
    return np.float32(img)

img = load(r"C:\Users\Public\Documents\Lebas\Process_Integration\data\tomo\Acquisition_rep_1673533223_res_1024x1024_dw_2e-06s_stp0.2_dri_True_foc_False\HAADF_Acquisition_rep_4_-57.dm4")


img = np.asarray(255*(img - np.min(img))/(np.max(img)-np.min(img)), dtype='uint8')

plt.imshow(img)
plt.show()

img_ret = cv.fastNlMeansDenoising(img, None, h=100, templateWindowSize=7, searchWindowSize=21)


plt.imshow(img)
plt.show()
