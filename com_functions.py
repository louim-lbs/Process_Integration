import copy
import time
import numpy as np
import os
from autoscript_sdb_microscope_client.structures import GrabFrameSettings, Point, StagePosition, AdornedImage

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
        img = DM.GetFrontImage()
        return img.GetDimensionScale(0)*img.GetDimensionSize(0)*1e-6

        
    def magnification(self, value:int=None):
        if value==None:
            return DM.Py_Microscope().GetMagnification()
        print('Magnififcation changes are not supported with ETEM')
        return
        return DM.Py_Microscope().SetMagIndex(value)
    
    def focus(self, value:float=None, mode:str=None):
        if value==None:
            return DM.Py_Microscope().GetFocus()*1e-9
        if mode == 'rel':
            return DM.Py_Microscope().ChangeFocus(value*1e9)
        return DM.Py_Microscope().SetFocus(value*1e9)
    
    def tilt_correction(self, *args):
        print('Tilt or angular correction for ETEM is not implemented')
        return
    
    def image_shift(self, value_x:float=None, value_y:float=None, mode:str=None):
        if value_x==None or value_y==None:
            x, y = DM.Py_Microscope().GetImageShift()
            return x*1e-9, y*1e-9
        if mode == 'rel':
            return DM.Py_Microscope().ChangeImageShift(value_x*1e9, value_y*1e9)
        return DM.Py_Microscope().SetImageShift(value_x*1e9, value_y*1e9)
    
    def beam_shift(self, value_x:float=None, value_y:float=None, mode:str=None):
        if value_x==None or value_y==None:
            x, y = DM.Py_Microscope().GetBeamShift()
            return y*1e-9, x*1e-9
        if mode == 'rel':
            return DM.Py_Microscope().ChangeBeamShift(value_y*1e9, value_x*1e9)
        return DM.Py_Microscope().SetBeamShift(value_y*1e9, value_x*1e9)
    
    def projector_shift(self, value_x:float=None, value_y:float=None, mode:str=None):
        if value_x==None or value_y==None:
            x, y = DM.Py_Microscope().GetProjectorShift()
            return x*1e-9, y*1e-9
        if mode == 'rel':
            return DM.Py_Microscope().ChangeProjectorShift(value_x*1e9, value_y*1e9)
        return DM.Py_Microscope().SetProjectorShift(value_x*1e9, value_y*1e9)
    
    # Imaging
    def image_settings(self):
        exposure, xBin, yBin, _, top, left, bottom, right = self.camera.GetDefaultParameters()
        x_resol = int((right - left)/xBin)
        y_resol = int((bottom - top)/yBin)
        resolution = str(y_resol) + 'x' + str(x_resol)
        dwell_time = exposure/(x_resol*y_resol)
        return resolution, dwell_time

    def get_image(self):
        return DM.GetFrontImage()
    
    def acquire_frame(self, resolution=None, dwell_time=None, bit_depth=None):
        if resolution==None and dwell_time==None and bit_depth==None:
            resolution, dwell_time = self.image_settings()
        resolution_y, resolution_x = resolution.split('x')
        paramID = DM.DS_CreateParameters(int(resolution_y), int(resolution_x), 4, 0, dwell_time*1e6, False)
        DM.DS_SetParametersSignal(paramID, signalIndex=0, dataType=4, selected=True, imageID=0)
        DM.DS_StartAcquisition(paramID, continuous=False, synchronous=True)
        ID = DM.DS_GetAcquiredImageID(0)
        img = DM.FindImageByID(ID)
        return img
    
    def acquire_multiple_frames(self, resolution=None, dwell_time=None, bit_depth=None):
        print('Multiple frames acquisition is not yet implemented')
    
    def image_array(self, image):
        return image.GetNumArray()
    
    def save(self, image, path):
        image.SaveAsGatan(path + '.dm4')
    
    def beam_blanking(self, ONOFF:bool):
        return DM.Py_Microscope().SetBeamBlanked(ONOFF)
    
    def start_acquisition(self):
        ####
        return

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
        self.quattro.specimen.stage.relative_move(StagePosition(x=dx, y=dy, z=dz, r=da))
        return 0
    
    
    def absolute_move(self, x=None, y=None, z=None, a=None, b=None):
        self.quattro.specimen.stage.absolute_move(StagePosition(x=x, y=y, z=z, r=a))
        return 0
    
    # Beam control
    def horizontal_field_view(self, value:int=None):
        if value==None:
            return self.quattro.beams.electron_beam.horizontal_field_width.value
        self.quattro.beams.electron_beam.horizontal_field_width.value = value
    
    def magnification(self, value:int=None):
        pass
    
    def focus(self, value:int=None, mode:str=None):
        if value==None:
            return self.quattro.beams.electron_beam.working_distance.value
        if mode == 'rel':
            self.quattro.beams.electron_beam.working_distance.value += value
            return
        self.quattro.beams.electron_beam.working_distance.value = value
    
    def tilt_correction(self, ONOFF:bool=None, value:float=None, mode:str=None):
        if ONOFF == True:
            self.quattro.beams.electron_beam.angular_correction.mode = 'Automatic'
            self.quattro.beams.electron_beam.angular_correction.tilt_correction.turn_on()
        elif ONOFF == False:
            self.quattro.beams.electron_beam.angular_correction.tilt_correction.turn_off()
            return
        if value != None and mode == 'rel':
            self.quattro.beams.electron_beam.angular_correction.specimen_pretilt.value += value*np.pi/180
        elif value != None and mode != 'rel':
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
    
    def acquire_frame(self, resolution='1536x1024', dwell_time=1e-6, bit_depth=16):
        img = self.quattro.imaging.get_image()
        img_prev_stamp = img.data[-1,:]

        micro_resolution = self.quattro.beams.electron_beam.scanning.resolution.value
        micro_dwell_time = self.quattro.beams.electron_beam.scanning.dwell_time.value
        micro_bit_depth = self.quattro.beams.electron_beam.scanning.bit_depth
        if [micro_resolution, micro_dwell_time, micro_bit_depth] != [resolution, dwell_time, bit_depth]:
            self.quattro.beams.electron_beam.scanning.resolution.value = resolution
            self.quattro.beams.electron_beam.scanning.dwell_time.value = dwell_time
            self.quattro.beams.electron_beam.scanning.bit_depth = bit_depth

        while (True):
            # t = time.time()
            img = self.quattro.imaging.get_image()
            # t2 = time.time()
            # print('while', t2-t)
            try:
                # t = time.time()
                if not np.array_equal(img_prev_stamp, img.data[-1,:]):# (img_prev_stamp == img.data[-1,:]).all():
                    # t2 = time.time()
                    # print('try', t2-t)
                    return img
            except:
                print('error acquire frame')
                pass
    
    def acquire_multiple_frames(self, resolution='1536x1024', dwell_time=1e-6, bit_depth=16, windows='123'):
        # settings = GrabFrameSettings(resolution=resolution, dwell_time=dwell_time, bit_depth=bit_depth)
        # images = self.quattro.imaging.grab_multiple_frames(settings)
        # return images
        
        windows         = [int(s) for s in windows]

        imgs            = [0]*len(windows)
        
        view = self.quattro.imaging.get_active_view()
        self.quattro.imaging.set_active_view(view)
        ind = windows.index(view)
        imgs[ind] = self.quattro.imaging.get_image()
        img_prev_stamp = imgs[ind].data[-1,:]

        micro_resolution = self.quattro.beams.electron_beam.scanning.resolution.value
        micro_dwell_time = self.quattro.beams.electron_beam.scanning.dwell_time.value
        micro_bit_depth = self.quattro.beams.electron_beam.scanning.bit_depth
        if [micro_resolution, micro_dwell_time, micro_bit_depth] != [resolution, dwell_time, bit_depth]:
            self.quattro.beams.electron_beam.scanning.resolution.value = resolution
            self.quattro.beams.electron_beam.scanning.dwell_time.value = dwell_time
            self.quattro.beams.electron_beam.scanning.bit_depth = bit_depth

        while (True):
            imgs[ind] = self.quattro.imaging.get_image()
            view2 = self.quattro.imaging.get_active_view()
            if view != view2:
                view = copy.deepcopy(view2)
                ind = windows.index(view)
                imgs[ind] = self.quattro.imaging.get_image()
                img_prev_stamp = imgs[ind].data[-1,:]
            if not (img_prev_stamp == imgs[ind].data[-1,:]).all():
                for j in range(len(windows)):
                    self.quattro.imaging.set_active_view(windows[j])
                    imgs[j] = self.quattro.imaging.get_image()
                return imgs
    
    def image_array(self, image):
        return image.data
    
    def save(self, image, path):
        image.save(path + '.tif')

    def load(self, path):
        img = AdornedImage.load(path)
        return img.data
    
    def beam_blanking(self, ONOFF:bool):
        if ONOFF == True:
            return self.quattro.beams.electron_beam.blank()
        elif ONOFF == False:
            return self.quattro.beams.electron_beam.unblank()
    
    def auto_contrast_brightness(self):
        return self.quattro.auto_functions.run_auto_cb()
    
    def start_acquisition(self):
        return self.quattro.imaging.start_acquisition()

class SMARACT_MCS_3D(microscope):
    def __init__(self) -> None:
        pass
           
    # Packages & Connexion
    def import_package_and_connexion(self):
        from smaract import connexion_smaract_64bits as sm
        self.positioner = sm.smaract_class(calibrate=False)
        self.InitState_status = 0
    
    # Stage Position & Move
    def current_position(self):
        z, y, a = self.positioner.getpos()
        if None in [z, y, a]:
            return None, None, None, None, None
        return  None, y*1e-9, z*1e-9, a*1e-6, None
    
    def relative_move(self, dx=0, dy=0, dz=0, da=0, db=0):
        self.positioner.setpos_rel([dz*1e9, dy*1e9, da*1e6])
        return 0
    
    def absolute_move(self, x=None, y=None, z=None, a=None, b=None):
        self.positioner.setpos_abs([z*1e9, y*1e9, a*1e6])
        return 0


if __name__ == "__main__":
    
    active_microscope = microscope().f
    a = active_microscope.import_package_and_connexion()
    print(a)