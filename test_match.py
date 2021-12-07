import numpy as np
from matplotlib import image

from scripts import match, set_eucentric

import os
import logging

dir_pi = os.getcwd()
logging.basicConfig(filename='last_execution.log', filemode='w', format='%(levelname)s:%(message)s', level=logging.INFO)

dir_pi = os.getcwd()



from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *
      

# Connexion

# Connect to microscope

quattro = SdbMicroscopeClient()

try:
    quattro.connect() # online connection
    SdbMicroscopeClient.InitState_status = property(lambda self: 0) # Or 1 if not connected
except:
    try:
        quattro.connect('localhost') # local connection (Support PC) or offline scripting
        SdbMicroscopeClient.InitState_status = property(lambda self: 0) # Or 1 if not connected
    except:
        SdbMicroscopeClient.InitState_status = property(lambda self: 1) # Or 0 if not connected


# Connect to positioner

from smaract import connexion_smaract as sm
smaract = sm.smaract_class(calibrate=False)
os.chdir(dir_pi)
smaract.setpos_abs([0, 0, 0])

quattro.imaging.set_active_view(3)

# resolution="1536x1024"
resolution="512x442"
settings = GrabFrameSettings(resolution=resolution, dwell_time=10e-6, bit_depth=16)



set_eucentric(quattro, smaract)

exit()

image1 = quattro.imaging.grab_multiple_frames(settings)

smaract.setpos_abs([0, 0, 0])

image2 = quattro.imaging.grab_multiple_frames(settings)

hfw = quattro.beams.electron_beam.horizontal_field_width.value
image_width_pix = int(resolution[:resolution.find('x')])

# for i in range(3):
#     image1[i].save('img3_0_' + str(i) + '.tif')
#     image2[i].save('img3_1_' + str(i) + '.tif')
dx, dy, trust = match(image1[2].data, image2[2].data, grid_size=5, ratio_template_master=0.9)
print(dx, dy)

smaract.setpos_abs([0, 0, 0])

exit()

img1 = np.asarray(image.imread('images/2_40.tif'))
img2 = np.asarray(image.imread('images/5_25.tif'))

try:
    img1 = img1[:,:,1]
    img2 = img2[:,:,1]
except:
    pass

import time


# ratio = [0.1*i for i in range(1,10)]
# ratio = 0.9
# grid =  [ 1*i for i in range(1, 10)]

# # for x in ratio:
# for y in grid:
#     try:
#         t = time.time()
#         dx, dy, trust = match(img1, img2, grid_size=y, ratio_template_master=ratio)
#         print(y, 1000000*dx*1.27e-05/512, 1000000*dy*1.27e-05/512, trust)
#         print('time = ', int((time.time()-t)*1000), 'ms')
#         # print(x, y, dx, dy, trust)
#     except:
        
#         pass


t = time.time()
res = match(img1, img2, grid_size=5, ratio_template_master=0.9)
print(res)
print('time = ', int((time.time()-t)*1000), 'ms')

# dx, dy, trust = match(img1, img2, grid_size=5, ratio_template_master=0.9)
# print(1000000*dx*1.27e-05/512, 1000000*dy*1.27e-05/512, trust)