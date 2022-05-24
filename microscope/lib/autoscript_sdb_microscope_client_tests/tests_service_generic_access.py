from autoscript_core.common import ApplicationServerException
from autoscript_sdb_microscope_client_tests.utilities import *
import enum
import unittest

class ControlItemType(enum.Enum):
    CONTROL_ITEM_BOOLEAN = 0
    CONTROL_ITEM_FLOAT = 1
    CONTROL_ITEM_INT = 2
    PARAMETER_BOOLEAN = 3
    PARAMETER_INT = 4
    CONTROL_ITEM_FLOAT_PAIR =5

class TestsServiceGenericAccess(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)

    def tearDown(self):
        pass

    def test_generic_access(self):
        self.__test_control_item("Instrument.Beams.ElectronBeam.BeamIsOn", ControlItemType.CONTROL_ITEM_BOOLEAN)
        self.__test_control_item("Instrument.Beams.ElectronBeam.WorkingDistance", ControlItemType.CONTROL_ITEM_FLOAT)
        self.__test_control_item("Instrument.Beams.ElectronBeam.BeamCurrentIndex", ControlItemType.CONTROL_ITEM_INT)
        self.__test_control_item("Instrument.Beams.ElectronBeam.TiltCorrectionAngleManualMode", ControlItemType.PARAMETER_BOOLEAN)
        self.__test_control_item_float_pair("Instrument.Beams.ElectronBeam.Stigmator")
        self.__test_action("Instrument.Sleep")

        print("Done.")

    def __test_control_item(self, object_model_path: str, item_type: ControlItemType):
        generic_access = self.microscope.service.generic_access

        print(f"Accessing {object_model_path}...")

        if not generic_access.item_exists(object_model_path):
            print("Not present, skipping")
            return

        item = generic_access.get_control_item(object_model_path)
        print("    Target value:", item.target_value)
        print("    Actual value:", item.actual_value)
        print("    Is controllable:", item.is_controllable)

        if item_type == ControlItemType.CONTROL_ITEM_BOOLEAN or item_type == ControlItemType.PARAMETER_BOOLEAN:
            with self.assertRaisesRegex(ApplicationServerException, "provide limits"):
                limits = item.logical_limits
        else:
            print("    Logical limits:", item.logical_limits)

        if item.is_controllable:
            print("    Setting target value...")
            item.target_value = item.target_value
            print("    Setting actual value...")
            item.actual_value = item.actual_value

    def __test_control_item_float_pair(self, object_model_path: str):
        generic_access = self.microscope.service.generic_access

        print(f"Accessing {object_model_path}...")

        if not generic_access.item_exists(object_model_path):
            print("Not present, skipping")
            return

        item = generic_access.get_control_item_pair(object_model_path)
        print("    Target value:", item.target_value)
        print("    Actual value:", item.actual_value)
        print("    Is controllable:", item.is_controllable)
        print("    Logical limits:", item.logical_limits)

        if item.is_controllable:
            print("    Setting target value...")
            item.target_value = item.target_value

    def __test_action(self, object_model_path: str):
        generic_access = self.microscope.service.generic_access

        print(f"Accessing {object_model_path}...")

        if not generic_access.item_exists(object_model_path):
            print("Not present, skipping")
            return

        action = generic_access.get_action(object_model_path)
        print("    Is startable:", action.is_startable)
