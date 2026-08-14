from pathlib import Path


def resolve_path(path : str | Path, relpath : str | Path | None = None) -> Path:
    path = Path(path)

    if path.is_absolute() :
        return path
    elif str(path).startswith('./'):
        return path.resolve()
    elif relpath is None :
        return path.resolve()
    
    return (Path(relpath) / path).resolve()
