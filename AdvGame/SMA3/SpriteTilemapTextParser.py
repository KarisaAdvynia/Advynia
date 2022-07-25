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
l : use layer tiles, not sprite tiles
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
"""

from collections import namedtuple

SpriteTilemapAttr = namedtuple("SpriteTilemapAttr",
    """tileID, paletterow, xflip, yflip, sprite, stripeID, dynamicptr,
    x, y, width, height, angle, scaleX, scaleY, opacity""",
    defaults=(None, None, False, False, True, None, None,
              0, 0, 8, 8, 0, 1, 1, 1)
                               )

def processrawtilemap(rawtilemap):
    """Converts the text-based sprite tilemap data format into a list of
    mappings, for use in drawing sprite graphics."""

    # ignore case
    rawtilemap = rawtilemap.lower()

    output = []
    stripes = set()
    dynamic = False
    for line in rawtilemap.split(";"):
        parts = line.split()
        if not parts: continue

        # use mutable dict to generate immutable namedtuple
        keymapping = {}
        for part in parts:
            command = part[0]
            arg = part[1:]
            if command == "t":
                keymapping["tileID"] = int(arg, base=16)
            elif command == "s":
                stripe = int(arg, base=16)
                keymapping["stripeID"] = stripe
                stripes.add(stripe)
            elif command == "d":
                keymapping["dynamicptr"] = int(arg, base=16)
                dynamic = True
            elif command == "p":
                keymapping["paletterow"] = int(arg, base=16)
            elif command in "xy":
                keymapping[command] = int(arg, base=16)
            elif command == "r":
                arg = arg.split(",")
                keymapping["width"] = int(arg[0])
                keymapping["height"] = int(arg[-1])
            elif command == "f":
                if "x" in arg:
                    keymapping["xflip"] = True
                if "y" in arg:
                    keymapping["yflip"] = True
            elif command == "o":
                keymapping["opacity"] = int(arg) / 100
            elif command == "l":
                keymapping["sprite"] = False
            elif command == "a":
                keymapping["angle"] = int(arg)
            elif command == "m":
                arg = arg.split(",")
                keymapping["scaleX"] = float(arg[0])
                keymapping["scaleY"] = float(arg[-1])
##            elif command == "c":
##                arg = arg.split(",")
##                copysprID = int(arg[0], base=16)
##                copyparity = None
##                if len(arg) > 1:
##                    copyparity = int(arg[1])
##                keymapping["copy"] = (copysprID, copyparity)
            else:
                raise ValueError("".join((
                    "Sprite tilemap line '", line,
                    "' has an invalid command: '" + command + "'")))

        # error checking
        if "paletterow" not in keymapping:
            raise ValueError("".join((
                "Sprite tilemap line '", line, "' did not specify a palette.")))
        if "tileID" not in keymapping and "dynamicptr" not in keymapping:
            raise ValueError("".join((
                "Sprite tilemap line '", line, "' did not specify a tile.")))
        output.append(SpriteTilemapAttr()._replace(**keymapping))
    return output, stripes, dynamic
