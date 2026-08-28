from PIL import Image



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

#----------------------------------------------------------------------------

def clamped_mask(input : Image.Image, threshold : int = 10) -> Image.Image :

    upper_threshold = 255 - threshold
    slope = 255 / (upper_threshold - threshold)

    def new_value(x : float) -> float :
        if x < threshold :
            return 0
        elif x > upper_threshold :
            return 255
        else :
            return (x - threshold) * slope

    return input.convert('L').point(new_value)
