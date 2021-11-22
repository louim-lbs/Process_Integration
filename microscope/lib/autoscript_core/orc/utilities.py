from ..common import CommunicationSide, CallRequest, ApiException, ApiErrorCode, ApplicationServerException
from ..logging import Logging, LogDomain, Logger, LogEntrySeverity, LogEntryCategory
from ..serialization import BasicValueSerializer, BasicValueDeserializer, BytesChopper, BytesBuilder
from .crates import *


class CallOperationCode:
    ENTER = "ENTER"
    LEAVE = "LEAVE"


class OrcLoggingHelper:
    @staticmethod
    def extend_loggers():
        Logger.log_orc_event = OrcLoggingHelper.log_orc_event  # "monkey patching"
        Logger.log_orc_state_change = OrcLoggingHelper.log_orc_state_change  # "monkey patching"
        Logger.log_orc_error = OrcLoggingHelper.log_orc_error  # "monkey patching"
        Logger.log_session_event = OrcLoggingHelper.log_session_event  # "monkey patching"
        Logger.log_session_error = OrcLoggingHelper.log_session_error  # "monkey patching"
        Logger.log_call_notification = OrcLoggingHelper.log_call_notification  # "monkey patching"
        Logger.log_call_error = OrcLoggingHelper.log_call_error  # "monkey patching"

    def log_orc_event(self, subject_type, subject_id, operation_code, communication_side: CommunicationSide, subsystem_id, message, severity, category=LogEntryCategory.DEVELOPER1):
        log_entry_message = "%s %s %s @ %s %s - %s" % (subject_type, subject_id, operation_code, OrcLoggingHelper.__abbreviate_communication_side(communication_side), subsystem_id, message)
        self.log_event(log_entry_message, severity, category)
        pass

    def log_orc_state_change(self, communication_side, subsystem_id, previous_state, transition, new_state):
        log_entry_message = "STATE @ %s %s - %s --%s--> %s" % (OrcLoggingHelper.__abbreviate_communication_side(communication_side), subsystem_id, previous_state, transition, new_state)
        self.log_event(log_entry_message, LogEntrySeverity.INFORMATIONAL, LogEntryCategory.STATE_CHANGE)
        pass

    def log_orc_error(self, communication_side, subsystem_id, message):
        log_entry_message = "ERR @ " + OrcLoggingHelper.__abbreviate_communication_side(communication_side) + " " + subsystem_id + " - " + message
        self.log_error(log_entry_message)

    def log_session_event(self, session_id, communication_side, message, severity, category=LogEntryCategory.DEVELOPER1):
        log_entry_message = "%s %s %s @ %s %s - %s" % ("SSN", "[" + session_id + "]", "EVT", OrcLoggingHelper.__abbreviate_communication_side(communication_side), "Endpoint", message)
        self.log_event(log_entry_message, severity, category)

    def log_session_error(self, session_id, communication_side, message):
        log_entry_message = "%s %s %s @ %s %s - %s" % ("SSN", "[" + session_id + "]", "ERR", OrcLoggingHelper.__abbreviate_communication_side(communication_side), "Endpoint", message)
        self.log_error(log_entry_message)

    def log_call_notification(self, wide_call_id, operation_code, communication_side: CommunicationSide, message):
        log_entry_message = "CALL %s %s @ %s Endpoint - %s" % (wide_call_id, operation_code, OrcLoggingHelper.__abbreviate_communication_side(communication_side), message)
        self.log_notification(log_entry_message)

    def log_call_error(self, wide_call_id, communication_side: CommunicationSide, api_exception=None):
        extended_message = "An error occurred during call processing"
        if api_exception:
            extended_message += "\r\n\r\n" + OrcLoggingHelper.api_exception_to_log_entry_string(api_exception)

        log_entry_message = "CALL %s %s @ %s Endpoint - %s" % (wide_call_id, "ERR", OrcLoggingHelper.__abbreviate_communication_side(communication_side), extended_message)
        self.log_error(log_entry_message)

    @staticmethod
    def format_call_target_parameter(call_request: CallRequest):
        formatted_parameter = "Target=%s.%s()" % (call_request.object_id, call_request.method_name)
        return formatted_parameter

    @staticmethod
    def api_exception_to_log_entry_string(api_exception):
        """
        Converts the given API exception into a string suitable for log entry message.

        The string is expected to be appended to the log entry message as an additional information.
        Standard string representation function ApiException.__str__() is not used for this purpose
        becaues it is also utilized by Python debuggers for which string representation provided
        by this method is not suitable.

        :param api_exception: API exception to be converted to a string.
        :type api_exception: ApiException
        """
        api_error_code_line = "API error code: 0x" + '{:04X}'.format(api_exception.api_error_code)
        description_line = "Description: " + str(api_exception)

        return api_error_code_line + "\r\n" + description_line

    @staticmethod
    def __abbreviate_communication_side(communication_side):
        if communication_side == CommunicationSide.SERVER:
            return "SERV"
        elif communication_side == CommunicationSide.CLIENT:
            return "CLNT"

        return "?"


