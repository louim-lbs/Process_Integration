from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import time
import unittest
import numpy as np


class TestsIonBeam(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.beam = self.microscope.beams.ion_beam
        self.system_name = self.microscope.service.system.name
        self.test_helper = TestHelper(self, self.microscope)

    def tearDown(self):
        pass

    def test_turn_beam_on(self):
        print("Turning beam on...")
        self.beam.turn_on()
        self.assertTrue(self.beam.is_on)
        print("Done.")

    def test_blank_unblank_beam(self):
        print("Blanking beam...")
        self.beam.blank()
        self.assertTrue(self.beam.is_blanked)
        time.sleep(0.5)

        print("Unblanking beam...")
        self.beam.unblank()
        self.assertFalse(self.beam.is_blanked)
        print("Done.")

    def test_change_high_voltage(self):
        self.test_helper.test_generic_setting(self.beam.high_voltage, "high voltage", [10e3, 5e3])
        print("Done.")

    def test_change_beam_current(self):
        print("Getting all available ion beam currents...")
        # Pick beam current values approximately in the first and second third of the available range
        available_beam_currents = self.beam.beam_current.available_values

        current1 = available_beam_currents[int(len(available_beam_currents) / 3 * 1)]
        current2 = available_beam_currents[int(len(available_beam_currents) / 3 * 2)]

        precision = self.test_helper.get_precision_for_decimal_places(current1, 2)
        self.test_helper.test_generic_setting(self.beam.beam_current, "ion beam current", [current1], precision)

        precision = self.test_helper.get_precision_for_decimal_places(current2, 2)
        self.test_helper.test_generic_setting(self.beam.beam_current, "ion beam current", [current2], precision)

        print("Done.")

    def test_change_scanning_resolution(self):
        self.test_helper.test_generic_setting(self.beam.scanning.resolution, "scanning resolution", ["1536x1024", "768x512"])
        print("Done.")

    def test_change_scanning_bit_depth(self):
        print("Changing bit depth to 16 bit...")
        self.beam.scanning.bit_depth = 16
        self.assertEqual(self.beam.scanning.bit_depth, 16)

        print("Changing bit depth to 8 bit...")
        self.beam.scanning.bit_depth = 8
        self.assertEqual(self.beam.scanning.bit_depth, 8)
        print("Done.")

    def test_change_stigmator(self):
        self.test_helper.test_generic_setting(self.beam.stigmator, "stigmator", [Point(0.5, -0.5), Point(-0.5, 0.5), Point(0.0)])
        print("Done.")

    def test_change_beam_shift(self):
        half_value = ((self.beam.beam_shift.limits.limits_x.max - self.beam.beam_shift.limits.limits_x.min) / 4) * 3 + self.beam.beam_shift.limits.limits_x.min
        self.test_helper.test_generic_setting(self.beam.beam_shift, "beam shift", [Point(half_value, -half_value), Point(-half_value, half_value), Point(0.0)], number_precision=6)
        print("Done.")

    def test_change_working_distance(self):
        self.test_helper.test_generic_setting(self.beam.working_distance, "working distance", [12e-3, 10e-3], number_precision=4)
        print("Done.")

    def test_switch_scanning_modes(self):
        scanning_mode = self.beam.scanning.mode
        delay_between_switches = 0.5

        print("Switching to reduced area scan mode...")
        scanning_mode.set_reduced_area()
        self.assertEqual(ScanningMode.REDUCED_AREA, scanning_mode.value)
        time.sleep(delay_between_switches)

        print("Switching to full frame scan mode...")
        scanning_mode.set_full_frame()
        self.assertEqual(ScanningMode.FULL_FRAME, scanning_mode.value)
        time.sleep(delay_between_switches)
        print("Done.")

    def test_get_time_to_heat_source(self):
        if self.test_helper.is_system_plasma_fib():
            self.skipTest("Not applicable on plasma systems, skipping")

        time_to_heat = self.beam.source.time_to_heat
        self.assertIsNotNone(time_to_heat)
        print("Time to heat ion beam source is %d s" % time_to_heat)

    def test_source_heating(self):
        if self.test_helper.is_system_plasma_fib():
            self.skipTest("Not applicable on plasma systems, skipping")

        if self.test_helper.is_system(SystemFamily.VERSA3D):
            self.skipTest("This test takes too long on Versa 3D, skipping")

        print("Heating ion beam source...")
        self.beam.source.heat()
        print("Done.")

    def test_change_plasma_gas(self):
        plasma_gas = self.microscope.beams.ion_beam.source.plasma_gas
        print("Testing access to plasma source gas...")
        print("Available plasma gasses:", plasma_gas.available_values)
        print("Currently selected plasma gas:", plasma_gas.value)
        print("Switching gas to Nitrogen...")
        plasma_gas.value = PlasmaGasType.NITROGEN
        print("Plasma gas is now", plasma_gas.value)
        print("Done.")
