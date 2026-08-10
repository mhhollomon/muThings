import pytest

from MuPic.geometry import point

def test_point() :
    p = point(1, 2)
    assert p.x == 1
    assert p.y == 2

    p = point.from_tuple((1, 2))
    assert p.x == 1
    assert p.y == 2

    with pytest.raises(ValueError) :
        p = point('a', 'b')

    with pytest.raises(ValueError) :
        p = point.from_tuple(('a', 'b'))

    assert point('1', '3') == point(1, 3)

    with pytest.raises(TypeError) :
        p = point(1,2)
        p.x = 2

    s = point(1,2)
    assert str(s) == 'point<1, 2>'
    assert repr(s) == 'point<1, 2>'
