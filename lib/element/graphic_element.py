from copy import deepcopy
from .element import ImageElement
from ..settings import GraphicSettings

class GraphicElement(ImageElement):
    def __init__(self, name : str, graphic_settings : GraphicSettings) :
        super().__init__(name)

        self._settings = deepcopy(graphic_settings)