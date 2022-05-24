from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *

from tests_imaging_big_snapshot import TestsImagingBigSnapshot
from tests_specimen_compustage import TestsSpecimenCompustage
from tests_patterning import TestsPatterning
from tests_detector import TestsDetector
from tests_beams_electron_beam import TestsBeamsElectronBeam
from tests_specimen_manipulator import TestsSpecimenManipulator
from tests_specimen_stage import TestsSpecimenStage
from tests_imaging import TestsImaging
from tests_beams_ion_beam import TestsBeamsIonBeam
from tests_structures import TestsPoint, TestsManipulatorPosition, TestsOtherStructures
from tests_structures import TestsStagePosition
from tests_auto_functions import TestsAutoFunctions
from tests_specimen_temperature_stage import TestsSpecimenTemperatureStage
from tests_service_generic_access import TestsServiceGenericAccess
from tests_vacuum import TestsVacuum

'''
tests = TestsServiceGenericAccess()
tests.setUp("localhost")
tests.test_generic_access()
'''

'''
tests = TestsCompustage()
tests.setUp("192.168.145.180")
tests.test_compustage_zy_link()
'''

'''
tests = TestsTemperatureStage()
tests.setUp("localhost")
tests.test_micro_heater()
'''

'''
tests = TestsAutoFunctions()
tests.setUp("localhost")
tests.test_run_ong_et_al_auto_stigmator()
'''

'''
tests = TestsPoint()
tests.setUp()
tests.test_point()
'''

'''
tests = TestsOtherStructures()
tests.setUp()
tests.test_other_structures()
'''

'''
tests = TestsImaging()
tests.setUp("localhost")
tests.test_grab_frame_with_drift_correction()
'''

'''
tests = TestsImagingBigSnapshot()
tests.setUp("localhost")
tests.test_grab_frame_to_disk_with_invalid_settings()
'''

'''
tests = TestsSpecimenStage()
tests.setUp("192.168.186.229")
tests.test_move_stage_to_device()
'''

'''
tests = TestsElectronBeam()
tests.setUp("192.168.145.151")
tests.test_change_optical_modes()
'''

'''
tests = TestsIonBeam()
tests.setUp("192.168.145.142")
tests.test_change_beam_current()
'''


tests = TestsPatterning()
tests.setUp("192.168.145.180")
tests.test_direct_pattern_property_access()

'''
tests = TestsDetector()
tests.setUp("192.168.145.148")
tests.test_stem3_set_custom_settings()
'''

'''
tests = TestsStagePosition()
tests.setUp("localhost")
tests.test_stage_position()
'''

'''
tests = TestsSpecimenManipulator()
tests.setUp("localhost")
tests.test_move_manipulator()
'''

'''
tests = TestsManipulatorPosition()
tests.setUp("localhost")
tests.test_manipulator_position()
'''

'''
tests = TestsVacuum()
tests.setUp("192.168.145.159")
tests.test_vacuum()
'''


