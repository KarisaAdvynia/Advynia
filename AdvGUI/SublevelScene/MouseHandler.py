"""Sublevel Scene Mouse Handler
Processes all types of mouse input for the sublevel scene."""

# standard library imports
import copy, itertools

# import from other files
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr
import AdvEditor
from AdvGame import SMA3
from AdvGUI.GeneralQt import *

def mousetilepos(event, minX=0, maxX=SMA3.Constants.maxtileX,
                        minY=0, maxY=SMA3.Constants.maxtileY):
    "Return the tile coordinates at the mouse's position."
    x, y = int(event.scenePos().x() / 16), int(event.scenePos().y() / 16)
    x = min(max(x, minX), maxX)
    y = min(max(y, minY), maxY)
    return x, y

class QSublevelMouseHandler(QGraphicsRectItem):
    """Mouse handler for the sublevel scene. Processes all mouse inputs and
    hover events."""
    def __init__(self, width, height, *args):
        super().__init__(0, 0, width, height, *args)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemHasNoContents)
        self.setAcceptHoverEvents(True)

        self.action = None
        self.resizeID = 0
        self.pantimer = QTimer()
        self.pantimer.setSingleShot(True)

        self.setZValue(100)

    def detectobj(self, event):
        """Return the tile coordinates, and associated object if any, at the
        mouse's position."""
        x, y = mousetilepos(event)
        for obj in reversed(Adv3Attr.sublevel.objects):
            if (x, y) in obj.tiles:
                break
        else:
            obj = None
        return x, y, obj

    def hoverMoveEvent(self, event, spr=None):
        """Process status bar tile/object/sprite hover text, object tooltip,
        and detecting resize handles."""
        x, y, obj = self.detectobj(event)
        tileID = self.scene().layer1.tilemap[y][x]
        if not self.scene().layer1.isVisible():
            obj = None
            tileID = None

        # status bar hover info
        AdvWindow.statusbar.setHoverText(
            x=x, y=y, tileID=tileID, obj=obj, spr=spr)

        # tooltip detection
        if obj is not None and spr is None:
            tooltip = SMA3.ObjectMetadata[(obj.ID, obj.extID)].tooltiplong
            self.setToolTip(tooltip.format(
                objID=obj.idstr(AdvSettings.extprefix),
                extprefix=AdvSettings.extprefix))
        else:
            self.setToolTip("")

        # resize handles
        self.checkresize(event)

    def hoverLeaveEvent(self, event):
        "Reset the hover resize cursor, but not action cursors."
        if not self.action and QApplication.overrideCursor():
            QApplication.restoreOverrideCursor()

    def checkresize(self, event):
        """Check if the mouse is overlapping a resize handle and no other action
        is occurring. If so, change the cursor and prepare for resizing."""
        if self.action:
            return

        resizeID = 0
        for item in self.scene().resizehandles:
            if item.contains(event.scenePos()):
                resizeID |= item.resizeID

        if resizeID == 3:
            # double overlap: check 4 adjacent corner tiles
            x = round(event.scenePos().x() / 16)
            y = round(event.scenePos().y() / 16)
            tiles = [(x, y), (x-1, y-1), (x-1, y), (x, y-1)]
            adjtiles = AdvWindow.selection.tiles.intersection(tiles)
            fdiag = adjtiles.issubset(tiles[0:2])
            bdiag = adjtiles.issubset(tiles[2:4])
            if fdiag ^ bdiag:
                # only one diagonal: use cursor corresponding to that diagonal
                if bdiag:
                    resizeID = 4
            else:
                # probably a concave corner: fall back to horizontal
                resizeID = 1
        self.resizeID = min(resizeID, 3)

        oldcursor = QApplication.overrideCursor()
        if oldcursor:  # compare shapes or None
            oldcursor = oldcursor.shape()
        newcursor = MouseResizeObjects.resizecursors[resizeID]
        if newcursor != oldcursor:
            if oldcursor: QApplication.restoreOverrideCursor()
            if newcursor: QApplication.setOverrideCursor(newcursor)

    def mousePressEvent(self, event, spriteitem=None):
        "Process the various types of clicks, and initialize mouse dragging."
        x, y, obj = self.detectobj(event)
        if not self.scene().layer1.isVisible():
            obj = None

        selection = AdvWindow.selection
        mouseinput = [event.button().value, event.modifiers().value]

        if mouseinput in AdvSettings.click_selectdrag:
            if self.resizeID:
                self.action = MouseResizeObjects(
                    event.scenePos().x(), event.scenePos().y(),
                    resizeflags=self.resizeID)
            elif spriteitem is not None:
                if spriteitem not in selection.spriteitems:
                    # click is not part of current selection
                    selection.setSelection(sprset={spriteitem})
                self.action = MouseMoveItems(x, y)
            elif obj is not None:
                if obj not in selection.objects and\
                        (x, y) not in selection.tiles:
                    # click is not part of current selection
                    selection.setSelection(objset={obj})
                self.action = MouseMoveItems(x, y)
            else:
                selection.clear()
                self.action = MouseRectSelect(
                    event.scenePos().x(), event.scenePos().y())

        elif mouseinput in AdvSettings.click_selectmulti:
            if spriteitem is not None:
                # select or deselect sprite
                selection.setSelectedSpriteItems(
                    selection.spriteitems ^ {spriteitem})
            elif obj is not None:
                # select or deselect object
                selection.setSelectedObjects(selection.objects ^ {obj})
            self.action = MouseRectSelect(
                event.scenePos().x(), event.scenePos().y(), add=True)

        elif mouseinput in AdvSettings.click_insert:
            # insert object or sprite from sidebar
            self.scene().insertfromsidebar(x, y)

    def mouseMoveEvent(self, event, spr=None):
        "Process mouse dragging."
        if not self.action or self.pantimer.remainingTime() > 0:
            return

        self.action.mousemove(event)

        x, y = event.scenePos().x(), event.scenePos().y()
        self.panscene(x, y, 32, cooldown=30)

        # also process hover event
        self.hoverMoveEvent(event, spr)

    def mouseReleaseEvent(self, event):
        "Delete the current mouse action, to run its finalizer if applicable."
        self.action = None

    def panscene(self, x, y, pandist, cooldown):
        """Scroll the scene if the provided mouse coordinates are near any edge.
        pandist: pixels to move
        cooldown: time to prevent future moves, in milliseconds"""

        view = self.scene().views()[0]
        viewportrect = view.viewport().rect()
        topleft = view.mapToScene(viewportrect.topLeft())
        bottomright = view.mapToScene(viewportrect.bottomRight())
        panwidth = viewportrect.width()/20
        panheight = viewportrect.height()/20

        shiftX, shiftY = 0, 0

        if x > bottomright.x() - panwidth:
            shiftX = +pandist
        elif x < topleft.x() + panwidth:
            shiftX = -pandist
        if y > bottomright.y() - panheight:
            shiftY = +pandist
        elif y < topleft.y() + panheight:
            shiftY = -pandist

        if shiftX:
            self.pantimer.start(cooldown)
            view.horizontalScrollBar().setValue(
                view.horizontalScrollBar().value() + shiftX)
        if shiftY:
            self.pantimer.start(cooldown)
            view.verticalScrollBar().setValue(
                view.verticalScrollBar().value() + shiftY)

