"""SMA3 Editor Main Window"""

# standard liberary imports
from functools import partial
import itertools
from collections import namedtuple
from collections.abc import Collection

# import from other files
import AdvMetadata, AdvEditor
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr, Adv3Sublevel, Adv3Visual
# Qt general
from AdvGUI import QtAdvFunc
from AdvGUI.GeneralQt import *
# Main window components
from AdvGUI.SublevelScene import QSMA3SublevelScene
from AdvGUI.InsertionSidebar import QInsertionSidebar
from AdvGUI.StatusBar import QMainEditorStatusBar
# Non-modal dialogs
from AdvGUI.PaletteViewer import QSMA3PaletteViewer
from AdvGUI.TileViewers import Q8x8TileViewer, Q16x16TileViewer
from AdvGUI.LayerViewer import QSMA3LayerViewer
# Modal dialogs
from AdvGUI.EntranceEditor import QDialogSMA3LevelEntrances, QDialogSMA3ScreenExits
from AdvGUI.HeaderEditor import QSMA3HeaderEditor
from AdvGUI.TextEditor import QSMA3TextEditor
from AdvGUI.Dialogs import *

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
            QtAdvFunc.protectedmoveresize(self, *AdvSettings.window_editor)
        except Exception:
            AdvSettings._resetsetting("window_editor")
            QtAdvFunc.protectedmoveresize(self, *AdvSettings.window_editor)

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
        if AdvSettings.window_editor_sidebarpos not in (1, 2):
            AdvSettings.window_editor_sidebarpos = 1
        self.addDockWidget(Qt.DockWidgetArea(AdvSettings.window_editor_sidebarpos),
                           AdvWindow.sidebar)

        # initialize status bar
        AdvWindow.statusbar = QMainEditorStatusBar()
        self.setStatusBar(AdvWindow.statusbar)

        # initialize dialogs
        self.viewerpalette = QSMA3PaletteViewer(self)
        self.viewer8x8 = Q8x8TileViewer(self)
        self.viewer16x16 = Q16x16TileViewer(self)
        self.viewerlayer = QSMA3LayerViewer(self)
        self.headereditor = QSMA3HeaderEditor(self)
        AdvWindow.entranceeditor = QDialogSMA3LevelEntrances(self)
        AdvWindow.texteditor = QSMA3TextEditor(self)

        # initialize toolbar/menu and actions
        # (actions frequently reference other objects, so this should be last)
        self.initActions()

        if AdvMetadata.printtime: print("Total editor init:",
              QtAdvFunc.timerend(timer), "ms")  # debug

    def initActions(self):
        """Initialize the main window's actions, and the toolbar/menu bar
        containing them."""

        AData = namedtuple("AData",
            "text, shortcut, triggered, icon, checked, tooltip",
            defaults=("", None, None, None, None, None))

        actiondata = {
            #key: text, tooltip, shortcut, triggered, icon, checked
            "Exit": AData("E&xit", "Ctrl+Q", QApplication.quit),
            "Open ROM": AData(
                "&Open ROM...", "Ctrl+O", AdvEditor.ROM.opendialog),
            "Load Sublevel": AData(
                "&Load Sublevel...", "Ctrl+D", QDialogLoadSublevel(self).open),
            "Save Sublevel": AData(
                "&Save Sublevel to ROM", "Ctrl+S",
                Adv3Sublevel.savesublevel_action),
            "Save Sublevel As": AData(
                "Save Sublevel to ROM &As...", "Ctrl+Shift+S",
                QDialogSaveSublevelAs(self).open),
            "Import Sublevel": AData(
                "&Import A3L File...", "Ctrl+Shift+I",
                AdvEditor.Export.importA3L_action),
            "Import Multiple": AData(
                "Import Multiple A3Ls...", None,
                AdvEditor.Export.importmultiple),
            "Export Sublevel": AData(
                "&Export Sublevel to A3L...", "Ctrl+Shift+E",
                AdvEditor.Export.exportsublevel_action),
            "Export YLT": AData(
                "&Export Sublevel to YLT (SNES)...", None,
                AdvEditor.Export.export_ylt),
            "Export YET": AData(
                "&Export Entrances to YET (SNES)...", None,
                AdvEditor.Export.export_yet),
            "Export All": AData(
                "Export All Data to A3Ls...", None,
                AdvEditor.Export.exportall_action),
            "Export SNES": AData(
                "Extract SNES YI Data...", None,
                AdvEditor.Export.exportSNESdata_action),
            "Info": AData(
                "Current ROM Info", "Ctrl+I", QDialogROMInfo(self).open),
            "Undo": AData(
                "&Undo", "Ctrl+Z", AdvWindow.undohistory.undo),
            "Redo": AData(
                "&Redo", ("Ctrl+Y", "Ctrl+Shift+Z"), AdvWindow.undohistory.redo),
            "Cut": AData("Cu&t", "Ctrl+X", AdvWindow.sublevelscene.cut),
            "Copy": AData("&Copy", "Ctrl+C", AdvWindow.sublevelscene.copy),
            "Paste": AData("&Paste", "Ctrl+V", AdvWindow.sublevelscene.paste),
            "Select All": AData(
                "Select &All", "Ctrl+A", AdvWindow.selection.selectall),
            "Insert": AData(
                "&Insert Object/Sprite", ("", "Insert"),
                AdvWindow.sublevelscene.quickinsertfromsidebar),
            "Delete": AData(
                "&Delete Objects/Sprites", ("Delete", "Backspace"),
                AdvWindow.selection.deleteitems),
            "Move Left": AData(
                "Move &Left", "Ctrl+Left",
                partial(AdvWindow.selection.moveitems, -1, 0)),
            "Move Right": AData(
                "Move &Right", "Ctrl+Right",
                partial(AdvWindow.selection.moveitems, 1, 0)),
            "Move Up": AData(
                "Move &Up", "Ctrl+Up",
                partial(AdvWindow.selection.moveitems, 0, -1)),
            "Move Down": AData(
                "Move &Down", "Ctrl+Down",
                partial(AdvWindow.selection.moveitems, 0, 1)),
            "Decrease Width": AData(
                "Decrease Width", "Shift+Left",
                partial(AdvWindow.selection.resizeobjects, -1, 0)),
            "Increase Width": AData(
                "Increase Width", "Shift+Right",
                partial(AdvWindow.selection.resizeobjects, 1, 0)),
            "Decrease Height": AData(
                "Decrease Height", "Shift+Up",
                partial(AdvWindow.selection.resizeobjects, 0, -1)),
            "Increase Height": AData(
                "Increase Height", "Shift+Down",
                partial(AdvWindow.selection.resizeobjects, 0, 1)),
            "Move Forward": AData(
                "Move Forward", "]",
                partial(AdvWindow.selection.moveobjectorder, 1)),
            "Move Backward": AData(
                "Move Backward", "[",
                partial(AdvWindow.selection.moveobjectorder, -1)),
            "Move to Front": AData(
                "Move to Front", "Ctrl+]",
                partial(AdvWindow.selection.moveobjectorder, 2)),
            "Move to Back": AData(
                "Move to Back", "Ctrl+[",
                partial(AdvWindow.selection.moveobjectorder, -2)),
            "Clear Sublevel": AData(
                "&Clear Sublevel...", ("Ctrl+Delete", "Ctrl+Backspace"),
                QDialogClearSublevel(self).open),
            "Filter": AData("&Filter Sidebar...", "Ctrl+F"),
            "Quick Filter": AData("&Quick Filter", "Ctrl+Shift+F"),
            "Reset Filter": AData("Reset Filter", "Ctrl+Alt+F"),
            "Edit Header": AData(
                "Edit Sublevel &Header...", "Ctrl+H",
                self.headereditor.open, icon="yoshi.png"),
            "Edit Screen Exits": AData(
                "Edit &Screen Exits...", "Ctrl+E",
                QDialogSMA3ScreenExits(self).open, icon="door16.png"),
            "Edit Level Entrances": AData(
                "Edit &Level Entrances...", "Ctrl+L",
                AdvWindow.entranceeditor.open, icon="egg.png"),
            "Edit Messages": AData(
                "Edit &Messages...", "Ctrl+M",
                AdvWindow.texteditor.open, icon="messageblock.png"),
            "Edit Internal Name": AData(
                "Edit Internal ROM &Name...", None,
                QDialogInternalName(self).open),
            "YI Title": AData(
                "View YI Title Screen Sprites...", None,
                QYITitleDialog(self).open),
            "Palette Viewer": AData(
                "&Palette Viewer", "Ctrl+P",
                QtAdvFunc.createdialogtogglefunc(self.viewerpalette),
                icon="palette.png", checked=False),
            "8x8 Viewer": AData(
                "&8x8 Tile Viewer", "Ctrl+8",
                QtAdvFunc.createdialogtogglefunc(self.viewer8x8),
                icon="8x8.png", checked=False),
            "16x16 Viewer": AData(
                "1&6x16 Tile Viewer", "Ctrl+6",
                QtAdvFunc.createdialogtogglefunc(self.viewer16x16),
                icon="16x16.png", checked=False),
            "Layer Viewer": AData(
                "&Layer 2/3 Viewer", "Ctrl+2",
                QtAdvFunc.createdialogtogglefunc(self.viewerlayer),
                icon="layerviewer.png", checked=False),
            "Refresh": AData(
                "&Refresh", "Ctrl+R",
                AdvWindow.sublevelscene.refresh, icon="refresh.png",
                tooltip="""Refresh
Refresh the current layer 1 tilemap, to reroll
RNG-dependent objects."""),
            "Zoom In": AData("Zoom &In", ("Ctrl++", "Ctrl+="), self._zoomin),
            "Zoom Out": AData("Zoom &Out", "Ctrl+-", self._zoomout),
            "Zoom Button": AData("Zoom"),
            "Show Layer 0": AData(
                "Layer &0 (Layer 1 FG)", "0",
                partial(self._layer1action, True), checked=False),
            "Show Layer 1": AData(
                "Layer &1 (Objects)", "1",
                partial(self._layer1action, False), checked=True),
            "Show Layer 2": AData(
                "Layer &2", "2",
                QtAdvFunc.createtogglefunc(AdvWindow.sublevelscene.layer2),
                checked=True),
            "Show Layer 3": AData(
                "Layer &3", "3",
                QtAdvFunc.createtogglefunc(AdvWindow.sublevelscene.layer3),
                checked=True),
            "Show Sprites": AData(
                "&Sprites", "4",
                QtAdvFunc.createtogglefunc(AdvWindow.sublevelscene.spritelayer),
                checked=True),
            "Show Level Entrances": AData(
                "&Level Entrances", "5",
                QtAdvFunc.createtogglefunc(AdvWindow.sublevelscene.entrancelayer),
                checked=True),
            "Show Grid": AData(
                "&Grid", "G",
                QtAdvFunc.createtogglefunc(AdvWindow.sublevelscene.grid),
                icon="grid.png", checked=True, tooltip="Show/Hide Screen Grid"),
            "Show Item Contents": AData(
                "&Item Contents", "I",
                None, checked=AdvSettings.visual_itemcontents),
            "Cycle Enabled Screens": AData(
                "&Quick Swap", "U",
                AdvWindow.sublevelscene.layer1.cycleDimScreens),
            "Show Red Coins": AData(
                "Hidden &Red Coins", None,
                self._magnifyingglass, checked=AdvSettings.visual_redcoins),
            "Screenshot": AData(
                "Save Sublevel &Screenshot", "F12",
                AdvWindow.sublevelscene.screenshot),
            "Window Screenshot": AData(
                "Save &Window Screenshot", "Shift+F12",
                QDialogBase.screenshotwindow),
            "Count Items": AData(
                "&Count Red Coins/Flowers", "F10",
                Adv3Sublevel.countitems, icon="redcoin.png"),
            "Item Memory": AData(
                "Check &Item Memory", "F11",
                Adv3Sublevel.itemmemorycheck, icon="cloud.png"),
            "Export Graphics": AData(
                "&Export Graphics/Tilemaps", None,
                AdvEditor.Export.exportgraphics_action,
                icon="graphicsexport.png", tooltip="""Export Graphics/Tilemaps
Export all graphics and compressed tilemaps."""),
            "Import Graphics": AData(
                "&Import Graphics/Tilemaps", None,
                AdvEditor.Export.importgraphics_action,
                icon="graphicsimport.png"),
            "Convert Graphics": AData(
                "Convert SNES to GBA Graphics...", None,
                QDialogGraphicsConvert(self).open),
            "About": AData("&About Advynia", "F1", QDialogAbout(self).open),
            }

        actiongroups = {}
        for key in ("Screens", "Zoom"):
            actiongroups[key] = QActionGroup(self)

        self.actions = {}

        for key, data in actiondata.items():
            args = []

            if data.icon: args.append(QAdvyniaIcon(data.icon))
            if data.text: args.append(data.text)
            action = QAction(*args)
            if data.tooltip: action.setToolTip(data.tooltip)
            if data.shortcut:
                try:
                    action.setShortcut(data.shortcut)
                except TypeError:
                    action.setShortcuts(data.shortcut)
            if data.triggered:
                action.triggered.connect(data.triggered)
            else:
                action.setDisabled(True)
            if data.checked is not None:
                action.setCheckable(True)
                action.setChecked(data.checked)
            self.actions[key] = action

        # extra action init, not in main tuples

        self.actions["Open ROM"].setIconText("Open")
        self.actions["Load Sublevel"].setIconText("Load")
        self.actions["Save Sublevel"].setIconText("Save")

        for actionkey in ("Undo", "Redo", "Paste"):
            self.actions[actionkey].setDisabled(True)

        for actionkey in ("Undo", "Redo",
                "Palette Viewer", "8x8 Viewer", "16x16 Viewer", "Layer Viewer"):
            self.actions[actionkey].setShortcutContext(
                Qt.ShortcutContext.ApplicationShortcut)

        if not (AdvSettings.import_includegraphics or
                AdvSettings.import_includetilemaps):
            self.actions["Import Graphics"].setDisabled(True)

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
            ("&File", [
                "Open ROM", "Menu:&Recent ROMs",
                "Load Sublevel", "Save Sublevel", "Save Sublevel As", 0,
                "Import Sublevel", "Import Multiple", "Export Sublevel"] +
                (["Export YLT", "Export YET"]
                 if AdvSettings.export_yileveltool_enable else []) +
                ["Export All", "Export SNES", 0,
                "Info", 0,
                "Exit"]),
            ("&Edit", (
                "Undo", "Redo", 0,
                "Cut", "Copy", "Paste", "Insert", "Delete",
                "Menu:&Resize Selected Objects",
                "Menu:Change Object &Order", "Select All", "Clear Sublevel", 0,
                "Filter", "Quick Filter", "Reset Filter", 0,
                "Edit Header", "Edit Screen Exits", 0,
                "Edit Level Entrances", "Edit Messages", "Edit Internal Name",
                )),
            ("&View", (
                "Palette Viewer", "8x8 Viewer", "16x16 Viewer", "Layer Viewer",
                0,
                "Refresh", "Menu:&Zoom", 0,
                "Show Layer 1", "Show Layer 0", "Show Layer 2", "Show Layer 3",
                "Show Sprites", "Show Level Entrances", "Show Grid",
                "Menu:&Enabled Screens",
                "Show Item Contents", "Show Red Coins",
                )),
            ("&Misc", (
                "Screenshot", "Window Screenshot", 0,
                "Count Items", "Item Memory", 0,
                "Export Graphics", "Import Graphics", "Convert Graphics", 0,
                "YI Title",
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
            "Palette Viewer", "8x8 Viewer", "16x16 Viewer", "Layer Viewer", 0,
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
            actionstr = f"{zoomlevel}%"
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

        AdvSettings.window_editor = (
            self.pos().x(), self.pos().y(),
            self.size().width(), self.size().height())
        AdvSettings._writecfg()

    def updatewindowtitle(self):
        self.windowtitle = [self.windowtitle[0], Adv3Attr.filename]
        if Adv3Attr.sublevel.ID is not None:
            self.windowtitle.append(f"Sublevel {Adv3Attr.sublevel.ID:02X}")
        self.setWindowTitle(" - ".join(self.windowtitle))

    def updaterecentROMmenu(self):
        self.menus["Recent ROMs"].clear()
        self.actions["Recent ROMs"] = []
        self.menus["Recent ROMs"].setEnabled(bool(AdvSettings.ROM_recent))
        for i, filepath in enumerate(AdvSettings.ROM_recent):
            numstr = str(i+1)
            action = QAction(f"{numstr[:-1]}&{numstr[-1:]}: {filepath}")
            action.triggered.connect(partial(AdvEditor.ROM.loadROM, filepath))
            self.actions["Recent ROMs"].append(action)
            self.menus["Recent ROMs"].addAction(action)

    zoomlevels = (25, 50, 100, 200, 300, 400, 600)

    def _setZoom(self, zoom):
        AdvSettings.visual_zoom = zoom
        self.sublevelview.resetTransform()
        self.sublevelview.scale(zoom/100, zoom/100)
        AdvWindow.statusbar.setActionText(f"Zoom: {zoom}%")

    def _zoomin(self):
        for value in self.zoomlevels:
            if AdvSettings.visual_zoom < value:
                self.actions[f"Zoom {value}%"].activate(
                    QAction.ActionEvent.Trigger)
                return

    def _zoomout(self):
        for value in reversed(self.zoomlevels):
            if AdvSettings.visual_zoom > value:
                self.actions[f"Zoom {value}%"].activate(
                    QAction.ActionEvent.Trigger)
                return

    def _layer1action(self, layer0newvalue):
        layer1 = AdvWindow.sublevelscene.layer1
        if Adv3Visual.layer0only is not layer0newvalue:
            # swap layer 0/1 tilemaps
            self.actions["Show Layer 0"].setChecked(layer0newvalue)
            self.actions["Show Layer 1"].setChecked(not layer0newvalue)
            Adv3Visual.layer0only = layer0newvalue
            self.reload({"Layer 1"})
            if not layer1.isVisible():
                layer1.setVisible(True)
            AdvWindow.statusbar.setActionText("Displaying layer {0}.".format(
                0 if layer0newvalue else 1))
        else:
            # toggle currently active layer
            layer1.setVisible(not layer1.isVisible())

    def _magnifyingglass(self):
        "Toggle whether disguised red coins are displayed red or yellow."
        AdvSettings.visual_redcoins = not AdvSettings.visual_redcoins
        Adv3Visual.palette.setRedCoinPalette(AdvSettings.visual_redcoins)
        AdvWindow.statusbar.setActionText("{0} red coins.".format(
            "Showing" if AdvSettings.visual_redcoins else "Hiding"))
        # reload layer 1 palette
        self.setHeader({2: Adv3Attr.sublevel.header[2]})
        # reload red coin sprites
        self.reloadSpriteIDs({0x65})

    # multi-window update methods

    def updatepatchlayouts(self):
        for widget in (self.viewer8x8, self.headereditor):
            widget.updatepatchlayout()

    def reloadSpriteIDs(self, spriteIDset):
        """Reload graphics of a specific set of sprite IDs, for all instances
        of QSMA3SpriteLayer."""
        Adv3Visual.resetcachesprite(spriteIDset)
        for widget in (AdvWindow.sublevelscene, AdvWindow.sidebar):
            widget.spritelayer.reloadSpriteIDs(spriteIDset)

    def setHeader(self, newvalues):
        """Accepts a mapping or a single (index, new value) pair. Should be
        called when updating the currently loaded sublevel's header, to reload
        any editor graphics involving that header setting."""

        updateset = set()

        for key, value in newvalues.items():
            Adv3Attr.sublevel.header[key] = value

            match key:
                # graphics settings
                case 0x1:  # layer 1 tileset
                    Adv3Visual.layergraphics.loadL1graphics(
                        Adv3Attr.filepath, newvalues[key])
                    Adv3Visual.resetcache8_layers(region="Layer 1")
                    Adv3Visual.resetcache8_layers(region="Animated")
                    updateset |= {"Layer 1", "Layer 1 Tilemap", "8x8"}
                case 0x3:  # layer 2 image
                    Adv3Visual.layergraphics.loadL2graphics(
                        Adv3Attr.filepath, newvalues[key])
                    Adv3Visual.resetcache8_layers(region="Layer 2")
                    updateset |= {"Layer 1", "Layer 2", "8x8"}
                case 0x5:  # layer 3 image
                    Adv3Visual.layergraphics.loadL3graphics(
                        Adv3Attr.filepath, newvalues[key])
                    Adv3Visual.resetcache8_layers(region="Layer 3")
                    Adv3Visual.palette.loadL3imagepal(
                        Adv3Attr.filepath, newvalues[key])
                    updateset |= {"Layer 3", "8x8", "Palette"}
                case 0xA:  # graphics animation
                    Adv3Visual.layergraphics.loadanimgraphics(
                        Adv3Attr.filepath, newvalues[key])
                    Adv3Visual.resetcache8_layers()
                    updateset |= {"Layer 1", "Layer 2", "Layer 3", "8x8"}
                case 0x7:
                    if not Adv3Attr.sublevelstripes:
                        # sprite tileset, not overridden
                        Adv3Visual.spritegraphics.loadstripes(
                            Adv3Attr.filepath, newvalues[key])
                        Adv3Visual.updatestripesfromsublevel()
                        updateset |= {"8x8", "Sprite Graphics"}

                # palette settings
                case 0x0:  # background color
                    Adv3Visual.palette.loadBGpalette(
                        Adv3Attr.filepath, newvalues[key])
                    updateset |= {"Palette", "Background Layer"}
                case 0x2:  # layer 1 palette
                    Adv3Visual.palette.loadL1palette(
                        Adv3Attr.filepath, newvalues[key])
                    updateset |= {"Layer 1", "Palette", "8x8", "cache8_layers"}
                case 0x4:  # layer 2 palette
                    Adv3Visual.palette.loadL2palette(
                        Adv3Attr.filepath, newvalues[key])
                    updateset |= {"Layer 1", "Layer 2", "Palette", "8x8",
                                  "cache8_layers"}
                case 0x6:  # layer 3 palette
                    Adv3Visual.palette.loadL3palette(
                        Adv3Attr.filepath, newvalues[key])
                    updateset |= {"Layer 1", "Layer 3", "Palette", "8x8",
                                  "cache8_layers"}
                case 0x8:  # sprite palette
                    Adv3Visual.palette.loadspritepalette(
                        Adv3Attr.filepath, newvalues[key])
                    updateset |= {"Palette", "8x8", "Sprite Graphics"}
                case 0xB:  # palette animation
                    Adv3Visual.palette.loadanimpalette(
                        Adv3Attr.filepath, newvalues[key])
                    updateset |= {"Palette", "8x8",
                                  "Layer 1", "Layer 2", "Layer 3",
                                  "cache8_layers", "Sprite Graphics"}

                # other settings
                case 0xE:  # item memory index
                    updateset |= {"Middle Rings"}

        self.reload(updateset)

    def reload(self, updateset: Collection[str]):
        "Reload one or more parts of the editor. Usually called from setHeader."

        if isinstance(updateset, str):
            # coding error mitigation, since strings are in themselves
            raise TypeError(
                "QSMA3Editor.reload takes a collection of strings, not a single string.")

        if "All" in updateset:
            updateset = {
                "cache8_layers",
                "Layer 1", "Layer 1 Tilemap", "Layer 2", "Layer 3",
                "Background Layer", "Sprites", "Sprite Graphics",
                "Entrances", "Screen Exits",
                "Palette", "8x8",
                }
            AdvWindow.selection.clear()
            AdvWindow.statusbar.setHoverText()
        if "All Graphics" in updateset:
            Adv3Visual.loadgraphics(Adv3Attr.sublevel)
            updateset |= {"Layer 1", "Layer 2", "Layer 3", "Sprites", "8x8"}

        spriteIDs_to_reload = set()

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
            if self.viewerlayer.layer == 2: self.viewerlayer.queueupdate()
            spriteIDs_to_reload |= SMA3.SpriteMetadata.uselayer[2]
        if "Layer 3" in updateset:
            AdvWindow.sublevelscene.layer3.dispLayer()
            if self.viewerlayer.layer == 3: self.viewerlayer.queueupdate()
            spriteIDs_to_reload |= SMA3.SpriteMetadata.uselayer[3]
        if "Background Layer" in updateset:
            AdvWindow.sublevelscene.background.dispBGgradient()
        if "Sprite Graphics" in updateset:
            if Adv3Attr.sublevelstripes:
                Adv3Visual.updatestripesfromsublevel()
            Adv3Visual.resetcache8_sprites()
            Adv3Visual.resetcachesprite()
            if "Sprites" not in updateset:
                AdvWindow.sublevelscene.spritelayer.reloadSpriteGraphics(
                    Adv3Attr.sublevel)
            AdvWindow.sidebar.reload(forcereload=True)
        if "Middle Rings" in updateset and not "Sprites" in updateset:
            spriteIDs_to_reload.add(0x4F)
        if "Sprites" in updateset:
            AdvWindow.sublevelscene.spritelayer.loadSprites(Adv3Attr.sublevel)
        if "Entrances" in updateset:
            AdvWindow.sublevelscene.entrancelayer.loadEntrances(
                itertools.chain(*(Adv3Attr.sublevelentr[key][Adv3Attr.sublevel.ID] 
                                  for key in Adv3Attr.sublevelentr)))
        if "Screen Exits" in updateset:
            AdvWindow.sublevelscene.grid.dispScreenExits(
                Adv3Attr.sublevel.exits)
        if "Palette" in updateset:
            self.viewerpalette.runqueuedupdate()
        if "8x8" in updateset:
            self.viewer8x8.queueupdate()
        if "Byte Text" in updateset:
            AdvWindow.statusbar.updateByteText()

        if spriteIDs_to_reload and "Sprite Graphics" not in updateset:
            self.reloadSpriteIDs(spriteIDs_to_reload)
