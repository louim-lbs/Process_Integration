from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import unittest


class TestsSpecimenLoadLock(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)

    def tearDown(self):
        pass

    def test_loadlock_actions(self):
        print("Determining state...")
        self.__determine_loadlock_state()
        print("Current LoadLock state is " + self.microscope.specimen.loadlock.state)

        if self.microscope.specimen.loadlock.state == LoadLockState.LOADED:
            print("Preparing for unload...")
            self.__prepare_loadlock_for_unloading()
            print("Success.")

            print("Unloading...")
            self.microscope.specimen.loadlock.unload()
            self.assertEqual(self.microscope.specimen.loadlock.state, LoadLockState.UNLOADED)
            print("Success.")

            print("Preparing for load...")
            self.__prepare_loadlock_for_loading()
            print("Success.")

            print("Loading...")
            self.microscope.specimen.loadlock.load()
            self.assertEqual(self.microscope.specimen.loadlock.state, LoadLockState.LOADED)

        elif self.microscope.specimen.loadlock.state == "Unloaded":
            print("Preparing for load...")
            self.__prepare_loadlock_for_loading()
            print("Success.")

            print("Loading...")
            self.microscope.specimen.loadlock.load()
            self.assertEqual(self.microscope.specimen.loadlock.state, LoadLockState.LOADED)
            print("Success.")

            print("Preparing for unload...")
            self.__prepare_loadlock_for_unloading()
            print("Success.")

            print("Unloading...")
            self.microscope.specimen.loadlock.unload()
            self.assertEqual(self.microscope.specimen.loadlock.state, LoadLockState.UNLOADED)

        else:
            self.fail("Unexpected state.")

        print("Done.")

    def __determine_loadlock_state(self):
        self.microscope.service.autoscript.server.configuration.set_value("Devices.LoadLock.Determine", "")

    def __prepare_loadlock_for_loading(self):
        if self.test_helper.get_system_major_version() >= 12:
            # Loadlock simulation control is supported from XT 12 onwards, do nothing on older XTs
            self.microscope.service.autoscript.server.configuration.set_value("Devices.LoadLock.PrepareLoad", "")

    def __prepare_loadlock_for_unloading(self):
        if self.test_helper.get_system_major_version() >= 12:
            # Loadlock simulation control is supported from XT 12 onwards, do nothing on older XTs
            self.microscope.service.autoscript.server.configuration.set_value("Devices.LoadLock.PrepareUnload", "")
