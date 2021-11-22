from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from tests_patterning import TestsPatterning
from tests_detector import TestsDetector
from tests_electron_beam import TestsElectronBeam
from tests_stage import TestsStage
from tests_imaging import TestsImaging
from tests_ion_beam import TestsIonBeam
from tests_structures import TestsPoint
from tests_structures import TestsStagePosition
from tests_auto_functions import TestsAutoFunctions
from tests_temperature_stage import TestsTemperatureStage


tests = TestsTemperatureStage()
tests.setUp("localhost")
tests.test_micro_heater()


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
tests = TestsImaging()
tests.setUp("192.168.145.129")
tests.test_grab_multiple_frames1()
'''

'''
tests = TestsStage()
tests.setUp("localhost")
tests.test_stage_move_with_link_zy()
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

'''
patterning_tests = TestsPatterning()
patterning_tests.setUp("localhost")
patterning_tests.test_direct_pattern_property_access()
'''

'''
tests = TestsDetector()
tests.setUp("192.168.145.128")
tests.test_insert_retract_detectors()
'''

'''
tests = TestsStagePosition()
tests.setUp("localhost")
tests.test_stage_position()
'''
