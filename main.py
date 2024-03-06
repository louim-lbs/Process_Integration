'''
Process Integration for tomogram acquisition using Quattro ESEM and Smaract MCS-3D

This Python script is designed for a 64-bit environment and controls the acquisition of tilt series
in an electron microscope. It utilizes the 'microscope' and 'positioner' components from 'com_functions' module,
and a GUI (Graphical User Interface) to interact with the user.

Author: L.-M. Lebas
Updated on Jul 27 2023
'''

import os
import logging
import sys

actual_path = os.getcwd()
sys.path.insert(1, actual_path)
os.chdir(actual_path)

import com_functions2  as com_functions # Importing custom functions related to microscope control
from gui import GUI   # Importing the GUI module

# Get the current working directory
dir_pi = os.getcwd()

# Configure logging to save messages in a log file
logging.basicConfig(filename='last_execution.log', filemode='w', format='%(levelname)s:%(message)s', level=logging.INFO)

# Initialize the microscope and positioner objects
microscope = com_functions.microscope().f
microscope.import_package_and_connexion()

positioner = com_functions.microscope().p
positioner.import_package_and_connexion()

# Launch the GUI
os.chdir(dir_pi)  # Set the current working directory back to the original directory

def on_closing():
    '''
    Function to execute when the GUI window is closed.
    It stops the microscope acquisition and resets the beam shift before exiting the program.
    '''
    try:
        microscope.start_acquisition()
        microscope.beam_shift(0, 0)
    except:
        pass
    print('Python closed')
    root.destroy()  # Destroy the GUI window
    exit(0)  # Exit the Python script

root = GUI.tk.Tk()  # Create the main GUI window
GUI.App(root, microscope, positioner)  # Initialize the application with the microscope and positioner objects
root.protocol("WM_DELETE_WINDOW", on_closing)  # Call on_closing() when the GUI window is closed
root.mainloop()  # Start the main event loop for the GUI
