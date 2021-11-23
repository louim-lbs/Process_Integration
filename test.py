''' Process Integration fot tomogram acquisition using Quattro ESEM and Smaract MCS-3D

Use Python 32-bits

@author: Louis-Marie Lebas
Created on Fri Oct 29 2021
'''

### Imports

import os
import logging
from time import sleep

from matplotlib import pyplot as plt

dir_pi = os.getcwd()
logging.basicConfig(filename='last_execution.log', filemode='w', format='%(levelname)s:%(message)s', level=logging.INFO)



imp = 0
while True:
    try:
        from autoscript_sdb_microscope_client import SdbMicroscopeClient
        from autoscript_sdb_microscope_client.enumerations import *
        from autoscript_sdb_microscope_client.structures import *
        break
    except:
        if imp == 0:
            logging.info('Autoscript import failed... Trying to install pillow and cv2 requirements and trying again')
            #!pip install pillow # type: ignore
            #!pip install opencv-python # type: ignore
            imp = 1
        if imp != 0:
            logging.info('Something went wrong. Check your Autoscript installation')

### Connexion

# Connect to microscope

quattro = SdbMicroscopeClient()

try:
    quattro.connect('localhost') # local connection (Support PC) or offline scripting
    SdbMicroscopeClient.InitState_status = property(lambda self: 0) # Or 0 if connected.
except:
    try:
        quattro.connect() # online connection
        SdbMicroscopeClient.InitState_status = property(lambda self: 0) # Or 0 if connected.
    except:
        pass


# Connect to positioner

from smaract import connexion_smaract as sm
smaract = sm.smaract_class(calibrate=False)




import autoscript_toolkit.vision as vision_toolkit
from autoscript_toolkit.template_matchers import *

# class MyTemplateMatcher(TemplateMatcher):
#     def match(self, image: AdornedImage, template: AdornedImage) -> ImageMatch:

#         # CUSTOM TEMPLATE MATCHING CODE SHOULD BE PLACED HERE

#         calculated_center = Point(1536//2, 1024//2)
#         calculated_score = 0.3

#         # returns structure containing values calculated by the custom logic
#         match = ImageMatch(center=calculated_center, score=calculated_score)
#         return match

# template_matcher = MyTemplateMatcher()

smaract.setpos_abs([0, 0, 0])
sleep(1)

quattro.imaging.set_active_view(2)
quattro.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)
# Take full frame image

settings = GrabFrameSettings(resolution="768x512", dwell_time=10e-6, reduced_area=Rectangle(0.25, 0.25, 0.5, 0.5))
image = quattro.imaging.grab_frame(settings)
quattro.imaging.start_acquisition()


smaract.setpos_abs([0, 1000, 0])
sleep(1)

# Take reduced area image
settings = GrabFrameSettings(resolution="1536x1024", dwell_time=10e-6)
template = quattro.imaging.grab_frame(settings)

smaract.setpos_abs([0, 0, 0])
quattro.imaging.start_acquisition()


# import cv2 as cv

# w = template.width
# h = template.height
# res = cv.matchTemplate(image.data, template.data, 0)
# min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)


# top_left = max_loc
# bottom_right = (top_left[0] + w, top_left[1] + h)

# print(bottom_right[0]-top_left[0], bottom_right[1]-top_left[1])

# cv.rectangle(image.data, top_left, bottom_right, 255, 2)

# plt.subplot(121)
# plt.imshow(res, cmap='gray')
# plt.subplot(122)
# plt.imshow(image.data, cmap='gray')

# plt.show()

# Locate feature from the template in the original image
template_matcher = HogMatcher(quattro)
# template_matcher = OpencvTemplateMatcher()
# template_matcher = DEFAULT_TEMPLATE_MATCHER
location = vision_toolkit.locate_feature(template, image, template_matcher)
location.print_all_information()
vision_toolkit.plot_match(template, image, location.center_in_pixels)


exit()