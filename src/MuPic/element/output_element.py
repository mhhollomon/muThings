from copy import deepcopy

from PIL import Image

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..music_image import MusicImage

from .bbox_element import BBoxElement
from .element import ImageElement

from ..settings import OutputSettings
from ..geometry import  rect, point


import logging
logger = logging.getLogger(__name__)

class OutputElement(ImageElement) :
    def __init__(self, name : str, output_settings : OutputSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        # Not sure why I need to force the typing.
        self.settings : OutputSettings = output_settings

    def generate(self) -> Image.Image :

        full_output_size = self.settings.size
        output_size = full_output_size
        output_offset = point(0,0)

        if self.settings.background is not None and self.settings.fit == 'cover':
            output_img = Image.open(self.settings.background)
            output_img = output_img.resize(full_output_size.to_tuple())
        else :
            output_img = Image.new("RGB", full_output_size.to_tuple(), color=self.settings.color)

        if self.settings.margin > 0 :
            output_size = output_size - self.settings.margin * 2
            output_offset += self.settings.margin
            
        border_size = output_size
        logger.debug(f"border size = {border_size}")

        if self.settings.border is not None :
            logger.info("Adding output border")
            w = self.settings.border.width
            logger.debug(f"Pre border size = {output_size}")
            output_size -=  (w.l+w.r, w.t+w.b)
            border_offset = point(self.settings.margin, self.settings.margin)
            output_offset += (w.l, w.t)
            logger.debug(f"Post border size = {output_size}")

            border_img = Image.new("RGB", border_size.to_tuple(), color=self.settings.border.color)

            black_img = Image.new("RGB", output_size.to_tuple(), color='black')
            border_img.paste(black_img, (w.l, w.t))
            mask_image = border_img.convert('L').point(lambda x : 0 if x < 10 else 255) # type: ignore

            output_img.paste(border_img, border_offset.to_tuple(), mask=mask_image)

        if self.settings.background is not None and self.settings.fit == 'contain':

            logger.info("Adding background image")
            bg_img = Image.open(self.settings.background)
            if bg_img.mode != 'RGB':
                bg_img = bg_img.convert('RGB')

            bg_img = bg_img.resize(output_size.to_tuple())
            output_img.paste(bg_img, output_offset.to_tuple())

        self.bbox = rect(output_offset, output_size)

        dummy = BBoxElement('full_output', self.parent)
        dummy.bbox = rect(point(0,0), full_output_size)

        return output_img
