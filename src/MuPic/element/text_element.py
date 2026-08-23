from copy import deepcopy

from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont

from MuPic.element.border_helper import BorderHelper

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
    if "\n" in text :
        img = Image.new("L", (1, 1))
        draw = ImageDraw.Draw(img)
        box = draw.multiline_textbbox((0,0), text=text, font=font)
    else :
        box = font.getbbox(text)
    size = sizet(int(box[2]-box[0]), int(box[3]-box[1]))
    return size

#---------------------------------------------------------

class TextElement(ImageElement) :
    def __init__(self, name : str, text_settings : TextSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        self.settings = deepcopy(text_settings)

    def generate(self) -> None :
        cfg = self.settings
        
        logger.info(f"---- Text -- Adding {self.name} text")


        title_font = ImageFont.truetype(cfg.font, cfg.size)
        text_size = _get_text_size(cfg.text, title_font) + (cfg.gap * 2)

        if cfg.rotation in [90, -90]:
            final_text_size = sizet(text_size.height, text_size.width)
        else:
            final_text_size = text_size


        if cfg.border is not None :
            bh = BorderHelper(cfg.border, mode='add')
            border_img = bh.generate(rect(point(0,0), final_text_size))
            content_rec = bh.get_content_rect()
            logger.debug(f"Text -- content_rec before offsets = {content_rec}")
            full_rec = bh.get_border_rect()
        else :
            content_rec = rect(point(0,0), final_text_size)
            full_rec = rect(point(0,0), final_text_size)
            border_img = None

        offsets =  self.offsets_for_position(
            pos=cfg.position,
            elem_size=full_rec.extent
            )
        
        content_rec = content_rec.add_offsets(offsets)
        logger.debug(f"Text -- content_rec after offsets = {content_rec}")
        self.set_bbox('content', content_rec)
        full_rec = full_rec.add_offsets(offsets)
        logger.debug(f"Text -- full_rec after offsets = {full_rec}")
        self.set_bbox('full', full_rec)
        # If we add margin, this will need to change. But good for now.
        self.set_bbox('border', full_rec)
        self.set_bbox('paste', full_rec)

        if cfg.stroke is not None :
            assert isinstance(cfg.stroke.width, int)
            stroke_params = { 'stroke_fill' : cfg.stroke.color,
                            'stroke_width' : cfg.stroke.width }
        else :
            stroke_params = {}



        logger.debug(f"Text Position: {offsets}")

        color_params = {'color' : cfg.color} if cfg.color is not None else {}

        text_image = Image.new("RGBA", text_size.to_tuple(), **color_params)
        draw = ImageDraw.Draw(text_image)
        draw_offsets = (cfg.gap, cfg.gap)

        if "\n" in cfg.text:
            logger.debug(f"Text --- Drawing multiline text")
            draw.multiline_text(draw_offsets, cfg.text, font=title_font, fill=cfg.fill, **stroke_params)
        else :
            logger.debug(f"Text --- Drawing single line text")
            draw.text(draw_offsets, cfg.text, font=title_font, fill=cfg.fill, anchor='lt', **stroke_params)

        if cfg.rotation != 0 :
            text_image = text_image.rotate(-cfg.rotation, expand=1, resample=Image.Resampling.BILINEAR)

        if border_img is not None :
            border_img.paste(text_image, (content_rec.origin - offsets).to_tuple(), mask=text_image)
            final_image = border_img
            mask_image = border_img
        else :
            final_image = text_image
            mask_image = text_image


        self.bbox['content'] = content_rec
        self.bbox['full'] = rect(point(*offsets), final_text_size)
        self.generated = True
        self.main_image = final_image
        self.mask_image = mask_image

        logger.debug(f"---- End {self.name} text")
