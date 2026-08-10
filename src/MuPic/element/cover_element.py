from copy import deepcopy

from typing import TYPE_CHECKING

from PIL import Image, ImageOps

if TYPE_CHECKING:
    from ..music_image import MusicImage

from ..settings import *
from ..geometry import rect, point

from .element import ImageElement
from .border_element import BorderElement

import logging
logger = logging.getLogger(__name__)

#---------------------------------------------------------

class CoverElement(ImageElement) :
    def __init__(self, name : str, settings : CoverSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        self._settings = deepcopy(settings)

    def generate(self) -> None :

        cfg : CoverSettings = self._settings

        if not cfg.path_valid() :
            logger.info("Skipping cover")
            return

        logger.info("Adding cover")
        output_size = self.parent.output_size

        fit = cfg.fit if not output_size.is_square() else 'cover'

        if fit == 'cover' :
            full_cover_size = self.parent.output_size
            full_cover_offset = point(0, 0)
        else :
            square_side = min(self.parent.output_size.width, self.parent.output_size.height)
            full_cover_size = sizet(square_side, square_side)
            if cfg.align == 'min':
                full_cover_offset = point(0, 0)
            elif cfg.align == 'mid':
                if output_size.is_landscape():
                    full_cover_offset = point((self.parent.output_size.width - square_side) // 2, 0)
                else:
                    full_cover_offset = point(0, (self.parent.output_size.height - square_side) // 2)
            elif cfg.align == 'max':
                if output_size.is_landscape():
                    full_cover_offset = point(self.parent.output_size.width - square_side, 0)
                else:
                    full_cover_offset = point(0, self.parent.output_size.height - square_side)
            else:
                raise Exception(f"Invalid cover alignment: {cfg.align}")

        
        border_size = full_cover_size - cfg.margin * 2
        border_offset = full_cover_offset + point(cfg.margin, cfg.margin)

        border_ele = BorderElement('border', cfg.border, self.parent)
        border_img = border_ele.generate(rect(border_offset,border_size))

        self.parent.img.paste(border_img, border_offset.to_tuple())

        cover_rect = border_ele.get_cover_rect()
        cover_size = cover_rect.extent
        logger.debug(f"calculated cover size = {cover_size.to_tuple()}")
        logger.debug(f"Calculated cover offsets = {cover_rect.start.to_tuple()}")

        cover_img = Image.open(cfg.path)
        cover_img_size = sizet(cover_img.size)

        if cover_img_size.is_landscape() :
            if cfg.crop == 'min':
                centering = (0, 0)
            elif cfg.crop == 'mid':
                centering = (0.5, 0)
            elif cfg.crop == 'max':
                centering = (1, 0)
            else:
                raise Exception(f"Invalid cover crop: {cfg.crop}")
        else :
            if cfg.crop == 'min':
                centering = (0, 0)
            elif cfg.crop == 'mid':
                centering = (0, 0.5)
            elif cfg.crop == 'max':
                centering = (0, 1)
            else:
                raise Exception(f"Invalid cover crop: {cfg.crop}")
        cover_img = ImageOps.fit(cover_img, size = cover_size.to_tuple(), centering = centering)

        self.parent.img.paste(cover_img, cover_rect.start.to_tuple())
