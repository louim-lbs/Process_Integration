from autoscript_core.common import ApplicationServerException, ApiException
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import tempfile
import os
import time
import unittest

'''
Terminology:
    - "Standard" resolution:      Preset from ScanningResolution enum, native to XT, all settings supported
    - "Non-standard" resolution:  Any resolution outside ScanningResolution presets up to 65536x65536, requires "BigSnapshot" acquisition technique and has limited settings 
    - "Large" resolution:         > 6k in X or Y, must be streamed to disk 
    - "Small" resolution:         <= 6k, can be represented as object in memory

Imaging situations:
    A. grab_frame() with standard resolution -> STANDARD acquisition
        a. Normal optics mode 
        b. Cross over mode, specifying settings is not allowed
    
    B. grab_frame() with non-standard resolution
        a. > 6k -> error
        b. < 6k -> BIG SNAPSHOT acquisition (settings are limited)
    
    C. grab_frame_to_disk() with standard resolution -> STANDARD acquisition
        - Returned image size is preview_resolution if specified in settings, otherwise original image resolution
    
    D. grab_frame_to_disk() with non-standard resolution -> BIG SNAPSHOT acquisition
        - Returned image size is preview_resolution if specified in settings, otherwise default size 768x768 rescaled to match original aspect ratio
'''


