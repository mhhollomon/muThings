import pytest

from MuPic.parsers import get_parser
from MuPic.position import positionXform, position

import logging
from lark import exceptions, logger as lark_logger
lark_logger.setLevel(logging.DEBUG)

def _parse_text(text : str)  :
    parser = get_parser('position')
    tree = parser.parse(text)
    return positionXform().transform(tree)


def test_simple_parser() :

    output = _parse_text('CENTER-center-20')
    assert output == ('overlay', ('output', 'content', None), None, ((50, '%'), (50, '%')), ('mid', 'mid'), 20)

    output = _parse_text('left-ToP')
    assert output == ('overlay', ('output', 'content', None), None, ((0, '%'), (0, '%')), ('min', 'min'), 10)

    output = _parse_text('right-bottom')
    assert output == ('overlay', ('output', 'content', None), None, ((100, '%'), (100, '%')), ('max', 'max'), 10)

    # Errors

    # wrong x value
    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text('bleh-center')

    # wrong y value
    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text('center-bleh')

    # wrong offset value
    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text('center-center-bleh')

    # Extra item
    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text('center-center-20-bleh')

    # Double dashes
    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text('center--center-20')

def test_attach_parser() :

    # Percent position value, anchor, no offset
    output = _parse_text("attach (output.border.left, left, 20%, mid)")
    assert output == ('attach', ('output','border','left'), 'left', ((20, '%'), None), ('mid', None), 0)

    # Negative Percent position value, anchor,  no offset
    output = _parse_text("attach (output.border.left, left, -20%, max)")
    assert output == ('attach', ('output','border','left'), 'left', ((-20, '%'), None), ('max', None), 0)

    # pixel position value, no anchor, no offset
    output = _parse_text("attach (output.border.left, right, 200px)")
    assert output == ('attach', ('output','border','left'), 'right', ((200, 'px'), None), ('min', None), 0)

    # negative pixel position value, no anchor, no offset
    output = _parse_text("attach (output.border.left, right, -200px)")
    assert output == ('attach', ('output','border','left'), 'right', ((-200, 'px'), None), ('min', None), 0)

    # minmax position value, anchor, offset
    output = _parse_text("attach (output.border.left, TOP, mid, max, 30)")
    assert output == ('attach', ('output','border','left'), 'top', ((50, '%'), None), ('max', None), 30)

    # minmax position value, no anchor, offset
    output = _parse_text("attach (output.content, BoTTom, min, 50)")
    assert output == ('attach', ('output','content', None), 'bottom', ((0, '%'), None), ('min', None), 50)

    # minmax position value, no anchor, no offset, shortcut triple
    output = _parse_text("attach (border.left, left, MIN )")
    assert output == ('attach', ('cover','border','left'), 'left', ((0, '%'), None), ('min', None), 0)

    # quoted element name
    output = _parse_text(" attach ( \"border\".left , top, min)  ")
    assert output == ('attach', ('cover','border','left'), 'top', ((0, '%'), None), ('min', None), 0)

    # quoted element name with spaces and other things
    output = _parse_text(" attach ( \"groovy ref : thing\".content , BOTTOM, min )  ")
    assert output == ('attach', ('groovy ref : thing','content', None), 'bottom', ((0, '%'), None), ('min', None), 0)

    # Wrong shortcut
    with pytest.raises(exceptions.VisitError) :
        output = _parse_text(" attach ( cover.left , RIGHT ,mid )  ")

    # badly formed triple
    with pytest.raises(exceptions.UnexpectedCharacters) :
        output = _parse_text("attach (output : border.left, min)")

    with pytest.raises(exceptions.UnexpectedCharacters) :
        output = _parse_text("attach (output.border.:left, min)")

    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text("attach (output.border.left., min,)")

    # Bad position
    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text("attach (output.border.left, bad)")

    # Bad position
    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text("attach (output.border.left, 900pt)")

def test_overlay_parser() :
    output = _parse_text("overlay (output.border.left,  mid, 20%)")
    assert output == ('overlay', ('output','border','left'), None, ((50, '%'), (20, '%')), ('mid', 'min'), 0)

    output = _parse_text("overlay (funky.full,  mid, 20%, min, max)")
    assert output == ('overlay', ('funky','full', None), None, ((50, '%'), (20, '%')), ('min', 'max'), 0)

    with pytest.raises(exceptions.VisitError) :
        output = _parse_text("overlay (funky.margin,  mid, 20%, min, max)")


def test_position() :
    """Test the position class"""
    p = position('CENTER-center-20')
    assert str(p) == 'overlay(output.content, 50%, 50%, mid, mid, 20)'

    p = position("overlay (funky.full,  mid, 20%, min, max)")
    assert str(p) == 'overlay(funky.full, 50%, 20%, min, max, 0)'

    p = position("overlay (\"funny element name\".full,  mid, 20%, min, max, 40)")
    assert str(p) == 'overlay("funny element name".full, 50%, 20%, min, max, 40)'

    p = position("attach (\"funny element name\".full, left,  mid, max, 40)")
    assert str(p) == 'attach("funny element name".full, left, 50%, max, 40)'
