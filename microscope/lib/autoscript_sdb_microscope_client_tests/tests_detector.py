from autoscript_core.common import ApplicationServerException
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import time
import unittest


class TestsDetector(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)
        self.xt_major_version = int(self.microscope.service.system.version.split('.')[0])
        self.system_name = self.microscope.service.system.name
        self.__prepare_for_electron_detector_setup()

    def tearDown(self):
        pass

    def __prepare_for_electron_detector_setup(self):
        self.microscope.imaging.set_active_view(1)
        self.microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)

    def __link_z_to_fwd(self):
        microscope = self.microscope

        if not microscope.specimen.stage.is_homed:
            print("Homing stage...")
            self.microscope.specimen.stage.home()

        if not microscope.beams.electron_beam.is_on:
            print("Turning electron beam on...")
            microscope.beams.electron_beam.turn_on()

        eucentric_height = self.test_helper.get_system_eucentric_height()

        print("Linking Z to WD at eucentric height", eucentric_height)
        microscope.specimen.stage.unlink()
        microscope.beams.electron_beam.working_distance.value = eucentric_height
        microscope.imaging.start_acquisition()
        microscope.specimen.stage.link()
        microscope.imaging.stop_acquisition()

    def __test_setting_out_of_range(self, node, name, out_of_range_values):
        """Asserts that an exception is thrown when any of the given out of range values is used to set up the given node."""

        for value in out_of_range_values:
            exception_thrown = False
            try:
                print("Setting %s to %.2f..." % (name, value))
                node.value = value
            except ApplicationServerException:
                print("Exception raised properly")
                exception_thrown = True

            self.assertTrue(exception_thrown, "Exception was not thrown when an out of range value was used for " + name + " setting.")

    def __configure_segments(self, segment_settings):
        for segment_name, segment_polarity in segment_settings.items():
            self.microscope.detector.custom_settings.set_segment_polarity(segment_name, segment_polarity)

    def __set_custom_mode_and_segment_polarity(self, custom_mode, segment_name):
        print("Setting detector mode to '" + custom_mode + "'...")
        self.microscope.detector.mode.value = custom_mode
        print("Resetting segment polarity...")
        self.microscope.detector.custom_settings.reset_segments()

        print("Setting segment '" + segment_name + "' polarity to Positive...")
        self.microscope.detector.custom_settings.set_segment_polarity(segment_name, SegmentPolarity.POSITIVE)
        print("Checking polarity...")
        polarity = self.microscope.detector.custom_settings.get_segment_polarity(segment_name)
        self.assertEqual(polarity, SegmentPolarity.POSITIVE, "The segment polarity was not changed...")

        print("Setting segment '" + segment_name + "' polarity to Negative...")
        self.microscope.detector.custom_settings.set_segment_polarity(segment_name, SegmentPolarity.NEGATIVE)
        print("Checking polarity...")
        polarity = self.microscope.detector.custom_settings.get_segment_polarity(segment_name)
        self.assertEqual(polarity, SegmentPolarity.NEGATIVE, "The segment polarity was not changed...")

    def __assert_segment_configuration(self, segment_settings):
        for segment_name, expected_segment_polarity in segment_settings.items():
            actual_segment_polarity = self.microscope.detector.custom_settings.get_segment_polarity(segment_name)
            assert_message = "Segment %s has polarity %s instead of expected polarity %s" % (segment_name, SegmentPolarity.explain(actual_segment_polarity), SegmentPolarity.explain(expected_segment_polarity))
            self.assertEqual(expected_segment_polarity, actual_segment_polarity, assert_message)

    def __insert_retract_detector(self, detector_type):
        self.microscope.detector.type.value = detector_type
        retractable_detector = self.microscope.detector
        self.test_helper.test_insert_retract_device(retractable_detector, detector_type + " detector")

    def test_set_detector_type(self):
        detector = self.microscope.detector
        available_detectors = detector.type.available_values

        if DetectorType.EXTERNAL in available_detectors:
            print("Switching to External...")
            detector.type.value = DetectorType.EXTERNAL
            self.assertEqual(detector.type.value, DetectorType.EXTERNAL)
            print("Success.")

        if DetectorType.TLD in available_detectors:
            print("Switching to TLD...")
            detector.type.value = DetectorType.TLD
            self.assertEqual(detector.type.value, DetectorType.TLD)
            print("Success.")

        # Make sure we end up with some reasonable detector active so the subsequent tests will pass
        if DetectorType.ETD in available_detectors:
            print("Switching to ETD...")
            detector.type.value = DetectorType.ETD
            self.assertEqual(detector.type.value, DetectorType.ETD)
        elif DetectorType.T1 in available_detectors:
            print("Switching to T1...")
            detector.type.value = DetectorType.T1
            self.assertEqual(detector.type.value, DetectorType.T1)

        print("Done.")

    def test_set_detector_mode(self):
        detector = self.microscope.detector

        if DetectorType.ETD not in detector.type.available_values:
            self.skipTest("ETD not installed, skipping")

        print("Switching to ETD detector...")
        detector.type.value = DetectorType.ETD
        print("Success.")

        if DetectorMode.BACKSCATTER_ELECTRONS in detector.mode.available_values:
            print("Setting ETD mode to backscatter electrons...")
            detector.mode.value = DetectorMode.BACKSCATTER_ELECTRONS
            self.assertEqual(detector.mode.value, DetectorMode.BACKSCATTER_ELECTRONS)
            print("Success.")

        if DetectorMode.SECONDARY_ELECTRONS in detector.mode.available_values:
            print("Setting ETD mode to secondary electrons...")
            detector.mode.value = DetectorMode.SECONDARY_ELECTRONS
            self.assertEqual(detector.mode.value, DetectorMode.SECONDARY_ELECTRONS)
            print("Success.")

        print("Done.")

    def test_change_contrast_brightness(self):
        detector = self.microscope.detector

        print("Changing detector brightness...")
        self.test_helper.test_generic_setting(detector.brightness, "detector brightness", [0.25, 0.75, 0.50], number_precision=2)
        self.__test_setting_out_of_range(detector.brightness, "detector brightness", [-100, -1.50, 1.50, 100])
        print("Success.")

        print("Changing detector contrast...")
        self.test_helper.test_generic_setting(detector.contrast, "detector contrast", [0.25, 0.75, 0.50], number_precision=2)
        self.__test_setting_out_of_range(detector.contrast, "detector contrast", [-100, -1.50, 1.50, 100])
        print("Done.")

    def test_insert_retract_detectors(self):
        if self.test_helper.is_system([SystemFamily.QUANTA, SystemFamily.PRISMA]):
            # On Quanta, Quanta FEG and Prisma ABS and CBS are not retractable.
            # Not sure if this is always the case or if we just have test configurations modulated with non retractable versions.
            self.skipTest("ABS and CBS re not retractable, skipping")

        suitable_retractable_detectors = [DetectorType.ABS, DetectorType.CBS]
        available_retractable_detectors = self.microscope.detector.type.available_values
        retractable_detectors_to_test = set(suitable_retractable_detectors).intersection(available_retractable_detectors)

        if self.test_helper.is_system_version(10):
            # Helios G3 does support CBS, but not yet ABS.
            print("ABS is present, but not yet supported in SAL, removing from tests")
            retractable_detectors_to_test.remove(DetectorType.ABS)

        if len(retractable_detectors_to_test) == 0:
            self.skipTest("No retractable detector found, skipping")

        print("Retractable detectors found:", retractable_detectors_to_test)
        print("Linking Z to WD...")
        self.__link_z_to_fwd()
        print("Success.")

        for detector in retractable_detectors_to_test:
            self.__insert_retract_detector(detector)

        print("Done.")

    def test_etd_set_custom_settings(self):
        detector = self.microscope.detector

        if DetectorType.ETD not in detector.type.available_values:
            self.skipTest("ETD not installed, skipping")

        if DetectorMode.CUSTOM not in detector.mode.available_values:
            self.skipTest("Custom mode not available on ETD, skipping")

        print("Setting ETD to Custom mode...")
        self.microscope.detector.set_type_mode(DetectorType.ETD, DetectorMode.CUSTOM)
        self.assertEqual(detector.mode.value, DetectorMode.CUSTOM)
        print("Success.")

        print("Setting grid voltage to -100V...")
        detector.custom_settings.grid_voltage.value = -100
        self.assertEqual(detector.custom_settings.grid_voltage.value, -100)

        print("Done.")

    def test_tld_set_custom_settings(self):
        self.microscope.detector.set_type_mode(DetectorType.TLD, DetectorMode.CUSTOM)

        self.microscope.detector.custom_settings.suction_tube_voltage.value = 100
        self.assertEqual(100, self.microscope.detector.custom_settings.suction_tube_voltage.value)

        # On XT 6.x systems (NNS, Quanta, Quanta FEG, Versa3D) the TLD detector doesn't (yet) have the mirror voltage parameter
        if self.xt_major_version > 6:
            self.microscope.detector.custom_settings.mirror_voltage.value = -25
            self.assertEqual(-25, self.microscope.detector.custom_settings.mirror_voltage.value)

        print("Done.")

    def test_ice_set_custom_settings(self):
        self.microscope.detector.set_type_mode(DetectorType.ICE, DetectorMode.CUSTOM)

        self.microscope.detector.custom_settings.grid_voltage.value = 300
        self.assertEqual(300, self.microscope.detector.custom_settings.grid_voltage.value)

        self.microscope.detector.custom_settings.converter_voltage.value = -600
        self.assertEqual(-600, self.microscope.detector.custom_settings.converter_voltage.value)
        print("Done.")

    def test_stem3_set_custom_settings(self):
        microscope = self.microscope

        print("Setting up view 1...")
        microscope.imaging.set_active_view(1)
        microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)

        if DetectorType.STEM3 not in microscope.detector.type.available_values:
            self.skipTest("STEM3 not installed, skipping")

        print("Switching to STEM3 detector...")
        microscope.detector.type.value = DetectorType.STEM3

        if DetectorMode.CUSTOM not in microscope.detector.mode.available_values:
            self.skipTest("STEM3 does not have Custom mode, skipping the test")

        print("Switching STEM3 to custom mode...")
        microscope.detector.mode.value = DetectorMode.CUSTOM

        segment_settings1 = {'Angular1': SegmentPolarity.POSITIVE, 'Angular4': SegmentPolarity.NEUTRAL}

        print("Applying segment settings...")
        self.__configure_segments(segment_settings1)
        self.__assert_segment_configuration(segment_settings1)

        segment_settings2 = {'Angular1': SegmentPolarity.NEUTRAL, 'Angular4': SegmentPolarity.POSITIVE}

        print("Applying segment settings...")
        self.__configure_segments(segment_settings2)
        self.__assert_segment_configuration(segment_settings2)

        print("Done.")

    def test_stem3_list_segments(self):
        microscope = self.microscope

        print("Setting up view 1...")
        microscope.imaging.set_active_view(1)
        microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)

        if DetectorType.STEM3 not in microscope.detector.type.available_values:
            self.skipTest("STEM3 not installed, skipping")

        print("Getting STEM3 segment names...")
        microscope.detector.type.value = DetectorType.STEM3
        available_segments = self.microscope.detector.custom_settings.list_all_segments()
        self.assertSequenceEqual(available_segments, ['Angular0', 'Angular1', 'Angular2', 'Angular3', 'Angular4', 'Angular5'])
        print("Done.")

    def test_stem3_reset_segments(self):
        microscope = self.microscope

        print("Setting up view 1...")
        microscope.imaging.set_active_view(1)
        microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)

        if DetectorType.STEM3 not in microscope.detector.type.available_values:
            self.skipTest("STEM3 not installed, skipping")

        print("Switching to STEM3 detector...")
        microscope.detector.type.value = DetectorType.STEM3
        print("Success.")

        if DetectorMode.CUSTOM not in microscope.detector.mode.available_values:
            self.skipTest("STEM3 does not support Custom mode, skipping the test")

        print("Setting mode to Custom...")
        microscope.detector.mode.value = DetectorMode.CUSTOM
        print("Success.")

        print("Setting all available segments' polarity to positive...")
        segments = microscope.detector.custom_settings.list_all_segments()
        for segment in segments:
            microscope.detector.custom_settings.set_segment_polarity(segment, 1)

        print("Success.")
        print("Attempting to reset segments...")
        self.microscope.detector.custom_settings.reset_segments()
        for segment in segments:
            if self.microscope.detector.custom_settings.get_segment_polarity(segment) != 0:
                raise Exception("Not all segments are reset on Stem3 detector after reset_segments() has finished.")

        print("Done.")

    def test_stem3_plus_identification(self):
        """
        This test ensures that STEM3+ detector is using the proper identification string, 'STEM3_GMode'.

        This test is designed to prevent regression of errors caused by using incorrect identification strings, particularly 'Stem3Plus'.
        This test should be considered eligible only on tools equipped with STEM3+ detector because it looks up the detector among available detectors.
        """

        if "STEM3" not in self.microscope.detector.type.available_values:
            self.skipTest("STEM3 not installed, skipping")

        self.assertEqual("STEM3_GMode", DetectorType.STEM3_PLUS, "STEM3+ identification string does not match the corresponding DetectorType enumeration value.")

        is_stem3_plus_among_available_detectors = "STEM3_GMode" in self.microscope.detector.type.available_values
        self.assertTrue(is_stem3_plus_among_available_detectors, "STEM3+ is not listed under its proper identification string, 'STEM3_GMode'.")
        print("Done.")

    def test_stem3_plus_reset_segments(self):
        if "STEM3" not in self.microscope.detector.type.available_values:
            self.skipTest("STEM3 not installed, skipping")

        print("Setting detector type and mode...")
        self.microscope.detector.set_type_mode("STEM3_GMode", "Custom")
        segments = self.microscope.detector.custom_settings.list_all_segments()
        print("Setting all available segments' polarity to positive...")
        for segment in segments:
            if "Annular" in segment:
                self.microscope.detector.custom_settings.set_segment_polarity(segment, 1)

        print("Attempting to reset segments...")
        self.microscope.detector.custom_settings.reset_segments()
        all_segments_reset = True

        for segment in segments:
            if "Annular" in segment:
                if self.microscope.detector.custom_settings.get_segment_polarity(segment) != 0:
                    all_segments_reset = False

        self.assertTrue(all_segments_reset, "Not all segments are reset on Stem3+ detector after reset_segments() has finished.")
        print("Done.")

    def test_stem3_plus_reset_segments2(self):
        if "STEM3" not in self.microscope.detector.type.available_values:
            self.skipTest("STEM3 not installed, skipping")

        print("Setting detector type and mode...")
        self.microscope.detector.set_type_mode("STEM3_GMode", "Custom3")
        segments = self.microscope.detector.custom_settings.list_all_segments()
        print("Setting all available segments' polarity to positive...")
        for segment in segments:
            if "Angular" in segment:
                self.microscope.detector.custom_settings.set_segment_polarity(segment, 1)

        print("Attempting to reset segments...")
        self.microscope.detector.custom_settings.reset_segments()
        all_segments_reset = True

        for segment in segments:
            if "Angular" in segment:
                if self.microscope.detector.custom_settings.get_segment_polarity(segment) != 0:
                    all_segments_reset = False

        self.assertTrue(all_segments_reset, "Not all segments are reset on Stem3+ detector after reset_segments() has finished.")
        print("Done.")

    def test_stem3_plus_set_segments_in_custom_modes(self):
        if "STEM3" not in self.microscope.detector.type.available_values:
            self.skipTest("STEM3 not installed, skipping")

        print("Setting detector type...")
        self.microscope.detector.type.value = "STEM3_GMode"

        self.__set_custom_mode_and_segment_polarity(DetectorMode.CUSTOM, DetectorSegment.ANNULAR_0)
        self.__set_custom_mode_and_segment_polarity(DetectorMode.CUSTOM2, DetectorSegment.ANNULAR_0)
        self.__set_custom_mode_and_segment_polarity(DetectorMode.CUSTOM3, DetectorSegment.ANGULAR_0)
        print("Done.")

    def test_stem4_set_segments_in_custom_modes(self):
        if "STEM4" not in self.microscope.detector.type.available_values:
            self.skipTest("STEM4 not installed, skipping")

        print("Setting detector type to STEM4...")
        self.microscope.detector.type.value = "STEM4"

        self.__set_custom_mode_and_segment_polarity(DetectorMode.CUSTOM, DetectorSegment.ANNULAR_0)
        self.__set_custom_mode_and_segment_polarity(DetectorMode.CUSTOM2, DetectorSegment.ANNULAR_0)
        self.__set_custom_mode_and_segment_polarity(DetectorMode.CUSTOM3, DetectorSegment.ANGULAR_0)

        print("Setting segment polarity in unsupported custom mode, which should fail...")
        exception_thrown = False
        try:
            self.__set_custom_mode_and_segment_polarity(DetectorMode.CUSTOM4, DetectorSegment.ANNULAR_0)
        except Exception:
            print("Segment polarity was not changed as expected...")
            exception_thrown = True

        self.assertTrue(exception_thrown, "Exception was not thrown...")
        print("Done.")

    def test_stem4_set_different_mode_in_different_views(self):
        if "STEM4" not in self.microscope.detector.type.available_values:
            self.skipTest("STEM4 not installed, skipping")

        print("Setting Stem4 (mode Bright field) in view 1...")
        self.microscope.imaging.set_active_view(1)
        self.microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)
        self.microscope.detector.set_type_mode(DetectorType.STEM4, DetectorMode.BRIGHT_FIELD)

        print("Setting Stem4 (mode Dark field 1) in view 2...")
        self.microscope.imaging.set_active_view(2)
        self.microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)
        self.microscope.detector.set_type_mode(DetectorType.STEM4, DetectorMode.DARK_FIELD1)
        self.microscope.imaging.set_active_view(3)

        print("Setting Stem4 (mode HAADF) in view 1...")
        self.microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)
        self.microscope.detector.set_type_mode(DetectorType.STEM4, DetectorMode.ANGULAR)

        print("Checking detector type and mode in view 1...")
        self.microscope.imaging.set_active_view(1)
        self.assertEqual(DetectorType.STEM4, self.microscope.detector.type.value)
        self.assertEqual(DetectorMode.BRIGHT_FIELD, self.microscope.detector.mode.value)
        print("Done.")

        print("Checking detector type and mode in view 2...")
        self.microscope.imaging.set_active_view(2)
        self.assertEqual(DetectorType.STEM4, self.microscope.detector.type.value)
        self.assertEqual(DetectorMode.DARK_FIELD1, self.microscope.detector.mode.value)
        print("Done.")

        print("Checking detector type and mode in view 3...")
        self.microscope.imaging.set_active_view(3)
        self.assertEqual(DetectorType.STEM4, self.microscope.detector.type.value)
        self.assertEqual(DetectorMode.ANGULAR, self.microscope.detector.mode.value)
        print("Done.")

    def test_stem4_insert_retract(self):
        stem4 = "STEM4"
        available_retractable_detectors = self.microscope.detector.type.available_values
        if stem4 not in available_retractable_detectors:
            self.skipTest("STEM4 is not present on the system.")

        self.__link_z_to_fwd()

        print("Settings active detector to STEM4...")
        self.microscope.detector.type.value = stem4
        settings = DetectorInsertSettings(Stem4Positions.IN_LENS)
        print("Inserting STEM4...")
        self.microscope.detector.insert(settings)
        time.sleep(0.5)
        self.assertEqual(self.microscope.detector.state, RetractableDeviceState.INSERTED)
        print("STEM4 detector is in state %s" % self.microscope.detector.state)

        print("Retracting STEM4...")
        self.microscope.detector.retract()
        time.sleep(0.5)

        # Set the detector type again, because STEM4 is unset once it is retracted
        if self.microscope.detector.type.value != stem4:
            print("Settings active detector to STEM4 after it was unset by XT...")
            self.microscope.detector.type.value = stem4
        self.assertEqual(self.microscope.detector.state, RetractableDeviceState.RETRACTED)
        print("STEM4 detector is in state %s" % self.microscope.detector.state)

        print("Inserting STEM4 with no insert position, which should fail...")
        exception_thrown = False
        try:
            self.microscope.detector.insert()
        except Exception:
            print("Insertion failed as expected...")
            exception_thrown = True

        self.assertTrue(exception_thrown, "Inserting STEM4 with no insertion position succeeded, which is wrong...")

        try:
            # after STEM4 was inserted and retracted, the compustage may stay inserted, so try to retract it
            print("Retracting Compustage...")
            self.microscope.specimen.compustage.retract()
        except Exception:
            # silently ignore all exceptions that may have occurred during cleanup
            pass

        # mpav: Be nice to subsequent tests and reactivate bulk stage again.
        # The homing is a workaround for Helios 5 error, when the stage is unable to go to 0, 0 from Stem4 position because of safety restrictions.
        # I believe it is simulation problem only.
        print("Re-activating bulk stage...")
        self.microscope.specimen.stage.home([StageAxis.X, StageAxis.Y])
        self.microscope.specimen.stage.relative_move(StagePosition(x=0, y=0, r=0, t=0))
        print("Done.")

    def test_abs_reset_segments(self):
        microscope = self.microscope

        if DetectorType.ABS not in microscope.detector.type.available_values:
            self.skipTest("ABS detector is not installed, skipping the test")

        if self.xt_major_version == 10 or self.test_helper.is_system(SystemFamily.QUANTA):
            self.skipTest("ABS detector is not supported in SAL, skipping the test")

        print("Setting detector type and mode...")
        microscope.detector.set_type_mode("ABS", "Custom")
        segments = microscope.detector.custom_settings.list_all_segments()
        print("Setting all available segments' polarity to positive...")
        for segment in segments:
            microscope.detector.custom_settings.set_segment_polarity(segment, 1)

        print("Attempting to reset segments...")
        microscope.detector.custom_settings.reset_segments()
        all_segments_reset = True

        for segment in segments:
            if microscope.detector.custom_settings.get_segment_polarity(segment) != 0:
                all_segments_reset = False

        self.assertTrue(all_segments_reset, "Not all segments are reset on ABS detector after reset_segments() has finished.")
        print("Done.")

    def test_abs_reset_segments_on_unsupported_mode(self):
        microscope = self.microscope
        if DetectorType.ABS not in microscope.detector.type.available_values:
            self.skipTest("ABS detector is not installed, skipping the test")

        if self.xt_major_version == 10 or self.test_helper.is_system(SystemFamily.QUANTA):
            self.skipTest("ABS detector is not supported in SAL, skipping the test")

        print("Setting detector type and mode...")
        microscope.detector.set_type_mode("ABS", "All")
        segments = microscope.detector.custom_settings.list_all_segments()
        raised = False
        print("Attempting to reset segments...")
        try:
            microscope.detector.custom_settings.reset_segments()
        except Exception:
            raised = True

        self.assertTrue(raised,
                        "No exception was raised when attempting to reset segments on ABS detector in 'All' mode"
                        " although the mode application server exception was expected.")
        print("Done.")

    def test_reset_segments_on_unsupported_detector_type(self):
        print("Setting ETD detector type and SE mode...")
        self.microscope.detector.set_type_mode(DetectorType.ETD, DetectorMode.SECONDARY_ELECTRONS)

        print("Attempting to reset segments, this should throw...")
        with self.assertRaises(Exception):
            self.microscope.detector.custom_settings.reset_segments()

        print("Done.")

    def test_md_shutter_is_needed(self):
        print("Determining if MD shutter is needed...")
        self.__link_z_to_fwd()
        is_needed = self.microscope.detector.custom_settings.md_shutter.is_needed
        self.assertIs(type(is_needed), bool)
        print("Done.")

    def test_md_shutter_insert_retract(self):
        print("Inserting and retracting MD shutter...")
        self.__link_z_to_fwd()
        self.test_helper.test_insert_retract_device(self.microscope.detector.custom_settings.md_shutter, "Shutter detector")
        print("Done.")


