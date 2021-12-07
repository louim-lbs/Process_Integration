''' Script to control Smaract MCS-3D - Connexion and methods

Use Python 32-bits

@author: Louis-Marie Lebas
Created on Fri Nov 05 2021
'''

###### Imports
try:
    import ctypes
except:
    logging.info(' Error while importing python module ctypes. Check your installation.')

import os
import time
import matplotlib.pyplot as plt
import logging
from typing import List

vector = List[int]

class smaract_class(object):
    def __init__(self, calibrate:bool) -> None:
        ''' Buid smaract_class.

        Class atributes:
            - status codes : dictionnary with status codes and meaning from MCSControl.h (dict{int:str}).
            - error codes  : dictionnary with errors codes and meaning from MCSControl.h, build from status codes (dict{int:str}).
            - state codes  : dictionnary with state codes and meaning from MCSControl.h, build from status codes (dict{int:str}).
            - smart        : library giving access to C++ methods from MCSControl.dll (class).
            - range limits : dictionnary with set deplacement range limits in nanometers or microdegrees.

        Return:
            - None (bool).

        Exemple:
            smaract = smaract_class()
        '''
        ##### Get status return values from MCSControl.h # adapted from nplab
        with open('smaract\\lib\\MCSControl.h', 'r') as f:
            lines = [line.strip().split(' ') for line in f.readlines() if line.startswith('#define')]
            self.status_codes = {}
            for line in lines:
                while '' in line: line.remove('')
                if len(line) == 3:
                    try:
                        self.status_codes[line[1]] = int(line[2])
                    except ValueError:
                        pass

        self.error_codes = {k:self.status_codes[k] for k in list(self.status_codes)[:38]}
        self.state_codes = {k:self.status_codes[k] for k in list(self.status_codes)[41:44]}

        ###### Initialisation
        logging.info(' Initialization...')
        # import dll with cdll et non windll sinon error 4 bytes in excess (cf :https://ammous88.wordpress.com/2014/12/31/ctypes-cdll-vs-windll/)
        dll_file = 'MCSControl'

        try:
            os.chdir('smaract\\lib\\')
            self.smart = ctypes.cdll.LoadLibrary(dll_file)
            os.chdir(os.path.dirname(os.getcwd())) # Change path to the parent directory of the actual path (ie dll path).
        except:
            logging.info(' Error while importing Smaract dll. Please check the path.')

        self.smart.SA_ClearInitSystemsList()

        AvailableSys_array = (ctypes.c_uint32*1)()
        AvailableSys_array_size = ctypes.c_uint32(1)
        AvailableSys_state = self.smart.SA_GetAvailableSystems(ctypes.byref(AvailableSys_array), ctypes.byref(AvailableSys_array_size))
        AvailableSys_list = list(AvailableSys_array)
        logging.info(' Available Systems IDs: ' + str(AvailableSys_list))

        if len(AvailableSys_list) >= 1 and AvailableSys_list[0] != 0:
            self.smart.SA_AddSystemToInitSystemsList(AvailableSys_list[0]) #3919851221
            InitSystems_status = self.smart.SA_InitSystems(ctypes.c_ulong(0))
            if InitSystems_status == 0:
                # Dll version
                version = ctypes.c_uint32()
                version_status = self.smart.SA_GetDLLVersion(ctypes.byref(version))

                # Init state
                InitState = ctypes.c_uint32()
                self.InitState_status = self.smart.SA_GetInitState(ctypes.byref(InitState))

                logging.info(' Initialization... OK')
                logging.info(' System ID:       ' + str(list(AvailableSys_array)[0]))
                logging.info(' Dll version:     ' + str(version.value))
                logging.info(' Init state:      ' + str(InitState.value) + ' ' + str(self.find_status_message(self.state_codes, InitState.value)))
                logging.info(' ---------------------------------------')
            else:
                self.check_status([InitSystems_status])
                self.InitState_status = 1
        else:
            self.check_status([AvailableSys_state], ' No systems detected: ')
            logging.info(' Check if MCS-3D is turned on. Check USB connexion.')
            self.InitState_status = 1

        self.range_limits = {'z_min':ctypes.c_int32(-1900000),
                            'z_max':  ctypes.c_int32(1900000),
                            'y_min': ctypes.c_int32(-1900000),
                            'y_max':  ctypes.c_int32(1900000),
                            't_min':ctypes.c_int32(-90000000),
                            't_max': ctypes.c_int32(90000000),
                            'revol_min':ctypes.c_int32(-1),
                            'revol_max':ctypes.c_int32(0)}
        
        # z_set_limit_status = self.smart.SA_SetPositionLimit_S(ctypes.c_uint32(0),ctypes.c_uint32(0),self.range_limits['z_min'],self.range_limits['z_max'])
        # y_set_limit_status = self.smart.SA_SetPositionLimit_S(ctypes.c_uint32(0),ctypes.c_uint32(0),self.range_limits['y_min'],self.range_limits['y_max'])
        # t_set_limit_status = self.smart.SA_SetPositionLimit_S(ctypes.c_uint32(0),ctypes.c_uint32(0),self.range_limits['t_min'],self.range_limits['revol_min'],self.range_limits['t_max'],self.range_limits['revol_max'])

        # if self.check_status([z_set_limit_status, y_set_limit_status, t_set_limit_status], error_text='Impossible to set limits. ') == 1:
        #     pass

        if calibrate:
            z_calibrate_status = self.smart.SA_FindReferenceMark_S(ctypes.c_uint32(0),ctypes.c_uint32(0),ctypes.c_uint32(3),ctypes.c_uint32(60000),ctypes.c_uint32(1))
            y_calibrate_status = self.smart.SA_FindReferenceMark_S(ctypes.c_uint32(0),ctypes.c_uint32(1),ctypes.c_uint32(3),ctypes.c_uint32(60000),ctypes.c_uint32(1))
            t_calibrate_status = 0
            # t_calibrate_status = self.smart.SA_FindReferenceMark_S(ctypes.c_uint32(0),ctypes.c_uint32(2),ctypes.c_uint32(3),ctypes.c_uint32(60000),ctypes.c_uint32(1))
            self.check_status([z_calibrate_status, y_calibrate_status, t_calibrate_status], error_text='Impossible to find reference mark. ')
            pass
        
        return None

    def find_status_message(self, dict:dict, code:int) -> str:
        ''' Retrieve status message from error code.

        Input:
            - dictionnary with status code and status messages (dict).
            - status code (int).

        Return:
            - status message (str).

        Exemple:
            find_status_message(self.error_codes, 3)
                -> SA_NO_SYSTEMS_FOUND_ERROR
        '''
        for k, val in dict.items(): 
            if code == val: 
                return k 
        return ''
    
    def check_status(self, list:vector, error_text:str = 'Something went wrong. ') -> int:
        ''' Check if an error occured during smart C++ function execution. If so, the corresponding status message is written in log.

        Input:
            - self (class).
            - list of status codes (list[int]).
            - text to add to log (str).
        
        Return:
            - 0 if evrything OK, 1 else.
        
        Exemple:
            check_status([z_pos_status, y_pos_status, t_angle_status])
                -> 0
        '''
        error = 0
        for status in list:
            if status != 0:
                message = self.find_status_message(self.error_codes, status)
                logging.info(error_text + str(status) + ' ' + str(message))
                error = 1
        return error

    def angle_convert(self, angle_py:int) -> int:
        ''' Convert "normal" angles to Smaract angle plus revolution type.

        Input:
            - angle in microdegrees (int).
        
        Return:
            - positive angle in microdegrees converted for absolute move (int).
            - revolution 0 or -1 according positive or negative rotation (int).

        Exemple:
            angle, revolution = angle_convert(90000000)
                -> 90000000, 0
            ngle, revolution = angle_convert(-90000000)
                -> 270000000, -1
        '''
        revolution = 0
        if angle_py < 0:
            revolution = -1
            angle_py = 360000000 + angle_py
        return angle_py, revolution
    
    def gets_limits(self):
        ''' Retrieve the travel range limits of positioners.
        If no limit is set then all output parameters will be 0.

        Input:
            - None.
        
        Return:
            - List of limits [z_min, z_max, y_min, y_max, t_min, t_max] (list[ints]).

        Exemple:
            [z_min, z_max, y_min, y_max, t_min, t_max] = gets_limits()
        '''
        z_min     = ctypes.c_int32()
        z_max     = ctypes.c_int32()
        y_min     = ctypes.c_int32()
        y_max     = ctypes.c_int32()
        t_min     = ctypes.c_uint32()
        t_max     = ctypes.c_uint32()
        revol_min = ctypes.c_int32()
        revol_max = ctypes.c_int32()
        
        try:
            z_limits_state = smaract.smart.SA_GetPositionLimit_S(ctypes.c_uint32(0), ctypes.c_uint32(0), z_min, z_max)
            y_limits_state = smaract.smart.SA_GetPositionLimit_S(ctypes.c_uint32(0), ctypes.c_uint32(0), y_min, y_max)
            t_limits_state = smaract.smart.SA_GetAngleLimit_S(ctypes.c_uint32(0), ctypes.c_uint32(0), t_min, revol_min, t_max, revol_max)
        except:
            logging.info(' Something went wrong when checking range limits of positioners')
            return [None, None, None, None, None, None]
        
        if self.check_status([z_limits_state, y_limits_state, t_limits_state], error_text='Impossible to check limits. ') == 1:
            return [None, None, None, None, None, None]

        return [z_min, z_max, y_min, y_max, t_min, t_max]

    def check_limits(self, pos:vector) -> bool:
        ''' Check if the positions are between the travel range limits of positioners.

        Input:
            - list of the [z, y, t] positions in nanometers or microdegrees (list[int, int, int]).

        Return:
            - True or False (bool).

        Exemple:
            if check_limits(pos):
                smaract.setpos_abs(pos)
        '''
        # limits = self.gets_limits()
        if (self.range_limits['z_min'].value <= pos[0] <= self.range_limits['z_max'].value) and (self.range_limits['y_min'].value <= pos[1] <= self.range_limits['y_max'].value) and (self.range_limits['t_min'].value <= pos[2] <= self.range_limits['t_max'].value):
            logging.info('    Positions in the list are between the travel range limits of positioners.')
            return True
        else:
            logging.info('    Positions in the list are out the travel range limits of positioners.')
            return False
    
    def hold_during_move(self) -> ctypes.c_uint32:
        ''' Hold instruction flow during movement of positioners.

        Input:
            - self (class).

        Return:
            - status code given by SA_GetStatus_S() for z, y and t (ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32).
        
        Exemple:
            z_status_status, y_status_status, t_status_status = self.hold_during_move()
        '''
        z_status = ctypes.c_uint32()
        y_status = ctypes.c_uint32()
        t_status = ctypes.c_uint32()
        z_status_status = self.smart.SA_GetStatus_S(ctypes.c_uint32(0),ctypes.c_uint32(0), ctypes.byref(z_status))
        y_status_status = self.smart.SA_GetStatus_S(ctypes.c_uint32(0),ctypes.c_uint32(1), ctypes.byref(y_status))
        t_status_status = self.smart.SA_GetStatus_S(ctypes.c_uint32(0),ctypes.c_uint32(2), ctypes.byref(t_status))
        logging.info('    Moving...')
        while z_status.value == 4 or y_status.value == 4 or t_status.value == 4:
            z_status_status = self.smart.SA_GetStatus_S(ctypes.c_uint32(0),ctypes.c_uint32(0), ctypes.byref(z_status))
            y_status_status = self.smart.SA_GetStatus_S(ctypes.c_uint32(0),ctypes.c_uint32(1), ctypes.byref(y_status))
            t_status_status = self.smart.SA_GetStatus_S(ctypes.c_uint32(0),ctypes.c_uint32(2), ctypes.byref(t_status))
        return z_status_status, y_status_status, t_status_status

    def getpos(self) -> vector:
        ''' Retrieve the position of nanocontrollers from Smaract device: Z, Y and T channels.
        
        Input:
            - self (class).

        Return:
            - list of the [z, y, t] positions in nanometers or microdegrees (list[int, int, int]).

        Exemple:
            [z, y, t] = smaract.getpos()
        '''
        z_pos   = ctypes.c_int32()
        y_pos   = ctypes.c_int32()
        t_angle = ctypes.c_uint32()
        t_revol = ctypes.c_int32()
        try:
            z_pos_status   = self.smart.SA_GetPosition_S(ctypes.c_uint32(0), ctypes.c_uint32(0), ctypes.byref(z_pos))
            y_pos_status   = self.smart.SA_GetPosition_S(ctypes.c_uint32(0), ctypes.c_uint32(1), ctypes.byref(y_pos))
            t_angle_status = self.smart.SA_GetAngle_S(ctypes.c_uint32(0), ctypes.c_uint32(2), ctypes.byref(t_angle), ctypes.byref(t_revol))
        except:
            logging.info(' Something went wrong when acquiring postition of positioners')
            return [None, None, None]

        if self.check_status([z_pos_status, y_pos_status, t_angle_status]) == 1:
            return [None, None, None]

        logging.info(' Current position:    ' + str([z_pos.value, y_pos.value, t_angle.value]))

        if t_revol == -1:
            t_angle *= -1
        return [z_pos.value, y_pos.value, t_angle.value]
    
    def setpos_abs(self, pos:vector) -> int:
        ''' Move the nanocontrollers from Smaract device (Z, Y and T channels) to desired absolute [z, y, t] position.

        Input:
            - pos: list of desired position [z, y, t] in nanometers or microdegrees (list[int, int, int]).

        Return:
            - succes code 0 (SA_OK) or error codes (int).

        Exemple:
            move_status = smaract.setpos([1242.14, 3456.32, 23.44])
                -> Move to absolute position
        '''
        try:
            if not self.check_limits(pos):
                return 1
        except:
            return 1
        pos[2], revolution = self.angle_convert(pos[2])
        
        pos = [ctypes.c_uint32(int(pos[0])), ctypes.c_uint32(int(pos[1])), ctypes.c_uint32(int(pos[2]))]
        revolution = ctypes.c_int32(revolution)
        
        try:
            z_setpos_status = self.smart.SA_GotoPositionAbsolute_S(ctypes.c_uint32(0),ctypes.c_uint32(0),pos[0],ctypes.c_uint32(60000))
            y_setpos_status = self.smart.SA_GotoPositionAbsolute_S(ctypes.c_uint32(0),ctypes.c_uint32(1),pos[1],ctypes.c_uint32(60000))
            t_setpos_status = self.smart.SA_GotoAngleAbsolute_S(ctypes.c_uint32(0),ctypes.c_uint32(2),pos[2], revolution,ctypes.c_uint32(60000))
        except:
            logging.info(' Something went wrong when setting absolute position.')
            return 1
        
        if self.check_status([z_setpos_status, y_setpos_status, t_setpos_status]) == 1:
            return 1

        z_status_status, y_status_status, t_status_status = self.hold_during_move()

        if self.check_status([z_status_status, y_status_status, t_status_status]) == 1:
            return 1

        logging.info('    Position set to:  ' + str([pos[0].value, pos[1].value, pos[2].value]))

        return 0
    
    def setpos_rel(self, step:vector) -> int:
        ''' Move the nanocontrollers from Smaract device (Z, Y and T channels) to desired relative [z, y, t] position.

        Input:
            - step: list of steps [z_step, y_step, t_step] in nanometers or microdegrees (list[int, int, int]).

        Return:
            - succes code 0 (//SA_OK) or error codes (int).

        Exemple:
            move_status = smaract.setpos([-100, O, 0.1])
                -> Move to previous + relative position
        '''
        try:
            if not self.check_limits(step):
                return 1
        except:
            return 1
        
        step = [ctypes.c_uint32(int(step[0])), ctypes.c_uint32(int(step[1])), ctypes.c_uint32(int(step[2]))]
        revolution = ctypes.c_int32(0)

        try:
            z_setpos_status = self.smart.SA_GotoPositionRelative_S(ctypes.c_uint32(0),ctypes.c_uint32(0),step[0],ctypes.c_uint32(60000))
            y_setpos_status = self.smart.SA_GotoPositionRelative_S(ctypes.c_uint32(0),ctypes.c_uint32(1),step[1],ctypes.c_uint32(60000))
            t_setpos_status = self.smart.SA_GotoAngleRelative_S(ctypes.c_uint32(0),ctypes.c_uint32(2),step[2], revolution,ctypes.c_uint32(60000))
        except:
            logging.info(' Something went wrong when setting relative position.')
            return 1
        
        if self.check_status([z_setpos_status, y_setpos_status, t_setpos_status]) == 1:
            return 1

        z_status_status, y_status_status, t_status_status = self.hold_during_move()

        if self.check_status([z_status_status, y_status_status, t_status_status]) == 1:
            return 1

        logging.info('    Position set to:  ' + str([step[0].value, step[1].value, step[2].value]))
        
        return 0