class TestsImaging(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)
        self.microscope.imaging.set_active_view(1)
        self.microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)

    def tearDown(self):
        pass

    def test_switch_views(self):
        delay_between_switches = 0.5

        for view_number in [2, 3, 4, 1]:
            self.microscope.imaging.set_active_view(view_number)
            self.assertEqual(view_number, self.microscope.imaging.get_active_view())
            time.sleep(delay_between_switches)

        print("Done.")

    def test_switch_imaging_devices(self):
        microscope = self.microscope

        microscope.imaging.set_active_view(1)

        backed_up_device = microscope.imaging.get_active_device()
        available_imaging_devices = [ImagingDevice.ELECTRON_BEAM]

        if microscope.beams.ion_beam.is_installed:
            available_imaging_devices.append(ImagingDevice.ION_BEAM)

        if self.test_helper.is_ccd_installed:
            available_imaging_devices.append(ImagingDevice.CCD_CAMERA)

        if self.test_helper.is_navcam_installed:
            available_imaging_devices.append(ImagingDevice.NAV_CAM)

        if self.test_helper.is_optical_microscope_installed:
            available_imaging_devices.append(ImagingDevice.OPTICAL_MICROSCOPE)

        for imaging_device in available_imaging_devices:
            print(f"Switching view 1 to {ImagingDevice.explain(imaging_device)}...")
            microscope.imaging.set_active_device(imaging_device)
            self.assertEqual(microscope.imaging.get_active_device(), imaging_device)
            print("Success.")
            time.sleep(2)

        print("Returning original imaging device...")
        microscope.imaging.set_active_device(backed_up_device)
        self.assertEqual(microscope.imaging.get_active_device(), backed_up_device)
        print("Done.")

    def test_switch_scanning_filters(self):
        microscope = self.microscope

        print("Switching to electrons, view 1...")
        microscope.imaging.set_active_view(1)
        microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)

        print("Setting scanning filter to integration, 4 frames...")
        microscope.imaging.scanning_filter.type = ScanningFilterType.INTEGRATION
        microscope.imaging.scanning_filter.number_of_frames = 4
        self.assertEqual(microscope.imaging.scanning_filter.type, ScanningFilterType.INTEGRATION)
        self.assertEqual(microscope.imaging.scanning_filter.number_of_frames, 4)

        if microscope.beams.ion_beam.is_installed:
            print("Switching to ions, view 2...")
            microscope.imaging.set_active_view(2)
            microscope.imaging.set_active_device(ImagingDevice.ION_BEAM)

            print("Setting scanning filter to averaging, 16 frames...")
            microscope.imaging.scanning_filter.type = ScanningFilterType.AVERAGING
            microscope.imaging.scanning_filter.number_of_frames = 16
            self.assertEqual(microscope.imaging.scanning_filter.type, ScanningFilterType.AVERAGING)
            self.assertEqual(microscope.imaging.scanning_filter.number_of_frames, 16)

            print("Switching back to electrons, view 1 and checking original filter state...")
            microscope.imaging.set_active_view(1)
            microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)
            self.assertEqual(microscope.imaging.scanning_filter.type, ScanningFilterType.INTEGRATION)
            self.assertEqual(microscope.imaging.scanning_filter.number_of_frames, 4)

            print("Cleaning up in ions...")
            microscope.imaging.set_active_view(2)
            microscope.imaging.set_active_device(ImagingDevice.ION_BEAM)
            microscope.imaging.scanning_filter.type = ScanningFilterType.NONE
            microscope.imaging.scanning_filter.number_of_frames = 1
            self.assertEqual(microscope.imaging.scanning_filter.type, ScanningFilterType.NONE)
            self.assertEqual(microscope.imaging.scanning_filter.number_of_frames, 1)

            print("Switching back to electrons, view 1...")
            microscope.imaging.set_active_view(1)
            microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)

        print("Setting scanning filter to live...")
        microscope.imaging.scanning_filter.type = ScanningFilterType.NONE
        microscope.imaging.scanning_filter.number_of_frames = 1
        self.assertEqual(microscope.imaging.scanning_filter.type, ScanningFilterType.NONE)
        self.assertEqual(microscope.imaging.scanning_filter.number_of_frames, 1)

        print("Done.")

    def test_start_stop_acquisition(self):
        self.microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)
        self.microscope.imaging.start_acquisition()
        time.sleep(1)
        self.microscope.imaging.stop_acquisition()
        print("Done.")

    def test_grab_frame_with_no_parameters(self):
        print("Grabbing frame...")
        frame = self.microscope.imaging.grab_frame()

        self.assertNotEqual(None, frame, "No image was returned.")
        print("Done.")

    def test_grab_frame_with_specific_bit_depth(self):
        if self.test_helper.is_offline:
            self.skipTest("Not simulated in offline mode, skipping")

        print("Grabbing 8-bit frame...")
        settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_768X512, dwell_time=1e-6, bit_depth=8)
        frame8 = self.microscope.imaging.grab_frame(settings)
        self.assertEqual(8, frame8.bit_depth)

        print("Grabbing 16-bit frame...")
        settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_768X512, dwell_time=1e-6, bit_depth=16)
        frame16 = self.microscope.imaging.grab_frame(settings)
        self.assertEqual(16, frame16.bit_depth)

        print("Done.")

    def test_grab_frame_with_reduced_area(self):
        print("Grabbing frame in reduced area...")

        reduced_area = Rectangle()
        reduced_area.left = 0.2
        reduced_area.top = 0.1
        reduced_area.width = 0.6
        reduced_area.height = 0.4

        settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_1536X1024, dwell_time=1e-6, reduced_area=reduced_area)

        image = self.microscope.imaging.grab_frame(settings)
        print("Scan area metadata from resulting image are " + str(image.metadata.scan_settings.scan_area))

        # Compare reduced area frame width with tolerance to overcome effects of different rounding on various systems
        if abs(image.width - 921) > 3:
            raise AssertionError("Reduced area frame width is much different than expected (%d != %d)" % (image.width, 921))

        # Compare reduced area frame height with tolerance to overcome effects of different rounding on various systems
        if abs(image.height - 410) > 3:
            raise AssertionError("Reduced area frame height is much different than expected (%d != %d)" % (image.height, 410))

        print("Grabbing frame in reduced area without specifying resolution...")
        self.microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)
        self.microscope.beams.electron_beam.scanning.resolution.value = ScanningResolution.PRESET_768X512
        settings = GrabFrameSettings(reduced_area=Rectangle(0.5, 0.5, 1.0 / 4, 1.0 / 4))
        image = self.microscope.imaging.grab_frame(settings)
        self.assertEqual(768 / 4, image.width)
        self.assertEqual(512 / 4, image.height)
        print("Done.")

    def test_grab_frame_in_crossover(self):
        print("Setting mode to crossover...")
        self.microscope.beams.electron_beam.scanning.mode.set_crossover()
        print("Success.")

        print("Grabbing a frame...")
        image = self.microscope.imaging.grab_frame()
        grabbed_in_crossover = image.metadata.optics.cross_over_on

        # TODO: have this fixed in XT
        # mpav: Temporarily skipped - this is a problem in XT, it was reported in January 2020,
        # reproduced on Helios by most probably also other systems (not tested).
        # The problem is that the 1st image taken after cross over is activated does not have cross over mode noted in metadata.
        # self.assertTrue(grabbed_in_crossover)
        print("Success.")

        print("Grabbing a frame with settings must throw...")
        with self.assertRaisesRegex(ApplicationServerException, "specific settings"):
            settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_1536X1024, dwell_time=1e-6, reduced_area=Rectangle(0.40, 0.40, 0.2, 0.2))
            image = self.microscope.imaging.grab_frame(settings)
        print("Success.")

        # Turn off crossover mode - cleanup
        print("Setting mode back to full frame...")
        self.microscope.beams.electron_beam.scanning.mode.set_full_frame()
        print("Done.")

    def test_grab_frame_and_load_image(self):
        print("Grabbing, saving and loading image in 8 bit...")
        self.__grab_and_load_image(8, 'Test8.tif', ImageDataEncoding.UNSIGNED)
        print("Success.")
        print("Grabbing, saving and loading image in 16 bit...")
        self.__grab_and_load_image(16, 'Test16.tif', ImageDataEncoding.UNSIGNED)
        print("Success.")

    def test_grab_frame_with_advanced_scan_settings(self):
        microscope = self.microscope

        microscope.imaging.set_active_view(1)
        microscope.imaging.set_active_device(imaging_device=ImagingDevice.ELECTRON_BEAM)

        print("Grabbing image with 8 integrated frames...")
        settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_3072X2048, bit_depth=8, dwell_time=100e-9, frame_integration=4)
        image = microscope.imaging.grab_frame(settings)
        self.test_helper.assert_image(image, 3072, 2048, 8)
        if not self.test_helper.is_offline:
            self.test_helper.assert_string_contains(image.metadata.metadata_as_ini, "Integrate=4")
        print("Success.")

        print("Grabbing image with scan interlacing set to 4...")
        settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_768X512, bit_depth=8, dwell_time=100e-9, scan_interlacing=4)
        image = microscope.imaging.grab_frame(settings)
        self.test_helper.assert_image(image, 768, 512, 8)
        if not self.test_helper.is_offline:
            self.test_helper.assert_string_contains(image.metadata.metadata_as_ini, "ScanInterlacing=4")
        print("Success.")

        print("Grabbing image with scan interlacing set to 4...")
        settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_768X512, bit_depth=8, dwell_time=100e-9, line_integration=4)
        image = microscope.imaging.grab_frame(settings)
        self.test_helper.assert_image(image, 768, 512, 8)
        if not self.test_helper.is_offline:
            self.test_helper.assert_string_contains(image.metadata.metadata_as_ini, "LineIntegration=4")
        print("Success.")

    def test_grab_frame_with_drift_correction(self):
        microscope = self.microscope

        print("Grabbing image with 8 drift corrected frames in electrons...")
        microscope.imaging.set_active_view(1)
        microscope.imaging.set_active_device(imaging_device=ImagingDevice.ELECTRON_BEAM)
        settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_768X512, dwell_time=500e-9, frame_integration=8, drift_correction=True)
        image = microscope.imaging.grab_frame(settings)
        if not self.test_helper.is_offline:
            self.test_helper.assert_image(image, 768, 512, 16)
            self.test_helper.assert_string_contains(image.metadata.metadata_as_ini, "Integrate=8")
        print("Success.")

        if microscope.beams.ion_beam.is_installed:
            print("Grabbing image with 12 drift corrected frames in ions...")
            microscope.imaging.set_active_view(2)
            microscope.imaging.set_active_device(imaging_device=ImagingDevice.ION_BEAM)
            settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_1536X1024, dwell_time=200e-9, bit_depth=16, frame_integration=12, drift_correction=True)
            image = microscope.imaging.grab_frame(settings)
            if not self.test_helper.is_offline:
                self.test_helper.assert_image(image, 1536, 1024, 16)
                self.test_helper.assert_string_contains(image.metadata.metadata_as_ini, "Integrate=12")
            microscope.imaging.set_active_view(1)
            print("Success.")

    def test_grab_frame_after_session_stopped(self):
        # Taking an image can fail on some systems when initiated immediately after microscope session is started.
        # Ending the session has inadvertent effect on microscope state - e.g. EDS pipeline gets disabled on systems with ChemiSEM.
        print("Stopping session...")
        self.microscope.service.autoscript.server.configuration.set_value("AutoScript.Session.Started", "False")
        time.sleep(2)

        print("Grabbing an image with resolution 1536x1024 and dwell time 1 ms...")
        settings = GrabFrameSettings(resolution="1536x1024", dwell_time=1e-6)
        image = self.microscope.imaging.grab_frame(settings)
        print("Image grabbed successfully, image width is", image.width)

    def test_grab_frame_to_disk_not_supported(self):
        # Note this test is not located in the big snapshot group because the whole group is meant to be skipped where b.s. is not supported
        print("On XT 6 big snapshot acquisition is not supported")

        if self.test_helper.is_system_version(6):
            file = "c:\\temp\\a.tmp"
            settings = GrabFrameSettings(resolution="10000x10000", dwell_time=50e-9)

            with self.assertRaisesRegex(ApplicationServerException, "not supported"):
                preview = self.microscope.imaging.grab_frame_to_disk(file, ImageFileFormat.RAW, settings)
            with self.assertRaisesRegex(ApplicationServerException, "not supported"):
                preview = self.microscope.imaging.grab_frame_to_disk(file, ImageFileFormat.TIFF, settings)

            settings = GrabFrameSettings(resolution="10000x10000", dwell_time=50e-9, reduced_area=Rectangle(0.3, 0.3, 0.2, 0.2))

            with self.assertRaisesRegex(ApplicationServerException, "not supported"):
                preview = self.microscope.imaging.grab_frame_to_disk(file, ImageFileFormat.RAW, settings)
            with self.assertRaisesRegex(ApplicationServerException, "not supported"):
                preview = self.microscope.imaging.grab_frame_to_disk(file, ImageFileFormat.TIFF, settings)

        print("Done.")

    def test_grab_frame_with_invalid_settings(self):
        imaging = self.microscope.imaging

        print("Grabbing frame with drift correction and not specified frame integration must throw")
        with self.assertRaisesRegex(ApplicationServerException, "frame_integration > 1"):
            settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_768X512, drift_correction=True)
            image = imaging.grab_frame(settings)
        print("Success.")

        print("Grabbing frame with drift correction and 8-bit depth must throw")
        with self.assertRaisesRegex(ApplicationServerException, "16-bit images"):
            settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_768X512, bit_depth=8, frame_integration=16, drift_correction=True)
            image = imaging.grab_frame(settings)
        print("Success.")

        print("Grabbing frame with drift correction and reduced area specified must throw")
        with self.assertRaisesRegex(ApplicationServerException, "requires full frame scanning"):
            settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_768X512, frame_integration=2, drift_correction=True,
                                         reduced_area=Rectangle(0.60, 0.60, 0.30, 0.30))
            image = imaging.grab_frame(settings)
        print("Success.")

        print("Grabbing multiple frames with drift correction must throw")
        with self.assertRaisesRegex(ApplicationServerException, "not yet implemented"):
            settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_768X512, frame_integration=2, drift_correction=True)
            images = imaging.grab_multiple_frames(settings)
        print("Success.")

        print("Passing settings out of range must throw")
        with self.assertRaisesRegex(ApplicationServerException, "must be"):
            settings = GrabFrameSettings(bit_depth=32)
            image = imaging.grab_frame(settings)
        with self.assertRaisesRegex(ApplicationServerException, "dwell"):
            settings = GrabFrameSettings(dwell_time=-1)
            image = imaging.grab_frame(settings)
        with self.assertRaisesRegex(ApplicationServerException, "out of"):
            settings = GrabFrameSettings(line_integration=0)
            image = imaging.grab_frame(settings)
        with self.assertRaisesRegex(ApplicationServerException, "out of"):
            settings = GrabFrameSettings(scan_interlacing=-1)
            image = imaging.grab_frame(settings)
        with self.assertRaisesRegex(ApplicationServerException, "out of"):
            settings = GrabFrameSettings(frame_integration=0)
            image = imaging.grab_frame(settings)
        print("Done.")

        print("Passing too large resolution must throw")
        with self.assertRaisesRegex(ApplicationServerException, "Maximum"):
            settings = GrabFrameSettings(resolution="65537x1000")
            images = imaging.grab_frame(settings)
        print("Success.")

        print("Passing too small resolution must throw")
        with self.assertRaisesRegex(ApplicationServerException, "Minimum"):
            settings = GrabFrameSettings(resolution="10x60")
            images = imaging.grab_frame(settings)
        print("Success.")

        print("Passing resolution in incorrect format must throw")
        with self.assertRaisesRegex(ApplicationServerException, "WIDTHxHEIGHT"):
            settings = GrabFrameSettings(resolution="Abc")
            images = imaging.grab_frame(settings)
        print("Success.")

    def test_grab_multiple_frames(self):
        microscope = self.microscope

        if self.test_helper.is_offline:
            self.skipTest("Skipping for offline because beam (in)compatibility is not respected in offline mode.")
            
        print("Setting up view 1...")
        primary_imaging_device = ImagingDevice.ELECTRON_BEAM
        microscope.imaging.set_active_view(1)
        microscope.imaging.set_active_device(primary_imaging_device)
        available_detector_types = microscope.detector.type.available_values

        print("Primary imaging device is", ImagingDevice.explain(primary_imaging_device))

        if DetectorType.ETD in available_detector_types:
            primary_detector_type = DetectorType.ETD
        elif DetectorType.T1 in available_detector_types:
            primary_detector_type = DetectorType.T1
        else:
            primary_detector_type = None
            self.skipTest("Suitable primary detector not found, skipping the test.")

        print("Primary detector is", primary_detector_type)

        # Secondary detector must be compatible with primary (=must allow simultaneous acquisition)
        if DetectorType.ICE in available_detector_types:
            secondary_detector_type = DetectorType.ICE
        elif DetectorType.CBS in available_detector_types:
            secondary_detector_type = DetectorType.CBS
        elif DetectorType.T2 in available_detector_types:
            secondary_detector_type = DetectorType.T2
        else:
            secondary_detector_type = primary_detector_type

        print("Secondary detector is", secondary_detector_type)

        # Secondary imaging device must be incompatible with electron beam acquisition
        if microscope.beams.ion_beam.is_installed:
            incompatible_imaging_device = ImagingDevice.ION_BEAM
        elif self.test_helper.is_ccd_installed:
            incompatible_imaging_device = ImagingDevice.CCD_CAMERA
        elif self.test_helper.is_navcam_installed:
            incompatible_imaging_device = ImagingDevice.NAV_CAM
        else:
            incompatible_imaging_device = None
            self.skipTest("Suitable secondary imaging device not found, skipping the test.")

        print("Incompatible imaging device is", ImagingDevice.explain(incompatible_imaging_device))

        # Set up views - 1 and 3 will be compatible, 2 and 4 incompatible
        print("Setting up views...")
        microscope.detector.type.value = primary_detector_type
        microscope.imaging.set_active_view(2)
        microscope.imaging.set_active_device(incompatible_imaging_device)
        microscope.imaging.set_active_view(3)
        microscope.imaging.set_active_device(primary_imaging_device)
        microscope.detector.type.value = secondary_detector_type
        microscope.imaging.set_active_view(4)
        microscope.imaging.set_active_device(incompatible_imaging_device)
        microscope.imaging.set_active_view(1)
        print("Success.")

        # Two views having ETD detectors in different modes would be incompatible
        if primary_detector_type == DetectorType.ETD and secondary_detector_type == DetectorType.ETD:
            print("Switching ETD to secondary electrons mode...")
            microscope.imaging.set_active_view(3)
            microscope.detector.mode.value = DetectorMode.SECONDARY_ELECTRONS
            microscope.imaging.set_active_view(1)
            microscope.detector.mode.value = DetectorMode.SECONDARY_ELECTRONS
            print("Success.")

        # Run test for resolution 768x512 and actual grab frame settings
        print("Grabbing multiple frames at resolution 768x512...")
        self.microscope.beams.electron_beam.scanning.resolution.value = "768x512"
        images = self.microscope.imaging.grab_multiple_frames()
        self.assertEqual(2, len(images))
        self.assertEqual(images[0].metadata.detectors[0].detector_type, primary_detector_type)
        self.assertEqual(images[1].metadata.detectors[0].detector_type, secondary_detector_type)
        self.test_helper.assert_image(images[0], 768, 512)

        # Run test for resolution 1536x1024 and grab frame settings supplied
        print("Grabbing multiple frames at resolution 1536x1024...")
        settings = GrabFrameSettings(resolution="1536x1024")
        images = self.microscope.imaging.grab_multiple_frames(settings)
        self.assertEqual(2, len(images))
        self.assertEqual(images[0].metadata.detectors[0].detector_type, primary_detector_type)
        self.assertEqual(images[1].metadata.detectors[0].detector_type, secondary_detector_type)
        self.test_helper.assert_image(images[0], 1536, 1024)

        print("Done.")

    def test_match_image_template(self):
        print("Locating template in image using HOG matcher...")
        lenna = self.test_helper.provide_lenna_gray8()
        face = self.test_helper.extract_lenna_face_region(lenna)
        lenna_adorned_image = AdornedImage(lenna)
        face_adorned_image = AdornedImage(face)

        match = self.microscope.imaging.match_template(lenna_adorned_image, face_adorned_image)
        self.assertAlmostEqual(300, match.center.x, places=0)
        self.assertAlmostEqual(300, match.center.y, places=0)
        self.assertGreater(match.score, 0.25)

        print("Done.")

    def test_set_image(self):
        print("Setting up initial situation...")
        microscope = self.microscope
        microscope.imaging.set_active_view(1)
        microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)
        microscope.beams.electron_beam.scanning.resolution.value = ScanningResolution.PRESET_768X512

        if microscope.beams.ion_beam.is_installed:
            microscope.imaging.set_active_view(2)
            microscope.imaging.set_active_device(ImagingDevice.ION_BEAM)
            microscope.beams.ion_beam.scanning.resolution.value = ScanningResolution.PRESET_1536X1024

        if microscope.service.autoscript.server.is_offline:
            self.__test_set_image_offline()
        else:
            self.__test_set_image_online()

        print("All done.")

    def __test_set_image_online(self):
        microscope = self.microscope

        if microscope.beams.ion_beam.is_installed:
            # This part of tests runs on a dual beam only
            print("Step 1: Take electron image in quad 1")
            microscope.imaging.set_active_view(1)
            settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_3072X2048, dwell_time=50e-9)
            electron_image = microscope.imaging.grab_frame(settings)
            print("Step 1: Success.")

            print("Step 2: Set the image to quad 2, it should change active beam from ion to electron")
            microscope.imaging.set_active_view(2)
            self.assertIs(microscope.imaging.get_active_device(), ImagingDevice.ION_BEAM)
            microscope.imaging.set_image(electron_image)
            self.assertEqual(microscope.imaging.get_active_device(), ImagingDevice.ELECTRON_BEAM)
            print("Step 2: Success.")

            print("Step 3: Get image back, it should have the original resolution and memento")
            image_got = microscope.imaging.get_image()
            self.assertEqual(image_got.width, 3072)
            self.assertAlmostEqual(image_got.metadata.optics.scan_field_of_view.width, electron_image.metadata.optics.scan_field_of_view.width)
            self.assertAlmostEqual(image_got.metadata.optics.scan_field_of_view.width, electron_image.metadata.optics.scan_field_of_view.width)
            print("Step 3: Success.")

            print("Step 4: Load 8-bit ion-beam image with databar from disk and set it to electron beam quad")
            print("Step 4: It should switch active beam to ion and cut off databar")
            ion_image = AdornedImage.load(self.test_helper.get_resource_path("ion_image_with_databar_3072x2188x8.tif"))
            microscope.imaging.set_active_view(1)
            microscope.imaging.set_image(ion_image)
            self.assertEqual(microscope.imaging.get_active_device(), ImagingDevice.ION_BEAM)
            image_got = microscope.imaging.get_image()
            self.assertEqual(image_got.width, ion_image.width)
            self.assertEqual(image_got.height, 2048)              # not 2188
            print("Step 4: Success.")

            print("Step 5: Load 16-bit electron-beam image with databar from disk and set it to ion beam quad")
            print("Step 5: It should switch active beam to electron and cut off databar")
            electron_image = AdornedImage.load(self.test_helper.get_resource_path("electron_image_with_databar_1536x1094x16.tif"))
            microscope.imaging.set_active_view(1)
            microscope.imaging.set_image(electron_image)
            self.assertEqual(microscope.imaging.get_active_device(), ImagingDevice.ELECTRON_BEAM)
            image_got = microscope.imaging.get_image()
            self.assertEqual(image_got.width, electron_image.width)
            self.assertEqual(image_got.height, 1024)  # not 1094
            print("Step 5: Success.")

        # This part of tests runs also on single beams
        print("SEM Step 1: Load 16-bit electron-beam image with databar from disk and set it to electron beam quad")
        print("SEM Step 1: It should cut off databar")
        electron_image = AdornedImage.load(self.test_helper.get_resource_path("electron_image_with_databar_1536x1094x16.tif"))
        microscope.imaging.set_image(electron_image)
        image_got = microscope.imaging.get_image()
        self.assertEqual(image_got.width, electron_image.width)
        self.assertEqual(image_got.height, 1024)  # not 1094
        print("SEM Step 1: Success.")

        print("SEM Step 2: Load 8-bit electron-beam image without databar from disk and set it to electron beam quad")
        electron_image = AdornedImage.load(self.test_helper.get_resource_path("electron_image_without_databar_768x512x8.tif"))
        microscope.imaging.set_image(electron_image)
        image_got = microscope.imaging.get_image()
        self.assertEqual(image_got.width, electron_image.width)
        self.assertEqual(image_got.height, electron_image.height)
        print("SEM Step 2: Success.")

        print("SEM Step 3: Load 8-bit image without memento in a non-FEI resolution 512x512")
        electron_image = AdornedImage.load(self.test_helper.get_resource_path("electron_image_without_databar_768x512x8.tif"))
        microscope.imaging.set_image(electron_image)
        image_got = microscope.imaging.get_image()
        self.assertEqual(image_got.width, electron_image.width)
        self.assertEqual(image_got.height, electron_image.height)
        print("SEM Step 3: Success.")

    def __test_set_image_offline(self):
        microscope = self.microscope

        print("Step 1: Get electron image from quad 1 prior to using set_image()")
        print("Step 1: It should return default Sal simulation image in some random resolution given by previous scripting activity")
        image_got = microscope.imaging.get_image()
        print(f"Step 1: Success. Resolution is {image_got.width}x{image_got.height}")

        print("Step 2: Do the same for ions in quad 2")
        microscope.imaging.set_active_view(2)
        image_got = microscope.imaging.get_image()
        print(f"Step 2: Success, resolution is {image_got.width}x{image_got.height}")

        print("Step 3: Load 8-bit ion-beam image with databar from disk and set it to 1st quad")
        print("Step 3: It should switch active beam to ions and store the image in simulation cache; databar will be cut off")
        ion_image = AdornedImage.load(self.test_helper.get_resource_path("ion_image_with_databar_3072x2188x8.tif"))
        microscope.imaging.set_active_view(1)
        microscope.imaging.set_image(ion_image)
        self.assertEqual(microscope.imaging.get_active_device(), ImagingDevice.ION_BEAM)
        print("Step 3: Success.")

        print("Step 4: Get the image, it should return the image in original resolution")
        image_got = microscope.imaging.get_image()
        self.assertEqual(image_got.width, 3072)
        self.assertEqual(image_got.height, 2048)  # not 2188
        print("Step 4: Success.")

        print("Step 5: Grab image without parameters; the simulated image should be resized to current ion beam scanning resolution")
        microscope.beams.ion_beam.scanning.resolution.value = ScanningResolution.PRESET_512X442
        image_grabbed = microscope.imaging.grab_frame()
        self.assertEqual(image_grabbed.width, 512)
        self.assertEqual(image_grabbed.height, 442)
        print("Step 5: Success.")

        print("Step 6: Load 16-bit electron-beam image with databar from disk and set it to ion beam quad.")
        print("Step 6: It should switch active beam to electrons and cut off databar part")
        microscope.imaging.set_active_view(2)
        microscope.imaging.set_active_device(ImagingDevice.ION_BEAM)
        electron_image = AdornedImage.load(self.test_helper.get_resource_path("electron_image_with_databar_1536x1094x16.tif"))
        microscope.imaging.set_image(electron_image)
        self.assertEqual(microscope.imaging.get_active_device(), ImagingDevice.ELECTRON_BEAM)
        image_got = microscope.imaging.get_image()
        self.assertEqual(image_got.width, electron_image.width)
        self.assertEqual(image_got.height, 1024)  # not 1094
        print("Step 6: Success.")

        print("Step 7: Grab 6k image; the simulated image should be resized to 6k resolution")
        settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_6144X4096, dwell_time=50e-9)
        image_grabbed = microscope.imaging.grab_frame(settings)
        self.assertEqual(image_grabbed.width, 6144)
        self.assertEqual(image_grabbed.height, 4096)
        print("Step 7: Success.")

    def __grab_and_load_image(self, bit_depth, filename, encoding):
        temporary_directory = tempfile.TemporaryDirectory()
        file_path = os.path.join(temporary_directory.name, filename)
        reduced_area = Rectangle(0.2, 0.1, 0.6, 0.4)

        settings = GrabFrameSettings(reduced_area=reduced_area, bit_depth=bit_depth)
        saved_image = self.microscope.imaging.grab_frame(settings)
        saved_image.save(file_path)

        loaded_image = AdornedImage.load(file_path)
        self.__evaluate_loaded_adorned_image(saved_image, loaded_image, bit_depth, encoding)
        temporary_directory.cleanup()

    def __evaluate_loaded_adorned_image(self, saved_image, loaded_image, bit_depth, encoding):
        self.test_helper.assert_image(loaded_image, loaded_image.width, loaded_image.height, loaded_image.bit_depth, loaded_image.encoding)
        self.assertEqual(saved_image.metadata.metadata_as_ini, loaded_image.metadata.metadata_as_ini)
        self.assertAlmostEqual(saved_image.metadata.optics.scan_field_of_view.height, loaded_image.metadata.optics.scan_field_of_view.height)
        self.assertAlmostEqual(saved_image.metadata.optics.scan_field_of_view.width, loaded_image.metadata.optics.scan_field_of_view.width)

