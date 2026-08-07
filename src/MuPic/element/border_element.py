from copy import deepcopy   

from typing import TYPE_CHECKING

from PIL import Image

from src.MuPic.position import geom, rect
if TYPE_CHECKING:
    from ..music_image import MusicImage


from ..settings import BorderSettings
from .element import ImageElement

import logging
logger = logging.getLogger(__name__)


class BorderElement(ImageElement):
    def __init__(self, name : str, settings : BorderSettings, parent : 'MusicImage') :
        super().__init__(name, parent)
        self._settings = deepcopy(settings)
        self._settings.sides = ''.join(set(self._settings.sides.lower()))

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
            extent = geom(self._settings.width, self.bbox.extent.height)
            
        elif side == 'r' :
            start = geom(self.bbox.start.width + self.bbox.extent.width - self._settings.width, self.bbox.start.height)
            extent = geom(self._settings.width, self.bbox.extent.height)

        elif side == 't' :
            start = geom(self.bbox.start.width, self.bbox.start.height)
            extent = geom(self.bbox.extent.width, self._settings.width)

        elif side == 'b' :
            start = geom(self.bbox.start.width, self.bbox.start.height + self.bbox.extent.height - self._settings.width)
            extent = geom(self.bbox.extent.width, self._settings.width)

        bbox = rect(start, extent)
    
        return bbox

    def generate(self, size_rect : rect) -> Image.Image :
        logger.debug(f"--- Generating border rect = {size_rect.to_tuple()}")
        self.bbox = size_rect.copy()
        return Image.new("RGB", size_rect.extent.to_tuple(), color=self._settings.color)

    def get_cover_rect(self) -> rect :
        start = self.bbox.start.copy()
        extent = self.bbox.extent.copy()
        for side in self._settings.sides :
            if side == 'l':
                start.width += self._settings.width
                extent.width -= self._settings.width
            elif side == 'r' :
                extent.width -= self._settings.width
            elif side == 't' :
                start.height += self._settings.width
                extent.height -= self._settings.width
            elif side == 'b' :
                extent.height -= self._settings.width
            else :
                raise ValueError(f"Invalid side: {side}")

        return rect(start, extent)       
