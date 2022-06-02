from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *
import time
import unittest


class TestsGasMultiChem(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)
        self.test_helper = TestHelper(self, self.microscope)

    def tearDown(self):
        pass

    def test_insert_retract_multichem(self):
        if not self.test_helper.is_multichem_installed:
            self.skipTest("MultiChem is not installed, skipping")

        self.__prepare_for_multichem_operation()

        print("Moving stage to position safe for MultiChem insertion...")
        self.microscope.specimen.stage.absolute_move(StagePosition(x=0, y=0, r=0, t=0))
        position = self.microscope.specimen.stage.current_position
        if position.z < 0.004:
            self.microscope.specimen.stage.absolute_move(StagePosition(z=0.004))
        print("Success.")

        # Insert MultiChem needle into default position
        multichem = self.microscope.gas.get_multichem()
        self.test_helper.test_insert_retract_device(multichem, "MultiChem")
        print("Success.")
        
        # Insert MultiChem needle into predefined position for electron beam
        print("Inserting MultiChem into electron position...")
        multichem.insert(MultiChemInsertPosition.ELECTRON_DEFAULT)
        print("Success.")

        print("Retracting...")
        multichem.retract()
        print("Done.")

    def test_open_close_multichem(self):
        if not self.test_helper.is_multichem_installed:
            self.skipTest("MultiChem is not installed, skipping")

        self.__prepare_for_multichem_operation()
        self.__heat_multichem()

        multichem = self.microscope.gas.get_multichem()
        print("Inserting MultiChem needle...")
        multichem.insert()
        print("Success.")

        try:
            print("Opening MultiChem valve...")
            multichem.open()
            print("Success.")
            print("Closing MultiChem valve...")
            multichem.close()
            print("Success.")
        finally:
            print("Retracting MultiChem needle...")
            multichem.retract()

        print("Done.")

    def test_turn_multichem_heater_on_off(self):
        if not self.test_helper.is_multichem_installed:
            self.skipTest("MultiChem is not installed, skipping")

        self.__prepare_for_multichem_operation()

        multichem = self.microscope.gas.get_multichem()
        gas_name = multichem.list_all_gases()[0]

        print("Turning heater on...")
        multichem.turn_heater_on(gas_name)
        print("Success.")

        print("Reading temperature...")
        print(multichem.get_temperature(gas_name))
        print("Success.")

        print("Turning heater off...")
        multichem.turn_heater_off(gas_name)
        print("Done.")

    def __prepare_for_multichem_operation(self):
        microscope = self.microscope

        if not microscope.specimen.stage.is_homed:
            print("Homing stage...")
            microscope.specimen.stage.home()
            print("Success.")

        if not microscope.beams.electron_beam.is_on:
            print("Turning electron beam on...")
            microscope.beams.electron_beam.turn_on()
            print("Success.")

        if not microscope.specimen.stage.is_linked:
            self.test_helper.link_z_to_fwd()

    def __heat_multichem(self):
        print("Heating MultiChem...")
        self.microscope.service.autoscript.server.configuration.set_value("Devices.MultiChem.Heat", "")
        print("Success.")

