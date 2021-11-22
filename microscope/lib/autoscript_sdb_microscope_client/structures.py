import autoscript_sdb_microscope_client._structures_shell as shell
from autoscript_sdb_microscope_client.enumerations import ImageDataEncoding
from autoscript_core.serialization import ReprAttr, BytesChopper, BytesBuilder, BasicValueDeserializer, BasicValueSerializer
from autoscript_sdb_microscope_client.tiff_image_loader import TiffImageLoader
from autoscript_sdb_microscope_client.ini_metadata_reader import IniMetadataReader
from autoscript_core.common import InvalidOperationException
import numpy
from hashlib import sha1
import cv2
from PIL import Image
from PIL.TiffImagePlugin import ImageFileDirectory_v2
from xml.etree import ElementTree


class StagePosition(shell.StagePosition):
    __slots__ = []

    def __repr__(self):
        repr_attrs = (ReprAttr("x", "%.8g"), ReprAttr("y", "%.8g"), ReprAttr("z", "%.8g"), ReprAttr("t", "%.8g"), ReprAttr("r", "%.8g"))
        return self._generate_repr(repr_attrs)

    def __len__(self):
        return 5

    def __getitem__(self, index):
        """
        Provides coordinate with the given index.

        The method is designed to behave in the same way as standard tuple/list indexer.
        """

        if not isinstance(index, (int, str)):
            raise TypeError("Stage position coordinate index has to be an integer or string.")
        if isinstance(index, str) and index not in ('x', 'y', 'z', 'r', 't'):
            raise TypeError("Stage axis must be in ('x', 'y', 'z', 'r', 't').")

        if index in (0, 'x'):
            return self.x
        elif index in (1, 'y'):
            return self.y
        elif index in (2, 'z'):
            return self.z
        elif index in (3, 'r'):
            return self.r
        elif index in (4, 't'):
            return self.t
        else:
            raise IndexError("Stage position coordinate index is out of allowed range of (0, 4).")

    def __setitem__(self, index, value):
        """
        Assigns the given value to the coordinate with the given index.

        The method is designed to behave in the same way as standard tuple/list indexer.
        """

        if not isinstance(index, (int, str)):
            raise TypeError("Stage position coordinate index has to be an integer or string.")
        if isinstance(index, str) and index not in ('x', 'y', 'z', 'r', 't'):
            raise TypeError("Stage axis must be in ('x', 'y', 'z', 'r', 't').")

        if index in (0, 'x'):
            self.x = value
        elif index in (1, 'y'):
            self.y = value
        elif index in (2, 'z'):
            self.z = value
        elif index in (3, 'r'):
            self.r = value
        elif index in (4, 't'):
            self.t = value
        else:
            raise IndexError("Stage position coordinate index is out of allowed range of (0, 4).")

    def __add__(self, other):
        """
        Adds the given position-like object or scalar value to this position and provides the result.

        :param other: Position-like object (with coordinates accessible by 0, 1, 2, 3, 4 indices) or a scalar value.
        :return: New position created as a result of the addition.
        """

        try:
            result = StagePosition()
            if hasattr(other, "__getitem__"):
                for i in range(len(self)):
                    if self[i] is not None and other[i] is not None:
                        result[i] = self[i] + other[i]
            else:
                for i in range(len(self)):
                    if self[i] is not None:
                        result[i] = self[i] + other
            return result
        except Exception:
            raise ValueError(f"Cannot add the given {type(other).__name__} to a StagePosition.") from None

    def __radd__(self, other):
        """
        Adds the given position-like object or scalar value to this position and provides the result.

        :param other: Position-like object (with coordinates accessible by 0, 1, 2, 3, 4 indices) or a scalar value.
        :return: New position created as a result of the addition.
        """

        return self.__add__(other)

    def __sub__(self, other):
        """
        Subtracts the given position-like object or scalar value from this position and provides the result.

        :param other: Position-like object (with coordinates accessible by 0, 1, 2, 3, 4 indices) or a scalar value.
        :return: New position created as a result of the subtraction.
        """

        try:
            result = StagePosition()
            if hasattr(other, "__getitem__"):
                for i in range(len(self)):
                    if self[i] is not None and other[i] is not None:
                        result[i] = self[i] - other[i]
            else:
                for i in range(len(self)):
                    if self[i] is not None:
                        result[i] = self[i] - other
            return result
        except Exception:
            raise ValueError(f"Cannot subtract the given {type(other).__name__} from a StagePosition.") from None

    def __rsub__(self, other):
        """
        Subtracts this position or scalar value from the given position-like object and provides the result.

        :param other: Position-like object (with coordinates accessible by 0, 1, 2, 3, 4 indices) or a scalar value.
        :return: New position created as a result of the subtraction.
        """

        try:
            result = StagePosition()
            if hasattr(other, "__getitem__"):
                for i in range(len(self)):
                    if self[i] is not None and other[i] is not None:
                        result[i] = other[i] - self[i]
            else:
                for i in range(len(self)):
                    if self[i] is not None:
                        result[i] = other - self[i]
            return result
        except Exception:
            raise ValueError(f"Cannot subtract a StagePosition from the given {type(other).__name__}.") from None

    def __mul__(self, other):
        """
        Multiplies this position by the given scalar value and provides the result.

        :param other: Scalar value.
        :return: New position created as a result of the multiplication.
        """

        try:
            result = StagePosition()
            for i in range(len(self)):
                if self[i] is not None:
                    result[i] = self[i] * other
            return result
        except Exception:
            raise ValueError(f"Cannot multiply the given {type(other).__name__} by a StagePosition.") from None

    def __rmul__(self, other):
        """
        Multiplies this position by the given scalar value and provides the result.

        :param other: Scalar value.
        :return: New position created as a result of the multiplication.
        """

        return self.__mul__(other)

    def __truediv__(self, other):
        """
        Divides this position by the given scalar value and provides the result.

        :param other: Scalar value.
        :return: New position created as a result of the division.
        """

        try:
            result = StagePosition()
            for i in range(len(self)):
                if self[i] is not None:
                    result[i] = self[i] / other
            return result
        except Exception:
            raise ValueError(f"Cannot divide the given {type(other).__name__} by a StagePosition.") from None

    def __rtruediv__(self, other):
        """
        Divides given scalar value by this position and provides the result.

        :param other: Scalar value.
        :return: New position created as a result of the division.
        """

        try:
            result = StagePosition()
            for i in range(len(self)):
                if self[i] is not None:
                    result[i] = other / self[i]
            return result
        except Exception:
            raise ValueError(f"Cannot divide a StagePosition by the given {type(other).__name__}.") from None

    def __floordiv__(self, other):
        """
        Divides (with floor) this position by the given scalar value and provides the result.

        :param other: Scalar value.
        :return: New position created as a result of the floor division.
        """

        try:
            result = StagePosition()
            for i in range(len(self)):
                if self[i] is not None:
                    result[i] = self[i] // other
            return result
        except Exception:
            raise ValueError(f"Cannot divide the given {type(other).__name__} by a StagePosition.") from None

    def __rfloordiv__(self, other):
        """
        Divides (with floor) given scalar value by this position and provides the result.

        :param other: Scalar value.
        :return: New position created as a result of the floor division.
        """

        try:
            result = StagePosition()
            for i in range(len(self)):
                if self[i] is not None:
                    result[i] = other // self[i]
            return result
        except Exception:
            raise ValueError(f"Cannot divide a StagePosition by the given {type(other).__name__}.") from None

    def __eq__(self, other):
        if not isinstance(other, StagePosition):
            return False

        if len(self) != len(other):
            return False

        for i in range(len(self)):
            if (self[i] is not None and other[i] is None) or (self[i] is None and other[i] is not None):
                return False
            if self[i] is not None and other[i] is not None and self[i] != other[i]:
                return False

        return True


