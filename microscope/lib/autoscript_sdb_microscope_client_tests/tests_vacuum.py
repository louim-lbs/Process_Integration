from autoscript_core.common import ApplicationServerException
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import unittest


class TestsVacuum(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)

    def tearDown(self):
        pass

    def test_vacuum(self):
        self.__test_vacuum_state()
        self.__test_vacuum_invalid_states()

        # mpav: Commenting out because of too long duration
        # self.__test_vacuum_control()

    def __test_vacuum_state(self):
        microscope = self.microscope

        print("Reading vacuum state...")
        print("    Chamber state is", microscope.vacuum.chamber_state)
        print("    Chamber pressure is", microscope.vacuum.chamber_pressure.value, "Pa")
        print("    Chamber pressure limits are", microscope.vacuum.chamber_pressure.limits)
        print("Done.")

    def __test_vacuum_invalid_states(self):
        microscope = self.microscope

        print("Specifying only gas type without vacuum mode must throw")
        with self.assertRaisesRegex(ApplicationServerException, "specify vacuum mode"):
            settings = VacuumSettings(gas=VacuumGasType.ARGON)
            microscope.vacuum.pump(settings)
        print("Success.")

        print("Providing an unknown mode must throw")
        with self.assertRaisesRegex(ApplicationServerException, "Unknown vacuum mode"):
            settings = VacuumSettings(mode="Dummy")
            microscope.vacuum.pump(settings)
        print("Success.")

        print("Trying to set gas for hi-vac must throw")
        with self.assertRaisesRegex(ApplicationServerException, "vacuum mode"):
            settings = VacuumSettings(mode=VacuumMode.HIGH_VACUUM, gas=VacuumGasType.WATER)
            microscope.vacuum.pump(settings)
        print("Success.")

        if not self.test_helper.is_vacuum_mode_esem_available:
            print("Asking for ESEM when there is no ESEM must throw")
            with self.assertRaisesRegex(ApplicationServerException, "not supported"):
                settings = VacuumSettings(mode=VacuumMode.ESEM)
                microscope.vacuum.pump(settings)
            print("Success.")

        if not self.test_helper.is_vacuum_mode_low_available:
            print("Asking for LoVac when there is no LoVac must throw")
            with self.assertRaisesRegex(ApplicationServerException, "not supported"):
                settings = VacuumSettings(mode=VacuumMode.LOW_VACUUM)
                microscope.vacuum.pump(settings)
            print("Success.")

    def __test_vacuum_control(self):
        microscope = self.microscope
        pressure_limits = microscope.vacuum.chamber_pressure.limits

        if microscope.vacuum.chamber_state == VacuumState.PUMPED:
            print("Venting chamber...")
            microscope.vacuum.vent()
            print("Vented.")

        if microscope.vacuum.chamber_state == VacuumState.VENTED:
            print("Pumping back to high vacuum...")
            settings = VacuumSettings(mode=VacuumMode.HIGH_VACUUM)
            microscope.vacuum.pump(settings)
            print("Pumped.")

        if self.test_helper.is_vacuum_mode_low_available:
            pressure = pressure_limits.midpoint
            print(f"Pumping to low vacuum to pressure {pressure} Pa...")
            settings = VacuumSettings(mode=VacuumMode.LOW_VACUUM, pressure=pressure)
            microscope.vacuum.pump(settings)
            print("Pumped.")

            pressure = pressure_limits.midpoint + 10
            print(f"Changing chamber pressure to {pressure} Pa...")
            settings = VacuumSettings(pressure=pressure)
            microscope.vacuum.pump(settings)
            print("Success.")

            if self.test_helper.is_vacuum_gas_available(VacuumMode.LOW_VACUUM, VacuumGasType.WATER):
                print("Changing gas type to Water...")
                settings = VacuumSettings(mode=VacuumMode.LOW_VACUUM, gas=VacuumGasType.WATER)
                microscope.vacuum.pump(settings)
                print("Success.")

            if self.test_helper.is_vacuum_gas_available(VacuumMode.LOW_VACUUM, VacuumGasType.AUXILIARY):
                print("Changing gas type to Auxiliary...")
                settings = VacuumSettings(mode=VacuumMode.LOW_VACUUM, gas=VacuumGasType.AUXILIARY)
                microscope.vacuum.pump(settings)
                print("Success.")

        if self.test_helper.is_vacuum_mode_esem_available:
            print("Pumping to ESEM vacuum...")
            pressure = pressure_limits.midpoint + 10
            settings = VacuumSettings(mode=VacuumMode.ESEM, pressure=pressure)
            microscope.vacuum.pump(settings)
            print("Pumped.")

            pressure = pressure_limits.midpoint - 10
            print(f"Changing chamber pressure to {pressure} Pa...")
            settings = VacuumSettings(pressure=pressure)
            microscope.vacuum.pump(settings)
            print("Success.")

            if self.test_helper.is_vacuum_gas_available(VacuumMode.ESEM, VacuumGasType.WATER):
                print("Changing gas type to Water...")
                settings = VacuumSettings(mode=VacuumMode.ESEM, gas=VacuumGasType.WATER)
                microscope.vacuum.pump(settings)
                print("Success.")

            if self.test_helper.is_vacuum_gas_available(VacuumMode.ESEM, VacuumGasType.AUXILIARY):
                print("Changing gas type to Auxiliary...")
                settings = VacuumSettings(mode=VacuumMode.ESEM, gas=VacuumGasType.AUXILIARY)
                microscope.vacuum.pump(settings)
                print("Success.")
