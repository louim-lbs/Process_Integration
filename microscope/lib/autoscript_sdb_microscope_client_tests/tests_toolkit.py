from autoscript_core.common import ApplicationServerException
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
from autoscript_toolkit.template_matchers import *
import autoscript_toolkit.drift_correction
import autoscript_toolkit.vision as vision_toolkit
from matplotlib import pyplot as plot
import unittest


class TestsToolkit(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, None)
        pass

    def tearDown(self):
        pass

    def test_locate_feature_opencv(self):
        print("Loading test images...")
        lenna = self.test_helper.provide_lenna_gray8()
        face = self.test_helper.extract_lenna_face_region(lenna)
        lenna_adorned_image = AdornedImage(lenna)
        face_adorned_image = AdornedImage(face)
        print("success.")

        print("Matching template using OpenCV matcher, approach #1...")
        opencv_matcher = OpencvTemplateMatcher()
        match = opencv_matcher.match(lenna_adorned_image, face_adorned_image)
        print("    Match center:", match.center)
        print("    Match score:", match.score)
        self.assertAlmostEqual(match.center.x, 300, places=0)
        self.assertAlmostEqual(match.center.y, 300, places=0)
        print("Success.")

        print("Matching template using OpenCV matcher, approach #2...")

        print("    For image without metadata, we throw...")
        with self.assertRaisesRegex(InvalidOperationException, "metadata"):
            location = vision_toolkit.locate_feature(lenna_adorned_image, face_adorned_image)

        print("    Loading ion beam image with metadata...")
        ion_image_path = self.test_helper.get_resource_path("ion_image_with_databar_3072x2188x8.tif")
        ion_image = AdornedImage.load(ion_image_path)
        print("    Success.")

        print("    Cutting out the 'Ion 0' part as a fiducial...")
        fiducial_top_left = Point(231, 147)
        fiducial_bottom_right = Point(522, 226)
        fiducial_image = vision_toolkit.cut_image(ion_image, top_left=fiducial_top_left, bottom_right=fiducial_bottom_right)
        fiducial_center = (fiducial_top_left.x + fiducial_image.width / 2, fiducial_top_left.y + fiducial_image.height / 2)
        print("    Fiducial center:", fiducial_center)
        print("    Success.")

        print("    Matching...")
        original_feature_center = Point(400, 200)  # Random coordinates
        location = vision_toolkit.locate_feature(ion_image, fiducial_image, DEFAULT_TEMPLATE_MATCHER, original_feature_center)
        print("    Location information:")
        location.print_all_information()
        self.assertAlmostEqual(fiducial_center[0], location.center_in_pixels[0], 0)
        self.assertAlmostEqual(fiducial_center[1], location.center_in_pixels[1], 0)

        print("    Opening popup window with match result...")
        plot.ion()
        vision_toolkit.plot_match(ion_image, fiducial_image, location.center_in_pixels)
        print("    Window closed.")
        print("Done.")

    def test_locate_feature_hog(self):
        print("Loading test images...")
        lenna = self.test_helper.provide_lenna_gray8()
        face = self.test_helper.extract_lenna_face_region(lenna)
        lenna_adorned_image = AdornedImage(lenna)
        face_adorned_image = AdornedImage(face)
        print("success.")

        hog_matcher = HogMatcher(self.microscope)

        print("Matching template using HOG matcher, approach #1...")
        match = hog_matcher.match(lenna_adorned_image, face_adorned_image)
        print("    Match center:", match.center)
        print("    Match score:", match.score)
        self.assertAlmostEqual(match.center.x, 300, places=0)
        self.assertAlmostEqual(match.center.y, 300, places=0)
        print("Success.")

        print("Matching template using HOG matcher, approach #2...")

        print("    Loading ion beam image with metadata...")
        ion_image_path = self.test_helper.get_resource_path("ion_image_with_databar_3072x2188x8.tif")
        ion_image = AdornedImage.load(ion_image_path)
        print("    Success.")

        print("    Cutting out the 'Ion 0' part as a fiducial...")
        fiducial_top_left = Point(231, 147)
        fiducial_bottom_right = Point(522, 226)
        fiducial_image = vision_toolkit.cut_image(ion_image, top_left=fiducial_top_left, bottom_right=fiducial_bottom_right)
        fiducial_center = (fiducial_top_left.x + fiducial_image.width / 2, fiducial_top_left.y + fiducial_image.height / 2)
        print("    Fiducial center:", fiducial_center)
        print("    Success.")

        print("    Matching...")
        location = vision_toolkit.locate_feature(ion_image, fiducial_image, hog_matcher)
        print("    Location information:")
        location.print_all_information()
        self.assertAlmostEqual(fiducial_center[0], location.center_in_pixels[0], 0)
        self.assertAlmostEqual(fiducial_center[1], location.center_in_pixels[1], 0)
        print("Done.")
