from copy import deepcopy   

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..music_image import MusicImage


from ..settings import BorderSettings
from .element import ImageElement


class BorderElement(ImageElement):
    def __init__(self, name : str, settings : BorderSettings, parent : 'MusicImage') :
        super().__init__(name, parent)
        self._settings = deepcopy(settings)