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
    assert output == ('overlay', ('output', 'content', None), None, (50, 50), ('mid', 'mid'), 20)

    output = _parse_text('left-ToP')
    assert output == ('overlay', ('output', 'content', None), None, (0, 0), ('min', 'min'), 10)

    output = _parse_text('right-bottom')
    assert output == ('overlay', ('output', 'content', None), None, (100, 100), ('max', 'max'), 10)

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

    output = _parse_text("attach (output.border.left, left, mid, 20%)")
    assert output == ('attach', ('output','border','left'), 'left', (50, 20), ('mid', 'min'), 0)

    output = _parse_text("attach (output.border.left, right, mid, 20%, mid, min)")
    assert output == ('attach', ('output','border','left'), 'right', (50, 20), ('mid', 'min'), 0)

    output = _parse_text("attach (output.border.left, TOP, mid, 20%, mid, min, 30)")
    assert output == ('attach', ('output','border','left'), 'top',(50, 20), ('mid', 'min'), 30)

    output = _parse_text("attach (output.content, BoTTom, mid, 80%, 30)")
    assert output == ('attach', ('output','content', None), 'bottom', (50, 80), ('mid', 'max'), 30)

    output = _parse_text("attach (border.left, left, max, 60%)")
    assert output == ('attach', ('cover','border','left'), 'left', (100, 60), ('max', 'mid'), 0)


    output = _parse_text(" attach ( \"border\".left , top, min , 60% )  ")
    assert output == ('attach', ('cover','border','left'), 'top', (0, 60), ('min', 'mid'), 0)

    output = _parse_text(" attach ( \"groovy ref : thing\".content , BOTTOM, mid , 60% )  ")
    assert output == ('attach', ('groovy ref : thing','content', None), 'bottom', (50, 60), ('mid', 'mid'), 0)

    with pytest.raises(exceptions.VisitError) :
        output = _parse_text(" attach ( cover.left , RIGHT ,mid , 60% )  ")

    with pytest.raises(exceptions.UnexpectedCharacters) :
        output = _parse_text("attach (output : border.left, min, 80%, 30)")

    with pytest.raises(exceptions.UnexpectedCharacters) :
        output = _parse_text("attach (output.border.:left, min, 80%, 30)")

    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text("attach (output.border.left., min, 80%, 30)")

    with pytest.raises(exceptions.UnexpectedToken) :
        output = _parse_text("attach (output.border.left, bad, 80%, 30)")

def test_overlay_parser() :
    output = _parse_text("overlay (output.border.left,  mid, 20%)")
    assert output == ('overlay', ('output','border','left'), None, (50, 20), ('mid', 'min'), 0)

    output = _parse_text("overlay (funky.full,  mid, 20%, min, max)")
    assert output == ('overlay', ('funky','full', None), None, (50, 20), ('min', 'max'), 0)

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

    p = position("attach (\"funny element name\".full, left,  mid, 20%, min, max, 40)")
    assert str(p) == 'attach("funny element name".full, left, 50%, 20%, min, max, 40)'
