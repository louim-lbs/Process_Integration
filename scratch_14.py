
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *

from threading import Thread, Lock
from time import sleep


def image(micro):
    while True:
        images = micro.imaging.grab_multiple_frames(settings)

def drift(micro):
    sign = 1
    sleep(1)
    while True:
        beamshift_x, beamshift_y =   micro.beams.electron_beam.beam_shift.value
        micro.beams.electron_beam.beam_shift.value = Point(x=beamshift_x + sign*1e-6, y=beamshift_y + sign*1e-6)
        print(sign)
        sign *= -1
        sleep(0.2)

quattro_2 = SdbMicroscopeClient()
quattro_2.connect()

settings = GrabFrameSettings(resolution='1536x1024', dwell_time=1e-5, bit_depth=16)


# create threads
t2 = Thread(target=drift, args=(quattro_2,))

# start the threads
t2.start()

# wait for the threads to complete
t2.join()

