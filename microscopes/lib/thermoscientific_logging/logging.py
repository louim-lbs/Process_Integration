import os
import ctypes


class Severity:
    INFORMATIONAL = 0x00000001
    WARNING = 0x00000002
    ERROR = 0x00000004
    FATAL_ERROR = 0x00000008


class Category:
    STATE_CHANGE = 0x00000001
    NOTIFICATION = 0x00000020
    INTERNAL_ERROR = 0x00001000
    DEVELOPER1 = 0x01000000


class CircularFileLogWriter:
    def __init__(self, log_file_path, log_file_size):
        self.__fei_logging_library = None
        self.__log_file = None

        try:
            self.__fei_logging_library = ctypes.cdll.LoadLibrary(os.path.dirname(__file__) + '\\FeiLogging.dll')
            self.__log_file = self.__open_log_file(log_file_path, log_file_size)

        except Exception as ex:
            raise Exception("Cannot initialize log writer.") from ex

    def __del__(self):
        self.__close_log_file()

    def log_event(self, severity, category, originator, message):
        self.__fei_logging_library.CFLW_Compat_Write(self.__log_file, severity, category, originator, message)

    def __open_log_file(self, path, size):
        self.__fei_logging_library.CFLW_Compat_Open.restype = ctypes.c_void_p
        log_file = ctypes.c_void_p(self.__fei_logging_library.CFLW_Compat_Open(path, size))
        return log_file

    def __close_log_file(self):
        if self.__log_file:
            self.__fei_logging_library.CFLW_Compat_Close(self.__log_file)
