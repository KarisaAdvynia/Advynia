# standard library imports
import copy

# import from other files
from AdvGame import GBA, SMA3
from .QtGeneral import *

# globals
import AdvSettings, Adv3Attr, Adv3Save, Adv3Patch

class QDialogSMA3Entrances(QDialog):
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
            (0, "Sublevel:"), (1, "X"), (2, "Y"), (3, ""),
            (4, "Camera byte 4?"), (5, "Camera byte 5?"),
            ("destscreen", ""),
            ("bandit", "Bandit minigame"),
            ("newscreen", "New screen number:"),
            ):
            self.labels[key] = QLabel(text)

        self.lineeditbytes = {}
        for key, maxvalue in (
            (0, SMA3.Constants.maxsublevel), (1, SMA3.Constants.maxtileX),
            (2, SMA3.Constants.maxtileY), (3, 0xFF),
            (4, 0xFF), (5, 0xFF),
            ("newscreen", SMA3.Constants.maxscreen),
            ("entrlist", SMA3.Constants.maxlevel),
            ):
            self.lineeditbytes[key] = QLineEditByte(maxvalue=maxvalue)

        for i in range(6):
            self.lineeditbytes[i].editingFinished.connect(
                self._genlineeditcallback(i))

        self.animdropdown = QComboBox()
        for i, text in enumerate(SMA3.Constants.entranceanim):
            text = "".join((format(i, "02X"), ": ", text))
            self.animdropdown.addItem(text)
        self.animdropdown.setPlaceholderText("(invalid)")
        self.animdropdown.activated.connect(self.animdropdowncallback)

        self.banditcheckbox = QCheckBox()
        self.banditcheckbox.clicked.connect(self.banditcheckboxcallback)

        self.banditIDlookup = {}
        self.banditdropdown = QComboBox()
        for sublevelID, text in zip(
                range(SMA3.Constants.maxsublevel + 1,
                      SMA3.Constants.maxsublevelscreenexit + 1),
                SMA3.Constants.banditminigames,
                strict=True):
            self.banditIDlookup[sublevelID] = len(self.banditdropdown)
            if not text:
                continue
            text = "".join((format(sublevelID, "02X"), ": ", text))
            self.banditdropdown.addItem(text, sublevelID)
        self.banditdropdown.activated.connect(self.banditdropdowncallback)

        # init layout
        layoutMain = QHBoxLayout()
        self.setLayout(layoutMain)

        layoutLeft = QVBoxLayout()
        layoutMain.addLayout(layoutLeft)
        layoutMain.addWidget(QVertLine())
        layoutRight = QVBoxLayout()
        layoutMain.addLayout(layoutRight)

        layoutL0 = QHBoxLayout()
        layoutLeft.addLayout(layoutL0)
        layoutL0.addWidget(self.labels["entrlist"])
        if not screenexits:
            layoutL0.addWidget(self.lineeditbytes["entrlist"])
            layoutL0.addWidget(self.labels["levelnum"])
        layoutL0.addStretch()

        layoutLeft.addWidget(self.entrlistwidget)

        layoutLEnd = QHBoxLayout()
        layoutLeft.addLayout(layoutLEnd)
        layoutLEnd.addStretch()
        if screenexits:
            layoutLEnd.addWidget(self.buttons["Delete"])
        else:
            layoutLEnd.addWidget(self.buttons["+"])
            layoutLEnd.addWidget(self.buttons["-"])
        layoutLEnd.addStretch()

        layoutR = []
        def _layoutRnewline():
            layoutR.append(QHBoxLayout())
            layoutRight.addLayout(layoutR[-1])
        _layoutRnewline()
        layoutR[-1].addWidget(QLabel("Entrance data:"))
        layoutR[-1].addStretch(1000)
        layoutR[-1].addWidget(self.buttons["Copy"])
        layoutR[-1].addWidget(self.buttons["Paste"])
        layoutRight.addWidget(QHorizLine())

        _layoutRnewline()
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
        _layoutRnewline()
        layoutR[-1].addWidget(self.labels[3])
        layoutR[-1].addWidget(self.lineeditbytes[3])
        layoutR[-1].addWidget(self.animdropdown)
        _layoutRnewline()
        layoutR[-1].addWidget(self.labels[4])
        layoutR[-1].addWidget(self.lineeditbytes[4])
        layoutR[-1].addSpacing(10)
        layoutR[-1].addWidget(self.labels[5])
        layoutR[-1].addWidget(self.lineeditbytes[5])
        _layoutRnewline()
        layoutR[-1].addWidget(self.labels["bandit"])
        layoutR[-1].addWidget(self.banditcheckbox)
        layoutR[-1].addWidget(self.banditdropdown)

        layoutRight.addStretch()

        if screenexits:
            layoutRight.addWidget(QHorizLine())
            _layoutRnewline()
            layoutR[-1].addWidget(self.labels["newscreen"])
            layoutR[-1].addWidget(self.lineeditbytes["newscreen"])
            _layoutRnewline()
            layoutR[-1].addWidget(self.buttons["Add"])
            layoutR[-1].addWidget(self.buttons["Move"])
            layoutR[-1].addWidget(self.buttons["Duplicate"])

        layoutRight.addWidget(QHorizLine())
        _layoutRnewline()
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
        self.lineeditbytes[i].setValue(value)
        if i == 0:
            if self.entrancelayout == "levelmain":
                return
            # swap normal/Bandit layout based on sublevel ID
            elif value > SMA3.Constants.maxsublevel:
                self.setEntranceLayout("bandit")
                self.banditcheckbox.setChecked(True)
                self.banditdropdown.setCurrentIndex(self.banditIDlookup[value])
                self.lineeditbytes[0].setText(format(value, "02X"))
            else:
                self.setEntranceLayout("normal")
                self.banditcheckbox.setChecked(False)
        elif i == 3:
            if value >= len(self.animdropdown):
                value = -1
            self.animdropdown.setCurrentIndex(value)
        elif i in (1, 2):
            # update dest screen number
            self.labels["destscreen"].setText(
                "Screen: " + format(SMA3.coordstoscreen(*self.entr[1:3]), "02X"))

    def setentrancebyte(self, i, value):
        self.entr[i] = value
        # ensure lineedit and dropdown/destscreen are synchronized
        self.loadentrancebyte(i, value)
        self.reloadsidebar()

    def addentrancerow(self, prefix, entr):
        "Add a new row to the entrance list, with the provided prefix."
        text = [prefix, ":"]
        text += (format(i, "02X") for i in entr[0:3])
        self.entrlistwidget.addItem(" ".join(text))

    def reloadsidebar(self):
        "Overridden by subclasses."
        raise NotImplementedError

    def setEntranceLayout(self, key):
        """Enable/disable widgets to account for the minor differences in
        entrance formats."""

        self.entrancelayout = key

        for widget in (
                self.labels[3], self.lineeditbytes[3], self.animdropdown,
                self.labels["bandit"], self.banditcheckbox, self.banditdropdown,
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
                       self.labels["bandit"], self.banditcheckbox):
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
            entr = SMA3.Entrance.fromhex(clipboardtext)
        except ValueError:
            QSimpleDialog(self, title="Error", text="".join((
                         'Clipboard contents "', clipboardtext[:100],
                         '" could not be parsed as entrance data.'
                         ))).exec()
        else:
            if self.entrancelayout == "levelmain":
                # don't change byte 3 of main entrances
                entr[3] = self.entr[3]
                # don't allow main entrances to use Bandit minigame IDs
                if entr[0] > SMA3.Constants.maxsublevel:
                    entr[0] = SMA3.Constants.maxsublevel
            for i in range(6):
                self.setentrancebyte(i, entr[i])
            self.loadentrance(entr)

