from copy import deepcopy
import os
import cv2 as cv
import numpy as np
import time
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
from scipy import interpolate
import tifffile
from PIL import Image
from PIL.TiffTags import TAGS

def number_format(number:float, decimals:int=2):
    if number == None:
        return 'None'
    return str('{:.{}e}'.format(float(number), decimals))

def function_displacement(x, z, y, R):#, x2, x3):
    x = [i*np.pi/180 for i in x]
    return y*(1-np.cos(x)) + z*np.sin(x) + R*(1-np.sin(x))#np.multiply(x, x2))) + x3

def correct_eucentric(displacement, angle):
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
    print('displacement' + str(displacement))
    print('angle' + str(angle))
    
    angle_sort = sorted(angle)
    if angle_sort == angle:
        direction = 1
    else:
        direction = -1
        displacement.reverse()

    print('direction: ' + str(direction))

    pas    = 1 # 1°
    alpha  = [i/pas for i in range(int(angle_sort[0]), int(angle_sort[-1]+1))]

    offset = displacement[min(range(len(angle_sort)), key=lambda i: abs(angle_sort[i]))][1]
    displacement_filt = np.array([i[1]-offset for i in displacement])


    finterpa               = interpolate.PchipInterpolator([i/pas for i in angle_sort], displacement_filt)
    displacement_y_interpa = finterpa(alpha)

    res, cov         = curve_fit(f=function_displacement, xdata=alpha, ydata=displacement_y_interpa, p0=[0,0,0], bounds=(-1e7, 1e7))
    # z0_calc, y0_calc, R_calc, x2_calc, x3_calc = res
    z0_calc, y0_calc, R_calc = res
    stdevs           = np.sqrt(np.diag(cov))

    print('z0 =', z0_calc, 'y0 = ', -direction*y0_calc)
    
    plt.plot([i/pas for i in angle_sort], [i[1]-offset for i in displacement], 'green')
    plt.plot(alpha, displacement_y_interpa, 'blue')
    plt.plot(alpha, function_displacement(alpha, *res), 'red')
    # plt.savefig('data/tmp/' + str(time.time()) + 'correct_eucentric.png')
    plt.show()


    plt.clf()

def cv2_copy(keypoints):
    keypoints_copy = []
    for i in range(len(keypoints)):
        temp = {'pt': keypoints[i].pt,
                'size': keypoints[i].size,
                'angle': keypoints[i].angle,
                'octave': keypoints[i].octave,
                'response':keypoints[i].response,
                'class_id': keypoints[i].class_id}
        
        point = cv.KeyPoint(x=temp['pt'][0],
                            y=temp['pt'][1],
                            size=temp['size'],
                            angle=temp['angle'],
                            octave=temp['octave'],
                            response=temp['response'],
                            class_id=temp['class_id'])
        keypoints_copy.append(point)

    return keypoints_copy

def match_by_features_SIFT_create(img, mid_strips=0, resize_factor=1):
    img_ret = cv.resize(img[mid_strips:], (0, 0), fx=resize_factor, fy=resize_factor)
    
    sift = cv.SIFT_create()
    img_ret = cv.cvtColor(img_ret, cv.IMREAD_GRAYSCALE)
    sift = cv.SIFT_create(nfeatures=1000)
    kp, des = sift.detectAndCompute(img_ret, None)
    return kp, des

def match_by_features(img_template, img_master, kp1, des1, kp2, des2, resize_factor, mid_strips_template, mid_strips_master, MIN_MATCH_COUNT = 20):
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
        return 0, 0
    
    matchesMask = mask.ravel().tolist()
    img_master = cv.polylines(cv.resize(img_master, (0, 0), fx=resize_factor, fy=resize_factor),[np.int32(disp)],True,255,3, cv.LINE_AA)
    draw_params = dict(matchColor = (0,255,0), # draw matches in green color
                singlePointColor = None,
                matchesMask = matchesMask, # draw only inliers
                flags = 2)
    
    img3 = cv.drawMatches(cv.resize(img_template, (0, 0), fx=resize_factor, fy=resize_factor),kp1,img_master,kp2,good,None,**draw_params)
    plt.imshow(img3)
    plt.savefig('data/tmp/' + str(time.time()) + '.png')
    plt.clf()

    return round(-disp[0,0,0]), round(disp[0,0,1]+mid_strips_master-mid_strips_template)

