"""SMA3 Layer 2/3 Viewer"""

# standard library imports
from functools import partial

# import from other files
from AdvEditor import Adv3Attr, Adv3Visual
from AdvGame import GBA, SMA3
from .GeneralQt import *
from .TileViewers import QTileGraphicsView

class QSMA3LayerViewer(QDialogViewerBase):
    """???????"""

    actionkey = "Layer Viewer"

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Layer 2/3 Viewer")

        self.layer = 2
        self.tilemap = None

        # init widgets
        scene = QGraphicsScene(0, 0, 0x200, 0x400)
        self.view = QTileGraphicsView(scene, startheight=0x200)
        self.pixmapitem = QSMA3LayerViewerItem(self)
        scene.addItem(self.pixmapitem)

        radiobuttons = {}
        for layer in (2, 3):
            radiobuttons[layer] = QRadioButton("Layer " + str(layer))
            radiobuttons[layer].clicked.connect(partial(self.changelayer, layer))
        radiobuttons[self.layer].setChecked(True)

        self.layername = QLabel()
        self.hoverinfo = QLabel()

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addRow()
        for button in radiobuttons.values():
            layoutMain[-1].addWidget(button)
        layoutMain[-1].addSpacing(10)
        layoutInfo = QVBoxLayout()
        layoutMain[-1].addLayout(layoutInfo)
        layoutMain[-1].addStretch()

        layoutInfo.addWidget(self.layername)
        layoutInfo.addWidget(self.hoverinfo)

        layoutMain.addWidget(self.view)

    def show(self):
        "Ensure scroll bar starts in the top position when first opened."
        super().show()
        if self.savedpos is None:
            vertbar = self.view.verticalScrollBar()
            vertbar.setValue(vertbar.minimum())
            self.tilehover(0, 0)

    def runqueuedupdate(self):
        self.reload()

    def changelayer(self, layernum):
        self.layer = layernum
        self.reload()

    def reload(self):
        # update layer image
        layerpixmap = Adv3Visual.getlayerpixmap(self.layer, 0x200, 0x400)
        self.pixmapitem.setPixmap(layerpixmap)

        # update layer text
        index = self.layer*2 - 1
        imageID = Adv3Attr.sublevel.header[index]
        self.layername.setText(
            f"{SMA3.Constants.header[index].name} {imageID:02X}: "
            f"{SMA3.Constants.header[index].names[imageID]}")

        # update tilemap reference
        self.tilemap = Adv3Visual.layergraphics.tilemap[self.layer]

    def tilehover(self, x, y):
        tileprop = self.tilemap[y * 0x20 + x]
        text = f"x{x:02X} y{y:02X} | "
        if tileprop is None:
            text += "None"
        else:
            tileID_8, paletterow, xflip, yflip = GBA.splittilemap(tileprop)
            if self.layer == 3: tileID_8 += 0x200

            tiles = [None]*4
            for i, offset16 in enumerate((0, 1, 0x10, 0x11)):
                if xflip: i ^= 1
                if yflip: i ^= 2
                tiles[i] = tileID_8 + offset16

            tileID_8str=",".join(f"{tileID:03X}" for tileID in tiles)
            flip=("", ", X-flip", ", Y-flip", ", XY-flip")[(tileprop&0xC00)>>10]
            text += (f"{tileprop:04X}: 8x8 tiles {tileID_8str}, "
                     f"palette {paletterow:X}{flip}")
        self.hoverinfo.setText(text)

class QSMA3LayerViewerItem(QGraphicsPixmapItem):
    def __init__(self, viewer, *args):
        super().__init__(*args)
        self.setAcceptHoverEvents(True)

        self.viewer = viewer
        self.oldcoords = None

    def shape(self):
        # ensure item collision detection is always rectangular,
        #  instead of ignoring transparent pixels
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def hoverMoveEvent(self, event):
        newcoords = int(event.pos().x() / 16), int(event.pos().y() / 16)
        if newcoords != self.oldcoords:
            self.oldcoords = newcoords
            self.viewer.tilehover(*newcoords)
