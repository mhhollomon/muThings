from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..music_image import MusicImage

from ..geometry import sizet, rect, point
from ..position import position
from ..settings import WidthSettings

import logging
logger = logging.getLogger(__name__)

#---------------------------------------------------------

class ImageElement :

    def __init__(self, name : str, parent : 'MusicImage', add_to_parent : bool = True) :
        self.name = name
        self.parent = parent
        self.bbox : dict[str, rect] = {}
        self.generated = False

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


    def border_widths(self) -> WidthSettings | None :
        raise NotImplementedError

    def margin_widths(self) -> WidthSettings | None :
        raise NotImplementedError

#-----------------------------------------------------------------------------

    def set_bbox(self, sub : str, new_bbox : rect) -> None :
    
        if sub not in ('full', 'border', 'margin', 'content') :
            raise ValueError(f"incorrect bbox subelement {sub} in {self.name}")

        logger.debug(f"setting {self.name} {sub} bbox to {new_bbox}")
        self.bbox[sub] = new_bbox

#-----------------------------------------------------------------------------

    def get_bbox(self, sub : str, piece : str | None = None) :
        """
        Returns the element's bbox. 
        """
        logger.debug(f"getting {self.name} {sub} bbox (piece={piece})")
        if not self.generated :
            raise ValueError(f"Element {self.name} has not been generated yet")
        if sub not in self.bbox :
            raise ValueError(f"Element {self.name} has no bbox for sub {sub}")

        cbox = self.bbox[sub]
        
        if piece is None :
            logger.debug(f"returning {self.name} {sub} bbox {cbox}")
            return cbox.copy()

        if sub == 'border' :
            widths = self.border_widths()
        elif sub == 'margin' :
            widths = self.margin_widths()
        else :
            raise ValueError(f"Invalid sub {sub}")

        if widths is None :
            raise ValueError(f"Element {self.name} has no {sub} widths")

        if piece == 'left' :
            if widths.l == 0 :
                raise ValueError(f"Left {sub} is 0 for element {self.name}")
            origin = cbox.origin.copy()
            extent = sizet(widths.l, cbox.extent.height)
        elif piece == 'right' :
            if widths.r == 0 :
                raise ValueError(f"Right {sub} is 0 for element {self.name}")
            origin = point(cbox.origin.x + cbox.extent.width - widths.r, cbox.origin.y)
            extent = sizet(widths.r, cbox.extent.height)
        elif piece == 'top' :
            if widths.t == 0 :
                raise ValueError(f"Top {sub} is 0 for element {self.name}")
            origin = cbox.origin
            extent = sizet(cbox.extent.width, widths.t)
        elif piece == 'bottom' :
            if widths.b == 0 :
                raise ValueError(f"Bottom {sub} is 0 for element {self.name}")
            origin = point(cbox.origin.x, cbox.origin.y + cbox.extent.height - widths.b)
            extent = sizet(cbox.extent.width, widths.b)
        else :
            raise ValueError(f"Invalid piece specifier {piece}")

        return rect(origin, extent)




#-----------------------------------------------------------------------------

    def _attach_offsets(self, pos : position, elem_size : sizet) -> point:
        ref_elem = self.parent.get_elem(pos.target.element)
        ref_bbox = ref_elem.get_bbox(sub=pos.target.sub, piece=pos.target.piece)

        logger.debug(f"attach : ref_bbox = {ref_bbox}")
        logger.debug(f"attach : elem_size = {elem_size}")

        return ref_bbox.origin


#-----------------------------------------------------------------------------

    def _overlay_offsets(self, pos : position, elem_size : sizet) -> point :
        ref_elem = self.parent.get_elem(pos.target.element)
        ref_bbox = ref_elem.get_bbox(sub=pos.target.sub, piece=pos.target.piece)

        logger.debug(f"overlay offsets - ref_bbox = {ref_bbox}")

        offset_pt = point(
            int(ref_bbox.extent.width * (pos.pos.x / 100.0)),
            int(ref_bbox.extent.height * (pos.pos.y / 100.0))
        )

        attach_point = ref_bbox.origin + offset_pt
        logger.debug(f'overlay offsets - attach_point = {attach_point}')

        anchor = pos.anchor.x
        adjust_fact = 0 if anchor == 'min' else 0.5 if anchor == 'mid' else 1
        adjust_x = int(elem_size.width * adjust_fact)

        anchor = pos.anchor.y
        adjust_fact = 0 if anchor == 'min' else 0.5 if anchor == 'mid' else 1
        adjust_y = int(elem_size.height * adjust_fact)

        adjustment = (adjust_x, adjust_y)
        logger.debug(f'overlay offsets - adjustment = {adjustment}')

        adjusted_pt = attach_point - adjustment
        logger.debug(f'overlay offsets - adjusted_pt = {adjusted_pt}')
       
        anchor = pos.anchor.x
        if anchor == 'min' :
            tweak_x = pos.offset - (adjusted_pt.x - ref_bbox.origin.x)
            tweak_x = 0 if tweak_x < 0 else tweak_x
        elif anchor == 'max' :
            tweak_x = -(pos.offset - (ref_bbox.end.x - (adjusted_pt.x + elem_size.width)))
            tweak_x = 0 if tweak_x > 0 else tweak_x
        else :
            tweak_x = 0

        anchor = pos.anchor.y
        if anchor == 'min' :
            tweak_y = pos.offset - (adjusted_pt.y - ref_bbox.origin.y)
            tweak_y = 0 if tweak_y < 0 else tweak_y
        elif anchor == 'max' :
            tweak_y = -(pos.offset - (ref_bbox.end.y - (adjusted_pt.y + elem_size.height)))
            tweak_y = 0 if tweak_y > 0 else tweak_y
        else :
            tweak_y = 0

        offset_tweak = (tweak_x, tweak_y)
        logger.debug(f'overlay offsets - offset_tweak = {offset_tweak}')

        final_offset = adjusted_pt + offset_tweak
        logger.debug(f'overlay offsets - final_offset = {final_offset}')

        return final_offset



#-----------------------------------------------------------------------------

    def offsets_for_position(self, pos : position, elem_size : sizet) -> point :

        logger.debug(f"""Position Inputs :
 position = {pos}
 elem_size = {elem_size.to_tuple()},
 """
    )
        
        if pos.ptype == 'attach' :
            return self._attach_offsets(pos, elem_size)
        else :
            return self._overlay_offsets(pos, elem_size)

