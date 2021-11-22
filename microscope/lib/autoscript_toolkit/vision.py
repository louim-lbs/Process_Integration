"""
AutoScript toolkit component providing computer vision functions.
"""

from .template_matchers import *
import cv2
import matplotlib.pyplot as plot
import numpy


class FeatureLocation:
    """
    FeatureLocation contains various information about a feature located in an image.
    """

    def __init__(self):
        self.confidence = None
        self.center_in_pixels = None
        self.center_in_meters = None
        self.shift_in_pixels = None
        self.shift_in_meters = None
        pass

    def print_all_information(self):
        if self.confidence is not None:
            print("Confidence [perc]: %.2f" % self.confidence)
        if self.center_in_pixels is not None:
            print("Center [px]: (%.1f, %.1f)" % (self.center_in_pixels[0], self.center_in_pixels[1]))
        if self.center_in_meters is not None:
            print("Center [m]: (%.4g, %.4g)" % (self.center_in_meters[0], self.center_in_meters[1]))
            print("Center [um]: (%.4f, %.4f)" % (self.center_in_meters[0] * 1e6, self.center_in_meters[1] * 1e6))
        if self.shift_in_pixels is not None:
            print("Shift [px]: (%.4g, %.4g)" % (self.shift_in_pixels[0], self.shift_in_pixels[1]))
        if self.shift_in_meters is not None:
            print("Shift [m]: (%.4g, %.4g)" % (self.shift_in_meters[0], self.shift_in_meters[1]))
            print("Shift [um]: (%.4f, %.4f)" % (self.shift_in_meters[0] * 1e6, self.shift_in_meters[1] * 1e6))


def locate_feature(image: AdornedImage, feature_template: AdornedImage, template_matcher=DEFAULT_TEMPLATE_MATCHER, original_feature_center=None) -> FeatureLocation:
    """
    Locates a feature according to the given template in the given image.

    :param image: Image to be searched for feature.
    :param feature_template: Template of the feature to be located.
    :param template_matcher: Template matcher to be used when matching template against the searched image.
    :param original_feature_center: Center of the original feature location, in pixels. The information is used for shift calculation.

    :return: Structure containing various information about feature location.
    """

    if image.metadata is None or image.metadata.optics is None:
        raise InvalidOperationException("The searched image must have standard metadata.")

    # Calculate size of a single image pixel in meters (based on scan field width corresponding to the image)
    image_pixel_size = image.metadata.optics.scan_field_of_view.width / image.width

    # Perform feature template matching using the selected template matcher
    match = template_matcher.match(image, feature_template)

    # Create a structure containing basic information about the feature location
    feature_location = FeatureLocation()
    feature_location.confidence = match.score
    feature_location.center_in_pixels = match.center
    feature_location.center_in_meters = Point((match.center.x - image.width / 2) * image_pixel_size, ((match.center.y - image.height / 2) * image_pixel_size) * -1)

    # Calculate shift and writes it to the result structure when possible
    if original_feature_center is not None:
        original_feature_center_in_pixels = (original_feature_center[0], original_feature_center[1])
        feature_location.shift_in_pixels = Point(match.center.x - original_feature_center_in_pixels[0], match.center.y - original_feature_center_in_pixels[1])
        feature_location.shift_in_meters = Point(feature_location.shift_in_pixels[0] * image_pixel_size * -1, feature_location.shift_in_pixels[1] * image_pixel_size)

    return feature_location


def cut_image(image, top_left=None, bottom_right=None, center=None, size=None, relative_center=None, relative_size=None):
    """
    Cuts out a part of the given image according to the given target area definition.

    Please note that only the following combinations of parameters are valid: top left and bottom right, center and size,
    or relative center and relative size.

    The method can accept AdornedImage or numpy.ndarray as an input image. The output image is in the same format at the input.

    :param image: Image to cut a part from.
    :param top_left: Top left point of the cut area, in pixels.
    :param bottom_right: Bottom right point of the cut area, in pixels.
    :param center: Center of the cut area, in pixels.
    :param size: Size of the cut area, in pixels.
    :param relative_center: Center of the cut area, in relative coordinates from 0.0 to 1.0.
    :param relative_size: Size of the cut area, in relative coordinates from 0.0 to 1.0.

    :return Cut taken out in the same format as the input image.

    :raises Exception: Raised when the given image is in unsupported format or the given combination of parameters is not valid.
    """

    if not isinstance(image, AdornedImage) and not isinstance(image, numpy.ndarray):
        raise Exception("The given image is in unsupported format.")

    adorned_image_mode = False

    if isinstance(image, AdornedImage):
        adorned_image_mode = True

    x0 = None
    x1 = None
    y0 = None
    y1 = None

    if center is not None and size is not None:
        x0 = int(center[0] - size[0] / 2)
        y0 = int(center[1] - size[1] / 2)
        x1 = x0 + int(size[0])
        y1 = y0 + int(size[1])

    if relative_center is not None and relative_size is not None:
        center = [relative_center[0] * image.width, relative_center[1] * image.height]
        size = [relative_size[0] * image.width, relative_size[1] * image.height]

        x0 = int(center[0] - size[0] / 2)
        y0 = int(center[1] - size[1] / 2)
        x1 = x0 + int(size[0])
        y1 = y0 + int(size[1])

    if top_left is not None and bottom_right is not None:
        x0 = top_left[0]
        x1 = bottom_right[0]
        y0 = top_left[1]
        y1 = bottom_right[1]

    if x0 is not None and x1 is not None and y0 is not None and y1 is not None:
        if adorned_image_mode:
            cut = AdornedImage(image.data[y0:y1, x0:x1])
        else:
            cut = image[y0:y1, x0:x1]

        return cut
    else:
        raise Exception("Cut area could not be properly identified from the given parameters.")


def plot_match(image: AdornedImage, template: AdornedImage, match_center):
    """
    Displays the searched image and the feature located in it on a pop-up window.

    :param image: Searched image in which a feature was located.
    :param template: Template image used for feature location.
    :param match_center: Point referring to the center of the feature located within the searched image, in pixels.
    """

    # Calculate the match location
    half_template_width = int(template.width / 2)
    half_template_height = int(template.height / 2)
    x0 = int(match_center[0] - half_template_width)
    y0 = int(match_center[1] - half_template_height)
    x1 = int(match_center[0] + half_template_width)
    y1 = int(match_center[1] + half_template_height)

    # Make a copy of the given image and draw a rectangle around the match location
    image_copy = AdornedImage(image.data)
    cv2.rectangle(image_copy.data, (x0, y0), (x1, y1), 255, 2)

    # Plot both the template image and whole image with match location marked by a rectangle
    plot.subplot(121), plot.imshow(template.data, cmap='gray')
    plot.title('Template image'), plot.xticks([]), plot.yticks([])
    plot.subplot(122), plot.imshow(image_copy.data, cmap='gray')
    plot.title('Match location'), plot.xticks([]), plot.yticks([])
    plot.show()
