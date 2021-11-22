from autoscript_sdb_microscope_client.tiff_image_loader import TiffImageLoader
import configparser


class IniMetadataReader:
    """
    IniMetadataReader allows reading microscope metadata in Windows INI format and provide them
    in a form a Python dictionary.
    """

    MICROSCOPE_METADATA_TIFF_TAG_ID = 34682

    def read_from_string(self, string: str) -> dict:
        """
        Parses the given string for metadata and provides a corresponding dictionary.
        The string is expected to be in Windows INI format.

        :param string: String to be parsed for metadata.
        :return: Dictionary corresponding to the metadata in the given string.
        :raises ValueError: Raised when any error occurs during the operation.
        """

        metadata = {}

        try:
            ini_parser = configparser.ConfigParser(strict=False)
            ini_parser.optionxform = str
            ini_parser.read_string(string)

            for ini_section_key in ini_parser.sections():
                ini_section = ini_parser[ini_section_key]

                for ini_item_key in ini_section.keys():
                    item_key = ini_section_key + "." + ini_item_key
                    item_value = ini_section[ini_item_key]

                    (item_value, value_parsed_as_int) = self.__int_try_parse(item_value)
                    if not value_parsed_as_int:
                        (item_value, value_parsed_as_float) = self.__float_try_parse(item_value)

                    metadata[item_key] = item_value

        except Exception as ex:
            raise ValueError("Unable to read metadata from the given string.") from ex

        return metadata

    def read_from_tiff_file(self, tiff_file_path):
        """
        Reads metadata from a TIFF file on the given path and provides a corresponding dictionary.

        :param tiff_file_path: Path to the TIFF file to read the metadata from.
        :return: Dictionary corresponding to the metadata in the TIFF file.

        :raises IOError: Raised when any error occurs during the operation.
        """

        metadata = None

        try:
            with TiffImageLoader().open_image(tiff_file_path) as tiff_image:
                tag = tiff_image.tag[self.MICROSCOPE_METADATA_TIFF_TAG_ID][0]
            metadata = self.read_from_string(tag)
        except Exception as ex:
            raise IOError("Unable to read metadata from the given TIFF file.") from ex

        return metadata

    def convert_beam_type(self, beam_type_from_ini_metadata):
        """
        Converts beam type from ini metadata format to AdornedImage metadata format.
        """
        if beam_type_from_ini_metadata == "EBeam":
            return "Electron"
        if beam_type_from_ini_metadata == "IBeam":
            return "Ion"
        if beam_type_from_ini_metadata == "OBeam":
            return "Optical"
        if beam_type_from_ini_metadata == "IRBeam":
            return "Infrared"

        raise ValueError("Invalid beam type in image metadata.")

    def __int_try_parse(self, string):
        """
        Tries to parse the given string for an integer value.

        :param string: String to be parsed.
        :return: Tuple containing the value (either converted to an integer or not) and a flag telling whether the conversion took place.
        """

        try:
            return int(string), True
        except ValueError:
            return string, False

    def __float_try_parse(self, string):
        """
        Tries to parse the given string for a float value.

        :param string: String to be parsed.
        :return: Tuple containing the value (either converted to a float or not) and a flag telling whether the conversion took place.
        """

        try:
            return float(string), True
        except ValueError:
            return string, False

