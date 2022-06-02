''' Process Integration for tomogram acquisition using Quattro ESEM and Smaract MCS-3D

Use Python 64-bits

@author: Louis-Marie Lebas
Updated on May 25 2022  
'''

import os
import logging
import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, 'G:\Mon Drive\Travail\Doctorat\Projets\Process_Integration')
os.chdir(r'G:\Mon Drive\Travail\Doctorat\Projets\Process_Integration')

dir_pi = os.getcwd()
print(dir_pi)
logging.basicConfig(filename='last_execution.log', filemode='w', format='%(levelname)s:%(message)s', level=logging.INFO)

from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *

### Connexion
# Connect to microscope
quattro = SdbMicroscopeClient()

try:
    quattro.connect('localhost') # local connection (Support PC) or offline scripting
    SdbMicroscopeClient.InitState_status = property(lambda self: 0) # Or 1 if not connected
except:
    SdbMicroscopeClient.InitState_status = property(lambda self: 1) # Or 0 if not connected

from smaract import connexion_smaract_64bits as sm
smaract = sm.smaract_class(calibrate=False)
# Lauch GUI
os.chdir(dir_pi)

from gui import GUI
    
def main_start():
    root = GUI.tk.Tk()
    GUI.App(root, quattro, smaract)
    root.mainloop()
    
main_start()
