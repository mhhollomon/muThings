from typing import Any


class NoneDict :
    """Alway return None if the key is not found.
    Also, support path keys like 'a.b.c'
    """
    def __init__(self, config : dict) :
        self.config = config

    def __getitem__(self, key) -> Any :
        if self.config is None :
            return None
        
        keys = key.split('.')
        value = self.config
        for k in keys :
            if k in value :
                value = value[k]
            else :
                return None
            if not isinstance(value, dict) :
                return value
        return value

    def __contains__(self, key) :
        return key in self.config
