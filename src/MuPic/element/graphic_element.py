from copy import deepcopy

from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from ..music_image import MusicImage

from .element import ImageElement
from ..settings import ImageSettings
from ..geometry import sizet, rect, point

from PIL import Image

import logging
logger = logging.getLogger(__name__)


class GraphicElement(ImageElement):
    def __init__(self, name : str, graphic_settings : ImageSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        self.settings = deepcopy(graphic_settings)

    def _compute_mask(self, img : Image.Image, mask : str, luminance_img : Image.Image | None = None) -> Image.Image | None :
        
        if luminance_img is None:
            luminance_img = img.convert('L')

        if mask == 'self':
            # use the luminance of the image as-is
            gray_img = luminance_img

        elif mask == 'black':
            # clamp the luminance to black and white
            gray_img = luminance_img.point(lambda x : 0 if x < 10 else 255) # type: ignore

        elif mask == 'none' :
            # no mask
            gray_img = None

        elif mask == 'alpha' :
            # use the alpha channel
            gray_img = img

        else : # auto
            # use alpha if it is there otherwise use black
            if 'A' in img.mode or 'a' in img.mode:
                gray_img = img
            else:
                gray_img = self._compute_mask(img, 'black', luminance_img)

        return gray_img

    def _build_image(self) -> Tuple[Image.Image, Image.Image | None] :

        file_path : str = self.settings.path or ''

        with Image.open(file_path) as img_img:

            img_width, img_height = img_img.size
            needed_size : int = self.settings.size.width

            if img_width > img_height:
                # Landscape
                new_size = (needed_size, int( needed_size * (img_height / img_width)))
            else:
                # Portrait
                new_size = (int(needed_size * (img_width / img_height)), needed_size)

            img_img = img_img.resize(new_size)

            gray_img = self._compute_mask(img_img, self.settings.mask)


            return (img_img, gray_img)
        
    def generate(self) -> None :

        cfg = self.settings
        logger.info(f"Adding {self.name} Element")

        if cfg.path is not None:   
            logger.debug(f"Loading image from {cfg.path}")
            img_img, mask_img = self._build_image()
        elif cfg.color is None :
            raise ValueError(f"Both color and path are missing for {self.name}")
        else :
            img_img = Image.new("RGB", cfg.size.to_tuple(), color=cfg.color)
            mask_img = None
        
        position = self.settings.position

        img_size = sizet(*img_img.size)

        offsets =  self.offsets_for_position(
            pos=position,
            elem_size=img_size
            )

        # Paste the logo
        self.parent.img.paste(img_img, offsets.to_tuple(), mask=mask_img)
        self.set_bbox('content', rect(offsets, img_size))
        self.set_bbox('full', rect(offsets, img_size))

        self.generated = True