class MouseMoveItems:
    "Handles moving selected items with the mouse."
    def __init__(self, x, y):
        self.startX = x
        self.startY = y
        self.mouseX = x
        self.mouseY = y
        self.moved = False

        minX, maxX, minY, maxY = AdvWindow.selection.itemrange()
        self.mouserange = [
            self.startX - minX,
            self.startX + SMA3.Constants.maxtileX - maxX,
            self.startY - minY,
            self.startY + SMA3.Constants.maxtileY - maxY]
##        print("init mouserange:", [format(i, "02X") for i in self.mouserange])

    def mousemove(self, event):
        x, y = mousetilepos(event, *self.mouserange)
        if (x, y) == (self.mouseX, self.mouseY):
            return

        while True:
            offsetX = x - self.mouseX
            offsetY = y - self.mouseY
            try:
                AdvWindow.selection.moveitems(offsetX, offsetY,
                                              setaction=False, raiseerror=True)
                break
            except SMA3.L1TilemapOverflowError as err:
                x -= err.dir[0]
                y -= err.dir[1]
                # cap mouserange to prevent repeated overflow
                if err.dir[1] > 0:
                    self.mouserange[3] -= 1
                elif err.dir[1] < 0:
                    self.mouserange[2] += 1
                if err.dir[0] > 0:
                    self.mouserange[1] -= 1
                elif err.dir[0] < 0:
                    self.mouserange[0] += 1
                if err.dir == [0, 0]:
                    # no direction: something went wrong, break infinite loop
                    raise

        self.mouseX = x
        self.mouseY = y
        self.moved = True

        # update status bar
        AdvWindow.statusbar.setActionText(
            "Moved {items} x{x} y{y}".format(
                items=AdvEditor.Format.sublevelitemstr(
                    AdvWindow.selection.objects, AdvWindow.selection.sprites),
                x=format(x - self.startX, "+03X"),
                y=format(y - self.startY, "+03X")
                ))

    def __del__(self):
        if self.moved:
            AdvWindow.undohistory.addaction("Move")

