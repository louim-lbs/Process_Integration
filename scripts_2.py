import linecache
import sys
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
from tifffile import imread
from PIL import Image, ImageTk
import faiss
from threading import Lock, Condition

from com_functions import microscope

s_print_lock = Lock()

def number_format(number:float, decimals:int=2):
    if number == None:
        return 'None'
    return str('{:.{}e}'.format(float(number), decimals))

def PrintException():
    ''' https://stackoverflow.com/questions/14519177/python-exception-handling-line-number
    '''
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

def s_print(*a, **b):
    """Thread safe print function from: https://stackoverflow.com/questions/40356200/python-printing-in-multiple-threads"""
    s_print_lock.acquire()
    print(*a, **b)
    s_print_lock.release()

# Automatic brightness and contrast optimization with optional histogram clipping
def automatic_brightness_and_contrast(image, clip_hist_percent=1):
    '''
    from:
    https://stackoverflow.com/questions/56905592/automatic-contrast-and-brightness-adjustment-of-a-color-photo-of-a-sheet-of-pape
    '''
    # Calculate grayscale histogram
    hist = cv.calcHist([image],[0],None,[256],[0,256])
    hist_size = len(hist)
    
    # Calculate cumulative distribution from the histogram
    accumulator = []
    accumulator.append(float(hist[0]))
    for index in range(1, hist_size):
        accumulator.append(accumulator[index -1] + float(hist[index]))
    
    # Locate points to clip
    maximum = accumulator[-1]
    clip_hist_percent *= (maximum/100.0)
    clip_hist_percent /= 2.0
    
    # Locate left cut
    minimum_gray = 0
    while accumulator[minimum_gray] < clip_hist_percent:
        minimum_gray += 1
    
    # Locate right cut
    maximum_gray = hist_size -1
    while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
        maximum_gray -= 1
    
    # Calculate alpha and beta values
    alpha = 255 / (maximum_gray - minimum_gray)
    beta = -minimum_gray * alpha

    auto_result = cv.convertScaleAbs(image, alpha=alpha, beta=beta)
    return auto_result

def fft(img):
    rows, cols = img.shape
    nrows = cv.getOptimalDFTSize(rows)
    ncols = cv.getOptimalDFTSize(cols)
    right = ncols - cols
    bottom = nrows - rows
    img = cv.copyMakeBorder(img, 0, bottom, 0, right, borderType=cv.BORDER_CONSTANT, value=0)
    
    # Compute FFT
    image_fft     = np.fft.fftshift(cv.dft(np.float32(img), flags=cv.DFT_COMPLEX_OUTPUT))
    image_fft_mag = 20*np.log(cv.magnitude(image_fft[:,:,0], image_fft[:,:,1]))
    return image_fft_mag

def find_ellipse(img, save=False):
    if save:
        plt.imshow(img, 'gray')
    
    img = cv.morphologyEx(img, cv.MORPH_CLOSE, cv.getStructuringElement(cv.MORPH_RECT, (5, 5))) # 5
    img = cv.morphologyEx(img, cv.MORPH_DILATE, cv.getStructuringElement(cv.MORPH_RECT, (3, 3))) # 3
    img = cv.medianBlur(img, 75)
    
    contours, _ = cv.findContours(img, mode=cv.RETR_LIST, method=cv.CHAIN_APPROX_NONE)
    if len(contours) != 0:
        ind = np.argmax([len(cont) for cont in contours])
        contours = contours[:ind] + contours[ind+1:]
        if len(contours) == 0:
            s_print('no contour found')
            return ((0, 0), (0, 0), 0)
        ind = np.argmax([len(cont) for cont in contours])

        cont = contours[ind]
        if len(cont) < 5:
            s_print('len contour < 5', len(contours))
            if save:
                plt.imshow(img)
                # plt.show()
            pass

        elps = cv.fitEllipse(cont)
        # plt.imshow(img, 'gray', alpha=0.1)
        if save:
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

        if save:
            plt.plot( u+Ell_rot[0,:] , v+Ell_rot[1,:],'r', alpha = 0.7)
            plt.savefig('images/ellipse/' + str(time.time()) + '.tif')
            
            # plt.show()
            plt.clf()
        return elps
    else:
        s_print('no contour found')
        if save:
            plt.imshow(img, 'gray')
            # plt.show()
    return ((0, 0), (0, 0), 0)

