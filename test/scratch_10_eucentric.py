import numpy as np
from scipy import interpolate
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

def function_displacement(x, z, y, R):
    x = [i*np.pi/180 for i in x]
    return y * (1 - np.cos(x)) + z * np.sin(x) + R * (1 - np.sin(x))  # np.multiply(x, x2))) + x3

def correct_eucentric(displacement, angle):
    angle_sort = sorted(angle)
    if angle_sort == angle:
        direction = 1
    else:
        direction = -1
        displacement.reverse()

    pas    = 1 # 1° with smaract convention
    alpha  = [i/pas for i in range(int(angle_sort[0]), int(angle_sort[-1]+1))]

    offset = displacement[min(range(len(angle_sort)), key=lambda i: abs(angle_sort[i]))][1]
    displacement_filt = np.array([i[1]-offset for i in displacement])
    
    finterpa               = interpolate.PchipInterpolator([i/pas for i in angle_sort], displacement_filt)
    displacement_y_interpa = finterpa(alpha)

    res, cov         = curve_fit(f=function_displacement, xdata=alpha, ydata=displacement_y_interpa, p0=[0,0,0], bounds=(-1e7, 1e7))
    z0_calc, y0_calc, R_calc = res
    stdevs           = np.sqrt(np.diag(cov))

    print('z0 =', z0_calc,
          'y0 = ', direction*y0_calc,
          'R = ', R_calc,)
    
    mod = function_displacement(alpha, *res)
    plt.plot([i/pas for i in angle_sort], [i[1]-offset for i in displacement], 'green')
    plt.plot(alpha, displacement_y_interpa, 'blue')
    plt.plot(alpha, mod , 'red') #- R_calc
    plt.show()

# displacement=[[0, 0], [-1407.2093776366057, 385.6446280995172], [-1828.2703491330174, 527.310001687095], [-1429.3704813995746, 594.2075392145623], [-90.63270099696479, 665.0402260083512], [1739.211707842581, 877.5382863897178], [4175.069103695654, 1137.2581379669437], [6956.184069388628, 1309.912812026804]]
# angle=[-9000138, -3000004, 1000008, 5000013, 9000003, 13000000, 16999996, 21000002]
displacement = [[0, 0], [-4.1341145833333334e-07, -6.407877604166667e-06], [-8.268229166666667e-07, -1.5089518229166667e-05], [-2.0670572916666664e-07, -2.1497395833333336e-05], [-2.0670572916666664e-07, -2.6044921875000003e-05], [-4.134114583333333e-07, -3.431315104166667e-05], [-4.134114583333333e-07, -3.8447265625e-05], [-4.134114583333333e-07, -4.444173177083334e-05], [-4.134114583333333e-07, -4.9609375000000005e-05], [-6.201171874999999e-07, -5.4570312500000006e-05], [-8.268229166666666e-07, -5.932454427083334e-05]]
angle = [0, 1.000007675, 2.000005717, 3.000006557, 3.999998981, 4.999998879, 5.999998477, 7.000004596999999, 8.000011397, 9.000013316999999, 10.000011845]



correct_eucentric(displacement, angle)



