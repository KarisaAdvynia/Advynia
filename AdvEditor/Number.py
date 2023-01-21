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

def hexstr_0tomax(maxvalue):
    return "".join(("(", "0"*hexlen(maxvalue), "-", format(maxvalue, "X"), ")"))

def megabytetext(bytecount, decimalplaces=3):
    return (str(bytecount // 1048576) if bytecount % 1048576 == 0
            else format(bytecount / 1048576, "." + str(decimalplaces) + "f"))
