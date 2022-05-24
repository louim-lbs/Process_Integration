from autoscript_core.common import ApplicationServerException
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_core.common import InvalidOperationException
from autoscript_sdb_microscope_client_tests.utilities import *
import time
import unittest


class TestsAdornedImage(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.test_helper = TestHelper(self, None)
        pass

    def tearDown(self):
        pass

    def test_adorned_image(self):
        self.test_local_image_construction()
        self.test_load_adorned_image8()
        self.test_load_adorned_image16()
        self.test_load_adorned_image24()
        self.test_load_adorned_image_without_metadata()
        self.test_load_adorned_image_with_empty_metadata()
        self.test_load_adorned_image_xml_only_metadata()
        self.test_load_adorned_image_bmp()
        self.test_load_adorned_image_png()
        self.test_load_adorned_image_jpg()
        self.test_checksum()
        self.test_data()
        self.test_thumbnails()

    def test_local_image_construction(self):
        print("Testing image construction...")
        lenna_gray8 = self.test_helper.provide_lenna_gray8()
        face_gray8 = self.test_helper.extract_lenna_face_region(lenna_gray8)
        face_gray8_adorned_image = AdornedImage(face_gray8)
        self.test_helper.assert_image(face_gray8_adorned_image, expected_width=150, expected_height=200, expected_bit_depth=8, expected_encoding=ImageDataEncoding.UNSIGNED)

        lenna_gray16 = self.test_helper.provide_lenna_gray16()
        face_gray16 = self.test_helper.extract_lenna_face_region(lenna_gray16)
        face_gray16_adorned_image = AdornedImage(face_gray16)
        self.test_helper.assert_image(face_gray16_adorned_image, expected_width=150, expected_height=200, expected_bit_depth=16, expected_encoding=ImageDataEncoding.UNSIGNED)

        # RGB is internally stored as BGR, only presented as RGB
        # BGR is default color encoding
        lenna_rgb = self.test_helper.provide_lenna_rgb()
        face_rgb = self.test_helper.extract_lenna_face_region(lenna_rgb)
        face_rgb_adorned_image = AdornedImage(face_rgb)
        self.test_helper.assert_image(face_rgb_adorned_image, expected_width=150, expected_height=200, expected_bit_depth=24, expected_encoding=ImageDataEncoding.RGB)

        # input data in BGR format will be presented as RGB and may be interpreted incorrectly
        # to do: look into potential fix
        lenna_bgr = self.test_helper.provide_lenna_bgr()
        face_bgr = self.test_helper.extract_lenna_face_region(lenna_bgr)
        face_bgr_adorned_image = AdornedImage(face_bgr)
        self.test_helper.assert_image(face_bgr_adorned_image, expected_width=150, expected_height=200, expected_bit_depth=24, expected_encoding=ImageDataEncoding.RGB)
        print("Success.")

    def test_load_adorned_image8(self):
        print("Loading 8-bit image with ini metadata...")
        image_path = self.test_helper.get_resource_path("electron_image_without_databar_768x512x8.tif")
        image = AdornedImage.load(image_path)
        self.test_helper.assert_image(image, 768, 512, 8, ImageDataEncoding.UNSIGNED)
        self.test_helper.assert_image_has_basic_metadata(image)
        print("Success.")

    def test_load_adorned_image16(self):
        print("Loading 16-bit image with ini metadata...")
        image_path = self.test_helper.get_resource_path("electron_image_with_databar_1536x1094x16.tif")
        image = AdornedImage.load(image_path)
        self.test_helper.assert_image(image, 1536, 1094, 16, ImageDataEncoding.UNSIGNED)
        self.test_helper.assert_image_has_basic_metadata(image)
        print("Success.")

    def test_load_adorned_image24(self):
        print("Loading 24-bit image with ini metadata...")
        image_path = self.test_helper.get_resource_path("electron_image_without_databar_1536x1024x24.tif")
        image = AdornedImage.load(image_path)
        self.test_helper.assert_image(image, 1536, 1024, 24, ImageDataEncoding.RGB)
        self.test_helper.assert_image_has_basic_metadata(image)
        print("Success.")

    def test_load_adorned_image_without_metadata(self):
        print("Loading image without metadata...")
        image_path = self.test_helper.get_resource_path("image_without_metadata_1843x820x16.tif")
        image = AdornedImage.load(image_path)
        self.test_helper.assert_image(image, 1843, 820, 16, ImageDataEncoding.UNSIGNED)
        assert_equal(image.metadata, None)
        print("Success.")

    def test_load_adorned_image_with_empty_metadata(self):
        print("Loading image with uninitialized ini metadata...")
        image_path = self.test_helper.get_resource_path("navcam_image_with_empty_metadata_768x512x24.tif")
        image = AdornedImage.load(image_path)
        self.test_helper.assert_image(image, 768, 512, 24, ImageDataEncoding.RGB)
        assert_equal(type(image.metadata.metadata_as_ini), str)
        print("Success.")

    def test_load_adorned_image_xml_only_metadata(self):
        print("Loading image from autotem...")
        image_path = self.test_helper.get_resource_path("ion_image_from_autotem_1536x1024x16.tif")
        image = AdornedImage.load(image_path)
        self.test_helper.assert_image(image, 1536, 1024, 16, ImageDataEncoding.UNSIGNED)
        assert_equal(type(image.metadata.metadata_as_xml), str)
        assert_equal(image.metadata.metadata_as_ini, None)

        print("Loading image with only xml metadata...")
        image_path = self.test_helper.get_resource_path("ion_image_with_only_xml_metadata_1536x1024x8.tif")
        image = AdornedImage.load(image_path)
        self.test_helper.assert_image(image, 1536, 1024, 8, ImageDataEncoding.UNSIGNED)
        assert_equal(type(image.metadata.metadata_as_xml), str)
        assert_equal(image.metadata.metadata_as_ini, None)
        print("Success.")

    def test_load_adorned_image_bmp(self):
        print("Loading png image...")
        image_path = self.test_helper.get_resource_path("puzzle.bmp")
        image = AdornedImage.load(image_path)
        self.test_helper.assert_image(image, 379, 375, 24, ImageDataEncoding.RGB)
        print("Success.")

    def test_load_adorned_image_png(self):
        print("Loading png image...")
        image_path = self.test_helper.get_resource_path("lenna.png")
        image = AdornedImage.load(image_path)
        self.test_helper.assert_image(image, 512, 512, 24, ImageDataEncoding.RGB)
        print("Success.")

    def test_load_adorned_image_jpg(self):
        print("Loading jpg image...")
        image_path = self.test_helper.get_resource_path("ion_image_without_databar_768x512x24.jpg")
        image = AdornedImage.load(image_path)
        self.test_helper.assert_image(image, 768, 512, 24, ImageDataEncoding.RGB)
        print("Success.")

    def test_checksum(self):
        print("Testing image checksum...")
        image_path = self.test_helper.get_resource_path("electron_image_with_databar_1536x1094x16.tif")
        image = AdornedImage.load(image_path)
        print("Checksum is", image.checksum)

        print("Testing empty image checksum...")
        empty_image = AdornedImage()
        with self.assertRaisesRegex(InvalidOperationException, "not initialized"):
            checksum = empty_image.checksum

        print("Success.")

    def test_data(self):
        print("Testing access to image data...")
        image_path = self.test_helper.get_resource_path("electron_image_with_databar_1536x1094x16.tif")
        image = AdornedImage.load(image_path)
        print("Data is", image.data)

        print("Testing access to image data on an empty image...")
        empty_image = AdornedImage()
        with self.assertRaisesRegex(InvalidOperationException, "not initialized"):
            data = empty_image.data

        print("Success.")

    def test_thumbnails(self):
        print("Testing empty image thumbnail...")
        empty_image = AdornedImage()
        with self.assertRaisesRegex(InvalidOperationException, "not initialized"):
            empty_thumbnail = empty_image.thumbnail

        print("Testing 16 bit thumbnail in wide screen resolution with databar...")
        self.__test_one_thumbnail("electron_image_with_databar_1536x1094x16.tif", 512, 365)
        print("Testing 24 bit thumbnail in wide screen resolution without databar...")
        self.__test_one_thumbnail("electron_image_without_databar_1536x1024x24.tif", 512, 341)
        print("Testing 8 bit thumbnail in square resolution without databar...")
        self.__test_one_thumbnail("electron_image_with_ini_and_xml_metadata_1024x884x8.tif", 512, 442)
        print("Testing 8 bit thumbnail in wide screen resolution with databar...")
        self.__test_one_thumbnail("ion_image_with_databar_3072x2188x8.tif", 512, 365)
        print("Testing 24 RGB thumbnail on image with size < 512")
        self.__test_one_thumbnail("puzzle.bmp", 512, 507)
        print("Success.")

    def __test_one_thumbnail(self, image_name, expected_width, expected_height):
        image_path = self.test_helper.get_resource_path(image_name)
        image = AdornedImage.load(image_path)
        print(f"    Image size is {image.width}x{image.height}x{image.bit_depth}")
        thumbnail = image.thumbnail
        print(f"    Thumbnail size is {thumbnail.width}x{thumbnail.height}x{thumbnail.bit_depth}")
        self.test_helper.assert_image(thumbnail, expected_width, expected_height, image.bit_depth, image.encoding)


class TestsStagePosition(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.test_helper = TestHelper(self, None)

    def tearDown(self):
        pass

    def test_stage_position(self):
        self.test_position_addition()
        self.test_position_subtraction()
        self.test_position_multiplication()
        self.test_position_division()
        self.test_position_division_floor()
        self.test_position_equality()
        self.test_position_initialization()
        self.test_position_coordinate_system_persistence()
        print("Done.")

    def test_position_addition(self):
        position = StagePosition(2, 3, 4, 0, 1)
        print("Add to another position...")
        result = position + StagePosition(2, 3, 4, 0, 1)
        self.test_helper.assert_stage_position(result, StagePosition(4, 6, 8, 0, 2))
        print("Add to tuple...")
        result = position + (2, 3, 4, 0, 1)
        self.test_helper.assert_stage_position(result, StagePosition(4, 6, 8, 0, 2))
        print("Add to scalar...")
        result = position + 4
        self.test_helper.assert_stage_position(result, StagePosition(6, 7, 8, 4, 5))
        print("Reverse add to another position...")
        result = StagePosition(2, 3, 4, 0, 1) + position
        self.test_helper.assert_stage_position(result, StagePosition(4, 6, 8, 0, 2))
        print("Reverse add to tuple...")
        result = (2, 3, 4, 0, 1) + position
        self.test_helper.assert_stage_position(result, StagePosition(4, 6, 8, 0, 2))
        print("Reverse add to scalar...")
        result = 4 + position
        self.test_helper.assert_stage_position(result, StagePosition(6, 7, 8, 4, 5))
        print("Add with some of the axes being None...")
        position = StagePosition(x=2, z=3)
        result = position + StagePosition(x=3, z=4)
        self.test_helper.assert_stage_position(result, StagePosition(x=5, z=7))

    def test_position_subtraction(self):
        position = StagePosition(2, 3, 4, 0, 1)
        print("Subtract another position...")
        result = position - StagePosition(1, 2, 3, 4, 5)
        self.test_helper.assert_stage_position(result, StagePosition(1, 1, 1, -4, -4))
        print("Subtract tuple...")
        result = position - (1, 2, 3, 4, 5)
        self.test_helper.assert_stage_position(result, StagePosition(1, 1, 1, -4, -4))
        print("Subtract scalar...")
        result = position - 1
        self.test_helper.assert_stage_position(result, StagePosition(1, 2, 3, -1, 0))
        print("Reverse subtract another position...")
        result = StagePosition(1, 2, 3, 4, 5) - position
        self.test_helper.assert_stage_position(result, StagePosition(-1, -1, -1, 4, 4))
        print("Reverse subtract tuple...")
        result = (1, 2, 3, 4, 5) - position
        self.test_helper.assert_stage_position(result, StagePosition(-1, -1, -1, 4, 4))
        print("Reverse subtract scalar...")
        result = 5 - position
        self.test_helper.assert_stage_position(result, StagePosition(3, 2, 1, 5, 4))
        print("Subtract with some of the axes being None...")
        position = StagePosition(x=2, y=3)
        result1 = position - StagePosition(x=3, y=4)
        result2 = StagePosition(x=10, y=10) - position
        self.test_helper.assert_stage_position(result1, StagePosition(x=-1, y=-1))
        self.test_helper.assert_stage_position(result2, StagePosition(x=8, y=7))

    def test_position_multiplication(self):
        position = StagePosition(2, 3, 4, 0, 1)
        print("Multiply by another position throws...")
        with self.assertRaises(ValueError):
            result = position * StagePosition(2, 3, 4, 0, 1)
        print("Multiply by tuple throws...")
        with self.assertRaises(ValueError):
            result = position * (2, 3, 4, 0, 1)
        print("Multiply by scalar...")
        result = position * 4
        self.test_helper.assert_stage_position(result, StagePosition(8, 12, 16, 0, 4))
        print("Reverse multiply by another position throws...")
        with self.assertRaises(ValueError):
            result = StagePosition(2, 3, 4, 0, 1) * position
        print("Reverse multiply by tuple throws...")
        with self.assertRaises(ValueError):
            result = (2, 3, 4, 0, 1) * position
        print("Reverse multiply by scalar...")
        result = -2 * position
        self.test_helper.assert_stage_position(result, StagePosition(-4, -6, -8, 0, -2))
        print("Multiply with some of the axes being None...")
        position = StagePosition(z=2, y=3)
        result1 = position * 2
        result2 = 2 * position
        self.test_helper.assert_stage_position(result1, StagePosition(z=4, y=6))
        self.test_helper.assert_stage_position(result2, StagePosition(z=4, y=6))

    def test_position_division(self):
        position = StagePosition(4, 5, 1, 2, 3)
        print("Divide by another position throws...")
        with self.assertRaises(ValueError):
            result = position / StagePosition(2, 3, 1, 1, 1)
        print("Divide by tuple throws...")
        with self.assertRaises(ValueError):
            result = position / (2, 3, 1, 1, 1)
        print("Divide by scalar...")
        result = position / 2
        self.test_helper.assert_stage_position(result, StagePosition(2, 2.5, 0.5, 1, 1.5))
        print("Divide by 0 scalar throws...")
        with self.assertRaises(ValueError):
            result = position / 0
        print("Reverse divide by another position throws...")
        with self.assertRaises(ValueError):
            result = StagePosition(2, 3, 1, 1, 1) / position
        print("Reverse divide by tuple throws...")
        with self.assertRaises(ValueError):
            result = (2, 3, 1, 1, 1) / position
        print("Reverse divide by scalar...")
        result = 20 / position
        self.test_helper.assert_stage_position(result, StagePosition(5, 4, 20, 10, 6.66666))
        print("Reverse divide by scalar with 0 values throws...")
        with self.assertRaises(ValueError):
            result = 20 / StagePosition(0, 0, 0, 0, 0)
        print("Divide with some of the axes being None...")
        position = StagePosition(z=4, r=6)
        result1 = position / 2
        result2 = 24 / position
        self.test_helper.assert_stage_position(result1, StagePosition(z=2, r=3))
        self.test_helper.assert_stage_position(result2, StagePosition(z=6, r=4))

    def test_position_division_floor(self):
        position = StagePosition(4, 5, 1, 2, 3)
        print("Divide with floor by another position throws...")
        with self.assertRaises(ValueError):
            result = position // StagePosition(4, 5, 1, 2, 3)
        print("Divide with floor by tuple throws...")
        with self.assertRaises(ValueError):
            result = position // (4, 5, 1, 2, 3)
        print("Divide with floor by scalar...")
        result = position // 2
        self.test_helper.assert_stage_position(result, StagePosition(2, 2, 0, 1, 1))
        print("Divide with floor by 0 scalar throws...")
        with self.assertRaises(ValueError):
            result = position // 0
        print("Reverse divide with floor by another position throws...")
        with self.assertRaises(ValueError):
            result = StagePosition(4, 5, 1, 2, 3) // position
        print("Reverse divide with floor by tuple throws...")
        with self.assertRaises(ValueError):
            result = (4, 5, 1, 2, 3) // position
        print("Reverse divide with floor by scalar...")
        result = 4 // position
        self.test_helper.assert_stage_position(result, StagePosition(1, 0, 4, 2, 1))
        print("Reverse divide with floor by scalar with 0 values throws...")
        with self.assertRaises(ValueError):
            result = 20 // StagePosition(0, 0, 0, 0, 0)
        print("Divide with floor with some of the axes being None...")
        position = StagePosition(z=4, r=6)
        result1 = position // 2
        result2 = 24 // position
        self.test_helper.assert_stage_position(result1, StagePosition(z=2, r=3))
        self.test_helper.assert_stage_position(result2, StagePosition(z=6, r=4))

    def test_position_equality(self):
        print("Test equality...")
        first = StagePosition(4, 5, 1, 2, 3)
        second = StagePosition(4, 5, 1, 2, 3)
        third = StagePosition(1, 1, 0, 2, 3)
        four = StagePosition(x=1, y=2)
        six = StagePosition(x=1, y=2)
        seven = StagePosition(x=1, y=2, z=3)

        self.assertTrue(first == second)
        self.assertFalse(first == third)
        self.assertTrue(four == six)
        self.assertFalse(six == seven)

        print("Test equality with tolerance...")
        first_position = StagePosition(0.0001, 0.0002, 0.00003, 0.12) + 0.001
        second_position = StagePosition(0.0011, 0.0012, 0.00103, 0.121)

        self.assertTrue(first_position == second_position)

    def test_position_initialization(self):
        print("Test position initialization...")
        position = StagePosition(x=1e-3, y=2e-3, z=3e-3, r=None)
        self.assertAlmostEqual(1e-3, position.x, 3)
        self.assertAlmostEqual(2e-3, position.y, 3)
        self.assertAlmostEqual(3e-3, position.z, 3)
        self.assertIsNone(position.r)
        self.assertIsNone(position.t)

        with self.assertRaises(InvalidOperationException):
            position = StagePosition(x="TestString")

        position = StagePosition()
        with self.assertRaises(InvalidOperationException):
            position.x = "TestString"

        print("Test indexers...")
        position = StagePosition(x=1e-3, y=2e-3, z=3e-3, r=4e-2, t=5e-3)
        self.assertEquals(position[0], position['x'])
        self.assertEquals(position[1], position['y'])
        self.assertEquals(position[2], position['z'])
        self.assertEquals(position[3], position['r'])
        self.assertEquals(position[4], position['t'])

        with self.assertRaises(IndexError):
            a = position[7]
        with self.assertRaises(IndexError):
            a = position["e"]

    def test_position_coordinate_system_persistence(self):
        print("Test coordinate system persistence...")
        r = StagePosition(x=0.001, coordinate_system=CoordinateSystem.RAW)
        s = StagePosition(x=0.001, coordinate_system=CoordinateSystem.SPECIMEN)
        n = StagePosition(x=0.001)

        a = r + n
        assert_equal(a.coordinate_system, CoordinateSystem.RAW)
        a = s + n
        assert_equal(a.coordinate_system, CoordinateSystem.SPECIMEN)
        a = s + s
        assert_equal(a.coordinate_system, CoordinateSystem.SPECIMEN)
        a = s + 2
        assert_equal(a.coordinate_system, CoordinateSystem.SPECIMEN)
        a = 2 + s
        assert_equal(a.coordinate_system, CoordinateSystem.SPECIMEN)
        a = r / 2
        assert_equal(a.coordinate_system, CoordinateSystem.RAW)
        a = n - n
        assert_equal(a.coordinate_system, None)
        a = s + (0.001, 0.002)
        assert_equal(a.coordinate_system, CoordinateSystem.SPECIMEN)
        a = r + [0.001, 0.002]
        assert_equal(a.coordinate_system, CoordinateSystem.RAW)

        with self.assertRaises(ValueError):
            a = r + s


class TestsCompustagePosition(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.test_helper = TestHelper(self, None)

    def tearDown(self):
        pass

    def test_compustage_position(self):
        self.test_position_addition()
        self.test_position_subtraction()
        self.test_position_multiplication()
        self.test_position_division()
        self.test_position_division_floor()
        self.test_position_equality()
        self.test_position_initialization()
        print("Done.")

    def test_position_addition(self):
        position = CompustagePosition(2, 3, 4, 0, 1)
        print("Add to another position...")
        result = position + CompustagePosition(2, 3, 4, 0, 1)
        self.test_helper.assert_compustage_position(result, CompustagePosition(4, 6, 8, 0, 2))
        print("Add to tuple...")
        result = position + (2, 3, 4, 0, 1)
        self.test_helper.assert_compustage_position(result, CompustagePosition(4, 6, 8, 0, 2))
        print("Add to scalar...")
        result = position + 4
        self.test_helper.assert_compustage_position(result, CompustagePosition(6, 7, 8, 4, 5))
        print("Reverse add to another position...")
        result = CompustagePosition(2, 3, 4, 0, 1) + position
        self.test_helper.assert_compustage_position(result, CompustagePosition(4, 6, 8, 0, 2))
        print("Reverse add to tuple...")
        result = (2, 3, 4, 0, 1) + position
        self.test_helper.assert_compustage_position(result, CompustagePosition(4, 6, 8, 0, 2))
        print("Reverse add to scalar...")
        result = 4 + position
        self.test_helper.assert_compustage_position(result, CompustagePosition(6, 7, 8, 4, 5))
        print("Add with some of the axes being None...")
        position = CompustagePosition(x=2, y=3)
        result = position + CompustagePosition(x=3, y=4)
        self.test_helper.assert_compustage_position(result, CompustagePosition(x=5, y=7))

    def test_position_subtraction(self):
        position = CompustagePosition(2, 3, 4, 0, 1)
        print("Subtract another position...")
        result = position - CompustagePosition(1, 2, 3, 4, 5)
        self.test_helper.assert_compustage_position(result, CompustagePosition(1, 1, 1, -4, -4))
        print("Subtract tuple...")
        result = position - (1, 2, 3, 4, 5)
        self.test_helper.assert_compustage_position(result, CompustagePosition(1, 1, 1, -4, -4))
        print("Subtract scalar...")
        result = position - 1
        self.test_helper.assert_compustage_position(result, CompustagePosition(1, 2, 3, -1, 0))
        print("Reverse subtract another position...")
        result = CompustagePosition(1, 2, 3, 4, 5) - position
        self.test_helper.assert_compustage_position(result, CompustagePosition(-1, -1, -1, 4, 4))
        print("Reverse subtract tuple...")
        result = (1, 2, 3, 4, 5) - position
        self.test_helper.assert_compustage_position(result, CompustagePosition(-1, -1, -1, 4, 4))
        print("Reverse subtract scalar...")
        result = 5 - position
        self.test_helper.assert_compustage_position(result, CompustagePosition(3, 2, 1, 5, 4))
        print("Subtract with some of the axes being None...")
        position = CompustagePosition(x=2, y=3)
        result1 = position - CompustagePosition(x=3, y=4)
        result2 = CompustagePosition(x=10, y=10) - position
        self.test_helper.assert_compustage_position(result1, CompustagePosition(x=-1, y=-1))
        self.test_helper.assert_compustage_position(result2, CompustagePosition(x=8, y=7))

    def test_position_multiplication(self):
        position = CompustagePosition(2, 3, 4, 0, 1)
        print("Multiply by another position throws...")
        with self.assertRaises(ValueError):
            result = position * CompustagePosition(2, 3, 4, 0, 1)
        print("Multiply by tuple throws...")
        with self.assertRaises(ValueError):
            result = position * (2, 3, 4, 0, 1)
        print("Multiply by scalar...")
        result = position * 4
        self.test_helper.assert_compustage_position(result, CompustagePosition(8, 12, 16, 0, 4))
        print("Reverse multiply by another position throws...")
        with self.assertRaises(ValueError):
            result = CompustagePosition(2, 3, 4, 0, 1) * position
        print("Reverse multiply by tuple throws...")
        with self.assertRaises(ValueError):
            result = (2, 3, 4, 0, 1) * position
        print("Reverse multiply by scalar...")
        result = -2 * position
        self.test_helper.assert_compustage_position(result, CompustagePosition(-4, -6, -8, 0, -2))
        print("Multiply with some of the axes being None...")
        position = CompustagePosition(z=2, b=3)
        result1 = position * 2
        result2 = 2 * position
        self.test_helper.assert_compustage_position(result1, CompustagePosition(z=4, b=6))
        self.test_helper.assert_compustage_position(result2, CompustagePosition(z=4, b=6))

    def test_position_division(self):
        position = CompustagePosition(4, 5, 1, 2, 3)
        print("Divide by another position throws...")
        with self.assertRaises(ValueError):
            result = position / CompustagePosition(2, 3, 1, 1, 1)
        print("Divide by tuple throws...")
        with self.assertRaises(ValueError):
            result = position / (2, 3, 1, 1, 1)
        print("Divide by scalar...")
        result = position / 2
        self.test_helper.assert_compustage_position(result, CompustagePosition(2, 2.5, 0.5, 1, 1.5))
        print("Divide by 0 scalar throws...")
        with self.assertRaises(ValueError):
            result = position / 0
        print("Reverse divide by another position throws...")
        with self.assertRaises(ValueError):
            result = CompustagePosition(2, 3, 1, 1, 1) / position
        print("Reverse divide by tuple throws...")
        with self.assertRaises(ValueError):
            result = (2, 3, 1, 1, 1) / position
        print("Reverse divide by scalar...")
        result = 20 / position
        self.test_helper.assert_compustage_position(result, CompustagePosition(5, 4, 20, 10, 6.66666))
        print("Reverse divide by scalar with 0 values throws...")
        with self.assertRaises(ValueError):
            result = 20 / CompustagePosition(0, 0, 0, 0, 0)
        print("Divide with some of the axes being None...")
        position = CompustagePosition(z=4, a=6)
        result1 = position / 2
        result2 = 24 / position
        self.test_helper.assert_compustage_position(result1, CompustagePosition(z=2, a=3))
        self.test_helper.assert_compustage_position(result2, CompustagePosition(z=6, a=4))

    def test_position_division_floor(self):
        position = CompustagePosition(4, 5, 1, 2, 3)
        print("Divide with floor by another position throws...")
        with self.assertRaises(ValueError):
            result = position // CompustagePosition(4, 5, 1, 2, 3)
        print("Divide with floor by tuple throws...")
        with self.assertRaises(ValueError):
            result = position // (4, 5, 1, 2, 3)
        print("Divide with floor by scalar...")
        result = position // 2
        self.test_helper.assert_compustage_position(result, CompustagePosition(2, 2, 0, 1, 1))
        print("Divide with floor by 0 scalar throws...")
        with self.assertRaises(ValueError):
            result = position // 0
        print("Reverse divide with floor by another position throws...")
        with self.assertRaises(ValueError):
            result = CompustagePosition(4, 5, 1, 2, 3) // position
        print("Reverse divide with floor by tuple throws...")
        with self.assertRaises(ValueError):
            result = (4, 5, 1, 2, 3) // position
        print("Reverse divide with floor by scalar...")
        result = 4 // position
        self.test_helper.assert_compustage_position(result, CompustagePosition(1, 0, 4, 2, 1))
        print("Reverse divide with floor by scalar with 0 values throws...")
        with self.assertRaises(ValueError):
            result = 20 // CompustagePosition(0, 0, 0, 0, 0)
        print("Divide with floor with some of the axes being None...")
        position = CompustagePosition(z=4, x=6)
        result1 = position // 2
        result2 = 24 // position
        self.test_helper.assert_compustage_position(result1, CompustagePosition(z=2, x=3))
        self.test_helper.assert_compustage_position(result2, CompustagePosition(z=6, x=4))

    def test_position_equality(self):
        print("Test equality...")
        first = CompustagePosition(4, 5, 1, 2, 3)
        second = CompustagePosition(4, 5, 1, 2, 3)
        third = CompustagePosition(1, 1, 0, 2, 3)
        four = CompustagePosition(x=1, y=2)
        six = CompustagePosition(x=1, y=2)
        seven = CompustagePosition(x=1, y=2, z=3)

        self.assertTrue(first == second)
        self.assertFalse(first == third)
        self.assertTrue(four == six)
        self.assertFalse(six == seven)

        print("Test equality with tolerance...")
        first_position = CompustagePosition(0.0001, 0.0002, 0.00003, 0.12) + 0.001
        second_position = CompustagePosition(0.0011, 0.0012, 0.00103, 0.121)

        self.assertTrue(first_position == second_position)

    def test_position_initialization(self):
        print("Test position initialization...")
        position = CompustagePosition(x=1e-3, y=2e-3, z=3e-3, a=None)
        self.assertAlmostEqual(1e-3, position.x, 3)
        self.assertAlmostEqual(2e-3, position.y, 3)
        self.assertAlmostEqual(3e-3, position.z, 3)
        self.assertIsNone(position.a)
        self.assertIsNone(position.b)

        with self.assertRaises(InvalidOperationException):
            position = CompustagePosition(x="TestString")

        position = CompustagePosition()
        with self.assertRaises(InvalidOperationException):
            position.x = "TestString"

        print("Test indexers...")
        position = CompustagePosition(x=1e-3, y=2e-3, z=3e-3, a=6e-2, b=3e-3)
        self.assertEquals(position[0], position['x'])
        self.assertEquals(position[1], position['y'])
        self.assertEquals(position[2], position['z'])
        self.assertEquals(position[3], position['a'])
        self.assertEquals(position[4], position['b'])

        with self.assertRaises(IndexError):
            a = position[5]
        with self.assertRaises(IndexError):
            a = position["e"]


class TestsManipulatorPosition(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.test_helper = TestHelper(self, None)

    def tearDown(self):
        pass

    def test_manipulator_position(self):
        self.test_position_addition()
        self.test_position_subtraction()
        self.test_position_multiplication()
        self.test_position_division()
        self.test_position_division_floor()
        self.test_position_equality()
        self.test_position_initialization()
        print("Done.")

    def test_position_addition(self):
        position = ManipulatorPosition(2, 3, 4, 0)
        print("Add to another position...")
        result = position + ManipulatorPosition(2, 3, 4, 0)
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(4, 6, 8, 0))
        print("Add to tuple...")
        result = position + (2, 3, 4, 0)
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(4, 6, 8, 0))
        print("Add to scalar...")
        result = position + 4
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(6, 7, 8, 4))
        print("Reverse add to another position...")
        result = ManipulatorPosition(2, 3, 4, 0) + position
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(4, 6, 8, 0))
        print("Reverse add to tuple...")
        result = (2, 3, 4, 0) + position
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(4, 6, 8, 0))
        print("Reverse add to scalar...")
        result = 4 + position
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(6, 7, 8, 4))
        print("Add with some of the axes being None...")
        position = ManipulatorPosition(x=2, y=3)
        result = position + ManipulatorPosition(x=3, y=4)
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(x=5, y=7))

    def test_position_subtraction(self):
        position = ManipulatorPosition(2, 3, 4, 0)
        print("Subtract another position...")
        result = position - ManipulatorPosition(1, 2, 3, 4)
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(1, 1, 1, -4))
        print("Subtract tuple...")
        result = position - (1, 2, 3, 4)
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(1, 1, 1, -4))
        print("Subtract scalar...")
        result = position - 1
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(1, 2, 3, -1))
        print("Reverse subtract another position...")
        result = ManipulatorPosition(1, 2, 3, 4) - position
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(-1, -1, -1, 4))
        print("Reverse subtract tuple...")
        result = (1, 2, 3, 4) - position
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(-1, -1, -1, 4))
        print("Reverse subtract scalar...")
        result = 5 - position
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(3, 2, 1, 5))
        print("Subtract with some of the axes being None...")
        position = ManipulatorPosition(x=2, y=3)
        result1 = position - ManipulatorPosition(x=3, y=4)
        result2 = ManipulatorPosition(x=10, y=10) - position
        self.test_helper.assert_manipulator_position(result1, ManipulatorPosition(x=-1, y=-1))
        self.test_helper.assert_manipulator_position(result2, ManipulatorPosition(x=8, y=7))

    def test_position_multiplication(self):
        position = ManipulatorPosition(2, 3, 4, 0)
        print("Multiply by another position throws...")
        with self.assertRaises(ValueError):
            result = position * ManipulatorPosition(2, 3, 4, 0)
        print("Multiply by tuple throws...")
        with self.assertRaises(ValueError):
            result = position * (2, 3, 4, 0)
        print("Multiply by scalar...")
        result = position * 4
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(8, 12, 16, 0))
        print("Reverse multiply by another position throws...")
        with self.assertRaises(ValueError):
            result = ManipulatorPosition(2, 3, 4, 0) * position
        print("Reverse multiply by tuple throws...")
        with self.assertRaises(ValueError):
            result = (2, 3, 4, 0, 1) * position
        print("Reverse multiply by scalar...")
        result = -2 * position
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(-4, -6, -8, 0))
        print("Multiply with some of the axes being None...")
        position = ManipulatorPosition(z=2, x=3)
        result1 = position * 2
        result2 = 2 * position
        self.test_helper.assert_manipulator_position(result1, ManipulatorPosition(z=4, x=6))
        self.test_helper.assert_manipulator_position(result2, ManipulatorPosition(z=4, x=6))

    def test_position_division(self):
        position = ManipulatorPosition(4, 5, 1, 2)
        print("Divide by another position throws...")
        with self.assertRaises(ValueError):
            result = position / ManipulatorPosition(2, 3, 1, 1)
        print("Divide by tuple throws...")
        with self.assertRaises(ValueError):
            result = position / (2, 3, 1, 1, 1)
        print("Divide by scalar...")
        result = position / 2
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(2, 2.5, 0.5, 1))
        print("Divide by 0 scalar throws...")
        with self.assertRaises(ValueError):
            result = position / 0
        print("Reverse divide by another position throws...")
        with self.assertRaises(ValueError):
            result = ManipulatorPosition(2, 3, 1, 1) / position
        print("Reverse divide by tuple throws...")
        with self.assertRaises(ValueError):
            result = (2, 3, 1, 1, 1) / position
        print("Reverse divide by scalar...")
        result = 20 / position
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(5, 4, 20, 10))
        print("Reverse divide by scalar with 0 values throws...")
        with self.assertRaises(ValueError):
            result = 20 / ManipulatorPosition(0, 0, 0, 0)
        print("Divide with some of the axes being None...")
        position = ManipulatorPosition(z=4, y=6)
        result1 = position / 2
        result2 = 24 / position
        self.test_helper.assert_manipulator_position(result1, ManipulatorPosition(z=2, y=3))
        self.test_helper.assert_manipulator_position(result2, ManipulatorPosition(z=6, y=4))

    def test_position_division_floor(self):
        position = ManipulatorPosition(4, 5, 1, 2)
        print("Divide with floor by another position throws...")
        with self.assertRaises(ValueError):
            result = position // ManipulatorPosition(4, 5, 1, 2)
        print("Divide with floor by tuple throws...")
        with self.assertRaises(ValueError):
            result = position // (4, 5, 1, 2)
        print("Divide with floor by scalar...")
        result = position // 2
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(2, 2, 0, 1))
        print("Divide with floor by 0 scalar throws...")
        with self.assertRaises(ValueError):
            result = position // 0
        print("Reverse divide with floor by another position throws...")
        with self.assertRaises(ValueError):
            result = ManipulatorPosition(4, 5, 1, 2) // position
        print("Reverse divide with floor by tuple throws...")
        with self.assertRaises(ValueError):
            result = (4, 5, 1, 2) // position
        print("Reverse divide with floor by scalar...")
        result = 4 // position
        self.test_helper.assert_manipulator_position(result, ManipulatorPosition(1, 0, 4, 2))
        print("Reverse divide with floor by scalar with 0 values throws...")
        with self.assertRaises(ValueError):
            result = 20 // ManipulatorPosition(0, 0, 0, 0)
        print("Divide with floor with some of the axes being None...")
        position = ManipulatorPosition(z=4, x=6)
        result1 = position // 2
        result2 = 24 // position
        self.test_helper.assert_manipulator_position(result1, ManipulatorPosition(z=2, x=3))
        self.test_helper.assert_manipulator_position(result2, ManipulatorPosition(z=6, x=4))

    def test_position_equality(self):
        print("Test equality...")
        first = ManipulatorPosition(4, 5, 1, 2)
        second = ManipulatorPosition(4, 5, 1, 2)
        third = ManipulatorPosition(1, 1, 0, 2)
        four = ManipulatorPosition(x=1, y=2)
        six = ManipulatorPosition(x=1, y=2)
        seven = ManipulatorPosition(x=1, y=2, z=3)

        self.assertTrue(first == second)
        self.assertFalse(first == third)
        self.assertTrue(four == six)
        self.assertFalse(six == seven)

        print("Test equality with tolerance...")
        first_position = ManipulatorPosition(0.0001, 0.0002, 0.00003, 0.12) + 0.001
        second_position = ManipulatorPosition(0.0011, 0.0012, 0.00103, 0.121)

        self.assertTrue(first_position == second_position)

    def test_position_initialization(self):
        print("Test position initialization...")
        position = ManipulatorPosition(x=1e-3, y=2e-3, z=3e-3, r=None)
        self.assertAlmostEqual(1e-3, position.x, 3)
        self.assertAlmostEqual(2e-3, position.y, 3)
        self.assertAlmostEqual(3e-3, position.z, 3)
        self.assertIsNone(position.r)

        with self.assertRaises(InvalidOperationException):
            position = ManipulatorPosition(x="TestString")

        position = ManipulatorPosition()
        with self.assertRaises(InvalidOperationException):
            position.x = "TestString"

        print("Test indexers...")
        position = ManipulatorPosition(x=1e-3, y=2e-3, z=3e-3, r=6e-2)
        self.assertEquals(position[0], position['x'])
        self.assertEquals(position[1], position['y'])
        self.assertEquals(position[2], position['z'])
        self.assertEquals(position[3], position['r'])

        with self.assertRaises(IndexError):
            a = position[5]
        with self.assertRaises(IndexError):
            a = position["e"]


