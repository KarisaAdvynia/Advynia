"""SMA3 Layer 1 Tilemap: Extended Object Functions

Functions to replicate in-game extended objects (object 00), which operate on
the tilemap without width/height parameters.

Each function takes 3 arguments: tilemap, initial X, initial Y.
Tilemap is abbreviated to "t" for compactness, given its frequent references.
"""

# standard library imports
import itertools, random
from collections.abc import Callable, Iterator

# import from other files
from AdvGame import SMA3
from .ExtObjData import *
from .Shared import *

# Non-formulaic extended objects

ext0Ctiles = (0x920F,0x9066,0x9076,0x9086)
def ext0C(t, x0, y0):
    for y, tileID in zip(t.yrange(y0, 3), ext0Ctiles):
        for relX, x in enumerate(t.xrange(x0, 1)):
            if t.getTile(x, y) == 0x9216:
                t.setTile(0x9213 + relX, x, y)
            else:
                t.setTile(tileID + relX, x, y)

ext10tiles = (0x84C2,0x84C4,0x84C3,0x84C5)
def ext10(t, x0, y0):
    tilegen = itertools.cycle(ext10tiles)
    parityX = 0
    for x in t.xrange(x0, 0xF):
        for y in t.yrange(y0, 0x1F):
            t.setTile(next(tilegen) ^ parityX, x, y)
        parityX ^= 1

#### Extended objects 14-15: Red stairs outlines

ext14tiles = (0x96D6,  -1,  0x96D6,0x96D7,  -1,
              0x96D7,  -1,  0x96D4,  -1,  0x96D4)
def ext14(t, x0, y0):
    ylist = list(t.yrange(y0+1, -5))
    for i, x in enumerate(t.xrange(x0, 4)):
        t.setTile(ext14tiles[2*i], x, ylist[i+1])
        t.setTile(ext14tiles[2*i+1], x, ylist[i])

ext15tiles = (  -1,  0x96D5,  -1,  0x96D5,  -1,
              0x96D8,0x96D9,0x96D8,0x96D9,  -1  )
def ext15(t, x0, y0):
    ylist = list(t.yrange(y0, 5))
    for i, x in enumerate(t.xrange(x0, 4)):
        t.setTile(ext15tiles[2*i], x, ylist[i])
        t.setTile(ext15tiles[2*i+1], x, ylist[i+1])

####

def ext16(t, x, y):
    t.setTile(t.dyn[0xA300] | (t.getTile(x, y) & 0xFF), x, y)

ext30center = (0x015D,0x015E,0x015F,0x0160)*2
def ext30(t, x0, y0):
    x_gen = t.xrange(x0 - 1, 3)
    x = next(x_gen)  # column 0
    for y in t.yrange(y0, 3):
        t.setTile(0x015C if t.getTile(x, y) != 0x015A else -1, x, y)
    x = next(x_gen)  # columns 1-2
    t.rect_iter_row(ext30center, x, y0, 1, 3)
    next(x_gen)      # ignore x for column 2
    x = next(x_gen)  # column 3
    for y in t.yrange(y0, 3):
        t.setTile(0x015C if t.getTile(x, y) != 0x015B else -1, x, y)

def ext46(t, x, y):
    t.setTile(random.choice((0x5F00,0x5F01,0x5F03,0x5F03)), x, y)

def ext4A(t, x, y):
    t.setTile(0x3D4C, x, y)
    if t.getTile(x-1, y) in (0x3D3B,0x3D49,0x3D4A):
        t.setTile(0x3D3C, x-1, y, priority=False, highlight=False)
def ext4B(t, x, y):
    t.setTile(0x3D41, x, y)
    if t.getTile(x+1, y) in (0x3D3B,0x3D49,0x3D3C):
        t.setTile(0x3D4A, x+1, y, priority=False, highlight=False)

ext50A8tiles = {
    0x50: (0x000C,0x000D,0x0013,0x0014),  # right arrow sign
    0xA8: (0x000E,0x000F,0x0011,0x0012)}  # left arrow sign
ext50A8alttiles = {
    # index 0 and 1 are unintended, but accessible by the game
    0x50: (0xD0700,0xD0800,0xD6A0A,0xD6A0B),  # right with ground
    0xA8: (0xD0603,0xD0604,0xD6A0C,0xD6A0D)}  # left with ground
