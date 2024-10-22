# --------------------------------------------------------------------------------------------------
# <auto-generated>
#     This code was generated by a tool.
#     Changes to this file may cause incorrect behavior and will be lost if the code is regenerated.
#     Template ID: 52
# </auto-generated>
# --------------------------------------------------------------------------------------------------

from typing import List, Union
from autoscript_sdb_microscope_client.structures import GetRtmPositionSettings, RtmPositionSet, GetRtmDataSettings, RtmDataSet 
from autoscript_sdb_microscope_client._sdb_microscope_client_extensions import SdbMicroscopeClientExtensions
from autoscript_core.common import CallRequest, DataType, DataTypeDefinition


class RealTimeMonitor(object):
    """
    The object provides control and status of the real time monitor (RTM).
    """
    __slots__ = ["__id", "__application_client"]

    def __init__(self, application_client):
        self.__application_client = application_client
        self.__id = "SdbMicroscope.Patterning.RealTimeMonitor"


    def start(self):
        """
        The function starts the real time monitoring process.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Start", signature= [], parameters=[]) 
        call_response = self.__application_client._perform_call(call_request)

    def stop(self):
        """
        The function stops the real time monitoring process.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Stop", signature= [], parameters=[]) 
        call_response = self.__application_client._perform_call(call_request)

    def restart(self):
        """
        The function restarts the real time monitoring process.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Restart", signature= [], parameters=[]) 
        call_response = self.__application_client._perform_call(call_request)

    def get_positions(self, settings: 'GetRtmPositionSettings' = None) -> 'List[RtmPositionSet]':
        """
        The function retrieves pattern point positions.
        
        :param settings: The settings structure.
        
        :return: The list of patterns with the appropriate pattern point positions.
        """
        call_request = CallRequest(object_id=self.__id, method_name="GetPositions", signature=[], parameters=[])
        if settings is None:
            call_request.parameters.data_types = []
            call_request.parameters.values = []
            call_response = self.__application_client._perform_call(call_request)
        elif isinstance(settings, GetRtmPositionSettings):
            call_request.parameters.data_types = [DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, secondary_id="GetRtmPositionSettings")]
            call_request.parameters.values = [settings]
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")

        if call_response.result.data_type != DataTypeDefinition(DataType.LIST_PRIMARY_ID, template_argument=DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, secondary_id="RtmPositionSet")):
            raise TypeError("Incompatible type: real_time_monitor.get_positions was expecting list, but server returned different object type: " + repr(call_response.result.data_type))

        return call_response.result.value

    def get_data(self, settings: 'GetRtmDataSettings' = None) -> 'List[RtmDataSet]':
        """
        The function retrieves pattern points grey scale values.
        
        :param settings: The settings where pattern IDs and other options can be specified.
        
        :return: The list of patterns with the appropriate pattern point grey scale values.
        """
        call_request = CallRequest(object_id=self.__id, method_name="GetData", signature=[], parameters=[])
        if settings is None:
            call_request.parameters.data_types = []
            call_request.parameters.values = []
            call_response = self.__application_client._perform_call(call_request)
        elif isinstance(settings, GetRtmDataSettings):
            call_request.parameters.data_types = [DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, secondary_id="GetRtmDataSettings")]
            call_request.parameters.values = [settings]
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")

        if call_response.result.data_type != DataTypeDefinition(DataType.LIST_PRIMARY_ID, template_argument=DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, secondary_id="RtmDataSet")):
            raise TypeError("Incompatible type: real_time_monitor.get_data was expecting list, but server returned different object type: " + repr(call_response.result.data_type))

        return call_response.result.value

    @property
    def mode(self) -> 'int':
        """
        Gets or sets the active RTM resolution mode. Maps to RtmMode enumeration.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Mode_GET")
        call_response = self.__application_client._perform_call(call_request)
        if call_response.result.data_type != DataType.INT32:
            raise TypeError("Incompatible type: real_time_monitor.mode was expecting int, but server returned different object type: " + repr(call_response.result.data_type))

        return call_response.result.value

    @mode.setter
    def mode(self, value: 'int'):
        """
        Gets or sets the active RTM resolution mode. Maps to RtmMode enumeration.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Mode_SET", signature=[DataType.INT32], parameters=[value])
        if isinstance(value, int):
            self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")