OrcLoggingHelper.extend_loggers()


class ApplicationClientLoggingHelper:
    @staticmethod
    def log_call_enter(call_request: CallRequest):
        parameter_types = ""
        for dtd in call_request.parameters.data_types:
            parameter_types += "" if parameter_types == "" else ","
            parameter_types += "0x" + '{:02X}'.format(dtd.primary_id)

        log_entry_message = "CALL [] ENTER @ CLNT ApplicationClient - Call entered application client, Target=%s.%s(%s)" % (call_request.object_id, call_request.method_name, parameter_types)
        Logging.loggers[LogDomain.APPLICATION_CLIENT].log_notification(log_entry_message)

    @staticmethod
    def log_call_leave():
        log_entry_message = "CALL [] LEAVE @ CLNT ApplicationClient - Call left application client"
        Logging.loggers[LogDomain.APPLICATION_CLIENT].log_notification(log_entry_message)

    @staticmethod
    def log_call_error(wide_call_id, api_exception=None):
        log_entry_message = "CALL %s ERR @ ApplicationClient - An error occurred during call processing" % wide_call_id
        if api_exception:
            log_entry_message += "\r\n\r\n" + OrcLoggingHelper.api_exception_to_log_entry_string(api_exception)

        Logging.loggers[LogDomain.APPLICATION_CLIENT].log_error(log_entry_message)


class MessageSerializer:
    @staticmethod
    def serialize_message(message):
        """
        Serializes the given message into a byte array.

        :raises MessageSerializationException: Thrown when serialization fails for whatever reason.
        """

        if message is None:
            raise MessageSerializationException("Null reference was passed to message serialization routine.")

        try:
            if message.type == MessageType.CALL_REQUEST:
                bytes_builder = BytesBuilder()
                call_request_message = message

                MessageSerializer.serialize_message_header(message, bytes_builder)
                BasicValueSerializer.serialize_string(call_request_message.session_id, bytes_builder)
                BasicValueSerializer.serialize_int32(call_request_message.call_id, bytes_builder)
                BasicValueSerializer.serialize_byte(call_request_message.attempt_number, bytes_builder)
                BasicValueSerializer.serialize_string(call_request_message.object_id, bytes_builder)
                BasicValueSerializer.serialize_string(call_request_message.method_name, bytes_builder)
                BasicValueSerializer.serialize_byte_array(call_request_message.parameter_bytes, bytes_builder)

                message_bytes = bytes_builder.get_data()

            elif message.type == MessageType.SESSION_INQUIRY:
                bytes_builder = BytesBuilder()
                MessageSerializer.serialize_message_header(message, bytes_builder)

                message_bytes = bytes_builder.get_data()

            elif message.type == MessageType.SESSION_JOIN_REQUEST:
                bytes_builder = BytesBuilder()
                session_join_request_message = message

                MessageSerializer.serialize_message_header(message, bytes_builder)
                BasicValueSerializer.serialize_string(session_join_request_message.desired_session_id, bytes_builder)

                message_bytes = bytes_builder.get_data()

            elif message.type == MessageType.KEEP_ALIVE:
                bytes_builder = BytesBuilder()
                MessageSerializer.serialize_message_header(message, bytes_builder)

                message_bytes = bytes_builder.get_data()
            else:
                raise MessageSerializationException("Serialization for message type of 0x" + '{:02X}'.format(message.type) + " is not implemented.")
        except Exception as ex:
            raise MessageSerializationException("An error occurred during serialization of message of type " + '{:02X}'.format(message.type) + ".", ex) from ex

        return message_bytes

    @staticmethod
    def serialize_message_header(message, bytes_builder):
        bytes_builder.add_bytes(bytes([message.type]))
        BasicValueSerializer.serialize_int32(message.sequence_number, bytes_builder)


