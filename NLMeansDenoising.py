import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from tifffile import imread, imsave
from tqdm import tqdm
from microscopes import DM34

from tkinter.filedialog import askopenfilename
import cv2 as cv
import time

'''Adapted from: https://stackoverflow.com/questions/41019222/deblur-an-image-using-scikit-image'''

def denoise(img, h):
    t = time.time()
    ret = cv.fastNlMeansDenoising(img, None, h, templateWindowSize=7, searchWindowSize=21)
    print('Denoising took: ' + str(time.time() - t) + ' seconds.')
    return ret

def load(path):
    img, _, _, _ = DM34.dm_load(path)
    return np.float32(img)

h_0 = 10
axis_color = 'lightgoldenrodyellow'

# Load image
# image_path = askopenfilename()


image = load(r"C:\Users\Public\Documents\Lebas\Process_Integration\data\tomo\Acquisition_rep_1673533223_res_1024x1024_dw_2e-06s_stp0.2_dri_True_foc_False\HAADF_Acquisition_rep_4_-57.dm4")
image = np.asarray(255*(image - np.min(image))/(np.max(image)-np.min(image)), dtype='uint8')

# Analyse image dimensions
try:
    image_depth, image_height, image_width = image.shape
except:
    image_height, image_width = image.shape
    image_depth = 1


if image.dtype != np.uint8 and image.dtype != np.uint16:
    print('Not supported image type. Convert to 8 or 16 bit.')
    exit()

# Choice of smoothing factor by patch visualisation
if image_depth == 1:
    frame_0 = ((image/np.max(image))*256).astype('uint8')
else:
    frame_0 = ((image[0,:,:]/np.max(image))*256).astype('uint8')

fig = plt.figure()

subplot1 = fig.add_subplot(121)
subplot2 = fig.add_subplot(122) # schematic

# Adjust the subplots region to leave some space for the sliders and buttons
fig.subplots_adjust(left=0.1, bottom=0.25)

# Draw the initial plot
img = subplot1.imshow(frame_0, cmap='gray')
frm_denoised = subplot2.imshow(denoise(frame_0, h_0), cmap='gray')

# Add two sliders for tweaking the parameters

# Define an axes area and draw a slider in it
slider_subplot2  = fig.add_axes([0.1, 0.15, 0.8, 0.03])
slider = Slider(slider_subplot2, 'h', 0, 50, valinit=h_0)

# Define an action for modifying the line when any slider's value changes
def sliders_on_changed(val):
    frm_denoised_2 = denoise(frame_0, slider.val)
    frm_denoised.set_data(frm_denoised_2)
    fig.canvas.draw_idle()
slider.on_changed(sliders_on_changed)

# Add a button to compute the result
compute_button_subplot1 = fig.add_axes([0.8, 0.025, 0.1, 0.04])
compute_button = Button(compute_button_subplot1, 'Compute', color=axis_color, hovercolor='0.975')
def compute_button_on_clicked(mouse_event):
    plt.close()
    image_denoised = np.zeros((image_depth, image_height, image_width), dtype=np.uint8)
    if image_depth == 1:
        image_denoised = denoise(((image/np.max(image))*256).astype('uint8'), slider.val)
    else:
        for i in tqdm(range(image_depth)):
            image_denoised[i,:,:] = denoise(((image[i,:,:]/np.max(image))*256).astype('uint8'), slider.val)
    imsave(image_path + '_denoised.tiff', np.array(image_denoised), bigtiff = True)
    print('Filtering done!')
    
compute_button.on_clicked(compute_button_on_clicked)

plt.show()