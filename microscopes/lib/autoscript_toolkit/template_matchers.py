"""
AutoScript toolkit component providing image template matching mechanisms.
"""

from autoscript_sdb_microscope_client import SdbMicroscopeClient
from autoscript_sdb_microscope_client.structures import *
import abc
import cv2
import numpy


class TemplateMatcher(metaclass=abc.ABCMeta):
    """
    TemplateMatcher is a base class for all image template matchers compliant with AutoScript toolkit.

    Every matcher to be compliant with AutoScript toolkit is expected to derive from TemplateMatcher
    and implement match() function with proper logic.
    """

    @abc.abstractmethod
    def match(self, image: AdornedImage, template: AdornedImage) -> ImageMatch:
        """
        Matches the given template image within the given image to be searched.

        :param image: Image to be searched for a template match.
        :param template: Template to be matched within the searched image.
        :return: Structure containing information about the resulting match.
        """
        raise NotImplementedError("Matching method is not implemented.")


class HogMatcher(TemplateMatcher):
    """
    HogMatcher is an image template matcher based on the advanced HOG algorithm.

    HogMatcher needs to be provided by SdbMicroscopeClient instance
    because the algorithm is being executed on AutoScript server.
    """

    def __init__(self, microscope: SdbMicroscopeClient):
        """Creates a new HogMatcher using the given SDB microscope for HOG algorithm execution."""

        self.microscope = microscope

    def match(self, image: AdornedImage, template: AdornedImage) -> ImageMatch:
        """
        Matches the given template image within the given image to be searched.

        :param image: Image to be searched for a template match.
        :param template: Template to be matched within the searched image.
        :return: Structure containing information about the resulting match.
        """

        match = self.microscope.imaging.match_template(image, template)
        return match


class OpencvComparisonMethod:
    """
    OpencvComparisonMethod lists comparison methods to be used by OpenCV template matching algorithm.

    The class allows convenient setup of OpencvTemplateMatcher.
    """

    EXPRESSIONS = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR', 'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']
    CCOEFF = 0
    CCOEFF_NORMED = 1
    CCORR = 2
    CCORR_NORMED = 3
    SQDIFF = 4
    SQDIFF_NORMED = 5

    @staticmethod
    def provide_expression(method_id):
        expression = OpencvComparisonMethod.EXPRESSIONS[method_id]
        return expression


class OpencvTemplateMatcher(TemplateMatcher):
    """
    OpencvTemplateMatcher is an image template matcher based on OpenCV template matching algorithm.
    """

    def __init__(self, comparison_method_id=OpencvComparisonMethod.CCORR_NORMED):
        """Creates a new OpencvTemplateMatcher using the given OpenCV comparison method."""

        self.comparison_method_id = comparison_method_id
        self.comparison_method = eval(OpencvComparisonMethod.provide_expression(comparison_method_id))

    def match(self, image: AdornedImage, template: AdornedImage):
        """
        Matches the given template image within the given image to be searched.

        :param image: Image to be searched for a template match.
        :param template: Template to be matched within the searched image.
        :return: Structure containing information about the resulting match.
        """

        # Perform image and template format checks
        if image.bit_depth != 8 and image.bit_depth != 16:
            raise ValueError("Cannot perform match because the given image has unsupported bit depth of %d." % (image.bit_depth))
        if template.bit_depth != 8 and template.bit_depth != 16:
            raise ValueError("Cannot perform match because the given template has unsupported bit depth of %d." % (template.bit_depth))

        # Create 8-bit view of image and template because OpenCV can work with 8-bit and 32-bit image data only.
        image_8bit = self.__map_uint16_to_uint8(image.data)
        template_8bit = self.__map_uint16_to_uint8(template.data)

        # Performs actual template matching
        res = cv2.matchTemplate(image_8bit, template_8bit, self.comparison_method)
        min_value, max_value, min_location, max_location = cv2.minMaxLoc(res)

        # Takes minimum when one of SQDIFF* methods is used, maximum otherwise
        if self.comparison_method_id in [OpencvComparisonMethod.SQDIFF, OpencvComparisonMethod.SQDIFF_NORMED]:
            match_top_left = min_location
        else:
            match_top_left = max_location

        # Calculate center point of the match
        match_center = Point(match_top_left[0] + (template.width / 2), match_top_left[1] + (template.height / 2))

        match = ImageMatch(center=match_center)
        return match

    def __map_uint16_to_uint8(self, image: numpy.ndarray) -> numpy.ndarray:
        lower_bound = numpy.min(image)
        upper_bound = numpy.max(image)

        lut = numpy.concatenate([
            numpy.zeros(lower_bound, dtype=numpy.uint16),
            numpy.linspace(0, 255, upper_bound - lower_bound).astype(numpy.uint16),
            numpy.ones(2 ** 16 - upper_bound, dtype=numpy.uint16) * 255
        ])

        return lut[image].astype(numpy.uint8)


DEFAULT_TEMPLATE_MATCHER = OpencvTemplateMatcher()
