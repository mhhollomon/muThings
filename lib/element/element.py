from typing import TYPE_CHECKING, Any, Tuple
if TYPE_CHECKING:
    from ..music_image import MusicImage

from ..position import geometry, position, rectangle

import logging
logger = logging.getLogger(__name__)

#---------------------------------------------------------

class ImageElement :
    generated = False
    _bbox = rectangle(geometry(0,0), geometry(0,0))

    def __init__(self, name : str, parent : 'MusicImage') :
        self.name = name
        self.parent = parent
        self._settings : Any = {}

        parent._add_element(self)


    @property
    def name(self) :
        return self._name

    @name.setter
    def name(self, name : str) :
        if name is None :
            raise ValueError("ImageElement name cannot be None")
        if name == '' :
            raise ValueError("ImageElement name cannot be empty")
        self._name = name


    @property
    def bbox(self) :
        if not self.generated :
            raise ValueError(f"ImageElement {self.name} has not been generated yet")
        return self._bbox

    @bbox.setter
    def bbox(self, bbox : rectangle) :
        if bbox is None :
            raise ValueError("ImageElement bbox cannot be None")
        if bbox.extent.width == 0 or bbox.extent.height == 0 :
            raise ValueError("ImageElement bbox cannot be empty")
        self._bbox = bbox
        self.generated = True


    def _pixel_offsets(self, pos : position, elem_size : geometry, gutter : int) -> Tuple[int, int] :

        output_rect = self.parent.get_elem('output').bbox

        if '%' in pos._width :
            w_offset = int(pos._width[:-1]) * output_rect.extent.width // 100
        else :
            w_offset = int(pos._width)

        if '%' in pos._height :
            h_offset = int(pos._height[:-1]) * output_rect.extent.height // 100
        else :
            h_offset = int(pos._height)

        # h_offset and w_offset are where our anchor should be.
        # Now, convert the offsets to the top left of the element.
        if pos._anchor[0] == 'max' :
            w_offset -=  elem_size.width 
        elif pos._anchor[0] == 'mid' :
            w_offset -= elem_size.width // 2
        elif pos._anchor[0] == 'min' :
            pass
        else :
            raise ValueError(f"Unknown anchor: {pos._anchor[0]}")

        logger.debug(f"Anchor offset = {w_offset}, {h_offset}")

        if pos._anchor[1] == 'max' :
            h_offset -= elem_size.height
        elif pos._anchor[1] == 'mid' :
            h_offset -= elem_size.height // 2
        elif pos._anchor[1] == 'min' :
            pass
        else :
            raise ValueError(f"Unknown anchor: {pos._anchor[1]}")

        logger.debug(f"element offset = {w_offset}, {h_offset}")

        # Check to make sure the element is fully in the output rec (if possible).
        if w_offset > output_rect.extent.width - elem_size.width - gutter:
            w_offset = output_rect.extent.width - elem_size.width - gutter

        if w_offset < gutter:
            w_offset = gutter

        if h_offset > output_rect.extent.height - elem_size.height - gutter:
            h_offset = output_rect.extent.height - elem_size.height - gutter

        if h_offset < gutter:
            h_offset = gutter

        logger.debug(f"final offset: {w_offset}, {h_offset}")
        return w_offset, h_offset

    
    def offsets_for_position(self, pos : position, elem_size : geometry, gutter : int) -> Tuple[int, int] :
        if not pos.valid():
            raise ValueError("Position is not valid")

        logger.debug(f"""Position Inputs :
 position = {pos.pos_str}
 elem_size = {elem_size.to_tuple()},
 gutter = {gutter}"""
    )
        
        if pos._side == 'pixel' :
            return self._pixel_offsets(pos, elem_size, gutter)

        ref_rect = self.parent.get_elem(pos._ref).bbox
        
        if pos._ref == 'cover' :
            gutter = 0
        elif pos._ref == 'border' :
            gutter = 0
            orig = ref_rect
            ref_rect = ref_rect.copy()
            if pos._side == 'left' :
                ref_rect.extent.width = orig.start.width - ref_rect.start.width
            elif pos._side == 'right' :
                ref_rect.start.width = orig.start.width + orig.extent.width
                ref_rect.extent.width = (ref_rect.extent.width - orig.extent.width) // 2
            elif pos._side == 'top' :
                ref_rect.extent.height = orig.start.height - ref_rect.start.height
            elif pos._side == 'bottom' :
                ref_rect.start.height = orig.start.height + orig.extent.height
                ref_rect.extent.height = ref_rect.extent.height - ref_rect.start.height

        logger.debug(f"Updated ref_rect = {ref_rect.to_tuple()}")
        
        # Calculate the offset
        if pos.w == 'min':
            width_offset = gutter
        elif pos.w == 'mid':
            width_offset = (ref_rect.extent.width - elem_size.width) // 2
        elif pos.w == 'max':
            width_offset = ref_rect.extent.width - elem_size.width - gutter

        if width_offset > ref_rect.extent.width - elem_size.width - gutter:
            width_offset = ref_rect.extent.width - elem_size.width - gutter

        if width_offset < 1:
            width_offset = 1

        if pos.h == 'min':
            height_offset = gutter
        elif pos.h == 'mid':
            height_offset = (ref_rect.extent.height - elem_size.height) // 2
        elif pos.h == 'max':
            height_offset = ref_rect.extent.height - elem_size.height - gutter

        if height_offset > ref_rect.extent.height - elem_size.height - gutter:
            height_offset = ref_rect.extent.height - elem_size.height - gutter

        if height_offset < 1:
            height_offset = 1

        logger.debug(f"Offsets = ({width_offset}, {height_offset})")

        # Match the references position
        width_offset += ref_rect.start.width
        height_offset += ref_rect.start.height

        logger.debug(f"Final offsets = ({width_offset}, {height_offset})")

        return (width_offset, height_offset)
