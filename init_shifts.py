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
    micro.image_shift(0, 0)
    micro.beam_shift(0, 0)
    micro.projector_shift(0, 0)
    
    #micro.beam_shift(1e-6, 0, 'rel')
    #micro.image_shift(1e-6, 0, 'rel')
    w11, w12 = micro.beam_shift()
    w21, w22 = micro.image_shift()
    
    print('Succes. beam_shift', w11, w12, w21, w22)
except:
    print('FAIL. beam_shift')
 