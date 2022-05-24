from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import time
import unittest


class TestsGasGis(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)

    def tearDown(self):
        pass

    def test_insert_retract_gis_port(self):
        if not self.test_helper.is_gis_installed:
            self.skipTest("No Gis port found, skipping")

        gis_port = self.__find_suitable_gis_port()
        self.__prepare_for_gis_operation()

        self.test_helper.test_insert_retract_device(gis_port, "GIS port")
        print("Done.")

    def test_open_close_gis(self):
        if not self.test_helper.is_gis_installed:
            self.skipTest("No Gis port found, skipping")

        gis_port = self.__find_suitable_gis_port()

        self.__prepare_for_gis_operation()
        self.__heat_all_gises()

        print("Inserting GIS needle...")
        gis_port.insert()
        try:
            print("Opening GIS valve...")
            gis_port.open()
            print("Success.")
            print("Closing GIS valve...")
            gis_port.close()
            print("Success.")
        finally:
            print("Retracting GIS needle...")
            gis_port.retract()

        print("Done.")

    def test_turn_gis_heater_on_off(self):
        if not self.test_helper.is_gis_installed:
            self.skipTest("No Gis port found, skipping")

        gis_port = self.__find_suitable_gis_port()

        self.__prepare_for_gis_operation()

        print("Turning heater on...")
        gis_port.turn_heater_on()
        print("Success.")

        print("Reading temperature...")
        print(gis_port.get_temperature())

        print("Turning heater off...")
        gis_port.turn_heater_off()

        print("Done.")

    def __find_suitable_gis_port(self):
        gis_port_names = self.microscope.gas.list_all_gis_ports()

        if len(gis_port_names) == 0:
            return None

        gis_port_name = gis_port_names[0]
        gis_port = self.microscope.gas.get_gis_port(gis_port_name)

        if gis_port is None:
            raise Exception("No suitable GIS port was found")

        return gis_port

    def __prepare_for_gis_operation(self):
        microscope = self.microscope

        if not microscope.beams.electron_beam.is_on:
            print("Turning electron beam on...")
            microscope.beams.electron_beam.turn_on()
            print("Success.")

        if not microscope.specimen.stage.is_installed:
            return

        # Move stage to center
        if not microscope.specimen.stage.is_homed:
            print("Homing stage...")
            microscope.specimen.stage.home()
        else:
            print("Moving stage to center...")
            p = StagePosition(x=0, y=0, r=0)
            microscope.specimen.stage.absolute_move(p)

        print("Success.")

        # ...and safe Z
        if not microscope.specimen.stage.is_linked:
            self.test_helper.link_z_to_fwd()

        safe_z = self.test_helper.get_system_eucentric_height() + 0.001
        position = microscope.specimen.stage.current_position
        if abs(position.z - safe_z) > 0.0005:
            print("Moving stage to safe Z...")
            microscope.specimen.stage.absolute_move(StagePosition(z=safe_z))
            print("Success.")

    def __heat_all_gises(self):
        print("Heating all Gises...")
        self.microscope.service.autoscript.server.configuration.set_value("Devices.Gis.HeatAll", "")
        print("Success.")
