from autoscript_sdb_microscope_client.enumerations import ImageFileFormat
from autoscript_sdb_microscope_client.structures import AdornedImage
from autoscript_core.common import ApiException, ApiErrorCode
from autoscript_sdb_microscope_client.build_information import *
import os
import cv2


class SdbMicroscopeClientExtensions:
    @staticmethod
    def grab_frame_to_disk(imaging, file_path, file_format=None, settings=None) -> 'AdornedImage':
        if file_path is None or file_path == "":
            raise ApiException(ApiErrorCode.APPLICATION_CLIENT_ERROR, "Invalid file path was provided.")

        if file_format is None:
            file_format = ImageFileFormat.TIFF

        if file_format == ImageFileFormat.TIFF:
            if not file_path.endswith("tiff") and not file_path.endswith("tif"):
                file_path = file_path + ".tiff"
        elif file_format == ImageFileFormat.RAW:
            if not file_path.endswith("raw"):
                file_path = file_path + ".raw"
        else:
            raise ApiException(ApiErrorCode.APPLICATION_CLIENT_ERROR, "Invalid file format was provided.")

        resolution_specified = settings is not None and settings.resolution is not None
        image = None

        if not resolution_specified:
            # Imaging without specified resolution will use resolution of active beam in active view
            image = imaging.grab_frame(settings)
        else:
            width, height = SdbMicroscopeClientExtensions.__parse_resolution(settings.resolution)

            is_small_resolution = width <= 6144 and height <= 6144
            if is_small_resolution:
                # Imaging in small resolutions is routed through grab_frame() to avoid using big snapshot imaging technique for
                # standard imaging resolutions. This would cause file transfer overhead and unnecessarily limit the applicable settings.
                # Note that even grab_frame() uses big snapshot for non-standard resolutions, so the settings constraints may still apply.
                image = imaging.grab_frame(settings)

        if image is not None:
            # Save the image to disk, note that AdornedImage.save() does not support Raw format yet
            if file_format == ImageFileFormat.TIFF:
                image.save(file_path)
            else:
                SdbMicroscopeClientExtensions.__save_image_as_raw(image, file_path)

            # And return the preview image, potentially resizing it first to the specified preview resolution
            preview_resolution_specified = settings is not None and settings.preview_resolution is not None
            if preview_resolution_specified:
                preview_width, preview_height = SdbMicroscopeClientExtensions.__parse_resolution(settings.preview_resolution)

                if settings.reduced_area is not None:
                    preview_width = int(preview_width * settings.reduced_area.width)
                    preview_height = int(preview_height * settings.reduced_area.height)

                if image.width != preview_width and image.height != preview_height:
                    resized_data = cv2.resize(image.data, (preview_width, preview_height))
                    return AdornedImage(resized_data, image.metadata)

            return image

        # Since the specified resolution is above 6k threshold, we will use the big snapshot imaging technique.
        # The file is first created on the microscope computer and then transferred in parts to the client.
        # File transfer overhead occurs and settings limitations apply.

        SdbMicroscopeClientExtensions.__delete_file_if_exists(file_path)

        # Invoke the large frame grab process on the server side
        large_image_header = imaging._grab_large_frame(file_format, settings)

        # The grabbed large image must have at least one part
        try:
            if large_image_header.part_count == 0:
                raise Exception("There was a problem retrieving image.")

            # Transfer file data from server to client and store it to the path the user provided
            with open(file_path, mode='wb') as file:
                for i in range(0, large_image_header.part_count):
                    image_part = imaging._get_large_image_part(large_image_header.image_id, i)
                    file.write(image_part)
        finally:
            # Inform the server it can clean up the large image file
            imaging._release_large_image(large_image_header.image_id)

        return large_image_header.preview

    @staticmethod
    def __delete_file_if_exists(file_path):
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return
        try:
            os.remove(file_path)
        except Exception:
            raise ApiException(ApiErrorCode.APPLICATION_CLIENT_ERROR, "The file '" + file_path + "' already exists and couldn't be deleted.")

    @staticmethod
    def __parse_resolution(resolution) -> (int, int):
        try:
            parts = resolution.split('x')
            if len(parts) == 2:
                width = int(parts[0])
                height = int(parts[1])
                return width, height
        except:
            pass

        raise ApiException(ApiErrorCode.APPLICATION_CLIENT_ERROR, f"Specified resolution '{resolution}' is not in WIDTHxHEIGHT format.") from None

    @staticmethod
    def __save_image_as_raw(image: AdornedImage, file_path: str):
        image.data.tofile(file_path, "", "")

    @staticmethod
    def version_GET(client) -> 'str':
        return INFO_VERSIONLONG
