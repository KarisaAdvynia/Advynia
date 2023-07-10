"""Sublevel Scene Selection
Handles displaying, changing, and manipulating the selected items."""

# standard library imports
import itertools

# import from other files
import AdvEditor
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr
from AdvGame import SMA3
from AdvGUI.GeneralQt import *

class QSublevelSelection(QAbstractGraphicsShapeItem):
    def __init__(self):
        super().__init__()
        self.tiles = set()
        self.objects = set()
        self.spriteitems = set()
        self.objpath = QPainterPath()
        self.sprpath = QPainterPath()

        self.selectionchanged = False

        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setZValue(300)

    # Technical methods

    def __len__(self):
        return len(self.objects) + len(self.spriteitems)

    @property
    def sprites(self):
        "Return a list of sprites corresponding to the selected sprite items."
        return [item.spr for item in self.spriteitems]

    def __iter__(self):
        # iterate over both objects and sprites
        return itertools.chain(self.objects, self.sprites)

    def boundingRect(self):
        # display anywhere in the scene
        return self.scene().sceneRect()

    def paint(self, painter, styleoption, widget=None):
        pen = QPen()
        # ensure selection border is still visible at <100% zoom
        pen.setCosmetic(AdvSettings.visual_zoom < 100)
        # draw black line first
        painter.setPen(pen)
        painter.drawPath(self.objpath)
        painter.drawPath(self.sprpath)
        # draw white dashed line on black line
        pen.setColor(0xFFFFFFFF)
        pen.setDashPattern((2, 2))
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        painter.drawPath(self.objpath)
        painter.drawPath(self.sprpath)

    def update(self):
        if self.selectionchanged:
            # enable menu actions
            AdvWindow.editor.enableSelectionActions(
                bool(self), bool(self.objects))

            # prevent undo actions from merging with the previous selection's
            if (AdvWindow.undohistory.mergeID is not None and
                    "Selection" in AdvWindow.undohistory.mergeID):
                AdvWindow.undohistory.mergeID = None

            # update status bar
            AdvWindow.statusbar.setActionText(
                "Selection: " + AdvEditor.Format.sublevelitemstr(
                    self.objects, self.spriteitems))

            self.selectionchanged = False
        super().update()

    # Information methods

    def itemrange(self):
        "Return the min/max X/Y of all items in the selection, in tiles."
        minX = SMA3.Constants.maxtileX
        maxX = 0
        minY = SMA3.Constants.maxtileY
        maxY = 0
        for item in self:
            minX = min(minX, item.x)
            maxX = max(maxX, item.x)
            minY = min(minY, item.y)
            maxY = max(maxY, item.y)
        return minX, maxX, minY, maxY

    def centertile(self):
        "Return the average X/Y of all items in the selection, in tiles."
        sumX = 0
        sumY = 0
        for item in self:
            sumX += item.x
            sumY += item.y
        length = len(self)
        return sumX // length, sumY // length

    def checklayers(self):
        """Check which layers are currently visible, to avoid selecting
        invisible items."""
        selectobjects = self.scene().layer1.isVisible()
        selectsprites = self.scene().spritelayer.isVisible()
        return selectobjects, selectsprites

    def resizeedges(self):
        "Calculate which edges can be used for resizing selected objects."
        horiz = set()
        vert = set()
        for obj in self.objects:
            # defines to save lookups during iteration
            r = SMA3.ObjectMetadata[obj].resizing
            if rhoriz := r["horiz"]:
                widthpositive = (obj.width >= 0 and rhoriz != 2)
                lastX = obj.lastX if hasattr(obj, "lastX") else obj.lasttile[0]
            if rvert := r["vert"]:
                heightpositive = (obj.height >= 0 and rvert != 2)
                lastY = obj.lastY if hasattr(obj, "lastY") else obj.lasttile[1]

            if rhoriz or rvert:
                for x, y in obj.tiles:
                    if rhoriz and x == lastX:
                        if widthpositive:
                            if (x+1, y) not in self.tiles:
                                horiz.add((x+1, y))  # right edge
                        elif (x-1, y) not in self.tiles:
                            horiz.add((x, y))  # left edge
                    if rvert and y == lastY:
                        if heightpositive:
                            if (x, y+1) not in self.tiles:
                                vert.add((x, y+1))  # bottom edge
                        elif (x, y-1) not in self.tiles:
                            vert.add((x, y))  # top edge
