def dictmerge(a: dict, b: dict) -> dict:
    """Merge b into a.
    'a' is modified in-place.
    Dicts are merged. Lists are concatenated.
    Found on stackoverflow with slight mods.
    """
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                dictmerge(a[key], b[key])
            elif isinstance(a[key], list) and isinstance(b[key], list):
                a[key].extend(b[key])
            else :
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a
