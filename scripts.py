from autoscript_sdb_microscope_client.structures import GrabFrameSettings
import numpy as np
import cv2 as cv

def correct_eucentric(microscope, positioner, displacement):
    # Check limits
    # Try to correct eucentric position (z (prior) and y)
    # Adjust stage position according y value along the y axis.
    # Adjust focus
    # Reset eucentric error
    return

def match(image_master, image_template, grid_size = 10, ratio_template_master = 0.5, ratio_master_template_patch = 0, speed_factor = 4):
    ''' Match two images

    Input:
        - image_master: image before the displacement (ndarray).
        - image_template: image after the displacement (nd_array).
        - grid_size: Computation resolution. Higher is more precise but slower (int).
        - ratio_template_master: Ratio of image_template used for computation. Between 0 and 1 (float).
        - ratio_master_template_patch: Ratio for master patch size from template patch. Is computed optimaly by default (float).
        - speed_factor: reduce master patch size for speed optimization. Decrease precision and is not recommended for high displacements (int).

    Output:
        - Displacement vector in pixels (list[float, float]).
        - Correlation coefficient between 0 and 1 (float).

    Exemple:
        res = match(img1, img2)
        print(res)
            -> ([20.0, 20.0], 0.9900954802437584)
    '''
    image_master = np.float32(image_master)
    image_template = np.float32(image_template)

    height_master, width_master = image_master.shape

    height_template, width_template = int(ratio_template_master*height_master), int(ratio_template_master*width_master)

    template_patch_size = (height_template//grid_size,
                            width_template//grid_size)

    # master_patch_size = (int(height_master - height_template + template_patch_size[0])//speed_factor,
    #                      int(width_master  - width_template  + template_patch_size[1])/speed_factor)
    
    # if ratio_master_template_patch != 0:
    #     if ratio_master_template_patch > max(master_patch_size[0], master_patch_size[1]):
    #         pass
    #     master_patch_size = (int(template_patch_size[0]*ratio_master_template_patch),
    #                          int(template_patch_size[1]*ratio_master_template_patch))

    displacement_vector = np.array([[0,0]])
    corr_trust = np.array(0)

    for i in range(grid_size):
        for j in range(grid_size):
            
            # master_patch_xA = (height_master - height_template)//2 - (master_patch_size[0] - template_patch_size[0])//2 + (i)*template_patch_size[0]
            # master_patch_yA = (width_master  - width_template)//2  - (master_patch_size[1] - template_patch_size[1])//2 + (j)*template_patch_size[1]
            # master_patch_xB = (height_master - height_template)//2 - (master_patch_size[0] - template_patch_size[0])//2 + (i)*template_patch_size[0] + master_patch_size[0]
            # master_patch_yB = (width_master  - width_template)//2  - (master_patch_size[1] - template_patch_size[1])//2 + (j)*template_patch_size[1] + master_patch_size[1]

            # master_patch = image_master[int(master_patch_xA):int(master_patch_xB),
            #                             int(master_patch_yA):int(master_patch_yB)]


            template_patch_xA = (height_master - height_template)//2 + (i)*template_patch_size[0]
            template_patch_yA = (width_master  - width_template)//2  + (j)*template_patch_size[1]
            template_patch_xB = (height_master - height_template)//2 + (i+1)*template_patch_size[0]
            template_patch_yB = (width_master  - width_template)//2  + (j+1)*template_patch_size[1]

            template_patch = image_template[int(template_patch_xA):int(template_patch_xB),
                                            int(template_patch_yA):int(template_patch_yB)]

            corr_scores = cv.matchTemplate(image_master, template_patch, cv.TM_CCOEFF_NORMED) # plein de param à modifier après pour que ça marche
            # corr_scores = cv.matchTemplate(master_patch, template_patch, cv.TM_CCOEFF_NORMED)

            _, max_val, _, max_loc = cv.minMaxLoc(corr_scores)

            dx = template_patch_xA - max_loc[1]
            dy = template_patch_yA - max_loc[0]

            # dx = (master_patch_size[0] - template_patch_size[0])//2 - max_loc[1]
            # dy = (master_patch_size[1] - template_patch_size[1])//2 - max_loc[0]

            displacement_vector = np.append(displacement_vector, [[dx, dy]], axis=0)

            corr_trust = np.append(corr_trust, max_val)

    displacement_vector = np.delete(displacement_vector,0,0)
    dx_tot = displacement_vector[:,0]
    dy_tot = displacement_vector[:,1]

    for k in range(2): # Delete incoherent values
        mean_x = np.mean(dx_tot)
        mean_y = np.mean(dy_tot)
        stdev_x = np.std(dx_tot)
        stdev_y = np.std(dy_tot)

        for d in dx_tot:
            if (d < mean_x - stdev_x) or (mean_x + stdev_x < d):
                dx_tot = np.delete(dx_tot, np.where(dx_tot==d))
        for d in dy_tot:
            if (d < mean_y - stdev_y) or (mean_y + stdev_y < d):
                dy_tot = np.delete(dy_tot, np.where(dy_tot==d))

    dx_tot = cv.blur(dx_tot, (1, dx_tot.shape[0]//4))
    dy_tot = cv.blur(dy_tot, (1, dy_tot.shape[0]//4))

    return np.mean(dx_tot), np.mean(dy_tot), np.mean(corr_trust)

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
    z0, y0, _ = positioner.getpos()
    positioner.setpos_abs([z0, y0, 0])
    hfw = microscope.beams.electron_beam.horizontal_field_width.value # meters
    angle_step0 = 2000000
    angle_step =  2000000             #  degrees
    angle_max  = 50000000             # udegrees
    precision  =     1000             # nanometers or pixels ? End condition with magnification ?
    eucentric_error = 0
    resolution="512x442" # Bigger pixels means less noise and better match
    image_width = int(resolution[:resolution.find('x')])
    image_height = int(resolution[-resolution.find('x'):])
    settings = GrabFrameSettings(resolution=resolution, dwell_time=1e-6, bit_depth=16)
    image_euc = np.zeros((2, image_height, image_width))
    displacement = []
    z0 = 0
    y0 = 0

    # HAADF analysis
    microscope.imaging.set_active_view(3)

    multiplicator = 1
    image_euc[0] = microscope.imaging.grab_multiple_frames(settings).data
    positioner.setpos_abs([z0, y0, angle_step])

    while eucentric_error > precision or positioner.getpos()[2] < angle_max:
        
        image_euc[1] = microscope.imaging.grab_multiple_frames(settings).data
        dx_pix, dy_pix, corr_trust = match(image_euc[1], image_euc[0])

        if corr_trust <= 0.3:
            if angle_step >= 100000: # 0.1 degrees
                angle_step /= 2
                positioner.setpos_rel([0, 0, -multiplicator*angle_step])
            else:
                z0, y0 = correct_eucentric(microscope, positioner, displacement)
                positioner.setpos_abs([z0, y0, 0])
                microscope.beams.electron_beam.horizontal_field_width.value = hfw*2
                image_euc[0] = microscope.imaging.grab_multiple_frames(settings).data
                angle_step = angle_step0
                positioner.setpos_abs([z0, y0, angle_step])
            continue
        
        dx_si = dx_pix*hfw/image_width
        dy_si = dy_pix*hfw/image_width
        displacement.append([dx_si, dy_si])
        eucentric_error = sum(displacement[1])


        current_pos = positioner.getpos()
        if abs(current_pos[2]) >= angle_max:
            if multiplicator == -1:
                
                break
            multiplicator = -1
            positioner.setpos_abs([z0, y0, 0])
            displacement = []
            image_euc[0] = microscope.imaging.grab_multiple_frames(settings).data
            angle_step = angle_step0
            positioner.setpos_abs([z0, y0, multiplicator*angle_step])
            

        positioner.setpos_rel([0, 0, multiplicator*angle_step])
        image_euc[0] = np.ndarray.copy(image_euc[1])

    # Deal magnification adjustements according step and if it find solution or not.         

    positioner.setpos_abs([z0, y0, 0])
    print('Done eucentrixx')
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