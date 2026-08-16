import pytest

from MuPic.geometry import sizet

def test_sizet() :
    s = sizet(1, 2)
    assert s.width == 1
    assert s.height == 2

    s = sizet((1, 2))
    assert s.width == 1
    assert s.height == 2

    s = sizet(1)
    assert s.width == 1
    assert s.height == 1

    s = sizet('10')
    assert s.width == 10
    assert s.height == 10

    s = sizet(10.3456)
    assert s.width == 10
    assert s.height == 10

    s = sizet((10.3456, 10.3456))
    assert s.width == 10
    assert s.height == 10

    with pytest.raises(ValueError) :
        s = sizet('blue', 3)

    s = sizet('1x2')
    assert s.width == 1
    assert s.height == 2
    
    with pytest.raises(ValueError) :
        s = sizet('1x')

    with pytest.raises(ValueError) :
        s = sizet('1.3x3.4')

    s = sizet(3,4).copy()
    assert s.width == 3
    assert s.height == 4

    # Test about to_tuple()
    s = sizet(3,4)
    assert s.to_tuple() == (3,4)

    # Tests about __add__() and __sub__()
    s = sizet(3,4) + (5,6)
    assert s == (8,10)

    s = sizet(3,4) - (5,6)
    assert s == (-2,-2)

    s = sizet(3,4) + 5
    assert s == (8,9)

    s = sizet(3,4) - 5
    assert s == (-2,-1)

    s = sizet(3, 4) + sizet(5, 6)
    assert s == (8, 10)
