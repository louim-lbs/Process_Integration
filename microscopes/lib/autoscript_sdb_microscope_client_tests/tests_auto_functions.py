from autoscript_core.common import ApplicationServerException, ApiException
from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import time
import unittest


class TestsAutoFunctions(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)

    def tearDown(self):
        pass

    def test_run_volumescope_auto_source_tilt(self):
        print("Running Volumescope auto source tilt...")
        self.microscope.auto_functions.run_auto_source_tilt(RunAutoSourceTiltSettings(method="Volumescope"))
        print("Done.")

    def test_run_standard_auto_cb(self):
        print("Running standard auto contrast brightness...")
        self.microscope.auto_functions.run_auto_cb()

        print("Running standard auto contrast brightness with settings...")
        self.microscope.auto_functions.run_auto_cb(RunAutoCbSettings(0.2, 0.8))

        if not self.test_helper.is_offline:
            print("Running standard auto contrast brightness with improper settings...")
            with self.assertRaises(ApplicationServerException):
                self.microscope.auto_functions.run_auto_cb(settings=RunAutoCbSettings(black_target=0.8))

        print("Done.")

    def test_run_max_contrast_auto_cb(self):
        microscope = self.microscope

        microscope.imaging.set_active_view(1)
        microscope.imaging.set_active_view(ImagingDevice.ELECTRON_BEAM)

        # Switch reduce area scan settings to 8-bit depth.
        # If it was set to 16-bit by previous tests, the MaxContrast AF will hang up XT (almost all from 12.x onwards).
        # TODO: This should be handled by the AF itself (AST-587)
        print("Settings reduce area bit depth to 8...")
        settings = GrabFrameSettings(reduced_area=Rectangle(0.2, 0.2, 0.6, 0.6), bit_depth=8)
        microscope.imaging.grab_frame(settings)
        print("Done.")

        print("Running max contrast auto contrast brightness...")
        microscope.auto_functions.run_auto_cb(RunAutoCbSettings(method="MaxContrast"))
        print("Done.")

    def test_run_standard_auto_focus(self):
        print("Running standard auto focus...")
        self.microscope.auto_functions.run_auto_focus()
        print("Done.")

    def test_run_standard_auto_lens_alignment(self):
        print("Running standard auto lens alignment...")
        self.microscope.auto_functions.run_auto_lens_alignment()
        print("Done.")

    def test_run_volumescope_auto_stigmator_centering(self):
        print("Running Volumescope auto stigmator centering...")

        if self.test_helper.is_system([SystemFamily.QUANTA, SystemFamily.QUANTA_FEG]):
            self.skipTest("Not supported on Quanta, skipping")

        self.microscope.auto_functions.run_auto_stigmator_centering(RunAutoStigmatorCenteringSettings(method="Volumescope"))
        print("Done.")

    def test_run_standard_auto_stigmator(self):
        print("Running standard auto stigmator...")
        self.microscope.auto_functions.run_auto_stigmator()
        print("Done.")

    def test_run_ong_et_al_auto_stigmator(self):
        print("Running Ong et al. auto stigmator...")

        if not self.test_helper.is_system([SystemFamily.TENEO, SystemFamily.SCIOS, SystemFamily.SCIOS_2, SystemFamily.APREO, SystemFamily.AQUILOS,
                                           SystemFamily.QUATTRO, SystemFamily.HELIOS, SystemFamily.HELIOS_1200, SystemFamily.HELIOS_PFIB_HYDRA,
                                           SystemFamily.PLUTO, SystemFamily.VERIOS]):
            self.skipTest(f"Not supported on {self.test_helper.get_system_name()}, skipping")

        self.microscope.auto_functions.run_auto_stigmator(RunAutoStigmatorSettings(method="OngEtAl"))
        print("Done.")
