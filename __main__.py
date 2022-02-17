''' Process Integration fot tomogram acquisition using Quattro ESEM and Smaract MCS-3D

Use Python 32-bits

@author: Louis-Marie Lebas
Updated on Dec 08 2021
'''

import os
import logging
from concurrent import futures 
thread_pool_executor = futures.ThreadPoolExecutor(max_workers=2)

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
# from smaract import connexion_smaract as sm
# smaract = sm.smaract_class(calibrate=False)

from smaract import connexion_smaract_64bits as sm
smaract = sm.smaract_class(calibrate=False)

# Lauch GUI
os.chdir(dir_pi)

global letsgo

from gui import GUI

def main_start():
    root = GUI.tk.Tk()
    GUI.App(root, quattro, smaract, thread_pool_executor)
    root.mainloop()
    
main_start()
