from msl.loadlib import Server32, Client64
import ctypes

class smaract_lib_server32(Server32):
    def __init__(self, host, port) -> None:
        super(smaract_lib_server32, self).__init__('smaract\\lib\\MCSControl.dll', 'cdll', host, port)
        
    def SA_ClearInitSystemsList(self):
        return self.lib.SA_ClearInitSystemsList()

    def SA_GetAvailableSystems(self):
        AvailableSys_array = (ctypes.c_uint32*1)()
        AvailableSys_array_size = ctypes.c_uint32(1)
        AvailableSys_status = self.lib.SA_GetAvailableSystems(ctypes.byref(AvailableSys_array), ctypes.byref(AvailableSys_array_size))
        AvailableSys_list = list(AvailableSys_array)
        return int(AvailableSys_status), AvailableSys_list

    def SA_AddSystemToInitSystemsList(self, system):
        return self.lib.SA_AddSystemToInitSystemsList(ctypes.c_uint32(system))

    def SA_InitSystems(self):
        return self.lib.SA_InitSystems(ctypes.c_ulong(0))

    def SA_GetDLLVersion(self):
        version = ctypes.c_uint32()
        version_status = self.lib.SA_GetDLLVersion(ctypes.byref(version))
        return int(version_status), int(version.value)

    def SA_GetInitState(self):
        InitState = ctypes.c_uint32()
        InitState_status = self.lib.SA_GetInitState(ctypes.byref(InitState))
        return int(InitState_status), int(InitState.value)
        
    def SA_GetStatus_S(self, channel):
        channel = ctypes.c_uint32(channel)
        status = ctypes.c_uint32()
        status_status = self.lib.SA_GetStatus_S(ctypes.c_uint32(0), channel, ctypes.byref(status))
        return int(status_status), int(status.value)
        
    def SA_GetPosition_S(self, channel):
        channel      = ctypes.c_uint32(channel)
        pos          = ctypes.c_int32()
        pos_status   = self.lib.SA_GetPosition_S(ctypes.c_uint32(0), channel, ctypes.byref(pos))
        return int(pos_status), int(pos.value)
        
    def SA_GetAngle_S(self):
        angle = ctypes.c_uint32()
        revol = ctypes.c_int32()
        ang_status   = self.lib.SA_GetPosition_S(ctypes.c_uint32(0), ctypes.c_uint32(2), ctypes.byref(angle), ctypes.byref(revol))
        return int(ang_status), int(angle.value), int(revol.value)

    def SA_GotoPositionAbsolute_S(self, channel, pos):
        channel = ctypes.c_uint32(channel)
        pos = ctypes.c_uint32(pos)
        return self.lib.SA_GotoPositionAbsolute_S(ctypes.c_uint32(0),channel,pos,ctypes.c_uint32(60000))

    def SA_GotoAngleAbsolute_S(self, ang, revol):
        ang = ctypes.c_uint32(ang)
        revol = ctypes.c_uint32(revol)
        return self.lib.SA_GotoAngleAbsolute_S(ctypes.c_uint32(0), ctypes.c_uint32(2), ang, revol, ctypes.c_uint32(60000))
        
    def SA_GotoPositionRelative_S(self, channel, pos):
        channel = ctypes.c_uint32(channel)
        pos = ctypes.c_uint32(pos)
        return self.lib.SA_GotoPositionAbsolute_S(ctypes.c_uint32(0),channel,pos,ctypes.c_uint32(60000))

    def SA_GotoAngleRelative_S(self, ang, revol):
        ang = ctypes.c_uint32(ang)
        revol = ctypes.c_uint32(revol)
        return self.lib.SA_GotoAngleAbsolute_S(ctypes.c_uint32(0), ctypes.c_uint32(2), ang, revol, ctypes.c_uint32(60000))

class smaract_lib_client64(Client64):
    def __init__(self) -> None:
        super(smaract_lib_client64, self).__init__(module32='smaract/smaract_lib.py', append_environ_path='smaract\lib')
    
    def __getattr__(self, name):
        def send(*args, **kwargs):
            return self.request32(name, *args, **kwargs)
        return send

if __name__ == "__main__":
    smaract = smaract_lib_client64()
    print(smaract.SA_ClearInitSystemsList())