ext50A8flowertiles = (0x000C,0x000D,0x008E,0x008F)  # right with flowers
ext50A8snowtop = {
    0x50: (0x0025,0x0026),  # right arrow sign
    0xA8: (0x0033,0x0034)}  # left arrow sign
def ext50A8(t, x0, y0):
    for i, (y, x) in enumerate(itertools.product(t.yrange(y0, 1),
                                                 t.xrange(x0, 1))):
        if t.getdyn(x, y) in (0x2A00,0x2A01,0x6A00,0x6A01):
            t.setTile(ext50A8alttiles[t.obj.extID][i], x, y)
        elif t.tileset == 0xC:  # flower tileset
            # left arrow sign becomes a right arrow sign!
            if t.getTile(x, y) >> 8 == 0x85:
                t.setTile(ext50A8flowertiles[i], x, y)
            else:
                t.setTile(ext50A8tiles[0x50][i], x, y)
        elif t.tileset == 4 and i < 2 and t.getTile(x, y+1) != 0:
            # replace top half of the arrow sign with identical, differently
            #   numbered tiles... but maybe the user edited those tiles?
            t.setTile(ext50A8snowtop[t.obj.extID][i], x, y)
        else:
            t.setTile(ext50A8tiles[t.obj.extID][i], x, y)

def ext5253replaceif(t, x, y, checktile):
    tileID = -1
    if t.getTile(x, y) == checktile:
        tileID = 0x015C
    t.setTile(tileID, x, y, highlight=False)
def ext5253shared(t, xlist, yiter, centertiles: Iterator):
    for y in yiter:
        ext5253replaceif(t, xlist[0], y, 0x015A)
        for x in xlist[1:4]:
            t.setTile(next(centertiles), x, y)
        ext5253replaceif(t, xlist[4], y, 0x015B)

ext52center = range(0x3D63, 0x3D69)
def ext52(t, x0, y0):
    ext5253shared(t, list(t.xrange(x0, 4)), t.yrange(y0, 1), iter(ext52center))

ext53center = (0x3D63,0x3D6C,0x3D65,0x3D69,0x3D6A,0x3D6B)
def ext53(t, x0, y0):
    xlist = list(t.xrange(x0, 4))
    ylist = list(t.yrange(y0, 2))
    # row 0-1
    ext5253shared(t, xlist, ylist[0:2], iter(ext53center))
    # row 2
    t.setTile(-1, xlist[0], ylist[2])
    ext5253replaceif(t, xlist[1], ylist[2], 0x015A)
    t.setTile(0x010E, xlist[2], ylist[2])
    t.setTile(0x010F, xlist[3], ylist[2])
    t.setTile(-1, xlist[4], ylist[2])

ext545Cprop = {
    0x54: (2, (  -1  ,  -1  ,0x3DA1,
               0x3D79,0x3D77,0x3DA2,
               0x3D7A,0x3DA0,  -1  )),
    0x55: (2, (0x3DA4,  -1  ,  -1  ,
               0x3DA3,0x3D78,0x3D7C,
                 -1  ,0x3D9F,0x3D7B)),
    0x59: (1, (  -1  ,0x3D79,0x3D73,
                 -1  ,0x3D7A,0x3DA0)),
    0x5C: (1, (0x3D74,0x3D7C,  -1  ,
               0x3D9F,0x3D7B,  -1  )),
    }
def ext5455595C(t, x0, y0):
    height, tiles = ext545Cprop[t.obj.extID]
    tile_iter = iter(tiles)
    for y, x in itertools.product(t.yrange(y0, height), t.xrange(x0, 2)):
        tileID = next(tile_iter)
        if tileID == 0x3DA0 and t.getTile(x, y) == 0x3D71:
            tileID = 0x3DA8
        elif tileID == 0x3D9F and t.getTile(x, y) == 0x3D72:
            tileID = 0x3DA8
        t.setTile(tileID, x, y)

ext67dynreplace = {0x0802:0xD0803, 0x0A04:0xD0A03, 
                   0x0C01:0xD0C02, 0x1003:0xD1002}
ext67staticreplace = {0x3DBD:0x3DCC, 0x3DC0:0x3DCD}
def ext67(t, x, y):
    prevtile = t.getTile(x, y)
    tileID = ext67dynreplace.get(t.dynrev.get(prevtile),
             ext67staticreplace.get(prevtile))
    if tileID is None:
        tileID = MultiTileID(prevtile, 0x11E67)
    t.setTile(tileID, x, y)
    # use error tile 11E67 if no valid slanted log tile to modify

