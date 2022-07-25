# standard library imports
import copy, itertools

# import from other files
from AdvGame import *
from .QtGeneral import *

# globals
import AdvMetadata, AdvSettings, Adv3Attr, Adv3Visual

class QSMA3SublevelScene(QGraphicsScene):
    """Graphics scene for displaying/editing a currently loaded SMA3 sublevel."""
    def __init__(self, *args):
        super().__init__(0, 0, 0x1000, 0x800, *args)

        # Z values:
        # -300: background
        # -100: layer 2
        #  -50: layer 3 (should vary with the layer 3 image ID)
        #    0: layer 1
        #   99: shaded screens
        #  100: mouse handler
        #  200: sprites
        #  250: grid
        #  300: selection
        #  301: rectangle for drag-selection

        self.mousehandler = QSublevelMouseHandler(0x1000, 0x800)
        self.addItem(self.mousehandler)

        self.background = QSMA3BackgroundGradient(scene=self)
        self.layer1 = QSMA3Layer1(scene=self)
        self.layer2 = QSMA3Layer23(layer=2, scene=self, zvalue=-100)
        self.layer3 = QSMA3Layer23(layer=3, scene=self, zvalue=-50)
        self.spritelayer = QSMA3SpriteLayer(scene=self, mouseinteract=True)

        self.grid = QSublevelScreenGrid(labels=True)
        self.addItem(self.grid)

        self.selection = QSublevelSelection()
        self.addItem(self.selection)

        self.rectselect = QSublevelRectSelect()
        self.addItem(self.rectselect)

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
        AdvSettings.editor.statusbar.setActionText("".join(
            ("Refreshed sublevel ", format(Adv3Attr.sublevel.ID, "02X"),
             ".")))

    def screenshot(self):
        """Save a screenshot of the current scene."""
        image = QImage(0x1000, 0x800, QImage.Format.Format_ARGB32)
        self.render(QPainter(image))

        filepath = "".join(
            ("Sublevel", format(Adv3Attr.sublevel.ID, "02X"),
             ".png"))
        image.save(filepath)

        AdvSettings.editor.statusbar.setActionText("Saved screenshot to "+filepath)

    def updateobjects(self, updateobjs=set()):
        """updateobjs: collection of modified objects, to retrieve tiles
        before and after recalculating the tilemap"""
        updatetiles = set()
        for obj in updateobjs:
            # account for objects' old tiles
            updatetiles |= obj.alltiles

        self.layer1.createTilemap(Adv3Attr.sublevel)

        for obj in updateobjs:
            # account for objects' new tiles
            updatetiles |= obj.alltiles
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
            tilemapnew.screens = self.layer1.tilemap.screens
            self.layer1.tilemap = tilemapnew

            # update graphics in this region
            self.layer1.updateLayerRegion(updatetiles)
        else:
            # if specific objects weren't provided, update entire layer
            self.layer1.updateLayerGraphics()

        self.selection.setSelectedObjects(self.selection.objects)
        AdvSettings.editor.statusbar.updateByteText()

    def updatesprites(self, updatesprs=set()):
        for spr in updatesprs:
            self.spritelayer.updateSprite(spr)

        self.selection.setSelectedSpriteItems(self.selection.spriteitems)
        AdvSettings.editor.statusbar.updateByteText()

    def insertitems(self, items, x, y):
        "Insert one or more objects/sprites at the specified tile coordinates."
        for item in items:
            if isinstance(item, SMA3.Object):
                self.insertobject(item, x, y)
            elif isinstance(item, SMA3.Sprite):
                self.insertsprite(item, x, y)

    def insertobject(self, newobj, x, y):
        "Insert an object at the specified tile coordinates."
        newobj.x, newobj.y = x, y
        Adv3Attr.sublevel.objects.append(newobj)

        # correct for out of bounds insertion
        adjustset = set()
        while True:
            try:
                self.updateobjects(updateobjs={newobj})
                break
            except SMA3.L1TilemapOverflowError as err:
                if err.y < 0xC0:
                    err.obj.y -= 1
                    adjustset.add(-1)
                else:
                    err.obj.y += 1
                    adjustset.add(1)
                if len(adjustset) == 2:
                    # to prevent infinite loop of adjusting y +1/-1,
                    #  shrink object in any valid dimensions
                    print("Debug: object y +1/-1 loop; shrinking object", err.obj)
                    if err.obj.adjheight > 1: err.obj.height -= 1
                    elif err.obj.adjheight < 1: err.obj.height += 1
                    if err.obj.adjwidth > 1: err.obj.width -= 1
                    elif err.obj.adjwidth < 1: err.obj.width += 1
                    adjustset.clear()
        self.selection.setSelection(objset={newobj})

        AdvSettings.editor.statusbar.setActionText("Inserted object " + str(newobj))

    def insertsprite(self, newspr, x, y):
        "Insert a sprite at the specified tile coordinates."
        newspr.x, newspr.y = x, y
        Adv3Attr.sublevel.sprites.append(newspr)

        self.updatesprites({newspr})

        self.selection.setSelection(sprset={self.spritelayer.spriteitems[-1]})

        AdvSettings.editor.statusbar.setActionText("Inserted sprite " + str(newspr))

    def moveselection(self, offsetX, offsetY):
        "Move the current selection by offsetX, offsetY tiles."
        if not self.selection:
            return

        objects = self.selection.objects
        sprites = self.selection.sprites()

        for item in itertools.chain(objects, sprites):
            # if any item would be moved out of bounds, don't move anything
            if item.x + offsetX > SMA3.Constants.maxtileX or item.x + offsetX < 0 or\
               item.y + offsetY > SMA3.Constants.maxtileY or item.y + offsetY < 0:
                return

        for item in itertools.chain(objects, sprites):
            item.backup()
            item.x += offsetX
            item.y += offsetY

        try:
            # update objects first, since they have extra out of bounds checks
            if objects:
                self.updateobjects(objects)
        except SMA3.L1TilemapOverflowError:
            # object went out of bounds: revert move
            for item in itertools.chain(objects, sprites):
                item.restorebackup()
            return False  # move failed
        else:
            # update sprites
            if sprites:
                self.updatesprites(sprites)
            # update status text
            statustext = ["Moved ", sublevelitemstr(objects, sprites),
                          " x", format(offsetX, "+03X"),
                          " y", format(offsetY, "+03X")]
            AdvSettings.editor.statusbar.setActionText("".join(statustext))
            return True  # move succeeded

    def resizeselection(self, offsetX, offsetY):
        """Resize any objects in the current selection by the given
        width/height offsets, rounding offsets away from 0 if needed."""
        objects = self.selection.objects
        if not objects:
            return

        update = False
        oldsizes = []
        for obj in objects:
            obj.backup()
            resizeprop = SMA3.ObjectMetadata[(obj.ID, obj.extID)].resizing
            if resizeprop["wstep"]:  # object allows horiz resizing
                if offsetX > 0:
                    maxwidth = resizeprop["wmax"]
                    if maxwidth == 0x80 and Adv3Attr.sublevel.header[1] == 2:
                        maxwidth = 0x100
                    newwidth = min(obj.adjwidth + offsetX, maxwidth)
                    while obj.adjwidth < newwidth:
                        obj.width += resizeprop["wstep"]
                        update = True
                elif offsetX < 0:
                    minwidth = resizeprop["wmin"]
                    if minwidth < 1 and Adv3Attr.sublevel.header[1] == 2:
                        minwidth = 1
                    newwidth = max(obj.adjwidth + offsetX, minwidth)
                    while obj.adjwidth > newwidth:
                        obj.width -= resizeprop["wstep"]
                        update = True
            if resizeprop["hstep"]:  # object allows vert resizing
                if offsetY > 0:
                    newheight = min(obj.adjheight + offsetY, resizeprop["hmax"])
                    while obj.adjheight < newheight:
                        obj.height += resizeprop["hstep"]
                        update = True
                elif offsetY < 0:
                    newheight = max(obj.adjheight + offsetY, resizeprop["hmin"])
                    while obj.adjheight > newheight:
                        obj.height -= resizeprop["hstep"]
                        update = True
        if update:
            try:
                self.updateobjects(objects)
            except SMA3.L1TilemapOverflowError:
                # object went out of bounds: revert resize
                for obj in objects:
                    obj.restorebackup()
                return False  # resize failed
            else:
                # update status text
                statustext = ["Resized ", sublevelitemstr(objects)]
                if offsetX: statustext += [" w", format(offsetX, "+03X")]
                if offsetY: statustext += [" h", format(offsetY, "+03X")]
                AdvSettings.editor.statusbar.setActionText("".join(statustext))
                return True  # resize succeeded

    def moveobjectorder(self, objects, direction):
        """Move objects forward/backward.
        Directions: +1:forward, +2:to front, -1:backward, -2:to back"""
        if not objects or not direction:
            return
        objects = sorted(objects, key=Adv3Attr.sublevel.objects.index)

        if abs(direction) == 1:
            # move backward/forward: calculate set of tiles, for overlap check
            tiles = set()
            for obj in objects:
                tiles |= obj.alltiles

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

        elif direction > 1:
            # bring to front
            for obj in objects:
                Adv3Attr.sublevel.objects.remove(obj)
            Adv3Attr.sublevel.objects += objects
            statustext = "Moved {items} to front."
        elif direction < -1:
            # send to back
            for obj in objects:
                Adv3Attr.sublevel.objects.remove(obj)
            Adv3Attr.sublevel.objects[0:0] = objects
            statustext = "Moved {items} to back."

        self.updateobjects(objects)

        AdvSettings.editor.statusbar.setActionText(statustext.format(
            items=sublevelitemstr(objects)))

    def deleteselection(self):
        "Delete all objects/sprites in the current selection."
        if not self.selection:
            return
        objects = self.selection.objects
        sprites = self.selection.sprites()

        statustext = ("Deleted ", sublevelitemstr(
            objects, sprites, long=True))

        for obj in objects: Adv3Attr.sublevel.objects.remove(obj)
        for spr in sprites: Adv3Attr.sublevel.sprites.remove(spr)
        self.selection.clear()
        if objects: self.updateobjects(objects)
        if sprites: self.updatesprites(sprites)

        AdvSettings.editor.statusbar.setActionText("".join(statustext))

    # callbacks to connect to actions

    def quickinsertfromsidebar(self):
        """Insert the current sidebar selected object/sprite, if any, in the
        center of the view."""
        newitem = AdvSettings.editor.sidebar.currentselection()
        if newitem:
            self.insertitems({copy.deepcopy(newitem)}, *self.centertile())
    def moveselectionleft(self):
        self.moveselection(-1, 0)
    def moveselectionright(self):
        self.moveselection(1, 0)
    def moveselectionup(self):
        self.moveselection(0, -1)
    def moveselectiondown(self):
        self.moveselection(0, 1)
    def decreaseselectionwidth(self):
        self.resizeselection(-1, 0)
    def increaseselectionwidth(self):
        self.resizeselection(1, 0)
    def decreaseselectionheight(self):
        self.resizeselection(0, -1)
    def increaseselectionheight(self):
        self.resizeselection(0, 1)
    def moveselectionforward(self):
        self.moveobjectorder(self.selection.objects, 1)
    def moveselectionbackward(self):
        self.moveobjectorder(self.selection.objects, -1)
    def moveselectiontofront(self):
        self.moveobjectorder(self.selection.objects, 2)
    def moveselectiontoback(self):
        self.moveobjectorder(self.selection.objects, -2)

