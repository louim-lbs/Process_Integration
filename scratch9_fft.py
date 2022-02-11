import time
import copy
import cv2 as cv
from cv2 import threshold
from matplotlib import image
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('dark_background')
from PIL import Image
from tifffile import imread
from scipy import signal
from scract10 import PSD2
from sklearn.cluster import KMeans



def fft_treh_filt(img, threshold=150):
    # plt.imshow(img)
    # plt.show()
    rows, cols = img.shape
    nrows = cv.getOptimalDFTSize(rows)
    ncols = cv.getOptimalDFTSize(cols)
    right = ncols - cols
    bottom = nrows - rows
    img = cv.copyMakeBorder(img, 0, bottom, 0, right, cv.BORDER_CONSTANT, value=0)
    
    # Compute FFT
    image_fft     = np.fft.fftshift(cv.dft(np.float32(img), flags=cv.DFT_COMPLEX_OUTPUT))
    image_fft_mag = 20*np.log(cv.magnitude(image_fft[:,:,0], image_fft[:,:,1]))
    # plt.imshow(cv.phase(image_fft[:,:,0], image_fft[:,:,1]), 'gray')
    # plt.show()
    # plt.imshow(image_fft_mag, 'gray')
    # plt.show()
    
    # Substract FFT background
    # treshold_calc = np.amin(img) + (np.amax(img) - np.amin(img))*100/255
    # image_fft_mag = image_fft_mag - np.full(shape=image_fft_mag.shape, fill_value=treshold_calc)
    # image_fft_mag[image_fft_mag<0] = 0
          
    
    # threshold32 = np.amin(image_fft_mag) + (np.amax(image_fft_mag) - np.amin(image_fft_mag))*threshold/255
    
    # image_fft_mag_tresh = cv.bitwise_not(np.uint8(cv.threshold(image_fft_mag, threshold32, np.amax(image_fft_mag), cv.THRESH_BINARY)[1]))
    # # plt.imshow(image_fft_mag_tresh, 'gray')
    # # plt.show()
    # # Delete isolated pixels
    # image_fft_mag_tresh_comp = cv.bitwise_not(image_fft_mag_tresh)

    # kernel1 = np.array([[0, 0, 0,],
    #                     [0, 1, 0] ,
    #                     [0, 0, 0]], np.uint8)
    # kernel2 = np.array([[1, 1, 1,],
    #                     [1, 0, 1] ,
    #                     [1, 1, 1]], np.uint8)

    # hitormiss1 = cv.morphologyEx(image_fft_mag_tresh,      cv.MORPH_ERODE, kernel1)
    # hitormiss2 = cv.morphologyEx(image_fft_mag_tresh_comp, cv.MORPH_ERODE, kernel2)
    # hitormiss = cv.bitwise_and(hitormiss1, hitormiss2)
    # hitormiss_comp = cv.bitwise_not(hitormiss)
    # image_fft_mag_tresh_filt = cv.bitwise_and(image_fft_mag_tresh, image_fft_mag_tresh, mask=hitormiss_comp)
    
    return image_fft_mag#_tresh#_filt

