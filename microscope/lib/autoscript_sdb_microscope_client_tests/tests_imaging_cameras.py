from autoscript_core.common import ApplicationServerException, ApiException
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import tempfile
import os
import time
import unittest


class TestsImagingCameras(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)

    def tearDown(self):
        pass

    def test_imaging_with_nav_cam(self):
        if not self.test_helper.is_navcam_installed:
            self.skipTest("NavCam is not installed, skipping the test")

        microscope = self.microscope
        imaging = microscope.imaging

        print("Setting up view 3 for NavCam acquisition...")
        imaging.set_active_view(3)
        backed_up_device = imaging.get_active_device()
        imaging.set_active_device(ImagingDevice.NAV_CAM)
        print("Success.")

        print("Moving stage to NavCam position...")
        microscope.specimen.stage.move_to_device(ImagingDevice.NAV_CAM)
        print("Success.")

        print("Unpausing acquisition for 2 seconds...")
        imaging.start_acquisition()
        time.sleep(2)
        imaging.stop_acquisition()
        print("Success.")

        print("Getting image...")
        frame = imaging.get_image()
        self.assertNotEqual(None, frame, "No image was returned.")
        print("Success.")

        print("Trying to grab frame, which should throw an exception")
        with self.assertRaisesRegex(ApplicationServerException, "Cannot grab frame"):
            imaging.grab_frame()
        print("Success.")

        print("Moving back to electron beam sight position...")
        microscope.specimen.stage.move_to_device(ImagingDevice.ELECTRON_BEAM)
        print("Success.")

        print("Restoring original imaging device...")
        imaging.set_active_device(backed_up_device)
        imaging.set_active_view(1)
        print("Done.")

    def test_imaging_with_ccd(self):
        imaging = self.microscope.imaging

        if not self.test_helper.is_ccd_installed:
            self.skipTest("CCD camera was not detected. Skipping the test.")

        print("Setting up view 4 for CCD acquisition...")
        imaging.set_active_view(4)
        backed_up_device = imaging.get_active_device()
        imaging.set_active_device(ImagingDevice.CCD_CAMERA)
        print("Success.")

        print("Unpausing acquisition for 2 seconds...")
        imaging.start_acquisition()
        time.sleep(2)
        imaging.stop_acquisition()
        print("Success.")

        print("Getting image...")
        image = imaging.get_image()
        self.assertNotEqual(None, image, "No image was returned.")
        print("Success.")

        print("Trying to grab frame, which should throw an exception")
        with self.assertRaisesRegex(ApplicationServerException, "Cannot grab frame"):
            image = imaging.grab_frame()
        print("Success.")

        print("Restoring original imaging device...")
        imaging.set_active_device(backed_up_device)
        imaging.set_active_view(1)
        print("Done.")

    def test_imaging_with_optical_microscope(self):
        microscope = self.microscope
        imaging = microscope.imaging
        stage = microscope.specimen.stage

        if not self.test_helper.is_optical_microscope_installed:
            self.skipTest("Optical microscope not present, skipping")

        print("Setting up view 4 for OM acquisition...")
        imaging.set_active_view(4)
        backed_up_device = imaging.get_active_device()
        imaging.set_active_device(ImagingDevice.OPTICAL_MICROSCOPE)
        print("Success.")

        print("Moving stage to 52 deg tilt and OM sight position...")
        stage.absolute_move(StagePosition(t=math.radians(52)))
        stage.move_to_device(ImagingDevice.OPTICAL_MICROSCOPE)
        print("Success.")

        print("Unpausing acquisition for 2 seconds...")
        imaging.start_acquisition()
        time.sleep(2)
        imaging.stop_acquisition()
        print("Success.")

        print("Getting image...")
        image = imaging.get_image()
        assert_equal(image.metadata.acquisition.beam_type, "Infrared")
        print("Success.")

        print("Grabbing image with no settings...")
        image = imaging.grab_frame()
        assert_equal(image.metadata.acquisition.beam_type, "Infrared")
        print("Success.")

        print("Grabbing image with all allowed settings...")
        settings = GrabFrameSettings(resolution="1600x1200", bit_depth=16, line_integration=1, frame_integration=20,
                                     scan_interlacing=1, drift_correction=False)
        image = imaging.grab_frame(settings)
        assert_equal(image.metadata.acquisition.beam_type, "Infrared")
        print("Success.")

        print("Grabbing image with most common settings...")
        settings = GrabFrameSettings(frame_integration=8)
        image = imaging.grab_frame(settings)
        assert_equal(image.metadata.acquisition.beam_type, "Infrared")
        print("Success.")

        print("Grabbing frame with invalid settings must throw")
        with self.assertRaisesRegex(ApplicationServerException, "dwell time"):
            settings = GrabFrameSettings(dwell_time=100e-6)
            image = microscope.imaging.grab_frame(settings)
        with self.assertRaisesRegex(ApplicationServerException, "reduced area"):
            settings = GrabFrameSettings(reduced_area=Rectangle(0, 0, 0.1, 0.1))
            image = microscope.imaging.grab_frame(settings)
        with self.assertRaisesRegex(ApplicationServerException, "resolution"):
            settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_1536X1024)
            image = microscope.imaging.grab_frame(settings)
        with self.assertRaisesRegex(ApplicationServerException, "line integration"):
            settings = GrabFrameSettings(line_integration=4)
            image = microscope.imaging.grab_frame(settings)
        with self.assertRaisesRegex(ApplicationServerException, "scan interlacing"):
            settings = GrabFrameSettings(scan_interlacing=4)
            image = microscope.imaging.grab_frame(settings)
        with self.assertRaisesRegex(ApplicationServerException, "drift"):
            settings = GrabFrameSettings(frame_integration=4, drift_correction=True)
            image = microscope.imaging.grab_frame(settings)
        with self.assertRaisesRegex(ApplicationServerException, "depth"):
            settings = GrabFrameSettings(bit_depth=24)
            image = microscope.imaging.grab_frame(settings)

        print("Moving stage back to 0 deg tilt and E-beam sight position...")
        stage.move_to_device(ImagingDevice.ELECTRON_BEAM)
        stage.absolute_move(StagePosition(t=0))
        print("Success.")

        print("Restoring original imaging device...")
        imaging.set_active_device(backed_up_device)
        imaging.set_active_view(1)
        print("Done.")
