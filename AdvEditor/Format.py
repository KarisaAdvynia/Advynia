# import from other files
from AdvEditor import AdvSettings

def pluralize(num, singular, plural=None, numformat=""):
    """Generate a string containing the given number and either a singular
    or plural word, depending on the number.
    The number may be formatted by specifying a format string.
    If a unique plural is not specified, the plural defaults to adding "s"."""
    if plural is None:
        plural = singular + "s"
    return format(num, numformat) + " " + (singular if num == 1 else plural)

def sublevelitemstr(objects=(), sprites=(), long=False):
    """Format a collection of objects and/or sprites into status bar text.
    The collections are not necessarily ordered.

    If there's 1 object or 1 sprite, the ID is included (or the entire
    object/sprite string form, if there's a single item and long==True),
    else only the count of objects/sprites is included."""
    result = []
    if len(objects) == 1:
        result.append("object ")
        if long and not sprites:
            result.append(str(tuple(objects)[0]))
        else:
            result.append(tuple(objects)[0].idstr())
    elif len(objects) > 1:
        result += str(len(objects)), " objects"
    if sprites:
        if result:
            result.append(", ")
        if len(sprites) == 1:
            result.append("sprite ")
            if long and not objects:
                result.append(str(tuple(sprites)[0]))
            else:
                result.append(tuple(sprites)[0].idstr())
        elif len(sprites) > 1:
            result += str(len(sprites)), " sprites"

    if result:
        return "".join(result)
    else:
        return "None"
