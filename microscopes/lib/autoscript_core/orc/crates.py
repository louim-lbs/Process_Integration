class MessageType:
    UNKNOWN = 0x00
    CALL_REQUEST = 0x21
    CALL_RESULT = 0x22
    CALL_ERROR = 0x23
    CALL_FINISH = 0x28
    SESSION_INQUIRY = 0x51
    SESSION_OFFER = 0x52
    SESSION_ERROR = 0x53
    SESSION_JOIN_REQUEST = 0x54
    SESSION_JOIN_RESPONSE = 0x55
    SESSION_END = 0x58
    KEEP_ALIVE = 0x99


class Message:
    def __init__(self, message_type):
        self.type = message_type
        self.sequence_number = 0


class CallMessageBase(Message):
    def __init__(self, message_type):
        super().__init__(message_type)
        self.session_id = None
        self.call_id = None


class CallRequestMessage(CallMessageBase):
    def __init__(self):
        super().__init__(MessageType.CALL_REQUEST)
        self.attempt_number = 1
        self.object_id = None
        self.method_name = None
        self.parameter_bytes = None


class CallResultMessage(CallMessageBase):
    def __init__(self):
        super().__init__(MessageType.CALL_RESULT)
        self.result_bytes = None


class CallErrorMessage(CallMessageBase):
    def __init__(self):
        super().__init__(MessageType.CALL_ERROR)
        self.error_code = None
        self.error_description = None
        self.optional_field_bytes = None


class SessionInquiryMessage(Message):
    def __init__(self):
        super().__init__(MessageType.SESSION_INQUIRY)


class SessionOfferMessage(Message):
    def __init__(self):
        super().__init__(MessageType.SESSION_OFFER)
        self.offered_session_id = None


class SessionErrorMessage(Message):
    def __init__(self):
        super().__init__(MessageType.SESSION_ERROR)
        self.session_id = None
        self.error_code = None
        self.error_description = None


class SessionJoinRequestMessage(Message):
    def __init__(self):
        super().__init__(MessageType.SESSION_JOIN_REQUEST)
        self.desired_session_id = None


class SessionJoinResponseMessage(Message):
    def __init__(self):
        super().__init__(MessageType.SESSION_JOIN_RESPONSE)
        self.assigned_session_id = None


class SessionEndMessage(Message):
    def __init__(self):
        super().__init__(MessageType.SESSION_END)


class KeepAliveMessage(Message):
    def __init__(self):
        super().__init__(MessageType.KEEP_ALIVE)


class OptionalFieldType:
    """
    OptionalFieldType lists possible types of optional fields used in API messages.

    Optional fields are used e.g. in API error messages like "Call error" message and "Session error" message.
    """

    APPLICATION_ERROR_CODE = 0x12
    """
    ApplicationErrorCode field holds application specific error code suitable for presentation to the user.

    ApplicationErrorCode field value has to be explicitly defined in the application server logic.
    """

    ORIGINAL_ERROR_TYPE = 0x21
    """
    OriginalErrorType field holds type of the error that originally caused the API error.

    OriginalErrorType is based on type of the original exception thrown by the application server logic.
    """

    ORIGINAL_ERROR_CODE = 0x22
    """
    OriginalErrorCode field holds code of the error that originally caused the API error.

    OriginalErrorCode is based on HRESULT of the original exception thrown by the application server logic.
    """

    ORIGINAL_ERROR_DESCRIPTION = 0x23
    """
    OriginalErrorDescription field holds the description of the error that originally caused the API error.
    
    OriginalErrorDescription is based on the message of the original exception thrown by the application server logic.
    """


class OptionalField:
    def __init__(self, optional_field_type):
        self.type = optional_field_type


class OptionalFields:
    """OptionalFields is a collection of optional fields used in API messages."""

    def __init__(self):
        self.__fields = []
        self.__current_field_index = 0
        self.serialized_bytes = None

    def __getitem__(self, index):
        return self.__fields[index]

    def __iter__(self):
        return self

    def __next__(self):
        if self.__current_field_index >= len(self.__fields):
            raise StopIteration
        else:
            current_field = self.__fields[self.__current_field_index]
            self.__current_field_index += 1
            return current_field

    def add_field(self, field):
        self.__fields.append(field)

    def get_field(self, index):
        return self.__fields[index]

    def get_field_attribute(self, field_type, attribute_name):
        """
        Provides value of an attribute of the given name in an optional field of the given type.

        The method uses first optional field in the collection if there are more optional fields of the given type.

        This is a convenience method for simple cases. Caller can iterate over the collection of optional fields
        and perform advanced operations on its own in more complex scenarios.

        :param field_type: Type of an optional field to look for.
        :param attribute_name: Name of the desired attribute.

        :return: Returns value of the desired attribute when available, None otherwise.
        """

        field = next((f for f in self.__fields if f.type == field_type), None)
        if field:
            return getattr(field, attribute_name)

        return None


class ApiError:
    """
    ApiError contains information about an error that occurred during API operation.

    The crate is intended to be used only for call processing errors and session management errors, not all errors that appear in the stack.

    This crate is expected to be used only in parts of the stack where reporting errors via API exception is not possible
    or feasible. In most parts of the stack, exceptions derived from ApiException are expected to be used.
    """

    def __init__(self):
        self.error_code = 0x0000
        self.error_description = None
        self.optional_fields = OptionalFields()
