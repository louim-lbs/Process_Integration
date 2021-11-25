import numpy as np
import cv2 as cv

def match(image1, image_master):
    ''' Match two images

    Input:

    Output:

    Exemple:

    '''
    image_width, image_height = image1.shape

    

    pixel_center_w = image_width//2
    pixel_center_h = image_height//2

    slave_size = 0.3

    zone_slave = (  int(pixel_center_h - slave_size*image_height//2),
                    int(pixel_center_w - slave_size*image_width //2),
                    int(pixel_center_h + slave_size*image_height//2),
                    int(pixel_center_w + slave_size*image_width //2))
    
    image_slave  = image1[zone_slave[0]:zone_slave[2], zone_slave[1]:zone_slave[3]]

    corr_scores = cv.matchTemplate(image_master, image_slave, cv.TM_CCOEFF_NORMED)

    delta_h, delta_w = np.unravel_index(corr_scores.argmax(), corr_scores.shape)

    print('delta_h, delta_w', delta_h, delta_w)

    # coordonnees du centre du fragment maitre dans image esclave entiere 
    pixel_center_w_master_in_slave = pixel_center_w - image_width//2  + delta_w + slave_size*image_width//2
    pixel_center_h_master_in_slave = pixel_center_h - image_height//2 + delta_h + slave_size*image_height//2
    
    print('pixel_center_w_master_in_slave, pixel_center_h_master_in_slave', pixel_center_w_master_in_slave, pixel_center_h_master_in_slave)
    
    # vecteur de deplacement en pixels :
    dw = -(pixel_center_w - pixel_center_w_master_in_slave)
    dh = pixel_center_h - pixel_center_h_master_in_slave

    print('Vecteur de déplacement selon l\'axe horizontal : ' + str(dw) + ' pixels')
    print('Vecteur de déplacement selon l\'axe vertical   : ' + str(dh) + ' pixels')

    import matplotlib.pyplot as plt
    fig=plt.figure()
    result = corr_scores
    img=plt.imshow(result,origin='lower')
    y,x = np.unravel_index(result.argmax(), result.shape)
    plt.plot(x,y,'ok')
    bar=plt.colorbar(img)
    plt.show()

    return dw, dh

from matplotlib import image

img1 = np.asarray(image.imread('images/cell_36.tif'))
img2 = np.asarray(image.imread('images/cell_37.tif'))

# results = []

# print('...')

# for i in range(100):
res = match(img1, img2)
#     results.append(res)

# for x in results:
#     if x != results[0]:
#         print('Not accurate')
#         break
# print('Accurate')
# print(results[1])

exit()

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
    hfw = microscope.beams.electron_beam.horizontal_field_width.value # meters
    angle_step = 5             # degrees
    angle_range = 100          # units
    precision = 100            # nanometers or fraction of image size ? End condition with magnification ?
    eucentric_error = int
    resolution="1536x1024"
    image_width = int(resolution[:resolution.find('x')])
    image_height = int(resolution[-resolution.find('x'):])
    settings = microscope.GrabFrameSettings(resolution=resolution, dwell_time=1e-6, bit_depth=16)
    image = np.array()

    if method == "Eucentric point model II":
        multiplicator = 1
        np.append(image, microscope.imaging.grab_multiple_frames(settings))
        while eucentric_error == int or (eucentric_error > precision or eucentric_error < image_height//2):
            positioner.setpos_abs([0, 0, multiplicator*angle_step])
            np.append(image, microscope.imaging.grab_multiple_frames(settings))
            # Try Match pictures and compute eucentric error
            match_status = match(image[-1], image[-2])




            if match_status != 0:
                # microscope.beams.electron_beam.horizontal_field_width.value = hfw*2
                # ou tenter un angle plus faible (d'abord)
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

    positioner.setpos_abs([0, 0, 0])
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