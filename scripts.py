from autoscript_sdb_microscope_client.structures import GrabFrameSettings, Point, StagePosition
import numpy as np
import cv2 as cv
from scipy import interpolate
from scipy.optimize import curve_fit
import os
import matplotlib.pyplot as plt
import logging
import time
from shutil import copyfile
from copy import deepcopy

def fft(img):
    rows, cols = img.shape
    nrows = cv.getOptimalDFTSize(rows)
    ncols = cv.getOptimalDFTSize(cols)
    right = ncols - cols
    bottom = nrows - rows
    img = cv.copyMakeBorder(img, 0, bottom, 0, right, cv.BORDER_CONSTANT, value=0)
    
    # Compute FFT
    image_fft     = np.fft.fftshift(cv.dft(np.float32(img), flags=cv.DFT_COMPLEX_OUTPUT))
    image_fft_mag = 20*np.log(cv.magnitude(image_fft[:,:,0], image_fft[:,:,1]))
    return image_fft_mag

def find_ellipse(img):
    plt.imshow(img, 'gray')
    
    img = cv.morphologyEx(img, cv.MORPH_CLOSE, cv.getStructuringElement(cv.MORPH_RECT, (5, 5))) # 5
    img = cv.morphologyEx(img, cv.MORPH_DILATE, cv.getStructuringElement(cv.MORPH_RECT, (3, 3))) # 3
    img = cv.medianBlur(img, 75)
    
    contours, _ = cv.findContours(img, mode=cv.RETR_LIST, method=cv.CHAIN_APPROX_NONE)
    if len(contours) != 0:
        ind = np.argmax([len(cont) for cont in contours])
        contours = contours[:ind] + contours[ind+1:]
        if len(contours) == 0:
            print('no contour found')
            return ((0, 0), (0, 0), 0)
        ind = np.argmax([len(cont) for cont in contours])

        cont = contours[ind]
        if len(cont) < 5:
            print('len contour < 5', len(contours))
            # plt.imshow(img)
            # plt.show()
            pass

        elps = cv.fitEllipse(cont)
        # plt.imshow(img, 'gray', alpha=0.1)
        plt.plot([i[0][0] for i in cont], [i[0][1] for i in cont], alpha = 0.7)

        u =     elps[0][0]        # x-position of the center
        v =     elps[0][1]        # y-position of the center
        a =     elps[1][0]/2        # radius on the x-axis
        b =     elps[1][1]/2        # radius on the y-axis
        t_rot = elps[2]*np.pi/180 # rotation angle

        t = np.linspace(0, 2*np.pi, 100)
        Ell = np.array([a*np.cos(t) , b*np.sin(t)])  
            #u,v removed to keep the same center location
        R_rot = np.array([[np.cos(t_rot) , -np.sin(t_rot)],[np.sin(t_rot) , np.cos(t_rot)]])  
            #2-D rotation matrix

        Ell_rot = np.zeros((2,Ell.shape[1]))
        for i in range(Ell.shape[1]):
            Ell_rot[:,i] = np.dot(R_rot,Ell[:,i])

        plt.plot( u+Ell_rot[0,:] , v+Ell_rot[1,:],'r', alpha = 0.7)
        plt.savefig('images/ellipse/' + str(time.time()) + '.tif')
        plt.clf()
        # plt.show()
        return elps
    else:
        print('no contour found')
        # plt.imshow(img, 'gray')
        # plt.show()
    return ((0, 0), (0, 0), 0)

