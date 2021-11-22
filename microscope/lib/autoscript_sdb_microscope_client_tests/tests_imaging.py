from autoscript_core.common import ApplicationServerException, ApiException
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import tempfile
import os
import time
import unittest


class TestsImaging(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)
        self.microscope.imaging.set_active_view(1)
        self.microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)
        self.temporary_directory = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temporary_directory.cleanup()
        pass

    def __grab_and_load_image(self, bit_depth, filename, encoding):
        file_path = os.path.join(self.temporary_directory.name, filename)
        reduced_area = Rectangle(0.2, 0.1, 0.6, 0.4)

        settings = GrabFrameSettings(reduced_area=reduced_area, bit_depth=bit_depth)
        saved_image = self.microscope.imaging.grab_frame(settings)
        saved_image.save(file_path)

        loaded_image = AdornedImage.load(file_path)
        self.__evaluate_loaded_adorned_image(saved_image, loaded_image, bit_depth, encoding)

    def __evaluate_loaded_adorned_image(self, saved_image, loaded_image, bit_depth, encoding):
        self.test_helper.assert_image(loaded_image, loaded_image.width, loaded_image.height, loaded_image.bit_depth, loaded_image.encoding)
        self.assertEqual(saved_image.metadata.metadata_as_ini, loaded_image.metadata.metadata_as_ini)
        self.assertAlmostEqual(saved_image.metadata.optics.scan_field_of_view.height, loaded_image.metadata.optics.scan_field_of_view.height)
        self.assertAlmostEqual(saved_image.metadata.optics.scan_field_of_view.width, loaded_image.metadata.optics.scan_field_of_view.width)

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

        if self.test_helper.is_ccd_installed():
            available_imaging_devices.append(ImagingDevice.CCD_CAMERA)

        if self.test_helper.is_navcam_installed():
            available_imaging_devices.append(ImagingDevice.NAV_CAM)

        if self.test_helper.is_optical_microscope_installed():
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

    def test_grab_frames_with_specific_bit_depth(self):
        print("Grabbing 8-bit frame...")
        settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_768X512, dwell_time=1e-6, bit_depth=8)
        frame8 = self.microscope.imaging.grab_frame(settings)
        self.assertEqual(8, frame8.bit_depth)

        print("Grabbing 16-bit frame...")
        settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_768X512, dwell_time=1e-6, bit_depth=16)
        frame16 = self.microscope.imaging.grab_frame(settings)
        self.assertEqual(16, frame16.bit_depth)

        print("Done.")

    def test_reduced_area_grab_frame(self):
        reduced_area = Rectangle()
        reduced_area.left = 0.2
        reduced_area.top = 0.1
        reduced_area.width = 0.6
        reduced_area.height = 0.4

        settings = GrabFrameSettings(resolution="1536x1024", dwell_time=1e-6, reduced_area=reduced_area)

        print("Grabbing frame in reduced area...")
        image = self.microscope.imaging.grab_frame(settings)

        print("Scan area metadata from resulting image are " + str(image.metadata.scan_settings.scan_area))

        # compares reduced area frame width with tolerance to overcome effects of different rounding on various systems
        if abs(image.width - 921) > 3:
            raise AssertionError("Reduced area frame width is much different than expected (%d != %d)" % (image.width, 921))

        # compares reduced area frame height with tolerance to overcome effects of different rounding on various systems
        if abs(image.height - 410) > 3:
            raise AssertionError("Reduced area frame height is much different than expected (%d != %d)" % (image.height, 410))

        print("Done.")

    def test_reduced_area_grab_frame_without_resolution(self):
        print("Preparing environment...")
        self.microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)
        self.microscope.beams.electron_beam.scanning.resolution.value = ScanningResolution.PRESET_768X512
        settings = GrabFrameSettings(reduced_area=Rectangle(0.5, 0.5, 1.0/4, 1.0/4))

        print("Grabbing frame...")
        frame = self.microscope.imaging.grab_frame(settings)

        print("Checking result...")
        self.assertEqual(768/4, frame.width)
        self.assertEqual(512/4, frame.height)

        print("Done.")

    def test_image_template_match(self):
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

    def test_grab_multiple_frames(self):
        microscope = self.microscope

        if self.test_helper.is_offline():
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

        # Secondary imaging device must me incompatible with electron beam acquisition
        if microscope.beams.ion_beam.is_installed:
            incompatible_imaging_device = ImagingDevice.ION_BEAM
        elif self.test_helper.is_ccd_installed():
            incompatible_imaging_device = ImagingDevice.CCD_CAMERA
        elif self.test_helper.is_navcam_installed():
            incompatible_imaging_device = ImagingDevice.NAV_CAM
        else:
            incompatible_imaging_device = None
            self.skipTest("Suitable secondary imaging device not found, skipping the test.")

        print("Incompatible imaging device is", ImagingDevice.explain(incompatible_imaging_device))

        # Set up views - 1 and 3 will be compatible, 2 and 4 incompatible
        print("Setting up views...")
        self.microscope.detector.type.value = primary_detector_type
        self.microscope.imaging.set_active_view(2)
        self.microscope.imaging.set_active_device(incompatible_imaging_device)
        self.microscope.imaging.set_active_view(3)
        self.microscope.imaging.set_active_device(primary_imaging_device)
        self.microscope.detector.type.value = secondary_detector_type
        self.microscope.imaging.set_active_view(4)
        self.microscope.imaging.set_active_device(incompatible_imaging_device)
        self.microscope.imaging.set_active_view(1)
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

    def test_crossover_grab_frame1(self):
        print("Setting mode to crossover...")
        self.microscope.beams.electron_beam.scanning.mode.set_crossover()

        print("Grabbing a frame...")
        image = self.microscope.imaging.grab_frame()
        grabbed_in_crossover = image.metadata.optics.cross_over_on

        # TODO: have this fixed in XT
        # mpav: temporarily skipped - this is a problem in XT, it was reported in January 2020
        # reproduced on Helios by most probably also other systems (not tested)
        # the problem is that the 1st image taken after cross over is activated does not have cross over mode noted in metadata
        # self.assertTrue(grabbed_in_crossover)

        # turn off crossover mode - cleanup
        self.microscope.beams.electron_beam.scanning.mode.set_full_frame()
        print("Done.")

    def test_crossover_grab_frame2(self):
        raised = False

        print("Creating GrabFrameSettings...")
        settings = GrabFrameSettings(resolution=ScanningResolution.PRESET_1536X1024, dwell_time=1e-6,
                                     reduced_area=Rectangle(0.40, 0.40, 0.2, 0.2))

        print("Setting mode to crossover...")
        self.microscope.beams.electron_beam.scanning.mode.set_crossover()

        try:
            print("Grabbing a frame with settings...")
            image = self.microscope.imaging.grab_frame(settings)
        except Exception:
            print("Exception raised...")
            raised = True

        if not raised:
            raise AssertionError("Exception is not raised when grabbing a frame with settings in crossover mode, "
                                 "although ApplicationServerException is expected.")

        # turn off crossover mode - cleanup
        self.microscope.beams.electron_beam.scanning.mode.set_full_frame()
        print("Done.")

    def test_grab_frame_to_disk_raw(self):
        if self.test_helper.is_system_version(6):
            # XT 6 does not support big snapshot
            print("Creating GrabFrameSettings...")
            settings = GrabFrameSettings(resolution="10000x10000", dwell_time=50e-9)
            file_path = os.path.join(self.temporary_directory.name, "raw_image.raw")

            print("Trying to grab big image on XT 6, should throw...")
            with self.assertRaises(ApiException):
                preview = self.microscope.imaging.grab_frame_to_disk(file_path, ImageFileFormat.RAW, settings)
            print("Done.")
            return

        print("Creating GrabFrameSettings...")
        settings = GrabFrameSettings(resolution="10000x10000", dwell_time=50e-9)
        file_path = os.path.join(self.temporary_directory.name, "raw_image.raw")

        print("Grabbing big image...")
        preview = self.microscope.imaging.grab_frame_to_disk(file_path, ImageFileFormat.RAW, settings)

        print("Checking image file presence...")
        file_exists = os.path.exists(file_path)
        self.assertTrue(file_exists, "The image file is missing on the hard drive.")

        expected_file_size = 100000000  # 100 MB = 10k x 10k image with 8 bit depth
        print("Checking image file size...")
        statinfo = os.stat(file_path)
        self.assertEqual(expected_file_size, statinfo.st_size, "The image is expected to be 100 MB, because the resolution was 10K x 10K with 1 byte per pixel.")

        expected_size = 768
        print("Checking preview resolution...")
        self.assertEqual(expected_size, preview.width)
        self.assertEqual(expected_size, preview.height)
        print("Done.")

    def test_grab_frame_to_disk_tiff(self):
        print("Creating GrabFrameSettings...")
        settings = GrabFrameSettings(resolution="10000x10000", dwell_time=50e-9)
        file_path = os.path.join(self.temporary_directory.name, "raw_image.tiff")

        print("Grabbing big image...")
        preview = self.microscope.imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)

        print("Checking image file presence...")
        file_exists = os.path.exists(file_path)
        self.assertTrue(file_exists, "The image file is missing on the hard drive.")

        expected_file_size = 100000000  # 100 MB = 10k x 10k image with 8 bit depth
        print("Checking image file size...")
        statinfo = os.stat(file_path)
        self.assertGreater(statinfo.st_size, expected_file_size, "The image is expected to be bigger than 100 MB, because the resolution was 10K x 10K with 1 byte per pixel and metadata has to be included.")

        expected_size = 768
        print("Checking preview resolution...")
        self.assertEqual(expected_size, preview.width)
        self.assertEqual(expected_size, preview.height)
        print("Done.")

    def test_grab_frame_with_reduced_area_to_disk_tiff(self):
        print("Creating GrabFrameSettings...")
        size = 0.25
        settings = GrabFrameSettings(resolution="10000x10000", dwell_time=50e-9, reduced_area=Rectangle(0.3, 0.3, size, size))
        file_path = os.path.join(self.temporary_directory.name, "raw_image.tiff")

        print("Grabbing big image...")
        preview = self.microscope.imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)

        print("Checking image file presence...")
        file_exists = os.path.exists(file_path)
        self.assertTrue(file_exists, "The image file is missing on the hard drive.")

        expected_file_size = 100000000 * (pow(size, 2))  # 100MB = 10k x 10k image with 8 bit depth, but multiplied by square size
        print("Checking image file size...")
        statinfo = os.stat(file_path)
        self.assertGreater(statinfo.st_size, expected_file_size, "The image is too small.")

        expected_size = 768
        print("Checking preview resolution...")
        self.assertEqual(expected_size * size, preview.width)
        self.assertEqual(expected_size * size, preview.height)
        print("Done.")

    def test_grab_frame_to_disk_with_16_bit(self):
        print("Creating GrabFrameSettings...")
        settings = GrabFrameSettings(resolution="10000x10000", dwell_time=50e-9, bit_depth=16)
        file_path = os.path.join(self.temporary_directory.name, "raw_image.raw")

        print("Grabbing big image...")
        exception_thrown = False
        try:
            preview = self.microscope.imaging.grab_frame_to_disk(file_path, ImageFileFormat.RAW, settings)
        except ApiException as ex:
            exception_thrown = True
            print("Exception thrown as expected.")

        self.assertTrue(exception_thrown, "The BigImage shouldn't support 16 bit depth.")
        print("Done.")

    def test_grab_frame_to_disk_with_unknown_format(self):
        print("Creating GrabFrameSettings...")
        settings = GrabFrameSettings(resolution="10000x10000")
        file_path = os.path.join(self.temporary_directory.name, "raw_image.raw")

        print("Grabbing big image...")
        exception_thrown = False
        try:
            preview = self.microscope.imaging.grab_frame_to_disk(file_path, "UNKN", settings)
        except ApiException as ex:
            exception_thrown = True
            print("Exception thrown as expected.")

        self.assertTrue(exception_thrown, "The BigImage shouldn't support unknown image formats.")
        print("Done.")

    def test_grab_big_snapshot(self):
        print("Creating GrabFrameSettings...")
        settings = GrabFrameSettings(resolution="1000x1000", dwell_time=50e-9)

        print("Grabbing big image...")
        image = self.microscope.imaging.grab_frame(settings)

        print("Checking image parameters...")
        self.assertEqual(1000, image.width)
        self.assertEqual(1000, image.height)
        self.assertEqual(8, image.bit_depth)
        self.assertEqual(ImageDataEncoding.UNSIGNED, image.encoding)
        print("Done.")

    def test_grab_big_snapshot_with_reduced_area(self):
        print("Creating GrabFrameSettings...")
        settings = GrabFrameSettings(resolution="1000x1000", dwell_time=50e-9, reduced_area=Rectangle(0.4, 0.4, 0.2, 0.2))

        print("Grabbing big image...")
        image = self.microscope.imaging.grab_frame(settings)

        print("Checking image parameters...")
        self.assertEqual(200, image.width)
        self.assertEqual(200, image.height)
        self.assertEqual(8, image.bit_depth)
        self.assertEqual(ImageDataEncoding.UNSIGNED, image.encoding)
        print("Done.")

    def test_imaging_with_nav_cam(self):
        if not self.test_helper.is_navcam_installed():
            self.skipTest("NavCam is not installed, skipping the test")

        imaging = self.microscope.imaging

        print("Setting up view 3 for NavCam acquisition...")
        imaging.set_active_view(3)
        backed_up_device = imaging.get_active_device()
        imaging.set_active_device(ImagingDevice.NAV_CAM)
        print("Success.")

        print("Moving stage to NavCam position...")
        # Changing sight beam is not yet on official API
        self.microscope.service.autoscript.server.configuration.set_value("Positioning.SightBeam", "NavCam")
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

        print("Trying to grab_frame, which should throw an exception.")
        with self.assertRaises(Exception):
            imaging.grab_frame()
        print("Exception thrown as expected.")

        print("Moving back to primary sight position...")
        self.microscope.service.autoscript.server.configuration.set_value("Positioning.SightBeam", "Primary")
        print("Success.")

        print("Restoring original ImagingDevice...")
        imaging.set_active_device(backed_up_device)
        imaging.set_active_view(1)
        print("Done.")

    def test_imaging_with_ccd(self):
        imaging = self.microscope.imaging

        if not self.test_helper.is_ccd_installed():
            self.skipTest("CCD camera was not detected. Skipping the test.")

        print("Backing up active ImagingDevice and settings it to CCD...")
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
        frame = imaging.get_image()
        self.assertNotEqual(None, frame, "No image was returned.")
        print("Success.")

        print("Trying to grab_frame, which should throw an exception.")
        with self.assertRaises(Exception):
            imaging.grab_frame()

        print("Exception thrown as expected.")
        print("Restoring ImagingDevice...")
        imaging.set_active_device(backed_up_device)
        imaging.set_active_view(1)
        print("Done.")

    def test_grab_and_load_image8(self):
        print("Grabbing, saving and loading image in 8 bit...")
        self.__grab_and_load_image(8, 'Test8.tif', ImageDataEncoding.UNSIGNED)
        print("Done.")

    def test_grab_and_load_image16(self):
        print("Grabbing, saving and loading image in 16 bit...")
        self.__grab_and_load_image(16, 'Test16.tif', ImageDataEncoding.UNSIGNED)
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

    def test_grab_frame_after_start_session(self):
        # Taking an image can fail on some systems when initiated immediately after microscope session is started.
        # The C# wrapper of this test will run this function 40s after the previous test has finished.
        # In this period, the AutoScript server will stop the microscope session with a built-in "clean up" mechanism.
        # The grab_frame call below will start up the session again and test if the acquisition gets aborted.
        print("Grabbing an image with resolution 1536x1024 and dwell time 1 ms...")
        settings = GrabFrameSettings(resolution="1536x1024", dwell_time=1e-6)
        image = self.microscope.imaging.grab_frame(settings)
        print("Image grabbed successfully, image width is", image.width)