def find_ellipse(img, treshold):
    
    plt.imshow(img, 'gray')
    # plt.show()
    
    # # rectKernel = cv.getStructuringElement(cv.MORPH_RECT, (6, 6))
    # # sqKernel   = cv.getStructuringElement(cv.MORPH_RECT, (30, 30))
    
    # Kernel1 = cv.getStructuringElement(cv.MORPH_RECT, (5, 5)) #20/#10
    # Kernel2 = cv.getStructuringElement(cv.MORPH_RECT, (7, 7)) #14
    # Kernel3 = cv.getStructuringElement(cv.MORPH_RECT, (2, 2))

    # img = cv.morphologyEx(img, cv.MORPH_DILATE, cv.getStructuringElement(cv.MORPH_RECT, (2, 2)))
    # plt.imshow(img, 'gray')
    # plt.show()
    
    # for i in range(1): #6
        
    #     img = cv.morphologyEx(img, cv.MORPH_OPEN,   cv.getStructuringElement(cv.MORPH_RECT, (2, 2)))
    #     # plt.imshow(img, 'gray')
    #     # plt.show()
        
    #     img = cv.morphologyEx(img, cv.MORPH_ERODE,   cv.getStructuringElement(cv.MORPH_RECT, (2, 2)))
    #     plt.imshow(img, 'gray')
    #     plt.show()
    
    
    # img = cv.morphologyEx(img, cv.MORPH_OPEN,   cv.getStructuringElement(cv.MORPH_RECT, (2, 2)))
    # plt.imshow(img, 'gray')
    # plt.show()
    
    img = cv.morphologyEx(img, cv.MORPH_CLOSE,   cv.getStructuringElement(cv.MORPH_RECT, (5, 5)))
    # plt.imshow(img, 'gray')
    # plt.show()
    img = cv.medianBlur(img, 63)#, sigmaX=100, sigmaY=100)
    # plt.imshow(img, 'gray')
    # plt.show()
    # img = cv.morphologyEx(img, cv.MORPH_CLOSE,   cv.getStructuringElement(cv.MORPH_RECT, (5, 5)))
    # plt.imshow(img, 'gray')
    # plt.show()
    
    # img = cv.morphologyEx(img, cv.MORPH_ERODE,   cv.getStructuringElement(cv.MORPH_RECT, (5, 5)))
    # plt.imshow(img, 'gray')
    # plt.show()
    
    # img = cv.morphologyEx(img, cv.MORPH_DILATE,   cv.getStructuringElement(cv.MORPH_RECT, (5, 5)))
    # plt.imshow(img, 'gray')
    # plt.show()
    
    # # for i in range(5):
    # #     Kernel1 = cv.getStructuringElement(cv.MORPH_RECT, (i+1, i+1)) #20/#10
    # #     Kernel2 = cv.getStructuringElement(cv.MORPH_RECT, (i+2, i+2)) #14
    # #     img = cv.morphologyEx(img, cv.MORPH_OPEN,   Kernel1, borderType=cv.BORDER_REPLICATE)
    # #     img = cv.morphologyEx(img, cv.MORPH_DILATE, Kernel2)
    # #     plt.imshow(img, 'gray')
    # #     plt.show()
    
    # # img = cv.morphologyEx(img, cv.MORPH_OPEN, Kernel1, borderType=cv.BORDER_REPLICATE)
    # # plt.imshow(img, 'gray')
    # # plt.show()  
    # # img = cv.morphologyEx(img, cv.MORPH_DILATE, Kernel2)
    # # plt.imshow(img, 'gray')
    # # plt.show()
        
    img = cv.medianBlur(img, 63)#, sigmaX=100, sigmaY=100)
    # plt.imshow(img, 'gray')
    # plt.show()

    treshold_calc = np.amin(img) + (np.amax(img) - np.amin(img))*treshold/255
    img = cv.threshold(img, treshold_calc, 255, cv.THRESH_TOZERO)[1]
    # plt.imshow(img, 'gray')
    # plt.show()
    
    contours, _ = cv.findContours(img, mode=cv.RETR_LIST, method=cv.CHAIN_APPROX_NONE)
    if len(contours) != 0:
        ind = np.argmax([len(cont) for cont in contours])
        contours = contours[:ind] + contours[ind+1:]
        if len(contours) == 0:
            print('no contour found')
            return ((0, 0), (0, 0), 0)
        ind = np.argmax([len(cont) for cont in contours])

        cont = contours[ind]
        if len(cont) < 5:
            print('len contour < 5', len(contours))
            # plt.imshow(img)
            # plt.show()
            pass

        elps = cv.fitEllipse(cont)
        # plt.imshow(img, 'gray', alpha=0.1)
        plt.plot([i[0][0] for i in cont], [i[0][1] for i in cont])

        u =     elps[0][0]        # x-position of the center
        v =     elps[0][1]        # y-position of the center
        a =     elps[1][0]/2        # radius on the x-axis
        b =     elps[1][1]/2        # radius on the y-axis
        t_rot = elps[2]*np.pi/180 # rotation angle

        t = np.linspace(0, 2*np.pi, 100)
        Ell = np.array([a*np.cos(t) , b*np.sin(t)])  
            #u,v removed to keep the same center location
        R_rot = np.array([[np.cos(t_rot) , -np.sin(t_rot)],[np.sin(t_rot) , np.cos(t_rot)]])  
            #2-D rotation matrix

        Ell_rot = np.zeros((2,Ell.shape[1]))
        for i in range(Ell.shape[1]):
            Ell_rot[:,i] = np.dot(R_rot,Ell[:,i])

        plt.plot( u+Ell_rot[0,:] , v+Ell_rot[1,:],'r' )
        plt.savefig('images/ellipse/' + str(time.time()) + '.tif')
        plt.clf()
        # plt.show()
        return elps
    else:
        print('no contour found')
        # plt.imshow(img, 'gray')
        # plt.show()
    return ((0, 0), (0, 0), 0)

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

