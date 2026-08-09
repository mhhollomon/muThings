from lark import Lark
from pathlib import Path
import sys

grammar = Path(__file__).parent.parent / 'src' / 'Mupic' / 'config.lark'
parser = Lark(grammar.read_text(), parser='lalr', debug=True, start='config')

with open(sys.argv[1], 'r') as f:
    text = f.read()
tree = parser.parse(text)
print(tree.pretty())
