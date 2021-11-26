import numpy as np
import cv2 as cv
from matplotlib import image
import matplotlib.pyplot as plt

def match(image_master, image_template, grid_size = 10, ratio_template_master = 0.5, ratio_master_template_patch = None, speed_factor = 2):
    ''' Match two images

    Input:

    Output:

    Exemple:

    '''
    height_master, width_master = image_master.shape

    height_template, width_template = int(ratio_template_master*height_master), int(ratio_template_master*width_master)

    x_A = (width_master  - width_template)//2
    y_A = (height_master - height_template)//2
    x_B = (width_master  + width_template)//2
    y_B = (height_master + height_template)//2
    
    cv.rectangle(image_master,
                (x_A,y_A),
                (x_B,y_B),
                255, 2)

    template_patch_size = (height_template//grid_size,
                            width_template//grid_size)

    master_patch_size = (int(height_master - height_template + template_patch_size[0])//speed_factor,
                         int(width_master  - width_template  + template_patch_size[1])/speed_factor)
    
    if ratio_master_template_patch != None:
        if ratio_master_template_patch > max(master_patch_size[0], master_patch_size[1]):
            pass
        master_patch_size = (int(template_patch_size[0]*ratio_master_template_patch),
                             int(template_patch_size[1]*ratio_master_template_patch))

    displacement_vector = np.array([[0,0]])
    corr_trust = np.array(0)

    for i in range(grid_size):
        for j in range(grid_size):
            
            master_patch_xA = (height_master - height_template)//2 - (master_patch_size[0] - template_patch_size[0])//2 + (i)*template_patch_size[0]
            master_patch_yA = (width_master  - width_template)//2  - (master_patch_size[1] - template_patch_size[1])//2 + (j)*template_patch_size[1]
            master_patch_xB = (height_master - height_template)//2 - (master_patch_size[0] - template_patch_size[0])//2 + (i)*template_patch_size[0] + master_patch_size[0]
            master_patch_yB = (width_master  - width_template)//2  - (master_patch_size[1] - template_patch_size[1])//2 + (j)*template_patch_size[1] + master_patch_size[1]


            master_patch = image_master[int(master_patch_xA):int(master_patch_xB),
                                        int(master_patch_yA):int(master_patch_yB)]


            template_patch_xA = (height_master - height_template)//2 + (i)*template_patch_size[0]
            template_patch_yA = (width_master  - width_template)//2  + (j)*template_patch_size[1]
            template_patch_xB = (height_master - height_template)//2 + (i+1)*template_patch_size[0]
            template_patch_yB = (width_master  - width_template)//2  + (j+1)*template_patch_size[1]

            template_patch = image_template[int(template_patch_xA):int(template_patch_xB),
                                            int(template_patch_yA):int(template_patch_yB)]

            corr_scores = cv.matchTemplate(master_patch, template_patch, cv.TM_CCOEFF_NORMED)

            _, max_val, _, max_loc = cv.minMaxLoc(corr_scores)

            dx = (master_patch_size[0] - template_patch_size[0])//2 - max_loc[1]
            dy = (master_patch_size[1] - template_patch_size[1])//2 - max_loc[0]

            displacement_vector = np.append(displacement_vector, [[dx, dy]], axis=0)

            # print('Correlation trust: ', max_val)
            corr_trust = np.append(corr_trust, max_val)

            # top_left = (template_patch_yA,
            #             template_patch_xA)
            
            # # top_left = (max_loc[0] + (width_master  - width_template)//2 + j*template_patch_size[1],
            # #             max_loc[1] + (height_master - height_template)//2 + i*template_patch_size[0])

            # bottom_right = (top_left[0] + template_patch_size[1],
            #                 top_left[1] + template_patch_size[0])

            # top_left_master = (master_patch_yA,
            #                    master_patch_xA)

            # bottom_right_master = (master_patch_yB,
            #                        master_patch_xB)

            # cv.rectangle(image_master,top_left, bottom_right, 255, 2)
            # # cv.rectangle(image_master,top_left_master, bottom_right_master, 255, 2)

    dx_tot = displacement_vector[:,0]
    dy_tot = displacement_vector[:,1]

    mean_x = np.mean(dx_tot)
    mean_y = np.mean(dy_tot)
    stdev_x = np.std(dx_tot)
    stdev_y = np.std(dy_tot)

    for d in dx_tot:
        if (d <= mean_x - stdev_x) or (mean_x + stdev_x <= d):
            dx_tot = np.delete(dx_tot, np.where(dx_tot==d))
    for d in dy_tot:
        if (d <= mean_y - stdev_y) or (mean_y + stdev_y <= d):
            dy_tot = np.delete(dy_tot, np.where(dy_tot==d))

    dx_tot = cv.blur(dx_tot, (1, dx_tot.shape[0]//4))
    dy_tot = cv.blur(dy_tot, (1, dy_tot.shape[0]//4))

    mean_x = np.mean(dx_tot)
    mean_y = np.mean(dy_tot)
    stdev_x = np.std(dx_tot)
    stdev_y = np.std(dy_tot)

    return [np.mean(dx_tot), np.mean(dy_tot)], np.mean(corr_trust)

img1 = np.asarray(image.imread('images/cell_20.tif'))
img2 = np.asarray(image.imread('images/cell_19.tif'))

import time


t = time.time()
res = match(img1, img2, grid_size= 10, ratio_template_master = 0.5, ratio_master_template_patch = None, speed_factor = 4)
print(res)
print('time = ', int((time.time()-t)*1000), 'ms')

