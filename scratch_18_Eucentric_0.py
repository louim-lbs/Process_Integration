import com_functions
import time

positioner = com_functions.SMARACT_MCS_3D()
positioner.import_package_and_connexion()

_, ygrec, zed, alpha, _ = positioner.current_position()


positioner.absolute_move(y=0, z=0, a=0)
