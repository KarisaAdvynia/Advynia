"""SMA3 Layer 1 Tilemap
For generating layer 1 tilemaps from sublevel object data."""

if __name__ == "__main__":
    # allow testing as if it's from the Advynia main directory
    import os, sys
    os.chdir("../..")
    sys.path.append(".")

# standard library imports
import itertools
from collections.abc import Iterable, Mapping

# import from other files
from AdvGame import SMA3
from AdvGame.SMA3.ObjectFunctions import (
    MultiTileID, stdobjs, stdobjs_alt, extobjs, extobjs_alt, objcount, extcount)

# Range generators

def def_range_loop(bits=8):
    """Return a generator of a directional range (inclusive of both endpoints),
    based on how YI objects interpret their width/height.
    The output numbers are capped to the specified bit count."""

    bitmask = (1 << bits) - 1
    def func(start, dist):
        value = start & bitmask
        yield value
        if not dist:
            return
        elif dist > 0:
            for _ in range(dist):
                value = (value + 1) & bitmask
                yield value
        elif dist < 0:
            for _ in range(-dist):
                value = (value - 1) & bitmask
                yield value
    return func

range8_loop = def_range_loop(8)
range7_loop = def_range_loop(7)

# Define mappings for each tileset's dynamic tiles
# Forward map: Indexed by tileset ID, then by the lowest tile ID in the group.
#   Returns the dynamic tile ID used in that tileset.
# Reverse map: Indexed by tileset ID, then by the tile ID (for overlap checks).
#   Returns the corresponding key to the forward map, if any. Should only be
#   used with dict.get, to avoid KeyErrors.

dynmaps = []
dynmaps_rev = []
for tilesetID in range(0x10):
    forwardmap = {}
    reversemap = {}
    for highbyte, length, tiles in SMA3.Constants.objdyntable:
        base = highbyte << 8
        for i in range(length):
            forwardmap[base + i] = tiles[tilesetID] + i
            reversemap[tiles[tilesetID] + i] = base + i
    dynmaps.append(forwardmap)
    dynmaps_rev.append(reversemap)

# Error handling

class L1TilemapOverflowError(Exception):
    "Raised when an object tries to generate a tile out of bounds."
    def __init__(self, obj: SMA3.Object, x, y):
        self.obj = obj
        self.x = x
        self.y = y
        self.dir = [0, 0]  # direction of overflow
        if y >= 0x80:
            self.dir[1] = 1
        elif y < 0:
            self.dir[1] = -1
        if x > 0xFF:
            self.dir[0] = 1
        elif x < 0:
            self.dir[0] = -1

def errorobject(t, obj: SMA3.Object, offset: int = 0x11000):
    """Fallback object to ensure invalid-size or out-of-bounds objects are still
    editable. Out-of-bounds objects are displayed at the bottom of the sublevel.
    Generated tiles are red by default to emphasize the error, but can be blue
    by using offset 0x10000 instead."""
    try:
        y = min(obj.y, SMA3.Constants.maxtileY)
        if obj.ID == 0 and obj.extID is not None:
            t.setTile(offset + 0xE00 + obj.extID, obj.x, y)
        else:
            for y, x in itertools.product(t.yrange(obj.y, obj.height),
                                          t.xrange(obj.x, obj.width)):
                t.setTile(MultiTileID(t.getTile(x, y), offset + obj.ID), x, y)
    except L1TilemapOverflowError:
        pass

# Tilemap class

