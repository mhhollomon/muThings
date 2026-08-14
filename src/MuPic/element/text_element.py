from copy import deepcopy

from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from ..music_image import MusicImage


from .element import ImageElement
from ..settings import TextSettings
from ..geometry import sizet, rect, point

import logging
logger = logging.getLogger(__name__)

#---------------------------------------------------------

def _get_text_size(text : str, font : ImageFont.FreeTypeFont) -> sizet:
    # Using ImageFont.getbbox is not good enough for multiline text
    img = Image.new("L", (1, 1))
    draw = ImageDraw.Draw(img)
    box = draw.multiline_textbbox((0,0), text=text, font=font)
    size = sizet(int(box[2]-box[0]), int(box[3]-box[1]))
    return size

#---------------------------------------------------------

class TextElement(ImageElement) :
    def __init__(self, name : str, text_settings : TextSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        self._settings = deepcopy(text_settings)

    def generate(self) -> None :
        if not self._settings.has_text():
            logger.info(f"Skipping {self.name} text")
            return
        
        logger.info(f"Adding {self.name} text")

        output_size = self.parent.output_size

        title_font = ImageFont.truetype(self._settings.font, self._settings.size)
        text_size = _get_text_size(self._settings.text, title_font)

        gutter = 10

        if output_size.is_landscape() and not output_size.is_square():
            max_text_width = output_size.width - output_size.height - (gutter * 2)
        else:
            max_text_width = output_size.width - (gutter * 2)

        if (text_size.width > max_text_width):
            # TODO : Need to retink this. What should max_text_width be?
            # The text is too long, so we need to scale it down
            new_size = self._settings.size * (max_text_width / text_size.width)
            logger.debug(f"Scaling text size from {self._settings.size} to {new_size}")
            title_font = ImageFont.truetype(self._settings.font, new_size)
            text_size = _get_text_size(self._settings.text, title_font)

        if self._settings.rotation in [90, -90]:
            final_text_size = sizet(text_size.height, text_size.width)
        else:
            final_text_size = text_size

        position = self._settings.position
        offsets =  self.offsets_for_position(
            pos=position,
            elem_size=final_text_size,
            gutter=10
            )


        if self._settings.stroke is not None :
            stroke_params = { 'stroke_fill' : self._settings.stroke.color,
                            'stroke_width' : self._settings.stroke.width }
        else :
            stroke_params = {}

        if "\n" in self._settings.text:
            anchor_params = {}
        else :
            anchor_params = { 'anchor' : 'lt' }


        logger.debug(f"Text Position: {offsets}")

        text_image = None

        if self._settings.rotation == 0 :
            draw = ImageDraw.Draw(self.parent.img)
            draw_offsets = offsets

        else :
            text_image = Image.new("RGBA", text_size.to_tuple())
            draw = ImageDraw.Draw(text_image)
            draw_offsets = (0,0)

        draw.text(draw_offsets, self._settings.text, font=title_font, fill=self._settings.fill, **anchor_params, **stroke_params)

        if text_image is not None:
            text_image = text_image.rotate(-self._settings.rotation, expand=1, resample=Image.Resampling.BILINEAR)
            self.parent.img.paste(text_image, offsets, mask=text_image)


        self.bbox = rect(point(*offsets), final_text_size)