##        print("horiz", " ".join(f"{x:02X}{y:02X}" for (x, y) in sorted(horiz)),
##              "vert", " ".join(f"{x:02X}{y:02X}" for (x, y) in sorted(vert, 
##                  key=lambda item : item[1])) )
        return horiz, vert

    # Select/deselect methods

    def setSelection(self, objset=frozenset(), sprset=frozenset()):
        "Change the current selection to the given objects and sprite items."
        self.setSelectedObjects(objset)
        self.setSelectedSpriteItems(sprset)

    def setSelectedObjects(self, objset):
        """Change the currently selected objects to the given set of objects,
        without affecting the currently selected sprites.
        objset=None can be used to deselect all objects."""

        if self.objects != objset:
            self.selectionchanged = True

        self.tiles.clear()

        if not objset:
            # streamlined deselect
            self.objects = set()
            self.objpath = QPainterPath()
            self.update()
            for handle in self.scene().resizehandles:
                handle.clear()
            return

        self.objects = objset
        for obj in objset:
            self.tiles |= obj.tiles

        # update dashed border
        # exterior borders occur once
        # interior borders occur twice and self-cancel
        vertlines = set()
        horizlines = set()
        for x, y in self.tiles:
            vertlines ^= {(x, y), (x+1, y)}
            horizlines ^= {(x, y), (x, y+1)}

        maxX = self.scene().width() - 0.5
        maxY = self.scene().height() - 0.5
        self.objpath = QPainterPath()
        for x, y in vertlines:
            cappedX = min(x<<4, maxX)
            self.objpath.moveTo(cappedX, y<<4)
            self.objpath.lineTo(cappedX, min((y+1)<<4, maxY))
        for x, y in horizlines:
            cappedY = min(y<<4, maxY)
            self.objpath.moveTo(x<<4, cappedY)
            self.objpath.lineTo(min((x+1)<<4, maxX), cappedY)

        # update resize handle collision
        for tiles, handle in zip(self.resizeedges(), self.scene().resizehandles,
                                 strict=True):
            handle.setcollision(tiles)

        self.update()

    def refreshSelectedObjects(self):
        """Recalculate the tiles and redraw the borders of the currently
        selected objects."""
        self.setSelectedObjects(self.objects)

    def setSelectedSpriteItems(self, sprset):
        """Change the currently selected sprite items to the given set, without
        affecting the currently selected objects.
        This accepts sprite items, not sprites!
        sprset=None can be used to deselect all sprites."""

        if self.spriteitems != sprset:
            self.selectionchanged = True

        if not sprset:
            self.spriteitems = set()
            self.sprpath = QPainterPath()
            self.update()
            return
        self.spriteitems = sprset

        self.sprpath = QPainterPath()
        for spriteitem in sprset:
            rect = spriteitem.boundingRect()
            rect.translate(spriteitem.pos())
            self.sprpath.addRect(rect)

        self.update()

    def clear(self):
        if self:
            self.setSelection()

    def selectall(self):
        "Select all visible items."

        selectobjects, selectsprites = self.checklayers()
        if not (selectobjects or selectsprites):
            return

        if selectobjects:
            self.setSelectedObjects(set(Adv3Attr.sublevel.objects))
        else:
            self.setSelectedObjects(None)

        if selectsprites:
            self.setSelectedSpriteItems(
                set(self.scene().spritelayer.spriteitems))
        else:
            self.setSelectedSpriteItems(None)

    # Operations on selected items

    def moveitems(self, offsetX, offsetY, *, setaction=True, raiseerror=False):
        """Move the items in the current selection by offsetX, offsetY tiles.
        If said location would place an item out of bounds, return False, or
        optionally reraise an L1TilemapOverflowError if one was raised."""

        if not self:
            return

        for item in self:
            # if any item would be moved out of bounds, don't move anything
            if not (0 <= item.x + offsetX <= SMA3.Constants.maxtileX and
                    0 <= item.y + offsetY <= SMA3.Constants.maxtileY):
                return False

        for item in self:
            item.backup()
            item.x += offsetX
            item.y += offsetY

        try:
            # update objects first, since they have extra out of bounds checks
            if self.objects:
                self.scene().updateobjects(self.objects)
        except SMA3.L1TilemapOverflowError:
            # object went out of bounds: revert move
            for item in self:
                item.restorebackup()
            if raiseerror: raise
            return False
        else:
            # update sprites
            if self.sprites:
                self.scene().updatesprites(self.sprites)

            if setaction:
                statustext = [
                    "Moved ", 
                    AdvEditor.Format.sublevelitemstr(self.objects, self.sprites),
                    f" x{offsetX:+03X} y{offsetY:+03X}"]
                AdvWindow.statusbar.setActionText("".join(statustext))
                AdvWindow.undohistory.addaction(
                    "Move", mergeID="Move Selection")
            return True

    def moveitemsto(self, x, y):
        """Move the items in the current selection to a specified location.
        If said location would place an item out of bounds, move as close as
        possible."""

        centerX, centerY = self.centertile()
        offsetX = x - centerX
        offsetY = y - centerY

        # prevent any single items from moving out of bounds
        minX, maxX, minY, maxY = self.itemrange()
        if minX + offsetX < 0:
            offsetX = -minX
        elif maxX + offsetX > SMA3.Constants.maxtileX:
            offsetX = SMA3.Constants.maxtileX - maxX
        if minY + offsetY < 0:
            offsetY = -minY
        elif maxY + offsetY > SMA3.Constants.maxtileY:
            offsetY = SMA3.Constants.maxtileX - maxY

        while True:
            try:
                self.moveitems(offsetX, offsetY,
                               raiseerror=True, setaction=False)
                break
            except SMA3.L1TilemapOverflowError as err:
                # prevent objects from generating tiles out of bounds
                offsetX -= err.dir[0]
                offsetY -= err.dir[1]

    def resizeobjects(self, offsetX, offsetY, *,
                      setaction=True, raiseerror=False):
        """Resize selected objects by the given width/height offsets, rounding
        offsets away from 0 if needed.
        If said location would extend an object out of bounds, return False, or
        optionally reraise the L1TilemapOverflowError."""

        if not self.objects:
            return

        update = False
        for obj in self.objects:
            obj.backup()
            resizing = SMA3.ObjectMetadata[obj].resizing

            if resizing["horiz"]:  # object allows horiz resizing
                if offsetX > 0:  # increase width
                    maxwidth = resizing["wmax"]
                    if maxwidth == 0x80 and Adv3Attr.sublevel.header[1] == 2:
                        maxwidth = 0x100
                    newwidth = min(obj.width + offsetX, maxwidth)
                    while obj.width < newwidth:
                        obj.width += resizing["wstep"]
                        update = True
                    obj.width = min(obj.width, maxwidth)
                elif offsetX < 0:  # decrease width
                    minwidth = resizing["wmin"]
                    if minwidth < 0 and Adv3Attr.sublevel.header[1] == 2:
                        minwidth = 0
                    newwidth = max(obj.width + offsetX, minwidth)
                    while obj.width > newwidth:
                        obj.width -= resizing["wstep"]
                        update = True
                    obj.width = max(obj.width, minwidth)
            if resizing["vert"]:  # object allows vert resizing
                if offsetY > 0:  # increase height
                    newheight = min(obj.height + offsetY, resizing["hmax"])
                    while obj.height < newheight:
                        obj.height += resizing["hstep"]
                        update = True
                    obj.height = min(obj.height, resizing["hmax"])
                elif offsetY < 0:  # decrease height
                    newheight = max(obj.height + offsetY, resizing["hmin"])
                    while obj.height > newheight:
                        obj.height -= resizing["hstep"]
                        update = True
                    obj.height = max(obj.height, resizing["hmin"])

        if update:
            try:
                self.scene().updateobjects(self.objects)
            except SMA3.L1TilemapOverflowError:
                # object went out of bounds: revert resize
                for obj in self.objects:
                    obj.restorebackup()
                if raiseerror: raise
                return False  # resize failed
            else:
                statustext = [
                    "Resized ", AdvEditor.Format.sublevelitemstr(self.objects)]
                if offsetX: statustext.append(f" w{offsetX:+03X}")
                if offsetY: statustext.append(f" h{offsetY:+03X}")
                AdvWindow.statusbar.setActionText("".join(statustext))
                if setaction:
                    AdvWindow.undohistory.addaction(
                        "Resize", mergeID="Resize Selection")
                return True  # resize succeeded

    def moveobjectorder(self, direction, *, setaction=True):
        """Move selected objects forward/backward. Does not affect sprite order.
        Directions: +1:forward, +2:to front, -1:backward, -2:to back"""

        if not self.objects or not direction:
            return

        # sort objects by their index in the sublevel
        objects = sorted(self.objects, key=Adv3Attr.sublevel.objects.index)

        if abs(direction) == 1:
            # move backward/forward: calculate set of tiles, for overlap check
            tiles = set()
            for obj in objects: tiles |= obj.alltiles

        if direction == 1:
            # move forward
            startindex = Adv3Attr.sublevel.objects.index(objects[0])
            for obj in Adv3Attr.sublevel.objects[startindex:]:
                # find first distinct overlapping object with a higher index
                if obj not in objects and tiles & obj.alltiles:
                    newindex = Adv3Attr.sublevel.objects.index(obj)
                    break
            else:
                newindex = len(Adv3Attr.sublevel.objects)
            for obj in objects:
                if Adv3Attr.sublevel.objects.index(obj) > newindex:
                    break
                Adv3Attr.sublevel.objects.remove(obj)
                Adv3Attr.sublevel.objects.insert(newindex, obj)
            statustext = "Moved {items} forward."
            actiontext = "Move Forward"
        elif direction == -1:
            # move backward
            startindex = Adv3Attr.sublevel.objects.index(objects[-1])
            for obj in Adv3Attr.sublevel.objects[startindex::-1]:
                # find first distinct overlapping object with a lower index
                if obj not in objects and tiles & obj.alltiles:
                    newindex = Adv3Attr.sublevel.objects.index(obj)
                    break
            else:
                newindex = 0
            # insert last object first, to preserve relative order
            for obj in reversed(objects):
                if Adv3Attr.sublevel.objects.index(obj) < newindex:
                    break
                Adv3Attr.sublevel.objects.remove(obj)
                Adv3Attr.sublevel.objects.insert(newindex, obj)
            statustext = "Moved {items} backward."
            actiontext = "Move Backward"

        elif direction > 1:
            # bring to front
            for obj in objects:
                Adv3Attr.sublevel.objects.remove(obj)
            Adv3Attr.sublevel.objects += objects
            statustext = "Moved {items} to front."
            actiontext = "Move to Front"
        elif direction < -1:
            # send to back
            for obj in objects:
                Adv3Attr.sublevel.objects.remove(obj)
            Adv3Attr.sublevel.objects[0:0] = objects
            statustext = "Moved {items} to back."
            actiontext = "Move to Back"

        self.scene().updateobjects(objects)

        if setaction:
            AdvWindow.statusbar.setActionText(statustext.format(
                items=AdvEditor.Format.sublevelitemstr(objects)))
            AdvWindow.undohistory.addaction(actiontext)

    def deleteitems(self, *, setaction=True):
        "Delete all objects/sprites in the current selection."

        if not self:
            return
        objects = self.objects
        sprites = self.sprites

        statustext = ("Deleted ", AdvEditor.Format.sublevelitemstr(
            objects, sprites, long=True))

        for obj in objects: Adv3Attr.sublevel.objects.remove(obj)
        for spr in sprites: Adv3Attr.sublevel.sprites.remove(spr)
        self.clear()
        if objects: self.scene().updateobjects(objects)
        if sprites: self.scene().updatesprites(sprites)

        if setaction:
            AdvWindow.undohistory.addaction("Delete")
            AdvWindow.statusbar.setActionText("".join(statustext))

class QSublevelRectSelect(QGraphicsRectItem):
    "Shaded rectangle graphic, depicted when drag-selecting multiple items."
    def __init__(self):
        super().__init__()

        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setZValue(301)
        self.setPen(QColor(255, 255, 255, 181))
        self.setBrush(QColor(123, 123, 123, 49))
