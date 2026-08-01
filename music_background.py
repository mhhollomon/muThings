#!/usr/bin/env python

import os
import sys
import logging
import logging.config

from lib.logconfig import LOGGING_CONFIG

logger = logging.getLogger('app')

import argparse
from typing import Any, Tuple

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from lib.configuration import Config, TextSettings, build_config, geometry, validate_config
from lib.position import rectangle
from lib.paths import resolve_path, set_resolve_path

COVER_RECT = rectangle(geometry(0,0), geometry(0,0))
BORDER_RECT = rectangle(geometry(0,0), geometry(0,0))



def _get_text_size(text : str, font : ImageFont.FreeTypeFont) -> geometry:
    img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(img)
    box = draw.multiline_textbbox((0,0), text=text, font=font)
    size = geometry(int(box[2]-box[0]), int(box[3]-box[1]))
    return size


#--------------------------------------------------------------------------------
# LOGO
#--------------------------------------------------------------------------------

def _compute_mask(img : Image.Image, mask : str, luminance_img : Image.Image | None = None) -> Image.Image | None :
    
    if luminance_img is None:
        luminance_img = img.convert('L')

    if mask == 'self':
        # use the luminance of the image as-is
        gray_img = luminance_img

    elif mask == 'black':
        # clamp the luminance to black
        gray_img = luminance_img.point(lambda x : 0 if x < 10 else 255) # type: ignore

    elif mask == 'none' :
        # no mask
        gray_img = None

    elif mask == 'alpha' :
        # use the alpha channel
        gray_img = img

    else : # auto
        # use alpha if it is there otherwise use black
        if 'A' in img.mode or 'a' in img.mode:
            gray_img = img
        else:
            gray_img = _compute_mask(img, 'black', luminance_img)

    return gray_img

def _build_logo(config : Any) -> Tuple[Image.Image, Image.Image | None] | None :
    logo_config = config.logo

    if not logo_config.path_valid():
        return None

    logo_path : str = resolve_path(logo_config.path)

    with Image.open(logo_path) as logo_img:

        logo_width, logo_height = logo_img.size
        needed_size : int = logo_config.size

        if logo_width > logo_height:
            # Landscape
            new_size = (needed_size, int( needed_size * (logo_height / logo_width)))
        else:
            # Portrait
            new_size = (int(needed_size * (logo_width / logo_height)), needed_size)

        logo_img = logo_img.resize(new_size)

        gray_img = _compute_mask(logo_img, logo_config.mask)


        return (logo_img, gray_img)
    
def _add_logo(config : Any, output_img : Image.Image) -> None :
    logo_img = _build_logo(config)
    if logo_img is None:
        logger.info("Skipping logo")
        return
    
    logger.info("Adding logo")
    logo_img, mask_img = logo_img
    logo_width, logo_height = logo_img.size
    output_size = config.output.size
    position = config.logo.position

    offsets = position.offsets(        
        output_rect=rectangle(geometry(0,0), output_size),
        cover_rect=COVER_RECT,
        border_rect=BORDER_RECT,
        elem_size=geometry(logo_width, logo_height), 
        gutter=config.globals.gutter)

    # Paste the logo
    output_img.paste(logo_img, offsets, mask=mask_img)

