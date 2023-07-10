"""Main Window Insertion Sidebar"""

# standard library imports
import os

# import from other files
import AdvMetadata
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr
from AdvGame import SMA3
from .SublevelScene import QSMA3Layer1, QSMA3SpriteLayer
from .GeneralQt import *

class QInsertionSidebar(QDockWidget):
    """Main editor's sidebar, for listing and filtering objects/sprites to
    insert."""
    def __init__(self, *args):
        super().__init__(*args)

        # preview is implemented as a distinct sublevel
        self.sublevel = SMA3.Sublevel()

        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setTitleBarWidget(QWidget())   # remove title bar

        # init widgets

        self.scene = QGraphicsScene(0, 0, 0x90, 0x90)
        self.layer1 = QSMA3Layer1(
            self.scene, width=9, height=9, is_sidebar=True)
        self.spritelayer = QSMA3SpriteLayer(self.scene)
        self.view = QGraphicsViewTransparent(self.scene)
        self.view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.metaicons = []
        for key in self.iconlist:
            self.metaicons.append(QLabel())
            self.metaicons[-1].hide()

        self.graphicstypelabel = QLabelToolTip("\n", prefix="Graphics type:\n")
        self.graphicstypelabel.setWordWrap(True)
        self.graphicstypelabel.setFixedHeight(
            self.graphicstypelabel.sizeHint().height())
        self.graphicstypelabel.setToolTip("")  # no initial tooltip
        self.graphicstypelabel.setSizePolicy(QSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed))

        filterbutton = QPushButton("&Filter")
        filterbutton.setDisabled(True)  # not yet implemented
        filterbutton.setToolTip("Not yet implemented")

        self.objectlist = QListWidgetResized(width=200)
        self.objects = []
        for key, metadata in SMA3.ObjectMetadata.items():
            if 0 <= metadata.enabled < 2:
                continue
            obj = SMA3.Object(**metadata.preview)
            self.objects.append(obj)
            self.objectlist.addItem(": ".join(
                (obj.idstr(AdvSettings.extprefix), metadata.name)))
        self.objectlist.setCurrentRow(0)  # needs to be before connecting
        self.objectlist.itemSelectionChanged.connect(self.selectobject)

        self.spritelist = QListWidgetResized(width=200)
        self.sprites = []
        for key, metadata in SMA3.SpriteMetadata.items():
            if 0 <= metadata.enabled < 2:
                continue
            if metadata.preview["parityID"] is not None:
                continue
            spr = SMA3.Sprite(**metadata.preview)
            self.sprites.append(spr)
            self.spritelist.addItem(": ".join(
                (spr.idstr(), metadata.name)))
        self.spritelist.setCurrentRow(0)  # needs to be before connecting
        self.spritelist.itemSelectionChanged.connect(self.selectsprite)

        for listwidget in self.objectlist, self.spritelist:
            listwidget.itemDoubleClicked.connect(
                AdvWindow.sublevelscene.quickinsertfromsidebar)

        liststack = QTabWidget()
        liststack.tabBarClicked.connect(self.changetab)

        # init layout

        base = QWidget()
        self.setWidget(base)
        layoutMain = QVHBoxLayout()
        base.setLayout(layoutMain)

        layoutMain.addRow()
        layoutMain[-1].addStretch(2)
        layoutMain[-1].addWidget(self.view)

        layoutMetaIcons = QVBoxLayout()
        layoutMain[-1].addLayout(layoutMetaIcons)
        layoutMetaIcons.addStretch()
        for label in self.metaicons:
            layoutMetaIcons.addWidget(label)
        self.setMetaIcons()

        layoutMain[-1].addStretch(1)

        layoutMain.addRow()
        layoutMain[-1].addWidget(self.graphicstypelabel, 3)
        layoutMain[-1].addWidget(filterbutton)

        layoutMain.addWidget(liststack, stretch=109)  # high-priority stretch
        liststack.addTab(self.objectlist, "Objects")
        liststack.addTab(self.spritelist, "Sprites")

    def currentselection(self):
        if self.sublevel.objects:
            return self.sublevel.objects[-1]
        elif self.sublevel.sprites:
            return self.sublevel.sprites[-1]
        # else return nothing

    def reload(self, forcereload=False):
        self.sublevel.header = Adv3Attr.sublevel.header
        self.layer1.createTilemap(self.sublevel)
        self.layer1.updateLayerGraphics(forcereload=forcereload)
        self.spritelayer.loadSprites(self.sublevel)

    def dispobject(self, obj):
        self.sublevel.objects = [obj]
        self.sublevel.sprites.clear()

        metadata = SMA3.ObjectMetadata[obj]

        tooltip = metadata.tooltiplong.format(objID=obj.idstr(
            AdvSettings.extprefix), extprefix=AdvSettings.extprefix)
        self.view.setToolTip(tooltip)

        self.setMetaIcons(
            horiz=metadata.resizing["horiz"],
            vert=metadata.resizing["vert"],
            itemmemory=metadata.itemmemory,
            warp=metadata.warp,
            rng=metadata.rng,
            layer0=metadata.layer0,
            overlap=metadata.overlap,
            )
        self.graphicstypelabel.setText(metadata.graphicstype)

        self.reload()

    def dispsprite(self, spr):
        self.sublevel.sprites = [spr]
        self.sublevel.objects.clear()

        metadata = SMA3.SpriteMetadata[(spr.ID, None)]

        tooltip = SMA3.SpriteMetadata[spr].tooltiplong.format(
            extprefix=AdvSettings.extprefix)
        self.view.setToolTip(tooltip)

        overlap = metadata.overlap
        if overlap: overlap += 2
        self.setMetaIcons(
            itemmemory=metadata.itemmemory,
            parity=metadata.parity,
            warp=metadata.warp,
            rng=metadata.rng,
            overlap=overlap,
            )
        self.graphicstypelabel.setText(
            SMA3.SpriteMetadata[(spr.ID, 0)].graphicstype)

        self.reload()

    def selectobject(self):
        if self.objectlist.currentRow() != -1:
            obj = self.objects[self.objectlist.currentRow()]
            self.dispobject(obj)

    def selectsprite(self):
        if self.spritelist.currentRow() != -1:
            spr = self.sprites[self.spritelist.currentRow()]
            self.dispsprite(spr)

    def changetab(self, tab):
        if tab == 0:
            self.selectobject()
        elif tab == 1:
            self.selectsprite()

    iconlist = {
        "horiz": (None, "arrow-right", "arrow-left", "arrow-leftright"),
        "vert": (None, "arrow-down", "arrow-up", "arrow-updown"),
        "layer0": (None, "layer0"),
        "itemmemory": (None, "yellowcoin", "redcoin", "greencoin"),
        "warp": (None, "door16", None),
        "rng": (None, "rng"),
        "overlap": (None, "overlap-object-blue", "overlap-object-red",
                   "overlap-objspr-blue", "overlap-objspr-red",
                   "overlap-sprite-blue", "overlap-sprite-red"),
        "parity": (None, "parityX", "parityY", "parityYX"),
        }
    icontooltips = {
        "arrow-right": "Positive width only",
        "arrow-left": "Negative width only",
        "arrow-leftright": "Positive/negative width allowed",
        "arrow-down": "Positive height only",
        "arrow-up": "Negative height only",
        "arrow-updown": "Positive/negative height allowed",
        "yellowcoin": "Affected by item memory",
        "redcoin": "Affected by item memory, high priority",
        "greencoin": "Affected by item memory, special",
        "door16": "Uses screen exit",
        "layer0": "Uses layer 0 for foreground graphics",
        "rng": "Affected by RNG",
        "overlap-object-blue": "May change on overlap",
        "overlap-object-red": "Requires overlap to function",
        "overlap-objspr-blue": "May change if overlapping a tile",
        "overlap-objspr-red": "Requires a tile to function",
        "overlap-sprite-blue": "May change if overlapping another sprite",
        "overlap-sprite-red": "Requires another sprite to function",
        "parityX": "Affected by X parity",
        "parityY": "Affected by Y parity",
        "parityYX": "Affected by YX parity",
        }
    def setMetaIcons(self, **kwargs):
        """Display icons for for object metadata properties. Inputs are
        iconlist key, index pairs."""
        icons = False
        for icon in self.metaicons:
            icon.hide()
        for i, (key, iconID) in enumerate(kwargs.items()):
            if self.iconlist[key][iconID]:
                iconname = self.iconlist[key][iconID]
                self.metaicons[i].setPixmap(QPixmap(
                    AdvMetadata.datapath("icon", iconname + ".png")))
                self.metaicons[i].setToolTip(self.icontooltips[iconname])
                self.metaicons[i].show()
                icons = True
        if not icons:
            # is there a better way to lock the layout to 16px wide?
            self.metaicons[0].setPixmap(QTransparentPixmap(16, 16))
            self.metaicons[0].setToolTip("")
            self.metaicons[0].show()

