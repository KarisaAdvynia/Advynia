"""SMA3 Tile Viewers
Dialogs for displaying 8x8 and 16x16 tiles, and their shared base class."""

# standard library imports
from functools import partial
import itertools

# import from other files
from AdvEditor import AdvWindow, Adv3Attr, Adv3Visual, Adv3Patch
from AdvGame import GBA, SMA3
from .GeneralQt import *
from . import QtAdvFunc, HeaderEditor

# Viewer dialog base class

class QTileViewer(QDialog):
    "Base class for the 8x8 and 16x16 tile viewers."
    def __init__(self, parent):
        super().__init__(parent)

        self.queuedupdate = True
        self.savedpos = None
        self.savedsize = None

    def show(self):
        "Restore saved window position/size, and update graphics if queued."
        if self.savedpos is not None:
            self.move(self.savedpos)
        if self.savedsize is not None:
            self.resize(self.savedsize)
        super().show()
        if self.queuedupdate:
            self.runqueuedupdate()
            self.queuedupdate = False

    def closeEvent(self, event):
        "Save window position/size on close, and uncheck the toolbar button."
        AdvWindow.editor.actions[self.actionkey].setChecked(False)
        self.savedpos = self.pos()
        self.savedsize = self.size()
        self.close()

    def reject(self):
        "Overridden to prevent Esc from closing the dialog."
        pass

    def queueupdate(self):
        if not self.isVisible():
            self.queuedupdate = True
            return
        else:
            self.runqueuedupdate()

    def runqueuedupdate(self):
        raise NotImplementedError

# Viewer dialog main classes

class Q8x8TileViewer(QTileViewer):
    """Dialog for displaying the currently loaded 8x8 tiles, and adjusting
    related sublevel settings."""

    actionkey = "Toggle 8x8"

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("8x8 Tile Viewer")

        self.page = 0

        # init widgets
        scenes = {}
        self.views = {}
        self.pixmapitems = {}

        scenes["layer"] = QGraphicsScene(0, 0, 0x80, 0x280)
        self.views["layer"] = QTileGraphicsView(
            scenes["layer"], startheight=0x142, zoom=2)
        self.pixmapitems["layer"] = Q8x8TileViewerItem(height=0x280)
        self.pixmapitems["layer"].viewer = self
        scenes["layer"].addItem(self.pixmapitems["layer"])

        scenes["sprite"] = QGraphicsScene(0, 0, 0x80, 0xA0)
        self.views["sprite"] = QTileGraphicsView(
            scenes["sprite"], startheight=0x142, zoom=2)
        self.pixmapitems["sprite"] = Q8x8TileViewerItem(height=0xA0)
        self.pixmapitems["sprite"].viewer = self
        scenes["sprite"].addItem(self.pixmapitems["sprite"])

        self.stripepixmapitems = []
        for i in range(6):
##        for i in range(8):
            scenes[i] = QGraphicsScene(0, 0, 0x80, 0x10)
            self.views[i] = Q8x8TileStripeView(scenes[i])
