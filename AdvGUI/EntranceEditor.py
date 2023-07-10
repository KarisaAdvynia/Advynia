"""SMA3 Entrance Editor
Dialogs for editing level entrances and screen exits, and their shared base
class."""

# standard library imports
import copy
from functools import partial

# import from other files
import AdvEditor, AdvFile
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr, Adv3Save, Adv3Patch
from AdvGame import GBA, SMA3
from .Dialogs import QDialogFileError
from .GeneralQt import *

class QDialogSMA3Entrances(QDialogBase):
    "Base class for level entrance and screen exit dialogs."
    def __init__(self, parent, screenexits=False):
        super().__init__(parent)

        self.entr = SMA3.Entrance()

        # init widgets
        self.entrlistwidget = QListWidgetResized(width=100, height=100)
        self.entrlistwidget.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.entrlistwidget.currentRowChanged.connect(self.entrselectcallback)

        self.buttons = {}
        for key, text, slot, tooltip in (
                ("Confirm", "OK", self.accept, None),
                ("Cancel", "Cancel", self.reject, None),
                ("Copy", "&Copy", self.copyentr, "Copy entrance to clipboard"),
                ("Paste", "&Paste", self.pasteentr,
                     "Paste entrance from clipboard"),
                ("+", "+", None, "Increase midway entrance count"),
                ("-", "\u2013", None, "Decrease midway entrance count"),
                ("Add", "&Add", None, "Add new screen exit.\n"
                     "Uses specified screen number if available."),
                ("Delete", "Delete", None, "Delete current screen exit"),
                ("Move", "&Move", None,
                     "Move current screen exit to specified screen,\n"
                     "replacing any existing screen exit."),
                ("Duplicate", "&Duplicate", None,
                     "Create duplicate of current screen exit.\n"
                     "Uses specified screen number if different from\n"
                     "current screen."),
                ("Export", "&Export", None, "Export entrances to file"),
                ("Import", "&Import", None, "Import entrances from file"),
                ):
            button = QPushButton(text)
            button.setToolTip(tooltip)
            if slot:
                button.clicked.connect(slot)
            if len(text) == 1:
                button.setFixedSize(25, 25)
            self.buttons[key] = button

        self.buttons["Confirm"].setDefault(True)

        self.labels = {}
        for key, text in (
            ("entrlist", "Level"),
            ("levelnum", ""),
            ("entrname", "Entrance data:"),
            (0, "Sublevel:"), (1, "X"), (2, "Y"), (3, ""),
            ("4hi", "Affects layer 1 Y (0-F)"), ("4lo", "Unknown scroll-related (0-F)"),
            ("destscreen", ""),
            ("newscreen", "New screen number:"),
            ):
            self.labels[key] = QLabel(text)

        self.lineeditbytes = {}
        for key, maxvalue in (
            (0, SMA3.Constants.maxsublevelID), (1, SMA3.Constants.maxtileX),
            (2, SMA3.Constants.maxtileY), (3, 0xFF),
            ("4hi", 0xF), ("4lo", 0xF),
            ("newscreen", SMA3.Constants.maxscreen),
            ("entrlist", SMA3.Constants.maxlevelID),
            ):
            self.lineeditbytes[key] = QLineEditHex(
                maxvalue=maxvalue, absorbEnter=(key=="entrlist"))

            if isinstance(key, int):
                self.lineeditbytes[key].editingFinished.connect(
                    self._genlineeditcallback(key))
            elif isinstance(key, str) and key[0] == "4":
                self.lineeditbytes[key].editingFinished.connect(
                    self.updatebyte4fromwidgets)

        self.byte5checkboxes = []
        for bitindex, text in (
            (0, "Disable horizontal"),
            (1, "Disable vertical"),
            (2, "Limit downward"),
            ):
            checkbox = QCheckBox(text)
            checkbox.clicked.connect(partial(self.byte5toggle, 1 << bitindex))
            self.byte5checkboxes.append(checkbox)
            

        self.animdropdown = QComboBox()
        for i, text in enumerate(SMA3.Constants.entranceanim):
            self.animdropdown.addItem(f"{i:02X}: {text}")
        self.animdropdown.setPlaceholderText("(invalid)")
        self.animdropdown.activated.connect(self.animdropdowncallback)

        self.banditcheckbox = QCheckBox("Bandit minigame")
        self.banditcheckbox.clicked.connect(self.banditcheckboxcallback)

        self.banditIDlookup = {}
        self.banditdropdown = QComboBox()
        for sublevelID, text in zip(
                range(SMA3.Constants.maxsublevelID + 1,
                      SMA3.Constants.maxsublevelIDscreenexit + 1),
                SMA3.Constants.banditminigames,
                strict=True):
            self.banditIDlookup[sublevelID] = len(self.banditdropdown)
            if not text:
                continue
            self.banditdropdown.addItem(f"{sublevelID:02X}: {text}", sublevelID)
        self.banditdropdown.activated.connect(self.banditdropdowncallback)

        # init layout
        layoutMain = QHBoxLayout()
        self.setLayout(layoutMain)

        layoutL = QVHBoxLayout()
        layoutMain.addLayout(layoutL)
        layoutMain.addWidget(QVertLine())
        layoutR = QVHBoxLayout()
        layoutMain.addLayout(layoutR)

        layoutL.addRow()
        layoutL[-1].addWidget(self.labels["entrlist"])
        if not screenexits:
            layoutL[-1].addWidget(self.lineeditbytes["entrlist"])
            layoutL[-1].addWidget(self.labels["levelnum"])
        layoutL[-1].addStretch()

        layoutL.addWidget(self.entrlistwidget)

        layoutL.addRow()
        layoutL[-1].addStretch()
        if screenexits:
            layoutL[-1].addWidget(self.buttons["Delete"])
        else:
            layoutL[-1].addWidget(self.buttons["+"])
            layoutL[-1].addWidget(self.buttons["-"])
        layoutL[-1].addStretch()

        layoutR.addRow()
        layoutR[-1].addWidget(self.labels["entrname"])
        layoutR[-1].addStretch(1000)
        layoutR[-1].addWidget(self.buttons["Copy"])
        layoutR[-1].addWidget(self.buttons["Paste"])

        layoutR.addWidget(QHorizLine())

        layoutR.addRow()
        layoutR[-1].addWidget(self.labels[0])
        layoutR[-1].addWidget(self.lineeditbytes[0])
        layoutR[-1].addSpacing(10)
        layoutR[-1].addWidget(self.labels[1])
        layoutR[-1].addWidget(self.lineeditbytes[1])
        layoutR[-1].addSpacing(10)
        layoutR[-1].addWidget(self.labels[2])
        layoutR[-1].addWidget(self.lineeditbytes[2])
        layoutR[-1].addSpacing(10)
        layoutR[-1].addWidget(self.labels["destscreen"])
        layoutR.addRow()
        layoutR[-1].addWidget(self.labels[3])
        layoutR[-1].addWidget(self.lineeditbytes[3])
        layoutR[-1].addWidget(self.animdropdown)
        layoutR.addRow()
        layoutR[-1].addWidget(self.banditcheckbox)
        layoutR[-1].addWidget(self.banditdropdown)

        layoutR.addWidget(QHorizLine())
        layoutR.addWidget(QLabel("Scrolling setings:"))
        layoutR.addRow()
        layoutR[-1].addWidget(self.byte5checkboxes[0])
        layoutR[-1].addWidget(self.byte5checkboxes[1])
        layoutR.addRow()
        layoutR[-1].addWidget(self.byte5checkboxes[2])
        layoutR[-1].addSpacing(10)
        layoutR[-1].addWidget(self.labels["4hi"])
        layoutR[-1].addWidget(self.lineeditbytes["4hi"])
        layoutR.addRow()
        layoutR[-1].addWidget(self.labels["4lo"])
        layoutR[-1].addWidget(self.lineeditbytes["4lo"])

        layoutR.addStretch()

        layoutR.addWidget(QHorizLine())
        layoutR.addRow()
        if screenexits:
            layoutR[-1].addWidget(self.labels["newscreen"])
            layoutR[-1].addWidget(self.lineeditbytes["newscreen"])
            layoutR.addRow()
            layoutR[-1].addWidget(self.buttons["Add"])
            layoutR[-1].addWidget(self.buttons["Move"])
            layoutR[-1].addWidget(self.buttons["Duplicate"])
        else:
            layoutR[-1].addWidget(QLabel("Manage entrances:"))
            layoutR[-1].addWidget(self.buttons["Export"])
            layoutR[-1].addWidget(self.buttons["Import"])

        layoutR.addWidget(QHorizLine())
        layoutR.addRow()
        layoutR[-1].addStretch(1000)
        layoutR[-1].addWidget(self.buttons["Confirm"])
        layoutR[-1].addWidget(self.buttons["Cancel"])

        for layout in layoutR:
            layout.addStretch()

        self.setEntranceLayout("normal")
        self.setFixedWidth(self.sizeHint().width())

    # general methods

    def open(self):
        self.entrlistwidget.setFocus()
        super().open()

    def loadentrance(self, entr):
        self.entr = entr
        for i, value in enumerate(entr):
            self.loadentrancebyte(i, value)

    def loadentrancebyte(self, i, value):
        if i <= 3:
            # update byte input
            self.lineeditbytes[i].setValue(value)

        match i:
            case 0:
                if self.entrancelayout == "levelmain":
                    return
                # swap normal/Bandit layout based on sublevel ID
                elif value > SMA3.Constants.maxsublevelID:
                    self.setEntranceLayout("bandit")
                    self.banditcheckbox.setChecked(True)
                    self.banditdropdown.setCurrentIndex(
                        self.banditIDlookup[value])
                    self.lineeditbytes[0].setText(f"{value:02X}")
                else:
                    self.setEntranceLayout("normal")
                    self.banditcheckbox.setChecked(False)
            case 3:
                if value >= len(self.animdropdown):
                    value = -1
                self.animdropdown.setCurrentIndex(value)
            case 1 | 2:
                # update dest screen number
                self.labels["destscreen"].setText(
                    f"Screen: {self.entr.destscreen:02X}")

            case 4:
                self.lineeditbytes["4hi"].setValue(value >> 4)
                self.lineeditbytes["4lo"].setValue(value & 0xF)
            case 5:
                for i in range(3):
                    self.byte5checkboxes[i].setChecked(value & (1<<i))

    def setentrancebyte(self, i, value):
        self.entr[i] = value
        # ensure lineedit and dropdown/destscreen are synchronized
        self.loadentrancebyte(i, value)
        self.reloadsidebar()

    def addentrancerow(self, prefix, entr):
        "Add a new row to the entrance list, with the provided prefix."
        text = [prefix, ":"]
        text += (f"{i:02X}" for i in entr[0:3])
        self.entrlistwidget.addItem(" ".join(text))

    def setEntranceLayout(self, key):
        """Enable/disable widgets to account for the minor differences in
        entrance formats."""

        self.entrancelayout = key

        for widget in (
                self.labels[3], self.lineeditbytes[3], self.animdropdown,
                self.banditcheckbox, self.banditdropdown,
                ):
            widget.setDisabled(True)
        for widget in (self.labels[0], self.lineeditbytes[0]):
            widget.setEnabled(True)
        self.lineeditbytes[3].hide()
        self.animdropdown.hide()

        if key == "levelmain":
            self.labels[3].setText("Level to unlock:")
            self.lineeditbytes[3].show()
            return

        for widget in (self.labels[3], self.animdropdown, self.lineeditbytes[3],
                       self.banditcheckbox):
            widget.setEnabled(True)
        if key == "normal":
            self.animdropdown.show()
            self.labels[3].setText("Animation:")
        elif key == "bandit":
            self.labels[0].setDisabled(True)
            self.lineeditbytes[0].setDisabled(True)
            self.lineeditbytes[3].show()
            self.labels[3].setText("Post-minigame sublevel:")
            self.banditdropdown.setEnabled(True)

    # widget callbacks

    def _genlineeditcallback(self, i):
        return lambda : self.setentrancebyte(i, self.lineeditbytes[i].value)

    def banditcheckboxcallback(self, checked):
        if checked:
            self.setEntranceLayout("bandit")
            self.setentrancebyte(0, self.banditdropdown.currentData())
        else:
            self.setEntranceLayout("normal")
            self.setentrancebyte(0, self.lineeditbytes[0].value)

    def banditdropdowncallback(self, index):
        self.setentrancebyte(0, self.banditdropdown.currentData())

    def animdropdowncallback(self, index):
        self.setentrancebyte(3, index)

    def entrselectcallback(self):
        "Overridden by subclasses."
        raise NotImplementedError

    def updatebyte4fromwidgets(self):
        self.setentrancebyte(4,
            self.lineeditbytes["4hi"].value << 4 |
            self.lineeditbytes["4lo"].value)

    def byte5toggle(self, bitmask):
        self.setentrancebyte(5, self.entr[5] ^ bitmask)

    # button functions

    def copyentr(self):
        if self.entrancelayout == "levelmain":
            # don't copy byte 3 of main entrances
            entr = copy.deepcopy(self.entr)
            entr[3] = 0
            text = str(entr)
        else:
            text = str(self.entr)
        QApplication.clipboard().setText(text)

    def pasteentr(self):
        clipboardtext = QApplication.clipboard().text()
        if not clipboardtext:
            return

        try:
            entrraw = bytes.fromhex(clipboardtext)
            if len(entrraw) == 0:
                raise ValueError
            if len(entrraw) > 6:
                QSimpleDialog(self, title="Warning", text=
                    f'Clipboard contents "{clipboardtext[:100]}"'
                    f" were parsed as {len(entrraw)} bytes. "
                    "Any bytes beyond the first 6 were truncated."
                    ).exec()
            entr = SMA3.Entrance(entrraw)
        except ValueError:
            QSimpleDialog(self, title="Error", text=
                         f'Clipboard contents "{clipboardtext[:100]}"'
                         " could not be parsed as entrance data."
                         ).exec()
        else:
            if self.entrancelayout == "levelmain":
                # don't change byte 3 of main entrances
                entr[3] = self.entr[3]
                # don't allow main entrances to use Bandit minigame IDs
                if entr[0] > SMA3.Constants.maxsublevelID:
                    entr[0] = SMA3.Constants.maxsublevelID
            for i in range(6):
                self.setentrancebyte(i, entr[i])
            self.loadentrance(entr)

