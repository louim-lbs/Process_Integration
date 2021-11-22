from PIL import Image


class TiffImageLoader:
    """
    TiffImageLoader allows loading large TIFF images.
    """
    def open_image(self, path: str):
        """
        Bypasses PIL's image size limit to load larger images.
        """

        max_pixels = Image.MAX_IMAGE_PIXELS
        try:
            Image.MAX_IMAGE_PIXELS = None
            return Image.open(path)
        finally:
            Image.MAX_IMAGE_PIXELS = max_pixels
