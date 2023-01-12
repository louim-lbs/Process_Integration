import DigitalMicrograph as DM
import matplotlib.pyplot as plt
import os
import sys
sys.path.insert(1, r'C:\Users\Public\Documents\Lebas\Process_Integration')
os.chdir(r'C:\Users\Public\Documents\Lebas\Process_Integration')

from com_functions import FEI_TITAN_ETEM

micro = FEI_TITAN_ETEM()

print(micro.image_shift())
print(micro.beam_shift(0, 0))
print(micro.projector_shift())