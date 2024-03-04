import time
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *

import copy
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

### Connexion

# Connect to microscope
quattro = SdbMicroscopeClient()
try:
    quattro.connect() # online connection
    SdbMicroscopeClient.InitState_status = property(lambda self: 0) # Or 1 if not connected
except:
    try:
        quattro.connect('localhost') # local connection (Support PC) or offline scripting
        SdbMicroscopeClient.InitState_status = property(lambda self: 0) # Or 1 if not connected
    except:
        SdbMicroscopeClient.InitState_status = property(lambda self: 1) # Or 0 if not connected

# Connect to positioner
from smaract_folder import connexion_smaract as sm
smaract = sm.smaract_class(calibrate=False)

import numpy.linalg as linalg

def fft_treh_filt(img, threshold=150):
    rows, cols = img.shape
    nrows = cv.getOptimalDFTSize(rows)
    ncols = cv.getOptimalDFTSize(cols)
    right = ncols - cols
    bottom = nrows - rows
    nimg = cv.copyMakeBorder(img, 0, bottom, 0, right, cv.BORDER_CONSTANT, value=0)

    # Compute FFT
    image_fft     = np.fft.fftshift(cv.dft(np.float32(nimg), flags=cv.DFT_COMPLEX_OUTPUT))
    image_fft_mag = 20*np.log(cv.magnitude(image_fft[:,:,0], image_fft[:,:,1]))
    
    # Threshold images
    image_fft_mag_tresh = cv.threshold(np.uint8(image_fft_mag), threshold, 255, cv.THRESH_BINARY)[1]
    
    # Delete isolated pixels
    image_fft_mag_tresh_comp = cv.bitwise_not(image_fft_mag_tresh)

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
    contours, _ = cv.findContours(img, mode=cv.RETR_EXTERNAL, method=cv.CHAIN_APPROX_NONE)
    print(len(contours))
    cv.drawContours(img, contours, -1, (0,255,0), 3)
    cv.waitKey()
    if len(contours) != 0:
        for cont in contours:
            if len(cont) < 5:
                break
            elps = cv.fitEllipse(cont)
            return elps
    return None

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

    nb_images = int((abs(pos[2])+abs(tilt_end))/tilt_increment + 1)

    image_width = int(resolution[:resolution.find('x')])
    image_height = int(resolution[-resolution.find('x'):])
    
    settings = GrabFrameSettings(resolution=resolution, dwell_time=dwell_time, bit_depth=bit_depth)
    
    anticipation_x = 0
    anticipation_y = 0
    correction_x = 0
    correction_y = 0

    for i in range(nb_images):
        print(i, positioner.angle_convert_Smaract2SI(positioner.getpos()[2]))
        
        images = microscope.imaging.grab_multiple_frames(settings)
        
        positioner.setpos_rel([0, 0, direction*tilt_increment])
        ###### Drift correction
        if drift_correction==True and i > 0:
            hfw = microscope.beams.electron_beam.horizontal_field_width.value
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
            t = time.time()

            fft = fft_treh_filt(images[2].data,      threshold=150)
            
            # plt.imshow(fft[int(3.75*image_height/8):int(4.25*image_height/8),
            #                 int(3.75*image_width/8):int(4.25*image_width/8)])
            # plt.show()

            elps = find_ellipse(fft[int(3.75*image_height/8):int(4.25*image_height/8),
                                    int(3.75*image_width/8):int(4.25*image_width/8)])

            print('elps', elps)

            print(time.time()-t, 's')

        images_prev = copy.deepcopy(images)

    print('Tomography is a Succes')
    return 0

## noise fait que le blur détection est pas exact. blur reult,
## proportionel et pas limite
## gérer les nan
## zone de l'image à analyser :les tilts font que les bords supérieurs ou inférieurs seront flous
## gérer la correction


if __name__ == "__main__":
    tomo_acquisition(quattro,
                     smaract,
                     resolution='1536x1024',
                     bit_depth=16,
                     dwell_time=1e-6,
                     tilt_increment=int(2*1e6),
                     tilt_end=int(70*1e6),
                     drift_correction=True,
                     focus_correction=True)