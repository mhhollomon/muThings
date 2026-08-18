from copy import deepcopy

from typing import TYPE_CHECKING, Tuple


if TYPE_CHECKING:
    from ..music_image import MusicImage

from .element import ImageElement
from .border_helper import BorderHelper
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

    def _build_image(self, needed_size : int) -> Image.Image :

        file_path : str = self.settings.path or ''

        with Image.open(file_path) as img_img:

            img_width, img_height = img_img.size

            if img_width > img_height:
                # Landscape
                new_size = (needed_size, int( needed_size * (img_height / img_width)))
            else:
                # Portrait
                new_size = (int(needed_size * (img_width / img_height)), needed_size)

            img_img = img_img.resize(new_size)

            #gray_img = self._compute_mask(img_img, self.settings.mask)


            return img_img
        
    def generate(self) -> None :

        cfg = self.settings
        logger.info(f"---- Image -- Adding {self.name} image")

        offsets =  self.offsets_for_position(
            pos=cfg.position,
            elem_size=cfg.size
            )

        content_rec = rect(offsets, cfg.size)
        self.set_bbox('full', content_rec)

        if cfg.margin > 0 :
            self.set_bbox('margin', content_rec)
            new_origin = content_rec.origin + cfg.margin
            new_extent = content_rec.extent - (cfg.margin * 2)
            content_rec = rect(new_origin, new_extent)
        


        border_img : Image.Image | None = None

        if cfg.border is not None :
            bh = BorderHelper(cfg.border)
            border_img = bh.generate(content_rec)
            self.set_bbox('border', content_rec)
            content_rec = bh.get_content_rect()
            self.set_bbox('content', content_rec)
        else :
            self.set_bbox('content', content_rec)

        if cfg.path is not None:   
            logger.debug(f"graphics element {self.name} -- Loading image from {cfg.path}")
            img_img = self._build_image(content_rec.extent.width)
        elif cfg.color is None :
            raise ValueError(f"Both color and path are missing for {self.name}")
        else :
            logger.debug(f"graphics element {self.name} -- color = {cfg.color}")
            img_img = Image.new("RGB", content_rec.extent.to_tuple(), color=cfg.color)

        if border_img is not None:
            logger.debug(f"graphics element {self.name} -- pasting image into border")
            mask_img = self._compute_mask(img_img, cfg.mask)
            content_offset = content_rec.origin - offsets
            border_img.paste(img_img, content_offset.to_tuple(), mask=mask_img)
            final_img = border_img
        else :
            final_img = img_img

        mask_img = self._compute_mask(final_img, cfg.mask)        

        # Paste the logo
        self.parent.img.paste(final_img, offsets.to_tuple(), mask=mask_img)

        self.generated = True
        logger.debug(f"---- End {self.name} image")

