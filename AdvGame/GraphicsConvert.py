"""Functions to convert graphics to GBA format."""

_bitmasks = bytes(1 << i for i in reversed(range(8)))

class GraphicsConvertError(ValueError):
    "Custom class for detecting graphics conversion errors."
    pass

def convert_SNES_4bpp(inputgfx: bytes):
    if len(inputgfx) % 0x20 != 0:
        raise GraphicsConvertError(
            f"Input file size (0x{len(inputgfx):X} bytes) does not contain "
            "an integer number of 4bpp tiles (0x20 bytes each).")
    output = bytearray()
    partialbyte = None
    for offset in range(0, len(inputgfx), 0x20):
        for rowoffset in range(offset, offset+0x10, 2):
            for bitmask in _bitmasks:
                color = 0
                if inputgfx[rowoffset + 0x11] & bitmask:
                    color |= 8
                if inputgfx[rowoffset + 0x10] & bitmask:
                    color |= 4
                if inputgfx[rowoffset + 1] & bitmask:
                    color |= 2
                if inputgfx[rowoffset] & bitmask:
                    color |= 1

                if partialbyte is None:
                    partialbyte = color
                else:
                    output.append(color << 4 | partialbyte)
                    partialbyte = None
    return output

def convert_SNESGB_2bpp(inputgfx: bytes):
    if len(inputgfx) % 0x10 != 0:
        raise GraphicsConvertError(
            f"Input file size (0x{len(inputgfx):X} bytes) does not contain "
            "an integer number of 2bpp tiles (0x10 bytes each).")
    output = bytearray()
    partialbyte = None
    for rowoffset in range(0, len(inputgfx), 2):
        for bitmask in _bitmasks:
            color = 0
            if inputgfx[rowoffset + 1] & bitmask:
                color |= 2
            if inputgfx[rowoffset] & bitmask:
                color |= 1

            if partialbyte is None:
                partialbyte = color
            else:
                output.append(color << 4 | partialbyte)
                partialbyte = None
    return output
