"""Advynia SMA3 Visuals
Handles loading, displaying, and caching the currently loaded in-game
graphics/palette."""

# standard library imports
import itertools

# import from other files
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr
import AdvGame
from AdvGame import GBA, SMA3
from AdvGUI.GeneralQt import *
from AdvGUI import QtAdvFunc

# initialize attributes
layergraphics = None
spritegraphics = None
palette = None
yoshipalID = 0
layer0only = False
cache8_layers = [None]*0x600
cache8_spriteglobal = [None]*0x280
cache8_stripes = {}
cache16 = {}
cachesprite = {}

# Graphics loading functions

def loadgraphics(sublevel):
    global layergraphics, spritegraphics
    header = sublevel.header

    # load layer graphics
    layergraphics = SMA3.LayerVRAM(
        Adv3Attr.filepath,
        layer1ID=header[1],
        layer2ID=header[3],
        layer3ID=header[5],
        # layer effects = header[9],
        animID=header[0xA],
        )

    # load sprite graphics
    if not Adv3Attr.sublevelstripes:
        # patch is not applied: use header setting
        kwargs = {"spritetileset":header[7]}
    elif sublevel.stripeIDs:
        # patch is applied and stripe IDs are already loaded
        kwargs = {"stripeIDs":sublevel.stripeIDs}
    else:
        # patch is applied: use sublevel ID as sprite tileset
        kwargs = {"spritetileset":sublevel.ID}
    spritegraphics = SMA3.SpriteVRAM(Adv3Attr.filepath, **kwargs)
    resetcaches()

def updatestripesfromsublevel():
    if not Adv3Attr.sublevelstripes or not Adv3Attr.sublevel.stripeIDs:
        # current sublevel might be from file; import stripeIDs from current ROM
        with GBA.Open(Adv3Attr.filepath) as f:
            Adv3Attr.sublevel.importspritetileset(f, Adv3Attr.sublevelstripes)
    for i, newID in enumerate(Adv3Attr.sublevel.stripeIDs):
        if newID != spritegraphics.stripeIDs[i]:
            spritegraphics.loadstripe(Adv3Attr.filepath, i, newID)
    AdvWindow.editor.reload({"8x8"})

def loadpalette(sublevel):
    global palette
    header = sublevel.header
    palette = SMA3.LevelPalette(Adv3Attr.filepath,
        layer1ID=header[2],
        layer2ID=header[4],
        layer3ID=header[6],
        layer3image=header[5],
        BGpalID=header[0],
        spritepalID=header[8],
        animID=header[0xB],
        yoshipalID=yoshipalID,
        showredcoins=AdvSettings.visual_redcoins,
        )

# Cache reset functions

def resetcaches():
    "Reset all pixmap caches."
    resetcache8_layers()
    resetcache8_sprites()
    resetcache16()
    resetcachesprite()

def resetcache8_layers(region=None):
    for i in _cachetoclear(region):
        cache8_layers[i] = [None]*0x40

def resetcache8_sprites():
    for i in range(0x280):
        cache8_spriteglobal[i] = [None]*0x40
    cache8_stripes.clear()

def resetcache16():
    cache16.clear()

def resetcachesprite(sprIDs=None):
    if sprIDs is not None:
        todelete = [key for key in cachesprite if key[0] in sprIDs]
        for key in todelete:
            del cachesprite[key]
    else:
        cachesprite.clear()

def _cachetoclear(region=None):
    if not region:
        return range(0x600)
    if region == "Layer 1":
        return itertools.chain(range(0x80), range(0x100, 0x200))
    if region == "Layer 2":
        return range(0x280, 0x380)
    if region == "Layer 3":
        return range(0x380, 0x480)
    if region == "Animated":
        return range(0x200, 0x240)

# Tile cache retrieval functions

