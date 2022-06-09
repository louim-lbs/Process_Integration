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

microscope = com_functions.microscope().f
microscope.import_package_and_connexion()

positioner = com_functions.microscope().p
positioner.import_package_and_connexion()

# Lauch GUI
os.chdir(dir_pi)

root = GUI.tk.Tk()
GUI.App(root, microscope, positioner)
root.mainloop()
    