def function_displacement(x, z, y, R):#, x2, x3):
    x = [i*np.pi/180 for i in x]
    return y*(1-np.cos(x)) + z*np.sin(x) + R*(1-np.sin(x))#np.multiply(x, x2))) + x3

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

    pas    = 1 # 1°
    alpha  = [i/pas for i in range(int(angle_sort[0]), int(angle_sort[-1]+1))]

    if microscope.microscope_type == 'ESEM':
        offset = displacement[min(range(len(angle_sort)), key=lambda i: abs(angle_sort[i]))][0]
        displacement_filt = np.array([i[0]-offset for i in displacement])
    else:
        offset = displacement[min(range(len(angle_sort)), key=lambda i: abs(angle_sort[i]))][1]
        displacement_filt = np.array([i[1]-offset for i in displacement])

    finterpa               = interpolate.PchipInterpolator([i/pas for i in angle_sort], displacement_filt)
    displacement_y_interpa = finterpa(alpha)

    res, cov         = curve_fit(f=function_displacement, xdata=alpha, ydata=displacement_y_interpa, p0=[0,0,0], bounds=(-1e7, 1e7))
    # z0_calc, y0_calc, R_calc, x2_calc, x3_calc = res
    z0_calc, y0_calc, R_calc = res
    stdevs           = np.sqrt(np.diag(cov))

    logging.info('z0 =' + str(z0_calc) + '+-' + str(stdevs[0]) + 'y0 = ' + str(-direction*y0_calc) + '+-' + str(stdevs[1]))# + 'R = ' + str(R_calc) + '+-' + str(stdevs[2]) + 'x2 = ' + str(x2_calc) + '+-' + str(stdevs[3]) + 'x3 = ' + str(x3_calc) + '+-' + str(stdevs[4]))
    s_print('z0 =', z0_calc, 'y0 = ', -direction*y0_calc)
    
    if microscope.microscope_type == 'ESEM':
        plt.plot([i/pas for i in angle_sort], [i[0]-offset for i in displacement], 'green')
    else:
        plt.plot([i/pas for i in angle_sort], [i[1]-offset for i in displacement], 'green')
    plt.plot(alpha, displacement_y_interpa, 'blue')
    plt.plot(alpha, function_displacement(alpha, *res), 'red')
    plt.savefig('data/tmp/' + str(time.time()) + 'correct_eucentric.png')
    plt.show()

    if microscope.microscope_type == 'ESEM':
        print('ESEM correction')
        positioner.relative_move(0, -direction*y0_calc, -z0_calc, 0, 0)
        microscope.relative_move(0, direction*y0_calc, 0, 0, 0)
        microscope.focus(z0_calc, 'rel') 
    elif microscope.microscope_type == 'ETEM':
        positioner.relative_move(0, -y0_calc, z0_calc, 0, 0)
        plt.plot(alpha, displacement_y_interpa, 'blue')
        plt.show()
        microscope.beam_shift(0, y0_calc, 'rel')
        plt.plot(alpha, displacement_y_interpa, 'blue')
        plt.show()
        microscope.image_shift(0, y0_calc, 'rel')
        microscope.focus(z0_calc, 'rel')
        plt.plot(alpha, displacement_y_interpa, 'blue')
        plt.show()
        #####################
        #####################
        #####################
    

