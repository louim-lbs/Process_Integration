#!/usr/bin/env python

'''
Test imaging
'''


import copy
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *
import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
import time

microscope = SdbMicroscopeClient()
try:
        microscope.connect()
except:
        microscope.connect('localhost')

# img = microscope.imaging.get_image().data
# h,w = img.shape
# out = cv.VideoWriter('output2.avi', cv.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (w, h), 0)

microscope.beams.electron_beam.scanning.resolution.value = '1536x1024'
microscope.beams.electron_beam.scanning.dwell_time.value = 1e-6

microscope.imaging.start_acquisition()

wndtext = "image_rate"
wndtext2 = 'image_complete'
starttime = time.time()
n = 0
maxruntime=15 #stop recording after n seconds

img = microscope.imaging.get_image().data
img_prev_stamp = img[-1,:]

while (True):
        img = microscope.imaging.get_image().data
        # mdata = microscope.imaging.get_image()
        gray = img
        # out.write(gray)
        cv.imshow(wndtext,gray)
        # print(img_prev_stamp)
        # print(img[-1,:])
        if not (img_prev_stamp == img[-1,:]).all():
                cv.imshow(wndtext2,gray)
                img_prev_stamp = img[-1,:]
                print(n)

        runtime = time.time() - starttime
        print("Runtime {}, FPS {}".format(runtime,n/runtime))

        k = cv.waitKey(1) & 0xFF
        if k == 27:
                break
        if cv.getWindowProperty(wndtext, cv.WND_PROP_AUTOSIZE) < 1:
                break
        n = n + 1
        if (runtime > maxruntime):
                break

# out.release()
cv.destroyAllWindows()