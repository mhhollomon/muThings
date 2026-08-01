from ..position import geometry, rectangle

class ImageElement :
    generated = False
    bbox = rectangle(geometry(0,0), geometry(0,0))
    
    def __init__(self, name : str) :
        self.name = name


    @property
    def name(self) :
        return self._name

    @name.setter
    def name(self, name : str) :
        if name is None :
            raise ValueError("ImageElement name cannot be None")
        if name == '' :
            raise ValueError("ImageElement name cannot be empty")
        self._name = name