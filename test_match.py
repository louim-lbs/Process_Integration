import numpy as np
import cv2 as cv
from matplotlib import image
import matplotlib.pyplot as plt
from numpy.core.fromnumeric import size

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

    mean_x = np.mean(dx_tot)
    mean_y = np.mean(dy_tot)
    stdev_x = np.std(dx_tot)
    stdev_y = np.std(dy_tot)
    # plt.plot(dx_tot)
    # plt.plot(dy_tot)
    # plt.show()
    for d in dx_tot:
        if (d < mean_x - stdev_x) or (mean_x + stdev_x < d):
            dx_tot = np.delete(dx_tot, np.where(dx_tot==d))
    for d in dy_tot:
        if (d < mean_y - stdev_y) or (mean_y + stdev_y < d):
            dy_tot = np.delete(dy_tot, np.where(dy_tot==d))
    mean_x = np.mean(dx_tot)
    mean_y = np.mean(dy_tot)
    stdev_x = np.std(dx_tot)
    stdev_y = np.std(dy_tot)
    # plt.plot(dx_tot)
    # plt.plot(dy_tot)
    # plt.show()
    for d in dx_tot:
        if (d < mean_x - stdev_x) or (mean_x + stdev_x < d):
            dx_tot = np.delete(dx_tot, np.where(dx_tot==d))
    for d in dy_tot:
        if (d < mean_y - stdev_y) or (mean_y + stdev_y < d):
            dy_tot = np.delete(dy_tot, np.where(dy_tot==d))
    # plt.plot(dx_tot)
    # plt.plot(dy_tot)
    # plt.show()
    dx_tot = cv.blur(dx_tot, (1, dx_tot.shape[0]//4))
    dy_tot = cv.blur(dy_tot, (1, dy_tot.shape[0]//4))
    # plt.plot(dx_tot)
    # plt.plot(dy_tot)
    # plt.show()

    return np.mean(dx_tot), np.mean(dy_tot), np.mean(corr_trust)

import os
dir_pi = os.getcwd()


imp = 0
while True:
    try:
        from autoscript_sdb_microscope_client import SdbMicroscopeClient
        from autoscript_sdb_microscope_client.enumerations import *
        from autoscript_sdb_microscope_client.structures import *
        break
    except:
        if imp == 0:
            logging.info('Autoscript import failed... Trying to install pillow and cv2 requirements and trying again')
            #!pip install pillow # type: ignore
            #!pip install opencv-python # type: ignore
            imp = 1
        if imp != 0:
            logging.info('Something went wrong. Check your Autoscript installation')

# # Connexion

# # Connect to microscope

# quattro = SdbMicroscopeClient()

# try:
#     quattro.connect() # online connection
#     SdbMicroscopeClient.InitState_status = property(lambda self: 0) # Or 1 if not connected
# except:
#     try:
#         quattro.connect('localhost') # local connection (Support PC) or offline scripting
#         SdbMicroscopeClient.InitState_status = property(lambda self: 0) # Or 1 if not connected
#     except:
#         SdbMicroscopeClient.InitState_status = property(lambda self: 1) # Or 0 if not connected


# # Connect to positioner

# from smaract import connexion_smaract as sm
# smaract = sm.smaract_class(calibrate=False)
# os.chdir(dir_pi)
# smaract.setpos_abs([0, 0, 0])

# quattro.imaging.set_active_view(3)

# # resolution="1536x1024"
# resolution="512x442"
# settings = GrabFrameSettings(resolution=resolution, dwell_time=10e-6, bit_depth=16)



# image1 = quattro.imaging.grab_multiple_frames(settings)

# smaract.setpos_abs([0, 0, 0])

# image2 = quattro.imaging.grab_multiple_frames(settings)

# hfw = quattro.beams.electron_beam.horizontal_field_width.value
# image_width_pix = int(resolution[:resolution.find('x')])

# for i in range(3):
#     image1[i].save('img3_0_' + str(i) + '.tif')
#     image2[i].save('img3_1_' + str(i) + '.tif')
# dx, dy, trust = match(image1[2].data, image2[2].data, grid_size=60, ratio_template_master=0.4)
# print(1000000*dx*hfw/image_width_pix, 1000000*dy*hfw/image_width_pix, trust)

# smaract.setpos_abs([0, 0, 0])

# exit()

img1 = np.asarray(image.imread('images/2_40.tif'))
img2 = np.asarray(image.imread('images/5_25.tif'))

try:
    img1 = img1[:,:,1]
    img2 = img2[:,:,1]
except:
    pass

import time


# ratio = [0.1*i for i in range(1,10)]
# ratio = 0.9
# grid =  [ 1*i for i in range(1, 10)]

# # for x in ratio:
# for y in grid:
#     try:
#         t = time.time()
#         dx, dy, trust = match(img1, img2, grid_size=y, ratio_template_master=ratio)
#         print(y, 1000000*dx*1.27e-05/512, 1000000*dy*1.27e-05/512, trust)
#         print('time = ', int((time.time()-t)*1000), 'ms')
#         # print(x, y, dx, dy, trust)
#     except:
        
#         pass


t = time.time()
res = match(img1, img2, grid_size=5, ratio_template_master=0.9)
print(res)
print('time = ', int((time.time()-t)*1000), 'ms')

# dx, dy, trust = match(img1, img2, grid_size=5, ratio_template_master=0.9)
# print(1000000*dx*1.27e-05/512, 1000000*dy*1.27e-05/512, trust)