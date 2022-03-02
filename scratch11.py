import glob
import os
from copy import deepcopy
from tracemalloc import stop
from tifffile import imread


def insert_str(string, index, param):
    return string[:index] + param + string[index:]

path = 'images/'
img_path_0 = ''
img_prev_path_0 = ''

while True:
    if 0 == 1:
        exit()
    # Load two most recent images
    try:
        list_of_imgs  = glob.glob(path + '*.tif')
        img_path      = max(list_of_imgs, key=os.path.getctime)
        list_of_imgs.remove(img_path)
        img_prev_path = max(list_of_imgs, key=os.path.getctime)
        
        if img_path == img_path_0 or img_prev_path == img_prev_path_0:
            print('nope, images already loaded')
            continue
        else:
            img_path_0      = deepcopy(img_path)
            img_prev_path_0 = deepcopy(img_prev_path)
            
        print(img_path)
        print(img_prev_path)
        # img       = imread(path + img_path)
        # img_prev  = imread(path + img_prev_path)
    except:
        print('nope, error')
        continue