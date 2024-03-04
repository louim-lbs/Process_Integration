import numpy as np
from matplotlib import image
# from test.scrath_parallelism import parallel_task
from scripts import match, set_eucentric
import os
import logging
import cv2 as cv

dir_pi = os.getcwd()
logging.basicConfig(filename='last_execution.log', filemode='w', format='%(levelname)s:%(message)s', level=logging.INFO)
dir_pi = os.getcwd()


from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

def sub_match(params):
    print(params[0])
    print(params[0].shape)

    return 0

def parallel(function, dataset):
    pool = Pool()
    results = pool.map(function, dataset)
    pool.close()
    pool.join()
    print('lolpool')
    return results

def match_pool(image_master, image_template, grid_size = 5, ratio_template_master = 0.9, ratio_master_template_patch = 0, speed_factor = 0):
    
    image_master = np.float32(image_master)
    image_template = np.float32(image_template)

    height_master, width_master = image_master.shape

    height_template, width_template = int(ratio_template_master*height_master), int(ratio_template_master*width_master)

    template_patch_size = (height_template//grid_size,
                            width_template//grid_size)

    displacement_vector = np.array([[0,0]])
    corr_trust = np.array(0)

    image_template_patchs = np.zeros((grid_size**2, template_patch_size[0], template_patch_size[1]))

    for i in range(grid_size):
        for j in range(grid_size):
            template_patch_xA = (height_master - height_template)//2 + (i)*template_patch_size[0]
            template_patch_yA = (width_master  - width_template)//2  + (j)*template_patch_size[1]
            template_patch_xB = (height_master - height_template)//2 + (i+1)*template_patch_size[0]
            template_patch_yB = (width_master  - width_template)//2  + (j+1)*template_patch_size[1]

            template_patch = image_template[int(template_patch_xA):int(template_patch_xB),
                                            int(template_patch_yA):int(template_patch_yB)]

            image_template_patchs[i*grid_size+j] = template_patch

    # displacement_vector, corr_trust = parallel(sub_match, [image_master, image_template_patchs])
    displacement_vector, corr_trust = parallel(sub_match, image_master)

    displacement_vector = np.delete(displacement_vector,0,0)
    dx_tot = displacement_vector[:,0]
    dy_tot = displacement_vector[:,1]

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

    return np.mean(dx_tot), np.mean(dy_tot), np.mean(corr_trust)


if __name__ == '__main__':

    from smaract_folder import connexion_smaract as sm
    smaract = sm.smaract_class(calibrate=False)
    os.chdir(dir_pi)

    img1 = np.asarray(image.imread('images/2_40.tif'))
    img2 = np.asarray(image.imread('images/5_25.tif'))

    try:
        img1 = img1[:,:,1]
        img2 = img2[:,:,1]
    except:
        pass

    import time

    t = time.time()
    res = match_pool(img1, img2, grid_size=5, ratio_template_master=0.9)
    print(res)
    print('time = ', int((time.time()-t)*1000), 'ms')
