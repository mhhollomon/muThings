from copy import deepcopy   

from typing import TYPE_CHECKING

from PIL import Image

from ..utils import clamped_mask

from ..geometry import sizet, rect, point

if TYPE_CHECKING:
    from ..music_image import MusicImage


from ..settings import BorderSettings

import logging
logger = logging.getLogger(__name__)


class BorderHelper:
    def __init__(self, settings : BorderSettings, mode : str = 'subtract') :
        self.settings = deepcopy(settings)
        self.mode = mode

        self.border_bbox = None


    def generate(self, size_rect : rect) -> Image.Image :
        logger.debug(f"--- Generating border rect = {size_rect} mode = {self.mode}")

        ws = self.settings.width

        if self.mode == 'subtract':
            self.border_bbox = size_rect
            origin = self.border_bbox.origin + (ws.l, ws.t)
            extent = self.border_bbox.extent - (ws.l + ws.r, ws.t + ws.b)
            self.content_bbox = rect(origin, extent)

        elif self.mode == 'add':
            origin = point(0, 0)
            extent = size_rect.extent + (ws.l + ws.r, ws.t + ws.b)

            new_content_origin = size_rect.origin + (ws.l, ws.t)
            self.content_bbox = rect(new_content_origin, size_rect.extent)

            self.border_bbox = rect(origin, extent)
        else :
            raise ValueError(f"Invalid BorderHelper mode {self.mode}")

        img = Image.new("RGB", self.border_bbox.extent.to_tuple(), color=self.settings.color)
        content_img = Image.new("L", self.content_bbox.extent.to_tuple(), color='black')
        origin_on_border = point(ws.l, ws.t)
        img.paste(content_img, origin_on_border.to_tuple())

        alpha = clamped_mask(img)
        logger.debug(f"alpha mode = {alpha.mode}")
        img.putalpha(alpha)

        return img

    def get_content_rect(self) -> rect :
        if self.border_bbox is None:
            raise ValueError("BorderHelper -- get_content_rect called before generate")
        return self.content_bbox
    
    def get_border_rect(self) -> rect :
        if self.border_bbox is None:
            raise ValueError("BorderHelper -- get_content_rect called before generate")
        return self.border_bbox
        