#### Extended objects 88-8C,9F-A3: Sewer tileset

ext88_pipebase = (
      -1,  0x8500,0x8503,  -1,
    0x8506,0x77EC,0x77ED,0x850A,
    0x850E,0x1800,0x77EE,0x8512,
      -1,  0x8516,0x8519,  -1  )
ext88_roombase = (
      -1,  0x857A,0x857E,  -1,
    0x8582,0x77EC,0x77ED,0x8586,
    0x858A,0x1800,0x77EE,0x858E,
      -1,  0x8592,0x8596,  -1  )
def ext88pipe(i, prevtile: int) -> int:
    """Calculate overlap generation for the sewer pipe variant of the door.
    Can overflow the in-game offset tables."""
    tileID = ext88_pipebase[i]
    if tileID >> 8 != 0x85:  # adjust only base tiles with high byte 85
        return tileID
    if (i < 4 and prevtile >> 8 == 0x79) or\
       (i >= 12 and prevtile >> 8 in (0x15, 0x79)):
        # don't modify tileID under these conditions
        return -1
    offset = ((prevtile - 0x99) & 0xFE) // 2
    if 4 <= i < 12:
        offset += 0x14  # use y1,y2 table start
    return (tileID + ext88_pipeoffsets[offset]) & 0xFFFF

def ext88(t, x0, y0):
    for i, (y, x) in enumerate(itertools.product(t.yrange(y0, 3),
                                                 t.xrange(x0, 3))):
        prevtile = t.getTile(x, y)
        if prevtile >> 8 != 0x85:
            # generate sewer pipe variant
            tileID = ext88pipe(i, prevtile)
        else:
            # generate sewer room variant
            tileID = ext88_roombase[i]
            if tileID >> 8 == 0x85:  # adjust only base tiles with high byte 85
                tileID = (tileID + prevtile - 0x854B) & 0xFFFF
        t.setTile(tileID, x, y)

ext898Atilebase = {0x89: (0x851B,0x8521), 0x8A: (0x8523,0x8529),
                   0x8B: (0x852B,0x8531), 0x8C: (0x8533,0x8539)}
def ext898A(t, x0, y0):
    tile0, tile1 = ext898Atilebase[t.obj.extID]
    y1 = (y0 + 1) & 0x7F
    for relX, x in enumerate(t.xrange(x0, 1)):
        offset = (t.getTile(x, y0) - 9) & 0xE
        t.setTile(tile0 + relX + offset, x, y0)
        if offset == 0:
            t.setTile(tile1 + relX, x, y1, priority=False)
def ext8B8C(t, x0, y0):
    tile0, tile1 = ext898Atilebase[t.obj.extID]
    x1 = t.x_offset(x0, 1)
    for relY, y in enumerate(t.yrange(y0, 1)):
        offset = (t.getTile(x0, y) - 9) & 0xE
        t.setTile(tile0 + relY + offset, x0, y)
        if offset == 0:
            t.setTile(tile1 + relY, x1, y, priority=False)

def ext8D(t, x0, y0):
    if t.getTile(x0, y0) & 1:  # odd: generate top-left corner
        t.setTile(0xD393E, x0, y0)
        t.setTile(0xD2A05, x0, y0-1, priority=False, highlight=False)
        t.setTile(0, x0-1, y0, priority=False, highlight=False)
        t.setTile(0, x0-1, y0-1, priority=False, highlight=False)
    else:  # even: generate top-right corner
        t.setTile(0xD393F, x0, y0)
        t.setTile(0xD2A02, x0, y0-1, priority=False, highlight=False)
        t.setTile(0, x0+1, y0, priority=False, highlight=False)
        t.setTile(0, x0+1, y0-1, priority=False, highlight=False)

ext9A9DB3data = {
    0x9A: {0: 0x872F, 1: 0x0006, "offsetX": 0, "offsetY": -1},
    0x9B: {0: 0x873F, 1: 0x0007, "offsetX": 0, "offsetY": -1},
    0x9C: {0: 0x874F, 1: 0x0008, "offsetX": -1, "offsetY": 0},
    0x9D: {0: 0x875F, 1: 0x0009, "offsetX": -1, "offsetY": 0},
    0xB3: {0: 0x8D8E, 1: 0x8D8F, "offsetX": +1, "offsetY": 0},
    }
