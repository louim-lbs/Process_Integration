#
from microscopes import DM34
import numpy as np
import matplotlib.pyplot as plt

def load(path):
    img, _, _, _ = DM34.dm_load(path)
    return np.float32(img)

img = load(r"C:\Users\Public\Documents\Lebas\Process_Integration\data\tomo\A_1673273569_res_2048x2048_dw_2e-07s_stp1.0_dri_True_foc_False\HAADF_A_1_-50.dm4")

print(img.dtype)


img = np.asarray(255*(img - np.min(img))/(np.max(img)-np.min(img)), dtype='uint8')

plt.imshow(img)
plt.show()

print(img)