#--------------------------------------------------------------------------------
# COVER
#--------------------------------------------------------------------------------
def _cover_square(config :Any, ornt : int) -> Image.Image :
    cover_cfg = config.cover

    def other(o : int) -> int :
        return 1 - o

    required_size = config.output.size
    cover_side = required_size[ornt]
    logger.debug(f"Cover side: {cover_side}")
    crop = cover_cfg.crop
    bg_color = cover_cfg.color

    cover_img = Image.open(resolve_path(cover_cfg.path))


    original_width, original_height = cover_img.size
    logger.debug(f"Original size: {original_width}x{original_height}")
    aspect_ratio = cover_img.size[other(ornt)] / cover_img.size[ornt]

    # Calculate the new height while keeping the aspect ratio
    new_dimension = int(cover_side * aspect_ratio)
    logger.debug(f"Aspect ratio: {aspect_ratio}, new dimension: {new_dimension}")

    new_size = [0, 0]
    new_size[ornt] = cover_side
    new_size[other(ornt)] = new_dimension

    logger.debug(f"New size: {new_size}")
    # Resize the image
    cover_img = cover_img.resize(new_size)

    # Crop the image if necessary
    if new_dimension > cover_side:
        if crop == 'min':
            offset = 0
        elif crop == 'mid':
            offset = (new_dimension - cover_side) // 2
        elif crop == 'max':
            offset = (new_dimension - cover_side)
        else :
            raise ValueError(f"Invalid crop value: {crop}")

        if ornt :
            box = (offset, 0, cover_side + offset, cover_side)
        else :
            box = (0, offset, cover_side, cover_side + offset)

        logger.debug(f"Cropping Box: {box}")
        cover_img = cover_img.crop(box)

    elif new_dimension < cover_side:
        box_img = Image.new("RGB", (cover_side, cover_side), bg_color)
        if crop == 'min':
            offset = 0
        if crop == 'mid':
            offset = (cover_side - new_dimension) // 2
        elif crop == 'max':
            offset = (cover_side - new_dimension)

        if ornt :
            origin = (offset, 0)
        else :
            origin = (0, offset)

        logger.debug(f"Paste Origin: {origin}")
        box_img.paste(cover_img, origin)
        cover_img = box_img

    return cover_img

def _landscape_cover_fit(config : Any) -> Image.Image:
    cover_cfg = config.cover

    required_size = config.output.size
    crop = cover_cfg.crop

    cover_img = Image.open(resolve_path(cover_cfg.path))

    orig_width, orig_height = cover_img.size
    aspect_ratio = orig_width / orig_height

    # try maxxing width first
    new_width = required_size.width
    new_height = int(new_width / aspect_ratio)
    if new_height < required_size.height:
        new_width = int(required_size.height * aspect_ratio)
        new_height = required_size.height
    
    cover_img = cover_img.resize((new_width, new_height))
    if new_height > required_size.height:
        if crop == 'min':
           height_offset = 0
        elif crop == 'mid':
            height_offset = (new_height - required_size.height) // 2
        elif crop == 'max':
            height_offset = new_height - required_size.height
    else :
        height_offset = 0

    if new_width > required_size.width:
        if crop == 'min':
            width_offset = 0
        elif crop == 'mid':
            width_offset = (new_width - required_size.width) // 2
        elif crop == 'max':
            width_offset = new_width - required_size.width
    else :
        width_offset = 0

    if width_offset != 0 or height_offset != 0:
        box = (width_offset, height_offset, width_offset + required_size.width,
               height_offset + required_size.height)
        cover_img = cover_img.crop(box)

    return cover_img

def _portrait_cover_fit(config : Any) -> Image.Image:
    cover_cfg = config.cover

    required_size = config.output.size
    crop = cover_cfg.crop

    cover_img = Image.open(resolve_path(cover_cfg.path))

    orig_width, orig_height = cover_img.size
    aspect_ratio = orig_height / orig_width

    # try maxxing width first
    new_height = required_size.height
    new_width = int(new_height * aspect_ratio)
    if new_width < required_size.width:
        new_height = int(required_size.width / aspect_ratio)
        new_width = required_size.width
    
    cover_img = cover_img.resize((new_width, new_height))
    if new_width > required_size.width:
        if crop == 'min':
           width_offset = 0
        elif crop == 'mid':
            width_offset = (new_width - required_size.width) // 2
        elif crop == 'max':
            width_offset = new_width - required_size.width
    else :
        width_offset = 0

    if new_height > required_size.height:
        if crop == 'min':
            height_offset = 0
        elif crop == 'mid':
            height_offset = (new_height - required_size.height) // 2
        elif crop == 'max':
            height_offset = new_height - required_size.height
    else :
        height_offset = 0

    if width_offset != 0 or height_offset != 0:
        box = (width_offset, height_offset, width_offset + required_size.width,
               height_offset + required_size.height)
        cover_img = cover_img.crop(box)

    return cover_img

