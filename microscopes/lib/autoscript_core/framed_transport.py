import socket
from .common import TransportEndpointDefinition, SequenceNumberGenerator
from .serialization import BasicValueSerializer, BasicValueDeserializer, BytesChopper, BytesBuilder


class FrameType:
    UNKNOWN = 0x00
    DATA = 0x01
    PROBE = 0x02


class Frame:
    """Frame represents a single block of data to be carried over the network using between two FrameSockets."""

    HEADER_LENGTH = 12
    HEADER_MAGIC_BYTE1 = 0x46
    HEADER_MAGIC_BYTE2 = 0x54
    DEFAULT_FRAME_TYPE = FrameType.DATA

    def __init__(self, content: bytes):
        """
        Frame constructor.

        :param content: Payload (upper layer data) to be carried over the network within the frame.
        :type content: bytes
        """
        self.type = Frame.DEFAULT_FRAME_TYPE
        self.sequence_number = 0
        self.content = content

    def construct_bytes(self):
        """Constructs a byte array representing the whole frame."""
        frame_bytes_builder = BytesBuilder()
        frame_content_length = len(self.content)

        # adds header bytes
        frame_bytes_builder.add_bytes(bytes([Frame.HEADER_MAGIC_BYTE1, Frame.HEADER_MAGIC_BYTE2, self.type, 0x00]))
        BasicValueSerializer.serialize_int32(self.sequence_number, frame_bytes_builder)
        BasicValueSerializer.serialize_int32(frame_content_length, frame_bytes_builder)

        # adds content bytes
        frame_bytes_builder.add_bytes(self.content)

        return frame_bytes_builder.get_data()


class FrameSocketState:
    """
    FrameSocketState lists possible states of FrameSocket.

    Every FrameSocket has at most one connection during its lifetime.
    """

    IDLE = 1
    """State in which FrameSocket is because there was no attempt to establish and/or complete a connection it so far."""
    CONNECTED = 2
    """State in which FrameSocket has completed connection establishment and there are no signs of error so far."""
    DISCONNECTED = 3
    """State in which FrameSocket considers previously established connection unusable."""


class FrameSocket:
    """
    FrameSocket represents a socket that allows to send and receive frames (blocks of data) over a single TCP connection.

    Please note that Python version of FrameSocket is NOT THREAD-SAFE. DO NOT attempt to send/receive frame simultaneously from different threads.
    """

    CHUNK_SIZE = 1024
    """Size of chunk (in bytes) to be read from TCP stream at once when receiving frames."""

    def __init__(self):
        self.state = FrameSocketState.IDLE
        self._tcp_socket = None
        self._frame_sequence_number_generator = SequenceNumberGenerator()

    def send_frame(self, frame: Frame):
        """
        Sends the given frame to the other side of the connection.
        :raises FrameSocketException: Raised when an error occurs when sending frame. The socket is disconnected and expected not to be used anymore in such case.
        """
        if self.state is not FrameSocketState.CONNECTED:
            raise FrameSocketException("Frame could not be sent because the socket is not connected.", None)

        try:
            self._send_frame_synchronously(frame)
        except TcpStreamIoException as tcp_stream_io_exception:
            raise FrameSocketException("An error occurred when sending frame.", tcp_stream_io_exception) from tcp_stream_io_exception

    def receive_frame(self):
        """
        Receives frame from the other side of the connection. The method blocks when there is no frame available.
        :raises FrameSocketException: Raised when an error occurs when receiving frame.
        """
        if self.state is not FrameSocketState.CONNECTED:
            raise FrameSocketException("Frame could not be received because the socket is not connected.", None)

        try:
            while True:
                frame = self._receive_frame_synchronously()
                if frame.type == FrameType.DATA:
                    break
        except Exception as ex:
            raise FrameSocketException("An error occurred when receiving frame.", ex) from ex

        return frame

    def _send_frame_synchronously(self, frame: Frame):
        """
        Sends frame with the given content to the other side of the connection synchronously.

        Please note that "synchronously" does not mean that the frame can be considered delivered when the method returns.
        :raises TcpStreamIoException: Raised when an error occurs when writing data to TCP stream.
        """
        frame.sequence_number = self._frame_sequence_number_generator.generate_sequence_number()

        frame_bytes = frame.construct_bytes()
        frame_bytes_length = len(frame_bytes)

        bytes_written = 0
        while bytes_written < frame_bytes_length:
            try:
                bytes_written_now = self._tcp_socket.send(frame_bytes[bytes_written:])
            except Exception as ex:
                raise TcpStreamIoException("An error occurred when writing data to TCP stream.", ex) from ex

            if bytes_written_now == 0:
                raise TcpStreamIoException("An error occurred when writing data to TCP stream.", None)
            bytes_written = bytes_written + bytes_written_now

    def _receive_frame_synchronously(self):
        """
        Receives frame from the other side of the connection synchronously.

        :raises TcpStreamIoException: Thrown when an error occurs when reading data from TCP stream.
        :raises FrameProcessingException: Thrown when frame processing fails on byte semantics level.
        """
        try:
            header_bytes = self._tcp_socket.recv(Frame.HEADER_LENGTH)
        except Exception as ex:
            raise TcpStreamIoException("An error occurred when reading data from TCP stream.", ex) from ex

        if header_bytes == b'':
            raise TcpStreamIoException("An error occurred when reading data from TCP stream.", None)

        if len(header_bytes) < Frame.HEADER_LENGTH:
            raise TcpStreamIoException("Not enough bytes could be read from TCP stream to form a frame header.", None)

        are_magic_bytes_valid = header_bytes[0] == Frame.HEADER_MAGIC_BYTE1 and header_bytes[1] == Frame.HEADER_MAGIC_BYTE2
        if not are_magic_bytes_valid:
            message = "Sequence of 0x" + '{:02X}'.format(header_bytes[0]) + '{:02X}'.format(header_bytes[1]) + " was not recognized as a valid frame header magic byte sequence."
            raise FrameProcessingException(message, None)
        
        chopper = BytesChopper(header_bytes, 4)
        frame_type_byte = header_bytes[2]
        sequence_number = BasicValueDeserializer.deserialize_int32(chopper)
        content_length = BasicValueDeserializer.deserialize_int32(chopper)

        chunks = []
        bytes_read = 0
        remaining_bytes = content_length
        while bytes_read < content_length:
            try:
                chunk = self._tcp_socket.recv(min(remaining_bytes, FrameSocket.CHUNK_SIZE))
            except Exception as ex:
                raise TcpStreamIoException("An error occurred when reading data from TCP stream.", ex) from ex

            if chunk == b'':
                raise TcpStreamIoException("An error occurred when reading data from TCP stream.", None)

            chunks.append(chunk)

            bytes_read_now = len(chunk)
            bytes_read += bytes_read_now
            remaining_bytes -= bytes_read_now

        content_bytes = b''.join(chunks)

        if frame_type_byte == FrameType.DATA or frame_type_byte == FrameType.PROBE:
            received_frame = Frame(content_bytes)
            received_frame.type = frame_type_byte
            received_frame.sequence_number = sequence_number

            return received_frame
        else:
            message = "Unknown frame type of 0x" + '{:02X}'.format(frame_type_byte) + " was encountered."
            raise FrameProcessingException(message, None)

    def disconnect(self):
        """
        Disconnects the socket. The socket is not expected to be used anymore.
        """
        self.state = FrameSocketState.DISCONNECTED

        if self._tcp_socket is not None:
            self._tcp_socket.close()