class TestsPoint(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.test_helper = TestHelper(self, None)

    def tearDown(self):
        pass

    def test_point(self):
        self.test_point_addition()
        self.test_point_subtraction()
        self.test_point_multiplication()
        self.test_point_division()
        self.test_point_division_floor()
        self.test_point_equality()
        self.test_point_functions()
        self.test_point_initialization()
        print("Done.")

    def test_point_addition(self):
        point = Point(2, 3)
        print("Add to another point...")
        result = point + Point(2, 3)
        self.test_helper.assert_point(result, Point(4, 6))
        print("Add to tuple...")
        result = point + (2, 3)
        self.test_helper.assert_point(result, Point(4, 6))
        print("Add to scalar...")
        result = point + 4
        self.test_helper.assert_point(result, Point(6, 7))
        print("Reverse add to another point...")
        result = Point(2, 3) + point
        self.test_helper.assert_point(result, Point(4, 6))
        print("Reverse add to tuple...")
        result = (2, 3) + point
        self.test_helper.assert_point(result, Point(4, 6))
        print("Reverse add to scalar...")
        result = 4 + point
        self.test_helper.assert_point(result, Point(6, 7))

    def test_point_subtraction(self):
        point = Point(2, 3)
        print("Subtract another point...")
        result = point - Point(1, 2)
        self.test_helper.assert_point(result, Point(1, 1))
        print("Subtract tuple...")
        result = point - (1, 2)
        self.test_helper.assert_point(result, Point(1, 1))
        print("Subtract scalar...")
        result = point - 1
        self.test_helper.assert_point(result, Point(1, 2))
        print("Reverse subtract another point...")
        result = Point(4, 4) - point
        self.test_helper.assert_point(result, Point(2, 1))
        print("Reverse subtract tuple...")
        result = (2, 3) - point
        self.test_helper.assert_point(result, Point(0, 0))
        print("Reverse subtract scalar...")
        result = 5 - point
        self.test_helper.assert_point(result, Point(3, 2))

    def test_point_multiplication(self):
        point = Point(2, 3)
        print("Multiply by another point returns dot product...")
        result = point * Point(2, 3)
        self.assertEqual(result, 2 * 2 + 3 * 3)
        print("Multiply by tuple return dot product...")
        result = point * (2, 3)
        self.assertEqual(result, 2 * 2 + 3 * 3)
        print("Multiply by scalar...")
        result = point * 4
        self.test_helper.assert_point(result, Point(8, 12))
        print("Reverse multiply by another point returns dot product...")
        result = Point(2, 3) * point
        self.assertEqual(result, 2 * 2 + 3 * 3)
        print("Reverse multiply by tuple return dot product...")
        result = (2, 3) * point
        self.assertEqual(result, 2 * 2 + 3 * 3)
        print("Reverse multiply by scalar...")
        result = -2 * point
        self.test_helper.assert_point(result, Point(-4, -6))

    def test_point_division(self):
        point = Point(4, 5)
        print("Divide by another point throws...")
        with self.assertRaises(ValueError):
            result = point / Point(2, 3)
        print("Divide by tuple throws...")
        with self.assertRaises(ValueError):
            result = point / (2, 3)
        print("Divide by scalar...")
        result = point / 2
        self.test_helper.assert_point(result, Point(2, 2.5))
        print("Divide by 0 scalar throws...")
        with self.assertRaises(ValueError):
            result = point / 0
        print("Reverse divide by another point throws...")
        with self.assertRaises(ValueError):
            result = Point(2, 3) / point
        print("Reverse divide by tuple throws...")
        with self.assertRaises(ValueError):
            result = (2, 3) / point
        print("Reverse divide by scalar...")
        result = 20 / point
        self.test_helper.assert_point(result, Point(5, 4))
        print("Reverse divide by scalar with 0 values throws...")
        with self.assertRaises(ValueError):
            result = 20 / Point(0, 0)

    def test_point_division_floor(self):
        point = Point(4, 5)
        print("Divide with floor by another point throws...")
        with self.assertRaises(ValueError):
            result = point // Point(2, 3)
        print("Divide with floor by tuple throws...")
        with self.assertRaises(ValueError):
            result = point // (2, 3)
        print("Divide with floor by scalar...")
        result = point // 2
        self.test_helper.assert_point(result, Point(2, 2))
        print("Divide with floor by 0 scalar throws...")
        with self.assertRaises(ValueError):
            result = point // 0
        print("Reverse divide with floor by another point throws...")
        with self.assertRaises(ValueError):
            result = Point(2, 3) // point
        print("Reverse divide with floor by tuple throws...")
        with self.assertRaises(ValueError):
            result = (2, 3) // point
        print("Reverse divide with floor by scalar...")
        result = 4 // point
        self.test_helper.assert_point(result, Point(1, 0))
        print("Reverse divide with floor by scalar with 0 values throws...")
        with self.assertRaises(ValueError):
            result = 20 // Point(0, 0)

    def test_point_equality(self):
        print("Test equality...")
        first = Point(4, 5)
        second = Point(4, 5)
        third = Point(1, 1)

        self.assertTrue(first == second)
        self.assertFalse(first == third)

        print("Test equality with tolerance...")
        first_point = Point(0.0001, 0.0002) + 0.001
        second_point = Point(0.0011, 0.0012)

        self.assertTrue(first_point == second_point)

    def test_point_functions(self):
        print("Point functions must not throw...")
        point = Point(5, 4)
        magnitude = point.magnitude()
        angle = point.angle()

    def test_point_initialization(self):
        print("Testing Point initialization...")
        point = Point(x=1, y=2)
        self.assertEqual(1, point.x)
        self.assertEqual(2, point.y)

        point = Point(x=1e-3, y=2e-3)
        self.assertAlmostEqual(1e-3, point.x, 3)
        self.assertAlmostEqual(2e-3, point.y, 3)

        with self.assertRaises(InvalidOperationException):
            point = Point(x=None, y=None)

        with self.assertRaises(InvalidOperationException):
            point = Point(x="TestString")

        with self.assertRaises(InvalidOperationException):
            point.x = None

        with self.assertRaises(InvalidOperationException):
            point.x = "TestString"


class TestsOtherStructures(unittest.TestCase):
    def setUp(self, host="localhost"):
        pass

    def tearDown(self):
        pass

    def test_other_structures(self):
        self.__test_grab_frame_settings_initialization()
        self.__test_limits()
        self.__test_limits2d()
        print("Done.")

    def __test_grab_frame_settings_initialization(self):
        print("Testing GrabFrameSettings...")

        with self.assertRaises(InvalidOperationException):
            settings = GrabFrameSettings(line_integration=5.0)

        with self.assertRaises(InvalidOperationException):
            settings = GrabFrameSettings(dwell_time="StringValue")

    def __test_limits(self):
        print("Testing Limits...")

        limits = Limits(100, 200)
        self.assertTrue(limits.is_in(150))
        self.assertTrue(limits.is_in(100))
        self.assertFalse(limits.is_in(40))
        self.assertFalse(limits.is_in(201))
        self.assertTrue(limits.is_in(100 - 2e-10))
        self.assertTrue(limits.is_in(200 + 2e-10))

        first = Limits(1, 2)
        second = Limits(1, 2)
        third = Limits(2, 3)
        fourth = Limits(1, 3)
        self.assertTrue(first == second)
        self.assertFalse(first == third)
        self.assertFalse(first == fourth)
        self.assertFalse(third == fourth)

        midpoint = first.midpoint
        self.assertAlmostEqual(midpoint, 1.5)

    def __test_limits2d(self):
        print("Testing Limits2d...")

        limits2d = Limits2d(Limits(0, 100), Limits(200, 300))
        self.assertTrue(limits2d.is_in(Point(50, 250)))
        self.assertTrue(limits2d.is_in(Point(0, 200)))
        self.assertFalse(limits2d.is_in(Point(-10, 250)))
        self.assertFalse(limits2d.is_in(Point(50, 350)))
        self.assertTrue(limits2d.is_in(Point(0 - 2e-10, 300 + 2e-10)))

        with self.assertRaises(ValueError):
            limits2d.is_in(50)

        first = Limits2d(Limits(1, 2), Limits(3, 4))
        second = Limits2d(Limits(1, 2), Limits(3, 4))
        third = Limits2d(Limits(1, 2), Limits(30, 40))
        fourth = Limits2d(Limits(10, 20), Limits(3, 4))
        fifth = Limits2d(Limits(10, 20), Limits(30, 40))
        self.assertTrue(first == second)
        self.assertFalse(first == third)
        self.assertFalse(first == fourth)
        self.assertFalse(first == fifth)
