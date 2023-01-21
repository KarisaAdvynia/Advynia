"""YI title screen dialog? WIP"""

# import from other files
from AdvEditor import Adv3Attr, Adv3Visual
from AdvGame import AdvGame, GBA, SMA3
from .GeneralQt import *
from .TileViewers import QTileGraphicsView

class QYITitleDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("YI Title Screen Sprites")

        self.titlemode = 0

        # init widgets
        self.scene = QGraphicsScene(0, 0, 0x210, 1216)
        self.view = QTileGraphicsView(self.scene, startheight=0x202)

        # init layout
        self.view.setParent(self)

##        layoutMain = QVHBoxLayout()
##        self.setLayout(layoutMain)
##        layoutMain.addWidget(self.view)

    def open(self):
        super().open()
        vertbar = self.view.verticalScrollBar()
        vertbar.setValue(vertbar.minimum())

        self.scene.clear()

        # draw sprites
        with GBA.Open(Adv3Attr.filepath, "rb") as f:
            # import palette
            match self.titlemode:
                case 0:
                    paladdr = 0x0819DA7C
                case 1:
                    paladdr = 0x0819DA9C
            f.seek(paladdr)
            self.spritepalette = []
            for i in range(0x10):
                self.spritepalette.append(f.readint(2))

            # import graphics
            self.spritegraphics = AdvGame.GameGraphics(
                f.read_decompress(0x0819A890), tilesize=0x20)

            for spriteID, ptr in enumerate(range(0x08198680, 0x08198AF8, 8)):
                # import sprite tilemap pointer and properties
                f.seek(ptr)
                tilemapptr = f.readint(4)
                tilecount = f.readint(1)

                x = (spriteID & 7) * 64 + 16
                y = spriteID // 8 * 64 + 64

                if spriteID % 8 == 0:
                    item = self.scene.addPixmap(
                        Adv3Visual.get16x16(0x10600 + spriteID))
                    item.setPos(0, y + 48)

                heightoffset = 64

                f.seek(tilemapptr)
                for i in range(tilecount):
                    # import tile data
                    tileraw = f.readint(2)
                    tileID = tileraw & 0x3FF
                    shapeID = (tileraw >> 0xA) & 3
                    sizeID = (tileraw >> 0xC) & 3
                    width, height = GBA.oamsizes[shapeID][sizeID]
                    xflip = tileraw & 0x4000
                    yflip = tileraw & 0x8000

                    # add tiles to graphics scene
                    item = self.scene.addPixmap(Adv3Visual.getstaticrect_direct(
                        width, height, tileID,
                        self.spritegraphics, self.spritepalette,
                        xflip, yflip
                        ))
                    heightoffset -= height
                    item.setPos(x + (64 - width) // 2,
                                y + heightoffset)

##        image = QImage(int(self.scene.width()), int(self.scene.height()),
##                       QImage.Format.Format_ARGB32)
##        self.scene.render(QPainter(image))
##        image.save("YITitleSprites.png")