def ext9A9DB3(t, x, y):
    data = ext9A9DB3data[t.obj.extID]
    t.setTile(data[0], x, y)
    t.setTile(data[1], x + data["offsetX"], y + data["offsetY"], priority=False)

def ext9E9F(t, x, y0):
    objoffset = t.obj.extID - 0x9E
    # this object doesn't check for in-game overflow!
    t.setTile((t.getTile(x, y0) + 0x17 + objoffset*4) & 0xFFFF, x, y0)
    t.setTile(0x8104 + objoffset, x, y0+1, priority=False)

extA0A3prop = {  # tiles, x starting offset, y starting offset,
                 # x offset to check, tiles to replace at x offset,
                 # y offset to check, tiles to replace at y offset
    0xA0: (range(0x7970, 0x7974), -1, -1,
        -1, {0x7946:0x7949, 0x794D:0x7950, 0x7944:0x7948, 0x794B:0x7951},
        -1, {0x7942:0x7945, 0x7943:0x7946}),
    0xA1: (range(0x7974, 0x7978), 0, -1,
        +1, {0x7957:0x7959, 0x795E:0x7960, 0x7955:0x7958, 0x795C:0x795F},
        +1, {0x7948:0x794B}),
    0xA2: (range(0x7978, 0x797C), -1, 0,
        -1, {0x7964:0x7967, 0x796B:0x796E, 0x7962:0x7966, 0x7969:0x796D},
        +1, {0x793D:0x7940, 0x793E:0x7941}),
    0xA3: (range(0x797C, 0x7980), 0, 0,
        +1, {0x7965:0x7967, 0x796C:0x796E, 0x7963:0x7966, 0x796C:0x796F},
        +1, {0x794F:0x7951, 0x7950:0x7952}),
    }
def extA0A3(t, x0, y0):
    tiles, startX, startY, offsetX, checkX, offsetY, checkY = extA0A3prop[t.obj.extID]
    tilegen = iter(tiles)
    for y, x in itertools.product(t.yrange(y0 + startY, 1),
                                  t.xrange(x0 + startX, 1)):
        t.setTile(next(tilegen), x, y)
        t.lookup_replace(checkX, x+offsetX, y, priority=False, highlight=False)
        t.lookup_replace(checkY, x, y+offsetY, priority=False, highlight=False)

extADB2prop = {
    0xAD: (2, (0x8D54,0x8D55,0x8D56,0x8D57,0x8D58,0x8D59)),
    0xAE: (2, (0x8D54,0x8D55,0x8D56,0x8D5A,0x8D58,0x8D5B)),
    0xAF: (1, (0x8D5C,0x8D5D,0x8D5E,0x8D5F)),
    0xB0: (1, (0x8D5C,0x8D5D,0x8D60,0x8D5F)),
    0xB1: (1, (0x8D5C,0x8D5D,0x8D5E,0x8D61)),
    0xB2: (1, (0x8D5C,0x8D5D,0x8D60,0x8D61)),
    }
def extADB2(t, x0, y0):
    height, tiles = extADB2prop[t.obj.extID]
    randoffset = random.randrange(0, 0x30, 0xE)
    t.rect_iter_row((tileID+randoffset for tileID in tiles), x0, y0, 1, height)

#### Extended objects B4-BF: Random-color cave decorations

extB4B7prop = {
    0xB4: (1, 1, (0xD0801,0xD0F02,0x8D00,0x8D01),
                 (0xD0802,0xD0F06,0x8D06,0x8D07)),
    0xB5: (1, 1, (0xD0D01,0xD0A01,0x8D02,0x8D03),
                 (0xD0D04,0xD0A02,0x8D04,0x8D05)),
    0xB6: (2, 2, (0xD0202,0xD0F04,0xD1001,0xD0303,0x8D08,0x8D09,
                  0x8D0A,0x8D0B,0x8D0C),
                 (0xD0203,0xD0F05,0xD1003,0xD0304,0x8D12,0x8D13,
                  0x8D14,0x8D15,0x8D16)),
    0xB7: (2, 2, (0xD0C01,0xD0D03,0xD0502,0x8D0D,0x8D0E,0xD0603,
                  0x8D0F,0x8D10,0x8D11),
                 (0xD0C02,0xD0D05,0xD0503,0x8D17,0x8D18,0xD0604,
                  0x8D19,0x8D1A,0x8D1B)),
    }
