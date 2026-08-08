from copy import deepcopy

from typing import TYPE_CHECKING, Any, Tuple

if TYPE_CHECKING:
    from ..music_image import MusicImage

from .element import ImageElement
from ..settings import GraphicSettings
from ..position import geom, rect

from PIL import Image

import logging
logger = logging.getLogger(__name__)


class GraphicElement(ImageElement):
    def __init__(self, name : str, graphic_settings : GraphicSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        self._settings = deepcopy(graphic_settings)

    def _compute_mask(self, img : Image.Image, mask : str, luminance_img : Image.Image | None = None) -> Image.Image | None :
        
        if luminance_img is None:
            luminance_img = img.convert('L')

        if mask == 'self':
            # use the luminance of the image as-is
            gray_img = luminance_img

        elif mask == 'black':
            # clamp the luminance to black
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

    def _build_logo(self) -> Tuple[Image.Image, Image.Image | None] | None :

        logo_path : str = self._settings.path

        with Image.open(logo_path) as logo_img:

            logo_width, logo_height = logo_img.size
            needed_size : int = self._settings.size

            if logo_width > logo_height:
                # Landscape
                new_size = (needed_size, int( needed_size * (logo_height / logo_width)))
            else:
                # Portrait
                new_size = (int(needed_size * (logo_width / logo_height)), needed_size)

            logo_img = logo_img.resize(new_size)

            gray_img = self._compute_mask(logo_img, self._settings.mask)


            return (logo_img, gray_img)
        
    def generate(self) -> None :
        if not self._settings.path_valid():
            return
        
        logo_img = self._build_logo()
        if logo_img is None:
            logger.info("Skipping logo")
            return
        
        logger.info("Adding logo")
        logo_img, mask_img = logo_img
        logo_width, logo_height = logo_img.size
        position = self._settings.position

        offsets =  self.offsets_for_position(
            pos=position,
            elem_size=geom(logo_width, logo_height),
            gutter=self.parent.config.globals.gutter
            )

        # Paste the logo
        self.parent.img.paste(logo_img, offsets, mask=mask_img)

        self.bbox = rect(geom(*offsets), geom(logo_width, logo_height))
