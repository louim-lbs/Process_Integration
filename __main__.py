''' Process Integration fot tomogram acquisition using Quattro ESEM and Smaract MCS-3D

Use Python 32-bits

@author: Louis-Marie Lebas
Created on Fri Oct 29 2021
'''

### Imports

import os
import logging

dir_pi = os.getcwd()
logging.basicConfig(filename='last_execution.log', filemode='w', format='%(levelname)s:%(message)s', level=logging.INFO)



imp = 0
while True:
    try:
        from autoscript_sdb_microscope_client import SdbMicroscopeClient
        from autoscript_sdb_microscope_client.enumerations import *
        from autoscript_sdb_microscope_client.structures import *
        break
    except:
        if imp == 0:
            logging.info('Autoscript import failed... Trying to install pillow and cv2 requirements and trying again')
            #!pip install pillow # type: ignore
            #!pip install opencv-python # type: ignore
            imp = 1
        if imp != 0:
            logging.info('Something went wrong. Check your Autoscript installation')

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

from gui import GUI

root = GUI.tk.Tk()
app = GUI.App(root, quattro, smaract)
root.mainloop()



