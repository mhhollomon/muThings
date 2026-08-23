import re
from typing import Dict

from PIL import Image, ImageDraw

from .element import *
from .settings import *

class MusicImage :
    def __init__(self, config : Settings) -> None:
        self.config = config
        self.elements : Dict[str, ImageElement] = {}
        
        self.output_size = self.config.output.size

    def generate(self) :
        ele = OutputElement('output', self.config.output, self)
        output_img = ele.generate()

        self.img = output_img        

        zorder : list[tuple[int, int, str]] = []
        for i, block in enumerate(self.config.elements):
            name = block.name or f'block_{i}'
            if isinstance(block, ImageSettings) :
                ele = GraphicElement(name, block, self)
            else :
                ele = TextElement(name, block, self)
            ele.generate()
            zorder.append((ele.settings.zorder, i, name))

        # Now we need figure out the order
        zorder.sort()

        for zorder_tuple in zorder :
            logger.debug(f"Pasting in {zorder_tuple}")
            ele = self.get_elem(zorder_tuple[2])
            bbox = ele.get_bbox('paste')
            img, mask = ele.get_images()
            self.output_image().paste(img, bbox.origin.to_tuple(), mask=mask)

        self._generate_grid()

        return self.output_image()


    def _generate_grid(self) :
        if self.config.grid is None :
            return

        logger.info(f"Generating Grid with {self.config.grid}")
        if self.config.grid.endswith('%') :
            factor = float(self.config.grid[:-1]) / 100.0
            logger.debug(f"grid factor = {factor}")
            xpix = int(self.output_size[0] * factor)
            ypix = int(self.output_size[1] * factor)
        elif re.fullmatch(r'\d+', self.config.grid) :
            factor = float(self.config.grid) / 100.0
            logger.debug(f"grid factor = {factor}")
            xpix = int(self.output_size[0] * factor)
            ypix = int(self.output_size[1] * factor)
        elif self.config.grid.endswith('px') :
            xpix = int(self.config.grid[:-2])
            ypix = xpix
        else :
            raise ValueError(f"Invalid grid value: {self.config.grid}")

        draw = ImageDraw.ImageDraw(self.output_image())
        p = xpix
        length = self.output_size[1]
        while p < self.output_size[0] :
            draw.line(((p, 0), (p, length)), fill='black', width=1)
            p += xpix

        p = ypix
        length = self.output_size[0]
        while p < self.output_size[1] :
            draw.line(((0, p), (length, p)), fill='black', width=1)
            p += ypix
            


    def _add_element(self, elem : ImageElement) :
        if elem.name in self.elements :
            raise ValueError(f"Element {elem.name} already exists")
        
        self.elements[elem.name] = elem

    def get_elem(self, name : str) :
        return self.elements[name]

    def output_image(self) -> Image.Image :
        return self.img

