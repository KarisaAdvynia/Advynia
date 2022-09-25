"""SMA3 Editor Main Window"""

# standard liberary imports
from functools import partial
import itertools

# import from other files
import AdvMetadata, AdvEditor.ROM
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr, Adv3Sublevel, Adv3Visual
from . import QtAdvFunc
from .GeneralQt import *
from .SublevelScene import QSMA3SublevelScene
from .InsertionSidebar import QInsertionSidebar
from .StatusBar import QMainEditorStatusBar
from .PaletteViewer import QSMA3PaletteViewer
from .TileViewers import Q8x8TileViewer, Q16x16TileViewer
from .Dialogs import *
from .EntranceEditor import QDialogSMA3LevelEntrances, QDialogSMA3ScreenExits
from .HeaderEditor import QSMA3HeaderEditor
from .TextEditor import QSMA3TextEditor

class QSMA3Editor(QMainWindow):
    """Main GUI window. Handles editor init, main window layout, and
    toolbar/menu bar actions."""
    def __init__(self):
        if AdvMetadata.printtime: timer = QtAdvFunc.timerstart()  # debug

        super().__init__()

        AdvWindow.editor = self

        self.windowtitle = [AdvMetadata.appnamefull]
        self.setWindowTitle(" - ".join(self.windowtitle))
        self.setWindowIcon(QAdvyniaIcon("Advynia3.png"))

        # load window position/size
        try:
            QtAdvFunc.protectedmoveresize(self, *AdvSettings.window_SMA3Editor)
        except Exception:
            AdvSettings._resetsetting("window_SMA3Editor")
            QtAdvFunc.protectedmoveresize(self, *AdvSettings.window_SMA3Editor)

        # initialize central sublevel scene
        AdvWindow.sublevelscene = QSMA3SublevelScene()
        self.sublevelview = QGraphicsView(AdvWindow.sublevelscene)
        zoomfloat = AdvSettings.visual_zoom/100
        self.sublevelview.scale(zoomfloat, zoomfloat)
        self.setCentralWidget(self.sublevelview)

        # start sublevel view in lower-left corner
        horizscroll = self.sublevelview.horizontalScrollBar()
        horizscroll.setValue(horizscroll.minimum())
        vertscroll = self.sublevelview.verticalScrollBar()
        vertscroll.setValue(vertscroll.maximum())

        # initialize sidebar
        AdvWindow.sidebar = QInsertionSidebar(self)
        if AdvSettings.window_sidebarpos not in (1, 2):
            AdvSettings.window_sidebarpos = 1
        self.addDockWidget(Qt.DockWidgetArea(AdvSettings.window_sidebarpos),
                           AdvWindow.sidebar)

        # initialize status bar
        AdvWindow.statusbar = QMainEditorStatusBar()
        self.setStatusBar(AdvWindow.statusbar)

        # initialize dialogs
        self.viewerpalette = QSMA3PaletteViewer(self)
        self.viewer8x8 = Q8x8TileViewer(self)
        self.viewer16x16 = Q16x16TileViewer(self)
        self.headereditor = QSMA3HeaderEditor(self)

        # initialize toolbar/menu and actions
        # (actions frequently reference other objects, so this should be last)
        self.initActions()

        if AdvMetadata.printtime: print("Total editor init:",
              QtAdvFunc.timerend(timer), "ms")  # debug

    def initActions(self):
        """Initialize the main window's actions, and the toolbar/menu bar
        containing them."""

        actiondata = {
            #key: text, tooltip, shortcut, triggered, icon, checked
            "Exit":("E&xit", None, "Ctrl+Q", QApplication.quit, None, None),
            "Open ROM":("&Open ROM...", None, "Ctrl+O",
                        AdvEditor.ROM.opendialog, None, None),
            "Load Sublevel":("&Load Sublevel...", None, "Ctrl+D",
                             QDialogLoadSublevel(self).open, None, None),
            "Save Sublevel":("&Save Sublevel to ROM", "Save Sublevel", "Ctrl+S",
                             Adv3Sublevel.savesublevel_action, None, None),
            "Save Sublevel As":(
                "Save Sublevel to ROM &As...", None, "Ctrl+Shift+S",
                QDialogSaveSublevelAs(self).open, None, None),
            "Import Sublevel":(
                "&Import Sublevel from File...", None, "Ctrl+Shift+I",
                Adv3Sublevel.importsublevel, None, None),
            "Export Sublevel":(
                "&Export Sublevel to File...", None, "Ctrl+Shift+E",
                Adv3Sublevel.exportsublevel_action, None, None),
            "Export All Sublevels":(
                "Export All Sublevels...", None, None,
                Adv3Sublevel.exportallsublevels, None, None),
            "Export SNES Sublevels":(
                "Extract Sublevels from SNES...", None, None,
                Adv3Sublevel.exportSNESsublevels, None, None),
            "Info":("Current ROM Info", None, "Ctrl+I",
                    QDialogROMInfo(self).open, None, None),
            "Undo":("&Undo", None, "Ctrl+Z",
                    AdvWindow.undohistory.undo, None, None),
            "Redo":("&Redo", None, ("Ctrl+Y", "Ctrl+Shift+Z"),
                    AdvWindow.undohistory.redo, None, None),
            "Cut":("Cu&t", None, "Ctrl+X",
                   AdvWindow.sublevelscene.cut, None, None),
            "Copy":("&Copy", None, "Ctrl+C",
                    AdvWindow.sublevelscene.copy, None, None),
            "Paste":("&Paste", None, "Ctrl+V",
                     AdvWindow.sublevelscene.paste, None, None),
            "Select All":("Select &All", None, "Ctrl+A",
                          AdvWindow.selection.selectall,
                          None, None),
            "Insert":(
                "&Insert Object/Sprite", None, ("", "Insert"),
                AdvWindow.sublevelscene.quickinsertfromsidebar, None, None),
            "Delete":(
                "&Delete Objects/Sprites", None, ("Delete", "Backspace"),
                AdvWindow.selection.deleteitems, None, None),
            "Move Left":("Move &Left", None, "Ctrl+Left",
                lambda : AdvWindow.selection.moveitems(-1, 0), None, None),
            "Move Right":("Move &Right", None, "Ctrl+Right",
                lambda : AdvWindow.selection.moveitems(1, 0), None, None),
            "Move Up":("Move &Up", None, "Ctrl+Up",
                lambda : AdvWindow.selection.moveitems(0, -1), None, None),
            "Move Down":("Move &Down", None, "Ctrl+Down",
                lambda : AdvWindow.selection.moveitems(0, 1), None, None),
            "Decrease Width":("Decrease Width", None, "Shift+Left",
                lambda : AdvWindow.selection.resizeobjects(-1, 0), None, None),
            "Increase Width":("Increase Width", None, "Shift+Right",
                lambda : AdvWindow.selection.resizeobjects(1, 0), None, None),
            "Decrease Height":("Decrease Height", None, "Shift+Up",
                lambda : AdvWindow.selection.resizeobjects(0, -1), None, None),
            "Increase Height":("Increase Height", None, "Shift+Down",
                lambda : AdvWindow.selection.resizeobjects(0, 1), None, None),
            "Move Forward":("Move Forward", None, "]",
                lambda : AdvWindow.selection.moveobjectorder(1), None, None),
            "Move Backward":("Move Backward", None, "[",
                lambda : AdvWindow.selection.moveobjectorder(-1), None, None),
            "Move to Front":("Move to Front", None, "Ctrl+]",
                lambda : AdvWindow.selection.moveobjectorder(2), None, None),
            "Move to Back":("Move to Back", None, "Ctrl+[",
                lambda : AdvWindow.selection.moveobjectorder(-2), None, None),
            "Clear Sublevel":("&Clear Sublevel...", None,
                              ("Ctrl+Delete", "Ctrl+Backspace"),
                              QDialogClearSublevel(self).open, None, None),
            "Filter":("&Filter Sidebar...", None, "Ctrl+F",
                      None, None, None),
            "Quick Filter":("&Quick Filter", None, "Ctrl+Shift+F",
                      None, None, None),
            "Edit Header":(
                "Edit Sublevel &Header...", None, "Ctrl+H",
                self.headereditor.open, "yoshi.png", None),
            "Edit Screen Exits":(
                "Edit &Screen Exits...", None, "Ctrl+E",
                QDialogSMA3ScreenExits(self).open, "door16.png", None),
            "Edit Level Entrances":(
                "Edit &Level Entrances...", None, "Ctrl+L",
                QDialogSMA3LevelEntrances(self).open, "egg.png", None),
            "Edit Messages":("Edit &Messages...", None, "Ctrl+M",
                             QSMA3TextEditor(self).open, "messageblock.png",
                             None),
            "Edit Internal Name":("Edit Internal ROM &Name...", None, None,
                                  QDialogInternalName(self).open, None, None),
            "Toggle Palette":("&Palette Viewer", None, "Ctrl+P",
                QtAdvFunc.createdialogtogglefunc(self.viewerpalette),
                              "palette.png", False),
            "Toggle 8x8":("&8x8 Tile Viewer", None, "Ctrl+8",
                QtAdvFunc.createdialogtogglefunc(self.viewer8x8),
                          "8x8.png", False),
            "Toggle 16x16":("Layer 1 1&6x16 Tile Viewer", None, "Ctrl+6",
                QtAdvFunc.createdialogtogglefunc(self.viewer16x16),
                          "16x16.png", False),
            "Refresh":("&Refresh", "Refresh\n"
                       "Refresh the current layer 1 tilemap, to reroll\n"
                       "RNG-dependent objects.", "Ctrl+R",
                       AdvWindow.sublevelscene.refresh, "refresh.png", None),
            "Zoom In":("Zoom &In", None, ("Ctrl++", "Ctrl+="),
                       self._zoomin, None, None),
            "Zoom Out":("Zoom &Out", None, "Ctrl+-", self._zoomout, None, None),
            "Zoom Button":("Zoom", None, None, None, None, None),
            "Show Layer 1":("Layer &1", None, "1",
                QtAdvFunc.createtogglefunc(AdvWindow.sublevelscene.layer1),
                            None, True),
            "Show Layer 2":("Layer &2", None, "2",
                QtAdvFunc.createtogglefunc(AdvWindow.sublevelscene.layer2),
                            None, True),
            "Show Layer 3":("Layer &3", None, "3",
                QtAdvFunc.createtogglefunc(AdvWindow.sublevelscene.layer3),
                            None, True),
            "Show Sprites":("&Sprites", None, "4",
                QtAdvFunc.createtogglefunc(AdvWindow.sublevelscene.spritelayer),
                            None, True),
            "Show Grid":("&Grid", "Show/Hide Screen Grid", "G",
                QtAdvFunc.createtogglefunc(AdvWindow.sublevelscene.grid),
                         "grid.png", True),
            "Cycle Enabled Screens":("&Quick Swap", None, "U",
                AdvWindow.sublevelscene.layer1.cycleDimScreens, None, None),
            "Show Red Coins":("&Red Coin Palette", None, None,
                self._magnifyingglass, None, AdvSettings.visual_redcoins),
            "Screenshot":("&Screenshot", None, "F12",
                          AdvWindow.sublevelscene.screenshot, None, None),
            "Count Items":("&Count Red Coins/Flowers", None, "F10",
                           Adv3Sublevel.countitems, "redcoin.png", None),
            "Item Memory":("Check &Item Memory", None, "F11",
                           Adv3Sublevel.itemmemorycheck, "cloud.png", None),
            "Export Graphics":("&Export Graphics/Tilemaps",
                "Export Graphics/Tilemaps\n"
                "Export all graphics and compressed tilemaps.", None,
                Adv3Visual.exportgraphics, "graphicsexport.png", None),
            "Import Graphics":("&Import Graphics/Tilemaps", None, None,
                               None, "graphicsimport.png", None),
            "About":("&About Advynia", None, "F1",
                     QDialogAbout(self).open, None, None),
            }

        actiongroups = {}
        for key in ("Screens", "Zoom"):
            actiongroups[key] = QActionGroup(self)

        self.actions = {}

        for key, (text, tooltip, shortcut, triggered, icon, checked) in\
                actiondata.items():
            args = []
            if icon: args.append(QAdvyniaIcon(icon))
            if text: args.append(text)
            action = QAction(*args)
            if tooltip: action.setToolTip(tooltip)
            if shortcut:
                try:
                    action.setShortcut(shortcut)
                except TypeError:
                    action.setShortcuts(shortcut)
            if triggered:
                action.triggered.connect(triggered)
            else:
                action.setDisabled(True)
            if checked is not None:
                action.setCheckable(True)
                action.setChecked(checked)
            self.actions[key] = action

        # extra action init, not in main tuples

        self.actions["Open ROM"].setIconText("Open")
        self.actions["Load Sublevel"].setIconText("Load")
        self.actions["Save Sublevel"].setIconText("Save")

        for actionkey in ("Undo", "Redo", "Paste"):
            self.actions[actionkey].setDisabled(True)

        for actionkey in ("Undo", "Redo",
                          "Toggle Palette", "Toggle 8x8", "Toggle 16x16"):
            self.actions[actionkey].setShortcutContext(
                Qt.ShortcutContext.ApplicationShortcut)

        # init Enabled Screens submenu actions
        for i, text in enumerate(("&No Shading", "&Default", "&High Contrast")):
            action = QAction(text, actiongroups["Screens"])
            action.triggered.connect(
                partial(AdvWindow.sublevelscene.layer1.setDimScreens, i))
            action.setCheckable(True)
            action.setChecked(AdvSettings.visual_dimscreens == i)
            self.actions["Screens" + str(i)] = action

        # initialize menu bar
        menubar = self.menuBar()
        self.menus = {}
        menubaractions = (
            # main menus
            ("&File", (
                "Open ROM", "Menu:&Recent ROMs",
                "Load Sublevel", "Save Sublevel", "Save Sublevel As", 0,
                "Import Sublevel", "Export Sublevel", "Export All Sublevels",
                "Export SNES Sublevels", 0,
                "Info", 0,
                "Exit")),
            ("&Edit", (
                "Undo", "Redo", 0,
                "Cut", "Copy", "Paste", "Insert", "Delete", 
                "Menu:&Resize Selected Objects",
                "Menu:Change Object &Order", "Select All", "Clear Sublevel", 0,
                "Filter", "Quick Filter", 0,
                "Edit Header", "Edit Screen Exits", 0,
                "Edit Level Entrances", "Edit Messages", "Edit Internal Name",
                )),
            ("&View", (
                "Toggle Palette", "Toggle 8x8", "Toggle 16x16", 0,
                "Refresh", "Menu:&Zoom", 0,
                "Show Layer 1", "Show Layer 2", "Show Layer 3",
                "Show Sprites", "Show Grid", "Menu:&Enabled Screens",
                "Show Red Coins",
                )),
            ("&Misc", (
                "Screenshot", 0,
                "Count Items", "Item Memory", 0,
                "Export Graphics", "Import Graphics",
                )),
            ("&Help", (
                "About",
                )),
            # submenus
##            ("Move Selection", (
##                "Move Left", "Move Right", "Move Up", "Move Down",
##                )),
            ("Resize Selected Objects", (
                "Decrease Width", "Increase Width", 
                "Decrease Height", "Increase Height",
                )),
            ("Change Object Order", (
                "Move Forward", "Move Backward",
                "Move to Front", "Move to Back",
                )),
            ("Zoom", (
                "Zoom In", "Zoom Out", 0,
                )),
            ("Enabled Screens", itertools.chain(
                ["Cycle Enabled Screens", 0],
                ("Screens" + str(i) for i in range(3)))
                ),
            )
        for name, actions in menubaractions:
            # Add menu, if it's not already defined
            if name not in self.menus:
                menu = menubar.addMenu(name)
                self.menus[name] = menu
            else:
                menu = self.menus[name]

            for actionkey in actions:
                if not actionkey:
                    menu.addSeparator()
                elif actionkey.startswith("Menu:"):
                    # insert submenu
                    menutext = actionkey[5:]
                    if "&" in menutext:
                        menukey = "".join(menutext.split("&"))
                    else:
                        menukey = menutext
                    self.menus[menukey] = menu.addMenu(menutext)
                else:
                    self.actions[actionkey].setIconVisibleInMenu(False)
                    menu.addAction(self.actions[actionkey])

        # initialize toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(18, 18))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
            # disable right-click menu to show/hide toolbar
        self.addToolBar(self.toolbar)

        toolbaractions = (
            "Open ROM", "Load Sublevel", "Save Sublevel",
            "Edit Header", "Edit Level Entrances", "Edit Screen Exits", 0,
            "Toggle Palette", "Toggle 8x8", "Toggle 16x16", 0,
            "Refresh", "Zoom Button", 0,
            "Count Items", "Item Memory", 0,
            "Edit Messages", "Export Graphics", "Import Graphics",
            )
        for actionkey in toolbaractions:
            if not actionkey:
                self.toolbar.addSeparator()
            else:
                self.toolbar.addAction(self.actions[actionkey])

        # special zoom submenu handling
        for zoomlevel in self.zoomlevels:
            actionstr = str(zoomlevel) + "%"
            action = QAction(actionstr, actiongroups["Zoom"])
            action.triggered.connect(partial(self._setZoom, zoomlevel))
            action.setCheckable(True)
            action.setChecked(AdvSettings.visual_zoom == zoomlevel)
            self.actions["Zoom " + actionstr] = action
            self.menus["Zoom"].addAction(action)
        self.actions["Zoom 100%"].setShortcut("Ctrl+0")

        zoombutton = QToolButton()
        zoombutton.setIcon(QAdvyniaIcon("zoom.png"))
        zoombutton.setToolTip("Zoom")
        zoombutton.setMenu(self.menus["Zoom"])
        zoombutton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.toolbar.insertWidget(self.actions["Zoom Button"], zoombutton)
        self.toolbar.removeAction(self.actions["Zoom Button"])

        # special move action handling, since they're not in a menu
        for actionkey in ("Move Left", "Move Right", "Move Up", "Move Down"):
            self.addAction(self.actions[actionkey])

        # dynamic actions/menus
        self.updaterecentROMmenu()
        self.enableSelectionActions(False)

    def enableSelectionActions(self, enabled, objectsonly=None):
        if objectsonly is None:
            objectsonly = enabled
        for key in ("Cut", "Copy", "Delete"):
            self.actions[key].setEnabled(enabled)
        for key in ("Resize Selected Objects", "Change Object Order"):
            self.menus[key].setEnabled(objectsonly)

    # main window methods

    def closeEvent(self, event):
        "Save settings, including this window's position/size, on close."
        if not Adv3Sublevel.savecheck():
            event.ignore()
            return

        AdvSettings.window_SMA3Editor = (
            self.pos().x(), self.pos().y(),
            self.size().width(), self.size().height())
        AdvSettings._writecfg()

    def updatewindowtitle(self):
        self.windowtitle = [self.windowtitle[0], Adv3Attr.filename]
        if Adv3Attr.sublevel.ID is not None:
            self.windowtitle.append(
                "Sublevel " + format(Adv3Attr.sublevel.ID, "02X"))
        self.setWindowTitle(" - ".join(self.windowtitle))

    def updaterecentROMmenu(self):
        self.menus["Recent ROMs"].clear()
        self.actions["Recent ROMs"] = []
        self.menus["Recent ROMs"].setEnabled(bool(AdvSettings.ROM_recent))
        for i, filepath in enumerate(AdvSettings.ROM_recent):
            numstr = str(i+1)
            action = QAction("".join((
                numstr[:-1], "&", numstr[-1:], ": ", filepath)))
            action.triggered.connect(partial(AdvEditor.ROM.loadROM, filepath))
            self.actions["Recent ROMs"].append(action)
            self.menus["Recent ROMs"].addAction(action)

    zoomlevels = (25, 50, 100, 200, 300, 400, 600)

    def _setZoom(self, zoom):
        AdvSettings.visual_zoom = zoom
        self.sublevelview.resetTransform()
        self.sublevelview.scale(zoom/100, zoom/100)
        AdvWindow.statusbar.setActionText("".join((
            "Zoom: ", str(zoom), "%")))

    def _zoomin(self):
        for value in self.zoomlevels:
            if AdvSettings.visual_zoom < value:
                self._setZoom(value)
                return

    def _zoomout(self):
        for value in reversed(self.zoomlevels):
            if AdvSettings.visual_zoom > value:
                self._setZoom(value)
                return

    def _magnifyingglass(self):
        "Toggle whether disguised red coins are displayed red or yellow."
        AdvSettings.visual_redcoins = not AdvSettings.visual_redcoins
        Adv3Visual.palette.setRedCoinPalette(AdvSettings.showredcoins)
        if AdvSettings.showredcoins:
            AdvWindow.statusbar.setActionText("Enabled red coin palette.")
        else:
            AdvWindow.statusbar.setActionText("Disabled red coin palette.")
        # reload layer 1 palette
        self.setHeader(2, Adv3Attr.sublevel.header[2])
        # reload red coin sprites
        self.reloadSpriteIDs({0x65})

    # multi-window update methods

    def updatepatchlayouts(self):
        for widget in (self.viewer8x8, self.headereditor):
            widget.updatepatchlayout()

    def reloadSpriteIDs(self, spriteIDset):
        """Reload graphics of a specific set of sprite IDs, for all instances
        of QSMA3SpriteLayer."""
        for widget in (AdvWindow.sublevelscene, AdvWindow.sidebar):
            widget.spritelayer.reloadSpriteIDs(spriteIDset)

    def setHeader(self, *args):
        """Accepts a mapping or a single (index, new value) pair. Should be
        called when updating the currently loaded sublevel's header, to reload
        any editor graphics involving that header setting."""

        updateset = set()
        try:
            # is this a dictionary?
            args[0].keys()	
        except AttributeError:
            # this is a single key-value pair, not a dictionary
            key, value = args
            newvalues = {key:value}
        else:
            newvalues = args[0]

        for key in newvalues:
            Adv3Attr.sublevel.header[key] = newvalues[key]

            if key == 1:  # layer 1 tileset
                Adv3Visual.layergraphics.loadL1graphics(
                    Adv3Attr.filepath, newvalues[key])
                Adv3Visual.resetcache8_layers(region="Layer 1")
                Adv3Visual.resetcache8_layers(region="Animated")
                updateset |= {"Layer 1", "Layer 1 Tilemap", "8x8"}
            elif key == 3:  # layer 2 image
                Adv3Visual.layergraphics.loadL2graphics(
                    Adv3Attr.filepath, newvalues[key])
                Adv3Visual.resetcache8_layers(region="Layer 2")
                updateset |= {"Layer 1", "Layer 2", "8x8"}
            elif key == 5:  # layer 3 image
                Adv3Visual.layergraphics.loadL3graphics(
                    Adv3Attr.filepath, newvalues[key])
                Adv3Visual.resetcache8_layers(region="Layer 3")
                updateset |= {"Layer 3", "8x8", "Palette"}
            elif key == 0xA:  # graphics animation
                Adv3Visual.layergraphics.loadanimgraphics(
                    Adv3Attr.filepath, newvalues[key])
                Adv3Visual.resetcache8_layers()
                updateset |= {"Layer 1", "Layer 2", "Layer 3", "8x8"}
            elif key == 0x7 and not Adv3Attr.sublevelstripes:
                # sprite tileset, not overridden
                Adv3Visual.spritegraphics.loadstripes(
                    Adv3Attr.filepath, newvalues[key])
                updateset |= {"8x8", "Sprite Graphics"}

            elif key == 0:  # background color
                Adv3Visual.palette.loadBGpalette(
                    Adv3Attr.filepath, newvalues[key])
                updateset |= {"Palette", "Background Layer"}
            elif key == 2:  # layer 1 palette
                Adv3Visual.palette.loadL1palette(
                    Adv3Attr.filepath, newvalues[key])
                updateset |= {"Layer 1", "Palette", "8x8", "cache8_layers"}
            elif key == 4:  # layer 2 palette
                Adv3Visual.palette.loadL2palette(
                    Adv3Attr.filepath, newvalues[key])
                updateset |= {"Layer 1", "Layer 2", "Palette", "8x8",
                              "cache8_layers"}
            elif key == 6:  # layer 3 palette
                Adv3Visual.palette.loadL3palette(
                    Adv3Attr.filepath, newvalues[key])
                updateset |= {"Layer 1", "Layer 3", "Palette", "8x8",
                              "cache8_layers"}
            elif key == 8:  # sprite palette
                Adv3Visual.palette.loadspritepalette(
                    Adv3Attr.filepath, newvalues[key])
                updateset |= {"Palette", "8x8", "Sprite Graphics"}

            elif key == 0xE:  # item memory index
                updateset |= {"Middle Rings"}

        self.reload(updateset)

    def reload(self, updateset):
        "Reload one or more parts of the editor. Usually called from setHeader."

        if "All" in updateset:
            updateset = {
                "cache8_layers",
                "Layer 1", "Layer 1 Tilemap", "Layer 2", "Layer 3",
                "Background Layer", "Sprites", "Sprite Graphics",
                "Screen Exits",
                "Palette", "8x8",
                }
            AdvWindow.selection.clear()
            AdvWindow.statusbar.setHoverText()

        # update relevant widgets with graphics/palette changes
        if "cache8_layers" in updateset:
            Adv3Visual.resetcache8_layers()
        if "Layer 1" in updateset:
            Adv3Visual.resetcache16()
            if "Layer 1 Tilemap" in updateset:
                AdvWindow.sublevelscene.layer1.createTilemap(Adv3Attr.sublevel)
            AdvWindow.sublevelscene.layer1.updateLayerGraphics(forcereload=True)
            AdvWindow.selection.refreshSelectedObjects()
            AdvWindow.sidebar.reload(forcereload=True)
            self.viewer16x16.queueupdate()
        if "Objects" in updateset:
            AdvWindow.sublevelscene.updateobjects()
        if "Layer 2" in updateset:
            AdvWindow.sublevelscene.layer2.dispLayer()
        if "Layer 3" in updateset:
            AdvWindow.sublevelscene.layer3.dispLayer()
        if "Background Layer" in updateset:
            AdvWindow.sublevelscene.background.dispBGgradient()
        if "Sprites" in updateset:
            AdvWindow.sublevelscene.spritelayer.loadSprites(Adv3Attr.sublevel)
        if "Sprite Graphics" in updateset:
            if Adv3Attr.sublevelstripes:
                Adv3Visual.updatestripesfromsublevel()
            Adv3Visual.resetcache8_sprites()
            if "Sprites" not in updateset:
                AdvWindow.sublevelscene.spritelayer.reloadSpriteGraphics(
                    Adv3Attr.sublevel)
            AdvWindow.sidebar.reload(forcereload=True)
        if ("Middle Rings" in updateset and
                not ({"Sprites", "Sprite Graphics"} & updateset)):
            self.reloadSpriteIDs({0x4F})
        if "Screen Exits" in updateset:
            AdvWindow.sublevelscene.grid.dispScreenExits(
                Adv3Attr.sublevel.exits)
        if "Palette" in updateset:
            self.viewerpalette.updateDropdowns()
            self.viewerpalette.reloadPalette()
        if "8x8" in updateset:
            self.viewer8x8.queueupdate()
##        if "Byte Text" in updateset:
##            AdvWindow.statusbar.updateByteText()

##_nonqtglobals = []
##for name in tuple(globals()):
##    if name.startswith("_") or QtAdvFunc.isQtglobal(name):
##        continue
##    _nonqtglobals.append(name)
##print(_nonqtglobals)
