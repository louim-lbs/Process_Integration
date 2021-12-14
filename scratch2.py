from numpy.core.fromnumeric import mean
from scipy import interpolate
import numpy as np
import matplotlib.pyplot as plt


displacement = [[0, 0], [971.3723776223777, 0.0], [2116.2041083916083, 0.0], [3261.035839160839, 0.0], [4405.867569930069, 0.0], [5359.894012237762, 0.0], [6123.115166083915, 0.0], [7267.9468968531455, 0.0], [8221.973339160839, 0.0], [8985.194493006993, 0.0], [9748.415646853147, 0.0], [10511.636800699302, 0.0], [11274.857954545456, 0.0], [11656.468531468532, 0.0], [12419.689685314686, 0.0], [12801.300262237763, 0.0], [13564.521416083917, 0.0], [13946.131993006993, 0.0], [13946.131993006993, 0.0], [14709.353146853147, 0.0], [14709.353146853147, 0.0], [15090.963723776224, 0.0], [15090.963723776224, 0.0], [15090.963723776224, 0.0], [15090.963723776224, 0.0], [15090.963723776224, 0.0], [15090.963723776224, 0.0], [14709.353146853147, 0.0], [14327.742569930071, 0.0], [15090.963723776225, 0.0], [15090.963723776225, 0.0], [15090.963723776225, 0.0], [14709.35314685315, 0.0], [14327.742569930073, 0.0], [13946.131993006997, 0.0], [13564.52141608392, 0.0], [13182.910839160844, 0.0], [12801.300262237768, 0.0], [12419.689685314692, 0.0], [11656.468531468538, 0.0], [10893.247377622383, 0.0], [10130.026223776229, 0.0], [9366.805069930075, 0.0], [8603.58391608392, 0.0], [7840.362762237766, 0.0], [6695.531031468536, 0.0], [5550.699300699305, 0.0], [4193.861693861699, 0.0], [2870.945027195032, 0.0], [1598.9097707847752, 0.0], [-309.14311383060954, 0.0], [-2217.1959984459945, 0.0], [-3743.638306138302, 0.0], [-5429.085020881892, 0.0], [-7337.137905497277, 0.0], [-10008.411943958816, 0.0], [-12679.685982420355, 0.0], [-15732.57059780497, 0.0], [-18690.052568958818, 0.0], [-21742.937184343435, 0.0], [-24414.211222804974, 0.0]]

angle = [29999990, 28500008, 27500001, 26500010, 25500015, 24500005, 23500006, 22500010, 21499998, 20499995, 19500010, 18500008, 17500007, 16500010, 15499999, 14500008, 13500010, 12499999, 11499999, 10499995, 9499993, 8499984, 7499995, 6500002, 5500001, 4500000, 3500003, 2499999, 1499996, 499990, -500001, -1500008, -2500003, -3500000, -4499997, -5499999, -6500000, -7500007, -8500001, -9499999, -10500017, -11499996, -12500012, -13499998, -14500007, -15500004, -16499995, -17500007, -18500012, -19499999, -20499997, -21499998, -22499998, -23500004, -24500003, -25499999, -26499993, -27500007, -28499989, -29500001, -30500003]

angle_sort = sorted(angle)
if angle_sort == angle:
    direction = 1
else:
    direction = -1

z0_ini, y0_ini = 0, 0
print('z0_ini, y0_ini =', z0_ini, y0_ini)


pas = 1000000 # 1° with smaract convention
alpha = [i/pas for i in range(int(angle_sort[0]), int(angle_sort[-1]+1), int(pas/10))]

try:
    index_0 = angle.index(min([abs(i) for i in angle]))
except:
    index_0 = angle.index(-min([abs(i) for i in angle]))

index_0 = min(range(len(angle)), key=lambda i: abs(angle[i])) # index of the nearest value of 0
print(index_0)

############ offset?
# print(index_0)
# print(displacement[index_0])
offset = displacement[index_0][0]
plt.plot(angle)
plt.show()

plt.plot([i/pas for i in angle[:]], [i[0]-offset for i in displacement[:]])
plt.show()

finterpa = interpolate.CubicSpline([i/pas for i in angle_sort], [i[0]-offset for i in displacement]) # i[0] -> displacement in x direction of images (vertical)
displacement_y_interpa = finterpa(alpha)

displacement_y_interpa_prime = [0]*len(displacement_y_interpa)

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
for i in range(index_0+1, len(displacement_y_interpa_prime)): # derivative is not define for angle_sort=0
    y0_calc[i] = (displacement_y_interpa_prime[i] - z0_calc*np.cos(alpha[i]*np.pi/180))/(np.sin(alpha[i]*np.pi/180))
del y0_calc[index_0] # delete not computed 0-angle_sort value from the result list

print('z0, y0 =', z0_calc, direction*mean(y0_calc))