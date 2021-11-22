from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
from matplotlib import pyplot as plot
import time
import unittest
import math


class TestsGeneral(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)

    def tearDown(self):
        pass

    def test_general1(self):
        """Simple test probing physical quantity readout and microscope image transfer."""

        # Read current electron beam HV and print it
        print("Reading current E-beam HV...")
        current_high_voltage = self.microscope.beams.electron_beam.high_voltage.value
        self.assertGreater(current_high_voltage, 0)
        print("Current E-beam HV is", current_high_voltage)

        # Get image from the active view
        print("Retrieving image from active view...")
        image = self.microscope.imaging.get_image()
        self.test_helper.assert_valid_image(image)
        print("Done.")

    def test_general2(self):
        """
        Advanced test based on system acceptance test (SAT) script.

        Effective SAT script logic is copied manually from the actual SAT script, which is included in the repository
        as Sources/Main.Python/user_application/AutoScript File With Examples.py. At the beginning of this test routine,
        environment is tweaked so the SAT script logic can proceed without unwanted effects, most importantly without
        showing blocking Matplotlib window.
        """

        microscope = self.microscope
        plot.ion()

        # Activate view 1
        print("Activating view 1...")
        microscope.imaging.set_active_view(1)
        print("Active view is now view %d" % microscope.imaging.get_active_view())

        # Turn electron beam on
        print("Turning electron beam on...")
        microscope.beams.electron_beam.turn_on()
        print("Electron beam is now %s" % ("on" if microscope.beams.electron_beam.is_on else "off"))

        # Check electron beam high voltage limits
        print("Checking electron beam high voltage limits...")
        print("Electron beam high voltage limits are %s" % microscope.beams.electron_beam.high_voltage.limits)

        # Adjust electron beam high voltage
        print("Setting electron beam high voltage value to 10 kV...")
        microscope.beams.electron_beam.high_voltage.value = 10e3
        print("Electron beam high voltage is now %.1f V" % microscope.beams.electron_beam.high_voltage.value)

        # Check available electron beam scanning resolutions
        print("Checking available electron beam scanning resolutions...")
        print("Available electron beam scanning resolutions are %s" % microscope.beams.electron_beam.scanning.resolution.available_values)

        # Adjust electron beam scanning resolution
        print("Setting electron beam scanning resolution to 1536x1024...")
        microscope.beams.electron_beam.scanning.resolution.value = ScanningResolution.PRESET_1536X1024
        print("Electron beam scanning resolution is now %s" % microscope.beams.electron_beam.scanning.resolution.value)

        # Check available detector types
        print("Checking available detector types...")
        available_detector_types = microscope.detector.type.available_values
        print("Available detector types are %s" % available_detector_types)

        # Filter available detector types to find basic ones and activates the first of them
        basic_detector_types = [d for d in available_detector_types if d in ['ETD', 'TLD', 'ICE']]
        if len(basic_detector_types) > 0:
            print("Activating %s detector..." % basic_detector_types[0])
            microscope.detector.type.value = basic_detector_types[0]
            print("Active detector type is now %s" % microscope.detector.type.value)

        # Adjust active detector contrast
        print("Adjusting active detector contrast...")
        microscope.detector.contrast.value = 0.75
        print("Active detector contrast is now %.2f%%" % (microscope.detector.contrast.value * 100))

        if microscope.specimen.stage.is_installed:
            # Ensure that bulk stage is homed
            print("Checking whether bulk stage is homed...")
            print("Bulk stage is %s" % ("homed" if microscope.specimen.stage.is_homed else "not homed"))
            if not microscope.specimen.stage.is_homed:
                print("Homing bulk stage...")
                microscope.specimen.stage.home()
                print("Bulk stage is now %s" % ("homed" if microscope.specimen.stage.is_homed else "not homed"))

            # Move bulk stage to absolute coordinates of X=2mm, Y=1mm, Z=4mm, R=0deg
            print("Moving bulk stage to absolute coordinates of X=2mm, Y=1mm, Z=4mm, R=0deg...")
            position = StagePosition(x=0.002, y=0.001, z=0.004, r=0)
            microscope.specimen.stage.absolute_move(position)
            print("Bulk stage position is now %s" % microscope.specimen.stage.current_position)

            # Rotate bulk stage compucentrically by 10 degrees
            print("Rotating bulk stage compucentrically by 10deg...")
            settings = MoveSettings(rotate_compucentric=True)
            position = StagePosition(r=math.radians(10))
            microscope.specimen.stage.relative_move(position, settings)
            print("Bulk stage position is now %s" % microscope.specimen.stage.current_position)

        # Start live acquisition
        print("Starting live acquisition...")
        microscope.imaging.start_acquisition()

        # Adjust working distance
        print("Electron beam working distance is %.3fmm" % (microscope.beams.electron_beam.working_distance.value * 1e3))
        print("Adjusting electron beam working distance by 0.5mm...")
        microscope.beams.electron_beam.working_distance.value += 0.5e-3
        print("Electron beam working distance is now %.3fmm" % (microscope.beams.electron_beam.working_distance.value * 1e3))

        # Link bulk stage to working distance
        if microscope.specimen.stage.is_installed:
            print("Linking bulk stage to working distance...")
            microscope.beams.electron_beam.turn_on()
            print("Bulk stage is now %s to working distance" % ("linked" if microscope.beams.electron_beam.is_on else "not linked"))

        # Stop live acquisition
        print("Stopping live acquisition...")
        microscope.imaging.stop_acquisition()

        # Take one image
        print("Grabbing complete frame with resolution of 1536x1024 and dwell time of 1 ms...")
        settings = GrabFrameSettings(resolution="1536x1024", dwell_time=1e-6)
        image = microscope.imaging.grab_frame(settings)
        print("Opening pop-up window with the grabbed frame... (please close it to continue)")
        plot.imshow(image.data, cmap='gray')
        plot.show()
        print("Pop-up window closed")

    def test_general3(self):
        """Advanced test containing essential operations from multiple categories."""

        microscope = self.microscope

        print("Setting microscope to initial state...")
        microscope.imaging.set_active_view(1)
        microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)
        microscope.beams.electron_beam.turn_on()
        self.assertTrue(self.microscope.beams.electron_beam.is_on)
        print("Success.")

        if microscope.specimen.stage.is_installed:
            print("Moving stage to 4 mm in Z axis...")
            microscope.specimen.stage.set_default_coordinate_system(CoordinateSystem.RAW)
            position = self.microscope.specimen.stage.current_position
            self.assertIsNotNone(position)
            microscope.specimen.stage.set_default_coordinate_system(CoordinateSystem.SPECIMEN)
            microscope.specimen.stage.absolute_move(StagePosition(z=0.004))
            position = self.microscope.specimen.stage.current_position
            position_delta = StagePosition(x=position.x)

            print("Current stage position is", position)
            if position.x == 0.003:
                position.x = 0.001
            else:
                position.x = 0.003

            print("Target stage position is", position)
            microscope.specimen.stage.absolute_move(position)
            position = self.microscope.specimen.stage.current_position
            print("New stage position is", position)

            position_delta.x -= position.x
            print("Moving x by %.3f m (relative move)" % position_delta.x)
            microscope.specimen.stage.relative_move(position_delta)
            position = self.microscope.specimen.stage.current_position
            print("New stage position is", position)

        # Read current electron beam HV and print it
        print("Reading current E-beam HV...")
        current_high_voltage = microscope.beams.electron_beam.high_voltage.value
        self.assertGreater(current_high_voltage, 0)
        print("Current E-beam HV is", current_high_voltage)

        # Toggle electron beam HV between 2 kV and 3 kV
        new_high_voltage = 3000.0 if current_high_voltage == 2000.0 else 2000.0
        print("Setting current HV to", new_high_voltage)
        microscope.beams.electron_beam.high_voltage.value = new_high_voltage

        # Get current electron beam HV and print it
        print("Reading current E-beam HV...")
        current_high_voltage = microscope.beams.electron_beam.high_voltage.value
        self.assertEqual(new_high_voltage, current_high_voltage)
        print("Current E-beam HV is", current_high_voltage)

        # Get electron beam HV limits and print them
        print("Reading E-beam HV limits...")
        hv_limits = microscope.beams.electron_beam.high_voltage.limits
        self.assertIsInstance(hv_limits, Limits)
        print("E-beam HV limits are", hv_limits)

        # Get e-beam beam shift value and print it
        print("Reading E-beam Beam Shift value...")
        current_beam_shift_value = microscope.beams.electron_beam.beam_shift.value
        self.assertIsInstance(current_beam_shift_value, Point)
        print("E-beam beam shift value is", current_beam_shift_value)

        # Gets e-beam beam shift limits and print them
        print("Reading E-beam Beam shift limits...")
        beam_shift_limits = microscope.beams.electron_beam.beam_shift.limits
        self.assertIsInstance(beam_shift_limits, Limits2d)
        print("E-beam beam shift limits are", beam_shift_limits)

        # Toggle e-beam beam shift value between 0 and half of the limits
        new_beam_shift_value = Point(0, 0)
        if current_beam_shift_value.x == 0:
            new_beam_shift_value.x = beam_shift_limits.limits_x.max / 2.0
            new_beam_shift_value.y = beam_shift_limits.limits_y.max / 2.0

        print("Setting new beam shift value to", new_beam_shift_value)
        microscope.beams.electron_beam.beam_shift.value = new_beam_shift_value
        current_beam_shift_value = self.microscope.beams.electron_beam.beam_shift.value
        self.test_helper.assert_points_almost_equal(new_beam_shift_value, current_beam_shift_value, 6)
        print("E-beam beam shift value is", current_beam_shift_value)

        print("Getting all available resolutions for E-Beam (using lists)...")
        available_values = self.microscope.beams.electron_beam.scanning.resolution.available_values
        self.assertGreater(len(available_values), 0)
        print("Available resolutions are:", available_values)

        print("Setting current view to 2...")
        microscope.imaging.set_active_view(2)
        self.assertEqual(2, self.microscope.imaging.get_active_view())

        print("Setting current view to 1...")
        microscope.imaging.set_active_view(1)
        self.assertEqual(1, self.microscope.imaging.get_active_view())

        print("Grabbing frame...")
        image1 = self.microscope.imaging.grab_frame(GrabFrameSettings(resolution="768x512", dwell_time=300e-9))
        self.test_helper.assert_valid_image(image1)

        print("Getting last frame...")
        image2 = self.microscope.imaging.get_image()
        self.test_helper.assert_valid_image(image2)

        print("Done.")
