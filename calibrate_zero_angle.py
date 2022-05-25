'''
Go to the center of the grid
'''

from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *

import numpy as np

# Connect to microscope
quattro = SdbMicroscopeClient()
quattro.connect('localhost') # local connection (Support PC) or offline scripting

from smaract import connexion_smaract_64bits as sm
smaract = sm.smaract_class(calibrate=False)


# Save the current position as the center of the grid
position_zero = quattro.specimen.stage.current_position
zoom_zero = quattro.beams.electron_beam.horizontal_field_width.value

# Go to the upper side of the grid
quattro.specimen.stage.relative_move(StagePosition(y=150e-6))

# Zoom in
quattro.beams.electron_beam.horizontal_field_width.value = 200e-6

# Autofocus
quattro.auto_functions.run_auto_focus()

# Save the value of focus
focus_1 = quattro.beams.electron_beam.working_distance.value

# Go to the lower side of the grid
quattro.specimen.stage.relative_move(StagePosition(y=-2*150e-6))

# Autofocus
quattro.auto_functions.run_auto_focus()

# Save the value of focus
focus_2 = quattro.beams.electron_beam.working_distance.value

# Go to the center
quattro.specimen.stage.absolute_move(position_zero)

# Go to the initial zoom level
quattro.beams.electron_beam.horizontal_field_width.value = zoom_zero

# Calculate the value of angle
angle = np.arctan(focus_1/focus_2)

# Correct the angle
zede, igrec, _ = smaract.getpos()
smaract.setpos_abs([zede, igrec, angle])

# Zero angle on Smaract device
smaract.set_zero_position(2)