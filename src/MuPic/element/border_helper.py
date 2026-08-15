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
    def __init__(self, settings : BorderSettings) :
        self.settings = deepcopy(settings)


    def generate(self, size_rect : rect) -> Image.Image :
        logger.debug(f"--- Generating border rect = {size_rect.to_tuple()}")
        self.border_bbox = size_rect
        self.content_bbox = self.get_content_rect()
        img = Image.new("RGB", size_rect.extent.to_tuple(), color=self.settings.color)
        content_img = Image.new("L", self.content_bbox.extent.to_tuple(), color='black')
        ws = self.settings.width
        origin_on_border = point(ws.l, ws.t)
        img.paste(content_img, origin_on_border.to_tuple())

        alpha = clamped_mask(img)
        logger.debug(f"alpha mode = {alpha.mode}")
        img.putalpha(alpha)

        return img

    def get_content_rect(self) -> rect :
        ws = self.settings.width
        logger.debug(f"BorderHelper -- ws = {ws}")
        origin = self.border_bbox.origin + (ws.l, ws.t)
        logger.debug(f"BorderHelper -- content origin = {origin}")
        extent = self.border_bbox.extent - (ws.l + ws.r, ws.t + ws.b)
        logger.debug(f"BorderHelper -- content extent = {extent}")

        return rect(origin, extent)       
