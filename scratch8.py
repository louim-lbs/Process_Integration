from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *

import copy
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

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
from smaract import connexion_smaract as sm
smaract = sm.smaract_class(calibrate=False)

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

def tomo_acquisition2(microscope, positioner, resolution='1536x1024', bit_depth=16, dwell_time=0.2e-6, tilt_increment=2000000, tilt_end=60000000, drift_correction:bool=False) -> int:
    ''' 
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

    settings = GrabFrameSettings(resolution=resolution, dwell_time=dwell_time, bit_depth=bit_depth)
    
    focus_scores_laplac = []
    focus_scores_mean = []
    focus_scores_mean2 = []
    focus_scores_mean3 = []
    focus_scores_mean4 = []
    focus_scores_mean5 = []
    focus_scores_mean6 = []
    focus_scores_mean7 = []

    for i in range(10):        
        images = microscope.imaging.grab_multiple_frames(settings)
        # positioner.setpos_rel([0, 0, direction*tilt_increment])
        
        # focus_score_lap = cv.Laplacian(images[2].data, cv.CV_16U).var()
        # focus_score_me  = np.mean(images[2].data)
        focus_score_me2 = np.mean(images[2].data[images[2].data>65536//2.5])
        focus_score_me6 = np.mean(images[2].data[images[2].data>65536//3])
        focus_score_me7 = np.mean(images[2].data[images[2].data>65536//3.5])
        # focus_score_me3 = np.average(images[2].data, weights=np.power(images[2].data, 2))
        # focus_score_me4 = np.average(images[2].data, weights=np.power(images[2].data, 3))
        # focus_score_me5 = np.average(images[2].data, weights=np.power(images[2].data, 4))

        # focus_scores_laplac.append(focus_score_lap)
        # focus_scores_mean.append(focus_score_me)
        focus_scores_mean2.append(focus_score_me2)
        # focus_scores_mean3.append(focus_score_me3)
        # focus_scores_mean4.append(focus_score_me4)
        # focus_scores_mean5.append(focus_score_me5)
        focus_scores_mean6.append(focus_score_me6)
        focus_scores_mean7.append(focus_score_me7)

        # print(focus_score_lap)
        # print(focus_score_me)
        print(focus_score_me2)
        # print(focus_score_me3)
    # plt.plot(focus_scores_laplac, 'blue')
    # plt.plot(focus_scores_mean, 'r+')
    plt.plot([i/np.max(focus_scores_mean2) for i in focus_scores_mean2], 'r+')
    plt.plot([i/np.max(focus_scores_mean6) for i in focus_scores_mean6], 'g+')
    plt.plot([i/np.max(focus_scores_mean7) for i in focus_scores_mean7], 'b+')
    # plt.plot([i/np.min(focus_scores_mean3) for i in focus_scores_mean3], 'r+')
    # plt.plot([i/np.min(focus_scores_mean4) for i in focus_scores_mean4], 'g+')
    # plt.plot([i/np.min(focus_scores_mean5) for i in focus_scores_mean5], 'b+')
    plt.show()

    print('Tomographixx is a Succes')
    return 0

## noise fait que le blur détection est pas exact. blur reult,
## proportionel et pas limite
## gérer les nan
## zone de l'image à analyser :les tilts font que les bords supérieurs ou inférieurs seront flous
## gérer la correction


if __name__ == "__main__":
    tomo_acquisition2(quattro,
                        smaract,
                        resolution='1536x1024',
                        bit_depth=16,
                        dwell_time=10e-6,
                        tilt_increment=int(2*1e6),
                        tilt_end=int(70*1e6),
                        drift_correction=True)