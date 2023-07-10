"""Main Window Status Bar"""

# import from other files
import AdvEditor
from AdvEditor import Adv3Attr
from AdvEditor.Format import pluralize
from .GeneralQt import *

class QMainEditorStatusBar(QStatusBar):
    def __init__(self, *args):
        super().__init__(*args)

        self.bytecount = 0
        self.screencount = 0

        self.setSizePolicy(QSPIgnoreWidth)

        # adjust text size based on label's font width
        font = self.font()
        defaultsize = font.pointSize()
        font.setPointSize(AdvEditor.Number.capvalue(
            round(defaultsize * 5 / QtAdvFunc.basewidth(self)), 5, defaultsize))
        self.setFont(font)

        # init widgets
        self.hovertext = QLabel()
        self.hovertext.setSizePolicy(QSPIgnoreWidth)
        self.addWidget(self.hovertext, 4)

        self.actiontext = QLabelToolTip()
        self.actiontext.setSizePolicy(QSPIgnoreWidth)
        self.addWidget(self.actiontext, 9)

        self.sizetext = QLabel()
        self.sizetext.setSizePolicy(QSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred))
        self.sizetext.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.addWidget(self.sizetext, 0)

    # updating method
    def setHoverText(self, x=None, y=None, tileID=None, obj=None, spr=None):
        if x is None or y is None:
            self.hovertext.clear()
            return

        text = [f"x{x:02X} y{y:02X}"]
        if tileID is not None:
            text.append(f" | {tileID:04X}")
        if spr is not None:
            text.append(f" | sprite {spr}")
        elif obj is not None:
            text.append(f" | object {obj}")
        self.hovertext.setText("".join(text))

    def setActionText(self, text=""):
        self.actiontext.setText(text)

    def updateByteText(self):
        self.setSizeText(newbytecount=Adv3Attr.sublevel.bytesize())

    def setSizeText(self, newbytecount=None, newscreencount=None):
        if newbytecount is not None: self.bytecount = newbytecount
        if newscreencount is not None: self.screencount = newscreencount

        self.sizetext.setText("".join((
            pluralize(self.screencount, "screen", numformat="02X"), ",  ",
            pluralize(self.bytecount, "byte", numformat="02X"))))
