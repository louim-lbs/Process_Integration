def correct_eucentric(microscope, positioner, displacement, angle):
    '''
    '''
    angle = sorted(angle)
    print(displacement)
    print(angle)

    z0_ini, y0_ini, _ = positioner.getpos()

    if displacement == [[0,0]]:

        return z0_ini, y0_ini

    print('z0_ini, y0_ini', z0_ini, y0_ini)

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
    # del displacement_y_interpa_prime[-1] # Edge effect correction

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

    # Adjust positioner position
    print(positioner.setpos_abs([z0, y0, 0]))

    # Adjust microscope stage position
    microscope.specimen.stage.relative_move(StagePosition(y=mean(y0_calc))) ####################Check this, sign?
    # microscope.specimen.stage.relative_move(StagePosition(y=y0*1e-9))

    # Adjust focus because z0 move
    # microscope.auto_functions.run_auto_focus()
    # Or
    microscope.beams.electron_beam.working_distance.value += z0_calc


    # Check limits
    return z0, y0