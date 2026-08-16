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

        self.settings = deepcopy(text_settings)

    def generate(self) -> None :
        cfg = self.settings
        
        logger.info(f"Adding {self.name} text")


        title_font = ImageFont.truetype(cfg.font, cfg.size)
        text_size = _get_text_size(cfg.text, title_font) + (cfg.gap * 2)


        if cfg.rotation in [90, -90]:
            final_text_size = sizet(text_size.height, text_size.width)
        else:
            final_text_size = text_size

        offsets =  self.offsets_for_position(
            pos=cfg.position,
            elem_size=final_text_size
            )


        if cfg.stroke is not None :
            stroke_params = { 'stroke_fill' : cfg.stroke.color,
                            'stroke_width' : cfg.stroke.width }
        else :
            stroke_params = {}

        if "\n" in cfg.text:
            anchor_params = {}
        else :
            anchor_params = { 'anchor' : 'lt' }


        logger.debug(f"Text Position: {offsets}")

        color_params = {'color' : cfg.color} if cfg.color is not None else {}

        text_image = Image.new("RGBA", text_size.to_tuple(), **color_params)
        draw = ImageDraw.Draw(text_image)
        draw_offsets = (cfg.gap, cfg.gap)


        draw.text(draw_offsets, cfg.text, font=title_font, fill=cfg.fill, **anchor_params, **stroke_params)

        if cfg.rotation != 0 :
            text_image = text_image.rotate(-cfg.rotation, expand=1, resample=Image.Resampling.BILINEAR)

        self.parent.img.paste(text_image, offsets.to_tuple(), mask=text_image)


        self.bbox['content'] = rect(point(*offsets), final_text_size)
        self.bbox['full'] = rect(point(*offsets), final_text_size)
        self.generated = True
