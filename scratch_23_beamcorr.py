import os
import logging
import time
import sys

sys.path.insert(1, r'D:\SharedData\LM LEBAS\Process_Integration')
os.chdir(r'D:\SharedData\LM LEBAS\Process_Integration')

import com_functions

dir_pi = os.getcwd()

microscope = com_functions.microscope().f
microscope.import_package_and_connexion()

positioner = com_functions.microscope().p
positioner.import_package_and_connexion()

# Lauch GUI
os.chdir(dir_pi)

microscope.tilt_correction(value = tangle*np.pi/180)

