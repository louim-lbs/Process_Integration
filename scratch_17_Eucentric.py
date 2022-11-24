import com_functions
import time

positioner = com_functions.SMARACT_MCS_3D()
positioner.import_package_and_connexion()

def absolute_move_with_autocorrect(y, z, a):
    """
    Move to a position with autocorrect
    """
    positioner.absolute_move(y=y, z=z, a=a)
    _, _, _, alpha2, _ = positioner.current_position()
    
    increment = 100e-6
    i = 0
    while (alpha2 < a-0.1 or alpha2 > a+0.1) and abs(i*increment) < 0.003:
        print("Autocorrecting")
        positioner.absolute_move(y=y, z=z - i*increment, a=alpha2)
        positioner.absolute_move(y=y, z=z - i*increment, a=a)
        _, _, _, alpha2, _ = positioner.current_position()
        i += 1
    if i != 0:
        positioner.absolute_move(y=y, z=z, a=a)
    return
        

angle1 = 60
angle2 = -angle1
_, ygrec, zed, alpha, _ = positioner.current_position()
for i in range(3):
    # absolute_move_with_autocorrect(y=ygrec, z=zed, a=i)
    # time.sleep(1)
    print(i)
    absolute_move_with_autocorrect(y=ygrec, z=zed, a=angle1)
    time.sleep(1)
    absolute_move_with_autocorrect(y=ygrec, z=zed, a=angle2)
    time.sleep(1)
absolute_move_with_autocorrect(y=ygrec, z=zed, a=0)


# _, ygrec, zed, alpha, _ = positioner.current_position()


# angle1 = 50
# angle2 = -angle1

# t0 = time.time()
# positioner.absolute_move(y=ygrec, z=zed, a=angle1)
# t1 = time.time()


# time.sleep(2)

# t2 = time.time()
# positioner.absolute_move(y=ygrec, z=zed, a=angle2)
# t3 = time.time()
# print('To ' + str(angle1) + ':', t1 - t0)
# print(str(angle1) + ' to ' + str(angle1) +' :', t3 - t2)
# print('Difference:', (100*(t1 - t0 - (t3 - t2))/(t1 - t0)))


# time.sleep(2)

# t2 = time.time()
# positioner.absolute_move(y=ygrec, z=zed, a=0)