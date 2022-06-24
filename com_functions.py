import numpy as np
import os
from autoscript_sdb_microscope_client.structures import GrabFrameSettings, Point, StagePosition

## Only for editing in VSCode. Remove before using?
try:
    from microscopes import DigitalMicrograph as DM
except:
    pass

class microscope(object):
    def __init__(self) -> None:
        # Test the microscope
        try:
            import DigitalMicrograph as DM
            microscope.f = FEI_TITAN_ETEM()
            microscope.p = microscope.f
        except:
            microscope.f = FEI_QUATTRO_ESEM()
            microscope.p = SMARACT_MCS_3D()


class FEI_TITAN_ETEM(microscope):
    def __init__(self) -> None:
        self.microscope_type = 'ETEM'
        self.InitState_status = 0
         
    # Packages & Connexion
    def import_package_and_connexion(self):
        # Already imported by the test
        # import DigitalMicroscope as DM
        # Connexion handled by GMS3
        self.camera = DM.GetActiveCamera()
        pass
    
    # Stage Position & Move
    def current_position(self):
        x, y, z, a, b = DM.Py_Microscope().GetStagePositions(15)
        print(x, y, z, a)
        return x*1e-6, y*1e-6, z*1e-6, a, 0
    
    def relative_move(self, dx, dy, dz, da, db):
        x, y, z, a, b = DM.Py_Microscope().GetStagePositions(15)
        DM.Py_Microscope().SetStagePositions(15, x+dx*1e6, y+dy*1e6, z+dz*1e6, a+da, b+db)
        return 0
    
    def absolute_move(self, x, y, z, a, b):
        DM.Py_Microscope().SetStagePositions(15, x*1e6, y*1e6, z*1e6, a, b)
        return 0
    
    # Beam control
    def horizontal_field_view(self):
        '''
        Read-only
        '''
        return DM.Py_Microscope().GetCalibratedFieldOfView(self.camera.GetDeviceLocation(), DM.Py_Microscope().GetCalibrationStateTags(), 2)

        
    def magnification(self, value:int=None):
        if value==None:
            return DM.Py_Microscope().GetMagnification()
        return DM.Py_Microscope().SetMagIndex(value)
    
    def working_distance(self, value:float=None, mode:str=None):
        if value==None:
            return DM.Py_Microscope().GetFocus()
        if mode == 'rel':
            return DM.Py_Microscope().ChangeFocus(value)
        return DM.Py_Microscope().SetFocus(value)
    
    def tilt_correction(self, *args):
        print('Tilt or angular correction for ETEM is not implemented')
        return
    
    def beam_shift(self, value_x:float=None, value_y:float=None, mode:str=None):
        if value_x==None or value_y==None:
            return DM.Py_Microscope().GetBeamShift()
        if mode == 'rel':
            return DM.Py_Microscope().ChangeBeamShift(value_x, value_y)
        return DM.Py_Microscope().SetBeamShift(value_x, value_y)
    
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
    
    def acquire_frame(self, resolution=None, dwell_time=None, bit_depth=None):
        if resolution!=None and dwell_time!=None and bit_depth!=None:
            paramID = DM.DS_CreateParameters(resolution[1], resolution[0], bit_depth, 0, dwell_time, False)
            DM.DS_SetParametersSignal(paramID, signalIndex=0, dataType=bit_depth, selected=True, imageID=0) # 0 = HAADF
            DM.DS_SetParametersSignal(paramID, signalIndex=1, dataType=bit_depth, selected=True, imageID=0) # 1 = BF?
            DM.DS_StartAcquisition(paramID, continuous=False, synchronous=True)
            DM.FindImageByID()
            # ?
        return self.camera.AcquireImage()
    
    def acquire_multiple_frames(self, resolution=None, dwell_time=None, bit_depth=None):
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
            self.quattro.connect() # online connection
            self.InitState_status = 0
        except:
            try:
                self.quattro.connect('localhost') # local connection (Support PC) or offline scripting
                self.InitState_status = 0
            except:
                self.InitState_status = 1

        try:
            self.quattro.beams.electron_beam.angular_correction.tilt_correction.turn_off()
        except:
            pass
        
    # Stage Position & Move
    def current_position(self):
        _, y, z, _, _, _ = self.quattro.specimen.stage.current_position()
        return  None, y, z, a, None
    
    def relative_move(self, dx=0, dy=0, dz=0, da=0, db=0):
        self.quattro.specimen.stage.relative_move(x=dx, y=dy, z=dz, a=da, b=db)
        return 0
    
    
    def absolute_move(self, x=None, y=None, z=None, a=None, b=None):
        self.quattro.specimen.stage.absolute_move(x=x, y=y, z=z, a=a, b=b)
        return 0
    
    # Beam control
    def horizontal_field_view(self, value:int=None):
        if value==None:
            return self.quattro.beams.electron_beam.horizontal_field_width.value
        self.quattro.beams.electron_beam.horizontal_field_width.value = value
    
    def magnification(self, value:int=None):
        pass
    
    def working_distance(self, value:int=None):
        if value==None:
            return self.quattro.beams.electron_beam.working_distance.value
        self.quattro.beams.electron_beam.working_distance.value = value
    
    def tilt_correction(self, ONOFF:bool=None, value:float=None, mode:str=None):
        if ONOFF == True:
            self.quattro.beams.electron_beam.angular_correction.tilt_correction.turn_on()
        elif ONOFF == False:
            self.quattro.beams.electron_beam.angular_correction.tilt_correction.turn_off()
            return
        if mode == 'rel':
            self.quattro.beams.electron_beam.angular_correction.specimen_pretilt.value += value*np.pi/180
        else:
            self.quattro.beams.electron_beam.angular_correction.specimen_pretilt.value = value*np.pi/180
        
    def beam_shift(self, value_x:float=None, value_y:float=None, mode:str=None):
        if value_x==None or value_y==None:
            return self.quattro.beams.electron_beam.beam_shift.value
        if mode == 'rel':
            actual_shift_x, actual_shift_y =   self.quattro.beams.electron_beam.beam_shift.value
            shift = Point(x=value_x+actual_shift_x, y=value_y+actual_shift_y)
            self.quattro.beams.electron_beam.beam_shift.value = shift
            return
        else:
            shift = Point(value_x, value_y)
            self.quattro.beams.electron_beam.beam_shift.value = shift
            return
    
    # Imaging
    def image_settings(self):
        resolution = self.quattro.beams.electron_beam.scanning.resolution.value
        dwell_time = self.quattro.beams.electron_beam.scanning.dwell_time.value
        return resolution, dwell_time
    
    def get_image(self):
        pass
    
    def acquire_frame(self, resolution='1536x1024', dwell_time=10e-6, bit_depth=16):
        settings = GrabFrameSettings(resolution=resolution, dwell_time=dwell_time, bit_depth=bit_depth)
        image = self.quattro.imaging.grab_frame(settings)
        return image
    
    def acquire_multiple_frames(self, resolution='1536x1024', dwell_time=10e-6, bit_depth=16):
        settings = GrabFrameSettings(resolution=resolution, dwell_time=dwell_time, bit_depth=bit_depth)
        images = self.quattro.imaging.grab_multiple_frames(settings)
        return images
    
    def image_array(self, image):
        return image.data
    
    def save(self, image, path):
        image.save(path + '.tif')
    
    def beam_blanking(self):
        pass 
    
    def auto_contras_brightness(self):
        return self.quattro.auto_functions.run_auto_cb()

class SMARACT_MCS_3D(microscope):
    def __init__(self) -> None:
        pass
           
    # Packages & Connexion
    def import_package_and_connexion(self):
        from smaract import connexion_smaract_64bits as sm
        self.positioner = sm.smaract_class(calibrate=False)
    
    # Stage Position & Move
    def current_position(self):
        z, y, a = self.positioner.getpos()
        if None in [z, y, a]:
            return None, None, None, None, None
        return  None, y*1e-9, z*1e-9, a*1e-6, None
    
    def relative_move(self, dx=0, dy=0, dz=0, da=0, db=0):
        self.positioner.setpos_rel([dz*1e9, dy*1e9, da*1e6])
        return
    
    def absolute_move(self, x=None, y=None, z=None, a=None, b=None):
        return self.positioner.setpos_abs([z*1e9, y*1e9, a*1e6])


if __name__ == "__main__":
    
    active_microscope = microscope().f
    a = active_microscope.import_package_and_connexion()
    print(a)