class MessageDeserializer:
    @staticmethod
    def deserialize_message(message_bytes):
        """
        Deserializes a message from the given byte array.

        :raises MessageSerializationException: Thrown when deserialization fails for whatever reason.
        """
        chopper = BytesChopper(message_bytes, 0)
        message_type_byte = BasicValueDeserializer.deserialize_byte(chopper)

        try:
            if message_type_byte == MessageType.CALL_RESULT:
                message = CallResultMessage()
                message.sequence_number = BasicValueDeserializer.deserialize_int32(chopper)
                message.session_id = BasicValueDeserializer.deserialize_string(chopper)
                message.call_id = BasicValueDeserializer.deserialize_int32(chopper)
                message.result_bytes = BasicValueDeserializer.deserialize_byte_array(chopper)

            elif message_type_byte == MessageType.CALL_ERROR:
                message = CallErrorMessage()
                message.sequence_number = BasicValueDeserializer.deserialize_int32(chopper)
                message.session_id = BasicValueDeserializer.deserialize_string(chopper)
                message.call_id = BasicValueDeserializer.deserialize_int32(chopper)
                message.error_code = BasicValueDeserializer.deserialize_int32(chopper)
                message.error_description = BasicValueDeserializer.deserialize_string(chopper)
                message.optional_field_bytes = BasicValueDeserializer.deserialize_byte_array(chopper)

            elif message_type_byte == MessageType.SESSION_OFFER:
                message = SessionOfferMessage()
                message.sequence_number = BasicValueDeserializer.deserialize_int32(chopper)
                message.offered_session_id = BasicValueDeserializer.deserialize_string(chopper)

            elif message_type_byte == MessageType.SESSION_ERROR:
                message = SessionErrorMessage()
                message.sequence_number = BasicValueDeserializer.deserialize_int32(chopper)
                message.session_id = BasicValueDeserializer.deserialize_string(chopper)
                message.error_code = BasicValueDeserializer.deserialize_int32(chopper)
                message.error_description = BasicValueDeserializer.deserialize_string(chopper)

            elif message_type_byte == MessageType.SESSION_JOIN_RESPONSE:
                message = SessionJoinResponseMessage()
                message.sequence_number = BasicValueDeserializer.deserialize_int32(chopper)
                message.assigned_session_id = BasicValueDeserializer.deserialize_string(chopper)

            elif message_type_byte == MessageType.SESSION_END:
                message = SessionEndMessage()
                message.sequence_number = BasicValueDeserializer.deserialize_int32(chopper)

            else:
                raise MessageSerializationException("Deserialization for message type of 0x" + '{:02X}'.format(message_type_byte) + " is not implemented.")
        except Exception as ex:
            raise MessageSerializationException("An error occurred during deserialization of message of type " + '{:02X}'.format(message_type_byte) + ".", ex) from ex

        return message