class L1Tilemap(list):
    """Grid of 16x16 tile IDs representing a sublevel's layer 1.
    Also stores which screens have in-game memory allocated for them.

    Valid loopsetting values, for if a tile would generate out of bounds:
    "crop": skip that tile
    "exception": abort by raising L1TilemapOverflowError
    "errortile": generate red error tile at object's location
    "loop": use 7-bit Y looping instead of 8-bit, to prevent out of bounds tiles
    """

    def __init__(self, sublevel: SMA3.Sublevel, loopsetting: str = "exception",
                 alt: bool = False, fixver: int = 0):
        self += ([0]*0x100 for y in range(0x80))

        self.screenstatus = [0]*0x80
        self.screenlink = {}
        self.loopsetting = loopsetting
        self.overflowerror = False
        self.fixver = fixver

        self.xrange = range8_loop
        if loopsetting == "loop":
            self.yrange = range7_loop
        else:
            self.yrange = range8_loop

        self.tileset = sublevel.header[1] & 0xF
        self.dyn = dynmaps[self.tileset]
        self.dynrev = dynmaps_rev[self.tileset]

        # determine which list of object functions to use
        if alt:
            # removes overlap code if it'd glitch the sidebar visuals
            self.extobjs = extobjs_alt
            self.stdobjs = stdobjs_alt
        else:
            # aims for accuracy to in-game object functions
            self.extobjs = extobjs
            self.stdobjs = stdobjs

        # process each object's code

        for obj in sublevel.objects:
            obj.tiles = set()
            obj.alltiles = set()
            obj.lasttile = None
            obj.error = None
            self.obj = obj

            try:
                if obj.ID == 0:
                    self.extobjs[obj.extID](self, obj.x, obj.y)
                else:
                    self.stdobjs[obj.ID](self, obj.x, obj.y, obj.width, obj.height)
                if obj.lasttile is None:
                    # object generated no selectable tiles
##                    print(f"Warning: Object {obj} generated no major tiles")
                    obj.error = "Error: Object generated no selectable tiles"
                    errorobject(self, obj, offset=0x10000)

            except (IndexError, KeyError, TypeError) as err:
                # object tilemap-constructing code failed, perhaps due to an
                #  invalid negative size?
                if __name__ == "__main__":
                    print(f"Object {obj} generation error!")
                    raise err
