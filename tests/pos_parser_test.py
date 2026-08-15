from MuPic.parsers import get_parser
import logging
from lark import exceptions, logger as lark_logger
lark_logger.setLevel(logging.DEBUG)
import pytest

def _parse_text(text : str)  :
    parser = get_parser('position')
    tree = parser.parse(text)
    return positionXform().transform(tree)

from MuPic.position import positionXform
def test_simple_parser() :

    output = _parse_text('center-center-20')
    assert output == ('overlay', ('output', 'content', None), (50, 50), ('mid', 'mid'), 20)

    output = _parse_text('left-top')
    assert output == ('overlay', ('output', 'content', None), (0, 0), ('min', 'min'), 10)

    output = _parse_text('right-bottom')
    assert output == ('overlay', ('output', 'content', None), (100, 100), ('max', 'max'), 10)

    # Errors
    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text('bleh-center')

    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text('center-bleh')

    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text('center-center-bleh')

    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text('center-center-20-bleh')

    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text('center--center-20')

    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text('center -center-20')

def test_attach_parser() :

    output = _parse_text("attach (output:border:left, mid, 20%)")
    assert output == ('attach', ('output','border','left'), ('mid', 20), ('mid', 'min'), None)

    output = _parse_text("attach (output:border:left, mid, 20%, mid, min)")
    assert output == ('attach', ('output','border','left'), ('mid', 20), ('mid', 'min'), None)

    output = _parse_text("attach (output:border:left, mid, 20%, mid, min, 30)")
    assert output == ('attach', ('output','border','left'), ('mid', 20), ('mid', 'min'), 30)

    output = _parse_text("attach (output:border:left, mid, 80%, 30)")
    assert output == ('attach', ('output','border','left'), ('mid', 80), ('mid', 'max'), 30)

    output = _parse_text("attach (border:left, mid, 60%)")
    assert output == ('attach', ('cover','border','left'), ('mid', 60), ('mid', 'mid'), None)

    output = _parse_text(" attach ( cover:left , mid , 60% )  ")
    assert output == ('attach', ('cover','content','left'), ('mid', 60), ('mid', 'mid'), None)

    output = _parse_text(" attach ( \"cover\":left , mid , 60% )  ")
    assert output == ('attach', ('cover','content','left'), ('mid', 60), ('mid', 'mid'), None)

    output = _parse_text(" attach ( \"groovy ref : thing\":left , mid , 60% )  ")
    assert output == ('attach', ('groovy ref : thing','content','left'), ('mid', 60), ('mid', 'mid'), None)

    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text("attach (output : border:left, min, 80%, 30)")

    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text("attach (output:border::left, min, 80%, 30)")

    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text("attach (output:border:left:, min, 80%, 30)")

    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text("attach (output:border:left, bad, 80%, 30)")
