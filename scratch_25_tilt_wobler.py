import os
import time
import sys
from autoscript_sdb_microscope_client.structures import GrabFrameSettings
from autoscript_sdb_microscope_client.enumerations import ScanningResolution

try:
    sys.path.insert(1, r'D:\SharedData\LM LEBAS\Process_Integration')
    os.chdir(r'D:\SharedData\LM LEBAS\Process_Integration')
except:
    sys.path.insert(1, r'C:\Users\User\Documents\LM Lebas\Process_Integration')
    os.chdir(r'C:\Users\User\Documents\LM Lebas\Process_Integration')

import com_functions

dir_pi = os.getcwd()

microscope = com_functions.microscope().f
microscope.import_package_and_connexion()

positioner = com_functions.microscope().p
positioner.import_package_and_connexion()

os.chdir(dir_pi)

alpha = 40


pos = positioner.current_position()
print(pos)
positioner.absolute_move(y=pos[1] , z=pos[2], a=0)
time.sleep(0.5)
positioner.relative_move(da = alpha)

microscope.start_acquisition()
while True:
    positioner.relative_move(da = -2*alpha)
    time.sleep(0.5)
    positioner.relative_move(da = 2*alpha)
    time.sleep(0.5)

# while True:
#     positioner.absolute_move(y=pos[1] , z=pos[2], a = -alpha)
#     time.sleep(0.5)
#     positioner.absolute_move(y=pos[1] , z=pos[2], a = alpha)
#     time.sleep(0.5)

