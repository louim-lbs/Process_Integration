from autoscript_core.common import ApplicationServerException, ApiException
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import tempfile
import os
import unittest

'''
See terminology and imaging situations description in tests_imaging.py.
'''


class TestsImagingBigSnapshot(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)
        self.temporary_directory = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_grab_frame_to_disk(self):
        microscope = self.microscope
        imaging = microscope.imaging
        file_path = os.path.join(self.temporary_directory.name, "image.tiff")

        # Situation C
        print("Grabbing frame to disk with small resolution and unspecified preview resolution...")
        size = 1000
        settings = GrabFrameSettings(resolution=f"{size}x{size}", dwell_time=50e-9)
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        self.test_helper.assert_image_file(file_path, size * size, size, size, 8)
        expected_preview_width, expected_preview_height = self.__get_default_preview_resolution(size, size)
        self.test_helper.assert_image(preview, expected_preview_width, expected_preview_height, 8)
        print("Success.")

        # Situation C
        print("Grabbing frame to disk with small resolution and specified preview resolution...")
        size = 2000
        preview_size = 1000
        settings = GrabFrameSettings(resolution=f"{size}x{size}", preview_resolution=f"{preview_size}x{preview_size}", dwell_time=50e-9)
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        self.test_helper.assert_image_file(file_path, size * size, size, size, 8)
        self.test_helper.assert_image(preview, preview_size, preview_size, 8)
        print("Success.")

        # Situation D
        print("Grabbing frame to disk with large resolution and unspecified preview resolution...")
        size = 10000
        settings = GrabFrameSettings(resolution=f"{size}x{size}", dwell_time=25e-9)
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        self.test_helper.assert_image_file(file_path, size * size, size, size, 8)
        expected_preview_width, expected_preview_height = self.__get_default_preview_resolution(size, size)
        self.test_helper.assert_image(preview, expected_preview_width, expected_preview_height, 8)
        print("Success.")

        # Situation D
        print("Grabbing frame to disk with large resolution and specified preview resolution...")
        size = 10000
        preview_size = 1500
        settings = GrabFrameSettings(resolution=f"{size}x{size}", preview_resolution=f"{preview_size}x{preview_size}", dwell_time=25e-9)
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        self.test_helper.assert_image_file(file_path, size * size, size, size, 8)
        self.test_helper.assert_image(preview, preview_size, preview_size, 8)
        print("Success.")

        # Situation C
        print("Grabbing frame to disk without specifying resolution...")
        microscope.beams.electron_beam.scanning.dwell_time.value = 50e-9
        microscope.beams.electron_beam.scanning.resolution.value = ScanningResolution.PRESET_1536X1024
        settings = GrabFrameSettings()
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        self.test_helper.assert_image_file(file_path, 1536 * 1024, 1536, 1024, 8)
        self.test_helper.assert_image(preview, 1536, 1024)
        print("Success.")

        print("Grabbing frame to disk without specifying settings at all...")
        preview = imaging.grab_frame_to_disk(file_path)
        self.test_helper.assert_image_file(file_path, 1536 * 1024, 1536, 1024, 8)
        self.test_helper.assert_image(preview, 1536, 1024)
        print("Success.")

    def test_grab_frame_to_disk_with_reduced_area(self):
        imaging = self.microscope.imaging
        file_path = os.path.join(self.temporary_directory.name, "image.tiff")

        # Situation C
        print("Grabbing frame to disk with small resolution and specified reduced area...")
        ra_size = 0.2
        size = 1000
        settings = GrabFrameSettings(resolution=f"{size}x{size}", reduced_area=Rectangle(0, 0, ra_size, ra_size), dwell_time=50e-9)
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        self.test_helper.assert_image_file(file_path, size * size * pow(ra_size, 2), round(size * ra_size), round(size * ra_size), 8)
        self.test_helper.assert_image(preview, round(size * ra_size), round(size * ra_size), 8)
        print("Success.")

        # Situation C
        print("Grabbing frame to disk with small resolution, specified reduced area and preview resolution...")
        ra_size = 0.2
        size = 2000
        preview_size = 1000
        settings = GrabFrameSettings(resolution=f"{size}x{size}", preview_resolution=f"{preview_size}x{preview_size}",
                                     reduced_area=Rectangle(0, 0, ra_size, ra_size), dwell_time=50e-9)
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        self.test_helper.assert_image_file(file_path, size * size * pow(ra_size, 2), round(size * ra_size), round(size * ra_size), 8)
        self.test_helper.assert_image(preview, round(preview_size * ra_size), round(preview_size * ra_size), 8)
        print("Success.")

        # Situation C
        print("Grabbing frame to disk without specified resolution but with specified reduced area...")
        settings = GrabFrameSettings(reduced_area=Rectangle(0.3, 0.3, 0.2, 0.2))
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        print("Success.")

        # Situation D
        print("Grabbing frame to disk with large resolution and specified reduced area...")
        ra_size = 0.25
        size = 10000
        settings = GrabFrameSettings(resolution=f"{size}x{size}", reduced_area=Rectangle(0, 0, ra_size, ra_size), dwell_time=25e-9)
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        self.test_helper.assert_image_file(file_path, size * size * pow(ra_size, 2), round(size * ra_size), round(size * ra_size), 8)
        self.test_helper.assert_image(preview, round(768 * ra_size), round(768 * ra_size), 8)
        print("Success.")

        # Situation D
        print("Grabbing frame to disk with large resolution, specified reduced area and preview resolution...")
        ra_size = 0.25
        size = 10000
        preview_size = 1500
        settings = GrabFrameSettings(resolution=f"{size}x{size}", preview_resolution=f"{preview_size}x{preview_size}",
                                     reduced_area=Rectangle(0, 0, ra_size, ra_size), dwell_time=25e-9)
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        self.test_helper.assert_image_file(file_path, size * size * pow(ra_size, 2), round(size * ra_size), round(size * ra_size), 8)
        self.test_helper.assert_image(preview, round(preview_size * ra_size), round(preview_size * ra_size), 8)
        print("Success.")

    def test_grab_frame_to_disk_raw(self):
        microscope = self.microscope
        imaging = microscope.imaging
        file_path = os.path.join(self.temporary_directory.name, "raw_image.raw")

        print("Grabbing frame to disk with small resolution...")
        size = 1000
        settings = GrabFrameSettings(resolution=f"{size}x{size}", dwell_time=50e-9)
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.RAW, settings)
        self.test_helper.assert_image_file(file_path, size * size, size, size, 8)
        expected_preview_width, expected_preview_height = self.__get_default_preview_resolution(size, size)
        self.test_helper.assert_image(preview, expected_preview_width, expected_preview_height, 8)
        print("Success.")

        print("Grabbing frame to disk with large resolution...")
        size = 10000
        settings = GrabFrameSettings(resolution=f"{size}x{size}", dwell_time=25e-9)
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.RAW, settings)
        self.test_helper.assert_image_file(file_path, size * size, size, size, 8)
        expected_preview_width, expected_preview_height = self.__get_default_preview_resolution(size, size)
        self.test_helper.assert_image(preview, expected_preview_width, expected_preview_height, 8)
        print("Success.")

    def test_grab_frame_to_disk_16bit(self):
        imaging = self.microscope.imaging
        file_path = os.path.join(self.temporary_directory.name, "raw_image.tiff")

        if not self.test_helper.is_big_snapshot_16bit_supported:
            with self.assertRaisesRegex(ApplicationServerException, "not supported"):
                settings = GrabFrameSettings(resolution="1000x1000", dwell_time=50e-9, bit_depth=16)
                preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
            self.skipTest(f"Not supported on XT {self.test_helper.get_system_major_version()}, skipping")

        print("Grabbing frame to disk with small non standard resolution and 16-bit depth...")
        width, height = 1000, 700
        settings = GrabFrameSettings(resolution=f"{width}x{height}", dwell_time=50e-9, bit_depth=16)
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        self.test_helper.assert_image_file(file_path, 2 * width * height, width, height, 16)
        expected_preview_width, expected_preview_height = self.__get_default_preview_resolution(width, height)
        self.test_helper.assert_image(preview, expected_preview_width, expected_preview_height, 16)
        print("Success.")

        print("Grabbing frame to disk with large resolution and 16-bit depth...")
        width, height = 8000, 2000
        settings = GrabFrameSettings(resolution=f"{width}x{height}", dwell_time=25e-9, bit_depth=16)
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        self.test_helper.assert_image_file(file_path, 2 * width * height, width, height, 16)
        expected_preview_width, expected_preview_height = self.__get_default_preview_resolution(width, height)
        self.test_helper.assert_image(preview, expected_preview_width, expected_preview_height, 16)
        print("Success.")

    def test_grab_frame_to_disk_with_line_integration(self):
        imaging = self.microscope.imaging
        file_path = os.path.join(self.temporary_directory.name, "image.raw")

        if not self.test_helper.is_big_snapshot_line_integration_supported:
            with self.assertRaisesRegex(ApplicationServerException, "line integration"):
                settings = GrabFrameSettings(resolution="1000x1000", dwell_time=50e-9, bit_depth=8, line_integration=2)
                preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
            self.skipTest(f"Not supported on XT {self.test_helper.get_system_major_version()}, skipping")

        print("Grabbing frame to disk with small non standard resolution and line integration...")
        width, height = 1000, 700
        settings = GrabFrameSettings(resolution=f"{width}x{height}", dwell_time=50e-9, line_integration=2)
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.RAW, settings)
        self.test_helper.assert_image_file(file_path, width * height, width, height, 8)
        expected_preview_width, expected_preview_height = self.__get_default_preview_resolution(width, height)
        self.test_helper.assert_image(preview, expected_preview_width, expected_preview_height, 8)
        print("Success.")

        print("Grabbing frame to disk with large resolution and 16-bit depth...")
        width, height = 8000, 2000
        settings = GrabFrameSettings(resolution=f"{width}x{height}", dwell_time=25e-9, line_integration=2)
        preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.RAW, settings)
        self.test_helper.assert_image_file(file_path, width * height, width, height, 8)
        expected_preview_width, expected_preview_height = self.__get_default_preview_resolution(width, height)
        self.test_helper.assert_image(preview, expected_preview_width, expected_preview_height, 8)
        print("Success.")

    def test_grab_frame_to_disk_with_invalid_settings(self):
        imaging = self.microscope.imaging
        file_path = os.path.join(self.temporary_directory.name, "image.tiff")

        imaging.set_active_view(1)
        imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)

        print("Grabbing frame to disk with large resolution and scan interlacing > 1 must throw")
        with self.assertRaisesRegex(ApplicationServerException, "scan interlacing"):
            settings = GrabFrameSettings(resolution="9000x9000", scan_interlacing=2)
            preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        print("Success.")

        print("Grabbing frame to disk with large resolution and frame integration > 1 must throw")
        with self.assertRaisesRegex(ApplicationServerException, "frame integration"):
            settings = GrabFrameSettings(resolution="9000x9000", frame_integration=20)
            preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        print("Success.")

        print("Grabbing frame to disk with non-standard resolution and drift correction must throw")
        with self.assertRaisesRegex(ApplicationServerException, "frame integration"):
            settings = GrabFrameSettings(resolution="2000x2000", frame_integration=20, drift_correction=True)
            preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        print("Success.")

        print("Grabbing frame to disk with too large preview resolution must throw")
        with self.assertRaisesRegex(ApplicationServerException, "preview resolution"):
            settings = GrabFrameSettings(resolution="8000x8000", preview_resolution="6155x2000")
            preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        print("Success.")

        if not self.test_helper.is_ccd_installed:
            print("CCD camera is not installed, skipping this part of the test")
        else:
            print("Backing up active ImagingDevice and settings it to CCD")
            imaging.set_active_view(4)
            backed_up_device = imaging.get_active_device()
            imaging.set_active_device(ImagingDevice.CCD_CAMERA)
            print("Success.")

            print("Grabbing frame to disk with large image resolution and CCD camera active must throw")
            with self.assertRaisesRegex(ApplicationServerException, "supported only for"):
                settings = GrabFrameSettings(resolution="9000x9000")
                preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
            print("Success.")

            print("Restoring ImagingDevice")
            imaging.set_active_device(backed_up_device)
            imaging.set_active_view(1)
            print("Success.")

        if not self.test_helper.is_navcam_installed:
            print("NavCam is not installed, skipping this part of the test")
        else:
            print("Backing up active ImagingDevice and settings it to CCD")
            imaging.set_active_view(4)
            backed_up_device = imaging.get_active_device()
            imaging.set_active_device(ImagingDevice.NAV_CAM)
            print("Success.")

            print("Grabbing frame to disk with big image resolution and infrared camera (NavCam) active must throw")
            with self.assertRaisesRegex(ApplicationServerException, "supported only for"):
                settings = GrabFrameSettings(resolution="9000x9000")
                preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
            print("Success.")

            print("Restoring ImagingDevice")
            imaging.set_active_device(backed_up_device)
            imaging.set_active_view(1)
            print("Success.")

        print("Grabbing frame to disk with unknown format must throw")
        with self.assertRaisesRegex(ApiException, "file format"):
            settings = GrabFrameSettings(resolution="1000x1000")
            preview = imaging.grab_frame_to_disk(file_path, "UNKN", settings)
        print("Success.")

        print("Passing too large resolution must throw")
        with self.assertRaisesRegex(ApplicationServerException, "Maximum"):
            settings = GrabFrameSettings(resolution="65537x1000")
            preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        print("Success.")

        print("Passing too small resolution must throw")
        with self.assertRaisesRegex(ApplicationServerException, "Minimum"):
            settings = GrabFrameSettings(resolution="10x60")
            preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        print("Success.")

        print("Passing resolution in incorrect format must throw")
        with self.assertRaisesRegex(ApiException, "WIDTHxHEIGHT"):
            settings = GrabFrameSettings(resolution="Abc")
            preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        print("Success.")

        print("Passing preview resolution in incorrect format must throw")
        with self.assertRaisesRegex(ApiException, "WIDTHxHEIGHT"):
            # This tests situation C
            settings = GrabFrameSettings(resolution="1000x1000", preview_resolution="1x1x1")
            preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        print("Success.")

        print("Passing preview resolution in incorrect format must throw")
        with self.assertRaisesRegex(ApiException, "WIDTHxHEIGHT"):
            # This tests situation D
            settings = GrabFrameSettings(resolution="8000x8000", preview_resolution="300")
            preview = imaging.grab_frame_to_disk(file_path, ImageFileFormat.TIFF, settings)
        print("Success.")

    def test_grab_frame_with_nonstandard_resolution(self):
        imaging = self.microscope.imaging
        file_path = os.path.join(self.temporary_directory.name, "image.tiff")

        # Situation B.b
        print("Grabbing frame with resolution 4000x4000...")
        size = 4000
        settings = GrabFrameSettings(resolution=f"{size}x{size}", dwell_time=50e-9)
        image = imaging.grab_frame(settings)
        image.save(file_path)
        self.test_helper.assert_image_file(file_path, size * size, size, size, 8)
        self.test_helper.assert_image(image, size, size, 8)
        print("Done.")

    def test_grab_frame_with_nonstandard_resolution_16bit(self):
        imaging = self.microscope.imaging
        file_path = os.path.join(self.temporary_directory.name, "image.tiff")

        if not self.test_helper.is_big_snapshot_16bit_supported:
            with self.assertRaisesRegex(ApplicationServerException, "not supported"):
                settings = GrabFrameSettings(resolution="1000x1000", dwell_time=50e-9, bit_depth=16)
                image = imaging.grab_frame(settings)
            self.skipTest(f"Not supported on XT {self.test_helper.get_system_major_version()}, skipping")

        print("Grabbing frame to disk with small non standard resolution and 16-bit depth...")
        size = 1000
        settings = GrabFrameSettings(resolution=f"{size}x{size}", dwell_time=50e-9, bit_depth=16)
        image = imaging.grab_frame(settings)
        image.save(file_path)
        self.test_helper.assert_image_file(file_path, size * size, size, size, 16)
        self.test_helper.assert_image(image, size, size, 16)
        print("Success.")

    def test_grab_frame_with_invalid_settings(self):
        imaging = self.microscope.imaging

        imaging.set_active_view(1)
        imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)

        # Situation B.a
        print("Grabbing frame with resolution >6k must throw")
        with self.assertRaisesRegex(ApplicationServerException, "image to memory"):
            settings = GrabFrameSettings(resolution="10000x10000")
            image = imaging.grab_frame(settings)
        print("Success.")

        print("Grabbing frame with non-standard resolution and scan interlacing > 1 must throw")
        with self.assertRaisesRegex(ApplicationServerException, "scan interlacing"):
            settings = GrabFrameSettings(resolution="2000x2000", scan_interlacing=2)
            image = imaging.grab_frame(settings)
        print("Success.")

        print("Grabbing frame with non-standard resolution and frame_integration > 1 must throw")
        with self.assertRaisesRegex(ApplicationServerException, "frame integration"):
            settings = GrabFrameSettings(resolution="2000x2000", frame_integration=6)
            image = imaging.grab_frame(settings)
        print("Success.")

        print("Grabbing frame with non-standard resolution and drift correction must throw")
        with self.assertRaisesRegex(ApplicationServerException, "Drift"):
            settings = GrabFrameSettings(resolution="2000x2000", drift_correction=True)
            image = imaging.grab_frame(settings)
        print("Success.")

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

    def __get_default_preview_resolution(self, width, height) -> (int, int):
        # Note that reduced area is not factored in
        if max(width, height) <= 6144:
            return width, height
        return (width * 768 // height, 768) if width < height else (768, height * 768 // width)



