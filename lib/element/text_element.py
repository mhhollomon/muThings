from copy import deepcopy

from typing import TYPE_CHECKING

from PIL import ImageDraw, ImageFont

if TYPE_CHECKING:
    from ..music_image import MusicImage


from .element import ImageElement
from ..settings import TextSettings
from ..position import geometry, rectangle

import logging
logger = logging.getLogger(__name__)

#---------------------------------------------------------

def _get_text_size(text : str, font : ImageFont.FreeTypeFont) -> geometry:

    box = font.getbbox(text)
    size = geometry(int(box[2]-box[0]), int(box[3]-box[1]))
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

        draw = ImageDraw.Draw(self.parent.img)
        title_font = ImageFont.truetype(self._settings.font, self._settings.size)
        text_size = _get_text_size(self._settings.text, title_font)

        gutter = self.parent.config.globals.gutter

        if output_size.is_landscape() and not output_size.is_square():
            max_text_width = output_size.width - output_size.height - (gutter * 2)
        else:
            max_text_width = output_size.width - (gutter * 2)

        if (text_size.width > max_text_width):
            # The text is too long, so we need to scale it down
            new_size = self._settings.size * (max_text_width / text_size.width)
            title_font = ImageFont.truetype(self._settings.font, new_size)
            text_size = _get_text_size(self._settings.text, title_font)

        position = self._settings.position
        offsets =  self.offsets_for_position(
            pos=position,
            elem_size=text_size,
            gutter=self.parent.config.globals.gutter
            )


        if self._settings.stroke.exists():
            stroke_params = { 'stroke_fill' : self._settings.stroke.color,
                            'stroke_width' : self._settings.stroke.width }
        else :
            stroke_params = {}

        logger.debug(f"Text Position: {offsets}")
        if "\n" in self._settings.text:
            draw.multiline_text(offsets, self._settings.text, font=title_font, fill=self._settings.fill, **stroke_params)
        else :
            draw.text(offsets, self._settings.text, font=title_font, fill=self._settings.fill, anchor='lt', **stroke_params)

        self.bbox = rectangle(geometry(*offsets), text_size)