def extB4B7(t, x0, y0):
    width, height, tilemapA, tilemapB = extB4B7prop[t.obj.extID]
    tiles = random.choice((tilemapA, tilemapB))
    t.rect_iter_row(tiles, x0, y0, width, height)

extBABFtiles = {
    0xBA: (0x8D36,0x8D42),
    0xBB: (0x8D36,0x8D39,0x8D3F),
    0xBC: (0x8D36,0x8D39,0x8D3C,0x8D3F),
    0xBD: (0x8D36,0x8D48,0x8D4B,0x8D4E),
    0xBE: (0x8D36,0x8D48,0x8D4E),
    0xBF: (0x8D45,0x8D51),
    }
def extBABF(t, x0, y0):
    tiles = extBABFtiles[t.obj.extID]
    randoffset = random.choice((0, 0, 1, 2))
    t.column_iter((tileID+randoffset for tileID in tiles), x0, y0)

#### Extended objects C0-C1: Rock spire connections

def extC0(t, x0, y0):
    xlist = list(t.xrange(x0, 1))
    # row 0
    t.setTile(0x8DA7, xlist[0], y0)
    t.setTile(0x8DA8, xlist[1], y0)
    # row 1
    y = t.y_offset(y0, 1)
    for relX, x in enumerate(xlist):
        tileID = 0x8F04 if (t.getTile(x, y+1) in (0x8DA5, 0x8DA6)) else 0x152A
        t.setTile(tileID + relX, x, y)

def extC1(t, x0, y0):
    xlist = list(t.xrange(x0, 1))
    # row 0
    t.setTile(0x8DA5, xlist[0], y0)
    t.setTile(0x8DA6, xlist[1], y0)
    # row -1
    y = t.y_offset(y0, -1)
    for relX, x in enumerate(xlist):
        prevtile = t.getTile(x, y)
        if prevtile in (0x152A, 0x152B):
            t.setTile(prevtile + 0x79DA, x, y, highlight=False)  # 8F04 or 8F05

####
# extra check for flower-tileset rock objects, which mostly share gen_extR code

def extD4DFgroundcheck(t, x0, y, width):
    for x in t.xrange(x0, width):
        tile = t.getTile(x, y)
        if tile == 0x100F:
            t.setTile(0x100E, x, y, priority=False, highlight=False)
        elif tile == 0x0C0B:
            t.setTile(0x0C0C, x, y, priority=False, highlight=False)

#### Extended objects FB/FE-FF: special commands

def extFB(t, objX, objY):  # screen linker
    obj = t.obj

    # display filler tile
    t.setTile(MultiTileID(t.getTile(objX, objY), 0x10EFB), objX, objY)

    currentscreen = SMA3.coordstoscreen(objX, objY)
    linkscreen = (objY&0xF)<<4 | objX&0xF
    if currentscreen == linkscreen or linkscreen > SMA3.Constants.maxscreen:
        return

    t.screenlink[linkscreen] = currentscreen

    if t.screenstatus[linkscreen] != 1:
        # set screen to enabled, but not included in screen count
        t.screenstatus[linkscreen] = 0xFB

    # this object is associated with the entire linked screen
    baseY = (objY&0xF)<<4
    baseX = (objX&0xF)<<4
    obj.tiles.update((x, y) for y in range(baseY, baseY+0x10) 
                            for x in range(baseX, baseX+0x10))
    obj.alltiles = obj.tiles.copy()

    # also, this object affects its entire current screen
    baseY = objY & 0xF0
    baseX = objX & 0xF0
    obj.alltiles.update((x, y) for y in range(baseY, baseY+0x10) 
                               for x in range(baseX, baseX+0x10))

def extFD(t, x, y):
    # display filler tile
    t.setTile(MultiTileID(0, 0x10EFD), x, y)

def extFEFF(t, objX, objY):  # disable screens in-game
    # display filler tile
    t.setTile(MultiTileID(t.getTile(objX, objY), 0x10E00 + t.obj.extID), objX, objY)
    # set screen to disabled
    t.screenstatus[SMA3.coordstoscreen(objX, objY)] = t.obj.extID

    # this object affects its entire screen
    baseY = objX & 0xF0
    baseX = objY & 0xF0
    t.obj.alltiles.update((x, y) for y in range(baseY, baseY+0x10) 
                                 for x in range(baseX, baseX+0x10))