##            if i >= 6:
##                self.views[i].hide()
            item = Q8x8TileViewerItem(height=0x10, stripeindex=i)
            item.viewer = self
            self.pixmapitems[i] = item
            scenes[i].addItem(item)

        radiobuttons = []
        for i, text in enumerate(("Layers", "Sprite Global", "Sprite Tileset")):
            radiobuttons.append(QRadioButton(text))
            radiobuttons[i].clicked.connect(partial(self.setLayoutPage, i))
        radiobuttons[0].setChecked(True)

        self.currenttile = QLabel()
        self.currenttile.setPixmap(QTransparentPixmap(16, 16))
        self.tileinfo = QLabel()
        self.settileinfo(None)

        self.paletteinputs = {}
        for key, minvalue, maxvalue, startvalue in (
                ("layer", 0, 0xF, 1),
                ("sprite", 0x10, 0x1F, 0x10)):
            self.paletteinputs[key] = QLineEditByte(
                minvalue=minvalue, maxvalue=maxvalue)
            self.paletteinputs[key].setValue(startvalue)
            self.paletteinputs[key].editingFinished.connect(self.reloadgraphics)

        self.headerdropdowns = {}
        self.headerlabels = {}
        for key in SMA3.Constants.headergraphics:
            self.headerdropdowns[key] = QComboBox()
            if key == 1:
                self.headerdropdowns[1].activated.connect(self.world6patchcheck)
            self.headerdropdowns[key].activated.connect(
                self.updateheaderfromviewer)
            self.headerlabels[key] = QLabel(SMA3.Constants.headersettings[key] + ":")

            if key in SMA3.Constants.headernames:
                for i, settingname in enumerate(SMA3.Constants.headernames[key]):
                    self.headerdropdowns[key].addItem("".join((
                        format(i, "02X"), ": ", settingname)))
            else:
                for i in range(SMA3.Constants.headermaxvalues[key]+1):
                    self.headerdropdowns[key].addItem(format(i, "02X"))

        self.stripelabels = []
        self.stripedropdowns = []
        stripetext = []
        self.stripeIDtoindex = {}
        for i, (ID, desc) in enumerate(SMA3.Constants.stripes):
            stripetext.append("".join((format(ID, "02X"), ": ", desc)))
            self.stripeIDtoindex[ID] = i
        for i in range(6):
            self.stripelabels.append(QLabel("Stripe " + str(i) + ":"))
            self.stripedropdowns.append(QComboBox())
            self.stripedropdowns[-1].addItems(stripetext)
            self.stripedropdowns[-1].activated.connect(
                self.updatestripesfromviewer)

        self.patchbutton = QPushButton("Override")
        self.patchbutton.clicked.connect(
            lambda : Adv3Patch.applypatch("sublevelstripes"))
        # prevent button from being activated with enter
        self.patchbutton.setAutoDefault(False)

        # init layout
        layoutMain = QGridLayout()
        self.setLayout(layoutMain)

        layoutGraphics = QVBoxLayout()
        layoutMain.addLayout(
            layoutGraphics, 0, 0, -1, 1, Qt.AlignmentFlag.AlignHCenter)
        layoutGraphics.addWidget(self.views["layer"])
        layoutGraphics.addWidget(self.views["sprite"])
        for key in self.views:
            if key == "layer":
                layoutGraphics.addWidget(self.views[key], stretch=1)
            else:
                layoutGraphics.addWidget(self.views[key])
        layoutGraphics.addStretch()

        layoutRadioButtons = QHBoxLayout()
        layoutMain.addLayout(layoutRadioButtons, 0, 1, 1, -1)
        for button in radiobuttons:
            layoutRadioButtons.addWidget(button)
        layoutRadioButtons.addStretch()

        layoutMain.addWidget(QLabel("Displayed palette:"), 1, 1)
        for lineedit in self.paletteinputs.values():
            layoutMain.addWidget(lineedit, 1, 2)

        layoutTileInfo = QHBoxLayout()
        layoutMain.addLayout(layoutTileInfo, 2, 1, 1, -1)
        layoutTileInfo.addWidget(self.currenttile)
        layoutTileInfo.addWidget(self.tileinfo)
        layoutTileInfo.addStretch()

        layoutMain.addWidget(QHorizLine(), 3, 1, 1, -1)

        for key in self.headerdropdowns:
            row = layoutMain.rowCount()
            layoutMain.addWidget(self.headerlabels[key], row, 1)
            layoutMain.addWidget(self.headerdropdowns[key], row, 2)

        layoutStripeDropdowns = QGridLayout()
        layoutMain.addLayout(layoutStripeDropdowns, row+1, 1, 1, -1)
        for i in range(6):
            layoutStripeDropdowns.addWidget(self.stripelabels[i], i, 0)
            layoutStripeDropdowns.addWidget(self.stripedropdowns[i], i, 1)
        layoutStripeDropdowns.setColumnStretch(2, 1000)

        layoutOverride = QHBoxLayout()
        layoutMain.addLayout(layoutOverride, row+2, 1, 1, -1)
        layoutOverride.addWidget(self.patchbutton)
        layoutOverride.addStretch()

        layoutMain.setRowStretch(row+3, 1000)

        self.setLayoutPage(0, reload=False)

        minwidths = (
            max(view.sizeHint().width() for view in self.views.values()),
            max(label.sizeHint().width() for label in
                self.headerlabels.values()),
            max(dropdown.sizeHint().width() for dropdown in
                self.headerdropdowns.values()),
            )
        for i, minwidth in enumerate(minwidths):
            layoutMain.setColumnMinimumWidth(i, minwidth)

        # set static window width determined by layout
        self.setFixedWidth(self.sizeHint().width())

    def show(self):
        "Ensure scroll bars start in the top position when first opened."
        super().show()
        if self.savedpos is None:
            for key in ("layer", "sprite"):
                vertbar = self.views[key].verticalScrollBar()
                vertbar.setValue(vertbar.minimum())

    viewpages = {0:["layer"], 1:["sprite"], 2:range(6)}
    headerpages = {0:[1, 3, 5, 0xA], 1:[], 2:[7]}
    def setLayoutPage(self, page, reload=True):
        "Show/hide widgets as needed when swapping between graphics types."
        self.page = page
        for item in self.views.values():
            item.hide()
        for key in self.viewpages[page]:
            self.views[key].show()
        self.paletteinputs["layer"].setVisible(page == 0)
        self.paletteinputs["sprite"].setVisible(page != 0)
        for item in itertools.chain(
                self.headerdropdowns.values(), self.headerlabels.values(),
                self.stripelabels, self.stripedropdowns):
            item.hide()
        self.patchbutton.hide()

        for key in self.headerpages[page]:
            self.headerdropdowns[key].show()
            self.headerlabels[key].show()
        if page == 2:
            for item in itertools.chain(self.stripelabels, self.stripedropdowns):
                item.show()
            self.headerdropdowns[7].setVisible(not Adv3Attr.sublevelstripes)
            self.patchbutton.setVisible(not Adv3Attr.sublevelstripes)

        if reload:
            self.reloadgraphics()

    def updatepatchlayout(self):
        for i in range(6):
            self.stripelabels[i].setEnabled(Adv3Attr.sublevelstripes)
            self.stripedropdowns[i].setEnabled(Adv3Attr.sublevelstripes)
        if self.page == 2:
            self.headerdropdowns[7].setVisible(not Adv3Attr.sublevelstripes)
            self.patchbutton.setVisible(not Adv3Attr.sublevelstripes)

    def updateheaderfromviewer(self):
        """Update the active sublevel's header IDs, using the current settings
        of the dropdowns. Then reload this window's graphics."""
        headertoupdate = {}
        for key in self.headerdropdowns:
            if Adv3Attr.sublevel.header[key] !=\
                    self.headerdropdowns[key].currentIndex():
                headertoupdate[key] = self.headerdropdowns[key].currentIndex()

        if headertoupdate:
            AdvWindow.editor.setHeader(headertoupdate)
            # calls updatefromsublevel in turn

            HeaderEditor.setaction(headertoupdate, usemergeID=True)
        else:
            self.reloadgraphics()

    def updatestripesfromviewer(self):
        """Update the active sublevel's stripe IDs, using the current settings
        of the dropdowns. Then update and reload this window's graphics."""
        stripestoupdate = set()
        for i in range(6):
            index = self.stripedropdowns[i].currentIndex()
            stripeID = SMA3.Constants.stripes[index][0]
            Adv3Attr.sublevel.stripeIDs[i] = stripeID
            if Adv3Visual.spritegraphics.stripeIDs[i] != stripeID:
                stripestoupdate.add(i)

        if stripestoupdate:
            AdvWindow.undohistory.addaction("Edit Sprite Tileset",
                mergeID=("Stripe Slot " + str(tuple(stripestoupdate)[0])
                         if len(stripestoupdate) == 1 else None),
                updateset={"Sprite Graphics"}, reload=True)
            self.reloadgraphics()
            AdvWindow.statusbar.setActionText(
                "Stripe slot " +
                ",".join(str(i) for i in stripestoupdate) +
                " updated.")

    def runqueuedupdate(self):
        self.updatefromsublevel()

    def updatefromsublevel(self):
        """Update dropdowns with the currently active sublevel's header
        settings. Then reload this window's graphics."""
        for i in self.headerdropdowns:
            self.headerdropdowns[i].setCurrentIndex(Adv3Attr.sublevel.header[i])
        for i, stripeID in enumerate(Adv3Attr.sublevel.stripeIDs):
            self.stripedropdowns[i].setCurrentIndex(
                self.stripeIDtoindex[stripeID])
        self.reloadgraphics()

    def reloadgraphics(self):
        "Display the currently active graphics."

        if self.page == 0:  # layers
            paletterow = self.paletteinputs["layer"].value
            with QPainterSource(self.pixmapitems["layer"].pixmap) as painter:
                for tileID in range(0x500):
                    x = tileID % 0x10 * 8
                    y = tileID // 0x10 * 8
                    painter.drawPixmap(x, y, Adv3Visual.get8x8(
                        tileID, paletterow))
            self.pixmapitems["layer"].setPixmap(
                self.pixmapitems["layer"].pixmap)

        elif self.page == 1:  # sprite global
            paletterow = self.paletteinputs["sprite"].value
            with QPainterSource(self.pixmapitems["sprite"].pixmap) as painter:
                for tilebase in range(0, 0x280, 0x20):
                    for tileID in range(tilebase, tilebase+0x10):
                        x = tileID % 0x10 * 8
                        y = tileID // 0x20 * 8
                        painter.drawPixmap(x, y, Adv3Visual.get8x8(
                            tileID, paletterow, sprite=True))
            self.pixmapitems["sprite"].setPixmap(
                self.pixmapitems["sprite"].pixmap)

        elif self.page == 2:  # stripes
            paletterow = self.paletteinputs["sprite"].value
            for i in range(6):
                stripeID = Adv3Visual.spritegraphics.stripeIDs[i]
                with QPainterSource(self.pixmapitems[i].pixmap) as painter:
                    for tileID in range(0x20):
                        x = tileID % 0x10 * 8
                        y = tileID // 0x10 * 8
                        painter.drawPixmap(x, y, Adv3Visual.get8x8(
                            tileID, paletterow, sprite=True, stripeID=stripeID))
                self.pixmapitems[i].setPixmap(
                    self.pixmapitems[i].pixmap)

    def settileinfo(self, tileID, pixmap=None, stripeindex=None):
        "Set text and image for hovering over a given tile."

        if tileID is None:
            text = ["Layer tile\nVRAM"]

        elif self.page == 0:  # layers
            if tileID < len(Adv3Visual.layergraphics.animated) and\
                    Adv3Visual.layergraphics.animated[tileID] is not None:
                tiletype = "Graphics Animation " +\
                           format(Adv3Attr.sublevel.header[0xA], "02X")
            elif 0x80 <= tileID < 0x100:
                tiletype = "Layer 1 Global"
            elif tileID < 0x200:
                tiletype = "Layer 1 Tileset " +\
                           format(Adv3Attr.sublevel.header[1], "X")
            elif 0x240 <= tileID < 0x250:
                tiletype = "Global Animation"
            elif 0x250 <= tileID < 0x280:
                tiletype = "Misc Global"
            elif 0x280 <= tileID < 0x380:
                tiletype = "Layer 2 Image " +\
                           format(Adv3Attr.sublevel.header[3], "02X")
            elif 0x380 <= tileID < 0x480:
                tiletype = "Layer 3 Image " +\
                           format(Adv3Attr.sublevel.header[5], "02X")
            else:
                tiletype = "Unknown"

            text = ["Layer tile ", format(tileID, "03X"), " (", tiletype, ")\n"
                    "VRAM ", format(0x06000000 + tileID*0x20, "08X")]
            if tileID > 0x200:
                text += ["  |  Layer 3: Tile ", format(tileID-0x200, "03X")]

        elif self.page == 1:  # sprite global
            text = ["Sprite tile ", format(tileID, "03X"), "\n"
                    "VRAM ", format(0x06010000 + tileID*0x20, "08X")]

        elif self.page == 2:  # stripes
            stripeID = Adv3Visual.spritegraphics.stripeIDs[stripeindex]
            vram = 0x06010200 + stripeindex*0x800 + tileID*0x20 +\
                   (tileID&0x10)*0x20
            text = ["Sprite stripe ", format(stripeID, "02X"),
                    " tile ", format(tileID, "02X"), "\n"
                    "VRAM ", format(vram, "08X")]

        self.tileinfo.setText("".join(text))

        if not pixmap:
            pixmap = QTransparentPixmap(8, 8)
        self.currenttile.setPixmap(pixmap.scaledToHeight(16))

    def world6patchcheck(self):
        if (self.headerdropdowns[1].currentIndex() > 0xF and
                not Adv3Attr.world6flag):
            applied = Adv3Patch.applypatch("world6flag")
            if not applied:
                self.headerdropdowns[1].setCurrentIndex(0xF)

