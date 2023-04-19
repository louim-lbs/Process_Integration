''' Process Integration for tomogram acquisition using Quattro ESEM and Smaract MCS-3D

Use Python 64-bits

@author: Louis-Marie Lebas
Updated on Jun 06 2022  
'''

import os
import logging

import sys
# insert at 1, 0 is the script path (or '' in REPL)

try:
    sys.path.insert(1, r'C:\Users\Public\Documents\Lebas\Process_Integration')
    os.chdir(r'C:\Users\Public\Documents\Lebas\Process_Integration')
except:
    try:
        sys.path.insert(1, r'D:\SharedData\LM LEBAS\Process_Integration')
        os.chdir(r'D:\SharedData\LM LEBAS\Process_Integration')
    except:
        sys.path.insert(1, r'C:\Users\User\Documents\LM Lebas\Process_Integration')
        os.chdir(r'C:\Users\User\Documents\LM Lebas\Process_Integration')

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

def on_closing():
    try:
        microscope.start_acquisition()
        microscope.beam_shift(0, 0)
    except:
        pass
    print('Python closed')
    root.destroy()
    exit(0)

root = GUI.tk.Tk()
GUI.App(root, microscope, positioner)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()