class MouseResizeObjects:
    "Handles resizing selected objects with the mouse."

    resizecursors = (
        None, Qt.CursorShape.SizeHorCursor, Qt.CursorShape.SizeVerCursor,
        Qt.CursorShape.SizeFDiagCursor, Qt.CursorShape.SizeBDiagCursor)

    def __init__(self, x, y, resizeflags):
        self.startX = x
        self.startY = y
        self.offsetX = 0
        self.offsetY = 0
        self.horiz = resizeflags & 1
        self.vert = resizeflags & 2
        self.resized = False

        self.objects = sorted(AdvWindow.selection.objects,
                              key=Adv3Attr.sublevel.objects.index)
        self.oldsizes = []
        minX, maxX, minY, maxY = 0, 0, 0, 0
        for obj in self.objects:
            # save old object sizes to restore between each move,
            self.oldsizes.append((obj.width, obj.height))

            # calculate initial resize range limits
            resizing = SMA3.ObjectMetadata[(obj.ID, obj.extID)].resizing
            if resizing["horiz"]:
                minX = min(minX, resizing["wmin"] - obj.width)
                maxX = max(maxX, resizing["wmax"] - obj.width)
            if resizing["vert"]:
                minY = min(minY, resizing["hmin"] - obj.height)
                maxY = max(maxY, resizing["hmax"] - obj.height)
        self.rangeX = [minX, maxX] if self.horiz else [0, 0]
        self.rangeY = [minY, maxY] if self.vert else [0, 0]
##        print("init range:", self.rangeX, self.rangeY)

    def mousemove(self, event):
        # check for mouse movements in steps of 1 tile, rounded
        resize = False
        if self.horiz:
            newX = AdvEditor.Number.capvalue(
                round((event.scenePos().x() - self.startX) / 16), *self.rangeX)
            if newX != self.offsetX:
                self.offsetX = newX
                resize = True
        if self.vert:
            newY = AdvEditor.Number.capvalue(
                round((event.scenePos().y() - self.startY) / 16), *self.rangeY)
            if newY != self.offsetY:
                self.offsetY = newY
                resize = True
        if not resize:
            return

        # revert old object sizes
        for obj, (width, height) in zip(self.objects, self.oldsizes):
            obj.width = width
            obj.height = height

        while True:
            # if original sizes, update as is
            if self.offsetX == 0 and self.offsetY == 0:
                AdvWindow.sublevelscene.updateobjects(self.objects)
                AdvWindow.statusbar.setActionText(
                    "Resized " + AdvEditor.Format.sublevelitemstr(self.objects))
                break

            # resize objects
            try:
                AdvWindow.selection.resizeobjects(self.offsetX, self.offsetY,
                                               setaction=False, raiseerror=True)
                break
            except SMA3.L1TilemapOverflowError as err:
                self.offsetX -= err.dir[0]
                self.offsetY -= err.dir[1]
                # cap resize ranges to prevent repeated overflow
                if err.dir[1] > 0:
                    self.rangeY[1] = self.offsetY
                elif err.dir[1] < 0:
                    self.rangeY[0] = self.offsetY
                if err.dir[0] > 0:
                    self.rangeX[1] = self.offsetX
                elif err.dir[0] < 0:
                    self.rangeX[0] = self.offsetX
                if err.dir == [0, 0]:
                    # no direction: something went wrong, break infinite loop
                    raise
        self.resized = True

    def __del__(self):
        if self.resized:
            AdvWindow.undohistory.addaction("Resize")