##                print(f"Warning: Object {obj} generation error!", type(err))
                obj.error = "Object code raised exception: " + type(err).__name__
                errorobject(self, obj)

            except L1TilemapOverflowError as err:
                self.overflowerror = True
                if loopsetting == "exception":
                    raise err
                elif loopsetting == "errortile":
                    ## include red error tile at the location of the object
                    ## if obj.y > SMA3.Constants.maxtileY, cap to maxtileY
                    NotImplemented

        self.obj = None

        # account for screen linking
        for linkscreen, currentscreen in self.screenlink.items():
            newX, newY = SMA3.screentocoords(linkscreen)
            oldX, oldY = SMA3.screentocoords(currentscreen)
            for y, x in itertools.product(range(0x10), range(0x10)):
                self[newY+y][newX+x] = int(self[oldY+y][oldX+x])

    # Informational functions

    def getTile(self, x, y) -> int:
        """Used for objects that check for pre-existing tile IDs. The game
        loops Y 7-bit when checking tiles, but 8-bit when writing tiles."""
        return int(self[y & 0x7F][x & 0xFF])

    def getdyn(self, x, y) -> int:
        """Used for objects that check for pre-existing dynamic tile IDs.
        Returns the index to self.dyn. Returns -1 instead of None as default,
        to allow for math comparisons on the result."""
        return self.dynrev.get(self.getTile(x, y), -1)

    def x_offset(self, x0, offset) -> int:
        """Return an x-value relative to the specified coordinate, after
        accounting for overflow."""
        return next(self.xrange(x0 + offset, 0))

    def y_offset(self, y0, offset) -> int:
        """Return a y-value relative to the specified coordinate, after
        accounting for overflow."""
        return next(self.yrange(y0 + offset, 0))

    def yrange_adj(self, y0, adjheight):
        """Alternate yrange generator that uses adjusted height as input,
        instead of raw height."""
        return self.yrange(y0, SMA3.Object._unadjlength(adjheight))

    # Screen-related functions

    def screencount(self) -> int:
        return sum(i in (1,0xFE,0xFF) for i in self.screenstatus)

    def enablescreen(self, screen: int):
        if self.screenstatus[screen] in (0, 0xFF):
            # clear all normal tiles on formerly-disabled screen when enabling it
            baseX, baseY = SMA3.screentocoords(screen)
            for y, x in itertools.product(range(baseY, baseY+0x10),
                                          range(baseX, baseX+0x10)):
                if isinstance(self[y][x], MultiTileID):
                    self[y][x] = MultiTileID(0, self[y][x].displayID)
                else:
                    self[y][x] = 0
        self.screenstatus[screen] = 1

    # Tilemap generation functions

    def setTile(self, tileID: int, x, y, priority=True, highlight=True):
        if priority:
            # check for overflow
            if y > SMA3.Constants.maxtileY or y < 0 or\
               x > SMA3.Constants.maxtileX or x < 0:
                if self.loopsetting in ("exception", "errortile"):
                    raise L1TilemapOverflowError(self.obj, x, y)
                return
        else:
            # in-game adjusted-generation tiles won't overflow
            y &= 0x7F
            x &= 0xFF

        screen = SMA3.coordstoscreen(x, y)

        # account for extFB
        if screen in self.screenlink:
            screen = self.screenlink[screen]
            y = screen&0xF0 | y&0xF
            x = ((screen&0xF)<<4) | x&0xF

        if priority:
            # screen is allocated, even if the game writes no tile to it
            self.enablescreen(screen)

        # update tiles affected by an object (for move forward/backward)
        self.obj.alltiles.add((x, y))

        # Advynia uses -1 to skip tiles, since 0 is a valid tile ID
        if tileID < 0:
            return

        # Advynia uses a high byte for extra tile properties
        highbyte = tileID >> 0x10
        if highbyte in (0xC, 0xD):  # load tile from dynamic table
            tileID = self.dyn[tileID & 0xFFFF]
            if highbyte == 0xC:  # dynamic + force disable highlight
                highlight = False
        elif highbyte == 0xA:  # force disable highlight
            highlight = False
            tileID &= 0xFFFF
        # high byte 1 (display numbered square) is processed with visuals

        # update tilemap
        self[y][x] = tileID

        if highlight:
            # tiles used for mouse interaction and dashed border
            self.obj.tiles.add((x, y))
            self.obj.lasttile = (x, y)

    def row_single(self, tileID: int, x0, y, width):
        "Generate a row of a single tile."
        for x in self.xrange(x0, width):
            self.setTile(tileID, x, y)

    def column_single(self, tileID: int, x, y0, height):
        "Generate a column of a single tile."
        for y in self.yrange(y0, height):
            self.setTile(tileID, x, y)

    def row_iter(self, tiles: Iterable[int], x0, y, width=0x100):
        """Generate a row of tiles from an iterable.
        Defaults to evaluating the entire iterable, if width is not specified."""
        for x, tileID in zip(self.xrange(x0, width), tiles):
            self.setTile(tileID, x, y)

    def column_iter(self, tiles: Iterable[int], x, y0, height=0x100):
        """Generate a column of tiles from an iterable.
        Defaults to evaluating the entire iterable, if height is not specified."""
        for y, tileID in zip(self.yrange(y0, height), tiles):
            self.setTile(tileID, x, y)

    def rect_single(self, tileID: int, x0, y0, width, height):
        "Generate a rectangle of a single tile."   
        for x, y in itertools.product(self.xrange(x0, width),
                                      self.yrange(y0, height)):
            self.setTile(tileID, x, y)

    def rect_iter_row(self, tiles: Iterable[int], x0, y0, width, height):
        """Generate a rectangle of tiles from an iterable, filling one row
        at a time."""
        tile_iter = iter(tiles)
        for y, x in itertools.product(self.yrange(y0, height),
                                      self.xrange(x0, width)):
            self.setTile(next(tile_iter), x, y)

    def rect_iter_column(self, tiles: Iterable[int], x0, y0, width, height):
        """Generate a rectangle of tiles from an iterable, filling one column
        at a time."""
        tiles = iter(tiles)
        for x, y in itertools.product(self.xrange(x0, width),
                                      self.yrange(y0, height)):
            self.setTile(next(tiles), x, y)

    def lookup_replace(self, mapping: Mapping[int, int], x, y, default=None,
                       dynamic=False, *, priority=True, highlight=True):
        """Use a mapping, with tile IDs as keys, to replace the tile at a
        specified coordinate."""
        tileID = mapping.get(self.getdyn(x, y) if dynamic
                             else self.getTile(x, y), default)
        if tileID is not None:
            self.setTile(tileID, x, y, priority, highlight)

######## Test code

if __name__ == "__main__":
    print("Object code implemented: "
          f"Total {objcount + extcount}/465, "
          f"Extended {extcount}/213, "
          f"Standard {objcount}/252")
    t = L1Tilemap(SMA3.Sublevel.importbyID("../sma3.gba", 0x43))
