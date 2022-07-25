# standard library imports
import copy, math, itertools, os, sys, zlib
from collections import defaultdict
from traceback import format_exc

# import from other files
import AdvFile, Adv3Save, Adv3Patch
from AdvGame import *
from AdvGUI import *

# globals
import AdvMetadata, AdvSettings, Adv3Attr, Adv3Visual

# Windows-specific: give unique taskbar icon
try:
    from ctypes import windll
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        AdvMetadata.appnamefull)
except ImportError:
    pass

# App class

class QAdvynia(QApplication):
    def __init__(self, *args):
        super().__init__(*args)

        editor = QSMA3Editor()

        # quick load for debug, until storing the most recent ROM is implemented
        quickpath = os.path.join(AdvMetadata.appdir, "sma3.gba")
        if os.path.exists("sma3.gba"):
            editor.loadROM("sma3.gba")
        elif os.path.exists(quickpath):
            editor.loadROM(quickpath)

        # prompt for ROM on open
        while not Adv3Attr.filepath:
            confirm = editor.openROMDialog()
            if not confirm:
                sys.exit()

        editor.show()

# Main editor window

class QSMA3Editor(QMainWindow):
    """Main GUI window."""
    def __init__(self):
        timer = timerstart()  # debug

        super().__init__()

        AdvSettings.editor = self

        self.windowtitle = [AdvMetadata.appnamefull]
        self.setWindowTitle(" - ".join(self.windowtitle))
        self.setWindowIcon(QAdvyniaIcon("Advynia3.png"))

        # this should be loaded from a settings file eventually
        self.move(64, 64)
        self.resize(0x400, 0x280)

        # initialize central sublevel scene
        self.sublevelscene = QSMA3SublevelScene()
        self.sublevelview = QGraphicsView(self.sublevelscene)
        self.sublevelview.scale(AdvSettings.zoom/100, AdvSettings.zoom/100)
        self.setCentralWidget(self.sublevelview)

        # start sublevel view in lower-left corner
        horizscroll = self.sublevelview.horizontalScrollBar()
        horizscroll.setValue(horizscroll.minimum())
        vertscroll = self.sublevelview.verticalScrollBar()
        vertscroll.setValue(vertscroll.maximum())

        # initialize sidebar
        self.sidebar = QInsertionSidebar(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)

        # initialize status bar
        self.statusbar = QMainEditorStatusBar()
        self.setStatusBar(self.statusbar)

        # initialize dialogs
        self.viewerpalette = QSMA3PaletteViewer(self)
        self.viewer8x8 = Q8x8TileViewer(self)
        self.viewer16x16 = Q16x16TileViewer(self)
        self.headereditor = QSMA3HeaderEditor(self)

        # initialize toolbar/menu and actions
        # (actions frequently reference other objects, so this should be last)
        self.initActions()

        if AdvMetadata.printtime: print("Total editor init:",
              timerend(timer), "ms")  # debug

    @staticmethod
    def _createtogglefunc(widget):
        return lambda : widget.setVisible(not widget.isVisible())

    @staticmethod
    def _createdialogtogglefunc(dialog):
        def _togglefunc(checked):
            if checked:
                dialog.show()
            else:
                dialog.done(1)
        return _togglefunc

    def initActions(self):
        """Initialize the main window's actions, and the toolbar/menu bar
        containing them."""

        actiondata = {
            #key: text, tooltip, shortcut, triggered, icon, checked
            "Exit":("E&xit", None, "Ctrl+Q", QApplication.quit, None, None),
            "Open ROM":("&Open ROM...", "Open ROM", "Ctrl+O",
                        self.openROMDialog, None, None),
            "Load Sublevel":("&Load Sublevel...", "Load Sublevel", "Ctrl+D",
                             QDialogLoadSublevel(self).open, None, None),
            "Save Sublevel":("&Save Sublevel to ROM", "Save Sublevel", "Ctrl+S",
                             self.saveSublevelAction, None, None),
            "Save Sublevel As":(
                "Save Sublevel to ROM &As...", None, "Ctrl+Shift+S",
                QDialogSaveSublevelAs(self).open, None, None),
            "Import Sublevel":(
                "&Import Sublevel from File...", None, "Ctrl+Shift+I",
                self.importSublevel, None, None),
            "Export Sublevel":(
                "&Export Sublevel to File...", None, "Ctrl+Shift+E",
                self.exportSublevel, None, None),
            "Export All Sublevels":(
                "Export All Sublevels...", None, None,
                self.exportAllSublevels, None, None),
            "Export SNES Sublevels":(
                "Extract Sublevels from SNES...", None, None,
                self.exportSNESSublevels, None, None),
            "Info":("Current ROM Info", None, "Ctrl+I",
                    QDialogROMInfo(self).open, None, None),
            "Undo":("&Undo", None, "Ctrl+Z", None, None, None),
            "Redo":("&Redo", None, ("Ctrl+Y", "Ctrl+Shift+Z"), None, None, None),
            "Cut":("Cu&t", None, "Ctrl+X", None, None, None),
            "Copy":("&Copy", None, "Ctrl+C", None, None, None),
            "Paste":("&Paste", None, "Ctrl+V", None, None, None),
            "Select All":("Select &All", None, "Ctrl+A",
                          self.sublevelscene.selection.selectall, None, None),
            "Insert":("&Insert Object/Sprite", None, ("", "Insert"),
                      self.sublevelscene.quickinsertfromsidebar, None, None),
            "Delete":("&Delete Objects/Sprites", None, ("Delete", "Backspace"),
                      self.sublevelscene.deleteselection, None, None),
            "Move Left":("Move &Left", None, "Ctrl+Left",
                self.sublevelscene.moveselectionleft, None, None),
            "Move Right":("Move &Right", None, "Ctrl+Right",
                self.sublevelscene.moveselectionright, None, None),
            "Move Up":("Move &Up", None, "Ctrl+Up",
                self.sublevelscene.moveselectionup, None, None),
            "Move Down":("Move &Down", None, "Ctrl+Down",
                self.sublevelscene.moveselectiondown, None, None),
            "Decrease Width":("Decrease Width", None, "Shift+Left",
                self.sublevelscene.decreaseselectionwidth, None, None),
            "Increase Width":("Increase Width", None, "Shift+Right",
                self.sublevelscene.increaseselectionwidth, None, None),
            "Decrease Height":("Decrease Height", None, "Shift+Up",
                self.sublevelscene.decreaseselectionheight, None, None),
            "Increase Height":("Increase Height", None, "Shift+Down",
                self.sublevelscene.increaseselectionheight, None, None),
            "Move Forward":("Move Forward", None, "]",
                self.sublevelscene.moveselectionforward, None, None),
            "Move Backward":("Move Backward", None, "[",
                self.sublevelscene.moveselectionbackward, None, None),
            "Move to Front":("Move to Front", None, "Ctrl+]",
                self.sublevelscene.moveselectiontofront, None, None),
            "Move to Back":("Move to Back", None, "Ctrl+[",
                self.sublevelscene.moveselectiontoback, None, None),
            "Clear Sublevel":("&Clear Sublevel...", None,
                              ("Ctrl+Delete", "Ctrl+Backspace"),
                              QDialogClearSublevel(self).open, None, None),
            "Edit Header":(
                "Edit Sublevel &Header...", "Edit Sublevel Header", "Ctrl+H",
                self.headereditor.open, "yoshi.png", None),
            "Edit Screen Exits":(
                "Edit &Screen Exits...", "Edit Screen Exits", "Ctrl+E",
                QDialogSMA3ScreenExits(self).open, "door16.png", None),
            "Edit Level Entrances":(
                "Edit &Level Entrances...", "Edit Level Entrances", "Ctrl+L",
                QDialogSMA3LevelEntrances(self).open, "egg.png", None),
            "Edit Messages":("Edit &Messages...", None, "Ctrl+M",
                             None, "messageblock.png",
##                             QSMA3MessageEditor(self).open, "messageblock.png",
                             None),
            "Edit Internal Name":("Edit Internal ROM Name...", None, None,
                                  QDialogInternalName(self).open, None, None),
            "Toggle Palette":("&Palette Viewer", None, "Ctrl+P",
                             self._createdialogtogglefunc(self.viewerpalette),
                              "palette.png", False),
            "Toggle 8x8":("&8x8 Tile Viewer", None, "Ctrl+8",
                          self._createdialogtogglefunc(self.viewer8x8),
                          "8x8.png", False),
            "Toggle 16x16":("1&6x16 Tile Viewer", None, "Ctrl+6",
                          self._createdialogtogglefunc(self.viewer16x16),
                          "16x16.png", False),
            "Refresh":("&Refresh", "Refresh\n"
                       "Refresh the current layer 1 tilemap, to reroll\n"
                       "RNG-dependent objects.", "Ctrl+R",
                       self.sublevelscene.refresh, "refresh.png", None),
            "Zoom In":("Zoom In", None, ("Ctrl++", "Ctrl+="),
                       self._zoomin, None, None),
            "Zoom Out":("Zoom Out", None, "Ctrl+-", self._zoomout, None, None),
            "Zoom Button":("Zoom", None, None, None, None, None),
            "Show Layer 1":("Layer &1", None, "1",
                self._createtogglefunc(self.sublevelscene.layer1), None, True),
            "Show Layer 2":("Layer &2", None, "2",
                self._createtogglefunc(self.sublevelscene.layer2), None, True),
            "Show Layer 3":("Layer &3", None, "3",
                self._createtogglefunc(self.sublevelscene.layer3), None, True),
            "Show Sprites":("&Sprites", None, "4",
                self._createtogglefunc(self.sublevelscene.spritelayer),
                            None, True),
            "Show Grid":("&Grid", "Show/Hide Screen Grid", "G",
                self._createtogglefunc(self.sublevelscene.grid),
                         "grid.png", True),
            "Show Dim Screens":("&Unused Screens", None, "U",
                self.sublevelscene.layer1.setDimScreens, None, True),
            "Show Red Coins":("&Red Coin Palette", None, None,
                              self._magnifyingglass, None, True),
            "Screenshot":("&Screenshot", None, "F12",
                          self.sublevelscene.screenshot, None, None),
            "Count Items":("&Count Red Coins/Flowers", None, "F10",
                           self.countitems, "redcoin.png", None),
            "Item Memory":("Check &Item Memory", None, "F11",
                           self.itemmemorycheck, "cloud.png", None),
            "Export Graphics":("&Export Graphics/Tilemaps",
                               "Export Graphics/Tilemaps\n"
                               "Export all graphics and compressed tilemaps.",
                               None, self.exportgraphics, "graphicsexport.png",
                               None),
            "Import Graphics":("&Import Graphics/Tilemaps", None, None,
                               None, "graphicsimport.png", None),
            "About":("&About Advynia", None, "F1",
                     QDialogAbout(self).open, None, None),
            }

        self.actions = {}

        for key, (text, tooltip, shortcut, triggered, icon, checked) in\
                actiondata.items():
            args = []
            if icon: args.append(QAdvyniaIcon(icon))
            if text: args.append(text)
            self.actions[key] = QAction(*args)
            if tooltip: self.actions[key].setToolTip(tooltip)
            if shortcut:
                try:
                    self.actions[key].setShortcut(shortcut)
                except TypeError:
                    self.actions[key].setShortcuts(shortcut)
            if triggered:
                self.actions[key].triggered.connect(triggered)
            else:
                self.actions[key].setDisabled(True)
            if checked is not None:
                self.actions[key].setCheckable(True)
                self.actions[key].setChecked(checked)

        self.actions["Open ROM"].setIconText("Open")
        self.actions["Load Sublevel"].setIconText("Load")
        self.actions["Save Sublevel"].setIconText("Save")

        # initialize menu bar
        menubar = self.menuBar()
        menus = {}
        menubaractions = (
            # main menus
            ("&File", (
                "Open ROM", "Load Sublevel", "Save Sublevel",
                "Save Sublevel As", 0,
                "Import Sublevel", "Export Sublevel", "Export All Sublevels",
                "Export SNES Sublevels", 0,
                "Info", 0,
                "Exit")),
            ("&Edit", (
                "Undo", "Redo", 0,
                "Cut", "Copy", "Paste", "Insert", "Delete", 
                "Menu:&Resize Selected Objects",
                "Menu:Change Object &Order", "Select All", "Clear Sublevel", 0,
                "Edit Header", "Edit Screen Exits", 0,
                "Edit Level Entrances", "Edit Messages", "Edit Internal Name",
                )),
            ("&View", (
                "Toggle Palette", "Toggle 8x8", "Toggle 16x16", 0,
                "Refresh", "Menu:&Zoom", 0,
                "Show Layer 1", "Show Layer 2", "Show Layer 3",
                "Show Sprites", "Show Grid", "Show Dim Screens",
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
            )
        for name, actions in menubaractions:
            # Add menu, if it's not already defined
            if name not in menus:
                menu = menubar.addMenu(name)
                menus[name] = menu
            else:
                menu = menus[name]

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
                    menus[menukey] = menu.addMenu(menutext)
                else:
                    self.actions[actionkey].setIconVisibleInMenu(False)
                    menu.addAction(self.actions[actionkey])

        # initialize toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
            # disable right-click menu to show/hide toolbar
        self.addToolBar(self.toolbar)

        toolbaractions = (
            "Open ROM", "Load Sublevel", "Save Sublevel",
            "Edit Header", "Edit Level Entrances", "Edit Screen Exits", 0,
            "Toggle Palette", "Toggle 8x8", "Toggle 16x16", 0,
            "Refresh", "Zoom Button", 0,
            "Count Items", "Item Memory", 0,
            "Export Graphics", "Import Graphics",
            )
        for actionkey in toolbaractions:
            if not actionkey:
                self.toolbar.addSeparator()
            else:
                self.toolbar.addAction(self.actions[actionkey])

        # special zoom submenu handling

        def _genZoomfunc(zoom):
            return lambda : self._setZoom(zoom)
        for zoomlevel in self.zoomlevels:
            actionstr = str(zoomlevel) + "%"
            action = QAction(actionstr)
            action.triggered.connect(_genZoomfunc(zoomlevel))
            self.actions["Zoom " + actionstr] = action
            menus["Zoom"].addAction(action)
        self.actions["Zoom 100%"].setShortcut("Ctrl+0")

        zoombutton = QToolButton()
        zoombutton.setIcon(QAdvyniaIcon("zoom.png"))
        zoombutton.setToolTip("Zoom")
        zoombutton.setMenu(menus["Zoom"])
        zoombutton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.toolbar.insertWidget(self.actions["Zoom Button"], zoombutton)
        self.toolbar.removeAction(self.actions["Zoom Button"])

        # special move action handling
        for actionkey in ("Move Left", "Move Right", "Move Up", "Move Down"):
            self.addAction(self.actions[actionkey])


    # Save/load functions

    def openROMDialog(self):
        directory = AdvMetadata.appdir
        if Adv3Attr.filepath:
            directory = os.path.dirname(Adv3Attr.filepath)

        filepath, _ = QFileDialog.getOpenFileName(
            self, caption="Open ROM", directory=directory,
            filter="GBA ROM Image (*.gba)")
        if filepath:
            self.loadROM(filepath)
            return filepath

    def loadROM(self, filepath):
        """Validate the given filepath as a ROM image of SMA3 (U), and if
        successful, load the ROM."""

        size = os.path.getsize(filepath)

        if size < 0x400000:
            QDialogROMValidation(self, size=size, override=False).exec()
            return

        savedmetadata, _ = GBA.importdata(filepath, 0x083FFFE0, 0x20)
        if savedmetadata == bytes(0x20):
            Adv3Attr.savedversion = None
        else:
            # metadata region is not blank: validate
            if savedmetadata[0:8] != b"Advynia3":
                QSimpleDialog(self, title="Error", text="".join(
                    ("Could not load file:\n", filepath, 
                     "\nFile does not appear to be a valid SMA3 (U) ROM image."))
                             ).exec()
                return
            versionlist = []
            for i in range(8, 0xE, 2):
                versionlist.append(int.from_bytes(
                    savedmetadata[i:i+2], byteorder="little"))
            Adv3Attr.savedversion = AdvMetadata.ProgramVersion(versionlist)

            # check for higher version
            if Adv3Attr.savedversion > AdvMetadata.version:
                cancelflag = QDialogROMValidation(
                    self, size=size, savedversion=Adv3Attr.savedversion).exec()
                if cancelflag:
                    return

            self.loadROMvalidated(filepath)
            return

        # if no Advynia metadata, try to validate as clean ROM
        if size == 0x400000:
            with open(filepath, "rb") as f:
                crc32 = zlib.crc32(f.read())
            if crc32 != 0x40A48276:
                # incorrect checksum
                internalID, _ = GBA.importdata(filepath, 0x080000AC, 4)
                internalID = str(internalID, encoding="ASCII")
                if internalID == "A3AJ" or internalID == "A3AP":
                    # If it's another region of SMA3, Advynia may successfully
                    # load a sublevel then crash on graphics load, so they need
                    # to be filtered manually.
                    QSimpleDialog(self, title="Error", text="".join(
                        ("Could not load file:\n", filepath, 
                         "\nFile appears to be a ROM image of SMA3 ",
                         {"A3AJ":"(J)", "A3AP":"(E)"}[internalID],
                         ". Advynia only supports the (U) version.",
                         ))).exec()
                    return
                else:
                    cancelflag = QDialogROMValidation(self, crc32=crc32).exec()
                    if cancelflag:
                        return
        else:
            # size > 0x400000: incorrect file size
            cancelflag = QDialogROMValidation(self, size=size).exec()
            if cancelflag:
                return

        try:
            # Try to load a sublevel. If the ROM isn't SMA3, this will usually
            # produce an invalid pointer, but might result in other errors.
            sublevel = SMA3.Sublevel.importbyID(filepath, 0)
            sublevel = SMA3.Sublevel.importbyID(filepath, 1)
        except Exception:
            internalname, _ = GBA.importdata(filepath, 0x080000A0, 0xC)
            internalname = str(internalname, encoding="ASCII")
            if internalname == "SUPER MARIOC":
                QSimpleDialog(self, title="Error", text="".join(
                    ("Could not load file:\n", filepath, 
                     "\nFile appears to be SMA3 (U), but SMA3 sublevel data "
                     "was not found or could not be parsed."))
                             ).exec()
            else:
                QSimpleDialog(self, title="Error", text="".join(
                    ("Could not load file:\n", filepath, 
                     "\nFile does not appear to be a valid SMA3 (U) ROM image."))
                             ).exec()

        else:
            # Validation successful, so load the ROM
            self.loadROMvalidated(filepath)

    def loadROMvalidated(self, filepath):
        Adv3Attr.filepath = filepath
        Adv3Attr.filename = os.path.basename(filepath)
        Adv3Attr.tilemapL1_8x8 = SMA3.importL1_8x8tilemaps(Adv3Attr.filepath)
        Adv3Patch.detectpatches()
        self.updatepatchlayouts()
        if Adv3Attr.sublevel.ID:
            self.loadSublevelID(Adv3Attr.sublevel.ID)
        else:
            self.loadSublevelID(0)
        self.statusbar.setActionText("Opened ROM: "+filepath)

    def updatepatchlayouts(self):
        for widget in (self.viewer8x8, self.headereditor):
            widget.updatepatchlayout()

    def updatewindowtitle(self):
        self.windowtitle = [self.windowtitle[0], Adv3Attr.filename]
        if Adv3Attr.sublevel.ID is not None:
            self.windowtitle.append(
                "Sublevel " + format(Adv3Attr.sublevel.ID, "02X"))
        self.setWindowTitle(" - ".join(self.windowtitle))

    def loadSublevel(self, sublevel):
        "Load a sublevel from an SMA3.Sublevel object."

        timer = timerstart()  # debug

        try:
            Adv3Attr.sublevel = sublevel
            if not sublevel.fromfile:
                Adv3Patch.loadsublevelpatchattr(sublevel)
            Adv3Visual.loadpalette(sublevel)
            Adv3Visual.loadgraphics(sublevel)

            self.reload("All")

        except Exception as err:
            message = ("Error loading sublevel.\n"
                "This sublevel appears to be corrupt. If you're getting this "
                "error from normal Advynia usage, please report this as a bug. "
                "Uploading your hack as a patch is recommended to help debug "
                "the error."
                "\n\n" + format_exc())
            QSimpleDialog(self, text=message).exec()
            return

        # window title and status bar
        if sublevel.ID is not None:
            if sublevel.datablocks:
                actiontext = ("Loaded sublevel {sublevelID}: main data from "
                "{mainptr}, sprite data from {spriteptr}.")
                self.statusbar.setActionText(actiontext.format(
                    sublevelID=format(sublevel.ID, "02X"),
                    mainptr=format(sublevel.datablocks["main"][0], "08X"),
                    spriteptr=format(sublevel.datablocks["sprite"][0], "08X")))
        self.updatewindowtitle()
        self.statusbar.updateByteText()

        if AdvMetadata.printtime: print("Total sublevel load:",
            timerend(timer), "ms")  # debug

        if sublevel.ID == 0x38:
            QSimpleDialog(self, text="Sublevel 38 is used by the intro "
                "cutscene. The header is unused, and "
                "editing this may result in unexpected in-game behavior.",
                title="Warning").exec()
        if sublevel.header[9] == 9:
            QSimpleDialog(self, text="This is the Raphael arena. "
                "Editing this may result in unexpected in-game behavior.",
                title="Warning").exec()
        elif sublevel.header[9] == 0xD:
            QSimpleDialog(self, text="This is the Froggy arena. "
                "Editing this may result in unexpected in-game behavior.",
                title="Warning").exec()

    def loadSublevelID(self, sublevelID):
        "Load a sublevel from the ROM."
        self.loadSublevel(SMA3.Sublevel.importbyID(Adv3Attr.filepath, sublevelID))

    def saveSublevelAction(self):
        """Called from the save sublevel action (toolbar, menu, Ctrl+S),
        and when confirming Save As.
        Handles other checks before saving."""

        # check for screen count first
        screencount = self.sublevelscene.layer1.tilemap.screencount()
        if self.sublevelscene.layer1.tilemap.screencount() >= 0x40:
            QSimpleDialog(self, title="Warning", text="".join(
                ("The current sublevel uses ", format(screencount, "02X"),
                 " screens. If a sublevel uses more than 3F screens, it "
                 "will freeze the game on the loading screen!\n"
                 "If this sublevel loads in-game, please report this-- "
                 "there may be an error with how Advynia simulates object "
                 "screen memory allocation."
                          ))).exec()

        # check for item memory errors
        self.itemmemorycheck(dialog_on_pass=False)

        self.saveSublevelToROM(Adv3Attr.sublevel, Adv3Attr.sublevel.ID)

    def saveSublevelToROM(self, sublevel, sublevelID):
        "Save a sublevel to the ROM, with the specified ID."

        if not Adv3Save.firstsavewarning(): return

        oldsublevel = SMA3.Sublevel.importbyID(Adv3Attr.filepath, sublevelID)

        ## should back up ROM before erasing old data

        # erase old sublevel data
        GBA.erasedata(Adv3Attr.filepath, *oldsublevel.datablocks["main"])
        GBA.erasedata(Adv3Attr.filepath, *oldsublevel.datablocks["sprite"])

        # save new sublevel data
        maindata = sublevel.exportmaindata()
        spritedata = sublevel.exportspritedata()

        mainptr2 = GBA.readptr(
            Adv3Attr.filepath, SMA3.Pointers.sublevelmainptrs) + 4*sublevelID
        spriteptr2 = GBA.readptr(
            Adv3Attr.filepath, SMA3.Pointers.sublevelspriteptrs) + 4*sublevelID

        mainptr1 = Adv3Save.saveDataToROM(maindata, mainptr2)
        if not mainptr1: return
        spriteptr1 = Adv3Save.saveDataToROM(spritedata, spriteptr2)
        if not spriteptr1: return

        # save extended sublevel data from patches
        Adv3Save.savesublevelpatchattr(sublevel, sublevelID)

        # update current sublevel's data blocks
        Adv3Attr.sublevel.datablocks = SMA3.Sublevel.importbyID(
            Adv3Attr.filepath, sublevelID).datablocks

        # window title and status bar
        self.updatewindowtitle()
        actiontext = ("Saved sublevel {sublevelID}: main data at {mainptr}, "
            "sprite data at {spriteptr}.")
        self.statusbar.setActionText(actiontext.format(
            sublevelID=format(sublevelID, "02X"),
            mainptr=format(mainptr1, "08X"),
            spriteptr=format(spriteptr1, "08X")))

    def importSublevel(self):
        "Load a sublevel from a separate file."

        filepath, _ = QFileDialog.getOpenFileName(
            self, caption="Import Sublevel",
            directory=os.path.dirname(Adv3Attr.filepath),
            filter=";;".join((
                "All supported files (*.a3l *.ylt)",
                AdvMetadata.export3ext,
                "SNES YI Level Tool file (*.ylt)")))
        if filepath:
            _, ext = os.path.splitext(filepath)

            warnSNES = False

            if ext.lower() == ".a3l":
                data = AdvFile.A3LFileData.importfromfile(filepath)
                if data.version > AdvMetadata.version:
                    QSimpleDialog(self, title="Warning", text="".join((
                        "This sublevel was created in Advynia ", str(version),
                        ". You are using version ", str(AdvMetadata.version),
                        "."
                        ))).exec()

                sublevel = data.tosublevel()
                if 0x95 in data:
                    warnSNES = True

                # check for patches that aren't applied to current ROM
                newpatches = []
                if 6 in data and not Adv3Attr.world6flag:
                    newpatches.append("world6flag")
                if sublevel.music and not Adv3Attr.musicoverride:
                    newpatches.append("musicoverride")
                if sublevel.stripeIDs and not Adv3Attr.sublevelstripes:
                    if sublevel.stripeIDs != SMA3.loadstripeIDs(
                            Adv3Attr.filepath, sublevel.header[7]):
                        newpatches.append("sublevelstripes")
                if 0x65 in data and not Adv3Attr.object65:
                    newpatches.append("object65")
                if newpatches:
                    if not QDialogImportPatch(newpatches, sublevel).exec():
                        return

                self.loadSublevel(sublevel)

                self.statusbar.setActionText("".join((
                    "Imported sublevel ", format(Adv3Attr.sublevel.ID, "02X"),
                    " from ", filepath)))

            elif ext.lower() == ".ylt":
                warnSNES = True
                sublevel = SMA3.SublevelFromSNES()
                sublevel.fromfile = True
                with open(filepath, "rb") as f:
                    sublevel.ID = f.read(1)[0]
                    sublevel.importmaindata(f)
                    sublevel.importspritedata(f)
                self.loadSublevel(sublevel)

                self.statusbar.setActionText("".join((
                    "Imported sublevel ", format(Adv3Attr.sublevel.ID, "02X"),
                    " from ", filepath)))

            if warnSNES:
                QSimpleDialog(self, title="Warning", text="".join((
                    "This sublevel was created on the SNES version. The "
                    "entrance camera bytes will need to be set manually, and "
                    "level design may need to be tweaked for the GBA screen "
                    "size."
                    ))).exec()

    def exportSublevel(self):
        "Export a sublevel to a separate file."

        # get filepath from user
        filename = [os.path.splitext(Adv3Attr.filename)[0], "-", "Sublevel"]
        if Adv3Attr.sublevel.ID is not None:
            filename.append(format(Adv3Attr.sublevel.ID, "02X"))
        filename.append(".a3l")
        defaultpath = os.path.join(
            os.path.dirname(Adv3Attr.filepath), "".join(filename))

        filepath, _ = QFileDialog.getSaveFileName(
            self, caption="Export Sublevel", filter=AdvMetadata.export3ext,
            directory=defaultpath)

        # export to filepath
        if filepath:
            data = AdvFile.A3LFileData.fromsublevel(Adv3Attr.sublevel)
            if not Adv3Attr.sublevelstripes:
                # include stripe data even if the patch isn't applied
                data[5] = Adv3Visual.spritegraphics.stripeIDs
            data.exporttofile(filepath)
            self.statusbar.setActionText("Exported sublevel to " + filepath)

    def exportAllSublevels(self):
        outputdir = QFileDialog.getExistingDirectory(
            self, caption="Export All Sublevels",
            directory=os.path.dirname(Adv3Attr.filepath))

        if outputdir:
            AdvFile.exportallYIsublevels(Adv3Attr.filepath, outputdir)
            self.statusbar.setActionText(
                "Exported all sublevels to " + outputdir)

    def exportSNESSublevels(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, caption="Open SNES ROM",
            directory=os.path.dirname(Adv3Attr.filepath),
            filter="SNES ROM Image (*.sfc, *.smc)")
        if not filepath:
            return

        outputdir = QFileDialog.getExistingDirectory(
            self, caption="Extract SNES Sublevels",
            directory=os.path.dirname(filepath))
        if outputdir:
            AdvFile.exportallYIsublevels(filepath, outputdir, console="SNES")
            self.statusbar.setActionText(
                "Extracted all sublevels from " + os.path.basename(filepath))

    # Sublevel display functions

    def exportgraphics(self):
        SMA3.exportgraphics(Adv3Attr.filepath)
        self.statusbar.setActionText(
            "Exported all graphics and compressed tilemaps.")

    zoomlevels = (25, 50, 100, 200, 300, 400)

    def _setZoom(self, zoom):
        AdvSettings.zoom = zoom
        self.sublevelview.resetTransform()
        self.sublevelview.scale(zoom/100, zoom/100)
        self.statusbar.setActionText("".join((
            "Zoom: ", str(AdvSettings.zoom), "%")))

    def _zoomin(self):
        for value in self.zoomlevels:
            if AdvSettings.zoom < value:
                break
        else: return
        self._setZoom(value)

    def _zoomout(self):
        for value in reversed(self.zoomlevels):
            if AdvSettings.zoom > value:
                break
        else: return
        self._setZoom(value)

    def _magnifyingglass(self):
        AdvSettings.showredcoins = not AdvSettings.showredcoins
        Adv3Visual.palette.setRedCoinPalette(AdvSettings.showredcoins)
        if AdvSettings.showredcoins:
            self.statusbar.setActionText("Enabled red coin palette.")
        else:
            self.statusbar.setActionText("Disabled red coin palette.")
        self.setHeader(2, Adv3Attr.sublevel.header[2])  # reload layer 1 palette
        for spriteitem in self.sublevelscene.spritelayer.spriteitems:
            if spriteitem.ID == 0x65:  # red coin
                spriteitem.reloadGraphics()

    def setHeader(self, *args):
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

        self.reload(updateset)

    def reload(self, updateset):
        if "All" in updateset:
            updateset = {
                "cache8_layers",
                "Layer 1", "Layer 1 Tilemap", "Layer 2", "Layer 3",
                "Background Layer", "Sprites", "Sprite Graphics",
                "Screen Exits",
                "Palette", "8x8",
                }
            self.sublevelscene.selection.clear()

        # update relevant widgets with graphics/palette changes
        if "cache8_layers" in updateset:
            Adv3Visual.resetcache8_layers()
        if "Layer 1" in updateset:
            Adv3Visual.resetcache16()
            if "Layer 1 Tilemap" in updateset:
                self.sublevelscene.layer1.createTilemap(Adv3Attr.sublevel)
                self.statusbar.setHoverText(None)
            self.sublevelscene.layer1.updateLayerGraphics(forcereload=True)
            self.sublevelscene.selection.setSelectedObjects(
                self.sublevelscene.selection.objects)
            self.sidebar.reload(forcereload=True)
            self.viewer16x16.queueupdate()
        if "Layer 2" in updateset:
            self.sublevelscene.layer2.dispLayer()
        if "Layer 3" in updateset:
            self.sublevelscene.layer3.dispLayer()
        if "Background Layer" in updateset:
            self.sublevelscene.background.dispBGgradient()
        if "Sprites" in updateset:
            self.sublevelscene.spritelayer.loadSprites(Adv3Attr.sublevel)
        if "Sprite Graphics" in updateset:
            Adv3Visual.resetcache8_sprites()
            self.sublevelscene.spritelayer.reloadSpriteGraphics(
                Adv3Attr.sublevel)
            self.sidebar.reload(forcereload=True)
        if "Screen Exits" in updateset:
            self.sublevelscene.grid.dispScreenExits(Adv3Attr.sublevel.exits)
        if "Palette" in updateset:
            self.viewerpalette.updateDropdowns()
            self.viewerpalette.reloadPalette()
        if "8x8" in updateset:
            self.viewer8x8.queueupdate()

    # Misc sublevel functions

    def countitems(self):
        redcoins = 0
        flowers = 0
        for row in self.sublevelscene.layer1.tilemap:
            for tileID in row:
                if tileID in (0x6001, 0x10E16) or tileID>>8 == 0xA3:
                    # red coin tile or in poundable post
                    redcoins += 1
        for spr in Adv3Attr.sublevel.sprites:
            if spr.ID in (0x065, 0x022, 0x068, 0x05B):
                # stationary sprite, flashing egg, flashing egg block,
                #  Bandit with red coin
                redcoins += 1
            elif spr.ID in (0x0FA, 0x110, 0x0B8):
                # flower, tileset-specific flower, ? cloud with flower
                flowers += 1
            elif spr.ID == 0x12C and not spr.x&1:
                # Fly Guy with red coin, back and forth
                redcoins += 1
            elif spr.ID == 0x08D and spr.parity() == 1:
                # Fly Guy with red coin, timed
                redcoins += 1
            elif spr.ID == 0x067 and spr.parity() == 2:
                # Chomp Rock ? cloud with flower
                flowers += 1
            elif spr.ID == 0x161:
                # reward for killing all enemies
                if spr.parity() == 0:
                    redcoins += 1
                elif spr.parity() == 2:
                    flowers += 1

        text = "Red coins: {redcoins}<br>Flowers: {flowers}"
        QSimpleDialog(self, title="Count Items",
            text=text.format(redcoins=redcoins, flowers=flowers)).exec()

    def itemmemorycheck(self, *, dialog_on_pass=True):
        # check for sprite conflicts, and track any item memory sprites
        sprcolstatus = defaultdict(int)
        for spr in Adv3Attr.sublevel.sprites:
            itemattr = SMA3.SpriteMetadata[(spr.ID, spr.parity())].itemmemory
            if spr.ID == 0x0B6:
                # if ring of 8 coins: activate 5 nearby columns, low priority
                for x in (spr.x-2, spr.x-1, spr.x+1, spr.x+2, spr.x+3):
                    if x < 0 or x >= 0x100:
                        continue
                    screen = SMA3.coordstoscreen(x, spr.y)
                    if sprcolstatus[(screen, x)] >= 2:
                        self._itemmemoryerror(screen, x)
                        return
                    sprcolstatus[(screen, x)] = 1
                itemattr = 2
            if itemattr:
                # sprite uses item memory
                screen = SMA3.coordstoscreen(spr.x, spr.y)
                if itemattr + sprcolstatus[(screen, spr.x)] >= 3:
                    self._itemmemoryerror(screen, spr.x)
                    return
                sprcolstatus[(screen, spr.x)] = itemattr

        # check for tile conflicts
        tilemap = self.sublevelscene.layer1.tilemap
        for screen in range(SMA3.Constants.maxscreen + 1):
            startX, startY = SMA3.screentocoords(screen)
            for x in range(startX, startX+0x10):
                passed = self._itemmemorycolcheck(
                    tilemap, x, startY, sprcolstatus[(screen, x)])
                if not passed:
                    self._itemmemoryerror(screen, x)
                    return

        if dialog_on_pass:
            QSimpleDialog(self, title="Item Memory Check",
                text="No item memory errors detected.").exec()

    @staticmethod
    def _itemmemorycolcheck(tilemap, x, startY, colstatus=0):
        for y in range(startY, startY+0x10):
            tileID = tilemap[y][x]
            if tileID in (0x6001, 0x10E16) or tileID>>8 == 0xA3:
                # red coin tile or in poundable post: high priority
                if colstatus:
                    return False
                colstatus = 2
            elif tileID in (0x6000, 0x7400):
                # normal coins only conflict with high priority
                if colstatus >= 2:
                    return False
                colstatus = 1
        return True

    def _itemmemoryerror(self, screen, x):
        text = """Items in the same column detected on screen {screen} at x={x}.
If one item is collected, any others may vanish!"""
        QSimpleDialog(self, title="Item Memory Check", text=text.format(
            screen=format(screen, "02X"), x=format(x, "02X"))).exec()

class QMainEditorStatusBar(QStatusBar):
    def __init__(self, *args):
        super().__init__(*args)

        self.hovertext = QLabel()
        self.addWidget(self.hovertext, 4)
        self.actiontext = QLabel()
        self.addWidget(self.actiontext, 9)
        self.sizetext = QLabel()
        self.addWidget(self.sizetext, 0)
        self.sizetext.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.bytecount = 0
        self.screencount = 0

        QSPIgnoreWidth = QSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setSizePolicy(QSPIgnoreWidth)
        self.hovertext.setSizePolicy(QSPIgnoreWidth)
        self.actiontext.setSizePolicy(QSPIgnoreWidth)
        self.sizetext.setSizePolicy(QSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))

    def setHoverText(self, x=None, y=None, tileID=None, obj=None, spr=None):
        if x is None or y is None:
            self.hovertext.clear()
            return

        text = ["x", format(x, "02X"), " y", format(y, "02X")]
        if tileID is not None:
            text += [" | ", format(tileID, "04X")]
        if spr is not None:
            text += [" | sprite ", str(spr)]
        elif obj is not None:
            text += [" | object ", str(obj)]
        self.hovertext.setText("".join(text))

    def setActionText(self, text):
        self.actiontext.setText(text)

    def updateByteText(self):
        self.setSizeText(newbytecount=sum(Adv3Attr.sublevel.size))

    def setSizeText(self, newbytecount=None, newscreencount=None):
        if newbytecount is not None: self.bytecount = newbytecount
        if newscreencount is not None: self.screencount = newscreencount

        sizetext = [format(self.screencount, "02X"), " screen"]
        if self.screencount != 1: sizetext.append("s")
        sizetext += [",  ", format(self.bytecount, "02X"), " bytes"]

        self.sizetext.setText("".join(sizetext))


########

# Run editor

if __name__ == "__main__":
    # print exceptions to console
    def excepthook(cls, value, traceback):
        sys.__excepthook__(cls, value, traceback)
    sys.excepthook = excepthook

    app = QAdvynia(sys.argv)
    sys.exit(app.exec())
