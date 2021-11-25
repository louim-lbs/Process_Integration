import numpy as np
import cv2 as cv
from matplotlib import image
import matplotlib.pyplot as plt

def match(image1, image_master):
    ''' Match two images

    Input:

    Output:

    Exemple:

    '''
    image_width, image_height = image1.shape


    pixel_center_w = image_width//2
    pixel_center_h = image_height//2

    slave_size = 0.9

    zone_slave = (  int(pixel_center_h - slave_size*image_height//2),
                    int(pixel_center_w - slave_size*image_width //2),
                    int(pixel_center_h + slave_size*image_height//2),
                    int(pixel_center_w + slave_size*image_width //2))
    
    image_slave  = image1[zone_slave[0]:zone_slave[2], zone_slave[1]:zone_slave[3]]

    image_width, image_height = image_slave.shape

    print(image_slave.shape)

    corr_scores = cv.matchTemplate(image_master, image_slave, cv.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(corr_scores)

    top_left = max_loc
    bottom_right = (top_left[0] + image_width, top_left[1] + image_height)


    cv.rectangle(image_master,top_left, bottom_right, 255, 2)
    plt.subplot(121),plt.imshow(corr_scores,cmap = 'gray')
    plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
    plt.subplot(122),plt.imshow(image_master,cmap = 'gray')
    plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
    plt.show()

    return 

img1 = np.asarray(image.imread('images/cell_15.tif'))
img2 = np.asarray(image.imread('images/cell_16.tif'))

res = match(img1, img2)
