from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
from autoscript_sdb_microscope_client.enumerations import *

import os
import random
import threading
import time
import unittest


class ConnectionCutter:
    DEFAULT_MINIMAL_WAITING_TIME = 25
    DEFAULT_MAXIMAL_WAITING_TIME = 100
    DEFAULT_PORT = 7520

    def __init__(self, minimal_waiting_time=DEFAULT_MINIMAL_WAITING_TIME, maximal_waiting_time=DEFAULT_MAXIMAL_WAITING_TIME, port=DEFAULT_PORT):
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValueError("Port has to be a number between 1 and 65535.")

        self.__curr_ports_path = os.path.dirname(__file__) + '\\resources\\currports.exe'
        self.__connection_cut_thread = None
        self.__stop_connection_cut_thread = False
        self.__minimal_waiting_time = minimal_waiting_time
        self.__maximal_waiting_time = maximal_waiting_time
        self.__port = port
        self.number_of_cuts = 0
        self.run_exception = None

    def start(self):
        self.__connection_cut_thread = threading.Thread(target=self.__run_connection_loop)
        self.__connection_cut_thread.start()

    def stop(self):
        self.__stop_connection_cut_thread = True
        self.__connection_cut_thread.join()

    def __run_connection_loop(self):
        self.number_of_cuts = 0

        while True:
            if self.__stop_connection_cut_thread:
                break

            try:
                self.__cut_connections()
                self.number_of_cuts += 1

            except Exception as ex:
                self.run_exception = ex
                break

            waiting_time = random.randint(self.__minimal_waiting_time, self.__maximal_waiting_time)
            time.sleep(waiting_time * 1e-3)

    def __cut_connections(self):
        exit_code1 = os.system("\"%s\" /close * * * %d" % (self.__curr_ports_path, self.__port))
        exit_code2 = os.system("\"%s\" /close * %d * *" % (self.__curr_ports_path, self.__port))

        if exit_code1 != 0 or exit_code2 != 0:
            raise Exception("Connection cut operation failed.")


class ThreadedCall:
    def __init__(self, microscope, callParameter):
        self.__microscope = microscope
        self.__call_parameter = callParameter
        self.__call_thread = None
        self.call_exception = None

    def start(self):
        self.__call_thread = threading.Thread(target=self.__perform_call)
        self.__call_thread.start()

    def wait_for_finish(self):
        self.__call_thread.join()

    def __perform_call(self):
        try:
            dwell_time = self.__call_parameter
            grab_frame_settings = GrabFrameSettings(resolution="768x512", dwell_time=dwell_time)
            image = self.__microscope.imaging.grab_frame(grab_frame_settings)
            if image.width != 768:
                raise Exception("Image width is %d although %d was expected." % (image.width, 768))
            if image.height != 512:
                raise Exception("Image height is %d although %d was expected." % (image.height, 512))
            if not image.metadata.scan_settings.dwell_time:
                raise Exception("Dwell time is not present in image metadata.")
            if image.metadata.scan_settings.dwell_time != dwell_time:
                raise Exception("Dwell time is %d although %d was expected." % (image.metadata.scan_settings.dwell_time, dwell_time))

        except Exception as ex:
            self.call_exception = ex


class TestsConnection(unittest.TestCase):
    def setUp(self, host="localhost"):
        self.host = host

    def tearDown(self):
        pass

    def __perform_normal_calls(self, microscope):
        number_of_short_calls = 500
        number_of_long_calls = 5

        print("Reading electron beam high voltage %d times..." % number_of_short_calls)
        for i in range(number_of_short_calls):
            high_voltage_value = microscope.beams.electron_beam.high_voltage.value
            self.assertEqual(5000, high_voltage_value)

        print("Taking grab frame %d times..." % number_of_long_calls)
        for i in range(number_of_long_calls):
            grab_frame_settings = GrabFrameSettings(resolution="768x512", dwell_time=1e-6)
            image = microscope.imaging.grab_frame(grab_frame_settings)
            self.assertEqual(768, image.width)
            self.assertEqual(512, image.height)

    def test_connection_recovery_with_internal_cuts(self):
        microscope = SdbMicroscopeClient()
        microscope.connect(self.host)

        print("Setting electron beam high voltage to 5 kV...")
        microscope.beams.electron_beam.high_voltage.value = 5000

        print("Activating networking error injection mechanism...")
        microscope.service.autoscript.server.configuration.set_value("Networking.ErrorInjection.Active", "1")

        try:
            self.__perform_normal_calls(microscope)
        finally:
            print("Deactivating networking error injection mechanism...")
            microscope.service.autoscript.server.configuration.set_value("Networking.ErrorInjection.Active", "0")

            print("Networking error injection mechanism deactivated")

        print("Done")

    def test_connection_recovery_with_external_cuts(self):
        microscope = SdbMicroscopeClient()
        microscope.connect(self.host)

        print("Setting electron beam high voltage to 5 kV...")
        microscope.beams.electron_beam.high_voltage.value = 5000

        print("Starting connection cutter...")
        connection_cutter = ConnectionCutter(100, 500)
        connection_cutter.start()

        try:
            self.__perform_normal_calls(microscope)
        finally:
            print("Stopping connection cutter...")
            connection_cutter.stop()

            print("Connections were cut %d times" % connection_cutter.number_of_cuts)

        if connection_cutter.run_exception is not None:
            raise Exception("An error occurred in ConnectionCutter. " + str(connection_cutter.run_exception))

        print("Done")

    def test_concurrent_call(self):
        number_of_threaded_calls = 5

        microscope = SdbMicroscopeClient()
        microscope.connect(self.host)

        print("Creating %d ThreadedCalls and starting them..." % number_of_threaded_calls)

        threaded_calls = []
        for i in range(number_of_threaded_calls):
            threaded_call = ThreadedCall(microscope, (i + 1) * 1e-6)
            threaded_calls.append(threaded_call)
            threaded_call.start()

        print("Waiting for ThreadedCalls to finish...")

        call_exception = None
        for threaded_call in threaded_calls:
            threaded_call.wait_for_finish()

            if not call_exception and threaded_call.call_exception:
                call_exception = threaded_call.call_exception

        if call_exception:
            raise Exception("An error occurred in one or more ThreadedCalls. Description of the first encountered exception follows. " + str(call_exception))

        print("Done")
