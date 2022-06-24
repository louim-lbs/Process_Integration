
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *
import time
import numpy as np

# Connect to microscope
quattro = SdbMicroscopeClient()
quattro.connect() # local connection (Support PC) or offline scripting

settings = GrabFrameSettings(resolution="512x442",
                             dwell_time=10e-6,
                             bit_depth=16)

i = 0
t2_list = []
t3_list = []
while True:
    t1 = time.time()
    images = quattro.imaging.grab_frame(settings)
    t2 = time.time() - t1
    t2_list.append(t2)
    t1 = time.time()
    images.save('data/test/HAADF_' + str(i) + '.tif')
    t3 = time.time() - t1
    t3_list.append(t3)
    print(i, 'Acquisition time = ', round(t2, 2), 'Mean =', round(np.mean(t2_list), 2), '; Saving time = ', round(t3, 4), 'Mean =', round(np.mean(t3_list), 4))
