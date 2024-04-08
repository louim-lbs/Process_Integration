import sys
import smaract.ctl as ctl
import ctypes
from typing import List
vector = List[int]

class smaract_class(object):
    def __init__(self) -> None:
        try:
            print('Initialization...')
            locator = "usb:ix:0"
            self.d_handle = None
            self.d_handle = ctl.Open(locator)
            print("MCS2 opened {}.".format(locator))
            
            self.range_limits = {'z_min': -19000000,
                                'z_max': 19000000,
                                'y_min': -19000000,
                                'y_max': 19000000,
                                't_min': -900000000,
                                't_max': 900000000,
                                'dx_min': -19000000,
                                'dx_max': 19000000,
                                'dy_min': -19000000,
                                'dy_max': 19000000,}
            self.InitState_status = 0
        except Exception as ex:
            self.InitState_status = 1
            print("Unexpected error: {}, {} in line: {}".format(ex, type(ex), (sys.exc_info()[-1].tb_lineno)))
            raise
        return None

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
    
    def check_limits_detector(self, pos:vector) -> bool:
        if (self.range_limits['dx_min'] <= pos[0] <= self.range_limits['dx_max']) and (self.range_limits['dy_min'] <= pos[1] <= self.range_limits['dy_max']):
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
        while (True):
            mask = ctl.ChannelState.ACTIVELY_MOVING
            state1 = ctl.GetProperty_i32(self.d_handle, 0, ctl.Property.CHANNEL_STATE)
            state2 = ctl.GetProperty_i32(self.d_handle, 1, ctl.Property.CHANNEL_STATE)
            state3 = ctl.GetProperty_i32(self.d_handle, 2, ctl.Property.CHANNEL_STATE)
            if (state1 & mask) == 0 and (state2 & mask) == 0 and (state3 & mask) == 0:
                break
        return 0

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
            z_pos = ctl.GetProperty_i64(self.d_handle, 1, ctl.Property.POSITION)*1e-3
            y_pos = ctl.GetProperty_i64(self.d_handle, 2, ctl.Property.POSITION)*1e-3
            t_angle = ctl.GetProperty_i64(self.d_handle, 0, ctl.Property.POSITION)*1e-3
        except:
            print('Error when acquiring positions')
            return [None, None, None]
        return [z_pos, y_pos, t_angle]
    
    def detector_getpos(self) -> vector:
        try:
            dx_pos = ctl.GetProperty_i64(self.d_handle, 3, ctl.Property.POSITION)*1e-3
            dy_pos = ctl.GetProperty_i64(self.d_handle, 4, ctl.Property.POSITION)*1e-3
        except:
            print('Error when acquiring positions')
            return [None, None]
        return [dx_pos, dy_pos]
    
    def setpos_abs(self, pos:vector, hold=True) -> int:
        ''' Move the nanocontrollers from Smaract device (Z, Y and T channels) to desired absolute [z, y, t] position.

        Input:
            - pos: list of desired position [z, y, t] in nanometers or microdegrees (list[int, int, int]).

        Return:
            - success code 0 (SA_OK) or error codes (int).

        Exemple:
            move_status = smaract.setpos([1242.14, 3456.32, 23.44])
                -> Move to absolute position
        '''
        try:
            # if None in self.getpos():
            #     return 1
            if not self.check_limits(pos):
                print('Position out of range')
                return 1
        except:
            print('Error when checking limits')
            return 1        
        
        try:
            # ctl.SetProperty_i64(self.d_handle, 1, ctl.Property.POSITION, int(pos[0]*1e3))
            # ctl.SetProperty_i64(self.d_handle, 2, ctl.Property.POSITION, int(pos[1]*1e3))
            # ctl.SetProperty_i64(self.d_handle, 0, ctl.Property.POSITION, int(pos[2]*1e3))
            ctl.Move(self.d_handle, 1, int(pos[0]*1e3), 0)
            ctl.Move(self.d_handle, 2, int(pos[1]*1e3), 0)
            ctl.Move(self.d_handle, 0, int(pos[2]*1e3), 0)
        except:
            print('Error when setting absolute position.')
            return 1
        
        # z_status_status, y_status_status, t_status_status = self.hold_during_move()

        # if self.check_status([z_status_status, y_status_status, t_status_status]) == 1:
        #     return 1

        if hold == True:
            self.hold_during_move()
            print('Position set at: ' + str([pos[0], pos[1], pos[2]]))
        else:
            print('Position set at: ' + str([pos[0], pos[1], pos[2]]))
        return 0
    
    def detector_setpos_abs(self, pos:vector, hold=True) -> int:
        try:
            if not self.check_limits_detector(pos):
                print('Position out of range')
                return 1
        except:
            print('Error when checking limits')
            return 1        
        
        try:
            ctl.Move(self.d_handle, 3, int(pos[0]*1e3), 0)
            ctl.Move(self.d_handle, 4, int(pos[1]*1e3), 0)
        except:
            print('Error when setting absolute position.')
            return 1
        
        # z_status_status, y_status_status, t_status_status = self.hold_during_move()

        # if self.check_status([z_status_status, y_status_status, t_status_status]) == 1:
        #     return 1

        if hold == True:
            self.hold_during_move()
            print('Position set at: ' + str([pos[0], pos[1]]))
        else:
            print('Position set at: ' + str([pos[0], pos[1]]))
        return 0
    
    def setpos_rel(self, step:vector, hold=True) -> int:
        ''' Move the nanocontrollers from Smaract device (Z, Y and T channels) to desired relative [z, y, t] position.

        Input:
            - step: list of steps [z_step, y_step, t_step] in nanometers or microdegrees (list[int, int, int]).

        Return:
            - success code 0 (//SA_OK) or error codes (int).

        Exemple:
            move_status = smaract.setpos([-100, 0, 0.1])
                -> Move to previous + relative position
        '''
        pos1 = self.getpos()
        pos2 = [pos1[0] + step[0], pos1[1] + step[1], pos1[2] + step[2]]
        
        try:
            if not self.check_limits(pos2):
                print(pos2)
                print('Position out of range')
                return 1
        except:
            print('Error when checking limits')
            return 1
    
        try:
            ctl.Move(self.d_handle, 1, int(pos2[0]*1e3), 0)
            ctl.Move(self.d_handle, 2, int(pos2[1]*1e3), 0)
            ctl.Move(self.d_handle, 0, int(pos2[2]*1e3), 0)
        except:
            print('Error when setting relative position.')
            return 1

        if hold == True:
            self.hold_during_move()
            print('Position increased of: ' + str([step[0], step[1], step[2]]))
        else:
            print('Position increasing of: ' + str([step[0], step[1], step[2]]))
        return 0
    
    def detector_setpos_rel(self, step:vector, hold=True) -> int:
        pos1 = self.detector_getpos()
        pos2 = [pos1[0] + step[0], pos1[1] + step[1]]
        
        try:
            if not self.check_limits_detector(pos2):
                print(pos2)
                print('Position out of range')
                return 1
        except:
            print('Error when checking limits')
            return 1
    
        try:
            ctl.Move(self.d_handle, 3, int(pos2[0]*1e3), 0)
            ctl.Move(self.d_handle, 4, int(pos2[1]*1e3), 0)
        except:
            print('Error when setting relative position.')
            return 1

        if hold == True:
            self.hold_during_move()
            print('Position increased of: ' + str([step[0], step[1]]))
        else:
            print('Position increasing of: ' + str([step[0], step[1]]))
        return 0
    
    def set_zero_position(self, channel):
        ctl.SetProperty_i64(self.d_handle, channel, ctl.Property.POSITION, 0)
    
if __name__ == "__main__":
    # logging.basicConfig(filename='last_execution.log', filemode='w', format='%(levelname)s:%(message)s', level=print)
    device = smaract_class()
    print(device.detector_getpos())
    # device.setpos_rel([0, 0, -10000000])
    
