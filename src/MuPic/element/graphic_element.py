from copy import deepcopy

from typing import TYPE_CHECKING, Any

from ..utils import clamped_mask

if TYPE_CHECKING:
    from ..music_image import MusicImage

from .element import ImageElement
from .border_helper import BorderHelper
from ..settings import ImageSettings
from ..geometry import sizet, rect

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
                img.save("./z-img-as-read.png")
                gray_img.save("./z-alpha-channel.png")
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
                        logger.debug(f"Image {self.name} -- too wide by {crop_width})")
                        crop_offset = crop_width * crop_factor
                        crop = (
                            crop_offset,
                            0,
                            new_size.width + crop_offset,
                            needed_size.height,
                        )
                    else :
                        crop_height = new_size.height - needed_size.height
                        logger.debug(f"Image {self.name} -- too tall by  {crop_height})")
                        crop = (
                            0,
                            crop_height * crop_factor,
                            needed_size.width,
                            needed_size.height + (crop_height * crop_factor),
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

        if isinstance(cfg.size, tuple):
            cfg.size = self._calc_size(cfg.size)
            logger.debug(f"Calculated size = {cfg.size}")

        offsets =  self.offsets_for_position(
            pos=cfg.position,
            elem_size=cfg.size
            )

        content_rec = rect(offsets, cfg.size)
        self.set_bbox('full', content_rec)
        full_rec = content_rec

        if cfg.margin > 0 :
            # 'full' and 'margin' bbox are the same.
            self.set_bbox('margin', content_rec)

            # Remove the margin from the content rect
            new_origin = content_rec.origin + cfg.margin
            new_extent = content_rec.extent - (cfg.margin * 2)
            content_rec = rect(new_origin, new_extent)
            logger.debug(f"Image -- content_rec after margin = {content_rec}")

        # Rather than mess with transparency, we simply create
        # a smaller content that ignores the margin.
        # The 'full' bbox for the element, however will still
        # include the margin.


        border_img : Image.Image | None = None

        if cfg.has_border() :
            assert cfg.border is not None
            bh = BorderHelper(cfg.border, cfg.name)
            border_img = bh.generate(content_rec)
            self.set_bbox('paste', content_rec)
            if border_img is not None:
                self.set_bbox('border', content_rec)
            
            # Get the new size for the content
            content_rec = bh.get_content_rect()
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
        

        img_color = cfg.color if cfg.color is not None else 'black'
        mask_color = 255 if cfg.color is not None else 0

        full_img = Image.new("RGB", full_rec.extent.to_tuple(), color=img_color)
        full_mask = Image.new("L", full_rec.extent.to_tuple(), color=mask_color)

        mask_img = None
        if img_img :
            mask_img = self._compute_mask(img_img, cfg.mask)
            logger.debug(f"Image {self.name} -- pasting image into final at {content_paste}")
            full_img.paste(img_img, content_paste, mask=mask_img)
            if mask_img :
                logger.debug(f"Image {self.name} -- updating full mask with mask_img")
                mask_img.save('./z-mask-img.png')
                full_mask.paste(mask_img, content_paste)

            full_mask.save("./z-full-mask-after-img.png")


        if border_img is not None:
            logger.debug(f"Image {self.name} -- pasting border into final")
            full_img.paste(border_img, (0,0), mask=border_img)
            logger.debug(f"Image {self.name} -- updating full mask with border_mask")
            border_mask = border_img.getchannel('A')
            border_mask.save("./z-border-mask.png")
            full_mask = Image.blend(full_mask, border_mask, alpha=0.5)
            full_mask.save("./z-full-mask-blend.png")
            full_mask = full_mask.point(lambda x : 2.0 * x)
            full_mask.save("./z-full-mask.png")
    
        self.generated = True
        self.main_image = full_img
        self.mask_image = full_mask

        logger.debug(f"---- End {self.name} image")

