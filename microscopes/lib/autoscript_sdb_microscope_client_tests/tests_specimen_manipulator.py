from autoscript_core.common import ApplicationServerException
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import math
import time
import unittest


class TestsSpecimenManipulator(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)

    def tearDown(self):
        pass

    def test_insert_retract_manipulator(self):
        manipulator = self.microscope.specimen.manipulator
        stage = self.microscope.specimen.stage

        if not stage.is_linked:
            self.test_helper.link_z_to_fwd()

        safe_z = self.test_helper.get_system_eucentric_height() + 0.001
        position = stage.current_position
        if abs(position.z - safe_z) > 0.0005:
            print("Moving stage to safe Z...")
            stage.absolute_move(StagePosition(z=safe_z))
            print("Success.")

        print("Inserting manipulator...")
        manipulator.insert()
        print("Success.")

        time.sleep(1)

        print("Retracting manipulator...")
        manipulator.retract()
        print("Success.")

    def test_move_manipulator(self):
        manipulator = self.microscope.specimen.manipulator

        # Assuming the stage is linked and in safe position from previous test

        print("Inserting manipulator...")
        manipulator.insert()
        print("Success.")

        print("Reading current position...")
        manipulator.set_default_coordinate_system(ManipulatorCoordinateSystem.STAGE)
        self.origin_position = manipulator.current_position
        print("    Position in stage system:", self.origin_position)
        manipulator.set_default_coordinate_system(ManipulatorCoordinateSystem.RAW)
        print("    Position in raw system:", manipulator.current_position)

        print("Performing absolute move in stage coordinate system...")
        manipulator.set_default_coordinate_system(ManipulatorCoordinateSystem.STAGE)
        current_position = manipulator.current_position
        target_position = ManipulatorPosition(x=current_position.x + 0.0001, y=current_position.y + 0.0001, z=current_position.z + 0.0001)

        # Rotation is not supported on Aquilos
        if self.test_helper.is_system([SystemFamily.AQUILOS]) is False:
            target_position.r = math.radians(2)
        else:
            with self.assertRaisesRegex(ApplicationServerException, "cannot be rotated"):
                print("Rotating manipulator on Aquilos should throw...")
                invalid_position = ManipulatorPosition(x=current_position.x + 0.0001, y=current_position.y + 0.0001, z=current_position.z + 0.0001, r=math.radians(2))
                manipulator.absolute_move(invalid_position)

        manipulator.absolute_move(target_position)
        self.__assert_manipulator_coordinates(manipulator.current_position, target_position)
        print("Success.")

        self.__move_to_origin()

        print("Performing absolute move in raw coordinate system...")
        manipulator.set_default_coordinate_system(ManipulatorCoordinateSystem.RAW)
        current_position = manipulator.current_position
        target_position = ManipulatorPosition(x=current_position.x - 0.0001, y=current_position.y - 0.00001, z=current_position.z)

        # Rotation is not supported on Aquilos
        if self.test_helper.is_system([SystemFamily.AQUILOS]) is False:
            target_position.r = math.radians(4)

        manipulator.absolute_move(target_position)
        self.__assert_manipulator_coordinates(manipulator.current_position, target_position)
        print("Success.")

        self.__move_to_origin()

        print("Performing relative move in stage coordinate system...")
        manipulator.set_default_coordinate_system(ManipulatorCoordinateSystem.STAGE)
        current_position = manipulator.current_position
        relative_position = ManipulatorPosition(x=0.0001, y=0.0001, z=0.0001)

        # Rotation is not supported on Aquilos
        if self.test_helper.is_system([SystemFamily.AQUILOS]) is False:
            relative_position.r = math.radians(2)
        else:
            with self.assertRaisesRegex(ApplicationServerException, "cannot be rotated"):
                print("Rotating manipulator on Aquilos should throw...")
                invalid_position = ManipulatorPosition(x=0.0001, y=0.0001, z=0.0001, r=math.radians(2))
                manipulator.relative_move(invalid_position)

        target_position = current_position + relative_position

        manipulator.relative_move(relative_position)
        self.__assert_manipulator_coordinates(manipulator.current_position, target_position)
        print("Success.")

        self.__move_to_origin()

        print("Performing relative move in raw coordinate system...")
        manipulator.set_default_coordinate_system(ManipulatorCoordinateSystem.RAW)
        current_position = manipulator.current_position
        relative_position = ManipulatorPosition(x=0.0001, y=0.0001, z=0.0001)

        # Rotation is not supported on Aquilos
        if self.test_helper.is_system([SystemFamily.AQUILOS]) is False:
            relative_position.r = math.radians(2)

        target_position = current_position + relative_position

        manipulator.relative_move(relative_position)
        self.__assert_manipulator_coordinates(manipulator.current_position, target_position)
        print("Success.")

        self.__move_to_origin()

        time.sleep(1)

        print("Retracting manipulator...")
        manipulator.retract()
        print("Done.")

    def __move_to_origin(self):
        print("Moving to origin...")
        manipulator = self.microscope.specimen.manipulator
        manipulator.set_default_coordinate_system(ManipulatorCoordinateSystem.STAGE)

        # Rotation is not supported on Aquilos
        if self.test_helper.is_system([SystemFamily.AQUILOS]) is True:
            self.origin_position.r = None

        manipulator.absolute_move(self.origin_position)
        print("Success.")

    def __assert_manipulator_coordinates(self, actual_position, expected_position):
        if expected_position.x is not None:
            self.assertAlmostEqual(expected_position.x, actual_position.x, delta=0.00009)
        if expected_position.y is not None:
            self.assertAlmostEqual(expected_position.y, actual_position.y, delta=0.00009)
        if expected_position.z is not None:
            self.assertAlmostEqual(expected_position.z, actual_position.z, delta=0.00009)
        if expected_position.r is not None:
            self.assertAlmostEqual(expected_position.r, actual_position.r, delta=0.0009)
