import os

CONFIG_DIR : str = ''

def set_resolve_path(path : str) :
    global CONFIG_DIR
    CONFIG_DIR = path

def resolve_path(path : str, relpath : str | None = None) -> str:
    relpath_clean : str = relpath if relpath is not None else CONFIG_DIR
    if os.path.isabs(path):
        return path
    elif path.startswith('./'):
        return os.path.abspath(path)
    else:
        return os.path.abspath(os.path.join(relpath_clean, path))