if __name__ == "__main__":

    logging.basicConfig(filename='last_execution.log', filemode='w', format='%(levelname)s:%(message)s', level=logging.INFO)

    smaract = smaract_class(calibrate=True)
    # smaract = smaract_class(calibrate=False)


    # print(smaract.getpos())
    # smaract.setpos_abs([0, 0, 15000000])
    # time.sleep(0.5)
    # print(smaract.getpos())
    # time.sleep(1)
    # smaract.setpos_abs([500000, 0, 15000000])
    # time.sleep(0.5)
    # print(smaract.getpos())
    # time.sleep(1)
    # smaract.setpos_abs([0, 0, 0])
    # time.sleep(0.5)
    # print(smaract.getpos())

    # t = [i for i in range(0, 11)]
    # z = [0]*11
    # y = [0]*11
    # ang = [0]*11
    # for i in range(0, 11):
    #     smaract.setpos_abs([0, 0, t[i]*10000000])
    #     time.sleep(1)
    #     z[i], y[i], ang[i] = smaract.getpos()
    #     print(ang)
    # smaract.setpos_abs([0, 0, 0])


    # print(smaract.angle_convert(-90000000))


    # t = [i for i in range(0, 11)]
    # z = [0]*11
    # y = [0]*11
    # ang = [0]*11
    # z[0], y[0], ang[0] = smaract.getpos()
    # print(ang)

    # for i in range(1, 11):
    #     smaract.setpos_rel([0, 0, 10000000])
    #     time.sleep(0.5)
    #     z[i], y[i], ang[i] = smaract.getpos()
    #     print(ang)

    # smaract.setpos_abs([0, 0, 0])


    # plt.plot(t[1:], ang[1:])
    # plt.show()


    # smaract.setpos_abs([0, 0, 0])
    # time.sleep(1)
    # smaract.setpos_abs([0, 0, 10000000])
    # time.sleep(1)
    # smaract.setpos_abs([0, 0, -10000000])
    # time.sleep(1)
    # smaract.setpos_abs([0, 0, 0])

    print(smaract.getpos())