class QDialogSMA3LevelEntrances(QDialogSMA3Entrances):
    "Dialog for editing the game's level main/midway entrances."
    def __init__(self, *args):
        super().__init__(*args)

        self.setWindowTitle("Edit Level Entrances")

        self.lineeditbytes["entrlist"].setValue(0)
        self.lineeditbytes["entrlist"].editingFinished.connect(
            self.levelnumcallback)
        self.buttons["Confirm"].setText("Save")
        self.buttons["Confirm"].setToolTip("Save modified entrances to ROM")
        for key, slot in (("+", self.addmidway),
                          ("-", self.delmidway),
                          ("Export", self.exportentrances),
                          ("Import", self.importentrances_dialog),
                          ):
            self.buttons[key].clicked.connect(slot)

        self.exportdialog = QDialogSMA3ExportEntrances(self)

        self.mainentrances = []
        self.midwayentrances = []
        self.levelID = 0

    def open(self):
        if not AdvEditor.ROM.exists(): return

        self.mainentrances, self.midwayentrances = AdvEditor.Entrance.loadentrances()

##        import itertools
##        print([hex(i) for i in itertools.chain(
##            self.mainentrances.datablock, self.midwayentrances.datablock)])
        self.reloadsidebar()
        super().open()

    def accept(self):
        if Adv3Save.savewrapper(Adv3Save.saveentrances,
                self.mainentrances, self.midwayentrances):
            super().accept()

    def reloadsidebar(self):
        row = self.entrlistwidget.currentRow()

        self.loadlevel(self.levelID)

        # select most recent row, if possible
        if not 0 <= row < len(self.entrlistwidget):
            row = 0
        self.entrlistwidget.setCurrentRow(row)

    def loadlevel(self, levelID):
        self.entrlistwidget.clear()
        self.levelID = levelID
        self.lineeditbytes["entrlist"].setValue(levelID)

        levelnumstr = SMA3.levelnumber(levelID, short=True)

        # add main/midway entrances to list
        self.addentrancerow("main", self.mainentrances[levelID])
        for i, entr in enumerate(self.midwayentrances[levelID]):
            self.addentrancerow(str(i), entr)

        self.buttons["+"].setEnabled(
            len(self.midwayentrances[levelID]) < Adv3Attr.maxmidpoints)
        self.buttons["-"].setEnabled(len(self.midwayentrances[levelID]))

        # set level name text
        self.labels["levelnum"].setText(levelnumstr)

        # select first row
        self.entrlistwidget.setCurrentRow(0)

    def levelnumcallback(self):
        self.loadlevel(self.lineeditbytes["entrlist"].value)

    def entrselectcallback(self):
        row = self.entrlistwidget.currentRow()
        if row == 0:
            self.setEntranceLayout("levelmain")
            self.loadentrance(self.mainentrances[self.levelID])
            self.labels["entrname"].setText("Main Entrance:")
        elif row >= 0:
            self.setEntranceLayout("normal")
            self.loadentrance(self.midwayentrances[self.levelID][row-1])
            self.labels["entrname"].setText(f"Midway Entrance {row-1:X}:")

    # button functions

    def addmidway(self):
        self.midwayentrances[self.levelID].append(SMA3.Entrance())
        self.reloadsidebar()
        self.buttons["-"].setEnabled(True)
        if len(self.midwayentrances[self.levelID]) >= Adv3Attr.maxmidpoints:
            self.buttons["+"].setDisabled(True)
            self.buttons["-"].setFocus()

    def delmidway(self):
        self.midwayentrances[self.levelID].pop()
        self.reloadsidebar()
        self.buttons["+"].setEnabled(True)
        if not self.midwayentrances[self.levelID]:
            self.buttons["-"].setDisabled(True)
            self.buttons["+"].setFocus()

    def exportentrances(self):
        # prompt for current level or all levels
        returnvalue = self.exportdialog.exec()
        if returnvalue == 1:
            caption = "Export Level Entrance"
            statustext = f"Exported level {self.levelID:02X}"
            dataargs = (self.mainentrances[self.levelID],
                        self.midwayentrances[self.levelID],
                        self.levelID)
        elif returnvalue == 2:
            caption = "Export Level Entrances"
            statustext = "Exported all"
            dataargs = (self.mainentrances, self.midwayentrances)
        else:
            return

        # prepare A3L data
        a3l = AdvFile.A3LFileData.fromentrances(*dataargs)
        defaultpath = os.path.join(
            os.path.dirname(Adv3Attr.filepath),
            a3l.defaultfilename(Adv3Attr.filename))

        # get filepath from user
        filepath, _ = QFileDialog.getSaveFileName(
            AdvWindow.editor, caption=caption, directory=defaultpath,
            filter=AdvFile.A3LFileData.longext)

        # export data
        if filepath:
            a3l.exporttofile(filepath)

            statustext += f" entrances to {filepath}"
            AdvWindow.statusbar.setActionText(statustext)

    def importentrances_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            AdvWindow.editor, caption="Import Level Entrances",
            directory=os.path.dirname(Adv3Attr.filepath),
            filter=";;".join((
                "All supported files (*.a3l *.yet)",
                AdvFile.A3LFileData.longext,
                "SNES YI Level Tool entrances (*.yet)")))
        if not filepath: return
        self.importentrances(filepath)

    def importentrances(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".a3l":
            a3l = AdvEditor.Export.importwrapper(
                AdvFile.A3LFileData.importfromfile, filepath)
            if not a3l: return
            datatype = a3l.datatype()
            warnSNES = False

            if datatype == "Entrances: Single Level":
                levelID, main, midways = a3l.toentrances()

                # prompt for level ID to replace
                newlevelID = QDialogSMA3Import1LevelEntr(
                    self, levelID, main, midways).exec()

                # replace entrances
                if newlevelID >= 0:
                    self.levelID = newlevelID
                    self.mainentrances[newlevelID] = main
                    self.midwayentrances[newlevelID] = midways
                    self.reloadsidebar()
                    AdvWindow.statusbar.setActionText(
                        f"Imported level {newlevelID:02X}"
                        f" entrances from {filepath}")
                return

            elif datatype == "Entrances: All Levels":
                mainentrances, midwayentrances = a3l.toentrances()
                if 0x95 in a3l:
                    warnSNES = True
                # continue to processing entrances

            else:
                QDialogFileError(AdvWindow.editor, filepath, text=(
                    "File does not contain entrance data. "
                    "Other .a3l file variants can be imported in the "
                    "main editor.")).exec()
                return

        elif ext == ".yet":
            result = AdvEditor.Export.loadwrapper(
                AdvFile.YILevelTool.import_yet, filepath)
            if not result: return
            mainentrances, midwayentrances = result
            warnSNES = True

        else:
            QDialogFileError(AdvWindow.editor, filepath,
                text=f"Importing from file extension {ext} is not supported."
                ).exec()
            return

        if warnSNES and not AdvSettings.warn_import_SNES:
            # change alert only if SNES warning is enabled
            warnSNES = False
        if ((warnSNES or AdvSettings.warn_import_allentrances) and
                not QDialogSMA3ImportAllLevelEntr(self, warnSNES).exec()):
            return

        self.mainentrances[:] = mainentrances
        self.midwayentrances[:] = midwayentrances
        self.reloadsidebar()
        AdvWindow.statusbar.setActionText(
            "Imported all entrances from " + filepath)

class QDialogSMA3ExportEntrances(QDialogBase):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Export Level Entrances")

        # init widgets

        self.buttons = [QRadioButton("Current level"),
                        QRadioButton("All levels")]
        self.buttons[1].setChecked(True)

        # init layout

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)
        for widget in self.buttons:
            layoutMain.addWidget(widget)
        layoutMain.addAcceptRow(self, accepttext="Export")

    def accept(self):
        for i, widget in enumerate(self.buttons):
            if widget.isChecked():
                super().done(i+1)

