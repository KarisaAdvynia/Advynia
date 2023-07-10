# standard library imports
import os
from functools import partial

# import from other files
from AdvGUI.GeneralQt import *
from AdvGame.GraphicsConvert import *

class QDialogGraphicsConvert(QDialogBase):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Convert to GBA Graphics")

        self.sourcefilepath = None
        self.convertfunc = convert_SNES_4bpp

        # init widgets
        browsebutton = QPushButton("Browse")
        browsebutton.clicked.connect(self.opengraphicsfile)

        self.sourcelabel = QLabel("No graphics file selected")

        formatlabel = QLabel("Source graphics format:")
        formatbuttons = []
        for func, text, tooltip in (
                (convert_SNES_4bpp, "SNES 4bpp",
                 "16-color SNES format, used for most SNES graphics."),
                (convert_SNESGB_2bpp, "SNES/GB 2bpp",
                 "4-color GB format. SNES also uses this, typically for layer 3."),
                ):
            button = QRadioButton(text)
            button.setToolTip("".join((text, "<br>", tooltip)))
            button.clicked.connect(partial(setattr, self, "convertfunc", func))
            formatbuttons.append(button)
        formatbuttons[0].setChecked(True)

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addRow()
        layoutMain[-1].addWidget(browsebutton)
        layoutMain[-1].addWidget(self.sourcelabel)
        layoutMain[-1].addStretch()

        layoutMain.addWidget(formatlabel)

        layoutRadioButtons = QVBoxLayout()
        layoutRadioButtons.setSpacing(0)
        for button in formatbuttons:
            layoutRadioButtons.addWidget(button)
        layoutMain.addLayout(layoutRadioButtons)

        layoutMain.addAcceptRow(self, accepttext="Convert", addattr=True)
        self.acceptbutton.setEnabled(False)

    def opengraphicsfile(self):
        filepath, _ = QFileDialog.getOpenFileName(
            AdvWindow.editor, caption="Select Graphics to Convert",
            directory=os.path.dirname(Adv3Attr.filepath),
            filter=";;".join((
                "Binary file (*.bin)",
                "All files (*.*)",
                )))
        if not filepath:
            return

        self.sourcelabel.setText(os.path.basename(filepath))
        self.sourcefilepath = filepath
        self.acceptbutton.setEnabled(True)
        self.acceptbutton.setFocus()

    def accept(self):
        try:
            sourcegraphics = open(self.sourcefilepath, "rb").read()
            newgraphics = self.convertfunc(sourcegraphics)

            savepath = os.path.splitext(self.sourcefilepath)[0] + "-gba.bin"

            filepath, _ = QFileDialog.getSaveFileName(
                AdvWindow.editor, caption="Save GBA Graphics",
                directory=savepath,
                filter="Binary file (*.bin)")
            if not filepath:
                return

            open(filepath, "wb").write(newgraphics)

            QSimpleDialog(self, title="Convert to GBA Graphics",
                text="Graphics successfully converted.", wordwrap=False).exec()

            super().accept()
        except Exception as err:
            # display error message
            if isinstance(err, FileNotFoundError):
                from AdvGUI.Dialogs import QDialogFileError
                QDialogFileError(self, self.sourcefilepath).exec()
                return
            if isinstance(err, GraphicsConvertError):
                text = err.args[0]
            else:
                import traceback
                text = ("An error occurred when converting graphics.\n\n" +
                        traceback.format_exc())
            QSimpleDialog(self, title="Error", text=text).exec()
