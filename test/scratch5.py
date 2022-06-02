from autoscript_sdb_microscope_client.structures import GrabFrameSettings, StagePosition
import numpy as np
import cv2 as cv
from numpy.core.fromnumeric import mean, std
from scipy import interpolate
from scipy.optimize import curve_fit
import os
import matplotlib.pyplot as plt
from tkinter import Tk     # from tkinter import Tk for Python 3.x. To open a file
from tkinter.filedialog import askopenfilename
import csv

def function_displacement(x, z, y, t):
    x = [i*np.pi/180 for i in x]
    t = t*np.pi/180
    return (y*(1-np.cos(x)) + z*np.sin(x))/np.cos(t)


displacement = [[0, 0], [-194.9137760037293, 0.0], [1833.961437853271, 194.9137760037293], [2888.267771691625, 363.2484007342228], [3162.9190015150616, 363.2484007342228], [2826.2497520540746, 363.2484007342228], [2826.2497520540746, 363.2484007342228], [2241.508424042887, 363.2484007342228], [1656.767096031699, 363.2484007342228], [682.1982160130526, 363.2484007342228], [-173.25668978109275, 363.2484007342228]]
angle = [-8000068, -7999998, -6000005, -4000011, -1999996, -1, 1999998, 3999979, 5999988, 7999993, 10000018]
pas = 1 # 1° with smaract convention

angle = [i*1 for i in angle]

## Calcul de l'angle

# disp_x = [i[1] for i in displacement]
# plt.plot(angle, disp_x)
# plt.show()



# print(displacement)
# print(angle)
angle_sort = sorted(angle)
if angle_sort == angle:
    direction = 1
else:
    direction = -1
    displacement.reverse()

z0_ini, y0_ini = 0, 0
# print('z0_ini, y0_ini =', z0_ini, y0_ini)


pas = 1000000 # 1° with smaract convention
alpha = [i/pas for i in range(int(angle_sort[0]), int(angle_sort[-1]+1), int(pas/20))]

displacement_filt = np.array([i[0] for i in displacement])
print(displacement_filt)
# x = cv.blur(displacement_filt, (1, 3))
# displacement_filt = [i[0] for i in x]
# print(displacement_filt)
plt.plot([i/pas for i in angle_sort], displacement_filt, 'yellow')

# finterpa = interpolate.CubicSpline([i/pas for i in angle_sort], displacement_filt) # i[0] -> displacement in x direction of images (vertical)
finterpa = interpolate.PchipInterpolator([i/pas for i in angle_sort], displacement_filt) # i[0] -> displacement in x direction of images (vertical)

displacement_y_interpa = finterpa(alpha)

plt.plot([i/pas for i in angle_sort], [i[0] for i in displacement], 'green')
plt.plot(alpha, displacement_y_interpa, 'blue')
plt.show()

##
offset = displacement_y_interpa[min(range(len(alpha)), key=lambda i: abs(alpha[i]))]
displacement_y_interpa = np.array([i-offset for i in displacement_y_interpa])
##

res, cov = curve_fit(f=function_displacement, xdata=alpha, ydata=displacement_y_interpa, p0=[0,0,0], bounds=([-1e9, -1e9, -10], [1e9, 1e9, 10]))
z0_calc, y0_calc, t_axis = res
stdevs = np.sqrt(np.diag(cov))

print('z0 =', z0_calc, '+-', stdevs[0], 'y0 = ', direction*y0_calc, '+-', stdevs[1], 't0 = ', t_axis*180/np.pi, '+-', stdevs[2])

# plt.plot(alpha, displacement_y_interpa, 'blue')
# for i in range(0, 90, 10):
#     plt.plot(alpha, function_displacement(alpha, z0_calc, y0_calc, i))
#     plt.plot(alpha, function_displacement(alpha, z0_calc, y0_calc, -i))
# plt.show()

plt.plot([i/pas for i in angle_sort], [i[0]-offset for i in displacement], 'green')
plt.plot(alpha, displacement_y_interpa, 'blue')
plt.plot(alpha, function_displacement(alpha, *res), 'red')
plt.show()

# Check limits
# print(z0_calc, y0_calc)