class QDialogSMA3Import1LevelEntr(QDialogBase):
    def __init__(self, parent, levelID, main, midway):
        super().__init__(parent)

        self.setWindowTitle("Import Level Entrances")

        # init widgets

        levellabel = QLabel("Replace level:")
        self.levelinput = QLineEditHex(maxvalue=SMA3.Constants.maxlevelID)
        self.levelinput.setValue(levelID)

        entrdesc = [
            f"Main Entrance:\n{main}\n\n"
            f"Midway Entrances:  {len(midway):X}"]
        for entr in midway:
            entrdesc += ["\n", str(entr)]
        entrlabel = QLabel("".join(entrdesc))

        # init layout

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addRow()
        layoutMain[-1].addWidget(levellabel)
        layoutMain[-1].addWidget(self.levelinput)
        layoutMain[-1].addStretch()
        layoutMain.addWidget(entrlabel)
        layoutMain.addAcceptRow(self, "Load")

    def accept(self):
        self.done(self.levelinput.value)

    def reject(self):
        self.done(-1)

class QDialogSMA3ImportAllLevelEntr(QDialogBase):
    def __init__(self, parent, warnSNES=False):
        super().__init__(parent)

        self.setWindowTitle("Import Level Entrances")

        # init widget

        if warnSNES:
            label = QLabel(
                """These entrances were created on the SNES version.<br><br>
                Extra/Secret entrances have been automatically swapped, but 
                the camera bytes will need to be set manually.""")
            label.setWordWrap(True)
            self.flag = "warn_import_SNES"
        else:
            label = QLabel("Replace all level entrances?\n"
                           "Entrances can be viewed before saving.")
            self.flag = "warn_import_allentrances"
        self.checkbox = QCheckBox("Don't show this message again")

        # init layout

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addWidget(label)
        layoutMain.addWidget(self.checkbox)
        layoutMain.addAcceptRow(self, "Load")

    def accept(self):
        if self.checkbox.isChecked():
            setattr(AdvSettings, self.flag, False)
        super().accept()

