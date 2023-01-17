from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *
import time
import numpy as np
import cv2 as cv

# Connect to microscope
quattro = SdbMicroscopeClient()
quattro.connect() # local connection (Support PC) or offline scripting

settings = GrabFrameSettings(resolution='512x442',
                             dwell_time=1e-6,
                             bit_depth=8)

images = quattro.imaging.grab_frame(settings)


  
_, bw_img = cv2.threshold(images.data, 70, 255, cv2.THRESH_BINARY)
  
cv2.imshow("Binary", bw_img)
cv2.waitKey(0)
cv2.destroyAllWindows()