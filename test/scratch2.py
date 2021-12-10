from numpy.core.fromnumeric import mean
from scipy import interpolate
import numpy as np

displacement = [[0, 0], [-3.8161057692307693e-07, 0.0], [-3.8161057692307693e-07, 0.0], [-6.802623327759197e-07, 0.0], [-6.802623327759197e-07, 0.0], [-1.0618729096989966e-06, 0.0], [-1.4434834866220735e-06, 0.0], [-1.8250940635451505e-06, 0.0], [-2.2067046404682274e-06, 0.0], [-2.9699257943143813e-06, 0.0], [-3.733146948160535e-06, 0.0]]

angle = [-9999993, -9000008, -8000014, -7000014, -6000014, -4999995, -4000008, -3000000, -1999996, -1000005, 0]

angle = sorted(angle)

z0_ini, y0_ini, _ = 0, 0, 0


pas = 1000000 # 1° with smaract convention
alpha = [i for i in range(int(angle[0]/pas), int(angle[-1]/pas)+1)]

index_0 = alpha.index(0)

finterpa = interpolate.CubicSpline([i/pas for i in angle[:]], [i[0] for i in displacement[:]])
displacement_y_interpa = finterpa(alpha)

displacement_y_interpa_prime = [0]*len(displacement_y_interpa)



## z0 computation
for j in range(1,len(displacement_y_interpa)-1):
    displacement_y_interpa_prime[j] = (displacement_y_interpa[j+1]-displacement_y_interpa[j-1])/((alpha[j+1]-alpha[j-1])*np.pi/180)
displacement_y_interpa_prime[0] = displacement_y_interpa_prime[1]   # Edge effect correction
displacement_y_interpa_prime[-1] = displacement_y_interpa_prime[-2]   # Edge effect correction
del displacement_y_interpa_prime[-1] # Edge effect correction

print(index_0)
print(len(displacement))
print(len(displacement_y_interpa))
print(len(displacement_y_interpa_prime))

z0_calc = displacement_y_interpa_prime[index_0]

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