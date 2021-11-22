from threading import Thread, Lock
import time
import sys

from ..common import CommunicationSide, TransportEndpointDefinition, CallRequest, CallResponse, SequenceNumberGenerator, ApiErrorCode, ApiException, CallResult
from ..framed_transport import Frame, FrameSocket, ClientFrameSocket, FrameSocketException
from ..logging import Logging, LogDomain, LogEntrySeverity

from .crates import *
from .utilities import CallOperationCode, OrcLoggingHelper, MessageSerializer, MessageDeserializer, OptionalFieldDeserializer, ErrorConverter


class EndpointState:
    """EndpointState lists possible states of an endpoint."""

    IDLE = 1
    """State in which an endpoint is until it starts proper operation."""

    RUNNING = 2
    """
    State in which an endpoint is during normal operation.

    For client endpoint, the state refers to a situation in which a session is active.
    """

    STOPPED = 3
    """
    State in which an endpoint is after it is deliberately stopped or recovery mechanism definitely fails.

    Intermittent communication breakdowns, usually caused by temporarily broken connections, are not considered reasons for stopping.
    Once the endpoint is stopped, it can not be made working again.
    """

    @staticmethod
    def to_log_entry_string(state):
        if state == EndpointState.IDLE:
            return "Idle"
        if state == EndpointState.RUNNING:
            return "Running"
        if state == EndpointState.STOPPED:
            return "Stopped"

        return "?"