class OptionalFieldDeserializer:
    """OptionalFieldDeserializer allows to deserialize optional fields used in API messages."""

    @staticmethod
    def deserialize_optional_fields(optional_fields: OptionalFields):
        """
        Deserializes all optional fields in the given collection.

        The given collection is expected to hold the optional fields in serialized form.
        Object representation of the fields is written back to the collection upon deserialization.

        :param optional_fields: Collection of optional fields to be deserialized.
        :type optional_fields: OptionalFields
        """

        try:
            chopper = BytesChopper(optional_fields.serialized_bytes)

            while chopper.bytes_left() > 0:
                optional_field_type = BasicValueDeserializer.deserialize_byte(chopper)
                optional_field_length = BasicValueDeserializer.deserialize_int32(chopper)

                optional_field = OptionalField(optional_field_type)

                if optional_field_type == OptionalFieldType.APPLICATION_ERROR_CODE:
                    optional_field.application_error_code = BasicValueDeserializer.deserialize_int32(chopper)
                elif optional_field_type == OptionalFieldType.ORIGINAL_ERROR_TYPE:
                    optional_field.original_error_type = BasicValueDeserializer.deserialize_string(chopper)
                elif optional_field_type == OptionalFieldType.ORIGINAL_ERROR_CODE:
                    optional_field.original_error_code = BasicValueDeserializer.deserialize_int32(chopper)
                elif optional_field_type == OptionalFieldType.ORIGINAL_ERROR_DESCRIPTION:
                    optional_field.original_error_description = BasicValueDeserializer.deserialize_string(chopper)
                else:
                    chopper.chop(optional_field_length)

                optional_fields.add_field(optional_field)

            pass
        except Exception:
            # Logs error during optional field deserialization. The whole method should never throw any exception
            # by design -- when optional fields can not be deserialized, they simply will not be available.
            Logging.loggers[LogDomain.ORC].log_error("An error occurred during optional field deserialization")


class ErrorConverter:
    """
    ErrorConverter allows to convert API error crate into API exception.

    API error crate (ApiError) is used in parts of the stack where reporting errors via exceptions is not possible or feasible.

    API exceptions are ApiException and its derivatives.
    """

    @staticmethod
    def api_error_to_api_exception(api_error: ApiError):
        """
        Converts the given API error into a corresponding API exception.

        The exception is not thrown from this method, it is just assembled and expected to be actually thrown by the caller.

        :param api_error: API error crate to be converted into a corresponding API exception.
        :type api_error: ApiError

        :return: API exception corresponding to the given API error crate.
        """

        if not api_error:
            api_exception = ApiException(ApiErrorCode.GENERAL_ERROR, "An unexpected error has occurred.")
        else:
            if api_error.error_code == ApiErrorCode.APPLICATION_SERVER_ERROR:
                api_exception = ApplicationServerException(api_error.error_description)
                api_exception.application_error_code = api_error.optional_fields.get_field_attribute(OptionalFieldType.APPLICATION_ERROR_CODE, "application_error_code")
                api_exception.original_error_type = api_error.optional_fields.get_field_attribute(OptionalFieldType.ORIGINAL_ERROR_TYPE, "original_error_type")
                api_exception.original_error_code = api_error.optional_fields.get_field_attribute(OptionalFieldType.ORIGINAL_ERROR_CODE, "original_error_code")
                api_exception.original_error_description = api_error.optional_fields.get_field_attribute(OptionalFieldType.ORIGINAL_ERROR_DESCRIPTION, "original_error_description")

            else:
                api_exception = ApiException(api_error.error_code, api_error.error_description)

        return api_exception


class MessageSerializationException(Exception):
    """
    MessageSerializationException is an exception that is thrown when message serialization/deserialization fails.

    MessageSerializationException is an internal exception, which should be handled and wrapped before being thrown out of the module.
    """

    def __init__(self, message, inner_exception=None):
        super().__init__(message)

        self.inner_exception = inner_exception
