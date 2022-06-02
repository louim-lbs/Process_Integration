## Remove before using?
from microscopes import DigitalMicrograph as DM


class microscope(object):
    def __init__(self) -> None:
        # Test the microscope
        try:
            import DigitalMicrograph as DM
            microscope.f = FEI_TITAN_ESEM()
        except:
            microscope.f = FEI_QUATTRO_ESEM()


class FEI_TITAN_ESEM(microscope):
    def __init__(self) -> None:
        pass
           
    # Packages & Connexion
    def import_package_and_connexion(self):
        # Already imported by the test
        # import DigitalMicroscope as DM
        # Connexion handled by GMS3
        pass
    
    # Stage Position & Move
    def current_position(self):
        x, y, z, a, b = DM.Py_Microscope().GetStagePositions(1)
        return x, y, z, a, b
    
    def relative_move(self, dx, dy, dz, da, db):
        x, y, z, a, b = DM.Py_Microscope().GetStagePositions(1)
        DM.Py_Microscope().SetStagePositions(31, x+dx, y+dy, z+dz, a+da, b+db)
    
    def absolute_move(self, x, y, z, a, b):
        DM.Py_Microscope().SetStagePositions(31, x, y, z, a, b)
    
    # Beam control
    def horizontal_field_view(self):
        print('HFW is not implemented')
    
    def magnification(self, value:int):
        if not value:
            return DM.Py_Microscope().GetMagnification()
        return DM.Py_Microscope().SetMagIndex(value)
    
    def working_distance(self, value:float, mode:str):
        if not value:
            return DM.Py_Microscope().GetFocus()
        if mode == 'rel':
            return DM.Py_Microscope().ChangeFocus(value)
        return DM.Py_Microscope().SetFocus(value)
    
    def tilt_correction(self):
        print('Tilt or angular correction is not implemented')
    
    def beam_shift(self, value_x:float, value_y:float, mode:str):
        if not value_x and not value_y:
            return DM.Py_Microscope().GetBeamShift()
        if mode == 'rel':
            return DM.Py_Microscope().ChangeBeamShift(value_x, value_y)
        return DM.Py_Microscope().SetBeamShift(value_x, value_y)
    
    # Imaging
    def image_settings(self, mode:str):
        # if mode == 'get_dwell_time':
        #     return DM.Py_Camera.GetDefaultParameters()[0]
        pass

    def get_image(self):
        return DM.Py_ImageDisplay.GetImage().GetNumArray()
    
    def acquire_frame(self):
        return DM.Py_ImageDisplay.AcquireImage().GetNumArray()
    
    def acquire_multiple_frames(self):
        print('Multiple frames acquisition is not yet implemented')
    
    def beam_blanking(self, ONOFF:bool):
        return DM.Py_Microscope().SetBeamBlanked(ONOFF)

class FEI_QUATTRO_ESEM(microscope):
    def __init__(self) -> None:
        pass
           
    # Packages & Connexion
    def import_package_and_connexion(self):
        from autoscript_sdb_microscope_client import SdbMicroscopeClient
        self.quattro = SdbMicroscopeClient()
    
    # Stage Position & Move
    def current_position(self):
        x, y, z, r, t, _ = self.specimen.stage.current_position()
        return  x, y, z, t, _
    
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
    
    def tilt_correction(self):
        pass
    
    def beam_shift(self):
        pass
    
    # Imaging
    def image_settings(self):
        pass
    
    def get_image(self):
        pass
    
    def acquire_frame(self):
        pass
    
    def acquire_multiple_frames(self):
        pass
    
    def beam_blanking(self):
        pass 
    
    
if __name__ == "__main__":
    
    active_microscope = microscope().f
    a = active_microscope.import_package_and_connexion()
    print(a)