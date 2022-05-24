from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
import os
import unittest
import time
import numpy as np


class TestsPatterningRtm(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)

    def tearDown(self):
        self.microscope.patterning.clear_patterns()

    def __prepare_for_patterning(self):
        beam_type = BeamType.ELECTRON
        target_view_number = 1
        target_imaging_device = ImagingDevice.ELECTRON_BEAM
        target_beam = self.microscope.beams.electron_beam

        if self.microscope.patterning.state is not PatterningState.IDLE:
            self.microscope.patterning.stop()

        self.microscope.imaging.set_active_view(target_view_number)
        self.microscope.imaging.set_active_device(target_imaging_device)
        self.microscope.patterning.set_default_beam_type(beam_type)
        self.microscope.patterning.set_default_application_file("None")

        target_beam.turn_on()
        target_beam.horizontal_field_width.value = 20e-6

        self.microscope.patterning.clear_patterns()
        self.microscope.imaging.grab_frame(GrabFrameSettings(resolution="768x512", dwell_time=1e-6))

    def __setup_regular_rtm_configuration(self):
        print("Preparing environment...")
        self.__prepare_for_patterning()

        print("Setting RTM and patterning modes...")
        self.__set_rtm_hires_mode_if_possible()
        self.microscope.patterning.mode = PatterningMode.PARALLEL

    def __create_rectangle_10s(self, x_offset: float = 0, y_offset: float = 0):
        rect = self.microscope.patterning.create_rectangle(x_offset, y_offset, 1e-6, 1e-6, 1e-6)
        rect.time = 10
        return rect

    def __set_rtm_hires_mode_if_possible(self):
        # First set low-res and after that try to set hi-res
        self.microscope.patterning.real_time_monitor.mode = RtmMode.LOW_RESOLUTION
        try:
            self.microscope.patterning.real_time_monitor.mode = RtmMode.HIGH_RESOLUTION
            print("Using High resolution mode.")
        except Exception:
            # Do nothing, hi-res is not supported on this tool
            print("High resolution mode is not supported on this tool, using Low resolution instead.")
            pass

    def __run_patterning_with_rtm(self, patterns_count_expected=1, positions_coordinate_system=RtmCoordinateSystem.IMAGE_PIXELS):
        # Use IMAGE_PIXELS by default so the test can be run for both low and high resolution solution
        position_settings = GetRtmPositionSettings(None, positions_coordinate_system)
        data_settings = GetRtmDataSettings()
        rtm_positions = []
        patterns_count_received = 0

        self.microscope.patterning.real_time_monitor.start()
        if self.microscope.patterning.state == PatterningState.IDLE:
            self.microscope.patterning.start()

        one_more_run = True

        try:
            while one_more_run:
                # If patterning is IDLE, lets read patterns for the last time. All the data should be present at this moment.
                if self.microscope.patterning.state == PatterningState.IDLE:
                    one_more_run = False

                patterns_count_received = 0
                rtm_data = self.microscope.patterning.real_time_monitor.get_data(data_settings)
                if len(rtm_positions) < len(rtm_data):
                    rtm_positions = self.microscope.patterning.real_time_monitor.get_positions(position_settings)

                if len(rtm_positions) > 0 and len(rtm_data) > 0 and rtm_data[0].values is not None:
                    for pattern in rtm_positions:
                        try:
                            data_set = next(x for x in rtm_data if x.pattern_id == pattern.pattern_id)
                        except Exception:  # ignore this exception, probably some pattern doesn't have any data yet
                            continue

                        # Check that any value is other than 0
                        if np.any(data_set.values > 1):
                            patterns_count_received += 1

                # If we received already the amount of data we wanted
                if patterns_count_received >= patterns_count_expected:
                    break

        except Exception as ex:
            print("Exception occurred:", ex)

        finally:

            self.microscope.patterning.real_time_monitor.stop()
            self.microscope.patterning.stop()

        return patterns_count_received

    def test_start_rtm_twice_correctly(self):
        self.__setup_regular_rtm_configuration()

        exception_occurred = False
        self.microscope.patterning.real_time_monitor.start()
        try:
            self.microscope.patterning.real_time_monitor.start()
        except Exception:
            exception_occurred = True
        finally:
            self.microscope.patterning.real_time_monitor.stop()

        self.microscope.patterning.real_time_monitor.stop()
        self.assertFalse(exception_occurred, "The exception on second RTM start should not occur, because the configuration was the same.")

    def test_start_rtm_twice_with_different_quad(self):
        self.__setup_regular_rtm_configuration()

        exception_occurred = False
        self.microscope.patterning.real_time_monitor.start()
        try:
            print("Setting different view...")
            view = self.microscope.imaging.get_active_view()
            view = (view % 4) + 1
            self.microscope.imaging.set_active_view(view)
            self.microscope.patterning.real_time_monitor.start()
        except Exception:
            exception_occurred = True
        finally:
            self.microscope.patterning.real_time_monitor.stop()

        self.microscope.patterning.real_time_monitor.stop()
        self.assertTrue(exception_occurred, "The exception on second RTM start should occur, because the configuration was different.")

    def test_start_rtm_twice_with_different_beam(self):
        self.__setup_regular_rtm_configuration()

        exception_occurred = False
        self.microscope.patterning.real_time_monitor.start()
        try:
            print("Setting different beam...")
            active_beam = self.microscope.imaging.get_active_device()
            active_beam = ImagingDevice.ION_BEAM if active_beam is ImagingDevice.ELECTRON_BEAM else ImagingDevice.ELECTRON_BEAM
            self.microscope.imaging.set_active_device(active_beam)
            self.microscope.patterning.real_time_monitor.start()
        except Exception:
            exception_occurred = True
        finally:
            self.microscope.patterning.real_time_monitor.stop()

        self.microscope.patterning.real_time_monitor.stop()
        self.assertTrue(exception_occurred, "The exception on second RTM start should occur, because the configuration was different.")

    def test_stop_rtm_when_not_started(self):
        print("Preparing environment...")
        self.__prepare_for_patterning()
        print("Stopping RTM ...")
        self.microscope.patterning.real_time_monitor.stop()  # it should not throw any exception

    def test_rtm_single_pattern_parallel(self):
        self.__setup_regular_rtm_configuration()
        print("Creating patterns...")
        self.__create_rectangle_10s()

        print("Starting patterning with RTM...")
        patterns_count_received = self.__run_patterning_with_rtm()
        print("Patterning finished.")

        self.assertEqual(1, patterns_count_received, "No valid data were captured during RTM acquisition.")

    def test_rtm_single_pattern_serial(self):
        self.__setup_regular_rtm_configuration()
        self.microscope.patterning.mode = PatterningMode.SERIAL
        print("Creating patterns...")
        self.__create_rectangle_10s()

        print("Starting patterning with RTM...")
        patterns_count_received = self.__run_patterning_with_rtm()
        print("Patterning finished.")

        self.assertEqual(1, patterns_count_received, "No valid data were captured during RTM acquisition.")

    def test_rtm_two_patterns_parallel(self):
        self.__setup_regular_rtm_configuration()
        print("Creating patterns...")
        self.__create_rectangle_10s()
        self.__create_rectangle_10s(2e-6)

        print("Starting patterning with RTM...")
        patterns_count_received = self.__run_patterning_with_rtm(2)
        print("Patterning finished.")

        self.assertEqual(2, patterns_count_received, "RTM data for 2 patterns were expected.")

    def test_rtm_two_patterns_serial(self):
        self.__setup_regular_rtm_configuration()
        self.microscope.patterning.mode = PatterningMode.SERIAL
        print("Creating patterns...")
        self.__create_rectangle_10s()
        self.__create_rectangle_10s(2e-6)

        print("Starting patterning with RTM...")
        patterns_count_received = self.__run_patterning_with_rtm(2)
        print("Patterning finished.")

        self.assertEqual(2, patterns_count_received, "RTM data for 2 patterns were expected.")

    def test_rtm_when_patterning_already_running(self):
        self.__setup_regular_rtm_configuration()
        print("Creating patterns...")
        self.__create_rectangle_10s()

        print("Starting patterning and waiting 2 seconds")
        self.microscope.patterning.start()
        time.sleep(2)

        self.assertEqual(PatterningState.RUNNING, self.microscope.patterning.state,
                         "Patterning is not running, even though it was started.")

        print("Starting patterning with RTM...")
        patterns_count_received = self.__run_patterning_with_rtm(1)
        print("Patterning finished.")

        self.assertEqual(1, patterns_count_received, "No valid data were captured during RTM acquisition.")

    def test_rtm_after_patterning_finished(self):
        self.__setup_regular_rtm_configuration()
        print("Creating patterns...")
        self.__create_rectangle_10s()

        print("Starting patterning with RTM...")
        patterns_count_received = self.__run_patterning_with_rtm(1)
        print("Patterning finished.")

        self.assertEqual(1, patterns_count_received, "No valid data were captured during RTM acquisition.")
        self.assertEqual(PatterningState.IDLE, self.microscope.patterning.state,
                         "Patterning is running, even though it was stopped.")

        print("Retrieving RTM data...")
        rtm_data = self.microscope.patterning.real_time_monitor.get_data(GetRtmDataSettings())

        rtm_positions = self.microscope.patterning.real_time_monitor.get_positions(GetRtmPositionSettings(coordinate_system=RtmCoordinateSystem.IMAGE_PIXELS))
        self.assertEqual(1, len(rtm_data), "No RTM data are present after patterning was finished.")
        self.assertEqual(1, len(rtm_positions), "No RTM positions are present after patterning was finished.")

    def test_rtm_after_patterns_were_deleted(self):
        self.__setup_regular_rtm_configuration()
        print("Creating patterns...")
        self.__create_rectangle_10s()

        print("Starting patterning with RTM...")
        patterns_count_received = self.__run_patterning_with_rtm(1)
        print("Patterning finished.")

        self.assertEqual(1, patterns_count_received, "No valid data were captured during RTM acquisition.")
        self.assertEqual(PatterningState.IDLE, self.microscope.patterning.state,
                         "Patterning is running, even though it was stopped.")

        print("Removing all patterns...")
        self.microscope.patterning.clear_patterns()

        print("Retrieving RTM data...")
        rtm_data = self.microscope.patterning.real_time_monitor.get_data(GetRtmDataSettings())
        rtm_positions = self.microscope.patterning.real_time_monitor.get_positions(GetRtmPositionSettings(coordinate_system=RtmCoordinateSystem.IMAGE_PIXELS))

        self.assertEqual(1, len(rtm_data), "No RTM data are present after patterning was finished.")
        self.assertEqual(1, len(rtm_positions), "No RTM positions are present after patterning was finished.")

    def test_rtm_high_resolution(self):
        self.__setup_regular_rtm_configuration()

        if self.microscope.patterning.real_time_monitor.mode != RtmMode.HIGH_RESOLUTION:
            self.skipTest("The high resolution mode is not supported on this tool.")

        print("Creating patterns...")
        self.__create_rectangle_10s()

        print("Starting patterning with RTM...")
        patterns_count_received = self.__run_patterning_with_rtm(1, RtmCoordinateSystem.DAC)
        print("Patterning finished.")

        self.assertEqual(1, patterns_count_received, "No valid data were captured during RTM acquisition.")

    def test_rtm_low_resolution(self):
        self.__setup_regular_rtm_configuration()
        print("Set low resolution mode.")
        self.microscope.patterning.real_time_monitor.mode = RtmMode.LOW_RESOLUTION

        print("Creating patterns...")
        self.__create_rectangle_10s()

        print("Starting patterning with RTM...")
        patterns_count_received = self.__run_patterning_with_rtm(1, RtmCoordinateSystem.IMAGE_PIXELS)
        print("Patterning finished.")

        self.assertEqual(1, patterns_count_received, "No valid data were captured during RTM acquisition.")

    def test_rtm_high_resolution_with_low_resolution_positions(self):
        self.__setup_regular_rtm_configuration()

        if self.microscope.patterning.real_time_monitor.mode != RtmMode.HIGH_RESOLUTION:
            self.skipTest("The high resolution mode is not supported on this tool.")

        print("Creating patterns...")
        self.__create_rectangle_10s()

        print("Starting patterning with RTM...")
        patterns_count_received = self.__run_patterning_with_rtm(1, RtmCoordinateSystem.IMAGE_PIXELS)
        print("Patterning finished.")

        self.assertEqual(1, patterns_count_received, "No valid data were captured during RTM acquisition.")

    def test_rtm_pattern_ids_parallel(self):
        self.__setup_regular_rtm_configuration()
        print("Creating patterns...")
        rect = self.__create_rectangle_10s()
        rect2 = self.__create_rectangle_10s(2e-6)

        print("Starting patterning with RTM...")
        patterns_count_received = self.__run_patterning_with_rtm(2)
        print("Patterning finished.")

        self.assertEqual(2, patterns_count_received, "Patterns count do not match.")
        self.assertEqual(PatterningState.IDLE, self.microscope.patterning.state,
                         "Patterning is running, even though it was stopped.")

        print("Retrieving RTM data...")
        rtm_data = self.microscope.patterning.real_time_monitor.get_data(GetRtmDataSettings())
        rtm_positions = self.microscope.patterning.real_time_monitor.get_positions(GetRtmPositionSettings(coordinate_system=RtmCoordinateSystem.IMAGE_PIXELS))

        self.assertEqual(2, len(rtm_data), "No RTM data are present after patterning was finished.")
        self.assertEqual(2, len(rtm_positions), "No RTM positions are present after patterning was finished.")

        print("Comparing pattern IDs...")
        self.assertEqual(rtm_data[0].pattern_id, rect.id, "Pattern ids do not match in RTM data.")
        self.assertEqual(rtm_data[1].pattern_id, rect2.id, "Pattern ids do not match in RTM data.")

        self.assertEqual(rtm_positions[0].pattern_id, rect.id, "Pattern ids do not match in RTM positions.")
        self.assertEqual(rtm_positions[1].pattern_id, rect2.id, "Pattern ids do not match in RTM positions.")

    def test_rtm_pattern_ids_serial(self):
        self.__setup_regular_rtm_configuration()
        self.microscope.patterning.mode = PatterningMode.SERIAL
        print("Creating patterns...")
        rect = self.__create_rectangle_10s()
        rect2 = self.__create_rectangle_10s(2e-6)

        print("Starting patterning with RTM...")
        patterns_count_received = self.__run_patterning_with_rtm(2)
        print("Patterning finished.")

        self.assertEqual(2, patterns_count_received, "Patterns count do not match.")
        self.assertEqual(PatterningState.IDLE, self.microscope.patterning.state,
                         "Patterning is running, even though it was stopped.")

        print("Retrieving RTM data...")
        rtm_data = self.microscope.patterning.real_time_monitor.get_data(GetRtmDataSettings())
        rtm_positions = self.microscope.patterning.real_time_monitor.get_positions(GetRtmPositionSettings(coordinate_system=RtmCoordinateSystem.IMAGE_PIXELS))

        self.assertEqual(2, len(rtm_data), "No RTM data are present after patterning was finished.")
        self.assertEqual(2, len(rtm_positions), "No RTM positions are present after patterning was finished.")

        print("Comparing pattern IDs...")
        self.assertEqual(rtm_data[0].pattern_id, rect.id, "Pattern ids do not match in RTM data.")
        self.assertEqual(rtm_data[1].pattern_id, rect2.id, "Pattern ids do not match in RTM data.")

        self.assertEqual(rtm_positions[0].pattern_id, rect.id, "Pattern ids do not match in RTM positions.")
        self.assertEqual(rtm_positions[1].pattern_id, rect2.id, "Pattern ids do not match in RTM positions.")
