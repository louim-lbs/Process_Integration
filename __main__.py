''' Process Integration fot tomogram acquisition using Quattro ESEM and Smaract MCS-3D

Use Python 32-bits

@author: Louis-Marie Lebas
Updated on Dec 08 2021
'''

import os
import logging
import threading

dir_pi = os.getcwd()
logging.basicConfig(filename='last_execution.log', filemode='w', format='%(levelname)s:%(message)s', level=logging.INFO)

from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *

### Connexion

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
from smaract import connexion_smaract as sm
smaract = sm.smaract_class(calibrate=False)

# Lauch GUI
os.chdir(dir_pi)

global letsgo


from gui import GUI

def main_start():
    letsgo = True
    root = GUI.tk.Tk()
    GUI.App(root, quattro, smaract, letsgo)

    # thread_z_up   = threading.Thread(target=GUI.App.z_up)
    # thread_z_down = threading.Thread(target=GUI.App.z_down)
    # thread_y_up   = threading.Thread(target=GUI.App.y_up)
    # thread_y_down = threading.Thread(target=GUI.App.y_down)
    # thread_t_up   = threading.Thread(target=GUI.App.t_up)
    # thread_t_down = threading.Thread(target=GUI.App.t_down)
    # thread_t_zero = threading.Thread(target=GUI.App.t_zero)

    # thread_z_up.start()
    # thread_z_down.start()
    # thread_y_up.start()
    # thread_y_down.start()
    # thread_t_up.start()
    # thread_t_down.start()
    # thread_t_zero.start()

    root.mainloop()
    # thread_z_up.join()
    # thread_z_down.join()
    # thread_y_up.join()
    # thread_y_down.join()
    # thread_t_up.join()
    # thread_t_down.join()
    # thread_t_zero.join()

main_start()
