"""SMA3 Graphics
Classes and functions for SMA3 graphics and palettes."""

# standard library imports
import os

# import from other files
from AdvGame import AdvGame, GBA
from AdvGame.SMA3 import Pointers
GameGraphics = AdvGame.GameGraphics  # shortened name

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

        # overwrite old animation with blank graphics
        self.animated.clear()

        animgfxptrs = []
        if animID in Pointers.levelgfxAnimIDs:
            animgfxptrs += Pointers.levelgfxAnimIDs[animID]

        if animID == 0x06:
##            if self.layereffectsID == 0xA:
##                animgfxptrs += Pointers.levelgfxAnimIDs[(0x06,0x0A)]
            # else, animation 06 uses the same graphics as 05
            animgfxptrs += Pointers.levelgfxAnimIDs[0x5]
        if animID == 0x0B:  # animation 0B loads both 02 and 0A
            animgfxptrs += Pointers.levelgfxAnimIDs[0x2]
            animgfxptrs += Pointers.levelgfxAnimIDs[0xA]
        elif animID == 0x0D:  # animation 0D loads both 05 and 07
            animgfxptrs += Pointers.levelgfxAnimIDs[0x5]
            animgfxptrs += Pointers.levelgfxAnimIDs[0x7]
        elif animID == 0x0E:  # animation 0E loads both 05 and 0C
            animgfxptrs += Pointers.levelgfxAnimIDs[0x5]
            animgfxptrs += Pointers.levelgfxAnimIDs[0xC]
        elif animID == 0x11:  # animation 11 loads both 03 and 0C
            animgfxptrs += Pointers.levelgfxAnimIDs[0x3]
            animgfxptrs += Pointers.levelgfxAnimIDs[0xC]

        if animID in (0x07, 0x0D) and self.layer1ID == 0xA:
            # animation 07 uses different graphics in tileset A
            animgfxptrs[-4:] = Pointers.levelgfxAnimIDs[(0x07,0x0A)]

        if animgfxptrs:
            for ptr, offset, size in animgfxptrs:
                self.animated.replacegraphics(GameGraphics(GBA.importdata(
                    filepath, ptr, size)), offset)
        elif animID == 0:  # overwrite animated region with blank tiles
            self.animated.replacegraphics(GameGraphics(bytes(0x800)), 0x4000)
        elif animID == 0x09:  # compressed animation
            with GBA.Open(filepath, "rb") as f:
                f.readseek(Pointers.levelgfxAnim09)
                graphics = GameGraphics(f.read_decompress())
            # not entirely documented; these offsets are estimates
            self.animated.replacegraphics(graphics[0x170:0x178], 0x8C00)
            self.animated.replacegraphics(graphics[0x178:0x180], 0x8E00)
        elif animID == 0x12:  # compressed animation
            with GBA.Open(filepath, "rb") as f:
                f.readseek(Pointers.levelgfxAnim12)
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
            raise ValueError("Tilemap data length " + hex(len(rawdata)) +\
                  " does not correspond to an integer number of tiles.")
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

def loadstripeIDs(filepath, spritetileset):
    with GBA.Open(filepath, "rb") as f:
        f.seek(f.readptr(Pointers.levelgfxstripeIDs) + spritetileset*6)
        return f.read(6)

