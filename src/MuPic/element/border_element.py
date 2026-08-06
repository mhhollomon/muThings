from copy import deepcopy   

from typing import TYPE_CHECKING

from src.MuPic.position import geometry, rectangle
if TYPE_CHECKING:
    from ..music_image import MusicImage


from ..settings import BorderSettings
from .element import ImageElement


class BorderElement(ImageElement):
    def __init__(self, name : str, settings : BorderSettings, parent : 'MusicImage') :
        super().__init__(name, parent)
        self._settings = deepcopy(settings)

    def get_bbox(self, **kwargs) :
        """
        Returns the element's bbox depending on the side. 
        """
        if 'side' not in kwargs :
            raise ValueError("Must specify a side for border bbox")

        side = kwargs['side']
        if side not in self._settings.sides :
            raise ValueError(f"Invalid side for border bbox: {side}")

        if side == 'l' :
            start = self.bbox.start
            extent = geometry(self._settings.width, self.bbox.extent.height)
            
        elif side == 'r' :
            start = geometry(self.bbox.start.width + self.bbox.extent.width - self._settings.width, self.bbox.start.height)
            extent = geometry(self._settings.width, self.bbox.extent.height)

        elif side == 't' :
            start = geometry(self.bbox.start.width, self.bbox.start.height)
            extent = geometry(self.bbox.extent.width, self._settings.width)

        elif side == 'b' :
            start = geometry(self.bbox.start.width, self.bbox.start.height + self.bbox.extent.height - self._settings.width)
            extent = geometry(self.bbox.extent.width, self._settings.width)

        bbox = rectangle(start, extent)
    
        return bbox