# List of extended objects, indexed by ID
# Strings are placeholders for formulaic functions

extobjs = [
    "R","R","R","R","R","R","R","R",  # 00-07
    "R","R","R","R",ext0C,"R","R","S",   # 08-0F
    ext10,"R","R","R",ext14,ext15,ext16,"S",   # 10-17
    "R","R","R","R","R","R","R","R",   # 18-1F
    None,None,None,None,None,None,None,None,   # 20-27
    None,None,None,None,None,None,None,None,   # 28-2F
    ext30,"R","S","S","S","S","S","S",   # 30-37
    "S","S","S","S","S","S","S","S",   # 38-3F
    "S","S","S","S","S","S",ext46,"R",   # 40-47
    "R","R",ext4A,ext4B,"S","R","R","S",   # 48-4F
    ext50A8,"S",ext52,ext53,ext5455595C,ext5455595C,"R","R",   # 50-57
    "R",ext5455595C,"R","R",ext5455595C,"R","S","R",   # 58-5F
    "R","R","R","R","R","R","R",ext67,   # 60-67
    "S","S","R","R","R","R","R","R",   # 68-6F
    "R","R","R","R","R","R","R","R",   # 70-77
    "R","R","R","R","R","R","S","S",   # 78-7F
    "S","R","R","R","R","R","R","R",   # 80-87
    ext88,ext898A,ext898A,ext8B8C,ext8B8C,ext8D,"S","S",   # 88-8F
    "S","S","R","R","R","R","R","R",   # 90-97
    "R","R",ext9A9DB3,ext9A9DB3,ext9A9DB3,ext9A9DB3,ext9E9F,ext9E9F,   # 98-9F
    extA0A3,extA0A3,extA0A3,extA0A3,"R","R","R","S",   # A0-A7
    ext50A8,"R","R","R","R",extADB2,extADB2,extADB2,   # A8-AF
    extADB2,extADB2,extADB2,ext9A9DB3,extB4B7,extB4B7,extB4B7,extB4B7,   # B0-B7
    "R","R",extBABF,extBABF,extBABF,extBABF,extBABF,extBABF,   # B8-BF
    extC0,extC1,"R","R","S","R","R","R",   # C0-C7
    "R","R","S","S","S","S","S","S",   # C8-CF
    "S","S","S","S","R+","R+","R+","R+",   # D0-D7
    "R+","R+","R+","R+","R+","R+","R+","R+",   # D8-DF
    "R",None,None,None,None,None,None,None,   # E0-E7
    None,None,None,None,None,None,None,None,   # E8-EF
    None,None,None,None,None,None,None,None,   # F0-F7
    None,None,None,extFB,None,extFD,extFEFF,extFEFF,   # F8-FF
    ]

# Rectangular grid extended objects

def gen_extR(param, extD4DF=False) -> Callable:
    offsetX = param["x"] if "x" in param else 0
    offsetY = param["y"] if "y" in param else 0
    tiles = param["tiles"]
    width = param["w"] - 1
    height = param["h"] - 1

    if extD4DF:
        def extR(t, x, y):
            t.rect_iter_row(tiles, x + offsetX, y + offsetY, width, height)
            extD4DFgroundcheck(
                t, x + offsetX, (y + offsetY + height + 1) & 0x7F, width)
    else:
        def extR(t, x, y):
            t.rect_iter_row(tiles, x + offsetX, y + offsetY, width, height)
    return extR

for _extID, _param in extRdata.items():
    extobjs[_extID] = gen_extR(_param, 0xD4 <= _extID <= 0xDF)

# Single-tile extended objects

def gen_extS(tileID) -> Callable:
    def extS(t, x, y):
        t.setTile(tileID, x, y)
    return extS

for _extID, _tileID in extStiles.items():
    extobjs[_extID] = gen_extS(_tileID)

# Fallback functions for unused/unimplemented objects

def _genericextobjfunc(ID) -> Callable:
    return lambda t, x, y : t.setTile(0x10E00 + ID, x, y)

extcount = 0
for i in range(0x100):
    if extobjs[i] is None:
        extobjs[i] = _genericextobjfunc(i)
    else:
        extcount += 1