class QDialogSMA3ScreenExits(QDialogSMA3Entrances):
    "Dialog for editing the current sublevel's screen exits."
    def __init__(self, *args):
        super().__init__(*args, screenexits=True)

        self.setWindowTitle("Edit Screen Exits")

        self.lineeditbytes["newscreen"].setValue(0)
        for key, slot in (("Add", self.addexit),
                          ("Delete", self.delexit),
                          ("Move", self.moveexit),
                          ("Duplicate", self.duplicateexit)):
            self.buttons[key].clicked.connect(slot)

        self.exits = None
        self.screen = None

    def open(self):
        if Adv3Attr.sublevel.exits != self.exits:
            self.exits = copy.deepcopy(Adv3Attr.sublevel.exits)
            self.reloadsidebar()
            if len(self.entrlistwidget) != 0:
                # select first row if non-empty
                self.entrlistwidget.setCurrentRow(0)
            else:
                self.loadentrance(SMA3.Entrance())
        self.labels["entrlist"].setText(f"Sublevel {Adv3Attr.sublevel.ID:02X}")
        super().open()

    def accept(self):
        if Adv3Attr.sublevel.exits != self.exits:
            Adv3Attr.sublevel.exits = copy.deepcopy(self.exits)

            AdvWindow.statusbar.setActionText("Screen exits updated.")
            AdvWindow.undohistory.addaction("Edit Screen Exits",
                updateset={"Screen Exits", "Byte Text"}, reload=True)

        super().accept()

    def reloadsidebar(self):
        "Load lines of text representing each screen exit to the sidebar."
        self.entrlistwidget.clear()
        for screen in sorted(self.exits.keys()):
            self.addentrancerow(f"{screen:02X}", self.exits[screen])
        self._setselectedscreen(self.screen)

    def entrselectcallback(self):
        row = self.entrlistwidget.currentRow()
        if row != -1:
            self.screen = sorted(self.exits.keys())[row]
            self.loadentrance(self.exits[self.screen])
            self.lineeditbytes["newscreen"].setValue(self.screen)

    # button functions

    def _setselectedscreen(self, screen):
        if screen is None or screen not in self.exits.keys():
            return
        newrow = sorted(self.exits.keys()).index(screen)
        self.entrlistwidget.setCurrentRow(newrow)
        self.screen = screen

    def _findfreescreen(self):
        # find a free screen number, starting from 0
        for screen in range(0x80):
            if screen not in self.exits.keys():
                return screen

    def addexit(self):
        screen = self.lineeditbytes["newscreen"].value
        if screen in self.exits.keys():
            # if screen number is already used, find another
            screen = self._findfreescreen()
            if screen is None:
                return
        self.exits[screen] = SMA3.Entrance()

        self.reloadsidebar()
        self._setselectedscreen(screen)

    def delexit(self):
        if self.screen in self.exits.keys():
            del self.exits[self.screen]

            newrow = max(self.entrlistwidget.currentRow()-1, 0)
            self.reloadsidebar()
            if self.exits:
                self.entrlistwidget.setCurrentRow(newrow)
            else:
                self.loadentrance(SMA3.Entrance())

    def moveexit(self):
        newscreen = self.lineeditbytes["newscreen"].value
        self.exits[newscreen] = self.entr
        del self.exits[self.screen]

        self.reloadsidebar()
        self._setselectedscreen(newscreen)

    def duplicateexit(self):
        newscreen = self.lineeditbytes["newscreen"].value
        if newscreen == self.screen:
            newscreen = self._findfreescreen()
            if newscreen is None:
                return
        self.exits[newscreen] = copy.deepcopy(self.entr)

        self.reloadsidebar()
        self._setselectedscreen(newscreen)