class QSublevelMouseHandler(QGraphicsRectItem):
    """Mouse handler for the sublevel scene. Processes all mouse inputs and
    hover events."""
    def __init__(self, width, height, *args):
        super().__init__(0, 0, width, height, *args)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemHasNoContents)
        self.setAcceptHoverEvents(True)

        self.action = None
        self.mouseX = None
        self.mouseY = None
        self.mousestartX = None
        self.mousestartY = None
        self.pantimer = QTimer()
        self.pantimer.setSingleShot(True)

        self.setZValue(100)

    def mousetilepos(self, event):
        "Return the tile coordinates at the mouse's position."
        x, y = int(event.scenePos().x() / 16), int(event.scenePos().y() / 16)
        if x < 0: x = 0
        if x > SMA3.Constants.maxtileX: x = SMA3.Constants.maxtileX
        if y < 0: y = 0
        if y > SMA3.Constants.maxtileY: y = SMA3.Constants.maxtileY
        return x, y

    def detectobj(self, event):
        """Return the tile coordinates, and associated object if any, at the
        mouse's position."""
        x, y = self.mousetilepos(event)
        for obj in reversed(Adv3Attr.sublevel.objects):
            if (x, y) in obj.tiles:
                break
        else:
            obj = None
        return x, y, obj

    def hoverMoveEvent(self, event, spr=None):
        "Process status bar tile/object/sprite hover text, and object tooltip."
        x, y, obj = self.detectobj(event)
        tileID = self.scene().layer1.tilemap[y][x]
        if not self.scene().layer1.isVisible():
            obj = None
            tileID = None

        # status bar hover info
        AdvSettings.editor.statusbar.setHoverText(
            x=x, y=y, tileID=tileID, obj=obj, spr=spr)

        # tooltip detection
        if obj is not None and spr is None:
            tooltip = SMA3.ObjectMetadata[(obj.ID, obj.extID)].tooltiplong
            self.setToolTip(tooltip.format(
                objID=obj.idstr(AdvSettings.extprefix),
                extprefix=AdvSettings.extprefix))
        else:
            self.setToolTip("")

    def mousePressEvent(self, event, spriteitem=None):
        "Process the various types of clicks, and initialize mouse dragging."
        x, y, obj = self.detectobj(event)
        if not self.scene().layer1.isVisible():
            obj = None

        selection = self.scene().selection

        mouseinput = event.button(), event.modifiers()

        if mouseinput == (Qt.MouseButton.LeftButton,
                          Qt.KeyboardModifier.NoModifier):
            # ordinary click
            if spriteitem is not None:
                if spriteitem not in selection.spriteitems:
                    # click is not part of current selection
                    selection.setSelection(sprset={spriteitem})
                self.action = "Move items"
                self.mousestartX, self.mousestartY = x, y
                self.mouseX, self.mouseY = x, y
            elif obj is not None:
                if obj not in selection.objects and\
                        (x, y) not in selection.tiles:
                    # click is not part of current selection
                    selection.setSelection(objset={obj})
                self.action = "Move items"
                self.mousestartX, self.mousestartY = x, y
                self.mouseX, self.mouseY = x, y
            else:
                selection.clear()
                # set up for multiple selection
                self.action = "Rectangle select"
                self.mousestartX, self.mousestartY = (
                    event.pos().x(), event.pos().y())

        elif mouseinput == (Qt.MouseButton.LeftButton,
                            Qt.KeyboardModifier.ShiftModifier):
            # shift+click
            if spriteitem is not None:
                # select or deselect sprite
                selection.setSelectedSpriteItems(
                    selection.spriteitems ^ {spriteitem})
            elif obj is not None:
                # select or deselect object
                selection.setSelectedObjects(selection.objects ^ {obj})

            self.action = "Rectangle select"
            self.scene().selection.addrectinit()
            self.mousestartX, self.mousestartY = (
                event.pos().x(), event.pos().y())

        elif mouseinput in (
              (Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier),
              (Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier)):
            # control+click. Also right-click for now
            # insert object or sprite from sidebar
            newitem = copy.deepcopy(
                AdvSettings.editor.sidebar.currentselection())
            if newitem:
                self.scene().insertitems({newitem}, x, y)

    def mouseMoveEvent(self, event, spr=None):
        "Process mouse dragging."
        if not self.action or self.pantimer.remainingTime() > 0:
            return
        x, y = self.mousetilepos(event)
        
        if self.action == "Move items" and (x, y) != (self.mouseX, self.mouseY):
            offsetX, offsetY = x-self.mouseX, y-self.mouseY
            success = self.scene().moveselection(offsetX, offsetY)
            if success:
                self.mouseX, self.mouseY = x, y
                totalX, totalY = x-self.mousestartX, y-self.mousestartY

                # update status bar
                statustext = "Moved {items} x{x} y{y}"
                AdvSettings.editor.statusbar.setActionText(statustext.format(
                    items=sublevelitemstr(self.scene().selection.objects,
                                          self.scene().selection.sprites()),
                    x=format(totalX, "+03X"),
                    y=format(totalY, "+03X")
                    ))

        elif self.action == "Rectangle select":
           try:
            # update selection rectangle
            rect = QRectF(self.mousestartX,
                          self.mousestartY,
                          event.pos().x() - self.mousestartX,
                          event.pos().y() - self.mousestartY
                          ).normalized()
            self.scene().rectselect.setRect(rect)
            self.scene().selection.selectrect(rect)
           except Exception: print_exc()

        x, y = event.scenePos().x(), event.scenePos().y()
        self.panscene(x, y, 32, cooldown=30)

        # also process hover event
        self.hoverMoveEvent(event, spr)

    def mouseReleaseEvent(self, event):
        "Finalize mouse dragging."
        if self.action == "Rectangle select":
            self.scene().rectselect.setRect(QRectF())
            self.scene().selection.addrectend()
        self.action = None
        self.mouseX = None
        self.mouseY = None
        self.mousestartX = None
        self.mousestartY = None

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

