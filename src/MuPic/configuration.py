import argparse
import os
import yaml
from typing import Any, Set
import re

from .paths import resolve_path
from .settings import *
from .none_dict import NoneDict

import logging
logger = logging.getLogger(__name__)

# Defaults
IMAGE_HEIGHT = 1080
IMAGE_WIDTH = 1920
LOGO_SIZE = 200
TITLE_FONT_SIZE = 200
GUTTER_SIZE = 10

CONFIG_FILE_LIST : Set[str] = set()

def _build_default_config() -> Config :

    return Config(
        globals = GlobalSettings(GUTTER_SIZE, ''),
        output  = OutputSettings("", sizet(IMAGE_WIDTH, IMAGE_HEIGHT), '#000000', background = ''),
        cover   = CoverSettings('', 'min', 'min', 'square', None, 
                                BorderSettings('#000000', 0), margin=0),
        logo    = GraphicSettings('', LOGO_SIZE, 'black', position('right-bottom')),
        text_blocks  = []
    )

def _merge_blocks(old : List[TextSettings], new : List[dict]) -> List[TextSettings] :

    retlist : List[TextSettings] = []
    seen_names : Set[str] = set()
    for block in old :
        if  block.named() :
            for new_block in new :
                if new_block['name'] == block.name :
                    seen_names.add(new_block['name'])
                    block.merge(new_block)


        retlist.append(block)

    logger.debug(f"_merge_blocks: Seen names: {seen_names}")
    for new_block in new :
        if new_block['name'] == '' or new_block['name'] not in seen_names :
            # need to find a better way to do this
            block = NoneDict(new_block)
            font = block['font'] or ''
            bpos = block['position'] or 'center-center'
            swidth = block['stroke.width'] or 0
            scolor = block['stroke.color'] or '#000000'
            name = block['name'] or f'block_{len(retlist)}'
            settings = TextSettings(name, block['text'], block['size'] or 0, font, 
                                        position(bpos), 
                                        block['fill'], 
                                        StrokeSettings(scolor, swidth),
                                        rotation=block['rotation'] or 0)
            retlist.append(settings)

    return retlist



def _add_supplied_config(config : Config, new_cfg : NoneDict, parent_dir : str) -> Config :

    if new_cfg['include'] is not None :
        file = new_cfg['include']
        file = os.path.abspath(resolve_path(file, parent_dir))
        with open(file, "r") as f:
            included_config = yaml.safe_load(f)

        config = _add_supplied_config(config, NoneDict(included_config), os.path.dirname(file))


    config.globals.override('gutter', new_cfg['gutter'])
    config.globals.override('font', new_cfg['font'])

    config.output.override('path', new_cfg['output.path'])
    config.output.override('size', sizet.from_string(new_cfg['output.size']))
    config.output.override('color', new_cfg['output.color'])
    config.output.override('background', new_cfg['output.background'])

    config.cover.override('path', new_cfg['cover.path'])
    config.cover.override('align', new_cfg['cover.align'])
    config.cover.override('crop', new_cfg['cover.crop'])
    config.cover.override('fit', new_cfg['cover.fit'])
    config.cover.border.override('color', new_cfg['cover.border.color'])
    config.cover.border.override('width', new_cfg['cover.border.width'])
    config.cover.border.override('sides', new_cfg['cover.border.sides'])   
    config.cover.override('margin', new_cfg['cover.margin'])

    config.logo.override('path', new_cfg['logo.path'])
    config.logo.override('size', new_cfg['logo.size'])
    config.logo.override('mask', new_cfg['logo.mask'])
    config.logo.override('position', position(new_cfg['logo.position']))

    if new_cfg['text_blocks'] is not None :
        blocks = new_cfg['text_blocks']
        config.text_blocks = _merge_blocks(config.text_blocks, blocks)

    return config

def _add_args(config : Config, args : argparse.Namespace) :
    config.globals.override('gutter', args.gutter)
    config.globals.override('font', args.font)

    config.output.override('path', args.output_path)
    config.output.override('size', sizet.from_string(args.output_size))
    config.output.override('color', args.output_color)
    config.output.override('background', args.output_background)

    config.cover.override('path', args.cover_path)
    config.cover.override('align', args.cover_align)
    config.cover.override('crop', args.cover_crop)
    config.cover.override('fit', args.cover_fit)
    config.cover.border.override('color', args.cover_border_color)
    config.cover.border.override('width', args.cover_border_width)
    config.cover.override('margin', args.cover_margin)

    config.logo.override('path', args.logo)
    config.logo.override('size', args.logo_size)
    config.logo.override('mask', args.logo_mask)
    config.logo.override('position', position(args.logo_position))
    
    return config