class QDialogSMA3LevelEntrances(QDialogSMA3Entrances):
    "Dialog for editing the game's level main/midway entrances."
    def __init__(self, *args, maxmidpoints=4):
        super().__init__(*args)
        
        self.setWindowTitle("Edit Level Main/Midway Entrances")

        self.lineeditbytes["entrlist"].setValue(0)
        self.lineeditbytes["entrlist"].editingFinished.connect(
            self.levelnumcallback)
        self.buttons["Confirm"].setText("Save")
        for key, slot in (("+", self.addmidway),
                          ("-", self.delmidway)):
            self.buttons[key].clicked.connect(slot)

        self.mainentrances = []
        self.midwayentrances = []
        self.levelID = 0
        self.maxmidpoints = maxmidpoints

    def open(self):
        if Adv3Attr.midway6byte:
            midwaylen = 6
        else:
            midwaylen = 4
        self.mainentrances, self.midwayentrances = SMA3.importlevelentrances(
            Adv3Attr.filepath, maxmidpoints=self.maxmidpoints,
            midwaylen=midwaylen)

##        import itertools
##        print([hex(i) for i in itertools.chain(
##            self.mainentrances.datablock, self.midwayentrances.datablock)])
        self.reloadsidebar()
        super().open()

    def accept(self):
        "Save level entrances to ROM."

        if not Adv3Save.firstsavewarning(): return

        # determine 4 or 6-byte midways
        if Adv3Attr.midway6byte:
            midwaylen = 6
        else:
            midwaylen = 4
            for level in self.midwayentrances:
                for entr in level:
                    if entr[4] or entr[5]:
                        applied = Adv3Patch.applymidway6byte()
                        if not applied:
                            return
                        midwaylen = 6
                        break
                if midwaylen == 6: break

        # generate bytearrays
        bytesmain = bytearray()
        offsetsmain = []
        for entr in self.mainentrances:
            if entr:
                offsetsmain.append(len(bytesmain))
                bytesmain += entr
            else:
                offsetsmain.append(None)
        bytesmain += b"\xFF\xFF\xFF\xFF"

        bytesmidway = bytearray()
        offsetsmidway = []
        for level in self.midwayentrances:
            if level:
                offsetsmidway.append(len(bytesmidway))
                for entr in level:
                    bytesmidway += entr[0:midwaylen]
            else:
                offsetsmidway.append(None)
        bytesmidway += b"\xFF\xFF\xFF\xFF"

        startptrs = []
        for entrances, data, offsets, ptrtoptrtable in (
                (self.mainentrances, bytesmain, offsetsmain,
                 SMA3.Pointers.entrancemainptrs),
                (self.midwayentrances, bytesmidway, offsetsmidway,
                 (SMA3.Pointers.entrancemidwayptrs,) )
                ):

            # calculate number of pointers to save
            oldlen = len(entrances.ptrs)
            newlen = len(offsets)
            if len(offsets) > oldlen:
                for ptr in reversed(offsets[oldlen:]):
                    if ptr != None:
                        break
                    newlen -= 1
            offsets = offsets[0:newlen]

            # save entrances
            GBA.erasedata(Adv3Attr.filepath, *entrances.datablock)
            startptr = Adv3Save.saveDataToROM(data, ())
            startptrs.append(startptr)

            # calculate pointers
            ptrs = GBA.PointerTable()
            for offset in offsets:
                if offset is None:
                    ptrs.append(1)
                else:
                    ptrs.append(startptr + offset)

            # save entrance pointer table
            if newlen != oldlen:
                ptrs.endmarker = True
                GBA.erasedata(Adv3Attr.filepath, *entrances.ptrs.datablock)
                newtableptr = Adv3Save.saveDataToROM(
                    bytes(ptrs), SMA3.Pointers.entrancemainptrs)
            else:
                ptrs.endmarker = False
                GBA.overwritedata(
                    Adv3Attr.filepath, bytes(ptrs),
                    GBA.readptr(Adv3Attr.filepath, ptrtoptrtable[0]))

        statustext = ("Saved main entrances to {mainptr}, "
                      "midway entrances to {midwayptr}.")
        AdvSettings.editor.statusbar.setActionText(statustext.format(
            mainptr=format(startptrs[0], "08X"),
            midwayptr=format(startptrs[1], "08X")))

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

        levelnumstr = SMA3.levelnumber(levelID, short=True)

        # add main/midway entrances to list
        self.addentrancerow("main", self.mainentrances[levelID])
        for i, entr in enumerate(self.midwayentrances[levelID]):
            self.addentrancerow(str(i), entr)

        self.buttons["+"].setEnabled(
            len(self.midwayentrances[levelID]) < self.maxmidpoints)
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
        elif row >= 0:
            self.setEntranceLayout("normal")
            self.loadentrance(self.midwayentrances[self.levelID][row-1])

    # button functions

    def addmidway(self):
        self.midwayentrances[self.levelID].append(SMA3.Entrance())
        self.reloadsidebar()
        self.buttons["-"].setEnabled(True)
        if len(self.midwayentrances[self.levelID]) >= self.maxmidpoints:
            self.buttons["+"].setDisabled(True)
            self.buttons["-"].setFocus()
        
    def delmidway(self):
        self.midwayentrances[self.levelID].pop()
        self.reloadsidebar()
        self.buttons["+"].setEnabled(True)
        if not self.midwayentrances[self.levelID]:
            self.buttons["-"].setDisabled(True)
            self.buttons["+"].setFocus()

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
        self.labels["entrlist"].setText(
            "Sublevel " + format(Adv3Attr.sublevel.ID, "02X"))
        super().open()

    def accept(self):
        if Adv3Attr.sublevel.exits != self.exits:
            Adv3Attr.sublevel.exits = copy.deepcopy(self.exits)
            AdvSettings.editor.statusbar.setActionText("Screen exits updated.")
            AdvSettings.editor.statusbar.updateByteText()

            AdvSettings.editor.reload("Screen Exits")
        super().accept()

    def reloadsidebar(self):
        "Load lines of text representing each screen exit to the sidebar."
        self.entrlistwidget.clear()
        for screen in sorted(self.exits.keys()):
            self.addentrancerow(format(screen, "02X"), self.exits[screen])
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
