# --------------------------------------------------------------------------------------------------
# <auto-generated>
#     This code was generated by a tool.
#     Changes to this file may cause incorrect behavior and will be lost if the code is regenerated.
#     Template ID: 52
# </auto-generated>
# --------------------------------------------------------------------------------------------------

from typing import List, Union
from autoscript_sdb_microscope_client.structures import RunAutoSourceTiltSettings, RunAutoCbSettings, RunAutoFocusSettings, RunAutoLensAlignmentSettings, RunAutoStigmatorCenteringSettings, RunAutoStigmatorSettings 
from autoscript_sdb_microscope_client._sdb_microscope_client_extensions import SdbMicroscopeClientExtensions
from autoscript_core.common import CallRequest, DataType, DataTypeDefinition


class AutoFunctions(object):
    """
    The object provides control of the microscope auto functions.
    """
    __slots__ = ["__id", "__application_client"]

    def __init__(self, application_client):
        self.__application_client = application_client
        self.__id = "SdbMicroscope.AutoFunctions"


    def run_auto_source_tilt(self, settings: 'RunAutoSourceTiltSettings' = None):
        """
        Runs a routine that automatically adjusts the source tilt in the active view.
        
        :param settings: Settings for the automatic source tilt adjustment routine.
        """
        call_request = CallRequest(object_id=self.__id, method_name="RunAutoSourceTilt", signature=[], parameters=[])
        if isinstance(settings, RunAutoSourceTiltSettings):
            call_request.parameters.data_types = [DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, secondary_id="RunAutoSourceTiltSettings")]
            call_request.parameters.values = [settings]
            call_response = self.__application_client._perform_call(call_request)
        elif settings is None:
            call_request.parameters.data_types = []
            call_request.parameters.values = []
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")


    def run_auto_cb(self, settings: 'RunAutoCbSettings' = None):
        """
        Runs a routine that automatically optimizes contrast and brightness of the active detector in the active view.
        
        :param settings: Settings for the automatic brightness and contrast adjustment routine.
        """
        call_request = CallRequest(object_id=self.__id, method_name="RunAutoCb", signature=[], parameters=[])
        if isinstance(settings, RunAutoCbSettings):
            call_request.parameters.data_types = [DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, secondary_id="RunAutoCbSettings")]
            call_request.parameters.values = [settings]
            call_response = self.__application_client._perform_call(call_request)
        elif settings is None:
            call_request.parameters.data_types = []
            call_request.parameters.values = []
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")


    def run_auto_focus(self, settings: 'RunAutoFocusSettings' = None):
        """
        Runs the automatic focus routine in the active view.
        
        :param settings: Settings for the automatic focus routine.
        """
        call_request = CallRequest(object_id=self.__id, method_name="RunAutoFocus", signature=[], parameters=[])
        if isinstance(settings, RunAutoFocusSettings):
            call_request.parameters.data_types = [DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, secondary_id="RunAutoFocusSettings")]
            call_request.parameters.values = [settings]
            call_response = self.__application_client._perform_call(call_request)
        elif settings is None:
            call_request.parameters.data_types = []
            call_request.parameters.values = []
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")


    def run_auto_lens_alignment(self, settings: 'RunAutoLensAlignmentSettings' = None):
        """
        Runs a routine that automatically adjusts the lens alignment in the active view.
        
        :param settings: Settings for the automatic lens alignment adjustment routine.
        """
        call_request = CallRequest(object_id=self.__id, method_name="RunAutoLensAlignment", signature=[], parameters=[])
        if isinstance(settings, RunAutoLensAlignmentSettings):
            call_request.parameters.data_types = [DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, secondary_id="RunAutoLensAlignmentSettings")]
            call_request.parameters.values = [settings]
            call_response = self.__application_client._perform_call(call_request)
        elif settings is None:
            call_request.parameters.data_types = []
            call_request.parameters.values = []
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")


    def run_auto_stigmator_centering(self, settings: 'RunAutoStigmatorCenteringSettings' = None):
        """
        Runs a routine that automatically optimizes stigmator centering in the active view.
        
        :param settings: Settings for the automatic stigmator centering adjustment routine.
        """
        call_request = CallRequest(object_id=self.__id, method_name="RunAutoStigmatorCentering", signature=[], parameters=[])
        if isinstance(settings, RunAutoStigmatorCenteringSettings):
            call_request.parameters.data_types = [DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, secondary_id="RunAutoStigmatorCenteringSettings")]
            call_request.parameters.values = [settings]
            call_response = self.__application_client._perform_call(call_request)
        elif settings is None:
            call_request.parameters.data_types = []
            call_request.parameters.values = []
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")


    def run_auto_stigmator(self, settings: 'RunAutoStigmatorSettings' = None):
        """
        Runs a routine that automatically optimizes stigmator in the active view.
        
        :param settings: Settings for the automatic stigmator adjustment routine.
        """
        call_request = CallRequest(object_id=self.__id, method_name="RunAutoStigmator", signature=[], parameters=[])
        if isinstance(settings, RunAutoStigmatorSettings):
            call_request.parameters.data_types = [DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, secondary_id="RunAutoStigmatorSettings")]
            call_request.parameters.values = [settings]
            call_response = self.__application_client._perform_call(call_request)
        elif settings is None:
            call_request.parameters.data_types = []
            call_request.parameters.values = []
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")