def remove_strips(img, dwell_time):
    img = np.asarray(img, dtype='int32')
    w, _ = img.shape
    scores = np.zeros(w//2, dtype='int32')
    for i in range(w//2-1):
        scores[i] = np.sum(abs(img[i+1] - img[i]))
    min_val = np.min(scores)
    max_val = np.max(scores)
    if max_val - min_val == 0:
        print(scores)
        plt.imshow(img)
        plt.show()
    scores = (scores[:-1] - min_val) / (max_val - min_val)
    scores_peaks, _ = find_peaks(scores, prominence=(0.4,1))
    if len(scores_peaks) == 0:
        mid_strips = 0
    else:
        mid_strips = scores_peaks[-1] + int(0.0512/(dwell_time*w)) # 0.0512 is the time before the movement stabilizes itself. Empirically determined.

    if np.max(img) > 255:
        img_ret = (img[mid_strips:,:]/256).astype('uint8')
    else:
        img_ret = (img).astype('uint8')
    return img_ret, mid_strips


if __name__ == '__main__':
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
    angle           = [0]


    path = 'data/tmp/'
    #list all files in the directory if they are images
    files = [f for f in os.listdir(path) if f.lower().endswith(('.tif', '.png', '.jpg', '.jpeg'))]
    img_tmp = cv.imread(path + files[0], cv.IMREAD_GRAYSCALE)

    image_euc[0] = img_tmp
    resize_factor = 1
    # img_master, mid_strips_master = remove_strips(image_euc[0], dwell_time)
    img_master = image_euc[0].astype('uint8')
    mid_strips_master = 0
    kp2, des2 = match_by_features_SIFT_create(img_master, mid_strips_master, resize_factor)     
    
    img = tifffile.TiffFile(path + files[0])
    metadata = img.__str__(detail=3, width=79)
    hfw = metadata[metadata.find('HFW'):]
    hfw = hfw[:hfw.find(',')]
    hfw = float(hfw[hfw.find(':')+1:])

    print(len(files))
    for i in range(len(files)-1):
        print('eucentric_error =', number_format(eucentric_error), 'precision =', number_format(precision), 'current angle =', number_format(i), 'angle_max =', number_format(angle_max))
        
        image_euc[1] = cv.imread(path + files[i+1], cv.IMREAD_GRAYSCALE)
    
        # img_template, mid_strips_template = remove_strips(image_euc[1], dwell_time)
        img_template = image_euc[1].astype('uint8')
        mid_strips_template = 0
        kp1, des1 = match_by_features_SIFT_create(img_template, mid_strips_template, resize_factor)

        dx_pix, dy_pix = match_by_features(img_template, img_master, kp1, des1, kp2, des2, resize_factor, mid_strips_template, mid_strips_master)

        dx_si = dx_pix*hfw/image_width
        dy_si = dy_pix*hfw/image_width

        print('dx_pix, dy_pix', number_format(dx_pix), number_format(dy_pix), 'dx_si, dy_si', number_format(dx_si), number_format(dy_si))

        displacement.append([displacement[-1][0] + dx_si, displacement[-1][1] + dy_si])
        angle.append(angle[-1] + angle_step)

        eucentric_error += abs(dy_pix)

        mid_strips_master = deepcopy(mid_strips_template)
        kp2 = cv2_copy(kp1)
        des2 = deepcopy(des1)
        img_master = deepcopy(img_template)

    print('Done calculation')
    
    correct_eucentric(displacement[:], angle[:])
    
    exit()