class LevelPalette(list):
    """Simulated palette during a standard SMA3 sublevel, in 15-bit color
    format. Includes main 0x200-byte palette and 0x18-byte background gradient."""
    def __init__(self, filepath, layer1ID=None, layer2ID=None, layer3ID=None,
                 layer3image=None, BGpalID=None, spritepalID=None, yoshipalID=0,
                 showredcoins=True):
        self.showredcoins = showredcoins
        self.extend([0]*0x200)
        self.BGgradient = [0]*0x18
        self.colortype = ["Unknown"]*0x200

        self.layer1ID = None
        self.layer2ID = None
        self.layer3ID = None
        self.layer3image = None
        self.BGpalID = None

        with GBA.Open(filepath, mode="rb") as f:
            # load global layer 1 colors (fixed color table index of 0x98)
            f.seek(Pointers.colortable + 0x98)
            for paletterow in (1, 2, 3):
                for i in range(1, 0xC):
                    colorID = paletterow<<4 | i
                    self[colorID] = f.readint(2)
                    self.colortype[colorID] = "Layer 1 Global"

            # load global sprite colors
            f.readseek(Pointers.levelpal100)
            for colorID in range(0x100, 0x150):
                self[colorID] = f.readint(2)
                self.colortype[colorID] = "Sprite Global"
            f.readseek(Pointers.levelpal180)
            for colorID in range(0x180, 0x1F8):
                self[colorID] = f.readint(2)
                self.colortype[colorID] = "Sprite Global"
            f.readseek(Pointers.levelpal1F8)
            for colorID in range(0x1F8, 0x200):
                self[colorID] = f.readint(2)
                self.colortype[colorID] = "Message Global"

            self._setuninitialized(0x80, 0xD0)

        if BGpalID is not None:
            self.loadBGpalette(filepath, BGpalID)
        if layer1ID is not None:
            self.loadL1palette(filepath, layer1ID)
        if layer2ID is not None:
            self.loadL2palette(filepath, layer2ID)
        if layer3ID is not None:
            self.loadL3palette(filepath, layer3ID)
        if layer3image is not None:
            self.loadL3imagepal(filepath, layer3image)
        if spritepalID is not None:
            self.loadspritepalette(filepath, spritepalID)
        self.loadyoshipalette(filepath, yoshipalID)

        self.colortype[0xF0:0x100] = ["Red Coin Palette"]*0x10

        # label transparent colors
        for colorID in range(0x10, 0x200, 0x10):
            self.colortype[colorID] = "Transparent"

    def loadBGpalette(self, filepath, paletteID):
        self.BGpalID = paletteID
        with GBA.Open(filepath, mode="rb") as f:
            colorindex = paletteID*2
            f.seek(Pointers.colortable + colorindex)
            self[0] = f.readint(2)
            self.colortype[0] = "Background Color " + format(paletteID, "02X")

            for colorID in range(0x80, 0xA0, 4):
                # account for layer 3 image region copying background color
                if self.colortype[colorID].startswith("Background Color"):
                    self[colorID] = self[0]
                    self.colortype[colorID] = self.colortype[0]

            if paletteID >= 0x10:
                f.seek(f.readptr(Pointers.levelBGgradient) + paletteID*4)
                colorindex = f.readint(2)
                f.seek(Pointers.colortable + colorindex)
                for i in range(0x18):
                    self.BGgradient[i] = f.readint(2)
            else:
                self.BGgradient = [self[0]]*0x18

    def loadL1palette(self, filepath, paletteID):
        self.layer1ID = paletteID
        with GBA.Open(filepath, mode="rb") as f:
            f.seek(f.readptr(Pointers.levelpalL1) + paletteID*2)
            colorindex = f.readint(2)
            f.seek(Pointers.colortable + colorindex)
            # layer 1 palettes load to 2 distinct rectangular regions
            for paletteIDrange, colorIDrange in (((4, 5), range(1, 0x10)),
                                                 ((1, 2, 3), range(0xC, 0x10))):
                for paletterow in paletteIDrange:
                    for i in colorIDrange:
                        colorID = paletterow<<4 | i
                        self[colorID] = f.readint(2)
                        self.colortype[colorID] = "Layer 1 Palette " +\
                                                  format(paletteID, "X")

        # red coin palette is a copy of palette 1 or 2
        self.setRedCoinPalette()

    def setRedCoinPalette(self, newvalue=None):
        if newvalue is not None:
            self.showredcoins = newvalue
        if self.showredcoins:
            self[0xF0:0x100] = self[0x10:0x20]
        else:
            self[0xF0:0x100] = self[0x20:0x30]

    def loadL2palette(self, filepath, paletteID):
        self.layer2ID = paletteID
        with GBA.Open(filepath, mode="rb") as f:
            f.seek(f.readptr(Pointers.levelpalL2) + paletteID*2)
            colorindex = f.readint(2)
            f.seek(Pointers.colortable + colorindex)
            for paletterow in (6, 7):
                for i in range(1, 0x10):
                    colorID = paletterow<<4 | i
                    self[colorID] = f.readint(2)
                    self.colortype[colorID] = "Layer 2 Palette " +\
                                              format(paletteID, "02X")

    def loadL3palette(self, filepath, paletteID):
        self.layer3ID = paletteID
        with GBA.Open(filepath, mode="rb") as f:
            f.seek(f.readptr(Pointers.levelpalL3) + paletteID*2)
            colorindex = f.readint(2)
            f.seek(Pointers.colortable + colorindex)
            for colorID in range(1, 0x10):
                self[colorID] = f.readint(2)
                self.colortype[colorID] = "Layer 3 Palette " +\
                                          format(paletteID, "02X")

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

            with GBA.Open(filepath, mode="rb") as f:
                ptr = f.readptr(f.readptr(Pointers.levelpalL3image) + index*4)
                colortype = "Layer 3 Image " + format(imageID, "02X")

                if imageID == 0x23 and self.layer3ID == 0x1C:
                    # game hardcodes a different palette for this combo
                    ptr += 0x20
                    colortype = "Layer 3 Image 23 + Palette 1C"

                f.seek(ptr)
                for colorID in range(0x80, stop):
                    if colorID & 3:
                        self[colorID] = f.readint(2)
                        self.colortype[colorID] = colortype
                    else:
                        f.read(2)  # discard next 2 bytes
                        if colorID & 0xF:
                            self[colorID] = self[0]  # copy background color
                            self.colortype[colorID] = self.colortype[0]

        self._setuninitialized(stop, 0xA0)


    def loadspritepalette(self, filepath, paletteID):
        with GBA.Open(filepath, mode="rb") as f:
            ptr = f.readptr(f.readptr(Pointers.levelpalsprite), paletteID)
            f.seek(ptr)
            for colorID in range(0x160, 0x180):
                self[colorID] = f.readint(2)
                if colorID & 0xF:
                    self.colortype[colorID] = "Sprite Palette " +\
                                              format(paletteID, "X")
            self._setunusedDE(f, paletteID, 0xE,
                                   "SNES leftover/Sprite Palette ")


    def loadyoshipalette(self, filepath, paletteID):
        with GBA.Open(filepath, mode="rb") as f:
            f.seek(Pointers.levelpalyoshi + 0x20*paletteID)
            for colorID in range(0x150, 0x160):
                self[colorID] = f.readint(2)
                if colorID & 0xF:
                    self.colortype[colorID] = "Yoshi Palette " +\
                                              format(paletteID, "X")
            self._setunusedDE(f, paletteID, 0xD,
                                   "SNES leftover/Yoshi Palette ")

    def _setunusedDE(self, f, paletteID, paletterow, basestr):
            f.seek(f.readptr(Pointers.levelpalunusedDE) + paletteID*2)
            colorindex = f.readint(2)
            f.seek(Pointers.colortable + colorindex)
            for colorID in range((paletterow << 4) + 1, (paletterow + 1) << 4):
                self[colorID] = f.readint(2)
                self.colortype[colorID] = basestr + format(paletteID, "X")

    def _setuninitialized(self, start, stop):
        for colorID in range(start, stop):
            if colorID & 0xF != 0:
                self[colorID] = 0x7C1F  # magenta to signal uninitialized
        self.colortype[start:stop] = ["Uninitialized"] * (stop-start)

    def row(self, paletteID):
        """Returns one 0x10-color palette, for use in coloring 8x8 tiles."""
        return self[paletteID*0x10 : (paletteID+1)*0x10]

