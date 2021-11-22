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

# quattro = SdbMicroscopeClient()
# try:
#     quattro.connect('localhost')  # local connection (Support PC) or offline scripting
# except:
#     quattro.connect()  # online connection

from smaract import connexion_smaract as sm
smaract = sm.smaract_class(calibrate=False)


def set_eucentric(microscope, controller) -> int:
    ''' Set eucentric point according to the image centered features.

    Input:
        - None (bool).

    Return:
        - Success or error code (int).

    Exemple:
        set_eucentric_status = set_eucentric()
            -> 0    
    '''
    print('eucentrixx')
    return 0

def tomo_acquisition(micro_settings:list, smaract_settings:list, drift_correction:bool=False) -> int:
    ''' Acquire set of images according to input parameters.

    Input:
        - Microscope parameters "micro_settings":
            - work folder
            - images naming
            - image resolution
            - bit depht
            - dwell time
        - Smaract parameters:
            - tilt increment
            - tilt to begin from
    
    Return:
        - success or error code (int).

    Exemple:
        tomo_status = tomo_acquisition(micro_settings, smaract_settings, drift_correction=False)
            -> 0
    '''
    return 0


os.chdir(dir_pi)

from gui import GUI

root = GUI.tk.Tk()
app = GUI.App(root, smaract)
root.mainloop()

# set_eucentric(quattro, smaract)


