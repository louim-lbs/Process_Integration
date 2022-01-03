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


displacement = [[0, 0], [9143.29869281161, 102.89189478999087], [14651.146556526252, 102.89189478999087], [18937.328916635015, 102.89189478999087], [21307.958172596405, 102.89189478999087], [22618.642616998135, 102.89189478999087], [22618.642616998135, 102.89189478999087], [21507.410153266235, 102.89189478999087], [19241.367482126672, -267.51892645397623], [14796.437627199066, -637.9297476979434], [8499.453666051624, -1008.3405689419105], [10.872345877378393, -1175.0254385016958], [-12860.903692350477, -1713.8048148565572], [-29236.961052610073, -2279.1686999131384]]
angle = [34999989, 27500011, 22499987, 17499991, 12499994, 7499999, 2500000, -2499999, -7499995, -12499997, -17499992, -22500003, -27500010, -32500005]
pas = 1 # 1° with smaract convention

angle = [i*1 for i in angle]

## Calcul de l'angle

disp_x = [i[1] for i in displacement]
plt.plot(angle, disp_x)
plt.show()



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

finterpa = interpolate.CubicSpline([i/pas for i in angle_sort], displacement_filt) # i[0] -> displacement in x direction of images (vertical)
displacement_y_interpa = finterpa(alpha)

##
offset = displacement_y_interpa[min(range(len(alpha)), key=lambda i: abs(alpha[i]))]
displacement_y_interpa = np.array([i-offset for i in displacement_y_interpa])
##

res, cov = curve_fit(f=function_displacement, xdata=alpha, ydata=displacement_y_interpa, p0=[0,0,0], bounds=([-1e9, -1e9, -10], [1e9, 1e9, 10]))
z0_calc, y0_calc, t_axis = res
stdevs = np.sqrt(np.diag(cov))

print('z0 =', z0_calc, '+-', stdevs[0], 'y0 = ', direction*y0_calc, '+-', stdevs[1], 't0 = ', t_axis*180/np.pi, '+-', stdevs[2])

plt.plot(alpha, displacement_y_interpa, 'blue')
for i in range(0, 90, 10):
    plt.plot(alpha, function_displacement(alpha, z0_calc, y0_calc, i))
    plt.plot(alpha, function_displacement(alpha, z0_calc, y0_calc, -i))
plt.show()

plt.plot([i/pas for i in angle_sort], [i[0]-offset for i in displacement], 'green')
plt.plot(alpha, displacement_y_interpa, 'blue')
plt.plot(alpha, function_displacement(alpha, *res), 'red')
plt.show()

# Check limits
# print(z0_calc, y0_calc)