"""Advynia SMA3 Visuals
Handles loading, displaying, and caching the currently loaded in-game
graphics/palette."""

# standard library imports
import itertools

# import from other files
from AdvGame import *
from AdvGUI.QtGeneral import *

# globals
import AdvSettings, Adv3Attr

# initialize attributes
layergraphics = None
spritegraphics = None
palette = None
cache8_layers = [None]*0x600
cache8_spriteglobal = [None]*0x280
cache8_stripes = {}
cache16 = {}

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
        # palette animation = header[0xB],
        yoshipalID=AdvSettings.yoshipalID,
        showredcoins=AdvSettings.showredcoins,
        )

# Cache reset functions

def resetcaches():
    "Reset all pixmap caches."
    resetcache8_layers()
    resetcache8_sprites()
    resetcache16()

def resetcache8_layers(region=None):
    for i in _cachetoclear(region):
        cache8_layers[i] = [None]*0x40

def resetcache8_sprites():
    for i in range(0x280):
        cache8_spriteglobal[i] = [None]*0x40
    cache8_stripes.clear()

def resetcache16():
    cache16.clear()

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

# Cache retrieval functions

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
        image = image.mirrored(horizontal=xflip, vertical=yflip)

    pixmap = QPixmap.fromImage(image)
    cache[tileID][propindex] = pixmap
    return pixmap

def get16x16(tileID):
    """Retrieve a particular layer 1 16x16 pixmap, using the cache if
    present. Otherwise generate the pixmap."""

    if tileID in cache16:
        return cache16[tileID]
    elif tileID >= 0x10000 or tileID == 0x10 or\
            tileID not in Adv3Attr.tilemapL1_8x8:
        # out of bounds tile ID, draw special 16x16 tile
        if tileID == 0x10EFF:
            image = QNumberedTile16("EFF", qRgb(255, 0, 0), shape="octagon")
        elif tileID == 0x10EFE:
            image = QNumberedTile16("EFE", qRgb(255, 132, 0), shape="octagon")
        elif tileID == 0x10EFD:
            image = QNumberedTile16("EFD", qRgb(0, 231, 0), shape="octagon")
        elif tileID == 0x0010:
            image = QNumberedTile16("E80", qRgb(0, 189, 189), shape="octagon")
        elif tileID == 0x10EFB:
            image = QNumberedTile16("EFB", qRgb(0, 189, 189), shape="octagon")
        elif 0x10E00 <= tileID < 0x10F00:
            # extended object filler tile
            image = QNumberedTile16(format(tileID&0xFFF, "02X"),
                qRgb(132, 0, 255), shape="square")
        elif 0x10000 <= tileID < 0x10100:
            # standard object filler tile
            image = QNumberedTile16(format(tileID&0xFF, "02X"),
                qRgb(0, 0, 255), shape="square")
        elif 0x10600 <= tileID < 0x10700:
            # 16x16 viewer label tile
            image = QNumberedTile16(format(tileID&0xFF, "02X"),
                qRgb(255, 0, 255), shape="square")
        else:
            # red error tile
            image = QNumberedTile16(format(tileID&0xFFF, "02X"),
            qRgb(255, 0, 64), shape="square")
        pixmap = QPixmap.fromImage(image)
    else:
        # ordinary 16x16 game graphics
        pixmap = QTransparentPixmap(16, 16)
        with QPainterSource(pixmap) as painter:
            tilemap8 = Adv3Attr.tilemapL1_8x8[tileID]
            for i in range(4):
                tileprop = tilemap8[i]
                painter.drawPixmap(
                    (i&1)<<3, (i&2)<<2, get8x8(*GBA.splittilemap(tileprop)))

            if 0xA300 <= tileID < 0xA314:
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
    offset = 0x10
    if sprite and (stripeID is None):
        offset = 0x20

    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(0)
    with QPainter(image) as painter:
        for y in range(0, height, 8):
            for x in range(0, width, 8):
                painter.drawPixmap(x, y, get8x8(
                    tileID + (x>>3) + (y>>3)*offset, paletterow,
                    False, False, sprite, stripeID))
    if xflip or yflip:
        image = image.mirrored(horizontal=xflip, vertical=yflip)
    return QPixmap.fromImage(image)

def getdynamicrect(width, height, ptr, paletterow, xflip=False, yflip=False):
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(0)
    with QPainter(image) as painter:
        for y in range(0, height, 8):
            graphics = GameGraphics(GBA.importdata(
                Adv3Attr.filepath, ptr + (y<<7), 0x20 * int(width/8))[0])
            for x in range(0, width, 8):
                painter.drawImage(x, y,
                    QGBA8x8Tile(graphics[x>>3], palette.row(paletterow)))
    if xflip or yflip:
        image = image.mirrored(horizontal=xflip, vertical=yflip)
    return QPixmap.fromImage(image)

# Sprite pixmap generation

# colors for fallback numbered circles: green, red, yellow(orange), pink
parityqcolors = (0xFF29B129, 0xFFCE2929, 0xFFFFA529, 0xFFDE2994)

class QPainterSprite(QPainter):
    def drawTileattr(self, offsetX, offsetY, tileattr):
        """Draw a pixmap corresponding to an entry in the sprite metadata
        tilemap."""
        a = tileattr  # short name since tileattr is referenced so frequently

        # adjust to absolute coordinates
        x = a.x - offsetX
        y = a.y - offsetY

        # generate pixmap
        if a.dynamicptr:
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
        self.setOpacity(a.opacity)
        if a.angle or a.scaleX != 1 or a.scaleY != 1:
            self.translate(x + pixmap.width()/2, y + pixmap.height()/2)
            self.rotate(-a.angle)
            self.scale(a.scaleX, a.scaleY)
            self.translate(-pixmap.width()/2, -pixmap.height()/2)
            self.drawPixmap(0, 0, pixmap)
            self.resetTransform()
        else:
            self.drawPixmap(x, y, pixmap)

def getspritepixmap(sprID, parity):
    pixmap = None
    offsetX, offsetY = 0, 0

    metadata = SMA3.SpriteMetadata[(sprID, parity)]
    if sprID == 0x65 and not AdvSettings.showredcoins:
        # use yellow coin sprite's graphic if red coins are hidden
        metadata = SMA3.SpriteMetadata[(0x1AF, parity)]
    if metadata.tilemap:
        try:
            offsetX, offsetY = metadata.offset
            pixmap = QTransparentPixmap(*metadata.pixmapsize)
            with QPainterSprite(pixmap) as painter:
                for tileattr in metadata.tilemap:
                    painter.drawTileattr(offsetX, offsetY, tileattr)
        except (KeyError, IndexError):
            # stripe graphics not loaded, or tile ID overflowed
            pixmap = None

    if not pixmap:
        # fallback image
        image = QNumberedTile16(
            format(sprID, "02X"), parityqcolors[parity & metadata.parity],
            shape="circle")
        pixmap = QPixmap.fromImage(image)
        offsetX, offsetY = 0, 0

    return pixmap, offsetX, offsetY
