from autoscript_core.common import ApplicationServerException
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import math
import time
import unittest


class TestsTemperatureStage(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)

    def tearDown(self):
        pass

    def __to_kelvin(self, celsius):
        return 273.15 + celsius

    def __to_celsius(self, kelvin):
        return kelvin - 273.15

    def __get_stage_configuration_key(self, stage_type):
        if stage_type == TemperatureStageType.HEATING_STAGE:
            return "Devices.HeatingStage"
        elif stage_type == TemperatureStageType.COOLING_STAGE:
            return "Devices.CoolingStage"
        elif stage_type == TemperatureStageType.HIGH_VACUUM_HEATING_STAGE:
            return "Devices.HighVacuumHeatingStage"
        elif stage_type == TemperatureStageType.MICRO_HEATER:
            return "Devices.MicroHeater"
        raise ValueError("Unknown stage type.")

    def __ensure_stage_is_installed(self, stage_type):
        configuration_key = self.__get_stage_configuration_key(stage_type) + ".Installed"
        is_installed = self.microscope.service.autoscript.server.configuration.get_value(configuration_key)
        if is_installed == "False":
            self.skipTest(f"{stage_type} is not installed, skipping...")

    def __connect_stage(self, stage_type):
        print(f"Connecting {stage_type}...")

        connected_stage_type = self.microscope.specimen.temperature_stage.type
        if connected_stage_type == stage_type:
            print(f"Already connected, no action taken")
            return

        if connected_stage_type != TemperatureStageType.NONE:
            print("Detected another connected stage, disconnecting it first...")
            self.__disconnect_stage(connected_stage_type)

        configuration_key = self.__get_stage_configuration_key(stage_type) + ".Connected"
        self.microscope.service.autoscript.server.configuration.set_value(configuration_key, "True")
        print(f"{stage_type} connected.")

    def __disconnect_stage(self, stage_type):
        print(f"Disconnecting {stage_type}...")
        configuration_key = self.__get_stage_configuration_key(stage_type) + ".Connected"
        self.microscope.service.autoscript.server.configuration.set_value(configuration_key, "False")
        print(f"{stage_type} disconnected.")

    def __calibrate_stage(self, stage_type):
        print(f"Calibrating {stage_type}...")
        if stage_type == TemperatureStageType.MICRO_HEATER:
            configuration_key = self.__get_stage_configuration_key(stage_type) + ".Calibrated"
            self.microscope.service.autoscript.server.configuration.set_value(configuration_key, "True")
        else:
            raise InvalidOperationException(f"Don't know how to calibrate {stage_type}")

    def __is_stage_calibrated(self, stage_type):
        if stage_type == TemperatureStageType.MICRO_HEATER:
            configuration_key = self.__get_stage_configuration_key(stage_type) + ".Calibrated"
            return self.microscope.service.autoscript.server.configuration.get_value(configuration_key) == "True"
        else:
            raise InvalidOperationException(f"Don't know if {stage_type} is calibrated")

    def __test_temperature_stage_properties(self, stage_type):
        temperature_stage = self.microscope.specimen.temperature_stage

        print(f"Testing {stage_type} properties...")
        self.assertEqual(temperature_stage.type, stage_type)

        temperature = temperature_stage.temperature
        target_value_celsius = self.__to_celsius(temperature.target_value)
        actual_value_celsius = self.__to_celsius(temperature.value)
        limits_celsius = Limits(self.__to_celsius(temperature.limits.min), self.__to_celsius(temperature.limits.max))
        print(f"Temperature target value is {target_value_celsius:.1f} C, actual value is {actual_value_celsius:.1f} C, limits are {limits_celsius} C")

        ramping_speed = temperature_stage.ramping_speed
        print(f"Ramping speed actual value is {ramping_speed.value:.1f} C/s, limits are {ramping_speed.limits} C/s")

        print("Turning the stage on...")
        temperature_stage.turn_on()
        self.assertTrue(temperature_stage.is_on)
        print("Success.")

        print("Setting target temperature...")
        new_temperature = temperature.limits.min + abs(temperature.limits.max - temperature.limits.min) / 2.0
        temperature_stage.temperature.target_value = new_temperature
        self.assertAlmostEqual(temperature_stage.temperature.target_value, new_temperature)
        print("Success.")

        print("Setting ramping speed...")
        new_ramping_speed = ramping_speed.limits.min + abs(ramping_speed.limits.max - ramping_speed.limits.min) / 3.0
        ramping_speed.target_value = new_ramping_speed
        self.assertAlmostEqual(ramping_speed.target_value, new_ramping_speed)
        print("Success.")

        print("Turning the stage off...")
        temperature_stage.turn_off()
        self.assertFalse(temperature_stage.is_on)
        print("Success.")

    def __test_ramping(self, target_temperature_celsius, ramping_speed, tolerance, soak_time, timeout):
        temperature_stage = self.microscope.specimen.temperature_stage

        print(f"Ramping to temperature={target_temperature_celsius:.1f} C with ramping speed={ramping_speed} C/s, tolerance={tolerance} C soak time={soak_time} s and timeout={timeout} s")

        actual_temperature_celsius = self.__to_celsius(temperature_stage.temperature.value)
        print(f"Actual temperature is {actual_temperature_celsius:.1f} C")

        start_time = time.time()
        target_temperature = self.__to_kelvin(target_temperature_celsius)
        settings = TemperatureSettings(target_temperature=target_temperature, ramping_speed=ramping_speed, tolerance=tolerance, soak_time=soak_time, timeout=timeout)
        temperature_stage.ramp(settings)
        end_time = time.time()

        print(f"Ramping finished in {(end_time - start_time):.1f} s")

    def test_micro_heater(self):
        temperature_stage = self.microscope.specimen.temperature_stage

        if self.test_helper.get_major_system_version() < 12 and not self.test_helper.is_offline():
            self.skipTest("Not supported on xT versions lower than 12.")

        self.__ensure_stage_is_installed(TemperatureStageType.MICRO_HEATER)
        self.__connect_stage(TemperatureStageType.MICRO_HEATER)

        if not self.__is_stage_calibrated(TemperatureStageType.MICRO_HEATER):
            print("Calling on uHeater before calibration must throw...")
            with self.assertRaisesRegex(ApplicationServerException, "has not been calibrated"):
                temperature_stage.turn_on()
            with self.assertRaisesRegex(ApplicationServerException, "has not been calibrated"):
                temperature_stage.turn_off()
            with self.assertRaisesRegex(ApplicationServerException, "has not been calibrated"):
                temperature_stage.ramp(TemperatureSettings(target_temperature=200))

            # Now, simulate calibration
            self.__calibrate_stage(TemperatureStageType.MICRO_HEATER)

        self.__test_temperature_stage_properties(TemperatureStageType.MICRO_HEATER)

        if self.test_helper.is_offline():
            # In offline mode we can test more scenarios
            self.__test_ramping(target_temperature_celsius=100, ramping_speed=10, tolerance=1, soak_time=None, timeout=None)
            self.__test_ramping(target_temperature_celsius=155, ramping_speed=None, tolerance=None, soak_time=None, timeout=None)
            self.__test_ramping(target_temperature_celsius=110, ramping_speed=15, tolerance=10, soak_time=1, timeout=None)
        else:
            # On XT simulator we go just once
            actual_temperature = round(self.__to_celsius(temperature_stage.temperature.value), 0)
            target_temperature = min(actual_temperature + 35, temperature_stage.temperature.limits.max)
            self.__test_ramping(target_temperature_celsius=target_temperature, ramping_speed=20, tolerance=1, soak_time=1, timeout=None)

        print("Testing situation when ramping times out...")
        with self.assertRaisesRegex(ApplicationServerException, "not reached in time"):
            target_temperature = temperature_stage.temperature.limits.max - 50
            settings = TemperatureSettings(target_temperature=target_temperature, ramping_speed=0.5, timeout=2)
            temperature_stage.ramp(settings)

        print("Turning the stage off...")
        temperature_stage.turn_off()

        self.__disconnect_stage(TemperatureStageType.MICRO_HEATER)
        print("Done.")

    def test_cooling_stage(self):
        temperature_stage = self.microscope.specimen.temperature_stage

        if self.test_helper.get_major_system_version() < 13 and not self.test_helper.is_offline():
            self.skipTest("Not supported on xT versions lower than 13.")

        self.__ensure_stage_is_installed(TemperatureStageType.COOLING_STAGE)
        self.__connect_stage(TemperatureStageType.COOLING_STAGE)

        self.__test_temperature_stage_properties(TemperatureStageType.COOLING_STAGE)

        if self.test_helper.is_offline():
            # In offline mode we can test more scenarios
            self.__test_ramping(target_temperature_celsius=-10, ramping_speed=8, tolerance=None, soak_time=2, timeout=3000)
            self.__test_ramping(target_temperature_celsius=5, ramping_speed=4, tolerance=2, soak_time=None, timeout=None)
        else:
            # On XT simulator, the real ramping speed is much lower than specified, set the tolerance such that we finish ramping almost immediately.
            # Still, this often times out on Prisma.
            actual_temperature = self.__to_celsius(temperature_stage.temperature.value)
            target_temperature = actual_temperature - 0.1
            self.__test_ramping(target_temperature_celsius=target_temperature, ramping_speed=0.3, tolerance=0.1, soak_time=0, timeout=90)

        print("Turning the stage off...")
        temperature_stage.turn_off()

        self.__disconnect_stage(TemperatureStageType.COOLING_STAGE)
        print("Done.")

    def test_heating_stage(self):
        temperature_stage = self.microscope.specimen.temperature_stage

        if self.test_helper.get_major_system_version() < 13 and not self.test_helper.is_offline():
            self.skipTest("Not supported on xT versions lower than 13.")

        self.__ensure_stage_is_installed(TemperatureStageType.HEATING_STAGE)
        self.__connect_stage(TemperatureStageType.HEATING_STAGE)

        self.__test_temperature_stage_properties(TemperatureStageType.HEATING_STAGE)

        # We cannot test ramping on XT simulator, ramping up to the minimum temperature with maximum speed takes minutes.
        # That would hold up tests for too long.

        if self.test_helper.is_offline():
            # In offline mode we can test more scenarios
            self.__test_ramping(target_temperature_celsius=60, ramping_speed=15, tolerance=None, soak_time=1, timeout=3000)
            self.__test_ramping(target_temperature_celsius=70, ramping_speed=4, tolerance=0.1, soak_time=None, timeout=None)

        print("Testing situation when ramping times out...")
        with self.assertRaisesRegex(ApplicationServerException, "not reached in time"):
            target_temperature = temperature_stage.temperature.limits.max - 50
            settings = TemperatureSettings(target_temperature=target_temperature, ramping_speed=0.5, timeout=2)
            temperature_stage.ramp(settings)

        print("Turning the stage off...")
        temperature_stage.turn_off()

        self.__disconnect_stage(TemperatureStageType.HEATING_STAGE)
        print("Done.")

    def test_high_vacuum_heating_stage(self):
        temperature_stage = self.microscope.specimen.temperature_stage

        if self.test_helper.get_major_system_version() < 13 and not self.test_helper.is_offline():
            self.skipTest("Not supported on xT versions lower than 13.")

        self.__ensure_stage_is_installed(TemperatureStageType.HIGH_VACUUM_HEATING_STAGE)
        self.__connect_stage(TemperatureStageType.HIGH_VACUUM_HEATING_STAGE)

        self.__test_temperature_stage_properties(TemperatureStageType.HIGH_VACUUM_HEATING_STAGE)

        # We cannot test ramping on XT simulator, ramping up to the minimum temperature with maximum speed takes minutes.
        # That would hold up tests for too long.

        if self.test_helper.is_offline():
            self.__test_ramping(target_temperature_celsius=40, ramping_speed=10, tolerance=10, soak_time=1, timeout=3000)

        print("Testing ramping with invalid input...")
        with self.assertRaisesRegex(ApplicationServerException, "not specified"):
            settings = TemperatureSettings()
            temperature_stage.ramp(settings)
        with self.assertRaisesRegex(ApplicationServerException, "must be"):
            settings = TemperatureSettings(target_temperature=20, tolerance=0)
            temperature_stage.ramp(settings)
        with self.assertRaisesRegex(ApplicationServerException, "must be"):
            settings = TemperatureSettings(target_temperature=20, soak_time=-1)
            temperature_stage.ramp(settings)
        with self.assertRaisesRegex(ApplicationServerException, "must be"):
            settings = TemperatureSettings(target_temperature=20, timeout=-1)
            temperature_stage.ramp(settings)
        with self.assertRaisesRegex(ApplicationServerException, "must be"):
            settings = TemperatureSettings(target_temperature=20, ramping_speed=0)
            temperature_stage.ramp(settings)

        print("Testing situation when ramping times out...")
        with self.assertRaisesRegex(ApplicationServerException, "not reached in time"):
            target_temperature = temperature_stage.temperature.limits.max - 50
            settings = TemperatureSettings(target_temperature=target_temperature, ramping_speed=0.5, timeout=2)
            temperature_stage.ramp(settings)

        self.__disconnect_stage(TemperatureStageType.HIGH_VACUUM_HEATING_STAGE)
        print("Done.")
