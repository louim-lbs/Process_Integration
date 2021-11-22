from threading import Lock
import time


class CommunicationSide:
    UNKNOWN = 0
    SERVER = 1
    CLIENT = 2


class SequenceNumberGenerator:
    INT32_MAX_VALUE = 2147483647

    def __init__(self, maximal_sequence_number=INT32_MAX_VALUE):
        self.__sequence_number_lock = Lock()
        self.__next_sequence_number = 1
        self.__maximal_sequence_number = maximal_sequence_number

    def reset(self):
        with self.__sequence_number_lock:
            self.__next_sequence_number = 1

    def generate_sequence_number(self):
        with self.__sequence_number_lock:
            sequence_number = self.__next_sequence_number

            if self.__next_sequence_number == self.__maximal_sequence_number:
                self.__next_sequence_number = 1
            else:
                self.__next_sequence_number += 1

        return sequence_number


MISSING_WIDE_CALL_ID_REPRESENTATION = "[]"


class CallRequest:
    """CallRequest represents a call request through the whole stack."""
    def __init__(self, object_id="", method_name="", signature=(), parameters=()):
        self.session_id = ""
        self.call_id = ""
        self.attempt_number = 0
        self.object_id = object_id
        self.method_name = method_name
        self.__parameters = CallParameters(signature, parameters)

    @property
    def parameters(self):
        return self.__parameters

    @property
    def wide_call_id(self):
        if self.session_id == "" and self.call_id == "":
            return MISSING_WIDE_CALL_ID_REPRESENTATION

        return "[{0}:{1}]".format(self.session_id, self.call_id)


class CallResponse:
    """CallResponse represents a call response through the whole stack."""
    def __init__(self, result=None):
        self.session_id = ""
        self.call_id = ""
        self.was_call_successful = False
        self.result = result
        self.error = None

    @property
    def wide_call_id(self):
        if self.session_id == "" and self.call_id == "":
            return MISSING_WIDE_CALL_ID_REPRESENTATION

        return "[{0}:{1}]".format(self.session_id, self.call_id)


class CallParameters:
    """CallParameters contain collection of values, along with their type information, to be passed to an application server object method."""
    def __init__(self, data_types=(), values=()):
        self.data_types = data_types
        self.values = values
        self.serialized_bytes = None


class CallResult:
    """CallResult contains value, along with its type information, returned by an application server object method."""
    def __init__(self):
        self.data_type = None
        self.value = None
        self.serialized_bytes = None

    def add_value(self, data_type, value):
        if self.data_type or self.value:
            raise Exception("Cannot add value because call result consists of a single value only.")

        self.data_type = data_type
        self.value = value


class TransportEndpointDefinition:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __repr__(self):
        return "[{0}:{1}]".format(self.host, self.port)


class BinaryDataHelper:
    @staticmethod
    def print_segments16(data_bytes):
        """
        Prints the given data bytes in well-readable form of 16-byte segments.

        The method mimics behavior of Wireshark "Packet bytes" inspection window
        because it was primarily designed for wire protocol inspection.
        """

        index = 0
        segment_hex_form = ""
        segment_ascii_form = ""

        for b in data_bytes:
            byte_hex_form = '{:02X}'.format(b)
            byte_ascii_form = BinaryDataHelper.byte_to_printable_character(b)

            segment_hex_form += byte_hex_form + " "
            segment_ascii_form += byte_ascii_form

            index += 1

            if index < len(data_bytes):
                # prints the whole segment when eligible
                if index % 16 == 0:
                    print("%s    %s" % (segment_hex_form.rstrip(), segment_ascii_form.rstrip()))
                    segment_hex_form = ""
                    segment_ascii_form = ""
                # splits segment into half when eligible
                elif index % 8 == 0:
                    segment_hex_form += " "
                    segment_ascii_form += " "

        # prints the last segment (strings are justified because the last segment usually contains less than 16 bytes)
        if segment_hex_form != "":
            print("%s    %s" % (segment_hex_form.rstrip().ljust(48), segment_ascii_form.rstrip().ljust(16)))

    @staticmethod
    def byte_to_printable_character(b):
        """
        Converts the given byte value into a printable character.

        The method mimics behavior of Wireshark "Packet bytes" inspection window
        because it was primarily designed for wire protocol inspection.

        :param b: Byte value to be converted into printable character.
        :type b: int
        """

        if b >= 32 and b <= 126:
            return chr(b)
        else:
            return '.'


