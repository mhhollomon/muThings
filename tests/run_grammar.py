from lark import Lark, logger
import logging

from pathlib import Path
import sys

from MuPic.config_transformer import ConfigTransformer

logger.setLevel(logging.DEBUG)

grammar = Path(__file__).parent.parent / 'src' / 'MuPic' / 'config.lark'
parser = Lark(grammar.read_text(), parser='lalr', debug=True, start='config_file', maybe_placeholders=True, strict=True)

with open(sys.argv[1], 'r') as f:
    text = f.read()
tree = parser.parse(text)
print(tree.pretty())

print("=====")

xform = ConfigTransformer()
new_tree = xform.transform(tree)
print(new_tree.pretty())

print("=====")

xform.config.print()
