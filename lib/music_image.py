from typing import Dict

from PIL import Image

from .element import *
from .settings import *

class MusicImage :
    def __init__(self, config : Config) -> None:
        self.config = config
        self.elements : Dict[str, ImageElement] = {}

    def generate(self) :
        output_elem = OutputElement('output', self.config.output, self)
        output_img = output_elem.generate()

        self.img = output_img

        return output_img

    def _add_element(self, elem : ImageElement) :
        if elem.name in self.elements :
            raise ValueError(f"Element {elem.name} already exists")
        
        self.elements[elem.name] = elem

    def get_elem(self, name : str) :
        return self.elements[name]

    def output_image(self) -> Image.Image :
        return self.img
