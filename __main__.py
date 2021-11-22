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
# try:
#     quattro.connect('localhost') # local connection (Support PC) or offline scripting
# except:
#     try:
#         quattro.connect() # online connection
#         imp = 1
#     except:
#         pass




from smaract import connexion_smaract as sm
smaract = sm.smaract_class(calibrate=False)




os.chdir(dir_pi)

from gui import GUI

root = GUI.tk.Tk()
app = GUI.App(root, quattro, smaract)
root.mainloop()