def get8x8(tileID, paletterow=1, xflip=False, yflip=False,
           sprite=False, stripeID=None):
    """Retrieve a particular 8x8 pixmap, using the cache if present.
    Otherwise generate the pixmap."""

    if tileID > 0x08000000:
        # dynamic pointer
        return getdynamic8x8(tileID, paletterow)

    propindex = (paletterow & 0xF) * 4
    if xflip: propindex |= 1
    if yflip: propindex |= 2

    if not sprite:
        graphics = layergraphics
        cache = cache8_layers
    else:
        if (stripeID is not None) and (not 0 <= tileID < 0x20):
            # account for tiles overflowing the requested stripe
            index = 5
            for ID in reversed(spritegraphics.stripeIDs):
                # game checks in reverse order
                if stripeID == ID:
                    break
                index -= 1
            else:
                raise KeyError("Requested stripe not in spritegraphics.stripeIDs")
            stripeID = spritegraphics.stripeIDs[index + (tileID>>5)]
            tileID = tileID & 0x1F
        elif stripeID is None and tileID & 0x10 and tileID < 0x180:
            # account for hardcoded tiles in stripe region
            stripeID = spritegraphics.stripeIDs[tileID >> 6]
            tileID = tileID & 0xF | (tileID & 0x20) >> 1

        if stripeID is not None:
            graphics = spritegraphics.stripes[stripeID]
            if stripeID not in cache8_stripes:
                cache8_stripes[stripeID] = []
                for i in range(0x20):
                    cache8_stripes[stripeID].append([None]*0x40)
            cache = cache8_stripes[stripeID]
        else:
            graphics = spritegraphics
            cache = cache8_spriteglobal

    if cache[tileID][propindex]:
        return cache[tileID][propindex]

    if not sprite and tileID < len(layergraphics.animated) and\
            layergraphics.animated[tileID] is not None:
        image = QGBA8x8Tile(layergraphics.animated[tileID],
                            palette.row(paletterow))
    elif tileID >= len(graphics):
        image = QGBA8x8Tile(None, palette.row(paletterow))
    else:
        image = QGBA8x8Tile(graphics[tileID],
                            palette.row(paletterow))
    if xflip or yflip:
        image.mirror(horizontal=xflip, vertical=yflip)

    pixmap = QPixmap.fromImage(image)
    cache[tileID][propindex] = pixmap
    return pixmap

_octagoncolors = {
    0x10EFF: qRgb(255, 0, 0),
    0x10EFE: qRgb(255, 132, 0),
    0x10EFD: qRgb(0, 231, 0),
    0x10EFB: qRgb(0, 189, 189),
    0x100A8: qRgba(0, 189, 189, 123),
    }

def get16x16(tileID):
    """Retrieve a particular layer 1 16x16 pixmap, using the cache if
    present. Otherwise generate the pixmap."""

    if tileID in cache16:
        return cache16[tileID]
    elif (tileID >= 0x10000 or tileID == 0x0010 or
            tileID not in Adv3Attr.tilemapL1_8x8):
        # out of in-game range tile ID: draw special 16x16 tile
        if qcolor := _octagoncolors.get(tileID):
            # misc octagonal filler tile for invisible objects
            image = QNumberedTile16(f"{tileID&0xFFF:02X}",
                                    qcolor, shape="octagon")
        elif tileID == 0x0010:
            # E80 visual (transparent teal)
            image = QNumberedTile16("E80",
                                    qRgba(0, 189, 189, 123), shape="octagon")
        elif 0x10E00 <= tileID < 0x10F00:
            # extended object filler tile (purple)
            image = QNumberedTile16(f"{tileID&0xFFF:03X}",
                                    qRgb(132, 0, 255), shape="square")
        elif 0x10000 <= tileID < 0x10100:
            # standard object filler tile (blue)
            image = QNumberedTile16(f"{tileID&0xFF:02X}",
                                    qRgb(0, 0, 255), shape="square")
        elif 0x10600 <= tileID < 0x10700:
            # 16x16 viewer label tile (magenta)
            image = QNumberedTile16(f"{tileID&0xFF:02X}",
                                    qRgb(255, 0, 255), shape="square")
        elif 0x11000 <= tileID < 0x12000:
            # object generation error tile (red)
            image = QNumberedTile16(f"{tileID&0xFFF:02X}",
                                    qRgb(255, 0, 66), shape="square")
        else:
            # invalid tile ID error (orange)
            image = QNumberedTile16(f"{tileID:04X}",
                                    qRgb(255, 132, 0), shape="square")
        pixmap = QPixmap.fromImage(image)
    else:
        # ordinary 16x16 game graphics
        pixmap = QTransparentPixmap(16, 16)
        with QPainterSource(pixmap) as painter:
            tilemap8 = Adv3Attr.tilemapL1_8x8[tileID]
            for i in range(4):
                tileprop = tilemap8[i]
                if layer0only and not Adv3Attr.tilemapL0flags[tileID][i]:
                    continue
                painter.drawPixmap(
                    (i&1)<<3, (i&2)<<2, get8x8(*GBA.splittilemap(tileprop)))

            if AdvSettings.visual_redcoins and tileID >> 8 == 0xA3:
                # draw red coin on poundable post tiles containing them
                painter.setCompositionMode(
                    painter.CompositionMode.CompositionMode_SourceOver)
                painter.setOpacity(0.6)
                redcoinpixmap = getstaticrect(16, 16, 0x140, 0x11, sprite=True)
                painter.drawPixmap(0, 0, redcoinpixmap)

    cache16[tileID] = pixmap
    return pixmap

