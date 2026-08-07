from typing import TYPE_CHECKING, Any, Tuple
if TYPE_CHECKING:
    from ..music_image import MusicImage

from ..position import geom, position, rect

import logging
logger = logging.getLogger(__name__)

#---------------------------------------------------------

class ImageElement :
    generated = False
    _bbox = rect(geom(0,0), geom(0,0))

    def __init__(self, name : str, parent : 'MusicImage', add_to_parent : bool = True) :
        self.name = name
        self.parent = parent
        self._settings : Any = {}

        if add_to_parent :
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
    def bbox(self, bbox : rect) :
        if bbox is None :
            raise ValueError("ImageElement bbox cannot be None")
        if bbox.extent.width == 0 or bbox.extent.height == 0 :
            raise ValueError("ImageElement bbox cannot be empty")
        logger.debug(f"Setting bbox for {self.name} to {bbox}")
        self._bbox = bbox
        self.generated = True

    def get_bbox(self, **kwargs) :
        """
        Returns the element's bbox. 
        Basically here to allow overrides in subclasses.
        """
        return self.bbox


    def _pixel_offsets(self, pos : position, elem_size : geom, gutter : int) -> Tuple[int, int] :

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
        if pos.anchor[0] == 'max' :
            w_offset -=  elem_size.width 
        elif pos.anchor[0] == 'mid' :
            w_offset -= elem_size.width // 2
        elif pos.anchor[0] == 'min' :
            pass
        else :
            raise ValueError(f"Unknown anchor: {pos.anchor[0]}")

        logger.debug(f"Anchor offset = {w_offset}, {h_offset}")

        if pos.anchor[1] == 'max' :
            h_offset -= elem_size.height
        elif pos.anchor[1] == 'mid' :
            h_offset -= elem_size.height // 2
        elif pos.anchor[1] == 'min' :
            pass
        else :
            raise ValueError(f"Unknown anchor: {pos.anchor[1]}")

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

    def _attach_offsets(self, pos : position, elem_size : geom, gutter : int) -> Tuple[int, int]:
        ref_bbox =  self.parent.get_elem(pos.ref).bbox

        logger.debug(f"attach : ref_bbox = {ref_bbox}")
        logger.debug(f"attach : elem_size = {elem_size}")

        side = pos.side[0].lower()
        logger.debug(f"attach : side = {side}")
        offset = int(pos.offset)
        logger.debug(f"attach : offset = {offset}")

        if side == 'l' :
            w_ref = ref_bbox.start.width
            l_ref = ref_bbox.start.height + ref_bbox.extent.height // 2
            standoff = geom(-offset, 0)
            ele_offset = geom(-elem_size.width, -elem_size.height // 2)
        elif side == 'r' :
            w_ref = ref_bbox.start.width + ref_bbox.extent.width
            l_ref = ref_bbox.start.height + ref_bbox.extent.height // 2
            standoff = geom(offset, 0)
            ele_offset = geom(0, -elem_size.height // 2)
        elif side == 't' :
            w_ref = ref_bbox.start.width + ref_bbox.extent.width // 2
            l_ref = ref_bbox.start.height
            standoff = geom(0, -offset)
            ele_offset = geom(elem_size.width // 2, 0)
        elif side == 'b' :
            w_ref = ref_bbox.start.width + ref_bbox.extent.width // 2
            l_ref = ref_bbox.start.height + ref_bbox.extent.height
            standoff = geom(0, offset)
            ele_offset = geom(-elem_size.width // 2, 0)
        else :
            raise ValueError(f"Invalid side: {side}")

        ref_point = geom(w_ref, l_ref)
        logger.debug(f"attach : ref_point = {ref_point.to_tuple()}")
        logger.debug(f"attach : standoff = {standoff.to_tuple()}")

        point = ref_point + standoff + ele_offset

        logger.debug(f"attach : point = {point.to_tuple()}")

        return point.to_tuple()
    
    def offsets_for_position(self, pos : position, elem_size : geom, 
                             gutter : int, ex_gutter : int = 0) -> Tuple[int, int] :
        if not pos.valid():
            raise ValueError("Position is not valid")

        logger.debug(f"""Position Inputs :
 position = {pos.pos_str}
 elem_size = {elem_size.to_tuple()},
 gutter = {gutter}
 ex_gutter = {ex_gutter}
 """
    )
        
        if pos.ptype == 'pixel' :
            return self._pixel_offsets(pos, elem_size, gutter)
        elif pos.ptype == 'attach' :
            return self._attach_offsets(pos, elem_size, ex_gutter)

        ref_elem = self.parent.get_elem(pos.ref)

        if pos.ref == 'border' :
            ref_rect = ref_elem.get_bbox(side=pos.side[0])
        else :
            ref_rect = ref_elem.bbox
        
        if pos.ref == 'cover' :
            gutter = 0
        elif pos.ref == 'border' :
            gutter = ex_gutter

        logger.debug(f"ref_rect = {ref_rect.to_tuple()}")
        
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
