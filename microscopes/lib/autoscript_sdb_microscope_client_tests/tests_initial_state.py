from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import unittest


class TestsInitialState(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)

    def tearDown(self):
        pass

    def test_set_initial_state(self):
        self.__pump_to_high_vacuum()
        self.__turn_beams_on()
        self.__set_standard_views()
        self.__set_standard_optical_mode()
        self.__set_reasonable_imaging_conditions()
        self.__disconnect_temperature_stages()
        self.__home_stage()
        self.__link_stage()
        self.__heat_ion_source()

        print("Done.")

    def __pump_to_high_vacuum(self):
        microscope = self.microscope

        # Chamber can be vented, in low vacuum or ESEM mode, we want high vacuum
        print("Pumping to high vacuum...")
        settings = VacuumSettings(mode=VacuumMode.HIGH_VACUUM)
        microscope.vacuum.pump(settings)
        print("Done.")

    def __turn_beams_on(self):
        microscope = self.microscope

        print("Switching all beams on...")
        microscope.beams.electron_beam.turn_on()

        if microscope.beams.ion_beam.is_installed:
            microscope.beams.ion_beam.turn_on()

        print("Done.")

    def __set_standard_views(self):
        microscope = self.microscope

        print("Configuring views into standard layout...")

        microscope.imaging.set_active_view(1)
        microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)

        microscope.imaging.set_active_view(2)
        if microscope.beams.ion_beam.is_installed:
            microscope.imaging.set_active_device(ImagingDevice.ION_BEAM)
        else:
            microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)

        microscope.imaging.set_active_view(3)
        if self.test_helper.is_navcam_installed:
            microscope.imaging.set_active_device(ImagingDevice.NAV_CAM)
        elif self.test_helper.is_optical_microscope_installed:
            microscope.imaging.set_active_device(ImagingDevice.OPTICAL_MICROSCOPE)
        else:
            microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)

        microscope.imaging.set_active_view(4)
        if self.test_helper.is_ccd_installed:
            microscope.imaging.set_active_device(ImagingDevice.CCD_CAMERA)
        elif self.test_helper.is_optical_microscope_installed:
            microscope.imaging.set_active_device(ImagingDevice.OPTICAL_MICROSCOPE)
        else:
            microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)

        microscope.imaging.set_active_view(1)
        print("Success.")

    def __disconnect_temperature_stages(self):
        microscope = self.microscope

        print("Checking temperature stages...")

        if not self.test_helper.get_system_major_version() < 12 and microscope.specimen.temperature_stage.type == TemperatureStageType.MICRO_HEATER:
            print("Disconnecting micro heater...")
            self.test_helper.disconnect_temperature_stage(TemperatureStageType.MICRO_HEATER)
        elif not self.test_helper.get_system_major_version() < 13 and microscope.specimen.temperature_stage.type == TemperatureStageType.COOLING_STAGE:
            print("Disconnecting cooling stage...")
            self.test_helper.disconnect_temperature_stage(TemperatureStageType.COOLING_STAGE)
        elif not self.test_helper.get_system_major_version() < 13 and microscope.specimen.temperature_stage.type == TemperatureStageType.HEATING_STAGE:
            print("Disconnecting heating stage...")
            self.test_helper.disconnect_temperature_stage(TemperatureStageType.HEATING_STAGE)
        elif not self.test_helper.get_system_major_version() < 13 and microscope.specimen.temperature_stage.type == TemperatureStageType.HIGH_VACUUM_HEATING_STAGE:
            print("Disconnecting high vacuum heating stage...")
            self.test_helper.disconnect_temperature_stage(TemperatureStageType.HIGH_VACUUM_HEATING_STAGE)

        # On XT 6 systems we have no way to determine if the temperature stages are connected, so we just disconnect them always
        if self.test_helper.is_system_version(6):
            if self.test_helper.is_temperature_stage_installed(TemperatureStageType.HEATING_STAGE):
                print("Disconnecting heating stage...")
                self.test_helper.disconnect_temperature_stage(TemperatureStageType.HEATING_STAGE)
            elif self.test_helper.is_temperature_stage_installed(TemperatureStageType.COOLING_STAGE):
                print("Disconnecting cooling stage...")
                self.test_helper.disconnect_temperature_stage(TemperatureStageType.COOLING_STAGE)

        print("Success.")

    def __set_reasonable_imaging_conditions(self):
        microscope = self.microscope

        print("Setting initial scanning conditions...")

        microscope.imaging.set_active_view(1)
        microscope.beams.electron_beam.scanning.dwell_time.value = 1e-6
        microscope.beams.electron_beam.scanning.resolution.value = ScanningResolution.PRESET_1536X1024
        microscope.beams.electron_beam.horizontal_field_width.value = 12.28e-6
        microscope.imaging.grab_frame()

        if microscope.beams.ion_beam.is_installed:
            microscope.imaging.set_active_view(2)
            microscope.beams.ion_beam.scanning.dwell_time.value = 1e-6
            microscope.beams.ion_beam.scanning.resolution.value = ScanningResolution.PRESET_768X512
            microscope.beams.ion_beam.horizontal_field_width.value = 12.28e-6
            microscope.imaging.grab_frame()

        if self.test_helper.is_ccd_installed:
            microscope.imaging.set_active_view(4)
            microscope.imaging.start_acquisition()
            time.sleep(1)
            microscope.imaging.stop_acquisition()

        microscope.imaging.set_active_view(1)
        print("Success.")

    def __set_standard_optical_mode(self):
        microscope = self.microscope

        if self.test_helper.is_system([SystemFamily.SCIOS, SystemFamily.SCIOS_2, SystemFamily.AQUILOS]):
            print("Setting standard optical mode...")
            microscope.beams.electron_beam.optical_mode.value = OpticalMode.STANDARD
            print("Success.")

    def __home_stage(self):
        microscope = self.microscope

        if microscope.specimen.stage.is_installed and not microscope.specimen.stage.is_homed:
            print("Homing stage...")
            microscope.specimen.stage.home()
            print("Success.")

    def __link_stage(self):
        if self.microscope.specimen.stage.is_installed:
            self.microscope.specimen.stage.absolute_move(StagePosition(t=0))
            self.test_helper.link_z_to_fwd()

    def __heat_ion_source(self):
        microscope = self.microscope

        if microscope.beams.ion_beam.is_installed and not self.test_helper.is_system_plasma_fib and microscope.beams.ion_beam.source.time_to_heat < 10 * 60:
            print("Heating ion source...")
            microscope.beams.ion_beam.source.heat()
