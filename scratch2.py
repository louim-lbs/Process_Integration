from numpy.core.fromnumeric import mean
from numpy.lib.function_base import disp
from scipy import interpolate
import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv
global alpha, displacement_y_interpa

displacement = [[0, 0], [9143.29869281161, 102.89189478999087], [14651.146556526252, 102.89189478999087], [18937.328916635015, 102.89189478999087], [21307.958172596405, 102.89189478999087], [22618.642616998135, 102.89189478999087], [22618.642616998135, 102.89189478999087], [21507.410153266235, 102.89189478999087], [19241.367482126672, -267.51892645397623], [14796.437627199066, -637.9297476979434], [8499.453666051624, -1008.3405689419105], [10.872345877378393, -1175.0254385016958], [-12860.903692350477, -1713.8048148565572], [-29236.961052610073, -2279.1686999131384]]

angle = [34999989, 27500011, 22499987, 17499991, 12499994, 7499999, 2500000, -2499999, -7499995, -12499997, -17499992, -22500003, -27500010, -32500005]

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

offset = displacement[min(range(len(angle_sort)), key=lambda i: abs(angle_sort[i]))][0]
index_0 = min(range(len(alpha)), key=lambda i: abs(alpha[i])) # index of the nearest value of 0
# print(index_0)

############ offset?
# print(index_0)
# print(displacement[index_0])
# offset = displacement[index_0][0]
# plt.plot(angle)
# plt.show()

displacement_filt = np.array([i[0]-offset for i in displacement])
filt =  cv.GaussianBlur(displacement_filt, (1,3), 0)
for i in range(1,len(displacement_filt)-1):
    displacement_filt[i] = filt[i]

plt.plot([i/pas for i in angle_sort], [i[0]-offset for i in displacement])
plt.plot([i/pas for i in angle_sort], displacement_filt)
# plt.show()

finterpa = interpolate.CubicSpline([i/pas for i in angle_sort], displacement_filt) # i[0] -> displacement in x direction of images (vertical)
displacement_y_interpa = finterpa(alpha)

# plt.plot(alpha, displacement_y_interpa)
# plt.show()

displacement_y_interpa_prime = [0]*len(displacement_y_interpa)

# print(alpha)
## z0 computation
for j in range(1,len(displacement_y_interpa)-1):
    displacement_y_interpa_prime[j] = (displacement_y_interpa[j+1]-displacement_y_interpa[j-1])/((alpha[j+1]-alpha[j-1])*np.pi/180)
displacement_y_interpa_prime[0] = displacement_y_interpa_prime[1]   # Edge effect correction
displacement_y_interpa_prime[-1] = displacement_y_interpa_prime[-2] # Edge effect correction
# del displacement_y_interpa_prime[-1] # Edge effect correction


# plt.plot(alpha, displacement_y_interpa_prime)
# plt.show()

z0_calc = displacement_y_interpa_prime[index_0]
# print(z0_calc)
###############################index0 is not the same for alpha, there are much more values than for angle

############## yA computation II
displacement_y_interpa_prime_2 = [0]*len(displacement_y_interpa_prime)
# print(alpha)
## z0 computation
for j in range(1,len(displacement_y_interpa_prime)-1):
    displacement_y_interpa_prime_2[j] = (displacement_y_interpa_prime[j+1]-displacement_y_interpa_prime[j-1])/((alpha[j+1]-alpha[j-1])*np.pi/180)
displacement_y_interpa_prime_2[0] = displacement_y_interpa_prime_2[1]   # Edge effect correction
displacement_y_interpa_prime_2[-1] = displacement_y_interpa_prime_2[-2] # Edge effect correction
print(displacement_y_interpa_prime_2[index_0])
# plt.plot(alpha, displacement_y_interpa_prime_2)
# plt.show()
########### Result positive? 

## yA computation
y0_calc = [0]*len(displacement_y_interpa_prime)
for i in range(index_0):
    y0_calc[i] = (displacement_y_interpa_prime[i] - z0_calc*np.cos(alpha[i]*np.pi/180))/(np.sin(alpha[i]*np.pi/180))
for i in range(index_0, len(displacement_y_interpa_prime)): # derivative is not define for angle_sort=0
    y0_calc[i] = (displacement_y_interpa_prime[i] - z0_calc*np.cos(alpha[i]*np.pi/180))/(np.sin(alpha[i]*np.pi/180))
del y0_calc[index_0] # delete not computed 0-angle_sort value from the result list

# plt.plot(y0_calc)
# plt.show()

### yA computation III
y0_calc3 = [0]*len(displacement_y_interpa)
for i in range(len(displacement_y_interpa)):
    y0_calc3[i] = (displacement_y_interpa[i] - z0_calc*np.sin(alpha[i]*np.pi/180))/(1-np.cos(alpha[i]*np.pi/180))

# plt.plot(y0_calc3)
# plt.show()


### zA and yA computation IV
# from scipy.optimize import fsolve
# result = []
# for i in range(len(displacement_y_interpa)-1):
#     global a1, d1, a2, d2
#     a1 = alpha[i]
#     d1 = displacement_y_interpa[i]
#     a2 = alpha[i+1]
#     d2 = displacement_y_interpa[i+1]
#     def func(p):
#         zA, yA = p
#         eq = [yA*(1-np.cos(a1*np.pi/180)) + zA*np.sin(a1*np.pi/180) - d1,
#               yA*(1-np.cos(a2*np.pi/180)) + zA*np.sin(a2*np.pi/180) - d2]
#         print(eq)
#         return eq
#     result.append(fsolve(func, (1,1)))
#     print(result[-1])

# plt.plot([i[1] for i in result])
# plt.show()

# from scipy.optimize import fsolve
# result = []

# def func(p):
#     zA, yA = p
#     eq = []
#     for i in range(len(displacement_y_interpa)):
#         a = alpha[i]
#         d = displacement_y_interpa[i]
#         eq.append(yA*(1-np.cos(a*np.pi/180)) + zA*np.sin(a*np.pi/180) - d)
#     return eq

# result = fsolve(func, (1,1))
# print(result)

## zA and yA computation V

# from scipy.optimize import curve_fit

# def function_displacement(x, z, y):
#     return y*(1-np.cos(x*np.pi/180)) + z*np.sin(x*np.pi/180)

# print(len(displacement))
# print(len(displacement_y_interpa))
# pars, cov = curve_fit(f=function_displacement, xdata=[np.pi/180*i/pas for i in angle], ydata=[i[0]-offset for i in displacement], p0=[0,0], bounds=(-1e9, 1e9))

# print('zA, yA =', pars)

# plt.plot([i/pas for i in angle], [i[0]-offset for i in displacement], 'blue')
# plt.plot([i/pas for i in angle], function_displacement([i/pas for i in angle], *pars), 'red')
# plt.show()

from scipy.optimize import curve_fit

def function_displacement(x, z, y):
    x = [i*np.pi/180 for i in x]
    return y*(1-np.cos(x)) + z*np.sin(x)

pars, cov = curve_fit(f=function_displacement, xdata=alpha, ydata=displacement_y_interpa, p0=[12000,200000], bounds=(-1e9, 1e9))

print('zA, yA =', pars)

plt.plot(alpha, displacement_y_interpa, 'blue')
plt.plot(alpha, function_displacement(alpha, *pars), 'red')
plt.show()

print('z0, y0 =', z0_calc, direction*mean(y0_calc))