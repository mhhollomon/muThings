from copy import deepcopy

from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from ..music_image import MusicImage

from ..settings import *
from ..paths import resolve_path
from ..position import rectangle

from .element import ImageElement
from .border_element import BorderElement

import logging
logger = logging.getLogger(__name__)

#---------------------------------------------------------

class CoverElement(ImageElement) :
    def __init__(self, name : str, settings : CoverSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        self._settings = deepcopy(settings)

    def _cover_square(self, ornt : int) -> Image.Image :
        cover_cfg = self._settings

        def other(o : int) -> int :
            return 1 - o

        required_size = self.parent.config.output.size
        cover_side = required_size[ornt]
        logger.debug(f"Cover side: {cover_side}")
        crop = cover_cfg.crop
        bg_color = cover_cfg.color

        cover_img = Image.open(resolve_path(cover_cfg.path))


        original_width, original_height = cover_img.size
        logger.debug(f"Original size: {original_width}x{original_height}")
        aspect_ratio = cover_img.size[other(ornt)] / cover_img.size[ornt]

        # Calculate the new height while keeping the aspect ratio
        new_dimension = int(cover_side * aspect_ratio)
        logger.debug(f"Aspect ratio: {aspect_ratio}, new dimension: {new_dimension}")

        new_size = [0, 0]
        new_size[ornt] = cover_side
        new_size[other(ornt)] = new_dimension

        logger.debug(f"New size: {new_size}")
        # Resize the image
        cover_img = cover_img.resize(new_size)

        # Crop the image if necessary
        if new_dimension > cover_side:
            if crop == 'min':
                offset = 0
            elif crop == 'mid':
                offset = (new_dimension - cover_side) // 2
            elif crop == 'max':
                offset = (new_dimension - cover_side)
            else :
                raise ValueError(f"Invalid crop value: {crop}")

            if ornt :
                box = (offset, 0, cover_side + offset, cover_side)
            else :
                box = (0, offset, cover_side, cover_side + offset)

            logger.debug(f"Cropping Box: {box}")
            cover_img = cover_img.crop(box)

        elif new_dimension < cover_side:
            box_img = Image.new("RGB", (cover_side, cover_side), bg_color)
            if crop == 'min':
                offset = 0
            if crop == 'mid':
                offset = (cover_side - new_dimension) // 2
            elif crop == 'max':
                offset = (cover_side - new_dimension)

            if ornt :
                origin = (offset, 0)
            else :
                origin = (0, offset)

            logger.debug(f"Paste Origin: {origin}")
            box_img.paste(cover_img, origin)
            cover_img = box_img

        return cover_img

    def _landscape_cover_fit(self) -> Image.Image:
        cover_cfg = self._settings

        required_size = self.parent.config.output.size
        crop = cover_cfg.crop

        cover_img = Image.open(resolve_path(cover_cfg.path))

        orig_width, orig_height = cover_img.size
        aspect_ratio = orig_width / orig_height

        # try maxxing width first
        new_width = required_size.width
        new_height = int(new_width / aspect_ratio)
        if new_height < required_size.height:
            new_width = int(required_size.height * aspect_ratio)
            new_height = required_size.height
        
        cover_img = cover_img.resize((new_width, new_height))
        if new_height > required_size.height:
            if crop == 'min':
                height_offset = 0
            elif crop == 'mid':
                height_offset = (new_height - required_size.height) // 2
            elif crop == 'max':
                height_offset = new_height - required_size.height
        else :
            height_offset = 0

        if new_width > required_size.width:
            if crop == 'min':
                width_offset = 0
            elif crop == 'mid':
                width_offset = (new_width - required_size.width) // 2
            elif crop == 'max':
                width_offset = new_width - required_size.width
        else :
            width_offset = 0

        if width_offset != 0 or height_offset != 0:
            box = (width_offset, height_offset, width_offset + required_size.width,
                height_offset + required_size.height)
            cover_img = cover_img.crop(box)

        return cover_img

    def _portrait_cover_fit(self) -> Image.Image:
        cover_cfg = self._settings

        required_size = self.parent.config.output.size
        crop = cover_cfg.crop

        cover_img = Image.open(resolve_path(cover_cfg.path))

        orig_width, orig_height = cover_img.size
        aspect_ratio = orig_height / orig_width

        # try maxxing width first
        new_height = required_size.height
        new_width = int(new_height * aspect_ratio)
        if new_width < required_size.width:
            new_height = int(required_size.width / aspect_ratio)
            new_width = required_size.width
        
        cover_img = cover_img.resize((new_width, new_height))
        if new_width > required_size.width:
            if crop == 'min':
                width_offset = 0
            elif crop == 'mid':
                width_offset = (new_width - required_size.width) // 2
            elif crop == 'max':
                width_offset = new_width - required_size.width
        else :
            width_offset = 0

        if new_height > required_size.height:
            if crop == 'min':
                height_offset = 0
            elif crop == 'mid':
                height_offset = (new_height - required_size.height) // 2
            elif crop == 'max':
                height_offset = new_height - required_size.height
        else :
            height_offset = 0

        if width_offset != 0 or height_offset != 0:
            box = (width_offset, height_offset, width_offset + required_size.width,
                height_offset + required_size.height)
            cover_img = cover_img.crop(box)

        return cover_img

    def generate(self) -> None :

        cover_cfg = self._settings

        if not cover_cfg.path_valid():
            logger.info("Skipping cover")
            return

        output_size = self.parent.config.output.size

        logger.info("Adding cover")

        if cover_cfg.fit == 'cover':
            if output_size.is_landscape() :
                cover_img = self._landscape_cover_fit()
            else :
                cover_img = self._portrait_cover_fit()
        else:
            cover_img = self._cover_square(
                        int(output_size.is_landscape()))

        cover_width, cover_height = cover_img.size

        logger.debug(f"Cover Size before margin or border: {cover_width}x{cover_height}")

        border_size = 0

        margin_size = cover_cfg.margin
        logger.debug(f"Cover Margin Size: {margin_size}")

        if cover_cfg.border.exists() :
            border_size = cover_cfg.border.width
            border_color = cover_cfg.border.color
            border_img = Image.new("RGB", (cover_width - margin_size * 2, cover_height - margin_size * 2), border_color)
            logger.debug(f"Border Image Size: {border_img.size}")
            cover_img = cover_img.resize(
                (cover_width - border_size * 2 - margin_size * 2, 
                cover_height - border_size * 2 - margin_size * 2))
            logger.debug(f"Cover Image New Size: {cover_img.size}")
            # border_img already has the margin_size baked in so we only need
            # to offset by the border_size.
            border_img.paste(cover_img, (border_size, border_size))
            cover_img = border_img

        if cover_cfg.align == 'min':
            position = (0 + margin_size, 0 + margin_size)
        elif cover_cfg.align == 'mid':
            if output_size.is_landscape():
                position = (((output_size.width - cover_img.width) // 2) + margin_size, 0 + margin_size)
            else:
                position = (0 + margin_size, ((output_size.height - cover_img.height) // 2) + margin_size)
        elif cover_cfg.align == 'max':
            if output_size.is_landscape():
                position = (output_size.width - cover_img.width + margin_size, 0 + margin_size)
            else:
                position = (0 + margin_size, output_size.height - cover_img.height + margin_size)
        else:
            raise Exception(f"Invalid cover alignment: {cover_cfg.align}")

        # Paste the cover
        logger.debug(f"Cover Position: {position}")
        self.parent.img.paste(cover_img, position)

        global COVER_RECT, BORDER_RECT

        # position already has the margin taken into account.
        # cover_img does not have the margin in it. so do not need to subtract.
        self.bbox = rectangle(geometry(position[0] + border_size + margin_size, position[1] + border_size + margin_size), 
                            geometry(cover_img.width - 2 * border_size, cover_img.height - 2 * border_size))

        # position already has the margin taken into account.
        # cover_img does not have the margin in it. so do not need to subtract.
        ele = BorderElement('border', cover_cfg.border, self.parent)
        ele.bbox = rectangle(geometry(position[0], position[1]), 
                                geometry(cover_img.width, cover_img.height))
