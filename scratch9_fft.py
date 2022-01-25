from autoscript_sdb_microscope_client.structures import GrabFrameSettings, Point, StagePosition
from cv2 import MORPH_ERODE
import numpy as np
import cv2 as cv
from scipy import interpolate
from scipy.optimize import curve_fit
import os
import matplotlib.pyplot as plt
import logging
import time
from shutil import copyfile
import copy
import numpy.linalg as linalg

def fft_treh_filt(img, threshold=150):
    # Compute FFT
    # cv.imshow('img', img)
    image_fft     = np.fft.fftshift(cv.dft(np.float32(img)))#, flags=cv.DFT_COMPLEX_OUTPUT))
    print(image_fft.shape)
    cv.imshow('image_fft', image_fft)
    cv.waitKey()
    image_fft_mag = 20*np.log(cv.magnitude(image_fft[:,0], image_fft[:,1]))
    cv.imshow('image_fft_mag', image_fft_mag)
    cv.waitKey()
    exit()
    # Threshold images
    image_fft_mag_tresh = cv.threshold(np.uint8(image_fft_mag), threshold, 255, cv.THRESH_BINARY)
    cv.imshow('image_fft_mag_tresh', image_fft_mag_tresh)
    cv.waitKey()
    # Delete isolated pixels
    image_fft_mag_tresh_comp = cv.bitwise_not(image_fft_mag_tresh)
    cv.imshow('image_fft_mag_tresh_comp', image_fft_mag_tresh_comp)
    cv.waitKey()

    kernel1 = np.array([[0, 0, 0,],
                        [0, 1, 0] ,
                        [0, 0, 0]], np.uint8)
    kernel2 = np.array([[1, 1, 1,],
                        [1, 0, 1] ,
                        [1, 1, 1]], np.uint8)

    hitormiss1 = cv.morphologyEx(image_fft_mag_tresh,      cv.MORPH_ERODE, kernel1)
    hitormiss2 = cv.morphologyEx(image_fft_mag_tresh_comp, cv.MORPH_ERODE, kernel2)
    hitormiss = cv.bitwise_and(hitormiss1, hitormiss2)
    hitormiss_comp = cv.bitwise_not(hitormiss)
    image_fft_mag_tresh_filt = cv.bitwise_and(image_fft_mag_tresh, image_fft_mag_tresh, mask=hitormiss_comp)
    
    return image_fft_mag_tresh_filt

def find_ellipse(img):
    _, contours, _ = cv.findContours(img, mode=cv.RETR_EXTERNAL, method=cv.CHAIN_APPROX_NONE)
    
    if len(contours) != 0:
        for cont in contours:
            if len(cont) < 5:
                break
            elps = cv.fitEllipse(cont)
            return elps
    return None

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
    # plt.plot(dy_tot)
    # plt.show()

    return np.mean(dx_tot), np.mean(dy_tot), np.mean(corr_trust)

def tomo_acquisition(microscope, positioner, work_folder='data/tomo/', images_name='image', resolution='1536x1024', bit_depth=16, dwell_time=0.2e-6, tilt_increment=2000000, tilt_end=60000000, drift_correction:bool=False, focus_correction:bool=False) -> int:
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
    if None in pos:
        return 1

    if positioner.angle_convert_Smaract2SI(pos[2]) > 0:
        direction = -1
        if tilt_end > 0:
            tilt_end *= -1
    else:
        direction = 1
        if tilt_end < 0:
            tilt_end *= -1
    print(dwell_time)
    nb_images = int((abs(pos[2])+abs(tilt_end))/tilt_increment + 1)

    print(tilt_increment, tilt_end)
    
    path = work_folder + images_name + '_' + str(round(time.time()))
    os.makedirs(path, exist_ok=True)

    settings = GrabFrameSettings(resolution=resolution, dwell_time=dwell_time, bit_depth=bit_depth)
    
    anticipation_x = 0
    anticipation_y = 0
    correction_x = 0
    correction_y = 0

    for i in range(nb_images):
        print(i, positioner.angle_convert_Smaract2SI(positioner.getpos()[2]))
        logging.info(str(i) + str(positioner.getpos()[2]))
        
        images = microscope.imaging.grab_multiple_frames(settings)
        # images[0].save(path + '/SE_'   + str(images_name) + '_' + str(i) + '_' + str(round(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])/100000)) + '.tif')
        # images[1].save(path + '/BF_'   + str(images_name) + '_' + str(i) + '_' + str(round(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])/100000)) + '.tif')
        # images[2].save(path + '/HAADF_' + str(images_name) + '_' + str(i) + '_' + str(round(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])/100000)) + '.tif')
        positioner.setpos_rel([0, 0, direction*tilt_increment])
        ###### Drift correction
        if drift_correction==True and i > 0:
            hfw = microscope.beams.electron_beam.horizontal_field_width.value
            image_width = int(resolution[:resolution.find('x')])
            dy_pix, dx_pix, _ = match(images[2].data, images_prev[2].data)
            dx_si = - dx_pix*hfw/image_width
            dy_si = dy_pix*hfw/image_width
            correction_x = - dx_si + correction_x
            correction_y = - dy_si + correction_y
            anticipation_x += correction_x
            anticipation_y += correction_y
            beamshift_x, beamshift_y = microscope.beams.electron_beam.beam_shift.value
            microscope.beams.electron_beam.beam_shift.value = Point(x=beamshift_x + correction_x + anticipation_x,
                                                                    y=beamshift_y + correction_y + anticipation_y)
            beamshift_x, beamshift_y = microscope.beams.electron_beam.beam_shift.value

        if focus_correction == True and i > 0:
            
            fft_1 = fft_treh_filt(images_prev[2].data, threshold=150)
            fft_2 = fft_treh_filt(images[2].data,      threshold=150)
            
            cv.imshow('fft_1', fft_1)
            cv.imshow('fft_2', fft_1)

            elps_1 = find_ellipse(fft_1)
            elps_2 = find_ellipse(fft_2)

            print(elps_1)
            print(elps_2)



        images_prev = copy.deepcopy(images)

    print('Tomography is a Succes')
    return 0