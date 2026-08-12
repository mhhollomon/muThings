
from pathlib import Path
import sys

from MuPic.configuration import Configuration

xform = Configuration(sys.argv[1])
xform.read_config()
xform.print()
