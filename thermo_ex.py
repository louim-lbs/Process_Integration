from lol import get_image, get_active_view, set_active_view, deepcopy

def acquire_frame():
    img = get_image()
    img_prev_stamp = img.data[-1,:]

    while (True):
        img = get_image()
        if not (img_prev_stamp == img.data[-1,:]).all():
            return img
        
        
def acquire_multiple_frames(windows='123'):
    windows         = [int(s) for s in windows]

    imgs            = [0]*len(windows)
    
    view = get_active_view()
    ind = windows.index(view)
    imgs[ind] = get_image()
    img_prev_stamp = imgs[ind].data[-1,:]

    while (True):
        imgs[ind] = get_image()
        if not (img_prev_stamp == imgs[ind].data[-1,:]).all():
            for j in windows:
                set_active_view(j)
                imgs[windows.index(j)] = get_image()
            return imgs