from autoscript_core.common import ApiException
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import math
import time
import unittest


class TestsStage(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)
        self.system_name = self.microscope.service.system.name

    def tearDown(self):
        pass

    def __assert_stage_coordinates(self, actual_position, expected_x=None, expected_y=None, expected_z=None, expected_r=None, expected_t=None):
        epsilon = 0.0009
        if expected_x is not None:
            self.assertAlmostEqual(expected_x, actual_position.x, delta=epsilon)
        if expected_y is not None:
            self.assertAlmostEqual(expected_y, actual_position.y, delta=epsilon)
        if expected_z is not None:
            self.assertAlmostEqual(expected_z, actual_position.z, delta=epsilon)
        if expected_t is not None:
            self.assertAlmostEqual(expected_t, actual_position.t, delta=epsilon)
        if expected_r is not None:
            self.test_helper.assert_angles_almost_equal(actual_position.r, expected_r)

    def __assert_stage_coordinates_equal(self, actual_position, expected_position):
        self.__assert_stage_coordinates(actual_position, expected_position.x, expected_position.y, expected_position.z, expected_position.r, expected_position.t)

    def test_home_stage(self):
        stage = self.microscope.specimen.stage

        if not stage.is_installed:
            self.skipTest("Bulk stage is not installed, skipping")

        print("Homing stage...")
        stage.home()
        self.assertTrue(stage.is_homed)
        self.__assert_stage_coordinates(stage.current_position, 0, 0, None, 0, 0)

    def test_home_axes(self):
        stage = self.microscope.specimen.stage

        if not stage.is_installed:
            self.skipTest("Bulk stage is not installed, skipping")

        print("Moving stage to non zero position...")
        target_position = StagePosition(x=0.001, y=-0.001, z=0.004, r=0.1)
        stage.absolute_move(target_position)
        self.__assert_stage_coordinates_equal(stage.current_position, target_position)

        print("Homing stage X and Y axes...")
        stage.home([StageAxis.X, StageAxis.Y])
        self.__assert_stage_coordinates(stage.current_position, 0, 0, target_position.z, target_position.r)

        print("Done.")

    def test_lock_axes(self):
        stage = self.microscope.specimen.stage

        if not stage.is_installed:
            self.skipTest("Bulk stage is not installed, skipping")

        print("Locking R axis...")
        stage.safety_settings.lock_axis("R")
        locked_axes = stage.safety_settings.locked_axes
        self.assertEqual(locked_axes, ["R"])
        print("Locked axes:", locked_axes)

        print("Locking Y axis...")
        stage.safety_settings.lock_axis("Y")
        locked_axes = stage.safety_settings.locked_axes
        self.assertEqual(locked_axes, ["Y", "R"])
        print("Locked axes:", locked_axes)

        print("Unlocking R axis...")
        stage.safety_settings.unlock_axis("R")
        locked_axes = stage.safety_settings.locked_axes
        self.assertEqual(locked_axes, ["Y"])
        print("Locked axes:", locked_axes)

        print("Unlocking Y axis...")
        stage.safety_settings.unlock_axis("Y")
        locked_axes = stage.safety_settings.locked_axes
        self.assertEqual(locked_axes, [])
        print("Locked axes:", locked_axes)
        print("Done.")

    def test_link_unlink_stage(self):
        microscope = self.microscope
        stage = microscope.specimen.stage

        if not stage.is_installed:
            self.skipTest("Bulk stage is not installed, skipping")

        # On WDB H1200 linking is allowed only in a narrow Z range
        if self.test_helper.is_system([SystemFamily.HELIOS_1200, SystemFamily.PLUTO]):
            print("We are on WDB, moving Z to 3.15mm...")
            p = StagePosition(z=0.00315)
            stage.absolute_move(p)

        print("Linking stage Z to WD...")
        microscope.imaging.start_acquisition()
        stage.link()
        self.assertTrue(stage.is_linked)
        microscope.imaging.stop_acquisition()
        print("Success.")

        time.sleep(0.5)

        print("Unlinking stage Z from WD...")
        stage.unlink()
        self.assertFalse(stage.is_linked)
        print("Done.")

    def test_compucentric_rotation(self):
        stage = self.microscope.specimen.stage

        if not stage.is_installed:
            self.skipTest("Bulk stage is not installed, skipping")

        print("Going to test origin...")
        p1 = StagePosition(x=0, y=0.005, r=0, t=0)
        stage.absolute_move(p1)
        print("Success.")

        print("Performing compucentric rotation by 45 degrees using absolute move...")
        settings = MoveSettings(rotate_compucentric=True)
        p2 = StagePosition(r=0.785)
        stage.absolute_move(p2, settings)
        self.__assert_stage_coordinates(stage.current_position, expected_x=0.0035, expected_y=0.0035, expected_r=0.785)
        print("Success.")

        print("Performing compucentric rotation by 45 degrees using relative move...")
        settings = MoveSettings(rotate_compucentric=True)
        p3 = StagePosition(r=0.785)
        stage.relative_move(p3, settings)
        self.__assert_stage_coordinates(stage.current_position, expected_x=0.005, expected_y=0.000, expected_r=1.570)
        print("Success.")

        print("Performing non-compucentric rotation by 45 degrees using absolute move...")
        settings = MoveSettings(rotate_compucentric=False)
        p4 = StagePosition(r=0.785)
        stage.absolute_move(p4, settings)
        self.__assert_stage_coordinates(stage.current_position, expected_x=0.005, expected_y=0.000, expected_r=0.785)
        print("Success.")

        print("Performing non-compucentric rotation by 45 degrees using relative move...")
        settings = MoveSettings(rotate_compucentric=False)
        p5 = StagePosition(r=-0.785)
        stage.relative_move(p5, settings)
        self.__assert_stage_coordinates(stage.current_position, expected_x=0.005, expected_y=0.000, expected_r=0.000)
        print("Success.")

        print("Going to stage origin...")
        self.microscope.specimen.stage.absolute_move(StagePosition(x=0, y=0, r=0, t=0))
        print("Done.")

    def test_stage_move(self):
        microscope = self.microscope
        stage = microscope.specimen.stage
        pi = math.pi

        if not stage.is_installed:
            self.skipTest("Bulk stage is not installed, skipping")

        print("Linking Z at eucentric height...")
        microscope.imaging.set_active_view(1)
        microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)
        stage.unlink()
        eucentric_height = self.test_helper.get_system_eucentric_height()
        microscope.beams.electron_beam.working_distance.value = eucentric_height
        microscope.imaging.start_acquisition()
        stage.link()
        microscope.imaging.stop_acquisition()
        print("Success.")

        print("Going to test origin...")
        stage.set_default_coordinate_system(CoordinateSystem.SPECIMEN)
        target_position = StagePosition(x=0.000, y=0.000, z=eucentric_height, r=0, t=0)
        stage.absolute_move(target_position)
        self.__assert_stage_coordinates_equal(stage.current_position, target_position)
        print("Success.")

        print("Performing absolute move in Specimen coordinates...")
        target_position = StagePosition(x=-0.006, y=0.005, z=eucentric_height, r=30*pi/180, t=15*pi/180, coordinate_system=CoordinateSystem.SPECIMEN)
        stage.absolute_move(target_position)
        self.__assert_stage_coordinates_equal(stage.current_position, target_position)
        print("Success.")

        print("Performing absolute move in X axis only...")
        old_position = stage.current_position
        target_position = StagePosition(x=0.001)
        stage.absolute_move(target_position)
        self.__assert_stage_coordinates(stage.current_position, target_position.x, old_position.y, old_position.z, old_position.r, old_position.t)
        print("Success.")

        print("Performing relative move in Specimen coordinates...")
        old_position = stage.current_position
        delta_position = StagePosition(x=-0.001, y=0.001, z=0, r=-15*pi/180, t=-5*pi/180, coordinate_system=CoordinateSystem.SPECIMEN)
        stage.relative_move(delta_position)
        new_position = old_position + delta_position
        self.__assert_stage_coordinates_equal(stage.current_position, new_position)
        print("Success.")

        print("Performing relative move in Y axis only...")
        old_position = stage.current_position
        delta_position = StagePosition(y=-0.001)
        stage.relative_move(delta_position)
        self.__assert_stage_coordinates(stage.current_position, old_position.x, old_position.y + delta_position.y, old_position.z, old_position.r, old_position.t)
        print("Success.")

        print("Performing absolute move in Raw coordinates...")
        stage.set_default_coordinate_system(CoordinateSystem.RAW)
        target_position = StagePosition(x=0.002, y=0.003, r=10*pi/180, z=eucentric_height, t=15*pi/180, coordinate_system=CoordinateSystem.RAW)
        stage.absolute_move(target_position)
        # We don't assert the result, positioning in raw coordinates is not simulated well on some XT's
        print("Success.")

        stage.set_default_coordinate_system(CoordinateSystem.SPECIMEN)

        print("Going back to origin...")
        target_position = StagePosition(x=0.000, y=0.000, z=eucentric_height, r=0, t=0)
        stage.absolute_move(target_position)
        self.__assert_stage_coordinates_equal(stage.current_position, target_position)

        if self.test_helper.is_navcam_installed():
            print("Performing move from NavCam view...")
            microscope.imaging.set_active_view(3)
            microscope.imaging.set_active_device(ImagingDevice.NAV_CAM)
            target_position = StagePosition(x=0.001)
            stage.absolute_move(target_position)
            self.__assert_stage_coordinates_equal(stage.current_position, target_position)
            print("Success.")

        if self.test_helper.is_ccd_installed():
            print("Performing move from CCD view...")
            microscope.imaging.set_active_view(4)
            microscope.imaging.set_active_device(ImagingDevice.CCD_CAMERA)
            target_position = StagePosition(x=-0.001)
            stage.absolute_move(target_position)
            self.__assert_stage_coordinates_equal(stage.current_position, target_position)
            print("Success.")

        microscope.imaging.set_active_view(1)
        print("Done.")

    def test_stage_zy_link(self):
        microscope = self.microscope
        stage = microscope.specimen.stage
        pi = math.pi

        if self.test_helper.is_offline():
            self.skipTest("LinkYZ is not simulated in offline mode, skipping")

        if not stage.is_installed:
            self.skipTest("Bulk stage is not installed, skipping")

        # Assuming the stage is linked and at eucentric from previous test_stage_move() run

        eucentric_height = self.test_helper.get_system_eucentric_height()

        print("Going to test origin 1mm below eucentric...")
        init_position = StagePosition(x=0, y=0.02, z=eucentric_height + 0.001, r=0, t=0)
        stage.absolute_move(init_position)
        self.__assert_stage_coordinates_equal(stage.current_position, init_position)
        print("Success.")

        y_at_zero_tilt = stage.current_position.y
        print("Y at zero tilt is", y_at_zero_tilt)

        print("Tilting without ZY link...")
        stage.absolute_move(StagePosition(t=15*pi/180), MoveSettings(link_z_y=False))
        y_when_tilted_without_link = stage.current_position.y
        print("Y when tilted is", y_when_tilted_without_link)
        self.assertAlmostEqual(y_at_zero_tilt, y_when_tilted_without_link, 5)
        print("Success.")

        print("Going back to test origin...")
        stage.absolute_move(init_position)
        self.__assert_stage_coordinates_equal(stage.current_position, init_position)
        print("Success.")

        y_at_zero_tilt = stage.current_position.y
        print("Y at zero tilt is", y_at_zero_tilt)

        print("Tilting with ZY link...")
        stage.absolute_move(StagePosition(t=15*pi/180), MoveSettings(link_z_y=True))
        y_when_tilted_with_link = stage.current_position.y
        print("Y when tilted is", y_when_tilted_with_link)
        self.assertNotAlmostEqual(y_at_zero_tilt, y_when_tilted_with_link, 5)
        print("Success.")

        print("Returning to stage center...")
        stage.absolute_move(StagePosition(x=0, y=0, z=eucentric_height, r=0, t=0))
        print("Done.")
