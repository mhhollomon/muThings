from copy import deepcopy   

from typing import TYPE_CHECKING

from PIL import Image, ImageDraw

from ..utils import clamped_mask

from ..geometry import rect, point


from ..settings import BorderSettings

import logging
logger = logging.getLogger(__name__)


class BorderHelper:
    def __init__(self, settings : BorderSettings, name : str, mode : str = 'subtract') :
        self.settings = deepcopy(settings)
        self.mode = mode
        self.name = name

        self.border_bbox = None


    def generate(self, size_rect : rect) -> Image.Image | None :
        logger.debug(f"--- Generating border - size_rect = {size_rect} mode = {self.mode}")

        ws = self.settings.width

        if ws.is_zero() :
            logger.debug("Border helper -- width is zero")
            self.content_bbox = size_rect
            return None

        if self.mode == 'subtract':
            self.border_bbox = size_rect
            origin = self.border_bbox.origin + (ws.l, ws.t)
            extent = self.border_bbox.extent - (ws.l + ws.r, ws.t + ws.b)
            self.content_bbox = rect(origin, extent)

        elif self.mode == 'add':
            origin = point(0, 0)
            extent = size_rect.extent + (ws.l + ws.r, ws.t + ws.b)

            new_content_origin = size_rect.origin + (ws.l, ws.t)
            self.content_bbox = rect(new_content_origin, size_rect.extent)

            self.border_bbox = rect(origin, extent)
        else :
            raise ValueError(f"Invalid BorderHelper mode {self.mode}")

        img = Image.new("RGB", self.border_bbox.extent.to_tuple(), color='black')

        alpha = Image.new("L", self.border_bbox.extent.to_tuple(), color=0)

        border_draw = ImageDraw.ImageDraw(img)
        alpha_draw = ImageDraw.ImageDraw(alpha)

        if ws.all_sides_same() :
            origin = point(0,0)
            end = self.border_bbox.extent
            logger.debug(f"BorderHelper ({self.name}) -- All sides same")
            # Rectangle doesn't seem to actually give you width*2 covered pixels.
            # With out this you wind up with one pixel wide strips just inside the
            # border at the right and bottom.
            self.content_bbox = rect(self.content_bbox.origin, self.content_bbox.extent + 1)
            if self.settings.round > 0 :
                if self.settings.round > 50 :
                    raise ValueError(f"rounding value in {self.name} is greater than 50 ({self.settings.round})")
                radius = int(self.settings.round * self.border_bbox.extent.small_side() / 100)
                border_draw.rounded_rectangle(
                    (origin.to_tuple(), end.to_tuple()), 
                    radius=radius,
                    width=ws.l, 
                    outline=self.settings.color)
                alpha_draw.rounded_rectangle(
                    (origin.to_tuple(), end.to_tuple()), 
                    radius=radius,
                    width=ws.l, 
                    outline=255)
            else :    
                logger.debug(f"BorderHelper ({self.name}) -- No Rounding")
                border_draw.rectangle(
                    (origin.to_tuple(), end.to_tuple()), 
                    width=ws.l, 
                    outline=self.settings.color)
                alpha_draw.rectangle(
                    (origin.to_tuple(), end.to_tuple()), 
                    width=ws.l, 
                    outline=255)
        else :
            fill_color = self.settings.color
            # TOP
            width = ws.t
            if width > 0 :
                # If width is even, then the "extra" pixel is on the bottom of the line
                border_mid = width // 2 - (1 - width %2)
                start = (0, border_mid)
                end = (self.border_bbox.extent.width, border_mid)
                border_draw.line((start, end), fill=fill_color, width=width)
                alpha_draw.line((start, end), fill=255, width=width)

            # RIGHT
            width = ws.r
            if width > 0 :
                # If width is even, then the "extra" pixel is on the right of the line
                border_mid = width // 2 - width %2
                start = (self.border_bbox.extent.width - border_mid, 0)
                end = (self.border_bbox.extent.width - border_mid, self.border_bbox.extent.height)
                border_draw.line((start, end), fill=fill_color, width=width)
                alpha_draw.line((start, end), fill=255, width=width)

            # BOTTOM
            width = ws.b
            if width > 0 :
                # If width is even, then the "extra" pixel is on the bottom of the line
                border_mid = width // 2 -  width %2
                start = (0, self.border_bbox.extent.height - border_mid)
                end = (self.border_bbox.extent.width, self.border_bbox.extent.height - border_mid)
                border_draw.line((start, end), fill=fill_color, width=width)
                alpha_draw.line((start, end), fill=255, width=width)

            # LEFT
            width = ws.l
            if width > 0 :
                # If width is even, then the "extra" pixel is on the right of the line
                border_mid = width // 2 - (1 - width %2)
                start = (border_mid, 0)
                end = (border_mid, self.border_bbox.extent.height)
                border_draw.line((start, end), fill=fill_color, width=width)
                alpha_draw.line((start, end), fill=255, width=width)


        img.putalpha(alpha)

        #img.show()

        return img

    def get_content_rect(self) -> rect :
        if self.border_bbox is None:
            raise ValueError("BorderHelper -- get_content_rect called before generate")
        return self.content_bbox
    
    def get_border_rect(self) -> rect :
        if self.border_bbox is None:
            raise ValueError("BorderHelper -- get_border_rect called before generate")
        return self.border_bbox
        
