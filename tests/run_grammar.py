
import sys

from MuPic.configuration import Configuration

xform = Configuration(sys.argv[1])
settings= xform.read_config()

print("========================== Final Settings :")
settings.print()
