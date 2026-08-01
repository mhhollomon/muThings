from copy import deepcopy

from .element import ImageElement
from ..settings import TextSettings

class TextElement(ImageElement) :
    def __init__(self, name : str, text_settings : TextSettings) :
        super().__init__(name)

        self._settings = deepcopy(text_settings)