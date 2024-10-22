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
from .electron_beam._high_voltage import HighVoltage
from .electron_beam._beam_shift import BeamShift
from .electron_beam._horizontal_field_width import HorizontalFieldWidth
from .electron_beam._stigmator import Stigmator
from .electron_beam._scanning import Scanning
from .electron_beam._working_distance import WorkingDistance
from .electron_beam._source import Source
from .electron_beam._beam_current import BeamCurrent
from .electron_beam._optical_mode import OpticalMode
from .electron_beam._source_tilt import SourceTilt
from .electron_beam._lens_alignment import LensAlignment
from .electron_beam._beam_deceleration import BeamDeceleration
from .electron_beam._angular_correction import AngularCorrection
from .electron_beam._emission_current import EmissionCurrent
from .electron_beam._crossover_zoom import CrossoverZoom


class ElectronBeam(object):
    """
    The object provides control and status of the electron beam.
    """
    __slots__ = ["__id", "__application_client", "__high_voltage", "__beam_shift", "__horizontal_field_width", "__stigmator", "__scanning", "__working_distance", "__source", "__beam_current", "__optical_mode", "__source_tilt", "__lens_alignment", "__beam_deceleration", "__angular_correction", "__emission_current", "__crossover_zoom"]

    def __init__(self, application_client):
        self.__application_client = application_client
        self.__id = "SdbMicroscope.Beams.ElectronBeam"

        self.__high_voltage = HighVoltage(self.__application_client)
        self.__beam_shift = BeamShift(self.__application_client)
        self.__horizontal_field_width = HorizontalFieldWidth(self.__application_client)
        self.__stigmator = Stigmator(self.__application_client)
        self.__scanning = Scanning(self.__application_client)
        self.__working_distance = WorkingDistance(self.__application_client)
        self.__source = Source(self.__application_client)
        self.__beam_current = BeamCurrent(self.__application_client)
        self.__optical_mode = OpticalMode(self.__application_client)
        self.__source_tilt = SourceTilt(self.__application_client)
        self.__lens_alignment = LensAlignment(self.__application_client)
        self.__beam_deceleration = BeamDeceleration(self.__application_client)
        self.__angular_correction = AngularCorrection(self.__application_client)
        self.__emission_current = EmissionCurrent(self.__application_client)
        self.__crossover_zoom = CrossoverZoom(self.__application_client)

    @property
    def high_voltage(self) -> 'HighVoltage':
        """
        The object provides control and status of the high tension voltage.
        """
        return self.__high_voltage

    @property
    def beam_shift(self) -> 'BeamShift':
        """
        The object provides control and status of beam shift.
        """
        return self.__beam_shift

    @property
    def horizontal_field_width(self) -> 'HorizontalFieldWidth':
        """
        The object provides control and status of the horizontal field width.
        """
        return self.__horizontal_field_width

    @property
    def stigmator(self) -> 'Stigmator':
        """
        The object provides control and status of stigmator. It can be used to correct image astigmatism.
        """
        return self.__stigmator

    @property
    def scanning(self) -> 'Scanning':
        """
        The object scanning provides control and status of the scanning properties of the beam.
        """
        return self.__scanning

    @property
    def working_distance(self) -> 'WorkingDistance':
        """
        The object provides control and status of the working distance.
        """
        return self.__working_distance

    @property
    def source(self) -> 'Source':
        """
        The object provides control and status of the electron beam source.
        """
        return self.__source

    @property
    def beam_current(self) -> 'BeamCurrent':
        """
        The object provides control and status of the electron beam current.
        """
        return self.__beam_current

    @property
    def optical_mode(self) -> 'OpticalMode':
        """
        The object provides control and status of the electron beam optical mode.
        """
        return self.__optical_mode

    @property
    def source_tilt(self) -> 'SourceTilt':
        """
        The object provides control and status of the electron beam source tilt.
        """
        return self.__source_tilt

    @property
    def lens_alignment(self) -> 'LensAlignment':
        """
        The object provides control and status of the electron beam lens alignment.
        """
        return self.__lens_alignment

    @property
    def beam_deceleration(self) -> 'BeamDeceleration':
        """
        The object provides control and status of the electron beam deceleration.
        """
        return self.__beam_deceleration

    @property
    def angular_correction(self) -> 'AngularCorrection':
        """
        The object provides control and status of the angular correction.
        """
        return self.__angular_correction

    @property
    def emission_current(self) -> 'EmissionCurrent':
        """
        The object provides control and status of the electron beam emission current.
        """
        return self.__emission_current

    @property
    def crossover_zoom(self) -> 'CrossoverZoom':
        """
        The object provides control and status of the crossover zoom parameter on the electron beam.
        """
        return self.__crossover_zoom

    def turn_on(self):
        """
        The method turns the beam on.
        """
        call_request = CallRequest(object_id=self.__id, method_name="TurnOn", signature= [], parameters=[]) 
        call_response = self.__application_client._perform_call(call_request)

    def turn_off(self):
        """
        The method turns the beam off.
        """
        call_request = CallRequest(object_id=self.__id, method_name="TurnOff", signature= [], parameters=[]) 
        call_response = self.__application_client._perform_call(call_request)

    def blank(self):
        """
        Blanks the beam.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Blank", signature= [], parameters=[]) 
        call_response = self.__application_client._perform_call(call_request)

    def unblank(self):
        """
        Unblanks the beam.
        """
        call_request = CallRequest(object_id=self.__id, method_name="Unblank", signature= [], parameters=[]) 
        call_response = self.__application_client._perform_call(call_request)

    @property
    def is_on(self) -> 'bool':
        """
        Retrieves current state of the beam.
        """
        call_request = CallRequest(object_id=self.__id, method_name="IsOn_GET")
        call_response = self.__application_client._perform_call(call_request)
        if call_response.result.data_type != DataType.BOOL:
            raise TypeError("Incompatible type: electron_beam.is_on was expecting bool, but server returned different object type: " + repr(call_response.result.data_type))

        return call_response.result.value

    @property
    def is_blanked(self) -> 'bool':
        """
        Gets the current blank state of the beam.
        """
        call_request = CallRequest(object_id=self.__id, method_name="IsBlanked_GET")
        call_response = self.__application_client._perform_call(call_request)
        if call_response.result.data_type != DataType.BOOL:
            raise TypeError("Incompatible type: electron_beam.is_blanked was expecting bool, but server returned different object type: " + repr(call_response.result.data_type))

        return call_response.result.value
