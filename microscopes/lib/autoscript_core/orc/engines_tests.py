import unittest

from autoscript_core.orc.engines import EndpointState

from autoscript_core.common import TransportEndpointDefinition
from autoscript_core.framed_transport import FrameSocketException
from autoscript_core.orc import ClientEndpoint, EndpointException, EndpointExceptionCause


class FakeClientFrameSocket:
    def connect(self, server_transport_endpoint: TransportEndpointDefinition):
        raise FrameSocketException("Cannot connect.")


class TestableClientEndpoint(ClientEndpoint):
    def _create_client_frame_socket(self):
        return FakeClientFrameSocket()


class ClientEndpointTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test__connect__when_endpoint_is_running__raises_proper_exception(self):
        client_endpoint = TestableClientEndpoint()
        server_transport_endpoint = TransportEndpointDefinition("127.0.0.1", 7520)
        proper_exception_raised = False

        try:
            client_endpoint.state = EndpointState.RUNNING
            client_endpoint.connect(server_transport_endpoint)
        except EndpointException as endpoint_exception:
            if endpoint_exception.cause == EndpointExceptionCause.STATE:
                proper_exception_raised = True

        self.assertTrue(proper_exception_raised)

    def test__connect__when_transport_layer_issues_occur__raises_proper_exception(self):
        client_endpoint = TestableClientEndpoint()
        server_transport_endpoint = TransportEndpointDefinition("127.0.0.1", 7520)
        proper_exception_raised = False

        try:
            client_endpoint.connect(server_transport_endpoint)
        except EndpointException as endpoint_exception:
            if endpoint_exception.cause == EndpointExceptionCause.L4_NETWORKING:
                proper_exception_raised = True

        self.assertTrue(proper_exception_raised)