class ClientEndpoint:
    """
    ClientEndpoint is a top-level component of ORC subsystem for client-side application.

    Python version of ORC comes with compact ClientEndpoint which does not contain internal subsystems like SessionManager, Messenger
    and includes functionality of these subsystems on its own.
    """

    VITALITY_CHECK_INTERVAL = 250
    """Timespan (in milliseconds) between two vitality checks."""

    PRESENT_VITALITY_CHECKS = False
    """Tells whether vitality checks (performed via keep-alive messages) should be presented to the user by dots in standard output."""

    def __init__(self):
        """Creates a client endpoint."""
        self.state = EndpointState.IDLE
        self.__state_lock = Lock()

        self.__call_processing_lock = Lock()
        self.__send_message_lock = Lock()

        self.session_id = None
        self.__server_transport_endpoint = None
        self.__socket = None
        self.__call_sequence_number_generator = SequenceNumberGenerator()

        self.__vitality_check_thread = None

    def connect(self, server_transport_endpoint: TransportEndpointDefinition):
        """
        Connects to a server expected to be listening on the given transport endpoint.

        :param server_transport_endpoint: Definition of a transport endpoint (ISO/OSI 4) on which the server is expected to listen.
        :type server_transport_endpoint: TransportEndpointDefinition

        :raises EndpointException: Raised when a connection can not be established. Common reasons include improper state (the endpoint is
        either already running or stopped), transport layer problems (e.g., server can not be reached or refuses the connection on transport
        layer) and session layer problems (server refuses the connection on session layer). See "cause" member for actual reason.
        """

        # Throws an exception when the endpoint is either already running or stopped.
        # DO NOT allow starting stopped endpoint, the logic is not ready for that.
        with self.__state_lock:
            if self.state != EndpointState.IDLE:
                error_message = "Endpoint cannot be started in a state of '" + str(self.state) + "'."
                Logging.loggers[LogDomain.ORC].log_orc_error(CommunicationSide.CLIENT, "Endpoint", error_message)
                raise EndpointException(error_message, EndpointExceptionCause.STATE)

        try:
            socket = self._create_client_frame_socket()
            socket.connect(server_transport_endpoint)

            try:
                self.__perform_handshake(socket)
            except SessionJoinException as ex:
                error_message = "Cannot connect to the server at " + str(server_transport_endpoint) + " because of session layer issues."
                Logging.loggers[LogDomain.ORC].log_orc_error(CommunicationSide.CLIENT, "Endpoint", error_message)
                raise EndpointException(error_message, EndpointExceptionCause.L5_NETWORKING, ex) from ex

            self.__socket = socket
            self.__server_transport_endpoint = server_transport_endpoint

            with self.__state_lock:
                Logging.loggers[LogDomain.ORC].log_orc_state_change(CommunicationSide.CLIENT, "Endpoint", EndpointState.to_log_entry_string(self.state), "Connect", EndpointState.to_log_entry_string(EndpointState.RUNNING))
                self.state = EndpointState.RUNNING

            self.__start_vitality_check_thread()

        except FrameSocketException as ex:
            error_message = "Cannot connect to the server at " + str(server_transport_endpoint) + " because of transport layer issues."
            Logging.loggers[LogDomain.ORC].log_orc_error(CommunicationSide.CLIENT, "Endpoint", error_message)
            raise EndpointException(error_message, EndpointExceptionCause.L4_NETWORKING, ex) from ex

    def disconnect(self):
        """
        Disconnects from the server.

        Once disconnected, the client can not connect again. Create a new client when another connection is desired.

        :raises EndpointException: Raised when disconnection can not take place. Common reason is improper state
        (the endpoint is already stopped). See "cause" member for actual reason.
        """

        with self.__state_lock:
            if self.state == EndpointState.IDLE:
                error_message = "Cannot disconnect client which has not been connected before."
                Logging.loggers[LogDomain.ORC].log_orc_error(CommunicationSide.CLIENT, "Endpoint", error_message)
                raise EndpointException(error_message, EndpointExceptionCause.STATE)

            if self.state == EndpointState.STOPPED:
                return

            Logging.loggers[LogDomain.ORC].log_orc_state_change(CommunicationSide.CLIENT, "Endpoint", EndpointState.to_log_entry_string(self.state), "Disconnect", EndpointState.to_log_entry_string(EndpointState.STOPPED))
            self.state = EndpointState.STOPPED

        if self.__socket:
            self.__socket.disconnect()

    def perform_call(self, call_request: CallRequest):
        """
        Performs call according to the given request and returns appropriate response.

        :type call_request:

        :raises ApiException: Raised when an error occurs (includes server as well as client errors).
        """

        # equips the given call request with information that could not be filled in by the original caller
        call_request.session_id = self.session_id if self.session_id is not None else "NONE"
        call_request.call_id = self.__call_sequence_number_generator.generate_sequence_number()

        log_entry_message = "Call entered client ORC, " + OrcLoggingHelper.format_call_target_parameter(call_request)
        Logging.loggers[LogDomain.ORC].log_call_notification(call_request.wide_call_id, CallOperationCode.ENTER, CommunicationSide.CLIENT, log_entry_message)

        # Acquires lock ensuring that only one call is processed at a moment.
        # DO NOT remove this lock -- Python version of ORC is not designed to deal with concurrent calls.
        with self.__call_processing_lock:

            # quits immediately if the endpoint is not running
            with self.__state_lock:
                if self.state != EndpointState.RUNNING:
                    api_exception = ApiException(ApiErrorCode.CALL_DISPATCH_ERROR, "Cannot perform a call because the client is not running.")
                    Logging.loggers[LogDomain.ORC].log_call_error(call_request.wide_call_id, CommunicationSide.CLIENT, api_exception)
                    raise api_exception

            # repeats call attempts until a response is received or an unrecoverable failure occurs
            while True:
                with self.__state_lock:
                    if self.state == EndpointState.STOPPED:
                        api_exception = CallInterruptException("Call was interrupted because the client was stopped.")
                        Logging.loggers[LogDomain.ORC].log_call_error(call_request.wide_call_id, CommunicationSide.CLIENT, api_exception)
                        raise api_exception

                try:
                    # issues the given call request
                    self.__issue_call_request(call_request)

                    # waits for a corresponding call response, throwing an exception when an unrecoverable error occurs
                    call_response = self.__wait_for_call_response(call_request)
                    
                    # throws an exception when call response was received properly, but the call was not successful
                    if not call_response.was_call_successful:
                        api_exception = ErrorConverter.api_error_to_api_exception(call_response.error)

                        Logging.loggers[LogDomain.ORC].log_call_error(call_request.wide_call_id, CommunicationSide.CLIENT, api_exception)
                        raise api_exception

                    Logging.loggers[LogDomain.ORC].log_call_notification(call_request.wide_call_id, CallOperationCode.LEAVE, CommunicationSide.CLIENT, "Call left client ORC")
                    return call_response

                except FrameSocketException:
                    Logging.loggers[LogDomain.ORC].log_call_error(call_request.wide_call_id, CommunicationSide.CLIENT)
                    socket_error_occurred = True

                if socket_error_occurred:
                    # attempts to recover if the call attempt failed due to connection issues
                    recovery_successful = self.__perform_recovery()

                    # throws an exception if all recovery attempts definitely fail
                    if not recovery_successful:
                        with self.__state_lock:
                            Logging.loggers[LogDomain.ORC].log_orc_state_change(CommunicationSide.CLIENT, "Endpoint", EndpointState.to_log_entry_string(self.state), "HandleRecoveryFailure", EndpointState.to_log_entry_string(EndpointState.STOPPED))
                            self.state = EndpointState.STOPPED

                        api_exception = CallInterruptException("Call was interrupted because connection to server has been lost and could not be recovered.")
                        Logging.loggers[LogDomain.ORC].log_call_error(call_request.wide_call_id, CommunicationSide.CLIENT, api_exception)
                        raise api_exception
                    else:
                        # issues the given call request again after recovery
                        self.__issue_call_request(call_request)

                        # waits for a corresponding call response, throwing an exception when an unrecoverable error occurs
                        call_response = self.__wait_for_call_response(call_request)

                        # throws an exception when call response was received properly, but the call was not successful
                        if not call_response.was_call_successful:
                            api_exception = ErrorConverter.api_error_to_api_exception(call_response.error)

                            Logging.loggers[LogDomain.ORC].log_call_error(call_request.wide_call_id,
                                                                          CommunicationSide.CLIENT, api_exception)
                            raise api_exception

                        Logging.loggers[LogDomain.ORC].log_call_notification(call_request.wide_call_id,
                                                                             CallOperationCode.LEAVE,
                                                                             CommunicationSide.CLIENT,
                                                                             "Call left client ORC")
                        return call_response

    def _create_client_frame_socket(self):
        client_frame_socket = ClientFrameSocket()
        return client_frame_socket

    def __run_vitality_check_loop(self):
        """
        Runs loop to perform vitality checks.

        Vitality checks are done by sending keep-alive messages. This loop only logs vitality check when it detects it.
        Recovery is a reponsibility of perform_call() method which is expected to perform the recovery and repeat the
        call request afterwards. If there is no call being processed at the moment, the recovery is expected to take
        place upon the next call request.
        """

        vitality_check_interval_in_seconds = ClientEndpoint.VITALITY_CHECK_INTERVAL / 1000

        previous_check_successful = True

        while True:
            if self.state == EndpointState.STOPPED:
                break

            # tries to send a keep-alive message through the current socket and evaluates the result
            try:
                keep_alive_message = KeepAliveMessage()

                # sends message under lock to avoid interference with normal traffic (usually related to calls)
                with self.__send_message_lock:
                    self.__send_message_directly(keep_alive_message, self.__socket)

                check_successful = True
            except:
                check_successful = False

            # logs vitality change when detected
            if check_successful != previous_check_successful:
                log_entry_severity = LogEntrySeverity.WARNING if not check_successful else LogEntrySeverity.INFORMATIONAL
                Logging.loggers[LogDomain.ORC].log_session_event(self.session_id, CommunicationSide.CLIENT, "Session vitality changed to %r" % check_successful, log_entry_severity)

                previous_check_successful = check_successful

            # presents vitality check by a dot in standard output where eligible
            if ClientEndpoint.PRESENT_VITALITY_CHECKS:
                print('.', end='')
                sys.stdout.flush()

            # waits before the next vitality check
            time.sleep(vitality_check_interval_in_seconds)

    def __start_vitality_check_thread(self):
        """Creates and starts vitality check thread."""

        self.__vitality_check_thread = Thread(target=self.__run_vitality_check_loop, daemon=True)
        self.__vitality_check_thread.start()

    def __perform_handshake(self, socket: FrameSocket):
        """
        Performs session handshake from client side using the given socket.

        :type socket: FrameSocket

        :raises FrameSocketException: Thrown when the handshake fails because of connection issues.
        :raises SessionJoinException: Thrown when the handshake fails for reasons beyond connection issues.
        """

        # sends "Session inquiry" message
        message = SessionInquiryMessage()
        self.__send_message_directly(message, socket)

        # receives "Session offer" message
        message = self.__receive_message_directly(socket)

        # handles "Session error" message
        if message.type == MessageType.SESSION_ERROR:
            raise SessionJoinException("An error occurred during session handshake.")

        # checks that the received message is "Session offer" message, which is the only one expected on success
        if message.type != MessageType.SESSION_OFFER:
            raise SessionJoinException("Unexpected message (0x" + '{:02X}'.format(message.type) + ") was received instead of \"Session offer\" message.")

        # handles "Session offer" message
        offered_session_id = message.offered_session_id

        # chooses desired session ID (either previously used one or the one offered by server)
        desired_session_id = self.session_id
        if desired_session_id is None:
            desired_session_id = offered_session_id

        # sends "Session join request" message
        message = SessionJoinRequestMessage()
        message.desired_session_id = desired_session_id
        self.__send_message_directly(message, socket)

        # receives "Session join response" message
        message = self.__receive_message_directly(socket)

        # handles "Session error" message
        if message.type == MessageType.SESSION_ERROR:
            raise SessionJoinException("An error occurred during session handshake.")

        # checks that the received message is "Session join response" message, which is the only one expected on success
        if message.type != MessageType.SESSION_JOIN_RESPONSE:
            raise SessionJoinException("Unexpected message (0x" + '{:02X}'.format(message.type) + ") was received instead of \"Session join response\" message.")

        # handles session join response message
        assigned_session_id = message.assigned_session_id

        if assigned_session_id != desired_session_id:
            raise SessionJoinException("Session join response could not be processed properly.")

        self.session_id = assigned_session_id

    def __perform_recovery(self):
        """
        Performs session recovery until it succeeds or definitely fails.

        :return: Returns True when session is successfully recovered, False when the session recovery definitely fails.
        """

        recovery_step_number = 1

        print("Client lost connection to server")
        Logging.loggers[LogDomain.ORC].log_session_event(self.session_id, CommunicationSide.CLIENT, "Recovery started", LogEntrySeverity.INFORMATIONAL)

        # disconnects previously used socket (if any) to avoid depletion of system resources
        if self.__socket is not None:
            try:
                self.__socket.disconnect()
            except:
                pass

        while True:
            print("Client is trying to recover connection...")

            try:
                Logging.loggers[LogDomain.ORC].log_session_event(self.session_id, CommunicationSide.CLIENT, "Performing recovery attempt %d" % recovery_step_number, LogEntrySeverity.INFORMATIONAL)

                new_socket = ClientFrameSocket()
                new_socket.connect(self.__server_transport_endpoint)

                self.__perform_handshake(new_socket)

                self.__socket = new_socket

                print("Client successfully recovered connection to server")
                Logging.loggers[LogDomain.ORC].log_session_event(self.session_id, CommunicationSide.CLIENT, "Recovery succeeded", LogEntrySeverity.INFORMATIONAL)

                return True

            except Exception:
                Logging.loggers[LogDomain.ORC].log_session_error(self.session_id, CommunicationSide.CLIENT, "Recovery attempt %d failed" % recovery_step_number)

            # advances to the next recovery step
            recovery_step_number += 1
            try_again, delay_in_milliseconds = self.__determine_next_recovery_step(recovery_step_number)

            # considers session recovery failed after several recovery attempts (steps)
            if not try_again:
                print("Client was not able to recover connection")
                Logging.loggers[LogDomain.ORC].log_session_error(self.session_id, CommunicationSide.CLIENT, "Recovery failed")
                return False

            delay_in_seconds = delay_in_milliseconds / 1000.0
            print("Client was not able to recover connection. Next recovery attempt in %.1fs" % delay_in_seconds)

            time.sleep(delay_in_seconds)

    def __determine_next_recovery_step(self, next_step_number):
        """
        Tells what step should be taken next in a session recovery process after an unsuccessful attempt.

        The method provides information whether another attempt should be made to recover the session (via try_again
        component of the result tuple) and timespan (in milliseconds) to wait before the next recovery attempt is made
        (via delay_in_milliseconds component of the result tuple).

        :param next_step_number: Sequence number of the next step.
        :return: Returns tuple (try_again, delay_in_milliseconds).
        """

        try_again = False
        delay_in_milliseconds = 0

        # 2 steps after 0.5 second delay
        if next_step_number >= 2 and next_step_number <= 3:
            try_again = True
            delay_in_milliseconds = 500

        # 2 steps after 2 second delay
        if next_step_number >= 4 and next_step_number <= 5:
            try_again = True
            delay_in_milliseconds = 2000

        # 5 steps after 5 second delay
        if next_step_number >= 6 and next_step_number <= 10:
            try_again = True
            delay_in_milliseconds = 5000

        return try_again, delay_in_milliseconds

    def __send_message_directly(self, message: Message, socket: FrameSocket):
        """
        Sends message directly through the given socket.

        :type message: Message
        :type socket: FrameSocket

        :raises FrameSocketException: Thrown when an error occurs when sending data through the socket.
        :raises MessageSerializationException: Thrown when message serialization fails.
        """

        message_bytes = MessageSerializer.serialize_message(message)
        frame = Frame(message_bytes)
        socket.send_frame(frame)

    def __receive_message_directly(self, socket: FrameSocket):
        """
        Receives message directly from the given socket. The method blocks if there is no message available.

        :type socket: FrameSocket

        :raises FrameSocketException: Thrown when an error occurs when receiving data from the socket.
        :raises MessageSerializationException: Thrown when message deserialization fails upon receiving data.
        """

        frame = socket.receive_frame()
        message = MessageDeserializer.deserialize_message(frame.content)
        return message

    def __issue_call_request(self, call_request: CallRequest):
        """
        Issues the given call request.

        :type call_request: CallRequest

        :raises FrameSocketException: Thrown when an error occurs when sending data through the socket.
        :raises MessageSerializationException: Thrown when message serialization fails.
        """

        # updates call attempt number
        if call_request.attempt_number == 255:
            call_request.attempt_number = 1
        else:
            call_request.attempt_number += 1

        # creates "Call request" message and sets it up according to the given call request
        call_request_message = CallRequestMessage()
        call_request_message.session_id = call_request.session_id
        call_request_message.call_id = call_request.call_id
        call_request_message.attempt_number = call_request.attempt_number
        call_request_message.method_name = call_request.method_name
        call_request_message.object_id = call_request.object_id
        call_request_message.parameter_bytes = call_request.parameters.serialized_bytes

        # sends message under lock to avoid interference with vitality checking mechanism
        with self.__send_message_lock:
            self.__send_message_directly(call_request_message, self.__socket)

        return

    def __wait_for_call_response(self, call_request: CallRequest):
        """
        Waits for proper response to the given call request.

        Proper call response may carry either call result or call error information.

        The method blocks until it is able to provide proper call response or until an unrecoverable error occurs.
        Call responses not matching the given call request are ignored as well as all messages not understood by the current endpoint implementation.
        When an unrecoverable error occurs (e.g., the session is ended by the server), an exception is fired directly from the method.

        :type call_request: CallRequest
        :raises ApiException: Raised when an unrecoverable error occurs and proper call response can not be provided.
        """

        while True:
            message = self.__receive_message_directly(self.__socket)

            if message.type == MessageType.CALL_RESULT or message.type == MessageType.CALL_ERROR:
                try:
                    call_response = self.__call_response_message_to_call_response(message)
                    if call_response and call_response.call_id == call_request.call_id:
                        return call_response

                    log_entry_message = "EVT @ CLNT Endpoint - Response to call %s was omitted during waiting for response to call %s" % (call_response.wide_call_id, call_request.wide_call_id)
                    Logging.loggers[LogDomain.ORC].log_event(log_entry_message, LogEntrySeverity.INFORMATIONAL)
                except Exception as ex:
                    api_exception = ApiException(ApiErrorCode.GENERAL_ERROR, "An unexpected error occurred during call processing.", ex)
                    Logging.loggers[LogDomain.ORC].log_call_error(call_request.wide_call_id, CommunicationSide.CLIENT, api_exception)
                    raise api_exception from ex

            if message.type == MessageType.SESSION_ERROR or message.type == MessageType.SESSION_END:
                api_exception = CallInterruptException("Call was interrupted because server ended the session.")
                Logging.loggers[LogDomain.ORC].log_call_error(call_request.wide_call_id, CommunicationSide.CLIENT, api_exception)
                raise api_exception

    def __call_response_message_to_call_response(self, message):
        """
        Converts the given call response message to call response crate.

        Call response message can be either "Call result" message or "Call error" message. In both cases, CallResponse() crate is created.
        """

        call_response = CallResponse()
        call_response.session_id = message.session_id
        call_response.call_id = message.call_id

        if message.type == MessageType.CALL_RESULT:
            call_response.was_call_successful = True
            call_response.result = CallResult()
            call_response.result.serialized_bytes = message.result_bytes

        if message.type == MessageType.CALL_ERROR:
            call_response.was_call_successful = False

            api_error = ApiError()
            api_error.error_code = message.error_code
            api_error.error_description = message.error_description
            api_error.optional_fields.serialized_bytes = message.optional_field_bytes
            call_response.error = api_error

            OptionalFieldDeserializer.deserialize_optional_fields(api_error.optional_fields)

        return call_response


