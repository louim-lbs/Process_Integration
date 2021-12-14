from numpy.core.fromnumeric import mean
from scipy import interpolate
import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv

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

# plt.plot([i/pas for i in angle_sort], [i[0]-offset for i in displacement])
# plt.plot([i/pas for i in angle_sort], displacement_filt)
# plt.show()

finterpa = interpolate.CubicSpline([i/pas for i in angle_sort], displacement_filt) # i[0] -> displacement in x direction of images (vertical)
displacement_y_interpa = finterpa(alpha)

plt.plot(alpha, displacement_y_interpa)
plt.show()

displacement_y_interpa_prime = [0]*len(displacement_y_interpa)

# print(alpha)
## z0 computation
for j in range(1,len(displacement_y_interpa)-1):
    displacement_y_interpa_prime[j] = (displacement_y_interpa[j+1]-displacement_y_interpa[j-1])/((alpha[j+1]-alpha[j-1])*np.pi/180)
displacement_y_interpa_prime[0] = displacement_y_interpa_prime[1]   # Edge effect correction
displacement_y_interpa_prime[-1] = displacement_y_interpa_prime[-2] # Edge effect correction
# del displacement_y_interpa_prime[-1] # Edge effect correction


plt.plot(alpha, displacement_y_interpa_prime)
plt.show()

z0_calc = displacement_y_interpa_prime[index_0]
###############################index0 is not the same for alpha, there are much more values than for angle

## yA computation
y0_calc = [0]*len(displacement_y_interpa_prime)
for i in range(index_0):
    y0_calc[i] = (displacement_y_interpa_prime[i] - z0_calc*np.cos(alpha[i]*np.pi/180))/(np.sin(alpha[i]*np.pi/180))
for i in range(index_0, len(displacement_y_interpa_prime)): # derivative is not define for angle_sort=0
    y0_calc[i] = (displacement_y_interpa_prime[i] - z0_calc*np.cos(alpha[i]*np.pi/180))/(np.sin(alpha[i]*np.pi/180))
# del y0_calc[index_0] # delete not computed 0-angle_sort value from the result list

plt.plot(y0_calc)
plt.show()

print('z0, y0 =', z0_calc, direction*mean(y0_calc))