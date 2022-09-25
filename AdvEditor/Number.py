def capvalue(value, minvalue, maxvalue):
    """If the input value is within the given range (inclusive), return it.
    Else, cap it to that range."""
    if minvalue > maxvalue:
        raise ValueError
    return min(max(value, minvalue), maxvalue)

def hexlen(i):
    "Return the number of hex digits needed to represent an integer."
    return (i.bit_length() + 3) // 4

def hexlenformatstr(i):
    "Return a format string corresponding to hexlen(i)."
    return "0" + str(hexlen(i)) + "X"
