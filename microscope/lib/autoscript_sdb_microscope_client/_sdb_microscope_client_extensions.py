from autoscript_sdb_microscope_client.enumerations import ImageFileFormat
from autoscript_sdb_microscope_client.structures import AdornedImage
from autoscript_core.common import ApiException, ApiErrorCode
from autoscript_sdb_microscope_client.build_information import *
import os


class SdbMicroscopeClientExtensions:
    
    @staticmethod
    def grab_frame_to_disk(imaging, file_path, file_format, settings) -> 'AdornedImage':
        # If the user didn't provide a file name, we throw because there is no way the large image can fit to RAM
        if file_path is None or file_path == "":
            raise ApiException(ApiErrorCode.APPLICATION_CLIENT_ERROR, "No valid file path was provided.")

        # If the user wants to save a tiff and didn't provide file extension, let's add it
        if file_format == ImageFileFormat.TIFF:
            if not file_path.endswith("tiff") and not file_path.endswith("tif"):
                file_path = file_path + ".tiff"

        # If the target file already exists, try to delete it
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception as ex:
                raise Exception("The file '" + file_path + "' already exists and couldn't be deleted.")

        # Invoke the large frame grab process on the server side
        large_image_header = imaging._grab_large_frame(file_format, settings)

        # The grabbed large image must have at least one part
        try:
            if large_image_header.part_count == 0:
                raise Exception("There was a problem retrieving image.")

            # Transfer file data from server to client and store it to the path the user provided
            with open(file_path, mode='wb') as f:
                for i in range(0, large_image_header.part_count):
                    image_part = imaging._get_large_image_part(large_image_header.image_id, i)
                    f.write(image_part)

        finally:
            # Inform the server it can clean up the large image file
            imaging._release_large_image(large_image_header.image_id)

        return large_image_header.preview

    @staticmethod
    def version_GET(client) -> 'str':
        return INFO_VERSIONLONG
