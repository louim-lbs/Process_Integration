# --------------------------------------------------------------------------------------------------
# <auto-generated>
#     This code was generated by a tool.
#     Changes to this file may cause incorrect behavior and will be lost if the code is regenerated.
#     Template ID: 52
# </auto-generated>
# --------------------------------------------------------------------------------------------------

from typing import List, Union
from autoscript_sdb_microscope_client._sdb_microscope_client_extensions import SdbMicroscopeClientExtensions
from autoscript_core.common import CallRequest, DataType, DataTypeDefinition


class Resolution(object):
    """
    The object provides control and status of scanning resolution.
    """
    __slots__ = ["__id", "__application_client"]

    def __init__(self, application_client):
        self.__application_client = application_client
        self.__id = "SdbMicroscope.Beams.ElectronBeam.Scanning.Resolution"


    @property
    def available_values(self) -> 'List[str]':
        """
        The list of valid resolutions.
        """
        call_request = CallRequest(object_id=self.__id, method_name="AvailableValues_GET")
        call_response = self.__application_client._perform_call(call_request)
        if call_response.result.data_type != DataTypeDefinition(DataType.LIST_PRIMARY_ID, template_argument=DataType.STRING):
            raise TypeError("Incompatible type: resolution.available_values was expecting list, but server returned different object type: " + repr(call_response.result.data_type))

        return call_response.result.value

    @property
    def value(self) -> 'str':
        """
        Gets or sets the scanning resolution for the image acquisition.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Value_GET")
        call_response = self.__application_client._perform_call(call_request)
        if call_response.result.data_type != DataType.STRING:
            raise TypeError("Incompatible type: resolution.value was expecting str, but server returned different object type: " + repr(call_response.result.data_type))

        return call_response.result.value

    @value.setter
    def value(self, value: 'str'):
        """
        Gets or sets the scanning resolution for the image acquisition.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Value_SET", signature=[DataType.STRING], parameters=[value])
        if isinstance(value, str):
            self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")
