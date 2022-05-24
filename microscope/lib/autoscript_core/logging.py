import logging
import sys
import traceback
import fnmatch
import datetime
import os
import platform
import time
import uuid
import thermoscientific_logging


class LogEntrySeverity:
    INFORMATIONAL = thermoscientific_logging.Severity.INFORMATIONAL
    WARNING = thermoscientific_logging.Severity.WARNING
    ERROR = thermoscientific_logging.Severity.ERROR
    FATAL_ERROR = thermoscientific_logging.Severity.FATAL_ERROR


class LogEntryCategory:
    STATE_CHANGE = thermoscientific_logging.Category.STATE_CHANGE
    NOTIFICATION = thermoscientific_logging.Category.NOTIFICATION
    INTERNAL_ERROR = thermoscientific_logging.Category.INTERNAL_ERROR
    DEVELOPER1 = thermoscientific_logging.Category.DEVELOPER1


class LogDomain:
    ORC = 1
    APPLICATION_SERVER = 2
    APPLICATION_CLIENT = 3
    HOST = 4


class Logger:
    def log_event(self, message, severity, category=thermoscientific_logging.Category.DEVELOPER1):
        raise NotImplementedError()  # Recommended way to simulate abstract methods

    def log_error(self, message):
        extended_message = message
        if self._is_exception_being_handled():
            extended_message += "\r\n\r\n" + traceback.format_exc()

        self.log_event(extended_message, LogEntrySeverity.ERROR, LogEntryCategory.INTERNAL_ERROR)

    def log_notification(self, message):
        self.log_event(message, LogEntrySeverity.INFORMATIONAL, LogEntryCategory.NOTIFICATION)

    def _is_exception_being_handled(self):
        exception_type = sys.exc_info()[0]
        return exception_type is not None


class VoidLogger(Logger):
    def log_event(self, message, severity, category=thermoscientific_logging.Category.DEVELOPER1):
        pass


class AggregateLogger(Logger):
    def __init__(self):
        self.loggers = []

    def add_logger(self, logger: Logger):
        self.loggers.append(logger)

    def log_event(self, message, severity, category=thermoscientific_logging.Category.DEVELOPER1):
        for logger in self.loggers:
            logger.log_event(message, severity, category)

    def log_error(self, message):
        for logger in self.loggers:
            logger.log_error(message)

    def log_notification(self, message):
        for logger in self.loggers:
            logger.log_notification(message)


class PythonLogger(Logger):
    def __init__(self, originator):
        self.internal_logger = logging.getLogger(originator)
        pass

    def log_event(self, message, severity, category=thermoscientific_logging.Category.DEVELOPER1):
        if severity == LogEntrySeverity.INFORMATIONAL:
            self.internal_logger.info(message)
        if severity == LogEntrySeverity.WARNING:
            self.internal_logger.warning(message)
        if severity == LogEntrySeverity.ERROR:
            self.internal_logger.error(message)
        if severity == LogEntrySeverity.FATAL_ERROR:
            self.internal_logger.critical(message)

    def log_error(self, message):
        include_exception_information = self._is_exception_being_handled()
        self.internal_logger.error(message, exc_info=include_exception_information)


class InfraLogger(Logger):
    DEFAULT_LOG_FILE_SIZE = 5 * 1024 * 1024

    def __init__(self, originator, log_file_path, log_file_size=DEFAULT_LOG_FILE_SIZE):
        self.originator = originator
        self.internal_logger = thermoscientific_logging.CircularFileLogWriter(log_file_path, log_file_size)

    def log_event(self, message, severity, category=thermoscientific_logging.Category.DEVELOPER1):
        self.internal_logger.log_event(severity, category, self.originator, message)


class _LoggerCollection:
    def __init__(self):
        self.__loggers = {}
        self.__void_logger = VoidLogger()

    def __getitem__(self, domain: int):
        if domain in self.__loggers.keys():
            return self.__loggers[domain]

        return self.__void_logger

    def register_logger(self, domain: int, logger: Logger):
        if domain in self.__loggers.keys():
            previous_logger = self.__loggers[domain]
            if isinstance(previous_logger, AggregateLogger):
                aggregate_logger = previous_logger
            else:
                aggregate_logger = AggregateLogger()
                aggregate_logger.add_logger(previous_logger)
                self.__loggers[domain] = aggregate_logger

            aggregate_logger.add_logger(logger)

        else:
            self.__loggers[domain] = logger


