from autoscript_sdb_microscope_client.structures import GrabFrameSettings, StagePosition
import numpy as np
import cv2 as cv
from numpy.core.fromnumeric import mean, std
from scipy import interpolate
from scipy.optimize import curve_fit
import os
import matplotlib.pyplot as plt
import logging
import time
from shutil import copyfile

def function_displacement(x, z, y):
    x = [i*np.pi/180 for i in x]
    return y*(1-np.cos(x)) + z*np.sin(x)

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
    logging.info('displacement' + str(displacement))
    logging.info('angle' + str(angle))
    print(displacement)
    print(angle)
    angle_sort = sorted(angle)
    if angle_sort == angle:
        direction = 1
    else:
        direction = -1
        displacement.reverse()

    logging.info('direction' + str(direction))
    print('direction', direction)
    z0_ini, y0_ini, _ = positioner.getpos()
    logging.info('z0_ini, y0_ini =' + str(z0_ini) + str(y0_ini))
    print('z0_ini, y0_ini =', z0_ini, y0_ini)

    if displacement == [[0,0]]:
        return z0_ini, y0_ini

    pas = 1000000 # 1° with smaract convention
    alpha = [i/pas for i in range(int(angle_sort[0]), int(angle_sort[-1]+1), int(pas/20))]

    offset = displacement[min(range(len(angle_sort)), key=lambda i: abs(angle_sort[i]))][0]

    displacement_filt = np.array([i[0]-offset for i in displacement])
    
    finterpa = interpolate.PchipInterpolator([i/pas for i in angle_sort], displacement_filt) # i[0] -> displacement in x direction of images (vertical)
    displacement_y_interpa = finterpa(alpha)

    res, cov = curve_fit(f=function_displacement, xdata=alpha, ydata=displacement_y_interpa, p0=[0,0], bounds=(-1e7, 1e7))
    z0_calc, y0_calc = res
    stdevs = np.sqrt(np.diag(cov))

    logging.info('z0 =' + str(z0_calc) + '+-' + str(stdevs[0]) + 'y0 = ' + str(direction*y0_calc) + '+-' + str(stdevs[1]))
    print('z0 =', z0_calc, '+-', stdevs[0], 'y0 = ', direction*y0_calc, '+-', stdevs[1])
    
    # Adjust positioner position
    positioner.setpos_rel([z0_calc, direction*y0_calc, 0])

    # Adjust microscope stage position
    microscope.specimen.stage.relative_move(StagePosition(y=1e-9*direction*y0_calc)) ####################Check this, sign for contre-positive image check?
    microscope.beams.electron_beam.working_distance.value += z0_calc*1e-9

    plt.plot([i/pas for i in angle_sort], [i[0]-offset for i in displacement], 'green')
    plt.plot(alpha, displacement_y_interpa, 'blue')
    plt.plot(alpha, function_displacement(alpha, *res), 'red')
    plt.savefig('data/tmp/' + str(time.time()) + 'correct_eucentric.png')
    plt.show()

    # Check limits
    return z0_calc, y0_calc #################### relative move in meters

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

    # plt.plot(dx_tot)

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

    # plt.plot(dx_tot)
    # plt.show()

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
    angle_step0 = 2000000
    angle_step =  2000000             # udegrees
    angle_max  = 10000000             # udegrees
    precision  =   100             # nanometers or pixels ? End condition with magnification ?
    eucentric_error = 0
    resolution="512x442" # Bigger pixels means less noise and better match
    image_width = int(resolution[:resolution.find('x')])
    image_height = int(resolution[-resolution.find('x'):])
    settings = GrabFrameSettings(resolution=resolution, dwell_time=10e-6, bit_depth=16)
    image_euc = np.zeros((2, image_height, image_width))
    displacement = [[0,0]]
    angle = [positioner.angle_convert_Smaract2SI(positioner.getpos()[2])]
    multiplicator = 1
    logging.info('z0' + str(z0) + 'y0' + str(y0) + 'hfw' + str(hfw) + 'angle_step0' + str(angle_step0) + 'angle_step' + str(angle_step) + 'angle_max' + str(angle_max) + 'precision' + str(precision) + 'resolution' + str(resolution) + 'settings' + str(settings) + 'angle' + str(angle))

    # HAADF analysis
    microscope.imaging.set_active_view(3)

    positioner.setpos_abs([z0, y0, 0])
    
    img_tmp = microscope.imaging.grab_multiple_frames(settings)[2]
    image_euc[0] = img_tmp.data
    img_tmp.save('data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])/1000000)) + '.tif')

    positioner.setpos_rel([0, 0, angle_step])

    while abs(eucentric_error) > precision or positioner.angle_convert_Smaract2SI(positioner.getpos()[2]) < angle_max:
        logging.info('eucentric_error =' + str(round(eucentric_error)) + 'precision =' + str(precision) + 'current angle =' + str(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])) + 'angle_max =' + str(angle_max))
        print('eucentric_error =', round(eucentric_error), 'precision =', precision, 'current angle =', positioner.angle_convert_Smaract2SI(positioner.getpos()[2]), 'angle_max =', angle_max)
        #### Deal with positioner error
        ####################
        
        img_tmp = microscope.imaging.grab_multiple_frames(settings)[2]
        image_euc[1] = img_tmp.data
        img_tmp.save('data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])/1000000)) + '.tif')
        
        dx_pix, dy_pix, corr_trust = match(image_euc[1], image_euc[0])

        if corr_trust <= 0.3: # 0.3 empirical value. Need to be optimized
            ############
            ### Increase dwell time
            ############
            '''If match is not good'''
            if angle_step >= 100000:
                logging.info('Decrease angle step')
                print('Decrease angle step')
                '''Decrease angle step up to 0.1 degree'''
                positioner.setpos_rel([0, 0, -multiplicator*angle_step])
                angle_step /= 2
            else:
                '''Zoom out x2'''
                logging.info('Zoom out x2')
                print('Zoom out x2')
                multiplicator = 1
                displacement = [[0,0]]
                angle_step = angle_step0
                positioner.setpos_rel([0, 0, angle_step])

                angle = [positioner.angle_convert_Smaract2SI(positioner.getpos()[2])]
                eucentric_error = 0
                z0, y0 = correct_eucentric(microscope, positioner, displacement, angle)
                microscope.beams.electron_beam.horizontal_field_width.value *= 2
                microscope.auto_functions.run_auto_cb()
                hfw = microscope.beams.electron_beam.horizontal_field_width.value # meters
                img_tmp = microscope.imaging.grab_multiple_frames(settings)[2]
                image_euc[0] = img_tmp.data
                img_tmp.save('data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])/1000000)) + '.tif')
            continue

        dx_si = 1e9*dx_pix*hfw/image_width
        dy_si = 1e9*dy_pix*hfw/image_width

        logging.info('dx_pix, dy_pix' + str(dx_pix) + str(dy_pix) + 'dx_si, dy_si' + str(dx_si) + str(dy_si))
        print('dx_pix, dy_pix', dx_pix, dy_pix, 'dx_si, dy_si', dx_si, dy_si)

        displacement.append([displacement[-1][0] + dx_si, displacement[-1][1] + dy_si])
        angle.append(positioner.angle_convert_Smaract2SI(positioner.getpos()[2]))

        eucentric_error += abs(dx_si)

        if abs(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])) >= angle_max:
            '''If out of the angle range'''
            if multiplicator == 1:
                '''Start again with negative angles'''
                z0, y0 = correct_eucentric(microscope, positioner, displacement, angle)
                logging.info('Start again with negative angles')
                print('Start again with negative angles')
                multiplicator = -1
                displacement = [[0,0]]
                # angle_step = angle_step0
                positioner.setpos_rel([0, 0, -1*angle_step])
                positioner.setpos_rel([0, 0, -0.5*angle_step])
                
                angle = [positioner.angle_convert_Smaract2SI(positioner.getpos()[2])]
                eucentric_error = 0
                microscope.auto_functions.run_auto_cb()
                img_tmp = microscope.imaging.grab_multiple_frames(settings)[2]
                image_euc[0] = img_tmp.data
                img_tmp.save('data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])/1000000)) + '.tif')
                positioner.setpos_rel([0, 0, -1.5*angle_step])
            elif multiplicator == -1:
                '''Zoom in x2'''
                z0, y0 = correct_eucentric(microscope, positioner, displacement, angle)
                logging.info('Zoom in x2')
                print('Zoom in x2')
                multiplicator = 1
                displacement = [[0,0]]
                # angle_step = angle_step0
                positioner.setpos_rel([0, 0, 1*angle_step])
                positioner.setpos_rel([0, 0, 0.5*angle_step])

                angle = [positioner.angle_convert_Smaract2SI(positioner.getpos()[2])]
                eucentric_error = 0
                microscope.auto_functions.run_auto_cb()

                # microscope.beams.electron_beam.horizontal_field_width.value /= 2
                hfw = microscope.beams.electron_beam.horizontal_field_width.value # meters
                
                ### Test increase angle
                if 2*angle_max <= 55000000:
                    angle_step *= 2
                    angle_max *= 2
                else:
                    angle_max = 55000000
                    angle_step = 5000000

                img_tmp = microscope.imaging.grab_multiple_frames(settings)[2]
                image_euc[0] = img_tmp.data
                img_tmp.save('data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])/1000000)) + '.tif')
                positioner.setpos_rel([0, 0, 1.5*angle_step])
            continue

        positioner.setpos_rel([0, 0, multiplicator*angle_step])
        image_euc[0] = np.ndarray.copy(image_euc[1])

    pos = positioner.getpos()
    positioner.setpos_abs([pos[1], pos[2], 0])
    logging.info('Done eucentrixx')
    copyfile('last_execution.log', 'data/tmp/log' + str(time.time()) + '.txt')
    print('Done eucentrixx')
    return 0

def tomo_acquisition(microscope, positioner, work_folder='data/tomo/', images_name='image', resolution='1536x1024', bit_depth=16, dwell_time=10e6, tilt_increment=2000000, drift_correction:bool=False) -> int:
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
            # - tilt to begin from
    
    Return:
        - success or error code (int).

    Exemple:
        tomo_status = tomo_acquisition(micro_settings, smaract_settings, drift_correction=False)
            -> 0
    '''
    pos = positioner.getpos()
    nb_images = int(pos[2]//(tilt_increment/1000000) + 1)

    os.makedirs('./data/tomo/' + images_name + str(round(time.time())), exist_ok=True)

    for i in range(nb_images):
        print(i, positioner.getpos()[2])
        ###### Drift correction
        settings = GrabFrameSettings(resolution=resolution, dwell_time=dwell_time, bit_depth=bit_depth)
        images = microscope.imaging.grab_multiple_frames(settings)
        # images[0].save(work_folder + 'SE'   + str(images_name) + str(i) + '.tif')
        # images[1].save(work_folder + 'BF'   + str(images_name) + str(i) + '.tif')
        images[2].save(work_folder + 'HAADF' + str(images_name) + str(i) + '.tif')
        positioner.setpos_rel([0, 0, -tilt_increment])

    print('Tomographixx is a Succes')
    return 0