from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import RetractableDeviceState
from numpy.testing import assert_equal, assert_almost_equal
import numpy
import time
import os
import math
import unittest


class SystemFamily:
    TENEO = "Teneo"
    VERSA3D = "Versa"
    QUANTA = "Quanta"
    QUANTA_FEG = "Quanta FEG"
    HELIOS = "Helios"
    HELIOS_1200 = "Helios 1200"
    HELIOS_PFIB_HYDRA = "Hydra"
    PLUTO = "Pluto"
    APREO = "Apreo"
    PRISMA = "Prisma"
    QUATTRO = "Quattro"
    SCIOS = "Scios"
    SCIOS_2 = "Scios 2"
    AQUILOS = "Aquilos"
    CRYOFIB = "CryoFIB"
    VERIOS = "Verios"
    NOVA_NANO_SEM = "Nova NanoSEM"
    AXIA = "Axia"


class TestHelper:

    def __init__(self, test_case: unittest.TestCase, microscope: SdbMicroscopeClient = None):
        self.__system_name = None
        self.__major_system_version = None
        self.__is_offline = None
        self.test_case = test_case
        self.microscope = microscope

    def assert_point(self, actual_point, expected_point):
        assert_almost_equal(actual_point.x, expected_point.x, decimal=5)
        assert_almost_equal(actual_point.y, expected_point.y, decimal=5)

    def assert_position(self, actual_position, expected_position):
        if actual_position.x is not None or expected_position.x is not None:
            assert_almost_equal(actual_position.x, expected_position.x, decimal=5)
        if actual_position.y is not None or expected_position.y is not None:
            assert_almost_equal(actual_position.y, expected_position.y, decimal=5)
        if actual_position.z is not None or expected_position.z is not None:
            assert_almost_equal(actual_position.z, expected_position.z, decimal=5)
        if actual_position.r is not None or expected_position.r is not None:
            assert_almost_equal(actual_position.r, expected_position.r, decimal=5)
        if actual_position.t is not None or expected_position.t is not None:
            assert_almost_equal(actual_position.t, expected_position.t, decimal=5)

    def assert_points_almost_equal(self, expected_point, given_point, number_precision):
        self.test_case.assertAlmostEqual(expected_point.x, given_point.x, number_precision)
        self.test_case.assertAlmostEqual(expected_point.y, given_point.y, number_precision)

    def assert_valid_image(self, image: AdornedImage):
        self.test_case.assertIsNotNone(image)
        self.test_case.assertGreater(image.width, 0)
        self.test_case.assertGreater(image.height, 0)
        self.test_case.assertGreater(image.bit_depth, 0)
        self.test_case.assertGreater(numpy.average(image.data), 0)

    def assert_image(self, image, expected_width=None, expected_height=None, expected_bit_depth=None, expected_encoding=None):
        if expected_width is not None:
            assert_equal(expected_width, image.width)
        if expected_height is not None:
            assert_equal(expected_height, image.height)
        if expected_bit_depth is not None:
            assert_equal(expected_bit_depth, image.bit_depth)
        if expected_encoding is not None:
            assert_equal(expected_encoding, image.encoding)

    def assert_image_has_basic_metadata(self, image):
        assert_equal(type(image.metadata.metadata_as_ini), str)
        assert_equal(type(image.metadata.optics.scan_field_of_view.width), float)
        assert_equal(type(image.metadata.optics.scan_field_of_view.width), float)

    def assert_angles_almost_equal(self, angle_actual, angle_expected):
        tau = 2 * math.pi
        delta_angle_normalized = (angle_expected - angle_actual + math.pi + tau) % tau - math.pi
        assert_almost_equal(delta_angle_normalized, 0, 3)

    def assert_value_in_limits(self, value: float, limits: Limits):
        if value < limits.min or value > limits.max:
            raise ValueError(f"Value {value} is outside limits {limits}")

    def test_generic_setting(self, node, name, values, number_precision=None):
        """
        Tests generic setting represented by the given node using the given values.

        The method takes care of changing the setting, asserting successful change
        as well as writing traces during the whole operation.

        :param number_precision: Number of decimal places to check when comparing numbers.
        """

        for value in values:
            print("Setting " + name + " to " + str(value) + "...")
            node.value = value

            if number_precision is not None:
                if isinstance(value, Point):
                    self.assert_points_almost_equal(value, node.value, number_precision)
                else:
                    self.test_case.assertAlmostEqual(value, node.value, number_precision)
            else:
                self.test_case.assertEqual(value, node.value)

    def test_insert_retract_device(self, device, device_name):
        """
        Tests the given retractable device ability to perform insert/retract operations.

        Each operation is attempted twice subsequently in order to check that the device does not report failure
        when it is already in target state, which is a user requirement.

        :param device: Retractable device to be tested, expected to implement insert() and retract() methods.
        :param device_name: Name of the given retractable device to be used for logging.
        """

        settle_time = 0.5
        has_state = hasattr(device, 'state')

        print("Inserting %s..." % device_name)
        device.insert()
        time.sleep(settle_time)
        if has_state:
            self.test_case.assertEqual(device.state, RetractableDeviceState.INSERTED)
            print("Device %s is in state %s" % (device_name, device.state))

        print("Inserting %s again..." % device_name)
        device.insert()
        time.sleep(settle_time)

        print("Retracting %s..." % device_name)
        device.retract()
        time.sleep(settle_time)
        if has_state:
            self.test_case.assertEqual(device.state, RetractableDeviceState.RETRACTED)
            print("Device %s is in state %s" % (device_name, device.state))

        print("Retracting %s again..." % device_name)
        device.retract()
        time.sleep(settle_time)

    def is_micro_heater_installed(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value("Devices.MicroHeater.Installed") == "True"

    def is_ccd_installed(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value("Devices.CCD.Installed") == "True"

    def is_navcam_installed(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value("Devices.NavCam.Installed") == "True"

    def is_multichem_installed(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value("Devices.Multichem.Installed") == "True"

    def is_optical_microscope_installed(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value("Devices.OpticalMicroscope.Installed") == "True"

    def is_system(self, names) -> bool:
        system_name = self.get_system_name()

        if isinstance(names, str):
            return names in system_name

        for name in names:
            if name in system_name:
                return True

        return False

    def is_system_version(self, versions) -> bool:
        if isinstance(versions, int):
            return versions == self.get_major_system_version()

        for version in versions:
            if version == self.get_major_system_version():
                return True

        return False

    def is_system_plasma_fib(self):
        system_name = self.get_system_name()
        is_plasma = "PFIB" in system_name or "Hydra" in system_name or self.is_system(SystemFamily.CRYOFIB)
        return is_plasma

    def is_offline(self):
        if self.__is_offline is None:
            self.__is_offline = self.microscope.service.autoscript.server.is_offline

        return self.__is_offline

    def get_system_eucentric_height(self) -> float:
        if self.is_system([SystemFamily.QUANTA, SystemFamily.VERSA3D, SystemFamily.APREO, SystemFamily.PRISMA, SystemFamily.QUATTRO,
                           SystemFamily.TENEO, SystemFamily.AXIA]):
            return 0.010
        elif self.is_system([SystemFamily.SCIOS, SystemFamily.AQUILOS]):
            return 0.007
        elif self.is_system(SystemFamily.NOVA_NANO_SEM):
            return 0.005
        else:
            return 0.004

    def get_system_name(self):
        if self.__system_name is None:
            self.__system_name = self.microscope.service.system.name
        return self.__system_name

    def get_major_system_version(self):
        if self.__major_system_version is None:
            self.__major_system_version = int(self.microscope.service.system.version.split('.')[0])
        return self.__major_system_version

    def provide_lenna_gray8(self):
        lenna_bgr = self.provide_lenna_bgr()
        lenna_gray8 = cv2.cvtColor(lenna_bgr, cv2.COLOR_BGR2GRAY)
        return lenna_gray8

    def provide_lenna_gray16(self):
        lenna_bgr = self.provide_lenna_gray8()
        lenna_gray16 = numpy.array(lenna_bgr, dtype=numpy.uint16)
        lenna_gray16 *= 256
        return lenna_gray16

    def provide_lenna_rgb(self):
        lenna_bgr = self.provide_lenna_bgr()
        lenna_rgb = lenna_bgr[..., ::-1]
        return lenna_rgb

    def provide_lenna_bgr(self):
        lenna_path = self.get_resource_path("lenna.png")
        lenna_bgr = cv2.imread(lenna_path)
        return lenna_bgr

    def extract_lenna_face_region(self, lenna):
        face_region = lenna[200:400, 225:375]
        return face_region

    def get_resource_path(self, file_name) -> str:
        """
        Returns full path of specified resource.

        :param file_name: Name of the resource file.
        :return: Full path of the resource file.
        """

        root_path = os.path.split(__file__)[0]
        return os.path.join(root_path, "resources", file_name)

    def get_precision_for_decimal_places(self, value, decimal_places):
        exponent = numpy.floor(numpy.log10(numpy.abs(value)))
        precision = int(numpy.abs(exponent)) + decimal_places
        return precision
