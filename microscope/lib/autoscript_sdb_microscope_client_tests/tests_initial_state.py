from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import unittest


class TestsInitialState(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)

    def tearDown(self):
        pass

    def test_initial_state(self):
        microscope = self.microscope

        print("Setting microscope to initial state...")

        if microscope.specimen.stage.is_installed and not microscope.specimen.stage.is_homed:
            print("Homing stage...")
            microscope.specimen.stage.home()

        # Disconnect temperature stage if connected
        if not self.test_helper.get_major_system_version() < 12 and microscope.specimen.temperature_stage.type == TemperatureStageType.MICRO_HEATER:
            print("Disconnecting micro heater...")
            self.microscope.service.autoscript.server.configuration.set_value("Devices.MicroHeater.Connected", "False")
        elif not self.test_helper.get_major_system_version() < 13 and microscope.specimen.temperature_stage.type == TemperatureStageType.COOLING_STAGE:
            print("Disconnecting cooling stage...")
            self.microscope.service.autoscript.server.configuration.set_value("Devices.CoolingStage.Connected", "False")
        elif not self.test_helper.get_major_system_version() < 13 and microscope.specimen.temperature_stage.type == TemperatureStageType.HEATING_STAGE:
            print("Disconnecting heating stage...")
            self.microscope.service.autoscript.server.configuration.set_value("Devices.HeatingStage.Connected", "False")
        elif not self.test_helper.get_major_system_version() < 13 and microscope.specimen.temperature_stage.type == TemperatureStageType.HIGH_VACUUM_HEATING_STAGE:
            print("Disconnecting high vacuum heating stage...")
            self.microscope.service.autoscript.server.configuration.set_value("Devices.HighVacuumHeatingStage.Connected", "False")

        print("Done.")