def importL1_8x8tilemaps(filepath):
    """Import the 8x8 tilemap for each layer 1 16x16 tile ID."""
    with GBA.Open(filepath, mode="rb") as f:
        ptrs = []
        f.seek(Pointers.tilemapL1_8x8)
        for i in range(0xA9):
            ptrs.append(f.readint(4))
        ptrs.append(Pointers.tilemapL1_8x8)
        # last entry of vanilla tilemap table ends with the pointer table itself

        output = {}
        for highbyte in range(0xA9):
            f.seek(ptrs[highbyte])
            # read until next pointer, or 0x100 table entries (in case of edited
            #  pointer), whichever comes first
            tile16count = min((ptrs[highbyte+1]-ptrs[highbyte]) // 8, 0x100)

            tile16 = highbyte << 8
            for i in range(tile16count):
                tilemap = []
                for j in range(4):
                    tilemap.append(f.readint(2))
                output[tile16] = tilemap
                tile16 += 1

    return output

class Font(GameGraphics):
    def __init__(self, filepath, font="main"):
        "Load the main or credits SMA3 font."
        GameGraphics.__init__(self, tilesize=0xC)

        graphicsptr, widthptr, charlength, start = Pointers.textgraphics[font]
        self.widths = bytearray(start)
        with GBA.Open(filepath, "rb") as f:
            f.seek(graphicsptr)
            rawdata = f.read(charlength*0xC)
            f.seek(widthptr)
            self.widths += f.read(charlength)
        self.replacegraphics(GameGraphics(bytes(start*0xC), tilesize=0xC))
        self.replacegraphics(GameGraphics(rawdata, tilesize=0xC), start*0xC)

def exporttextgraphics(sourcefilepath, exportfilepath, font="main"):
    """Export SMA3's variable-width font graphics to a pixel graphics file.

    The export format expands each character's graphics from 8x12 to 8x16,
    and arranges them vertically as viewed in YY-CHR, so that they're reasonably
    editable. The variable width is indicated with an underline."""

    graphicsptr, widthptr, charlength, _ = Pointers.textgraphics[font]
    with GBA.Open(sourcefilepath, "rb") as f:
        f.seek(graphicsptr)
        textgraphicsraw = f.read(charlength*0xC)
        f.seek(widthptr)
        widths = f.read(charlength)

    bitlines = (0b00000000, 0b10000000, 0b11000000, 0b11100000, 0b11110000,
                0b11111000, 0b11111100, 0b11111110, 0b11111111)

    with open(exportfilepath, "wb") as f:
        # Fill with empty space. Should be 0x1000, but it won't display
        #  in YYCHR without at least 0x2000
        f.write(bytes(0x2000))
        for charID in range(charlength):
            # first 8 8px rows
            f.seek(charID // 0x10 * 0x100 + charID % 0x10 * 8)
            f.write(textgraphicsraw[charID*12 : charID*12 + 8])

            # remaining 4 8px rows
            f.seek(charID // 0x10 * 0x100 + 0x80 + charID % 0x10 * 8)
            f.write(textgraphicsraw[charID*12 + 8 : charID*12 + 12])

            # use padding area to represent width
            f.seek(charID // 0x10 * 0x100 + 0x85 + charID % 0x10 * 8)
            try:
                widthline = bytes((bitlines[widths[charID]],))
            except IndexError:
                widthline = bytes((bitlines[0],))
            widthline += b"\x80"  # hook to mark left edge of line
            f.write(widthline)

def exportmessageimages(sourcefilepath, exportfilepath, bytelength=0x1F00):
    with GBA.Open(sourcefilepath, "rb") as f:
        ptr = f.readptr(Pointers.messageimages)
        f.seek(ptr)
        rawdata = f.read(bytelength)

    output = bytearray()
    for y in range(bytelength >> 4):
        for x in range(0x10):
            i = y << 7 | x
            output += rawdata[i:i+0x80:0x10]

    with open(exportfilepath, "wb") as f:
        f.write(output)
        if bytelength < 0x2000:
            f.write(bytes(0x2000 - bytelength))

def exportgraphics(filepath, exportdir=None):
    """Export all currently known SMA3 graphics and compressed tilemaps.

    Also generate two directories in exportdir, {basename}-Graphics and
    {basename}-Tilemaps, to hold the exports if they don't already exist."""

    # generate a filename-safe prefix for the export directories
    sourcefileroot = os.path.splitext(os.path.basename(filepath))[0]

    if not exportdir:
        exportdir = os.path.dirname(filepath)
    outputroot = os.path.join(exportdir, sourcefileroot)

    folders = {}
    for name in ("Graphics", "Tilemaps"):
        folders[name] = outputroot + "-" + name
        if not os.path.exists(folders[name]):
            os.mkdir(folders[name])

    with GBA.Open(filepath, "rb") as f:
        # compressed graphics
        for destfile, ptrs in Pointers.LZ77_graphics:
            f.readseek(ptrs[0])
            data = f.read_decompress()
            AdvGame.exportdatatofile(
                os.path.join(folders["Graphics"], destfile), data)

        for destfile, ptrs in Pointers.LZ77_tilemaps:
            f.readseek(ptrs[0])
            data = f.read_decompress()
            AdvGame.exportdatatofile(
                os.path.join(folders["Tilemaps"], destfile), data)

        # uncompressed graphics
        for ptr, destfile, length in Pointers.uncompressed_graphics:
            f.seek(ptr)
            data = f.read(length)
            AdvGame.exportdatatofile(folders["Graphics"] + "/" + destfile, data)

    exporttextgraphics(
        filepath, os.path.join(folders["Graphics"], "Font_082F63CC_main.bin"),
        font="main")
    exporttextgraphics(
        filepath, os.path.join(folders["Graphics"], "Font_0816D509_credits.bin"),
        font="credits")
    exportmessageimages(
        filepath, os.path.join(folders["Graphics"], "Font_082F6FCC_images.bin"))

def importmodifiedgraphics(filepath, exportdir, exporttype=None):
    """Scan a folder for compressed data that was previously exported, and if
    any files were modified, import them."""
    if not exporttype:
        for string in ("Graphics", "Tilemaps"):
            if exportdir.endswith(string):
                exporttype = string
                break
        else:
            raise ValueError("Export type was not provided and could not be "
                "auto-detected. It should \n"
                "be one of: 'Graphics', 'Tilemaps'")

    ptrdata = {"Graphics":Pointers.LZ77_graphics,
               "Tilemaps":Pointers.LZ77_tilemaps}

    count = 0
    # import compressed data from files
    with GBA.Open(filepath, "rb") as f:
        for filename, ptrseq in ptrdata[exporttype]:
            exportpath = os.path.join(exportdir, filename)
            if os.path.exists(os.path.join(exportdir, filename)):
                with open(exportpath, "rb") as e:
                    newdata = e.read()
                olddataptr = f.readptr(ptrseq[0])
                olddata = f.read_decompress(olddataptr)
                if newdata == olddata:
                    continue

                # update data only if different
                count += 1

                compresseddata = GBA.compressLZ77(newdata)

                length = f.tell() - olddataptr
                print(filename, hex(olddataptr), hex(length))

                ## erase old data, find freespace, write new data, update ptrseq
                # freespace search should prioritize vanilla graphics region?

    if exporttype == "Graphics":
        # also import uncompressed graphics
        pass


    print("Total reinserted data:", count)
    return count

def findgraphicsfreespace(filepath):
    """Search for freespace in ROM regions corresponding to vanilla compressed
    data."""
    output = []
    for start, end in Pointers.vanillacompressedregions:
        output += AdvGame.findfreespace(
            "sma3.gba", GBA.addrtofile(start), GBA.addrtofile(end),
            minlength=0x10, width=4)
    print(";  ".join(", ".join(format(i, "X") for i in j) for j in output))
    return output
