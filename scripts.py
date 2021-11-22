
def set_eucentric(microscope, positioner) -> int:
    ''' Set eucentric point according to the image centered features.

    Input:
        - Microscope control class (class).
        - Positioner control class (class).

    Return:
        - Success or error code (int).

    Exemple:
        set_eucentric_status = set_eucentric()
            -> 0    
    '''
    method = "Eucentric point model II"
    magnification_start = 5000 # units
    angle_step = 5             # degrees
    angle_range = 100          # units
    precision = 100            # nanometers or fraction of image size ? End condition with magnification ?
    eucentric_error = int

    if method == "Eucentric point model II":
        multiplicator = 1
        # Take picture 1
        while eucentric_error == int or (eucentric_error > precision or eucentric_error < image_height//2):
            # Move relative multiplicator*angle_step
            # Take picture 2
            # Match pictures and compute eucentric error
            if match is not OK:
                # Set magnification -= 500
                # Take picture 1
                pass
            # Add value to the curve model
            if abs(eucentric_error) > image_height//2:
                # Check stability?
                # Check limits
                # Try to correct eucentric position (z (prior) and y)
                # Adjust stage position according y value along the y axis.
                # Adjust focus
                # Reset eucentric error
                # Take picture 1
                pass
            if abs(current_angle) > angle_range//2:
                if multiplicator == -1:
                    break
                # Move to angle zero
                # Reset eucentric error
                # Take picture 1
                multiplicator = -1

    # Deal magnification adjustements according step and if it find solution or not.         


    pos = positioner.getpos()
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
    print('Tomographixx')
    return 0