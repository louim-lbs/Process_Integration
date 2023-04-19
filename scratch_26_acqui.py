import os
import logging
import time
import sys

from matplotlib import pyplot as plt
import numpy as np

sys.path.insert(1, r'C:\Users\User\Documents\LM Lebas\Process_Integration')
os.chdir(r'C:\Users\User\Documents\LM Lebas\Process_Integration')

import com_functions

dir_pi = os.getcwd()

microscope = com_functions.microscope().f
microscope.import_package_and_connexion()

positioner = com_functions.microscope().p
positioner.import_package_and_connexion()

# Lauch GUI
os.chdir(dir_pi)

resolution='1536x1024'
bit_depth=8
dwell_time=1e-6

def acquire_frame2(resolution='1536x1024', dwell_time=1e-6, bit_depth=16, square_area=False):
    microscope.quattro.imaging.start_acquisition()
    img = microscope.quattro.imaging.get_image()
    img_prev_stamp = img.data[-1,:]
    micro_resolution = microscope.quattro.beams.electron_beam.scanning.resolution.value
    micro_dwell_time = microscope.quattro.beams.electron_beam.scanning.dwell_time.value
    micro_bit_depth = microscope.quattro.beams.electron_beam.scanning.bit_depth
    if [micro_resolution, micro_dwell_time, micro_bit_depth] != [resolution, dwell_time, bit_depth]:
        microscope.quattro.beams.electron_beam.scanning.resolution.value = resolution
        microscope.quattro.beams.electron_beam.scanning.dwell_time.value = dwell_time
        microscope.quattro.beams.electron_beam.scanning.bit_depth = bit_depth
    if square_area == True:
        image_width, image_height = resolution.split('x')
        image_width, image_height = int(image_width), int(image_height)
        dim_max = max(image_width, image_height)
        dim_min = min(image_width, image_height)
        left = (dim_max - dim_min)/(2*dim_max)
        top = 0
        width = dim_min/dim_max
        height = 1
        microscope.quattro.beams.electron_beam.scanning.mode.set_reduced_area(left, top, width, height)
    
    while (True):
        img = microscope.quattro.imaging.get_image()
        try:
            if not np.array_equal(img_prev_stamp, img.data[-1,:]):
                microscope.quattro.imaging.stop_acquisition()
                return img
        except:
            print('Error acquiring frame')
            pass

i = 0
for i in range(10):
    image = acquire_frame2(resolution, dwell_time, bit_depth, square_area=True)
    print('Acquired frame: ', i)
microscope.quattro.imaging.start_acquisition()
# plt.imshow(microscope.image_array(image), cmap='gray')
# plt.show()

