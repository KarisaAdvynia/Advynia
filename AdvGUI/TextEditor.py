"SMA3 Text Editor"

# standard library imports
import copy, itertools

# import from other files
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr, Adv3Save, Adv3Visual
import AdvEditor, AdvFile
from AdvEditor.Format import pluralize
from AdvGame import GBA, SMA3
from .Dialogs import QDialogFileError
from .GeneralQt import *
from . import QtAdvFunc

class QSMA3TextEditor(QDialogBase):
    "Dialog for editing SMA3 text."
    def __init__(self, *args):
        super().__init__(*args)

        self.setWindowTitle("Edit Messages")

        self.font = None
        self.fonttype = "main"
        self.texttypeschanged = []
        self.textdata = None
        self.messages = {}
        self.msgID = 0
        self._texttype = "Level name"
        self._charID = None
        self._textlistformatstr = "02X"

        # init widgets

        def _gentexttypefunc(newtexttype):
            def _tempfunc():
                self.texttype = newtexttype
            return _tempfunc

        msgtypebuttons = []
        for key, tooltip in SMA3.Constants.msgtypes:
            button = QRadioButton(key)
            button.setToolTip(key + "<br>" + tooltip)
            button.clicked.connect(_gentexttypefunc(key))
            msgtypebuttons.append(button)
            self.messages[key] = []
        msgtypebuttons[0].setChecked(True)

        pushbuttons = {}
        for key, text, tooltip, action in (
                ("Command", "Add &Command", None,
                 lambda : QDialogAddTextCommand(self, self.texttype).open()),
                ("Export", "&Export", "Export messages to file",
                 self.exportmessages),
                ("Import", "&Import", "Import messages from file",
                 self.importmessages_dialog),
                ):
            button = QPushButton(text)
            if tooltip: button.setToolTip(tooltip)
            button.clicked.connect(action)
            pushbuttons[key] = button

        self.textlistwidget = QListWidgetResized(
            width=QtAdvFunc.basewidth(QListWidget()) * 50,
            height=100)
        self.textlistwidget.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.textlistwidget.currentRowChanged.connect(self.textselectcallback)

        self.fontscene = QGraphicsScene(0, 0, 0x80, 0x100)
        fontview = QGraphicsViewTransparent(self.fontscene)
        fontview.setSizePolicy(QSizePolicy())
        fontview.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        fontview.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        fontview.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.fontitem = QSMA3FontGraphicsItem(self)
        self.fontscene.addItem(self.fontitem)

        self.messagescene = QGraphicsScene(0, 0, 0x80, 0x80)
        self.messageview = QGraphicsView(self.messagescene)
        self.messageview.setSizePolicy(QSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred))
        self.messageview.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.messageview.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.messageview.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messageview.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.messagepixmapitem = QGraphicsPixmapItem()
        self.messagescene.addItem(self.messagepixmapitem)

        self.charinfo = QLabel()

        self.messagelabel = QLabelToolTip()
        self.messagelabel.setSizePolicy(QSPIgnoreWidth)
        self.linkinfo = QLabelToolTip()
        self.linkinfo.setSizePolicy(QSPIgnoreWidth)
        self.linkbutton = QPushButton("&Link")
        self.linkbutton.setFixedWidth(QtAdvFunc.basewidth(self.linkbutton) * 12)
        self.linkbutton.clicked.connect(self.linkaction)

        self.textedit = QMessageTextEdit()
        self.textedit.textChanged.connect(self.texteditcallback)

        self.simplifiedbox = QCheckBox("&Simplified")
        self.simplifiedbox.setToolTip("""
Simplified Mode<br>
<i>When enabled</i>: Line breaks are interpreted as common commands. 
Temporarily disabled if a message doesn't fit the vanilla command pattern.<br>
<i>When disabled</i>: All commands must be input manually; line breaks are 
ignored.
""")
        self.simplifiedbox.clicked.connect(self.simplifiedboxcallback)

        self.messagestats = QLabel()

        # init layout

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)
        layoutMain.addRow()

        layoutFontView = QVHBoxLayout()
        layoutMain[-1].addLayout(layoutFontView)
        layoutFontView.addWidget(QLabel("Characters"))
        layoutFontView.addWidget(fontview)
        layoutFontView.addWidget(self.charinfo)
        layoutFontView.addRow()
        layoutFontView[-1].addStretch()
        layoutFontView[-1].addWidget(pushbuttons["Command"])
        layoutFontView.addStretch()

        layoutMain[-1].addWidget(QVertLine())

        layoutVH = QVHBoxLayout()
        layoutMain[-1].addLayout(layoutVH, 1)
        layoutVH.addRow(stretch=2)

        layoutRadioButtons = QVBoxLayout()
        layoutRadioButtons.setSpacing(0)
        for button in msgtypebuttons:
            layoutRadioButtons.addWidget(button)
        layoutRadioButtons.addStretch()
        layoutVH[-1].addLayout(layoutRadioButtons)
        layoutVH[-1].addWidget(self.textlistwidget)

        layoutVH.addWidget(QHorizLine())
        layoutVH.addRow(stretch=3)
        layoutHalfRow = [QVBoxLayout(), QVHBoxLayout()]
        for layout in layoutHalfRow:
            layoutVH[-1].addLayout(layout)
        layoutHalfRow[0].addWidget(self.messagelabel)
        layoutHalfRow[0].addWidget(self.messageview, 1)
        layoutHalfRow1Top = QHBoxLayout()
        layoutHalfRow[1].addLayout(layoutHalfRow1Top)
        layoutHalfRow1Top.addWidget(self.linkbutton)
        layoutHalfRow1Top.addWidget(self.linkinfo, 1)
        layoutHalfRow1Top.addStretch()
        layoutHalfRow[1].addWidget(self.textedit)
        layoutHalfRow[1].addRow()
        layoutHalfRow[1][-1].addWidget(self.simplifiedbox)
        layoutHalfRow[1][-1].addStretch()
        layoutHalfRow[1][-1].addWidget(self.messagestats)

        layoutMain.addWidget(QHorizLine())

        layoutMain.addAcceptRow(self, "Save")
        layoutMain[-1].insertWidget(0, QLabel("Manage Messages:"))
        layoutMain[-1].insertWidget(1, pushbuttons["Export"])
        layoutMain[-1].insertWidget(2, pushbuttons["Import"])
        layoutMain[-1].insertWidget(3, QVertLine())

    # init/load methods

    def open(self):
        if not AdvEditor.ROM.exists(): return

        self.simplifiedbox.setChecked(AdvSettings.text_simplified)
        self.texttypeschanged.clear()
        self.loadfont()
        if self.charID is None: self.charID = 0

        # load message data for each type
        self.messages = SMA3.importalltext(Adv3Attr.filepath)

        self.reload()
        self.textedit.setFocus()
        super().open()

    def reload(self):
        # reload list widget for current type
        self.texttype = self.texttype

    def accept(self):
        if not self.texttypeschanged:
            # nothing to save
            super().accept()
            return
        if Adv3Save.savewrapper(Adv3Save.savemessages,
                self.messages, self.texttypeschanged):
            super().accept()

    def exportmessages(self):
        # get list of text types from user
        texttypes = []
        if not QDialogExportMessages(self, texttypes).exec() or not texttypes:
            return

        # prepare A3L data
        exportmessages = {}
        for texttype in texttypes:
            exportmessages[texttype] = self.messages[texttype]
        a3l = AdvFile.A3LFileData.fromtextdata(exportmessages)

        # get filepath from user
        defaultpath = os.path.join(
            os.path.dirname(Adv3Attr.filepath),
            a3l.defaultfilename(Adv3Attr.filename))
        filepath, _ = QFileDialog.getSaveFileName(
            AdvWindow.editor, caption="Export Messages", directory=defaultpath,
            filter=AdvFile.A3LFileData.longext)

        # export data
        if filepath:
            a3l.exporttofile(filepath)

            AdvWindow.statusbar.setActionText(
                "Exported messages to " + filepath)

    def importmessages_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            AdvWindow.editor, caption="Import Messages",
            directory=os.path.dirname(Adv3Attr.filepath),
            filter=AdvFile.A3LFileData.longext)
        if not filepath: return
        self.importmessages(filepath)

    def importmessages(self, filepath):
        a3l = AdvEditor.Export.importwrapper(
            AdvFile.A3LFileData.importfromfile, filepath)
        if not a3l: return
        if a3l.datatype() != "Text":
            QDialogFileError(AdvWindow.editor, filepath, text=(
                "File does not contain message data. "
                "Other .a3l file variants can be imported in the main editor."
                )).exec()
            return
        newmessages = AdvEditor.Export.importprocesswrapper(
            lambda filepath : a3l.totextdata(), filepath)
        if not newmessages: return

        if (AdvSettings.warn_import_messages and
                not QDialogImportMessages(self, newmessages.keys()).exec()):
            return

        for texttype in newmessages:
            self.messages[texttype] = newmessages[texttype]

        self.reload()

    @property
    def texttype(self):
        return self._texttype
    @texttype.setter
    def texttype(self, newtexttype):
        if self._texttype == newtexttype:
            # preserve current row only if reloading the same messages
            row = self.textlistwidget.currentRow()
            if row < 0: row = 0
        else:
            row = 0

        self._texttype = newtexttype

        self.textlistwidget.clear()
        messages = self.messages[newtexttype]
        if len(messages) == 1:
            self.textlistwidget.addItem(messages[0].shortstr())
        else:
            self._textlistformatstr = AdvEditor.Number.hexlenformatstr(len(messages) - 1)
            for msgID, text in enumerate(messages):
                self.textlistwidget.addItem("".join((
                    format(msgID, self._textlistformatstr), ": ", text.shortstr()
                    )))
        self.textlistwidget.setCurrentRow(row)

        self.simplifiedbox.setVisible(self._texttype == "Standard message")

    def loadfont(self, fonttype=None):
        if fonttype is None:
            # if opening the dialog, force reload the current font
            fonttype = self.fonttype
        elif fonttype == self.fonttype:
            # otherwise, don't reload if same as the current font
            return
        self.fonttype = fonttype
        self.font = SMA3.Font(Adv3Attr.filepath, fonttype)
        self.fontitem.setFont(self.font)

    def loadmessage(self, msgID):
        "Load a message of any type from the text data in memory."

        self.msgID = msgID
        textdata = self.messages[self.texttype][msgID]
        if not isinstance(textdata, SMA3.Text):
            raise TypeError(
                f"Attempted to load non-text data {repr(textdata)} as text data.")
        self.textdata = textdata

        self.loadmessagestr()

        if (self.texttype == "Credits" and
                msgID + 3 < len(self.messages[self.texttype])):
            # credits, except last 3 hardcoded messages, use different font
            self.loadfont("credits")
        else:
            self.loadfont("main")

        self.messagelabel.setText(self.messagelabeltext(msgID))
        self.updatelinkinfo()
        self.loadmessagefromtextdata()

    def loadmessagestr(self):
        if self.texttype == "Standard message":
            self.simplifiedbox.setEnabled(self.textdata.issimplified())

        if (self.texttype == "Standard message" and
                AdvSettings.text_simplified):
            textstr = self.textdata.simplifiedstr()
        else:
            textstr = str(self.textdata)
        with QSignalBlocker(self.textedit):
            self.textedit.setPlainText(textstr)

    def loadmessagefromtextdata(self):
        "Load the graphics of the current text data."
        pixmap = QPixmap.fromImage(QSMA3TextGraphics(self.textdata, self.font))
        self.messagepixmapitem.setPixmap(pixmap)

        # change scene size and view width to match message pixmap
        self.messagescene.setSceneRect(QRectF(pixmap.rect()))
        self.messageview.setFixedWidth(
            int(pixmap.width()) +
            self.messageview.verticalScrollBar().sizeHint().width() + 2)

        self.messagestats.setText(
            "{valid}{lines}, {bytes}".format(
            valid="" if self.textdata.valid else "<i>Error</i>, ",
            lines=pluralize(self.textdata.linecount(), "line", numformat="X"),
            bytes=pluralize(self.textdata.bytecount(), "byte", numformat="X"),
            ))

    def messagelabeltext(self, msgID):
        """Return a string description of the message ID, using the current
        texttype."""
        msgIDstr = format(msgID, self._textlistformatstr)
        match self.texttype:
            case "Level name":
                return "Level {msgID}: {levelnum}".format(
                    msgID=msgIDstr,
                    levelnum=SMA3.levelnumber(msgID),
                    )
            case "Standard message":
                return "Message {msgID}: {levelnum}-{parity}".format(
                        msgID=msgIDstr,
                        levelnum=SMA3.levelnumber(msgID // 4),
                        parity=msgID & 3,
                        )
            case "Ending":
                return "Ending message"
            case _:
                return self.texttype + " " + msgIDstr

    def updatelinkinfo(self):
        if self.texttype == "Ending":
            self.linkbutton.setText("&Link")
            self.linkbutton.setDisabled(True)
            self.linkinfo.clear()
        else:
            self.linkbutton.setEnabled(True)
            self.linkinfo.setText(
                "Linked: " +
                self.messages[self.texttype].linksetstr(self.msgID, "02X"))

            if self.messages[self.texttype].islinked(self.msgID):
                self.linkbutton.setText("Un&link")
            else:
                self.linkbutton.setText("&Link")

    def textselectcallback(self):
        row = self.textlistwidget.currentRow()
        if row >= 0:
            self.loadmessage(row)

    def simplifiedboxcallback(self, newvalue):
        AdvSettings.text_simplified = newvalue
        self.loadmessagestr()

    # editing current message

    def texteditcallback(self):
        includenewlines = (self.texttype == "Standard message" and
            AdvSettings.text_simplified and self.simplifiedbox.isEnabled())
        self.textdata.updatefromstr(
            self.textedit.toPlainText(), includenewlines=includenewlines)

        if self.textdata.valid:
            # update row in list widget
            shortstr = self.textdata.shortstr()
            try:
                linksets = self.messages[self.texttype].linksets
            except AttributeError:
                self.textlistwidget.currentItem().setText(shortstr)
            else:
                # update linked rows if any exist
                for msgID in linksets[self.msgID]:
                    listtext = "".join((
                        format(msgID, self._textlistformatstr), ": ", shortstr))
                    self.textlistwidget.item(msgID).setText(listtext)
        if self.texttype not in self.texttypeschanged:
            self.texttypeschanged.append(self.texttype)
        self.loadmessagefromtextdata()

    def linkaction(self):
        if self.messages[self.texttype].islinked(self.msgID):
            # unlink
            linked = False
            self.messages[self.texttype].unlinkitem(self.msgID)
        else:
            linked = True
            # open link dialog
            accepted = QDialogLinkMessage(
                self, self.messages[self.texttype], self.msgID).exec()
            if not accepted: return

        if self.texttype not in self.texttypeschanged:
            self.texttypeschanged.append(self.texttype)
        self.loadmessage(self.msgID)
        self.updatelinkinfo()

        if linked:
            # also update row in list widget
            listtext = "".join((
                format(self.msgID, self._textlistformatstr), ": ",
                self.textdata.shortstr()))
            self.textlistwidget.item(self.msgID).setText(listtext)

    # text inserting

    levelnamecommandstr = ("<i>Invalid</i>", "@{YY,XX}", "@{XX}")
    @property
    def charID(self):
        return self._charID
    @charID.setter
    def charID(self, charID):
        self._charID = charID

        if charID >= 0xFD and self.texttype == "Level name":
            charstr = self.levelnamecommandstr[charID - 0xFD]
        elif charID == 0xFF:
            charstr = "<i>Command</i>"
        else:
            charstr = str(SMA3.Text(charID))

        self.charinfo.setText(f"{charID:02X}: {charstr}")

    def insertchar(self):
        "Insert the currently hovered font character."
        if self.charID == 0xFF or (
                self.charID == 0xFE and self.texttype == "Level name"):
            # prompt for command
            QDialogAddTextCommand(self, self.texttype, self.charID).open()
        elif self.charID == 0xFD and self.texttype == "Level name":
            # don't insert end of data command
            return
        else:
            self.textedit.textCursor().insertText(str(SMA3.Text(self.charID)))
            self.textedit.setFocus()

    def insertcommand(self, commandID):
        """Insert the string representation of a text command, based on the
        command ID and current text type.
        If the command takes parameters, they default to 0."""
        command = SMA3.TextCommand()
        match self.texttype:
            case "Level name":
                command.charID = commandID
                command.params = bytes(0x100 - commandID)
            case "File select":
                command.params = bytes(2)
            case _:
                command.params = bytearray([commandID])
                if commandID == 0x60 and self.texttype == "Standard message":
                    command.params += b"\x00\x00\x00\x80\x30\x00\x10"
                elif self.texttype == "Credits" or (
                        self.texttype == "Story intro" and
                        commandID not in (0x04, 0x31)):
                    command.params.append(0)
        self.textedit.textCursor().insertText(str(command))
        self.textedit.setFocus()

class QSMA3TextGraphics(QImage):
    "QImage containing the graphics of an SMA3 message."
    def __init__(self, textdata: SMA3.Text, font: SMA3.Font,
                 colortable=(0xFF000000, 0xFFFFFFFF)):
        width, height = textdata.size()
        super().__init__(width, height, self.Format.Format_Indexed8)

        self.setColorTable(colortable)
        self.fill(0)

        pixelarray = self.bits().asarray(width*height)
        startX = 0
        startY = 0
        scrollY = 0
        scaleX = 1
        scaleY = 1
        savedscale = None
        charYoffset = 0
        if textdata.texttype == "Standard message":
            charYoffset = 3

        for char in textdata:
            if isinstance(char, SMA3.TextCommand):
                match textdata.texttype:
                    case "Standard message":
                        commandID = char.params[0]
                        if 5 <= commandID <= 8:
                            # start non-buffered line
                            startX = 0
                            startY = (commandID - 5) << 4
                        elif commandID == 0xE:
                            # start buffered line
                            startX = 0
                            startY = 0x40
                            # erase line
                            e = (scrollY + 0x40) * width
                            for i in range(e, min(e + 0x10*width, width*height)):
                                pixelarray[i] = 0
                        elif 0x11 <= commandID <= 0x14:
                            # scroll message
                            scrollY += (commandID & 0xF) * char.repcount
                        elif 1 <= commandID <= 4:
                            # erase line
                            e = (scrollY + (commandID-1)*0x10) * width
                            for i in range(e, min(e + 0x10*width, width*height)):
                                pixelarray[i] = 0
                        elif 0x30 <= commandID <= 0x3B:
                            # change scale
                            newscaleX, newscaleY = self.scalecommands[
                                commandID & 0xF]
                            if newscaleX: scaleX = newscaleX
                            if newscaleY: scaleY = newscaleY
                        elif 0x3D <= commandID <= 0x3F:
                            # display life count digits (as 999)
                            char = 0xA9
                        elif commandID == 0x60:
                            # large image
                            self.displayimage(pixelarray, width, char, scrollY)

                    case "Level name":
                        if char.charID == 0xFE:
                            # set position
                            startY, startX = char.params
                        elif char.charID == 0xFF:
                            # set X only
                            startX = char.params[0]

                    case "File select":
                        # set position
                        startX = char.params[0]
                        startY = char.params[1] - 0x10

                    case "Ending":
                        # restart line
                        startX = 0
                        if char.params[0] in (0x09, 0x0A):
                            # new line
                            startY += 0x10 * char.repcount

                    case "Story intro" | "Credits":
                        commandID = char.params[0]
                        if commandID == 0x02:
                            # set Y
                            startY = char.params[1] * 2
                        elif commandID == 0x03:
                            # set X
                            startX = char.params[1]
                        elif commandID == 0x00:
                            # single 1x scale character
                            char = char.params[1]
                            savedscale = scaleX, scaleY
                            scaleX = 1
                            scaleY = 1
                        elif textdata.texttype == "Story intro":
                            if commandID == 0x05:
                                # single 2x scale character
                                char = char.params[1]
                                savedscale = scaleX, scaleY
                                scaleX = 2
                                scaleY = 2
                            elif commandID in (0x04, 0x31):
                                # 2x scale for rest of message
                                scaleX = 2
                                scaleY = 2

                if isinstance(char, SMA3.TextCommand):
                    # if command has not been replaced by a character
                    continue

            # text character
            charwidth = min(font.widths[char], 8)
            if scaleX == 1 and scaleY == 1:
                # unscaled text character
                for byte, y in zip(font[char], itertools.count(
                        scrollY + startY + charYoffset)):
                    if not (byte and 0 <= y < height):
                        continue
                    for bitindex, x in zip(range(charwidth),
                                           itertools.count(startX)):
                        if x >= width:
                            continue
                        if byte & 0x80>>bitindex:
                            pixelarray[y*width + x] = 1
                startX = (startX + font.widths[char]) & 0xFF

            else:
                # scaled text character
                # This code could handle unscaled, but it runs so rarely, it's
                #  copied to avoid extra calculations. In-game also does this.
                for byte, y in zip(font[char], itertools.count(
                        scrollY + startY + charYoffset, scaleY)):
                    if not (byte and 0 <= y < height):
                        continue
                    for bitindex, x in zip(range(charwidth),
                                           itertools.count(startX, scaleX)):
                        if x >= width:
                            continue
                        if byte & 0x80>>bitindex:
                            for pixelY, pixelX in itertools.product(
                                    range(y, min(y+scaleY, height)),
                                    range(x, min(x+scaleX, width))):
                                pixelarray[pixelY*width + pixelX] = 1
                startX = (startX + font.widths[char]*scaleX) & 0xFF

            if savedscale is not None:
                scaleX, scaleY = savedscale
                savedscale = None

    scalecommands = (
        (1,1), (2,2), (3,3), (4,4),
        (None,1), (None,2), (None,3), (None,4),
        (1,None), (2,None), (3,None), (4,None),
        )

    @staticmethod
    def displayimage(pixelarray, messagewidth, command, scrollY):
        "Display a standard message large image."
        # interpret commands
        offset = ((int.from_bytes(command.params[2:4], "little") << 4)
                       + (command.params[1] >> 3)) & 0xFFFF
        startX = command.params[6]
        startY = command.params[7] + scrollY
        imagetilewidth = (command.params[4] + 7) >> 3
        imageheight = min(command.params[5], 0x50 - startY)
        if AdvSettings.fix_text_imageoffbyone:
            offsetXperbyte = 8
        else:
            # account for in-game off-by-one error
            startX += 8
            offsetXperbyte = 7

        # load image data
        with GBA.Open(Adv3Attr.filepath, "rb") as f:
            ptr = f.readptr(SMA3.Pointers.messageimages) + offset
            f.seek(ptr)
            rawimage = f.read(imageheight*0x10 + max(imagetilewidth-0x10, 0))

        # set pixels
        for y in range(imageheight):
            for x in range(0, imagetilewidth):
                byte = rawimage[y*0x10 + x]
                for bitindex, offset in zip(
                        range(8), itertools.count((startY + y) * messagewidth +
                                                  startX + x*offsetXperbyte)):
                    if byte & 0x80>>bitindex:
                        pixelarray[offset] = 1

class QSMA3FontGraphicsItem(QGraphicsPixmapItem):
    "Pixmap item depicting all characters in an SMA3 font."
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setAcceptHoverEvents(True)
        self.setToolTip("Click to insert character")

    def hoverMoveEvent(self, event):
        x, y = int(event.scenePos().x() / 8), int(event.scenePos().y() / 0x10)
        self.window.charID = y<<4 | x

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.window.insertchar()

    def setFont(self, font):
        """Load the characters of the provided font.
        Not quite the same as QSMA3TextGraphics, due to different startX/Y
        and newline handling."""
        image = QImage(0x80, 0x100, QImage.Format.Format_Indexed8)
        image.setColorTable((0xFF000000, 0xFFFFFFFF))
        image.fill(0)

        pixelarray = image.bits().asarray(0x8000)
        for char in range(0x100):
            startY = char & 0xF0
            startX = (char & 0xF) << 3
            charwidth = min(font.widths[char], 8)
            for byte, y in zip(font[char], itertools.count(startY)):
                if not byte:
                    continue
                for bitindex, x in zip(range(charwidth),
                                       itertools.count(startX)):
                    if byte & 0x80>>bitindex:
                        pixelarray[y*0x80 + x] = 1

        self.setPixmap(QPixmap.fromImage(image))

class QMessageTextEdit(QPlainTextEdit):
    "Subclassed to change the default width, and allow tabbing out."
    def __init__(self):
        super().__init__()

        self.defaultwidth = QtAdvFunc.basewidth(self) * 50
        self.setTabChangesFocus(True)

    def sizeHint(self):
        return QSize(self.defaultwidth, 0x80)

class QDialogLinkMessage(QDialogBase):
    def __init__(self, parent, messages, msgID):
        super().__init__(parent)

        self.setWindowTitle("Link Message")

        self.messages = messages
        self.msgID = msgID

        # init widgets

        self.linkdestinput = QLineEditHex(maxvalue=len(messages)-1)
        self.linktext = QLabel()

        self.linkdestinput.editingFinished.connect(self.updatelinktext)
        self.linkdestinput.setValue(0)
        self.updatelinktext()

        # init layout

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addWidget(QLabel("Link message data with:".format(
            msgID=format(msgID, AdvEditor.Number.hexlenformatstr(
                self.linkdestinput.maxvalue)))))

        layoutMain.addRow()
        layoutMain[-1].addWidget(self.linkdestinput)
        layoutMain[-1].addWidget(self.linktext)
        layoutMain[-1].addStretch()

        layoutMain.addWidget(QLabel("This will overwrite the current message!"))

        layoutMain.addAcceptRow(self, "Link")

        layoutMain.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def accept(self):
        if self.msgID == self.linkdestinput.value:
            QSimpleDialog(self, wordwrap=False,
                text="Cannot link a message with itself.").exec()
            return
        self.messages.linkitem(self.msgID, self.linkdestinput.value)
        super().accept()

    def updatelinktext(self):
        self.linktext.setText(
            self.parent().messagelabeltext(self.linkdestinput.value))

class QDialogAddTextCommand(QDialogBase):
    def __init__(self, parent, texttype, char=None):
        super().__init__(parent)

        self.setWindowTitle("Add Command")
        
        if char is None:
            # default char if Add Command button was clicked
            char = 0xFE if texttype == "Level name" else 0xFF

        # init widgets

        self.commanddata = SMA3.Constants.msgcommands[texttype]
        self.commandlist = QListWidgetResized(
            width=QtAdvFunc.basewidth(QListWidget()) * 50,
            height=250 if len(self.commanddata) > 6 else 125)
        for num, desc in self.commanddata:
            if num is None:
                self.commandlist.addItem(desc)
            else:
                self.commandlist.addItem(f"{num:02X}: {desc}")

        if texttype == "Level name":
            self.commandlist.setCurrentRow(char & 1)
        else:
            self.commandlist.setCurrentRow(0)
        self.commandlist.itemDoubleClicked.connect(self.accept)

        # init layout

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addWidget(self.commandlist)

        layoutMain.addAcceptRow(self, "Add")

    def accept(self):
        try:
            commandID = self.commanddata[self.commandlist.currentRow()][0]
        except IndexError:
            return
        self.parent().insertcommand(commandID)
        super().accept()

class QDialogExportMessages(QDialogBase):
    def __init__(self, parent, texttypes):
        super().__init__(parent)

        self.setWindowTitle("Export Messages")

        self.texttypes = texttypes

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addWidget(QLabel("Message types to export:"))

        self.checkboxes = {}
        layoutCheckbox = QVBoxLayout()
        layoutMain.addLayout(layoutCheckbox)
        layoutCheckbox.setSpacing(0)
        for seq in SMA3.Constants.msgtypes:
            texttype = seq[0]
            checkbox = QCheckBox(texttype)
            checkbox.setChecked(True)
            layoutCheckbox.addWidget(checkbox)
            self.checkboxes[texttype] = checkbox
        layoutMain.addAcceptRow(self, "Export")

    def accept(self):
        for key, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                self.texttypes.append(key)
        if self.texttypes:
            super().accept()
        else:
            QSimpleDialog(self, wordwrap=False,
                text="Export file must include at least one message type."
                ).exec()

class QDialogImportMessages(QDialogBase):
    def __init__(self, parent, newtexttypes):
        super().__init__(parent)

        self.setWindowTitle("Import Messages")

        # init widgets

        label = QLabel(
            "Replace these message types?\n"
            "Messages can be viewed before saving.\n\n" +
            "\n".join(newtexttypes)
            )
        self.checkbox = QCheckBox("Don't show this message again")

        # init layout

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addWidget(label)
        layoutMain.addWidget(self.checkbox)
        layoutMain.addAcceptRow(self, "Load")

    def accept(self):
        if self.checkbox.isChecked():
            setattr(AdvSettings, "warn_import_messages", False)
        super().accept()