def function_displacement(x, z, y, R, x2, x3):
    x = [i*np.pi/180 for i in x]
    return y*(1-np.cos(x)) + z*np.sin(x) + R*(1-np.sin(np.multiply(x, x2))) + x3

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
    
    angle_sort = sorted(angle)
    if angle_sort == angle:
        direction = 1
    else:
        direction = -1
        displacement.reverse()

    logging.info('direction' + str(direction))
    
    z0_ini, y0_ini, _ = positioner.getpos()
    logging.info('z0_ini, y0_ini =' + str(z0_ini) + str(y0_ini))

    if displacement == [[0,0]]:
        return z0_ini, y0_ini

    pas    = 1000000 # 1° with smaract convention
    alpha  = [i/pas for i in range(int(angle_sort[0]), int(angle_sort[-1]+1), int(pas/20))]

    offset = displacement[min(range(len(angle_sort)), key=lambda i: abs(angle_sort[i]))][0]

    displacement_filt = np.array([i[0]-offset for i in displacement])
    
    finterpa               = interpolate.PchipInterpolator([i/pas for i in angle_sort], displacement_filt)
    displacement_y_interpa = finterpa(alpha)

    res, cov         = curve_fit(f=function_displacement, xdata=alpha, ydata=displacement_y_interpa, p0=[0,0,0,5,0], bounds=(-1e7, 1e7))
    z0_calc, y0_calc, R_calc, x2_calc, x3_calc = res
    stdevs           = np.sqrt(np.diag(cov))

    logging.info('z0 =' + str(z0_calc) + '+-' + str(stdevs[0]) + 'y0 = ' + str(direction*y0_calc) + '+-' + str(stdevs[1]) + 'R = ' + str(R_calc) + '+-' + str(stdevs[2]) + 'x2 = ' + str(x2_calc) + '+-' + str(stdevs[3]) + 'x3 = ' + str(x3_calc) + '+-' + str(stdevs[4]))
    print('z0 =', z0_calc, '+-', stdevs[0], 'y0 = ', direction*y0_calc, '+-', stdevs[1])
    
    plt.plot([i/pas for i in angle_sort], [i[0]-offset for i in displacement], 'green')
    plt.plot(alpha, displacement_y_interpa, 'blue')
    plt.plot(alpha, function_displacement(alpha, *res), 'red')
    plt.savefig('data/tmp/' + str(time.time()) + 'correct_eucentric.png')
    plt.show()
    
    # Adjust positioner position
    positioner.setpos_rel([z0_calc, direction*y0_calc, 0])

    # Adjust microscope stage position
    microscope.specimen.stage.relative_move(StagePosition(y=1e-9*direction*y0_calc)) ####################Check this, sign for contre-positive image check?
    microscope.beams.electron_beam.working_distance.value += z0_calc*1e-9

    # Check limits
    return z0_calc, y0_calc #################### relative move in meters

