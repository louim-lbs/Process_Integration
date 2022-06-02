from autoscript_sdb_microscope_client.structures import GrabFrameSettings, StagePosition
import numpy as np
import cv2 as cv
from numpy.core.fromnumeric import mean, std
from numpy.lib.function_base import disp
from scipy import interpolate
from scipy.optimize import curve_fit
import os
import matplotlib.pyplot as plt
from tkinter import Tk     # from tkinter import Tk for Python 3.x. To open a file
from tkinter.filedialog import askopenfilename
import csv

plt.style.use('dark_background')

def function_displacement(x, z, y, t):
    x = [i*1*np.pi/180 for i in x]
    # t = t*np.pi/180
    return (y*(1-np.cos(x)) + z*np.sin(x))/np.cos(t)

pas = 1 # 1° with smaract convention

Tk().withdraw() # Close the little useless tk window
file = open(askopenfilename())
file_read = list(csv.reader(file, delimiter = ';'))

angle =         [float(x[0])*7 for x in file_read]
displacement =  [float(x[1]) for x in file_read]

# plt.plot(angle, displacement)
# plt.show()

# print(displacement)
# print(angle)

angle_sort = sorted(angle)
if angle_sort == angle:
    direction = 1
else:
    direction = -1
    displacement.reverse()
# print('direction =', direction)

z0_ini, y0_ini = 0, 0


alpha = [1*i/pas for i in range(int(angle_sort[0]), int(angle_sort[-1]+1))]#, int(pas/20))]

displacement_filt = np.array([i for i in displacement])

finterpa = interpolate.CubicSpline([i/pas for i in angle_sort], displacement_filt) # i[0] -> displacement in x direction of images (vertical)
displacement_y_interpa = finterpa(alpha)

##
offset = displacement_y_interpa[min(range(len(alpha)), key=lambda i: abs(alpha[i]))]
displacement_y_interpa = np.array([i-offset for i in displacement_y_interpa])
##

res, cov = curve_fit(f=function_displacement, xdata=alpha, ydata=displacement_y_interpa, bounds=([-1e9, -1e9, -10*np.pi/180], [1e9, 1e9, 10*np.pi/180]))
z0_calc, y0_calc, t_axis = res
stdevs = np.sqrt(np.diag(cov))

print('z0 =', z0_calc, '+-', stdevs[0], 'y0 = ', direction*y0_calc, '+-', stdevs[1], 't0 = ', t_axis*180/np.pi, '+-', stdevs[2])

# plt.plot(alpha, displacement_y_interpa, 'blue')
# for i in range(0, 90, 10):
#     plt.plot(alpha, function_displacement(alpha, z0_calc, y0_calc, i))
#     plt.plot(alpha, function_displacement(alpha, z0_calc, y0_calc, -i))
# plt.show()

plt.plot([i/pas for i in angle_sort], [i-offset for i in displacement], 'green')
plt.plot(alpha, displacement_y_interpa, 'blue')
plt.plot(alpha, function_displacement(alpha, *res), 'red')
plt.show()

# print(z0_calc, y0_calc)