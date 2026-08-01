from copy import deepcopy

from PIL import Image

from .element import ImageElement

from ..settings import OutputSettings
from ..paths import resolve_path
from ..position import geometry, rectangle

import logging
logger = logging.getLogger(__name__)

class OutputElement(ImageElement) :
    def __init__(self, name : str, output_settings : OutputSettings) :
        super().__init__(name)

        self._settings = deepcopy(output_settings)

    def generate(self) -> Image.Image :
        # Open the image
        output_path = self._settings.path
        output_size = self._settings.size

        if self._settings.valid_attr('background'):
            logger.info("Using background image")
            output_img = Image.open(resolve_path(self._settings.background))
            output_img = output_img.resize(output_size.to_tuple())
            if output_img.mode != 'RGB':
                output_img = output_img.convert('RGB')
        else:
            logger.info("Creating color background")
            output_img = Image.new("RGB", output_size.to_tuple(), color=self._settings.color)

        self.bbox = rectangle(geometry(0,0), output_size)
        self.generated = True

        return output_img
