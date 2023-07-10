"""Sprite Tilemap Text Parser
Processes tilemap strings from Advynia's sprite metadata."""

"""
Text-based sprite tilemap data format:

Each line of commands (separated by semicolons) corresponds to one rectangle of
tiles. Within a line, commands can be listed in any order, separated by
whitespace (newlines are treated as whitespace).
First character is the command, anything after that is the argument.
This format is not case-sensitive.

Commands:
t<hex> : tile ID (000-26F for sprite global, 00-1F for stripes, 000-4FF for
    layers). If "s" or "l" is specified, it's that tile type; otherwise it's
    sprite global.
s<hex> : stripe ID
l : use layer graphics, not sprite tiles
    overloaded:
    l1 : use 8x8 layer tiles
    l2 or l3 : use graphics from layer pixmap
        if "t": copy one scanline at a time;
            offsets specified in SMA3.ScanlineOffsetData, index "t"
        else: "r" specifies x,y,width,height, to copy a rectangle from the layer
        in either case, "r" values do not need to be multiples of 8
d<hex> : dynamic pointer
  "s"/"l"/"d" are mutually exclusive
p<hex> : palette (00-1F). No default.
r<int[,int]> : rectangle size (width, height, separated by comma).
    Each dimension should be a multiple of 8. If height is omitted, rectangle is
    square (r16 is the same as r16,16). If entire command is omitted,
    defaults to 8x8.
x<hex> : x offset
y<hex> : y offset
    Both offsets are relative to the top-left corner of the tile the sprite is
    placed at, and default to 0. "+" sign is not required, but useful for
    readability.
f<str> : flip rectangle. Should be followed by x and/or y ("fx", "fy", "fxy")
a<int> : angle to rotate rectangle about its center, in degrees,
    counterclockwise. Defaults to 0.
m<float,float> : scaling factors (horiz, vert). If vert is omitted,
    defaults to same as horiz. If entire command is omitted, defaults to 1.
o<int> : opacity, in % (0-100). Defaults to 100.
!<str> : text string. ASCII, but cannot contain a semicolon. Spaces can be
    escaped with backslash.
z<str> : string, for anything that requires special handling.
"""

# standard library imports
from collections import namedtuple

# import from other files
import AdvMetadata

SpriteTilemapAttr = namedtuple("SpriteTilemapAttr",
    """tileID, paletterow, xflip, yflip, sprite, stripeID, dynamicptr, layer,
    x, y, width, height, angle, scaleX, scaleY, opacity, text, size, misc""",
    defaults=(None, None, False, False, True, None, None, None,
              0, 0, 8, 8, 0, 1, 1, 1, None, None, None)
                               )

def processrawtilemap(rawtilemap):
    """Converts the text-based sprite tilemap data format into a list of
    mappings, for use in drawing sprite graphics."""

    output = []
    stripes = set()
    dynamic = False
    for line in rawtilemap.split(";"):
        parts = line.split()
        if not parts: continue

        # use mutable dict to generate immutable namedtuple
        keymapping = {}
        partsgen = iter(parts)
        for part in partsgen:
            command = part[0].lower()  # ignore case
            arg = part[1:]
            while arg.endswith("\\"):
                arg = arg[0:-1] + " " + next(partsgen)
            match command:
                case "t":
                    keymapping["tileID"] = int(arg, base=16)
                case "s":
                    stripe = int(arg, base=16)
                    keymapping["stripeID"] = stripe
                    stripes.add(stripe)
                case "d":
                    keymapping["dynamicptr"] = int(arg, base=16)
                    dynamic = True
                case "p":
                    keymapping["paletterow"] = int(arg, base=16)
                case "x" | "y":
                    keymapping[command] = int(arg, base=16)
                case "l":
                    layer = int(arg)
                    if layer == 1:
                        keymapping["sprite"] = False
                    else:
                        keymapping["layer"] = int(arg)
                case "r":
                    arg = arg.split(",")
                    if len(arg) <= 2:
                        keymapping["width"] = int(arg[0])
                        keymapping["height"] = int(arg[-1])
                    else:
                        keymapping["width"] = int(arg[-2])
                        keymapping["height"] = int(arg[-1])
                        keymapping["size"] = tuple(int(i) for i in arg[0:-2])
                case "f":
                    arg = arg.lower()
                    if "x" in arg:
                        keymapping["xflip"] = True
                    if "y" in arg:
                        keymapping["yflip"] = True
                case "o":
                    keymapping["opacity"] = int(arg) / 100
                case "a":
                    keymapping["angle"] = int(arg)
                case "m":
                    arg = arg.split(",")
                    keymapping["scaleX"] = float(arg[0])
                    keymapping["scaleY"] = float(arg[-1])
                case "!":
                    keymapping["text"] = arg
                    keymapping["width"] = 1 + sum(
                        AdvMetadata.fontwidths[ord(char)] for char in arg)
                    keymapping["height"] = 1 + AdvMetadata.fontheight
                case "z":
                    keymapping["misc"] = arg
                case _:
                    raise ValueError(
                        f"Sprite tilemap line '{line}' "
                        f"has an invalid command: '{command}'")

        # error checking
        if not {"paletterow", "layer", "misc"}.intersection(keymapping):
            raise ValueError(
                f"Sprite tilemap line '{line}' did not specify a palette.")
        if not {"tileID", "dynamicptr", "layer", "text", "misc"}.intersection(keymapping):
            raise ValueError(
                f"Sprite tilemap line '{line}' did not specify a tile.")
        output.append(SpriteTilemapAttr()._replace(**keymapping))
    return output, stripes, dynamic
