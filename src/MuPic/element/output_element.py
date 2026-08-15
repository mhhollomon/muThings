from copy import deepcopy

from PIL import Image

from typing import TYPE_CHECKING



if TYPE_CHECKING:
    from ..music_image import MusicImage

from .element import ImageElement
from .border_helper import BorderHelper

from ..settings import OutputSettings, WidthSettings
from ..geometry import  rect, point


import logging
logger = logging.getLogger(__name__)

class OutputElement(ImageElement) :
    def __init__(self, name : str, output_settings : OutputSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        self.settings  = output_settings

    def border_widths(self) -> WidthSettings | None :
        b = self.settings.border
        return None if b is None else b.width

    def margin_widths(self) -> WidthSettings | None:
        m = self.settings.margin
        return None if m < 1 else WidthSettings(m, m, m, m)
    
    def generate(self) -> Image.Image :

        full_output_size = self.settings.size
        full_bbox = rect(point(0,0), full_output_size)
        self.set_bbox('full', full_bbox)

        output_size = full_output_size
        output_offset = point(0,0)

        if self.settings.background is not None and self.settings.fit == 'cover':
            output_img = Image.open(self.settings.background)
            output_img = output_img.resize(full_output_size.to_tuple())
        else :
            output_img = Image.new("RGB", full_output_size.to_tuple(), color=self.settings.color)

        if self.settings.margin > 0 :
            # Calculate the border_bbox
            output_size = output_size - self.settings.margin * 2
            output_offset += self.settings.margin
            self.set_bbox('margin', full_bbox)
            
        border_size = output_size
        logger.debug(f"border size = {border_size}")

        if self.settings.border is not None :
            bh = BorderHelper(self.settings.border)

            border_img = bh.generate(rect(output_offset, output_size))
            self.set_bbox('border', rect(output_offset, output_size))

            content_bbox = bh.get_content_rect()

            output_img.paste(border_img, output_offset.to_tuple(), mask=border_img)
        else :
            content_bbox = rect(output_offset, output_size)

        self.set_bbox('content', content_bbox)

        if self.settings.background is not None and self.settings.fit == 'contain':

            logger.info("Adding background image")
            bg_img = Image.open(self.settings.background)
            if bg_img.mode != 'RGB':
                bg_img = bg_img.convert('RGB')

            bg_img = bg_img.resize(content_bbox.extent.to_tuple())
            output_img.paste(bg_img, content_bbox.origin.to_tuple())

        self.generated = True


        return output_img
