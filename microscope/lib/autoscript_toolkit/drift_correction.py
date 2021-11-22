"""
AutoScript toolkit component providing drift correction mechanisms.
"""

from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.enumerations import *
from autoscript_sdb_microscope_client.structures import *
from autoscript_core.common import ApplicationServerException
from .vision import cut_image, locate_feature
from .template_matchers import *
import time


class DcPatterningEngine:
    """
    DcPatterningEngine is an engine able to run a patterning job while performing drift correction.
    """

    def __init__(self, microscope: SdbMicroscopeClient, template_matcher=DEFAULT_TEMPLATE_MATCHER):
        """
        Creates and initializes a new DC patterning engine.

        :param microscope: Microscope to be used for patterning control.
        :param template_matcher: Template matcher to be used for fiducial search.
        """
        self.microscope = microscope
        self.fiducial_image = None
        self.fiducial_center = None
        self.template_matcher = template_matcher

    def define_fiducial(self, image, center, size):
        """
        Defines fiducial according to the given center point and size.

        The fiducial coordinates are expected in meters, using the same coordinate system as patterns.
        The given image is used to create fiducial template for search during patterning job.

        :param image: Image to be used for fiducial definition.
        :param center: Center point of the fiducial, in meters.
        :param size: Size of the fiducial, in meters.
        """

        hfw = image.metadata.optics.scan_field_of_view.width
        vfw = image.metadata.optics.scan_field_of_view.height

        relative_fiducial_center = (((center[0] + (hfw / 2)) / hfw), (((center[1] - (vfw / 2)) * -1) / vfw))
        relative_fiducial_size = size / hfw

        fiducial_center_in_pixels = (round(relative_fiducial_center[0] * image.width), round(relative_fiducial_center[1] * image.height))
        fiducial_size_in_pixels = self.__make_multiple2(relative_fiducial_size * image.width)

        self.__check_fiducial_boundaries(image, fiducial_center_in_pixels, fiducial_size_in_pixels)

        cut = cut_image(image.data, center=fiducial_center_in_pixels, size=[fiducial_size_in_pixels, fiducial_size_in_pixels])

        self.fiducial_image = AdornedImage(cut)
        self.fiducial_center = fiducial_center_in_pixels

    def run(self, correction_interval):
        """
        Starts a new patterning job and waits for its completion, performing drift correction while the job is running.

        Prior to calling this method, fiducial has to be defined using define_fiducial() method.

        :param correction_interval: Interval in which the engine should attempt drift correction, in seconds.
        """

        # Quit immediately if no fiducial was defined for this engine so far
        if self.fiducial_image is None or self.fiducial_center is None:
            raise Exception("Drift corrected patterning can not run because no fiducial was defined. Defined it using define_fiducial() method.")

        # Try to start a new patterning job
        try:
            self.microscope.patterning.start()
        except ApplicationServerException:
            raise Exception("Unable to start a new patterning job.")

        while True:
            # Wait until the patterning job ends or until the next drift correction interval passes by
            if self.__wait_for_patterning_end(correction_interval):
                break

            # Pause the patterning job
            try:
                self.microscope.patterning.pause()
            except ApplicationServerException:
                raise Exception("Unable to pause patterning job to perform drift correction.")

            # Acquire a new snapshot
            current_snapshot = self.microscope.imaging.grab_frame()

            # Locate the fiducial in the snapshot
            template_location = locate_feature(current_snapshot, self.fiducial_image, template_matcher=self.template_matcher, original_feature_center=self.fiducial_center)

            # Try to correct for the measured drift using beam shift
            try:
                self.microscope.beams.ion_beam.beam_shift.value += template_location.shift_in_meters
            except ApplicationServerException:
                self.microscope.patterning.stop()
                raise Exception("Unable to perform drift correction. Drift corrected patterning was stopped.")

            # Resume the patterning job
            try:
                self.microscope.patterning.resume()
            except ApplicationServerException:
                raise Exception("Unable to resume patterning job after performing drift correction.")

    def __wait_for_patterning_end(self, timeout=None):
        """
        Waits until the current patterning job stops.

        When timeout is specified, the method after the given number of seconds even if the patterning is still running.

        :param timeout: Timeout in seconds.
        :return: True when patterning ended, False otherwise (i.e., timeout was reached).
        """

        remaining_time = timeout

        while True:
            if self.microscope.patterning.state == PatterningState.IDLE:
                return True

            time.sleep(1)

            remaining_time -= 1
            if timeout is not None and remaining_time == 0:
                return False

    def __check_fiducial_boundaries(self, image, center, size):
        """
        Checks whether a fiducial defined by the given boundaries fits completely inside the given image.

        The method does not return any value. Instead, it fires an exception when the boundaries are not proper.

        :param image: Image supposed to completely contain the fiducial.
        :param center: Center point of the fiducial, in pixels.
        :param size: Size of the fiducial, in pixels.

        :raises Exception: Raised when the fiducial does not fit completely inside the given image.
        """

        left = center[0] - size / 2
        top = center[1] - size / 2
        right = center[0] + size / 2
        bottom = center[1] + size / 2

        if top < 0 or left < 0 or bottom > image.height or right > image.width:
            raise ValueError("Fiducial cannot be defined according to the given coordinates. Corresponding area of [%d,%d,%d,%d] is outside the given image." % (left, top, right, bottom))

    def __make_multiple2(self, number):
        """Rounds the given number to the nearest multiple of two."""

        remainder = number % 2

        if remainder > 1:
            number += (2 - remainder)
        else:
            number -= remainder

        return int(number)


class DriftSimulator:
    def __init__(self, microscope: SdbMicroscopeClient, step_size=2e-7, interval=0.25):
        self.microscope = microscope
        self.vectors = []
        self.vectors.append(StagePosition(x=step_size, y=step_size))
        self.vectors.append(StagePosition(x=step_size, y=-1 * step_size))
        self.vectors.append(StagePosition(x=-1 * step_size, y=-1 * step_size))
        self.vectors.append(StagePosition(x=-1 * step_size, y=step_size))
        self.interval = interval

    def run(self):
        while True:
            for vector in self.vectors:
                for step in range(10):
                    self.microscope.specimen.stage.relative_move(vector)
                    time.sleep(self.interval)
