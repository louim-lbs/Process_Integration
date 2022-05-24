from autoscript_core.common import ApplicationServerException
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import math
import unittest


class TestsSpecimenCompustage(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)

    def tearDown(self):
        pass

    def test_load_rod(self):
        if self.test_helper.is_system(SystemFamily.CRYOFIB):
            self.skipTest("The compustage is not retractable on CryoFIB, skipping")

        print("Loading Compustage rod...")
        # There's no standard api for controlling the rod, use server configuration interface
        self.microscope.service.autoscript.server.configuration.set_value("Devices.Compustage.RodLoaded", "True")
        print("Compustage is operative.")

    def test_unload_rod(self):
        if self.test_helper.is_system(SystemFamily.CRYOFIB):
            self.skipTest("The compustage is not retractable on CryoFIB, skipping")

        print("Unloading Compustage rod...")
        # There's no standard api for controlling the rod, we have to use the server configuration interface
        self.microscope.service.autoscript.server.configuration.set_value("Devices.Compustage.RodLoaded", "False")
        print("Compustage rod unloaded successfully.")

        print("Retracting compustage...")
        self.microscope.specimen.compustage.retract()
        print("Success.")

        print("Moving bulk stage to origin, this will activate bulk stage...")
        self.microscope.specimen.stage.absolute_move(StagePosition(x=0, y=0))
        print("Done.")

    def test_insert_retract(self):
        if self.test_helper.is_system(SystemFamily.CRYOFIB):
            self.skipTest("The compustage is not retractable on CryoFIB, skipping")

        compustage = self.microscope.specimen.compustage

        print("Inserting Compustage...")
        compustage.insert()
        print("Success.")

        print("Attempting to insert Compustage again...")
        compustage.insert()
        print("Success.")

        print("Retracting Compustage...")
        compustage.retract()
        print("Success.")

        print("Attempting to retract Compustage again...")
        compustage.retract()
        print("Done.")

    def test_absolute_move_xy(self):
        compustage = self.microscope.specimen.compustage

        print("Performing absolute move in X, Y axes...")

        if self.test_helper.is_system(SystemFamily.CRYOFIB):
            target_position = CompustagePosition(0.0002, 0.0003, 0.0007)
        else:
            target_position = CompustagePosition(0.0002, 0.0003, 0.004)

        compustage.absolute_move(target_position)
        actual_position = compustage.current_position
        self.__assert_compustage_coordinates(actual_position, target_position.x, target_position.y)
        print("Done.")

    def test_absolute_move_ab(self):
        compustage = self.microscope.specimen.compustage

        print("Performing absolute move in A, B axes...")

        if self.test_helper.is_system(SystemFamily.CRYOFIB):
            target_position = CompustagePosition(a=math.radians(8))
        else:
            target_position = CompustagePosition(a=math.radians(80), b=math.radians(-5))

        compustage.absolute_move(target_position)
        actual_position = compustage.current_position
        self.__assert_compustage_coordinates(actual_position, expected_a=target_position.a, expected_b=target_position.b)
        print("Done.")

    def test_relative_move_xy(self):
        compustage = self.microscope.specimen.compustage

        self.__move_to_initial_position()

        print("Performing relative move in X, Y axes...")
        previous_position = compustage.current_position
        delta_position = CompustagePosition(0.0001, 0.0002)
        compustage.relative_move(delta_position)
        actual_position = compustage.current_position
        self.__assert_compustage_coordinates(actual_position, previous_position.x + delta_position.x, previous_position.y + delta_position.y)
        print("Done.")

    def test_relative_move_ab(self):
        compustage = self.microscope.specimen.compustage

        self.__move_to_initial_position()

        if self.test_helper.is_system(SystemFamily.CRYOFIB):
            print("Performing relative move in A axis...")
            previous_position = compustage.current_position
            delta_position = CompustagePosition(a=math.radians(5))
            compustage.relative_move(delta_position)
            actual_position = compustage.current_position
            self.__assert_compustage_coordinates(actual_position, expected_a=previous_position.a + delta_position.a)
        else:
            print("Performing relative move in A, B axes...")
            previous_position = compustage.current_position
            delta_position = CompustagePosition(a=math.radians(5), b=math.radians(10))
            compustage.relative_move(delta_position)
            actual_position = compustage.current_position
            self.__assert_compustage_coordinates(actual_position, expected_a=previous_position.a + delta_position.a, expected_b=previous_position.b + delta_position.b)

        print("Done.")

    def test_neutral_mill_position(self):
        compustage = self.microscope.specimen.compustage

        print("Setting neutral mill position value...")
        target_value = 0.5
        compustage.neutral_mill_position.value = target_value
        actual_value = compustage.neutral_mill_position.value
        self.assertEqual(target_value, actual_value, "Neutral mill position value is incorrect.")
        print("Success.")

        print("Setting neutral mill position to alfa axis value...")
        target_value = math.degrees(compustage.current_position.a)
        compustage.neutral_mill_position.set()
        actual_value = math.degrees(compustage.neutral_mill_position.value)
        self.assertEqual(target_value, actual_value, "Neutral mill position value is incorrect.")
        print("Done.")

    def test_compucentric_flip(self):
        if self.test_helper.is_system(SystemFamily.CRYOFIB):
            self.skipTest("Flipping the compustage is not supported on CryoFIB, skipping")

        compustage = self.microscope.specimen.compustage

        print("Performing compucentric flips...")
        target_position = CompustagePosition(x=0.0001)
        target_position.b = 10 * math.pi / 180.0
        compustage.absolute_move(target_position)
        compustage.flip()
        self.__assert_compustage_coordinates(compustage.current_position, expected_x=-0.0001, expected_b=math.radians(-170))

        target_position.b = -89 * math.pi / 180.0
        compustage.absolute_move(target_position)
        compustage.flip()
        self.__assert_compustage_coordinates(compustage.current_position, expected_b=math.radians(-190))

        target_position.b = -90 * math.pi / 180.0
        compustage.absolute_move(target_position)
        compustage.flip()
        self.__assert_compustage_coordinates(compustage.current_position, expected_b=math.radians(50))

        target_position.b = -175 * math.pi / 180.0
        compustage.absolute_move(target_position)
        compustage.flip()
        self.__assert_compustage_coordinates(compustage.current_position, expected_b=math.radians(5))

        print("Done.")

    def test_compustage_home(self):
        compustage = self.microscope.specimen.compustage

        if not self.test_helper.is_system(SystemFamily.CRYOFIB):
            print("Retracting Compustage...")
            compustage.retract()
            print("Success.")

        print("Homing compustage...")
        compustage.home()
        self.assertTrue(compustage.is_homed)
        print("Success.")

        if not self.test_helper.is_system(SystemFamily.CRYOFIB):
            print("Inserting compustage...")
            compustage.insert()
            print("Success.")

        self.__move_to_initial_position()

    def test_compustage_link(self):
        if self.test_helper.is_system(SystemFamily.CRYOFIB):
            self.skipTest("Linking compustage is not supported on CryoFIB, skipping")

        compustage = self.microscope.specimen.compustage

        print("Preparing environment...")
        self.microscope.imaging.start_acquisition()
        self.microscope.beams.electron_beam.turn_on()
        self.microscope.beams.electron_beam.unblank()
        self.microscope.beams.electron_beam.scanning.mode.set_full_frame()
        print("Success.")

        self.__move_to_initial_position()

        is_linked = compustage.is_linked
        if is_linked:
            compustage.absolute_move(CompustagePosition(z=0.0035))
            print("Success.")

        print("Linking Compustage Z to WD...")
        compustage.link()
        self.assertTrue(compustage.is_linked)
        print("Done.")

    def test_compustage_zy_link(self):
        if self.test_helper.is_system(SystemFamily.CRYOFIB):
            # TODO: Remove this once the LinkZY support is implemented on CryoFIB
            self.skipTest("Linking compustage is not (yet) supported on CryoFIB, skipping")

        print("Moving Compustage to initial position...")
        compustage = self.microscope.specimen.compustage
        initial_position_z_y_link = CompustagePosition(0.0001, 0.0002, 0.003, math.radians(45), math.radians(0))
        compustage.absolute_move(initial_position_z_y_link)
        print("Success.")

        print("Moving Compustage in alpha tilt with z-y link option enabled...")
        previous_position = compustage.current_position
        settings = MoveSettings(link_z_y=True)
        new_a_position = CompustagePosition(a=math.radians(90))
        old_a_position = CompustagePosition(a=initial_position_z_y_link.a)
        compustage.absolute_move(new_a_position, settings)
        print("Success.")

        print("Moving Compustage in alpha tilt back to previous position with z-y link option enabled...")
        compustage.absolute_move(old_a_position, settings)
        actual_position = compustage.current_position
        self.assertNotEqual(previous_position.y, actual_position.y, "Y position do not differ from initial position although z-y compensation was enabled")
        self.assertNotEqual(previous_position.z, actual_position.z, "Z position do not differ from initial position although z-y compensation was enabled")
        print("Done.")

    def test_compustage_zb_link(self):
        compustage = self.microscope.specimen.compustage

        # CryoFIB does not support LinkZB correction
        if self.test_helper.is_system(SystemFamily.CRYOFIB):
            with self.assertRaisesRegex(ApplicationServerException, "not supported"):
                compustage.absolute_move(CompustagePosition(z=0.003), MoveSettings(link_z_b=True))
            self.skipTest("Not supported on CryoFIB, skipping")

        self.__move_to_initial_position()

        print("Moving Compustage in z axis with z-beta link option enabled...")
        previous_position = compustage.current_position
        settings = MoveSettings(link_z_b=True)
        new_z_position = CompustagePosition(z=0.003)
        compustage.absolute_move(new_z_position, settings)
        actual_position = compustage.current_position
        self.assertNotEqual(previous_position.b, actual_position.b, "Beta position didn't change, although z-beta compensation was enabled")
        print("Done.")

    def __assert_compustage_coordinates(self, actual_position, expected_x=None, expected_y=None, expected_z=None, expected_a=None, expected_b=None):
        if expected_x is not None:
            self.assertAlmostEqual(expected_x, actual_position.x, places=5)
        if expected_y is not None:
            self.assertAlmostEqual(expected_y, actual_position.y, places=5)
        if expected_z is not None:
            self.assertAlmostEqual(expected_z, actual_position.z, places=5)
        if expected_a is not None:
            self.assertAlmostEqual(expected_a, actual_position.a, places=5)
        if expected_b is not None:
            self.assertAlmostEqual(expected_b, actual_position.b, places=5)

    def __assert_compustage_position(self, actual_position: CompustagePosition, expected_position: CompustagePosition):
        self.__assert_compustage_coordinates(actual_position, expected_position.x, expected_position.y, expected_position.z,
                                             expected_position.a, expected_position.b)

    def __move_to_initial_position(self):
        print("Moving Compustage to initial position...")

        if self.test_helper.is_system(SystemFamily.CRYOFIB):
            initial_position = CompustagePosition(0.0001, 0.0002, 0.0007, math.radians(0))
        else:
            initial_position = CompustagePosition(0.0001, 0.0002, 0.004, math.radians(90), math.radians(0))

        compustage = self.microscope.specimen.compustage
        compustage.absolute_move(initial_position)
        self.__assert_compustage_position(compustage.current_position, initial_position)
        print("Success.")
