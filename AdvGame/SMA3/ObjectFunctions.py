"""SMA3 Object Functions
For generating layer 1 tilemaps from sublevel object data."""

# standard library imports
import itertools, random

if __name__ == "__main__":
    # allow testing as if it's from the Advynia main directory
    import os, sys
    os.chdir("../..")
    sys.path.append(".")

# import from other files
from AdvGame import SMA3
from AdvGame.SMA3 import ObjectExtraData

class L1Tilemap(list):
    """Grid of 16x16 tile IDs representing a sublevel's layer 1.
    Also stores which screens have in-game memory allocated for them."""
    def __init__(self):
        self += ([0]*0x100 for y in range(0x80))

        self.screens = [0]*0x80

    def screencount(self):
        return sum(i in (1,0xFE,0xFF) for i in self.screens)

class L1TilemapOverflowError(Exception):
    "Raised when an object tried to generate a tile out of bounds."
    def __init__(self, obj, x, y):
        self.obj = obj
        self.x = x
        self.y = y
        self.dir = [0, 0]  # direction of overflow
        if 0x80 <= self.y < 0xC0:
            self.dir[1] = 1
        elif 0xC0 <= self.y <= 0xFF:
            self.dir[1] = -1

class L1Constructor:
    """This constructor is only intended to be used once per instance.
    After creating it, retrieve the tilemap attribute.
    For example:
    SMA3L1Constructor(sublevel).tilemap"""
    def __init__(self, sublevel, allowYoverflow=False):
        self.tilemap = L1Tilemap()
        self.tileset = sublevel.header[1]
        self.screenlink = {}
        self.allowYoverflow = allowYoverflow

        # process each object's code
        for obj in sublevel.objects:
            obj.tiles = set()
            obj.alltiles = set()
            obj.lasttile = None
            self.obj = obj
            self.x = obj.x
            self.y = obj.y
            self.relX = 0
            self.relY = 0
            try:
                if obj.ID == 0:
                    L1Constructor.SMA3objectcode[0][obj.extID](self)
                else:
                    L1Constructor.SMA3objectcode[obj.ID](self,
                        obj.adjwidth, obj.adjheight)
                if obj.lasttile is None:
                    # object generated no major tiles
                    if obj.ID != 0x7F:
                        print("Warning: Object", obj, "generated no major tiles")
                    self.errorobject()
            except (IndexError, KeyError, TypeError) as err:
                # object tilemap-constructing code failed, perhaps due to an
                #  invalid negative size?
                if __name__ == "__main__":
                    raise err
                print("Warning: Object", obj, "generation error!", type(err))
                self.errorobject()

        # account for screen linking
        for linkscreen, currentscreen in self.screenlink.items():
            newX, newY = SMA3.screentocoords(linkscreen)
            oldX, oldY = SMA3.screentocoords(currentscreen)
            for y in range(0x10):
                for x in range(0x10):
                    if self.tilemap[oldY+y][oldX+x] not in (
                            0x10EFB,0x10EFD,0x10EFE,0x10EFF):
                        self.tilemap[newY+y][newX+x] =\
                            self.tilemap[oldY+y][oldX+x]

    def errorobject(self):
        """Fallback object to ensure invalid-size objects are still editable.
        Generated tiles are red to emphasize the error."""
        self.x = self.obj.x
        self.y = self.obj.y
        self.relX = 0
        self.relY = 0
        try:
            if self.obj.ID == 0 and self.obj.extID is not None:
                self.setTile(0x11E00+self.obj.extID)
            else:
                self.setRect(0x11000+self.obj.ID,
                             self.obj.adjwidth, self.obj.adjheight)
        except L1TilemapOverflowError:
            pass

    ## Methods to be called by object functions

    def setTile(self, tile, major=True):
        """The main recursive function called by object functions. Any
        function passed to setTile should call setTile within it.

        Major tiles are used for mouse interaction, usually corresponding to
        the object's rectangle, while minor tiles include decorations that
        extend outside the rectangle."""
        if isinstance(tile, tuple):
            # single tile, dynamic: convert to static
            tile = self.dynamicshift(tile[0]) + tile[1]

        if isinstance(tile, int):
            # single tile, static
            x = (self.x + self.relX) & 0xFF  # account for 8-bit overflow
            y = (self.y + self.relY) & 0xFF