class QResizeHandle(QGraphicsPathItem):
    def __init__(self, resizeID, basewidth=0, baseheight=0):
        super().__init__()
##        self.setBrush(QColor(0, 255, 0))  # debug
        self.setPen(QColor(0, 0, 0, 0))
        self.setZValue(301)
        self.resizeID = resizeID
        self.basewidth = basewidth
        self.baseheight = baseheight

    def clear(self):
        self.setPath(QPainterPath())

    @property
    def margin(self):
        return AdvSettings.mouse_resizeradius

    def setcollision(self, tiles):
        path = QPainterPath()
        path.setFillRule(Qt.FillRule.WindingFill)
        for x, y in tiles:
            path.addRect((x<<4) - self.margin, (y<<4) - self.margin,
                         self.basewidth + 2*self.margin,
                         self.baseheight + 2*self.margin)
        self.setPath(path)

class MouseRectSelect:
    "Handles selecting a rectangle of items."
    def __init__(self, x, y, add=False):
        self.rectselect = AdvWindow.sublevelscene.rectselect
        self.mousestartX = x
        self.mousestartY = y
        if add:
            self.oldobjects = AdvWindow.selection.objects.copy()
            self.oldspriteitems = AdvWindow.selection.spriteitems.copy()
        else:
            self.oldobjects = frozenset()
            self.oldspriteitems = frozenset()

    def mousemove(self, event):
        if not QApplication.overrideCursor():
            QApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)

        # update selection rectangle
        rect = QRectF(self.mousestartX,
                      self.mousestartY,
                      event.scenePos().x() - self.mousestartX,
                      event.scenePos().y() - self.mousestartY
                      ).normalized()
        self.rectselect.setRect(rect)

        newobjects, newspriteitems = self._calcrect(rect)
        AdvWindow.selection.setSelection(newobjects | self.oldobjects,
                                         newspriteitems | self.oldspriteitems)

    def _calcrect(self, qrect):
        "Return all objects and/or sprites within the given rectangle."
        selectobjects, selectsprites = AdvWindow.selection.checklayers()

        newobjects = set()
        newspriteitems = set()

        if selectobjects:
            coords = qrect.getCoords()
            x1 = int(coords[0] / 16)
            y1 = int(coords[1] / 16)
            x2 = int(coords[2] / 16) + 1
            y2 = int(coords[3] / 16) + 1

            selecttiles = [(x, y) for x, y in itertools.product(
                range(x1, x2), range(y1, y2))]

            for obj in Adv3Attr.sublevel.objects:
                if obj.tiles.intersection(selecttiles):
                    newobjects.add(obj)

        if selectsprites:
            for item in AdvWindow.sublevelscene.spritelayer.spriteitems:
                if item.collidesWithItem(self.rectselect):
                    newspriteitems.add(item)

        return newobjects, newspriteitems

    def __del__(self):
        if QApplication.overrideCursor():
            QApplication.restoreOverrideCursor()
        self.rectselect.setRect(QRectF())