def match(image_master, image_template, grid_size = 5, ratio_template_master = 0.9, ratio_master_template_patch = 0, speed_factor = 0, resize_factor = 1):
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
    image_master   = cv.resize(image_master,   (0, 0), fx=resize_factor, fy=resize_factor)
    image_template = cv.resize(image_template, (0, 0), fx=resize_factor, fy=resize_factor)

    image_master   = np.float32(image_master)
    image_template = np.float32(image_template)

    height_master, width_master = image_master.shape

    height_template, width_template = int(ratio_template_master*height_master), int(ratio_template_master*width_master)

    template_patch_size = (height_template//grid_size,
                            width_template//grid_size)

    displacement_vector = np.array([[0,0]])
    corr_trust = np.array(0)

    for i in range(grid_size):
        for j in range(grid_size):
            template_patch_xA      = (height_master - height_template)//2 + (i)*template_patch_size[0]
            template_patch_yA      = (width_master  - width_template)//2  + (j)*template_patch_size[1]
            template_patch_xB      = (height_master - height_template)//2 + (i+1)*template_patch_size[0]
            template_patch_yB      = (width_master  - width_template)//2  + (j+1)*template_patch_size[1]

            template_patch         = image_template[int(template_patch_xA):int(template_patch_xB),
                                                    int(template_patch_yA):int(template_patch_yB)]

            corr_scores            = cv.matchTemplate(image_master, template_patch, cv.TM_CCOEFF_NORMED)

            _, max_val, _, max_loc = cv.minMaxLoc(corr_scores)

            dx                     = (template_patch_xA - max_loc[1])*resize_factor
            dy                     = (template_patch_yA - max_loc[0])*resize_factor

            displacement_vector    = np.append(displacement_vector, [[dx, dy]], axis=0)
            corr_trust             = np.append(corr_trust, max_val)

    displacement_vector = np.delete(displacement_vector,0,0)
    dx_tot              = displacement_vector[:,0]
    dy_tot              = displacement_vector[:,1]

    # plt.plot(dx_tot)
    # plt.plot(dy_tot)

    for k in range(2): # Delete incoherent values
        mean_x  = np.mean(dx_tot)
        mean_y  = np.mean(dy_tot)
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
    if z0 == None or y0 == None:
        return 1
    hfw             = microscope.beams.electron_beam.horizontal_field_width.value # meters
    angle_step0     =  2000000
    angle_step      =  2000000  # udegrees
    angle_max       = 10000000  # udegrees
    precision       = 5         # pixels
    eucentric_error = 0
    resolution      = "512x442" # Bigger pixels means less noise and better match
    image_width     = int(resolution[:resolution.find('x')])
    image_height    = int(resolution[-resolution.find('x'):])
    settings        = GrabFrameSettings(resolution=resolution, dwell_time=10e-6, bit_depth=16)
    image_euc       = np.zeros((2, image_height, image_width))
    displacement    = [[0,0]]
    angle           = [positioner.angle_convert_Smaract2SI(positioner.getpos()[2])]
    direction       = 1
    logging.info('z0' + str(z0) + 'y0' + str(y0) + 'hfw' + str(hfw) + 'angle_step0' + str(angle_step0) + 'angle_step' + str(angle_step) + 'angle_max' + str(angle_max) + 'precision' + str(precision) + 'resolution' + str(resolution) + 'settings' + str(settings) + 'angle' + str(angle))

    # HAADF analysis
    microscope.imaging.set_active_view(3)

    positioner.setpos_abs([z0, y0, 0])
    
    img_tmp      = microscope.imaging.grab_multiple_frames(settings)[2]
    image_euc[0] = img_tmp.data
    img_tmp.save('data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])/1000000)) + '.tif')

    positioner.setpos_rel([0, 0, angle_step])

    while abs(eucentric_error) > precision or positioner.angle_convert_Smaract2SI(positioner.getpos()[2]) < angle_max:
        logging.info('eucentric_error =' + str(round(eucentric_error)) + 'precision =' + str(precision) + 'current angle =' + str(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])) + 'angle_max =' + str(angle_max))
        print(       'eucentric_error =', round(eucentric_error), 'precision =', precision, 'current angle =', positioner.angle_convert_Smaract2SI(positioner.getpos()[2]), 'angle_max =', angle_max)
        
        img_tmp      = microscope.imaging.grab_multiple_frames(settings)[2]
        image_euc[1] = img_tmp.data
        img_tmp.save('data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])/1000000)) + '.tif')
        
        dx_pix, dy_pix, corr_trust = match(image_euc[1], image_euc[0])

        if corr_trust <= 0.3: # 0.3 empirical value
            '''If match is not good'''
            #### Correct eucentric and go to other direction
            if angle_step >= 100000:
                logging.info('Decrease angle step')
                print(       'Decrease angle step')
                '''Decrease angle step up to 0.1 degree'''
                positioner.setpos_rel([0, 0, -2*direction*angle_step])
                positioner.setpos_rel([0, 0, +1*direction*angle_step]) # Two moves to prevent direction-change approximations
                angle_step /= 2
            else:
                logging.info('Error doing eucentric. Tips: check your acquisition parameters (mainly dwell time) or angle range.')
                return 1
            continue

        dx_si = 1e9*dx_pix*hfw/image_width
        dy_si = 1e9*dy_pix*hfw/image_width

        logging.info('dx_pix, dy_pix' + str(dx_pix) + str(dy_pix) + 'dx_si, dy_si' + str(dx_si) + str(dy_si))
        print(       'dx_pix, dy_pix', dx_pix, dy_pix, 'dx_si, dy_si', dx_si, dy_si)

        displacement.append([displacement[-1][0] + dx_si, displacement[-1][1] + dy_si])
        angle.append(positioner.angle_convert_Smaract2SI(positioner.getpos()[2]))

        eucentric_error += abs(dx_pix)

        if abs(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])) >= angle_max - 10000: # 0.010000 degree of freedom
            '''If out of the angle range'''
            z0, y0 = correct_eucentric(microscope, positioner, displacement, angle)
            logging.info('Start again with negative angles')
            print(       'Start again with negative angles')
            
            displacement  = [[0,0]]
            positioner.setpos_rel([0, 0, direction*angle_step])
            zed, ygrec, _ = positioner.getpos()
            positioner.setpos_abs([zed, ygrec, direction*angle_max])
            
            direction      *= -1
            angle           = [positioner.angle_convert_Smaract2SI(positioner.getpos()[2])]
            eucentric_error = 0
            microscope.auto_functions.run_auto_cb()
            
            ### Test increase angle
            if 2*angle_max <= 50000000:
                angle_step *= 1.5
                angle_max  *= 1.5
            else:
                angle_max   = 50000000
                angle_step  =  4000000
            
            img_tmp = microscope.imaging.grab_multiple_frames(settings)[2]
            image_euc[0] = img_tmp.data
            img_tmp.save('data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.angle_convert_Smaract2SI(positioner.getpos()[2])/1000000)) + '.tif')
            positioner.setpos_rel([0, 0, direction*angle_step])
            continue

        positioner.setpos_rel([0, 0, direction*angle_step])
        image_euc[0] = np.ndarray.copy(image_euc[1])

    pos = positioner.getpos()
    positioner.setpos_abs([pos[1], pos[2], 0])
    logging.info('Done eucentrixx')
    print(       'Done eucentrixx')
    copyfile('last_execution.log', 'data/tmp/log' + str(time.time()) + '.txt')
    return 0

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
    
    Return:
        - success or error code (int).

    Exemple:
        tomo_status = tomo_acquisition(micro_settings, smaract_settings, drift_correction=False)
            -> 0
    '''
    pos = positioner.getpos()
    if None in pos:
        return 1
    
    if bit_depth == 16:
        dtype_number = 65536
    elif bit_depth == 8:
        dtype_number = 255

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

    image_width  = int(resolution[:resolution.find('x')])
    image_height = int(resolution[-resolution.find('x'):])
    
    path = work_folder + images_name + '_' + str(round(time.time()))
    os.makedirs(path, exist_ok=True)

    settings = GrabFrameSettings(resolution=resolution, dwell_time=dwell_time, bit_depth=bit_depth)
    microscope.beams.electron_beam.angular_correction.tilt_correction.turn_on()
    
    anticipation_x = 0
    anticipation_y = 0
    correction_x   = 0
    correction_y   = 0

    for i in range(nb_images):
        tangle = positioner.angle_convert_Smaract2SI(positioner.getpos()[2])
        microscope.beams.electron_beam.angular_correction.specimen_pretilt.value = 1e-6*tangle*np.pi/180 # Tilt correction for e- beam

        print(i, tangle)
        logging.info(str(i) + str(positioner.getpos()[2]))
        
        images = microscope.imaging.grab_multiple_frames(settings)
        images[0].save(path + '/SE_'    + str(images_name) + '_' + str(i) + '_' + str(round(tangle/100000)) + '.tif')
        images[1].save(path + '/BF_'    + str(images_name) + '_' + str(i) + '_' + str(round(tangle/100000)) + '.tif')
        images[2].save(path + '/HAADF_' + str(images_name) + '_' + str(i) + '_' + str(round(tangle/100000)) + '.tif')
        positioner.setpos_rel([0, 0, direction*tilt_increment])
        
        img = images[2].data
        if drift_correction == True and i > 0:
            hfw = microscope.beams.electron_beam.horizontal_field_width.value
            dy_pix, dx_pix, _        =   match(img, images_prev[2].data, resize_factor=0.5)
            dx_si                    = - dx_pix * hfw / image_width
            dy_si                    =   dy_pix * hfw / image_width
            correction_x             = - dx_si + correction_x
            correction_y             = - dy_si + correction_y
            anticipation_x          +=   correction_x
            anticipation_y          +=   correction_y
            beamshift_x, beamshift_y =   microscope.beams.electron_beam.beam_shift.value
            microscope.beams.electron_beam.beam_shift.value = Point(x=beamshift_x + correction_x + anticipation_x,
                                                                    y=beamshift_y + correction_y + anticipation_y)
            beamshift_x, beamshift_y = microscope.beams.electron_beam.beam_shift.value

        images_prev      = deepcopy(images)

    print('Tomography is a Succes')
    return 0

def record(microscope, positioner, work_folder='data/record/', images_name='image', resolution='1536x1024', bit_depth=16, dwell_time=0.2e-6, drift_correction:bool=False, focus_correction:bool=False) -> int:
    ''' 
    '''
    pos = positioner.getpos()
    if None in pos:
        return 1

    image_width  = int(resolution[:resolution.find('x')])
    image_height = int(resolution[-resolution.find('x'):])
    
    path = work_folder + images_name + '_' + str(round(time.time()))
    os.makedirs(path, exist_ok=True)

    settings = GrabFrameSettings(resolution=resolution, dwell_time=dwell_time, bit_depth=bit_depth)
    microscope.beams.electron_beam.angular_correction.tilt_correction.turn_on()
    
    anticipation_x = 0
    anticipation_y = 0
    correction_x   = 0
    correction_y   = 0
    i              = 0

    while True:
        tangle = positioner.angle_convert_Smaract2SI(positioner.getpos()[2])
        microscope.beams.electron_beam.angular_correction.specimen_pretilt.value = 1e-6*tangle*np.pi/180 # Tilt correction for e- beam

        print(i, tangle)
        logging.info(str(i) + str(positioner.getpos()[2]))
        
        images = microscope.imaging.grab_multiple_frames(settings)
        # images[0].save(path + '/SE_'    + str(images_name) + '_' + str(i) + '_' + str(round(tangle/100000)) + '.tif')
        images[1].save(path + '/BF_'    + str(images_name) + '_' + str(i) + '_' + str(round(tangle/100000)) + '.tif')
        images[2].save(path + '/HAADF_' + str(images_name) + '_' + str(i) + '_' + str(round(tangle/100000)) + '.tif')
                
        if drift_correction == True and i > 0:
            hfw = microscope.beams.electron_beam.horizontal_field_width.value
            dy_pix, dx_pix, _        =   match(images[2].data, images_prev[2].data, resize_factor=0.5)
            print('dy_pix', 'dx_pix', dy_pix, dx_pix)
            dx_si                    = - dx_pix * hfw / image_width
            dy_si                    =   dy_pix * hfw / image_width
            correction_x             = - dx_si + correction_x
            correction_y             = - dy_si + correction_y
            anticipation_x          +=   correction_x
            anticipation_y          +=   correction_y
            beamshift_x, beamshift_y =   microscope.beams.electron_beam.beam_shift.value
            microscope.beams.electron_beam.beam_shift.value = Point(x=beamshift_x + correction_x + anticipation_x,
                                                                    y=beamshift_y + correction_y + anticipation_y)
            beamshift_x, beamshift_y = microscope.beams.electron_beam.beam_shift.value

        images_prev = deepcopy(images)
        i += 1

    print('Tomography is a Succes')
    return 0