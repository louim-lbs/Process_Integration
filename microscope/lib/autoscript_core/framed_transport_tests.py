import unittest

from .framed_transport import *


class FrameTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test__frame_type_byte__when_default_frame_constructor_is_used__returns_data_frame_type_byte(self):
        frame = Frame(bytearray())

        self.assertEqual(FrameType.DATA, frame.type)


class ClientFrameSocketTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test__connect__when_invalid_server_endpoint_is_given__throws_proper_exception(self):
        client_frame_socket = ClientFrameSocket()

        proper_exception_thrown = False
        try:
            client_frame_socket.connect(None)
        except FrameSocketException:
            proper_exception_thrown = True

        self.assertTrue(proper_exception_thrown)