class QSublevelSelection(QAbstractGraphicsShapeItem):
    def __init__(self):
        super().__init__()
        self.tiles = set()
        self.alltiles = set()
        self.objects = set()
        self.spriteitems = set()
        self.objpath = QPainterPath()
        self.sprpath = QPainterPath()

        self.oldobjects = set()
        self.oldspriteitems = set()
        self.selectionchanged = False

        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setZValue(300)

    def __bool__(self):
        "Return False if the current selection is empty."
        return bool(self.objects or self.spriteitems)

    def sprites(self):
        "Return a list of sprites corresponding to the selected sprite items."
        return [item.spr for item in self.spriteitems]

    def boundingRect(self):
        # display anywhere in the scene
        return self.scene().sceneRect()

    def paint(self, painter, styleoption, widget=None):
        pen = QPen()
        # ensure selection border is still visible at <100% zoom
        pen.setCosmetic(AdvSettings.zoom < 100)
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

    def setSelection(self, objset=set(), sprset=set()):
        "Change the current selection to the given objects and sprite items."
        self.setSelectedObjects(objset)
        self.setSelectedSpriteItems(sprset)

        self.update()

    def setSelectedObjects(self, objset):
        """Change the currently selected objects to the given set of objects.
        objset=None can be used to deselect all objects."""
        if self.objects != objset:
            self.selectionchanged = True

        self.tiles.clear()
        self.alltiles.clear()

        if not objset:
            # streamlined deselect
            self.objects = set()
            self.objpath = QPainterPath()
            self.update()
            return

        self.objects = objset
        for obj in objset:
            self.tiles |= obj.tiles
            self.alltiles |= obj.alltiles

        # update dashed border
        vertlines = set()
        horizlines = set()
        for x, y in self.tiles:
            vertlines ^= {(x, y), (x+1, y)}
            horizlines ^= {(x, y), (x, y+1)}

        self.objpath = QPainterPath()
        for x, y in vertlines:
            self.objpath.moveTo(x<<4, y<<4)
            self.objpath.lineTo(x<<4, (y+1)<<4)
        for x, y in horizlines:
            self.objpath.moveTo(x<<4, y<<4)
            self.objpath.lineTo((x+1)<<4, y<<4)

        self.update()

    def setSelectedSpriteItems(self, sprset):
        """Change the currently selected sprite items to the given set.
        This accepts sprite items, not sprites!"""
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

    def selectall(self):
        selectobjects, selectsprites = self.checklayers()
        if not (selectobjects or selectsprites): return

        if selectobjects:
            self.setSelectedObjects(set(Adv3Attr.sublevel.objects))
        else:
            self.setSelectedObjects(None)

        if selectsprites:
            self.setSelectedSpriteItems(
                set(self.scene().spritelayer.spriteitems))
        else:
            self.setSelectedSpriteItems(None)

    def addrectinit(self):
        "Save the current selection, so that selectrect can add to it."
        self.oldobjects = self.objects.copy()
        self.oldspriteitems = self.spriteitems.copy()

    def addrectend(self):
        "Clear the saved selection."
        self.oldobjects.clear()
        self.oldspriteitems.clear()

    def selectrect(self, qrect):
        selectobjects, selectsprites = self.checklayers()
        if not (selectobjects or selectsprites): return

        if selectobjects:
            coords = qrect.getCoords()
            x1 = int(coords[0] / 16)
            y1 = int(coords[1] / 16)
            x2 = int(coords[2] / 16) + 1
            y2 = int(coords[3] / 16) + 1

            selecttiles = []
            for x in range(x1, x2):
                for y in range(y1, y2):
                    selecttiles.append((x, y))

            newobjects = set()
            for obj in Adv3Attr.sublevel.objects:
                if obj.tiles.intersection(selecttiles):
                    newobjects.add(obj)
            self.setSelectedObjects(newobjects | self.oldobjects)

        if selectsprites:
            rectselect = self.scene().rectselect
            newspriteitems = set()
            for item in self.scene().spritelayer.spriteitems:
                if item.collidesWithItem(rectselect):
                    newspriteitems.add(item)
            self.setSelectedSpriteItems(newspriteitems | self.oldspriteitems)

    def checklayers(self):
        selectobjects = self.scene().layer1.isVisible()
        selectsprites = self.scene().spritelayer.isVisible()
        return selectobjects, selectsprites

    def clear(self):
        if self:
            self.setSelection()

    def update(self):
        if self.selectionchanged:
            # also update status bar
            AdvSettings.editor.statusbar.setActionText(
                "Selection: " + sublevelitemstr(self.objects, self.spriteitems))
            self.selectionchanged = False
        super().update()

