from copy import deepcopy   

from PIL import Image, ImageDraw

from ..geometry import rect, point


from ..settings import BorderSettings
from ..utils import DebugBase

import logging
logger = logging.getLogger(__name__)

_MULT_FACTOR : int = 4

class BorderHelper(DebugBase):
    DBGCATEGORY = 'BorderHelper'

    def __init__(self, settings : BorderSettings, name : str, mode : str = 'subtract', color:str='black') :
        self.settings = deepcopy(settings)
        self.mode = mode
        self.name = name
        self.bg_color = color

        self.border_bbox = None
        self.content_bbox = None

    def _debug(self, msg) :
        logger.debug(f"BorderHelper {self.name} -- {msg}")

    def layout(self, size_rect : rect) :
        self._debug(f"layout")
        ws = self.settings.width

        if ws.is_zero() :
            self._debug(f"width is zero")
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

    def _draw_piecewise(self) -> tuple[Image.Image, Image.Image]:

        self._debug("using piecewise")
        ws = self.settings.width
        fill_color = self.settings.color
        assert self.border_bbox is not None

        border_ext = self.border_bbox.extent
        img = Image.new("RGBA", border_ext.to_tuple(), color=(0, 0, 0, 0))
        alpha = Image.new("L", border_ext.to_tuple(), color=0)

        border_draw = ImageDraw.ImageDraw(img)
        alpha_draw = ImageDraw.ImageDraw(alpha)

        # TOP
        width = ws.t
        if width > 0 :
            # If width is even, then the "extra" pixel is on the bottom of the line
            border_mid = width // 2 - (1 - width %2)
            start = (0, border_mid)
            # Coordinates are included so need to stop one short
            end = (border_ext.width - 1, border_mid)
            self._debug(f"piecewise top = mid = {border_mid} : {start} , {end}")
            border_draw.line((start, end), fill=fill_color, width=width)
            alpha_draw.line((start, end), fill=255, width=width)

        # RIGHT
        width = ws.r
        if width > 0 :
            # If width is even, then the "extra" pixel is on the right of the line
            border_mid = width // 2 + 1
            start = (border_ext.width - border_mid, 0)
            # Coordinates are included so need to stop one short
            end = (border_ext.width - border_mid, border_ext.height-1)
            self._debug(f"piecewise right = mid = {border_mid} : {start} , {end}")
            border_draw.line((start, end), fill=fill_color, width=width)
            alpha_draw.line((start, end), fill=255, width=width)

        # BOTTOM
        width = ws.b
        if width > 0 :
            # If width is even, then the "extra" pixel is on the bottom of the line
            border_mid = width // 2 + 1
            start = (0, border_ext.height - border_mid)
            # Coordinates are included so need to stop one short
            end = (border_ext.width -1, border_ext.height - border_mid)
            self._debug(f"piecewise bottom = mid = {border_mid} : {start} , {end}")
            border_draw.line((start, end), fill=fill_color, width=width)
            alpha_draw.line((start, end), fill=255, width=width)

        # LEFT
        width = ws.l
        if width > 0 :
            # If width is even, then the "extra" pixel is on the right of the line
            border_mid = width // 2 - (1 - width %2)
            start = (border_mid, 0)
            # Coordinates are included so need to stop one short
            end = (border_mid, border_ext.height - 1)
            self._debug(f"piecewise left = mid = {border_mid} : {start} , {end}")
            border_draw.line((start, end), fill=fill_color, width=width)
            alpha_draw.line((start, end), fill=255, width=width)

        return (img, alpha)

    def _draw_rounded(self) -> tuple[Image.Image, Image.Image] :
        self._debug(f"Using rounded_rectangle - bg_color = {self.bg_color}")

        ws = self.settings.width
        assert self.border_bbox is not None
        big_extent = self.border_bbox.extent * _MULT_FACTOR
        img = Image.new("RGB", big_extent.to_tuple(), color=self.bg_color)

        alpha = Image.new("L", big_extent.to_tuple(), color=0)

        border_draw = ImageDraw.ImageDraw(img)
        alpha_draw = ImageDraw.ImageDraw(alpha)

        if self.settings.round > 50 :
            raise ValueError(f"rounding value in {self.name} is greater than 50 ({self.settings.round})")
        
        origin = point(0,0)
        # Coordinates are included so need to stop one short
        end = big_extent - 1
        radius = int(self.settings.round * big_extent.small_side() / 100)
        border_draw.rounded_rectangle(
            (origin.to_tuple(), end.to_tuple()), 
            radius=radius,
            width=ws.l * _MULT_FACTOR, 
            outline=self.settings.color)
        alpha_draw.rounded_rectangle(
            (origin.to_tuple(), end.to_tuple()), 
            radius=radius,
            width=ws.l * _MULT_FACTOR, 
            outline=255)

        img = img.resize(self.border_bbox.extent.to_tuple(),resample=Image.Resampling.LANCZOS)
        alpha = alpha.resize(self.border_bbox.extent.to_tuple(),resample=Image.Resampling.LANCZOS)

        return (img, alpha)


    def generate(self) -> Image.Image | None :
        logger.debug(f"--- Generating border - mode = {self.mode}")

        ws = self.settings.width

        if ws.is_zero() :
            self._debug(f"width is zero")
            return None


        if ws.all_sides_same() and  self.settings.round > 0 :
            img, alpha = self._draw_rounded()
        else :
            img, alpha = self._draw_piecewise()


        img.putalpha(alpha)

        return img

    def get_content_rect(self) -> rect :
        if self.content_bbox is None:
            raise ValueError("BorderHelper -- get_content_rect called before layout")
        return self.content_bbox
    
    def get_border_rect(self) -> rect :
        if self.border_bbox is None:
            raise ValueError("BorderHelper -- get_border_rect called before generate")
        return self.border_bbox
        