class AdornedImage(shell.AdornedImage):
    __slots__ = []
    __INI_METADATA_TIFF_TAG = 34682
    __XML_METADATA_TIFF_TAG = 34683

    def __init__(self, data=None, metadata=None):
        """
        Constructs a new AdornedImage.

        :param data: Data to construct the new AdornedImage from, in a form of numpy.ndarray.
        :type data: numpy.ndarray
        :param metadata: Metadata to assign to this instance of AdornedImage.
        :type metadata: AdornedImageMetadata
        """

        super().__init__()

        # Constructs a new AdornedImage from the given image data and metadata.
        # This approach is intended for images created directly by user. Images coming from the AutoScript Server
        # get their members filled in during object deserialization.
        if data is not None:
            self.__construct_from_data(data)

        # Assigns metadata from an external source to this instance of AdornedImage
        if metadata is not None:
            self.metadata = metadata

    @property
    def encoding(self):
        if self.bit_depth == 24 and self.raw_encoding == ImageDataEncoding.BGR:
            # BGR is presented as RGB and a conversion is done on .data access
            return ImageDataEncoding.RGB

        if self.bit_depth == 24 and self.raw_encoding == ImageDataEncoding.RGB:
            return ImageDataEncoding.RGB

        return ImageDataEncoding.UNSIGNED

    @property
    def data(self) -> numpy.ndarray:
        """
        Provides access to data in a form of numpy.ndarray.

        :return: Image data in a form of numpy.ndarray.
        """
        self.__ensure_not_empty()
        data = None

        if self.bit_depth == 8 and self.raw_encoding == ImageDataEncoding.UNSIGNED:
            raw_data_bytes = numpy.frombuffer(self.raw_data, dtype=numpy.uint8)
            data = numpy.reshape(raw_data_bytes, (self.height, self.width))
        elif self.bit_depth == 16 and self.raw_encoding == ImageDataEncoding.UNSIGNED:
            raw_data_bytes = numpy.frombuffer(self.raw_data, dtype=numpy.uint16)
            data = numpy.reshape(raw_data_bytes, (self.height, self.width))
        elif self.bit_depth == 24 and self.raw_encoding == ImageDataEncoding.BGR:
            raw_data_bytes = numpy.frombuffer(self.raw_data, dtype=numpy.uint8)
            bgr_data = numpy.reshape(raw_data_bytes, (self.height, self.width, 3))
            data = bgr_data[..., ::-1]  # This doesn't make a copy, it just creates a new view on the data (we need RGB)
        elif self.bit_depth == 24 and self.raw_encoding == ImageDataEncoding.RGB:
            raw_data_bytes = numpy.frombuffer(self.raw_data, dtype=numpy.uint8)
            data = numpy.reshape(raw_data_bytes, (self.height, self.width, 3))
        else:
            data = numpy.frombuffer(self.raw_data, dtype=numpy.uint8)

        return data

    @property
    def checksum(self) -> str:
        """
        Provides checksum of the raw_data.

        :return: checksum of the raw_data.
        """

        self.__ensure_not_empty()
        return sha1(self.raw_data).hexdigest()

    @property
    def thumbnail(self) -> 'AdornedImage':
        """
        Provides a thumbnail of this image. The thumbnail width is 512 pixels, the height is calculated to maintain the original aspect ratio.
        The thumbnail image will not have image metadata.

        :return: Thumbnail of this image as a new AdornedImage object.
        """

        self.__ensure_not_empty()

        ratio = self.width / 512
        thumbnail_height = round(self.height / ratio)

        # PIL won't resize 16-bit grayscale images, ask OpenCV
        resized_data = cv2.resize(self.data, (512, thumbnail_height))
        return AdornedImage(resized_data)

    def save(self, path):
        if not path.endswith("tiff") and not path.endswith("tif"):
            path = path + ".tiff"

        pil_image = self.__get_raw_data_as_pil_image()

        # Construct exif data
        tiff_tags = ImageFileDirectory_v2()
        tiff_tags.__setitem__(256, self.width)   # Width
        tiff_tags.__setitem__(257, self.height)  # Height
        tiff_tags.__setitem__(259, 1)            # Compression = 1 (raw)
        tiff_tags.__setitem__(296, 2)            # Resolution unit = 2 (cm)

        if self.bit_depth < 24:
            tiff_tags.__setitem__(258, (self.bit_depth,))  # Bit depth - if 24, save 8,8,8
            tiff_tags.__setitem__(262, 1)        # Photometric interpretation = 1(BlackIsZero)
        else:
            tiff_tags.__setitem__(258, (8, 8, 8))
            tiff_tags.__setitem__(262, 2)        # Photometric interpretation = 2(RGB)

        # Store image metadata
        if self.metadata is not None:
            if self.metadata.metadata_as_ini is not None:
                tiff_tags.__setitem__(AdornedImage.__INI_METADATA_TIFF_TAG, self.metadata.metadata_as_ini)

            if self.metadata.metadata_as_xml is not None:
                tiff_tags.__setitem__(AdornedImage.__XML_METADATA_TIFF_TAG, self.metadata.metadata_as_xml)

        pil_image.save(path, format=None, tiffinfo=tiff_tags)

        # Append metadata in INI format once more to the resulting image file
        if self.metadata is not None and self.metadata.metadata_as_ini is not None:
            with open(path, mode='a') as image_file:
                # Replace \r\n with just \n, because python writes \n as \r\n to text file
                metadata_as_ini = self.metadata.metadata_as_ini.replace("\r\n", "\n")
                image_file.write(metadata_as_ini)

    @staticmethod
    def load(path: str) -> 'AdornedImage':
        with TiffImageLoader().open_image(path) as tiff_image:

            raw_data = tiff_image.tobytes()

            if tiff_image.mode == 'L':
                raw_data_bytes = numpy.frombuffer(raw_data, dtype=numpy.uint8)
                new_data = numpy.reshape(raw_data_bytes, (tiff_image.height, tiff_image.width))
            elif tiff_image.mode == 'I;16':
                raw_data_bytes = numpy.frombuffer(raw_data, dtype=numpy.uint16)
                new_data = numpy.reshape(raw_data_bytes, (tiff_image.height, tiff_image.width))
            elif tiff_image.mode == 'RGB':
                raw_data_bytes = numpy.frombuffer(raw_data, dtype=numpy.uint8)
                new_data = numpy.reshape(raw_data_bytes, (tiff_image.height, tiff_image.width, 3))
            else:
                # The other PIL supported types and bit depths are expected to be managed by the user
                new_data = numpy.frombuffer(raw_data, dtype=numpy.uint8)

            image = AdornedImage(new_data)

            AdornedImage.__read_image_metadata_xml(image, tiff_image)
            AdornedImage.__read_image_metadata_ini(image, tiff_image)

            return image

    @staticmethod
    def __read_image_metadata_xml(image, tiff_image):
        if not hasattr(tiff_image, "tag"):
            return

        if AdornedImage.__XML_METADATA_TIFF_TAG in tiff_image.tag:
            xml_metadata = tiff_image.tag[AdornedImage.__XML_METADATA_TIFF_TAG][0]
            try:
                if image.metadata is None:
                    image.metadata = AdornedImageMetadata()

                ElementTree.fromstring(xml_metadata)
                image.metadata = AdornedImageMetadata()
                image.metadata.metadata_as_xml = xml_metadata
            except ElementTree.ParseError:
                pass

    @staticmethod
    def __read_image_metadata_ini(image, tiff_image):
        if not hasattr(tiff_image, "tag"):
            return

        if AdornedImage.__INI_METADATA_TIFF_TAG in tiff_image.tag:
            ini_metadata = tiff_image.tag[AdornedImage.__INI_METADATA_TIFF_TAG][0]

            metadata_reader = IniMetadataReader()
            metadata = metadata_reader.read_from_string(ini_metadata)

            if image.metadata is None:
                image.metadata = AdornedImageMetadata()

            image.metadata.metadata_as_ini = ini_metadata

            if "Beam.Beam" in metadata:
                image_beam = metadata["Beam.Beam"]
                if image_beam == "Beam":
                    # Empty metadata block, typically from uninitialized server pipeline, do not continue parsing
                    return
                if image.metadata.acquisition is None:
                    image.metadata.acquisition = AdornedImageMetadataAcquisition()
                image.metadata.acquisition.beam_type = metadata_reader.convert_beam_type(image_beam)

            if "Scan.HorFieldsize" in metadata and "Scan.VerFieldsize" in metadata:
                image.metadata.optics = AdornedImageMetadataOptics()
                image.metadata.optics.scan_field_of_view = AdornedImageMetadataOpticsScanFieldSize()
                image.metadata.optics.scan_field_of_view.width = metadata["Scan.HorFieldsize"]
                image.metadata.optics.scan_field_of_view.height = metadata["Scan.VerFieldsize"]

            if "Scan.PixelWidth" in metadata and "Scan.PixelHeight" in metadata:
                image.metadata.binary_result = AdornedImageMetadataBinaryResult()
                image.metadata.binary_result.pixel_size = Point()
                image.metadata.binary_result.pixel_size.x = metadata["Scan.PixelWidth"]
                image.metadata.binary_result.pixel_size.y = metadata["Scan.PixelHeight"]

    def __repr__(self):
        repr_attrs = (ReprAttr("width", "%.8g"), ReprAttr("height", "%.8g"), ReprAttr("bit_depth", "%.8g"))
        return self._generate_repr(repr_attrs)

    def __construct_from_data(self, data: numpy.ndarray):
        """
        Constructs the AdornedImage object from the given data in a form of numpy.ndarray.

        The method is expected to be used when user creates a new AdornedImage directly, providing a numpy.ndarray as a data source.
        """

        if not isinstance(data, numpy.ndarray):
            raise ValueError("Cannot construct AdornedImage because the given data are not of numpy.ndarray type.")

        try:
            (width, height, bit_depth) = self.__determine_image_dimensions(data)
            self.width = width
            self.height = height
            self.bit_depth = bit_depth
        except:
            raise ValueError("Cannot construct AdornedImage because the given data are not in compatible form.")

        # Internal format for color images is always BGR
        self.raw_encoding = ImageDataEncoding.BGR if self.bit_depth == 24 else ImageDataEncoding.UNSIGNED

        self.__generate_raw_data(data, self.bit_depth)

    def __generate_raw_data(self, ndarray: numpy.ndarray, bit_depth: int):
        """
        Generates raw image data according to the given data in a form of numpy.ndarray and the given bit depth.
        Raw data are stored in neutral AutoScript form.

        :param ndarray: Data in a form of numpy.ndarray to serve as a data source.
        :param bit_depth: Bit depth of the given data.
        """

        # Creates memory view of the given data compatible with neutral AutoScript form.
        # For 8-bit and 16-bit images, numpy.ndarray form is similar to neutral AutoScript form.
        compatible_memory_view = None
        if bit_depth == 8 or bit_depth == 16:
            compatible_memory_view = memoryview(ndarray)

        # Creates memory view of the given data compatible with neutral AutoScript form.
        # For 24-bit images, a conversion from RGB to BGR has to be made.
        if bit_depth == 24:
            compatible_memory_view = ndarray[..., ::-1]

        # Creates a copy of the compatible memory view and stores it as a raw image data
        self.raw_data = compatible_memory_view.tobytes()

    def __determine_image_dimensions(self, ndarray: numpy.ndarray) -> (int, int, int):
        """
        Determines image dimensions from the given numpy.ndarray.

        :param ndarray: numpy.ndarray to determine image dimensions from.
        :return: Triplet of width, height and bit depth of the image.

        :raises Exception: Raised when dimensions can not be properly determined.
        """

        if ndarray.ndim == 2 and ndarray.dtype == numpy.uint8:
            return ndarray.shape[1], ndarray.shape[0], 8
        if ndarray.ndim == 2 and ndarray.dtype == numpy.uint16:
            return ndarray.shape[1], ndarray.shape[0], 16
        if ndarray.ndim == 3 and ndarray.shape[2] == 3 and ndarray.dtype == numpy.uint8:
            return ndarray.shape[1], ndarray.shape[0], 24

        raise Exception("Cannot determine image dimensions from the given numpy.ndarray.")

    def __ensure_not_empty(self):
        if self.raw_data is None:
            raise InvalidOperationException("Adorned image object was not initialized with image data.")

    def __get_raw_data_as_pil_image(self) -> Image:
        self.__ensure_not_empty()

        if self.bit_depth == 16:
            # 16 bit images need special treatment
            return Image.frombuffer("I;16", (self.width, self.height), self.raw_data, "raw", "I;16", 0, 1)

        return Image.fromarray(self.data)