class ClientFrameSocket(FrameSocket):
    """
    ClientFrameSocket is a client-side flavor of <see cref="FrameSocket"/>.

    ClientFrameSocket allows to manage a single connection established to a server with FrameSocket support. The client is expected
    to create ClientFrameSocket instance directly and initiate connection using connect() method.
    """

    def __init__(self):
        super().__init__()
        pass

    def connect(self, server_transport_endpoint: TransportEndpointDefinition):
        """
        Connects to a server expected to be listening on the given endpoint.

        :param server_transport_endpoint: Definition of an endpoint on which the server is expected to listen.
        :type server_transport_endpoint: TransportEndpointDefinition
        """

        if server_transport_endpoint is None:
            raise FrameSocketException("Invalid endpoint was provided for connection to server.", None)

        self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        try:
            self._tcp_socket.connect((server_transport_endpoint.host, server_transport_endpoint.port))
        except Exception as ex:
            self._tcp_socket = None
            raise FrameSocketException("An error occurred when establishing TCP connection.", ex)

        self.state = FrameSocketState.CONNECTED


class FrameSocketException(Exception):
    """FrameSocketException is an exception that is fired when an error occurs during any FrameSocket operation."""

    def __init__(self, message, inner_exception=None):
        super().__init__(message)

        self.inner_exception = inner_exception


class TcpStreamIoException(Exception):
    """
    TcpStreamIoException is an exception that is fired when an error occurs during TCP stream I/O operations.

    TcpStreamIoException covers errors during opening TCP stream, which takes place during TCP connection establishment,
    and subsequent writing to the stream and reading from it. TcpStreamIoException is an internal exception, which
    should be handled and wrapped before being thrown out of the module.
    """

    def __init__(self, message, inner_exception):
        super().__init__(message)

        self.inner_exception = inner_exception


class FrameProcessingException(Exception):
    """
    FrameProcessingException is an exception that is thrown when frame processing fails.

    FrameProcessingException is expected to be used when bytes read from TCP stream do not seem to make sense
    (e.g., header can not be properly reconstructed from them). FrameProcessingException is an internal exception,
    which should be handled and wrapped before being thrown out of the module.
    """

    def __init__(self, message, inner_exception):
        super().__init__(message)

        self.inner_exception = inner_exception
