import DigitalMicrograph as DM
import matplotlib.pyplot as plt
import os
import sys
sys.path.insert(1, r'C:\Users\Public\Documents\Lebas\Process_Integration')
os.chdir(r'C:\Users\Public\Documents\Lebas\Process_Integration')

from com_functions import FEI_TITAN_ETEM

micro = FEI_TITAN_ETEM()

try:
    micro.import_package_and_connexion()
    print('Succes. import_package_and_connexion')
except:
    print('FAIL. import_package_and_connexion')
    
try:
    x, y, z, a, b  = micro.current_position()
    print('Succes. current_position', x, y, z, a, b )
except:
    print('FAIL. current_position')
    
try:
    micro.relative_move(1e-7, 1e-7, 1e-7, 1e-7, 0)
    micro.relative_move(-1e-7, -1e-7, -1e-7, -1e-7, 0)
    print('Succes. relative_move', '+1-1')
except:
    print('FAIL. relative_move')
    
try:
    micro.absolute_move(0, 0, 0, 0, 0)
    micro.absolute_move(x, y, z, a, b)
    x, y, z, a, b = micro.current_position()
    print('Succes. absolute_move', '0, ini', x, y, z, a, b)
except:
    print('FAIL. absolute_move')

try:
    b = micro.horizontal_field_view()
    print('Succes. horizontal_field_view', b)
except:
    print('FAIL. horizontal_field_view')
    
try:
    m1 = micro.magnification()
    print('Succes. magnification', m1)
except:
    print('FAIL. magnification')
    
try:
    micro.focus(1e-7, 'rel')
    micro.focus(-1e-7, 'rel')
    w1 = micro.focus()
    micro.focus(w1 + 10e-7)
    micro.focus(w1 - 10e-7)
    w1 = micro.focus()
    print('Succes. focus', w1)
except:
    print('FAIL. focus')
    
try:
    w11, w21 = micro.beam_shift()
    micro.beam_shift(1e-7, 1e-7, 'rel')
    micro.beam_shift(-1e-7, -1e-7, 'rel')
    micro.beam_shift(w11 + 10e-7, w21 + 10e-7)
    micro.beam_shift(w11, w21)
    w12, w22 = micro.beam_shift()
    print('Succes. beam_shift', w11, w12, w21, w22)
except:
    print('FAIL. beam_shift')
    
try:
    r, d = micro.image_settings()
    print('Succes. image_settings', r, d)
except:
    print('FAIL. image_settings')
    
try:
    img_get = micro.get_image()
    print('Succes. get_image')
except:
    print('FAIL. get_image')
    
try:
    img_one = micro.acquire_frame()
    print('Succes. acquire_frame')
except:
    print('FAIL. acquire_frame')


try:
    img_get2 = micro.image_array(img_get)
    img_one2 = micro.image_array(img_one)
    print('Succes. image_array')
except:
    print('FAIL. image_array')
    
try:
    micro.save(img_one, r'C:\Users\Public\Documents\Lebas\Process_Integration\images\test')
    print('Succes. save')
except Exception as ex:
    print('FAIL. save', ex)
    
try:
    micro.beam_blanking(True)
    micro.beam_blanking(False)
    print('Succes. beam_blanking')
except:
    print('FAIL. beam_blanking')


plt.imshow(img_get2)
plt.show()
#plt.imshow(img_one2)
#plt.show()