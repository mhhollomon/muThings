from typing import TYPE_CHECKING

from .element import ImageElement

if TYPE_CHECKING:
    from ..music_image import MusicImage


class BBoxElement(ImageElement):
    """This element simply represents a area in the image.
    It does not have any content.
    """
    def __init__(self, name : str, parent : 'MusicImage') :
        super().__init__(name, parent)

    # bbox and get_bbox are inherited.
