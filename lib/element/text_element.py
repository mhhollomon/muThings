from copy import deepcopy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..music_image import MusicImage


from .element import ImageElement
from ..settings import TextSettings

class TextElement(ImageElement) :
    def __init__(self, name : str, text_settings : TextSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        self._settings = deepcopy(text_settings)