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


# microscope.relative_move(dx=0, dy=10e-6)
print(8.0920756e-05-7.9587102e-05)

