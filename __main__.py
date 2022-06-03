''' Process Integration for tomogram acquisition using Quattro ESEM and Smaract MCS-3D

Use Python 64-bits

@author: Louis-Marie Lebas
Updated on May 25 2022  
'''

import os
import logging
import com_functions
from gui import GUI

dir_pi = os.getcwd()
logging.basicConfig(filename='last_execution.log', filemode='w', format='%(levelname)s:%(message)s', level=logging.INFO)

active_microscope = com_functions.microscope().f
active_microscope.import_package_and_connexion()

if active_microscope.microscope_type == 'ESEM':
    from smaract import connexion_smaract_64bits as sm
    positioner = sm.smaract_class(calibrate=False)
elif active_microscope.microscope_type == 'ETEM':
    positioner = 0

# Lauch GUI
os.chdir(dir_pi)

root = GUI.tk.Tk()
GUI.App(root, active_microscope, positioner)
root.mainloop()
    
