
from copy import deepcopy
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *

from threading import Thread, Lock
from time import sleep
from tifffile import imsave


def image(micro):
    i = 0
    image_prev = []
    while True:
        # images = micro.imaging.grab_multiple_frames(settings)
        image = micro.imaging.get_image()
        if len(image_prev) == 0:
            image_prev = deepcopy(image.data)
        if set(image.data[0]) != set(image_prev[0]):
            imsave('data/test/HAADF_' + str(i) + '.tif', image.data)
            image_prev = deepcopy(image.data)
            print(i)
            i += 1

def drift(micro):
    sign = 1
    sleep(1)
    while True:
        beamshift_x, beamshift_y =   micro.beams.electron_beam.beam_shift.value
        micro.beams.electron_beam.beam_shift.value = Point(x=beamshift_x + sign*1e-6, y=beamshift_y + sign*1e-6)
        print(sign)
        sign *= -1
        sleep(0.2)

# Connect to microscope
quattro_1 = SdbMicroscopeClient()
quattro_1.connect('localhost') # local connection (Support PC) or offline scripting

quattro_2 = SdbMicroscopeClient()
quattro_2.connect('localhost')

settings = GrabFrameSettings(resolution='1536x1024', dwell_time=100e-5, bit_depth=16)


print(quattro_1, quattro_2)
# create threads
t1 = Thread(target=image, args=(quattro_1,))
t2 = Thread(target=drift, args=(quattro_2,))

# start the threads
t1.start()
t2.start()

# wait for the threads to complete
t1.join()
t2.join()

