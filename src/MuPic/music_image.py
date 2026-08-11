from typing import Dict

from PIL import Image

from .element import *
from .settings import *

class MusicImage :
    def __init__(self, config : Config) -> None:
        self.config = config
        self.elements : Dict[str, ImageElement] = {}
        
        self.output_size = self.config.output.size

    def generate(self) :
        ele = OutputElement('output', self.config.output, self)
        output_img = ele.generate()

        self.img = output_img

        ele = CoverElement('cover', self.config.cover, self)
        ele.generate()
        
        ele = GraphicElement('logo', self.config.logo, self)
        ele.generate()

        for i, block in enumerate(self.config.elements):
            name = block.name or f'block_{i}'
            if isinstance(block, GraphicSettings) :
                ele = GraphicElement(name, block, self)
            else :
                ele = TextElement(name, block, self)
            ele.generate()

        return output_img

    def _add_element(self, elem : ImageElement) :
        if elem.name in self.elements :
            raise ValueError(f"Element {elem.name} already exists")
        
        self.elements[elem.name] = elem

    def get_elem(self, name : str) :
        return self.elements[name]

    def output_image(self) -> Image.Image :
        return self.img
