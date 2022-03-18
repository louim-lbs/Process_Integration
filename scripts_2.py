import glob
import io
from pickle import TRUE
from autoscript_sdb_microscope_client.structures import GrabFrameSettings, Point, StagePosition
from cv2 import mean, pencilSketch
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
    img = cv.copyMakeBorder(img, 0, bottom, 0, right, cv.BORDER_CONSTANT, value=0)
    
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
            print('no contour found')
            return ((0, 0), (0, 0), 0)
        ind = np.argmax([len(cont) for cont in contours])

        cont = contours[ind]
        if len(cont) < 5:
            print('len contour < 5', len(contours))
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
        print('no contour found')
        if save:
            plt.imshow(img, 'gray')
            # plt.show()
    return ((0, 0), (0, 0), 0)

def function_displacement(x, z, y):#, R, x2, x3):
    x = [i*np.pi/180 for i in x]
    return y*(1-np.cos(x)) + z*np.sin(x)# + R*(1-np.sin(np.multiply(x, x2))) + x3

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

    pas    = 1000000 # u°
    alpha  = [i/pas for i in range(int(angle_sort[0]), int(angle_sort[-1]+1), int(pas/20))]

    offset = displacement[min(range(len(angle_sort)), key=lambda i: abs(angle_sort[i]))][0]

    displacement_filt = np.array([i[0]-offset for i in displacement])
    
    finterpa               = interpolate.PchipInterpolator([i/pas for i in angle_sort], displacement_filt)
    displacement_y_interpa = finterpa(alpha)

    res, cov         = curve_fit(f=function_displacement, xdata=alpha, ydata=displacement_y_interpa, p0=[0,0], bounds=(-1e7, 1e7))
    # z0_calc, y0_calc, R_calc, x2_calc, x3_calc = res
    z0_calc, y0_calc = res

    stdevs           = np.sqrt(np.diag(cov))

    logging.info('z0 =' + str(z0_calc) + '+-' + str(stdevs[0]) + 'y0 = ' + str(direction*y0_calc) + '+-' + str(stdevs[1]))# + 'R = ' + str(R_calc) + '+-' + str(stdevs[2]) + 'x2 = ' + str(x2_calc) + '+-' + str(stdevs[3]) + 'x3 = ' + str(x3_calc) + '+-' + str(stdevs[4]))
    print('z0 =', z0_calc, '+-', stdevs[0], 'y0 = ', direction*y0_calc, '+-', stdevs[1])
    
    plt.plot([i/pas for i in angle_sort], [i[0]-offset for i in displacement], 'green')
    plt.plot(alpha, displacement_y_interpa, 'blue')
    plt.plot(alpha, function_displacement(alpha, *res), 'red')
    plt.savefig('data/tmp/' + str(time.time()) + 'correct_eucentric.png')
    plt.show()
    
    # Adjust positioner position
    positioner.setpos_rel([z0_calc, -direction*y0_calc, 0])

    # Adjust microscope stage position
    microscope.specimen.stage.relative_move(StagePosition(y=1e-9*direction*y0_calc))
    microscope.beams.electron_beam.working_distance.value += z0_calc*1e-9
    # plt.plot([0, 1, 2], [0, 2, 3])
    # plt.show()
    # Check limits

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
        print('lol')
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
    angle           = [positioner.getpos()[2]]
    direction       = 1
    # logging.info('z0' + str(z0) + 'y0' + str(y0) + 'hfw' + str(hfw) + 'angle_step0' + str(angle_step0) + 'angle_step' + str(angle_step) + 'angle_max' + str(angle_max) + 'precision' + str(precision) + 'resolution' + str(resolution) + 'settings' + str(settings) + 'angle' + str(angle))

    # HAADF analysis
    microscope.imaging.set_active_view(3)

    positioner.setpos_abs([z0, y0, 0])
    
    img_tmp      = microscope.imaging.grab_multiple_frames(settings)[2]
    image_euc[0] = img_tmp.data
    img_tmp.save('data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.getpos()[2])/1000000) + '.tif')

    positioner.setpos_rel([0, 0, angle_step])

    while abs(eucentric_error) > precision or positioner.getpos()[2] < angle_max:
        # logging.info('eucentric_error =' + str(round(eucentric_error)) + 'precision =' + str(precision) + 'current angle =' + str(positioner.getpos()[2]) + 'angle_max =' + str(angle_max))
        print(       'eucentric_error =', round(eucentric_error), 'precision =', precision, 'current angle =', positioner.getpos()[2], 'angle_max =', angle_max)
        
        img_tmp      = microscope.imaging.grab_multiple_frames(settings)[2]
        image_euc[1] = img_tmp.data
        img_tmp.save('data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.getpos()[2]/1000000)) + '.tif')
        
        dx_pix, dy_pix, corr_trust = match(image_euc[1], image_euc[0])

        if corr_trust <= 0.3: # 0.3 empirical value
            '''If match is not good'''
            #### Correct eucentric and go to other direction
            if angle_step >= 100000:
                # logging.info('Decrease angle step')
                print(       'Decrease angle step')
                '''Decrease angle step up to 0.1 degree'''
                positioner.setpos_rel([0, 0, -2*direction*angle_step])
                positioner.setpos_rel([0, 0, +1*direction*angle_step]) # Two moves to prevent direction-change approximations
                angle_step /= 2
            else:
                # logging.info('Error doing eucentric. Tips: check your acquisition parameters (mainly dwell time) or angle range.')
                return 1
            continue

        dx_si = 1e9*dx_pix*hfw/image_width
        dy_si = 1e9*dy_pix*hfw/image_width

        # logging.info('dx_pix, dy_pix' + str(dx_pix) + str(dy_pix) + 'dx_si, dy_si' + str(dx_si) + str(dy_si))
        print(       'dx_pix, dy_pix', dx_pix, dy_pix, 'dx_si, dy_si', dx_si, dy_si)

        displacement.append([displacement[-1][0] + dx_si, displacement[-1][1] + dy_si])
        angle.append(positioner.getpos()[2])

        eucentric_error += abs(dx_pix)

        if abs(positioner.getpos()[2]) >= angle_max - 10000: # 0.010000 degree of freedom
            '''If out of the angle range'''
            correct_eucentric(microscope, positioner, displacement, angle)
            # logging.info('Start again with negative angles')
            print(       'Start again with negative angles')
            
            displacement  = [[0,0]]
            positioner.setpos_rel([0, 0, direction*angle_step])
            zed, ygrec, _ = positioner.getpos()
            positioner.setpos_abs([zed, ygrec, direction*angle_max])
            
            direction      *= -1
            angle           = [positioner.getpos()[2]]
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
            img_tmp.save('data/tmp/' + str(round(time.time(),1)) + 'img_' + str(round(positioner.getpos()[2])/1000000) + '.tif')
            positioner.setpos_rel([0, 0, direction*angle_step])
            continue

        positioner.setpos_rel([0, 0, direction*angle_step])
        image_euc[0] = np.ndarray.copy(image_euc[1])

    pos = positioner.getpos()
    positioner.setpos_abs([pos[1], pos[2], 0])
    # logging.info('Done eucentrixx')
    print(       'Done eucentrixx')
    copyfile('last_execution.log', 'data/tmp/log' + str(time.time()) + '.txt')
    return 0

class acquisition(object):
    
    def __init__(self, microscope, positioner, work_folder='data/tomo/', images_name='image', resolution='1536x1024', bit_depth=16, dwell_time=0.2e-6, tilt_increment=2000000, tilt_end=60000000) -> int:
        '''
        '''
        self.flag = 0
        
        self.image_width  = int(resolution[:resolution.find('x')])
        self.image_height = int(resolution[-resolution.find('x'):])
        
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

        self.pos = positioner.getpos()
        if None in self.pos:
            return None

        if bit_depth == 16:
            self.dtype_number = 65536
        elif bit_depth == 8:
            self.dtype_number = 255

        self.path = work_folder + images_name + '_' + str(round(time.time()))
        os.makedirs(self.path, exist_ok=True)

    def tomo(self):    
        if self.positioner.getpos()[2] > 0:
            self.direction = -1
            if tilt_end > 0:
                tilt_end *= -1
        else:
            direction = 1
            if tilt_end < 0:
                tilt_end *= -1

        nb_images = int((abs(self.pos[2])+abs(tilt_end))/self.tilt_increment + 1)

        settings = GrabFrameSettings(resolution=self.resolution, dwell_time=self.dwell_time, bit_depth=self.bit_depth)
        self.microscope.beams.electron_beam.angular_correction.tilt_correction.turn_on()
        self.microscope.beams.electron_beam.angular_correction.mode = 'Manual'

        for i in range(nb_images):
            if self.flag == 1:
                return

            tangle = self.positioner.getpos()[2]
            self.microscope.beams.electron_beam.angular_correction.angle.value = 1e-6*tangle*np.pi/180 # Tilt correction for e- beam

            print(i, tangle)
            # logging.info(str(i) + str(self.positioner.getpos()[2]))
            
            images = self.microscope.imaging.grab_multiple_frames(settings)
            images[0].save(self.path + '/SE_'    + str(self.images_name) + '_' + str(i) + '_' + str(round(tangle/100000)) + '.tif')
            images[1].save(self.path + '/BF_'    + str(self.images_name) + '_' + str(i) + '_' + str(round(tangle/100000)) + '.tif')
            images[2].save(self.path + '/HAADF_' + str(self.images_name) + '_' + str(i) + '_' + str(round(tangle/100000)) + '.tif')
            self.positioner.setpos_rel([0, 0, direction*self.tilt_increment])
        
        self.flag = 1
        print('Tomography is a Success')
        return 0

    def f_drift_correction(self):
        '''
        '''
        anticipation_x   = 0
        anticipation_y   = 0
        correction_x     = 0
        correction_y     = 0
        img_path_0       = ''
        img_prev_path_0  = ''
        # path_absolute = os.getcwd()
        # path_absolute = path_absolute.replace(os.sep, '/') + self.path
        while True:
            if self.flag == 1:
                return
            # Load two most recent images
            try:
                list_of_imgs  = os.listdir(self.path)# + '*.tif')
                img_path      = max(list_of_imgs, key=lambda fn:os.path.getmtime(os.path.join(self.path, fn)))
                list_of_imgs.remove(img_path)
                img_prev_path = max(list_of_imgs, key=lambda fn:os.path.getmtime(os.path.join(self.path, fn)))
                print(img_path, img_prev_path)
                if img_path == img_path_0 or img_prev_path == img_prev_path_0:
                    continue
                else:
                    img_path_0      = deepcopy(img_path)
                    img_prev_path_0 = deepcopy(img_prev_path)
                
                img       = imread(self.path + '/' + img_path)
                img_prev  = imread(self.path + '/' + img_prev_path)
            except:
                time.sleep(0.1)
                continue
            print('Correction to be done')
            
            hfw = self.microscope.beams.electron_beam.horizontal_field_width.value
            
            dy_pix, dx_pix, _        =   match(img, img_prev, resize_factor=0.5)
            dx_si                    = - dx_pix * hfw / self.image_width
            dy_si                    =   dy_pix * hfw / self.image_width
            correction_x             = - dx_si + correction_x
            correction_y             = - dy_si + correction_y
            anticipation_x          +=   correction_x
            anticipation_y          +=   correction_y
            beamshift_x, beamshift_y =   self.microscope.beams.electron_beam.beam_shift.value
            self.microscope.beams.electron_beam.beam_shift.value = Point(x=beamshift_x + correction_x + anticipation_x,
                                                                         y=beamshift_y + correction_y + anticipation_y)
            beamshift_x, beamshift_y = self.microscope.beams.electron_beam.beam_shift.value
            print('Correction Done')
    
    def f_focus_correction(self, appPI):
        '''
        '''
        img_path_0 = ''
        focus_tollerance = 0.95
        averaging = 2
        focus_score_list = []*averaging
        dtype_number = 2**self.bit_depth
        
        img = imread('images/cell_15.tif')
        image_height, image_width  = img.shape
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
                    list_of_imgs = glob.glob(self.path + '*.tif')
                    img_path     = max(list_of_imgs, key=os.path.getctime)
                    if img_path == img_path_0:
                        continue
                    else:
                        img_path_0 = deepcopy(img_path)
                    img = imread(self.path + img_path)
                except:
                    time.sleep(0.1)
                    continue
                
                # # STDEV
                # noise_level         = np.mean(img[img<self.dtype_number//2])
                # noise_level_std     = np.std( img[img<self.dtype_number//2])
                # img2                = img - np.full(img.shape, noise_level + noise_level_std)
                # focus_score_list[i] = np.std(img2[img2>0])
                
                image_height, image_width  = img.shape
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
                
                im = Image.fromarray(img_fft)
                
                # img_elps = ImageTk.PhotoImage(Image.fromarray(automatic_brightness_and_contrast(img_fft)))
                img_elps = ImageTk.PhotoImage(im)
                
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
        settings = GrabFrameSettings(resolution=self.resolution, dwell_time=self.dwell_time, bit_depth=self.bit_depth)
        self.microscope.beams.electron_beam.angular_correction.tilt_correction.turn_on()
        self.microscope.beams.electron_beam.angular_correction.mode = 'Manual'
        i = 0
        
        while True:
            if self.flag == 1:
                return
            pos = self.positioner.getpos()
            
            tangle = pos[2]
            self.microscope.beams.electron_beam.angular_correction.angle.value = 1e-6*tangle*np.pi/180 # Tilt correction for e- beam

            # logging.info(str(i) + str(self.positioner.getpos()[2]))
            
            images = self.microscope.imaging.grab_multiple_frames(settings)
            # images[0].save(self.path + '/SE_'    + str(self.images_name) + '_' + str(i) + '_' + str(round(tangle/100000)) + '.tif')
            # images[1].save(self.path + '/BF_'    + str(self.images_name) + '_' + str(i) + '_' + str(round(tangle/100000)) + '.tif')
            images[2].save(self.path + '/HAADF_' + str(self.images_name) + '_' + str(i) + '_' + str(round(tangle/100000)) + '.tif')
            
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
                list_of_imgs = glob.glob(self.path + '*.tif')
                img_path     = max(list_of_imgs, key=os.path.getctime)
                if img_path == img_path_0:
                    continue
                else:
                    img_path_0 = deepcopy(img_path)
                    
                img = imread(self.path + img_path)
                
                image_height, image_width  = img.shape
                img = img[:,(image_width-image_height)//2:(image_width+image_height)//2]

                img_0 = ImageTk.PhotoImage(Image.fromarray(automatic_brightness_and_contrast(fft(img))))

                appPI.lbl_img.configure(image = img_0)
                appPI.lbl_img.photo = img_0
                appPI.lbl_img.update()
            except:
                time.sleep(0.1)
                continue