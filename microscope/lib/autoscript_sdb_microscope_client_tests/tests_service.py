from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client_tests.utilities import *

import re
import unittest


class TestsService(unittest.TestCase):
    version_pattern = r'\d+\.\d+\.\d+\.\d+'

    def setUp(self, host="localhost"):
        self.microscope = SdbMicroscopeClient()
        self.microscope.connect(host)

    def tearDown(self):
        pass

    def __assert_proper_version(self, subject, version):
        subject = subject[0].upper() + subject[1:]  #
        version_pattern_match = re.match(self.version_pattern, version)

        self.assertNotEqual("0.0.0.0", version, subject + " version '" + version + "' is not proper")
        self.assertIsNotNone(version_pattern_match, subject + " version '" + version + "' is not proper")

        print(subject + " version '" + version + "' is proper")

    def test_system_name(self):
        system_name = self.microscope.service.system.name
        self.assertIsNotNone(system_name, "System name '" + system_name + "' is not proper")
        self.assertNotEqual("", system_name, "System name '" + system_name + "' is not proper")
        print("System name '" + system_name + "' is proper")

    def test_system_version(self):
        self.__assert_proper_version("system", self.microscope.service.system.version)

    def test_autoscript_server_version(self):
        self.__assert_proper_version("AutoScript server", self.microscope.service.autoscript.server.version)

    def test_autoscript_client_version(self):
        self.__assert_proper_version("AutoScript client", self.microscope.service.autoscript.client.version)