class EndpointExceptionCause:
    """
    EndpointExceptionCause lists possible reasons for throwing EndpointException.

    EndpointException handling differs very slightly for different causes so introduction
    of distinct exception classes is considered overkill.
    """

    UNKOWN = 0

    STATE = 1
    """STATE cause is used when endpoint state is not in an eligible state to perform an operation."""

    CONFIGURATION = 2

    L4_NETWORKING = 4
    """L4_NETWORKING cause is used when an operation failed because of transport layer (ISO/OSI level 4) issues."""

    L5_NETWORKING = 5
    """L5_NETWORKING cause is used when an operation failed because of session layer (ISO/OSI level 5) issues."""


class EndpointException(Exception):
    """
    EndpointException is an exception to be thrown when an endpoint encounters an error which is not an API error.

    Reasons for throwing this exception include e.g. invalid node configuration, initial connection issues (e.g., transport endpoint
    binding failure or host name resolution) and invalid operation issues related to the endpoint state.
    """

    def __init__(self, message, cause=None, inner_exception=None):
        super().__init__(message)

        self.cause = cause
        self.inner_exception = inner_exception


class CallInterruptException(ApiException):
    """
    CallInterruptException is an exception to be thrown when a call is unexpectedly interrupted.
    """

    def __init__(self, message):
        super().__init__(ApiErrorCode.CALL_INTERRUPT, message)


class SessionJoinException(Exception):
    """
    SessionJoinException is an exception that is thrown when a session join attempt fails for reasons beyond connection issues.

    When this exception is thrown, a session join attempt probably run into a failure which is very rare and non-standard (in contrary to usual
    connection issues). Possible reasons primarily include errors in handshake protocol -- e.g., unexpected order or type of messages,
    mismatch in session identifier offered/desired/assigned w.r.t. session join type (new/recovered) and session state.

    SessionJoinException is an internal exception, which should be handled and wrapped before being thrown out of ORC code.
    """

    def __init__(self, message, inner_exception=None):
        super().__init__(message)

        self.inner_exception = inner_exception
