from numpy.core.fromnumeric import mean
from scipy import interpolate
import numpy as np
import matplotlib.pyplot as plt


displacement = [[0, 0], [7.911850965327922e-06, 0.0], [1.1943088286533426e-05, 3.505423757570003e-07], [1.4876142071187701e-05, 1.139262721210251e-06], [1.7335093736424305e-05, 1.7527118787850016e-06], [1.9878716850511038e-05, 1.7527118787850016e-06], [2.2078831498354316e-05, 2.1885836486407454e-06], [2.3656272189260817e-05, 2.0352213592470576e-06], [2.5316736074425556e-05, 2.2543103440951828e-06], [2.6762723374423183e-05, 2.184717372437543e-06], [2.83648115761251e-05, 2.555879887944955e-06], [2.9498597072714147e-05, 2.555879887944955e-06], [3.073097261248485e-05, 2.927042403452367e-06], [3.174152055509683e-05, 3.205414290082926e-06], [3.262303152942693e-05, 3.512138868870301e-06], [3.359733313263389e-05, 3.1177786961436757e-06], [3.4223669877552646e-05, 3.293049884022176e-06], [3.4837119035127396e-05, 3.293049884022176e-06], [3.530107217951166e-05, 3.7750456506880513e-06], [3.5185083893415594e-05, 4.125588026445052e-06], [3.48695957552343e-05, 4.476130402202052e-06]]

angle = [-10499997, -8999997, -7999996, -7000009, -5999994, -5000003, -3999992, -3000027, -1999992, -1000002, 9, 1000002, 1999992, 3000005, 4000002, 4999999, 6000003, 6999993, 8000022, 8999983, 10000002]


angle = sorted(angle)

z0_ini, y0_ini, _ = 0, 0, 0


pas = 1000000 # 1° with smaract convention
# alpha = [i/pas for i in angle]
alpha = [i/pas for i in range(int(angle[0]), int(angle[-1]+1), int(pas/10))]
plus = 0
# if 0 not in alpha:
#     alpha.append(0)
#     alpha = sorted(alpha)
#     plus = 1
print(plus)
print(angle)
print(alpha)

index_0 = alpha.index(0)

finterpa = interpolate.CubicSpline([i/pas for i in angle], [i[0] for i in displacement])
displacement_y_interpa = finterpa(alpha)

displacement_y_interpa_prime = [0]*len(displacement_y_interpa)



## z0 computation
for j in range(1,len(displacement_y_interpa)-1):
    displacement_y_interpa_prime[j] = (displacement_y_interpa[j+1]-displacement_y_interpa[j-1])/((alpha[j+1]-alpha[j-1])*np.pi/180)
displacement_y_interpa_prime[0] = displacement_y_interpa_prime[1]   # Edge effect correction
displacement_y_interpa_prime[-1] = displacement_y_interpa_prime[-2]   # Edge effect correction
# del displacement_y_interpa_prime[-1] # Edge effect correction

plt.plot([i/pas for i in angle[:]], [i[0] for i in displacement[:]])
plt.plot(alpha, displacement_y_interpa)
plt.show()
plt.plot(alpha, displacement_y_interpa_prime)
plt.show()

z0_calc = displacement_y_interpa_prime[index_0-1]

## yA computation
y0_calc = [0]*len(displacement_y_interpa_prime)
for i in range(index_0):
    y0_calc[i] = (displacement_y_interpa_prime[i] - z0_calc*np.cos(alpha[i]*np.pi/180))/(np.sin(alpha[i]*np.pi/180))
for i in range(index_0+1, len(displacement_y_interpa_prime)): # derivative is not define for angle=0
    y0_calc[i] = (displacement_y_interpa_prime[i] - z0_calc*np.cos(alpha[i]*np.pi/180))/(np.sin(alpha[i]*np.pi/180))
del y0_calc[index_0] # delete not computed 0-angle value from the result list

z0 = z0_ini + z0_calc*1000000000
y0 = y0_ini + mean(y0_calc)*1000000000

print('z0, y0', z0, y0)