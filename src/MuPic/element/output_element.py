from copy import deepcopy

from PIL import Image

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..music_image import MusicImage

from .element import ImageElement

from ..settings import OutputSettings
from ..position import geom, rect


import logging
logger = logging.getLogger(__name__)

class OutputElement(ImageElement) :
    def __init__(self, name : str, output_settings : OutputSettings, parent : 'MusicImage') :
        super().__init__(name, parent)

        self._settings = deepcopy(output_settings)

    def generate(self) -> Image.Image :
        # Open the image
        output_size = self._settings.size

        if self._settings.valid_attr('background'):
            logger.info("Using background image")
            output_img = Image.open(self._settings.background)
            output_img = output_img.resize(output_size.to_tuple())
            if output_img.mode != 'RGB':
                output_img = output_img.convert('RGB')
        else:
            logger.info("Creating color background")
            output_img = Image.new("RGB", output_size.to_tuple(), color=self._settings.color)

        self.bbox = rect(geom(0,0), output_size)

        return output_img