##            # overlap debug: display tiles written
##            if self.obj.ID == 0x52:
##                print(self.obj, "x", self.relX, "y", self.relY, hex(tile))

            if y > 0x7F:
                if not self.allowYoverflow:
                    # custom exception bypasses the tilemap's error handling,
                    #  used to prevent insert/move/resize out of bounds
                    raise L1TilemapOverflowError(self.obj, x, y)
                return

            screen = y&0xF0 | x>>4

            # account for extFB
            if screen in self.screenlink:
                screen = self.screenlink[screen]
                y = screen&0xF0 | y&0xF
                x = ((screen&0xF)<<4) | x&0xF

            # screen is allocated, even if the game writes no tile to it
            self.tilemap.screens[screen] = 1

            # Advynia uses -1 to skip tiles, since 0 is a valid tile ID
            if tile < 0:
                return

            # update tilemap
            self.tilemap[y][x] = tile
            self.obj.alltiles.add((x, y))  # tiles affected by an object
            if major:
                self.obj.tiles.add((x, y))  # tiles associated with an object
                self.obj.lasttile = (x, y)

        else:
            # recursive function
            tile()

    def shifthoriz(self, slope=0):
        "YI's horizontal shift. Accounts for signed widths and sloped objects."
        if self.obj.adjwidth > 0:
            self.relX += 1
        else:
            self.relX -= 1
        self.y -= slope

    def shiftvert(self):
        "YI's vertical shift. Accounts for signed heights."
        if self.obj.adjheight > 0:
            self.relY += 1
        else:
            self.relY -= 1

    def resetX(self):
        self.relX = 0
    def resetY(self):
        self.relY = 0

    def setLine(self, tile, shift, length,
                first=None, last=None, length1=None,
                finalshift=None, major=True):
        """Generate a line of tiles, in an arbitrary direction specified by
        the provided shift function.
        A custom first and last tile can be provided. If length==1, precedence
        is length1 > first > last > tile.
        When nesting this function to create a rectangle, set finalshift to
        resetX or resetY."""
        for i in range(abs(length)):
            if length1 is not None and length == 1:
                self.setTile(length1, major)
            elif i == 0 and first is not None:
                self.setTile(first, major)
            elif i == abs(length)-1 and last is not None:
                self.setTile(last, major)
            else:
                self.setTile(tile, major)
            shift()
        if finalshift:
            finalshift()

    def setRect(self, tiles, width, height, major=True):
        """Generate a rectangle of tiles, filling one row at a time.
        A single tile or looping sequence of tiles can be provided."""
        startrelX = self.relX
        width = abs(width)
        size = abs(width*height)
        try:
            tiles[0]
        except TypeError:
            # not a sequence: single tile or function
            tileiter = itertools.repeat(tiles)
        else:
            tileiter = itertools.cycle(tiles)
        
        for i in range(size):
            self.setTile(next(tileiter), major)
            if i % width == width-1:
                self.relX = startrelX
                self.shiftvert()
            else:
                self.shifthoriz()

    def setColumn(self, tiles, height, default=-1, majorthreshold=0):
        """Specialized variant of setLine for a frequent vanilla pattern:
        a sequence of specific surface tiles followed by a default tile.

        Resets relY after finishing.
        majorthreshold: first row number that uses major tiles"""
        startrelY = self.relY
        major = False
        for row in range(abs(height)):
            if row >= majorthreshold:
                major = True
            try:
                self.setTile(tiles[row], major)
            except IndexError:
                self.setTile(default, major)
            self.shiftvert()
        self.relY = startrelY

    def setBorderRect(self, width, height, tile3x3,
                      tile1row=None, tile1col=None, tile1x1=None):
        """Generate a rectangle of bordered tiles, with compatibility for
        width and height 1. Requires 16 tile inputs:
        tile3x3: default sequence of 9 tiles (3 each in first/default/last row),
        tile1row: sequence of 3 tiles (first/default/last), used if height 1,
        tile1col: sequence of 3 tiles (first/default/last), used if width 1,
        tile1x1: single tile, used only if 1x1"""
        if tile1row:
            def _length1():
                self.setLine(
                    first=tile1row[0], tile=tile1row[1], last=tile1row[2],
                    length1=tile1x1,
                    length=width, shift=self.shifthoriz, finalshift=self.resetX)
        else:
            _length1 = None
        if not tile1col:
            tile1col = [None]*3

        def _first():
            self.setLine(
                first=tile3x3[0], tile=tile3x3[1], last=tile3x3[2],
                length1=tile1col[0],
                length=width, shift=self.shifthoriz, finalshift=self.resetX)
        def _main():
            self.setLine(
                first=tile3x3[3], tile=tile3x3[4], last=tile3x3[5],
                length1=tile1col[1],
                length=width, shift=self.shifthoriz, finalshift=self.resetX)
        def _last():
            self.setLine(
                first=tile3x3[6], tile=tile3x3[7], last=tile3x3[8],
                length1=tile1col[2],
                length=width, shift=self.shifthoriz, finalshift=self.resetX)
        self.setLine(first=_first, tile=_main, last=_last, length1=_length1,
                        shift=self.shiftvert, length=height)

    def parityX(self):
        return self.relX&1
    def parityY(self):
        return self.relY&1
    def parityYX(self):
        return (self.relY&1) << 1 | self.relX&1

    def getTile(self, offsetX=0, offsetY=0):
        # the game loops Y when retrieving an adjacent tile, but not when
        #  writing tiles
        x = (self.x + self.relX + offsetX) & 0xFF
        y = (self.y + self.relY + offsetY) & 0x7F
        return self.tilemap[y][x]

    def simpleoverlap(self, default, checktile, alttile, major=True):
        "If a specific existing tile is detected, generate an alternate tile."
        if self.getTile() == checktile:
            self.setTile(alttile, major)
        else:
            self.setTile(default, major)

    def dynamicshift(self, highbyte):
        return ObjectExtraData.dynamictable[highbyte][self.tileset & 0xF]

    ## Define extended object functions

    # Rectangular grid extended objects

    extRtiles = {
        0x00:{"w":2, "h":3,
              "tiles":(0x9600,0x9601,0x9610,0x9611,  -1,  0x920D)},
        0x01:{"w":2, "h":3,
              "tiles":(0x967D,0x967E,0x967B,0x967C,0x920C,  -1  )},
        0x02:{"w":2, "h":3,
              "tiles":(  -1,    -1,  0x9606,0x9607,0x9208,0x920C)},
        0x03:{"w":2, "h":3,
              "tiles":(  -1,    -1,  0x9604,0x9605,0x920D,0x920E)},
        0x04:{"w":1, "h":3, "tiles":(  -1,  0x967A,0x920D)},
        0x05:{"w":1, "h":3, "tiles":(  -1,  0x9618,0x920C)},
        0x06:{"w":1, "h":3, "tiles":(  -1,  0x967F,0x920B)},
        0x07:{"w":1, "h":3, "tiles":(  -1,  0x9612,0x920A)},
        0x08:{"w":3, "h":3,
              "tiles":(  -1,  0x9604,0x9605,0x9613,0x9614,0x9615,0x9208,0x9209,0x920A)},
        0x09:{"w":2, "h":3,
              "tiles":(0x9606,0x9607,0x9616,0x9617,0x920B,0x920C,  -1  )},
        0x0A:{"w":2, "h":2, "tiles":(0x9096,0x9097,0x90A6,0x90A7)},
        0x0B:{"w":2, "h":2, "tiles":(0x907C,0x9095,0x90A4,0x90A5)},
        0x0D:{"w":8, "h":0x10, "tiles":(
            0x9D84,0x9D85,0x9D84,0x9D85,0x9D84,0x9D85,0x9D84,0x9D85,
            0x9D86,0x9D87,0x9D86,0x9D87,0x9D86,0x9D87,0x9D86,0x9D87,
            0x9684,0x9685,0x9686,0x9687,0x9688,0x9689,0x968A,0x968B,
            0x968C,0x968D,0x968E,0x968F,0x9690,0x9691,0x9692,0x9693,
            0x9696,0x9697,0x9698,0x9699,0x969A,0x969B,0x969C,0x969D,
            0x96A0,0x96A1,-1,-1,-1,-1,-1,-1,
            0x96A6,0x96A7,-1,-1,-1,-1,-1,-1,
            0x96AA,0x96AB,-1,-1,-1,-1,-1,-1,
            0x96AE,0x96AF,-1,-1,-1,-1,-1,-1,
            0x96B2,0x96B3,-1,-1,-1,-1,-1,-1,
            0x96B6,0x96B7,-1,-1,-1,-1,-1,-1,
            0x9684,0x9685,-1,-1,-1,-1,-1,-1,
            0x9D93,0x9D94,0x9D95,0x9D8C,0x9D8D,0x9D8E,0x9D8F,0x9D92,
            0x9D97,0x9D98,0x9D99,0x9D96,0x9D90,0x9D91,0x9D99,0x9D96,
            0x9D89,0x9D88,0x9D89,0x9D88,0x9D89,0x9D88,0x9D89,0x9D88,
            0x9D8A,0x9D8A,0x9D8A,0x9D8A,0x9D8A,0x9D8A,0x9D8A,0x9D8A)},
        0x0E:{"w":8, "h":0x10, "tiles":(
            0x9D84,0x9D85,0x9D84,0x9D85,0x9D84,0x9D85,0x9D84,0x9D85,
            0x9D86,0x9D87,0x9D86,0x9D87,0x9D86,0x9D87,0x9D86,0x9D87,
            0x9684,0x9685,0x96A2,0x96A5,0x96BA,0x96BB,0x96BC,0x96BD,
            0x9694,0x9695,0x96BE,0x96BF,0x96C0,0x96C1,0x96C2,0x96C3,
            0x969E,0x969F,0x96C4,0x96C5,0x96C6,0x96C7,0x96C8,0x96C9,
            0x96A3,0x96A4,-1,-1,-1,-1,-1,-1,
            0x96A8,0x96A9,-1,-1,-1,-1,-1,-1,
            0x96AC,0x96AD,-1,-1,-1,-1,-1,-1,
            0x96B0,0x96B1,-1,-1,-1,-1,-1,-1,
            0x96B4,0x96B5,-1,-1,-1,-1,-1,-1,
            0x96B8,0x96B9,-1,-1,-1,-1,-1,-1,
            0x9684,0x9685,-1,-1,-1,-1,-1,-1,
            0x9D93,0x9D94,0x9D95,0x9D8C,0x9D8D,0x9D8E,0x9D8F,0x9D92,
            0x9D97,0x9D98,0x9D99,0x9D96,0x9D90,0x9D91,0x9D99,0x9D96,
            0x9D89,0x9D88,0x9D89,0x9D88,0x9D89,0x9D88,0x9D89,0x9D88,
            0x9D8A,0x9D8A,0x9D8A,0x9D8A,0x9D8A,0x9D8A,0x9D8A,0x9D8A)},
        0x11:{"w":2, "h":1, "tiles":(0x7797,0x7798)},
        0x12:{"w":5, "h":1, "tiles":(0x96D1,0x96D1,0x96D1,0x96D2,0x96D2)},
        0x13:{"w":5, "h":1, "tiles":(0x96D3,0x96D3,0x96D1,0x96D1,0x96D1)},
        0x18:{"w":0x10, "h":0x10, "tiles":ObjectExtraData.ext18tiles},
        0x19:{"w":0x18, "h":3, "tiles":(
            0x9D65,0x9D6B,0x9D66,0x9D6C,0x9D71,0x9D6A,(0x0C,1),(0x0D,1),
            0x9D6B,0x9D6D,(0x0F,2),(0x10,0),0x9D70,0x9D65,0x9D6B,0x9D6D,
            (0x0F,2),(0x10,0),(0x0C,1),(0x0D,1),0x9D66,0x9D6C,0x9D71,0x9D6A,
            0x9D6E,0x9D72,0x9D6E,0x9D73,0x9D7B,-1,0x9D7C,0x9D69,
            0x9D6E,0x9D73,0x9D74,0x9D75,0x9D76,0x9D72,0x9D6E,0x9D73,
            0x9D74,0x9D75,0x9D7C,0x9D69,0x9D6E,0x9D67,0x9D6F,0x9D72,
            0x9D67,0x9D6F,0x9D67,0x9D77,0x9D78,0x9D68,0x9D7D,0x9D7E,
            0x9D67,0x9D77,0x9D78,0x9D68,0x9D79,0x9D7A,0x9D67,0x9D77,
            0x9D78,0x9D68,0x9D7D,0x9D7E,0x9D72,0x9D6E,0x9D67,0x9D6F)},
        0x1A:{"w":0x20, "h":0xA, "tiles":ObjectExtraData.ext1Atiles},
        0x1B:{"w":2, "h":2, "tiles":(  -1,  0xA55E,0xA561,0xA562)},
        0x1C:{"w":2, "h":2, "tiles":(  -1,  0xA55F,0xA563,0xA564)},
        0x1D:{"w":2, "h":2, "tiles":(  -1,  0xA560,0xA565,0xA566)},
        0x1F:{"w":4, "h":4,
              "tiles":(0x96CA,0x96CB,0x96CF,0x96D0,
                       0x96CC,0x96CD,0x96CD,0x96CE,
                       0x96CD,0x96CD,0x96CD,0x96CD,
                       0x96CD,0x96CD,0x96CD,0x96CD)},
        0x47:{"w":4, "h":4, "y":-3,
              "tiles":(  -1,  0x3D18,0x3D19,  -1,  
                       0x3D1A,0x3D1B,0x3D1C,0x3D1D,
                       0x3D1E,0x3D26,0x3D27,0x3D21,
                       0x3D22,0x6300,0x3D28,0x3D25)},
        0x49:{"w":3, "h":1, "x":-1, "tiles":(0x3D4D,0x3D4E,0x3D4F)},
        0x4D:{"w":2, "h":2, "tiles":(0x0080,0x0081,0x014B,0x014C)},
        0x4E:{"w":1, "h":2, "tiles":(0x0082,0x000C)},
        0x56:{"w":5, "h":3,
              "tiles":(0x3D8F,0x3D90,0x3D91,0x3D92,  -1  ,
                       0x3D93,0x3D94,0x3D95,0x3D96,0x3D7C,
                         -1  ,0x3D8C,0x3D8D,0x3D8E,0x3D7B)},
        0x57:{"w":5, "h":3,
              "tiles":(  -1  ,0x3D81,0x3D82,0x3D83,0x3D84,
                       0x3D79,0x3D85,0x3D86,0x3D87,0x3D88,
                       0x3D7A,0x3D89,0x3D8A,0x3D8B,  -1  )},
        0x58:{"w":3, "h":2,
              "tiles":(  -1  ,0x3D80,0x3DA6,  -1  ,0x3D7F,  -1  )},
        0x5A:{"w":3, "h":2,
              "tiles":(0x3D9D,0x3D9E,  -1  ,0x3D9B,0x3D9C,0x3D72)},
        0x5B:{"w":3, "h":2,
              "tiles":(0x3DA5,0x3D7D,  -1  ,  -1  ,0x3D7E,  -1  )},
        0x5D:{"w":3, "h":2,
              "tiles":(  -1  ,0x3D97,0x3D98,0x3D71,0x3D99,0x3D9A)},
        0x5F:{"w":4, "h":2,
              "tiles":((0x02,1),(0x0F,1),(0x10,1),  -1,  
                       (0x03,2),0x01A8,0x01B0,(0x0A,2))},
        0x60:{"w":5, "h":3,
              "tiles":(  -1,  (0x08,1),(0x0F,1),(0x10,1),  -1,  
                       (0x02,1),0x01B1,0x01B2,0x01B3,(0x05,1),
                       (0x03,2),0x01B4,0x01B5,0x01B6,(0x06,2))},
        0x61:{"w":3, "h":2,
              "tiles":((0x02,1),0x01A7,(0x0A,1),(0x03,2),0x01A8,0x01A9)},
        0x62:{"w":3, "h":2,
              "tiles":((0x02,1),0x01A7,(0x05,1),(0x03,2),0x01A8,(0x06,1))},
        0x63:{"w":5, "h":4,
              "tiles":(  -1,  (0x02,1),(0x0F,1),(0x10,1),  -1,  
                         -1,  (0x03,1),0x01AA,0x01AB,  -1,  
                       (0x02,1),0x01B1,0x01B2,0x01AC,(0x05,1),
                       (0x03,2),0x01B4,0x01B5,0x01AD,(0x06,2))},
        0x64:{"w":5, "h":4,
              "tiles":(  -1,  (0x02,1),0x01A7,(0x0A,1),  -1,  
                         -1,  (0x03,1),0x01AA,0x01AB,  -1,  
                       (0x02,1),0x01B1,0x01B2,0x01AC,(0x05,1),
                       (0x03,2),0x01B4,0x01B5,0x01AD,(0x06,2))},
        0x65:{"w":4, "h":3,
              "tiles":(  -1,  (0x08,1),(0x0A,1),  -1,  
                       (0x02,1),0x01B1,0x01B3,(0x05,1),
                       (0x03,2),0x01AE,0x01B6,(0x06,2))},
        0x66:{"w":2, "h":2,
              "tiles":((0x02,1),(0x0A,1),(0x03,2),0x01A9,)},
        0x6A:{"w":3, "h":2,
              "tiles":(0x776A,0x776B,0x776C,0x01CB,0x01D0,0x01CF)},
        0x6B:{"w":4, "h":3,
              "tiles":(0x7760,0x7761,0x7763,0x7764,
                       0x7765,0x7766,0x7768,0x7769,
                       0x01CB,0x01CC,0x01CE,0x01CF)},
        0x6C:{"w":5, "h":3,
              "tiles":(0x7760,0x7761,0x7762,0x7763,0x7764,
                       0x7765,0x7766,0x7767,0x7768,0x7769,
                       0x01CB,0x01CC,0x01CD,0x01CE,0x01CF)},
        0x6D:{"w":2, "h":2, "tiles":range(0x7D14, 0x7D18)},
        0x6E:{"w":2, "h":2, "tiles":range(0x7D18, 0x7D1C)},
        0x6F:{"w":2, "h":2, "tiles":range(0x7D0C, 0x7D10)},
        0x70:{"w":2, "h":2, "tiles":range(0x7D10, 0x7D14)},
        0x71:{"w":6, "h":1,
              "tiles":(0x791E,0x0A2F,0x77BB,0x77BA,0x082D,0x791D)},
        0x72:{"w":6, "h":1,
              "tiles":(0x792E,0x5D09,0x77B9,0x77CC,0x5B0D,0x792D)},
        0x73:{"w":1, "h":6,
              "tiles":(0x792D,0x5B0C,0x77C9,0x77BA,0x082D,0x791D)},
        0x74:{"w":1, "h":6,
              "tiles":(0x792E,0x5D09,0x77B9,0x77CA,0x0A2E,0x791E)},
        0x75:{"w":2, "h":4,
              "tiles":(0x7917,0x7918,
                       0x77B1,  -1,  
                       0x77B4,  -1,  
                       0x7927,0x7928)},
        0x76:{"w":2, "h":4,
              "tiles":(0x7919,0x791A,
                         -1,  0x77B5,
                         -1,  0x77B8,
                       0x7929,0x792A)},
        0x77:{"w":2, "h":6,
              "tiles":(0x7917,0x7918,
                       0x77B1,  -1,  
                       0x77B2,  -1,  
                       0x77B3,  -1,  
                       0x77B4,  -1,  
                       0x7927,0x7928)},
        0x78:{"w":2, "h":6,
              "tiles":(0x7919,0x791A,
                         -1,  0x77B5,
                         -1,  0x77B6,
                         -1,  0x77B7,
                         -1,  0x77B8,
                       0x7929,0x792A)},
        0x79:{"w":4, "h":2,
              "tiles":(0x7911,0x77A1,0x77A4,0x7912,
                       0x7921,  -1,    -1,  0x7922)},
        0x7A:{"w":4, "h":2,
              "tiles":(0x7913,  -1,    -1,  0x7914,
                       0x7923,0x77A5,0x77A8,0x7924,)},
        0x7B:{"w":6, "h":2,
              "tiles":(0x7911,0x77A1,0x77A2,0x77A3,0x77A4,0x7912,
                       0x7921,  -1,    -1,    -1,    -1,  0x7922)},
        0x7C:{"w":6, "h":2,
              "tiles":(0x7913,  -1,    -1,    -1,    -1,  0x7914,
                       0x7923,0x77A5,0x77A6,0x77A7,0x77A8,0x7924)},
        0x7D:{"w":2, "h":1, "tiles":(0x77C6,0x77C7)},
        0x81:{"w":4, "h":1, "tiles":range(0x6F00, 0x6F04)},
        0x82:{"w":8, "h":5, "y":-4, "tiles":(
            0x8400,0x8401,0x8402,0x8403,0x8401,0x8402,0x8404,0x8405,
            0x840C,0x840D,0x840E,0x840F,0x840E,0x840D,0x8411,0x8412,
            0x8406,0x8407,0x8406,0x8407,0x8406,0x8407,0x8406,0x8407,
            0x8408,0x8409,0x840A,0x840B,0x8408,0x8409,0x840A,0x840B,
            0x840A,0x840B,0x840A,0x840B,0x8408,0x8409,0x8408,0x8409)},
        0x83:{"w":0x20, "h":0x16, "y":-9, "tiles":ObjectExtraData.ext83tiles},
        0x84:{"w":0x13, "h":0x0B, "y":-5, "tiles":ObjectExtraData.ext84tiles},
        0x85:{"w":0x0A, "h":7, "y":-3,
              "tiles":(-1,-1,-1,-1,0x84AF,
                           0x84AF,-1,-1,-1,-1,
                       -1,-1,0x8415,0x8426,0x8414,
                           0x84B5,0x842D,0x84AF,-1,-1,
                       -1,0x8426,0x8419,(0x0C,0),(0x0D,0),(0x38,0),
                           (0x0A,4),0x8414,0x842D,-1,
                       0x845B,(0x08,2),(0x38,0),0x8434,0x8434,
                           0x8434,0x8434,(0x0F,0),(0x10,2),0x8466,
                       -1,0x8451,0x8487,0x8434,0x8434,
                           0x845E,0x848E,0x8437,0x84A4,0x842F,
                       -1,-1,0x8451,0x8487,0x848E,
                           0x8437,0x8447,0x842A,0x842B,0x8493,
                       -1,-1,-1,0x84A8,0x84A6,
                           0x84AC,0x84AD,0x84A8,0x84AD,-1)},
        0x86:{"w":8, "h":7, "y":-3, "tiles":(
              -1,    -1,    -1,    -1,    -1,  0x84AF,  -1,    -1,  
              -1,    -1,  0x8415,0x8416,0x8426,0x8414,0x842D,  -1,  
              -1,  0x8426,0x8419,0x84B4,0x8427,0x8434,0x8465,0x8466,
            0x845B,(0x0C,2),(0x0D,0),(0x38,0),(0x38,0),(0x0F,0),(0x10,4),0x8475,
              -1,  0x8451,0x8497,0x8434,0x8482,0x8490,0x84A3,0x842F,
              -1,    -1,  0x8451,0x84A5,0x8423,0x849E,0x849F,0x8493,
              -1,    -1,    -1,  0x84A8,0x84A9,0x84AC,0x84AD,  -1,  
            )},
        0x87:{"w":0x0D, "h":8, "y":-3, "tiles":(ObjectExtraData.ext87tiles)},
        0x92:{"w":2, "h":2, "tiles":(0x8714,0x8715,0x8718,  -1  )},
        0x93:{"w":2, "h":2, "tiles":(0x8716,0x8717,  -1,  0x8719)},
        0x94:{"w":2, "h":2, "tiles":(0x871E,  -1,  0x871A,0x871B)},
        0x95:{"w":2, "h":2, "tiles":(  -1,  0x871F,0x871C,0x871D)},
        0x96:{"w":8, "h":8, "tiles":(
              -1,    -1,    -1,    -1,  0x8720,0x8721,0x8722,0x8723,
              -1,    -1,  0x8724,0x8725,0x8726,  -1,    -1,    -1,  
              -1,  0x8727,0x8728,  -1,    -1,    -1,    -1,    -1,  
              -1,  0x8729,  -1,    -1,    -1,    -1,    -1,    -1,  
            0x872A,0x872B,  -1,    -1,    -1,    -1,    -1,    -1,  
            0x872C,  -1,    -1,    -1,    -1,    -1,    -1,    -1,  
            0x872D,  -1,    -1,    -1,    -1,    -1,    -1,    -1,  
            0x872E,  -1,    -1,    -1,    -1,    -1,    -1,    -1  )},
        0x97:{"w":8, "h":8, "tiles":(
            0x874B,0x874C,0x874D,0x874E,  -1,    -1,    -1,    -1,  
              -1,    -1,    -1,  0x8748,0x8749,0x874A,  -1,    -1,  
              -1,    -1,    -1,    -1,    -1,  0x8746,0x8747,  -1,  
              -1,    -1,    -1,    -1,    -1,    -1,  0x8745,  -1,  
              -1,    -1,    -1,    -1,    -1,    -1,  0x8743,0x8744,
              -1,    -1,    -1,    -1,    -1,    -1,    -1,  0x8742,
              -1,    -1,    -1,    -1,    -1,    -1,    -1,  0x8741,
              -1,    -1,    -1,    -1,    -1,    -1,    -1,  0x8740)},
        0x98:{"w":8, "h":8, "tiles":(
            0x873E,  -1,    -1,    -1,    -1,    -1,    -1,    -1,  
            0x873D,  -1,    -1,    -1,    -1,    -1,    -1,    -1,  
            0x873C,  -1,    -1,    -1,    -1,    -1,    -1,    -1,  
            0x873A,0x873B,  -1,    -1,    -1,    -1,    -1,    -1,  
              -1,  0x8739,  -1,    -1,    -1,    -1,    -1,    -1,  
              -1,  0x8737,0x8738,  -1,    -1,    -1,    -1,    -1,  
              -1,    -1,  0x8734,0x8735,0x8736,  -1,    -1,    -1,  
              -1,    -1,    -1,    -1,  0x8730,0x8731,0x8732,0x8733)},
        0x99:{"w":8, "h":8, "tiles":(
              -1,    -1,    -1,    -1,    -1,    -1,    -1,  0x8750,
              -1,    -1,    -1,    -1,    -1,    -1,    -1,  0x8751,
              -1,    -1,    -1,    -1,    -1,    -1,    -1,  0x8752,
              -1,    -1,    -1,    -1,    -1,    -1,  0x8753,0x8754,
              -1,    -1,    -1,    -1,    -1,    -1,  0x8755,  -1,  
              -1,    -1,    -1,    -1,    -1,  0x8756,0x8757,  -1,  
              -1,    -1,    -1,  0x8758,0x8759,0x875A,  -1,    -1,  
            0x875B,0x875C,0x875D,0x875E,  -1,    -1,    -1,    -1  )},
        0x9A:{"w":1, "h":2, "y":-1, "tiles":(0x0006,0x872F)},
        0x9B:{"w":1, "h":2, "y":-1, "tiles":(0x0007,0x873F)},
        0x9C:{"w":2, "h":1, "x":-1, "tiles":(0x0008,0x874F)},
        0x9D:{"w":2, "h":1, "x":-1, "tiles":(0x0009,0x875F)},
        0xA4:{"w":2, "h":2, "tiles":(0x000A,0x000B,0x8800,0x8801)},
        0xA5:{"w":5, "h":9, "x":-2, "y":-8, 
              "tiles":(  -1,    -1,  0x3DDE,  -1,    -1,  
                         -1,  0x3DDF,0x8B04,0x3DE0,  -1,  
                         -1,  0x8B0A,0x8B01,0x8B0C,  -1,  
                       0x3DE1,0x8B07,0x8B08,0x8B09,  -1,  
                       0x3DE2,0x8B0E,0x8B0F,0x8B10,0x3DE3,
                       0x8B02,0x8B0B,0x8B15,0x8B16,0x8B0C,
                       0x8B12,0x8B19,0x8B1A,0x8B1B,0x8B14,
                         -1,    -1,  0x3DE4,  -1,    -1,  
                         -1,    -1,  0x6A25,  -1,    -1,  )},
        0xA6:{"w":3, "h":5, "x":-1, "y":-4,
              "tiles":(  -1,  0x3DDE,  -1,  
                       0x3DDF,0x8B04,0x3DE0,
                       0x8B0A,0x8B0B,0x8B0C,
                       0x8B12,0x8B13,0x8B14,
                         -1,  0x6A24,  -1,  )},
        0xA9:{"w":1, "h":5, "tiles":(0x799D,0x8E00,0x8E01,0x8E02,0x8D95)},
        0xAA:{"w":1, "h":4, "tiles":(0x799D,0x8E01,0x8E02,0x8D95)},
        0xAB:{"w":1, "h":3, "tiles":(0x799D,0x8E02,0x8D95)},
        0xAC:{"w":1, "h":3, "tiles":(0x799D,0x799E,0x8D94)},
        0xB3:{"w":2, "h":1, "tiles":(0x8D8E,0x8D8F)},
        0xB8:{"w":4, "h":4,
              "tiles":(-1,(0x0C,1),(0x0D,3),(0x05,2),
                       -1,0x8D0D,0x8D0E,(0x06,3),
                       (0x08,1),(0x0F,3),0x8D1C,0x8D1D,
                       0x8D00,0x8D1E,0x8D1F,0x8D20)},
        0xB9:{"w":5, "h":6,
              "tiles":(-1,(0x02,3),(0x0F,5),(0x10,3),-1,
                       -1,(0x03,4),0x8D12,0x8D13,-1,
                       -1,0x8D21,0x8D22,(0x0D,2),(0x0A,1),
                       (0x02,2),(0x0F,4),(0x10,2),0x8D23,0x8D24,
                       (0x03,3),0x8D08,0x8D25,0x8D26,0x8D27,
                       0x8D0A,0x8D0B,0x8D28,0x8D1F,0x8D20)},
        0xC2:{"w":4, "h":4,
              "tiles":(0x8D96,0x8D97,0x8D98,0x8D99,
                       0x152C,0x152D,0x152E,0x152F,
                       0x8DB4,0x8DB5,0x8DB6,0x8DB7,
                       0x0000,0x8DC3,0x8DC4,0x8DC5)},
        0xC3:{"w":4, "h":4,
              "tiles":(0x8DD1,0x8DD2,0x8DD3,0x8DD4,
                       0x8F00,0x8F01,0x8F02,0x8F03,
                       0x8DD5,0x8DD6,0x8DD7,0x8DD8,
                       0x0000,0x8DD9,0x8DDA,0x8DDB)},
        0xC5:{"w":2, "h":2, "tiles":(0x00CD,0x00CE,0x00CF,0x00D0)},
        0xC6:{"w":3, "h":3,
              "tiles":(-1,0x00D1,0x00D2,0x00D0,0x00D5,0x00CF,0x00D0,0x00D2,-1)},
        0xC7:{"w":2, "h":3, "tiles":(-1,0x00D2,0x00CD,0x00D5,0x00CF,-1)},
        0xC8:{"w":2, "h":2, "tiles":(0x00CA,-1,0x00CB,0x00CC)},
        0xC9:{"w":2, "h":2, "tiles":(-1,0x00C5,0x00C6,0x00C7)},
        0xD4:{"w":5, "h":5,
              "tiles":(  -1,    -1,  0x0817,0x0A18,  -1,  
                         -1,  0x0817,0x9000,0x9001,0x0A1A,
                       0x79DE,0x9002,0x9003,0x9004,0x9005,
                       0x79B6,0x9006,0x9007,0x9008,0x5D0C,
                       0x79AE,0x9009,0x900A,0x5D0C,  -1,  )},
        0xD5:{"w":5, "h":5,
              "tiles":(0x79DE,0x900B,0x900C,0x0F12,0x1010,
                       0x79AE,0x900D,0x900E,0x900F,0x9010,
                       0x79C7,0x9002,0x9011,0x9003,0x9012,
                         -1,  0x9013,0x9014,0x9015,0x5D0C,
                         -1,  0x79BF,0x9009,0x5D0C,  -1,  )},
        0xD6:{"w":5, "h":6,
              "tiles":(  -1,  0x0C0D,0x0D0F,0x9016,0x0A18,
                       0x79DE,0x9017,0x9018,0x9019,0x901A,
                       0x79BD,0x901B,0x901C,0x901D,0x901E,
                       0x79C6,0x901F,0x901D,0x9015,0x5D0C,
                       0x79C3,0x9020,0x9008,0x5D0C,  -1,  
                       0x79AF,0x9009,0x5D0C,  -1,    -1,  )},
        0xD7:{"w":3, "h":4,
              "tiles":(  -1,  0x0817,0x0A18,
                       0x79C6,0x9021,0x901A,
                       0x79AE,0x9006,0x9022,
                       0x79BD,0x9009,0x9023)},
        0xD8:{"w":3, "h":3,
              "tiles":(0x79C6,0x900B,0x0A18,
                       0x79BE,0x9024,0x5D0D,
                       0x79DE,0x5D0E,  -1,  )},
        0xD9:{"w":5, "h":5,
              "tiles":(  -1,  0x0817,0x0A19,  -1,    -1,  
                       0x0817,0x9000,0x9025,0x0A19,  -1,  
                       0x9026,0x9027,0x9028,0x9029,0x79DA,
                       0x5B10,0x902A,0x902B,0x902C,0x79BD,
                         -1,  0x5B10,0x900A,0x902D,0x79AE)},
        0xDA:{"w":5, "h":5,
              "tiles":(0x0C0D,0x0D0F,0x0F13,0x1011,  -1,  
                       0x902E,0x902F,0x9030,0x9029,0x79DA,
                       0x9031,0x9032,0x9033,0x9034,0x79B6,
                       0x5B10,0x9035,0x9036,0x9037,  -1,  
                         -1,  0x5B10,0x902D,0x79AF,  -1,  )},
        0xDB:{"w":5, "h":6,
              "tiles":(0x0C0D,0x0D0F,0x0F12,0x1010,  -1,  
                       0x902E,0x9038,0x9039,0x903A,0x79DA,
                       0x9026,0x9027,0x903B,0x903C,0x79AF,
                       0x5B10,0x902A,0x903D,0x903E,0x79CC,
                         -1,  0x5B10,0x902A,0x903F,0x79C3,
                         -1,    -1,  0x5B10,0x902D,0x79AD)},
        0xDC:{"w":3, "h":4,
              "tiles":(0x0817,0x0A18,  -1,  
                       0x9040,0x9041,0x79CC,
                       0x9042,0x902C,0x79BD,
                       0x9043,0x902D,0x79CD)},
        0xDD:{"w":3, "h":3,
              "tiles":(0x0817,0x9044,0x79CC,
                       0x5B11,0x904F,0x79AE,
                         -1,  0x5B12,0x79B6)},
        0xDE:{"w":7, "h":6,
              "tiles":(  -1,    -1,    -1,  0x0817,0x0A18,  -1,    -1,  
                         -1,    -1,  0x0817,0x9000,0x9001,0x0F14,0x1010,
                         -1,  0x0817,0x9045,0x9038,0x9039,0x9033,0x9010,
                         -1,  0x9046,0x9047,0x9048,0x9004,0x9049,0x9010,
                         -1,  0x79DC,0x79C1,0x79CA,0x9009,0x902B,0x9022,
                         -1,  0x79D0,0x79CE,0x79C0,0x79DC,0x9009,0x9023)},
        0xDF:{"w":7, "h":6,
              "tiles":(  -1,  0x0817,0x900C,0x0A18,  -1,    -1,    -1,  
                       0x0817,0x9045,0x9038,0x9001,0x0A1A,  -1,    -1,  
                       0x902E,0x9011,0x904A,0x9039,0x904B,0x0A1A,  -1,  
                       0x9026,0x9027,0x9022,0x904C,0x901F,0x903E,  -1,  
                       0x904D,0x904E,0x902D,0x79DC,0x79B6,0x79C5,  -1,  
                       0x9043,0x902D,0x79AF,0x79D0,0x79B3,0x79B4,  -1,  )},
        0xE0:{"w":2, "h":2, "tiles":(0x7D24,0x7D25,0x0118,0x0119)},
        }
    def extR(self):
        "Extended object that creates a rectangle of specified tiles."
        param = self.extRtiles[self.obj.extID]
        if "x" in param:
            self.x += param["x"]
        if "y" in param:
            self.y += param["y"]
        self.setRect(param["tiles"], param["w"], param["h"])

    # Single-tile extended objects

    extStiles = {
        0x0F:0x00B6, 0x17:0x6001,
        0x32:(0x1E,0),
        0x33:(0x20,0), 0x34:(0x21,0), 0x35:(0x22,0), 0x36:(0x23,0),
        0x37:(0x25,0), 0x38:(0x26,0), 0x39:(0x27,0), 0x3A:(0x28,0),
        0x3B:(0x9E,0), 0x3C:(0x9E,0), 0x3D:(0x5E,0), 0x3E:(0x5E,0),
        0x3F:(0x9E,1), 0x40:(0x9E,2), 0x41:(0x9E,3), 0x42:(0x9E,4),
        0x43:(0x9E,5), 0x44:(0x9E,6), 0x45:(0x9E,7),
        0x4C:(0x3B,4), 0x4F:0x014A, 0x51:0x0183,
        0x5E:0x7502, 0x68:0x775E, 0x69:0x775F, 0x7E:0x77BB, 0x7F:0x77CC,
        0x80:0x0010, 0x8E:0x8710, 0x8F:0x8711, 0x90:0x8712, 0x91:0x8713,
        0xA7:0x799C, 0xC4:0x5F04,
        0xCA:0x79BB, 0xCB:0x79BC, 0xCC:0x79BD, 0xCD:0x79BE, 0xCE:0x79BF,
        0xCF:0x79C0, 0xD0:0x79C1, 0xD1:0x79C2, 0xD2:0x79C3, 0xD3:0x79C4,
        0xFD:0,
        }
    def extS(self):
        "Extended object that creates a single tile."
        self.setTile(self.extStiles[self.obj.extID])

    # Other extended objects

    ext0Ctiles = (0x920F,0x9066,0x9076,0x9086)
    def ext0C(self):
        self.setRect(lambda : self.simpleoverlap(
            self.ext0Ctiles[self.relY]+self.relX, 0x9216, 0x9213+self.relX),
                     width=2, height=4)

    def ext10(self):
        self.setRect(lambda : self.setTile(
            0x84C2 + ((0,2,1,3)[self.relY&3] ^ (self.relX&1))), 0x10, 0x20)

    ext1415tiles = {
        0x14:( 1, (0x96D6,  -1,  0x96D6,0x96D7,  -1,  
                   0x96D7,  -1,  0x96D4,  -1,  0x96D4)),
        0x15:(-1, (  -1,  0x96D5,  -1,  0x96D5,  -1,  
                   0x96D8,0x96D9,0x96D8,0x96D9,  -1, ))}
    def ext1415(self):
        slope, tiles = self.ext1415tiles[self.obj.extID]
        for i in range(5):
            self.setTile(tiles[2*i])
            self.shiftvert()
            self.setTile(tiles[2*i+1])
            self.relY=0
            self.shifthoriz(slope=slope)

    def ext16(self):
        newtile = self.dynamicshift(0xA3) | (self.getTile()&0xFF)
        if newtile >= 0xA314:
            # Invalid tile ID: Display red filler tile as a warning
            self.setTile(0x11E16)
        else:
            self.setTile(newtile)