class Q16x16TileViewer(QTileViewer):
    "Dialog for displaying and selecting layer 1 16x16 tiles."

    actionkey = "Toggle 16x16"

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Layer 1 16x16 Tile Viewer")

        self.tile16x16items = {}
        self.tilenumitems = []
        self.jumpYvalues = []
        self._selectedtile = None

        # init widgets
        self.scene = QGraphicsScene(-0x18, 0, 0x118, 0x2000)
        self.view = QTileGraphicsView(self.scene, startheight=0x182, zoom=1)        

        jumplabel = QLabel("Scroll to high byte")
        self.jumpinput = QLineEditByte("00", maxvalue=0xFF)
        self.jumpinput.textChanged.connect(self.scrolltojumpinput)

        self.currenttile = QLabel()
        self.currenttile.setPixmap(QTransparentPixmap(16, 16))
        self.tileinfo = QLabel()
        self.tileinfo.setMinimumWidth(QtAdvFunc.basewidth(self.tileinfo) * 40)
        self.settileinfo(None)

        insertlabel = QLabel("Insert tile as object")
        self.insertbutton = QPushButton("Insert")
        self.insertbutton.clicked.connect(
            lambda : self.inserttile(self.selectedtile))
        self.insertbutton.setAutoDefault(False)
        self.insertbutton.setDisabled(True)

        # init layout
        layoutMain = QHBoxLayout()
        self.setLayout(layoutMain)
        layoutMain.addWidget(self.view)

        layoutSidebar = QVBoxLayout()
        layoutMain.addLayout(layoutSidebar)
        
        layoutJump = QHBoxLayout()
        layoutSidebar.addLayout(layoutJump)
        layoutJump.addWidget(jumplabel)
        layoutJump.addWidget(self.jumpinput)
        layoutJump.addStretch()

        layoutTileInfo = QHBoxLayout()
        layoutSidebar.addLayout(layoutTileInfo)
        layoutTileInfo.addWidget(self.currenttile)
        layoutTileInfo.addWidget(self.tileinfo)
        layoutTileInfo.addStretch()

        layoutInsert = QHBoxLayout()
        layoutSidebar.addLayout(layoutInsert)
        layoutInsert.addWidget(insertlabel)
        layoutInsert.addWidget(self.insertbutton)
        layoutInsert.addStretch()

        layoutSidebar.addStretch()

        # set static window width determined by layout
        self.setFixedWidth(self.sizeHint().width())

    # init functions

    def show(self):
        "Ensure scroll bar starts in the top position when first opened."
        super().show()
        if self.savedpos is None:
            vertbar = self.view.verticalScrollBar()
            vertbar.setValue(vertbar.minimum())
            self.settileinfo(0)
        self.jumpinput.setFocus()

    def runqueuedupdate(self):
        if not self.tile16x16items:
            self.createtileitems()
        else:
            self.reloadtiles()

    def createtileitems(self):
        maxtile = max(Adv3Attr.tilemapL1_8x8)
        x = 0
        y = 0
        for highbyte in range(maxtile//0x100 + 1):
            tileitem = self.scene.addPixmap(
                Adv3Visual.get16x16(0x10600 + highbyte))
            tileitem.setPos(-0x18, y)
            self.tilenumitems.append(tileitem)
            self.jumpYvalues.append(y)

            for tileID in range(highbyte*0x100, (highbyte+1)*0x100):
                if tileID not in Adv3Attr.tilemapL1_8x8:
                    # add gap between high bytes
                    x = 0
                    y += 0x18
                    break
                elif x == 0x100:
                    # advance to next row
                    x = 0
                    y += 0x10

                tileitem = Q16x16TileViewerItem(
                    self, tileID, Adv3Visual.get16x16(tileID))
                tileitem.setPos(x, y)
                self.scene.addItem(tileitem)
                self.tile16x16items[tileID] = tileitem

                x += 0x10

        # set up for max y
        self.jumpinput.maxvalue = highbyte

        rect = self.scene.sceneRect()
        rect.setBottom(y)
        self.scene.setSceneRect(rect)

    def reloadtiles(self):
        for tileID, item in self.tile16x16items.items():
            item.setPixmap(Adv3Visual.get16x16(tileID))

    # callback functions

    def scrolltojumpinput(self):
        self.view.verticalScrollBar().setValue(
            self.jumpYvalues[self.jumpinput.value])

    @property
    def selectedtile(self):
        return self._selectedtile
    @selectedtile.setter
    def selectedtile(self, value):
        self._selectedtile = value
        self.insertbutton.setDisabled(value is None)

    def inserttile(self, tileID):
        """Insert the current selected tile, if any, in the
        center of the view."""

        if tileID is not None:
            newobj = SMA3.Object(ID=0x65, adjwidth=1, adjheight=1, extID=tileID,
                                 extIDbytes=2)
            scene = AdvWindow.sublevelscene
            scene.insertitems({newobj}, *scene.centertile())

    fliptext = ("", ", X-flip", ", Y-flip", ", XY-flip")
    def settileinfo(self, tileID, pixmap=None):
        "Set text and image for hovering/selecting a given tile."

        if self.selectedtile is not None and tileID != self.selectedtile:
            # selected tile overrides other tiles
            return

        if tileID is None:
            text = ["16x16 tile "] + [""]*4
        else:
            text = ["16x16 tile {tileID}:".format(
                tileID=format(tileID, "04X"))]
            for tileprop in Adv3Attr.tilemapL1_8x8[tileID]:
                tileID_8, paletterow, _, _ = GBA.splittilemap(tileprop)
                text.append(
                    "{tileprop}: 8x8 tile {tileID_8}, palette {pal}"
                    "{flip}".format(
                        tileprop=format(tileprop, "04X"),
                        tileID_8=format(tileID_8, "03X"),
                        pal=format(paletterow, "X"),
                        flip=self.fliptext[(tileprop&0xC00)>>10]
                        ))
        self.tileinfo.setText("\n".join(text))

        if not pixmap:
            pixmap = QTransparentPixmap(16, 16)
        self.currenttile.setPixmap(pixmap)

# Dialog component classes

class QTileGraphicsView(QGraphicsViewTransparent):
    """Graphics view for the 16x16 Tile Viewer, and for non-stripe graphics in
    the 8x8 Tile Viewer."""
    def __init__(self, scene, startheight=0x100, zoom=1):
        super().__init__(scene)

        self.zoom = zoom
        self.fixedwidth = (
            int(scene.width()) * self.zoom +
            self.verticalScrollBar().sizeHint().width() + 2)
        self.startheight = startheight

        self.scale(self.zoom, self.zoom)
        self.setMinimumHeight(self.zoom * 0x80)
        self.setMaximumHeight(int(scene.height()) * self.zoom + 2)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setFixedWidth(self.fixedwidth)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def sizeHint(self):
        return QSize(self.fixedwidth, self.startheight)

class Q8x8TileStripeView(QGraphicsViewTransparent):
    """Graphics view for the 8x8 Tile Viewer, stripe graphics.
    Unlike the other views, this view is fixed size and doesn't have a scroll
    bar."""
    def __init__(self, scene):
        super().__init__(scene)

        self.zoom = 2

        self.scale(self.zoom, self.zoom)
        self.setFixedSize(int(scene.width()) * self.zoom + 2,
                          int(scene.height()) * self.zoom + 2)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

class Q8x8TileViewerItem(QGraphicsPixmapItem):
    """Pixmap item for each graphics scene in the 8x8 Tile Viewer. Sends hover
    event data to the viewer."""
    def __init__(self, height, stripeindex=None):
        super().__init__()

        self.stripeindex = stripeindex
        self.pixmap = QTransparentPixmap(0x80, height)
        self.setAcceptHoverEvents(True)

    def shape(self):
        # ensure item collision detection is always rectangular,
        #  instead of ignoring transparent pixels
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def hoverMoveEvent(self, event):
        x = int(event.pos().x() / 8)
        y = int(event.pos().y() / 8)
        if self.viewer.page == 1:
            tileID = y*0x20 + x
        else:
            tileID = y*0x10 + x
        tilepixmap = self.pixmap.copy(x*8, y*8, 8, 8)
        self.viewer.settileinfo(tileID, tilepixmap, self.stripeindex)

class Q16x16TileViewerItem(QGraphicsPixmapItem):
    """Pixmap item for each tile in the 16x16 Tile Viewer. Sends hover event and
    selection data to the viewer.."""
    def __init__(self, viewer, tileID, *args):
        super().__init__(*args)
        self.setAcceptHoverEvents(True)
        self.setFlags(self.GraphicsItemFlag.ItemIsSelectable)

        self.viewer = viewer
        self.tileID = tileID

    def shape(self):
        # ensure item collision detection is always rectangular,
        #  instead of ignoring transparent pixels
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def hoverEnterEvent(self, event):
        self.viewer.settileinfo(self.tileID, self.pixmap())

    def mouseDoubleClickEvent(self, event):
        self.viewer.inserttile(self.tileID)

    def itemChange(self, change, value):
        if change == self.GraphicsItemChange.ItemSelectedChange:
            if value:
                self.setZValue(1)
                self.viewer.selectedtile = self.tileID
                self.viewer.settileinfo(self.tileID, self.pixmap())
            else:
                self.setZValue(0)
                self.viewer.selectedtile = None
        return super().itemChange(change, value)
