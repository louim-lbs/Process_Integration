from autoscript_sdb_microscope_client.structures import GrabFrameSettings, StagePosition
import numpy as np
import cv2 as cv
from numpy.core.fromnumeric import mean
from scipy import interpolate

def correct_eucentric(microscope, positioner, displacement, angle):
    ''' Calculate z and y parameters for postioner eucentric correction, correct it, correct microscope view and focus.

    Input:
        - Microscope control class (class).
        - Positioner control class (class).
        - Displacement vector of images in meters (list[float, float]).
        - Angle list according to images in degrees (list[float]).

    Output:
        - z relative parameter in meter (float).
        - y relative parameter in meter (float).

    Exemple:
        z0, y0 = correct_eucentric(microscope, positioner, displacement, angle)
            -> z0 = 0.000001, y0 = 0.000001
    '''
    angle_sort = sorted(angle)
    if angle_sort == angle:
        direction = 1
    else:
        direction = -1

    z0_ini, y0_ini, _ = positioner.getpos()

    if displacement == [[0,0]]:

        return z0_ini, y0_ini

    pas = 1000000 # 1° with smaract convention
    alpha = [i for i in range(int(angle_sort[0]/pas), int(angle_sort[-1]/pas)+1)]
    index_0 = alpha.index(0)

    finterpa = interpolate.CubicSpline([i/pas for i in angle_sort], [i[0] for i in displacement]) # i[0] -> displacement in x direction of images (vertical)
    displacement_y_interpa = finterpa(alpha)

    displacement_y_interpa_prime = [0]*len(displacement_y_interpa)

    ## z0 computation
    for j in range(1,len(displacement_y_interpa)-1):
        displacement_y_interpa_prime[j] = (displacement_y_interpa[j+1]-displacement_y_interpa[j-1])/((alpha[j+1]-alpha[j-1])*np.pi/180)
    displacement_y_interpa_prime[0] = displacement_y_interpa_prime[1]   # Edge effect correction
    displacement_y_interpa_prime[-1] = displacement_y_interpa_prime[-2] # Edge effect correction
    # del displacement_y_interpa_prime[-1] # Edge effect correction

    z0_calc = displacement_y_interpa_prime[index_0]

    ## yA computation
    y0_calc = [0]*len(displacement_y_interpa_prime)
    for i in range(index_0):
        y0_calc[i] = (displacement_y_interpa_prime[i] - z0_calc*np.cos(alpha[i]*np.pi/180))/(np.sin(alpha[i]*np.pi/180))
    for i in range(index_0+1, len(displacement_y_interpa_prime)): # derivative is not define for angle_sort=0
        y0_calc[i] = (displacement_y_interpa_prime[i] - z0_calc*np.cos(alpha[i]*np.pi/180))/(np.sin(alpha[i]*np.pi/180))
    del y0_calc[index_0] # delete not computed 0-angle_sort value from the result list

    # Adjust positioner position
    positioner.setpos_rel([z0_calc*1e9, direction*mean(y0_calc)*1e9, 0])

    # Adjust microscope stage position
    microscope.specimen.stage.relative_move(StagePosition(y=direction*mean(y0_calc))) ####################Check this, sign for contre-positive image check?
    # microscope.specimen.stage.relative_move(StagePosition(y=y0*1e-9))

    # Adjust focus because z0 move
    # microscope.auto_functions.run_auto_focus()
    # Or
    microscope.beams.electron_beam.working_distance.value += z0_calc


    # Check limits
    return z0_calc, mean(y0_calc) #################### relative move in meters

