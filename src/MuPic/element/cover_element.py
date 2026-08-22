from copy import deepcopy

from typing import TYPE_CHECKING

from PIL import Image, ImageOps

if TYPE_CHECKING:
    from ..music_image import MusicImage

from ..settings import *
from ..geometry import rect, point

from .element import ImageElement
from .border_helper import BorderHelper

import logging
logger = logging.getLogger(__name__)

#---------------------------------------------------------

class CoverElement(ImageElement) :
    def __init__(self, name : str, settings : CoverSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        self.settings = deepcopy(settings)

    def generate(self) -> None :

        cfg : CoverSettings = self.settings

        output_rect = self.parent.elements['output'].get_bbox('content')
        output_size = output_rect.extent
        output_origin = output_rect.origin

        logger.info("Adding cover")

        fit = cfg.fit if not output_size.is_square() else 'cover'

        if fit == 'cover' :
            # size of the cover including the border and margin
            full_cover_size = output_size
            # origin of the cover including the border and margin
            # This is where we will paste into the output image
            full_cover_origin = output_rect.origin
        else :
            square_side = min(output_size.width, output_size.height)
            full_cover_size = sizet(square_side, square_side)
            if cfg.align == 'min':
                full_cover_origin = output_origin
            elif cfg.align == 'mid':
                if output_size.is_landscape():
                    full_cover_origin =  output_origin + point((output_size.width - square_side) // 2, 0)
                else:
                    full_cover_origin = output_origin +point(0, (output_size.height - square_side) // 2)
            elif cfg.align == 'max':
                if output_size.is_landscape():
                    full_cover_origin = output_origin + point(output_size.width - square_side, 0)
                else:
                    full_cover_origin = output_origin + point(0, output_size.height - square_side)
            else:
                raise Exception(f"Invalid cover alignment: {cfg.align}")

        if cfg.margin > 0 :
            self.set_bbox('margin', rect(full_cover_origin, full_cover_size))

            border_size = full_cover_size - cfg.margin * 2
            border_offset = full_cover_origin + point(cfg.margin, cfg.margin)
        else :
            border_size = full_cover_size
            border_offset = full_cover_origin

        if cfg.border is not None :
            border_helper = BorderHelper(cfg.border)
            border_img = border_helper.generate(rect(border_offset,border_size))

            self.set_bbox('border', rect(border_offset, border_size))
            self.set_bbox('content', border_helper.get_content_rect())

            self.parent.img.paste(border_img, border_offset.to_tuple(), mask=border_img)

            cover_rect = border_helper.get_content_rect()
            cover_size = cover_rect.extent
            logger.debug(f"calculated cover size = {cover_size.to_tuple()}")
            logger.debug(f"Calculated cover offsets = {cover_rect.origin.to_tuple()}")
        else :
            cover_rect = rect(full_cover_origin, full_cover_size)
            cover_size = cover_rect.extent
            logger.debug(f"calculated cover size = {cover_size.to_tuple()}")
            logger.debug(f"Calculated cover offsets = {cover_rect.origin.to_tuple()}")

        if cfg.path is not None :

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
        else :
            cover_img = Image.new('RGB', cover_size.to_tuple(), cfg.color)

        self.parent.img.paste(cover_img, cover_rect.origin.to_tuple())
        self.generated = True
