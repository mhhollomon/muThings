from copy import deepcopy

from typing import TYPE_CHECKING, Any

from ..utils import clamped_mask

if TYPE_CHECKING:
    from ..music_image import MusicImage

from .element import ImageElement
from .border_helper import BorderHelper
from ..settings import ImageSettings
from ..geometry import sizet, rect

from PIL import Image, ImageChops

import logging
logger = logging.getLogger(__name__)


class GraphicElement(ImageElement):
    def __init__(self, name : str, graphic_settings : ImageSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        self.settings = deepcopy(graphic_settings)
        self.bh : BorderHelper | None = None
        self.img_bg_color = 'black'

    def _debug(self, msg : str) :
        logger.debug(f"Image {self.name} -- {msg}")

    def layout(self) :
        """Compute all the bboxen"""


        cfg = self.settings
        self._debug(f"layout {self.name} image")

        # When using antialising with mask, we need to make sure
        # we are blending with a color as close as possible to the
        # expected background color.
        # If this element declares a color, use that
        # If not, use the color of the output element (this defaults to black).
        #
        # This isn't perfect, but it is the best we can do until the split between
        # layout and image generation happens.
        #
        if cfg.color :
            self.img_bg_color = cfg.color
        else :
            self.img_bg_color = self.parent.get_elem('output').settings.color # type: ignore


        if isinstance(cfg.size, tuple):
            # cfg.size is one of the relative size settings.
            cfg.size = self._calc_size(cfg.size)
            self._debug(f"Calculated size = {cfg.size}")

        offsets =  self.offsets_for_position(
            pos=cfg.position,
            elem_size=cfg.size
            )

        content_rec = rect(offsets, cfg.size)
        # --- FULL
        self.set_bbox('full', content_rec)

        if cfg.margin > 0 :
            # 'full' and 'margin' bbox are the same.
            # This is set inside the `if` because margin should not exist
            # if there is no margin.
            # --- MARGIN
            self.set_bbox('margin', content_rec)

            # Remove the margin from the content rect
            new_origin = content_rec.origin + cfg.margin
            new_extent = content_rec.extent - (cfg.margin * 2)
            content_rec = rect(new_origin, new_extent)

        self._debug(f"content_rec after margin = {content_rec}")

        if cfg.has_border() :
            assert cfg.border is not None
            self.bh = BorderHelper(cfg.border, cfg.name, color=self.img_bg_color)
            self.bh.layout(content_rec)
            # --- PASTE
            self.set_bbox('paste', content_rec)
            if self.bh.get_content_rect() is not None:

                # --- BORDER
                self.set_bbox('border', content_rec)
            
            # Get the new size for the content that excludes the border
            content_rec = self.bh.get_content_rect()

            # --- CONTENT
            self.set_bbox('content', content_rec)

        else :
            logger.debug("Image -- No border spec")
            # --- CONTENT
            self.set_bbox('content', content_rec)
            # --- PASTE
            self.set_bbox('paste', content_rec)

        logger.debug(f"Image -- content_rec after border = {content_rec}")

        self.layout_done = True


    def _compute_mask(self, img : Image.Image, mask : str, luminance_img : Image.Image | None = None) -> Image.Image | None :
        
        if luminance_img is None:
            luminance_img = img.convert('L')

        if mask == 'self':
            # use the luminance of the image as-is
            gray_img = luminance_img

        elif mask == 'black':
            # clamp the luminance to black and white
            gray_img = clamped_mask(luminance_img)

        elif mask == 'none' :
            # no mask
            gray_img = None

        elif mask == 'alpha' :
            # use the alpha channel
            gray_img = img.getchannel('A')

        else : # auto
            # use alpha if it is there otherwise use black
            if 'A' in img.mode or 'a' in img.mode:
                logger.debug(f"Image {self.name} -- computing mask : using A channel of image")
                gray_img = img.getchannel('A')
            else:
                gray_img = self._compute_mask(img, 'black', luminance_img)

        return gray_img
            
    def _build_image(self, needed_size : sizet) -> Image.Image :

        cfg = self.settings

        file_path  = cfg.path
        assert file_path is not None

        with Image.open(file_path) as img_img:

            fit = cfg.fit
            img_size = sizet(img_img.size)

            if fit[0] == 'stretch' :
                # forget aspect ratio. Just make the image fill the rectangle
                new_size = needed_size
                img_img = img_img.resize(new_size.to_tuple())

            elif fit[0] == 'contain' :
                # Make the image as large as possible while making sure it fits in
                # entirely into container. But maintain A.R.
                width_factor = needed_size.width / img_size.width
                height_factor = needed_size.height / img_size.height
                new_size = img_size * min(width_factor, height_factor)
                img_img = img_img.resize(new_size.to_tuple())

                if new_size != needed_size :
                    # it will be smaller
                    buffer = Image.new("RGB", size=needed_size.to_tuple(), color=cfg.color)
                    if fit[1] == 'min' :
                        paste_pt = sizet(0, 0)
                    elif fit[1] == 'mid' :
                        paste_pt = (needed_size - new_size) // 2
                    else :
                        paste_pt = (needed_size - new_size)

                    buffer.paste(img_img, paste_pt.to_tuple())
                    img_img = buffer
            elif fit[0] == 'fill' :
                # Make sure the image completely fills the container
                # while preserving A.R.
                # This means the image will need to be cropped.
                width_factor = needed_size.width / img_size.width
                height_factor = needed_size.height / img_size.height
                new_size = img_size * max(width_factor, height_factor)
                img_img = img_img.resize(new_size.to_tuple())

                crop_factor = 0.0 if fit[1] == 'min' else 0.5 if fit[1] == 'mid' else 1.0
                if new_size != needed_size :
                    logger.debug(f"Image {self.name} -- need to crop ({new_size} down to {needed_size})")

                    # The image will be bigger than the container.
                    if new_size.width > needed_size.width :
                        crop_width = new_size.width - needed_size.width
                        logger.debug(f"Image {self.name} -- too wide by {crop_width}")
                        crop_offset = crop_width * crop_factor
                        crop = (
                            crop_offset,
                            0,
                            needed_size.width + crop_offset,
                            needed_size.height,
                        )
                    else :
                        crop_height = new_size.height - needed_size.height
                        logger.debug(f"Image {self.name} -- too tall by  {crop_height}")
                        crop_offset = crop_height * crop_factor
                        crop = (
                            0,
                            crop_offset,
                            needed_size.width,
                            needed_size.height + crop_offset,
                        )

                    img_img = img_img.crop(crop)
            else :
                raise ValueError(f"unknown fit algorithm `{fit[0]}` for {self.name}")

            logger.debug(f"Image {self.name} -- _build_image final size = {img_img.size}")

            return img_img

    def _calc_size(self, size : tuple[str, Any]) -> sizet :
        if size[0] == 'maxsquare' :
            pos = self.settings.position
            ref_elem = self.parent.get_elem(pos.target.element)
            ref_bbox = ref_elem.get_bbox(sub=pos.target.sub, piece=pos.target.piece)

            bbox_min = min(ref_bbox.extent.width, ref_bbox.extent.height)

            return sizet(bbox_min, bbox_min)
        elif size[0] == "scale" :
            pos = self.settings.position
            ref_elem = self.parent.get_elem(pos.target.element)
            ref_bbox = ref_elem.get_bbox(sub=pos.target.sub, piece=pos.target.piece)

            factor  = size[1]
            assert isinstance(factor, float)

            return ref_bbox.extent * factor
        elif size[0] == "max" :
            pos = self.settings.position
            ref_elem = self.parent.get_elem(pos.target.element)
            ref_bbox = ref_elem.get_bbox(sub=pos.target.sub, piece=pos.target.piece)

            return ref_bbox.extent

        raise ValueError(f"Invalid size {size}")
        
    def generate(self) -> None :

        cfg = self.settings
        logger.info(f"---- Image -- Adding {self.name} image")

        self.layout()


        content_rec = self.get_bbox('content')
        full_rec = self.get_bbox('full')

        border_img : Image.Image | None = None


        if cfg.has_border() :
            assert cfg.border is not None
            assert self.bh is not None
            border_img = self.bh.generate(content_rec)
            self.set_bbox('paste', content_rec)
            if border_img is not None:
                self.set_bbox('border', content_rec)
            
            # Get the new size for the content
            content_rec = self.bh.get_content_rect()
            self.set_bbox('content', content_rec)

            content_paste = (cfg.border.width.l, cfg.border.width.t)
        else :
            logger.debug("Image -- No border spec")
            content_paste = (0, 0)
            self.set_bbox('content', content_rec)
            self.set_bbox('paste', content_rec)

        logger.debug(f"Image -- content_rec after border = {content_rec}")


        if cfg.path is not None:   
            logger.debug(f"graphics element {self.name} -- Loading image from {cfg.path}")
            img_img = self._build_image(content_rec.extent)
        elif cfg.color is None :
            raise ValueError(f"Both color and path are missing for {self.name}")
        else :
            img_img = None
        
        mask_color = 255 if cfg.color is not None else 0

        full_img = Image.new("RGB", full_rec.extent.to_tuple(), color=self.img_bg_color)
        full_mask = Image.new("L", full_rec.extent.to_tuple(), color=mask_color)

        mask_img = None
        if img_img :
            mask_img = self._compute_mask(img_img, cfg.mask)
            logger.debug(f"Image {self.name} -- pasting image into final at {content_paste}")
            full_img.paste(img_img, content_paste, mask=mask_img)
            if mask_img :
                logger.debug(f"Image {self.name} -- updating full mask with mask_img")
                full_mask.paste(mask_img, content_paste)



        if border_img is not None:
            logger.debug(f"Image {self.name} -- pasting border into final")
            full_img.paste(border_img, (0,0), mask=border_img)
            logger.debug(f"Image {self.name} -- updating full mask with border_mask")
            border_mask = border_img.getchannel('A')
            full_mask = ImageChops.lighter(full_mask, border_mask)
    
        self.generated = True
        self.main_image = full_img
        self.mask_image = full_mask

        logger.debug(f"---- End {self.name} image")

