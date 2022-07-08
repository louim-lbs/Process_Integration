import matplotlib.pyplot as plt
import os
import sys
sys.path.insert(1, r'D:\SharedData\LM LEBAS\Process_Integration')
os.chdir(r'D:\SharedData\LM LEBAS\Process_Integration')

from com_functions import SMARACT_MCS_3D

micro = SMARACT_MCS_3D()

try:
    micro.import_package_and_connexion()
    print('Succes. import_package_and_connexion')
except:
    print('FAIL. import_package_and_connexion')

micro.relative_move(dy=10e-6)
exit()



# try:
#     micro.quattro.imaging.start_acquisition()
#     img_one = micro.acquire_frame(resolution='1536x1024', dwell_time=5e-6, bit_depth=16)
#     print('Succes. acquire_frame')
#     micro.quattro.imaging.stop_acquisition()
# except:
#     print('FAIL. acquire_frame')
# img_one2 = micro.image_array(img_one)
# plt.imshow(img_one2)
# plt.show()
# exit()

# for i in range(10):
#     micro.quattro.imaging.start_acquisition()
#     img_one = micro.acquire_multiple_frames(resolution='1536x1024', dwell_time=1e-6, bit_depth=16)
#     print('Succes. acquire_frame', i)
# # micro.quattro.imaging.stop_acquisition()

img_one2 = micro.image_array(img_one[0])
img_one3 = micro.image_array(img_one[2])
    
    
plt.imshow(img_one2)
plt.show()
plt.imshow(img_one3)
plt.show()
#plt.imshow(img_one2)
#plt.show()
exit()