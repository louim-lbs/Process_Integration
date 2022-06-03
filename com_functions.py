## Remove before using?
from microscopes import DigitalMicrograph as DM


class microscope(object):
    def __init__(self) -> None:
        # Test the microscope
        try:
            import DigitalMicrograph as DM
            microscope.f = FEI_TITAN_ETEM()
        except:
            microscope.f = FEI_QUATTRO_ESEM()


class FEI_TITAN_ETEM(microscope):
    def __init__(self) -> None:
        self.microscope_type = 'ETEM'
           
    # Packages & Connexion
    def import_package_and_connexion(self):
        # Already imported by the test
        # import DigitalMicroscope as DM
        # Connexion handled by GMS3
        self.camera = DM.GetActiveCamera()
        pass
    
    # Stage Position & Move
    def current_position(self):
        x, y, z, a, b = DM.Py_Microscope().GetStagePositions(31)
        return x*1e-6, y*1e-6, z*1e-6, a, b
    
    def relative_move(self, dx, dy, dz, da, db):
        x, y, z, a, b = DM.Py_Microscope().GetStagePositions(31)
        DM.Py_Microscope().SetStagePositions(31, x+dx*1e6, y+dy*1e6, z+dz*1e6, a+da, b+db)
    
    def absolute_move(self, x, y, z, a, b):
        DM.Py_Microscope().SetStagePositions(31, x*1e6, y*1e6, z*1e6, a, b)
    
    # Beam control
    def horizontal_field_view(self):
        '''
        Read-only
        '''
        return DM.Py_Microscope().GetCalibratedFieldOfView(self.camera.GetDeviceLocation(), DM.Py_Microscope().GetCalibrationStateTags(), 2)

        
    def magnification(self, value:int):
        if not value:
            return DM.Py_Microscope().GetMagnification()
        return DM.Py_Microscope().SetMagIndex(value)
    
    def working_distance(self, value:float, mode:str):
        if not value:
            return DM.Py_Microscope().GetFocus()
        if mode == 'rel':
            return DM.Py_Microscope().ChangeFocus(value*1e6)
        return DM.Py_Microscope().SetFocus(value*1e6)
    
    def tilt_correction(self, *args):
        print('Tilt or angular correction for ETEM is not implemented')
        return
    
    def beam_shift(self, value_x:float, value_y:float, mode:str):
        if not value_x and not value_y:
            return DM.Py_Microscope().GetBeamShift()
        if mode == 'rel':
            return DM.Py_Microscope().ChangeBeamShift(value_x*1e6, value_y*1e6)
        return DM.Py_Microscope().SetBeamShift(value_x*1e6, value_y*1e6)
    
    # Imaging
    def image_settings(self):
        exposure, xBin, yBin, _, top, left, bottom, right = self.camera.GetDefaultParameters()
        x_resol = int((right - left)/xBin)
        y_resol = int((bottom - top)/yBin)
        resolution = str(y_resol) + 'x' + str(x_resol)
        dwell_time = exposure/(x_resol*y_resol)
        return resolution, dwell_time

    def get_image(self):
        return self.camera.GetImage()
    
    def acquire_frame(self, resolution, dwell_time, bit_depth):
        # DS_CreateParameters() ?
        return self.camera.AcquireImage()
    
    def acquire_multiple_frames(self, resolution, dwell_time, bit_depth):
        print('Multiple frames acquisition is not yet implemented')
    
    def image_array(self, image):
        return image.GetNumArray()
    
    def save(self, image, path):
        image.SaveAsGatan(path + '.dm4')
    
    def beam_blanking(self, ONOFF:bool):
        return DM.Py_Microscope().SetBeamBlanked(ONOFF)

class FEI_QUATTRO_ESEM(microscope):
    def __init__(self) -> None:
        self.microscope_type = 'ESEM'
           
    # Packages & Connexion
    def import_package_and_connexion(self):
        from autoscript_sdb_microscope_client import SdbMicroscopeClient
        self.quattro = SdbMicroscopeClient()
        try:
            quattro.connect() # online connection
            SdbMicroscopeClient.InitState_status = property(lambda self: 0) # Or 1 if not connected
        except:
            try:
                quattro.connect('localhost') # local connection (Support PC) or offline scripting
                SdbMicroscopeClient.InitState_status = property(lambda self: 0) # Or 1 if not connected
            except:
                SdbMicroscopeClient.InitState_status = property(lambda self: 1) # Or 0 if not connected

        quattro.beams.electron_beam.angular_correction.tilt_correction.turn_off()

    # Stage Position & Move
    def current_position(self):
        x, y, z, a, b = self.specimen.stage.current_position()
        return  x, y, z, a, b
    
    def relative_move(self, dx, dy, dz, da, db):
        self.specimen.stage.relative_move(StagePosition(x=0,y=0))
        pass
    
    def absolute_move(self):
        pass
    
    # Beam control
    def horizontal_field_view(self):
        pass
    
    def magnification(self):
        pass
    
    def working_distance(self):
        pass
    
    def tilt_correction(self, ONOFF:bool, value:float, mode:str):
        pass
    
    def beam_shift(self):
        pass
    
    # Imaging
    def image_settings(self):
        resolution = 0
        dwell_time = 0
        return resolution, dwell_time
    
    def get_image(self):
        pass
    
    def acquire_frame(self):
        GrabFrameSettings(resolution=resolution, dwell_time=10e-6, bit_depth=16)
        pass
    
    def acquire_multiple_frames(self):
        GrabFrameSettings(resolution=resolution, dwell_time=10e-6, bit_depth=16)
        pass
    
    def image_array(self, image):
        return image.data
    
    def save(self, image, path):
        image.save(path + '.tif')
    
    def beam_blanking(self):
        pass 
    
    def auto_contras_brightness(self):
        return auto_functions.run_auto_cb()

if __name__ == "__main__":
    
    active_microscope = microscope().f
    a = active_microscope.import_package_and_connexion()
    print(a)