# Multi-tile retreival functions

def getstaticrect(width, height, tileID, paletterow=1, xflip=False, yflip=False,
                  sprite=False, stripeID=None):
    """Draw a rectangle of 8x8 tiles from the currently loaded graphics/palette,
    and return it as a QPixmap."""

    offset = 0x10
    if sprite and (stripeID is None):
        offset = 0x20
    func = lambda x, y : get8x8(
        tileID + (x>>3) + (y>>3)*offset, paletterow,
        False, False, sprite, stripeID)

    return _getstaticrect_base(func, width, height, xflip, yflip)

def getstaticrect_direct(width, height, tileID, graphics, palette,
                         xflip=False, yflip=False, offset=0x20):
    """Draw a rectangle of 8x8 tiles from the provided graphics/palette,
    and return it as a QPixmap."""

    func = lambda x, y : QPixmap.fromImage(
        QGBA8x8Tile(graphics[tileID + (x>>3) + (y>>3)*offset], palette))
    return _getstaticrect_base(func, width, height, xflip, yflip)

def _getstaticrect_base(pixmapfunc, width, height, xflip, yflip):
    "Base function for shared code between the getstaticrect variants."

    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(0)
    with QPainter(image) as painter:
        for y in range(0, height, 8):
            for x in range(0, width, 8):
                painter.drawPixmap(x, y, pixmapfunc(x, y))
    if xflip or yflip:
        image.mirror(horizontal=xflip, vertical=yflip)
    return QPixmap.fromImage(image)

def getdynamicrect(width, height, ptr, paletterow, xflip=False, yflip=False):
    """Draw a rectangle of 8x8 tiles extracted directly from the ROM, using the
    currently loaded palette, and return it as a QPixmap."""

    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(0)
    with QPainter(image) as painter:
        for y in range(0, height, 8):
            with GBA.Open(Adv3Attr.filepath, "rb") as f:
                f.seek(ptr + (y<<7))
                graphics = AdvGame.GameGraphics(f.read(0x20 * int(width/8)))
            for x in range(0, width, 8):
                painter.drawImage(x, y,
                    QGBA8x8Tile(graphics[x>>3], palette.row(paletterow)))
    if xflip or yflip:
        image.mirror(horizontal=xflip, vertical=yflip)
    return QPixmap.fromImage(image)

# Pixel font pixmap generation

def getfontpixmap(string, bgcolor, fontcolor, bordercolor=None):
    "Draw a pixmap of an ASCII string."

    widths = [AdvMetadata.fontwidths[ord(char)] for char in string]
    width = 1 + sum(widths)
    height = 1 + AdvMetadata.fontheight

    image = QImage(width, height, QImage.Format.Format_Indexed8)
    palette = [bgcolor, fontcolor]
    if bordercolor is not None:
        palette.append(bordercolor)
    image.setColorTable(palette)
    image.fill(0)

    rowlength = image.bytesPerLine()  # account for multiple of 4 padding
    pixelarray = image.bits().asarray(rowlength * height)

    # draw border, if applicable
    if bordercolor is not None:
        for i in range(width):
            pixelarray[i] = 2  # first row
            pixelarray[rowlength*(height-1) + i] = 2  # last row
        for i in range(0, rowlength*height, rowlength):
            pixelarray[i] = 2  # first column
            pixelarray[i + width - 1] = 2  # last column

    # draw text
    startX = 1
    with open(AdvMetadata.datapath("font", "advpixelfont.bin"), "rb") as bitmap:
        for char, charwidth in zip(string, widths, strict=True):
            bitmap.seek(ord(char) * 8)

            y = 1
            for byte in bitmap.read(8):
                x = startX
                for bitindex in range(charwidth):
                    if (byte >> (7-bitindex)) & 1:
                        pixelarray[rowlength*y + x] = 1
                    x += 1
                y += 1
            startX += charwidth

    return QPixmap.fromImage(image)

# Layer 2/3 pixmap generation