class QSublevelRectSelect(QGraphicsRectItem):
    def __init__(self):
        super().__init__()

        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setZValue(301)
        self.setPen(QColor(255, 255, 255, 181))
        self.setBrush(QColor(123, 123, 123, 49))

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
            self.colorrects[2*i].setBrush(color15toQRGB(color))
            try:
                nextcolor = color15interpolate(
                    color, Adv3Visual.palette.BGgradient[-i-2])
                self.colorrects[2*i+1].setBrush(color15toQRGB(nextcolor))
            except IndexError:
                pass

class QSMA3Layer1(QAbstractLayer):
    """Handles displaying a sublevel's layer 1 from its objects.
    Specified width and height are in 16x16 tiles, not pixels."""
    def __init__(self, *args, width=0x100, height=0x80, allowYoverflow=False,
                 **kwargs):
        super().__init__(*args, **kwargs)

        self.width = width
        self.height = height
        self.allowYoverflow = allowYoverflow

        self.tilemap = []
        for y in range(self.height):
            self.tilemap.append([0]*self.width)

        timer = timerstart()  # debug

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

        if AdvMetadata.printtime and isinstance(self.scene, QSMA3SublevelScene):
            print("Layer 1 pixmap grid init:", timerend(timer), "ms")  # debug

        # init grid of mostly-transparent screens

        self.screenrects = []
        for screen in range(0x80):
            item = QGraphicsRectItem(0, 0, 0x100, 0x100)
            item.setPen(QPen(Qt.PenStyle.NoPen))
            item.setBrush(qRgb(132, 132, 132))  # why doesn't qRgba work?
            item.setOpacity(0.20)
            item.setPos((screen&0xF) * 0x100, (screen>>4) * 0x100)
            item.setZValue(99)
            item.setVisible(False)
            self.scene.addItem(item)
            self.screenrects.append(item)

    def createTilemap(self, sublevel):
        """Generate the layer 1 tilemap (list) from the editor's active
        sublevel. The previous tilemap is saved to self.tilemapold."""
        timer = timerstart()  # debug

        self.tilemapold = self.tilemap
        self.tilemap = SMA3.L1Constructor(
            sublevel, allowYoverflow=self.allowYoverflow).tilemap

        if AdvMetadata.printtime and isinstance(self.scene, QSMA3SublevelScene):
            print("Layer 1 tilemap generation:", timerend(timer), "ms")  # debug

    def updateLayerGraphics(self, forcereload=False):
        """Update the displayed tiles with the currently loaded tilemap.

        To save time, this will not normally display tiles with unchanged IDs.
        Set forcereload to reload all tiles, such as after a graphics or
        palette edit."""

        timer = timerstart()  # debug

        for y in range(self.height):
            for x in range(self.width):
                self.updateTileGraphics(x, y, forcereload)

        if isinstance(self.scene, QSMA3SublevelScene):
            # run only for main sublevel scene, not sidebar preview
            self.setDimScreens()
            AdvSettings.editor.statusbar.setSizeText(
                newscreencount=self.tilemap.screencount())
            
            if AdvMetadata.printtime: print("Layer 1 pixmap processing:",
                  timerend(timer), "ms")  # debug

    def updateLayerRegion(self, tiles):
        """Update only some of the layer's tiles, specified as a collection
        of (x, y) tuples."""
        timer = timerstart()  # debug

        for x, y in tiles:
            if 0 <= x < self.width and 0 <= y < self.height:
                self.updateTileGraphics(x, y)

        self.setDimScreens()
        AdvSettings.editor.statusbar.setSizeText(
            newscreencount=self.tilemap.screencount())
        if AdvMetadata.printtime: print("Layer 1 pixmap processing:",
              timerend(timer), "ms")  # debug

    def updateTileGraphics(self, x, y, forcereload=False):
        tileID = self.tilemap[y][x]
        if not forcereload and tileID == self.tilemapold[y][x]:
            # don't update identical tiles
            return
        else:
            self.pixmapgrid[y][x].setPixmap(Adv3Visual.get16x16(tileID))

    def setDimScreens(self, enabled=None):
        if enabled is not None:
            AdvSettings.showdimscreens = enabled
        if AdvSettings.showdimscreens:
            for i in range(0x80):
                self.screenrects[i].setVisible(
                    self.tilemap.screens[i] not in (1, 0xFB))
        else:
            for i in range(0x80):
                self.screenrects[i].setVisible(False)

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

        timer = timerstart()  # debug

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

        if AdvMetadata.printtime: print("Layer", self.layer, "image pixmap processing:",
              timerend(timer), "ms")  # debug

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
        timer = timerstart()  # debug

        for spriteitem in self.spriteitems:
            self.scene.removeItem(spriteitem)
        self.spriteitems = []

        for spr in sublevel.sprites:
            self.addSprite(spr)

        if AdvMetadata.printtime and isinstance(self.scene, QSMA3SublevelScene):
            print("Sprite loading:", timerend(timer), "ms")  # debug

    def reloadSpriteGraphics(self, sublevel):
        timer = timerstart()  # debug

        for spriteitem in self.spriteitems:
            spriteitem.reloadGraphics()

        if AdvMetadata.printtime: print("Sprite pixmap processing:",
            timerend(timer), "ms")  # debug

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

# Misc status bar formatting function

def sublevelitemstr(objects=(), sprites=(), long=False):
    "Format a group of objects and/or sprites into status bar text."
    result = []
    if objects:
        if len(objects) == 1:
            result.append("object ")
            if long and not sprites:
                result.append(str(tuple(objects)[0]))
            else:
                result.append(tuple(objects)[0].idstr())
        elif len(objects) > 1:
            result += str(len(objects)), " objects"
    if sprites:
        if result and len(sprites) >= 1:
            result.append(", ")
        if len(sprites) == 1:
            result.append("sprite ")
            if long and not objects:
                result.append(str(tuple(sprites)[0]))
            else:
                result.append(tuple(sprites)[0].idstr())
        elif len(sprites) > 1:
            result += str(len(sprites)), " sprites"

    if result:
        return "".join(result)
    else:
        return "None"

