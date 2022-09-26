import microscopes.DM34 as DM34
import numpy as np
import time
import cv2 as cv
import matplotlib.pyplot as plt
from copy import deepcopy

def match(microscope, image_master, image_template, grid_size = 5, ratio_template_master = 0.9, resize_factor = 1):
    ''' Match two images

    Input:
        - image_master: image before the displacement (ndarray).
        - image_template: image after the displacement (nd_array).
        - grid_size: Computation resolution. Higher is more precise but slower (int).
        - ratio_template_master: Ratio of image_template used for computation. Between 0 and 1 (float).
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
    
    image_master_cop = deepcopy(image_master)
    # plt.imshow(image_master_cop)
    # plt.show()
    
    # if 0==0 or microscope.type == 'ETEM':
    #     image_master = cv.flip(image_master, 0)
    #     image_template = cv.flip(image_template, 0)
    
    image_master   = cv.resize(image_master,   (0, 0), fx=resize_factor, fy=resize_factor)
    image_template = cv.resize(image_template, (0, 0), fx=resize_factor, fy=resize_factor)

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
            
            

            corr_scores            = cv.matchTemplate(image_master, template_patch, cv.TM_CCOEFF) #TM_CCOEFF_NORMED
            corr_scores = corr_scores
            _, max_val, _, max_loc = cv.minMaxLoc(corr_scores)
            
            
            # plt.imshow(corr_scores)
            # plt.show()
            
            top_left = (template_patch_yA, template_patch_xA)
            bottom_right = (top_left[0] + template_patch_size[0], top_left[1] + template_patch_size[0])
            cv.rectangle(image_master_cop, top_left, bottom_right, 0, 2)
            
            top_left = (max_loc[0], max_loc[1])
            bottom_right = (top_left[0] + template_patch_size[0], top_left[1] + template_patch_size[0])
            cv.rectangle(image_master_cop, top_left, bottom_right, 255, 2)
            
            # plt.imshow(image_master_cop)
            # plt.show()
            
            
            dx                     = (template_patch_xA - max_loc[1])*resize_factor
            dy                     = (template_patch_yA - max_loc[0])*resize_factor
            
            print(int(template_patch_xA),int(template_patch_xB),int(template_patch_yA),int(template_patch_yB), dx, dy, max_val)
            displacement_vector    = np.append(displacement_vector, [[dx, dy]], axis=0)
            corr_trust             = np.append(corr_trust, max_val)
    
    plt.imshow(image_master_cop)
    plt.show()

    corr_trust_x          = np.delete(corr_trust, 0)
    corr_trust_y          = deepcopy(corr_trust_x)
    displacement_vector = np.delete(displacement_vector,0,0)
    dx_tot              = displacement_vector[:,0]
    dy_tot              = displacement_vector[:,1]
    print(displacement_vector)

    plt.plot(dx_tot, '--r')
    plt.plot(dy_tot, '--g')

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

    plt.plot(dx_tot, 'red')
    plt.plot(dy_tot, 'green')
    plt.show()

    a = np.average(dx_tot.reshape((len(dx_tot),)), weights=corr_trust_x)
    b = np.average(dy_tot.reshape((len(dy_tot),)), weights=corr_trust_y)
    c = np.mean(np.array([np.mean(corr_trust_x), np.mean(corr_trust_y)]))
    return a, b, c


img1, _, _, _ = DM34.dm_load(r'C:\Users\Public\Documents\Lebas\Process_Integration\data\record\Acquisition_1663928476\HAADF_Acquisition_0_0.dm4')
img2, _, _, _ = DM34.dm_load(r'C:\Users\Public\Documents\Lebas\Process_Integration\data\record\Acquisition_1663928476\HAADF_Acquisition_1_0.dm4')


print(match(0, np.float32(img1), np.float32(img2), grid_size = 3, ratio_template_master = 0.9, resize_factor = 1))