from scipy import interpolate
import numpy as np
from numpy.core.fromnumeric import mean
import matplotlib.pyplot as plt

displacement = [[0, 0], [1.1902804904513889e-05, -5.874794407894737e-07], [2.4068045023999185e-05, -8.200233861019738e-07], [3.601346032005182e-05, -1.203036943087268e-06], [4.8260774773176824e-05, -1.803775468477893e-06], [6.0280104966191526e-05, -2.027706675075115e-06], [7.19266808939259e-05, -2.7511767271584485e-06], [8.396424982774944e-05, -2.6964605047319777e-06], [9.566034900309666e-05, -3.079474061717272e-06], [0.00010752009021403416, -3.389532655467272e-06], [0.00011961237537028416, -3.5617874297728273e-06], [0.00013179078791368694, -3.8029441138006052e-06], [0.00014438261191542306, -4.058286485124135e-06], [0.00015693998496229807, -4.368345078874135e-06], [0.0001691011720282703, -4.895444688249135e-06], [0.00018166670451182294, -5.417648635617556e-06], [0.00019406904826182292, -5.7277072293675565e-06], [0.00020625435099619793, -5.711388356012294e-06], [0.0002191952175669216, -6.021446949762294e-06], [0.00023164923774921328, -6.400407453234516e-06], [0.00024379047952552906, -6.6587896146928496e-06], [0.0002558517588224041, -6.96884820844285e-06], [0.00026828510843177907, -7.244455847331738e-06], [0.000281242293875858, -7.66874655456858e-06], [0.0002940632167274205, -8.118331515506081e-06], [0.00030713463428498633, -8.52630334938766e-06], [0.0003202191069412363, -8.901637436558713e-06], [0.0003333394811188679, -9.211696030308713e-06], [0.0003466564977204304, -9.50543575070345e-06], [0.00036031539471878565, -9.848132091163977e-06], [0.00037363382067759246, -1.0158190684913977e-05]]

angle = [0, 999997, 1999989, 3000000, 3999994, 4999999, 6000007, 6999983, 7999995, 9000001, 9999991, 11000007, 12000014, 13000001, 14000001, 15000001, 15999995, 17000009, 17999999, 19000000, 19999993, 21000009, 22000003, 23000009, 24000000, 25000000, 25999998, 27000000, 28000024, 28999991, 29999994]

pas = 1000000
z0_ini, y0_ini = -1, 0

alpha = [i for i in range(int(angle[0]/pas), int(angle[-1]/pas)+1)]
index_0 = alpha.index(0)

finterpa = interpolate.CubicSpline([i/pas for i in angle[:]], [i[0] for i in displacement[:]])
displacement_y_interpa = finterpa(alpha)

displacement_y_interpa_prime = [0]*len(displacement_y_interpa)

## z0 computation
for j in range(1,len(displacement_y_interpa)-1):
    displacement_y_interpa_prime[j] = (displacement_y_interpa[j+1]-displacement_y_interpa[j-1])/((alpha[j+1]-alpha[j-1])*np.pi/180)
displacement_y_interpa_prime[0] = displacement_y_interpa_prime[1]   # Edge effect correction
del displacement_y_interpa_prime[-1] # Edge effect correction

z0_calc = displacement_y_interpa_prime[index_0]

plt.plot([i/pas for i in angle[:]], [i[0] for i in displacement[:]])
plt.plot(alpha, displacement_y_interpa)
plt.show()
plt.plot(alpha[:-1], displacement_y_interpa_prime)
plt.show()

## yA computation
y0_calc = [0]*len(displacement_y_interpa_prime)
for i in range(index_0):
    y0_calc[i] = (displacement_y_interpa_prime[i] - z0_calc*np.cos(alpha[i]*np.pi/180))/(np.sin(alpha[i]*np.pi/180))
for i in range(index_0+1, len(displacement_y_interpa_prime)): # derivative is not define for angle=0
    y0_calc[i] = (displacement_y_interpa_prime[i] - z0_calc*np.cos(alpha[i]*np.pi/180))/(np.sin(alpha[i]*np.pi/180))
del y0_calc[index_0] # delete not computed 0-angle value from the result list

plt.plot(y0_calc)
plt.show()

z0 = z0_ini + z0_calc*1000000000
y0 = y0_ini + mean(y0_calc)*1000000000

print(z0, y0)