class DataTypeDefinition:
    def __init__(self, primary_id, secondary_id="", template_argument=None):
        self._primary_id = primary_id
        self._secondary_id = secondary_id
        self._template_argument = template_argument

    @property
    def primary_id(self):
        return self._primary_id

    @property
    def secondary_id(self):
        return self._secondary_id

    @property
    def template_argument(self):
        return self._template_argument

    def __eq__(self, other):
        if isinstance(other, DataTypeDefinition):
            return self._primary_id == other._primary_id and self._secondary_id == other._secondary_id \
                   and self._template_argument == other.template_argument
        else:
            raise NotImplementedError

    def __ne__(self, other):
        if isinstance(other, DataTypeDefinition):
            return not (self == other)
        else:
            raise NotImplementedError

    def __repr__(self):
        argument = self._secondary_id if self._secondary_id != "" else ""
        argument = repr(self._template_argument) if self._template_argument is not None else argument

        if self == DataType.UNKNOWN:
            primary = "Unknown"
        elif self == DataType.INT32:
            primary = "Int32"
        elif self == DataType.INT64:
            primary = "Int64"
        elif self == DataType.DOUBLE:
            primary = "Double"
        elif self == DataType.BOOL:
            primary = "Bool"
        elif self == DataType.STRING:
            primary = "String"
        elif self == DataType.BYTE_ARRAY:
            primary = "ByteArray"
        elif self == DataType.VOID:
            primary = "Void"
        elif self._primary_id == DataType.LIST_PRIMARY_ID:
            primary = "List"
        elif self._primary_id == DataType.STRUCTURE_PRIMARY_ID or self._primary_id == DataType.DYNAMIC_OBJECT_HANDLE_PRIMARY_ID\
                or self._primary_id == DataType.DYNAMIC_OBJECT_PRIMARY_ID:
            primary = "Complex"
        else:
            primary = hex(self._primary_id)

        return primary + (("<" + argument + ">") if argument != "" else "")


class DataType:
    """DataType lists descriptors of common API data types."""

    UNKNOWN = DataTypeDefinition(0x00)
    INT32 = DataTypeDefinition(0x01)
    INT64 = DataTypeDefinition(0x02)
    DOUBLE = DataTypeDefinition(0x03)
    BOOL = DataTypeDefinition(0x04)
    STRING = DataTypeDefinition(0x05)
    BYTE_ARRAY = DataTypeDefinition(0x06)
    VOID = DataTypeDefinition(0x64)

    STRUCTURE_PRIMARY_ID = 0x0B
    """Primary identifier for structure data types."""

    LIST_PRIMARY_ID = 0x0C
    """Primary identifier for list data types."""

    DYNAMIC_OBJECT_HANDLE_PRIMARY_ID = 0x0D
    """Primary identifier for dynamic object handle data types."""

    DYNAMIC_OBJECT_PRIMARY_ID = 0x0E
    """Primary identifier for dynamic object handle data types."""


class __UndefinedParameter:
    pass


UndefinedParameter = __UndefinedParameter()


class HandyStopwatch:
    def __init__(self, format="Duration: %.3f ms", evaluation_action=None, is_in_use=True):
        self.format = format
        self.evaluation_action = evaluation_action
        self.is_in_use = is_in_use
        self.begin = None
        self.end = None

    def __enter__(self):
        if not self.is_in_use:
            return

        self.begin = time.perf_counter()

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if not self.is_in_use:
            return

        self.end = time.perf_counter()
        duration_in_milliseconds = (self.end - self.begin) * 1000.0

        if self.evaluation_action:
            self.evaluation_action(duration_in_milliseconds)
        else:
            print(self.format % duration_in_milliseconds)

        self.end = time.perf_counter()


class ApiErrorCode:
    GENERAL_ERROR = 0x0001
    SESSION_HANDSHAKE_ERROR = 0x0044
    MESSAGE_PROCESSING_ERROR = 0x0057
    CALL_DISPATCH_ERROR = 0x0120
    CALL_ROUTING_ERROR = 0x0123
    CALL_INTERRUPT = 0x0127
    APPLICATION_SERVER_ERROR = 0x0208
    APPLICATION_CLIENT_ERROR = 0x0209
    MARSHALLING_ERROR = 0x0215


class ApiException(Exception):
    """
    ApiException is a generic exception to be thrown when an API error occurs anywhere in the stack.

    There is a set of exceptions derived from ApiException that may be used to carry additional information about the error. Usage of
    descendants is encouraged where possible, but it is not unusual to throw ApiException itself.
    """
    def __init__(self, api_error_code, message, inner_exception=None):
        super().__init__(message)

        self.api_error_code = api_error_code
        self.inner_exception = inner_exception


class ApplicationServerException(ApiException):
    """
    ApplicationServerException is an exception expected to be thrown by application server logic when an error is encountered.

    This exception is expected to be used in all cases in which an implemented (non-generated) part of the application server needs to report an API error.
    """

    def __init__(self, message):
        super().__init__(ApiErrorCode.APPLICATION_SERVER_ERROR, message)

        self.application_error_code = None
        self.original_error_type = None
        self.original_error_code = None
        self.original_error_description = None

    def __str__(self):
        string_representation = super().__str__()

        if self.application_error_code:
            string_representation += " (Error code: " + '0x{:04X}'.format(self.application_error_code) + ")"

        if self.original_error_description:
            string_representation += "\r\n" + self.original_error_description

        return string_representation


class MarshallingException(ApiException):
    """
    MarshallingException is an exception to be thrown when an error occurs during marshalling of call parameters or call result.
    """

    DEFAULT_ERROR_MESSAGE = "An error occurred during data encoding/decoding."

    def __init__(self):
        super().__init__(ApiErrorCode.MARSHALLING_ERROR, MarshallingException.DEFAULT_ERROR_MESSAGE)


class InvalidOperationException(Exception):
    def __init__(self, message):
        super().__init__(message)
