"""Sublevel Scene Layers
Includes the various displayed layers of the sublevel scene:
background gradient, GBA layers 1-3, sprites, and screen border grid."""

# import from other files
import AdvMetadata
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr, Adv3Visual
from AdvGame import AdvGame, GBA, SMA3
from AdvGUI.GeneralQt import *
from AdvGUI import QtAdvFunc

class QAbstractLayer:
    """Base class of items that process each layer of a displayed sublevel.
    Actually not a QGraphicsItem (and cannot be added to a scene), but
    partially acts like an abstract parent item for all items on its layer."""
    def __init__(self, scene, zvalue=0):
        self.scene = scene
        self.zvalue = zvalue
        self.visibility = True
        self.delayedupdate = False

    def isVisible(self):
        return self.visibility

class QSMA3BackgroundGradient(QAbstractLayer):
    """Handles displaying a sublevel's background gradient."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rectheight = 43

        self.colorrects = []
        for i in range(47):
            item = QGraphicsRectItem(0, 0, 0x1000, rectheight)
            item.setPen(QPen(Qt.PenStyle.NoPen))
            item.setPos(0, i*rectheight)
            item.setZValue(-300)
            self.scene.addItem(item)
            self.colorrects.append(item)
        self.colorrects[46].setRect(0, 0, 0x1000, 0x800-(rectheight*46))

    def dispBGgradient(self):
        for i in range(24):
            color = Adv3Visual.palette.BGgradient[-i-1]
            self.colorrects[2*i].setBrush(QtAdvFunc.color15toQRGB(color))
            try:
                nextcolor = AdvGame.color15interpolate(
                    color, Adv3Visual.palette.BGgradient[-i-2])
                self.colorrects[2*i+1].setBrush(QtAdvFunc.color15toQRGB(nextcolor))
            except IndexError:
                pass

class QSMA3Layer1(QAbstractLayer):
    """Handles displaying a sublevel's layer 1 from its objects.
    Specified width and height are in 16x16 tiles, not pixels."""
    def __init__(self, *args, width=0x100, height=0x80, allowYoverflow=False,
                 sublevelscene=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.width = width
        self.height = height
        self.allowYoverflow = allowYoverflow
        self.sublevelscene = sublevelscene

        self.tilemap = []
        for y in range(self.height):
            self.tilemap.append([0]*self.width)

        if AdvMetadata.printtime: timer = QtAdvFunc.timerstart()  # debug

        # initialize grid of 16x16 pixmaps
        self.blankpixmap = QTransparentPixmap(16, 16)
        self.pixmapgrid = []
        for y in range(self.height):
            self.pixmapgrid.append([])
            for x in range(self.width):
                pixmapitem = QGraphicsPixmapItem(self.blankpixmap)
                pixmapitem.setPos(x<<4, y<<4)
                self.scene.addItem(pixmapitem)
                self.pixmapgrid[y].append(pixmapitem)

        if AdvMetadata.printtime and self.sublevelscene == True:
            print("Layer 1 pixmap grid init:", QtAdvFunc.timerend(timer), "ms")  # debug

        if self.sublevelscene:
            # init grid of mostly-transparent screens
            self.screenrects = []
            for screen in range(0x80):
                item = QGraphicsRectItem(0, 0, 0x100, 0x100)
                item.setPen(QPen(Qt.PenStyle.NoPen))
                item.setBrush(QColor(0, 0, 0, 0))
                item.setPos((screen&0xF) * 0x100, (screen>>4) * 0x100)
                item.setZValue(99)
                self.scene.addItem(item)
                self.screenrects.append(item)

    def createTilemap(self, sublevel):
        """Generate the layer 1 tilemap (list) from the editor's active
        sublevel. The previous tilemap is saved to self.tilemapold."""
        if AdvMetadata.printtime: timer = QtAdvFunc.timerstart()  # debug

        self.tilemapold = self.tilemap
        self.tilemap = SMA3.L1Constructor(
            sublevel, allowYoverflow=self.allowYoverflow).tilemap

        if AdvMetadata.printtime and self.sublevelscene == True:
            print("Layer 1 tilemap generation:", QtAdvFunc.timerend(timer), "ms")  # debug

    def updateLayerGraphics(self, forcereload=False):
        """Update the displayed tiles with the currently loaded tilemap.

        To save time, this will not normally display tiles with unchanged IDs.
        Set forcereload to reload all tiles, such as after a graphics or
        palette edit."""

        if AdvMetadata.printtime: timer = QtAdvFunc.timerstart()  # debug

        for y in range(self.height):
            for x in range(self.width):
                self.updateTileGraphics(x, y, forcereload)

        if self.sublevelscene == True:
            # run only for main sublevel scene, not sidebar preview
            self.setDimScreens()
            AdvWindow.statusbar.setSizeText(
                newscreencount=self.tilemap.screencount())
            
            if AdvMetadata.printtime: print("Layer 1 pixmap processing:",
                  QtAdvFunc.timerend(timer), "ms")  # debug

    def updateLayerRegion(self, tiles):
        """Update only some of the layer's tiles, specified as a collection
        of (x, y) tuples."""
        if AdvMetadata.printtime: timer = QtAdvFunc.timerstart()  # debug

        for x, y in tiles:
            if 0 <= x < self.width and 0 <= y < self.height:
                self.updateTileGraphics(x, y)

        self.setDimScreens()
        AdvWindow.statusbar.setSizeText(
            newscreencount=self.tilemap.screencount())
        if AdvMetadata.printtime: print("Layer 1 pixmap processing:",
              QtAdvFunc.timerend(timer), "ms")  # debug

    def updateTileGraphics(self, x, y, forcereload=False):
        tileID = self.tilemap[y][x]
        if not forcereload and tileID == self.tilemapold[y][x]:
            # don't update identical tiles
            return
        else:
            self.pixmapgrid[y][x].setPixmap(Adv3Visual.get16x16(tileID))

    _transparent = QColor(0, 0, 0, 0)
    screentype = {
        1:(_transparent, QColor(132, 132, 132, 51), _transparent),
        2:(QColor(0, 0, 255, 51), QColor(255, 0, 0, 51), QColor(255, 255, 0, 51)),
        }
    def setDimScreens(self, newvalue=None):
        if newvalue is not None:
            AdvSettings.visual_dimscreens = newvalue
        if AdvSettings.visual_dimscreens == 0:
            # hide all rectangles
            for i in range(0x80):
                self.screenrects[i].setBrush(QColor(0, 0, 0, 0))
            return

        # set rectangle colors
        enabledcolor, disabledcolor, duplicatedcolor = self.screentype[AdvSettings.visual_dimscreens]
        for i in range(0x80):
            if self.tilemap.screens[i] == 1:
                self.screenrects[i].setBrush(enabledcolor)
            elif self.tilemap.screens[i] == 0xFB:
                self.screenrects[i].setBrush(duplicatedcolor)
            else:
                self.screenrects[i].setBrush(disabledcolor)

    def cycleDimScreens(self):
        self.setDimScreens((AdvSettings.visual_dimscreens + 1) % 3)

    def setVisible(self, visibility):
        self.visibility = visibility
        for row in self.pixmapgrid:
            for tile in row:
                tile.setVisible(self.visibility)

class QSMA3Layer23(QAbstractLayer):
    def __init__(self, layer, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.height = 0x400
        self.width = 0x200
        self.layer = layer
        self.layerIDoffset = 0
        if layer == 3:
            self.layerIDoffset = 0x200

        self.tilemap = [None]*0x800

        # initialize background copies
        self.blankpixmap = QTransparentPixmap(self.width, self.height)
        self.pixmapitemgrid = []
        for y in range(0, 0x800, self.height):
            for x in range(0, 0x1000, self.width):
                self.pixmapitemgrid.append(QGraphicsPixmapItem(self.blankpixmap))
                self.pixmapitemgrid[-1].setPos(x, y)
                self.pixmapitemgrid[-1].setZValue(self.zvalue)
                self.scene.addItem(self.pixmapitemgrid[-1])

    def dispLayer(self):
        if not self.isVisible():
            # if layer is hidden, queue an update for when it's made visible
            self.delayedupdate = True
            return

        if AdvMetadata.printtime: timer = QtAdvFunc.timerstart()  # debug

        self.tilemap = Adv3Visual.layergraphics.tilemap[self.layer]

        if len(self.tilemap) > 0x800:
            del self.tilemap[0x800:]
        if len(self.tilemap) < 0x800:
            self.tilemap[0:0] = [None]*(0x800-len(self.tilemap))

        layerpixmap = QPixmap(self.blankpixmap)

        # display layer only if it's a background/foreground image
        enabletilemap = SMA3.Constants.layer23enable[self.layer][
            Adv3Attr.sublevel.header[self.layer*2 - 1]]
        if enabletilemap:
          with QPainterSource(layerpixmap) as painter:

            # iterate over 16x16 tiles in tilemap
            for y in range(self.height//0x10):
                for x in range(self.width//0x10):
                    tileprop = self.tilemap[y*self.width//0x10 + x]
                    if tileprop is None:
                        continue
                    tileID_8, paletterow, xflip, yflip = GBA.splittilemap(
                        tileprop)

##                    painter.drawPixmap(x<<4, y<<4, Adv3Visual.getstaticrect(
##                        16, 16, self.layerIDoffset+tileID_8, paletterow,
##                        xflip, yflip))

                    xflip >>= 10  # convert True from 0x400 to 1
                    yflip >>= 10  # convert True from 0x800 to 2

                    for i, offset16 in enumerate((0, 1, 0x10, 0x11)):
                        tilepixmap = Adv3Visual.get8x8(
                            self.layerIDoffset+tileID_8+offset16,
                            paletterow, xflip, yflip)
                        painter.drawPixmap(
                            (i&1^xflip)<<3 | x<<4,
                            (i&2^yflip)<<2 | y<<4,
                            tilepixmap)

        for item in self.pixmapitemgrid:
            item.setPixmap(layerpixmap)

        if AdvMetadata.printtime:
            print("Layer", self.layer, "image pixmap processing:",
              QtAdvFunc.timerend(timer), "ms")  # debug

    def setVisible(self, visibility):
        self.visibility = visibility
        if self.delayedupdate and self.visibility:
            self.dispLayer()
            self.delayedupdate = False
        for item in self.pixmapitemgrid:
            item.setVisible(self.visibility)

class QSublevelScreenGrid(QGraphicsPixmapItem):
    """Grid to display a sublevel's screen boundaries, screen numbers,
    and screen exits."""
    def __init__(self, *args, labels=True):
        super().__init__(*args)

        self.setZValue(250)

        width = 0x1000
        height = 0x800
        self.gridimage = QImage(width, height, QImage.Format.Format_Indexed8)
        self.gridimage.setColorTable((
            0,                          # transparent
            qRgba(33, 33, 33, 181),     # dark gray, for grid
            qRgba(255, 255, 255, 214),  # white, for numbers
            qRgba(239, 140, 41, 214),   # orange, for screen exit highlights
            ))

        pixelarray = self.gridimage.bits().asarray(width*height)

        # draw vertical lines
        for y in range(height):
            for x in range(0x100, width, 0x100):
                pixelarray[width*y + x] = 1
        # draw horizontal lines
        for x in range(width):
            for y in range(0x100, height, 0x100):
                pixelarray[width*y + x] = 1

        if labels:
            for num in range(0x80):
                self.drawnumbox(screen=num, data=((num, 1),),
                    pixelarray=pixelarray, arraywidth=width,
                    bgcolor=1, numcolor=2)
                
        pixmap = QPixmap.fromImage(self.gridimage)
        self.setPixmap(pixmap)

    def drawnumbox(self, screen, data, pixelarray, arraywidth,
                   bgcolor, numcolor):
        """Create a box of numbers or ASCII strings in the top-left corner of
        a screen, with data specified as a tuple of (string, x) pairs."""

        width = max(i[1] for i in data) + 10
        height = 9

        startX = (screen&0xF) * 0x100
        startY = (screen>>4) * 0x100

        # include top row/left edge if applicable
        if startX != 0: xrange = range(startX+1, startX+width)
        else: xrange = range(startX, startX+width)
        if startY != 0: yrange = range(startY+1, startY+height)
        else: yrange = range(startY, startY+height)

        # draw rectangle
        for x in xrange:
            for y in yrange:
                pixelarray[y*arraywidth + x] = bgcolor
        # draw text
        for value, x in data:
            if isinstance(value, int):
                value = format(value, "02X")
            self.dispstr(value, pixelarray, arraywidth, startX+x, startY+1,
                         color=numcolor)

    def dispstr(self, inputstr, pixelarray, arraywidth, startX, startY, color):
        "Draw an ASCII string at the given startX, startY."

        with open(AdvMetadata.datapath("font", "5x8font.bin"), "rb") as bitmap:
            for char in bytes(inputstr, encoding="ASCII"):
                bitmap.seek(char*8)

                y = startY
                for byte in bitmap.read(8):
                    x = startX
                    for bitindex in range(5):
                        bit = (byte >> (7-bitindex)) & 1
                        if bit:
                            pixelarray[arraywidth*y + x] = color
                        x += 1
                    y += 1
                startX += 5

    def dispScreenExits(self, exits):
        """Display a sublevel's screen exits on their corresponding screens.

        Highlights the screen number box, and adds the first 3 bytes of the
        screen exit."""
        if not exits:
            # reload base image, to restore the non-exit screen numbers
            pixmap = QPixmap.fromImage(self.gridimage)
            self.setPixmap(pixmap)
            return

        gridimage = QImage(self.gridimage)  # create copy of base image
        width, height = gridimage.width(), gridimage.height()
        pixelarray = gridimage.bits().asarray(width*height)

        for screen, entr in exits.items():
            self.drawnumbox(screen=screen,
                data=((screen,1), (":", 12),
                      (entr[0], 18), (SMA3.coordstoscreen(*entr[1:3]), 30)),
                pixelarray=pixelarray, arraywidth=width, bgcolor=3, numcolor=2)

        pixmap = QPixmap.fromImage(gridimage)
        self.setPixmap(pixmap)

class QSMA3SpriteLayer(QAbstractLayer):
    """Handles displaying a sublevel's sprites."""
    def __init__(self, *args, mouseinteract=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.mouseinteract = mouseinteract

        # initialize list of sprite items
        self.spriteitems = []

    def loadSprites(self, sublevel):
        if AdvMetadata.printtime: timer = QtAdvFunc.timerstart()  # debug

        for spriteitem in self.spriteitems:
            self.scene.removeItem(spriteitem)
        self.spriteitems = []

        for spr in sublevel.sprites:
            self.addSprite(spr)

        if AdvMetadata.printtime:
            from .MainScene import QSMA3SublevelScene
            if isinstance(self.scene, QSMA3SublevelScene):
                print("Sprite loading:", QtAdvFunc.timerend(timer), "ms")  # debug

    def reloadSpriteGraphics(self, sublevel):
        if AdvMetadata.printtime: timer = QtAdvFunc.timerstart()  # debug

        for spriteitem in self.spriteitems:
            spriteitem.reloadGraphics()

        if AdvMetadata.printtime: print("Sprite pixmap processing:",
            QtAdvFunc.timerend(timer), "ms")  # debug

    def reloadSpriteIDs(self, spriteIDset):
        "Reload graphics of a specific set of sprite IDs."
        for spriteitem in self.spriteitems:
            if spriteitem.ID in spriteIDset:
                spriteitem.reloadGraphics()

    def addSprite(self, spr):
        spriteitem = QSMA3SpriteItem(spr, mouseinteract=self.mouseinteract)
        spriteitem.setVisible(self.visibility)
        self.scene.addItem(spriteitem)
        self.spriteitems.append(spriteitem)

    def updateSprite(self, spr):
        for item in self.spriteitems:
            if item.spr is spr:
                if spr in Adv3Attr.sublevel.sprites:
                    # sprite changed
                    item.update()
                    return
                else:
                    # sprite was deleted
                    self.scene.removeItem(item)
                    self.spriteitems.remove(item)
                    return
        else:
            # new sprite was inserted
            self.addSprite(spr)

    def setVisible(self, visibility):
        self.visibility = visibility
        for spriteitem in self.spriteitems:
            spriteitem.setVisible(self.visibility)

class QSMA3SpriteItem(QGraphicsPixmapItem):
    "Graphics of a single sprite."
    def __init__(self, spr, *args, mouseinteract=False):
        super().__init__(*args)

        self.spr = spr

        if mouseinteract:
            self.setAcceptHoverEvents(True)
            self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        else:
            self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setZValue(200)

        self.setPos(spr.x*16, spr.y*16)

        self.setToolTip(SMA3.SpriteMetadata[(spr.ID, None)].tooltiplong.format(
            extprefix=AdvSettings.extprefix))

        self.reloadGraphics()

    def __getattr__(self, name):
        "Allow this item to retrieve attributes of the associated sprite."
        try:
            return getattr(self.spr, name)
        except AttributeError:
            raise AttributeError(" ".join((repr(self.__class__.__name__),
                "object has no attribute", repr(name))))

    def reloadGraphics(self):
        pixmap, offsetX, offsetY = Adv3Visual.getspritepixmap(
            self.spr.ID, self.spr.parity())
        self.setPixmap(pixmap)
        self.setOffset(offsetX, offsetY)

        # reload tooltip
        if SMA3.SpriteMetadata[(self.spr.ID, None)].parity:
            self.setToolTip(SMA3.SpriteMetadata[
                (self.spr.ID, self.spr.parity())].tooltiplong.format(
                extprefix=AdvSettings.extprefix))

    def update(self):
        self.setPos(self.spr.x*16, self.spr.y*16)
        self.reloadGraphics()
        super().update()

    def hoverMoveEvent(self, event):
        "Propagate event to mouse handler, with current sprite."
        self.scene().mousehandler.hoverMoveEvent(event, self.spr)

    def mousePressEvent(self, event):
        "Propagate event to mouse handler, with this item itself."
        self.scene().mousehandler.mousePressEvent(event, self)

    def mouseMoveEvent(self, event):
        "Propagate event to mouse handler, with current sprite."
        self.scene().mousehandler.mouseMoveEvent(event, self.spr)

    def mouseReleaseEvent(self, event):
        "Propagate event to mouse handler."
        self.scene().mousehandler.mouseReleaseEvent(event)
