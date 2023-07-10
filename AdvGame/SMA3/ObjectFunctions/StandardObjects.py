"""SMA3 Layer 1 Tilemap: Standard Object Functions

Functions to replicate in-game standard objects (objects 01-FE), which operate
on the tilemap.

Each function takes 5 arguments: tilemap, initial X, initial Y, width, height.
Tilemap is abbreviated to "t" for compactness, given its frequent references.
One of the dimension arguments is unused for 4-byte objects, but to simplify
code processing, both dimensions are provided to all standard objects.
"""

# standard library imports
import itertools, math, random
from collections.abc import Callable, Iterable, Iterator

# import from other files
from .StdObjData import *
from .Shared import *

## Non-formulaic standard objects

#### Objects 01-0B: Regular land, floor and side wall variants

landinterior_randtile = (0xD390E,0xD390E,0xD390F,0xD390F,
                         0xD3910,0xD3911,0xD392B,0xD392C)
    # used by objects that call setlandinterior_shared (01, 04-09, 87-88, 99)
    # also used directly by 3A-3B, 59-62, 67, 85-86
landinterior_surfacesidetiles = (0x390E,0x390F,0x3910,0x3911,0x392B,0x392C)
def setlandinterior_shared(t, x, y, lastYflag: bool):
    prevdyn = t.getdyn(x, y)
    t.setTile(-1, x, y)
    if (prevdyn in (0x3931,0x3932) or 0x3921 <= prevdyn <= 0x392A or 
            (lastYflag and prevdyn in (0x3918,0x3919,0x391D))):
        return
    elif lastYflag and prevdyn in (0x3912,0x3913):
        # overlapping a solid surface
        if t.getdyn(x-1, y) in landinterior_surfacesidetiles:
            t.setTile(0xD3918, x, y+1, priority=False, highlight=False)
            tileID = 0xD391D
        elif t.getdyn(x+1, y) in landinterior_surfacesidetiles:
            t.setTile(0xD3919, x, y+1, priority=False, highlight=False)
            tileID = 0xD391C
        else:
            tileID = 0xD390D
    else:
        leftcheck = (t.getdyn(x-1, y) == 0x390D)
        rightcheck = (t.getdyn(x+1, y) == 0x390D)
        if leftcheck:
            t.setTile(0xD391C, x-1, y, priority=False, highlight=False)
            t.setTile(0xD3919, x, y+1, priority=False, highlight=False)
        if rightcheck:
            if not leftcheck:
                # this replace uses x, y+1 in-game if leftcheck succeeded
                t.setTile(0xD391D, x-1, y, priority=False, highlight=False)
            t.setTile(0xD3918, x, y+1, priority=False, highlight=False)
        # default tile
        tileID = random.choice(landinterior_randtile)
    t.setTile(tileID, x, y)

def obj01(t, x0, y0, width, height):
    ylist = list(t.yrange(y0-1, height+1))

    parityX = 0
    for x in t.xrange(x0, width):
        # row 0
        prevdyn = t.getdyn(x, ylist[0])
        if prevdyn >> 8 == 0x39:
            if x == x0:
                if prevdyn == 0x3922: tileID = 0xD3937
                else: tileID = 0xD392A
            else:
                if prevdyn == 0x3921: tileID = 0xD3936
                else: tileID = 0xD3929
        else:
            tileID = 0xD2A00 + parityX
        t.setTile(tileID, x, ylist[0], highlight=False)

        # row 1
        prevdyn = t.getdyn(x, ylist[1])
        if prevdyn >> 8 == 0x39:
            if x == x0:
                if prevdyn == 0x3922: tileID = 0xD3937
                else: tileID = 0xD3907
            else:
                if prevdyn == 0x3921: tileID = 0xD3936
                else: tileID = 0xD3908
        else:
            tileID = 0xD3912 + parityX
        t.setTile(tileID, x, ylist[1])

        if height > 0:
            # row 2
            y = ylist[2]
            prevdyn = t.getdyn(x, y)
            if x == x0 and prevdyn == 0x3922: tileID = 0xD3937
            elif x != x0 and prevdyn == 0x3921: tileID = 0xD3936
            else:
                if prevdyn >> 8 == 0x39:
                    offset = (x == x0)
                else:
                    offset = parityX
                if t.getdyn(x, y-1) in (0x3907, 0x3908):
                    tileID = 0xD3918 + offset
                else:
                    tileID = 0xD3914 + offset
            t.setTile(tileID, x, y)

            # remaining rows
            for y in ylist[3:]:
                setlandinterior_shared(t, x, y, y == ylist[-1])

        parityX ^= 1

landwalltiles = (
    (0xD3923, 0xD3923, 0xD3925, 0xD3927),  # left wall
    (0xD3924, 0xD3924, 0xD3926, 0xD3928))  # right wall
def setlandwalltile(t, x, y, side: int):
    """Create a land wall tile at the specified coordinates.
    side: 0 = left wall (obj 02/0A), 1 = right wall (obj 03/0B)"""
    tileID = random.choice(landwalltiles[side])
    match t.getdyn(x, y):
        case 0x2A00 | 0x2A01:
            tileID = 0xD3929 + side
        case 0x3907 | 0x3912 | 0x3913:
            if t.getdyn(x, y-1) not in (0x3936, 0x3937):
                t.setTile(0xD3929 + side, x, y-1, priority=False, highlight=False)
            if (side == 1 and t.getdyn(x-1, y) == 0x390D or
                side == 0 and t.getdyn(x+1, y) == 0x390D):
                tileID = 0xD390B + side
            else:
                t.setTile(0xD3919 - side, x, y+1, priority=False, highlight=False)
                tileID = 0xD3907
    t.setTile(tileID, x, y)

obj0203data = {
    0x02: {"offsetX": -1,
           "cornertiles": (0xC3B00, 0xC2A01, 0xC3B02, 0xD391F)},
    0x03: {"offsetX": 0,
           "cornertiles": (0xC2A01, 0xC3B01, 0xD3920, 0xC3B03)},
    }
def obj0203(t, x, y0, _, height):
    data = obj0203data[t.obj.ID]
    side = t.obj.ID & 1
    ylist = list(t.yrange(y0-1, height+1))

    # row 0-1
    t.rect_iter_row(data["cornertiles"], x + data["offsetX"], y0-1, 1, 1)
    if height != 0:  # height only affects main column
        # row 2
        if t.getdyn(x, ylist[2]) in (0x2A00, 0x2A01):
            tilebase = 0xD3936
        else:
            tilebase = 0xD3921
        t.setTile(tilebase + side, x, ylist[2])
        # remaining rows
        for y in ylist[3:]:
            setlandwalltile(t, x, y, side)

obj0A0Bcorner = (0xD3909, 0xD390A)
def obj0A0B(t, x, y0, _, height):
    ygen = t.yrange(y0, height)
    side = t.obj.ID & 1

    # row 0
    y = next(ygen)
    t.setTile(obj0A0Bcorner[side], x, y)
    # remaining rows
    for y in ygen:
        setlandwalltile(t, x, y, side)
    
obj0409data = {
    0x04: {"columns": ((0xC2A02, 0xD0F00, 0xD1300, 0xD390E),
                       (0xC2A03, 0xD1000, 0xD1100, 0xD3918)),
           "heightoffset": 1, "slope": -1, "parityX": True},
    0x05: {"columns": ((0xC2A04, 0xD0C00, 0xD0E00, 0xD3919),
                       (0xC2A05, 0xD0D00, 0xD1200, 0xD390F)),
           "heightoffset": 2, "slope": +1, "parityX": True},
    0x06: {"surface": (0xC2A07, 0xD0A00, 0xD0B00, 0xD3916),
           "heightoffset": 1, "slope": -1, "parityX": False},
    0x07: {"surface": (0xC2A06, 0xD0800, 0xD0900, 0xD3917),
           "heightoffset": 2, "slope": +1, "parityX": False},
    0x08: {"surface": (0xC2A08, 0xD0500, 0xD0600, 0xD0700, 0xD392D),
           "heightoffset": 1, "slope": -2, "parityX": False},
    0x09: {"surface": (0xC2A09, 0xD0200, 0xD0300, 0xD0400, 0xD392E),
           "heightoffset": 2, "slope": +2, "parityX": False},
    }
def obj0409(t, x0, y0, width, height):
    parityX = 0
    data = obj0409data[t.obj.ID]
    y0 -= data["heightoffset"]
    adjheight = t.obj.adjheight
    adjheight += data["heightoffset"]
    if data["parityX"]:
        colgen = itertools.cycle(data["columns"])
    else:
        colgen = itertools.repeat(data["surface"])

    for x, toptiles in zip(t.xrange(x0, width), colgen):
        ylist = list(t.yrange_adj(y0, adjheight))
        if adjheight > 0:
            # positive height: normal behavior
            threshold = len(toptiles)

            for tileID, y in zip(toptiles, ylist):
                t.setTile(tileID, x, y)
            for y in ylist[threshold:]:
                setlandinterior_shared(t, x, y, y == ylist[-1])
        else:
            # negative height due to slope -2 (obj 08): glitched behavior
            t.setTile(toptiles[0], x, ylist[0])
            for y in ylist[1:]:
                t.setTile(0x11000 + t.obj.ID, x, y)

        # adjust for slope
        if data["parityX"] is False or parityX == 1:
            # for obj04-05, only adjust slope if odd X
            y0 -= data["slope"]
            adjheight += data["slope"]
            if adjheight == 0:
                return

        parityX ^= 1

####

def obj0C(t, x, y0, _, height):
    t.column_iter(genseq_bordered(height+1, 0xD6B00, 0xD6B01, 0xD6B02), x, y0)

def obj2B(t, x, y0, _, height):
    # same as 0C, but with a glitched height 1 (0 internally)
    if height != 0:
        obj0C(t, x, y0, _, height)
    else:
        # overflowed tile ID
        t.setTile(0xD6B03 if t.fixver > 0 else 0x01FD, x, y0)

obj0Dwalls = (0xD3904, 0xD3801, 0xD3903)
def obj0D(t, x0, y, width, _):
    for x, i in zip(t.xrange(x0, width), genseq_bordered(width+1)):
        prevhi = t.getTile(x, y) & 0xFF00
        if prevhi == t.dyn[0x3800]:
            # extend platform
            # can only match in tilesets 1/9/11, where t.dyn[0x3800] == 0x3800
            tileID = 0xD3801
        elif prevhi == t.dyn[0x3900]:
            tileID = obj0Dwalls[i]
        else:
            tileID = 0xD3800 + i
        t.setTile(tileID, x, y)

#### Objects 0E-13,3E: ski lifts

def obj0E(t, x, y0, _, height):
    t.column_iter(genseq_bordered(height+1, 0x0091, 0x0095, 0xD2A0B), x, y0)

def obj0F(t, x, y0, _, height):
    t.column_iter(genseq_bordered(height+1, 0x0090, 0x0094, 0xD2A0A), x, y0)

def obj1012edge(t, default: int, x, ylist):
    """Shared overlap check for ski lift poles of objects 10-12, to detect the
    double-pole object 3E."""
    if t.getTile(x, ylist[0]) in (0x00B4, 0x00A7):
        edgetile = 0x00A7
    else:
        edgetile = default
    t.setTile(edgetile, x, ylist[0])
    for y in ylist[1:]:
        t.setTile(-1, x, y)
