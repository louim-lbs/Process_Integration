from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import os
import time
import unittest


class TestsPatterning(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)
        self.system_name = self.microscope.service.system.name

    def tearDown(self):
        print("Deleting all patterns...")
        self.microscope.patterning.clear_patterns()
        print("Done.")

    def __prepare_for_patterning(self, beam_type=BeamType.ION):
        target_view_number = 1 if beam_type == BeamType.ELECTRON else 2
        target_imaging_device = ImagingDevice.ELECTRON_BEAM if beam_type == BeamType.ELECTRON else ImagingDevice.ION_BEAM
        target_beam = self.microscope.beams.electron_beam if beam_type == BeamType.ELECTRON else self.microscope.beams.ion_beam

        self.microscope.imaging.set_active_view(target_view_number)
        self.microscope.imaging.set_active_device(target_imaging_device)
        self.microscope.patterning.set_default_beam_type(beam_type)
        self.microscope.patterning.set_default_application_file("None")

        target_beam.turn_on()
        target_beam.horizontal_field_width.value = 20e-6

        self.microscope.patterning.clear_patterns()
        self.microscope.imaging.grab_frame(GrabFrameSettings(resolution="768x512", dwell_time=1e-6))

    def __create_and_mill_stream_pattern(self, beam_type=BeamType.ION):
        """Creates a stream pattern (defined by a numpy array) and mills it with ion beam."""

        print("Loading stream pattern definition from a stream file...")
        stream_file_path = os.path.dirname(__file__) + '\\resources\\frame.str'
        stream_pattern_definition = StreamPatternDefinition.load(stream_file_path)

        expected_points = numpy.array([[1000, 11922, 1e-06, 0], [32767, 11922, 1e-06, 0], [64535, 11922, 1e-06, 0],
                                       [64535, 53613, 1e-06, 1], [32767, 53613, 1e-06, 1], [1000, 53613, 1e-06, 1]],
                                      dtype=object)

        self.__assert_stream_pattern_points_equal(expected_points, stream_pattern_definition.points)

        print("Creating stream pattern...")
        self.microscope.patterning.set_default_application_file("None")
        p = self.microscope.patterning.create_stream(0, 0, stream_pattern_definition)
        print("Stream pattern created")

        if self.test_helper.is_offline():
            print("Skipping milling part for offline mode, because it halts tests for too long")
            return

        print("Milling the pattern...")
        self.microscope.patterning.run()
        print("Milling finished")

    def __assert_stream_pattern_points_equal(self, expected_array, actual_array):
        self.assertTupleEqual(expected_array.shape, actual_array.shape)

        for p in range(expected_array.shape[0]):
            for e in range(expected_array.shape[1]):
                self.assertAlmostEqual(expected_array[p][e], actual_array[p][e])

    def __get_bitmap_pattern_definition(self, size=10) -> BitmapPatternDefinition:
        print("Defining bitmap pattern with a numpy array...")
        bpd = BitmapPatternDefinition()
        bpd.points = numpy.zeros(shape=(size, size, 2), dtype=object)

        flags = 0
        i = 0
        for y in range(size):
            for x in range(size):
                bpd.points[y, x] = [i / (size * size), flags]
                i += 1

        print("Bitmap pattern definition created")
        return bpd

    def test_patterning1(self):
        # prepare view and reset image in pipeline
        self.__prepare_for_patterning(BeamType.ION)

        print("Adjusting FOV...")
        self.microscope.beams.ion_beam.horizontal_field_width.value = 20e-6
        self.assertEqual(20e-6, self.microscope.beams.ion_beam.horizontal_field_width.value)

        print("Creating patterns...")
        applications = self.microscope.patterning.list_all_application_files()
        self.microscope.patterning.set_default_application_file("Si")
        rect = self.microscope.patterning.create_rectangle(0, 0, 1e-6, 1e-6, 1e-6)
        line = self.microscope.patterning.create_line(-1e-6, -1e-6, -2e-6, -2e-6, 1e-6)
        circle = self.microscope.patterning.create_circle(3e-6, 3e-6, 2e-6, 1e-6, 5e-6)
        ccs = None
        rcs = None
        if any(x == "Si-ccs" for x in applications):
            self.microscope.patterning.set_default_application_file("Si-ccs")
            ccs = self.microscope.patterning.create_cleaning_cross_section(6e-6, 1e-6, 3e-6, 0.5e-6, 5e-6)
        if any(x == "Si-multipass" for x in applications):
            self.microscope.patterning.set_default_application_file("Si-multipass")
            rcs = self.microscope.patterning.create_regular_cross_section(-6e-6, 1e-6, 3e-6, 0.5e-6, 5e-6)

        print("Adjusting patterns...")
        rect.center_x = -8e-6
        line.length = 8e-6
        circle.outer_diameter = 5e-6
        rect.overlap_x = 0.6
        line.overlap = 0.8
        if ccs is not None:
            ccs.overlap_y = 0.65
        if rcs is not None:
            rcs.overlap_x = 0.763

        self.assertEqual(rect.beam_type, BeamType.ION)

        rect_center_x_target_dev = abs(-8e-6 - rect.center_x)
        circle_outer_diameter_target_dev = abs(5e-6 - circle.outer_diameter)

        eps = 1e-6
        self.assertLess(rect_center_x_target_dev, eps)
        self.assertLess(circle_outer_diameter_target_dev, eps)

        print("Starting patterning...")
        self.microscope.patterning.start()
        time.sleep(2)
        if self.microscope.patterning.state == PatterningState.RUNNING:
            print("Patterning is running...")
        else:
            print("Patterning is not running...")

        self.assertEqual(PatterningState.RUNNING, self.microscope.patterning.state)

        print("Pausing patterning...")
        self.microscope.patterning.pause()
        time.sleep(2)
        if self.microscope.patterning.state == PatterningState.PAUSED:
            print("Patterning is paused...")
        else:
            print("Patterning is not paused...")

        self.assertEqual(PatterningState.PAUSED, self.microscope.patterning.state)

        print("Resuming patterning...")
        self.microscope.patterning.resume()
        time.sleep(2)
        if self.microscope.patterning.state == PatterningState.RUNNING:
            print("Patterning is running...")
        else:
            print("Patterning is not running...")

        self.assertEqual(PatterningState.RUNNING, self.microscope.patterning.state)

        print("Stopping patterning...")
        self.microscope.patterning.stop()
        time.sleep(2)
        if self.microscope.patterning.state == PatterningState.IDLE:
            print("Patterning is stopped...")
        else:
            print("Patterning is not stopped...")

        self.assertEqual(PatterningState.IDLE, self.microscope.patterning.state)
        print("Done.")

    def test_stream_pattern_operations1(self):
        # Prepare view and reset image in pipeline
        self.__prepare_for_patterning(BeamType.ION)

        # Define stream pattern directly with a numpy array
        print("Defining stream pattern with a numpy array...")
        spd = StreamPatternDefinition()
        spd.points = numpy.array([[32768, 32768, 5.025e-06, 0]])
        spd.repeat_count = 1000
        print("Stream pattern definition created")

        # Create stream pattern according to the definition in the center of the view
        print("Creating stream pattern...")
        self.microscope.patterning.set_default_application_file("Si")
        p = self.microscope.patterning.create_stream(0, 0, spd)
        print("Stream pattern created")

        step_size = 4e-6
        x_deltas = [-1, 2, -1, -1, 2]
        y_deltas = [1, 0, -1, -1, 0]

        if self.test_helper.is_offline():
            print("Skipping the milling part in offline mode, because it halts tests for too long")
            return

        print("Milling pattern multiple times in different positions...")
        for i in range(len(x_deltas)):
            p.center_x += x_deltas[i] * step_size
            p.center_y += y_deltas[i] * step_size
            self.microscope.patterning.run()

        print("Done.")

    def test_stream_pattern_operations2(self):
        """Creates a stream pattern (defined by file) and mills it with ion beam."""

        self.__prepare_for_patterning(BeamType.ION)
        self.__create_and_mill_stream_pattern(BeamType.ION)

    def test_stream_pattern_operations3(self):
        """Creates a stream pattern (defined by file) and mills it with electron beam."""

        self.__prepare_for_patterning(BeamType.ELECTRON)
        self.__create_and_mill_stream_pattern(BeamType.ELECTRON)

    def test_stream_pattern_operations4(self):
        self.__prepare_for_patterning(BeamType.ION)

        print("Defining stream pattern with a numpy array...")
        spd = StreamPatternDefinition()
        spd.points = numpy.zeros(shape=(15, 4), dtype=object)

        dwell_time = 1e-6
        flags = 0
        i = 0
        for x in [22768, 27768, 32768, 37768, 42768]:
            for y in [27768, 32768, 37768]:
                spd.points[i] = [x, y, dwell_time, flags]
                i += 1

        spd.repeat_count = 1000
        print("Stream pattern definition created")

        print("Creating stream pattern...")
        p = self.microscope.patterning.create_stream(0, 0, spd)
        print("Stream pattern created")

        if self.test_helper.is_offline():
            print("Skipping the milling part in offline mode, because it halts tests for too long")
            return

        print("Milling the pattern...")
        self.microscope.patterning.run()
        print("Done.")

    def test_bitmap_pattern_from_file(self):
        self.__prepare_for_patterning(BeamType.ION)

        print("Loading bitmap pattern definition from a BMP file...")
        bmp_file_path = os.path.dirname(__file__) + '\\resources\\puzzle.bmp'
        bitmap_pattern_definition = BitmapPatternDefinition.load(bmp_file_path)

        print("Checking loaded bitmap size...")
        self.assertEqual(3, bitmap_pattern_definition.points.ndim)
        self.assertEqual(2, bitmap_pattern_definition.points.shape[2])
        self.assertEqual(375, len(bitmap_pattern_definition.points))
        self.assertEqual(375, bitmap_pattern_definition.height)
        self.assertEqual(379, len(bitmap_pattern_definition.points[1]))
        self.assertEqual(379, bitmap_pattern_definition.width)

        print("Creating bitmap pattern...")
        self.microscope.patterning.set_default_application_file("None")
        p = self.microscope.patterning.create_bitmap(0, 0, 3e-6, 3e-6, 1e-6, bitmap_pattern_definition)
        p.time = 1
        print("Bitmap pattern created")

        print("Milling the pattern...")
        self.microscope.patterning.run()
        print("Done.")

    def test_bitmap_pattern_from_numpy_array(self):
        self.__prepare_for_patterning(BeamType.ION)

        bpd = self.__get_bitmap_pattern_definition()

        print("Creating bitmap pattern...")
        p = self.microscope.patterning.create_bitmap(0, 0, 3e-6, 3e-6, 1e-6, bpd)
        p.time = 5
        print("Bitmap pattern created")

        if self.test_helper.is_offline():
            print("Skipping the milling part in offline mode, because it halts tests for too long")
            return

        # Helios 5 PFIB seems to have a bug in XTUI that is causing a deadlock between XT and XTUI while milling
        if self.test_helper.is_system(SystemFamily.HELIOS_PFIB_HYDRA) and self.test_helper.get_major_system_version() == 17:
            # TODO: Monitor this and remove when fixed in XTUI
            print("Skipping the milling part on Helios 5 PFIB Hydra to avoid hitting the XT-XTUI deadlock bug")
            return

        print("Milling the pattern...")
        self.microscope.patterning.run()
        print("Done.")

    def test_bitmap_pattern_change_size(self):
        self.__prepare_for_patterning(BeamType.ELECTRON)

        print("Creating bitmap pattern...")
        bpd = self.__get_bitmap_pattern_definition()
        p = self.microscope.patterning.create_bitmap(0, 0, 3e-6, 3e-6, 1e-6, bpd)
        print("Success.")

        original_width = p.width
        original_height = p.height

        print("Settings 'fix_aspect_ratio' to false...")
        p.fix_aspect_ratio = False

        print("Changing width and checking height...")
        p.width = original_width + 1e-6
        self.assertAlmostEqual(p.width, original_width + 1e-6, delta=1e-9, msg="Width should change, but it did not...")
        self.assertAlmostEqual(p.height, original_height, delta=1e-9, msg="Height should not change when changing width...")
        print("Success.")

        print("Changing height and checking width...")
        p.width = original_width
        p.height = original_height + 1e-6
        self.assertAlmostEqual(p.height, original_height + 1e-6, delta=1e-9, msg="Height should change, but it did not...")
        self.assertAlmostEqual(p.width, original_width, delta=1e-9, msg="Width should not change when changing height...")
        print("Success.")

        # Skip this part for offline mode where pattern property inter-dependencies are not simulated
        if not self.test_helper.is_offline():
            print("Settings 'fix_aspect_ratio' to true...")
            p.fix_aspect_ratio = True

            print("Changing width and checking height...")
            p.width = original_width + 1e-6
            self.assertAlmostEqual(p.width, original_width + 1e-6, delta=1e-9, msg="Width should change, but it did not...")
            self.assertNotAlmostEqual(p.height, original_height, delta=1e-9, msg="Height should change when changing width...")
            print("Success.")

            print("Changing height and checking width...")
            p.width = original_width
            p.height = original_height + 1e-6
            self.assertAlmostEqual(p.height, original_height + 1e-6, delta=1e-9, msg="Height should change, but it did not...")
            self.assertNotAlmostEqual(p.width, original_width, delta=1e-9, msg="Width should change when changing height...")

        print("Done.")

    def test_pattern_adjustments1(self):
        delay = 0.250

        print("Preparing for patterning...")
        self.__prepare_for_patterning(BeamType.ION)

        print("Creating patterns...")
        rectangle_pattern = self.microscope.patterning.create_rectangle(0, 0, 3e-6, 1e-6, 8e-6)
        ccs_pattern = self.microscope.patterning.create_cleaning_cross_section(0, -3e-6, 3e-6, 1e-6, 8e-6)
        rcs_pattern = self.microscope.patterning.create_regular_cross_section(0, +3e-6, 3e-6, 1e-6, 8e-6)

        time.sleep(delay)

        subtests = [("rectangle", rectangle_pattern), ("CCS", ccs_pattern), ("RCS", rcs_pattern)]

        for subtest in subtests:
            pattern_name = subtest[0]
            pattern = subtest[1]

            print("Testing %s pattern" % pattern_name)

            print("Adjusting %s pattern width..." % pattern_name)
            width_values = [5e-6, 3e-6]
            for v in width_values:
                pattern.width = v
                self.assertAlmostEqual(v, pattern.width, 6)
                time.sleep(delay)

            print("Adjusting %s pattern height..." % pattern_name)
            height_values = [2e-6, 1e-6]
            for v in height_values:
                pattern.height = v
                self.assertAlmostEqual(v, pattern.height, 6)
                time.sleep(delay)

            print("Adjusting %s pattern depth..." % pattern_name)
            depth_values = [10e-6, 8e-6]
            for v in depth_values:
                pattern.depth = v
                self.assertAlmostEqual(v, pattern.depth, 6)
                time.sleep(delay)

        print("Done.")

    def test_change_gas_flow(self):
        patterning = self.microscope.patterning

        print("Preparing environment...")
        self.__prepare_for_patterning(BeamType.ELECTRON)

        if "Pt dep" not in patterning.list_all_application_files():
            self.skipTest("Platinum deposition is not supported, skipping the test")

        print("Setting gas flow...")
        rectangle_pattern = self.microscope.patterning.create_rectangle(0, 0, 1e-6, 1e-6, 1e-6)
        rectangle_pattern.gas_type = "Pt dep"
        rectangle_pattern.gas_flow = [0.75]
        self.assertSequenceEqual(rectangle_pattern.gas_type, "Pt dep")
        self.assertSequenceEqual(rectangle_pattern.gas_flow, [0.75])

        print("Gas flow setting is", rectangle_pattern.gas_type, rectangle_pattern.gas_flow)
        print("Done.")

    def test_direct_pattern_property_access(self):
        print("Preparing environment...")
        self.__prepare_for_patterning(BeamType.ELECTRON)

        self.__test_direct_pattern_property_access_rectangle()

        # Quanta feg has problems with creating css, just ignore it, rcs, ccs don't make sense on XT 6 SEM anyway
        if not self.test_helper.is_system(SystemFamily.QUANTA_FEG):
            self.__test_direct_pattern_property_access_ccs()
            self.__test_direct_pattern_property_access_rcs()

        self.__test_direct_pattern_property_access_bitmap()
        self.__test_direct_pattern_property_access_circle()
        self.__test_direct_pattern_property_access_line()
        self.__test_direct_pattern_property_access_stream_file()

        self.microscope.patterning.clear_patterns()
        print("All done.")

    def __test_direct_pattern_property_access_general_pattern(self, p, application):
        microscope = self.microscope

        print("    Testing general pattern properties...")

        applications = microscope.patterning.list_all_application_files()
        if application in applications:
            target_value = application
            p.application_file = target_value
            self.assertEqual(p.application_file, target_value)

        target_value = BeamType.ELECTRON
        p.beam_type = target_value
        self.assertEqual(p.beam_type, target_value)

        target_value = 1e-6
        p.defocus = target_value
        self.assertAlmostEqual(p.defocus, target_value)

        target_value = 3.14 / 3
        p.rotation = target_value
        self.assertAlmostEqual(p.rotation, target_value)

        target_value = 1000
        p.pass_count = target_value
        self.assertEqual(p.pass_count, target_value)

        target_value = 1
        p.refresh_time = target_value
        self.assertAlmostEqual(p.refresh_time, target_value)

        target_value = 2e-6
        p.interaction_diameter = target_value
        self.assertAlmostEqual(p.interaction_diameter, target_value)

        target_value = 1e-9
        p.volume_per_dose = target_value
        self.assertAlmostEqual(p.volume_per_dose, target_value)

        target_value = 1e-6
        p.blur = target_value
        self.assertAlmostEqual(p.blur, target_value)

        target_value = 1e-9
        p.dose = target_value
        self.assertAlmostEqual(p.dose, target_value)

        self.assertEqual(p.enabled, True)
        p.enabled = False
        self.assertEqual(p.enabled, False)
        p.enabled = True

        pattern_id = p.id

        if "Pt dep" in applications:
            target_value = "Pt dep"
            p.gas_type = target_value
            self.assertEqual(p.gas_type, target_value)

        if self.test_helper.is_multichem_installed():
            multichem = microscope.gas.get_multichem()
            gases = multichem.list_all_gases()
            target_value = "+".join(gases)
            p.gas_type = target_value
            self.assertEqual(p.gas_type, target_value)
            target_value = [10, 20, 30, 40, 50]
            target_value = target_value[0:len(gases)]
            p.gas_flow = target_value
            self.assertEqual(p.gas_flow, target_value)

    def __test_direct_pattern_property_access_shape_pattern(self, p, application):
        self.__test_direct_pattern_property_access_general_pattern(p, application)

        print("    Testing shape pattern properties...")

        target_value = 2e-6
        p.dwell_time = target_value
        self.assertAlmostEqual(p.dwell_time, target_value)

        target_value = 10
        p.time = target_value
        self.assertAlmostEqual(p.time, target_value, 0)

    def __test_direct_pattern_property_access_rectangular_pattern(self, p, application):
        self.__test_direct_pattern_property_access_general_pattern(p, application)

        print("    Testing rectangular pattern properties...")

        target_value_x = 1e-6
        target_value_y = 2e-6
        p.center_x = target_value_x
        p.center_y = target_value_y
        self.assertAlmostEqual(p.center_x, target_value_x)
        self.assertAlmostEqual(p.center_y, target_value_y)

        target_value_x = 3e-6
        target_value_y = 2e-6
        p.width = target_value_x
        p.height = target_value_y
        self.assertAlmostEqual(p.width, target_value_x)
        self.assertAlmostEqual(p.height, target_value_y)

        target_value = 1e-6
        p.depth = target_value
        self.assertAlmostEqual(p.depth, target_value, 4)

        target_value = PatternScanDirection.LEFT_TO_RIGHT
        p.scan_direction = target_value
        self.assertEqual(p.scan_direction, target_value)

        target_value = PatternScanType.RASTER
        p.scan_type = target_value
        self.assertEqual(p.scan_type, target_value)

    def __test_direct_pattern_property_access_rectangular_pattern_with_overlap(self, p, application):
        self.__test_direct_pattern_property_access_rectangular_pattern(p, application)

        print("    Testing rectangular pattern with overlap properties...")

        target_value_x = 0.1
        target_value_y = 0.2
        p.overlap_x = target_value_x
        p.overlap_y = target_value_y
        self.assertAlmostEqual(p.overlap_x, target_value_x)
        self.assertAlmostEqual(p.overlap_y, target_value_y)

        target_value_x = 0.04e-6
        target_value_y = 0.06e-6
        p.pitch_x = target_value_x
        p.pitch_y = target_value_y
        self.assertAlmostEqual(p.pitch_x, target_value_x)
        self.assertAlmostEqual(p.pitch_y, target_value_y)

    def __test_direct_pattern_property_access_rectangle(self):
        print("Testing rectangle pattern...")
        p = self.microscope.patterning.create_rectangle(0, 0, 1e-6, 1e-6, 1e-6)
        self.__test_direct_pattern_property_access_rectangular_pattern_with_overlap(p, "Pt dep e")
        print("Done with rectangle.")

    def __test_direct_pattern_property_access_ccs(self):
        print("Testing ccs pattern...")
        p = self.microscope.patterning.create_cleaning_cross_section(-1e-6, 0, 2e-6, 1e-6, 1e-6)
        self.__test_direct_pattern_property_access_rectangular_pattern_with_overlap(p, "__skip__")
        print("Done with css.")

    def __test_direct_pattern_property_access_rcs(self):
        print("Testing rcs pattern...")
        p = self.microscope.patterning.create_regular_cross_section(-2e-6, 1e-6, 1e-6, 2e-6, 1.5e-6)
        self.__test_direct_pattern_property_access_rectangular_pattern_with_overlap(p, "__skip__")
        print("Done with css.")

    def __test_direct_pattern_property_access_bitmap(self):
        print("Testing bitmap pattern...")
        bmp_file_path = os.path.dirname(__file__) + '\\resources\\puzzle.bmp'
        bitmap_pattern_definition = BitmapPatternDefinition.load(bmp_file_path)
        p = self.microscope.patterning.create_bitmap(0, 0, 3e-6, 3e-6, 1e-6, bitmap_pattern_definition)

        self.__test_direct_pattern_property_access_rectangular_pattern(p, "Pt dep e")

        p.fix_aspect_ratio = True
        self.assertEqual(p.fix_aspect_ratio, True)
        print("Done with bitmap.")

    def __test_direct_pattern_property_access_circle(self):
        print("Testing circle pattern...")
        p = self.microscope.patterning.create_circle(3e-6, -2e-6, 1e-6, 0, 1e-6)

        self.__test_direct_pattern_property_access_shape_pattern(p, "Pt dep e")

        target_value_x = 1e-6
        target_value_y = 2e-6
        p.center_x = target_value_x
        p.center_y = target_value_y
        self.assertAlmostEqual(p.center_x, target_value_x)
        self.assertAlmostEqual(p.center_y, target_value_y)

        target_value = 1e-6
        p.depth = target_value
        self.assertAlmostEqual(p.depth, target_value, 4)

        target_value = PatternScanDirection.OUTER_TO_INNER
        p.scan_direction = target_value
        self.assertEqual(p.scan_direction, target_value)

        target_value = PatternScanType.SERPENTINE
        p.scan_type = target_value
        self.assertEqual(p.scan_type, target_value)

        target_value = 0.6
        p.overlap_r = target_value
        self.assertAlmostEqual(p.overlap_r, target_value)

        target_value = 0.5
        p.overlap_t = target_value
        self.assertAlmostEqual(p.overlap_t, target_value)
        print("Done with circle.")

    def __test_direct_pattern_property_access_line(self):
        print("Testing line pattern...")
        p = self.microscope.patterning.create_line(-2e-6, -1e-6, 2e-6, 4e-6, 2e-6)

        self.__test_direct_pattern_property_access_shape_pattern(p, "Pt dep e")

        target_value = 1e-6
        p.depth = target_value
        self.assertAlmostEqual(p.depth, target_value, 4)

        target_value = 4e-6
        p.start_x = target_value
        self.assertAlmostEqual(p.start_x, target_value, 0)

        target_value = -3e-6
        p.start_y = target_value
        self.assertAlmostEqual(p.start_y, target_value, 0)

        target_value = -4e-6
        p.end_x = target_value
        self.assertAlmostEqual(p.end_x, target_value, 0)

        target_value = 5e-6
        p.end_y = target_value
        self.assertAlmostEqual(p.end_y, target_value, 0)

        target_value = 5e-6
        p.length = target_value
        self.assertAlmostEqual(p.length, target_value, 0)

        target_value = 0.15
        p.overlap = target_value
        self.assertAlmostEqual(p.overlap, target_value, 0)

        target_value = 0.4e-6
        p.pitch = target_value
        self.assertAlmostEqual(p.pitch, target_value, 0)
        print("Done with line.")

    def __test_direct_pattern_property_access_stream_file(self):
        print("Testing stream file pattern...")
        spd = StreamPatternDefinition.load(os.path.dirname(__file__) + '\\resources\\frame.str')
        p = self.microscope.patterning.create_stream(-2e-6, 1e-6, spd)

        self.__test_direct_pattern_property_access_general_pattern(p, "Pt dep e")

        target_value_x = 1e-6
        target_value_y = 2e-6
        p.center_x = target_value_x
        p.center_y = target_value_y
        self.assertAlmostEqual(p.center_x, target_value_x)
        self.assertAlmostEqual(p.center_y, target_value_y)
        print("Done with stream file.")

