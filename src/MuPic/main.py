#!/usr/bin/env python

import os
import sys
import logging
import logging.config

from .music_image import MusicImage
from .logconfig import LOGGING_CONFIG

logger = logging.getLogger('app')

import argparse

from .config_old import ConfigOld, build_config, validate_config
from .paths import set_resolve_path


#--------------------------------------------------------------------------------
# TOP LEVEL FUNCTION
#--------------------------------------------------------------------------------

def build_image(config : ConfigOld) :

    final = MusicImage(config)

    output_img = final.generate()

    output_path = config.output.path

    # Save the image
    output_img.save(output_path)

#--------------------------------------------------------------------------------
# ARGUMENT PARSING
#--------------------------------------------------------------------------------
def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    # --- Application Level Arguments ---
    parser.add_argument("--config_file", "-c", type=str, required=True, default=None,
                        help="yaml file containing configuration values.")
    parser.add_argument("--debug", "-d", action='store_true', required=False, default=False,
                        help="Enable debug logging.")
    parser.add_argument("--noaction", "-n", action='store_true', required=False, default=False,
                        help="Print the configuration and exit.")
    parser.add_argument("--print_config", "-p", action='store_true', required=False, default=False,
                        help="Print the configuration")

    # --- GLOBAL ARGUMENTS ---
    parser.add_argument("--gutter", type=int, required=False, default=None,
                        help="The size of the gutter between the edge of the output image and the title."
                        " If not specified, the gutter will be 10 pixels.")
    parser.add_argument("--font", type=str, required=False, default=None,
                        help="The default font to use for for any text."
                        " If not specified, the font will be the default system font.")

    # --- OUTPUT ARGUMENTS ---
    parser.add_argument("--output_path", '-o', type=str, required=False, default=None,
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


    
    return parser
#--------------------------------------------------------------------------------
# MAIN
#--------------------------------------------------------------------------------

def main() :
    args = build_arg_parser().parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO

    print_config = args.debug or args.print_config or args.noaction

    lc= LOGGING_CONFIG
    lc['loggers']['app']['level'] = log_level
    lc['loggers']['MuPic']['level'] = log_level
    logging.config.dictConfig(lc)
    logger.setLevel(log_level)

    config_file = args.config_file
    set_resolve_path(os.path.dirname(os.path.abspath(config_file)))

    config = build_config(args, config_file, print_config)
    if not validate_config(config):
        sys.exit(1)

    if args.noaction:
        logger.info("No action requested. Exiting.")
        sys.exit(0)

    build_image(config)

if __name__ == "__main__":
    main()