def _add_cover(config : Any, output_img : Image.Image) -> None :

    cover_cfg = config.cover
    if not cover_cfg.path_valid():
        logger.info("Skipping cover")
        return

    output_size = config.output.size

    logger.info("Adding cover")

    if cover_cfg.fit == 'cover':
        if output_size.is_landscape() :
            cover_img = _landscape_cover_fit(config)
        else :
            cover_img = _portrait_cover_fit(config)
    else:
        cover_img = _cover_square(config,
                      int(output_size.is_landscape()))

    cover_width, cover_height = cover_img.size

    logger.debug(f"Cover Size before margin or border: {cover_width}x{cover_height}")

    border_size = 0

    margin_size = cover_cfg.margin
    logger.debug(f"Cover Margin Size: {margin_size}")

    if cover_cfg.border.exists() :
        border_size = cover_cfg.border.width
        border_color = cover_cfg.border.color
        border_img = Image.new("RGB", (cover_width - margin_size * 2, cover_height - margin_size * 2), border_color)
        logger.debug(f"Border Image Size: {border_img.size}")
        cover_img = cover_img.resize(
            (cover_width - border_size * 2 - margin_size * 2, 
             cover_height - border_size * 2 - margin_size * 2))
        logger.debug(f"Cover Image New Size: {cover_img.size}")
        # border_img already has the margin_size baked in so we only need
        # to offset by the border_size.
        border_img.paste(cover_img, (border_size, border_size))
        cover_img = border_img

    if cover_cfg.align == 'min':
        position = (0 + margin_size, 0 + margin_size)
    elif cover_cfg.align == 'mid':
        if output_size.is_landscape():
            position = (((output_size.width - cover_img.width) // 2) + margin_size, 0 + margin_size)
        else:
            position = (0 + margin_size, ((output_size.height - cover_img.height) // 2) + margin_size)
    elif cover_cfg.align == 'max':
        if output_size.is_landscape():
            position = (output_size.width - cover_img.width + margin_size, 0 + margin_size)
        else:
            position = (0 + margin_size, output_size.height - cover_img.height + margin_size)
    else:
        raise Exception(f"Invalid cover alignment: {cover_cfg.align}")

    # Paste the cover
    logger.debug(f"Cover Position: {position}")
    output_img.paste(cover_img, position)

    global COVER_RECT, BORDER_RECT

    # position already has the margin taken into account.
    # cover_img does not have the margin in it. so do not need to subtract.
    COVER_RECT = rectangle(geometry(position[0] + border_size + margin_size, position[1] + border_size + margin_size), 
                           geometry(cover_img.width - 2 * border_size, cover_img.height - 2 * border_size))

    # position already has the margin taken into account.
    # cover_img does not have the margin in it. so do not need to subtract.
    BORDER_RECT = rectangle(geometry(position[0], position[1]), 
                            geometry(cover_img.width, cover_img.height))

#--------------------------------------------------------------------------------
# TITLE
#--------------------------------------------------------------------------------

def text_to_image(config : Config, text_cfg : TextSettings, text_type : str, output_img : Image.Image) -> None :
    if not text_cfg.has_text():
        logger.info(f"Skipping {text_type} text")
        return
    
    logger.info(f"Adding {text_type} text")

    output_size = config.output.size

    draw = ImageDraw.Draw(output_img)
    title_font = ImageFont.truetype(text_cfg.font, text_cfg.size)
    text_size = _get_text_size(text_cfg.text, title_font)

    gutter = config.globals.gutter

    if output_size.is_landscape() and not output_size.is_square():
        max_text_width = output_size.width - output_size.height - (gutter * 2)
    else:
        max_text_width = output_size.width - (gutter * 2)

    if (text_size.width > max_text_width):
        # The text is too long, so we need to scale it down
        new_size = text_cfg.size * (max_text_width / text_size.width)
        title_font = ImageFont.truetype(text_cfg.font, new_size)
        text_size = _get_text_size(text_cfg.text, title_font)

    offsets = text_cfg.position.offsets(
        output_rect=rectangle(geometry(0,0), output_size),
        cover_rect=COVER_RECT,
        border_rect=BORDER_RECT,
        elem_size=text_size, 
        gutter=gutter)

    if text_cfg.stroke.exists():
        stroke_params = { 'stroke_fill' : text_cfg.stroke.color,
                          'stroke_width' : text_cfg.stroke.width }
    else :
        stroke_params = {}

    logger.debug(f"Text Position: {offsets}")
    if "\n" in text_cfg.text:
        draw.multiline_text(offsets, text_cfg.text, font=title_font, fill=text_cfg.fill, **stroke_params)
    else :
        draw.text(offsets, text_cfg.text, font=title_font, fill=text_cfg.fill, anchor='lt', **stroke_params)

#--------------------------------------------------------------------------------
# TOP LEVEL FUNCTION
#--------------------------------------------------------------------------------

def build_image(config : Config) :
    # Open the image
    output_path = config.output.path
    output_size = config.output.size

    if config.output.valid_attr('background'):
        logger.info("Using background image")
        output_img = Image.open(resolve_path(config.output.background))
        output_img = output_img.resize(output_size.to_tuple())
        if output_img.mode != 'RGB':
            output_img = output_img.convert('RGB')
    else:
        logger.info("Creating color background")
        output_img = Image.new("RGB", output_size.to_tuple(), color=config.output.color)


    _add_cover(config, output_img)

    _add_logo(config, output_img)

    text_to_image(config, config.title, 'track', output_img)
    text_to_image(config, config.album, 'album', output_img)

    for i, block in enumerate(config.text_blocks):
        text_to_image(config, block, f'block[{i}]', output_img)

    # Save the image
    output_img.save(resolve_path(output_path))

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    # --- Application Level Arguments ---
    parser.add_argument("--config_file", "-c", type=str, required=False, default=None,
                        help="yaml file containing configuration values. Most can then be overridden on the command line.")
    parser.add_argument("--log_level", "-l", type=str, required=False, default=None)

    # --- GLOBAL ARGUMENTS ---
    parser.add_argument("--gutter", type=int, required=False, default=None,
                        help="The size of the gutter between the edge of the output image and the title."
                        " If not specified, the gutter will be 10 pixels.")
    parser.add_argument("--font", type=str, required=False, default=None,
                        help="The default font to use for for any text."
                        " If not specified, the font will be the default system font.")

    # --- OUTPUT ARGUMENTS ---
    parser.add_argument("--output_path", type=str, required=False, default=None,
                        help="The path and filename on to which to write the output." 
                        " The extension given on the filename will be used to determine the format.")
    parser.add_argument("--output_size", type=str, required=False, default=None,
                        help="The size of the output image. Must be in the format 'WIDTHxHEIGHT'.")
    parser.add_argument("--output_color", type=str, required=False, default=None,
                        help="The background color of the output image.")
    parser.add_argument("--output_background", type=str, required=False, default=None,
                        help="The image that will fill the background of the output image.")

    # --- COVER ARGUMENTS ---
    parser.add_argument("--cover_path", type=str, required=False, default=None,
                        help="The path to the cover image.")
    parser.add_argument("--cover_align", type=str, required=False, default=None,
                        choices=['min', 'mid', 'max'], 
                        help="The alignment of the cover image. Default is 'min'")
    parser.add_argument("--cover_crop", type=str, required=False, default=None,
                        choices=['min', 'mid', 'max'], 
                        help="The crop of the cover image. Default is 'min'")
    parser.add_argument("--cover_fit", type=str, required=False, default=None,
                        choices=['square', 'cover'], 
                        help="The fit of the cover image. Default is 'square'")
    parser.add_argument("--cover_border_color", type=str, required=False, default=None,
                        help="The color of the border around the cover image.")
    parser.add_argument("--cover_border_width", type=int, required=False, default=None,
                        help="The width of the border around the cover image.")
    parser.add_argument("--cover_margin", type=int, required=False, default=None,
                        help="The width of the clear margin around the cover image and border.")

    # --- LOGO ARGUMENTS ---
    parser.add_argument("--logo", type=str, required=False, default=None,
                        help="The path to the logo image. If not specified, no logo will be added.")
    parser.add_argument("--logo_size", type=int, default=None, required=False,
                        help="The size of the logo image. If not specified, the logo will be scaled to 200 pixels.")
    parser.add_argument("--logo_mask", type=str, required=False, default=None,
                        choices=['self', 'black'], 
                        help="The mask algorithm to use for the logo image. Default is 'black'.")
    parser.add_argument("--logo_position", type=str, required=False, default='',
                        help="The position of the logo on the output image. Must be in the format 'WIDTH-HEIGHT'.")

    # --- TRACK TITLE ARGUMENTS ---
    parser.add_argument("--title", type=str, required=False, default=None,
                        help="The text to display in the title. If not specified, no title will be added.")
    parser.add_argument("--title_size", type=int, required=False, default=None,
                        help="The size of the title text. If not specified, the title will be scaled to 200 pixels.")
    parser.add_argument("--title_font", type=str, required=False, default=None,
                        help="The font to use for the title text. If not specified, the default font will be used.")
    parser.add_argument("--title_position", type=str, required=False, default='',
                        help="The position of the title on the output image. Must be in the format 'WIDTH-HEIGHT'.")
    parser.add_argument("--title_fill", type=str, required=False, default=None,
                        help="The fill color for the title text.")
    parser.add_argument("--title_stroke_color", type=str, required=False, default=None,
                        help="The stroke color for the title text.")
    parser.add_argument("--title_stroke_width", type=int, required=False, default=None,
                        help="The stroke width for the title text.")
    
    
    # --- ALBUM TITLE ARGUMENTS ---
    parser.add_argument("--album", type=str, required=False, default=None,
                        help="The text to display in the album. If not specified, no album will be added.")
    parser.add_argument("--album_size", type=int, required=False, default=None,
                        help="The size of the album text. If not specified, the album will be scaled to 200 pixels.")
    parser.add_argument("--album_font", type=str, required=False, default=None,
                        help="The font to use for the album text. If not specified, the default font will be used.")
    parser.add_argument("--album_position", type=str, required=False, default='',
                        help="The position of the album text on the output image. Must be in the format 'WIDTH-HEIGHT'.")
    parser.add_argument("--album_fill", type=str, required=False, default=None,
                        help="The fill color for the album text.")
    parser.add_argument("--album_stroke_color", type=str, required=False, default=None,
                        help="The stroke color for the album text.")
    parser.add_argument("--album_stroke_width", type=int, required=False, default=None,
                        help="The stroke width for the album text.")

    
    return parser

_LEVELS = {
    'debug' : logging.DEBUG,
    'info' : logging.INFO,
    'warning' : logging.WARNING,
    'error' : logging.ERROR,
    'critical' : logging.CRITICAL
}

def run() :
    args = build_arg_parser().parse_args()

    new_level = logging.INFO

    if args.log_level is not None:
        new_level = args.log_level.lower()
        if new_level not in _LEVELS:
            if new_level.isnumeric():
                new_level = int(new_level)
            else :
                raise Exception(f"Invalid log level: {args.log_level}")
        else :
            new_level = _LEVELS[new_level]
            
    print(f"++ Setting log level to {new_level}")

    lc= LOGGING_CONFIG
    lc['loggers']['app']['level'] = new_level
    lc['loggers']['lib']['level'] = new_level
    logging.config.dictConfig(lc)
    logger.setLevel(new_level)

    config_file = args.config_file
    if args.config_file is not None:
        set_resolve_path(os.path.dirname(os.path.abspath(args.config_file)))

    config = build_config(args, config_file)
    if not validate_config(config):
        sys.exit(1)

    build_image(config)

if __name__ == "__main__":
    run()