def match(image_master, image_template, grid_size = 3, ratio_template_master = 0.9, ratio_master_template_patch = 0, speed_factor = 0, resize_factor = 1):
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
        s_print(res)
            -> ([20.0, 20.0], 0.9900954802437584)
    '''
    n = 51
    image_master   = cv.GaussianBlur(np.uint8(image_master), (n,n), 0)
    image_template = cv.GaussianBlur(np.uint8(image_template), (n,n), 0)
    
    image_master   = cv.resize(image_master,   (0, 0), fx=resize_factor, fy=resize_factor)
    image_template = cv.resize(image_template, (0, 0), fx=resize_factor, fy=resize_factor)

    height_master, width_master = image_master.shape

    height_template, width_template = int(ratio_template_master*height_master), int(ratio_template_master*width_master)

    template_patch_size = (height_template//grid_size,
                            width_template//grid_size)

    displacement_vector = np.array([[0,0]])
    corr_trust = np.array(0)

    t_temp = 0
    t_match = 0
    t_calc = 0
    t_append = 0
    for i in range(grid_size):
        for j in range(grid_size):
            t1 = time.time()
            template_patch_xA      = (height_master - height_template)//2 + (i)*template_patch_size[0]
            template_patch_yA      = (width_master  - width_template)//2  + (j)*template_patch_size[1]
            template_patch_xB      = (height_master - height_template)//2 + (i+1)*template_patch_size[0]
            template_patch_yB      = (width_master  - width_template)//2  + (j+1)*template_patch_size[1]

            template_patch         = image_template[int(template_patch_xA):int(template_patch_xB),
                                                    int(template_patch_yA):int(template_patch_yB)]

            t2 = time.time()
            t_temp += t2 - t1
            corr_scores            = cv.matchTemplate(image_master, template_patch, cv.TM_CCOEFF) #TM_CCOEFF_NORMED
            t3 = time.time()
            t_match += t3 - t2
            _, max_val, _, max_loc = cv.minMaxLoc(corr_scores)
            
            dx                     = (template_patch_xA - max_loc[1])*resize_factor
            dy                     = (template_patch_yA - max_loc[0])*resize_factor
            t4 = time.time()
            t_calc += t4 - t3
            displacement_vector    = np.append(displacement_vector, [[dx, dy]], axis=0)
            corr_trust             = np.append(corr_trust, max_val)
            t5 = time.time()
            t_append += t5 - t4

    # t_temp = t_temp/(grid_size**2)
    # t_match = t_match/(grid_size**2)
    # t_calc = t_calc/(grid_size**2)
    # t_append = t_append/(grid_size**2)
    #print('t_temp', t_temp, 't_match', t_match, 't_calc', t_calc, 't_append', t_append)

    corr_trust_x          = np.delete(corr_trust, 0)
    corr_trust_y          = deepcopy(corr_trust_x)
    displacement_vector = np.delete(displacement_vector,0,0)
    dx_tot              = displacement_vector[:,0]
    dy_tot              = displacement_vector[:,1]

    # plt.plot(dx_tot, '--r')
    # plt.plot(dy_tot, '--g')

    for k in range(2): # Delete incoherent values
        mean_x  = np.mean(dx_tot)
        mean_y  = np.mean(dy_tot)
        stdev_x = np.std(dx_tot)
        stdev_y = np.std(dy_tot)

        for d in dx_tot:
            if (d < mean_x - stdev_x) or (mean_x + stdev_x < d):
                corr_trust_x = np.delete(corr_trust_x, np.where(dx_tot==d))
                dx_tot = np.delete(dx_tot, np.where(dx_tot==d))
        for d in dy_tot:
            if (d < mean_y - stdev_y) or (mean_y + stdev_y < d):
                corr_trust_y = np.delete(corr_trust_y, np.where(dy_tot==d))
                dy_tot = np.delete(dy_tot, np.where(dy_tot==d))

    try:
        dx_tot = cv.blur(dx_tot, (1, dx_tot.shape[0]//4))
        dy_tot = cv.blur(dy_tot, (1, dy_tot.shape[0]//4))
    except:
        pass

    # plt.plot(dx_tot, 'red')
    # plt.plot(dy_tot, 'green')
    # plt.show()

    a = np.average(dx_tot.reshape((len(dx_tot),)), weights=corr_trust_x)
    b = np.average(dy_tot.reshape((len(dy_tot),)), weights=corr_trust_y)
    c = np.mean(np.array([np.mean(corr_trust_x), np.mean(corr_trust_y)]))
    return a, b, c

def match_by_features(img_template, img_master, mid_strips_template=0, mid_strips_master=0, resize=205, MIN_MATCH_COUNT = 20):
    if resize != -1:
        resize_factor = resize/img_master.shape[1]

        img_master   = cv.resize(img_master,   (0, 0), fx=resize_factor, fy=resize_factor)
        img_template = cv.resize(img_template, (0, 0), fx=resize_factor, fy=resize_factor)
    else:
        resize_factor = 1

    w, h = img_template.shape[::-1]
    sift = cv.SIFT_create()

    img_master = cv.cvtColor(img_master, cv.IMREAD_GRAYSCALE)

    t = time.time()
    sift = cv.SIFT_create(nfeatures=500)

    kp1, des1 = sift.detectAndCompute(img_template,None)
    kp2, des2 = sift.detectAndCompute(img_master,None)

    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks = 1)
    flann = cv.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1,des2,k=2)

    good = []
    for m,n in matches:
        if m.distance < 0.9*n.distance:
            good.append(m)

    if len(good)>MIN_MATCH_COUNT:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1,1,2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1,1,2)
        M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC,5.0)
        disp = cv.perspectiveTransform(np.float32([[0,0]]).reshape(-1,1,2),M)/resize_factor
        
    else:
        print('Not enough match to perform homography')
        return None
    
    return round(-disp[0,0,0]), round(disp[0,0,1]+mid_strips_master-mid_strips_template)

def remove_strips(img, dwell_time):
    img = np.asarray( img, dtype='int32')
    w, h = img.shape
    scores = np.zeros(w, dtype='int32')
    for i in range(w-1):
        scores[i] = np.sum(abs(img[i+1] - img[i]))
    mid_strips = np.argmax(scores) + int(0.0512/(dwell_time*w)) # 0.0512 is the time before the movement stabilizes itself. Empirically determined.
    return np.array(img[mid_strips:,:], dtype='uint8'), mid_strips

def set_eucentric_ESEM(microscope, positioner) -> int:
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
    x0, y0, z0, a0, _ = positioner.current_position()
    if z0 == None or y0 == None or a0 == None:
        s_print('Error. Positioner is not initialized.')
        return 1
    
    angle_step0     =  1
    angle_step      =  1  # °
    angle_max       = 10  # °
    precision       = 5   # pixels
    eucentric_error = 0
    resolution      = "512x442" # Bigger pixels means less noise and better match
    image_width     = int(resolution[:resolution.find('x')])
    image_height    = int(resolution[-resolution.find('x'):])
    dwell_time      = 10e-6
    bit_depth       = 16
    image_euc       = np.zeros((2, image_height, image_width))
    displacement    = [[0,0]]
    angle           = [a0]
    direction       = 1
    # logging.info('z0' + str(z0) + 'y0' + str(y0) + 'hfw' + str(hfw) + 'angle_step0' + str(angle_step0) + 'angle_step' + str(angle_step) + 'angle_max' + str(angle_max) + 'precision' + str(precision) + 'resolution' + str(resolution) + 'settings' + str(settings) + 'angle' + str(angle))

    # HAADF analysis
    if microscope.microscope_type == 'ESEM':
        microscope.quattro.imaging.set_active_view(3)
    microscope.start_acquisition()

    positioner.absolute_move(x0, y0, z0, 0, 0)

    img_tmp      = microscope.acquire_frame(resolution, dwell_time, bit_depth)
    image_euc[0] = microscope.image_array(img_tmp)
    path = 'data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.current_position()[3])/1000000)
    microscope.save(img_tmp, path)

    positioner.relative_move(0, 0, 0, angle_step, 0)
    hfw             = microscope.horizontal_field_view() # meters

    while abs(eucentric_error) > precision or positioner.current_position()[3] < angle_max:
        # logging.info('eucentric_error =' + str(round(eucentric_error)) + 'precision =' + str(precision) + 'current angle =' + str(positioner.current_position()[3]) + 'angle_max =' + str(angle_max))
        s_print(       'eucentric_error =', number_format(eucentric_error), 'precision =', number_format(precision), 'current angle =', number_format(positioner.current_position()[3]), 'angle_max =', number_format(angle_max))
        
        img_tmp      = microscope.acquire_frame(resolution, dwell_time, bit_depth)
        image_euc[1] = microscope.image_array(img_tmp)
        path = 'data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.current_position()[3]))
        microscope.save(img_tmp, path)
        
        dx_pix, dy_pix, corr_trust = match(image_euc[1], image_euc[0])

        if corr_trust <= 0.3: # 0.3 empirical value
            '''If match is not good'''
            #### Correct eucentric and go to other direction
            if angle_step >= 0.1:
                # logging.info('Decrease angle step')
                s_print(       'Decrease angle step')
                '''Decrease angle step up to 0.1 degree'''
                positioner.relative_move(0, 0, 0, -2*direction*angle_step, 0)
                positioner.relative_move(0, 0, 0, +1*direction*angle_step, 0) # Two moves to prevent direction-change approximations
                angle_step /= 2
            else:
                # logging.info('Error doing eucentric. Tips: check your acquisition parameters (mainly dwell time) or angle range.')
                return 1
            continue

        dx_si = dx_pix*hfw/image_width
        dy_si = dy_pix*hfw/image_width

        # logging.info('dx_pix, dy_pix' + str(dx_pix) + str(dy_pix) + 'dx_si, dy_si' + str(dx_si) + str(dy_si))
        s_print(       'dx_pix, dy_pix', number_format(dx_pix), number_format(dy_pix), 'dx_si, dy_si', number_format(dx_si), number_format(dy_si))

        displacement.append([displacement[-1][0] + dx_si, displacement[-1][1] + dy_si])
        angle.append(positioner.current_position()[3])

        if microscope.microscope_type == 'ESEM':
            eucentric_error += abs(dx_pix)
        else:
            eucentric_error += abs(dy_pix)

        if abs(positioner.current_position()[3]) >= angle_max - 0.01: # 0.010000 degree of freedom
            '''If out of the angle range'''
            correct_eucentric(microscope, positioner, displacement, angle)
            # logging.info('Start again with negative angles')
            s_print(       'Start again with negative angles')
            
            displacement  = [[0,0]]
            positioner.relative_move(0, 0, 0, direction*angle_step, 0)
            ixe, ygrec, zed, _, _ = positioner.current_position()
            positioner.absolute_move(ixe, ygrec, zed, direction*angle_max, 0)
            
            direction      *= -1
            angle           = [positioner.current_position()[3]]
            eucentric_error = 0
            
            if microscope.microscope_type == 'ESEM':
                microscope.auto_contrast_brightness()
            
            ### Test increase angle
            if 2*angle_max <= 50:
                angle_step *= 1.5
                angle_max  *= 1.5
            else:
                angle_max   = 50
                angle_step  =  2
            
            img_tmp = microscope.acquire_frame(resolution, dwell_time, bit_depth)
            image_euc[0] = microscope.image_array(img_tmp)
            path = 'data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.current_position()[3]))
            microscope.save(img_tmp, path)
            positioner.relative_move(0, 0, 0, direction*angle_step, 0)
            continue

        positioner.relative_move(0, 0, 0, direction*angle_step, 0)
        image_euc[0] = np.ndarray.copy(image_euc[1])

    ixe, ygrec, zed, _, _ = positioner.current_position()
    positioner.absolute_move(ixe, ygrec, zed, 0, 0)
    # logging.info('Done eucentrixx')
    s_print(       'Done eucentrixx')
    copyfile('last_execution.log', 'data/tmp/log' + str(time.time()) + '.txt')
    return 0

def set_eucentric_ESEM_2(microscope, positioner) -> int:
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
    x0, y0, z0, a0, _ = positioner.current_position()
    if z0 == None or y0 == None or a0 == None:
        s_print('Error. Positioner is not initialized.')
        return 1
    
    angle_step0     =  1
    angle_step      =  1  # °
    angle_max       = 10  # °
    precision       = 5   # pixels
    eucentric_error = 0
    resolution      = "512x442" # Bigger pixels means less noise and better match
    image_width     = int(resolution[:resolution.find('x')])
    image_height    = int(resolution[-resolution.find('x'):])
    dwell_time      = 10e-6
    bit_depth       = 16
    image_euc       = np.zeros((2, image_height, image_width))
    displacement    = [[0,0]]
    angle           = [a0]

    # HAADF analysis
    if microscope.microscope_type == 'ESEM':
        microscope.quattro.imaging.set_active_view(3)
    microscope.start_acquisition()

    positioner.absolute_move(x0, y0, z0, -2*angle_step, 0)
    positioner.absolute_move(x0, y0, z0, 0, 0)

    img_tmp      = microscope.acquire_frame(resolution, dwell_time, bit_depth)
    image_euc[0] = microscope.image_array(img_tmp)
    path = 'data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.current_position()[3])/1000000)
    microscope.save(img_tmp, path)

    positioner.relative_move(0, 0, 0, angle_step, 0)
    hfw          = microscope.horizontal_field_view() # meters

    while abs(eucentric_error) > precision or positioner.current_position()[3] < angle_max:
        s_print(       'eucentric_error =', number_format(eucentric_error), 'precision =', number_format(precision), 'current angle =', number_format(positioner.current_position()[3]), 'angle_max =', number_format(angle_max))
        
        img_tmp      = microscope.acquire_frame(resolution, dwell_time, bit_depth)
        image_euc[1] = microscope.image_array(img_tmp)
        path = 'data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.current_position()[3]))
        microscope.save(img_tmp, path)
        
        img_master, mid_strips_master = remove_strips(image_euc[0], dwell_time)
        img_template, mid_strips_template = remove_strips(image_euc[1], dwell_time)
        
        dx_pix, dy_pix = match_by_features(img_template, img_master, mid_strips_template, mid_strips_master, resize=-1)

        dx_si = dx_pix*hfw/image_width
        dy_si = dy_pix*hfw/image_width

        s_print(       'dx_pix, dy_pix', number_format(dx_pix), number_format(dy_pix), 'dx_si, dy_si', number_format(dx_si), number_format(dy_si))

        displacement.append([displacement[-1][0] + dx_si, displacement[-1][1] + dy_si])
        angle.append(positioner.current_position()[3])

        eucentric_error += abs(dx_pix)

        if abs(positioner.current_position()[3]) >= angle_max - 0.01: # 0.010000 degree of freedom
            '''If out of the angle range'''
            correct_eucentric(microscope, positioner, displacement, angle)
            s_print(       'Start again with negative angles')
            
            displacement  = [[0,0]]
            ixe, ygrec, zed, _, _ = positioner.current_position()
            positioner.absolute_move(ixe, ygrec, zed, -angle_step, 0)
            positioner.absolute_move(ixe, ygrec, zed, 0, 0)
            
            angle           = [positioner.current_position()[3]]
            eucentric_error = 0
            
            if microscope.microscope_type == 'ESEM':
                microscope.auto_contrast_brightness()
            
            ### Test increase angle
            if angle_max <= 50:
                angle_step *= 1.5
                angle_max  *= 1.5
            else:
                angle_max   = 50
                angle_step  =  2
            
            img_tmp = microscope.acquire_frame(resolution, dwell_time, bit_depth)
            image_euc[0] = microscope.image_array(img_tmp)
            path = 'data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.current_position()[3]))
            microscope.save(img_tmp, path)
            positioner.relative_move(0, 0, 0, angle_step, 0)
            continue

        positioner.relative_move(0, 0, 0, angle_step, 0)
        image_euc[0] = np.ndarray.copy(image_euc[1])

    ixe, ygrec, zed, _, _ = positioner.current_position()
    positioner.absolute_move(ixe, ygrec, zed, 0, 0)
    # logging.info('Done eucentrixx')
    s_print(       'Done eucentrixx')
    copyfile('last_execution.log', 'data/tmp/log' + str(time.time()) + '.txt')
    return 0

def set_eucentric_ETEM(microscope, positioner) -> int:
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
    x0, y0, z0, a0, _ = positioner.current_position()
    if z0 == None or y0 == None or a0 == None:
        s_print('Error. Positioner is not initialized.')
        return 1
    
    angle_step0     =  1
    angle_step      =  1  # °
    angle_max       = 10  # °
    precision       = 5   # pixels
    eucentric_error = 0
    resolution      = "512x512" # Bigger pixels means less noise and better match
    image_width     = int(resolution[:resolution.find('x')])
    image_height    = int(resolution[-resolution.find('x'):])
    dwell_time      = 10e-6
    bit_depth       = 16
    image_euc       = np.zeros((2, image_height, image_width))
    displacement    = [[0,0]]
    angle           = [a0]

    positioner.absolute_move(x0, y0, z0, -angle_step, 0)
    positioner.absolute_move(x0, y0, z0, 0, 0)
    microscope.start_acquisition()
    print('1')
    img_tmp      = microscope.acquire_frame(resolution, dwell_time, bit_depth)
    print('2')
    image_euc[0] = microscope.image_array(img_tmp)
    path = 'data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.current_position()[3])/1000000)
    microscope.save(img_tmp, path)

    positioner.relative_move(0, 0, 0, angle_step, 0)
    hfw = microscope.horizontal_field_view() # meters
    
    while abs(eucentric_error) > precision or positioner.current_position()[3] < angle_max:
                
        s_print(       'eucentric_error =', number_format(eucentric_error), 'precision =', number_format(precision), 'current angle =', number_format(positioner.current_position()[3]), 'angle_max =', number_format(angle_max))
        
        img_tmp      = microscope.acquire_frame(resolution, dwell_time, bit_depth)
        image_euc[1] = microscope.image_array(img_tmp)
        path = 'data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.current_position()[3]))
        microscope.save(img_tmp, path)
        
        img_master, mid_strips_master = remove_strips(image_euc[0], dwell_time)
        img_template, mid_strips_template = remove_strips(image_euc[1], dwell_time)
        
        dx_pix, dy_pix = match_by_features(img_template, img_master, mid_strips_template, mid_strips_master, resize=-1)

        dx_si = dx_pix*hfw/image_height
        dy_si = dy_pix*hfw/image_width

        s_print(       'dx_pix, dy_pix', number_format(dx_pix), number_format(dy_pix), 'dx_si, dy_si', number_format(dx_si), number_format(dy_si))

        displacement.append([displacement[-1][0] + dx_si, displacement[-1][1] + dy_si])
        angle.append(positioner.current_position()[3])

        if microscope.microscope_type == 'ESEM':
            eucentric_error += abs(dx_pix)
        else:
            eucentric_error += abs(dy_pix)

        if abs(positioner.current_position()[3]) >= angle_max - 0.01: # 0.010000 degree of freedom
            '''If out of the angle range'''
            correct_eucentric(microscope, positioner, displacement, angle)
            s_print(       'Start again with negative angles')
            
            displacement  = [[0,0]]
            ixe, ygrec, zed, _, _ = positioner.current_position()
            positioner.absolute_move(ixe, ygrec, zed, -angle_step, 0)
            positioner.absolute_move(ixe, ygrec, zed, 0, 0)
            
            # direction      *= -1
            angle           = [positioner.current_position()[3]]
            eucentric_error = 0
            
            ### Test increase angle
            if angle_max == 10:
                angle_max   = 30
                angle_step  =  2
            
            img_tmp = microscope.acquire_frame(resolution, dwell_time, bit_depth)
            image_euc[0] = microscope.image_array(img_tmp)
            path = 'data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.current_position()[3]))
            microscope.save(img_tmp, path)
            positioner.relative_move(0, 0, 0, angle_step, 0)
            continue
        
        positioner.relative_move(0, 0, 0, angle_step, 0)
        image_euc[0] = np.ndarray.copy(image_euc[1])

    ixe, ygrec, zed, _, _ = positioner.current_position()
    positioner.absolute_move(ixe, ygrec, zed, 0, 0)
    # logging.info('Done eucentrixx')
    s_print(       'Done eucentrixx')
    copyfile('last_execution.log', 'data/tmp/log' + str(time.time()) + '.txt')
    return 0

class acquisition(object):
    
    def __init__(self, microscope, positioner, work_folder='data/tomo/', images_name='image', resolution='1536x1024', bit_depth=16, dwell_time=0.2e-6, tilt_increment=2, tilt_end=60) -> int:
        '''
        '''
        
        self.flag = 0
        self.image_width, self.image_height = resolution.split('x')
        
        global imgID
        imgID = 0
        
        self.c = Condition()
        
        try:
            self.microscope = microscope
            self.positioner = positioner
            self.images_name = images_name
            self.resolution = resolution
            self.bit_depth = bit_depth
            self.dwell_time = dwell_time
            self.tilt_increment = tilt_increment
            self.tilt_end = tilt_end
        except:
            self.microscope       = 0
            self.positioner       = 0

        self.pos = positioner.current_position()
        if None in self.pos[1:-1]:
            return None

        if bit_depth == 16:
            self.dtype_number = 65536
        elif bit_depth == 8:
            self.dtype_number = 255

        self.path = work_folder + images_name + '_' + str(round(time.time()))
        print('path = ', self.path)
        os.makedirs(self.path, exist_ok=True)

    def tomo(self):
        self.c.acquire()
        self.microscope.start_acquisition()

        if self.positioner.current_position()[3] > 0:
            self.direction = -1
            if self.tilt_end > 0:
                self.tilt_end *= -1
        else:
            self.direction = 1
            if self.tilt_end < 0:
                self.tilt_end *= -1

        nb_images = int((abs(self.pos[3])+abs(self.tilt_end))/self.tilt_increment + 1)
        s_print('number of images', nb_images)

        if self.microscope.microscope_type == 'ESEM':
            self.microscope.tilt_correction(ONOFF=True)
        
        for i in range(nb_images):
            if self.flag == 1:
                s_print('stopped')
                return
            
            tangle = self.positioner.current_position()[3]
            
            s_print('Image {} / {}. Current tilt angle = {}'.format(i, nb_images, tangle))
            
            if self.microscope.microscope_type == 'ESEM':
                self.microscope.tilt_correction(value = tangle*np.pi/180) # Tilt correction for e- beam

            self.c.notify_all()
            self.c.wait()
            # logging.info(str(i) + str(self.positioner.current_position()[3]))
            images = self.microscope.acquire_frame(self.resolution, self.dwell_time, self.bit_depth)
            # images[0].save(self.path + '/SE_'    + str(self.images_name) + '_' + str(i) + '_' + str(round(tangle)) + '.tif')
            # images[1].save(self.path + '/BF_'    + str(self.images_name) + '_' + str(i) + '_' + str(round(tangle)) + '.tif')
            
            path = self.path + '/HAADF_' + str(self.images_name) + '_' + str(i) + '_' + str(round(tangle))
            self.microscope.save(images, path)

            self.positioner.relative_move(0, 0, 0, self.direction*self.tilt_increment, 0)
            
        self.c.notify_all()
        self.c.release()    
        self.flag = 1
        s_print('Tomography is a Success')
        return 0

    def f_drift_correction(self):
        '''
        '''
        self.c.acquire()
        # i=0
        # while True:
        #     if self.flag == 1:
        #         self.c.notify_all()
        #         self.c.release()
        #         return
        #     s_print('i', i)
        #     i+=1
        #     self.c.notify_all()
        #     self.c.wait()
        
        
        anticipation_x   = 0
        anticipation_y   = 0
        correction_x     = 0
        correction_y     = 0
        img_path_0       = ''
        img_prev_path_0  = ''
        hfw = self.microscope.horizontal_field_view()

        while True:
            # t1 = time.time()
            if self.flag == 1:
                self.c.notify_all()
                self.c.release()
                return
            # Load two most recent images
            # try:
            list_of_imgs  = [file for file in os.listdir(self.path) if 'HAADF' in file]
            if len(list_of_imgs) < 2:
                print('Not enough images yet')
                #time.sleep(0.1)
                self.c.notify_all()
                self.c.wait()
                continue

            img_path      = max(list_of_imgs, key=lambda fn:os.path.getmtime(os.path.join(self.path, fn)))
            list_of_imgs.remove(img_path)
            img_prev_path = max(list_of_imgs, key=lambda fn:os.path.getmtime(os.path.join(self.path, fn)))

            if img_path == img_path_0 or img_prev_path == img_prev_path_0:
                "Waiting for a new image..."
                #time.sleep(0.1)
                self.c.notify_all()
                self.c.wait()
                continue
            else:
                img_path_0      = deepcopy(img_path)
                img_prev_path_0 = deepcopy(img_prev_path)

            
            img       = self.microscope.load(self.path + '/' + img_path)
            img_prev  = self.microscope.load(self.path + '/' + img_prev_path)
            # except:
            #     s_print('Sleeping', time.time())
            #     time.sleep(0.1)
            #     continue
            
            print('New image found for drift correction')
            # t = time.time()

            # img                    = np.float32(img)
            # img_prev               = np.float32(img_prev)
            # shape                  = img_prev.shape
            # corr_scores            = cv.matchTemplate(img, img_prev, cv.TM_CCOEFF) #TM_CCOEFF_NORMED
            # _, max_val, _, max_loc = cv.minMaxLoc(corr_scores)
            # print(corr_scores)
            # print(shape, max_loc, max_val)
            # dx_pix                 = shape[1]//2 - max_loc[1]
            # dy_pix                 = shape[0]//2 - max_loc[0]
        

            #dy_pix, dx_pix, _        =   match(img, img_prev, resize_factor=1)
            
            img_master, mid_strips_master = remove_strips(img_prev, self.dwell_time)
            img_template, mid_strips_template = remove_strips(img, self.dwell_time)
            
            dx_pix, dy_pix = match_by_features(img_template, img_master, mid_strips_template, mid_strips_master, resize=500)
            
            # print('** Match', time.time()-t)
            dx_si                    =   dx_pix * hfw / int(self.image_width)
            dy_si                    =   dy_pix * hfw / int(self.image_height)
            correction_x             = - dx_si + correction_x
            correction_y             = - dy_si + correction_y
            anticipation_x          +=   correction_x
            anticipation_y          +=   correction_y

            # t = time.time()

            print('dx_pix', number_format(dx_pix), 'dy_pix', number_format(dy_pix))
            if dy_pix != 0:
                value_x = correction_x + anticipation_x
                value_y = correction_y + anticipation_y
                print('value_x, value_y', number_format(value_x), number_format(value_y))
                if self.microscope.microscope_type == 'ESEM':
                    self.microscope.beam_shift(-value_x, value_y, mode = 'rel')
                else:
                    self.microscope.beam_shift(-value_y, value_x, mode = 'rel')
                # print('** Correction', time.time()-t)
                # print('** Total', time.time()-t1)
                print('Correction Done')
                
    def f_focus_correction(self, appPI):
        '''
        '''
        img_path_0 = ''
        focus_tollerance = 0.95
        averaging = 2
        focus_score_list = []*averaging
        dtype_number = 2**self.bit_depth
        
        image_width  = int(self.image_width)
        image_height = int(self.image_height)
        # Create radial alpha/transparency layer. 255 in centre, 0 at edge
        Y = np.linspace(-1, 1, image_height)[None, :]*dtype_number
        X = np.linspace(-1, 1, image_height)[:, None]*dtype_number
        alpha_factor = 1
        alpha = np.sqrt(alpha_factor*X**2 + alpha_factor*Y**2)
        alpha = (dtype_number - np.clip(0, dtype_number, alpha))/dtype_number
        
        while True:
            for i in range(averaging):
                if self.flag == 1:
                    return
                try:
                    list_of_imgs = os.listdir(self.path)
                    img_path     = max(list_of_imgs, key=lambda fn:os.path.getmtime(os.path.join(self.path, fn)))
                    if img_path == img_path_0:
                        continue
                    else:
                        img_path_0 = deepcopy(img_path)
                    img = imread(self.path + '/' + img_path)
                except:
                    time.sleep(0.1)
                    continue
                
                # # STDEV
                # noise_level         = np.mean(img[img<self.dtype_number//2])
                # noise_level_std     = np.std( img[img<self.dtype_number//2])
                # img2                = img - np.full(img.shape, noise_level + noise_level_std)
                # focus_score_list[i] = np.std(img2[img2>0])
                
                img_crop = img[:,(image_width-image_height)//2:(image_width+image_height)//2]
                img_crop_alpha = np.uint16(np.multiply(img_crop, alpha))
                
                img_fft = fft(img_crop_alpha)
                
                vec_image = np.reshape(img_fft, (-1,1))
                labels = faiss.Kmeans(d=vec_image.shape[1], k=2)
                labels.train(vec_image)
                _, labels = labels.index.search(vec_image, 1)
                means = [np.mean(vec_image[labels == label]) for label in np.unique(labels)]
                index_array = [np.argsort(means)[0]]

                if index_array[0] == 0:
                    mask = np.where((labels==0)|(labels==1), labels^1, labels)
                else:
                    mask = labels

                img_fft = np.uint8(np.reshape(mask, img_fft.shape))
                
                elps = find_ellipse(img_fft, save=True)
                
                img_fft = (img_fft * 255).astype(np.uint8)
                img_fft = cv.cvtColor(img_fft, cv.COLOR_GRAY2RGB)

                img_fft = cv.ellipse(img_fft, (round(elps[0][0]), round(elps[0][1])), (round(elps[1][0]), round(elps[1][1])), round(elps[2]), 0, 360, (255, 0, 0), 2)
                                
                # img_elps = ImageTk.PhotoImage(Image.fromarray(automatic_brightness_and_contrast(img_fft)))
                img_elps = ImageTk.PhotoImage(Image.fromarray(automatic_brightness_and_contrast(np.uint8(fft(img)))))
                
                appPI.lbl_img.configure(image = img_elps)
                appPI.lbl_img.photo = img_elps
                appPI.lbl_img.update()
                
                ##########
                # if len(list_of_imgs) == 1:
                #     focus_score_0 = deepcopy(focus_score_list[0])

            # focus_score_mean = mean(focus_score_list)
            
            # if focus_score_mean < focus_score_0*focus_tollerance:
                
            #     direction_guess = 1
            #     dFS = 0# ? ###########################
            #     self.microscope.beams.electron_beam.working_distance.value += direction_guess*dFS
                
            # direction_focus = +-1

    def record(self) -> int:
        ''' 
        '''
        self.c.acquire()
        self.microscope.start_acquisition()
        
        if self.microscope.microscope_type == 'ESEM':
            self.microscope.tilt_correction(ONOFF=True)
        i = 0
        
        while True:
            print('Image ' + str(i))
            if self.flag == 1:
                self.c.notify_all()
                self.c.release()
                return
            pos = self.positioner.current_position()
            
            tangle = pos[3]
            
            if self.microscope.microscope_type == 'ESEM':
                self.microscope.tilt_correction(value = tangle*np.pi/180) # Tilt correction for e- beam

            # logging.info(str(i) + str(self.positioner.getpos()[2]))

            self.c.notify_all()
            self.c.wait()
            images = self.microscope.acquire_frame(self.resolution, self.dwell_time, self.bit_depth)
            
            # images[0].save(self.path + '/SE_'    + str(self.images_name) + '_' + str(i) + '_' + str(round(tangle)) + '.tif')
            # images[1].save(self.path + '/BF_'    + str(self.images_name) + '_' + str(i) + '_' + str(round(tangle)) + '.tif')

            path = self.path + '/HAADF_' + str(self.images_name) + '_' + str(i) + '_' + str(round(tangle))
            self.microscope.save(images, path)
            
            i += 1
    
    def f_image_fft(self, appPI):
        '''
        '''
        img_path_0 = ''
        i = 0
        while True:
            if self.flag == 1:
                return
            try:
                list_of_imgs = os.listdir(self.path)
                img_path     = max(list_of_imgs, key=lambda fn:os.path.getmtime(os.path.join(self.path, fn)))
                if img_path == img_path_0:
                    continue
                else:
                    img_path_0 = deepcopy(img_path)
                
                if self.microscope.microscope_type == 'ESEM':
                    img = self.microscope.load(self.path + '/' + img_path)
                else:
                    img = imread(self.path + '/' + img_path)
                
                image_height, image_width  = img.shape
                img = img[:,(image_width-image_height)//2:(image_width+image_height)//2]

                img_0 = ImageTk.PhotoImage(Image.fromarray(automatic_brightness_and_contrast(np.uint8(fft(img)))))
                # img_0 = ImageTk.PhotoImage(Image.fromarray(np.uint8(fft(img))))

                appPI.lbl_img.configure(image = img_0)
                appPI.lbl_img.photo = img_0
                appPI.lbl_img.update()
            except Exception as e:
                PrintException()
                time.sleep(0.1)
                continue