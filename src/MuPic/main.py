#!/usr/bin/env python

import sys
import logging
import logging.config

from .configuration import Configuration
from .settings import Settings

from .music_image import MusicImage
from .logconfig import LOGGING_CONFIG

logger = logging.getLogger('app')

import argparse


#--------------------------------------------------------------------------------
# TOP LEVEL FUNCTION
#--------------------------------------------------------------------------------

def build_image(s : Settings) :

    output_path = s.output.path
    if output_path is None :
        logger.error("No output path specified")
        sys.exit(1)

    final = MusicImage(s)

    output_img = final.generate()


    # Save the image
    output_img.save(output_path)

#--------------------------------------------------------------------------------
# ARGUMENT PARSING
#--------------------------------------------------------------------------------
def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    # --- Application Level Arguments ---
    parser.add_argument("config_file", type=str, default=None,
                        help="file containing configuration values.")
    parser.add_argument("--debug", "-d", action='store_true', required=False, default=False,
                        help="Enable debug logging.")
    parser.add_argument("--noaction", "-n", action='store_true', required=False, default=False,
                        help="Print the configuration and exit.")
    parser.add_argument("--print_config", "-p", action='store_true', required=False, default=False,
                        help="Print the configuration")
    parser.add_argument("--grid", "-g", nargs='?', const='10', required=False, default=None,
                        help="Generate a grid over the resulting output image. GRID may be either a percentage value, or a pixel value (with px)")


    # --- OUTPUT ARGUMENTS ---
    parser.add_argument("--output_path", '-o', type=str, required=False, default=None,
                        help="The path and filename on to which to write the output." 
                        " The extension given on the filename will be used to determine the format.")


    
    return parser
#--------------------------------------------------------------------------------
# MAIN
#--------------------------------------------------------------------------------

def main() :
    args = build_arg_parser().parse_intermixed_args()

    log_level = logging.DEBUG if args.debug else logging.INFO

    print_config = args.debug or args.print_config or args.noaction

    lc= LOGGING_CONFIG
    lc['loggers']['app']['level'] = log_level
    lc['loggers']['MuPic']['level'] = log_level
    logging.config.dictConfig(lc)
    logger.setLevel(log_level)

    config_file = args.config_file

    config = Configuration(config_file, args).read_config()

    if print_config:
        config.print()

    if args.noaction:
        logger.info("No action requested. Exiting.")
        sys.exit(0)

    build_image(config)

if __name__ == "__main__":
    main()
