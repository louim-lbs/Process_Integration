# --------------------------------------------------------------------------------------------------
# <auto-generated>
#     This code was generated by a tool.
#     Changes to this file may cause incorrect behavior and will be lost if the code is regenerated.
#     Template ID: 52
# </auto-generated>
# --------------------------------------------------------------------------------------------------

from typing import List, Union
from autoscript_sdb_microscope_client.structures import StreamPatternDefinition, BitmapPatternDefinition 
from autoscript_sdb_microscope_client._sdb_microscope_client_extensions import SdbMicroscopeClientExtensions
from autoscript_core.common import CallRequest, DataType, DataTypeDefinition, UndefinedParameter
from .patterning._real_time_monitor import RealTimeMonitor
from autoscript_sdb_microscope_client._dynamic_object_proxies import RectanglePattern, LinePattern, CirclePattern, CleaningCrossSectionPattern, RegularCrossSectionPattern, StreamPattern, BitmapPattern 
from autoscript_sdb_microscope_client._dynamic_object_handles import RectanglePatternHandle, LinePatternHandle, CirclePatternHandle, CleaningCrossSectionPatternHandle, RegularCrossSectionPatternHandle, StreamPatternHandle, BitmapPatternHandle 


class Patterning(object):    
    """
    The object provides control and status of the microscope's patterning engine.
    """
    __slots__ = ["__id", "__application_client", "__real_time_monitor"]

    def __init__(self, application_client):
        self.__application_client = application_client
        self.__id = "SdbMicroscope.Patterning"

        self.__real_time_monitor = RealTimeMonitor(self.__application_client)

    @property
    def real_time_monitor(self) -> 'RealTimeMonitor':        
        """
        The object provides control and status of the real time monitor.
        """
        return self.__real_time_monitor

    def set_default_beam_type(self, beam_index):        
        """
        The method sets the default beam type to be used when creating new patterns.
        
        :param int beam_index: Beam type to be used by default when creating new patterns. Use the BeamType enumeration to specify the proper beam index.
        """
        call_request = CallRequest(object_id=self.__id, method_name="SetDefaultBeamType", signature= [DataType.INT32], parameters=[beam_index]) 
        if isinstance(beam_index, int):
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")

    def set_default_application_file(self, application_file):        
        """
        The method sets the default application file to be used when creating new patterns.
        
        :param str application_file: Name of the application file.
        """
        call_request = CallRequest(object_id=self.__id, method_name="SetDefaultApplicationFile", signature= [DataType.STRING], parameters=[application_file]) 
        if isinstance(application_file, str):
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")

    def create_rectangle(self, center_x, center_y, width, height, depth) -> 'RectanglePattern':        
        """
        The method creates a new rectangular pattern.
        
        :param float center_x: X coordinate of the pattern center position.
        
        :param float center_y: Y coordinate of the pattern center position.
        
        :param float width: The pattern width.
        
        :param float height: The pattern height.
        
        :param float depth: Depth of the pattern.
        
        :return: The new rectangular pattern.
        :rtype: RectanglePattern
        """
        call_request = CallRequest(object_id=self.__id, method_name="CreateRectangle", signature= [DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE], parameters=[center_x, center_y, width, height, depth]) 
        if isinstance(center_x, (int, float)) and isinstance(center_y, (int, float)) and isinstance(width, (int, float)) and isinstance(height, (int, float)) and isinstance(depth, (int, float)):
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")
        if call_response.result.data_type != DataTypeDefinition(DataType.DYNAMIC_OBJECT_HANDLE_PRIMARY_ID, "RectanglePattern"):
            raise TypeError("Incompatible type: patterning.create_rectangle was expecting RectanglePattern, but server returned different object type: " + repr(call_response.result.data_type))

        handle = call_response.result.value
        return RectanglePattern(self.__application_client, handle)

    def create_line(self, start_x, start_y, end_x, end_y, depth) -> 'LinePattern':        
        """
        The method creates a new line pattern.
        
        :param float start_x: X coordinate of the pattern start position.
        
        :param float start_y: Y coordinate of the pattern start position.
        
        :param float end_x: X coordinate of the pattern end position.
        
        :param float end_y: Y coordinate of the pattern end position.
        
        :param float depth: Depth of the pattern.
        
        :return: The new line pattern.
        :rtype: LinePattern
        """
        call_request = CallRequest(object_id=self.__id, method_name="CreateLine", signature= [DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE], parameters=[start_x, start_y, end_x, end_y, depth]) 
        if isinstance(start_x, (int, float)) and isinstance(start_y, (int, float)) and isinstance(end_x, (int, float)) and isinstance(end_y, (int, float)) and isinstance(depth, (int, float)):
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")
        if call_response.result.data_type != DataTypeDefinition(DataType.DYNAMIC_OBJECT_HANDLE_PRIMARY_ID, "LinePattern"):
            raise TypeError("Incompatible type: patterning.create_line was expecting LinePattern, but server returned different object type: " + repr(call_response.result.data_type))

        handle = call_response.result.value
        return LinePattern(self.__application_client, handle)

    def create_circle(self, center_x, center_y, outer_diameter, inner_diameter, depth) -> 'CirclePattern':        
        """
        The method creates a new circular pattern.
        
        :param float center_x: X coordinate of the pattern center position.
        
        :param float center_y: Y coordinate of the pattern center position.
        
        :param float outer_diameter: Diameter of the circle.
        
        :param float inner_diameter: Diameter of the inner circle.
        
        :param float depth: Depth of the pattern.
        
        :return: The new circular pattern.
        :rtype: CirclePattern
        """
        call_request = CallRequest(object_id=self.__id, method_name="CreateCircle", signature= [DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE], parameters=[center_x, center_y, outer_diameter, inner_diameter, depth]) 
        if isinstance(center_x, (int, float)) and isinstance(center_y, (int, float)) and isinstance(outer_diameter, (int, float)) and isinstance(inner_diameter, (int, float)) and isinstance(depth, (int, float)):
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")
        if call_response.result.data_type != DataTypeDefinition(DataType.DYNAMIC_OBJECT_HANDLE_PRIMARY_ID, "CirclePattern"):
            raise TypeError("Incompatible type: patterning.create_circle was expecting CirclePattern, but server returned different object type: " + repr(call_response.result.data_type))

        handle = call_response.result.value
        return CirclePattern(self.__application_client, handle)

    def create_cleaning_cross_section(self, center_x, center_y, width, height, depth) -> 'CleaningCrossSectionPattern':        
        """
        The method creates a new cleaning cross section pattern.
        
        :param float center_x: X coordinate of the pattern center position.
        
        :param float center_y: Y coordinate of the pattern center position.
        
        :param float width: The pattern width.
        
        :param float height: The pattern height.
        
        :param float depth: Depth of the pattern.
        
        :return: The new cleaning cross section pattern.
        :rtype: CleaningCrossSectionPattern
        """
        call_request = CallRequest(object_id=self.__id, method_name="CreateCleaningCrossSection", signature= [DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE], parameters=[center_x, center_y, width, height, depth]) 
        if isinstance(center_x, (int, float)) and isinstance(center_y, (int, float)) and isinstance(width, (int, float)) and isinstance(height, (int, float)) and isinstance(depth, (int, float)):
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")
        if call_response.result.data_type != DataTypeDefinition(DataType.DYNAMIC_OBJECT_HANDLE_PRIMARY_ID, "CleaningCrossSectionPattern"):
            raise TypeError("Incompatible type: patterning.create_cleaning_cross_section was expecting CleaningCrossSectionPattern, but server returned different object type: " + repr(call_response.result.data_type))

        handle = call_response.result.value
        return CleaningCrossSectionPattern(self.__application_client, handle)

    def create_regular_cross_section(self, center_x, center_y, width, height, depth) -> 'RegularCrossSectionPattern':        
        """
        The method creates a new regular cross section pattern.
        
        :param float center_x: X coordinate of the pattern center position.
        
        :param float center_y: Y coordinate of the pattern center position.
        
        :param float width: The pattern width.
        
        :param float height: The pattern height.
        
        :param float depth: Depth of the pattern.
        
        :return: The new regular cross section pattern.
        :rtype: RegularCrossSectionPattern
        """
        call_request = CallRequest(object_id=self.__id, method_name="CreateRegularCrossSection", signature= [DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE], parameters=[center_x, center_y, width, height, depth]) 
        if isinstance(center_x, (int, float)) and isinstance(center_y, (int, float)) and isinstance(width, (int, float)) and isinstance(height, (int, float)) and isinstance(depth, (int, float)):
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")
        if call_response.result.data_type != DataTypeDefinition(DataType.DYNAMIC_OBJECT_HANDLE_PRIMARY_ID, "RegularCrossSectionPattern"):
            raise TypeError("Incompatible type: patterning.create_regular_cross_section was expecting RegularCrossSectionPattern, but server returned different object type: " + repr(call_response.result.data_type))

        handle = call_response.result.value
        return RegularCrossSectionPattern(self.__application_client, handle)

    def create_stream(self, center_x, center_y, stream_pattern_definition) -> 'StreamPattern':        
        """
        The method creates the stream file pattern.
        
        :param float center_x: X coordinate of the pattern center position.
        
        :param float center_y: Y coordinate of the pattern center position.
        
        :param StreamPatternDefinition stream_pattern_definition: The stream pattern definition.
        
        :return: The new stream file pattern.
        :rtype: StreamPattern
        """
        call_request = CallRequest(object_id=self.__id, method_name="CreateStream", signature= [DataType.DOUBLE, DataType.DOUBLE, DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, secondary_id="StreamPatternDefinition")], parameters=[center_x, center_y, stream_pattern_definition]) 
        if isinstance(center_x, (int, float)) and isinstance(center_y, (int, float)) and isinstance(stream_pattern_definition, StreamPatternDefinition):
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")
        if call_response.result.data_type != DataTypeDefinition(DataType.DYNAMIC_OBJECT_HANDLE_PRIMARY_ID, "StreamPattern"):
            raise TypeError("Incompatible type: patterning.create_stream was expecting StreamPattern, but server returned different object type: " + repr(call_response.result.data_type))

        handle = call_response.result.value
        return StreamPattern(self.__application_client, handle)

    def create_bitmap(self, center_x, center_y, width, height, depth, bitmap_pattern_definition) -> 'BitmapPattern':        
        """
        The method creates the bitmap pattern.
        
        :param float center_x: X coordinate of the pattern center position.
        
        :param float center_y: Y coordinate of the pattern center position.
        
        :param float width: The pattern width.
        
        :param float height: The pattern height.
        
        :param float depth: Depth of the pattern.
        
        :param BitmapPatternDefinition bitmap_pattern_definition: The bitmap pattern definition.
        
        :return: The new bitmap pattern.
        :rtype: BitmapPattern
        """
        call_request = CallRequest(object_id=self.__id, method_name="CreateBitmap", signature= [DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE, DataType.DOUBLE, DataTypeDefinition(DataType.STRUCTURE_PRIMARY_ID, secondary_id="BitmapPatternDefinition")], parameters=[center_x, center_y, width, height, depth, bitmap_pattern_definition]) 
        if isinstance(center_x, (int, float)) and isinstance(center_y, (int, float)) and isinstance(width, (int, float)) and isinstance(height, (int, float)) and isinstance(depth, (int, float)) and isinstance(bitmap_pattern_definition, BitmapPatternDefinition):
            call_response = self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")
        if call_response.result.data_type != DataTypeDefinition(DataType.DYNAMIC_OBJECT_HANDLE_PRIMARY_ID, "BitmapPattern"):
            raise TypeError("Incompatible type: patterning.create_bitmap was expecting BitmapPattern, but server returned different object type: " + repr(call_response.result.data_type))

        handle = call_response.result.value
        return BitmapPattern(self.__application_client, handle)

    def clear_patterns(self):        
        """
        The method deletes all the existing patterns in the current view.
        """
        call_request = CallRequest(object_id=self.__id, method_name="ClearPatterns", signature= [], parameters=[]) 
        call_response = self.__application_client._perform_call(call_request)

    def list_all_application_files(self) -> 'List[str]':        
        """
        The method returns all application files available on the system.
        
        :return: The list of all application files available on the system.
        :rtype: list
        """
        call_request = CallRequest(object_id=self.__id, method_name="ListAllApplicationFiles", signature= [], parameters=[]) 
        call_response = self.__application_client._perform_call(call_request)
        if call_response.result.data_type != DataTypeDefinition(DataType.LIST_PRIMARY_ID, template_argument=DataType.STRING):
            raise TypeError("Incompatible type: patterning.list_all_application_files was expecting list, but server returned different object type: " + repr(call_response.result.data_type))

        return call_response.result.value

    def run(self):        
        """
        The method runs patterning job synchronously (waits for the patterning end).
        """
        call_request = CallRequest(object_id=self.__id, method_name="Run", signature= [], parameters=[]) 
        call_response = self.__application_client._perform_call(call_request)

    def resume(self):        
        """
        The method resumes paused patterning job.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Resume", signature= [], parameters=[]) 
        call_response = self.__application_client._perform_call(call_request)

    def start(self):        
        """
        The method starts the patterning asynchronously.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Start", signature= [], parameters=[]) 
        call_response = self.__application_client._perform_call(call_request)

    def stop(self):        
        """
        The method aborts running patterning job.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Stop", signature= [], parameters=[]) 
        call_response = self.__application_client._perform_call(call_request)

    def pause(self):        
        """
        The method pauses running patterning job.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Pause", signature= [], parameters=[]) 
        call_response = self.__application_client._perform_call(call_request)

    @property
    def mode(self) -> 'str':        
        """
        Gets and sets the active patterning mode.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Mode_GET")
        call_response = self.__application_client._perform_call(call_request)
        if call_response.result.data_type != DataType.STRING:
            raise TypeError("Incompatible type: patterning.mode was expecting str, but server returned different object type: " + repr(call_response.result.data_type))

        return call_response.result.value

    @mode.setter
    def mode(self, value):        
        """
        Gets and sets the active patterning mode.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Mode_SET", signature=[DataType.STRING], parameters=[value])
        if isinstance(value, str):
            self.__application_client._perform_call(call_request)
        else:
            raise Exception("Cannot execute method with the given parameters combination. Read the documentation for details of how to call this method.")

    @property
    def state(self) -> 'str':        
        """
        Gets the current state of the patterning engine.
        """
        call_request = CallRequest(object_id=self.__id, method_name="State_GET")
        call_response = self.__application_client._perform_call(call_request)
        if call_response.result.data_type != DataType.STRING:
            raise TypeError("Incompatible type: patterning.state was expecting str, but server returned different object type: " + repr(call_response.result.data_type))

        return call_response.result.value