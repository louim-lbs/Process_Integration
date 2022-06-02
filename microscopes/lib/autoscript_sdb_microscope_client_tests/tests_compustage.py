from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
import math
import unittest


class TestsCompustage(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)

    def tearDown(self):
        pass

    initial_position = CompustagePosition(0.0001, 0.0002, 0.004, math.radians(90), math.radians(0))

    def test_load_rod(self):
        print("Loading Compustage rod...")
        # There's no standard api for controlling rod, use server configuration interface
        self.microscope.service.autoscript.server.configuration.set_value("Devices.Compustage.RodLoaded", "True")
        print("Compustage is operative.")

    def test_unload_rod(self):
        print("Unloading Compustage rod...")
        # There's no standard api for controlling rod, use server configuration interface
        self.microscope.service.autoscript.server.configuration.set_value("Devices.Compustage.RodLoaded", "False")
        print("Compustage rod unloaded successfully.")

        print("Retracting compustage...")
        self.microscope.specimen.compustage.retract()

        print("Moving bulk stage to origin, this will activate bulk stage...")
        self.microscope.specimen.stage.absolute_move(StagePosition(x=0, y=0))
        print("Done.")

    def test_insert_retract(self):
        print("Inserting Compustage...")
        self.microscope.specimen.compustage.insert()
        print("Attempting to insert Compustage again...")
        self.microscope.specimen.compustage.insert()

        print("Retracting Compustage...")
        self.microscope.specimen.compustage.retract()
        print("Attempting to retract Compustage again...")
        self.microscope.specimen.compustage.retract()

    def test_absolute_move_xy(self):
        print("Performing absolute move in X, Y axes...")
        target_position = CompustagePosition(0.0002, 0.0003, 0.004)
        self.microscope.specimen.compustage.absolute_move(target_position)

        actual_position = self.microscope.specimen.compustage.current_position
        self.__assert_compustage_coordinates(actual_position, target_position.x, target_position.y)

    def test_absolute_move_ab(self):
        print("Performing absolute move in A, B axes...")
        target_position = CompustagePosition(a=math.radians(80), b=math.radians(-5))
        self.microscope.specimen.compustage.absolute_move(target_position)

        actual_position = self.microscope.specimen.compustage.current_position
        self.__assert_compustage_coordinates(actual_position, expected_a=target_position.a, expected_b=target_position.b)

    def test_relative_move_xy(self):
        print("Moving Compustage to initial position...")
        self.microscope.specimen.compustage.absolute_move(self.initial_position)

        previous_position = self.microscope.specimen.compustage.current_position

        print("Performing relative move in X, Y axes...")
        delta_position = CompustagePosition(0.0001, 0.0002)
        self.microscope.specimen.compustage.relative_move(delta_position)

        actual_position = self.microscope.specimen.compustage.current_position
        self.__assert_compustage_coordinates(actual_position, previous_position.x + delta_position.x, previous_position.y + delta_position.y)

    def test_relative_move_ab(self):
        print("Moving Compustage to initial position...")
        self.microscope.specimen.compustage.absolute_move(self.initial_position)

        previous_position = self.microscope.specimen.compustage.current_position
        print("Performing relative move in A, B axes...")
        delta_position = CompustagePosition(a=math.radians(5), b=math.radians(10))
        self.microscope.specimen.compustage.relative_move(delta_position)

        actual_position = self.microscope.specimen.compustage.current_position
        self.__assert_compustage_coordinates(actual_position, expected_a=previous_position.a + delta_position.a, expected_b=previous_position.b + delta_position.b)

    def test_neutral_mill_position(self):
        target_value = 0.5
        print("Setting neutral mill position value...")
        self.microscope.specimen.compustage.neutral_mill_position.value = target_value
        actual_value = self.microscope.specimen.compustage.neutral_mill_position.value
        self.assertEqual(target_value, actual_value, "Neutral mill position value is incorrect.")

    def test2_neutral_mill_position(self):
        target_value = math.degrees(self.microscope.specimen.compustage.current_position.a)
        print("Setting neutral mill position to alfa axis value...")
        self.microscope.specimen.compustage.neutral_mill_position.set()
        actual_value = math.degrees(self.microscope.specimen.compustage.neutral_mill_position.value)
        self.assertEqual(target_value, actual_value, "Neutral mill position value is incorrect.")

    def test_compucentric_flip(self):
        self.microscope.specimen.compustage.absolute_move(self.initial_position)

        print("Performing compucentric flip...")
        previous_position = self.microscope.specimen.compustage.current_position
        self.microscope.specimen.compustage.flip()
        actual_position = self.microscope.specimen.compustage.current_position

        self.__assert_compustage_coordinates(actual_position, expected_x=previous_position.x * -1, expected_b=previous_position.b + math.radians(-180))

    def test_compustage_home(self):
        print("Retracting Compustage...")
        self.microscope.specimen.compustage.retract()

        print("Homing compustage...")
        self.microscope.specimen.compustage.home()

        is_homed = self.microscope.specimen.compustage.is_homed
        self.assertTrue(is_homed)

        print("Inserting compustage...")
        self.microscope.specimen.compustage.insert()

        print("Moving Compustage to initial position...")
        self.microscope.specimen.compustage.absolute_move(self.initial_position)

    def test_compustage_link(self):
        print("Preparing environment...")
        self.microscope.imaging.start_acquisition()
        self.microscope.beams.electron_beam.turn_on()
        self.microscope.beams.electron_beam.unblank()
        self.microscope.beams.electron_beam.scanning.mode.set_full_frame()

        print("Moving Compustage to initial position...")
        self.microscope.specimen.compustage.absolute_move(self.initial_position)

        is_linked = self.microscope.specimen.compustage.is_linked
        if is_linked:
            self.microscope.specimen.compustage.absolute_move(CompustagePosition(z=0.0035))

        print("Linking Compustage Z to WD...")
        self.microscope.specimen.compustage.link()
        is_linked = self.microscope.specimen.compustage.is_linked
        self.assertTrue(is_linked)

    def test_compustage_zy_link(self):
        initial_position_z_y_link = CompustagePosition(0.0001, 0.0002, 0.003, math.radians(45), math.radians(0))
        self.microscope.specimen.compustage.absolute_move(initial_position_z_y_link)
        previous_position = self.microscope.specimen.compustage.current_position
        settings = MoveSettings(link_z_y=True)
        new_a_position = CompustagePosition(a=math.radians(90))
        old_a_position = CompustagePosition(a=initial_position_z_y_link.a)
        print("Moving Compustage in alpha tilt with z-y link option enabled...")
        self.microscope.specimen.compustage.absolute_move(new_a_position, settings)
        print("Moving Compustage in alpha tilt back to previous position with z-y link option enabled...")
        self.microscope.specimen.compustage.absolute_move(old_a_position, settings)
        actual_position = self.microscope.specimen.compustage.current_position
        self.assertNotEqual(previous_position.y, actual_position.y,
                            "Y position do not differ from initial position although z-y compensation was enabled")
        self.assertNotEqual(previous_position.z, actual_position.z,
                            "Z position do not differ from initial position although z-y compensation was enabled")

    def test_compustage_zb_link(self):
        print("Moving Compustage to initial position...")
        self.microscope.specimen.compustage.absolute_move(self.initial_position)

        previous_position = self.microscope.specimen.compustage.current_position
        settings = MoveSettings(link_z_b=True)
        new_z_position = CompustagePosition(z=0.003)
        print("Moving Compustage in z axis with z-beta link option enabled...")
        self.microscope.specimen.compustage.absolute_move(new_z_position, settings)
        actual_position = self.microscope.specimen.compustage.current_position
        self.assertNotEqual(previous_position.b, actual_position.b, "Beta position didn't change, although z-beta compensation was enabled")

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