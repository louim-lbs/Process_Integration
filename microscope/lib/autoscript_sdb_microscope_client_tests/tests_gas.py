from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *

import time
import unittest


class TestsGas(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)
        self.system_name = self.microscope.service.system.name

        if not self.microscope.specimen.stage.is_homed:
            print("Homing stage...")
            self.microscope.specimen.stage.home()

        if not self.microscope.beams.electron_beam.is_on:
            print("Turning electron beam on...")
            self.microscope.beams.electron_beam.turn_on()

        if not self.microscope.specimen.stage.is_linked:
            # on WDB H1200 linking is allowed only in a narrow Z range
            if self.system_name == "Helios 1200" or self.system_name == "PlutoWDB":
                p = StagePosition(z=0.00315)
                self.microscope.specimen.stage.absolute_move(p)

            print("Linking Z to WD...")
            self.microscope.imaging.start_acquisition()
            self.microscope.specimen.stage.link()
            self.microscope.imaging.stop_acquisition()

    def tearDown(self):
        pass

    def __find_suitable_gis_port(self):
        gis_port_names = self.microscope.gas.list_all_gis_ports()

        if len(gis_port_names) == 0:
            return None

        gis_port_name = gis_port_names[0]
        gis_port = self.microscope.gas.get_gis_port(gis_port_name)

        return gis_port

    def test_insert_retract_multichem(self):
        print("Moving stage to position safe for multichem insertion...")
        self.microscope.specimen.stage.absolute_move(StagePosition(x=0, y=0, r=0, t=0))
        position = self.microscope.specimen.stage.current_position
        if position.z < 0.004:
            self.microscope.specimen.stage.absolute_move(StagePosition(z=0.004))

        # insert MultiChem needle into default position
        multichem = self.microscope.gas.get_multichem()
        self.test_helper.test_insert_retract_device(multichem, "MultiChem")
        print("Done.")
        
        # insert MultiChem needle into predefined position for electron beam
        print("Inserting MultiChem into electron position...")
        multichem.insert(MultiChemInsertPosition.ELECTRON_DEFAULT)
        print("Done.")

        print("Retracting...")
        multichem.retract()
        print("Done.")

    def test_open_close_multichem(self):
        multichem = self.microscope.gas.get_multichem()
        print("Inserting MultiChem needle...")
        multichem.insert()
        try:
            print("Opening MultiChem valve...")
            multichem.open()
            print("Closing MultiChem valve...")
            multichem.close()
        finally:
            print("Retracting MultiChem needle...")
            multichem.retract()

        print("Done.")

    def test_insert_retract_gis_port(self):
        gis_port = self.__find_suitable_gis_port()
        if gis_port is None:
            raise Exception("No suitable GIS port was found")

        self.test_helper.test_insert_retract_device(gis_port, "GIS port")
        print("Done.")

    def test_open_close_gis(self):
        gis_port = self.__find_suitable_gis_port()
        if gis_port is None:
            raise Exception("No suitable GIS port was found")

        print("Inserting GIS needle...")
        gis_port.insert()
        try:
            print("Opening GIS valve...")
            gis_port.open()
            print("Closing GIS valve...")
            gis_port.close()
        finally:
            print("Retracting GIS needle...")
            gis_port.retract()

        print("Done.")

    def test_turn_gis_heater_on_off(self):
        gis_port = self.__find_suitable_gis_port()
        if gis_port is None:
            raise Exception("No suitable GIS port was found")

        print("Turning heater on...")
        gis_port.turn_heater_on()
        print("Reading temperature...")
        print(gis_port.get_temperature())
        print("Turning heater off...")
        gis_port.turn_heater_off()
        print("Done.")

    def test_turn_multichem_heater_on_off(self):
        multichem = self.microscope.gas.get_multichem()
        gas_name = multichem.list_all_gases()[0]

        print("Turning heater on...")
        multichem.turn_heater_on(gas_name)
        print("Reading temperature...")
        print(multichem.get_temperature(gas_name))
        print("Turning heater off...")
        multichem.turn_heater_off(gas_name)
        print("Done.")
