from autoscript_sdb_microscope_client import SdbMicroscopeClient
import unittest
import time


class TestsLoadLock(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)

    def tearDown(self):
        pass

    def test_loadlock_actions(self):
        print("Current LoadLock state is " + self.microscope.specimen.loadlock.state)

        if self.microscope.specimen.loadlock.state == "Loaded":
            print("Unloading")
            self.microscope.specimen.loadlock.unload()
            print("Unloaded")

            print("Loading")
            self.microscope.specimen.loadlock.load()
            print("Loaded")

            self.assertEqual(self.microscope.specimen.loadlock.state, "Loaded")
        elif self.microscope.specimen.loadlock.state == "Unloaded":
            print("Loading")
            self.microscope.specimen.loadlock.load()
            print("Loaded")

            print("Unloading")
            self.microscope.specimen.loadlock.unload()
            print("Unloaded")

            self.assertEqual(self.microscope.specimen.loadlock.state, "Unloaded")
        else:
            self.fail("Unexpected state.")

        print("Done")
