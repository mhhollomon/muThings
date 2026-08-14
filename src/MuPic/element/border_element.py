from copy import deepcopy   

from typing import TYPE_CHECKING

from PIL import Image

from ..geometry import sizet, rect, point

if TYPE_CHECKING:
    from ..music_image import MusicImage


from ..settings import BorderSettings
from .element import ImageElement

import logging
logger = logging.getLogger(__name__)


class BorderElement(ImageElement):
    def __init__(self, name : str, settings : BorderSettings, parent : 'MusicImage') :
        super().__init__(name, parent)
        self.settings = deepcopy(settings)

    def get_bbox(self, **kwargs) :
        """
        Returns the element's bbox depending on the side. 
        """
        if 'side' not in kwargs :
            raise ValueError("Must specify a side for border bbox")

        side = kwargs['side']
        if side not in 'lrtb' :
            raise ValueError(f"Invalid side for border bbox: {side}")

        if side == 'l' :
            start = self.bbox.origin
            extent = sizet(self.settings.width.l, self.bbox.extent.height)
            
        elif side == 'r' :
            start = point(self.bbox.origin.x + self.bbox.extent.width - self.settings.width.r, self.bbox.origin.y)
            extent = sizet(self.settings.width.r, self.bbox.extent.height)

        elif side == 't' :
            start = point(self.bbox.origin.x, self.bbox.origin.y)
            extent = sizet(self.bbox.extent.width, self.settings.width.t)

        elif side == 'b' :
            start = point(self.bbox.origin.x, self.bbox.origin.y + self.bbox.extent.height - self.settings.width.b)
            extent = sizet(self.bbox.extent.width, self.settings.width.b)

        bbox = rect(start, extent)
    
        return bbox

    def generate(self, size_rect : rect) -> Image.Image :
        logger.debug(f"--- Generating border rect = {size_rect.to_tuple()}")
        self.bbox = size_rect.copy()
        return Image.new("RGB", size_rect.extent.to_tuple(), color=self.settings.color)

    def get_cover_rect(self) -> rect :
        ws = self.settings.width
        start = self.bbox.origin.copy() + (ws.l, ws.t)
        extent = self.bbox.extent.copy() - (ws.l + ws.r, ws.t + ws.b)

        return rect(start, extent)       