def _get_default_font() :
    #import sys
    import platform
    #print(f"==== sys.platform: {sys.platform}")
    #print(f"==== platform: {platform.platform()}")
    if 'WSL2' in platform.platform():
        return '/mnt/c/Windows/Fonts/arial.ttf'
    else:
        return 'Arial'

def build_config(args : argparse.Namespace, config_path : str, print_config : bool) -> Config:

    retval = _build_default_config()

    if config_path is not None:
        if CONFIG_FILE_LIST :
            # use the resolver to find the file
            path = os.path.abspath(resolve_path(config_path))
        else :
            # At the top, so let the os decide.
            path = os.path.abspath(config_path)
        if path in CONFIG_FILE_LIST :
            raise RuntimeError(f"cycle detected in config file includes at {config_path}")
        CONFIG_FILE_LIST.add(path)
        with open(path, "r") as f:
            supplied_config = yaml.safe_load(f)

        retval = _add_supplied_config(retval, NoneDict(supplied_config), os.path.dirname(config_path))

    retval = _add_args(retval, args)

    # HELPER
    # Makes the code a littler cleaner. cover color is not
    # actually settable by the user.
    # Make sure we inherit the output color
    # even if overridden in the args.
    retval.cover.color = retval.output.color

    # set a default font that depends on the platform
    retval.globals.default('font', _get_default_font())

    # update the other fonts to use this if needed.
    for block in retval.text_blocks :
        block.default('font', retval.globals.font)

    if print_config :
        print("++++++ Using configuration:")
        dump = yaml.dump(retval, default_flow_style=False, sort_keys=False)
        dump = re.sub(r'\s?!![^\n]*\n', '\n', dump)
        print(dump)
        print("++++++")


    return retval

def validate_config(config : Config) -> bool :
    if not config.output.path_valid():
        logger.error("No output path specified")
        return False
    else :
        output_path = resolve_path(config.output.path)
        dirname = os.path.dirname(output_path)
        if dirname != "" and not os.path.exists(dirname) :
            logger.error(f"The directory {dirname} does not exist.")
            return False
        ext = (os.path.splitext(output_path)[1]).lower()
        if ext not in ('.png', '.jpeg', '.jpg', 'webp'):
            logger.error(f"Unsupported output file type: {ext}")
            return False
        config.output.path = output_path
        
    width, height = config.output.size.to_tuple()
    if width < 1 or height < 1:
        logger.error("Invalid output size")
        return False
    
    if config.output.valid_attr('background'):
        path = resolve_path(config.output.background)
        if not os.path.isfile(path):
            logger.error(f"The background image file {path} does not exist.")
            return False
        config.output.background = path

    if config.cover.path_valid():
        cover_path = resolve_path(config.cover.path)
        if not os.path.isfile(cover_path):
            logger.error(f"The cover image file {cover_path} does not exist.")
            return False
        config.cover.border.validate()
        config.cover.path = cover_path
    

    if config.logo.path_valid():
        logo_path = resolve_path(config.logo.path)
        if not os.path.isfile(logo_path):
            logger.error(f"The logo image file {logo_path} does not exist.")
            return False
        if config.logo.size < 0:
            logger.error("Logo size must be >= 0")
            return False
        if config.logo.mask not in ('self', 'black', 'alpha', 'auto', 'none'):
            logger.error("Invalid logo mask value")
            return False
        config.logo.path = logo_path
        
    if config.globals.gutter < 0:
        logger.error("Gutter must be >= 0")
        return False
    
    if config.cover.border.width < 0:
        logger.error("Cover border width must be >= 0")
        return False

    if config.cover.crop not in ('min', 'mid', 'max'):
        logger.error(f"Invalid cover crop value {config.cover.crop}")
        return False

    if config.cover.align not in ('min', 'mid', 'max'):
        logger.error(f"Invalid cover align value {config.cover.align}")
        return False

    for block in config.text_blocks:
        block.validate()

    return True
