import os
import time
import sys
from autoscript_sdb_microscope_client.structures import GrabFrameSettings
from autoscript_sdb_microscope_client.enumerations import ScanningResolution

sys.path.insert(1, r'D:\SharedData\LM LEBAS\Process_Integration')
os.chdir(r'D:\SharedData\LM LEBAS\Process_Integration')

import com_functions2

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

