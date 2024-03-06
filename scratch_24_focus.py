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

# Lauch GUI
os.chdir(dir_pi)

min_focus = -6e-6
max_focus = 6e-6
nb_points = 20
ref_focus = microscope.focus()
resolution = '1024x884'
dwell_time = '1e-6'
bit_depth = 16

# name = 'Bis_Mag_10000_P_5_DW_1e-6_'

# path = 'data/focus/' + name + str(round(time.time())) + '_res_' + str(resolution)
# os.makedirs(path, exist_ok=True)


# settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_1536X1024, dwell_time=1e-6)
# image = microscope.quattro.imaging.grab_frame(settings)
# microscope.save(image, path + '/ref')
# for i in range(nb_points):
#     focus = min_focus + (max_focus - min_focus) * i / (nb_points - 1)
#     print(i, round(ref_focus + focus, 6))
#     microscope.focus(ref_focus + focus)
#     settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_1536X1024, dwell_time=1e-6)
#     image = microscope.quattro.imaging.grab_frame(settings)
#     microscope.save(image, path + '/focus_' + str(i))

while True:
    microscope.quattro.imaging.grab_frame(GrabFrameSettings(resolution=ScanningResolution.PRESET_1536X1024, dwell_time=1e-6))



