#!/usr/bin/env python

'''
Test imaging
'''


from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *
import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
import time

microscope = SdbMicroscopeClient()
try:
        microscope.connect('localhost')
except:
        microscope.connect()

img = microscope.imaging.get_image().data
h,w = img.shape
out = cv.VideoWriter('output2.avi', cv.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (w, h), 0)

wndtext = "image"
starttime = time.time()
n = 0
maxruntime=10 #stop recording after n seconds

while (True):
        img = microscope.imaging.get_image().data
        mdata = microscope.imaging.get_image()
        gray = img
        out.write(gray)
        cv.imshow(wndtext,gray)

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

out.release()
cv.destroyAllWindows()