class Limits(shell.Limits):
    __slots__ = []

    def __repr__(self):
        repr_attrs = (ReprAttr("min", "%.8g"), ReprAttr("max", "%.8g"))
        return self._generate_repr(repr_attrs)

    def is_in(self, value):
        return self.min <= value <= self.max


class Limits2d(shell.Limits2d):
    __slots__ = []

    def __repr__(self):
        repr_attrs = (ReprAttr("limits_x", "%s"), ReprAttr("limits_y", "%s"))
        return self._generate_repr(repr_attrs)

    def is_in(self, point):
        if not isinstance(point, Point):
            raise ValueError("You need to provide Point.")

        return (self.limits_x.min <= point.x <= self.limits_x.max) and (self.limits_y.min <= point.y <= self.limits_y.max)


class Point(shell.Point):
    __slots__ = []

    def __len__(self):
        return 2

    def __getitem__(self, index):
        """
        Provides coordinate with the given index.

        The method is designed to behave in the same way as standard tuple/list indexer.
        It allows Point to be treated as tuple/list in numpy/scipy and other libraries
        that work with points represented by tuples/lists.
        """

        if not isinstance(index, int):
            raise TypeError("Point coordinate index has to be an integer.")

        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            raise IndexError("Point coordinate index is out of range (0, 1).")

    def __setitem__(self, index, value):
        """
        Assigns a value to the coordinate with the given index.

        The method is designed to behave in the same way as standard tuple/list indexer.
        It allows Point to be treated as tuple/list in numpy/scipy and other libraries
        that work with points represented by tuples/lists.
        """

        if not isinstance(index, int):
            raise TypeError("Point coordinate index has to be an integer.")

        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        else:
            raise IndexError("Point coordinate index is out of range (0, 1).")

    def __add__(self, other):
        """
        Adds a point-like object or scalar value to this point and provides the result.

        :param other: Point-like object (with coordinates accessible by 0, 1 indices) or a scalar value.
        :return: New point created as a result of the addition.
        """

        try:
            if isinstance(other, (int, float, numpy.floating)):
                return Point(self[0] + other, self[1] + other)

            return Point(self[0] + other[0], self[1] + other[1])
        except Exception:
            raise ValueError(f"Cannot add the given {type(other).__name__} to a Point.") from None

    def __radd__(self, other):
        """
        Adds a point-like object or scalar value to this point and provides the result.

        :param other: Point-like object (with coordinates accessible by 0, 1 indices) or a scalar value.
        :return: New point created as a result of the addition.
        """

        return self.__add__(other)

    def __sub__(self, other):
        """
        Subtracts a point-like object or scalar value from this point and provides the result.

        :param other: Point-like object (with coordinates accessible by 0, 1 indices) or a scalar value.
        :return: New point created as a result of the subtraction.
        """

        try:
            if isinstance(other, (int, float, numpy.floating)):
                return Point(self[0] - other, self[1] - other)

            return Point(self[0] - other[0], self[1] - other[1])
        except Exception:
            raise ValueError(f"Cannot subtract the given {type(other).__name__} from a Point.") from None

    def __rsub__(self, other):
        """
        Subtracts this point from a point-like object or scalar value and provides the result.

        :param other: Point-like object (with coordinates accessible by 0, 1 indices) or a scalar value.
        :return: New point created as a result of the subtraction.
        """

        try:
            if isinstance(other, (int, float, numpy.floating)):
                return Point(other - self[0], other - self[1])

            return Point(other[0] - self[0], other[1] - self[1])
        except Exception:
            raise ValueError(f"Cannot subtract a Point from the given {type(other).__name__}.") from None

    def __mul__(self, other):
        """
        Multiplies this point with a scalar and returns the result.
        If a point-like object is provided it returns the dot product.

        :param other: Scalar value or Point-like object (with coordinates accessible by 0, 1 indices).
        :return: New point created as a result of the multiplication.
        """

        try:
            if isinstance(other, (int, float, numpy.floating)):
                return Point(other * self[0], other * self[1])

            return other[0] * self[0] + other[1] * self[1]
        except Exception:
            raise ValueError(f"Cannot multiply the given {type(other).__name__} by a Point.") from None

    def __rmul__(self, other):
        """
        Multiplies this point with a scalar and returns the result.
        If a point-like object is provided it returns the dot product.

        :param other: Scalar value or Point-like object (with coordinates accessible by 0, 1 indices).
        :return: New point created as a result of the multiplication.
        """

        return self.__mul__(other)

    def __truediv__(self, other):
        """
        Divides this point by a scalar and returns the result.

        :param other: Scalar value.
        :return: New point created as a result of dividing the Point by the scalar.
        """

        try:
            return Point(self[0] / other, self[1] / other)
        except Exception:
            raise ValueError(f"Cannot divide the given {type(other).__name__} by a Point.") from None

    def __rtruediv__(self, other):
        """
        Divides a scalar by this point and provides the result.

        :param other: Scalar value.
        :return: New point created as a result of dividing the Point by the scalar.
        """

        try:
            return Point(other / self[0], other / self[1])
        except Exception:
            raise ValueError(f"Cannot divide a Point by the given {type(other).__name__}.") from None

    def __floordiv__(self, other):
        """
        Divides (with floor) this point by a scalar and returns the result.

        :param other: Scalar value.
        :return: New point created as a result of the floor division.
        """

        try:
            return Point(self[0] // other, self[1] // other)
        except Exception:
            raise ValueError(f"Cannot divide the given {type(other).__name__} by a Point.") from None

    def __rfloordiv__(self, other):
        """
        Divides (with floor) a scalar by this point and provides the result.

        :param other: Scalar value.
        :return: New point created as a result of the floor division.
        """

        try:
            return Point(other // self[0], other // self[1])
        except Exception:
            raise ValueError(f"Cannot divide a Point by the given {type(other).__name__}.") from None

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False

        if len(self) != len(other):
            return False

        return self[0] == other[0] and self[1] == other[1]

    def __repr__(self):
        repr_attrs = (ReprAttr("x", "%.8g"), ReprAttr("y", "%.8g"))
        return self._generate_repr(repr_attrs)

    def magnitude(self):
        """
        Returns the magnitude of the point which is the distance from 0, 0.

        :return: Magnitude as a float.
        """

        try:
            return float(numpy.sqrt(self.x ** 2 + self.y ** 2))
        except:
            raise ValueError("Cannot compute Point distance.")

    def angle(self):
        """
        Returns the angle of the point.

        :return: Radian angle as a float.
        """

        try:
            return float(numpy.arctan2(self.y, self.x))
        except:
            raise ValueError("Cannot compute Point angle.")

    @classmethod
    def create_from(cls, value):
        instance = cls()
        if isinstance(value, Point):
            return value
        elif isinstance(value, tuple):
            if len(value) != 2:
                raise TypeError("Need tuple of 2 elements to create Point.")
            instance.x = value[0]
            instance.y = value[1]
        elif isinstance(value, list):
            if len(value) != 2:
                raise TypeError("Need list of 2 elements to create Point.")
            instance.x = value[0]
            instance.y = value[1]
        else:
            raise TypeError(f"Can't create Point from {type(value)}.")
        return instance


class Rectangle(shell.Rectangle):
    """
    The structure representing a rectangular shape.
    """
    __slots__ = []

    def __repr__(self):
        repr_attrs = (ReprAttr("left", "%.8g"), ReprAttr("top", "%.8g"), ReprAttr("width", "%.8g"), ReprAttr("height", "%.8g"))
        return self._generate_repr(repr_attrs)


class ManipulatorPosition(shell.ManipulatorPosition):
    __slots__ = []

    def __repr__(self):
        repr_attrs = (ReprAttr("x", "%.8g"), ReprAttr("y", "%.8g"), ReprAttr("z", "%.8g"), ReprAttr("r", "%.8g"))
        return self._generate_repr(repr_attrs)


class MoveSettings(shell.MoveSettings):
    __slots__ = []


class GrabFrameSettings(shell.GrabFrameSettings):
    __slots__ = []


class ImageMatch(shell.ImageMatch):
    __slots__ = []

    def __repr__(self):
        repr_attrs = (ReprAttr("center", "%s"), ReprAttr("score", "%.2f"))
        return self._generate_repr(repr_attrs)


class StreamPatternDefinition(shell.StreamPatternDefinition):
    __slots__ = []

    # STREAMFILE_HEADER()
    # {
    #    DACResolution = 12;
    #    repeat = 0;
    #    count = 0;
    #    DwellTimeBase = 100;
    #    isDACvalues = FALSE;
    #    toReportBlankProblem = TRUE;
    #    toBlank = TRUE;
    # }

    # overwrite __init__ so load_from_file has to be called to initialize data
    def __init__(self):
        super().__init__(bit_depth=16)
        self._dwell_time_base = 25
        self._points = numpy.array([])

    @property
    def points(self) -> numpy.ndarray:
        return self._points

    @points.setter
    def points(self, arr: numpy.ndarray):
        self._check_array_dimensions(arr)
        self._points = arr

    @shell.StreamPatternDefinition.bit_depth.setter
    def bit_depth(self, value):
        if value == 12 or value == 16:
            super(StreamPatternDefinition, self.__class__).bit_depth.fset(self, value)
        else:
            raise Exception("Stream pattern bit depth can be either 12 or 16.")

    @staticmethod
    def load(path: str) -> 'StreamPatternDefinition':
        spd = StreamPatternDefinition()

        with open(path, 'r') as f:
            # line 1
            line = f.readline()
            tokens = [x.strip().lower() for x in line.split(',')]
            if "s16" in tokens:
                spd.bit_depth = 16
            elif "s" in tokens:
                spd.bit_depth = 12
            else:
                raise Exception("Missing 's' title signature!")

            if "25ns" in tokens:
                spd._dwell_time_base = 25
            else:
                spd._dwell_time_base = 100

            # line 2
            line = f.readline()
            spd.repeat_count = int(line)

            # line 3
            line = f.readline()
            points_count = int(line)

            points = numpy.zeros(shape=(points_count, 4), dtype=object)

            import re
            numeric_tokens_regex = re.compile(r'\d\d*')

            # points
            for i in range(0, points_count):
                line = f.readline()
                numeric_tokens = numeric_tokens_regex.findall(line)

                if len(numeric_tokens) < 3:
                    continue

                points[i][0] = int(numeric_tokens[1])  # x
                points[i][1] = int(numeric_tokens[2])  # y
                points[i][2] = float(numeric_tokens[0]) * spd._dwell_time_base * 1e-9  # dwell time in seconds
                points[i][3] = 0  # bit mask for additional settings

                if len(numeric_tokens) > 3:
                    # reads blank setting from stream file: 0 means blank, 1 means unblank
                    blank_setting = int(numeric_tokens[3])

                    # sets blanking bit in the additional settings bitmask if blank setting says the point should be blanked
                    if blank_setting == 0:
                        points[i][3] |= 1

            spd._points = points

            return spd

    def _check_array_dimensions(self, arr: numpy.ndarray):
        if not isinstance(arr, numpy.ndarray):
            raise TypeError("The passed value is not an ndarray.")
        if not arr.ndim == 2:
            raise TypeError("The passed value is not a 2 dimensional array.")
        if not arr.shape[1] == 4:
            raise TypeError("All points in the array must have 4 items: [x, y, dwell_time_in_seconds, blank].")

    def _serialize_to(self, bytes_builder: BytesBuilder, serializer):
        raw_points_builder = BytesBuilder()
        for p in self.points:
            BasicValueSerializer.serialize_int32(p[0], raw_points_builder)
            BasicValueSerializer.serialize_int32(p[1], raw_points_builder)
            BasicValueSerializer.serialize_double(p[2], raw_points_builder)
            BasicValueSerializer.serialize_int32(p[3], raw_points_builder)

        self.raw_points = raw_points_builder.get_data()
        super()._serialize_to(bytes_builder, serializer)

    def _deserialize_from(self, chopper: BytesChopper, deserializer):
        super()._deserialize_from(chopper, deserializer)

        raw_points_chopper = BytesChopper(self.raw_points)
        points = []

        while raw_points_chopper.bytes_left() > 0:
            x = BasicValueDeserializer.deserialize_int32(raw_points_chopper)
            y = BasicValueDeserializer.deserialize_int32(raw_points_chopper)
            dwell_time = BasicValueDeserializer.deserialize_double(raw_points_chopper)
            blank = BasicValueDeserializer.deserialize_int32(raw_points_chopper)
            points.append([x, y, dwell_time, blank])

        self.points = numpy.array(points)


class GetRtmPositionSettings(shell.GetRtmPositionSettings):
    __slots__ = []


class RtmPositionSet(shell.RtmPositionSet):
    __slots__ = []

    def __init__(self):
        super().__init__()
        self._positions = numpy.array([])

    @property
    def positions(self) -> numpy.ndarray:
        return self._positions

    def _serialize_to(self, bytes_builder: BytesBuilder, serializer):
        raw_positions_builder = BytesBuilder()
        for p in self.positions:
            BasicValueSerializer.serialize_int32(p[0], raw_positions_builder)
            BasicValueSerializer.serialize_int32(p[1], raw_positions_builder)

        self.raw_positions = raw_positions_builder.get_data()
        super()._serialize_to(bytes_builder, serializer)

    def _deserialize_from(self, chopper: BytesChopper, deserializer):
        super()._deserialize_from(chopper, deserializer)

        if self.raw_positions is not None:
            positions_1d = numpy.frombuffer(self.raw_positions, dtype=">i4")
            count = int(len(positions_1d) / 2)
            self._positions = numpy.reshape(positions_1d, (count, 2))

        else:
            self._positions = None


class GetRtmDataSettings(shell.GetRtmDataSettings):
    __slots__ = []


class RtmDataSet(shell.RtmDataSet):
    __slots__ = []

    def __init__(self):
        super().__init__()
        self._values = numpy.array([])

    @property
    def values(self) -> numpy.ndarray:
        return self._values

    def _serialize_to(self, bytes_builder: BytesBuilder, serializer):
        raw_values_builder = BytesBuilder()
        for value in self.values:
            BasicValueSerializer.serialize_byte(value, raw_values_builder)

        self.raw_values = raw_values_builder.get_data()
        super()._serialize_to(bytes_builder, serializer)

    def _deserialize_from(self, chopper: BytesChopper, deserializer):
        super()._deserialize_from(chopper, deserializer)

        if self.raw_values is not None:
            self._values = numpy.frombuffer(self.raw_values, dtype=numpy.uint8)
        else:
            self._values = None



class RunAutoCbSettings(shell.RunAutoCbSettings):
    __slots__ = []


class CompustagePosition(shell.CompustagePosition):
    __slots__ = []

    def __repr__(self):
        repr_attrs = (ReprAttr("x", "%.8g"), ReprAttr("y", "%.8g"), ReprAttr("z", "%.8g"), ReprAttr("a", "%.8g"),
                      ReprAttr("b", "%.8g"))
        return self._generate_repr(repr_attrs)


class LargeImageHeader(shell.LargeImageHeader):
    __slots__ = []


class RunAutoFocusSettings(shell.RunAutoFocusSettings):
    __slots__ = []


class RunAutoStigmatorSettings(shell.RunAutoStigmatorSettings):
    __slots__ = []


class RunAutoLensAlignmentSettings(shell.RunAutoLensAlignmentSettings):
    __slots__ = []


class DetectorInsertSettings(shell.DetectorInsertSettings):
    __slots__ = []


class RunAutoSourceTiltSettings(shell.RunAutoSourceTiltSettings):
    __slots__ = []


class RunAutoStigmatorCenteringSettings(shell.RunAutoStigmatorCenteringSettings):
    __slots__ = []


class BitmapPatternDefinition(shell.BitmapPatternDefinition):
    __slots__ = []

    def __init__(self):
        super().__init__()
        self.width = 0
        self.height = 0
        self._points = numpy.array([])

    @property
    def points(self) -> numpy.ndarray:
        return self._points

    @points.setter
    def points(self, arr: numpy.ndarray):
        self._check_array_dimensions(arr)
        self.width = len(arr[0])
        self.height = len(arr)
        self._points = arr

    @staticmethod
    def load(path: str) -> 'BitmapPatternDefinition':
        bpd = BitmapPatternDefinition()

        image = TiffImageLoader().open_image(path)
        arr = numpy.array(image)

        bpd.width = len(arr[0])
        bpd.height = len(arr)
        bpd.points = numpy.zeros(shape=(bpd.height, bpd.width, 2), dtype=object)
        bpd.points[:, :, 0] = arr[:, :, 2] / 255.0

        # The logic below is reverted, in original image blanking was signaled by providing zero,
        # in BitmapPatternDefinition blanking is signaled by providing a non zero value.
        bpd.points[arr[:, :, 1] == 0, 1] = 1  # 1 means blank
        bpd.points[arr[:, :, 1] != 0, 1] = 0  # 0 means do not blank

        return bpd

    def _check_array_dimensions(self, arr: numpy.ndarray):
        if not isinstance(arr, numpy.ndarray):
            raise TypeError("The passed value is not an ndarray.")
        if not arr.ndim == 3:
            raise TypeError("The passed value is not a 3 dimensional array.")
        if not arr.shape[2] == 2:
            raise TypeError("All points in the array must have 2 items: [dwell_time_coefficient, bitmask].")

    def _serialize_to(self, bytes_builder: BytesBuilder, serializer):
        raw_points_builder = BytesBuilder()
        for y in range(self.height):
            for x in range(self.width):
                BasicValueSerializer.serialize_double(self.points[y, x, 0], raw_points_builder)
                BasicValueSerializer.serialize_int32(self.points[y, x, 1], raw_points_builder)

        self.raw_points = raw_points_builder.get_data()
        super()._serialize_to(bytes_builder, serializer)

    def _deserialize_from(self, chopper: BytesChopper, deserializer):
        super()._deserialize_from(chopper, deserializer)

        self.points = numpy.zeros(shape=(self.width, self.height, 2), dtype=object)
        chopper = BytesChopper(self.raw_points, 0)

        for y in range(self.height):
            for x in range(self.width):
                self.points[y, x, 0] = BasicValueDeserializer.deserialize_double(chopper)
                self.points[y, x, 1] = BasicValueDeserializer.deserialize_int32(chopper)


class RtmPosition(shell.RtmPosition):
    __slots__ = []


class StreamPatternPoint(shell.StreamPatternPoint):
    __slots__ = []


class BitmapPatternPoint(shell.BitmapPatternPoint):
    __slots__ = []


class VacuumSettings(shell.VacuumSettings):
    __slots__ = []


class Variant(shell.Variant):
    __slots__ = []

    @classmethod
    def create_from(cls, value):
        instance = cls()
        if isinstance(value, float):
            instance.value_double = value
        elif isinstance(value, int):
            instance.value_int = value
        elif isinstance(value, bool):
            instance.value_bool = value
        elif isinstance(value, str):
            instance.value_string = value
        else:
            raise TypeError(f"Can't create Variant from {type(value)}.")
        return instance

    def _is_float(self):
        return self.value_double is not None

    def _is_int(self):
        return self.value_int is not None

    def _is_bool(self):
        return self.value_bool is not None

    def _is_string(self):
        return self.value_string is not None

    @property
    def value(self):
        if self._is_float():
            return self.value_double
        if self._is_int():
            return self.value_int
        if self._is_bool():
            return self.value_bool
        if self._is_string():
            return self.value_string
        return None

    def __repr__(self):
        return str(self.value)

    def __str__(self):
        return str(self.value)

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)

    def __bool__(self):
        return bool(self.value)

    def __eq__(self, other):
        return self.value == other

    def __gt__(self, other):
        return self.value > other

    def __lt__(self, other):
        return self.value < other

    def __ne__(self, other):
        return self.value != other

    def __ge__(self, other):
        return self.value >= other

    def __le__(self, other):
        return self.value <= other

    def __add__(self, other):
        return self.value + other

    def __radd__(self, other):
        return other + self.value

    def __mul__(self, other):
        return self.value * other

    def __rmul__(self, other):
        return other * self.value

    def __sub__(self, other):
        return self.value - other

    def __rsub__(self, other):
        return other - self.value

    def __truediv__(self, other):
        return self.value / other

    def __rtruediv__(self, other):
        return other / self.value

    def __floordiv__(self, other):
        return self.value // other

    def __rfloordiv__(self, other):
        return other // self.value

class AdornedImageMetadataBinaryResult(shell.AdornedImageMetadataBinaryResult):
    __slots__ = []


class AdornedImageMetadataCore(shell.AdornedImageMetadataCore):
    __slots__ = []


class AdornedImageMetadataDetector(shell.AdornedImageMetadataDetector):
    __slots__ = []


class AdornedImageMetadataEnergyFilterSettings(shell.AdornedImageMetadataEnergyFilterSettings):
    __slots__ = []


class AdornedImageMetadataGasInjectionSystemGas(shell.AdornedImageMetadataGasInjectionSystemGas):
    __slots__ = []


class AdornedImageMetadataGasInjectionSystem(shell.AdornedImageMetadataGasInjectionSystem):
    __slots__ = []


class AdornedImageMetadataOpticsAperture(shell.AdornedImageMetadataOpticsAperture):
    __slots__ = []


class AdornedImageMetadataOpticsScanFieldSize(shell.AdornedImageMetadataOpticsScanFieldSize):
    __slots__ = []

    def __repr__(self):
        repr_attrs = (ReprAttr("width", "%.8g"), ReprAttr("height", "%.8g"))
        return self._generate_repr(repr_attrs)


class AdornedImageMetadataScanSettings(shell.AdornedImageMetadataScanSettings):
    __slots__ = []


class AdornedImageMetadataStageSettings(shell.AdornedImageMetadataStageSettings):
    __slots__ = []


class AdornedImageMetadataVacuumProperties(shell.AdornedImageMetadataVacuumProperties):
    __slots__ = []


class AdornedImageMetadata(shell.AdornedImageMetadata):
    __slots__ = []


class AdornedImageMetadataInstrument(shell.AdornedImageMetadataInstrument):
    __slots__ = []


class AdornedImageMetadataSample(shell.AdornedImageMetadataSample):
    __slots__ = []


class AdornedImageMetadataOptics(shell.AdornedImageMetadataOptics):
    __slots__ = []


class AdornedImageMetadataAcquisition(shell.AdornedImageMetadataAcquisition):
    __slots__ = []



class TemperatureSettings(shell.TemperatureSettings):    
    """
    Settings for controlling temperature of heating or cooling stages.
    
    :param float target_temperature: Target temperature in Kelvins.
    
    :param float ramp_speed: Ramping speed in Kelvins per second.
    
    :param float soak_time: Time in seconds to remain at the target temperature after it has been reached within the specified tolerance.
    
    :param float tolerance: Minimum desired difference between target and actual temperatures, in Kelvins.
    
    :param int timeout: Maximum time the temperature ramping can last, in seconds.
    """
    __slots__ = []
