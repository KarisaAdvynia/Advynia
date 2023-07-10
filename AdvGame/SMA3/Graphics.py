"""SMA3 Graphics
Classes and functions for SMA3 graphics and palettes."""

# standard library imports
from collections import defaultdict

# import from other files
import AdvGame
from AdvGame import GBA, GameGraphics
from AdvGame.SMA3 import Pointers

# Level graphics

class LayerVRAM(GameGraphics):
    """Simulated GBA VRAM, of the layer tiles loaded during a standard SMA3
    sublevel. Used to display game graphics in the GUI. Includes functions to
    load specific tilesets."""
    def __init__(self, filepath, layer1ID=None, layer2ID=None, layer3ID=None,
                 animID=None):
        GameGraphics.__init__(self, tilesize=0x20)

        self.tilemap = {}
        self.animated = GameGraphics()
        self.layer1ID = None
        self.layer2ID = None
        self.layer3ID = None
        self.animID = None

        # load global graphics
        for ptr, offset, size in Pointers.levelgfxlayerglobal:
            self.replacegraphics(GameGraphics(GBA.importdata(
                filepath, GBA.readptr(filepath, ptr), size)), offset)

        # load global animated graphics, first frame
        for ptr, offset, size in Pointers.levelgfxanimglobal:
            self.replacegraphics(GameGraphics(GBA.importdata(
                filepath, ptr, size)), offset)

        if layer1ID is not None:
            self.loadL1graphics(filepath, layer1ID)
        if layer2ID is not None:
            self.loadL2graphics(filepath, layer2ID)
        if layer3ID is not None:
            self.loadL3graphics(filepath, layer3ID)
        if animID is not None:
            self.loadanimgraphics(filepath, animID)

    def loadL1graphics(self, filepath, tilesetID):
        self.layer1ID = tilesetID
        tableptr = Pointers.levelgfxL1 + tilesetID*0xC
        if tilesetID > 0xF:  # higher values are treated as W6 alternate tilesets
            tableptr = Pointers.levelgfxL1W6 + (tilesetID-0x10)*0xC
        self._loadgraphicsloop(filepath, tableptr, (0x2000, 0x3000, 0))

        if self.animID in (0x7, 0xD):
            # animation 7 uses different graphics in tileset A
            self.loadanimgraphics(filepath, 7)

    def loadL2graphics(self, filepath, imageID):
        self.layer2ID = imageID
        tableptr = Pointers.levelgfxL2 + imageID*8
        self._loadgraphicsloop(filepath, tableptr, (0x5000, 0x6000))
        self.tilemap[2] = self.loadL23image(filepath, 2, imageID)

    def loadL3graphics(self, filepath, imageID):
        self.layer3ID = imageID
        tableptr = Pointers.levelgfxL3 + imageID*8
        self._loadgraphicsloop(filepath, tableptr, (0x7000, 0x8000))
        self.tilemap[3] = self.loadL23image(filepath, 3, imageID)

    def loadanimgraphics(self, filepath, animID):
        self.animID = animID
        self.animated.clear()  # remove old graphics overrides

        animgfxptrs = []
        if animID in Pointers.levelgfxanimIDs:
            animgfxptrs += Pointers.levelgfxanimIDs[animID]

        match animID:
            case 0x06:
##                if self.layereffectsID == 0xA:
##                    animgfxptrs += Pointers.levelgfxanimIDs[(0x06,0x0A)]
                # else, animation 06 uses the same graphics as 05
                animgfxptrs += Pointers.levelgfxanimIDs[0x5]
            case 0x0B:  # animation 0B loads both 02 and 0A
                animgfxptrs += Pointers.levelgfxanimIDs[0x2]
                animgfxptrs += Pointers.levelgfxanimIDs[0xA]
            case 0x0D:  # animation 0D loads both 05 and 07
                animgfxptrs += Pointers.levelgfxanimIDs[0x5]
                animgfxptrs += Pointers.levelgfxanimIDs[0x7]
            case 0x0E:  # animation 0E loads both 05 and 0C
                animgfxptrs += Pointers.levelgfxanimIDs[0x5]
                animgfxptrs += Pointers.levelgfxanimIDs[0xC]
            case 0x11:  # animation 11 loads both 03 and 0C
                animgfxptrs += Pointers.levelgfxanimIDs[0x3]
                animgfxptrs += Pointers.levelgfxanimIDs[0xC]

        if animID in (0x07, 0x0D) and self.layer1ID & 0xF == 0xA:
            # animation 07 uses different graphics in tileset A
            animgfxptrs[-4:] = Pointers.levelgfxanimIDs[(0x07,0x0A)]

        if animgfxptrs:
            for ptr, offset, size in animgfxptrs:
                self.animated.replacegraphics(GameGraphics(GBA.importdata(
                    filepath, ptr, size)), offset)
        elif animID == 0:  # overwrite animated region with blank tiles
            self.animated.replacegraphics(GameGraphics(bytes(0x800)), 0x4000)
        elif animID == 0x09:  # compressed animation
            with GBA.Open(filepath, "rb") as f:
                f.readseek(Pointers.levelgfxanim09)
                graphics = GameGraphics(f.read_decompress())
            # not entirely documented; these offsets are estimates
            self.animated.replacegraphics(graphics[0x170:0x178], 0x8C00)
            self.animated.replacegraphics(graphics[0x178:0x180], 0x8E00)
        elif animID == 0x12:  # compressed animation
            with GBA.Open(filepath, "rb") as f:
                f.readseek(Pointers.levelgfxanim12)
                graphics = GameGraphics(f.read_decompress())
            self.animated.replacegraphics(graphics[0:0x80], 0)
            self.animated.replacegraphics(graphics[0x80:0x90], 0x3E00)

    def _loadgraphicsloop(self, filepath, tableptr, offsets):
        for offset in offsets:
            graphicsptr = GBA.readmultiptr(filepath, tableptr, 2)
            self.replacegraphics(GameGraphics(GBA.importdata(
                filepath, graphicsptr, -1)), offset)
            tableptr += 4

    def loadL23image(self, filepath, layer, imageID):
        "Import the tilemap for a layer 2 or 3 image."
        with GBA.Open(filepath, "rb") as f:
            ptr = f.readptr(Pointers.leveltilemapL23[layer], imageID)
            tilemapraw = f.read_decompress(ptr)
        tilemap = []
        if len(tilemapraw) % 2 != 0:
            raise ValueError(f"Tilemap data length {len(tilemapraw):#x} "
                "does not correspond to an integer number of tiles.")
        for i in range(len(tilemapraw)//2):
            tilemap.append(int.from_bytes(tilemapraw[2*i:2*i+2], "little"))
        return tilemap

class SpriteVRAM(GameGraphics):
    def __init__(self, filepath, spritetileset=None, stripeIDs=None):
        GameGraphics.__init__(self, tilesize=0x20)

        self.stripeIDs = bytearray(6)
        self.stripes = {}

        # load global graphics
        for ptr, offset, size in Pointers.levelgfxspriteglobal:
            self.replacegraphics(GameGraphics(GBA.importdata(
                filepath, GBA.readptr(filepath, ptr), size)), offset)

        if stripeIDs is not None:
            for i, stripeID in enumerate(stripeIDs):
                self.loadstripe(filepath, i, stripeID)
        elif spritetileset is not None:
            self.loadstripes(filepath, spritetileset)

    def loadstripes(self, filepath, spritetileset):
        with GBA.Open(filepath, "rb") as f:
            idptr = f.readptr(Pointers.levelgfxstripeIDs) + spritetileset*6
            graphicsptrs = f.readptr(Pointers.levelgfxstripe) +\
                           spritetileset*0x18

            stripeptrs = []
            f.seek(idptr)
            self.stripeIDs[:] = f.read(6)
            for i in range(6):
                stripeptrs.append(f.readmultiptr(graphicsptrs + 4*i, 2))

        self.stripes.clear()
        with GBA.Open(filepath, "rb") as f:
            for stripeID, graphicsptr in zip(self.stripeIDs, stripeptrs, strict=True):
                self.stripes[stripeID] = GameGraphics(
                    f.read_decompress(graphicsptr))

    def loadstripe(self, filepath, index, stripeID):
        oldID = self.stripeIDs[index]
        if oldID and self.stripeIDs.count(oldID) == 1:
            # delete graphics only if there's exactly one instance of the old ID
            del self.stripes[oldID]

        self.stripeIDs[index] = stripeID
        ptr = Pointers.levelgfxstripesbyID[stripeID]
        with GBA.Open(filepath, "rb") as f:
            f.readseek(ptr)
            self.stripes[stripeID] = GameGraphics(f.read_decompress())

class _PaletteColorTypes(list):
    """Holds the color type strings of LevelPalette.
    This class exists primarily to ensure "Palette Animation XX" and
    "Transparent" override any assigned color types."""
    def __init__(self, parent, length):
        self += [""] * length
        self.parent = parent

    def __getitem__(self, index):
        if index and index % 0x10 == 0:
            return "Transparent"
        elif self.parent.animated[index] is not None:
            return f"Palette Animation {self.parent.animID:02X}"
        else:
            return super().__getitem__(index)

class LevelPalette(list):
    """Simulated palette during a standard SMA3 sublevel, in 15-bit color
    format. Includes main 0x200-byte palette and 0x18-byte background gradient."""
    def __init__(self, filepath, layer1ID=None, layer2ID=None, layer3ID=None,
                 layer3image=None, BGpalID=None, spritepalID=None, animID=None,
                 yoshipalID=0, showredcoins=True):
        self.showredcoins = showredcoins
        self.BGgradient = [0]*0x18
        self._palette = [0]*0x200
        self.animated = [None]*0x200
        self.colortype = _PaletteColorTypes(self, 0x200)

        self.layer1ID = None
        self.layer2ID = None
        self.layer3ID = None
        self.layer3image = None
        self.BGpalID = None
        self.animID = None

        with GBA.Open(filepath, "rb") as f:
            # load global layer 1 colors (fixed color table index of 0x98)
            f.seek(Pointers.colortable + 0x98)
            for paletterow in (1, 2, 3):
                for i in range(1, 0xC):
                    colorID = paletterow<<4 | i
                    self._palette[colorID] = f.readint(2)
                    self.colortype[colorID] = "Layer 1 Global"

            # load global sprite colors
            for ptr, start, stop, colortype in (
                    (Pointers.levelpal100, 0x100, 0x150, "Sprite Global"),
                    (Pointers.levelpal180, 0x180, 0x1F8, "Sprite Global"),
                    (Pointers.levelpal1F8, 0x1F8, 0x200, "Message Global"),
                    ):
                f.readseek(ptr)
                for colorID in range(start, stop):
                    self._palette[colorID] = f.readint(2)
                    self.colortype[colorID] = colortype

            self._setuninitialized(0x80, 0xD0)

        for arg, loadmethod in (
                (BGpalID, self.loadBGpalette),
                (layer1ID, self.loadL1palette),
                (layer2ID, self.loadL2palette),
                (layer3ID, self.loadL3palette),
                (layer3image, self.loadL3imagepal),
                (spritepalID, self.loadspritepalette),
                (animID, self.loadanimpalette),
                ):
            if arg is not None:
                loadmethod(filepath, arg)
        self.loadyoshipalette(filepath, yoshipalID)

        self.colortype[0xF0:0x100] = ["Red Coin Palette"]*0x10

    def __getitem__(self, key):
        if isinstance(key, slice):
            indices = slice.indices(key, len(self._palette))
            output = []
            for i in range(*indices):
                if self.animated[i] is not None:
                    output.append(self.animated[i])
                else:
                    output.append(self._palette[i])
            return output
        elif self.animated[key] is not None:
            return self.animated[key]
        else:
            return self._palette[key]

    def loadBGpalette(self, filepath, paletteID):
        self.BGpalID = paletteID
        with GBA.Open(filepath, "rb") as f:
            colorindex = paletteID*2
            f.seek(Pointers.colortable + colorindex)
            self._palette[0] = f.readint(2)
            self.colortype[0] = f"Background Color {paletteID:02X}"

            for colorID in range(0x80, 0xA0, 4):
                # account for layer 3 image region copying background color
                if self.colortype[colorID].startswith("Background Color"):
                    self._palette[colorID] = self._palette[0]
                    self.colortype[colorID] = self.colortype[0]

            if paletteID >= 0x10:
                f.seek(f.readptr(Pointers.levelBGgradient) + paletteID*4)
                colorindex = f.readint(2)
                f.seek(Pointers.colortable + colorindex)
                for i in range(0x18):
                    self.BGgradient[i] = f.readint(2)
            else:
                self.BGgradient = [self._palette[0]]*0x18

    def loadL1palette(self, filepath, paletteID):
        self.layer1ID = paletteID
        colortype = f"Layer 1 Palette {paletteID:X}"

        with GBA.Open(filepath, "rb") as f:
            f.seek(f.readptr(Pointers.levelpalL1) + paletteID*2)
            colorindex = f.readint(2)
            f.seek(Pointers.colortable + colorindex)
            # layer 1 palettes load to 2 distinct rectangular regions
            for paletteIDrange, colorIDrange in (((4, 5), range(1, 0x10)),
                                                 ((1, 2, 3), range(0xC, 0x10))):
                for paletterow in paletteIDrange:
                    for i in colorIDrange:
                        colorID = paletterow<<4 | i
                        self._palette[colorID] = f.readint(2)
                        self.colortype[colorID] = colortype

        # red coin palette is a copy of palette 1 or 2
        self.setRedCoinPalette()

    def setRedCoinPalette(self, newvalue=None):
        if newvalue is not None:
            self.showredcoins = newvalue
        if self.showredcoins:
            self._palette[0xF0:0x100] = self._palette[0x10:0x20]
        else:
            self._palette[0xF0:0x100] = self._palette[0x20:0x30]

    def loadL2palette(self, filepath, paletteID):
        self.layer2ID = paletteID
        colortype = f"Layer 2 Palette {paletteID:02X}"

        with GBA.Open(filepath, "rb") as f:
            f.seek(f.readptr(Pointers.levelpalL2) + paletteID*2)
            colorindex = f.readint(2)
            f.seek(Pointers.colortable + colorindex)
            for paletterow in (6, 7):
                for i in range(1, 0x10):
                    colorID = paletterow<<4 | i
                    self._palette[colorID] = f.readint(2)
                    self.colortype[colorID] = colortype

    def loadL3palette(self, filepath, paletteID):
        self.layer3ID = paletteID
        colortype = f"Layer 3 Palette {paletteID:02X}"
        with GBA.Open(filepath, "rb") as f:
            f.seek(f.readptr(Pointers.levelpalL3) + paletteID*2)
            colorindex = f.readint(2)
            f.seek(Pointers.colortable + colorindex)
            for colorID in range(1, 0x10):
                self._palette[colorID] = f.readint(2)
                self.colortype[colorID] = colortype

    L3images = (0x0D, 0x18, 0x23, 0x20, 0x13, 0x2A, 0x0C, 0x05)
    def loadL3imagepal(self, filepath, imageID):
        self.layer3image = imageID
        try:
            index = self.L3images.index(imageID)
        except ValueError:
            stop = 0x80
        else:
            stop = 0x90
            if imageID == 0x18:
                stop = 0xA0

            with GBA.Open(filepath, "rb") as f:
                ptr = f.readptr(f.readptr(Pointers.levelpalL3image) + index*4)
                colortype = f"Layer 3 Image {imageID:02X}"

                if imageID == 0x23 and self.layer3ID == 0x1C:
                    # game hardcodes a different palette for this combo
                    ptr += 0x20
                    colortype = "Layer 3 Image 23 + Palette 1C"

                f.seek(ptr)
                for colorID in range(0x80, stop):
                    if colorID & 3:
                        self._palette[colorID] = f.readint(2)
                        self.colortype[colorID] = colortype
                    else:
                        f.read(2)  # discard next 2 bytes
                        if colorID & 0xF:
                            # copy background color
                            self._palette[colorID] = self[0]
                            self.colortype[colorID] = self.colortype[0]

        self._setuninitialized(stop, 0xA0)

    def loadspritepalette(self, filepath, paletteID):
        colortype = f"Sprite Palette {paletteID:X}"
        with GBA.Open(filepath, "rb") as f:
            ptr = f.readptr(f.readptr(Pointers.levelpalsprite), paletteID)
            f.seek(ptr)
            for colorID in range(0x160, 0x180):
                self._palette[colorID] = f.readint(2)
                self.colortype[colorID] = colortype
            self._setunusedDE(f, paletteID, 0xE,
                              "SNES leftover/Sprite Palette ")

    def loadyoshipalette(self, filepath, paletteID):
        colortype = f"Yoshi Palette {paletteID:X}"
        with GBA.Open(filepath, "rb") as f:
            f.seek(Pointers.levelpalyoshi + 0x20*paletteID)
            for colorID in range(0x150, 0x160):
                self._palette[colorID] = f.readint(2)
                self.colortype[colorID] = colortype
            self._setunusedDE(f, paletteID, 0xD,
                              "SNES leftover/Yoshi Palette ")

    def loadanimpalette(self, filepath, animID):
        self.animID = animID
        self.animated = [None]*0x200  # remove old palette overrides

        animpalptrs = []
        if animID in Pointers.levelpalanim:
            animpalptrs += Pointers.levelpalanim[animID]

        with GBA.Open(filepath, "rb") as f:
            for ptr, startindex, num in animpalptrs:
                f.seek(ptr)
                for colorID in range(startindex, startindex+num):
                    self.animated[colorID] = f.readint(2)

    def _setunusedDE(self, f, paletteID, paletterow, basestr):
            f.seek(f.readptr(Pointers.levelpalunusedDE) + paletteID*2)
            colorindex = f.readint(2)
            f.seek(Pointers.colortable + colorindex)
            for colorID in range((paletterow << 4) + 1, (paletterow + 1) << 4):
                self._palette[colorID] = f.readint(2)
                self.colortype[colorID] = basestr + f"{paletteID:X}"

    def _setuninitialized(self, start, stop):
        for colorID in range(start, stop):
            if colorID & 0xF != 0:
                self._palette[colorID] = 0x7C1F # magenta to signal uninitialized
        self.colortype[start:stop] = ["Uninitialized"] * (stop-start)

    def row(self, paletteID):
        """Returns one 0x10-color palette, for use in coloring 8x8 tiles."""
        return self._palette[paletteID*0x10 : (paletteID+1)*0x10]

def importL1_8x8tilemaps(filepath):
    "Import the 8x8 tilemap for each layer 1 16x16 tile ID."

    with GBA.Open(filepath, "rb") as f:
        f.seek(Pointers.tilemapL1_8x8)
        return _importtilemaptables(f, _importL1_8x8tilemaps_func, {}, 8)

def _importL1_8x8tilemaps_func(f):
    "Function passed to _importtilemaptables by importL1_8x8tilemaps"
    tilemap = []
    for j in range(4):
        tilemap.append(f.readint(2))
    return tilemap

def importL0flags(filepath):
    "Import the layer 0 8x8 tile flags for each layer 1 16x16 tile ID."

    with GBA.Open(filepath, "rb") as f:
        f.seek(Pointers.tilemapL0flags)
        data = _importtilemaptables(
            f, _importL0flags_func, defaultdict(lambda : [0, 0, 0, 0]), 1)

    if 0x6001 not in data:  # account for vanilla overflow, if unchanged
        data[0x6001] = data[0x6100].copy()
    return data

def _importL0flags_func(f):
    "Function passed to _importtilemaptables by importL0flags"
    flags = f.read(1)[0]
    return [flags&8, flags&4, flags&2, flags&1]

def _importtilemaptables(f, importfunc, outputdict, bytespertile):
    "Shared code for importing data indexed by layer 1 16x16 tile ID."

    ptrs = []
    for i in range(0xA9):
        ptrs.append(f.readint(4))
    ptrs.append(Pointers.tilemapL1_8x8)
    # last entry of vanilla tilemap table ends with the pointer table itself

    for highbyte in range(0xA9):
        f.seek(ptrs[highbyte])
        # read until next pointer, or 0x100 table entries (in case of edited
        #  pointer), whichever comes first
        tile16count = min((ptrs[highbyte+1] - ptrs[highbyte]) // bytespertile,
                          0x100)

        for tile16 in range(highbyte << 8, (highbyte << 8) + tile16count):
            outputdict[tile16] = importfunc(f)

    return outputdict


# Text graphics

class Font(GameGraphics):
    def __init__(self, filepath, font="main"):
        "Load the main or credits SMA3 font."

        GameGraphics.__init__(self, tilesize=0xC)
        textattr = Pointers.textgraphics[font]
        start = textattr.start

        self.widths = bytearray(start)
        with GBA.Open(filepath, "rb") as f:
            f.seek(textattr.graphicsptr)
            rawdata = f.read(textattr.charlength*0xC)
            f.seek(textattr.widthptr)
            self.widths += f.read(textattr.charlength)
        self.replacegraphics(GameGraphics(bytes(start*0xC), tilesize=0xC))
        self.replacegraphics(GameGraphics(rawdata, tilesize=0xC), start*0xC)

def exporttextgraphics(f, exportfilepath, font="main"):
    """Export SMA3's variable-width font graphics to a pixel graphics file.

    The export format expands each character's graphics from 8x12 to 8x16,
    and arranges them vertically as viewed in 8x8 tile editors, so that they're
    reasonably editable. The character width is indicated with an underline."""

    textattr = Pointers.textgraphics[font]
    charlength = textattr.charlength

    f.seek(textattr.graphicsptr)
    textgraphicsraw = f.read(charlength*0xC)
    f.seek(textattr.widthptr)
    widths = f.read(charlength)

    bitlines = (0b00000000, 0b10000000, 0b11000000, 0b11100000, 0b11110000,
                0b11111000, 0b11111100, 0b11111110, 0b11111111)

    with open(exportfilepath, "wb") as f:
        # Fill with empty space. Should be 0x1000, but it won't display
        #  in YYCHR without at least 0x2000
        f.write(bytes(0x2000))
        for charID in range(charlength):
            offset = charID // 0x10 * 0x100 + charID % 0x10 * 8

            # first 8 8px rows
            f.seek(offset)
            f.write(textgraphicsraw[charID*12 : charID*12 + 8])

            # remaining 4 8px rows
            f.seek(offset + 0x80)
            f.write(textgraphicsraw[charID*12 + 8 : charID*12 + 12])

            # use padding area to represent width
            f.seek(offset + 0x85)
            try:
                widthline = bytes((bitlines[widths[charID]],))
            except IndexError:
                widthline = bytes((bitlines[0],))
            widthline += b"\x80"  # hook to mark left edge of line
            f.write(widthline)

def importtextgraphics(filepath, font="main"):
    """Import SMA3's variable-width font graphics from a pixel graphics file,
    converting them back to their in-game format. Remaining pixels are ignored.
    Returns a bytearray."""

    charlength = Pointers.textgraphics[font].charlength
    output = bytearray()
    with open(filepath, "rb") as f:
        for charID in range(charlength):
            offset = charID // 0x10 * 0x100 + charID % 0x10 * 8

            # first 8 8px rows
            f.seek(offset)
            output += f.read(8)

            # remaining 4 8px rows
            f.seek(offset + 0x80)
            output += f.read(4)
    return output

def exportmessageimages(f, exportfilepath, bytelength=0x1F00):
    """Export the images used in SMA3 standard messages to a pixel graphics
    file."""

    ptr = f.readptr(Pointers.messageimages)
    f.seek(ptr)
    rawdata = f.read(bytelength)

    output = bytearray()
    for tileY in range(bytelength >> 4):
        for tileX in range(0x10):
            i = tileY << 7 | tileX
            output += rawdata[i:i+0x80:0x10]

    with open(exportfilepath, "wb") as f:
        f.write(output)
        if bytelength < 0x2000:
            f.write(bytes(0x2000 - bytelength))

def importmessageimages(filepath, bytelength=0x1F00):
    """Import the images used in SMA3 standard messages from a pixel graphics
    file, converting them back to their in-game format.
    Returns a bytearray."""

    data = open(filepath, "rb").read(bytelength)
    output = bytearray()
    for tileY in range(bytelength >> 4):
        for pixelY in range(8):
            i = tileY << 7 | pixelY
            output += data[i:i+0x80:8]
    return output

    