def obj10(t, x0, y0, width, _):
    if width >= 0:
        slopetiles = ((0x009C,0x009A),(0x009B,-1))
        edgetiles = (0x0093, 0x0092)
    else:
        slopetiles = ((0x009D,0x009F),(0x009E,-1))
        edgetiles = (0x0092, 0x0093)
    xgen = t.xrange(x0, width)
    ylist = list(t.yrange(y0, (abs(width) // 2 + 1)))

    # first column
    x = next(xgen)
    obj1012edge(t, edgetiles[0], x, ylist[0:2])
    if width != 0:
        y_index = 0
        parity = 1
        # middle columns
        for _ in range(abs(width)-1):
            x = next(xgen)
            tiles = slopetiles[parity]
            t.setTile(tiles[0], x, ylist[y_index])
            t.setTile(tiles[1], x, ylist[y_index + 1])
            if parity == 0:
                y_index += 1  # offset 1 tile downward, every 2 columns
            parity ^= 1
        # last column
        x = next(xgen)
        obj1012edge(t, edgetiles[parity], x, ylist[y_index:y_index+2])

obj1112column = {
    0x11: ((0x0097,0x0096), (0x0098,0x0099)),
    0x12: ((0x00A5,0x00A3,0x00A4), (0x00A0,0x00A2,0x00A1))}
def obj1112(t, x0, y0, width, _):
    slope = t.obj.ID & 0xF
    slopetiles = obj1112column[t.obj.ID][0 if width >= 0 else 1]
    xgen = t.xrange(x0, width)
    ylist = list(t.yrange(y0, (abs(width) - 1) * slope))

    # first column
    x = next(xgen)
    obj1012edge(t, 0x0093 if width >= 0 else 0x0092, x, ylist[0:slope+1])
    if width != 0:
        y_index = 0
        # middle columns
        for _ in range(abs(width)-1):
            x = next(xgen)
            for y, tileID in zip(ylist[y_index:y_index+slope+1], slopetiles):
                t.setTile(tileID, x, y)
            y_index += slope
        # last column
        x = next(xgen)
        obj1012edge(t, 0x0092 if width >= 0 else 0x0093,
                    x, ylist[y_index:y_index+slope+1])

def obj13(t, x0, y, width, _):
    tilegen = genseq_bordered(width+1, 0x0093, 0x00A6, 0x0092)
    for x in t.xrange(x0, width):
        tileID = next(tilegen)
        if t.getTile(x, y) in (0x00B4, 0x00A7):
            tileID = 0x00A7
        t.setTile(tileID, x, y)

def obj3E(t, x, y0, _, height):
    tilegen = genseq_bordered(height+1, 0x00B3, 0x00B4, 0xD2A0C)
    for y in t.yrange(y0, height):
        tileID = next(tilegen)
        if t.getTile(x, y) in (0x0092, 0x0093, 0x00A7):
            tileID = 0x00A7
        t.setTile(tileID, x, y)

####

obj14checktiles = {
    0x3912:0x14, 0x3913:0x15, 0x2A00:0x16, 0x2A01:0x17, 0x3930:0x18,
    0x3933:0x19, 0x3923:0x1A, 0x3925:0x1B, 0x3927:0x1C,
    0x3924:0x21, 0x3926:0x22, 0x3928:0x23, 0x3929:0x24, 0x392A:0x25, 
    }
obj14rect_subindexlookup = (6, 9, 11, 7, None, 12, 8, 10, 13)
def obj14replacetile(t, x, y, subtableindex: int):
    prevtile = t.getTile(x, y)
    if prevtile & 0xFF00 == t.dyn[0x1900]:
        subindex = (prevtile & 0xFF) + 1
    else:
        subindex = obj14checktiles.get(t.getdyn(x, y), 0)

    tileID = obj14replace[subtableindex * 0x2F + subindex]
    if tileID is None:
        # in-game dynamic RAM table overflow: use red error tile
        tileID = 0x11014
    t.setTile(tileID, x, y)

def obj14(t, x0, y0, width, height):
    if width == 0:
        indexgen = genseq_bordered(height+1, 1, 0, 2)
        for y in t.yrange(y0, height):
            obj14replacetile(t, x0, y, next(indexgen))
    elif height == 0:
        indexgen = genseq_bordered(width+1, 4, 3, 5)
        for x in t.xrange(x0, width):
            obj14replacetile(t, x, y0, next(indexgen))
    else:
        indexgen = gen_rectindex(width, height)
        for y, x in itertools.product(t.yrange(y0, height),
                                      t.xrange(x0, width)):
            subindex = obj14rect_subindexlookup[next(indexgen)]
            if subindex is None:  # central tile doesn't depend on overlap
                t.setTile(0xD1912, x, y)
            else:
                obj14replacetile(t, x, y, subindex)

        # replace land surface decorations above
        y_above = t.y_offset(y0, -1)
        for x, replacetile in zip(t.xrange(x0, width),
                                  genseq_bordered(width+1, 0x007E, 0, 0x007F)):
            if t.getdyn(x, y_above) in (0x2A00, 0x2A01):
                t.setTile(replacetile, x, y_above, priority=False, highlight=False)

def obj15(t, x0, y0, width, _):
    ygen = t.yrange(y0, 1)
    t.row_iter(genseq_bordered(width+1, 0x00DB, 0x00DD, 0x00DC), x0, next(ygen))
    t.row_iter(genseq_bordered(width+1, 0x150F, 0x1511, 0x1510), x0, next(ygen))

#### Objects 16-1C: Submarine tileset

def obj1619widthfix(obj, tileset: int) -> int:
    if obj.width < 0 and tileset == 2:
        obj.width %= 0x100
    elif obj.width >= 0x80 and tileset != 2:
        obj.width -= 0x100
    return obj.width

def obj16(t, x0, y0, width, height):
    width = obj1619widthfix(t.obj, t.tileset)
    for x, y in itertools.product(t.xrange(x0, width),
                                  t.yrange(y0, height)):
        if t.getTile(x, y) == 0:
            t.setTile(0x1600, x, y)

obj17tiles_land =  (0x011A, 0x011A, 0x011A,
                    0x011C, 0x011D, 0x011E,
                    0x013A, 0x013B, 0x013C)
obj17tiles_water = (0x011F, 0x0120, 0x0121,
                    0x0122, 0x0123, 0x0124,
                    0x0137, 0x0138, 0x0139)
def obj17(t, x0, y0, width, height):
    xlist = list(t.xrange(x0-1, width+2))
    y_above = t.y_offset(y0, -1)

    # object generates 2 rows of vines at y-1 and y0, if not in water
    # vine center
    for x in xlist[1:-1]:
        if t.getTile(x, y_above) >> 8 == 0x16:
            t.setTile(-1, x, y_above)  # skip tile but enable screen
        else:
            t.setTile(0x0021, x, y_above)
    # vine left edge
    if t.getTile(x0, y0) >> 8 != 0x16 and\
       t.getTile(xlist[0], y_above) == 0:
        t.setTile(0x0020, xlist[0], y_above, priority=False, highlight=False)
    if t.getTile(x0, t.y_offset(y0, 1)) >> 8 != 0x16 and\
       t.getTile(xlist[0], y0) == 0:
        t.setTile(0x001F, xlist[0], y0, priority=False, highlight=False)
    # vine right edge
    if t.getTile(xlist[-2], y0) >> 8 != 0x16 and\
       t.getTile(xlist[-1], y_above) == 0:
        t.setTile(0x0023, xlist[-1], y_above, priority=False, highlight=False)
    if t.getTile(xlist[-2], t.y_offset(y0, 1)) >> 8 != 0x16 and\
       t.getTile(xlist[-1], y0) == 0:
        t.setTile(0x0024, xlist[-1], y0, priority=False, highlight=False)

    # main rectangular block
    indexgen = gen_rectindex(width, height)
    for y, x in itertools.product(t.yrange(y0, height), xlist[1:-1]):
        if t.getTile(x, y) >> 8 == 0x16:  # water
            t.setTile(obj17tiles_water[next(indexgen)], x, y)
        else:
            t.setTile(obj17tiles_land[next(indexgen)], x, y)

def obj18(t, x0, y0, width, height):
    indexgen = gen_rectindex(width, height)
    for y, x in itertools.product(t.yrange(y0, height), t.xrange(x0, width)):
        if t.getTile(x, y) >> 8 == 0x16:  # water
            t.setTile(0x012E + next(indexgen), x, y)
        else:
            t.setTile(0x0125 + next(indexgen), x, y)

def obj19columngen(relX) -> Iterator[int]:
    tiles = range(0x1601 + (relX&3), 0x1615, 4)
    yield from tiles
    while True:
        yield tiles[3]
        yield tiles[4]
def obj19(t, x0, y0, width, height):
    width = obj1619widthfix(t.obj, t.tileset)
    for relX, x in enumerate(t.xrange(x0, width)):
        t.column_iter(obj19columngen(relX), x, y0, height)

def obj1A(t, x0, y, width, _):
    xlist = list(t.xrange(x0, width))
    t.setTile(0x1505, x0, y)
    if width > 1:
        for x in xlist[1:-1]:
            t.setTile(0x1509 if t.getTile(x, y) == 0x0019 else 0x1501, x, y)
        t.setTile(0x1506, xlist[-1], y)

obj1Btiles = (0x1500,0x0019,0x001A,  # default
              0x1400,0x1615,0x1616,  # in water
                -1  ,0x1509,0x1507)  # crossing platform
def obj1B(t, x, y0, _, height):
    for y, index in zip(t.yrange(y0, height), genseq_bordered(height)):
        prevtile = t.getTile(x, y)
        if prevtile & 0xFF00 == 0x1600:  # water
            index += 3
        elif prevtile in (0x1501,0x1502):  # semisolid platform
            index += 6
        t.setTile(obj1Btiles[index], x, y)

def obj1C(t, x0, y0, _, height):
    x1 = t.x_offset(x0, 1)
    tilegen = genseq_bordered(height+1, 0x1507, 0x001B, 0x1503)
    for y in t.yrange(y0, height):
        tileID = next(tilegen)
        t.setTile(tileID, x0, y)
        t.setTile(tileID+1, x1, y)

#### Objects 21-36 (except 2B,35): Jungle tileset

randmudinterior = (  # 9068-9071, but with 906B weight 2, 906D weight 5
    0x9068,0x9069,0x906A,0x906B,0x906C,0x906D,0x906E,0x906F,0x9070,0x9071,
    0x906B,0x906D,0x906D,0x906D,0x906D,0x906D)

def obj21_y0(t, x, y, xlist, prevtile: int, height) -> int:
    if 0x9400 <= prevtile < 0x9600:  # mud slope, high byte 94 or 95
        if x == xlist[0]:
            t.setTile(0x90A3, x, y+1, priority=False, highlight=(height>=1))
            t.setTile(0x9073, x, y+2, priority=False, highlight=(height>=2))
            return 0x9500
        elif x == xlist[-1]:
            t.setTile(0x90A2, x, y+1, priority=False, highlight=(height>=1))
            t.setTile(0x9072, x, y+2, priority=False, highlight=(height>=2))
            return 0x9402

def obj21_y1(t, x, y, xlist, prevtile: int, height) -> int | None:
    # tile ID for current location depends on direction of mud slope
    if prevtile >> 8 == 0x94:
        tileID = 0x330D
    elif prevtile >> 8 == 0x95:
        tileID = 0x3512
    else:
        return

    # tile IDs for adjacent locations depend on first/last X
    # return None for mid X
    if x == xlist[0]:
        t.setTile(0x9204, x, y-1, priority=False)
        t.setTile(0x908F, x, y+1, priority=False, highlight=(height>=2))
        t.setTile(0x964D, x-1, y, priority=False, highlight=False)
        return tileID
    elif x == xlist[-1]:
        t.setTile(0x9205, x, y-1, priority=False)
        t.setTile(0x907F, x, y+1, priority=False, highlight=(height>=2))
        t.setTile(0x964E, x+1, y, priority=False, highlight=False)
        return tileID

obj21overlapfunc = (obj21_y0, obj21_y1, lambda *_ : None)
obj21defaults = (0x9200,0x9080,0x9090)
obj21checktiles = (0x9072,0x9073,0x907F,0x908F,0x90A2,0x90A3)
def obj21(t, x0, y0, width, height):
    xlist = list(t.xrange(x0, width))
    ylist = list(t.yrange(y0, height))
    for x in xlist:
        randoffset = random.randrange(4)
        for relY, y in enumerate(ylist[0:3]):
            prevtile = t.getTile(x, y)
            overlaptile = obj21overlapfunc[relY](t, x, y, xlist, prevtile, height)
            if overlaptile is not None:
                tileID = overlaptile
            elif prevtile in obj21checktiles:
                tileID = -1
            else:
                tileID = obj21defaults[relY] + randoffset
            t.setTile(tileID, x, y)
        for y in ylist[3:]:
            t.setTile(random.choice(randmudinterior), x, y)

obj24surfacebase = (0xA9608, 0x9300)
def obj24(t, x0, y0, width, height):
    xlist = list(t.xrange(x0, width))
    ygen = t.yrange(y0, height)

    if height == 0:
        # make top row major if it's the only row
        for x in xlist:
            t.setTile(0x9608 + random.randrange(4), x, y0)
    else:
        # first 2 rows
        for tileID, y in zip(obj24surfacebase, ygen):
            for x in xlist:
                t.setTile(tileID + random.randrange(4), x, y)
        # remaining rows
        for y in ygen:
            for x in xlist:
                t.setTile(random.choice(randmudinterior), x, y)

def _junglegrassoverlap(prevtile) -> int:
    if 0x9200 <= prevtile < 0x9204:
        return 0
    elif 0x9080 <= prevtile < 0x9084:
        return 1
    elif 0x9090 <= prevtile < 0x9094:
        return 2

def _mudcolumn(t, x, y, default, overlapseq: Iterable[int]):
    i = _junglegrassoverlap(t.getTile(x, y))
    t.setTile(overlapseq[i] if i is not None else default, x, y)

obj22top = (0x9204,0x330D,0x909C)
mudwall_overlap_left = (0x90A0,0x90A2,0x9072)
def obj22(t, x0, y0, _, height):
    x1 = t.x_offset(x0, 1)
    # column 0 (grass left tip)
    for relY, y in enumerate(t.yrange(y0, height)):
        t.setTile(0x964D if relY == 1 else -1, x0, y)

    # column 1 (main)
    ygen = t.yrange(y0, height)
    for tileID, y in zip(obj22top, ygen):
        t.setTile(tileID, x1, y)
    for y in ygen:
        _mudcolumn(t, x1, y, random.randrange(0x909E, 0x90A0),
                   mudwall_overlap_left)

obj23top = (0x9205,0x3512,0x909D)
mudwall_overlap_right = (0x90A1,0x90A3,0x9073)
def obj23(t, x0, y0, _, height):
    x1 = t.x_offset(x0, 1)
    # column 0 (main)
    ygen = t.yrange(y0, height)
    for tileID, y in zip(obj23top, ygen):
        t.setTile(tileID, x0, y)
    for y in ygen:
        _mudcolumn(t, x0, y, random.randrange(0x9062, 0x9064),
                   mudwall_overlap_right)

    # column 1 (grass right tip)
    for relY, y in enumerate(t.yrange(y0, height)):
        t.setTile(0x964E if relY == 1 else -1, x1, y)

def obj25(t, x, y0, _, height):
    ygen = t.yrange(y0, height)
    # surface slope
    y = next(ygen)
    if 0x9090 <= t.getTile(x+1, y) < 0x9094:
        t.setTile(0x908F, x+1, y, priority=False, highlight=False)
        t.setTile(0x964D, x, y-1, priority=False, highlight=False)
        t.setTile(0x330D, x+1, y-1, priority=False, highlight=False)
        t.setTile(0x9204, x+1, y-2, priority=False, highlight=False)
    t.setTile(0x9400, x, y)
    # remaining tiles
    for y in ygen:
        _mudcolumn(t, x, y, random.randrange(0x909E, 0x90A0),
                   mudwall_overlap_left)

def obj26(t, x, y0, _, height):
    ygen = t.yrange(y0, height)
    # surface slope
    y = next(ygen)
    if 0x9090 <= t.getTile(x-1, y) < 0x9094:
        t.setTile(0x907F, x-1, y, priority=False, highlight=False)
        t.setTile(0x964E, x, y-1, priority=False, highlight=False)
        t.setTile(0x3512, x-1, y-1, priority=False, highlight=False)
        t.setTile(0x9205, x-1, y-2, priority=False, highlight=False)
    t.setTile(0x9502, x, y)
    # remaining tiles
    for y in ygen:
        _mudcolumn(t, x, y, random.randrange(0x9062, 0x9064), mudwall_overlap_right)

obj2728data = {
    0x27: {"slopetiles": (0x9400,0x905C),
           "firstX_9080": (0x330D,0x9204,0x964D),
           "firstX_9080offsetX": -1,
           "firstX_9090": 0x908F,
           "lastXoverlap": (0x9402,0x90A2,0x9072),
           },
    0x28: {"slopetiles": (0x9501,0x905E),
           "firstX_9080": (0x3512,0x9205,0x964E),
           "firstX_9080offsetX": +1,
           "firstX_9090": 0x907F,
           "lastXoverlap": (0x9500,0x90A3,0x9073),
           }}
def obj2728(t, x0, y0, width, height):
    data = obj2728data[t.obj.ID]
    xlist = list(t.xrange(x0, width))
    for x in xlist:
        for relY, y in enumerate(t.yrange(y0, height)):
            # default tile
            if relY < 2:
                tileID = data["slopetiles"][relY] + random.randrange(2)
            else:
                tileID = random.choice(randmudinterior)
            # overlap checks
            if relY < 3:
                prevtile = t.getTile(x, y)
                if x == x0 and 0x9080 <= prevtile < 0x9084:
                    t.setTile(data["firstX_9080"][0], x, y)
                    t.setTile(data["firstX_9080"][1], x, y-1,
                              priority=False, highlight=False)
                    t.setTile(data["firstX_9080"][2],
                              x + data["firstX_9080offsetX"], y,
                              priority=False, highlight=False)
                    continue
                elif x == x0 and 0x9090 <= prevtile < 0x9094:
                    tileID = data["firstX_9090"]
                elif x == xlist[-1] and (index := _junglegrassoverlap(prevtile)) is not None:
                    tileID = data["lastXoverlap"][index]
            t.setTile(tileID, x, y)
        # adjust for slope
        if height == 0:
            return
        height -= 1
        y0 += 1

obj292Arandcol = {
    0x29: (((0x9B01,0x9639,0x9629,0x9631,0x961B),    # 29 variant A, relX even
            (0x9B00,0x9638,0x9628,0x9630,0x9620)),   # 29 variant A, relX odd
           ((0x961D,0x963D,0x962D,0x9635,0x961B),    # 29 variant B, relX even
            (0x961C,0x963C,0x962C,0x9634,0x9624))),  # 29 variant B, relX odd
    0x2A: (((0x960E,0x963A,0x962A,0x9632,0x961B),    # 2A variant A, relX even
            (0x960F,0x963B,0x962B,0x9633,0x9623)),   # 2A variant A, relX odd
           ((0x9B02,0x963E,0x962E,0x9636,0x961B),    # 2A variant B, relX even
            (0x9B03,0x963F,0x962F,0x9637,0x9627))),  # 2A variant B, relX odd
    }
def obj292Acolgen(randcol) -> Iterator[int]:
    # generate random pairs of columns
    while True:
        yield from random.choice(randcol)
def obj292A(t, x0, y0, width, height):
    colgen = obj292Acolgen(obj292Arandcol[t.obj.ID])
    parityX = 0
    adjheight = t.obj.adjheight
    for x in t.xrange(x0, width):
        tiles = next(colgen)
        if adjheight > 0:
            # positive height due to slope -2: glitched behavior
            tiles = tiles[0:1]
        for y, tileID in zip(t.yrange_adj(y0, adjheight),
                             gen_iter_default(tiles, 0x961B)):
            t.setTile(tileID, x, y)

        if parityX == 1:  # apply slope every 2 tiles
            adjheight += 2
            if adjheight == 0: break
            y0 -= 2
        parityX ^= 1

def obj2C(t, x0, y0, width, height):
    ygen = t.yrange(y0, height)
    x1 = t.x_offset(x0, 1)
    # row 0
    y = next(ygen)
    t.setTile(0x330E, x0, y)
    t.setTile(0x3511, x1, y)
    # remaining rows
    for y in ygen:
        tileID = random.randrange(0x90DA, 0x90E2, 2)
        t.setTile(tileID, x0, y)
        t.setTile(tileID+1, x1, y)

obj2D2Erandtiles = (
    {"top": (0x9211,0x9065,0x9075,0x9085),
     "Y0_9214replace": 0x9213,
     "mid": (0x9064,0x9074),
     "bottom": (0x9084,0x9094)},
    {"top": (0x9212,0x9078,0x9088,0x9079),
     "Y0_9214replace": 0x9214,
     "mid": (0x9074,0x9064),
     "bottom": (0x907E,0x908E)})
def obj2D2Ecolumngen(tiles, height, y0overlap: bool) -> Iterator[int]:
    for relY in range(height-1):
        if relY == 0 and y0overlap:
            yield tiles["Y0_9214replace"]
        elif relY < 4:
            yield tiles["top"][relY]
        else:
            yield tiles["mid"][relY&1]
    if height != 0:
        yield tiles["bottom"][0]
    yield tiles["bottom"][1]
def obj2D2E(t, x, y0, _, height):
    columngen = obj2D2Ecolumngen(random.choice(obj2D2Erandtiles), height,
                                 t.getTile(x, y0) == 0x9214)
    for y, tileID in zip(t.yrange(y0, height), columngen, strict=True):
        if t.obj.ID == 0x2E and random.randrange(2):
            if tileID == 0x9064:
                t.setTile(0x907B, x, y)
                t.setTile(0x907A, x-1, y, priority=False)
                continue
            elif tileID == 0x9064:
                t.setTile(0x9089, x, y)
                t.setTile(0x908A, x+1, y, priority=False)
                continue
        t.setTile(tileID, x, y)

obj2Ftop = (0x966F,0x9670,0x9671), (0x1530,0x9A00,0x1531)
def obj2F(t, x, y0, _, height):
    ylist = list(t.yrange(y0, height))
    for y, tiles in zip(ylist, obj2Ftop):  # rows 0-1
        t.setTile(tiles[1], x, y)
        t.setTile(tiles[0], x-1, y, priority=False)
        t.setTile(tiles[2], x+1, y, priority=False)
    if height >= 3:  # row 2
        t.setTile(0x990A, x, ylist[2])
    if height >= 2:
        for y in ylist[3:-1]:  # remaining rows
            t.setTile(random.randrange(0x990B,0x990D), x, y)
        t.setTile(0x9206, x, ylist[-1])  # last row


obj303136_replaceabove = {
    0x963B:0x9B04, 0x963C:0x9B05, 0x960E:0x9B06, 0x961D:0x9B07}
def obj303136_junglevinegen(t, x, y0, height, randoffset) -> Iterator[int]:
    """Code for object 30, and provides a default tile ID for 31/36 if not
    overridden."""
    # check above first row
    prevtile = t.getTile(x, y0)
    if 0x9B00 <= prevtile < 0x9B04:
        # skip row, and skip check above
        yield prevtile
        if height == 0: return
        y0 += 1
        height -= 1
    else:
        t.lookup_replace(obj303136_replaceabove, x, y0-1,
                         priority=False, highlight=False)

    ygen = t.yrange(y0, height)
    if height != 0:
        # all non-last rows
        for i in range(height):
            y = next(ygen)
            prevtile = t.getTile(x, y)
            if prevtile == 0x960F:
                yield 0x9900
            elif prevtile == 0x961C:
                yield 0x9901
            else:
                yield 0x9908 + randoffset + random.randrange(2)

    # last row
    y = next(ygen)
    prevtile = t.getTile(x, y)
    if prevtile >> 8 == 0x92:
        if prevtile <= 0x920E:
            yield 0x9215
        else:
            yield obj303136_replace920F[prevtile - 0x920F]
    else:
        if randoffset == 0:
            yield 0x00AC + random.randrange(2)
        else:
            yield 0x00AE + random.randrange(2)

def obj30(t, x, y0, _, height):
    randoffset = random.choice((0, 0xB))
    t.column_iter(obj303136_junglevinegen(t, x, y0, height, randoffset), x, y0)

def obj3136(t, x, y0, _, height):
    if t.obj.ID == 0x31:
        randoffset = random.choice((0, 0xB))
    else:
        randoffset = 0xB
    for relY, (y, tileID) in enumerate(zip(t.yrange(y0, height),
                        obj303136_junglevinegen(t, x, y0, height, randoffset))):
        if 2 <= relY < height:
            leafoffset = random.randrange(8)
            if leafoffset <= 5:
                # replace central tile, add side leaves 3/4 of the time
                tileID = 0x9902 + leafoffset
            t.setTile(tileID, x, y)

            # add side leaves if applicable
            if leafoffset <= 3:  # left leaf
                t.setTile(0x9672 + (leafoffset&1)*2 + (4 if randoffset else 0),
                          x-1, y, priority=False)
            if leafoffset in (0, 1, 4, 5):  # right leaf
                t.setTile(0x9673 + (leafoffset&1)*2 + (4 if randoffset else 0),
                          x+1, y, priority=False)
        else:
            t.setTile(tileID, x, y)

def obj3233leftcheck(t, x, y) -> int:
    tileID = random.randrange(0x90B6, 0x90BA)
    if 0x90C4 <= t.getTile(x-1, y) < 0x90C8:
        tileID += 4
    return tileID
def obj3233rightcheck(t, x, y) -> int:
    tileID = random.randrange(0x90C4, 0x90C8)
    if 0x90B6 <= t.getTile(x+1, y) < 0x90BA:
        tileID += 4
    return tileID
obj32func = [
    lambda *_ : 0x90A8,
    lambda *_ : random.randrange(0x90BE, 0x90C0),
    lambda *_: 0x90A9,
    obj3233leftcheck,
    lambda *_ : random.randrange(0x90D2, 0x90DA),
    obj3233rightcheck,
    lambda t, x, y : 0x90CC if t.getTile(x, y) >> 8 == 0x92 else 0x90AE,
    lambda t, x, y : (0x90CE if t.getTile(x, y) >> 8 == 0x92 else 0x90B2)
                      + random.randrange(4),
    lambda t, x, y : 0x90CD if t.getTile(x, y) >> 8 == 0x92 else 0x90AF,
    ]
obj33func = [
    lambda *_ : 0x90AA,
    lambda *_ : random.randrange(0x90C0, 0x90C4),
    lambda *_ : 0x90AB,
    ] + obj32func[3:]

def obj3233(t, x0, y0, width, height):
    rectgen = gen_rectindex(width, height)
    funclist = obj33func if t.obj.ID == 0x33 else obj32func
    for y, x in itertools.product(t.yrange(y0, height), t.xrange(x0, width)):
        tileID = funclist[next(rectgen)](t, x, y)
        t.setTile(tileID, x, y)

def obj34(t, x0, y0, width, _):
    y1 = t.y_offset(y0, 1)
    for x in t.xrange(x0, width):
        tile1 = random.randrange(0x964F,0x965F)
        tile0 = tile1 - 0xF if tile1 <= 0x965A else -1
        if 0x9608 <= t.getTile(x, y1) < 0x960C:
            tile1 += 0x10
        t.setTile(tile0, x, y0)
        t.setTile(tile1, x, y1)

#### Object 35: Animated water

obj35surfacecol = (
    ((0x161B,0x1628), (0x161C,0x1628)),  # default
    ((0x1619,0x1626), (0x161A,0x1627)))  # light beams 1/4 chance
def obj35(t, x0, y0, width, height):
    ylist = list(t.yrange(y0, height))
    parityX = 0
    for x in t.xrange(x0, width):
        if parityX == 0:
            randindex = (random.randrange(4) == 0)  # 1/4 chance of 1
        for relY, y in enumerate(ylist):
            # default tile
            if relY <= 1:
                # manual lookup since randindex can change on overlap
                tileID = obj35surfacecol[randindex][parityX][relY]
            else:
                tileID = 0x1628

            # overlap check
            prevtilehi = t.getTile(x, y) >> 8
            match prevtilehi:
                case 0x6B | 0x90 | 0x93:  # poundable post, solid jungle tiles
                    randindex = 0  # reset randindex
                    if relY == 0:
                        tileID = 0x9061
                    elif relY == 1:
                        tileID = random.choice((0x9098,0x9098,0x9099,0x909A))
                    else:
                        tileID = 0x909B
                case 0x94 | 0x95:  # water slope
                    tileID = (prevtilehi + 3) << 8
                    if relY != 0:
                        tileID += 1
            t.setTile(tileID, x, y)
        parityX ^= 1

#### Object 37: Red bridge, horizontal

def obj37(t, x0, y, width, _):
    for x in t.xrange(x0, width):
        if t.getTile(x, y) == 0:
            t.setTile(0x1512, x, y)

#### Objects 38-39: Hookbill/4-Secret blocks

def obj3839cornercheck(t, x0, y0):
    """Apply the game's object 38/39 corner conversion to 4 tiles in a square,
    if applicable, given the coordinates of the square's top-left corner."""
    corners = list(itertools.product(t.xrange(x0, 1), t.yrange(y0, 1)))

    # test if all tiles have high byte 9D
    for x, y in corners:
        if t.getTile(x, y) >> 8 != 0x9D:
            return
    # if so, replace corners
    for x, y in corners:
        t.setTile(obj3839transformed[t.getTile(x, y) & 0xFF],
                  x, y, priority=False, highlight=False)

def obj38vertedgecheck(t, x0, y0, offsetX):
    """Apply the game's object 38 left/right edge conversion to a tile, and its
    adjacent tile in the specified direction."""
    x1 = t.x_offset(x0, offsetX)

    # test if the 3 adjacent tiles have high byte 9D
    for x, y in ((x1, y0), (x1, t.y_offset(y0, -1)), (x1, t.y_offset(y0, +1))):
        if t.getTile(x, y) >> 8 != 0x9D:
            return
    # if so, replace edges
    for x, y in ((x0, y0), (x1, y0)):
        t.setTile(obj3839transformed[t.getTile(x, y) & 0xFF],
                  x, y, priority=False, highlight=False)

def obj38horizedgecheck(t, x0, y0, offsetY):
    """Apply the game's object 38 top/bottom edge conversion to a tile, and its
    adjacent tile in the specified direction."""
    y1 = t.y_offset(y0, offsetY)

    # test if the 3 adjacent tiles have high byte 9D
    for x, y in ((x0, y1), (t.x_offset(x0, -1), y1), (t.x_offset(x0, +1), y1)):
        if t.getTile(x, y) >> 8 != 0x9D:
            return
    # if so, replace edges
    for x, y in ((x0, y0), (x0, y1)):
        t.setTile(obj3839transformed[t.getTile(x, y) & 0xFF],
                  x, y, priority=False, highlight=False)

def obj38centercolumn(t, x, ylist, tiles):
    # top edge
    t.setTile(tiles[0], x, ylist[0])
    obj38horizedgecheck(t, x, ylist[0], -1)
    if len(ylist) > 1:
        # center tile
        for y in ylist[1:-1]:
            t.setTile(tiles[1], x, y)
        # bottom edge
        t.setTile(tiles[2], x, ylist[-1])
        obj38horizedgecheck(t, x, ylist[-1], 1)

obj38tiles = ((0x9D00,0x9D01,0x9D02,0x9D03,0x9D0A,0x9D0B,0x9D0C,0x9D0D,
               0x9D12,0x9D13,0x9D14,0x9D15),  # palette 2
              (0x9D1C,0x9D1D,0x9D1E,0x9D1F,0x9D24,0x9D25,0x9D26,0x9D27,
               0x9D2A,0x9D2B,0x9D2C,0x9D2D))  # palette 3
def obj38(t, x0, y0, width, height):
    tiles = random.choice(obj38tiles)
    xlist = list(t.xrange(x0, width))
    ylist = list(t.yrange(y0, height))

    # first column
    # top-left corner
    t.setTile(tiles[0], x0, y0)
    obj3839cornercheck(t, x0-1, y0-1)
    if height != 0:
        # left edge
        for y in ylist[1:-1]:
            t.setTile(tiles[4], x0, y)
            obj38vertedgecheck(t, x0, y, -1)
        # bottom-left corner
        t.setTile(tiles[8], x0, ylist[-1])
        obj3839cornercheck(t, x0-1, ylist[-1])

    if width != 0:
        # center columns
        parityX = 0
        for x in xlist[1:-1]:
            obj38centercolumn(t, x, ylist, tiles[1+parityX::4])
            parityX ^= 1

        # right column
        # top-right corner
        t.setTile(tiles[3], xlist[-1], y0)
        obj3839cornercheck(t, xlist[-1], y0-1)
        if height != 0:
            # right edge
            for y in ylist[1:-1]:
                t.setTile(tiles[7], xlist[-1], y)
                obj38vertedgecheck(t, xlist[-1], y, 1)
            # bottom-right corner
            t.setTile(tiles[0xB], xlist[-1], ylist[-1])
            obj3839cornercheck(t, xlist[-1], ylist[-1])

obj39tiles = (0x9D08,0x9D09,0x9D10,0x9D11)
def obj39(t, x0, y0, width, height):
    if width & 1 == 0: width += 1
    if height & 1 == 0: height += 1

    # modified objYX, with overlap check
    parityX = 0
    for x in t.xrange(x0, width):
        parityY = 0
        for y in t.yrange(y0, height):
            t.setTile(obj39tiles[parityY | parityX], x, y)
            obj3839cornercheck(t, x - (0 if parityX else 1),
                                  y - (0 if parityY else 1))
            parityY ^= 2
        parityX ^= 1

#### Objects 3A-3B: Regular land, ceiling slopes +2/-2

obj3A3Bdata = {
    0x3A: {"tiles": (0xA200, 0xA100), "slope": -2},
    0x3B: {"tiles": (0xA000, 0x9F00), "slope": +2}}
def obj3A3B(t, x0, y0, width, height):
    data = obj3A3Bdata[t.obj.ID]
    if t.obj.ID == 0x3B:  # 3B's actual height depends on its width
        height = t.obj._unadjlength(max(1, t.obj.adjheight - t.obj.adjwidth*2))

    for x in t.xrange(x0, width):
        ylist = list(t.yrange(y0, height))
        for y in ylist[:-2]:
            setlandinterior_shared(t, x, y, False)
        # last 2 rows: sloped surface
        for y, tileID in zip(reversed(ylist[-2:]), data["tiles"]):
            t.setTile(tileID, x, y)

        # adjust for slope
        height += data["slope"]
        if height < 0: height = 0

####

obj3CF4tiles = {  # +height tiles, -height tiles
    0x3C: ((0x7D08,0x9D32,0x9D34), (0x7D0A,0x9D32,0x9D36)),
    0xF4: ((0x79F1,0x79F3,0x79F5), (0x79A8,0x79F3,0x79A0))}
def obj3CF4(t, x0, y0, _, height):
    xlist = list(t.xrange(x0, 1))
    tilegen = genseq_bordered(
        abs(height)+1, *obj3CF4tiles[t.obj.ID][0 if height >= 0 else 1])
    for y in t.yrange(y0, height):
        tileID = next(tilegen)
        t.setTile(tileID, xlist[0], y)
        t.setTile(tileID+1, xlist[1], y)

def obj3D(t, x0, y0, width, _):
    columngen = genseq_bordered_cycle(width+1,
        (0x00B5 if t.getTile(x0, y0) in (0x00A8, 0x00A9) else 0x00A7,
         0x3C00, 0x00AB),  # left
        ((0x00A8, 0x3C01, 0x00B0), (0x00A9, 0x3C02, 0x00B1)),  # mid
        (0x00AA, 0x3C03, 0x00B2))  # right
    ylist = list(t.yrange(y0, 2))
    for x in t.xrange(x0, width):
        for y, tileID in zip(ylist, next(columngen)):
            t.setTile(tileID, x, y)

def obj3F40(t, x, y0, _, height):
    objoffset = t.obj.ID - 0x3F
    ygen = t.yrange(y0, height)

    y0 = next(ygen)
    t.setTile((0x0114 if t.getTile(x, y0) == 0 else 0x2904) + objoffset, x, y0)
    for y in ygen:
        t.setTile((0x2904 if t.getTile(x, y) == 0 else 0x2906) + objoffset, x, y)

#### Objects 41-43,48: Castle objects that can cast shadows on BG walls

castleBGwall_bottomleft = {  # to replace at y+1 in 41-43,48,6C
    0x00C2:0x00C3, 0x00C4:0x00D5, 0x00C5:0x00D5, 0x00C7:0x00C6,
    0x00D1:0x00C3, 0x150D:0x151B, 0x150E:0x151B}
castleBGwall_bottom = {  # to replace at y+1 (except first X) in 41,48,6C
    0x00BE:0x77DE, 0x00BF:0x77DF, 0x00C0:0x77E0, 0x00C1:0x77E1,
    0x00C2:0x00C6, 0x00C3:0x00C6, 0x00C4:0x00D5, 0x00C5:0x00D5,
    0x00C7:0x00C6, 0x00C9:0x77DA, 0x00CA:0x77DB, 0x00CB:0x77DC,
    0x00CC:0x77DD, 0x00D1:0x00C6, 0x00D6:0x77D8, 0x00D7:0x77D9,
    0x150D:0x151A, 0x150E:0x151A}
castleBGwall_topright = {  # to replace at x+1 in 41-43,48,6C
    0x00C2:0x00C4, 0x00C3:0x00D5, 0x00C6:0x00D5, 0x00C7:0x00C5,
    0x00D1:0x00C4, 0x150D:0x151B, 0x150E:0x151B}
castleBGwall_right = {  # to replace at x+1 (except first Y) in 42-43,48,6C
    0x002E:0x002F, 0x00BE:0x77E7, 0x00BF:0x77E9, 0x00C0:0x77E8,
    0x00C1:0x77E6, 0x00C2:0x00C5, 0x00C3:0x00D5, 0x00C4:0x00C5,
    0x00C6:0x00D5, 0x00C7:0x00C6, 0x00C9:0x77E5, 0x00CA:0x77E3,
    0x00CB:0x77E2, 0x00CC:0x77E4, 0x00D1:0x00C5, 0x00D6:0x77D8,
    0x00D7:0x77D9, 0x150D:0x151B, 0x150E:0x151B}
castleBGwall_bottomright = {  # to replace at x+1 y+1 in 41-43,48,6C
    0x00C2:0x00C7, 0x00C3:0x00C6, 0x00C4:0x00C5, 0x00D1:0x00C7,
    0x150D:0x151B, 0x150E:0x151B}
def obj4243486C_addshadows_right(t, x, ylist):
    for y in ylist[1:]:
        prevtile = t.getTile(x, y)
        if 0x0084 <= prevtile < 0x0089:
            if y == ylist[1]:
                tileID = random.randrange(0x0084, 0x0088)
            else:
                tileID = 0x0031
        else:
            tileID = castleBGwall_right.get(prevtile)
        if tileID is not None:
            t.setTile(tileID, x, y, priority=False, highlight=False)
def obj4243_addshadows(t, x, ylist):
    t.lookup_replace(castleBGwall_bottomleft, x, ylist[-1] + 1,
                     priority=False, highlight=False)
    t.lookup_replace(castleBGwall_topright, x + 1, ylist[0],
                     priority=False, highlight=False)
    obj4243486C_addshadows_right(t, x + 1, ylist)
    t.lookup_replace(castleBGwall_bottomright, x + 1, ylist[-1] + 1,
                     priority=False, highlight=False)
def obj486C_addshadows(t, xlist, ylist):
    t.lookup_replace(castleBGwall_bottomleft, xlist[0], ylist[-1] + 1,
                     priority=False, highlight=False)
    for x in xlist[1:]:
        t.lookup_replace(castleBGwall_bottom, x, ylist[-1] + 1,
                         priority=False, highlight=False)
    t.lookup_replace(castleBGwall_topright, xlist[-1] + 1, ylist[0],
                     priority=False, highlight=False)
    obj4243486C_addshadows_right(t, xlist[-1] + 1, ylist)
    t.lookup_replace(castleBGwall_bottomright, xlist[-1] + 1, ylist[-1] + 1,
                     priority=False, highlight=False)

def obj41(t, x0, y, width, _):
    xlist = list(t.xrange(x0, width))
    if width == 0:
        t.setTile(0x0156, x0, y)
    else:
        for x, tileID in zip(xlist,
                             genseq_bordered(width+1, 0x0153, 0x0154, 0x0155)):
            t.setTile(tileID, x, y)
        # top-right shadow runs only if adjwidth != 1
        t.lookup_replace(castleBGwall_topright, xlist[-1] + 1, y,
                         priority=False, highlight=False)

    # remaining shadow code
    t.lookup_replace(castleBGwall_bottomleft, xlist[0], y + 1,
                     priority=False, highlight=False)
    for x in xlist[1:]:
        t.lookup_replace(castleBGwall_bottom, x, y + 1,
                         priority=False, highlight=False)
    t.lookup_replace(castleBGwall_bottomright, xlist[-1] + 1, y + 1,
                     priority=False, highlight=False)

obj4243lavapillar = {
    0x00B6:0x7794, 0x00B7:0x7795, 0x00B8:0x7796, 0x00B9:0x7794, 0x00BA:0x7794,
    0: 0x11042,  # overflowed lookup reads part of level data, 4808 in vanilla
    }
def obj4243check(t, defaulttile: int, prevtile: int) -> int:
    if prevtile == 0x7E:
        return -1
    elif prevtile == 0x0032 or 0x0084 <= prevtile <= 0x008D:
        return obj4243lavapillar[defaulttile]
    return defaulttile

obj42_bottomtiles = (0x0000,0x00BA,0x00B9,0x00B6)
def obj42(t, x, y0, _, height):
    ylist = list(t.yrange(y0, height))
    parityY = 0
    for y in ylist[0:-3]:
        t.setTile(obj4243check(t, 0x00B6 + parityY, t.getTile(x, y)), x, y)
        parityY ^= 2
    index = 1
    for y in reversed(ylist[-3:]):
        if t.fixver > 0:
            tileID = obj42_bottomtiles[index]
        else:
            tileID = obj42_bottomtiles[index >> 1]
        t.setTile(obj4243check(t, tileID, t.getTile(x, y)), x, y)
        index += 1

    # add shadows to adjacent castle BG walls
    obj4243_addshadows(t, x, ylist)

def obj43(t, x, y0, _, height):
    tilegen = genseq_bordered(height+1, 0x00B6, 0x00B7, 0x00B8)
    ylist = list(t.yrange(y0, height))
    for y in ylist:
        t.setTile(obj4243check(t, next(tilegen), t.getTile(x, y)), x, y)

    # add shadows to adjacent castle BG walls
    obj4243_addshadows(t, x, ylist)

obj48lavachecktiles = {0x7E00, 0x7E01}.union(
    range(0x002E, 0x0033), range(0x0084, 0x008E))
def obj48(t, x0, y0, width, height):
    xlist = list(t.xrange(x0, width))
    ylist = list(t.yrange(y0, height))
    for x in xlist:
        for y in ylist:
            t.setTile(-1, x, y)  # enable screen if disabled
            if width == 0: tileID = 0x0152
            else: tileID = 0x015A + ((x^y)&1)

            if x == xlist[0]:
                lefttile = t.getTile(x-1, y)
                if lefttile in obj48lavachecktiles:
                    # add lava glow on left
                    if tileID == 0x015A: tileID = 0x01A2
                    else: tileID = 0x01A4
                elif tileID == 0x015B:
                    # merge bricks to left
                    if lefttile == 0x0152:
                        t.setTile(0x015A, x-1, y, priority=False, highlight=False)
                    else: tileID = 0x0151
            elif x == xlist[-1]:
                righttile = t.getTile(x+1, y)
                if righttile in obj48lavachecktiles:
                    # add lava glow on right
                    if tileID == 0x015B: tileID = 0x01A1
                    else: tileID = 0x01A3
                elif tileID == 0x015A:
                    # merge bricks to right
                    if righttile == 0x015B: tileID = 0x015A
                    elif righttile == 0x0151:
                        t.setTile(0x015B, x+1, y, priority=False, highlight=False)
                    else: tileID = 0x0152
            if y == ylist[0] and t.getTile(x, y-1) in (0x7E00, 0x7E01):
                # add lava glow on top
                tileID += 0x4B
            t.setTile(tileID, x, y)

    # add shadows to adjacent castle BG walls
    obj486C_addshadows(t, xlist, ylist)

#### Objects 44-46,CB-CD: Castle BG walls

def obj444546CCCD_addshadows_left(t, x, y):
    toptile = t.getTile(x, y-1)
    if 0x0151 <= t.getTile(x-1, y) <= 0x0160:
        # solid castle wall to left
        if 0x0151 <= toptile <= 0x0160:
            tileID = 0x00D5
        elif toptile in (0x00C2, 0x77E6, 0x77E7):
            tileID = 0x00C4
        else: tileID = 0x00C5
    elif toptile == 0x00C5:
        tileID = 0x00C7
    else:
        return  # leave tile unmodified
    t.setTile(tileID, x, y)
def obj44CBCCCD_addshadows_top(t, x, y, nextshadow: bool) -> bool:
    if 0x0151 <= t.getTile(x, y-1) <= 0x0160:
        # solid castle wall above
        if nextshadow:
            tileID = 0x00C6
        else:
            nextshadow = True
            if t.getTile(x, y) == 0x00D5:
                return nextshadow  # leave tile unmodified
            tileID = 0x00C3
            if t.getTile(x-1, y) == 0x00C6:
                tileID = 0x00C6
    else:
        if not nextshadow:
            return nextshadow  # leave tile unmodified
        nextshadow = False
        tileID = 0x00C7
    t.setTile(tileID, x, y)
    return nextshadow

def obj44(t, x0, y0, width, height):
    xlist = list(t.xrange(x0, width))
    ylist = list(t.yrange(y0, height))

    # start by filling rectangle with 00C2
    for x, y in itertools.product(xlist, ylist):
        t.setTile(0x00C2, x, y)

    # add shadows
    for y in ylist:
        obj444546CCCD_addshadows_left(t, x0, y)
    nextshadow = False
    for x in xlist:
        nextshadow = obj44CBCCCD_addshadows_top(t, x, y0, nextshadow)

    # fix bricks on either side
    x_left = t.x_offset(x0, -1)
    x_right = t.x_offset(xlist[-1], +1)
    for y in ylist:
        if t.getTile(x_left, y) == 0x015A:
            t.setTile(0x0152, x_left, y, priority=False, highlight=False)
        if t.getTile(x_right, y) == 0x015B:
            t.setTile(0x0151, x_right, y, priority=False, highlight=False)

objCBdefaulttiles = (0x00D6,0x00C2,0x00D7)
objCBshadowtiles = (0x77D8,None,0x77D9)
def objCB(t, x0, y0, width, height):
    ylist = list(t.yrange(y0, height))

    nextshadow = False
    for x, i in zip(t.xrange(x0, width), genseq_bordered(width+1)):
        defaulttile = objCBdefaulttiles[i]
        # first row
        if i != 1 and 0x0153 <= t.getTile(x, y0-1) <= 0x0160:
            # special handling for CB's top corners
            t.setTile(objCBshadowtiles[i], x, y0)
            nextshadow = True
        else:
            t.setTile(defaulttile, x, y0)
            nextshadow = obj44CBCCCD_addshadows_top(t, x, y0, nextshadow)
        # remaining rows
        for y in ylist[1:]:
            t.setTile(defaulttile, x, y)

castleslopedBGwalldata = {
    0x45: {"default": (0x00C1,0x00C0), "slope": -1,
           "topshadow": 0x77E1, "leftshadow": (0x77E6,0x77E8)},
    0x46: {"default": (0x00BE,0x00BF), "slope": +1,
           "topshadow": 0x77DE, "leftshadow": (0x77E7,0x77E9)},
    0xCC: {"default": (0x00C9,0x00CA), "slope": +1, "xleftindex": -1,
           "topshadow": (0x77DA,0x77DB), "leftshadow": (0x77E5,0x77E3)},
    0xCD: {"default": (0x00CC,0x00CB), "slope": +1, "xleftindex": 0,
           "topshadow": (0x77DD,0x77DC), "leftshadow": (0x77E4,0x77E2)},
    }

castlebricktiles = (0x0151,0x0152,0x015A,0x015B)
castleBGwall_LREdges = (0x00D6,0x00D7,0x77D8,0x77D9)
def obj4546(t, x0, y0, width, height):
    y0 -= 1
    height += 1
    data = castleslopedBGwalldata[t.obj.ID]
    xlist = list(t.xrange(x0, width))

    for x in xlist:
        ygen = t.yrange(y0, height)
        # first 2 rows
        for relY, y in zip(range(2), ygen):
            if relY == 0 and t.getTile(x, y-1) in castlebricktiles:
                t.setTile(data["topshadow"], x, y)
            elif t.getTile(x-1, y) in castlebricktiles:
                t.setTile(data["leftshadow"][relY], x, y)
            else:
                tileID = data["default"][relY]
                if tileID == 0x00C1 and t.getTile(x, y) in castleBGwall_LREdges:
                    tileID = -1
                t.setTile(tileID, x, y)
                obj444546CCCD_addshadows_left(t, x, y)
        # remaining rows: fall back to 44's code
        for y in ygen:
            t.setTile(0x00C2, x, y)
            obj444546CCCD_addshadows_left(t, x, y)
            # fix bricks on either side
            if x == xlist[0] and t.getTile(x-1, y) == 0x015A:
                t.setTile(0x0152, x-1, y, priority=False, highlight=False)
            elif x == xlist[-1] and t.getTile(x+1, y) == 0x015B:
                t.setTile(0x0151, x+1, y, priority=False, highlight=False)

        # adjust for slope
        y0 -= data["slope"]
        height += data["slope"]
        if height < 0:
            return

def objCCCD(t, x0, y0, width, height):
    data = castleslopedBGwalldata[t.obj.ID]
    xlist = list(t.xrange(x0, width))
    xleftedge = xlist[data["xleftindex"]]

    nextshadow = False
    for x in xlist:
        ygen = t.yrange(y0, height)
        # first 2 rows
        for relY, y in zip(range(2), ygen):
            if 0x0153 <= t.getTile(x, y-1) <= 0x0160:
                tileID = data["topshadow"][relY]
            elif 0x0153 <= t.getTile(x-1, y) <= 0x0160:
                tileID = data["leftshadow"][relY]
            elif relY == 0 and t.getTile(x, y) != 0:
                tileID = -1
            else:
                tileID = data["default"][relY]
            t.setTile(tileID, x, y)
        # remaining rows
        if height <= -2:
            for y in ygen:
                t.setTile(0x00C2, x, y)
                if x == xleftedge:
                    if (0x0153 <= t.getTile(x, y-1) <= 0x0160 and
                        0x0153 <= t.getTile(x-1, y-1) <= 0x0160):
                            t.setTile(0x00C7, x, y)
                    obj444546CCCD_addshadows_left(t, x, y)
            # extra checks for top (last) row
            if t.getTile(x, y) == 0x00D5:
                nextshadow = False
            elif 0x0153 <= t.getTile(x-1, y-1) <= 0x0160:
                nextshadow = True
            elif t.obj.ID == 0xCC:
                nextshadow = False
                # object CD leaves nextshadow unchanged here
            nextshadow = obj44CBCCCD_addshadows_top(t, x, y, nextshadow)

        # adjust for slope
        y0 -= data["slope"]
        height += data["slope"]
        if height > 0:
            return

#### Object 47: Lava pool

obj47randsurface = (0x0084,0x0084,0x0085,0x0085,0x0086,0x0086,0x0087,0x0088)
obj47replaceleft = {0x015A:0x01A3, 0x015B:0x01A1, 0x0151:0x01A3, 0x0152:0x01A3}
obj47replaceright = {0x015A:0x01A2, 0x015B:0x01A4, 0x0151:0x01A4, 0x0152:0x01A4}
obj47replacedown = {0x015A:0x01A5, 0x015B:0x01A6, 0x0151:0x01A5, 0x0152:0x01A6}
def obj47(t, x0, y0, width, height):
    xlist = list(t.xrange(x0, width))
    ylist = list(t.yrange(y0, height))

    # row 0: lava surface
    for x in xlist:
        tileID = random.choice(obj47randsurface)
        match t.getTile(x, y0-1):
            # replace certain BG walls above
            case 0x00C2:
                newtileabove = 0x002E
            case 0x00C4:
                newtileabove = 0x0030
                tileID = 0x0031
            case 0x00C5:
                newtileabove = 0x002F
                tileID = 0x0031
            case _:
                # add to BG wall surface, to produce non-BG wall surface
                newtileabove = None
                tileID += 5
        t.setTile(tileID, x, y0)
        if newtileabove is not None:
            t.setTile(newtileabove, x, y0-1, priority=False, highlight=False)

    # remaining rows: lava interior
    for y in ylist[1:]:
        tileID = 0x7E00
        for x in xlist:
            t.setTile(tileID, x, y)
            tileID ^= 1  # alternate 7E00 and 7E01

    # add lava glow to adjacent castle bricks
    for y in ylist:
        t.lookup_replace(obj47replaceleft, x0-1, y,
                         priority=False, highlight=False)
        t.lookup_replace(obj47replaceright, xlist[-1]+1, y,
                         priority=False, highlight=False)
    for x in xlist:
        t.lookup_replace(obj47replacedown, x, ylist[-1]+1,
                         priority=False, highlight=False)

#### Objects 49-4D: Misc castle tileset objects

def obj49(t, x0, y0, _, height):
    x1 = t.x_offset(x0, 1)
    ygen = t.yrange(y0, height)
    # row 0
    y0 = next(ygen)
    t.setTile(0x00C8, x0, y0)
    t.setTile(0x00CD, x1, y0)
    for y in ygen:  # row 1+
        t.setTile(0x00CE, x0, y)
        t.setTile(0x00CF, x1, y)

def obj4A(t, x0, y0, _, height):
    x1 = t.x_offset(x0, 1)
    for y in t.yrange(y0, height):
        t.setTile(0x00D3, x0, y)
        t.setTile(0x00D4, x1, y)

obj4B4Ddata = {
    0x4B: ((0x0174,0x0175,0x0175,0x0178),
           (0x0179,0x017A,0x017A,0x017D),
           (0x017E,0x017F,0x017F,0x0182)),
    0x4C: ((0x0174,0x0175,0x0175,0x0175,0x0176,0x0178),
           (0x0179,0x017A,0x017A,0x017A,0x017B,0x017D),
           (0x017E,0x017F,0x017F,0x017F,0x0180,0x0182)),
    0x4D: ((0x0174,0x0175,0x0175,0x0175,0x0175,0x0175,0x0177,0x0178),
           (0x0179,0x017A,0x017A,0x017A,0x017A,0x017A,0x017C,0x017D),
           (0x017E,0x017F,0x017F,0x017F,0x017F,0x017F,0x0181,0x0182)),
    }
def obj4B4D(t, x0, y0, _, height):
    rowgen = genseq_bordered(height+1, *obj4B4Ddata[t.obj.ID])
    for y in t.yrange(y0, height):
        t.row_iter(next(rowgen), x0, y)

#### Objects 4E-4F: Breakable dirt

def obj4Etile(t, x, y, pos, tilebase):
    prevdyn = t.getdyn(x, y)
    if prevdyn & 0xFF00 == 0x1A00:
        # dirt overlap
        if pos == 11:  # center tile
            if prevdyn & 0xFF <= 0x0F:
                tileID = tilebase + 0x04
            else:
                tileID = tilebase + 0x14
        else:
            dirttype, overlapindex = obj4E_dirtindex[prevdyn & 0xFF]
            newpos = obj4E_dirtredirect[pos][dirttype]
            if newpos is None:
                tileID = 0x1104E  # in-game overflow: error tile
            else:
                tileID = tilebase + obj4Etilelow[newpos][overlapindex]
    elif t.getTile(x, y) in (0, 0x00C2):
        # overlap index 0 (non-dynamic)
        tileID = tilebase + obj4Etilelow[pos][0]
    elif overlapindex := obj4E_nondirtindex.get(prevdyn):
        # dynamic non-dirt overlap
        tileID = tilebase + obj4Etilelow[pos][overlapindex]
    else:
        # don't replace other tiles
        tileID = -1
    t.setTile(tileID, x, y)

obj4Erectindex = (7, 10, 13, 8, 11, 14, 9, 12, 15)
def obj4E(t, x0, y0, width, height):
    tilebase = t.dyn[0x1A00]
    if width > 0:
        if height > 0:
            indexgen = gen_rectindex(width, height)
            for y, x in itertools.product(t.yrange(y0, height),
                                          t.xrange(x0, width)):
                pos = obj4Erectindex[next(indexgen)]
                obj4Etile(t, x, y, pos, tilebase)
        else:
            for x, pos in zip(t.yrange(x0, width),
                            genseq_bordered(width+1, 4, 5, 6)):
                obj4Etile(t, x, y0, pos, tilebase)
    elif height > 0:
        for y, pos in zip(t.yrange(y0, height),
                        genseq_bordered(height+1, 1, 2, 3)):
            obj4Etile(t, x0, y, pos, tilebase)
    else:
        # alternate logic for 1x1
        prevdyn = t.getdyn(x0, y0)
        if t.getTile(x0, y0) in (0, 0x00C2) or prevdyn & 0xFF00 == 0x1A00:
            tileID = tilebase + obj4Etilelow[0][0]
        elif overlapindex := obj4E_nondirtindex.get(prevdyn):
            # dynamic non-dirt overlap
            tileID = tilebase + obj4Etilelow[0][overlapindex]
        else:
            tileID = -1
        t.setTile(tileID, x0, y0)

def obj4Fadjacent(t, x, y, subtableoffset: int, tilebase: int):
    prevtile = t.getTile(x, y)
    if prevtile & 0xFF00 == tilebase:
        t.setTile(obj4Freplacetiles[(prevtile & 0xFF) + subtableoffset], x, y,
                  priority=False, highlight=False)
def obj4F(t, x0, y0, width, height):
    tilebase = t.dyn[0x1A00]
    for x, y in itertools.product(t.xrange(x0, width), t.yrange(y0, height)):
        prevtile = t.getTile(x, y)
        tileID = obj4Freplacetiles[(prevtile & 0xFF) + 0x2FC]
        if tileID is None:
            tileID = 0x1104F  # in-game overflow: error tile
        t.setTile(tileID, x, y, highlight=prevtile)
        obj4Fadjacent(t, x, y-1, 0, tilebase)
        obj4Fadjacent(t, x, y+1, 0xBF, tilebase)
        obj4Fadjacent(t, x+1, y, 0x17E, tilebase)
        obj4Fadjacent(t, x-1, y, 0x23D, tilebase)

#### Objects 50-52: Train tracks

def obj50(t, x, y0, _, height):
    for y in t.yrange(y0, height):
        if t.getdyn(x, y) in (0x2A00,0x2A01,0x6805):
            t.setTile(0xD1F01, x, y)
        else:
            t.setTile(0xD1F00, x, y)
def obj51(t, x0, y, width, _):
    for x in t.xrange(x0, width):
        if t.getdyn(x, y) in (0x2A00,0x2A01,0x6805):
            t.setTile(0xD1F01, x, y)
        else:
            t.setTile(0xD2400, x, y)

def obj52(t, x0, y0, width, height):
    tiles = (0xD2300,0xD2200) if width >= 0 else (0xD2000,0xD2100)
    for x in t.xrange(x0, width):
        t.column_iter(gen_iter_default(tiles, -1), x, y0, height)
        height -= 1
        if height < 0:
            break
        y0 += 1

#### Objects 53-56: Castle BG ledges

obj53defaulttiles = (0x00D1,0x150D,0x00D2)
obj53replacetiles = (0x151B,0x151B,0x0000,0x151A)
def obj53(t, x0, y, width, _):
    parityX = 0
    for x, i in zip(t.xrange(x0, width), genseq_bordered(width+1)):
        prevtile = t.getTile(x, y)
        if not (0x00C2 <= prevtile <= 0x00C7):
            tileID = -1
        elif i >= 1 and prevtile >= 0x00C4:
            tileID = obj53replacetiles[prevtile-0x00C4]
        else:
            tileID = obj53defaulttiles[i]
            if i == 1:
                tileID += parityX
        t.setTile(tileID, x, y)
        parityX ^= 1

def obj5456edge(t, x, ygen, edgetype, negwidth: bool):
    edgetype = bool(edgetype)  # 0 if left edge, 1 if right edge
    # first row
    y = next(ygen)
    prevtile = t.getTile(x, y)
    if prevtile in (0x00D1,0x00D2):
        # 150D/150E based on prevtile and left/right edge
        tileID = 0x150D + ((prevtile == 0x00D2) ^ edgetype)
    elif prevtile == 0x00C5:
        tileID = 0x151B
    elif t.dyn[0x0200] <= prevtile < t.dyn[0x1200] or prevtile in (0x150D,0x150E):
        tileID = -1
    else:
        tileID = 0x00D1 + (edgetype ^ negwidth)
    t.setTile(tileID, x, y)
    for y in ygen:  # do nothing after first row
        t.setTile(-1, x, y)

obj5456data = {
    0x54: {"columns": (((0xD0F00,0xD1300),(0xD1000,0xD1100)),
                       ((0xD0D00,0xD1200),(0xD0C00,0xD0E00))),
                       # indexed by (width<0), then X parity, then relY
           "slope": -1, "parityX": True},
    0x55: {"tiles": ((0xD0A00,0xD0B00),(0xD0800,0xD0900)),
           "slope": -1, "parityX": False},
    0x56: {"tiles": ((0xD0500,0xD0600,0xD0700),(0xD0200,0xD0300,0xD0400)),
           "slope": -2, "parityX": False},
    }
def obj5456(t, x0, y0, width, height):
    data = obj5456data[t.obj.ID]
    adjheight = t.obj.adjheight
    if data["parityX"]:
        colgen = itertools.cycle(data["columns"][t.obj.width < 0])
    else:
        colgen = itertools.repeat(data["tiles"][t.obj.width < 0])
    parityX = 0

    for x, i in zip(t.xrange(x0, width), genseq_bordered(abs(width)+1)):
        if i != 1:
            obj5456edge(t, x, t.yrange_adj(y0, adjheight), i, t.obj.width < 0)
        else:
            if adjheight > 0:
                # positive height: normal behavior
                for y, tileID in zip(t.yrange_adj(y0, adjheight),
                                     gen_iter_default(next(colgen), -1)):
                    t.setTile(tileID, x, y)
            else:
                # negative height due to slope -2 (obj 56): glitched behavior
                ygen = t.yrange_adj(y0, adjheight)
                t.setTile(next(colgen)[0], x, next(ygen))
                for y in ygen:
                    t.setTile(-1, x, y)

            # adjust for slope, only if not an edge
            if parityX == 0:  # for obj54, only adjust slope if even X
                y0 -= data["slope"]
                adjheight += data["slope"]
                if adjheight == 0:
                    return

        if data["parityX"]:
            parityX ^= 1

#### Objects 57-62: Regular land, BG wall and ceiling variants

def obj57(t, x0, y, width, _):
    xlist = list(t.xrange(x0, width))

    # first tile
    t.setTile(0xD3F03 if t.getdyn(xlist[0], y) == 0x190C else 0xD3F00,
              xlist[0], y)
    if width != 0:
        # mid tiles
        for x in xlist[1:-1]:
            t.setTile(0xD3F01, x, y)
        # last tile
        t.setTile(0xD3F04 if t.getdyn(xlist[-1], y) == 0x190D else 0xD3F02,
                  xlist[-1], y)

def obj58side(t, x, ylist, side: int):
    # side: 1:left edge/right wall if extended,
    #       0:right edge/left wall if extended

    y1dyn = t.getdyn(x, ylist[0]+1)
    if y1dyn in (0x392B, 0x392C) or 0x390E <= y1dyn <= 0x391B:
        # generate left/right wall
        t.setTile(0xD3931 + side, x, ylist[0])  # interior corner

        if side == 1:
            sidecheck = (0x007D,0x007E,t.dyn[0x2A00],0x0142)
            side_x = x + 1
            alttile = 0xD392A
        else:
            sidecheck = (0x007D,0x007F,t.dyn[0x2A00],t.dyn[0x2A01])
            side_x = x - 1
            alttile = 0xD3929
        for y in ylist[1:]:  # extend with land wall tiles
            setlandwalltile(t, x, y, side)
            if t.getTile(side_x, y) in sidecheck:
                t.setTile(alttile, x, y)
        # move resize handle to end of wall
        t.obj.lastY = ylist[-1]

    else:
        # misc overlap checks for ceiling corner
        prevdyn = t.getdyn(x, ylist[0])
        if 0x392F <= prevdyn <= 0x3934:
            tileID = 0xD3930
        elif prevdyn == 0x1924:
            tileID = -1
        elif prevdyn == 0x190B:
            tileID = 0xD1924
        elif side == 1:
            tileID = 0xD392F  # left default: bottom-left corner
        else:
            tileID = 0xD3934  # right default: bottom-right corner
        t.setTile(tileID, x, ylist[0])

        for y in ylist[1:]:  # ignore object height
            t.setTile(-1, x, y)

obj58ceilingreplace = {
    0x1901:0xD1924, 0x1903:0xD1924, 0x1904:0xD1923, 0x1907:0xD1925,
    0x190B:0xD1924, 0x1910:0xD1923, 0x1911:0xD1925, 0x191D:0xD1924, 0x1924:-1,
    0x1928:0xD1925, 0x192A:0xD1923, 0x192B:0xD1925, 0x192D:0xD1926}

def obj58(t, x0, y0, width, height):
    xlist = list(t.xrange(x0, width))
    ylist = list(t.yrange(y0, height))
    # default downward resize handle, if neither end generates a wall
    t.obj.lastY = ylist[0]

    # left column
    obj58side(t, xlist[0], ylist, 1)
    if width != 0:
        # central ceiling
        for x in xlist[1:-1]:
            # top row
            t.lookup_replace(obj58ceilingreplace, x, ylist[0], 0xD3930,
                             dynamic=True)
            # remaining rows: do nothing but enable screen
            for y in ylist[1:]:
                t.setTile(-1, x, y)
        # right column
        obj58side(t, xlist[-1], ylist, 0)

obj595Edata = {
    #index with (0,4 for 59,5C + inverted X parity *2 + relY)
    0x59: {"columns": ((0xD4400, 0xD3910), (0xD4500, 0xD3911)),
           "heightoffset": 1, "slope": -1, "parityX": True, "rightstart": 1},
    0x5A: {"tiles": (0xD5000, 0xD3910),
           "heightoffset": 1, "slope": -1, "parityX": False, "rightstart": 1},
    0x5B: {"tiles": (0xD4B00, 0xD4C00, 0xD3910),
           "heightoffset": 1, "slope": -2, "parityX": False, "rightstart": 2},
    0x5C: {"columns": ((0xD4000, 0xD3910), (0xD4100, 0xD3911)),
           "heightoffset": 0, "slope": +1, "parityX": True, "rightstart": 0},
    0x5D: {"tiles": (0xD4E00, 0xD3911),
           "heightoffset": 0, "slope": +1, "parityX": False, "rightstart": 0},
    0x5E: {"tiles": (0xD4800, 0xD4900, 0xD3911),
           "heightoffset": 0, "slope": +2, "parityX": False, "rightstart": 0},
    }
obj5962sideoffsets = {"left": 0x2E, "right": 0}
def obj5962sidereplace(t, x, ygen: Iterable[int], side: str):
    offset = obj5962sideoffsets[side]
    for y in ygen:
        prevdyn = t.getdyn(x, y)
        if prevdyn >> 8 == 0x19:
            tileID = landBGwall_replace19_LR[(prevdyn & 0xFF) + offset]
        else:
            tileID = -1
        t.setTile(tileID, x, y, highlight=False)
def obj595E(t, x0, y0, width, height):
    data = obj595Edata[t.obj.ID]
    if data["parityX"]:
        colgen = itertools.cycle(data["columns"])
    else:
        colgen = itertools.repeat(data["tiles"])
    xlist = list(t.xrange(x0-1, width+2))
    y0 -= data["heightoffset"]
    adjheight = t.obj.adjheight
    adjheight += data["heightoffset"]

    # left column
    obj5962sidereplace(t, xlist[0], t.yrange_adj(y0, adjheight), "left")

    if data["slope"] > 0:  # only adjust for slope for 5C-5E
        y0 -= data["slope"]
        adjheight += data["slope"]
        if adjheight == 0: return

    # center columns
    parityX = 1
    for x in xlist[1:-1]:
        ygen = t.yrange_adj(y0, adjheight)
        tiles = next(colgen)
        if adjheight < 0:  # 5B can reach glitched negative heights
            tiles = tiles[0:1]
        for tileID, y in zip(tiles, ygen):
            if t.getdyn(x, y) in (0x3931, 0x3932):
                tileID = -1
            t.setTile(tileID, x, y)
        for y in ygen:
            t.setTile(random.choice(landinterior_randtile), x, y)

        # adjust for slope, except if second-to-last column
        if x != xlist[-2] and (parityX == 0 or not data["parityX"]):
            # for obj59/5C, only adjust slope if odd X
            y0 -= data["slope"]
            adjheight += data["slope"]
            if adjheight == 0: return
        parityX ^= 1

    # right column
    ylist = list(t.yrange_adj(y0, adjheight))
    obj5962sidereplace(t, xlist[-1], ylist[data["rightstart"]:], "right")

obj5F62tiles = {
    # indexed by obj ID -> tileset (else/8) -> parityX -> inverted relY
    0x5F: {0: ((-1,0xD5700), (0xD5900,0xD3911)),
           8: ((-1,0x5703), (0x5903,0xD3911))},
    0x60: {0: [(-1,0xD5D00)],
           8: [(-1,0x5D04)]},
    0x61: {0: ((0xD5300,0xD3910), (0xD191E,0xD5500)),
           8: ((0x5303,0xD3910), (-1,0x5503))},
    0x62: {0: [(0xD191E,0xD5B00)],
           8: [(-1,0x5B05)]},
    }

def obj5F60(t, x0, y0, width, height):
    if t.obj.ID == 0x5F:
        altadjheight = t.obj.adjwidth >> 1
    else:
        altadjheight = t.obj.adjwidth
    if altadjheight >= t.obj.adjheight:
        height = t.obj._unadjlength(altadjheight)
    colgen = itertools.cycle(obj5F62tiles[t.obj.ID][8 if t.tileset == 8 else 0])
    height += 1
    xlist = list(t.xrange(x0-1, width+2))

    # left column
    ylist = list(t.yrange(y0, height))
    if height != 0:
        obj5962sidereplace(t, xlist[0], ylist[0:-1], "left")
    t.setTile(-1, xlist[0], ylist[-1])

    # center columns
    parityX = 1
    rightcolumn = True
    for x, tiles in zip(xlist[1:-1], colgen):
        # adjust height and width, irregularly
        if t.obj.ID == 0x60 and x != xlist[1]:
            height -= 1
        ylist = list(t.yrange(y0, height))
        if x == xlist[-2] and height <= 1:
            # the game sometimes adjusts index for the last center column
            if height == 0 and width == 0:
                tiles = [tiles[1]]
            elif height == 1 and width != 0 and t.obj.ID == 0x5F:
                tiles = [-1, tiles[0]]
            rightcolumn = False  # the game also decrements width if so
        elif t.obj.ID == 0x5F and parityX == 0 and height > 1:
            height -= 1
            t.setTile(random.choice(landinterior_randtile), x, y0)
            ylist = list(t.yrange(y0+1, height-1))

        # before last 2 rows: land interior
        for y in ylist[:-2]:
            t.setTile(random.choice(landinterior_randtile), x, y)
        # last 2 rows: sloped surface
        for y, tileID in zip(reversed(ylist[-2:]), tiles):
            t.setTile(tileID, x, y)

        parityX ^= 1

    if rightcolumn:
        # right column
        if t.obj.ID == 0x60:
            height -= 1
        ylist = list(t.yrange(y0, height))
        tileID = -1
        if height != 0:
            obj5962sidereplace(t, xlist[-1], ylist[0:-1], "right")
            if t.getdyn(xlist[-1], ylist[-1]) == 0x1912:
                tileID = 0xD191F
        t.setTile(tileID, xlist[-1], ylist[-1], highlight=False)

obj6162_D191E = {0x1912:0xD191E, 0x190D:0xD1927, 0x1911:0xD1928}
def obj6162(t, x0, y0, width, height):
    width += 2
    height += 2
    if t.obj.ID == 0x61:
        height -= (width+1) // 2
    else:
        height -= width+1
    if height < 0: height = 0
    colgen = itertools.cycle(obj5F62tiles[t.obj.ID][8 if t.tileset == 8 else 0])
    xlist = list(t.xrange(x0-1, width))

    # left column
    ylist = list(t.yrange(y0, height))
    if height != 0:
        obj5962sidereplace(t, xlist[0], ylist[0:-1], "left")
    t.setTile(-1, xlist[0], ylist[-1])

    # center columns
    parityX = 1
    for x, tiles in zip(xlist[1:-1], colgen):
        if parityX == 0 or t.obj.ID == 0x62:  # adjust for slope
            height += 1

        ylist = list(t.yrange(y0, height))

        # before last 2 rows: land interior
        for y in ylist[:-2]:
            t.setTile(random.choice(landinterior_randtile), x, y)
        # last 2 rows: sloped surface
        for y, tileID in zip(reversed(ylist[-2:]), tiles):
            if tileID == 0xD191E:  # special casing for 19/1D/701E
                t.lookup_replace(obj6162_D191E, x, y, default=-1, dynamic=True)
            else:
                t.setTile(tileID, x, y)

        parityX ^= 1

    # right column
    height += 1
    ylist = list(t.yrange(y0, height))
    tileID = -1
    if height != 0:
        obj5962sidereplace(t, xlist[-1], ylist[0:-2], "right")
        if t.getdyn(xlist[-1], ylist[-2]) == 0x1912:
            tileID = 0xD191F
    t.setTile(tileID, xlist[-1], ylist[-2], highlight=False)
    t.setTile(-1, xlist[-1], ylist[-1], highlight=False)

#### Object 63-6C: Misc global/multi-tileset objects

def obj63(t, x0, y, width, _):
    t.row_iter(genseq_bordered(width+1, 0x151E, 0x151F, 0x1520), x0, y)

def obj66(t, x0, y0, width, height):
    # ice block is not objYX becaues it doesn't enforce even lengths
    tileID = 0x8900
    for y in t.yrange(y0, height):
        for x in t.xrange(x0, width):
            t.setTile(tileID, x, y)
            tileID ^= 1
        tileID &= 0xFFFE
        tileID ^= 2

def obj67replace19(t, x, y, data, offset):
    prevdyn = t.getdyn(x, y)
    if prevdyn >> 8 == 0x19:
        t.setTile(data[(prevdyn & 0xFF) + offset],
                  x, y, priority=False, highlight=False)
def obj67(t, x0, y0, width, height):
    if t.tileset == 0xC:
        for y, x in itertools.product(t.yrange(y0, height), t.xrange(x0, width)):
            offset = random.randrange(0x40)
            if offset <= 0xA:
                tileID = 0x79BB + offset
            else:
                tileID = 0x79E0
            t.setTile(tileID, x, y)
    else:
        # generate rectangle of dirt tiles
        xlist = list(t.xrange(x0, width))
        ylist = list(t.yrange(y0, height))
        for x, y in itertools.product(xlist, ylist):
            t.setTile(random.choice(landinterior_randtile), x, y)

        # modify BG walls in each direction
        x_left = xlist[0] - 1
        x_right = xlist[-1] + 1
        y_above = ylist[0] - 1
        y_below = ylist[-1] + 1
        for y in ylist:
            # left edge
            obj67replace19(t, x_left, y, landBGwall_replace19_LR, 0x2E)
            # right edge
            obj67replace19(t, x_right, y, landBGwall_replace19_LR, 0)
        for x in xlist:
            # top edge
            obj67replace19(t, x, y_above, obj67replace19data, 0x5C)
            # bottom edge
            obj67replace19(t, x, y_below, obj67replace19data, 0x8A)
        # top-left corner
        obj67replace19(t, x_left, y_above, obj67replace19data, 0)
        # top-right corner
        obj67replace19(t, x_right, y_above, obj67replace19data, 0x2E)
        # bottom-left corner
        obj67replace19(t, x_left, y_below, obj67replace19data, 0xB8)
        # bottom-right corner
        obj67replace19(t, x_right, y_below, obj67replace19data, 0xE6)

obj69tiles = (0x6100,0x6101,0x6102,0x0185,0x0186,0x0187,0x6103,0x6104,0x6105)
def obj69(t, x0, y0, width, height):
    t.rect_iter_row((obj69tiles[i] for i in gen_rectindex(width, height)),
                    x0, y0, width, height)

def obj6A(t, x0, y, width, _):
    t.row_iter(genseq_bordered(width+1, 0x6400, 0x6401, 0x6402), x0, y)

def obj6B(t, x0, y0, width, height):
    # top-left corner land overlap checks
    if t.getdyn(x0-1, y0-1) in (0x2A00,0x2A01):
        t.setTile(0xD3B01, x0, t.y_offset(y0, -1), priority=False, highlight=False)
    if t.getdyn(x0-1, y0) in (0x3912,0x3913,0x3920,0x392A):
        first = 0xD3935
    else:
        first = 0x0188  # default top-left corner tile
    
    # main goal platform
    ygen = t.yrange(y0, height)
    t.row_iter(genseq_bordered(width+1, first, 0x0189, 0x018A), x0, next(ygen))
    for y in ygen:
        t.row_iter(genseq_bordered(width+1, 0x018B, 0x018C, 0x018D), x0, y)

def obj6C(t, x0, y0, width, height):
    xlist = list(t.xrange(x0, width))
    ylist = list(t.yrange(y0, height))
    for x, y in itertools.product(xlist, ylist):
        t.setTile(0x0184, x, y)
    # add shadows to adjacent castle BG walls
    obj486C_addshadows(t, xlist, ylist)

def obj6D(t, x, y0, _, height):
    t.column_iter(genseq_bordered(height+1, 0xD6C00, 0xD6B01, 0xD6B02), x, y0)

def obj6Egen() -> Iterator[int]:
    while True: yield random.randrange(0x0199, 0x01A1)
def obj6E(t, x0, y0, width, height):
    t.rect_iter_column(obj6Egen(), x0, y0, width, height)

#### Objects 6F-78: Forest trees

def obj6F(t, x, y0, _, height):
    for relY, y in enumerate(t.yrange(y0, height)):
        if relY == height and t.getdyn(x, y) in (0x2A00,0x2A01):
            t.setTile(0x3D4B, x, y)
        else:
            t.setTile(random.randrange(0x3D3B, 0x3D3D), x, y)

obj7376data = {
    0x73: (2, (0x3D42,0x3D43,0x3D44,0x3D50,0x3D51,0x3D52)),
    0x74: (2, (0x3D53,0x3D54,0x3D55)),
    0x75: (1, (0x3D53,0x3D57)),
    0x76: (1, (0x3D56,0x3D55)),
    }
def obj7376(t, x0, y0, _, height):
    width, tiles = obj7376data[t.obj.ID]
    t.rect_iter_row(itertools.cycle(tiles), x0, y0, width, height)

obj7879tiles = {0x78: ((0x3D3E,0x3D3D), (0x3D3F,0x3D40)),
                0x79: ((0x3D5A,0x6700), (0x3D59,0x6600))}
def obj7879(t, x0, y0, width, _):
    tiles = obj7879tiles[t.obj.ID][0 if width >= 0 else 1]
    ygen = t.yrange(y0, abs(width))
    xlist = list(t.xrange(x0, width))

    # first column: single tile
    y = next(ygen)
    t.setTile(tiles[1], x0, y)
    # remaning columns: slope downward
    for x in xlist[1:]:
        t.setTile(tiles[0], x, y)
        y = next(ygen)
        t.setTile(tiles[1] if x != xlist[-1] else -1, x, y)

#### Objects 7A-80,85-86: Land BG wall related

def obj7Atopleft(t, x, y, _) -> int:
    if t.getdyn(x, y) in (0x6803,0x6811): return 0xD680A
    if t.getdyn(x, y+1) == 0x6809: return -1
    return 0xD6812
def obj7Atopright(t, x, y, _) -> int:
    if t.getdyn(x, y) in (0x6800,0x6810): return 0xD6809
    if t.getdyn(x, y+1) == 0x680A: return -1
    return 0xD6812
def obj7Acenterleft(t, x, y, parityX) -> int:
    match t.getdyn(x, y):
        case 0x6801 | 0x6802 | 0x6803 | 0x6811: return 0xD6801 + parityX
        case 0x6809 | 0x680A | 0x680D: return -1
        case 0x6812: return 0xD6809
        case _: return 0xD6800
def obj7Acenter(t, x, y, parityX) -> int:
    return 0xD6801 + parityX
def obj7Acenterright(t, x, y, parityX):
    match t.getdyn(x, y):
        case 0x6801 | 0x6802 | 0x6800 | 0x6810: return 0xD6801 + parityX
        case 0x6809 | 0x680A | 0x680E: return -1
        case 0x6812: return 0xD680A
        case _: return 0xD6811 if parityX else 0xD6803
def obj7Abottomleft(t, x, y, parityX) -> int:
    match t.getdyn(x, y):
        case 0x6805 | 0x6806 | 0x6807:
            return obj7Abottomcenter(t, x, y, parityX)
        case 0x6803 | 0x6811: return 0xD680E
        case 0x680C: return -1
        case _: return 0xD6804
def obj7Abottomcenter(t, x, y, parityX) -> int:
    if t.getTile(x, y) != 0: return 0xD6805 + parityX
    return 0xD6813
def obj7Abottomright(t, x, y, parityX) -> int:
    match t.getdyn(x, y):
        case 0x6804 | 0x6805 | 0x6806:
            return obj7Abottomcenter(t, x, y, parityX)
        case 0x6800 | 0x6810: return 0xD680D
        case 0x680F: return -1
        case _: return 0xD6807

obj7Afunc = [obj7Atopleft, lambda *_ : 0xD6812, obj7Atopright,
             obj7Acenterleft, obj7Acenter, obj7Acenterright,
             obj7Abottomleft, obj7Abottomcenter, obj7Abottomright]

def obj7A(t, x0, y0, width, height):
    indexgen = gen_rectindex(width, height)
    xlist = list(t.xrange(x0, width))
    for y in t.yrange(y0, height):
        parityX = 0
        for x in xlist:
            t.setTile(obj7Afunc[next(indexgen)](t, x, y, parityX), x, y)
            parityX ^= 1

obj7Btiles = (
    {0: 0xD680B, 1: 0xD680A, "firstX": 0xD6803, "lastX": 0xD6811,
     "surface": 0x6807},  # positive width
    {0: 0xD6808, 1: 0xD6809, "firstX": 0xD6800, "lastX": 0xD6810,
     "surface": 0xD6804})  # negative width
def obj7B_Y1(t, x, y, tiles: dict, lastX: bool) -> int:
    prevdyn = t.getdyn(x, y)
    tileID = tiles[1]  # default tile
    if lastX:
        if prevdyn == 0x6812:
            return tileID
        else:
            tileID = tiles["lastX"]  # default tile for last X
    if prevdyn in (0x2A00, 0x2A01, 0x6804, 0x6807):
        return tiles["surface"]
    elif prevdyn in (0x6801, 0x6802, 0x6809, 0x680A):
        return -1
    return tileID
def obj7B(t, x0, y0, width, height):
    xlist = list(t.xrange(x0, width))
    tiles = obj7Btiles[0 if width >= 0 else 1]
    parityX = 0
    for x in xlist:
        ylist = list(t.yrange(y0, height))
        lastX = (x == xlist[-1])
        # row 0
        prevdyn = t.getdyn(x, ylist[0])
        if prevdyn >> 8 == 0x68 and prevdyn != 0x6812:
            tileID = -1
        else:
            tileID = tiles[0]
        t.setTile(tileID, x, ylist[0])

        if height != 0:
            # row 1
            t.setTile(obj7B_Y1(t, x, ylist[1], tiles, lastX), x, ylist[1])

        if height > 1:
            # rows 2+
            for y in ylist[2:-1]:
                tileID = 0xD6801 + parityX
                if lastX:
                    match t.getdyn(x, y):
                        case 0x6800|0x6801|0x6802|0x6803|0x6810|0x6811:
                            pass
                        case 0x6809 | 0x680A:
                            tileID = -1
                        case 0x6812:
                            tileID = tiles[1]
                        case _:
                            tileID = tiles["lastX" if parityX == 1 else "firstX"]
                t.setTile(tileID, x, y)

            # last row
            tileID = 0xD6801 + parityX
            prevdyn = t.getdyn(x, ylist[-1])
            if prevdyn in (0x2A00,0x2A01,0x6804,0x6805,0x6806,0x6807):
                tileID = 0xD6805 + parityX
            if lastX:
                if prevdyn in (0x2A00, 0x2A01):
                    tileID = tiles["surface"]
                elif prevdyn >> 8 != 0x68:
                    tileID = tiles["lastX"]
            t.setTile(tileID, x, ylist[-1])

        # adjust for slope and parity
        y0 += 1
        height -= 1
        if height < 0:
            return
        parityX ^= 1

obj7Cslopetiles = ((0xD680F, 0xD680E),  # positive width
                   (0xD680C, 0xD680D))  # negative width
def obj7C(t, x0, y0, width, _):
    height = abs(width)
    slopetiles = obj7Cslopetiles[0 if width >= 0 else 1]
    parityX = 0
    for x in t.xrange(x0, width):
        ylist = list(t.yrange(y0, height))
        if height > 0:
            # most rows
            parity = parityX
            for y in ylist[0:-2]:
                t.setTile(0xD6801 + parity, x, y)
                parity ^= 1
            # second-to-last row
            t.setTile(slopetiles[1], x, ylist[-2])
        # last row
        prevdyn = t.getdyn(x, ylist[-1])
        if prevdyn >> 8 != 0x68 or prevdyn in (0x6804, 0x6807):
            tileID = slopetiles[0]
        else:
            tileID = -1
        t.setTile(tileID, x, ylist[-1])

        height -= 1
        parityX ^= 1

obj7Dtiles = {
    "default":       ((0xD6A00,0xD6A01,0xD6A02,0xD6A03),
                      (0xD3803,0xD3805,0xD3806,0xD3808)),
    "edgeoverlap":   ((0xD6A04,0xD6A04,0xD6A05,0xD6A05),
                      (0xD3804,0xD3805,0xD3806,0xD3807)),
    "insideoverlap": ((0xD6A06,0xD6A07,0xD6A08,0xD6A09),
                      (0xD3803,0xD3805,0xD3806,0xD3808))}
def obj7D(t, x0, y0, width, _):
    for x, i in zip(t.xrange(x0, width),
                    genseq_bordered_cycle(width+1, 0, (1, 2), 3)):
        for relY, y in enumerate(t.yrange(y0, 1)):
            match t.getdyn(x, y):
                case 0x6801 | 0x6802:
                    key = "insideoverlap"
                case 0x6800 | 0x6810 | 0x6803 | 0x6811:
                    key = "edgeoverlap"
                case _:
                    key = "default"
            t.setTile(obj7Dtiles[key][relY][i], x, y)

def obj7E(t, x0, y, width, _):
    t.row_iter(genseq_bordered(width+1, 0xD3809, 0xD380A, 0xD380B), x0, y)

obj7F_68subindexlookup = (0, 3, 6, 1, 4, 7, 2, 5, 8)
obj7Freplacecarved = (0xD680E,0xD6813,0xD680D,
                      0xD6811,0x0000,0xD6810,
                      0xD680A,0xD6812,0xD6809)
obj7Freplacecarvededge = (0xD680C,0xD6813,0xD680F,
                          0x0000,0x0000,0x0000,
                          0xD6808,0xD6812,0xD680B)
def obj7F(t, x0, y0, width, height):
    if width == 0: width = 1
    if height == 0: height = 1
    for (y, x), i in zip(itertools.product(t.yrange(y0, height),
                                           t.xrange(x0, width)),
                         gen_rectindex(width, height)):
        prevdyn = t.getdyn(x, y)
        tileID = -1  # default: don't change tile
        if prevdyn >> 8 == 0x68:
            tileID = obj7Freplace68[0x14 * obj7F_68subindexlookup[i]
                                    + (prevdyn & 0xFF)]
            if tileID is None:
                # in-game dynamic RAM table overflow: use red error tile
                tileID = 0x1107F
        elif prevdyn in (0x1916, 0x1917):
            tileID = obj7Freplacecarvededge[i]
        elif prevdyn >> 8 == 0x19:
            tileID = obj7Freplacecarved[i]
        t.setTile(tileID, x, y)

def obj80(t, x0, y0, width, _):
    height = abs(width)
    secondlast = 0xD680E if width >= 0 else 0xD680D
    threshold = 1 if width >= 0 else 0
    for relX, x in enumerate(t.xrange(x0, width)):
        ylist = list(t.yrange(y0, height))
        for y in ylist:
            t.setTile(0xD6801 + relX if relX <= threshold else 0x11080, x, y)
        if height > 0:
            t.setTile(secondlast, x, ylist[-2])
        height -= 1
        if height < 0:
            return

obj85tiles = (0xA201, 0xA101)
def obj85(t, x0, y0, width, height):
    # modify BG walls to left
    for y in t.yrange(y0, height):
        obj67replace19(t, x0-1, y, landBGwall_replace19_LR, 0x2E)

    xlist = list(t.xrange(x0, width))
    for x in t.xrange(x0, width):
        ylist = list(t.yrange(y0, height))

        # before last 2 rows: land interior
        for y in ylist[:-2]:
            t.setTile(random.choice(landinterior_randtile), x, y)
        # last 2 rows: sloped surface
        for y, tileID in zip(reversed(ylist[-2:]), obj85tiles):
            t.setTile(tileID, x, y)
            # 85 runs this check on last 2 Y values
            if t.getdyn(x, y+1) == 0x1912:
                t.setTile(0xD3B0E, x, y+1, priority=False, highlight=False)
            if t.getdyn(x-1, y+1) == 0x1912:
                t.setTile(0xD3B0D, x-1, y+1, priority=False, highlight=False)

        # adjust for slope, except final column
        if x != xlist[-1]:
            height -= 2
            if height < 0: height = 0

    # modify BG walls to right
    if height >= 2:
        for y in t.yrange(y0, height-2):
            obj67replace19(t, x+1, y, landBGwall_replace19_LR, 0)

obj86tiles = (0xA001, 0x9F01)
def obj86(t, x0, y0, width, height):
    height = max(height-width-1, 0)

    # modify BG walls to left
    if height >= 2:
        for y in t.yrange(y0, height-2):
            obj67replace19(t, x0-1, y, landBGwall_replace19_LR, 0x2E)

    xlist = list(t.xrange(x0, width))
    for x in t.xrange(x0, width):
        ylist = list(t.yrange(y0, height))

        # before last 2 rows: land interior
        for y in ylist[:-2]:
            t.setTile(random.choice(landinterior_randtile), x, y)
        # last 2 rows: sloped surface
        for y, tileID in zip(reversed(ylist[-2:]), obj86tiles):
            t.setTile(tileID, x, y)

        # 86 runs this check only if last Y
        y_below = ylist[-1] + 1
        if t.getdyn(x+1, y_below) == 0x1912:
            t.setTile(0xD3B0E, x+1, y_below, priority=False, highlight=False)
        if t.getdyn(x, y_below) == 0x1912:
            t.setTile(0xD3B0D, x, y_below, priority=False, highlight=False)

        # adjust for slope, except final column
        if x != xlist[-1]:
            height += 2

    # modify BG walls to right
    for y in t.yrange(y0, height):
        obj67replace19(t, x+1, y, landBGwall_replace19_LR, 0)

####

obj8788edgereplace = {"left": (0xD3B01, 0x0145), "right": (0xD3B00, 0x0150)}
obj8788randsurface = {0x87: range(0x0146,0x014A), 0x88: range(0x014E,0x0150)}
obj8788surfacecheck = (0x2A00, 0x2A01, 0x3912, 0x3913)
def obj8788(t, x0, y0, width, height):
    ylist = list(t.yrange(y0, height))
    surfacetiles = obj8788randsurface[t.obj.ID]

    for x, pos in zip(t.xrange(x0, width),
                      genseq_bordered(width+1, "left", "center", "right")):
        # row 0: just some overlap checks
        prevtile = t.getdyn(x, ylist[0])
        if pos != "center" and prevtile in obj8788surfacecheck:
            tileID = obj8788edgereplace[pos][0]
        elif prevtile in (0x2A00, 0x2A01):
            tileID = 0
        else:
            tileID = -1
        t.setTile(tileID, x, ylist[0], highlight=False)

        # row 1
        if pos != "center" and t.getdyn(x, ylist[1]) in obj8788surfacecheck:
            tileID = obj8788edgereplace[pos][1]
        else:
            tileID = random.choice(surfacetiles)
        t.setTile(tileID, x, ylist[1])

        # remaining rows
        for y in ylist[2:]:
            setlandinterior_shared(t, x, y, ylist[-1])

####

def obj89(t, x0, y0, width, height):
    if width != 0:
        adjwidth = width+1
        if height != 0:
            # rectangle: nested bordered sequences
            rowgen = genseq_bordered_cycle(height+1,
                genseq_bordered(adjwidth, 0x7200, 0x7201, 0x7202), (
                    list(genseq_bordered(adjwidth, 0x7203, 0x7204, 0x7205)),
                    list(genseq_bordered(adjwidth, 0x7210, 0x7211, 0x7212)),
                    ),
                genseq_bordered(adjwidth, 0x7206, 0x7207, 0x7208),
                )
            for y in t.yrange(y0, height):
                t.row_iter(next(rowgen), x0, y)
        else:
            # single row
            t.row_iter(genseq_bordered(adjwidth, 0x7209, 0x720A, 0x720B),
                x0, y0)
    elif height != 0:
        # single column
        t.column_iter(genseq_bordered_cycle(
            height+1, 0x720C, (0x720E,0x7213), 0x720F), x0, y0)
    else:
        # single tile
        t.setTile(0x720D, x0, y0)

def obj8C(t, x0, y0, width, _):
    offset = 0
    ylist = list(t.yrange(y0, 1))
    y2 = t.y_offset(y0, 2)
    for x in t.xrange(x0, width):
        # rows 0-1
        for y in ylist:
            if not 0x00B6 <= t.getTile(x, y) <= 0x00BA:
                t.setTile(0x016F + offset, x, y)
            offset ^= 2
        offset ^= 1
        # row 2
        match t.getTile(x, y2):
            case 0x00C3:
                if x == x0: tileID = -1
                else: tileID = 0x00C6
            case 0x00C2 | 0x00C7: tileID = 0x00C6
            case 0x00C5: tileID = 0x00D5
            case _: tileID = -1
        t.setTile(tileID, x, y2, highlight=False)

def obj8D(t, x, y0, _, height):
    ylist = list(t.yrange(y0, height))
    for y in ylist[:-1]:
        t.setTile(random.choice((0x3D70,0x3DA7)), x, y)
    t.setTile(0x3D6F, x, ylist[-1])

#### Objects 8F-93: Forest logs and more trees

obj8Ftiles = (
    # positive width
    {"firstX": (0xD0806,0x3DBF), "firstXoverlap": (0x3DBF,0x3DDB),
     1: {"default": (0xD0F02,0x3DC0), "surface": (0xD0F03,0x3DDC)},
     0: {"default": (0xD1003,0x3DC1,0x3DBF), "surface": (0xD1004,0x3DDD,0x3DDB)},
     },
    # negative width
    {"firstX": (0xD0A06,0x3DBE), "firstXoverlap": (0x3DBE,0x3DDA),
     1: {"default": (0xD0D01,0x3DBD), "surface": (0xD0D02,0x3DD9)},
     0: {"default": (0xD0C01,0x3DBC,0x3DBE), "surface": (0xD0C04,0x3DD8,0x3DDA)},
     },
    )
def obj8Fcolumn(t, x, ygen: Iterable[int], tiles: dict, maxrelY: int):
    for relY, y in enumerate(ygen):
        tileID = -1
        if relY <= maxrelY:
            prevdyn = t.getdyn(x, y)                    
            if t.getTile(x, y) == 0 or prevdyn in (0x0805, 0x0A01):
                tileID = tiles["default"][relY]
            elif prevdyn in (0x2A00, 0x2A01):
                tileID = tiles["surface"][relY]
        t.setTile(tileID, x, y)
def obj8F(t, x0, y0, width, height):
    tiles = obj8Ftiles[0 if width >= 0 else 1]
    xgen = t.xrange(x0, width)

    # first column
    x = next(xgen)
    for relY, y in enumerate(t.yrange(y0, height)):
        tileID = -1
        if relY <= 1:
            if t.getTile(x, y) == 0 or t.getdyn(x, y) in (0x0805, 0x0A01):
                tileID = tiles["firstX"][relY]
            else:
                tileID = tiles["firstXoverlap"][relY]
        t.setTile(tileID, x, y)

    # remaining columns
    parityX = 1
    for x in xgen:
        obj8Fcolumn(t, x, t.yrange(y0, height), tiles[parityX], 2 - parityX)
        if parityX == 0:  # adjust for slope if even X
            y0 += 1
            height -= 1
            if height < 0: return
        parityX ^= 1

obj90tiles = (
    # positive width
    ({"empty": (0xD0805,0x3DB1), "surface": (0x3DB1,0x3DB6)},
     {"empty": (0xD0A04,0x3DBB,0x3DBA), "surface": (0xD0A05,0x3DB7,0x3DB6)}),
    # negative width
    ({"empty": (0xD0A01,0x3DB0), "surface": (0x3DB0,0x3DB5)},
     {"empty": (0xD0802,0x3DB8,0x3DB9), "surface": (0xD0801,0x3DB4,0x3DB5)}),
    )
def obj90column(t, x, ygen: Iterable[int], tiles: dict, maxrelY: int):
    for relY, y in enumerate(ygen):
        tileID = -1
        if relY <= maxrelY:
            if t.getTile(x, y) == 0:
                tileID = tiles["empty"][relY]
            elif t.getdyn(x, y) in (0x2A00, 0x2A01):
                tileID = tiles["surface"][relY]
        t.setTile(tileID, x, y)
def obj90(t, x0, y0, width, height):
    tilelookup = obj90tiles[0 if width >= 0 else 1]
    xgen = t.xrange(x0, width)

    # first column
    obj90column(t, next(xgen), t.yrange(y0, height), tilelookup[0], 1)
    # remaining columns
    for x in xgen:
        obj90column(t, x, t.yrange(y0, height), tilelookup[1], 2)
        # adjust for slope
        y0 += 1
        height -= 1
        if height < 0: return

obj9192data = {
    0x91: ((0x3DC2,0x3DC3,0x3DC4), (0x3DC8,0x3DC9,0x3DCA), (-1,0x3DB2,-1),
          {0x0802:0xD0804, 0x0C01:0xD0C03}, None),
    0x92: ((0x3DC5,0x3DC6,0x3DC7), (0x3DCB,0x3DAE,0x3DAF), (-1,0x3DB3,-1),
           {0x0A04:0xD0A02, 0x1003:0x1001}, 0x3DAD)}
def obj9192(t, x, y0, _, height):
    data = obj9192data[t.obj.ID]
    xlist = list(t.xrange(x-1, 2))
    ylist = list(t.yrange(y0, height))

    # treetop
    for y, row in zip(ylist, data[0:2]):
        for x, tileID in zip(xlist, row):
            t.setTile(tileID, x, y)
    if height >= 2:
        # tree trunk
        row = data[2]
        for y in ylist[2:-1]:
            for x, tileID in zip(xlist, row):
                t.setTile(tileID, x, y)
        # base of trunk
        t.setTile(-1, xlist[0], ylist[-1])
        t.setTile(-1, xlist[2], ylist[-1])
        defaulttile = data[4]
        if defaulttile is None:
            defaulttile = 0x3DAC if t.fixver > 0 else 0x11091
        t.lookup_replace(data[3], xlist[1], ylist[-1], defaulttile, dynamic=True)

obj93rows = ((0x3DCE,0x3DCF,0x3DD0,  -1  ),  # row 0 (tree top)
             (0x3DD1,0x3DD2,0x3DD3,0x3DD4),  # row 1 (tree top)
             (  -1,  0x3DD5,  -1,    -1  ),  # other rows (trunk)
             (  -1,  0x3DD6,0x3DD7,  -1  ))  # last row, if height>1 (base)
def obj93(t, x0, y0, _, height):
    ylist = list(t.yrange(y0, height))
    for relX, x in enumerate(t.xrange(x0-1, 3)):
        # row 0-1
        for relY, y in enumerate(ylist[0:2]):
            t.setTile(obj93rows[relY][relX], x, y)
        if height > 1:
            # other rows
            for y in ylist[2:-1]:
                t.setTile(obj93rows[2][relX], x, y)
            # last row
            t.setTile(obj93rows[3][relX], x, ylist[-1])

#### Objects 98-9C: Cave (tileset 0) decorations

def obj98(t, x0, y0, width, height):
    ygen = t.yrange(y0, height)
    # row 0
    t.row_iter(itertools.cycle((0xA7750,0xA7754)), x0, next(ygen), width)
    if height > 0:
        # row 1
        if width != 0:
            t.row_iter(genseq_bordered_cycle(
                width+1, 0x7800, (0x7801,0x7802), 0x7803), x0, next(ygen))
        else:
            t.setTile(0x7804, x0, next(ygen))
    if height > 1:
        # row 2+: alternate between tiles based on Y^X parity
        tilegen = itertools.cycle((0x01B7,0x01B8))
        for y in ygen:
            t.row_iter(tilegen, x0, y, width)
            if width & 1: next(tilegen)  # waste a tile to toggle parity                

obj99top = ((0x01B9,0x01BA,0x01BB), (0x01BC,0x01BD,0x01BE))
def obj99(t, x0, y0, _, height):
    xlist = list(t.xrange(x0-1, 2))
    ylist = list(t.yrange(y0, height))

    for row, y in zip(obj99top, ylist[0:2]):
        for tileID, x in zip(row, xlist):
            t.setTile(tileID, x, y)
    for y in ylist[2:]:
        t.setTile(-1, xlist[0], y)
        setlandinterior_shared(t, xlist[1], y, ylist[-1])
        t.setTile(-1, xlist[2], y)

obj9Atop = (  # first set for raw height even (adjheight odd)
              # second set for raw height odd (adjheight even)
    (  -1  ,0x7701,0x7702,0x7703,0x7710,0x7711,0x7712,0x7713),
    (0x7730,0x7731,0x7732,  -1  ,0x7740,0x7741,0x7742,0x7743))
obj9B9Crandtop = {  # first set for raw height even (adjheight odd)
                    # second set for raw height odd (adjheight even)
    0x9B: (((0x7751,), (0x7757,), (0x775A,), (0x775D,)),
           ((0x7722,), (0x7724,), (0x7728,), (0x772C,))),
    0x9C: (((0x7720,0x7721), (0x7725,0x7726), (0x7729,0x772A), (0x772D,0x772E)),
           ((0x7753,0x7752), (0x7756,0x7755), (0x7759,0x7758), (0x775C,0x775B))),
    }
obj9A9Crandmid = (  # first tile for adjheight^Y parity 0, second for parity 1
                    # 9B-9C invert the index
    (0x7733,0x7700), (0x7737,0x7704), (0x773B,0x7708), (0x773F,0x770C))
obj9A9Crandlast = range(0x7723, 0x7730, 4)

def obj9A(t, x0, y0, _, height):
    randindex = random.randrange(4)
    ylist = list(t.yrange(y0, height))
    xlist = list(t.xrange(x0-2, 3))
    stemX = xlist[2 if (height & 1 == 0) else 1]

    # row 0-1
    top_iter = iter(obj9Atop[height & 1])
    for y, x in itertools.product(ylist[0:2], xlist):
        tileID = next(top_iter)
        if tileID != -1:
            tileID += randindex*4
        t.setTile(tileID, x, y)
    if height >= 2:
        # central rows
        midtiles = obj9A9Crandmid[randindex]
        parityY = height & 1 ^ 1  # swap parity if raw height even (adjheight odd)
        for y in ylist[2:-1]:
            for x in xlist:
                t.setTile(midtiles[parityY] if x == stemX else -1, x, y)
            parityY ^= 1
        # last row
        t.setTile(obj9A9Crandlast[randindex], stemX, ylist[-1])

def obj9B9C(t, x, y0, _, height):
    randindex = random.randrange(4)
    ygen = t.yrange(y0, height)
    toptiles = obj9B9Crandtop[t.obj.ID][height & 1][randindex]
    parityY = height & 1 ^ 1  # swap parity if raw height even (adjheight odd)

    # row 0 (9B) or 0-1 (9C)
    for tileID, y in zip(toptiles, ygen):
        t.setTile(tileID, x, y)
        parityY ^= 1
    if height >= len(toptiles):
        # central rows
        midtiles = obj9A9Crandmid[randindex^3]
        for y in ygen:
            t.setTile(midtiles[parityY], x, y)
            parityY ^= 1
        # last row (reuses last y from ygen)
        t.setTile(obj9A9Crandlast[randindex^3], x, y)

####

def obj9D(t, x0, y0, width, height):
    ygen = t.yrange(y0, height)
    # first row
    t.row_iter(genseq_bordered(width+1, 0x7900, 0x7901, 0x7902), 
        x0, next(ygen))
    # central rows
    midrows = (
        list(genseq_bordered(width+1, 0x7903, 0x7904, 0x7905)),
        list(genseq_bordered(width+1, 0x7906, 0x7907, 0x7908)),
        )
    for i in range(height-1):
        t.row_iter(midrows[i&1], x0, next(ygen), width)
    # last row
    y = next(ygen)
    tilegen = genseq_bordered(width+1, 0x7909, 0x790A, 0x790B)
    for x in t.xrange(x0, width):
        tile = next(tilegen)
        if t.getdyn(x, y) in (0x2A00,0x2A01):
            tile += 6
        t.setTile(tile, x, y)

obj9Fcolumns = ((0x3308, 0x0004),(0x3508, 0x0005),(-1,-1),(-1,-1))
def obj9F(t, x0, y0, width, _):
    if width & 1 == 0:  # force even width (odd internal width)
        width += 1
    tilegen = itertools.cycle(obj9Fcolumns)
    for x in t.xrange(x0, width):
        t.column_iter(next(tilegen), x, y0)

#### Objects A0-A2: Breakout blocks

def objA0A2(t, x0, y0, width, height):
    if width & 1 == 0:  # force even width (odd internal width)
        width += 1
    tileID = 0x78C0 + 2*t.obj.ID  # 7A00 + (objID-A0)*2
    for x in t.xrange(x0, width):
        t.column_single(tileID, x, y0, height)
        tileID ^= 1

#### Objects A5-A6: Double-ended pipes

objA5castledata = (
    # tile IDs, only fills empty tiles
    ((0x7D02,0x7D03), True),
    (((0x01C7,0x01C8), False),
     ((0x01C9,0x01CA), False)),
    ((0x7D06,0x7D07), True),
    )
def objA5_t3gen(height) -> Iterator[int]:
    yield 0x905A
    if height == 0: return
    if height > 1:
        for _ in range(height - 2):
            yield 0x9050
        yield 0x7D1C
    yield 0x3D29
def objA5(t, x0, y0, _, height):
    if t.tileset == 3:
        x1 = t.x_offset(x0, 1)
        for y, tileID in zip(t.yrange(y0, height), objA5_t3gen(height)):
            t.setTile(tileID, x0, y)
            t.setTile(tileID + 1, x1, y)
    else:
        datagen = genseq_bordered_cycle(height+1, *objA5castledata)
        xlist = list(t.xrange(x0, 1))
        for y in t.yrange(y0, height):
            tiles, emptyrequired = next(datagen)
            for x, tileID in zip(xlist, tiles):
                if emptyrequired and t.getTile(x, y) not in (0, 0x1600):
                    tileID = -1
                t.setTile(tileID, x, y)

objA6t3columns = (
    (0x3D2B,0x7D1E,0x7D1F,0x9056),
    ((0x3D2C,0x9052,0x9054,0x9057),
     (0x3D2D,0x9053,0x9055,0x9058)),
    (0x3D2E,0x7D20,0x7D21,0x9059))
objA6castledata = (
    # tile IDs, only fills empty tiles
    ((0x7D00,0x7D01), True),
    (((0x01C3,0x01C6), False),
     ((0x01C4,0x01C5), False)),
    ((0x7D04,0x7D05), True),
    )
def objA6(t, x0, y0, width, _):
    if t.tileset == 3:
        columngen = genseq_bordered_cycle(width+1, *objA6t3columns)
        for x in t.xrange(x0, width):
            t.column_iter(next(columngen), x, y0)
    else:
        datagen = genseq_bordered_cycle(width+1, *objA6castledata)
        ylist = list(t.yrange(y0, 1))
        for x in t.xrange(x0, width):
            tiles, emptyrequired = next(datagen)
            for y, tileID in zip(ylist, tiles):
                if emptyrequired and t.getTile(x, y) not in (0, 0x1600):
                    tileID = -1
                t.setTile(tileID, x, y)

#### Objects A7-A8: Blue thorns

def objA7thornedge(t, oldtile: int, newtile: int) -> int:
    if oldtile == 0:
        return newtile
    elif 0x777D <= oldtile <= 0x778B:
        # bitwise OR old edge with new edge
        return (oldtile-0x777C | newtile-0x777C) + 0x777C
    else:
        return -1
def objA7(t, x0, y0, width, height):
    xlist = list(t.xrange(x0-1, width+2))
    ylist = list(t.yrange(y0-1, height+2))

    # central thorn tile
    t.rect_single(0x7C00, x0, y0, width, height)
    for x in xlist[1:-1]:
        # top edge
        t.setTile(objA7thornedge(t, t.getTile(x, ylist[0]), 0x7780),
                  x, ylist[0], highlight=False)
        # bottom edge
        t.setTile(objA7thornedge(t, t.getTile(x, ylist[-1]), 0x7784),
                  x, ylist[-1], highlight=False)
    for y in ylist[1:-1]:
        # left edge
        t.setTile(objA7thornedge(t, t.getTile(xlist[0], y), 0x777E),
                  xlist[0], y, highlight=False)
        # right edge
        t.setTile(objA7thornedge(t, t.getTile(xlist[-1], y), 0x777D),
                  xlist[-1], y, highlight=False)
    # enable screens of unused corners
    t.setTile(-1, xlist[0], ylist[0])
    t.setTile(-1, xlist[-1], ylist[0])
    t.setTile(-1, xlist[0], ylist[-1])
    t.setTile(-1, xlist[-0], ylist[-1])

def objA8removethornedge(t, oldtile: int, newtile: int) -> int:
    if 0x777D <= oldtile <= 0x778B:
        newbits = oldtile-0x777C &~ (newtile-0x777C)
        if newbits != 0:  # thorn edges remaining
            return newbits + 0x777C
        else:  # clear tile
            return 0
    else:
        return -1
def objA8(t, x0, y0, width, height):
    xlist = list(t.xrange(x0-1, width+2))
    ylist = list(t.yrange(y0-1, height+2))

    # remove central tiles
    for x, y in itertools.product(t.xrange(x0, width), t.yrange(y0, height)):
        # detect adjacent thorns
        thornbits = 0
        if t.getTile(x, y-1) == 0x7C00: thornbits |= 8
        if y == ylist[-2] and t.getTile(x, y+1) == 0x7C00: thornbits |= 4
        if t.getTile(x-1, y) == 0x7C00: thornbits |= 1
        if x == xlist[-2] and t.getTile(x+1, y) == 0x7C00: thornbits |= 2
        if thornbits:
            t.setTile(0x777C + thornbits, x, y)
        else:
            # filler tile to ensure object is visible, acts as tile 0
            t.setTile(MultiTileID(0, 0x100A8), x, y)
    # remove thorn edges
    for x in xlist[1:-1]:
        # top edge
        t.setTile(objA8removethornedge(t, t.getTile(x, ylist[0]), 0x7780),
                  x, ylist[0], highlight=False)
        # bottom edge
        t.setTile(objA8removethornedge(t, t.getTile(x, ylist[-1]), 0x7784),
                  x, ylist[-1], highlight=False)
    for y in ylist[1:-1]:
        # left edge
        t.setTile(objA8removethornedge(t, t.getTile(xlist[0], y), 0x777E),
                  xlist[0], y, highlight=False)
        # right edge
        t.setTile(objA8removethornedge(t, t.getTile(xlist[-1], y), 0x777D),
                  xlist[-1], y, highlight=False)
    # enable screens of unused corners
    t.setTile(-1, xlist[0], ylist[0])
    t.setTile(-1, xlist[-1], ylist[0])
    t.setTile(-1, xlist[0], ylist[-1])
    t.setTile(-1, xlist[-0], ylist[-1])

#### Object A9

objA9pipe_top = (0x3D2F,0x7D22,0x0110,0x0112)
objA9pipe_mid = (0x3D31,0x3D16,0x3D33)
objA9pipe_bottom = (0x3D35,0x7D22,0x0110)
def objA9gen(height) -> Iterator[int]:
    # first 4 rows
    yield from objA9pipe_top[0:height]
    # cycle through 3 middle tiles
    tilegen = itertools.cycle(objA9pipe_mid)
    for _ in range(height-7):
        yield next(tilegen)
    # last 3 rows
    if height > 4:
        yield from objA9pipe_bottom[4-height:]
def objA9(t, x0, y0, _, height):
    if t.tileset == 3:
        # 2.5D floor connector pipe
        x1 = t.x_offset(x0, 1)
        ylist = list(t.yrange(y0, height))
        for y, tileID in zip(ylist, objA9gen(height+1)):
            t.setTile(tileID, x0, y)
            t.setTile(tileID+1, x1, y)
    else:
        # Chomp signpost
        landsurface = (t.dyn[0x2A00], t.dyn[0x2A01])
        for y in t.yrange(y0, height):
            prevtile = t.getTile(x0, y)
            if prevtile == 0:
                tileID = 0x0083
            elif prevtile in landsurface:
                tileID = t.dyn[0x2A0E]
            else:
                tileID = -1
            t.setTile(tileID, x0, y)            

#### Objects AA-C3: Sewer tileset pipes

objAAABtiles = {0xAA: (0x790F,0x7799, 0x791F,0x779A),  # alternating rows
                0xAB: (0x779F,0x7910, 0x77A0,0x7920)}
objACADtiles = {0xAC: (0x7915,0x77A9, 0x7916,0x77AA),  # alternating columns
                0xAD: (0x77AF,0x7925, 0x77B0,0x7926)}
objAAABoverlapindexes = {
    0x7915: 0, 0x7916: 0,  # pipe ceiling
    0x7925: 3, 0x7926: 3,  # pipe floor
    0x77A9: 6, 0x77AA: 6,  # BG wall ceiling
    0x77AF: 9, 0x77B0: 9}  # BG wall floor
objACADoverlapindexes = {
    0x790F: 0, 0x791F: 0,  # pipe left
    0x7910: 3, 0x7920: 3,  # pipe right
    0x7799: 6, 0x779A: 6,  # BG wall left
    0x779F: 9, 0x77A0: 9}  # BG wall right
def objAAAD_coordindex(rel, length) -> int:
    if rel < 2:  # first 2 tiles
        return 0
    elif rel >= length - 1:  # last 2 tiles
        return 1
    else:
        return 2
objAAADoverlaptiles = {
    # Indexes:
    # outer tuple: relX (AA-AB) or relY (AC-AD)
    # inner tuple: overlapindex (0,3,6,9) + coordindex (first 2, last 2, else)
    0xAA: ((0x7931,0x792C,0x792C, 0x791C,0x7931,0x791C,  # original: pipe left
            0x792E,  -1,    -1,     -1,  0x791E,  -1  ),
           (0x792E, None,  None,   None, 0x791E, None,   # original: BGwall left
            0x5D09,0x77B9,0x77B9, 0x77BB,0x0A2F,0x77BB)),
    0xAB: ((0x792D, None,  None,   None, 0x791D, None,   # original: BGwall right
            0x5B0D,0x77CC,0x77CC, 0x77BA,0x082D,0x77BA),
           (0x7931,0x792B,0x792B, 0x791B,0x7931,0x791B,  # original: pipe right
            0x792D,  -1,    -1,     -1,  0x791D,  -1  )),
    0xAC: ((0x7931,0x792C,0x792C, 0x792B,0x7931,0x792B,  # original: pipe ceiling
            0x792E,  -1,    -1,     -1,  0x792D,  -1  ),
           (0x792E, None,  None,   None, 0x792D, None,   # original: BGwall ceiling
            0x5D09,0x77B9,0x77B9, 0x77CC,0x5B0D,0x77CC)),
    0xAD: ((0x791E, None,  None,   None, 0x791D, None,   # original: BGwall floor
            0x0A2F,0x77BB,0x77BB, 0x77BA,0x082D,0x77BA),
           (0x7931,0x791C,0x791C, 0x791B,0x7931,0x791B,  # original: pipe floor
            0x791E,  -1,    -1,     -1,  0x791D,  -1  )),
    }

def objAAAB(t, x0, y0, _, height):
    tilegen = itertools.cycle(objAAABtiles[t.obj.ID])
    overlaptiles_obj = objAAADoverlaptiles[t.obj.ID]
    for relY, y in enumerate(t.yrange(y0, height)):
        coordindex = objAAAD_coordindex(relY, height)
        for x, overlaptiles in zip(t.xrange(x0, 1), overlaptiles_obj):
            tileID = next(tilegen)
            overlapindex = objAAABoverlapindexes.get(t.getTile(x, y))
            if overlapindex is not None:
                newtileID = overlaptiles[coordindex + overlapindex]
                if newtileID is not None:
                    tileID = newtileID
            t.setTile(tileID, x, y)
def objACAD(t, x0, y0, width, _):
    tilegen = itertools.cycle(objACADtiles[t.obj.ID])
    overlaptiles_obj = objAAADoverlaptiles[t.obj.ID]
    for relX, x in enumerate(t.xrange(x0, width)):
        coordindex = objAAAD_coordindex(relX, width)
        for y, overlaptiles in zip(t.yrange(y0, 1), overlaptiles_obj):
            tileID = next(tilegen)
            overlapindex = objACADoverlapindexes.get(t.getTile(x, y))
            if overlapindex is not None:
                newtileID = overlaptiles[coordindex + overlapindex]
                if newtileID is not None:
                    tileID = newtileID
            t.setTile(tileID, x, y)
def objAC(t, x0, y0, width, _):
    if t.tileset == 0xB:  # in sewer tileset, AC/AD share code
        objACAD(t, x0, y0, width, _)
    else:  # unfinished unrelated object outside sewer tileset: runs ext46 code
        for x in t.xrange(x0, width):
            t.setTile(random.choice((0x5F00,0x5F01,0x5F03,0x5F03)), x, y0)

def objAE(t, x0, y0, _, height):
    x1 = t.x_offset(x0, 1)
    parity = 0
    for y in t.xrange(y0, height):
        t.setTile(0x779B + parity, x0, y)
        t.setTile(0x779D + parity, x1, y)
        parity ^= 1
def objAF(t, x0, y0, width, _):
    y1 = t.y_offset(y0, 1)
    parity = 0
    for x in t.xrange(x0, width):
        t.setTile(0x77AB + parity, x, y0)
        t.setTile(0x77AD + parity, x, y1)
        parity ^= 1

objB0tiles = (0x77AB, 0x77AC, 0x77AB, 0x77CE,
              0x779C, 0x77AE, 0x77AD, 0x77AD,
              0x779B, 0x779E, 0x779D, 0x779D,
              0x77CE, 0x779E, 0x779D, 0x779D)
def objB0(t, x0, y0, width, height):
    indexgen = gen_rectindex_parity2(width, height)
    for y, x in itertools.product(t.yrange(y0, height), t.xrange(x0, width)):
        tileID = objB0tiles[next(indexgen)]
        if t.getTile(x, y) == 0:
            t.setTile(tileID, x, y)

objB1general = (0x1513,0x1514,0x1515,0x1516,0,0,0,0)
objB1replace = {
    0x77B9:0x1519, 0x77BB:0x1519, 0x77C9:0x1519, 0x77CC:0x1519,
    0x8100:0x1517, 0x8101:0x1517, 0x8102:0x1517, 0x8103:0x1517,
    0x854B:0x151C, 0x854C:0x151D, 0x854D:0x151D, 0x854E:0x151D}
def objB1(t, x0, y, width, _):
    for x in t.xrange(x0, width):
        prevtile = t.getTile(x, y)
        if prevtile <= 0x77B8:
            tileID = objB1general[(prevtile - 9) >> 1 & 7]
        else:
            tileID = objB1replace.get(prevtile, -1)
        t.setTile(tileID, x, y)

objB2B9tiles = {
    0xB2: (0x792E,0x5D09,0x77B9),
    0xB3: (0x77BA,0x082D,0x791D),
    0xB4: (0x792E,0x5D09,0x77B9,0x77AB),
    0xB5: (0x77AE,0x77BA,0x082D,0x791D),
    0xB6: (0x792D,0x5B0C,0x77C9),
    0xB7: (0x77CA,0x0A2E,0x791E),
    0xB8: (0x792D,0x5B0C,0x77C9,0x77AC),
    0xB9: (0x77AD,0x77CA,0x0A2E,0x791E),
    }
def objB2B9(t, x0, y0, width, _):
    tiles = objB2B9tiles[t.obj.ID]
    for x in t.xrange(x0, width):
        for tileID, y in zip(tiles, t.yrange(y0, 4)):
            if t.getTile(x, y) == 0:
                if (tileID == 0x0A2E and t.getTile(x, y-1) in (0x7799,0x779A)) or\
                   (tileID == 0x5B0C and t.getTile(x, y+1) in (0x779F,0x77A0)):
                    # B6-B9 overlap checks with vertical pipes
                    tileID += 1
                t.setTile(tileID, x, y)
        y0 += 1

def objBA(t, x0, y, width, _):
    t.row_iter(genseq_bordered_cycle(
        width+1, 0x792F, (0x7916,0x7915), 0x7930), x0, y)
def objBB(t, x0, y, width, _):
    t.row_iter(genseq_bordered_cycle(
        width+1, 0x7932, (0x7926,0x7925), 0x7933), x0, y)
def objBC(t, x, y0, _, height):
    t.column_iter(genseq_bordered_cycle(
        height+1, 0x7930, (0x7920,0x7910), 0x7933), x, y0)
def objBD(t, x, y0, _, height):
    t.column_iter(genseq_bordered_cycle(
        height+1, 0x792F, (0x791F,0x790F), 0x7932), x, y0)

objBEBFreplace_floor2 = {
    0x7925:0x7805, 0x7926:0x7806, 0x7927:0x7807, 0x7928:0x7808,
    0x7929:0x7809, 0x792A:0x780A, 0x791B:0x780B, 0x791C:0x780C,
    0x082D:0x7F01, 0x082E:0x7F01, 0x0A2D:0x8001, 0x0A2E:0x8001,
    0x0A2F:0x8001, 0x0A30:0x8001,
    }
objBEBFreplace_floor1 = {
    0x7925:0x7805, 0x7926:0x7806, 0x7927:0x7807, 0x7928:0x7808,
    0x7929:0x7809, 0x792A:0x780A, 0x791B:0x780B, 0x791C:0x780C,
    0x7962:0x780D, 0x7963:0x780E, 0x7966:0x780F, 0x7968:0x7810,
    0x7969:0x7811, 0x796A:0x7812, 0x796D:0x7813, 0x796F:0x7814,
    0x7978:0x7815, 0x7979:0x7816, 0x797C:0x7817, 0x797D:0x7818,
    0x7936:0x1513, 0x7937:0x1514, 0x7939:0x1515, 0x793B:0x1516,
    }
objBEreplace_firstY = {
    0x7799:0x77CF, 0x779A:0x77CF, 0x779B:0x77CF, 0x779C:0x77CF,
    0x779D:0x77C8, 0x779E:0x77C8, 0x779F:0x77C8, 0x77A0:0x77C8,
    0x77A1:0x77CF, 0x77A2:0x77CF, 0x77A3:0x77C8, 0x77A4:0x77C8,
    0x77A5:0x77CF, 0x77A6:0x77CF, 0x77A7:0x77C8, 0x77A8:0x77C8,
    0x77A9:0x77CF, 0x77AA:0x77CF, 0x77AB:0x77CF, 0x77AC:0x77CF,
    0x77AD:0x77C8, 0x77AE:0x77C8, 0x77AF:0x77C8, 0x77B0:0x77C8,
    0x77B1:0x77CF, 0x77B2:0x77CF, 0x77B3:0x77C8, 0x77B4:0x77C8,
    0x77B5:0x77CF, 0x77B6:0x77CF, 0x77B7:0x77C8, 0x77B8:0x77C8,
    0x77B9:0x77CF, 0x77BA:0x77C8, 0x77BB:0x77CF, 0x77BE:0x77CF,
    0x77C9:0x77CF, 0x77CA:0x77C8, 0x77CC:0x77CF, 0x77CE:0x77CF,
    0x854B:0x854F, 0x854C:0x854F, 0x854D:0x854F, 0x854E:0x854F,
    }

def objBE(t, x, y0, _, height):
    ylist = list(t.yrange(y0, height))
    # first Y
    t.lookup_replace(objBEreplace_firstY, x, y0, -1)
    if height > 1:
        # mid Y
        for y in ylist[1:-2]:
            t.setTile(0x1517 if (0x1513 <= t.getTile(x, y) <= 0x1519)
                      else 0x8101, x, y) 
        # second-last Y
        y = ylist[-2]
        t.lookup_replace(objBEBFreplace_floor2, x, y, 0x8103)
    if height != 0:
        # last Y
        y = ylist[-1]
        t.lookup_replace(objBEBFreplace_floor1, x, y, -1)

objBF_Y1replace = {0x779F:0x8100, 0x77A0:0x8100, 0x1513:0x1517, 0x1516:0x1517}
def objBF(t, x, y0, _, height):
    ylist = list(t.yrange(y0, height))
    # first Y
    prevtile = t.getTile(x, y0)
    if prevtile == 0x77BA: tileID = 0x77BF
    elif prevtile >> 8 == 0x85: tileID = -1
    else: tileID = 0x77C0
    t.setTile(tileID, x, y0)
    if height != 0:
        # second Y
        t.lookup_replace(objBF_Y1replace, x, ylist[1], 0x8102)
    if height > 2:
        # mid Y
        for y in ylist[2:-2]:
            t.setTile(0x1517 if (0x1513 <= t.getTile(x, y) <= 0x1519)
                      else 0x8101, x, y) 
        # second-last Y
        t.setTile(
            0x8103 if t.getTile(x, ylist[-2]) in objBEBFreplace_floor1.keys()
            else 0x8101, x, ylist[-2])
    if height > 1:
        # last Y
        prevtile = t.getTile(x, ylist[-1])
        tileID = objBEBFreplace_floor2.get(prevtile)
        if tileID is None:
            tileID = objBEBFreplace_floor1.get(prevtile, 0x8101)
        t.setTile(tileID, x, ylist[-1])

objC0C1floorreplace = {
    # C0: directly used. C1: same values but +0x100
    0x7925:0x8200, 0x7926:0x8201, 0x7927:0x8202, 0x7928:0x8203,
    0x7929:0x8204, 0x792A:0x8205, 0x791B:0x8206, 0x791C:0x8207,
    0x7962:0x8208, 0x7963:0x8209, 0x7966:0x820A, 0x7968:0x820B,
    0x7969:0x820C, 0x796A:0x820D, 0x796D:0x820E, 0x796F:0x820F,
    0x7978:0x8210, 0x7979:0x8211, 0x797C:0x8212, 0x797D:0x8213,
    0x7936:0x8215, 0x7937:0x8215, 0x7939:0x8214, 0x793B:0x8214,
    }
objC0C1_BGwallreplace = {
    0xC0: {0x77AF:0x77C2, 0x77B0:0x77C3, 0x77B4:0x77D2, 0x77B8:0x77D3,
           0x77C6:0x77D6, 0x77C7:0x77D7,
           0x082D:0x082E, 0x0A2E:0x0A2D, 0x0A2F:0x0A30,
           0x854B:0x855A, 0x854C:0x855B, 0x854D:0x855C, 0x854E:0x855D},
    0xC1: {0x77AF:0x77C4, 0x77B0:0x77C5, 0x77B4:0x77D5, 0x77B8:0x77D4,
           0x77C6:0x77D6, 0x77C7:0x77D7, 
           0x082D:0x082E, 0x0A2E:0x0A2D, 0x0A2F:0x0A30,
           0x854B:0x855E, 0x854C:0x855F, 0x854D:0x8560, 0x854E:0x8561},
    }
objC0C1_Y0replace = {
    0xC0: (0x854A, 0x8550), 0xC1: (0x8546, 0x8551)}
objC0C1splashtiles = {
    # indexed by: objID -> detected 8101 on left,right
    #             -> (pipe wall tile ID, room wall offset to prevtile)
    0xC0: ((0x77EB, 0xB), (0x77D0, 0x1F)),
    0xC1: ((0x77D1, 0x23), (0x77D0, 0x7)),
    }
def objC0C1(t, x0, y0, width, _):
    BGwallreplace = objC0C1_BGwallreplace[t.obj.ID]
    Y0replace = objC0C1_Y0replace[t.obj.ID]
    flooroffset = 0x100 if t.obj.ID == 0xC1 else 0
    y1 = t.y_offset(y0, 1)

    for x in t.xrange(x0, width):
        # row 0: replace BG walls with currents
        prevtile = t.getTile(x, y0)
        if prevtile == Y0replace[0]:
            tileID = Y0replace[1]
        elif t.getTile(x + (-1 if x == x0 else +1), y0) == 0x8101:
            # runs if waterfall on left if x0, right otherwise
            splashtiles = objC0C1splashtiles[t.obj.ID][0 if x == x0 else 1]
            if 0x854B <= prevtile <= 0x854E:
                tileID = prevtile + splashtiles[1]  # room walls use an offset
            else:
                tileID = splashtiles[0]  # pipe walls use a single tile
        else:
            tileID = BGwallreplace.get(prevtile, -1)
        t.setTile(tileID, x, y0)

        # row 1: replace floors with variants that move Yoshi/sprites
        tileID = objC0C1floorreplace.get(t.getTile(x, y1), -1)
        if tileID != -1:
            tileID += flooroffset
        t.setTile(tileID, x, y1)

objC2C3tiles = {
    0xC2: (0x77BF, 0x7F00, (0x082D,0x082E)),
    0xC3: (0x77C0, 0x8000, range(0x0A2D,0x0A31))}
def objC2C3(t, x0, y0, width, _):
    tile0, tile1, checkrange = objC2C3tiles[t.obj.ID]
    ygen = t.yrange(y0, abs(width)+1)
    y = next(ygen)
    for x in t.xrange(x0, width):
        t.setTile(tile0, x, y)
        y = next(ygen)
        t.setTile(tile1 if t.getTile(x, y) in checkrange else -1, x, y)

#### Objects 83-84, C4-C9: Coin lines, every 2nd tile

obj8384C4C9tiles = {0x83: 0x6001, 0x84: 0x6001,
                    0xC4: 0x6000, 0xC5: 0x6000, 0xC6: 0x6000,
                    0xC7: 0x7400, 0xC8: 0x7400, 0xC9: 0x7400}
def obj83C4C7(t, x0, y, width, _):
    tilegen = itertools.cycle((obj8384C4C9tiles[t.obj.ID], -1))
    for x in t.xrange(x0, width):
        t.setTile(next(tilegen), x, y)
def objC5C8(t, x, y0, _, height):
    tilegen = itertools.cycle((obj8384C4C9tiles[t.obj.ID], -1))
    for y in t.yrange(y0, height):
        t.setTile(next(tilegen), x, y)
def obj84C6C9(t, x0, y0, width, _):
    tilegen = itertools.cycle((obj8384C4C9tiles[t.obj.ID], -1))
    for x, y in zip(t.xrange(x0, width), t.yrange(y0, abs(width))):
        t.setTile(next(tilegen), x, y)

#### Object CA: Sewer water

objCAcheckdark = (0x779B,0x779C,0x77AB,0x77AC,0x77B9,0x77BB,0x77BE)
objCAchecklight = (0x779D,0x779E,0x77AD,0x77AE,0x77BA)
def objCA_tileY0check(t, x, y) -> int:
    prevtile = t.getTile(x, y)
    if prevtile == 0x8101:
        return 0x8103
    elif t.getTile(x-1, y) == 0x8103:
        if prevtile in objCAcheckdark: return 0x77CB
        elif prevtile in objCAchecklight: return 0x77CD
    elif t.getTile(x+1, y) in (0x8101, 0x8103):
        if prevtile in objCAcheckdark: return 0x77BC
        elif prevtile in objCAchecklight: return 0x77BD
    return -1
def objCA(t, x0, y0, width, height):
    xlist = list(t.xrange(x0, width))
    ygen = t.yrange(y0, height)
    # row 0
    y = next(ygen)
    for x in xlist:
        t.setTile(objCA_tileY0check(t, x, y), x, y, highlight=False)
    if height != 0:
        # row 1
        y = next(ygen)
        for x in xlist:
            t.setTile(0x161F, x, y)
        # remaining rows
        for y in ygen:
            for x in xlist:
                t.setTile(0x1620, x, y)

#### Objects CE-D0: Diagonal line-guides

def objCE(t, x0, y0, width, _):
    tileID = 0x8701 if width >= 0 else 0x8700
    for x, y in zip(t.xrange(x0, width), t.yrange(y0, abs(width))):
        t.setTile(tileID, x, y)

objCFD0data = {0xCF: (0x8702, 2), 0xD0: (0x8706, 4)}
def objCFD0(t, x0, y0, width, _):
    tileID, period = objCFD0data[t.obj.ID]
    if width >= 0:
        tileID += period
    ygen = t.yrange(y0, abs(width)//period + 1)
    offset = 0
    y = next(ygen)
    for x in t.xrange(x0, width):
        t.setTile(tileID + offset, x, y)
        offset += 1
        if offset == period:
            offset = 0
            y = next(ygen)  # shift down every 2 or 4 tiles

#### Objects D3-D7: Sewer rooms

def objD3(t, x0, y0, width, height):
    parity = 0
    for y in t.yrange(y0, height):
        for x in t.xrange(x0, width):
            t.setTile(0x854B + (parity ^ (x & 3)), x, y)
        parity ^= 2

sewerroom_replace = {
    0xD4: {
        0x7915:0x7938, 0x7916:0x7938, 0x77A9:0x8543, 0x77AA:0x8543,
        0x77AB:0x8544, 0x77AC:0x8544, 0x77AD:0x8545, 0x77AE:0x8545,
        0x77AF:0x8546, 0x77B0:0x8546, 0x7925:0x7939, 0x7926:0x7939},
    0xD5: {
        0x7915:0x793A, 0x7916:0x793A, 0x77A9:0x8547, 0x77AA:0x8547,
        0x77AB:0x8548, 0x77AC:0x8548, 0x77AD:0x8549, 0x77AE:0x8549,
        0x77AF:0x854A, 0x77B0:0x854A, 0x7925:0x793B, 0x7926:0x793B},
    0xD6: {
        0x790F:0x7934, 0x791F:0x7934, 0x7799:0x853B, 0x779A:0x853B,
        0x779B:0x853C, 0x779C:0x853C, 0x779D:0x853D, 0x779E:0x853D,
        0x779F:0x853E, 0x77A0:0x853E, 0x7910:0x7935, 0x7920:0x7935,
        0x77CE:0x853C},
    0xD7: {
        0x790F:0x7936, 0x791F:0x7936, 0x7799:0x853F, 0x779A:0x853F,
        0x779B:0x8540, 0x779C:0x8540, 0x779D:0x8541, 0x779E:0x8541,
        0x779F:0x8542, 0x77A0:0x8542, 0x7910:0x7937, 0x7920:0x7937,
        0x77CE:0x8540},
    }
sewerroom_random = {
    0xD4: (
        (0x7941,None), (0x7947,None), (0x7941,None), (0x7947,None),
        (0x7940,0x793F), (0x7946,0x7945), (0x793C,0x7931), (0x7943,0x7942)),
    0xD5: (
        (0x794D,None), (0x7953,None), (0x794D,None), (0x7953,None),
        (0x794B,0x794C), (0x7951,0x7952), (0x794E,0x7931), (0x7948,0x7949)),
    0xD6: (
        (0x795A,None), (0x7961,None), (0x795A,None), (0x7961,None),
        (0x7959,0x7958), (0x7960,0x795F), (0x7956,0x7954), (0x795D,0x795B)),
    0xD7: (
        (0x7968,None), (0x796F,None), (0x7968,None), (0x796F,None),
        (0x7966,0x7967), (0x796D,0x796E), (0x7962,0x7964), (0x7969,0x796B)),
    }
sewerroom_finish2x2 = {
    0xD4: ((0x793E,0x793D), (0x7944,None)),
    0xD5: ((0x794F,0x7950), (0x794A,None)),
    0xD6: ((0x7957,0x7955), (0x795E,0x795C)),
    0xD7: ((0x7963,0x7965), (0x796A,0x796C)),
    }
sewerroom_corner = {
    0xD4: (0x7982,0x7980,0x7981, 0x7987,0x7986,0x7988),
    0xD5: (0x7984,0x7983,0x7985, 0x7989,0x798A,0x798B),
    0xD6: (0x7982,0x7981,0x7980, 0x7984,0x7983,0x7985),
    0xD7: (0x7987,0x7986,0x7988, 0x7989,0x798B,0x798A),
    }

def objD4D5(t, x0, y0, _, height):
    x_side = t.x_offset(x0, -1 if t.obj.ID == 0xD4 else +1)
    ylist = list(t.yrange(y0, height))
    cornertiles = sewerroom_corner[t.obj.ID]
    randomtiles = sewerroom_random[t.obj.ID]
    replacetiles = sewerroom_replace[t.obj.ID]
    finish2x2tiles = sewerroom_finish2x2[t.obj.ID]

    # top corner
    t.setTile(cornertiles[0], x0, y0)
    t.setTile(cornertiles[1], x0, y0 - 1, priority=False)
    t.setTile(cornertiles[2], x_side, y0, priority=False)
    if height != 0:
        # middle
        index = -1
        for y in ylist[1:-1]:
            tileID = replacetiles.get(t.getTile(x0, y))
            if tileID is None:
                if t.fixver > 0:
                    # unused due to vanilla bugs
                    if index >= 6:  # previous index generated a 2x2 block
                        tileID, tile_side = finish2x2tiles[index-6]
                        index = -1
                    else:
                        index = random.randrange(8)
                        if index >= 6 and y == ylist[-2]:
                            # don't start a 2x2 block in the last row before the corner
                            index -= 4
                        tileID, tile_side = randomtiles[index]
                else:
                    tileID, tile_side = randomtiles[random.randrange(8)]
                if tile_side is not None:
                    t.setTile(tile_side, x_side, y, priority=False)
            t.setTile(tileID, x0, y)
        # bottom corner
        t.setTile(cornertiles[3], x0, ylist[-1])
        t.setTile(cornertiles[4], x_side, ylist[-1], priority=False)
        t.setTile(cornertiles[5], x0, ylist[-1] + 1, priority=False)

def objD6D7(t, x0, y0, width, _):
    y_side = (y0 + (-1 if t.obj.ID == 0xD6 else +1)) & 0x7F
    xlist = list(t.xrange(x0, width))
    cornertiles = sewerroom_corner[t.obj.ID]
    randomtiles = sewerroom_random[t.obj.ID]
    replacetiles = sewerroom_replace[t.obj.ID]
    finish2x2tiles = sewerroom_finish2x2[t.obj.ID]

    # left corner
    t.setTile(cornertiles[0], x0, y0)
    t.setTile(cornertiles[1], (x0 - 1) & 0xFF, y0, priority=False)
    t.setTile(cornertiles[2], x0, y_side, priority=False)
    if width != 0:
        # middle
        index = -1
        for x in xlist[1:-1]:
            tileID = replacetiles.get(t.getTile(x, y0))
            if tileID is None:
                if index >= 6:  # previous index generated a 2x2 block
                    tileID, tile_side = finish2x2tiles[index-6]
                    index = -1
                else:
                    index = random.randrange(8)
                    if index >= 6 and x == xlist[-2]:
                        # don't start a 2x2 block in the last column before the corner
                        index -= 4
                    tileID, tile_side = randomtiles[index]
                if tile_side is not None:
                    t.setTile(tile_side, x, y_side, priority=False)
            t.setTile(tileID, x, y0)
        # right corner
        t.setTile(cornertiles[3], xlist[-1], y0)
        t.setTile(cornertiles[4], xlist[-1], y_side, priority=False)
        t.setTile(cornertiles[5], (xlist[-1] + 1) & 0xFF, y0, priority=False)

####

objD8tiles = (0xA84BA,0x330C,0x84BC,0x84BE,
              0xA84BB,0x3510,0x84BD,0x84BF)
def objD8(t, x0, y0, width, _):
    t.rect_iter_column(itertools.cycle(objD8tiles), x0, y0, width, 3)

objD9tiles = (0xA84C0, 0x8600, 0xA84C1)
def objD9(t, x0, y0, width, _):
    t.rect_iter_column(itertools.cycle(objD9tiles), x0, y0, width, 2)

#### Objects DB-DC,E3: Snow tileset ice

objDBsurface = (-1,-1,0xA0017,0xA0018)
objDBcolumns = ((0x8C01,0x8C05,0x8C09), (0x8C02,0x8C06,0x8C0A))
def objDB(t, x0, y0, width, height):
    ylist = list(t.yrange(y0, height))
    parity = 0
    for x in t.xrange(x0, width):
        # row 0
        if t.getTile(x, y0) == 0:
            t.setTile(random.choice(objDBsurface), x, y0)
        # remaining rows
        tilegen = iter(objDBcolumns[parity])
        for y in ylist[1:]:
            t.setTile(next(tilegen, 0x8C0D), x, y)  # default to 8C0D
        parity ^= 1

objDCcolumns = (  # start of column, default
     ((0x8C03,0x8C07,0x8C0B), 0x8C0E),  # left
    (((0x0000,0x0016,0x1622,0x1624), 0x1625),  # center, X odd
     ((0x0000,0x0015,0x1621,0x1623), 0x1625)),  # center, X even
     ((0x8C00,0x8C04,0x8C08), 0x8C0C))  # right
def objDC(t, x0, y0, width, height):
    columngen = genseq_bordered_cycle(width+1, *objDCcolumns)
    xlist = list(t.xrange(x0, width))
    # first X
    t.column_iter(gen_iter_default(*next(columngen)), x0, y0, height)
    if width != 0:
        # middle X: alternating water tiles
        for x in xlist[1:-1]:
            t.setTile(0, x, y0-1, priority=False)
            t.column_iter(gen_iter_default(*next(columngen)), x, y0, height)
        # last X
        t.column_iter(gen_iter_default(*next(columngen)),
                      xlist[-1], y0, height)

def objE3(t, x0, y0, width, height):
    xlist = list(t.xrange(x0, width))
    ylist = list(t.yrange(y0, height))
    # first X
    t.column_iter(gen_iter_default((0x8C03,0x8C07), 0x8C0E), x0, y0, height)
    if width != 0:
        # clear middle
        for x in xlist[1:-1]:
            t.setTile(0, x, y0-1, priority=False)
            for y in ylist:
                t.setTile(0, x, y)
        # last X
        t.column_iter(gen_iter_default((0x8C00,0x8C04), 0x8C08),
                      xlist[-1], y0, height)

#### Objects DD-DE: Cave tileset (tileset 8) misc objects

objDDinterior = ((0x8C0F,0x8C10,0x8C11,0x8C10,0x8C11,0x8C12,0x8C0F,0x8C10),
                 (0x798C,0x798D,0x798E,0x798D,0x798F,0x7990,0x798C,0x7990),
                 (0x7991,0x7992,0x7991,0x7993,0x7994,0x7997,0x7997,0x7997),
                 (0x7997,0x7997,0x7997,0x7997,0x7997,0x7995,0x7996,0x7994),
                 (0x7995,0x7996,0x7997,0x7997,0x7997,0x7997,0x7997,0x7997))
def objDD(t, x0, y0, width, height):
    xlist = list(t.xrange(x0, width))
    ylist = list(t.yrange(y0, height))
    randstart = random.randrange(8)

    # row 0
    parityX = 0
    for x in xlist:
        t.setTile(0x8D8C + parityX, x, ylist[0], highlight=False)
        parityX ^= 1
    # row 1-5
    for y, tilepool in zip(ylist[1:6], objDDinterior):
        i = randstart
        for x in xlist:
            t.setTile(tilepool[i], x, y)
            i = (i+1) & 7
    # row 6+
    for y, x in itertools.product(ylist[6:], xlist):
        t.setTile(0x7997, x, y)

    # modify columns left/right of rectangle
    if height > 0:
        # left column
        t.setTile(0x7998, xlist[0]-1, ylist[1], priority=False)
        for y in ylist[2:]:
            t.setTile(0x7999, xlist[0]-1, y, priority=False)

        if width > 0:  # right column
            t.setTile(0x799A, xlist[-1]+1, ylist[1], priority=False)
            for y in ylist[2:]:
                t.setTile(0x799B, xlist[-1]+1, y, priority=False)

def objDEgen() -> Iterator[int]:
    yield from range(0x79A4,0x79A8)
    while True:
        yield 0x799B
        yield 0x7999
def objDE(t, x0, y0, _, height):
    t.rect_iter_row(objDEgen(), x0, y0, 1, height)

def objDF(t, x, y0, width, _):
    t.row_iter(genseq_bordered_cycle(
        width+1, 0x8D92, (0x8D90,0x8D91), 0x8D93), x, y0)
    t.row_iter(genseq_bordered_cycle(
        width+1, 0xA602, (0xA600,0xA601), 0xA603), x, t.y_offset(y0, 1))

def objE0(t, x, y0, _, height):
    t.setTile(0xA605, x, y0)
    for y in t.yrange(y0 + 1, height - 1):
        t.setTile(0xA606, x, y)

objE1captiles = ((0x2C0C,0x1527,0x2F0B),
                 (0x2C0E,0x1528,0x2F0D),
                 (0x2C10,0x1529,0x2F0F))
objE1dist = (0, 0, 1, 2)
def objE1stalkgen() -> Iterator[int]:
    yield from range(0x8D29, 0x8D2E)
    while True:
        yield from range(0x8D2A, 0x8D2E)
def objE1(t, x0, y0, width, height):
    xlist = list(t.xrange(x0, width))
    ylist = list(t.yrange(y0, height))
    # row 0: mushroom cap platform
    captiles = objE1captiles[random.choice(objE1dist)]
    for x, tileID in zip(xlist, itertools.cycle(captiles)):
        if 0x8D2A <= t.getTile(x, y0) < 0x8D2E:
            tileID += 1
        t.setTile(tileID, x, y0)
    # ensure horizontal resize handle is on mushroom cap, not stalk
    t.obj.lastX = x
    # row 1+: mushroom stalk
    if height > 1:
        for y, tileID in zip(ylist[1:-1], objE1stalkgen()):
            for i, x in enumerate(xlist):
                t.setTile(tileID if i % 3 == 1 else -1, x, y)
    # last row: base of stalk
    if height >= 1:
        y = ylist[-1]
        for i, x in enumerate(xlist):
            if i % 3 == 1:
                tileID = 0x8D2E + (height+2 & 3)
                if 0x8D90 <= t.getTile(x, y) < 0x8D93:
                    tileID += 4
            else:
                tileID = -1
            t.setTile(tileID, x, y)

#### Object E2: Rock spire

objE2tiles = (  -1,  0x8D9A,0x8D9B,  -1,     -1,  0x8DA9,0x8DAA,  -1,
                -1,  0x8DB8,0x8DB9,  -1,     -1,  0x8DC6,0x8DC7,  -1,
              0x8D9C,0x8D9D,0x8D9E,0x8D9F, 0x8DAB,0x8DAC,0x8DAD,0x8DAE,
              0x8DBA,0x8DBB,0x8DBC,0x8DBD, 0x8DC8,0x8DC9,0x8DCA,0x8DCB,
              0x8D9A,0x8DA0,0x8DA0,0x8D9B, 0x8DA9,0x8DAF,0x8DAF,0x8DAA,
              0x8DB8,0x8DBE,0x8DBE,0x8DB9, 0x8DC6,0x8DCC,0x8DCC,0x8DC7,
              0x8DA1,0x8DA2,0x8DA3,0x8DA4, 0x8DB0,0x8DB1,0x8DB2,0x8DB3,
              0x8DBF,0x8DC0,0x8DC1,0x8DC2, 0x8DCD,0x8DCE,0x8DCF,0x8DD0)
def objE2(t, x0, y0, _, height):
    if height < 0x10:
        t.rect_iter_row(objE2tiles, x0, y0, 3, height)
    else:
        t.rect_iter_row(objE2tiles, x0, y0, 3, 7)
        t.rect_iter_row(itertools.cycle(objE2tiles[0x20:]),
            x0, y0+8, 3, height-8)

#### Objects E4-EC: Flower tileset ground

def objE4EArandinterior(i: int) -> int:
    offset = random.randrange(0x10) + 2 * i
    if 0 <= offset <= 9:
        return 0x79BB + offset
    else:
        return 0x79E0
def flowerleftedgecheck(t, x, y):
    if t.getTile(x-1, y) in (0x79D8, 0x79D9):
        t.setTile(0x79C9, x-1, y, priority=False, highlight=False)
def flowerrightedgecheck(t, x, y):
    if t.getTile(x+1, y) in (0x79D6, 0x79D7):
        t.setTile(0x79C8, x+1, y, priority=False, highlight=False)

objE4colpairs = (
    ((   -1,  0x859A,0x79DA), (   -1,  0x859B,0x79DB)),
    ((   -1,  0x859F,0x79DD), (   -1,  0x85A0,0x79DE)),
    ((   -1,  0x859A,0x79DD), (   -1,  0x859C,0x79DE)),
    ((   -1,  0x859F,0x79DD), (   -1,  0x85A1,0x79DF)),
    ((   -1,  0x859A,0x79DC), (   -1,  0x859B,0x79DB)),
    ((   -1,  0x85A2,0x79DD), (   -1,  0x85A0,0x79DC)),
    ((   -1,  0x85A2,0x79DA), (0xA85C5,0x859D,0x79AC)),
    ((0xA85C8,0x85A3,0x79AD), (   -1,  0x85A4,0x79AF)),
    ((0xA85C6,0x859E,0x79DC), (0xA85C7,0x859D,0x79DB)),
    ((0xA85C8,0x85A3,0x79DC), (0xA85C5,0x85A4,0x79B6)))
objE4dist = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 4, 6, 8)

def objE4(t, x0, y0, width, height):
    ylist = list(t.yrange(y0 - 2, height + 2))
    parityX = 0
    for x in t.xrange(x0, width):
        if parityX == 0:
            randcolgen = iter(objE4colpairs[random.choice(objE4dist)])
        for y, tileID in zip(ylist[0:3], next(randcolgen)):
            t.setTile(tileID, x, y)
        for i, y in enumerate(ylist[3:]):
            t.setTile(objE4EArandinterior(i), x, y)
        parityX ^= 1

objE5toEAdata = {
    0xE5: {
        "tiles": (
            ((   -1,  0x85A8,0x0D0D,0x79AD), (   -1,  0x85A7,0x0C0C,0x79AC)),
            ((   -1,  0x85A8,0x0D0E,0x79B6), (   -1,  0x85A7,0x0C0C,0x79AE)),
            ((   -1,  0x85A8,0x0D0E,0x79BD), (   -1,  0x85A6,0x0C0B,0x79AE)),
            ((0xA85C2,0x85A9,0x0D0E,0x79AD), (   -1,  0x85A6,0x0C0C,0x79AF)),
            ((0xA85C3,0x85AA,0x0D0E,0x79B1), (0xA85C1,0x85A5,0x0C0C,0x79B0))),
        "firstedge": flowerrightedgecheck, "lastedge": flowerleftedgecheck},
    0xE8: {
        "tiles": (
            ((   -1,  0x85AD,0x0F11,0x79B2), (   -1,  0x85B1,0x100E,0x79BE)),
            ((   -1,  0x85AD,0x0F10,0x79AF), (   -1,  0x85B1,0x100E,0x79B7)),
            ((   -1,  0x85AD,0x0F10,0x79B3), (   -1,  0x85B2,0x100F,0x79B4)),
            ((0xA85C3,0x85AE,0x0F10,0x79C2), (   -1,  0x85B1,0x100E,0x79B6)),
            ((0xA85C2,0x85AF,0x0F11,0x79B2), (0xA85C3,0x85B0,0x100E,0x79BE))),
        "firstedge": flowerleftedgecheck, "lastedge": flowerrightedgecheck},
    0xE6: {
        "tiles": (
            (   -1,  0x85B9,0x0814,0x79AA),
            (   -1,  0x85BA,0x0815,0x79AA),
            (   -1,  0x85B9,0x0816,0x79AB),
            (0xA85C1,0x85BB,0x0816,0x79AB),
            (0xA85C2,0x85BC,0x0814,0x79B6)),
        "heightoffset": 2, "slope": 1, "lastedge": flowerleftedgecheck},
    0xE9: {
        "tiles": (
            (   -1,  0x85BD,0x0A15,0x79B7),
            (   -1,  0x85BF,0x0A16,0x79B7),
            (   -1,  0x85BD,0x0A17,0x79B8),
            (0xA85C3,0x85BE,0x0A17,0x79B8),
            (0xA85C4,0x85C0,0x0A15,0x79AF)),
        "heightoffset": 2, "slope": 1, "lastedge": flowerrightedgecheck},
    0xE7: {
        "tiles": (
            (0xA85B3,0x020A,0x030D,0x79B9),
            (0xA85A7,0x020A,0x030D,0x79B6),
            (0xA85A6,0x020B,0x030D,0x79B9),
            (0xA85A7,0x020A,0x030D,0x79AC),
            (0xA85A7,0x020A,0x030D,0x79B9)),
        "heightoffset": 1, "slope": 2},
    0xEA: {
        "tiles": (
            (0xA85B6,0x050B,0x060D,0x79BA),
            (0xA85B6,0x050B,0x060D,0x79AF),
            (0xA85B7,0x050A,0x060D,0x79BA),
            (0xA85B8,0x050B,0x060D,0x79AC),
            (0xA85B8,0x050B,0x060D,0x79BA)),
        "heightoffset": 1, "slope": 2},
    }
objE5toEAdist = (0, 1, 2, 3, 4, 0, 3, 4)

def objE5E8(t, x0, y0, width, height):
    data = objE5toEAdata[t.obj.ID]
    y0 -= 2
    height += 2
    parityX = 0

    # extra check before first column
    data["firstedge"](t, x0, y0+1)

    for x in t.xrange(x0, width):
        if parityX == 0:
            randcolgen = iter(data["tiles"][random.choice(objE5toEAdist)])
        ygen = t.yrange(y0, height)

        for tileID, y in zip(next(randcolgen), ygen):
            t.setTile(tileID, x, y)
        for i, y in enumerate(ygen):
            t.setTile(objE4EArandinterior(i), x, y)

        if parityX == 1:  # adjust for slope
            if height == 0:
                return
            height -= 1
            y0 += 1
        parityX ^= 1

    # extra check after last column
    data["lastedge"](t, x, y0+1)  # y0+2, but y0 was incremented at end of loop

def objE6E7E9EA(t, x0, y0, width, height):
    data = objE5toEAdata[t.obj.ID]
    y0 -= data["heightoffset"]
    adjheight = t.obj.adjheight
    adjheight += data["heightoffset"]

    for x in t.xrange(x0, width):
        ygen = t.yrange_adj(y0, adjheight)
        randcol = data["tiles"][random.choice(objE5toEAdist)]
        if adjheight < 0:  # negative height due to slope -2: glitched behavior
            randcol = randcol[0:1]

        for tileID, y in zip(randcol, ygen):
            t.setTile(tileID, x, y)
        for i, y in enumerate(ygen):
            if adjheight < 0:  # negative height due to slope -2: glitched behavior
                i = -5 - i
            t.setTile(objE4EArandinterior(i), x, y)

        # adjust for slope
        adjheight -= data["slope"]
        if adjheight == 0:
            return
        y0 += data["slope"]

    # extra check after last column in E6/E9
    if "lastedge" in data:
        data["lastedge"](t, x, y0+1)  # y0+2, but y0 was incremented at end of loop

objEBECdata = {
    0xEB: {"slopetiles": objE5toEAdata[0xE7]["tiles"][0:3],
           "maintile": 0x79D6,
           "awaydir": -1, "awayalt": 0x79C8},
    0xEC: {"slopetiles": objE5toEAdata[0xEA]["tiles"][0:3],
           "maintile": 0x79D8,
           "awaydir": +1, "awayalt": 0x79C9},
    }
objEBECsidereplace = (0x79AD,0x79AE,0x79B5,0x79DD)
def objEBEC(t, x0, y0, width, height):
    y0 -= 1
    height += 1
    data = objEBECdata[t.obj.ID]
    ylist = list(t.yrange(y0, height))

    for x in t.xrange(x0, width):
        # rows 0-2: use tiles from slope 2 or -2
        for tileID, y in zip(random.choice(data["slopetiles"]), ylist):
            t.setTile(tileID, x, y)

        # remaining rows
        parityY = 0
        for y in ylist[3:]:
            tileID = data["maintile"] + parityY
            # check tiles on either side
            if t.getTile(x - data["awaydir"], y) >> 8 == 0x79:
                t.setTile(random.choice(objEBECsidereplace),
                          x - data["awaydir"], y,
                          priority=False, highlight=False)
            if y != ylist[-1]:
                awaytile = t.getTile(x + data["awaydir"], y)
                if (awaytile >> 8 in (0x03,0x06,0x08,0x0A,0x0C,0x10) or
                        0x85A8 <= awaytile <= 0x85AF):
                    tileID = data["awayalt"]

            t.setTile(tileID, x, y)
            parityY ^= 1

#### Objets 1F-20, EE-F3: 2.5D tileset

obj1Ftiles = ((0x002B,0x0027,0x9100,0x7E02,0x7E05),
              (0x002C,0x0027,0x9101,0x7E03,0x7E05))
def obj1F(t, x0, y0, width, height):
    parity = 0
    for x in t.xrange(x0, width):
        t.column_iter(gen_iter_default(obj1Ftiles[parity], 0x7E04),
                      x, y0, height)
        parity ^= 1

def objED_row0gen(width, parity) -> Iterator[int]:
    # first (bottom) row
    # left tile
    yield 0x3D0A - parity
    if width != 0:
        # middle tiles
        parity ^= 1
        for _ in range(width-1):
            yield 0x3D0A + parity
            parity ^= 1
        # right tile
        yield 0x3D0B if parity else 0x3D09
def objED_rowgen(width, parity, randoffsets) -> Iterator[int]:
    # remaining rows
    # left tile
    tileID = 0x79E9 - parity + random.choice(randoffsets)
    yield tileID
    if width != 0:
        parity ^= 1
        # middle tiles
        for _ in range(width-1):
            if parity:
                yield tileID + 1
            else:
                tileID = 0x79E9 + random.choice(randoffsets)
                yield tileID
            parity ^= 1
        # right tile
        yield tileID + 1 if parity else 0x79E8 + random.choice(randoffsets)

def objED(t, x0, y0, width, height):
    parity = (x0^y0)&1
    xlist = list(t.xrange(x0, width))
    for i, y in enumerate(t.yrange(y0, height)):
        if i == 0:
            tilegen = objED_row0gen(width, parity)
        else:
            i = min(i, 4)
            tilegen = objED_rowgen(width, parity, (i//2*3, (i+1)//2*3))
        for x in xlist:
            t.setTile(next(tilegen), x, y)
        parity ^= 1

def objEE_modifier(tileID) -> int:
    if tileID in (0, 0x0106) or tileID >> 8 == 0x77:
        return tileID
    if tileID == 0x0108: return 0x7792
    if tileID == 0x0109: return 0x7793
    if tileID == 0x79E7: return 0
    return tileID - 0x255

obj20EEF3_toptiles = (0x0028,0x0100,0x0103)
obj20EEF3_toprightcheck = (0x0029,0x002D,0x0101,0x010A,0x0104,0x0105)
obj20EEEF_toprightreplace = (0x002D,0x010A,0x0105)
objF0F3_toprightreplace = (0x002D,0x9C03,0x0105)
objEEF3_shaded1wide = (0x0106,0x79E1,0x79E4,0x79E7)
def obj20EEF3(t, x0, y0, width, height):
    xlist = list(t.xrange(x0, width))
    ylist = list(t.yrange(y0, height))
    lastX = xlist[-1]
    shaded = (t.obj.ID != 0x20)

    # rows 0-2
    for relY, y in enumerate(ylist[0:3]):
        rowbase = obj20EEF3_toptiles[relY]
        for x in xlist:
            # top 3 rows use (initial Y)^(absolute X) parity
            tileID = rowbase + ((y0^x)&1)
            if x == lastX:
                # replace final left brick half with 1-wide brick
                checktile = t.getTile(x-1, y)
                if checktile in obj20EEF3_toprightcheck:
                    if t.obj.ID >= 0xF0:
                        tileID = objF0F3_toprightreplace[relY]
                    else:
                        tileID = obj20EEEF_toprightreplace[relY]
                else:
                    tileID = checktile + 1
            t.setTile(tileID, x, y)

    # rows 3+: new relY is actually relY-3
    for relY3, y in enumerate(ylist[3:]):
        for x in xlist:
            tileID = 0x0108 | (y^x)&1
            if x == x0 and tileID == 0x0109:
                # replace initial right brick half with 1-wide brick
                if t.getTile(x-1, y) != 0x0108:
                    tileID = 0x0106
            if t.fixver > 0 and x == lastX and tileID == 0x0108:
                # unused due to vanilla bug
                # replace final right brick half with 1-wide brick
                if t.getTile(x+1, y) != 0x0109:
                    tileID = 0x0106
            if shaded:
                if tileID == 0x0106:
                    # 1-wide brick
                    index = relY3 >> 1 if relY3 <= 5 else random.randint(2, 3)
                    tileID = objEEF3_shaded1wide[index]
                elif tileID == 0x0109:
##                if tileID in (0x0109,0x79E3,0x79E6):
                    # right brick half: match color of left brick
                    checktile = t.getTile(x-1, y)
                    if checktile in (0, 0x79E7):
                        tileID = checktile
                    else:
                        tileID = checktile + 1
                else:
                    # left brick half
                    index = relY3 + random.randint(0, 3)
                    tileID = 0x79E2 if index >= 3 else 0x0108
            if t.obj.ID == 0xEE:
                tileID = objEE_modifier(tileID)
            t.setTile(tileID, x, y)

####

def objF5(t, x0, y0, width, height):
    ylist = list(t.yrange(y0+1, height-1))
    for x in t.xrange(x0, width):
        t.setTile(0x8413, x, y0)
        for y in ylist:
            t.setTile(0x2910, x, y)

def objF6(t, x0, y0, width, height):
    for x, y in itertools.product(t.xrange(x0, width), t.yrange(y0, height)):
        if t.getTile(x, y) == 0:
            t.setTile(0x9D8B, x, y)

#### Objects F7-FE: Submarine tileset GBA additions

def objF7FC(t, x0, y, width, _):
    starttile = 0x01D1 + (t.obj.ID - 0xF7) * 3
    t.row_iter(
        genseq_bordered(width+1, starttile, starttile+1, starttile+2), x0, y)

def objFEcolumngen(i) -> Iterator[int]:
    yield from range(0xA800+i, 0xA820, 8)
    yield 0xA700+i
    while True: yield 0x110FE
def objFE(t, x0, y0, width, height):
    i = 0
    for x in t.xrange(x0, width):
        t.column_iter(objFEcolumngen(i), x, y0, height)
        i = (i + 1) & 7

#### Advynia custom object functions

def advtile(t, x0, y0, width, height):
    # Arbitrary single tile
    t.rect_single(t.obj.extID, x0, y0, width, height)

####

# List of standard objects, indexed by ID
# Strings are placeholders for formulaic functions

stdobjs = [
    None,obj01,obj0203,obj0203,obj0409,obj0409,obj0409,obj0409,   # 01-07
    obj0409,obj0409,obj0A0B,obj0A0B,obj0C,obj0D,obj0E,obj0F,   # 08-0F
    obj10,obj1112,obj1112,obj13,obj14,obj15,obj16,obj17,   # 10-17
    obj18,obj19,obj1A,obj1B,obj1C,"S","S",obj1F,   # 18-1F
    obj20EEF3,obj21,obj22,obj23,obj24,obj25,obj26,obj2728,   # 20-27
    obj2728,obj292A,obj292A,obj2B,obj2C,obj2D2E,obj2D2E,obj2F,   # 28-2F
    obj30,obj3136,obj3233,obj3233,obj34,obj35,obj3136,obj37,   # 30-37
    obj38,obj39,obj3A3B,obj3A3B,obj3CF4,obj3D,obj3E,obj3F40,   # 38-3F
    obj3F40,obj41,obj42,obj43,obj44,obj4546,obj4546,obj47,   # 40-47
    obj48,obj49,obj4A,obj4B4D,obj4B4D,obj4B4D,obj4E,obj4F,   # 48-4F
    obj50,obj51,obj52,obj53,obj5456,obj5456,obj5456,obj57,   # 50-57
    obj58,obj595E,obj595E,obj595E,obj595E,obj595E,obj595E,obj5F60,   # 58-5F
    obj5F60,obj6162,obj6162,obj63,obj63,advtile,obj66,obj67,   # 60-67
    "S",obj69,obj6A,obj6B,obj6C,obj6D,obj6E,obj6F,   # 68-6F
    "YX","YX","YX",obj7376,obj7376,obj7376,obj7376,"S",   # 70-77
    obj7879,obj7879,obj7A,obj7B,obj7C,obj7D,obj7E,obj7F,   # 78-7F
    obj80,None,"S",obj83C4C7,obj84C6C9,obj85,obj86,obj8788,   # 80-87
    obj8788,obj89,"S","S",obj8C,obj8D,"YX",obj8F,   # 88-8F
    obj90,obj9192,obj9192,obj93,"YX","YX","YX","YX",   # 90-97
    obj98,obj99,obj9A,obj9B9C,obj9B9C,obj9D,"S",obj9F,   # 98-9F
    objA0A2,objA0A2,objA0A2,"YX","YX",objA5,objA6,objA7,   # A0-A7
    objA8,objA9,objAAAB,objAAAB,objAC,objACAD,objAE,objAF,   # A8-AF
    objB0,objB1,objB2B9,objB2B9,objB2B9,objB2B9,objB2B9,objB2B9,   # B0-B7
    objB2B9,objB2B9,objBA,objBB,objBC,objBD,objBE,objBF,   # B8-BF
    objC0C1,objC0C1,objC2C3,objC2C3,obj83C4C7,objC5C8,obj84C6C9,obj83C4C7,   # C0-C7
    objC5C8,obj84C6C9,objCA,objCB,objCCCD,objCCCD,objCE,objCFD0,   # C8-CF
    objCFD0,"S","S",objD3,objD4D5,objD4D5,objD6D7,objD6D7,   # D0-D7
    objD8,objD9,"S",objDB,objDC,objDD,objDE,objDF,   # D8-DF
    objE0,objE1,objE2,objE3,objE4,objE5E8,objE6E7E9EA,objE6E7E9EA,   # E0-E7
    objE5E8,objE6E7E9EA,objE6E7E9EA,objEBEC,objEBEC,objED,obj20EEF3,obj20EEF3,   # E8-EF
    obj20EEF3,obj20EEF3,obj20EEF3,obj20EEF3,obj3CF4,objF5,objF6,objF7FC,   # F0-F7
    objF7FC,objF7FC,objF7FC,objF7FC,objF7FC,None,objFE   # F8-FE
    ]

# Single-tile rectangle/line objects

objStiles = {
    0x1D:0x001D, 0x1E:0x001E, 0x68:0x6000, 0x77:0x3D58, 0x82:0x6001,
    0x8A:0x7400, 0x8B:0x7300, 0x9E:0x7502, 0xD1:0x870F, 0xD2:0x870E,
    0xDA:0x8A00
    }

def gen_objS(tileID) -> Callable:
    def objS(t, x, y, width, height):
        t.rect_single(tileID, x, y, width, height)
    return objS

for _extID, _tileID in objStiles.items():
    stdobjs[_extID] = gen_objS(_tileID)

# 2x2 parity rectangle/line objects that enforce even lengths

objYXtiles = {0x70: (0x3D37,0x3D38,0x3D45,0x3D46),
              0x71: (0x0141,0x0142,0x0143,0x0144),
              0x72: (0x3D39,0x3D3A,0x3D47,0x3D48),
              0x8E: (0x7500,0x7501,0x3DAA,0x3DAB),
              0x94: (0x7600,0x7601,0x7775,0x7776),
              0x95: (0x7602,0x7603,0x7777,0x7778),
              0x96: (0x7604,0x7605,0x7779,0x777A),
              0x97: (0x7606,0x7607,0x777B,0x777C),
              0xA3: (0x7B00,0x7B01,0x7B02,0x7B03),
              0xA4: (0x7B04,0x7B05,0x7B06,0x7B07),
              }

def gen_objYX(tiles) -> Callable:
    def objYX(t, x0, y0, width, height):
        if width & 1 == 0: width += 1
        if height is None: height = 1
        elif height & 1 == 0: height += 1

        parityY = 0
        for y in t.yrange(y0, height):
            parityYX = parityY
            for x in t.xrange(x0, width):
                t.setTile(tiles[parityYX], x, y)
                parityYX ^= 1
            parityY ^= 2

    return objYX

for _extID, _tiles in objYXtiles.items():
    stdobjs[_extID] = gen_objYX(_tiles)

# Fallback functions for unused/unimplemented objects

objcount = (0x100 - stdobjs.count(None))

def _genericobjfunc(ID) -> Callable:
    return lambda t, x, y, width, height : t.rect_single(
        0x10000 + ID, x, y, width, height)

from inspect import signature

objcount = 0
for i in range(1, 0xFF):
    if stdobjs[i] is None:
        stdobjs[i] = _genericobjfunc(i)
    else:
        objcount += 1
