import numpy as np
from scipy import interpolate
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

def function_displacement(x, z, y, R, x2, x3):
    x = [i*np.pi/180 for i in x]
    return y*(1-np.cos(x)) + z*np.sin(x) + R*(1-np.sin(np.multiply(x, x2))) + x3 #+ x2))5.435457

def correct_eucentric(displacement, angle):
    angle_sort = sorted(angle)
    if angle_sort == angle:
        direction = 1
    else:
        direction = -1
        displacement.reverse()
    
    z0_ini, y0_ini, _ = 0, 0, 0

    if displacement == [[0,0]]:
        return z0_ini, y0_ini

    pas    = 1000000 # 1° with smaract convention
    alpha  = [i/pas for i in range(int(angle_sort[0]), int(angle_sort[-1]+1), int(pas/20))]

    offset = displacement[min(range(len(angle_sort)), key=lambda i: abs(angle_sort[i]))][0]

    displacement_filt = np.array([i[0]-offset for i in displacement])
    
    finterpa               = interpolate.PchipInterpolator([i/pas for i in angle_sort], displacement_filt)
    displacement_y_interpa = finterpa(alpha)

    res, cov         = curve_fit(f=function_displacement, xdata=alpha, ydata=displacement_y_interpa, p0=[0,0,0,5,0], bounds=(-1e7, 1e7))
    z0_calc, y0_calc, R_calc, x2_calc, x3_calc = res
    stdevs           = np.sqrt(np.diag(cov))

    print('z0 =', z0_calc,
          'y0 = ', direction*y0_calc,
          'R = ', R_calc,
          'x2 = ', x2_calc,
          'x3 = ', x3_calc)
    
    mod = function_displacement(alpha, *res)
    plt.plot([i/pas for i in angle_sort], [i[0]-offset for i in displacement], 'green')
    plt.plot(alpha, displacement_y_interpa, 'blue')
    plt.plot(alpha, mod , 'red') #- R_calc
    plt.show()

# displacement=[[0, 0], [-1407.2093776366057, 385.6446280995172], [-1828.2703491330174, 527.310001687095], [-1429.3704813995746, 594.2075392145623], [-90.63270099696479, 665.0402260083512], [1739.211707842581, 877.5382863897178], [4175.069103695654, 1137.2581379669437], [6956.184069388628, 1309.912812026804]]
# angle=[-9000138, -3000004, 1000008, 5000013, 9000003, 13000000, 16999996, 21000002]
displacement = [[0, 0], [-1980.1047631931124, -736.3253108965688], [-2602.8030971598823, -945.4101986431345], [-3049.868567700127, -1059.5996853597148], [-3626.328597193484, -1098.5816135836508], [-3834.5275320258693, -1165.7275186583731], [-3314.768489040056, -1236.6037517928023], [-3413.207701726763, -1423.120154778142], [-3502.9842636970398, -1587.254589405241], [-2761.1463568900153, -1609.6365577634817], [-1802.2326144830336, -1712.013338957657], [-396.52065731685684, -1924.6420383609443], [708.3147415433612, -2279.0232040330898], [1749.3094157052883, -2633.4043697052352], [1936.1649394233286, -2775.1568359740936], [2509.0811572599637, -2916.909302242952], [-381.09412722175557, -3395.3238759003484], [-3767.4030436444787, -3984.715709334022], [-5854.314352602669, -4551.725574409455], [-6770.642795269217, -4878.543760529322], [-7857.411703330463, -5051.111980334888], [-9904.94732721397, -5051.111980334888]]
angle = [51999756, 44500003, 39500001, 34499994, 29499998, 24500003, 19500005, 14499997, 9499997, 4500009, -500004, -5499999, -10499985, -15499996, -20499998, -25500001, -30500003, -35500004, -40499996, -45500001, -50500000, -55500004]



correct_eucentric(displacement, angle)



