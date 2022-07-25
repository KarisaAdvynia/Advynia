# import from other files
from AdvGame import SMA3
from .QtGeneral import *

# globals
import Adv3Attr

class QSMA3MessageEditor(QDialog):
    """Dialog for editing standard messages."""
    def __init__(self, *args):
        super().__init__(*args)

        self.setWindowTitle("Message Editor")

        self.textdata = []

        # init widgets

        messagescene = QGraphicsScene(0, 0, 0x80, 0x80)
        messageview = QGraphicsView(messagescene)
        messageview.setFixedWidth(0x80)
        messageview.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.textedit = QTextEdit()
        self.textedit.setAcceptRichText(False)

        confirmbutton = QPushButton("OK")
        confirmbutton.clicked.connect(self.accept)
        confirmbutton.setDefault(True)
        cancelbutton = QPushButton("Cancel")
        cancelbutton.clicked.connect(self.reject)

        # init layout

        layoutMain = QVBoxLayout()
        self.setLayout(layoutMain)

        layoutH = QHBoxLayout()
        layoutMain.addLayout(layoutH)

        layoutH.addWidget(messageview)
        layoutH.addWidget(self.textedit)

##        layoutMain.addWidget(QHorizLine())

        layoutButtons = QHBoxLayout()
        layoutMain.addLayout(layoutButtons)
        layoutButtons.addStretch()
        layoutButtons.addWidget(confirmbutton)
        layoutButtons.addWidget(cancelbutton)

    def open(self):
        self.loadMessage(0x23)
        super().open()

    def loadMessage(self, messageID):
        self.textdata = SMA3.importmessage(Adv3Attr.filepath, messageID)
        self.textedit.setPlainText(SMA3.printabletext(self.textdata))

    def accept(self):
        NotImplemented
        super().accept()