def match(image_master, image_template, grid_size = 5, ratio_template_master = 0.9, ratio_master_template_patch = 0, speed_factor = 0):
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

    displacement_vector = np.array([[0,0]])
    corr_trust = np.array(0)

    for i in range(grid_size):
        for j in range(grid_size):
            template_patch_xA = (height_master - height_template)//2 + (i)*template_patch_size[0]
            template_patch_yA = (width_master  - width_template)//2  + (j)*template_patch_size[1]
            template_patch_xB = (height_master - height_template)//2 + (i+1)*template_patch_size[0]
            template_patch_yB = (width_master  - width_template)//2  + (j+1)*template_patch_size[1]

            template_patch = image_template[int(template_patch_xA):int(template_patch_xB),
                                            int(template_patch_yA):int(template_patch_yB)]

            corr_scores = cv.matchTemplate(image_master, template_patch, cv.TM_CCOEFF_NORMED)

            _, max_val, _, max_loc = cv.minMaxLoc(corr_scores)

            dx = template_patch_xA - max_loc[1]
            dy = template_patch_yA - max_loc[0]

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
    hfw = microscope.beams.electron_beam.horizontal_field_width.value # meters
    angle_step0 = 1000000
    angle_step =  1000000             # udegrees
    angle_max  = 10000000             # udegrees
    precision  =   100e-9             # nanometers or pixels ? End condition with magnification ?
    eucentric_error = 0
    resolution="512x442" # Bigger pixels means less noise and better match
    image_width = int(resolution[:resolution.find('x')])
    image_height = int(resolution[-resolution.find('x'):])
    settings = GrabFrameSettings(resolution=resolution, dwell_time=10e-6, bit_depth=16)
    image_euc = np.zeros((2, image_height, image_width))
    displacement = [[0,0]]
    angle = [0]
    z0 = 0
    y0 = 0

    # HAADF analysis
    microscope.imaging.set_active_view(3)

    multiplicator = 1
    image_euc[0] = microscope.imaging.grab_multiple_frames(settings)[2].data
    # positioner.setpos_abs([z0, y0, angle_step])
    positioner.setpos_rel([0, 0, angle_step])

    while abs(eucentric_error) > precision or positioner.angle_convert_Smaract2SI(positioner.getpos()[2]) < angle_max:
        print(eucentric_error, precision, positioner.angle_convert_Smaract2SI(positioner.getpos()[2]), angle_step)
        #### Deal with positioner error
        ####################
        
        image_euc[1] = microscope.imaging.grab_multiple_frames(settings)[2].data
        dx_pix, dy_pix, corr_trust = match(image_euc[1], image_euc[0])

        if corr_trust <= 0.3: # 0.3 empirical value. Need to be optimized
            ############
            ### Increase dwell time
            ############
            '''If match is not good'''
            if angle_step >= 100000:
                '''Decrease angle step up to 0.1 degree'''
                positioner.setpos_rel([0, 0, -multiplicator*angle_step])
                angle_step /= 2
            else:
                '''Zoom out x2'''
                z0, y0 = correct_eucentric(microscope, positioner, displacement, angle)
                microscope.beams.electron_beam.horizontal_field_width.value *= 2
                image_euc[0] = microscope.imaging.grab_multiple_frames(settings)[2].data
                angle_step = angle_step0
                positioner.setpos_rel([0, 0, angle_step])
            continue

        dx_si = dx_pix*hfw/image_width
        dy_si = dy_pix*hfw/image_width

        displacement.append([displacement[-1][0] + dx_si, displacement[-1][1] + dy_si])
        angle.append(positioner.angle_convert_Smaract2SI(positioner.getpos()[2]))

        eucentric_error = sum([i[0] for i in displacement])

        if abs(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])) >= angle_max:
            '''If out of the angle range'''
            if multiplicator == 1:
                '''Start again with negative angles'''
                z0, y0 = correct_eucentric(microscope, positioner, displacement, angle)
                multiplicator = -1
                displacement = [[0,0]]
                angle = [0]
                image_euc[0] = microscope.imaging.grab_multiple_frames(settings)[2].data
                angle_step = angle_step0
                positioner.setpos_rel([0, 0, multiplicator*angle_step])
            elif multiplicator == -1:
                '''Zoom in x2'''
                z0, y0 = correct_eucentric(microscope, positioner, displacement, angle)
                multiplicator = 1
                microscope.beams.electron_beam.horizontal_field_width.value /= 2
                image_euc[0] = microscope.imaging.grab_multiple_frames(settings)[2].data
                angle_step = angle_step0
                positioner.setpos_abs([0, 0, multiplicator*angle_step])
            continue

        positioner.setpos_rel([0, 0, multiplicator*angle_step])
        image_euc[0] = np.ndarray.copy(image_euc[1])

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