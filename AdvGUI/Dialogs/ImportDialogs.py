# import from other files
from AdvEditor import Adv3Attr, Adv3Patch, Adv3Save
from AdvEditor.Format import pluralize
from AdvGame import SMA3
from AdvGUI.GeneralQt import *

class QDialogSMA3ImportMultiple(QDialogBase):
    """Dialog for displaying info about importing multiple files, and progress
    during importing."""
    def __init__(self, parent, text, datatosave):
        super().__init__(parent)

        self.datatosave = datatosave

        self.setWindowTitle("Import Multiple A3Ls")
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        # init widgets

        self.label = QLabel(text)
        self.label.setWordWrap(True)

        # init layout

        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addWidget(self.label)
        layoutMain.addAcceptRow(self, "Import", addattr=True)

        layoutMain.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def accept(self):
        self.acceptbutton.setDisabled(True)
        self.rejectbutton.setDisabled(True)
        success = Adv3Save.savewrapper(
            self._importmultiple_save, *self.datatosave)
        if success:
            super().accept()
        else:
            self.acceptbutton.setEnabled(True)
            self.rejectbutton.setEnabled(True)

    def reject(self):
        """Overridden to prevent Esc from closing the dialog when importing is
        in progress."""
        if self.rejectbutton.isEnabled():
            super().reject()

    def _importmultiple_save(self,
            newsublevels, newentrances, allentrances, newmessages, newpatches):

        # apply patches, if any
        self._updateprogresstext("Applying patches...")
        Adv3Patch.applymultiplepatches(newpatches)

        # save sublevels, if any
        for sublevelID, sublevel in newsublevels.items():
            self._updateprogresstext(f"Saving sublevel {sublevelID:02X}...")
            Adv3Save.savesubleveltoROM(sublevel, sublevelID)

        # update and save entrances, if any
        if allentrances:
            self._updateprogresstext("Saving level entrances...")
            Adv3Save.saveentrances(*allentrances)
        elif newentrances:
            self._updateprogresstext("Saving level entrances...")
            oldmidwaylen = (6 if (Adv3Attr.midway6byte and
                            "midway6byte" not in newpatches) else 4)
            mainentrances, midwayentrances = SMA3.importlevelentrances(
                Adv3Attr.filepath, maxmidpoints=Adv3Attr.maxmidpoints,
                midwaylen=oldmidwaylen)
            for levelID, (main, midways) in newentrances.items():
                mainentrances[levelID] = main
                midwayentrances[levelID] = midways
            Adv3Save.saveentrances(mainentrances, midwayentrances,
                                   oldmidwaylen=oldmidwaylen)

        # update and save messages, if any
        if newmessages:
            self._updateprogresstext("Saving messages...")
            messages = SMA3.importalltext(Adv3Attr.filepath)
            messages.update(newmessages)
            Adv3Save.savemessages(messages)

        return True

    def _updateprogresstext(self, text):
        self.label.setText(text)
        self.label.updateGeometry()
        QCoreApplication.processEvents()

class QDialogImportGraphics(QDialogBase):
    def __init__(self, parent, allowoverride,
                 dirwarnings, exporttypes, sizewarnings, sizeerrors, nodata):
        super().__init__(parent)

        self.setWindowTitle("Import Graphics/Tilemaps")

        # calculate text and create layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        if nodata:
            if len(exporttypes) > len(dirwarnings):
                text = "All processed files are identical to ROM data."
            else:
                text = """No importable files were found. 
Did you export graphics/tilemaps first? Exported graphics can be modified in a 
GBA tile editor."""
            label = QLabel(text)
            label.setWordWrap(True)
            layoutMain.addWidget(label)

        else:
            if dirwarnings:
                text = [pluralize(len(dirwarnings), "export folder"),
                        " could not be found:<br>",
                        "<br>".join(seq[1] for seq in dirwarnings)]
                remainingtypes = set(exporttypes).difference(
                    seq[0] for seq in dirwarnings)
                if remainingtypes:
                    text += ["<br>", remainingtypes.pop().capitalize(),
                             " can still be imported."]
                layoutMain.addWidget(QLabel("".join(text)))

            if sizeerrors:
                if layoutMain.count(): layoutMain.addWidget(QHorizLine())
                label = QLabel(
                    """<i></i>File size for uncompressed data did not match. 
Data cannot be imported since it would risk ROM data corruption.""")
                label.setWordWrap(True)
                layoutMain.addWidget(label)
                layoutMain.addLayout(_LayoutSizeGrid(sizeerrors))

            if sizewarnings:
                if layoutMain.count(): layoutMain.addWidget(QHorizLine())
                label = QLabel(
                    """<i></i>File size for compressed data did not match. 
Data can be imported, but may overflow console RAM. Importing is not 
recommended unless you know exactly what you're doing.""")
                label.setWordWrap(True)
                layoutMain.addWidget(label)
                layoutMain.addLayout(_LayoutSizeGrid(sizewarnings))

        layoutMain.addStretch()

        if allowoverride:
            layoutMain.addAcceptRow(self, accepttext="Import", rejecttext="Cancel")
        else:
            layoutMain.addAcceptRow(self, rejecttext="OK", acceptbutton=False)

class _LayoutSizeGrid(QGridLayout):
    def __init__(self, sizetable):
        super().__init__()
        self.addWidget(QLabel("File name"), 0, 0)
        self.addWidget(QLabel("File size"), 0, 1, Qt.AlignmentFlag.AlignRight)
        self.addWidget(QLabel("Expected size"), 0, 2, Qt.AlignmentFlag.AlignRight)
        row = 1
        for filename, newlen, oldlen in sizetable:
            self.addWidget(QLabel(filename), row, 0)
            self.addWidget(QLabel(f"0x{newlen:X}"), row, 1, Qt.AlignmentFlag.AlignRight)
            self.addWidget(QLabel(f"0x{oldlen:X}"), row, 2, Qt.AlignmentFlag.AlignRight)
            row += 1