def getlayerpixmap(layer, width, height):
    "Draw a pixmap of the current sublevel's layer 2 or 3 image."

    if layer == 2: layerIDoffset = 0
    elif layer == 3: layerIDoffset = 0x200
    else: raise ValueError("Layer must be 2 or 3.")

    tilemap = layergraphics.tilemap[layer]

    if len(tilemap) > 0x800: del tilemap[0x800:]
    elif len(tilemap) < 0x800: tilemap[0:0] = [None] * (0x800 - len(tilemap))

    layerpixmap = QTransparentPixmap(width, height)

    with QPainterSource(layerpixmap) as painter:
        # iterate over 16x16 tiles in tilemap
        for y in range(height >> 4):
            for x in range(width >> 4):
                tileprop = tilemap[y * (width >> 4) | x]
                if tileprop is None:
                    continue
                tileID_8, paletterow, xflip, yflip = GBA.splittilemap(tileprop)

                xflip = bool(xflip)  # convert True from 0x400 to 1
                yflip = bool(yflip)*2  # convert True from 0x800 to 2

                for i, offset16 in enumerate((0, 1, 0x10, 0x11)):
                    tilepixmap = get8x8(layerIDoffset + tileID_8 + offset16,
                        paletterow, xflip, yflip)
                    painter.drawPixmap(
                        (i&1^xflip)<<3 | x<<4,
                        (i&2^yflip)<<2 | y<<4,
                        tilepixmap)

    return layerpixmap

def getscanlinepixmap(layer, width, height, offsets):
    sourceimage = getlayerpixmap(layer, 0x200, 0x400).toImage()
    sourceimage_linelen = sourceimage.bytesPerLine()
    sourceimage_bytes = sourceimage.bits()
    sourceimage_bytes.setsize(sourceimage.sizeInBytes())

    newimage = QImage(width, len(offsets), sourceimage.format())
    newimage_linelen = newimage.bytesPerLine()
    newimage_bytes = newimage.bits()
    newimage_bytes.setsize(newimage.sizeInBytes())
    newimage.fill(0)

    bytesperpixel = newimage.depth() // 8

    for y, (offsetX, offsetY) in enumerate(offsets):
        sourceoffset = offsetY * sourceimage_linelen + offsetX * bytesperpixel
        destoffset = y * newimage_linelen
        newimage_bytes[destoffset : destoffset + newimage_linelen] =\
            sourceimage_bytes[sourceoffset : sourceoffset + newimage_linelen]
    return QPixmap.fromImage(newimage)

def _compressed8bpp_to_pixmap(ptrref, tilewidth):
    with GBA.Open(Adv3Attr.filepath) as f:
        f.readseek(ptrref)
        graphics = AdvGame.GameGraphics(f.read_decompress(), tilesize=0x40)

    tileheight = len(graphics) // tilewidth
    if len(graphics) % tilewidth:
        tileheight += 1  # round up

    pixmap = QTransparentPixmap(tilewidth*8, tileheight*8)
    with QPainter(pixmap) as painter:
        for i, tile in enumerate(graphics):
            painter.drawImage(i % tilewidth * 8, i // tilewidth * 8,
                              QGBA8x8Tile_8bpp(tile, palette[0:0x100]))
    return pixmap

# Sprite pixmap generation

# colors for fallback numbered circles and default text
#  green, red, yellow(orange), pink
parityqcolors = (0xFF29B129, 0xFFCE2929, 0xFFFFA529, 0xFFDE2994)

