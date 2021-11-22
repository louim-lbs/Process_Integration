from autoscript_core.common import ApplicationServerException
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import time
import unittest
import numpy as np


class TestsElectronBeam(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.beam = self.microscope.beams.electron_beam
        self.test_helper = TestHelper(self, self.microscope)
        self.xt_major_version = int(self.microscope.service.system.version.split('.')[0])
        self.system_name = self.microscope.service.system.name

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
    
    def test_change_beam_current(self):
        print("Testing subset of beam currents at HV 10k...")
        print("Beam current limits are", self.beam.beam_current.limits)

        print("Setting HV to 10kV...")
        self.beam.high_voltage.value = 10000
        print("Success.")

        min_current = self.beam.beam_current.limits.min
        max_current = self.beam.beam_current.limits.max

        has_elstar_column = self.test_helper.is_system([SystemFamily.HELIOS, SystemFamily.PLUTO, SystemFamily.VERIOS, SystemFamily.CRYOFIB])
        tolerance_in_percent = 25 if has_elstar_column else 10

        if self.test_helper.is_offline():
            self.__test_beam_current_setting(1e-12, tolerance_in_percent)
        else:
            current1 = min_current
            current2 = min_current + (max_current - min_current) * 0.2
            current3 = min_current + (max_current - min_current) * 0.5
            current4 = min_current + (max_current - min_current) * 0.8
            current5 = max_current

            self.__test_beam_current_setting(current1, tolerance_in_percent)
            self.__test_beam_current_setting(current2, tolerance_in_percent)
            self.__test_beam_current_setting(current3, tolerance_in_percent)
            self.__test_beam_current_setting(current4, tolerance_in_percent)
            self.__test_beam_current_setting(current5, tolerance_in_percent)

        print("Done.")

    def __test_beam_current_setting(self, value, tolerance_in_percent):
        print(f"Setting beam current to {value:.3e}...")
        self.beam.beam_current.value = value

        # Read the value back
        actual_value = self.beam.beam_current.value
        delta = np.abs(actual_value - value)
        delta_percent = np.round(delta/value*100, 0)
        print(f"    Actual value is {actual_value:.3e}, delta is {delta:.3e}, which is {delta_percent:.0f}%")

        self.assertLessEqual(delta_percent, tolerance_in_percent)

    def test_change_working_distance(self):
        self.test_helper.test_generic_setting(self.beam.working_distance, "working distance", [5e-3, 4e-3], number_precision=4)

    def test_set_working_distance_without_degauss(self):
        self.beam.working_distance.set_value_no_degauss(5e-3)
        self.assertAlmostEqual(5e-3, self.beam.working_distance.value, places=4)
        self.beam.working_distance.set_value_no_degauss(4e-3)
        self.assertAlmostEqual(4e-3, self.beam.working_distance.value, places=4)

    def test_change_scanning_resolution(self):
        self.test_helper.test_generic_setting(self.beam.scanning.resolution, "scanning resolution", ["1536x1024", "768x512"])

    def test_change_scanning_bit_depth(self):
        print("Changing bit depth to 16 bit...")
        self.beam.scanning.bit_depth = 16
        self.assertEqual(self.beam.scanning.bit_depth, 16)

        print("Changing bit depth to 8 bit...")
        self.beam.scanning.bit_depth = 8
        self.assertEqual(self.beam.scanning.bit_depth, 8)

    def test_change_horizontal_field_width(self):
        self.test_helper.test_generic_setting(self.beam.horizontal_field_width, "HFW", [30e-6, 50e-6], number_precision=6)

    def test_change_stigmator(self):
        half_positive_range = (self.beam.stigmator.limits.limits_x.max / 2)
        self.test_helper.test_generic_setting(self.beam.stigmator, "stigmator", [Point(half_positive_range, -half_positive_range), Point(-half_positive_range, half_positive_range), Point(0.0)])

    def test_change_beam_shift(self):
        half_positive_range = (self.beam.beam_shift.limits.limits_x.max / 2)
        self.test_helper.test_generic_setting(self.beam.beam_shift, "beam shift", [Point(half_positive_range, -half_positive_range), Point(-half_positive_range, half_positive_range), Point(0.0)], number_precision=6)

    def test_switch_scanning_modes(self):
        scanning_mode = self.beam.scanning.mode
        delay_between_switches = 0.5

        print("Switching to reduced area scan mode...")
        scanning_mode.set_reduced_area()
        self.assertEqual(ScanningMode.REDUCED_AREA, scanning_mode.value)
        time.sleep(delay_between_switches)

        print("Switching to line scan mode...")
        scanning_mode.set_line()
        self.assertEqual(ScanningMode.LINE, scanning_mode.value)
        time.sleep(delay_between_switches)

        print("Switching to spot scan mode...")
        scanning_mode.set_spot()
        self.assertEqual(ScanningMode.SPOT, scanning_mode.value)
        time.sleep(delay_between_switches)

        print("Switching to external scan mode...")
        scanning_mode.set_external()
        self.assertEqual(ScanningMode.EXTERNAL, scanning_mode.value)

        print("Switching to crossover scan mode...")
        scanning_mode.set_crossover()
        self.assertEqual(ScanningMode.CROSSOVER, scanning_mode.value)

        print("Switching to full frame scan mode...")
        scanning_mode.set_full_frame()
        self.assertEqual(ScanningMode.FULL_FRAME, scanning_mode.value)
        time.sleep(delay_between_switches)

        # unblanks beam (beam is blanked as a side-effect of scanning mode switching on some platforms)
        print("Unblanking beam...")
        self.microscope.beams.electron_beam.unblank()

        print("Done.")

    def test_beam_deceleration(self):
        """This test checks normal beam deceleration operation."""

        microscope = self.microscope

        print("Turning electron beam on...")
        microscope.beams.electron_beam.turn_on()

        # Retract easylift if inserted
        if microscope.specimen.manipulator.is_installed:
            microscope.specimen.manipulator.retract()

        # On WDB H1200 linking is allowed only in a narrow Z range
        if self.test_helper.is_system([SystemFamily.HELIOS_1200, SystemFamily.PLUTO]):
            p = StagePosition(z=0.00315)
            self.microscope.specimen.stage.absolute_move(p)

        print("Linking Z to WD...")
        microscope.imaging.start_acquisition()
        microscope.specimen.stage.link()
        microscope.imaging.stop_acquisition()

        print("Turning beam deceleration on...")
        microscope.beams.electron_beam.beam_deceleration.turn_on()

        # On Axia, stage bias is set to a fix value and is not controllable
        if not self.test_helper.is_system(SystemFamily.AXIA):
            # Calculate stage bias value at 1/3 and 2/3 of available range
            stage_bias = microscope.beams.electron_beam.beam_deceleration.stage_bias
            limits = stage_bias.limits
            stage_bias1 = round(limits.min + (limits.max - limits.min) * 0.3, 1)
            stage_bias2 = round(limits.min + (limits.max - limits.min) * 0.7, 1)
            # Try setting the two stage biases
            print(f"Setting stage bias to {stage_bias1} V...")
            microscope.beams.electron_beam.beam_deceleration.stage_bias.value = stage_bias1
            print(f"Setting stage bias to {stage_bias2} V...")
            microscope.beams.electron_beam.beam_deceleration.stage_bias.value = stage_bias2

        print("Turning beam deceleration off...")
        microscope.beams.electron_beam.beam_deceleration.turn_off()
        print("Done.")

    def test_unsupported_beam_deceleration(self):
        """This test checks that AutoScript behaves properly on systems without beam deceleration support."""

        microscope = self.microscope

        print("Testing beam deceleration operations on a system without beam deceleration support...")
        print("Turning electron beam on...")
        microscope.beams.electron_beam.turn_on()

        print("Linking Z to WD...")
        if microscope.specimen.stage.is_installed:
            microscope.imaging.start_acquisition()
            microscope.specimen.stage.link()
            microscope.imaging.stop_acquisition()

        with self.assertRaises(ApplicationServerException):
            print("Turning beam deceleration on, this must throw...")
            microscope.beams.electron_beam.beam_deceleration.turn_on()

        with self.assertRaises(ApplicationServerException):
            print("Setting stage bias to 1 kV, this must throw...")
            microscope.beams.electron_beam.beam_deceleration.stage_bias.value = 1000

        print("Done.")

    def test_change_optical_modes(self):
        """Cycle through all available optical modes"""
        microscope = self.microscope

        if self.test_helper.is_system([SystemFamily.QUANTA, SystemFamily.QUATTRO, SystemFamily.PRISMA, SystemFamily.AXIA]):
            self.skipTest(f"Skipping for {self.system_name} because it doesn't support optical modes.")

        mode_original = microscope.beams.electron_beam.optical_mode.value
        hv_original = microscope.beams.electron_beam.high_voltage.value
        print("Current mode is " + mode_original)
        print("Setting HV to 5k...")
        microscope.beams.electron_beam.high_voltage.value = 5000

        modes = microscope.beams.electron_beam.optical_mode.available_values
        for mode in modes:
            # Skip fib immersion for now
            if mode == "FIBImmersion":
                continue

            print("Switching to " + mode + "...")
            microscope.beams.electron_beam.optical_mode.value = mode
            print("Optical mode is is now " + microscope.beams.electron_beam.optical_mode.value)

        print("Restoring original microscope state...")
        microscope.beams.electron_beam.optical_mode.value = mode_original
        microscope.beams.electron_beam.high_voltage.value = hv_original
        print("Done.")

    def test_crossover_zoom(self):
        microscope = self.microscope
        print("Activating crossover mode...")
        microscope.beams.electron_beam.scanning.mode.set_crossover()
        microscope.beams.electron_beam.crossover_zoom.value = 0.62
        zoom = microscope.beams.electron_beam.crossover_zoom.value
        print("Zoom is", zoom)
        self.assertAlmostEqual(zoom, 0.62)
        limits = microscope.beams.electron_beam.crossover_zoom.limits
        print("Zoom limits are", limits)
        microscope.beams.electron_beam.scanning.mode.set_full_frame()
        print("Done.")

    def test_emission_current(self):
        print("Retrieving emission current...")
        emission_current = self.microscope.beams.electron_beam.emission_current.value
        print("Done.")