class Logging:
    DEFAULT_LOG_FILE_LOCATION_SEM_PRODUCT = "c:\\ProgramData\\Thermo Scientific AutoScript\\Log\\Client"
    DEFAULT_LOG_FILE_LOCATION_TEM_PRODUCT = "c:\\ProgramData\\Thermo Scientific AutoScript TEM\\Log\\Client"

    loggers = _LoggerCollection()

    @staticmethod
    def register_logger(domain, logger: Logger):
        Logging.loggers.register_logger(domain, logger)

    @staticmethod
    def initialize_application_client_logging(application_name):
        if platform.system() != "Windows":
            return

        # Quits immediately if application client logging is already established (e.g., when multiple clients are used in a single script)
        is_application_client_logging_established = Logging.__is_logger_registered_for_domain(LogDomain.APPLICATION_CLIENT)
        if is_application_client_logging_established:
            return

        if application_name == "TemMicroscope":
            log_file_location = Logging.DEFAULT_LOG_FILE_LOCATION_TEM_PRODUCT
        else:
            log_file_location = Logging.DEFAULT_LOG_FILE_LOCATION_SEM_PRODUCT

        base_logger = VoidLogger()

        try:
            os.makedirs(log_file_location, exist_ok=True)
        except Exception:
            base_logger.log_error("Cannot ensure existence of log file location: " + log_file_location)

        log_file_helper = LogFileHelper(log_file_location)
        log_file_helper.remove_old_log_files()

        try:
            orc_log_file_path = log_file_helper.generate_log_file_path("ORC")
            orc_infra_logger = InfraLogger("AutoScript.Client.ORC", orc_log_file_path)
            Logging.register_logger(LogDomain.ORC, orc_infra_logger)
            base_logger.log_notification("ORC INFRA log writer was successfully initialized.\r\n\r\nLog file path: " + orc_log_file_path)
        except:
            base_logger.log_error("Cannot initialize ORC INFRA log writer.\r\n\r\nLog file path: " + orc_log_file_path)

        try:
            application_client_log_file_path = log_file_helper.generate_log_file_path()
            application_client_infra_logger = InfraLogger("AutoScript.Client", application_client_log_file_path)
            Logging.register_logger(LogDomain.APPLICATION_CLIENT, application_client_infra_logger)
            base_logger.log_notification("Application client INFRA log writer was successfully initialized.\r\n\r\nLog file path: " + application_client_log_file_path)
        except:
            base_logger.log_error("Cannot initialize application client INFRA log writer.\r\n\r\nLog file path: " + orc_log_file_path)

    @staticmethod
    def __is_logger_registered_for_domain(domain: int):
        """Tells whether an actual logger is registered for the given log domain."""
        is_logger_registered = not isinstance(Logging.loggers[domain], VoidLogger)
        return is_logger_registered


class LogFileHelper:
    """
    LogFileHelper provides set of tools for management of log files.
    """

    TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

    def __init__(self, log_file_location, application_prefix="AutoScript_PythonClient"):
        """
        Initializes helper.

        :param application_prefix: Prefix component referring to the target application.
        """

        self.log_file_location = log_file_location

        timestamp_component = datetime.datetime.now().strftime(self.TIMESTAMP_FORMAT)
        random_component = uuid.uuid4().hex[:8]

        self.application_prefix = application_prefix
        self.log_file_name_prefix = application_prefix + "_" + timestamp_component + "_" + random_component

    def generate_log_file_path(self, suffix=None):
        """
        Generates path for a log file with the given suffix.

        All paths generated by a single LogFileHelper instance will be the same except for the suffix.
        LogFileHelper uses the same prefix for all generated paths so the log files can be easily coupled
        together. The prefix consists of an application prefix component given to LogFileHelper constructor,
        timestamp component and a random component. This generator does not ensure that the generated
        paths are unique or that the log files can actually be created on the paths.

        :param suffix: Suffix to distinguish the path from other paths provided by this generator.
        :return: Returns path for a log file with the given suffix.
        """

        log_file_name = self.log_file_name_prefix
        if suffix:
            log_file_name += "_" + suffix
        log_file_name += ".log"

        log_file_path = os.path.join(self.log_file_location, log_file_name)

        return log_file_path

    def remove_old_log_files(self, age_threshold_in_days=14, max_file_count=50):
        """
        Removes old log files according to the given age threshold and maximum number of files allowed in folder.

        Only log files at location given to LogFileHelper constructor are considered for removal.
        Only log files with name starting with application prefix component given to LogFileHelper
        constructor are considered for removal.

        :param age_threshold_in_days: Threshold to determine which log files should be considered old, in days.
        :param max_file_count: The maximum number of files which is allowed to be in the folder.
        """

        operation_begin = time.perf_counter()
        long_running_operation = False
        log_file_name_pattern = self.application_prefix + "*.log"

        try:
            timestamp_component_position = len(self.application_prefix) + 1  # One character is added for underscore
            timestamp_component_length = len(self.TIMESTAMP_FORMAT)

            log_file_names = [f for f in os.listdir(self.log_file_location) if fnmatch.fnmatch(f, log_file_name_pattern)]
            current_timestamp = datetime.datetime.now()

            for log_file_name in log_file_names:
                try:
                    timestamp_component = log_file_name[timestamp_component_position:(timestamp_component_position + timestamp_component_length)]

                    log_file_timestamp = datetime.datetime.strptime(timestamp_component, self.TIMESTAMP_FORMAT)
                    log_file_age = (current_timestamp - log_file_timestamp)

                    if log_file_age.days > age_threshold_in_days:
                        os.remove(os.path.join(self.log_file_location, log_file_name))
                except:
                    # Silently skips the current file if any error occurs during its processing.
                    pass

                    long_running_operation = LogFileHelper.update_and_report_long_running_operation(long_running_operation, operation_begin)

            # Check if there is still more then max_file_count files, if it is, remove the extra files
            log_file_names = [f for f in os.listdir(self.log_file_location) if fnmatch.fnmatch(f, log_file_name_pattern)]

            if len(log_file_names) > max_file_count:
                log_file_names.sort()  # Just to be sure the old ones are at the beginning of the list
                log_file_names = log_file_names[:len(log_file_names)-max_file_count]  # Take just the files to be removed

                for log_file_name in log_file_names:
                    try:
                        os.remove(os.path.join(self.log_file_location, log_file_name))
                        pass
                    except:
                        # Silently ignore the file deletion, because it is probably used by other script
                        pass

                    long_running_operation = LogFileHelper.update_and_report_long_running_operation(long_running_operation, operation_begin)

        except:
            # Silently skips the rest of the operation if any error occurs.
            pass

        if long_running_operation:
            print("Cleanup operation finished")

    @staticmethod
    def update_and_report_long_running_operation(long_running_operation, operation_begin):

        if not long_running_operation:
            operation_duration = time.perf_counter() - operation_begin
            if operation_duration > 1.0:
                print("Cleanup operation in progress, please wait...")
                long_running_operation = True

        return long_running_operation
