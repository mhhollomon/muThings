from argparse import Namespace
from copy import deepcopy
from typing import Any, NamedTuple

from lark import Lark, Transformer, v_args, Token, logger as lark_logger
import logging

from .paths import resolve_path
from .parsers import get_parser

lark_logger.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

from .settings import *
from .utils import dictmerge

from pathlib import Path

def _get_default_font() :
    #import sys
    import platform
    if 'WSL2' in platform.platform():
        return '/mnt/c/Windows/Fonts/arial.ttf'
    else:
        return 'Arial'


class OptionTuple(NamedTuple) :
    name : str
    value : Any

class DefaultOption(NamedTuple) :
    name : str
    value : Any

#--------------------------------------------------------------------------

class Configuration(Transformer) :
    context : Path
    elements : List[ImageSettings | TextSettings]

    def __init__(self, config_file : str | Path) :
        super().__init__()
        self._config_file = Path(config_file)

        self.context = self._config_file.parent

    def read_config(self, args : Namespace) -> Settings :
        settings_dict = self._get_settings()

        if 'output_path' in args and args.output_path is not None :
            settings_dict['output']['path'] = args.output_path

        settings_dict = self._handle_defaults(settings_dict)

        return Settings(settings_dict)

    def _handle_defaults(self, input : dict) -> dict :
        defaults = { 'font' : _get_default_font(), 'fill' : 'white' }
        defaults = dictmerge(defaults, input['defaults'])
        input['defaults'] = defaults
        logger.debug(f"updated default settings = {defaults}")
        new_ele = []
        for i, e in enumerate(input['elements'] ):
            if 'name' not in e :
                e['name'] = f"element_{i}"

            if e['type'] == 'text' :
                z = deepcopy(defaults)
                dictmerge(z, e)
                new_ele.append(z)
            elif e['type'] == 'image' :
                if 'path' in e :
                    e['path'] = resolve_path(e['path'], self.context)
                new_ele.append(e)
        input['elements'] = new_ele

        # - background path
        if 'background' in input['output'] :
            input['output']['background'] = resolve_path(input['output']['background'], self.context)

        return input

    def _get_settings(self) -> dict[str, Any] :
        """Parse the configuration file.
        This is the lower level routine that actually does the parsing.
        It returns a dictionary of setting. That can be merged with includes, etc."""

        parser = get_parser('config')

        with open(self._config_file, 'r') as f :
            text = f.read()

        tree = parser.parse(text)
        settings = self.transform(tree)
        if 'include' in settings :
            base_settings = settings['include']
            del settings['include']
            settings = dictmerge(base_settings, settings)
            self._reconcile_elements(settings)
        return settings

    def _reconcile_elements(self, settings : dict[str, Any]) -> None:
        """Run through the element list merging later copies of the same name/type
        with earlier ones."""
        new_list = []
        seen : set[int] = set()
        for index, e in enumerate(settings['elements']) :
            if index in seen :
                continue
            if 'name' in e  and index < len(settings['elements'])-1 :
                other = next(((i, x) for i, x in enumerate(settings['elements'][index+1:]) if 'name' in x and x['name'] == e['name']
                               and x['type'] == e['type']), None)
                if other is None :
                    new_list.append(e)
                else :
                    seen_index = other[0] + index+1
                    seen.add(seen_index)
                    new_e = deepcopy(e)
                    new_e = dictmerge(new_e, other[1])
                    new_list.append(new_e)
                    seen.add(index)
            else :
                new_list.append(e)

            # Run through the new list and make sure there aren't two elements of the same
            # name.
            name_seen : set[str] = set()
            for i, e in enumerate(new_list) :
                if 'name' in e :
                    if e['name'] in name_seen :
                        raise ValueError(f"Duplicate element name: {e['name']}")
                    name_seen.add(e['name'])

        settings['elements'] = new_list

    def _util_consolidate(self, stype : str, children : list, extras:dict = {}) -> OptionTuple:
        """Turns a list of OptionTuples into a dictionary and returns an OptionTuple.
        Checks for duplicates."""

        settings = {**extras}
        for child in children :
            if isinstance(child, OptionTuple) :
                if child.name in settings :
                    raise ValueError(f"Duplicate {stype} statement: {child}")
                
                settings[child.name] = child.value
            else :
                raise ValueError(f"Invalid {stype} statement: {child}")

        return OptionTuple(stype, settings)
    
    #--------------------------------------------
    # Lark Transform routines
    #--------------------------------------------

    def __default__(self, data, children, meta) :
        if data.endswith('_option') :
            if data.endswith('_int_option') :
                data = data[:-11]
                return OptionTuple(data, int(children[0].value))
            else :
                data = data[:-7]
                value = children[0].value if isinstance(children[0], Token) else children[0]
                return OptionTuple(data, value)
            
        elif data.endswith('_spec') :
            data = data[:-5]
            return self._util_consolidate(data, children)

        elif data.endswith('_stmt') :
            data = data[:-5]
            return self._util_consolidate(data, children)

        return super().__default__(data, children, meta)

    def ESCAPED_STRING(self, token : Token) -> Token :
        if token.value.startswith('"') :
            token.value = token.value[1:-1]
        return token

    def STRING_VALUE(self, token : Token) -> Token :
        if token.value.startswith('"') :
            token.value = token.value[1:-1]
        return token

    def mupic_config_file(self, children) -> dict:
        settings = {'defaults':{}, 'elements':[] }
        for child in children :
            if child is None :
                continue
            if isinstance(child, OptionTuple) :
                if child.name in ('text', 'image'):
                    settings['elements'].append(child.value)
                else :
                    settings[child.name] = child.value
            elif isinstance(child, DefaultOption) :
                settings['defaults'][child.name] = child.value
            else :
                raise ValueError(f"Invalid top-level statement: {child}")

        return settings

    @v_args(inline=True)
    def default_stmt(self, name : Token, value : Token) :
        name = name.value
        dvalue = value.value
        # if dvalue.startswith('"') :
        #     dvalue = dvalue[1:-1]
        return DefaultOption(name, dvalue)

    @v_args(inline=True)
    def size_2d_option(self, value : Token) -> OptionTuple:
        return OptionTuple('size', sizet(value.value))
    
    @v_args(inline=True)
    def one_side(self, side : Token, value : Token) -> OptionTuple:
        return OptionTuple(side.value, value.value)
        

    def width_spec(self, children) -> OptionTuple :
        settings = {}
        if len(children) == 1 and isinstance(children[0], Token) :
            size = int(children[0].value)
            settings = {'l':size, 'r':size, 't':size, 'b':size}
        else :
            for child in children :
                if isinstance(child, OptionTuple) :
                    settings[child.name] = int(child.value)
                else :
                    raise ValueError(f"Invalid width spec: {child}")
        return OptionTuple('width', settings)

    def image_stmt(self, children) -> OptionTuple:
        settings = self._util_consolidate('image', children[1:], extras={'type':'image'})
        if children[0] is not None : 
            name = children[0].value
            if name.startswith('"') :
                name = name[1:-1]
            settings.value['name'] = name
        return settings

    def text_stmt(self, children) -> OptionTuple:
        settings = self._util_consolidate('text', children[1:], extras={'type':'text'})
        if children[0] is not None : 
            name = children[0].value
            if name.startswith('"') :
                name = name[1:-1]
            settings.value['name'] = name
        return settings

    @v_args(inline=True)
    def include_stmt(self, path : str) :
        logger.debug(f"=== include_stmt given path: '{path}'")
        if path.startswith('"') :
            path = path[1:-1]

        full_path = resolve_path(path, self.context)
        logger.debug(f"=== include_stmt resolved path: '{full_path}'")
        if not full_path.is_file() :
            raise ValueError(f"include file '{full_path}' does not exist")

        xform = Configuration(full_path)
        cfg = xform._get_settings()

        return OptionTuple('include', cfg)