class QPainterSprite(QPainter):
    def __init__(self, pixmap):
        super().__init__(pixmap)

        self.size = pixmap.size()
        self.lastopacity = None
        self.subpixmap = None

    def drawTileattr(self, offsetX, offsetY, tileattr):
        """Draw a pixmap corresponding to an entry in the sprite metadata
        tilemap."""
        a = tileattr  # short name since tileattr is referenced so frequently

        # draw all tiles with the same opacity to one sub-pixmap,
        #  then apply it to the main pixmap on opacity change
        if a.opacity != self.lastopacity:
            self.finalize_subpixmap()
            self.lastopacity = a.opacity
            if a.opacity != 1:
                self.subpixmap = QTransparentPixmap(self.size)
        if a.opacity != 1:
            with QPainterSprite(self.subpixmap) as subpainter:
                subpainter.drawTileattr(offsetX, offsetY, a._replace(opacity=1))
            return

        # adjust to absolute coordinates
        x = a.x - offsetX
        y = a.y - offsetY

        # generate pixmap
        if a.misc:
            if a.misc == "Hookbill":
                # Hookbill 8bpp graphics special handling
                pixmap = _compressed8bpp_to_pixmap(SMA3.Pointers.LZ77_graphics[
                        "Gameplay_Hookbill_L2_8bpp.bin"], 0x10)
            else:
                raise ValueError(
                    "Invalid value for sprite tile attribute misc:\n" + a.misc)
        elif a.text:
            if a.paletterow < 4:
                # repurpose paletterow as parity color
                color = parityqcolors[a.paletterow]
            else:
                # repurpose paletterow as 15-bit color
                color = QtAdvFunc.color15toQRGB(a.paletterow & 0x7FFF)
            pixmap = getfontpixmap(a.text, color, 0xFFFFFFFF, 0xFF000000)                
        elif a.layer:
            if a.tileID is not None:
                pixmap = getscanlinepixmap(a.layer, a.width, a.height,
                    SMA3.ScanlineOffsetData.sprite[a.tileID])
            elif a.size is not None:
                pixmap = getlayerpixmap(a.layer, 0x200, 0x400).copy(
                    *a.size, a.width, a.height)
            else:
                print(a)
                raise ValueError(
                    "Layer-based sprite graphics:\n" + str(a) +
                    "\n...did not provide either a ScanlineOffsetData index,"
                    " or a 4-argument rectangular region to crop.")
        elif a.dynamicptr:
            pixmap = getdynamicrect(
                a.width, a.height, a.dynamicptr, a.paletterow, a.xflip, a.yflip)
        elif a.width == 8 and a.height == 8:
            pixmap = get8x8(
                a.tileID, a.paletterow, a.xflip, a.yflip, a.sprite, a.stripeID)
        else:
            pixmap = getstaticrect(
                a.width, a.height, a.tileID, a.paletterow,
                a.xflip, a.yflip, a.sprite, a.stripeID)

        # apply transformations if needed
        if a.angle or a.scaleX != 1 or a.scaleY != 1:
            self.translate(x + pixmap.width()/2, y + pixmap.height()/2)
            self.rotate(-a.angle)
            self.scale(a.scaleX, a.scaleY)
            self.translate(-pixmap.width()/2, -pixmap.height()/2)
            self.drawPixmap(0, 0, pixmap)
            self.resetTransform()
        else:
            self.drawPixmap(x, y, pixmap)

    def __exit__(self, *args):
        if args[0] is None:  # exited normally, not via exception
            self.finalize_subpixmap()
        super().__exit__(*args)

    def finalize_subpixmap(self):
        """Apply a subpixmap with non-100% opacity to the main image.
        Called when the opacity changes, and when the painter is finished."""
        if self.subpixmap is not None:
            self.setOpacity(self.lastopacity)
            self.drawPixmap(0, 0, self.subpixmap)
            self.setOpacity(1)
            self.lastopacity = None
            self.subpixmap = None

def getspritepixmap(sprID, parity):
    "Draw a pixmap of a specified sprite, from its metadata."

    pixmap = None
    offsetX, offsetY = 0, 0

    metadata = SMA3.SpriteMetadata[(sprID, parity)]

    # if pixmap was cached, return that
    cachekey = (sprID, parity & metadata.parity)
    if cachekey in cachesprite:
        return cachesprite[cachekey]

    # else, generate sprite
    if sprID == 0x65 and not AdvSettings.visual_redcoins:
        # red coin: use yellow coin sprite's graphic if red coins are hidden
        metadata = SMA3.SpriteMetadata[(0x1AF, parity)]
    if metadata.tilemap:
        try:
            offsetX, offsetY = metadata.offset
            pixmap = QTransparentPixmap(*metadata.pixmapsize)
            with QPainterSprite(pixmap) as painter:
                for tileattr in metadata.tilemap:
                    painter.drawTileattr(offsetX, offsetY, tileattr)
                if sprID == 0x4F:
                    # middle ring: display checkpoint ID on star
                    painter.drawImage(-offsetX + 3, -offsetY, QNumberedTile16(
                        str(Adv3Attr.sublevel.header[0xE]),
                        QtAdvFunc.color15toQRGB(0x7FF0),
                        "superstar", textcolorindex=1))
        except (KeyError, IndexError):
            # stripe graphics not loaded, or tile ID overflowed
            pixmap = None

    if pixmap:
        cachesprite[cachekey] = (pixmap, offsetX, offsetY)
        return pixmap, offsetX, offsetY
    else:
        # use fallback pixmap, don't cache
        return getspritefallbackpixmap(sprID, parity), 0, 0

def getspritefallbackpixmap(sprID, parityID):
    """Draw a numbered circle containing a sprite ID, with varying color if
    the sprite is affected by parity."""

    image = QNumberedTile16(
        f"{sprID:02X}",
        parityqcolors[parityID & SMA3.SpriteMetadata[(sprID, parityID)].parity],
        shape="circle")
    return QPixmap.fromImage(image)
