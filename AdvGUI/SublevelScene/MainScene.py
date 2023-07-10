"""SMA3 Sublevel Scene
Main graphics scene code."""

# standard library imports
import copy, os

# import from other files
import AdvEditor
from AdvEditor import AdvWindow, Adv3Attr, Adv3Patch
from AdvGame import SMA3
from AdvGUI.GeneralQt import *
from .MouseHandler import (QSublevelMouseHandler, QResizeHandle)
from .Layers import (QSMA3BackgroundGradient, QSMA3Layer1, QSMA3Layer23,
                     QSMA3SpriteLayer, QSMA3EntranceLayer, QSublevelScreenGrid)
from .Selection import QSublevelSelection, QSublevelRectSelect

# Z values:
# -300: background
# -100: layer 2
#  -50: layer 3 (should vary with the layer 3 image ID)
#    0: layer 1
#   50: shaded screens
#  100: mouse handler
#  200: sprites
#  230: entrances
#  250: grid
#  300: selection
#  301: rectangle for drag-selection, resize handles

class QSMA3SublevelScene(QGraphicsScene):
    """Graphics scene for displaying/editing a currently loaded SMA3 sublevel."""
    def __init__(self, *args):
        super().__init__(0, 0, 0x1000, 0x800, *args)

        self.clipboard = []

        self.mousehandler = QSublevelMouseHandler(0x1000, 0x800)
        self.addItem(self.mousehandler)

        self.background = QSMA3BackgroundGradient(scene=self)
        self.layer1 = QSMA3Layer1(scene=self, sublevelscene=True)
        self.layer2 = QSMA3Layer23(layer=2, scene=self, zvalue=-100)
        self.layer3 = QSMA3Layer23(layer=3, scene=self, zvalue=-50)
        self.entrancelayer = QSMA3EntranceLayer(scene=self, zvalue=230)
        self.spritelayer = QSMA3SpriteLayer(scene=self, mouseinteract=True)

        self.grid = QSublevelScreenGrid(labels=True)
        self.addItem(self.grid)

        self.selection = QSublevelSelection()
        AdvWindow.selection = self.selection
        self.addItem(self.selection)

        self.rectselect = QSublevelRectSelect()
        self.addItem(self.rectselect)

        self.resizehandles = []
        for item in (QResizeHandle(1, baseheight=0x10),
                     QResizeHandle(2, basewidth=0x10)):
            self.resizehandles.append(item)
            self.addItem(item)

    # Information methods

    def centerpixel(self):
        "Return pixel coordinates of scene's visible center."
        view = self.views()[0]
        center = view.mapToScene(view.viewport().rect().center())
        return center.x(), center.y()

    def centertile(self):
        "Return tile coordinates of scene's visible center."
        x, y = self.centerpixel()
        return int(x/16), int(y/16)

    # Action methods

    def refresh(self):
        """Refresh the current sublevel's tilemap, to reroll RNG-dependent
        objects."""
        self.selection.clear()
        self.layer1.createTilemap(Adv3Attr.sublevel)
        self.layer1.updateLayerGraphics()
        AdvWindow.statusbar.setActionText(
            f"Refreshed sublevel {Adv3Attr.sublevel.ID:02X}.")

    def screenshot(self):
        """Save a screenshot of the current scene."""
        image = QImage(0x1000, 0x800, QImage.Format.Format_ARGB32)
        self.render(QPainter(image))

        filepath = (os.path.splitext(Adv3Attr.filepath)[0] +
                    f"-Sublevel{Adv3Attr.sublevel.ID:02X}.png")
        image.save(filepath)

        AdvWindow.statusbar.setActionText("Saved screenshot to " + filepath)

    def updateobjects(self, updateobjs=frozenset()):
        """updateobjs: collection of modified objects, to retrieve tiles
        before and after recalculating the tilemap"""

        # account for objects' old tiles
        updatetiles = set()
        for obj in updateobjs: updatetiles |= obj.alltiles

        self.layer1.createTilemap(Adv3Attr.sublevel)

        # account for objects' new tiles
        for obj in updateobjs: updatetiles |= obj.alltiles

        if updatetiles:
            # also update the 8 tiles surrounding each tile
            # any overflows are filtered out in updateLayerRegion
            for x, y in list(updatetiles):
                updatetiles |= {
                    (x-1, y-1), (x, y-1), (x+1, y-1),
                    (x-1, y), (x+1, y),
                    (x-1, y+1), (x, y+1), (x+1, y+1)}
            # change layer 1 tilemap to correspond to displayed tilemap
            tilemapnew = copy.deepcopy(self.layer1.tilemapold)
            for x, y in updatetiles:
                if 0 <= x < 0x100 and 0 <= y < 0x80:
                    tilemapnew[y][x] = self.layer1.tilemap[y][x]
            tilemapnew.screenstatus = self.layer1.tilemap.screenstatus
            self.layer1.tilemap = tilemapnew

            # update graphics in this region
            self.layer1.updateLayerRegion(updatetiles)
        else:
            # if specific objects weren't provided, update entire layer
            self.layer1.updateLayerGraphics()

        self.selection.refreshSelectedObjects()
        AdvWindow.statusbar.updateByteText()

    def updatesprites(self, updatesprs=frozenset()):
        for spr in updatesprs:
            self.spritelayer.updateSprite(spr)

        self.selection.setSelectedSpriteItems(self.selection.spriteitems)
        AdvWindow.statusbar.updateByteText()

    def insertitems(self, items, x, y, *, setaction=True):
        "Insert one or more objects/sprites at the specified tile coordinates."

        objects = set()
        sprites = set()
        for item in items:
            item = copy.deepcopy(item)
            if isinstance(item, SMA3.Object):
                if (not Adv3Attr.object65 and item.ID == 0x65 and
                        item.extID is not None):
                    if not Adv3Patch.applypatch("object65"): return False
                Adv3Attr.sublevel.objects.append(item)
                objects.add(item)
            elif isinstance(item, SMA3.Sprite):
                Adv3Attr.sublevel.sprites.append(item)
                sprites.add(item)

        self.selection.setSelection(objset=objects)
        if sprites:
            self.updatesprites(sprites)
            # new sprite items are at end of list
            self.selection.setSelectedSpriteItems(
                set(self.spritelayer.spriteitems[-len(sprites):]))
        self.selection.moveitemsto(x, y)

        if setaction:
            AdvWindow.statusbar.setActionText("Inserted " +
                AdvEditor.Format.sublevelitemstr(objects, sprites, long=True))
            AdvWindow.undohistory.addaction("Insert")
        else:
            return objects, sprites

    def insertfromsidebar(self, x, y):
        """Insert the sidebar's selected object/sprite, if any, at the specified
        coordinates."""
        newitem = AdvWindow.sidebar.currentselection()
        if newitem:
            self.insertitems({newitem}, x, y)

    def quickinsertfromsidebar(self):
        """Insert the sidebar's selected object/sprite, if any, in the center
        of the view."""
        self.insertfromsidebar(*self.centertile())

    ## Clipboard

    def copy(self):
        "Copy the items in the current selection."

        objects = sorted(self.selection.objects,
                         key=Adv3Attr.sublevel.objects.index)
        sprites = sorted((item.spr for item in self.selection.spriteitems),
                         key=Adv3Attr.sublevel.sprites.index)
        newclipboard = objects + sprites
        if newclipboard:
            self.clipboard = copy.deepcopy(newclipboard)
            AdvWindow.editor.actions["Paste"].setEnabled(True)

            AdvWindow.statusbar.setActionText("Copied " +
                AdvEditor.Format.sublevelitemstr(objects, sprites))
            return True
        return False

    def cut(self):
        "Copy the items in the current selection, then delete them."

        if not self.copy():
            return False
        actiontext = "Cut " + AdvEditor.Format.sublevelitemstr(
            self.selection.objects, self.selection.spriteitems)
        self.selection.deleteitems(setaction=False)

        AdvWindow.statusbar.setActionText(actiontext)
        AdvWindow.undohistory.addaction("Cut")
        return True

    def paste(self):
        "Insert previously copied or cut items in the center of the view."

        if not self.clipboard:  # action should be disabled, but just in case
            return False
        items = self.insertitems(self.clipboard, *self.centertile(),
                                 setaction=False)
        if not items:
            return False

        AdvWindow.statusbar.setActionText("Pasted " +
            AdvEditor.Format.sublevelitemstr(*items))
        AdvWindow.undohistory.addaction("Paste")
        return True

