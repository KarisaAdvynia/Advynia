"""SMA3 Layer 1 Tilemap: Sidebar Object Variants

Certain objects require overlapping another object to display properly.
These objects still need a sidebar preview, which may be tileset-specific.
As such, these functions were written to generate reasonable previews, with the
overlap-related code removed.

Functions are in the same format as in ExtendedObjects or StandardObjects.
"""

# standard library imports
##import itertools, random

# import from other files
from .Shared import *
from .ExtendedObjects import extobjs, gen_extR, gen_extS, ext88_pipebase
from .StandardObjects import (stdobjs, obj4F, obj53defaulttiles,
                              obj7Freplacecarved, obj9192, objC2C3tiles)

# override certain object functions, in copies of their lists
extobjs_alt = extobjs.copy()
stdobjs_alt = stdobjs.copy()

# extended object overrides can be created systematically
extRdata_alt = {
    0x88: {"w":4, "h":4, "tiles":ext88_pipebase},
    0x89: {"w":2, "h":1, "tiles":(0x851F, 0x8520)},
    0x8A: {"w":2, "h":1, "tiles":(0x8527, 0x8528)},
    0x8B: {"w":1, "h":2, "tiles":(0x852F, 0x8530)},
    0x8C: {"w":1, "h":2, "tiles":(0x8537, 0x8538)},
    0x9E: {"w":1, "h":2, "tiles":(0x8562, 0x8104)},
    0x9F: {"w":1, "h":2, "tiles":(0x8566, 0x8105)},
    }
for extID, param in extRdata_alt.items():
    extobjs_alt[extID] = gen_extR(param)

extStiles_alt = {
    0x67: 0xD0803,
    }
for extID, tileID in extStiles_alt.items():
    extobjs_alt[extID] = gen_extS(tileID)

# standard objects need customized functions
def alt4F(t, x0, y0, width, height):
    t.rect_single(t.dyn[0x1A04], x0-1, y0-1, width+2, height+2)
    obj4F(t, x0, y0, width, height)

def alt53(t, x0, y, width, _):
    parityX = 0
    for x, i in zip(t.xrange(x0, width), genseq_bordered(width+1, 0, 1, 2)):
        tileID = obj53defaulttiles[i]
        if i == 1:
            tileID += parityX
        t.setTile(tileID, x, y)
        parityX ^= 1

def alt7F(t, x0, y0, width, height):
    if width == 0: width = 1
    if height == 0: height = 1
    for (y, x), i in zip(itertools.product(t.yrange(y0, height),
                                           t.xrange(x0, width)),
                         gen_rectindex(width, height)):
        t.setTile(obj7Freplacecarved[i], x, y)

def alt91(t, x, y0, _, height):
    obj9192(t, x, y0, _, height)
    if t.fixver == 0:
        t.setTile(0xD0804, x, t.y_offset(y0, height))

def altB1(t, x0, y, width, _):
    for x in t.xrange(x0, width):
        t.setTile(0x1515, x, y)

def altBE(t, x, y0, _, height):
    ylist = list(t.yrange(y0, height))
    # first Y
    t.setTile(0x77C8, x, y0)
    if height > 1:
        # mid Y
        for y in ylist[1:-2]:
            t.setTile(0x8101, x, y) 
        # second-last Y
        y = ylist[-2]
        t.setTile(0x8103, x, y)
    if height != 0:
        # last Y
        y = ylist[-1]
        t.setTile(0x7805, x, y)

altC0C1tiles = {0xC0: (0x77C2,0x8200), 0xC1: (0x77C4,0x8300)}
def altC0C1(t, x0, y0, width, _):
    column = altC0C1tiles[t.obj.ID]
    y1 = t.y_offset(y0, 1)
    parity = 0
    for x in t.xrange(x0, width):
        t.setTile(column[0] + parity, x, y0)
        t.setTile(column[1] + parity, x, y1)
        parity ^= 1

def altC2C3(t, x0, y0, width, _):
    tile0, tile1, _ = objC2C3tiles[t.obj.ID]
    ygen = t.yrange(y0, abs(width)+1)
    y = next(ygen)
    for x in t.xrange(x0, width):
        t.setTile(tile0, x, y)
        y = next(ygen)
        t.setTile(tile1, x, y)

stdobjs_overrides = {
    0x4F: alt4F,
    0x53: alt53,
    0x7F: alt7F,
    0x91: alt91,
    0xB1: altB1,
    0xBE: altBE,
    0xC0: altC0C1, 0xC1: altC0C1, 
    0xC2: altC2C3, 0xC3: altC2C3, 
    }
for objID, func in stdobjs_overrides.items():
    stdobjs_alt[objID] = func
