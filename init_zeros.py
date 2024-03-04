import os
import logging

dir_pi = os.getcwd()
logging.basicConfig(filename='last_execution.log', filemode='w', format='%(levelname)s:%(message)s', level=logging.INFO)

dir_pi = os.getcwd()



from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *
      

# Connexion

# Connect to microscope

quattro = SdbMicroscopeClient()

try:
    quattro.connect() # online connection
    SdbMicroscopeClient.InitState_status = property(lambda self: 0) # Or 1 if not connected
except:
    try:
        quattro.connect('localhost') # local connection (Support PC) or offline scripting
        SdbMicroscopeClient.InitState_status = property(lambda self: 0) # Or 1 if not connected
    except:
        SdbMicroscopeClient.InitState_status = property(lambda self: 1) # Or 0 if not connected


# Connect to positioner

from smaract_folder import connexion_smaract as sm
smaract = sm.smaract_class(calibrate=False)
os.chdir(dir_pi)
smaract.setpos_abs([0, 0, 0])

# quattro.imaging.set_active_view(3)

# # resolution="1536x1024"
# resolution="512x442"
# settings = GrabFrameSettings(resolution=resolution, dwell_time=10e-6, bit_depth=16)

# print(quattro.beams.electron_beam.horizontal_field_width.value)
# quattro.specimen.stage.relative_move(StagePosition(y=210105*1e-9))