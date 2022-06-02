from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
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

    def assert_stage_position(self, actual_position: StagePosition, expected_position: StagePosition):
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

    def assert_compustage_position(self, actual_position: CompustagePosition, expected_position: CompustagePosition):
        if actual_position.x is not None or expected_position.x is not None:
            assert_almost_equal(actual_position.x, expected_position.x, decimal=5)
        if actual_position.y is not None or expected_position.y is not None:
            assert_almost_equal(actual_position.y, expected_position.y, decimal=5)
        if actual_position.z is not None or expected_position.z is not None:
            assert_almost_equal(actual_position.z, expected_position.z, decimal=5)
        if actual_position.a is not None or expected_position.a is not None:
            assert_almost_equal(actual_position.a, expected_position.a, decimal=5)
        if actual_position.b is not None or expected_position.b is not None:
            assert_almost_equal(actual_position.b, expected_position.b, decimal=5)

    def assert_manipulator_position(self, actual_position: ManipulatorPosition, expected_position: ManipulatorPosition):
        if actual_position.x is not None or expected_position.x is not None:
            assert_almost_equal(actual_position.x, expected_position.x, decimal=5)
        if actual_position.y is not None or expected_position.y is not None:
            assert_almost_equal(actual_position.y, expected_position.y, decimal=5)
        if actual_position.z is not None or expected_position.z is not None:
            assert_almost_equal(actual_position.z, expected_position.z, decimal=5)
        if actual_position.r is not None or expected_position.r is not None:
            assert_almost_equal(actual_position.r, expected_position.r, decimal=3)

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

    def assert_image_file(self, file_path, expected_minimum_file_size=None, expected_width=None, expected_height=None, expected_bit_depth=None):
        file_exists = os.path.exists(file_path)
        self.test_case.assertTrue(file_exists, f"File {file_path} was not found")

        if expected_minimum_file_size is not None:
            stat_info = os.stat(file_path)
            self.test_case.assertGreaterEqual(stat_info.st_size, expected_minimum_file_size,
                                              f"Image file {file_path} was found but has incorrect size of {stat_info.st_size} instead of {expected_minimum_file_size}")

        if file_path.endswith(".tiff") or file_path.endswith(".tif"):
            image = AdornedImage.load(file_path)
            self.assert_image(image, expected_width, expected_height, expected_bit_depth)

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

    def assert_string_contains(self, string: str, sub_string: str):
        assert_equal(sub_string in string, True)

    def test_generic_setting(self, node, name, values, number_precision=None):
        """
        Tests generic setting represented by the given node using the given values.

        The method takes care of changing the setting, asserting successful change
        as well as writing traces during the whole operation.

        :param values:
        :param name:
        :param node:
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

    def get_stage_configuration_key(self, stage_type) -> str:
        if stage_type == TemperatureStageType.HEATING_STAGE:
            return "Devices.HeatingStage"
        elif stage_type == TemperatureStageType.COOLING_STAGE:
            return "Devices.CoolingStage"
        elif stage_type == TemperatureStageType.HIGH_VACUUM_HEATING_STAGE:
            return "Devices.HighVacuumHeatingStage"
        elif stage_type == TemperatureStageType.MICRO_HEATER:
            return "Devices.MicroHeater"
        raise ValueError("Unknown stage type.")

    def is_temperature_stage_installed(self, stage_type) -> bool:
        configuration_key = self.get_stage_configuration_key(stage_type) + ".Installed"
        is_installed = self.microscope.service.autoscript.server.configuration.get_value(configuration_key) == "True"
        return is_installed

    def is_temperature_stage_connected(self, stage_type) -> bool:
        configuration_key = self.get_stage_configuration_key(stage_type) + ".Connected"
        is_connected = self.microscope.service.autoscript.server.configuration.get_value(configuration_key) == "True"
        return is_connected

    def connect_temperature_stage(self, stage_type):
        configuration_key = self.get_stage_configuration_key(stage_type) + ".Connected"
        self.microscope.service.autoscript.server.configuration.set_value(configuration_key, "True")

    def disconnect_temperature_stage(self, stage_type):
        configuration_key = self.get_stage_configuration_key(stage_type) + ".Connected"
        self.microscope.service.autoscript.server.configuration.set_value(configuration_key, "False")

    @property
    def is_ccd_installed(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value("Devices.CCD.Installed") == "True"

    @property
    def is_navcam_installed(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value("Devices.NavCam.Installed") == "True"

    @property
    def is_multichem_installed(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value("Devices.MultiChem.Installed") == "True"

    @property
    def is_optical_microscope_installed(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value("Devices.OpticalMicroscope.Installed") == "True"

    @property
    def is_beam_deceleration_installed(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value("Devices.BeamDeceleration.Installed") == "True"

    @property
    def is_multi_ion_species_gun_installed(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value("Devices.MultiIonSpecies.Installed") == "True"

    @property
    def is_mirror_detector_shutter_installed(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value("Devices.MirrorDetectorShutter.Installed") == "True"

    @property
    def is_gis_installed(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value("Devices.Gis.Installed") == "True"

    def is_detector_retractable(self, detector_name) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value(f"Detectors.{detector_name}.Retractable") == "True"

    @property
    def is_vacuum_mode_low_available(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value(f"Vacuum.Mode.LowVacuum.Available") == "True"

    @property
    def is_vacuum_mode_esem_available(self) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value(f"Vacuum.Mode.Esem.Available") == "True"

    def is_vacuum_gas_available(self, mode: str, gas: str) -> bool:
        return self.microscope.service.autoscript.server.configuration.get_value(f"Vacuum.Mode.{mode}.Gas.{gas}.Available") == "True"

    @property
    def is_vacuum_gas_water_available(self):
        return self.microscope.service.autoscript.server.configuration.get_value(f"Vacuum.Gas.Water.Available") == "True"

    @property
    def is_big_snapshot_supported(self):
        return self.microscope.service.autoscript.server.configuration.get_value(f"Features.Imaging.BigSnapshot.Supported") == "True"

    @property
    def is_big_snapshot_16bit_supported(self):
        return self.microscope.service.autoscript.server.configuration.get_value(f"Features.Imaging.BigSnapshot.16-bit.Supported") == "True"

    @property
    def is_big_snapshot_line_integration_supported(self):
        return self.microscope.service.autoscript.server.configuration.get_value(f"Features.Imaging.BigSnapshot.LineIntegration.Supported") == "True"

    @property
    def is_compucentric_tilt_supported(self):
        return self.microscope.service.autoscript.server.configuration.get_value(f"Features.Stage.CompucentricTilt.Supported") == "True"

    @property
    def is_link_zy_supported(self):
        return self.microscope.service.autoscript.server.configuration.get_value(f"Features.Stage.LinkZY.Supported") == "True"

    @property
    def is_pia4_or_newer_installed(self) -> bool:
        return self.get_system_major_version() >= 12

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
            return versions == self.get_system_major_version()

        for version in versions:
            if version == self.get_system_major_version():
                return True

        return False

    @property
    def is_system_plasma_fib(self) -> bool:
        system_name = self.get_system_name()
        is_plasma = "PFIB" in system_name or "Hydra" in system_name or self.is_system(SystemFamily.CRYOFIB)
        return is_plasma

    @property
    def is_offline(self) -> bool:
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
        elif self.is_system(SystemFamily.PLUTO):
            return 0.0043
        else:
            return 0.004

    def get_system_raw_z_for_linking(self) -> float:
        if self.is_system([SystemFamily.PLUTO]):
            return 0.0028
        else:
            return 0.007

    def get_system_name(self) -> str:
        if self.__system_name is None:
            self.__system_name = self.microscope.service.system.name
        return self.__system_name

    def get_system_major_version(self) -> int:
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

    def get_precision_for_decimal_places(self, value, decimal_places) -> float:
        exponent = numpy.floor(numpy.log10(numpy.abs(value)))
        precision = int(numpy.abs(exponent)) + decimal_places
        return precision

    def link_z_to_fwd(self):
        print("Linking Z to FWD...")
        self.microscope.imaging.set_active_view(1)
        self.microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)
        self.microscope.specimen.stage.unlink()
        raw_z = self.get_system_raw_z_for_linking()
        self.microscope.specimen.stage.absolute_move(StagePosition(z=raw_z, coordinate_system=CoordinateSystem.RAW))
        self.microscope.imaging.start_acquisition()
        wd = self.get_system_eucentric_height()
        self.microscope.beams.electron_beam.working_distance.value = wd
        self.microscope.specimen.stage.link()
        self.microscope.imaging.stop_acquisition()
        print("Success.")
