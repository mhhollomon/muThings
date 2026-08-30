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
    DBGCATEGORY = 'Text'
    LOGGER = logger

    def __init__(self, name : str, text_settings : TextSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        self.settings = deepcopy(text_settings)

        self.bh : BorderHelper | None = None

    #-----------------------------------------------------
    # LAYOUT
    #-----------------------------------------------------
    def layout(self) :
        """Compute all the bboxen"""

        cfg = self.settings
        self._debug(f"START Layout")

        self.title_font = ImageFont.truetype(cfg.font, cfg.size)
        self.unrotated_text_size = _get_text_size(cfg.text, self.title_font) + (cfg.gap * 2)

        if cfg.rotation in [90, -90]:
            final_text_size = sizet(self.unrotated_text_size.height, self.unrotated_text_size.width)
        else:
            final_text_size = self.unrotated_text_size

        if cfg.color :
            self.text_bg_color = cfg.color
        else :
            self.text_bg_color = self.parent.get_elem('output').settings.color # type: ignore

        if cfg.border is not None :
            self.bh = BorderHelper(cfg.border, cfg.name, mode='add')

            self.bh.layout(rect(point(0,0), final_text_size))
            content_rec = self.bh.get_content_rect()
            self._debug("content_rec before offsets = {content_rec}")
            full_rec = self.bh.get_border_rect()
        else :
            content_rec = rect(point(0,0), final_text_size)
            full_rec = rect(point(0,0), final_text_size)

        self.offsets =  self.offsets_for_position(
            pos=cfg.position,
            elem_size=full_rec.extent
            )
        
        content_rec = content_rec.add_offsets(self.offsets)
        logger.debug(f"Text -- content_rec after offsets = {content_rec}")

        # --- CONTENT
        self.set_bbox('content', content_rec)

        full_rec = full_rec.add_offsets(self.offsets)
        logger.debug(f"Text -- full_rec after offsets = {full_rec}")

        # --- FULL
        self.set_bbox('full', full_rec)

        # --- BORDER
        # If we add margin, this will need to change. But good for now.
        self.set_bbox('border', full_rec)

        ## -- PASTE
        self.set_bbox('paste', full_rec)

        self.layout_done = True
        self._debug("END layout")

    #-----------------------------------------------------
    # RENDER
    #-----------------------------------------------------
    def render(self, output_img : Image.Image) -> Image.Image :

        logger.info(f"Adding text {self.name}")

        cfg = self.settings
        self._debug(f"START Render")

        if not self.layout_done :
            raise RuntimeError(f"Layout not called before render on {self.name}")

        full_bbox = self.get_bbox('full')
        content_bbox = self.get_bbox('content')

        ## Background color
        if cfg.color :
            color_params = {'color' : cfg.color}
            # No mask since this is supposed to be a solid background color.
            bg = Image.new("RGB", full_bbox.extent.to_tuple(), 
                           **color_params)
            self._debug(f"pasting color bg at {full_bbox.origin.to_tuple()}")
            output_img.paste(bg, full_bbox.origin.to_tuple())
        else :
            self._debug("No background color")
            color_params = {}


        ## Text
        if cfg.stroke is not None :
            assert isinstance(cfg.stroke.width, int)
            stroke_params = { 'stroke_fill' : cfg.stroke.color,
                            'stroke_width' : cfg.stroke.width }
        else :
            stroke_params = {}

        # TODO : Allow masking on text
        text_img = Image.new("RGBA", self.unrotated_text_size.to_tuple(), 
                           **color_params)
        text_draw = ImageDraw.Draw(text_img)
        draw_offsets = (cfg.gap, cfg.gap)
        anchor_params = {'anchor' : 'lt'} if "\n" not in cfg.text else {}
        text_draw.text(draw_offsets, cfg.text, font=self.title_font, 
                       fill=cfg.fill, **anchor_params, **stroke_params)
        if cfg.rotation != 0 :
            self._debug(f"Rotating text by {cfg.rotation} degrees")
            text_img = text_img.rotate(cfg.rotation, expand=1, resample=Image.Resampling.BILINEAR)

        self._debug(f"pasting text at {content_bbox.origin.to_tuple()}")
        output_img.paste(text_img, content_bbox.origin.to_tuple(), mask=text_img)

        ## Border
        if cfg.has_border() :
            assert cfg.border is not None
            assert self.bh is not None
            border_img = self.bh.generate()
            border_bbox = self.bh.get_border_rect()
            if border_img is not None:
                self._debug(f"pasting border at {border_bbox.origin.to_tuple()}")
                output_img.paste(border_img, border_bbox.origin.to_tuple(), mask=border_img )

        self._debug("END render")
        return output_img
