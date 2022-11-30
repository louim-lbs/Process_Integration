import com_functions
import time

positioner = com_functions.SMARACT_MCS_3D()
positioner.import_package_and_connexion()

def absolute_move_with_autocorrect(y, z, a):
    """
    Move to a position with autocorrect
    """
    positioner.absolute_move(y=y, z=z, a=a)
    _, _, _, alpha2, _ = positioner.current_position()
    
    increment = 100e-6
    i = 0
    while (alpha2 < a-0.1 or alpha2 > a+0.1) and abs(i*increment) < 0.003:
        print("Autocorrecting")
        positioner.absolute_move(y=y, z=z - i*increment, a=alpha2)
        positioner.absolute_move(y=y, z=z - i*increment, a=a)
        _, _, _, alpha2, _ = positioner.current_position()
        i += 1
    if i != 0:
        positioner.absolute_move(y=y, z=z, a=a)
    return

_, ygrec, zed, alpha, _ = positioner.current_position()
absolute_move_with_autocorrect(y=ygrec, z=zed, a=0)