def tomo_acquisition(work_folder='data/tomo/', images_name='image', resolution='1536x1024', bit_depth=16, dwell_time=0.2e-6, tilt_increment=2000000, tilt_end=60000000, drift_correction:bool=False, focus_correction:bool=False) -> int:
    
    # file = open(askopenfilename())

    stack = imread('E:\LM LEBAS\Quattro 2022-02-08\Stack_90_focus_0.25-20_0.5-40-0-60.tif')
    # stack = imread('images\\Stack_64_stigY-1.tif')
    
    if stack.dtype == np.uint8:
        dtype_number = 255
    else:
        dtype_number = 65536

    image_width = stack.shape[2]
    image_height = stack.shape[1]

    ellipse_array = np.zeros((5, stack.shape[0]))

    # Create radial alpha/transparency layer. 255 in centre, 0 at edge
    Y = np.linspace(-1, 1, image_height)[None, :]*dtype_number
    X = np.linspace(-1, 1, image_height)[:, None]*dtype_number
    alpha_factor = 1
    alpha = np.sqrt(alpha_factor*X**2 + alpha_factor*Y**2)
    alpha = (dtype_number - np.clip(0, dtype_number, alpha))/dtype_number

    for i in range(stack.shape[0]):
        
        if focus_correction == True:
            # img  = cv.resize(stack[i], None, fx=0.25, fy=0.25, interpolation=cv.INTER_CUBIC)
            img_crop = stack[i][:,(image_width-image_height)//2:(image_width+image_height)//2]
            
            img_crop = np.uint16(np.multiply(img_crop, alpha))
            
            
            threshold = 130 #128
            
            # fft = fft_treh_filt(image_for_fft, threshold) #185
            fft = fft_treh_filt(img_crop, threshold) #185
            
            vec_image = np.reshape(fft, (-1,1))
            labels = KMeans(n_clusters=2).fit_predict(vec_image)

            # removing background by clustering pixels and sorting means (lowest mean 
            # corresponds to darkest object, here it's a chromosome)

            means = [np.mean(vec_image[labels == label]) for label in np.unique(labels)]
            index_array = np.argsort(means)[0:1]
            mask = np.array([label in index_array for label in labels])
        
            binary_image = np.reshape(mask, fft.shape)
            
            fft = np.uint8(binary_image)
            
            elps = find_ellipse(fft, threshold)


            if elps != None:
                print(elps)
                ellipse_array[0][i] = (elps[0][0])# + ellipse_array[0][i-1])/2
                ellipse_array[1][i] = (elps[0][1])# + ellipse_array[1][i-1])/2
                ellipse_array[2][i] = (elps[1][0])# + ellipse_array[2][i-1])/2
                ellipse_array[3][i] = (elps[1][1])# + ellipse_array[3][i-1])/2
                ellipse_array[4][i] = (elps[2])#    + ellipse_array[4][i-1])/2
            
            # img = cv.blur(img, ksize=(1,1))
            # plt.imshow(img)
            # plt.show()
            img = img_crop
            
            focus_score_lap = cv.Laplacian(img, cv.CV_16U).var()
            focus_score_me  = np.mean(img)
            focus_score_me2 = np.mean(img[img>dtype_number//2.5])
            focus_score_me6 = np.mean(img[img>dtype_number//3])
            focus_score_me7 = np.mean(img[img>dtype_number//3.5])
            focus_score_me3 = np.average(img, weights=np.power(img, 2))
            focus_score_me4 = np.average(img, weights=np.power(img, 3))
            focus_score_me5 = np.average(img, weights=np.power(img, 4))
            focus_score_std = np.std(img)
            focus_score_std2 = np.std(img[img>dtype_number//2])
            corr = np.mean(img[img<dtype_number//2])
            corr_std = np.std(img[img<dtype_number//2])
            img2 = img - np.full(img.shape, corr + corr_std)
            focus_score_std3 = np.std(img2[img2>0])


            if i == 0:
                focus_scores_laplac = [focus_score_lap]
                focus_scores_mean   = [focus_score_me]
                focus_scores_mean2  = [focus_score_me2]
                focus_scores_mean6  = [focus_score_me6]
                focus_scores_mean7  = [focus_score_me7]
                focus_scores_mean3  = [focus_score_me3]
                focus_scores_mean4  = [focus_score_me4]
                focus_scores_mean5  = [focus_score_me5]
                focus_scores_std    = [focus_score_std]
                focus_scores_std2   = [focus_score_std2]
                focus_scores_std3   = [focus_score_std3]
    
            focus_scores_laplac.append((focus_score_lap))# + focus_scores_laplac[-1])/2)
            focus_scores_mean.append((  focus_score_me))#  + focus_scores_mean[-1])/2)
            focus_scores_mean2.append(( focus_score_me2))# + focus_scores_mean2[-1])/2)
            focus_scores_mean3.append(( focus_score_me3))# + focus_scores_mean3[-1])/2)
            focus_scores_mean4.append(( focus_score_me4))# + focus_scores_mean4[-1])/2)
            focus_scores_mean5.append(( focus_score_me5))# + focus_scores_mean5[-1])/2)
            focus_scores_mean6.append(( focus_score_me6))# + focus_scores_mean6[-1])/2)
            focus_scores_mean7.append(( focus_score_me7))# + focus_scores_mean7[-1])/2)
            focus_scores_std.append((   focus_score_std))# + focus_scores_std[-1])/2)
            focus_scores_std2.append((  focus_score_std2))# + focus_scores_std2[-1])/2)
            focus_scores_std3.append((  focus_score_std3))# + focus_scores_std3[-1])/2)


            # print(time.time()-t, 's')

        # images_prev = copy.deepcopy(images)

    print('Tomography is a Succes')
    
    # plt.plot(ellipse_array[0], 'b')
    # plt.plot(ellipse_array[1], 'b')
    fig, axs = plt.subplots(2, 2)
    axs[0, 0].plot(ellipse_array[2], '-ro', label='a')
    axs[0, 0].plot(ellipse_array[3], '-bv', label='b')
    axs[0, 0].set_title('a and b ellipse parameters (pix)')
    axs[0, 0].legend(loc='upper right')

    axs[0, 1].plot(ellipse_array[4], '-bo', label='teta')
    axs[0, 1].set_title('teta ellipse parameter (°)')
    axs[0, 1].legend(loc='upper right')

    axs[1, 0].plot((ellipse_array[3]/ellipse_array[2] - 1)*100, '-ro') # Analyze of b/a parameter -> astigmatism
    axs[1, 0].set_title('b/a (D%)')

    axs[1, 1].plot([(i-np.min(focus_scores_laplac))/(np.max(focus_scores_laplac)-np.min(focus_scores_laplac)) for i in focus_scores_laplac], '-ws', label='Laplacian var.')
    axs[1, 1].plot([(i-np.min(focus_scores_mean))  /(np.max(focus_scores_mean) - np.min(focus_scores_mean))   for i in focus_scores_mean],   '-ro', label='Mean',               alpha=0.15)
    axs[1, 1].plot([(i-np.min(focus_scores_mean2)) /(np.max(focus_scores_mean2)- np.min(focus_scores_mean2))  for i in focus_scores_mean2],  '-rv', label='Mean > 1/2.5',       alpha=0.15)
    axs[1, 1].plot([(i-np.min(focus_scores_mean6)) /(np.max(focus_scores_mean6)- np.min(focus_scores_mean6))  for i in focus_scores_mean6],  '-gv', label='Mean > 1/3',         alpha=0.15)
    axs[1, 1].plot([(i-np.min(focus_scores_mean7)) /(np.max(focus_scores_mean7)- np.min(focus_scores_mean7))  for i in focus_scores_mean7],  '-bv', label='Mean > 1/3.5',       alpha=0.15)
    axs[1, 1].plot([(i-np.min(focus_scores_mean3)) /(np.max(focus_scores_mean3)- np.min(focus_scores_mean3))  for i in focus_scores_mean3],  '-r+', label='AW 2', alpha=0.15)
    axs[1, 1].plot([(i-np.min(focus_scores_mean4)) /(np.max(focus_scores_mean4)- np.min(focus_scores_mean4))  for i in focus_scores_mean4],  '-g+', label='AW 3', alpha=0.15)
    axs[1, 1].plot([(i-np.min(focus_scores_mean5)) /(np.max(focus_scores_mean5)- np.min(focus_scores_mean5))  for i in focus_scores_mean5],  '-b+', label='AW 4', alpha=0.15)
    axs[1, 1].plot([(i-np.min(focus_scores_std))   /(np.max(focus_scores_std)  - np.min(focus_scores_std))    for i in focus_scores_std],    '-o', color='orange', label='Std Dev', alpha=0.15)
    axs[1, 1].plot([(i-np.min(focus_scores_std2))   /(np.max(focus_scores_std2)  - np.min(focus_scores_std2))    for i in focus_scores_std2],    '-v', color='orange', label='Std Dev > 1/2', alpha=0.15)
    axs[1, 1].plot([(i-np.min(focus_scores_std3))   /(np.max(focus_scores_std3)  - np.min(focus_scores_std3))    for i in focus_scores_std3],    '-s', color='orange', label='Std Dev > NM', mfc = 'r')#, alpha=0.15)
    axs[1, 1].set_title('Normalized focus score by Laplacian and different means')
    axs[1, 1].legend(loc='upper left')

    # axs[1, 1].plot([i for i in focus_scores_laplac], '-ws', label='Laplacian var.')
    # axs[1, 1].plot([i for i in focus_scores_mean], '-ro', label='Mean')
    # axs[1, 1].plot([i for i in focus_scores_mean2], '-rv', label='Mean > 1/2.5')
    # axs[1, 1].plot([i for i in focus_scores_mean6], '-gv', label='Mean > 1/3')
    # axs[1, 1].plot([i for i in focus_scores_mean7], '-bv', label='Mean > 1/3.5')
    # axs[1, 1].plot([i for i in focus_scores_mean3], '-r+', label='Average weighted 2')
    # axs[1, 1].plot([i for i in focus_scores_mean4], '-g+', label='Average weighted 3')
    # axs[1, 1].plot([i for i in focus_scores_mean5], '-b+', label='Average weighted 4')
    # axs[1, 1].plot([i for i in focus_scores_std],   '-o', color='orange', label='Std Dev')
    # axs[1, 1].set_title('Focus score by Laplacian and different means')
    # axs[1, 1].legend(loc='upper left')

    plt.show()
    return 0

## noise fait que le blur détection est pas exact. blur reult,
## proportionel et pas limite
## gérer les nan
## zone de l'image à analyser :les tilts font que les bords supérieurs ou inférieurs seront flous
## gérer la correction


if __name__ == "__main__":
    tomo_acquisition(bit_depth=16,
                     dwell_time=1e-6,
                     tilt_increment=int(2*1e6),
                     tilt_end=int(70*1e6),
                     drift_correction=True,
                     focus_correction=True)