from copy import deepcopy

from PIL import Image

from typing import TYPE_CHECKING



if TYPE_CHECKING:
    from ..music_image import MusicImage

from .element import ImageElement
from .border_helper import BorderHelper

from ..settings import OutputSettings
from ..geometry import  rect, point


import logging
logger = logging.getLogger(__name__)

class OutputElement(ImageElement) :
    DBGCATEGORY = 'Output'
    LOGGER = logger

    def __init__(self, name : str, output_settings : OutputSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        self.settings  = output_settings

        self.bh : BorderHelper | None = None

    #-----------------------------------------------------
    # LAYOUT
    #-----------------------------------------------------
    def layout(self) :
        """Compute all the bboxen"""

        full_output_size = self.settings.size
        full_bbox = rect(point(0,0), full_output_size)

        # --- FULL
        self.set_bbox('full', full_bbox)

        output_size = full_output_size
        output_offset = point(0, 0)

        if self.settings.margin > 0 :
            # Calculate the border_bbox
            output_size = output_size - self.settings.margin * 2
            output_offset += self.settings.margin

            # --- MARGIN
            self.set_bbox('margin', full_bbox)

        # Output should probably not have a border.
        # You could add a border by overlaying a image element. 
        # May Trash later.
        if self.settings.border is not None :
            self.bh = BorderHelper(self.settings.border, 'output')

            self.bh.layout(rect(output_offset, output_size))

            if self.bh.border_bbox :
                # --- BORDER
                self.set_bbox('border', rect(output_offset, output_size))

                content_bbox = self.bh.get_content_rect()
            else :
                content_bbox = rect(output_offset, output_size)
        else :
            content_bbox = rect(output_offset, output_size)

        # --- CONTENT
        self.set_bbox('content', content_bbox)

        self.layout_done = True


    def generate(self) -> Image.Image :

        if not self.layout_done :
            self.layout()

        full_output_size = self.settings.size
        content_bbox = self.get_bbox('content')


        if self.settings.background is not None and self.settings.fit == 'cover':
            output_img = Image.open(self.settings.background)
            output_img = output_img.resize(full_output_size.to_tuple())
        else :
            output_img = Image.new("RGB", full_output_size.to_tuple(), color=self.settings.color)

        if self.bh :
            border_bbox = self.get_bbox('border')

            border_img = self.bh.generate(content_bbox)
            if border_img :
                self._debug(f"pasting border at {border_bbox.origin}")
                output_img.paste(border_img, border_bbox.origin.to_tuple(), mask=border_img)



        if self.settings.background is not None and self.settings.fit == 'contain':

            self._debug("Adding background image")
            bg_img = Image.open(self.settings.background)
            if bg_img.mode != 'RGB':
                bg_img = bg_img.convert('RGB')

            bg_img = bg_img.resize(content_bbox.extent.to_tuple())
            output_img.paste(bg_img, content_bbox.origin.to_tuple())

        self.generated = True
        self.layout_done = True

        return output_img
