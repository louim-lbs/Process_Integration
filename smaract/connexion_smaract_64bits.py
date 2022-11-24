import ctypes
import logging
from typing import List
from smaract.smaract_lib import smaract_lib_client64

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
        print(' Initialization...')
        try:
            self.smaract = smaract_lib_client64()
        except:
            print(' Error while importing Smaract dll. Please check the path.')

        self.smaract.SA_ClearInitSystemsList()
        
        AvailableSys_state, AvailableSys_list = self.smaract.SA_GetAvailableSystems()
        print(' Available Systems IDs: ' + str(AvailableSys_list))
        
        if len(AvailableSys_list) >= 1 and AvailableSys_list[0] != 0:
            self.smaract.SA_AddSystemToInitSystemsList(AvailableSys_list[0]) #3919851221
            InitSystems_status = self.smaract.SA_InitSystems()
            if InitSystems_status == 0:
                # Dll version
                version_status, version = self.smaract.SA_GetDLLVersion()

                # Init state
                self.InitState_status, InitState = self.smaract.SA_GetInitState()

                print(' Initialization... OK')
                print(' System ID:       ' + str(AvailableSys_list[0]))
                print(' Dll version:     ' + str(version))
                print(' Init state:      ' + str(InitState) + ' ' + str(self.find_status_message(self.state_codes, InitState)))
                print(' ---------------------------------------')
            else:
                self.check_status([InitSystems_status])
                self.InitState_status = 1
        else:
            self.check_status([AvailableSys_state], ' No systems detected: ')
            print(' Check if MCS-3D is turned on. Check USB connexion.')
            self.InitState_status = 1

        self.range_limits = {'z_min': -1900000,
                            'z_max':   1900000,
                            'y_min':  -1900000,
                            'y_max':   1900000,
                            't_min': -90000000,
                            't_max':  90000000,
                            'revol_min':    -1,
                            'revol_max':     0}
        
        # z_set_limit_status = self.smaract.SA_SetPositionLimit_S(ctypes.c_uint32(0),ctypes.c_uint32(0),self.range_limits['z_min'],self.range_limits['z_max'])
        # y_set_limit_status = self.smaract.SA_SetPositionLimit_S(ctypes.c_uint32(0),ctypes.c_uint32(0),self.range_limits['y_min'],self.range_limits['y_max'])
        # t_set_limit_status = self.smaract.SA_SetPositionLimit_S(ctypes.c_uint32(0),ctypes.c_uint32(0),self.range_limits['t_min'],self.range_limits['revol_min'],self.range_limits['t_max'],self.range_limits['revol_max'])

        # if self.check_status([z_set_limit_status, y_set_limit_status, t_set_limit_status], error_text='Impossible to set limits. ') == 1:
        #     pass

        # if calibrate:
        #     z_calibrate_status = self.smaract.SA_FindReferenceMark_S(ctypes.c_uint32(0),ctypes.c_uint32(0),ctypes.c_uint32(3),ctypes.c_uint32(60000),ctypes.c_uint32(1))
        #     y_calibrate_status = self.smaract.SA_FindReferenceMark_S(ctypes.c_uint32(0),ctypes.c_uint32(1),ctypes.c_uint32(3),ctypes.c_uint32(60000),ctypes.c_uint32(1))
        #     t_calibrate_status = 0
        #     # t_calibrate_status = self.smaract.SA_FindReferenceMark_S(ctypes.c_uint32(0),ctypes.c_uint32(2),ctypes.c_uint32(3),ctypes.c_uint32(60000),ctypes.c_uint32(1))
        #     self.check_status([z_calibrate_status, y_calibrate_status, t_calibrate_status], error_text='Impossible to find reference mark. ')
        #     pass
        
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
    
    def check_status(self, list_error:vector, error_text:str = 'Error. ') -> int:
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
        list_error = list(dict.fromkeys(list_error))
        error = 0
        for status in list_error:
            if status != 0:
                message = self.find_status_message(self.error_codes, status)
                print(error_text + str(status) + ' ' + str(message))
                return 1
        return error

    def angle_convert_SI2Smaract(self, angle_py:int) -> int:
        ''' Convert SI angles to Smaract angle plus revolution type.

        Input:
            - angle in microdegrees (int).
        
        Return:
            - positive angle in microdegrees converted for absolute move (int).
            - revolution 0 or -1 according positive or negative rotation (int).

        Exemple:
            angle, revolution = angle_convertSI2Smaract(90000000)
                -> 90000000, 0
            angle, revolution = angle_convertSI2Smaract(-90000000)
                -> 270000000, -1
        '''
        revolution = 0
        if angle_py < 0:
            revolution = -1
            angle_py = 360000000 + angle_py
        return angle_py, revolution

    def angle_convert_Smaract2SI(self, angle_smaract:int) -> int:
        ''' Convert Smaract angle plus revolution type to SI angles.

        Input:
            - positive angle in microdegrees converted for absolute move (int).
        
        Return:
            - angle in microdegrees (int).

        Exemple:
            angle = angle_convert_Smaract2SI(90000000)
                -> 90000000, 0
            angle = angle_convert_Smaract2SI(270000000)
                -> -90000000
        '''
        try:
            if 0 <= angle_smaract <= 180000000:
                return angle_smaract
            elif 180000000 < angle_smaract <= 360000000:
                return angle_smaract-360000000
        except:
            return None
    
    def gets_limits_deprecated(self):
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
            print('Error when checking range limits of positioners')
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
        if (self.range_limits['z_min'] <= pos[0] <= self.range_limits['z_max']) and (self.range_limits['y_min'] <= pos[1] <= self.range_limits['y_max']) and (self.range_limits['t_min'] <= pos[2] <= self.range_limits['t_max']):
            return True
        else:
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
        z_status_status, z_status = self.smaract.SA_GetStatus_S(0)
        y_status_status, y_status = self.smaract.SA_GetStatus_S(1)
        t_status_status, t_status = self.smaract.SA_GetStatus_S(2)
        while z_status == 4 or y_status == 4 or t_status == 4:
            z_status_status, z_status = self.smaract.SA_GetStatus_S(0)
            y_status_status, y_status = self.smaract.SA_GetStatus_S(1)
            t_status_status, t_status = self.smaract.SA_GetStatus_S(2)
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
        try:
            z_pos_status, z_pos              = self.smaract.SA_GetPosition_S(0)
            y_pos_status, y_pos              = self.smaract.SA_GetPosition_S(1)
            t_angle_status, t_angle, t_revol = self.smaract.SA_GetAngle_S()
            t_angle = self.angle_convert_Smaract2SI(t_angle)
        except:
            print('Error when acquiring postitions')
            return [None, None, None]

        if self.check_status([z_pos_status, y_pos_status, t_angle_status]) == 1:
            return [None, None, None]

        # print('Current position: ' + str([z_pos, y_pos, t_angle]))

        return [z_pos, y_pos, t_angle]
    
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
            if None in self.getpos():
                return 1
            if not self.check_limits(pos):
                print('Position out of range')
                return 1
        except:
            print('Error when checking limits')
            return 1
        pos[2], revolution = self.angle_convert_SI2Smaract(pos[2])
        
        pos = [int(pos[0]), int(pos[1]), int(pos[2])]
        
        try:
            z_setpos_status = self.smaract.SA_GotoPositionAbsolute_S(0, pos[0])
            y_setpos_status = self.smaract.SA_GotoPositionAbsolute_S(1, pos[1])
            t_setpos_status = self.smaract.SA_GotoAngleAbsolute_S(      pos[2], revolution)
        except:
            print('Error when setting absolute position.')
            return 1
        
        if self.check_status([z_setpos_status, y_setpos_status, t_setpos_status]) == 1:
            return 1

        z_status_status, y_status_status, t_status_status = self.hold_during_move()

        if self.check_status([z_status_status, y_status_status, t_status_status]) == 1:
            return 1

        print('Position set to:  ' + str(pos))

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
            if None in self.getpos():
                return 1
            if not self.check_limits(step):
                print(step)
                print('Position out of range')
                return 1
            # print('Moving to position: ' + str(step))
        except:
            print('Error when checking limits')
            return 1
    
        step[2], revolution = self.angle_convert_SI2Smaract(step[2])

        step = [int(step[0]), int(step[1]), int(step[2])]
        try:
            z_setpos_status = self.smaract.SA_GotoPositionRelative_S(0, step[0])
            y_setpos_status = self.smaract.SA_GotoPositionRelative_S(1, step[1])
            t_setpos_status = self.smaract.SA_GotoAngleRelative_S(      step[2], revolution)
        except:
            print('Error when setting relative position.')
            return 1
        if self.check_status([z_setpos_status, y_setpos_status, t_setpos_status]) == 1:
            return 1

        z_status_status, y_status_status, t_status_status = self.hold_during_move()
        if self.check_status([z_status_status, y_status_status, t_status_status]) == 1:
            return 1

        print('Position increased of: ' + str([step[0], step[1], self.angle_convert_Smaract2SI(step[2])]))
        return 0
    
    def set_zero_position(self, channel):
        self.smaract.SA_SetZeroPosition_S(channel)
    
if __name__ == "__main__":

    logging.basicConfig(filename='last_execution.log', filemode='w', format='%(levelname)s:%(message)s', level=print)

    smaract = smaract_class(calibrate=False)
    print(smaract.getpos())