##            # filler tile for now, to indicate the object exists
##            # needs to display a semitransparent red coin sprite on the tile
##            self.setTile(0x10E16)

    def ext1E(self):
        for i in range(4):
            self.setLine(first=lambda:self.setTile(0x9D9A+self.relY*2), tile=0,
                         last=lambda:self.setTile(0x9D9B+self.relY*2),
                         shift=self.shifthoriz, length=8)
            self.relX = 0
            self.shiftvert()

    def ext30(self):
        for i in range(4):
            self.relX = -1
            self.setLine(
                first=lambda:self.simpleoverlap(0x015C, 0x015A, -1),
                tile=lambda:self.setTile(0x015D + self.parityYX()),
                last=lambda:self.simpleoverlap(0x015C, 0x015B, -1),
                shift=self.shifthoriz, length=4)
            self.relY += 1

    def ext48(self):
        # is this simpler than just using extR, full of duplicate rows?
        #  rows 1 to 0x10 and 0x12 are just -1,-1,0x00E1,0x00E2
        self.relY = -0x13
        self.setTile(-1)
        self.relY = -0x10
        self.setTile(-1)

        self.relY = 0
        self.setTile(0x00DE)
        self.relX = 1
        self.setTile(0x00DE)
        self.relY = -2
        self.setTile(0x00E5)

        self.relY, self.relX = -0x13, 2
        self.setLine(first=0x00DF, tile=0x00E1, last=0x00E3,
                     length=0x14, shift=self.shiftvert)
        self.relY, self.relX = -0x13, 3 
        self.setLine(first=0x00E0, tile=0x00E2, last=0x00E4,
                     length=0x14, shift=self.shiftvert)

    def ext52(self):
        centertiles = iter(range(0x3D63, 0x3D69))
        for i in range(2):
            self.relX = -1
            self.setLine(
                first=lambda:self.simpleoverlap(0x015C, 0x015A, -1),
                tile=lambda:self.setTile(next(centertiles)),
                last=lambda:self.simpleoverlap(0x015C, 0x015B, -1),
                shift=self.shifthoriz, length=5)
            self.relY += 1

    def ext53(self):
        centertiles = iter((0x3D63,0x3D6C,0x3D65,0x3D69,0x3D6A,0x3D6B,
                            lambda:self.simpleoverlap(-1, 0x015A, 0x015C),
                            0x010E,0x010F))
        for i in range(2):
            self.relX = -1
            self.setLine(
                first=lambda:self.simpleoverlap(0x015C, 0x015A, -1),
                tile=lambda:self.setTile(next(centertiles)),
                last=lambda:self.simpleoverlap(0x015C, 0x015B, -1),
                shift=self.shifthoriz, length=5)
            self.relY += 1
        self.relX = 0
        self.setLine(lambda:self.setTile(next(centertiles)),
                     shift=self.shifthoriz, length=3)
        

    def ext31(self):
        for i in range(7):
            self.setLine(tile=lambda:self.setTile(0x00BD-self.parityX()),
                         first=0x00BB, length=6, shift=self.shifthoriz)
            self.relX = 0
            self.relY += 1

    def ext46(self):
        self.setTile(random.choice((0x5F00,0x5F01,0x5F03,0x5F03)))

    def ext4A(self):
        self.setTile(0x3D4C)
        if self.getTile(offsetX=-1) in (0x3D3B,0x3D49,0x3D4A):
            self.relX = -1
            self.setTile(0x3D3C)
    def ext4B(self):
        self.setTile(0x3D41)
        if self.getTile(offsetX=1) in (0x3D3B,0x3D49,0x3D3C):
            self.relX = 1
            self.setTile(0x3D4A)

    ext50A8tiles = {
        0x50:(0x000C,0x000D,0x0013,0x0014),  # right arrow sign
        0xA8:(0x000E,0x000F,0x0011,0x0012)}  # left arrow sign
    ext50A8alttiles = {
        # index 0 and 1 are unintended, but accessible by the game
        0x50:((0x07,0),(0x08,0),(0x6A, 0xA),(0x6A, 0xB)),  # right with ground
        0xA8:((0x06,3),(0x06,4),(0x6A, 0xC),(0x6A, 0xD))}  # left with ground
    ext50A8flowertiles = (0x000C,0x000D,0x008E,0x008F)  # right with flowers
    ext50A8snowtop = {
        0x50:(0x0025,0x0026),  # right arrow sign
        0xA8:(0x0033,0x0034)}  # left arrow sign
    def _ext50A8if(self):
        if self.getTile() in (self.dynamicshift(0x2A),
                              self.dynamicshift(0x2A)+1,
                              self.dynamicshift(0x6A),
                              self.dynamicshift(0x6A)+1):
            self.setTile(self.ext50A8alttiles[self.obj.extID][self.parityYX()])
        elif self.tileset == 0xC:  # flower tileset
            # left arrow sign becomes a right arrow sign!
            if self.getTile() >> 8 == 0x85:
                self.setTile(self.ext50A8flowertiles[self.parityYX()])
            else:
                self.setTile(self.ext50A8tiles[0x50][self.parityYX()])
        elif self.tileset == 4 and self.parityY() == 0 and\
             self.getTile(offsetY=1) != 0:
            # Replacing top half of the arrow sign with identical, differently
            #   numbered tiles... but maybe the user edited those tiles?
            self.setTile(self.ext50A8snowtop[0x50][self.parityYX()])
        else:
            self.setTile(self.ext50A8tiles[self.obj.extID][self.parityYX()])
    def ext50A8(self):
        self.setRect(self._ext50A8if, 2, 2)

    def ext545C(self):
        ext545Cprop = {
            0x54:(3, 3, (-1,-1,0x3DA1,0x3D79,0x3D77,0x3DA2,0x3D7A,
                         lambda:self.simpleoverlap(0x3DA0,0x3D71,0x3DA8),
                         -1)),
            0x55:(3, 3, (0x3DA4,-1,-1,0x3DA3,0x3D78,0x3D7C,-1,
                         lambda:self.simpleoverlap(0x3D9F,0x3D72,0x3DA8),
                         0x3D7B)),
            0x59:(3, 2, (-1,0x3D79,0x3D73,-1,0x3D7A,
                         lambda:self.simpleoverlap(0x3DA0,0x3D71,0x3DA8))),
            0x5C:(3, 2, (0x3D74,0x3D7C,-1,
                         lambda:self.simpleoverlap(0x3D9F,0x3D72,0x3DA8),
                         0x3D7B,-1))}
        width, height, tiles = ext545Cprop[self.obj.extID]
        self.setRect(tiles, width, height)

    ext67check = ((0x08,2),(0x0A,4),(0x0C,1),(0x10,3))
    ext67tiles = ((0x08,3),(0x0A,3),(0x0C,2),(0x10,2))
    def ext67(self):
        prevtile = self.getTile()
        for oldtile, newtile in zip(self.ext67check, self.ext67tiles):
            if prevtile == self.dynamicshift(oldtile[0]) + oldtile[1]:
                self.setTile(newtile)
                return
        if prevtile == 0x3DBD:
            self.setTile(0x3DCC)
        elif prevtile == 0x3DC0:
            self.setTile(0x3DCD)
        else:  # no valid slanted log tile to modify
            self.setTile(0x11E67)

    ext898Atiles = {0x89:(0x851B,0x8521), 0x8A:(0x8523,0x8529),
                    0x8B:(0x852B,0x8531), 0x8C:(0x8533,0x8539)}
    def ext898A(self):
        tiles = self.ext898Atiles[self.obj.extID]
        for i in range(2):
            offset = self.getTile()-9 & 0xE
            self.setTile(tiles[0] + self.relX + offset)
            if not offset:
                self.relY = 1
                self.setTile(tiles[1] + self.relX)
                self.relY = 0
            self.relX = 1
    def ext8B8C(self):
        tiles = self.ext898Atiles[self.obj.extID]
        for i in range(2):
            offset = self.getTile()-9 & 0xE
            self.setTile(tiles[0] + self.relY + offset)
            if not offset:
                self.relX = 1
                self.setTile(tiles[1] + self.relY)
                self.relX = 0
            self.relY = 1

    def ext8D(self):
        parity = self.getTile() & 1
        self.setTile((0x39,0x3F-parity))
        if parity:  # generate top-left corner
            self.relY = -1
            self.setTile((0x2A,5), major=False)
            self.relX = -1
            self.setTile(0, major=False)
            self.relY = 0
            self.setTile(0, major=False)
        else:  # generate top-right corner
            self.relY = -1
            self.setTile((0x2A,2), major=False)
            self.relX = +1
            self.setTile(0, major=False)
            self.relY = 0
            self.setTile(0, major=False)

    def ext9E9F(self):
        objoffset = self.obj.extID - 0x9E
        # this object doesn't check for in-game overflow!
        self.setTile((0x8562 + objoffset*4 + self.getTile()-0x854B) & 0xFFFF)
        self.relY = 1
        self.setTile(0x8104 + objoffset)

    extADB2prop = {
        0xAD:(3, (0x8D54,0x8D55,0x8D56,0x8D57,0x8D58,0x8D59)),
        0xAE:(3, (0x8D54,0x8D55,0x8D56,0x8D5A,0x8D58,0x8D5B)),
        0xAF:(2, (0x8D5C,0x8D5D,0x8D5E,0x8D5F)),
        0xB0:(2, (0x8D5C,0x8D5D,0x8D60,0x8D5F)),
        0xB1:(2, (0x8D5C,0x8D5D,0x8D5E,0x8D61)),
        0xB2:(2, (0x8D5C,0x8D5D,0x8D60,0x8D61)),
        }
    def extADB2(self):
        height, tiles = self.extADB2prop[self.obj.extID]
        randoffset = random.randrange(0, 0x30, 0xE)
        self.setRect(
            lambda : self.setTile(tiles[self.relY*2 + self.relX] + randoffset),
                     2, height)

    extB4B7prop = {
        0xB4:(2, 2, ((0x08,1),(0x0F,2),0x8D00,0x8D01),
                    ((0x08,2),(0x0F,6),0x8D06,0x8D07)),
        0xB5:(2, 2, ((0x0D,1),(0x0A,1),0x8D02,0x8D03),
                    ((0x0D,4),(0x0A,2),0x8D04,0x8D05)),
        0xB6:(3, 3, ((0x02,2),(0x0F,4),(0x10,1),(0x03,3),0x8D08,0x8D09,
                     0x8D0A,0x8D0B,0x8D0C),
                    ((0x02,3),(0x0F,5),(0x10,3),(0x03,4),0x8D12,0x8D13,
                     0x8D14,0x8D15,0x8D16)),
        0xB7:(3, 3, ((0x0C,1),(0x0D,3),(0x05,2),0x8D0D,0x8D0E,(0x06,3),
                     0x8D0F,0x8D10,0x8D11),
                    ((0x0C,2),(0x0D,5),(0x05,3),0x8D17,0x8D18,(0x06,4),
                     0x8D19,0x8D1A,0x8D1B)),
        }
    def extB4B7(self):
        width, height, tilemapA, tilemapB = self.extB4B7prop[self.obj.extID]
        tiles = random.choice((tilemapA, tilemapB))
        self.setRect(tiles, width, height)

    extBABFtiles = {
        0xBA:(2, (0x8D36,0x8D42)),
        0xBB:(3, (0x8D36,0x8D39,0x8D3F)),
        0xBC:(4, (0x8D36,0x8D39,0x8D3C,0x8D3F)),
        0xBD:(4, (0x8D36,0x8D48,0x8D4B,0x8D4E)),
        0xBE:(3, (0x8D36,0x8D48,0x8D4E)),
        0xBF:(2, (0x8D45,0x8D51)),
        }
    def extBABF(self):
        height, tiles = self.extBABFtiles[self.obj.extID]
        randoffset = random.choice((0, 0, 1, 2))
        self.setColumn([tile+randoffset for tile in tiles], height)

    def extC0(self):
        self.setTile(0x8DA7)
        self.relX = 1
        self.setTile(0x8DA8)
        self.relX = 0

        self.relY = 1
        for i in range(2):
            if self.getTile(offsetY=1) in (0x8DA5, 0x8DA6):
                self.setTile(0x8F04 + self.relX)
            else:
                self.setTile(0x152A + self.relX)
            self.relX += 1

    def extC1(self):
        self.setTile(0x8DA5)
        self.relX = 1
        self.setTile(0x8DA6)
        self.relX = 0

        self.relY = 1
        for i in range(2):
            if self.getTile() in (0x152A, 0x152B):
                self.setTile(self.getTile() + 0x79DA)  # 8F04 or 8F05
            self.relX += 1

    def _extD4DFgroundcheck(self):
        if self.getTile() == 0x100F: self.setTile(0x100E, major=False)
        elif self.getTile() == 0x0C0B: self.setTile(0x0C0C, major=False)
    def extD4DF(self):
        self.extR()
        self.setLine(tile=lambda : self._extD4DFgroundcheck(),
            shift=self.shifthoriz,
            length=self.extRtiles[self.obj.extID]["w"])

    def extFB(self):  # screen linker
        # display filler tile
        self.setTile(0x10EFB)

        currentscreen = SMA3.coordstoscreen(self.x, self.y)
        linkscreen = (self.y&0xF)<<4 | self.x&0xF
        if (currentscreen == linkscreen or
                linkscreen >= SMA3.Constants.maxscreen):
            return

        self.screenlink[linkscreen] = currentscreen

        if self.tilemap.screens[linkscreen] != 1:
            # set screen to enabled, but not included in screen count
            self.tilemap.screens[linkscreen] = 0xFB

        # this object is associated with the entire linked screen
        baseY = (self.y&0xF)<<4
        baseX = (self.x&0xF)<<4
        for y in range(baseY, baseY+0x10):
            for x in range(baseX, baseX+0x10):
                self.obj.tiles.add((x, y))
        self.obj.alltiles = self.obj.tiles.copy()

        # also, this object affects its entire current screen
        baseY = self.y&0xF0
        baseX = self.x&0xF0
        for y in range(baseY, baseY+0x10):
            for x in range(baseX, baseX+0x10):
                self.obj.alltiles.add((x, y))

    def extFEFF(self):  # disable screens in-game
        # display filler tile
        self.setTile(0x10E00 + self.obj.extID)
        # set screen to disabled
        self.tilemap.screens[self.y&0xF0 | self.x>>4] = self.obj.extID

    ## Define standard object functions

    # Single-tile rectangle/line objects
    objStiles = {
        0x1D:0x001D, 0x1E:0x001E,
        0x68:0x6000, 0x6C:0x0184, 0x77:0x3D58, 0x82:0x6001,
        0x8A:0x7400, 0x8B:0x7300, 0x9E:0x7502,
        0xD1:0x870F, 0xD2:0x870E, 0xDA:0x8A00
        }
    def objS(self, width, height):
        "Standard object that creates a rectangle/line of a constant tile ID."
        self.setRect(self.objStiles[self.obj.ID], width, height)

    # 2x2 parity rectangle/line objects that enforce even lengths

    objYXtiles = {0x70:(0x3D37,0x3D38,0x3D45,0x3D46),
                  0x71:(0x0141,0x0142,0x0143,0x0144),
                  0x72:(0x3D39,0x3D3A,0x3D47,0x3D48),
                  0x8E:(0x7500,0x7501,0x3DAA,0x3DAB),
                  0x94:(0x7600,0x7601,0x7775,0x7776),
                  0x95:(0x7602,0x7603,0x7777,0x7778),
                  0x96:(0x7604,0x7605,0x7779,0x777A),
                  0x97:(0x7606,0x7607,0x777B,0x777C),
                  0xA3:(0x7B00,0x7B01,0x7B02,0x7B03),
                  0xA4:(0x7B04,0x7B05,0x7B06,0x7B07),
                  }
    def objYX(self, width, height):
        if width&1: width += 1
        if height&1: height += 1
        tiles = self.objYXtiles[self.obj.ID]
        self.setRect(lambda : self.setTile(tiles[self.parityYX()]),
                        width, height)

    # Other standard objects

    # Objects 01-0B: Regular land

    _landinteriorrandoffset = (0x0E, 0x0E, 0x0F, 0x0F, 0x10, 0x11, 0x2B, 0x2C)
    def _landinterior(self):
        # should be called by overlap check for 67, and 
        #  by function for 08029548 (01/04-09/99 interior overlap checks)
        self.setTile((0x39, random.choice(self._landinteriorrandoffset)))

    def obj01row0(self, tilebase):
        if self.getTile() & 0xFF00 == tilebase:
            if self.relX == 0: self.setTile(tilebase+0x2A, major=False)
            else: self.setTile(tilebase+0x29, major=False)
        else: self.setTile((0x2A, self.parityX()), major=False)
    def obj01row1(self, tilebase):
        if self.getTile() & 0xFF00 == tilebase:
            if self.relX == 0: self.setTile(tilebase+0x07)
            else: self.setTile(tilebase+0x08)
        else: self.setTile(tilebase+0x12+self.parityX())
    def obj01row2(self, tilebase):
        offset = self.parityX()
        if self.getTile() & 0xFF00 == tilebase and self.relX != 0:
            offset = 1
        if self.getTile(offsetY=-1) in (tilebase+0x07, tilebase+0x08):
            self.setTile(tilebase+0x18+offset)
        else:
            self.setTile(tilebase+0x14+offset)
    obj01rowfunc = (obj01row0, obj01row1, obj01row2)
    def obj01(self, width, height):
        height += 1
        self.y -= 1

        tilebase = self.dynamicshift(0x39)
        for i in range(height):
            try:
                self.setLine(
                    tile=lambda:self.obj01rowfunc[self.relY](self, tilebase),
                    shift=self.shifthoriz, length=width,
                    finalshift=self.resetX)
            except IndexError:
                # relY not in (0,1,2)
                self.setLine(
                    tile=self._landinterior, shift=self.shifthoriz,
                    length=width, finalshift=self.resetX)
            self.shiftvert()

    obj0203corner = {
        0x02:{"startoffset":(-1, -1),
              "startrect":((0x3B,0x00), (0x2A,0x01), (0x3B,0x02), -1),
              0:(0x39,0x1F),
              1:(0x39,0x21),
              "overlap":(0x39,0x36),
              },
        0x03:{"startoffset":(0, -1),
              "startrect":((0x2A,0x00), (0x3B,0x01), -1, (0x3B,0x03)),
              0:(0x39,0x20),
              1:(0x39,0x22),
              "overlap":(0x39,0x37),
              }
        }
    obj02030A0Bwalltiles = (
        ((0x39,0x23),(0x39,0x23),(0x39,0x25),(0x39,0x27)),  # left wall
        ((0x39,0x24),(0x39,0x24),(0x39,0x26),(0x39,0x28)))  # right wall
    def _obj02030A0Bwall(self, objparity):
        if self.getTile() in (self.dynamicshift(0x2A),
                              self.dynamicshift(0x2A)+1):
            self.setTile((0x39,0x29+objparity))
        elif self.getTile() in (self.dynamicshift(0x39)+0x07,
                                self.dynamicshift(0x39)+0x12,
                                self.dynamicshift(0x39)+0x13):
            if self.getTile(offsetY=-1) in (self.dynamicshift(0x39)+0x36,
                                            self.dynamicshift(0x39)+0x37):
                self.relY -= 1
                self.setTile((0x39,0x29+objparity))
                self.relY += 1
            if (objparity and self.getTile(offsetX=-1) ==\
                    self.dynamicshift(0x39)+0x0D) or\
                    (not objparity and self.getTile(offsetX=1) ==\
                    self.dynamicshift(0x39)+0x0D):
                self.setTile((0x39,0x0B+objparity))
            else:
                self.setTile((0x39,0x07))
                self.relY += 1
                self.setTile((0x39,0x19-objparity), major=False)
                self.relY -= 1
        else:
            self.setTile(random.choice(self.obj02030A0Bwalltiles[objparity]))
    def obj0203(self, _, height):
        prop = self.obj0203corner[self.obj.ID]

        while self.relY != height:
            if self.relY == 0:
                self.relX, self.relY = prop["startoffset"]
                self.setRect(
                    tiles=prop["startrect"], width=2, height=2, major=False)
                self.relX, self.relY = 0, 0
                self.setTile(prop[0])  # 0,0 tile is major
            elif self.relY == 1:
                if self.getTile() in (self.dynamicshift(0x2A),
                                      self.dynamicshift(0x2A)+1):
                    self.setTile(prop["overlap"])
                else:
                    self.setTile(prop[1])
            else:
                self._obj02030A0Bwall(self.obj.ID & 1)
            self.shiftvert()
    def obj0A0B(self, _, height):
        self.setLine(first=(0x39, 0x09 + (self.obj.ID & 1)),
                     tile=lambda:self._obj02030A0Bwall(self.obj.ID & 1),
                     shift=self.shiftvert, length=height)

    obj04tiles = (((0x2A,0x02),(0x0F,0),(0x13,0),(0x39,0x0E)),
                  ((0x2A,0x03),(0x10,0),(0x11,0),(0x39,0x18)))
    obj05tiles = (((0x2A,0x04),(0x0C,0),(0x0E,0),(0x39,0x19)),
                  ((0x2A,0x05),(0x0D,0),(0x12,0),(0x39,0x0F)))
    obj06tiles = (0x2A,0x07),(0x0A,0),(0x0B,0),(0x39,0x16)
    obj07tiles = (0x2A,0x06),(0x08,0),(0x09,0),(0x39,0x17)
    obj08tiles = (0x2A,0x08),(0x05,0),(0x06,0),(0x07,0),(0x39,0x2D)
    obj09tiles = (0x2A,0x09),(0x02,0),(0x03,0),(0x04,0),(0x39,0x2E)
    obj0409prop = {0x04:(obj04tiles, 1, -1, True),
                   0x05:(obj05tiles, 2, 1, True),
                   0x06:(obj06tiles, 1, -1, False),
                   0x07:(obj07tiles, 2, 1, False),
                   0x08:(obj08tiles, 1, -2, False),
                   0x09:(obj09tiles, 2, 2, False),
                   }
    def obj0409(self, width, height):
        tiles, heightoffset, slope, halfslope = self.obj0409prop[self.obj.ID]
        height += heightoffset
        self.y -= heightoffset

        if halfslope:
            for i in range(abs(width)):
                self.setColumn(
                    tiles=tiles[self.parityX()], default=self._landinterior,
                    height=height, majorthreshold=1)
                height += slope*self.parityX()
                if height <= 0:
                    break
                self.shifthoriz(slope=slope*self.parityX())
        else:
            for i in range(abs(width)):
                self.setColumn(
                    tiles=tiles, default=self._landinterior,
                    height=height, majorthreshold=1)
                height += slope
                if height <= 0:
                    break
                self.shifthoriz(slope=slope)

    def obj0C2B(self, _, height):
        length1 = None
        if self.obj.ID == 0x2B:
            length1 = 0x01FD  # overflow
        self.setLine(first=(0x6B,0), tile=(0x6B,1), last=(0x6B,2),
                     length1=length1, shift=self.shiftvert, length=height)

    def _obj0Dif(self, default, other):
        if self.getTile() & 0xFF00 == self.dynamicshift(0x39):
            self.setTile(other)
        else:
            self.setTile(default)
    def obj0D(self, width, _):
        self.setLine(first=lambda:self._obj0Dif((0x38, 0), (0x39, 4)),
                     tile=(0x38, 1),
                     last=lambda:self._obj0Dif((0x38, 2), (0x39, 3)),
                     shift=self.shifthoriz, length=width)

    def obj0E0F(self, _, height):
        offset = 0xF - self.obj.ID
        self.setLine(
            first=0x0090+offset, tile=0x0094+offset, last=(0x2A, 0x0A+offset),
            shift=self.shiftvert, length=height)

    def _obj1013precheck(self, defaulttile):
        if self.getTile() in (0x00B4, 0x00A7):
            self.setTile(0x00A7)
        else:
            self.setTile(defaulttile)
    _obj1012slopetiles = {
        (0x10, True):(0x009C,0x009B,0x009A,-1),
        (0x10, False):(0x009D,0x009E,0x009F,-1),
        (0x11, True):(0x0097,0x0096),
        (0x11, False):(0x0098,0x0099),
        (0x12, True):(0x00A5,0x00A3,0x00A4),
        (0x12, False):(0x00A0,0x00A2,0x00A1)}
    def obj1012(self, width, _):
        slope = (-1,-1,-2)[self.obj.ID&0xF]
        halfslope = (self.obj.ID == 0x10)
        positive = (width > 0)
        def _first():
            if positive: self._obj1013precheck(0x0093)
            else: self._obj1013precheck(0x0092)
            self.y += slope
        def _last():
            if positive: self._obj1013precheck(0x0092)
            else: self._obj1013precheck(0x0093)
        def _slopedline():
            if halfslope:
                tiles = self._obj1012slopetiles[
                    (self.obj.ID, positive)][self.parityX()::2]
            else:
                tiles = self._obj1012slopetiles[(self.obj.ID, positive)]
            for tile in tiles:
                self.setTile(tile)
                self.shiftvert()
            self.relY=0

        if halfslope:
            self.setLine(first=_first, tile=_slopedline, last=_last,
                shift=lambda : self.shifthoriz(slope=(not self.parityX())*slope),
                         length=width)
        else:
            self.setLine(first=_first, tile=_slopedline, last=_last,
                shift=lambda : self.shifthoriz(slope=slope), length=width)
    def obj13(self, width, _):
        self.setLine(
            first=lambda : self._obj1013precheck(0x0093),
            tile=lambda : self._obj1013precheck(0x00A6),
            last=lambda : self._obj1013precheck(0x0092),
            shift=self.shifthoriz, length=width)

    obj14checktiles = (
        (0x39,0x12),(0x39,0x13),(0x2A,0x00),(0x2A,0x01),(0x39,0x30),(0x39,0x33),
        (0x39,0x23),(0x39,0x25),(0x39,0x27),(0x19,0x00),(0x19,0x00),(0x19,0x00),
        (0x19,0x00),(0x39,0x24),(0x39,0x26),(0x39,0x28),(0x39,0x29),(0x39,0x2A))
    def _obj14main(self, tilebase, tilekey, cutsurface=False):
        if cutsurface:
            if self.getTile(offsetY=-1) in (self.dynamicshift(0x2A),
                                            self.dynamicshift(0x2A)+1):
                self.relY -= 1
                if self.relX == 0:
                    self.setTile(0x007E, major=False)
                elif self.relX + 1 == self.obj.adjwidth:
                    self.setTile(0x007F, major=False)
                else:
                    self.setTile(0, major=False)
                self.relY += 1

        tiles = ObjectExtraData.obj14tiles[tilekey]
        prevtile = self.getTile()
        if prevtile & 0xFF00 == tilebase:
            index = (prevtile & 0xFF) + 1
        else:
            for i, (high, low) in enumerate(self.obj14checktiles):
                if prevtile == self.dynamicshift(high) + low:
                    index = i + 0x14
                    break
            else:
                index = 0
        self.setTile(tiles[index])

    def obj14(self, width, height):
        tilebase = self.dynamicshift(0x19)
        self.setBorderRect(width, height,
            tile3x3=(lambda : self._obj14main(tilebase, "yfirst_xfirst", True),
                     lambda : self._obj14main(tilebase, "yfirst_xmid", True),
                     lambda : self._obj14main(tilebase, "yfirst_xlast", True),
                     lambda : self._obj14main(tilebase, "ymid_xfirst"),
                     (0x19,0x12),
                     lambda : self._obj14main(tilebase, "ymid_xlast"),
                     lambda : self._obj14main(tilebase, "ylast_xfirst"),
                     lambda : self._obj14main(tilebase, "ylast_xmid"),
                     lambda : self._obj14main(tilebase, "ylast_xlast")),
            tile1row=(lambda : self._obj14main(tilebase, "h1_xfirst"),
                      lambda : self._obj14main(tilebase, "h1_xmid"),
                      lambda : self._obj14main(tilebase, "h1_xlast")),
            tile1col=(lambda : self._obj14main(tilebase, "w1_yfirst"),
                      lambda : self._obj14main(tilebase, "w1_ymid"),
                      lambda : self._obj14main(tilebase, "w1_ylast")),
            tile1x1=lambda : self._obj14main(tilebase, "w1_yfirst")
                           )

    def obj15(self, width, _):
        self.setLine(first=0x00DB, tile=0x00DD, last=0x00DC,
                     shift=self.shifthoriz, length=width)
        self.shiftvert()
        self.relX = 0
        self.setLine(first=0x150F, tile=0x01511, last=0x1510,
                     shift=self.shifthoriz, length=width)

    def _obj1619widthfix(self):
        if self.obj.width < 0 and self.tileset == 2:
            self.obj.width %= 0x100
        elif self.obj.width >= 0x80 and self.tileset != 2:
            self.obj.width -= 0x100
        return self.obj.adjwidth

    def _obj16if(self):
        if not self.getTile(): self.setTile(0x1600)
    def obj16(self, width, height):
        width = self._obj1619widthfix()
        self.setRect(self._obj16if, width, height)

    def _obj17vinesides(self, left, right, width):
        if self.getTile(offsetY=1) & 0xFF00 != 0x1600 and\
           not self.getTile(offsetX=-1):
            self.relX = -1
            self.setTile(left, major=False)
            self.relX = 0
        if self.getTile(offsetX=width-1, offsetY=1) & 0xFF00 != 0x1600 and\
           not self.getTile(offsetX=width):
            self.relX = width
            self.setTile(right, major=False)
            self.relX = 0
    def _obj17precheck(self, default, watertile):
        if self.getTile() & 0xFF00 == 0x1600:
            self.setTile(watertile)
        else:
            self.setTile(default)
    def obj17(self, width, height):
        self.relY = -1
        self._obj17vinesides(0x0020, 0x0023, width)
        self.setLine(
            lambda : self._obj17precheck(0x0021, -1),
            shift=self.shifthoriz, length=width)
        self.relY, self.relX = 0, 0
        self._obj17vinesides(0x001F, 0x0024, width)
        self.setBorderRect(width, height, tile3x3=(
            lambda : self._obj17precheck(0x011A, 0x011F),
            lambda : self._obj17precheck(0x011A, 0x0120),
            lambda : self._obj17precheck(0x011A, 0x0121),
            lambda : self._obj17precheck(0x011C, 0x0122),
            lambda : self._obj17precheck(0x011D, 0x0123),
            lambda : self._obj17precheck(0x011E, 0x0124),
            lambda : self._obj17precheck(0x013A, 0x0137),
            lambda : self._obj17precheck(0x013B, 0x0138),
            lambda : self._obj17precheck(0x013C, 0x0139),
                           ))

    def _obj18funcgen(self, tile):
        def _obj18precheck():
            if self.getTile() & 0xFF00 == 0x1600:  # water
                self.setTile(tile+9)
            else:
                self.setTile(tile)
        return _obj18precheck
    def obj18(self, width, height):
        tilefunc = []
        for tile in range(0x0125,0x012E):
            tilefunc.append(self._obj18funcgen(tile))
        self.setBorderRect(width, height, tile3x3=tilefunc)

    def obj19(self, width, height):
        width = self._obj1619widthfix()
        for x in range(abs(width)):
            tiles = range(0x1601 + (self.relX&3), 0x1615, 4)
            self.setColumn(tiles, height,
                           default=lambda:self.setTile(tiles[4 - self.parityY()]))
            self.shifthoriz()

    def obj1A(self, width, _):
        self.setLine(first=0x1505, last=0x1506,
                     tile=lambda:self.simpleoverlap(0x1501, 0x0019, 0x1509),
                     shift=self.shifthoriz, length=width)

    obj1Btiles = (0x1500,0x0019,0x001A,  # default
                  0x1400,0x1615,0x1616,  # in water
                    -1  ,0x1509,0x1507)  # crossing platform
    def _obj1Bprecheck(self, index):
        if self.getTile() & 0xFF00 == 0x1600:  # water
            index += 3
        elif self.getTile() in (0x1501,0x1502):  # semisolid platform
            index += 6
        self.setTile(self.obj1Btiles[index])
    def obj1B(self, _, height):
        self.setLine(first=lambda:self._obj1Bprecheck(0),
                     tile=lambda:self._obj1Bprecheck(1),
                     last=lambda:self._obj1Bprecheck(2),
                     shift=self.shiftvert, length=height)

    def obj1C(self, _, height):
        for i in range(2):
            self.setLine(first=0x1507+i, tile=0x001B+i, last=0x1503+i,
                         shift=self.shiftvert, length=height)
            self.relY, self.relX = 0, 1

    # Objects 21-28: Jungle mud

    randmudtiles = (
        0x9068,0x9069,0x906A,0x906B,0x906C,0x906D,0x906E,0x906F,0x9070,0x9071,
        0x906B,0x906D,0x906D,0x906D,0x906D,0x906D)

    obj21tiles = (0x9200,0x9080,0x9090)
    def _obj21columngen(self, firstX, lastX):
        offset = random.randrange(4)
        for i in range(3):
        # relY == 0
            if self.getTile() in (0x9072,0x9073,0x907F,0x908F,0x90A2,0x90A3):
                yield -1
            elif i == 0 and firstX and self.getTile() >> 8 in (0x94, 0x95):
                self.relY += 1
                self.setTile(0x90A3)
                self.relY += 1
                self.setTile(0x9073)
                self.relY -= 2
                yield 0x9500
            elif i == 0 and lastX and self.getTile() >> 8 in (0x94, 0x95):
                self.relY += 1
                self.setTile(0x90A2)
                self.relY += 1
                self.setTile(0x9072)
                self.relY -= 2
                yield 0x9402
            elif i == 1 and self.getTile() >> 8 in (0x94, 0x95):
                if firstX:
                    self.relY -= 1
                    self.setTile(0x9204)
                    self.relY += 2
                    self.setTile(0x908F)
                    self.relY -= 1
                    self.relX -= 1
                    self.setTile(0x964D, major=False)
                    self.relX += 1
                    yield 0x330D
                elif lastX:
                    self.relY -= 1
                    self.setTile(0x9205)
                    self.relY += 2
                    self.setTile(0x907F)
                    self.relY -= 1
                    self.relX += 1
                    self.setTile(0x964E, major=False)
                    self.relX -= 1
                    yield 0x3512
                else:
                    yield 0
            else:
                yield self.obj21tiles[i] + offset
        while True:
            yield random.choice(self.randmudtiles)
    def obj21(self, width, height):
        for i in range(abs(width)):
            columngen = self._obj21columngen(i == 0, i+1 == abs(width))
            for j in range(abs(height)):
                self.setTile(next(columngen))
                self.shiftvert()
            self.relY = 0
            self.shifthoriz()

    def obj24(self, width, height):
        for i in range(abs(width)):
            tiles = (0x9608 + random.randrange(4), 0x9300 + random.randrange(4))
            self.setColumn(tiles, height,
                lambda : self.setTile(random.choice(self.randmudtiles)), 1)
            self.shifthoriz()

    _mudleft = (0x90A0,0x90A2,0x9072,0x909E)
    _mudright = (0x90A1,0x90A3,0x9073,0x9062)
    def _mudwallprecheck(self, tiles):
        prevtile = self.getTile()
        if 0x9200 <= prevtile < 0x9204:
            return tiles[0]
        elif 0x9080 <= prevtile < 0x9084:
            return tiles[1]
        elif 0x9090 <= prevtile < 0x9094:
            return tiles[2]
        else:
            return tiles[3] + random.randrange(2)

    obj2223tiles = {
        0x22:((0x9204,0x330D,0x909C), _mudleft, 0x964D),
        0x23:((0x9205,0x3512,0x909D), _mudright, 0x964E),
        }
    def _obj2223columngen(self, tiles):
        for tile in tiles[0]:
            yield tile
        while True:
            yield self._mudwallprecheck(tiles[1])
    def obj2223(self, _, height):
        tiles = self.obj2223tiles[self.obj.ID]
        self.relX = self.obj.ID & 1
        self.relY = 1
        self.setTile(tiles[-1], major=False)
        self.relX ^= 1
        self.relY = 0
        columngen = self._obj2223columngen(tiles)
        for i in range(abs(height)):
            self.setTile(next(columngen))
            self.shiftvert()

    obj2526tiles = {
        0x25:(0x9400, _mudleft, 1, (0x908F,0x964D,0x330D,0x9204)),
        0x26:(0x9502, _mudright, -1, (0x907F,0x964E,0x3512,0x9205)),
        }
    def _obj2526columngen(self, tiles):
        if 0x9090 <= self.getTile(offsetX=tiles[2]) < 0x9094:
            self.relX += tiles[2]
            self.setTile(tiles[3][0], major=False)
            self.relY -= 2
            self.setTile(tiles[3][3], major=False)
            self.relY += 1
            self.setTile(tiles[3][2], major=False)
            self.relX -= tiles[2]
            self.setTile(tiles[3][1], major=False)
            self.relY += 1
        yield tiles[0]
        while True:
            yield self._mudwallprecheck(tiles[1])
    def obj2526(self, _, height):
        columngen = self._obj2526columngen(self.obj2526tiles[self.obj.ID])
        for i in range(abs(height)):
            self.setTile(next(columngen))
            self.shiftvert()

    obj2728tiles = {
        0x27:((0x9400,0x905C), (-1,0x9204,0x964D,0x330D), 0x908F,
              (0x9402,0x90A2,0x9072)),
        0x28:((0x9501,0x905E), (1,0x9205,0x964E,0x3512), 0x907F,
              (0x9500,0x90A3,0x9073)),
        }
    def _obj2728columngen(self, tiles, firstX, lastX):
        for i in range(3):
            prevtile = self.getTile()
            if firstX and 0x9080 <= prevtile < 0x9084:
                self.relY -= 1
                self.setTile(tiles[1][1])
                self.relY += 1
                self.relX += tiles[1][0]
                self.setTile(tiles[1][2], major=False)
                self.relX -= tiles[1][0]
                yield tiles[1][3]
            elif firstX and 0x9090 <= prevtile < 0x9094:
                yield tiles[2]
            elif lastX and 0x9200 <= prevtile < 0x9204:
                yield tiles[3][0]
            elif lastX and 0x9080 <= prevtile < 0x9084:
                yield tiles[3][1]
            elif lastX and 0x9090 <= prevtile < 0x9094:
                yield tiles[3][2]
            elif i < 2:
                yield tiles[0][i] + random.randrange(2)
            # else (relY == 2 and no match): use random mud tile
        while True:
            yield random.choice(self.randmudtiles)
    def obj2728(self, width, height):
        tiles = self.obj2728tiles[self.obj.ID]
        for i in range(abs(width)):
            columngen = self._obj2728columngen(tiles, i == 0, i+1 == abs(width))
            for j in range(abs(height)):
                self.setTile(next(columngen))
                self.shiftvert()
            self.relY = 0
            height -= 1
            self.shifthoriz(slope=-1)

    obj29tiles = (
        (0x9B01,0x9B00,0x9639,0x9638,0x9629,0x9628,0x9631,0x9630,0x961B,0x9620),
        (0x961D,0x961C,0x963D,0x963C,0x962D,0x962C,0x9635,0x9634,0x961B,0x9624))
    obj2Atiles = (
        (0x960E,0x960F,0x963A,0x963B,0x962A,0x962B,0x9632,0x9633,0x961B,0x9623),
        (0x9B02,0x9B03,0x963E,0x963F,0x962E,0x962F,0x9636,0x9637,0x961B,0x9627))
    def obj292A(self, width, height):
        if height == 1: height = -1  # prevents breaking the loop too early
        if self.obj.ID == 0x29:
            tiles = self.obj29tiles
        else:
            tiles = self.obj2Atiles

        for i in range(abs(width)):
            if not self.parityX():
                pattern = random.choice(tiles)
            self.setColumn(pattern[self.parityX()::2], height, 0x961B)
            height += 2*self.parityX()
            if height >= 0:
                break
            self.shifthoriz(slope=2*self.parityX())

    def obj2C(self, _, height):
        tiles = [0x330E, 0x3511]
        for i in range(height-1):
            tiles.append(random.randrange(0x90DA,0x90E2,2))
            tiles.append(tiles[-1] + 1)
        self.setRect(tiles, 2, height)

    obj2D2Etiles = (
        ((0x9211,0x9065,0x9075,0x9085), 0x9213, (0x9064,0x9074), (0x9084,0x9094)),
        ((0x9212,0x9078,0x9088,0x9079), 0x9216, (0x9074,0x9064), (0x907E,0x908E)),
        )
    def _obj2D2Ecolumngen(self, tiles, height):
        for i in range(height-2):
            if i == 0 and self.getTile() == 0x9214:
                yield tiles[1]
            elif i < 4:
                yield tiles[0][i]
            else:
                yield tiles[2][i&1]
        if height != 1:
            yield tiles[3][0]
        yield tiles[3][1]
    def obj2D(self, _, height):
        tiles = self.obj2D2Etiles[random.randrange(2)]
        columngen = self._obj2D2Ecolumngen(tiles, height)
        for tile in columngen:
            self.setTile(tile)
            self.relY += 1

    def obj2E(self, _, height):
        tiles = self.obj2D2Etiles[random.randrange(2)]
        columngen = self._obj2D2Ecolumngen(tiles, height)
        for tile in columngen:
            if tile == 0x9064 and random.randrange(2):
                tile = 0x907B
                self.relX -= 1
                self.setTile(0x907A, major=False)
                self.relX += 1
            elif tile == 0x9074 and random.randrange(2):
                tile = 0x9089
                self.relX += 1
                self.setTile(0x908A, major=False)
                self.relX -= 1
            self.setTile(tile)
            self.relY += 1

    obj2Ftop = (0x966F,0x9670,0x9671,0x1530,0x9A00,0x1531)
    def obj2F(self, _, height):
        self.relX = -1
        self.setRect(self.obj2Ftop, 3, min(2, height))
        if height > 2:
            self.relX = 0
            self.setLine(
                first=0x990A, last=0x9206,
                tile=lambda:self.setTile(random.randrange(0x990B,0x990D)),
                shift=self.shiftvert, length=height-2)

    def obj34(self, width, _):
        for i in range(abs(width)):
            tiles = [-1, random.randrange(0x964F,0x965F)]
            if tiles[1] < 0x965B:
                tiles[0] = tiles[1] - 0xF
            if 0x9608 <= self.getTile(offsetY=1) < 0x960C:
                tiles[1] += 0x10
            self.setColumn(tiles, 2)
            self.shifthoriz()

    obj35tiles = ((0x161B,0x161C,0x1628,0x1628),  # default
                  (0x1619,0x161A,0x1626,0x1627))  # 1/4 chance
    def _obj35precheck(self, default):
        resetrand = False
        highbyte = self.getTile() >> 8
        if highbyte in (0x6B, 0x90, 0x93):
            resetrand = True
            if self.relY < 2:
                tile = (0x9061, 0x909B)[self.relY]
            else:
                tile = random.choice((0x9098,0x9098,0x9099,0x909A))                
        elif highbyte in (0x94, 0x95):
            tile = (highbyte + 3) << 8
            if self.relY:
                tile += 1
        else:
            tile = default
        self.setTile(tile)
        return resetrand
    def obj35(self, width, height):
        for i in range(abs(width)):
            if not self.parityX():
                tiles = self.obj35tiles[random.randrange(4) == 0]
            for j in range(abs(height)):
                if self.relY < 2:
                    resetrand = self._obj35precheck(tiles[self.relY*2 + self.parityX()])
                else:
                    resetrand = self._obj35precheck(0x1628)
                if resetrand:
                    tiles = self.obj35tiles[0]
                self.shiftvert()
            self.relY = 0
            self.shifthoriz()

    def _obj37if(self):
        if not self.getTile(): self.setTile(0x1512)
    def obj37(self, width, _):
        self.setLine(tile=self._obj37if, shift=self.shifthoriz,  length=width)

    obj3CF4tiles = {0x3C:((0x7D08,0x9D32,0x9D34),(0x7D0A,0x9D32,0x9D36)),
                     0xF4:((0x79F1,0x79F3,0x79F5),(0x79A8,0x79F3,0x79A0))}
    def obj3CF4(self, _, height):
        vert = 0
        if height < 0:
            vert = 1
        def _set2tiles(tile):
            def _tempfunc():
                self.setTile(tile)
                self.relX += 1
                self.setTile(tile+1)
                self.relX = 0
            return _tempfunc
        self.setLine(
            first=_set2tiles(self.obj3CF4tiles[self.obj.ID][vert][0]),
            tile=_set2tiles(self.obj3CF4tiles[self.obj.ID][vert][1]),
            last=_set2tiles(self.obj3CF4tiles[self.obj.ID][vert][2]),
            shift=self.shiftvert, length=height)

    def _obj3Dtopleft(self):
        if self.getTile() in (0x00A8,0x00A9):
            self.setTile(0x00B5)
        else:
            self.setTile(0x00A7)
    def obj3D(self, width, _):
        self.setLine(first=self._obj3Dtopleft, last=0x00AA,
                     tile=lambda:self.setTile(0x00A9-self.parityX()),
                     shift=self.shifthoriz, length=width)
        self.relY, self.relX = 1, 0
        self.setLine(first=0x3C00, last=0x3C03,
                     tile=lambda:self.setTile(0x3C02-self.parityX()),
                     shift=self.shifthoriz, length=width)
        self.relY, self.relX = 2, 0
        self.setLine(first=0x00AB, last=0x00B2,
                     tile=lambda:self.setTile(0x00B1-self.parityX()),
                     shift=self.shifthoriz, length=width)

    def _obj3Eprecheck(self, defaulttile):
        if self.getTile() in (0x0092, 0x0093, 0x00A7):
            self.setTile(0x00A7)
        else:
            self.setTile(defaulttile)
    def obj3E(self, _, height):
        self.setLine(
            first=lambda : self._obj3Eprecheck(0x00B3),
            tile=lambda : self._obj3Eprecheck(0x00B4),
            last=lambda : self._obj3Eprecheck((0x2A,0x0C)),
            shift=self.shiftvert, length=height)

    obj3F40tiles = (0x0114,0x2904,0x2906)
    def _obj3F40tile(self):
        index = bool(self.relY)
        if self.getTile(): index += 1
        self.setTile(self.obj3F40tiles[index] + self.obj.ID-0x3F)
    def obj3F40(self, _, height):
        self.setLine(tile=self._obj3F40tile,
                     shift=self.shiftvert, length=height)

    def obj49(self, _, height):
        self.setLine(first=0x00C8, tile=0x00CE,
                     shift=self.shiftvert, length=height)
        self.relY, self.relX = 0, 1
        self.setLine(first=0x00CD, tile=0x00CF,
                     shift=self.shiftvert, length=height)

    def obj4A(self, _, height):
        self.setLine(0x00D3, shift=self.shiftvert, length=height)
        self.relY, self.relX = 0, 1
        self.setLine(0x00D4, shift=self.shiftvert, length=height)

    obj4B4Dprop = {
        0x4B:(4, (0x0174,0x0175,0x0175,0x0178),
                 (0x0179,0x017A,0x017A,0x017D),
                 (0x017E,0x017F,0x017F,0x0182)),
        0x4C:(6, (0x0174,0x0175,0x0175,0x0175,0x0176,0x0178),
                 (0x0179,0x017A,0x017A,0x017A,0x017B,0x017D),
                 (0x017E,0x017F,0x017F,0x017F,0x0180,0x0182)),
        0x4D:(8, (0x0174,0x0175,0x0175,0x0175,0x0175,0x0175,0x0177,0x0178),
                 (0x0179,0x017A,0x017A,0x017A,0x017A,0x017A,0x017C,0x017D),
                 (0x017E,0x017F,0x017F,0x017F,0x017F,0x017F,0x0181,0x0182)),
        }
    def obj4B4D(self, _, height):
        width, rowfirst, rowmid, rowlast = self.obj4B4Dprop[self.obj.ID]
        tiles = list(rowfirst)
        if height >= 2:
            tiles += rowmid*(height-2)
            tiles += rowlast
        self.setRect(tiles, width, height)

    def obj4Etemp(self, width, height):
        self.setBorderRect(width=width, height=height,
            tile3x3=[(0x1A, i) for i in range(9)],
            tile1row=[(0x1A, i) for i in range(9,0xC)],
            tile1col=[(0x1A, i) for i in range(0xC,0xF)],
            tile1x1=(0x1A, 0xF))

    def _obj5051if(self, tile):
        if self.getTile() in (self.dynamicshift(0x2A),
                              self.dynamicshift(0x2A)+1,
                              self.dynamicshift(0x68)+5):
            self.setTile((0x1F, 1))
        else:
            self.setTile(tile)
    def obj50(self, _, height):
        self.setLine(lambda : self._obj5051if(tile=(0x1F, 0)),
                     shift=self.shiftvert, length=height)
    def obj51(self, width, _):
        self.setLine(lambda : self._obj5051if(tile=(0x24, 0)),
                     shift=self.shifthoriz, length=width)

    def obj52(self, width, height):
        if width > 0:
            tiles = ((0x23,0),(0x22,0))
        else:
            tiles = ((0x20,0),(0x21,0))
        for i in range(abs(width)):
            self.setColumn(tiles, height)
            height -= 1
            if height <= 0:
                break
            self.shifthoriz(slope=-1)

    def obj57(self, width, _):
        overlapbase = self.dynamicshift(0x19)
        self.setLine(
            first=lambda:self.simpleoverlap((0x3F,0), overlapbase+0xC, (0x3F,3)),
            tile=(0x3F,1),
            last=lambda:self.simpleoverlap((0x3F,2), overlapbase+0xD, (0x3F,4)),
            shift=self.shifthoriz, length=width)

    def _obj58columngen(self, edge, tilebase, bgwallbase):
        # edge: 1:left edge/right wall if extended,
        #       0:right edge/left wall if extended
        if self.getTile(offsetY=1) in (tilebase+0x2B, tilebase+0x2C) or\
           tilebase+0x0E <= self.getTile(offsetY=1) <= tilebase+0x1B:
            # generate left/right wall
            yield tilebase+0x31+edge  # concave corner
            while True:
                # generate tile from object 02/0A or 03/0B
                self._obj02030A0Bwall(edge)
                # object 58 overlap code
                if edge and self.getTile(offsetX=1) in (
                                0x007D,0x007E,self.dynamicshift(0x2A),0x0142):
                    yield tilebase+0x2A
                elif not edge and self.getTile(offsetX=-1) in (
                                  0x007D,0x007F,self.dynamicshift(0x2A),
                                  self.dynamicshift(0x2A)+1):
                    yield tilebase+0x29
                else:
                    yield -1  # don't change tile from _obj02030A0Bwall call
        else:
            # misc overlap checks
            if tilebase+0x2F <= self.getTile() <= tilebase+0x34:
                yield tilebase+0x30
            elif self.getTile() == bgwallbase+0x24:
                yield -1
            elif self.getTile() == bgwallbase+0x1C:
                yield (0x19,0x24)
            elif edge:
                yield tilebase+0x2F  # bottom-left corner
            else:
                yield tilebase+0x34  # bottom-right corner
            while True: yield -1  # ignore object height

    obj58ceilingoverlap = {
        0x01:0x24, 0x03:0x24, 0x04:0x23, 0x07:0x25, 0x0B:0x24, 0x10:0x23,
        0x11:0x25, 0x1D:0x24, 0x28:0x25, 0x2A:0x23, 0x2B:0x25, 0x2D:0x26}
    def _obj58ceiling(self, height, bgwallbase):
        prevtile = self.getTile()
        if prevtile-bgwallbase == 0x24:
            return
        try:
            self.setTile(
                bgwallbase + self.obj58ceilingoverlap[prevtile - bgwallbase])
        except KeyError:
            self.setTile((0x39, 0x30))

        # loop purely to enable screens within the bounding box
        self.shiftvert()
        while self.relY != height:
            if not (self.relY+self.y)&0xF:
                self.setTile(-1)
            self.shiftvert()
        self.relY = 0

    def obj58(self, width, height):
        tilebase = self.dynamicshift(0x39)
        bgwallbase = self.dynamicshift(0x19)

        # left column
        columngen = self._obj58columngen(1, tilebase, bgwallbase)
        for i in range(abs(height)):
            self.setTile(next(columngen))
            self.shiftvert()

        self.relY = 0
        if width == 1:
            return
        self.shifthoriz()

        # central ceiling
        for i in range(abs(width-2)):
            self._obj58ceiling(height, bgwallbase)
            self.shifthoriz()

        # right column
        columngen = self._obj58columngen(0, tilebase, bgwallbase)
        for i in range(abs(height)):
            self.setTile(next(columngen))
            self.shiftvert()


    def obj63(self, width, _):
        self.setLine(first=0x151E, tile=0x151F, last=0x1520,
                        shift=self.shifthoriz, length=width)

    def obj66(self, width, height):
        # ice block is not objYX becaues it doesn't enforce even lengths
        self.setRect(lambda : self.setTile(0x8900 | self.parityYX()),
                     width, height)

    def _obj67randflowertile(self):
        index = random.randrange(0x40)
        if index <= 0xA:
            self.setTile(0x79BB+index)
        else:
            self.setTile(0x79E0)
    def obj67(self, width, height):
        if self.tileset & 0xF == 0xC:
            self.setRect(self._obj67randflowertile, width, height)
        else:
            self.setRect(self._landinterior, width, height)

    def obj69(self, width, height):
        if width < 4: width = 4
        if height < 4: height = 4
        self.setBorderRect(width, height, tile3x3=(
            0x6100,0x6101,0x6102,0x0185,0x0186,0x0187,0x6103,0x6104,0x6105))

    def obj6A(self, width, _):
        self.setLine(first=0x6400, tile=0x6401, last=0x6402,
                     shift=self.shifthoriz, length=width)

    def obj6B(self, width, height):
        # top-left corner land overlap checks
        if self.getTile(offsetX=-1, offsetY=-1) in (self.dynamicshift(0x2A),
                                                    self.dynamicshift(0x2A)+1):
            self.relY = -1
            self.setTile((0x3B,1), major=False)
            self.relY = 0
        first = 0x0188  # default top-left corner tile
        tilebase = self.dynamicshift(0x39)
        if self.getTile(offsetX=-1) in (tilebase+0x12, tilebase+0x13,
                                        tilebase+0x20, tilebase+0x2A):
            first = tilebase+0x35

        # main goal platform
        self.setLine(first=first, tile=0x0189, last=0x018A,
                     shift=self.shifthoriz, length=width)
        self.relY, self.relX = 1, 0
        self.setLine(tile=lambda : self.setLine(
            first=0x018B, tile=0x018C, last=0x018D,
            shift=self.shifthoriz, length=width, finalshift=self.resetX),
                     shift=self.shiftvert, length=height-1)

    def obj6D(self, _, height):
        self.setLine(first=(0x6C,0), tile=(0x6B,1), last=(0x6B,2),
                     shift=self.shiftvert, length=height)

    def obj6E(self, width, height):
        self.setRect(lambda:self.setTile(random.randrange(0x0199, 0x01A1)),
                     width, height)

    def obj6F(self, _, height):
        if self.getTile(offsetY=height-1) in (self.dynamicshift(0x2A),
                                                self.dynamicshift(0x2A)+1):
            lasttile=0x3D4B
        else:
            lasttile=None
        self.setLine(tile=lambda:self.setTile(0x3D3B+random.randrange(2)),
                     last=lasttile, shift=self.shiftvert, length=height)

    obj7376prop = {
        0x73:(3, (0x3D42,0x3D43,0x3D44,0x3D50,0x3D51,0x3D52)),
        0x74:(3, (0x3D53,0x3D54,0x3D55)),
        0x75:(2, (0x3D53,0x3D57)),
        0x76:(2, (0x3D56,0x3D55)),
        }
    def obj7376(self, _, height):
        width, tiles = self.obj7376prop[self.obj.ID]
        self.setRect(tiles, width, height)

    obj7879tiles = {0x78:(0x3D3E,0x3D3D,0x3D3F,0x3D40),
                    0x79:(0x3D5A,0x6700,0x3D59,0x6600)}
    def obj7879(self, width, _):
        if width > 0:
            tiles = self.obj7879tiles[self.obj.ID][0:2]
        else:
            tiles = self.obj7879tiles[self.obj.ID][2:4]
        def _column(upper, lower):
            self.relY = -1
            self.setTile(upper)
            self.relY = 0
            self.setTile(lower)
        self.setLine(first=tiles[1],
                     tile=lambda : _column(tiles[0], tiles[1]),
                     last=lambda : _column(tiles[0], -1),
                     shift=lambda : self.shifthoriz(slope=-1), length=width)

    def obj7E(self, width, _):
        self.setLine(first=(0x38,0x09), tile=(0x38,0x0A), last=(0x38,0x0B),
                     shift=self.shifthoriz, length=width)

    def _obj7Ffuncgen(self, index):
        def _obj7Fmain():
            prevtile = self.getTile()
            if prevtile & 0xFF00 == self.dynamicshift(0x68):
                tile = ObjectExtraData.obj7Ftiles_prev68[index][prevtile&0xFF]
            elif prevtile & 0xFF00 == self.dynamicshift(0x19):
                if prevtile & 0xFF in (0x16, 0x17):
                    tile = ObjectExtraData.obj7Ftiles_prev1916[index]
                else:
                    tile = ObjectExtraData.obj7Ftiles_prev19[index]
            else:
                tile = -1
            self.setTile(tile)
        return _obj7Fmain
    def obj7F(self, width, height):
        if width < 2: width = 2
        if height < 2: height = 2
        funclist = []
        for i in range(9):
            funclist.append(self._obj7Ffuncgen(i))
        self.setBorderRect(width, height, tile3x3=funclist)

    def obj89(self, width, height):
        self.setBorderRect(width, height,
            tile3x3=(0x7200, 0x7201, 0x7202,
                     lambda:self.setTile((0x7203,0x7210)[self.parityY()]),
                     lambda:self.setTile((0x7204,0x7211)[self.parityY()]),
                     lambda:self.setTile((0x7205,0x7212)[self.parityY()]),
                     0x7206, 0x7207, 0x7208),
            tile1row=(0x7209, 0x720A, 0x720B),
            tile1col=(0x720C,
                      lambda:self.setTile((0x720E,0x7213)[self.parityY()]),
                      0x720F),
            tile1x1=0x720D
            )

    def obj8D(self, _, height):
        self.setLine(tile=lambda:self.setTile(random.choice((0x3D70,0x3DA7))),
                     last=0x3D6F, shift=self.shiftvert, length=height)

    obj8Ftiles = (
        ((0x08,6),(0x0A,6),0x3DBF,0x3DBE,0x3DDB,0x3DDA),
        ((0x0F,2),(0x0D,1),0x3DC0,0x3DBD,(0x0F,3),(0x0D,2),0x3DDC,0x3DD9),
        ((0x10,3),(0x0C,1),0x3DC1,0x3DBC,0x3DBF,0x3DBE),
        ((0x10,4),(0x0C,4),0x3DDD,0x3DD8,0x3DDB,0x3DDA),
        )
    def _obj8Fcolumngen(self, firstX, parityX, slopeoffset, group0, group1):
        if firstX:
            for i in range(2):
                offset = slopeoffset + 2*i
                if self.getTile() not in group0:
                    offset += 2
                yield self.obj8Ftiles[0][offset]
        elif parityX:  # relX is odd
            for i in range(2):
                offset = slopeoffset + 2*i
                if self.getTile() in group0:
                    yield self.obj8Ftiles[1][offset]
                elif self.getTile() in group1:
                    yield self.obj8Ftiles[1][offset+4]
                else:
                    yield -1
        else:  # relX is even and nonzero
            for i in range(3):
                offset = slopeoffset + 2*i
                if self.getTile() in group0:
                    yield self.obj8Ftiles[2][offset]
                elif self.getTile() in group1:
                    yield self.obj8Ftiles[3][offset]
                else:
                    yield -1
        while True:
            yield -1

    def obj8F(self, width, height):
        if width >= 0:
            slopeoffset = 0
        else:
            slopeoffset = 1
        group0 = (0, self.dynamicshift(0x08)+5, self.dynamicshift(0x0A)+1)
        group1 = (self.dynamicshift(0x2A), self.dynamicshift(0x2A)+1)
        for i in range(abs(width)):
            columngen = self._obj8Fcolumngen(
                i == 0, i & 1, slopeoffset, group0, group1)
            for j in range(abs(height)):
                self.setTile(next(columngen))
                self.shiftvert()
            self.relY = 0
            slope = 0
            if i & 1 == 0 and i != 0:
                slope = -1
            self.shifthoriz(slope=slope)

    obj90tilesX0 = ((0x08,5),(0x0A,1),0x3DB1,0x3DB0,None,None,
                       0x3DB1,0x3DB0,0x3DB6,0x3DB5)
    obj90tiles = ((0x0A,4),(0x08,2),0x3DBB,0x3DB8,0x3DBA,0x3DB9,
                  (0x0A,5),(0x08,1),0x3DB7,0x3DB4,0x3DB6,0x3DB5)
    def _obj90column(self, tiles, slopeoffset, height):
        for y in range(height):
            offset = self.relY*2
            if self.getTile() in (self.dynamicshift(0x2A),
                                  self.dynamicshift(0x2A)+1):
                offset += 6
            elif self.getTile():
                continue
            self.setTile(tiles[offset + slopeoffset])
            self.shiftvert()
        self.relY = 0
        if self.relX == 0:  # don't use slope in first column
            self.y -= 1
    def obj90(self, width, height):
        if width >= 0:
            slopeoffset = 0
        else:
            slopeoffset = 1
        self.setLine(first=lambda:self._obj90column(
                         self.obj90tilesX0, slopeoffset, min(height, 2)),
                     tile=lambda:self._obj90column(
                         self.obj90tiles, slopeoffset, min(height, 3)),
                     shift=lambda:self.shifthoriz(slope=-1), length=width)

    def _obj91base(self):
        # join to positive-slope logs?
        if self.getTile() == self.dynamicshift(0x08)+2: tile = (0x08,4)
        elif self.getTile() == self.dynamicshift(0x0C)+1: tile = (0x0C,3)
        else: tile = 0x11091
        self.setTile(tile)
    def _obj92base(self):
        # join to negative-slope logs?
        if self.getTile() == self.dynamicshift(0x0A)+4: tile = (0x0A,2)
        elif self.getTile() == self.dynamicshift(0x10)+3: tile = (0x10,1)
        else: tile = 0x3DAD
        self.setTile(tile)
    obj9192prop = {
        0x91:((0x3DC2,0x3DC3,0x3DC4,0x3DC8,0x3DC9,0x3DCA), 0x3DB2, _obj91base),
        0x92:((0x3DC5,0x3DC6,0x3DC7,0x3DCB,0x3DAE,0x3DAF), 0x3DB3, _obj92base)}
    def obj9192(self, _, height):
        toptiles, midtile, basefunc = self.obj9192prop[self.obj.ID]

        self.relX = -1
        self.setRect(toptiles, 3, min(2, height))
        if height > 2:
            self.relX = 0
            self.setLine(tile=midtile, last=lambda:basefunc(self),
                         shift=self.shiftvert, length=height-2)

    obj93toptiles = (0x3DCE,0x3DCF,0x3DD0,  -1,
                     0x3DD1,0x3DD2,0x3DD3,0x3DD4)
    def obj93(self, _, height):
        self.relX = -1
        self.setRect(self.obj93toptiles, 4, min(2, height))
        if height > 2:
            self.relX = 0
            self.setLine(tile=0x3DD5, last=0x3DD6,
                         shift=self.shiftvert, length=height-2)
            self.relY, self.relX = height-1, 1
            self.setTile(0x3DD7)

    def obj98(self, width, height):
        self.setLine(
            lambda : self.setTile((0x7750,0x7754)[self.parityX()], major=False),
            shift=self.shifthoriz, length=width)
        if height > 1:
            self.relY, self.relX = 1, 0
            self.setLine(first=0x7800, last=0x7803,
                         tile=lambda:self.setTile(0x7801+self.parityX()),
                         shift=self.shifthoriz, length=width)
        if height > 2:
            self.relY, self.relX = 2, 0
            self.setRect(lambda : self.setTile(0x01B7 + (self.relX+self.relY & 1)),
                         width, height-2)

    def obj99(self, _, height):
        self.relX = -1
        self.setRect(range(0x01B9,0x01BF), 3, min(2, height))
        self.relX, self.relY = 0, 0
        self.setColumn((0x01BA,0x01BD), height, default=self._landinterior)

    def _obj9Dprecheck(self, tile):
        if self.getTile() in (self.dynamicshift(0x2A),
                              self.dynamicshift(0x2A)+1):
            tile += 6
        self.setTile(tile)
    def obj9D(self, width, height):
        self.setBorderRect(width, height,
            tile3x3=(0x7900, 0x7901, 0x7902,
                     lambda:self.setTile((0x7903,0x7906)[self.parityY()]),
                     lambda:self.setTile((0x7904,0x7907)[self.parityY()]),
                     lambda:self.setTile((0x7905,0x7908)[self.parityY()]),
                     lambda:self._obj9Dprecheck(0x7909),
                     lambda:self._obj9Dprecheck(0x790A),
                     lambda:self._obj9Dprecheck(0x790B),
            ))

    obj9Ftiles = ((0x3308,0x3508,  -1,    -1,  ),
                  (0x0004,0x0005,  -1,    -1,  ))
    def obj9F(self, width, _):
        if width&1:
            width += 1
        self.setRect(
            lambda : self.setTile(self.obj9Ftiles[self.relY][self.relX&3]),
                     width, 2)

    def objA0A2(self, width, height):
        if width&1:
            width += 1
        self.setRect(lambda : self.setTile(
            0x78C0 + 2*self.obj.ID + self.parityX()),  # 7A00 + (objID-A0)*2
                     width, height)

    def _objA5A6blank(self, tile):
        if self.getTile() in (0, 0x1600): self.setTile(tile)
    def objA5(self, _, height):
        if self.tileset == 3:
            def _Ytile():
                if self.relY == 0:
                    return 0x905A
                if self.relY + 1 == height:
                    return 0x3D29
                if self.relY + 2 == height:
                    return 0x7D1C
                else:
                    return 0x9050
            self.setRect(lambda : self.setTile(_Ytile() + self.parityX()),
                         2, height)
        else:
            self.setLine(
                tile=lambda:self.setLine(
                    first=lambda:self._objA5A6blank(0x7D02 + self.parityX()),
                    tile=lambda:self.setTile(0x01C7 + (self.parityYX()^2)),
                    last=lambda:self._objA5A6blank(0x7D06 + self.parityX()),
                    shift=self.shiftvert, length=height, finalshift=self.resetY),
                shift=self.shifthoriz, length=2)
    objA6center = (0x01C4,0x01C3,0x01C5,0x01C6)
    objA6t3tiles = {"first":(0x3D2B,0x7D1E,0x7D1F,0x9056),
                    "mid":((0x3D2C,0x9052,0x9054,0x9057),
                           (0x3D2D,0x9053,0x9055,0x9058)),
                    "last":(0x3D2E,0x7D20,0x7D21,0x9059)}
    def objA6(self, width, _):
        if self.tileset == 3:
            def _column(tiles):
                for tileID in tiles:
                    self.setTile(tileID)
                    self.shiftvert()
                self.relY = 0
            self.setLine(
                first=lambda:_column(self.objA6t3tiles["first"]),
                tile=lambda:_column(self.objA6t3tiles["mid"][self.parityX()]),
                last=lambda:_column(self.objA6t3tiles["last"]),
                shift=self.shifthoriz, length=width)
        else:
            self.setLine(
                tile=lambda:self.setLine(
                    first=lambda:self._objA5A6blank(0x7D00 + self.parityY()),
                    tile=lambda:self.setTile(self.objA6center[self.parityYX()]),
                    last=lambda:self._objA5A6blank(0x7D04 + self.parityY()),
                    shift=self.shifthoriz, length=width, finalshift=self.resetX),
                shift=self.shiftvert, length=2)

    def _thornedge(self, newtile):
        oldtile = self.getTile()
        if oldtile == 0:
            self.setTile(newtile, major=False)
        elif 0x777D <= self.getTile() <= 0x778B:  # thorn edge already exists
            # bitwise OR old edge with new edge
            self.setTile((oldtile-0x777C | newtile-0x777C) + 0x777C,
                         major=False)
    def objA7(self, width, height):
        self.x -= 1
        self.y -= 1
        self.setBorderRect(width=width+2, height=height+2, tile3x3=(
            -1, lambda:self._thornedge(0x7780), -1,
            lambda:self._thornedge(0x777E), 0x7C00,
                lambda:self._thornedge(0x777D),
            -1, lambda:self._thornedge(0x7784), -1))


    # Objects AA-C3: Sewer tileset pipes

    objAAADtiles = {0xAA:(0x790F,0x7799,0x791F,0x779A),
                    0xAB:(0x779F,0x7910,0x77A0,0x7920),
                    0xAC:(0x7915,0x7916,0x77A9,0x77AA),
                    0xAD:(0x77AF,0x77B0,0x7925,0x7926),
                    }
    objAAADoverlapcheck = (
        # pipe left, pipe right, BGwall left, BGwall right
        0x790F,0x791F,0x7910,0x7920,0x7799,0x779A,0x779F,0x77A0,
        # pipe ceiling, pipe floor, BGwall ceiling, BGwall floor
        0x7915,0x7916,0x7925,0x7926,0x77A9,0x77AA,0x77AF,0x77B0)
    objDAAADoverlaptiles = (
        # 3-dimensional table represented as a single tuple, indexed by:
        # default tile index // 2, then overlap tile index // 2, then coordindex
        0x7931,0x792C,0x792C, 0x791C,0x7931,0x791C,  # original: pipe left
        0x792E,  -1,    -1,     -1,  0x791E,  -1,  
        0x7931,0x792B,0x792B, 0x791B,0x7931,0x791B,  # original: pipe right
        0x792D,  -1,    -1,     -1,  0x791D,  -1,  
        0x792E, None,  None,   None, 0x791E, None,   # original: BGwall left
        0x5D09,0x77B9,0x77B9, 0x77BB,0x0A2F,0x77BB,
        0x792D, None,  None,   None, 0x791D, None,   # original: BGwall right
        0x5B0D,0x77CC,0x77CC, 0x77BA,0x082D,0x77BA,
        0x7931,0x792C,0x792C, 0x792B,0x7931,0x792B,  # original: pipe ceiling
        0x792E,  -1,    -1,     -1,  0x792D,  -1,  
        0x7931,0x791C,0x791C, 0x791B,0x7931,0x791B,  # original: pipe floor
        0x791E,  -1,    -1,     -1,  0x791D,  -1,  
        0x792E, None,  None,   None, 0x792D, None,   # original: BGwall ceiling
        0x5D09,0x77B9,0x77B9, 0x77CC,0x5B0D,0x77CC,
        0x791E, None,  None,   None, 0x791D, None,   # original: BGwall floor
        0x0A2F,0x77BB,0x77BB, 0x77BA,0x082D,0x77BA,
        )
    def _sewerpipeoverlap(self, defaulttile, coord, length):
        defaulttype = self.objAAADoverlapcheck.index(defaulttile) // 2
        try:
            overlaptype = self.objAAADoverlapcheck.index(self.getTile()) // 2
        except ValueError:
            return
        if not (defaulttype ^ overlaptype) & 4:
            # overlap must have one wall and one floor/ceiling
            return

        if coord < 2:  # first 2 tiles
            coordindex = 0
        elif coord >= length - 2:  # last 2 tiles
            coordindex = 1
        else:
            coordindex = 2
        index = defaulttype*12 + (overlaptype&3)*3 + coordindex

        return self.objDAAADoverlaptiles[index]

    def _objAAADmain(self, tiles, coord, length):
        defaulttile = tiles[self.parityYX()]
        tile = self._sewerpipeoverlap(defaulttile, coord, length)
        if tile is not None:
            self.setTile(tile)
        else:
            self.setTile(defaulttile)
    def objAAAB(self, _, height):
        tiles = self.objAAADtiles[self.obj.ID]
        self.setRect(lambda : self._objAAADmain(tiles, self.relY, height),
                     2, height)
    def objAC(self, width, _):
        if self.tileset == 0xB:
            self.objACAD(width, _)
        else:  # unrelated unfinished-in-game object outside sewer tileset
            self.setLine(self.ext46, shift=self.shifthoriz, length=width)
    def objACAD(self, width, _):
        tiles = self.objAAADtiles[self.obj.ID]
        self.setRect(lambda : self._objAAADmain(tiles, self.relX, width),
                     width, 2)

    objAEtiles = (0x779B,0x779D,0x779C,0x779E)
    objAFtiles = (0x77AB,0x77AC,0x77AD,0x77AE)
    def objAE(self, _, height):
        self.setRect(
            lambda : self.setTile(self.objAEtiles[self.parityYX()]), 2, height)
    def objAF(self, width, _):
        self.setRect(
            lambda : self.setTile(self.objAFtiles[self.parityYX()]), width, 2)

    def objB0(self, width, height):
        def _notblank(tile):
            if not self.getTile(): self.setTile(tile)
        self.setBorderRect(width, height, tile3x3=(
            lambda:_notblank(0x77AB),
            lambda:_notblank(0x77AB+self.parityX()),
            lambda:_notblank(0x77CE),
            lambda:_notblank(0x779B+self.parityY()),
            lambda:_notblank(0x779D + 0x10*self.parityY() + self.parityX()),
            lambda:_notblank(0x779D + 0x10*self.parityY()),
            lambda:_notblank(0x77CE),
            lambda:_notblank(0x779D+self.parityX()),
            lambda:_notblank(0x779D),
            ))

    objB1general = (0x1513,0x1514,0x1515,0x1516,0x0000,0x0000,0x0000,0x0000)
    def _objB1precheck(self):
        prevtile = self.getTile()
        if prevtile <= 0x77B8:
            tile = self.objB1general[(prevtile - 9) >> 1 & 7]
        elif prevtile in (0x77B9,0x77BB,0x77C9,0x77CC):
            tile = 0x1519
        elif 0x8100 <= prevtile < 0x8104:
            tile = 0x1517
        elif 0x854B <= prevtile < 0x854F:
            tile = 0x151D
        else:
            tile = -1
        self.setTile(tile)
    def objB1(self, width, _):
        self.setLine(self._objB1precheck, shift=self.shifthoriz, length=width)

    objB2B9prop = {
        0xB2:(3, (0x792E,0x5D09,0x77B9)),
        0xB3:(3, (0x77BA,0x082D,0x791D)),
        0xB4:(4, (0x792E,0x5D09,0x77B9,0x77AB)),
        0xB5:(4, (0x77AE,0x77BA,0x082D,0x791D)),
        0xB6:(3, (0x792D,0x5B0C,0x77C9)),
        0xB7:(3, (0x77CA,0x0A2E,0x791E)),
        0xB8:(4, (0x792D,0x5B0C,0x77C9,0x77AC)),
        0xB9:(4, (0x77AD,0x77CA,0x0A2E,0x791E)),
        }
    def objB2B9(self, width, _):
        height, tiles = self.objB2B9prop[self.obj.ID]
        for i in range(abs(width)):
            for row in range(height):
                if not self.getTile():
                    tile = tiles[row]
                    if (tile == 0x0A2E and\
                            self.getTile(offsetY=-1) in (0x7799,0x779A)) or\
                            (tile == 0x5B0C and\
                            self.getTile(offsetY=1) in (0x779F,0x77A0)):
                        tile += 1
                    self.setTile(tile)
                self.relY += 1
            self.shifthoriz(slope=-1)
            self.relY = 0

    def objBA(self, width, _):
        self.setLine(first=0x792F, last=0x7930,
                     tile=lambda:self.setTile(0x7915 + self.parityX()),
                     shift=self.shifthoriz, length=width)
    def objBB(self, width, _):
        self.setLine(first=0x7932, last=0x7933,
                     tile=lambda:self.setTile(0x7925 + self.parityX()),
                     shift=self.shifthoriz, length=width)
    def objBC(self, _, height):
        self.setLine(first=0x7930, last=0x7933,
                     tile=lambda:self.setTile(0x7910 + 0x10*self.parityY()),
                     shift=self.shiftvert, length=height)
    def objBD(self, _, height):
        self.setLine(first=0x792F, last=0x7932,
                     tile=lambda:self.setTile(0x790F + 0x10*self.parityY()),
                     shift=self.shiftvert, length=height)

    objC2C3tiles = {
        0xC2:(0x77BF, (0x082D,0x082E), 0x7F00),
        0xC3:(0x77C0, range(0x0A2D,0x0A31), 0x8000)}
    def objC2C3(self, width, _):
        tile0, prerange, tile1 = self.objC2C3tiles[self.obj.ID]
        for i in range(abs(width)):
            self.setTile(tile0)
            self.relY = 1
            if self.getTile() in prerange:
                self.setTile(tile1)
            else:
                self.setTile(-1)
            self.relY = 0
            self.shifthoriz(slope=-1)

    def objC4C9(self, width, height):
        prop = {
            0x83:(0x6001, self.shifthoriz, width, self.parityX),
            0x84:(0x6001, lambda : self.shifthoriz(slope=-1),
                  width, self.parityX),
            0xC4:(0x6000, self.shifthoriz, width, self.parityX),
            0xC5:(0x6000, self.shiftvert, height, self.parityY),
            0xC6:(0x6000, lambda : self.shifthoriz(slope=-1),
                  width, self.parityX),
            0xC7:(0x7400, self.shifthoriz, width, self.parityX),
            0xC8:(0x7400, self.shiftvert, height, self.parityY),
            0xC9:(0x7400, lambda : self.shifthoriz(slope=-1),
                  width, self.parityX),
            }
        tile, shift, length, parity = prop[self.obj.ID]
        def _paritycoin():
            if not parity(): self.setTile(tile)
        self.setLine(_paritycoin, shift, length)

    objCAcheckdark = (0x779B,0x779C,0x77AB,0x77AC,0x77B9,0x77BB,0x77BE)
    objCAchecklight = (0x779D,0x779E,0x77AD,0x77AE,0x77BA)
    def _objCAfirstrow(self):
        prevtile = self.getTile()
        tile = -1
        if prevtile == 0x8101:
            tile = 0x8103
        elif self.getTile(offsetX=-1) == 0x8103:
            if prevtile in self.objCAcheckdark: tile = 0x77BC
            elif prevtile in self.objCAchecklight: tile = 0x77BD
        elif self.getTile(offsetX=1) in (0x8101, 0x8103):
            if prevtile in self.objCAcheckdark: tile = 0x77CB
            elif prevtile in self.objCAchecklight: tile = 0x77CD
        self.setTile(tile, major=False)
    def objCA(self, width, height):
        for i in range(abs(width)):
            self.setColumn((self._objCAfirstrow, 0x161F), height, 0x1620)
            self.shifthoriz()

    def objCE(self, width, _):
        if width >= 0:
            tile = 0x8701
        else:
            tile = 0x8700
        self.setLine(tile=tile, shift=lambda:self.shifthoriz(slope=-1),
                     length=width)

    objCFD0prop = {0xCF:(0x8702, 2), 0xD0:(0x8706, 4)}
    def objCFD0(self, width, _):
        tile, offset = self.objCFD0prop[self.obj.ID]
        if width > 0:
            tile += offset
        def _modshift(self):
            if abs(self.relX) % offset == offset-1:
                self.shifthoriz(-1)
            else:
                self.shifthoriz()
        self.setLine(tile=lambda : self.setTile(tile + abs(self.relX)%offset),
                     shift=lambda : _modshift(self),
                     length=width)

    def objD3(self, width, height):
        self.setRect(lambda : self.setTile(
            0x854B + (self.parityY()*2 ^ (self.x+self.relX & 3))),
                     width, height)

    objD8tiles = (0x84BA,0x84BB,0x330C,0x3510,0x84BC,0x84BD,0x84BE,0x84BF)
    def objD8(self, width, _):
        self.setLine(lambda : self.setColumn(
            self.objD8tiles[self.parityX()::2], height=4, majorthreshold=1),
                     shift=self.shifthoriz, length=width)

    def _objD9column(self):
        for tileID, major in ((0x84C0, False), (0x8600, True), (0x84C1, False)):
            self.setTile(tileID, major)
            self.shiftvert()
        self.relY = 0
    def objD9(self, width, _):
        self.setLine(self._objD9column, shift=self.shifthoriz, length=width)

    objDBtiles = ((0x8C01,0x8C05,0x8C09), (0x8C02,0x8C06,0x8C0A))
    def objDB(self, width, height):
        for i in range(abs(width)):
            if self.getTile():
                tiles = [-1]
            else:
                tiles = [random.choice((-1,-1,0x17,0x18))]
            tiles += self.objDBtiles[self.parityX()]
            self.setColumn(tiles, height, default=0x8C0D, majorthreshold=1)
            self.shifthoriz()

    def _iceclearabove(self):
        self.setTile(0)
        self.relY -= 1
        self.setTile(0, major=False)
        self.relY += 1

    objDCtiles = (
        (0x8C03,0x8C07,0x8C0B),  # left
        ([0x0015,0x1621,0x1623],  # center, X even
         [0x0016,0x1622,0x1624]),  # center, X odd
        (0x8C00,0x8C04,0x8C08),  # right
        )
    def objDC(self, width, height):
        self.setLine(
            first=lambda:self.setColumn(self.objDCtiles[0], height, 0x8C0E),
            tile=lambda:self.setColumn(
                [self._iceclearabove] + self.objDCtiles[1][self.parityX()],
                height, 0x1625),
            last=lambda:self.setColumn(self.objDCtiles[2], height, 0x8C0C),
            shift=self.shifthoriz, length=width)

    objDDinterior = (0x8C0F,0x8C10,0x8C11,0x8C10,0x8C11,0x8C12,0x8C0F,0x8C10,
                     0x798C,0x798D,0x798E,0x798D,0x798F,0x7990,0x798C,0x7990,
                     0x7991,0x7992,0x7991,0x7993,0x7994,0x7997,0x7997,0x7997,
                     0x7997,0x7997,0x7997,0x7997,0x7997,0x7995,0x7996,0x7994,
                     0x7995,0x7996,0x7997,0x7997,0x7997,0x7997,0x7997,0x7997)
    def _objDDinterior(self):
        if self.relY <= 5:
            # was it really that important to use this RNG distribution?
            self.setTile(self.objDDinterior[
                (self.relX+random.randrange(4) & 7) + (self.relY-1)*8])
        else:
            self.setTile(0x7997)
    def objDD(self, width, height):
        self.setLine(lambda:self.setTile(0x8D8C+self.parityX(), major=False),
                     shift=self.shifthoriz, length=width)
        self.shiftvert()
        while self.relY != height:
            self.relX = 0
            self.setLine(
                first=0x110DD,  # to be implemented
                tile=self._objDDinterior,
                last=0x110DD,  # to be implemented
                shift=self.shifthoriz, length=width)
            self.shiftvert()

    def objDE(self, _, height):
        self.setColumn(tiles=(0x79A4,0x79A6), height=height, default=0x799B)
        self.relX = 1
        self.setColumn(tiles=(0x79A5,0x79A7), height=height, default=0x7999)

    def objDF(self, width, _):
        self.setLine(first=0x8D92, last=0x8D93,
                     tile=lambda:self.setTile(0x8D90+self.parityX()),
                     shift=self.shifthoriz, length=width)
        self.relY, self.relX = 1, 0
        self.setLine(first=0xA602, last=0xA603,
                     tile=lambda:self.setTile(0xA600+self.parityX()),
                     shift=self.shifthoriz, length=width)

    def objE0(self, _, height):
        self.setLine(first=0xA605, tile=0xA606,
                     shift=self.shiftvert, length=height)

    objE1captiles = ((0x2C0C,0x1527,0x2F0B),
                     (0x2C0E,0x1528,0x2F0D),
                     (0x2C10,0x1529,0x2F0F))
    def _objE1cap(self, tiles):
        tile = tiles[self.relX % 3]
        if 0x8D2A <= self.getTile() < 0x8D2E:
            tile += 1
        self.setTile(tile)
    def _objE1ground(self):
        tile = 0x8D2E + (self.relY+2 & 3)
        if 0x8D90 <= self.getTile() < 0x8D93:
            tile += 4
        self.setTile(tile)
    def objE1(self, width, height):
        tiles = random.choice(self.objE1captiles)
        self.setLine(lambda:self._objE1cap(tiles),
                     shift=self.shifthoriz, length=width)
        self.obj.lastX = self.obj.x + self.relX - 1
        for x in range(1, width, 3):
            self.relX, self.relY = x, 1
            self.setLine(first=0x8D29,
                         tile=lambda:self.setTile(0x8D2A + (self.relY+2 & 3)),
                         last=self._objE1ground, length1=self._objE1ground,
                         shift=self.shiftvert, length=height-1)

    objE2tiles = (  -1,  0x8D9A,0x8D9B,  -1,     -1,  0x8DA9,0x8DAA,  -1,  
                    -1,  0x8DB8,0x8DB9,  -1,     -1,  0x8DC6,0x8DC7,  -1,  
                  0x8D9C,0x8D9D,0x8D9E,0x8D9F, 0x8DAB,0x8DAC,0x8DAD,0x8DAE,
                  0x8DBA,0x8DBB,0x8DBC,0x8DBD, 0x8DC8,0x8DC9,0x8DCA,0x8DCB,
                  0x8D9A,0x8DA0,0x8DA0,0x8D9B, 0x8DA9,0x8DAF,0x8DAF,0x8DAA,
                  0x8DB8,0x8DBE,0x8DBE,0x8DB9, 0x8DC6,0x8DCC,0x8DCC,0x8DC7,
                  0x8DA1,0x8DA2,0x8DA3,0x8DA4, 0x8DB0,0x8DB1,0x8DB2,0x8DB3,
                  0x8DBF,0x8DC0,0x8DC1,0x8DC2, 0x8DCD,0x8DCE,0x8DCF,0x8DD0)
    def objE2(self, _, height):
        if height <= 0x10:
            self.setRect(self.objE2tiles, 4, height)
        else:
            self.setRect(self.objE2tiles, 4, 8)
            self.setRect(self.objE2tiles[0x20:], 4, height-8)

    def objE3(self, width, height):
        self.setLine(
            first=lambda:self.setColumn((0x8C03,0x8C07), height, 0x8C0B),
            tile=lambda:self.setColumn((self._iceclearabove,), height, 0),
            last=lambda:self.setColumn((0x8C00,0x8C04), height, 0x8C08),
            shift=self.shifthoriz, length=width)


    # Objects E4-EC: Flower tileset ground

    objE4tiles = (
        (  -1,    -1,  0x859A,0x859B,0x79DA,0x79DB),
        (  -1,    -1,  0x859F,0x85A0,0x79DD,0x79DE),
        (  -1,    -1,  0x859A,0x859C,0x79DD,0x79DE),
        (  -1,    -1,  0x859F,0x85A1,0x79DD,0x79DF),
        (  -1,    -1,  0x859A,0x859B,0x79DC,0x79DB),
        (  -1,    -1,  0x85A2,0x85A0,0x79DD,0x79DC),
        (  -1,  0x85C5,0x85A2,0x859D,0x79DA,0x79AC),
        (0x85C8,  -1,  0x85A3,0x85A4,0x79AD,0x79AF),
        (0x85C6,0x85C7,0x859E,0x859D,0x79DC,0x79DB),
        (0x85C8,0x85C5,0x85A3,0x85A4,0x79DC,0x79B6))
    objE5tiles = (
        (  -1,    -1,  0x85A8,0x85A7,0x0D0D,0x0C0C,0x79AD,0x79AC),
        (  -1,    -1,  0x85A8,0x85A7,0x0D0E,0x0C0C,0x79B6,0x79AE),
        (  -1,    -1,  0x85A8,0x85A6,0x0D0E,0x0C0B,0x79BD,0x79AE),
        (0x85C2,  -1,  0x85A9,0x85A6,0x0D0E,0x0C0C,0x79AD,0x79AF),
        (0x85C3,0x85C1,0x85AA,0x85A5,0x0D0E,0x0C0C,0x79B1,0x79B0))
    objE6tiles = (
        (  -1,  0x85B9,0x0814,0x79AA),
        (  -1,  0x85BA,0x0815,0x79AA),
        (  -1,  0x85B9,0x0816,0x79AB),
        (0x85C1,0x85BB,0x0816,0x79AB),
        (0x85C2,0x85BC,0x0814,0x79B6))
    objE7tiles = (
        (0x85A7,0x020A,0x030D,0x79B9),
        (0x85A7,0x020A,0x030D,0x79AC),
        (0x85A6,0x020B,0x030D,0x79B9),
        (0x85A7,0x020A,0x030D,0x79B6),
        (0x85B3,0x020A,0x030D,0x79B9))
    objE8tiles = (
        (  -1,    -1,  0x85AD,0x85B1,0x0F11,0x100E,0x79B2,0x79BE),
        (  -1,    -1,  0x85AD,0x85B1,0x0F10,0x100E,0x79AF,0x79B7),
        (  -1,    -1,  0x85AD,0x85B2,0x0F10,0x100F,0x79B3,0x79B4),
        (0x85C3,  -1,  0x85AE,0x85B1,0x0F10,0x100E,0x79C2,0x79B6),
        (0x85C2,0x85C3,0x85AF,0x85B0,0x0F11,0x100E,0x79B2,0x79BE))
    objE9tiles = (
        (  -1,  0x85BD,0x0A15,0x79B7),
        (  -1,  0x85BF,0x0A16,0x79B7),
        (  -1,  0x85BD,0x0A17,0x79B8),
        (0x85C3,0x85BE,0x0A17,0x79B8),
        (0x85C4,0x85C0,0x0A15,0x79AF))
    objEAtiles = (
        (0x85B8,0x050B,0x060D,0x79BA),
        (0x85B8,0x050B,0x060D,0x79AC),
        (0x85B7,0x050A,0x060D,0x79BA),
        (0x85B6,0x050B,0x060D,0x79AF),
        (0x85B6,0x050B,0x060D,0x79BA))
    objE4dist = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 4, 6, 8)
    objE5E6E8E9dist = (0, 1, 2, 3, 4, 0, 3, 4)
    objE7EAdist = (0, 1, 2, 3, 4, 0, 1, 3)

    def _objE4EArandinterior(self, startY):
        index = random.randrange(0x10) + 2*(self.relY - startY)
        if index <= 9:
            self.setTile(0x79BB+index)
        else:
            self.setTile(0x79E0)
    def _objE4EAflowercolumn(self, pattern, maxY):
        try:
            self.setTile(pattern[self.relY], major=self.relY)
        except IndexError:
            self._objE4EArandinterior(maxY)

    def objE4(self, width, height):
        height += 2
        self.y -= 2

        for i in range(abs(width)):
            if not self.parityX():
                pattern = self.objE4tiles[random.choice(self.objE4dist)]
            self.setLine(
                tile=lambda : self._objE4EAflowercolumn(
                    pattern[self.parityX()::2], 3),
                shift=self.shiftvert, length=height, finalshift=self.resetY)
            self.shifthoriz()

    objE6E7E9EAprop = {0xE6:(objE6tiles, objE5E6E8E9dist, 2, -1),
                       0xE7:(objE7tiles, objE7EAdist, 1, -2),
                       0xE9:(objE9tiles, objE5E6E8E9dist, 2, -1),
                       0xEA:(objEAtiles, objE7EAdist, 1, -2)}
    def objE6EA(self, width, height):
        tiles, dist, heightoffset, slope = self.objE6E7E9EAprop[self.obj.ID]

        height += heightoffset
        self.y -= heightoffset

        for i in range(abs(width)):
            pattern = tiles[random.choice(dist)]
            self.setLine(
                tile=lambda : self._objE4EAflowercolumn(pattern, 4),
                shift=self.shiftvert, length=height, finalshift=self.resetY)
            height += slope
            if height <= 0:
                break
            self.shifthoriz(slope=slope)

    objE5E8tiles = {0xE5:objE5tiles, 0xE8:objE8tiles}
    def objE5E8(self, width, height):
        height += 2
        self.y -= 2

        for i in range(abs(width)):
            if not self.parityX():
                pattern = self.objE5E8tiles[self.obj.ID][random.choice(
                    self.objE5E6E8E9dist)]
            self.setLine(
                tile=lambda : self._objE4EAflowercolumn(
                    pattern[self.parityX()::2], 4),
                shift=self.shiftvert, length=height, finalshift=self.resetY)
            height -= self.parityX()
            if height <= 0:
                break
            self.shifthoriz(slope=-self.parityX())

    objEBECcolumnside = (0x79AD,0x79AE,0x79B5,0x79DD)
    objEBECprop = {0xEB:{"surface":objE7tiles, "maintile":0x79D6, "awayside":-1},
                    0xEC:{"surface":objEAtiles, "maintile":0x79D8, "awayside":1}}
    def _objEBECcolumn(self, height):
        self.setTile(
            self.objEBECprop[self.obj.ID]["maintile"] + self.parityY())

        awayside = self.objEBECprop[self.obj.ID]["awayside"]

        # EB-EC check the tiles on either side of the column 
        if self.getTile(offsetX=-awayside) >> 8 == 0x79:
            self.relX -= awayside
            self.setTile(random.choice(self.objEBECcolumnside))
            self.relX += awayside
        awaytile = self.getTile(offsetX=awayside)
        if self.relY+1 < height and (
                awaytile >> 8 in (0x03,0x06,0x08,0x0A,0x0C,0x10) or
                0x85A8 <= awaytile <= 0x85AF):
            self.setTile(0x79C8)
    def objEBEC(self, width, height):
        height += 1
        self.y -= 1

        for i in range(abs(width)):
            # relY <= 2 defers to object E7/EA's code
            pattern = self.objEBECprop[self.obj.ID]["surface"][
                random.choice(self.objE7EAdist)]
            self.setLine(tile=lambda : self._objE4EAflowercolumn(pattern, 4),
                         shift=self.shiftvert, length=min(3, height))

            if self.relY < height:
                self.setLine(tile=lambda : self._objEBECcolumn(height),
                             shift=self.shiftvert, length=height-3)
            self.shifthoriz()
            self.relY = 0


    def objF5(self, width, height):
        self.setLine(tile=lambda : self.setLine(
            first=0x8413, tile=0x2910,
            shift=self.shiftvert, length=height, finalshift=self.resetY),
                     shift=self.shifthoriz, length=width)

    def _objF6if(self):
        if not self.getTile(): self.setTile(0x9D8B)
    def objF6(self, width, height):
        self.setRect(self._objF6if, width, height)

    def objF7FC(self, width, _):
        starttile = 0x01D1 + (self.obj.ID - 0xF7) * 3
        self.setLine(first=starttile, tile=starttile+1, last=starttile+2,
                     shift=self.shifthoriz, length=width)

    objFEtiles = (0xA800,0xA801,0xA802,0xA803,0xA804,0xA805,0xA806,0xA807,
                  0xA808,0xA809,0xA80A,0xA80B,0xA80C,0xA80D,0xA80E,0xA80F,
                  0xA810,0xA811,0xA812,0xA813,0xA814,0xA815,0xA816,0xA817,
                  0xA818,0xA819,0xA81A,0xA81B,0xA81C,0xA81D,0xA81E,0xA81F,
                  0xA700,0xA701,0xA702,0xA703,0xA704,0xA705,0xA706,0xA707)
    def objFE(self, width, height):
        self.setLine(
            tile=lambda : self.setColumn(
                tiles=self.objFEtiles[self.relX%8::8],
                default=0x110FE,  # overflow: display red warning tile
                height=height),
            shift=self.shifthoriz, length=width)

    ## Define custom object functions

    def advtile(self, width, height):
        # Arbitrary single tile
        self.setRect(self.obj.extID, width, height)

    ## Index functions by object/extended ID

    SMA3objectcode = [
        # extended objects
        [extR,extR,extR,extR,extR,extR,extR,extR,  # 00-07
        extR,extR,extR,extR,ext0C,extR,extR,extS,   # 08-0F
        ext10,extR,extR,extR,ext1415,ext1415,ext16,extS,   # 10-17
        extR,extR,extR,extR,extR,extR,ext1E,extR,   # 18-1F
        None,None,None,None,None,None,None,None,   # 20-27
        None,None,None,None,None,None,None,None,   # 28-2F
        ext30,ext31,extS,extS,extS,extS,extS,extS,   # 30-37
        extS,extS,extS,extS,extS,extS,extS,extS,   # 38-3F
        extS,extS,extS,extS,extS,extS,ext46,extR,   # 40-47
        ext48,extR,ext4A,ext4B,extS,extR,extR,extS,   # 48-4F
        ext50A8,extS,ext52,ext53,ext545C,ext545C,extR,extR,   # 50-57
        extR,ext545C,extR,extR,ext545C,extR,extS,extR,   # 58-5F
        extR,extR,extR,extR,extR,extR,extR,ext67,   # 60-67
        extS,extS,extR,extR,extR,extR,extR,extR,   # 68-6F
        extR,extR,extR,extR,extR,extR,extR,extR,   # 70-77
        extR,extR,extR,extR,extR,extR,extS,extS,   # 78-7F
        extS,extR,extR,extR,extR,extR,extR,extR,   # 80-87
        None,ext898A,ext898A,ext8B8C,ext8B8C,ext8D,extS,extS,   # 88-8F
        extS,extS,extR,extR,extR,extR,extR,extR,   # 90-97
        extR,extR,extR,extR,extR,extR,ext9E9F,ext9E9F,   # 98-9F
        None,None,None,None,extR,extR,extR,extS,   # A0-A7
        ext50A8,extR,extR,extR,extR,extADB2,extADB2,extADB2,   # A8-AF
        extADB2,extADB2,extADB2,extR,extB4B7,extB4B7,extB4B7,extB4B7,   # B0-B7
        extR,extR,extBABF,extBABF,extBABF,extBABF,extBABF,extBABF,   # B8-BF
        extC0,extC1,extR,extR,extS,extR,extR,extR,   # C0-C7
        extR,extR,extS,extS,extS,extS,extS,extS,   # C8-CF
        extS,extS,extS,extS,extD4DF,extD4DF,extD4DF,extD4DF,   # D0-D7
        extD4DF,extD4DF,extD4DF,extD4DF,extD4DF,extD4DF,extD4DF,extD4DF,   # D8-DF
        extR,None,None,None,None,None,None,None,   # E0-E7
        None,None,None,None,None,None,None,None,   # E8-EF
        None,None,None,None,None,None,None,None,   # F0-F7
        None,None,None,extFB,None,None,extFEFF,extFEFF,   # F8-FF
        ],
        # standard objects
             obj01,obj0203,obj0203,obj0409,obj0409,obj0409,obj0409,   # 01-07
        obj0409,obj0409,obj0A0B,obj0A0B,obj0C2B,obj0D,obj0E0F,obj0E0F,   # 08-0F
        obj1012,obj1012,obj1012,obj13,obj14,obj15,obj16,obj17,   # 10-17
        obj18,obj19,obj1A,obj1B,obj1C,objS,objS,None,   # 18-1F
        None,obj21,obj2223,obj2223,obj24,obj2526,obj2526,obj2728,   # 20-27
        obj2728,obj292A,obj292A,obj0C2B,obj2C,obj2D,obj2E,obj2F,   # 28-2F
        None,None,None,None,obj34,obj35,None,obj37,   # 30-37
        None,None,None,None,obj3CF4,obj3D,obj3E,obj3F40,   # 38-3F
        obj3F40,None,None,None,None,None,None,None,   # 40-47
        None,obj49,obj4A,obj4B4D,obj4B4D,obj4B4D,obj4Etemp,None,   # 48-4F
        obj50,obj51,obj52,None,None,None,None,obj57,   # 50-57
        obj58,None,None,None,None,None,None,None,   # 58-5F
        None,None,None,obj63,obj63,advtile,obj66,obj67,   # 60-67
        objS,obj69,obj6A,obj6B,objS,obj6D,obj6E,obj6F,   # 68-6F
        objYX,objYX,objYX,obj7376,obj7376,obj7376,obj7376,objS,   # 70-77
        obj7879,obj7879,None,None,None,None,obj7E,obj7F,   # 78-7F
        None,None,objS,objC4C9,objC4C9,None,None,None,   # 80-87
        None,obj89,objS,objS,None,obj8D,objYX,obj8F,   # 88-8F
        obj90,obj9192,obj9192,obj93,objYX,objYX,objYX,objYX,   # 90-97
        obj98,obj99,None,None,None,obj9D,objS,obj9F,   # 98-9F
        objA0A2,objA0A2,objA0A2,objYX,objYX,objA5,objA6,objA7,   # A0-A7
        None,None,objAAAB,objAAAB,objAC,objACAD,objAE,objAF,   # A8-AF
        objB0,objB1,objB2B9,objB2B9,objB2B9,objB2B9,objB2B9,objB2B9,   # B0-B7
        objB2B9,objB2B9,objBA,objBB,objBC,objBD,None,None,   # B8-BF
        None,None,objC2C3,objC2C3,objC4C9,objC4C9,objC4C9,objC4C9,   # C0-C7
        objC4C9,objC4C9,objCA,None,None,None,objCE,objCFD0,   # C8-CF
        objCFD0,objS,objS,objD3,None,None,None,None,   # D0-D7
        objD8,objD9,objS,objDB,objDC,objDD,objDE,objDF,   # D8-DF
        objE0,objE1,objE2,objE3,objE4,objE5E8,objE6EA,objE6EA,   # E0-E7
        objE5E8,objE6EA,objE6EA,objEBEC,objEBEC,None,None,None,   # E8-EF
        None,None,None,None,obj3CF4,objF5,objF6,objF7FC,   # F0-F7
        objF7FC,objF7FC,objF7FC,objF7FC,objF7FC,None,objFE]   # F8-FE

    implementedcount = (0xFE - SMA3objectcode.count(None),
                        0x100 - SMA3objectcode[0].count(None))

    @staticmethod
    def _genericobjfunc(ID):
        return lambda self, width, height : self.setRect(
            0x10000+ID, width, height)

    @staticmethod
    def _genericextobjfunc(ID):
        return lambda self : self.setTile(0x10E00+ID)

    for ID in range(0x100):
        if SMA3objectcode[0][ID] is None:
            SMA3objectcode[0][ID] = _genericextobjfunc(ID)
    for ID in range(1, 0xFF):
        if SMA3objectcode[ID] is None:
            SMA3objectcode[ID] = _genericobjfunc(ID)

########

if __name__ == "__main__":
    implementedcount = L1Constructor.implementedcount
    print("Object code implemented: "
          "Total ", sum(implementedcount), "/466, "
          "Extended ", implementedcount[1], "/213, ",
          "Standard ", implementedcount[0], "/253", sep="")
    tilemap = L1Constructor(
        SMA3.Sublevel.importbyID("sma3.gba", 0xD6)).tilemap
