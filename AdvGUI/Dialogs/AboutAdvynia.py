# standard library imports
import platform

# import from other files
import AdvMetadata
from AdvGUI import PyQtImport
from AdvGUI.GeneralQt import *

class QDialogAbout(QDialogBase):
    "Dialog for describing the editor."

    def __init__(self, *args):
        super().__init__(*args)

        self.setWindowTitle("About Advynia")

        # init widgets
        advyniaicon = QLabel()
        advyniaicon.setPixmap(QPixmap(
            AdvMetadata.datapath("icon", "Advynia3.png")))
        advynianame = QLabel(f"<b>{AdvMetadata.appnamefull}</b>")
        advynianame.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction)
        advyniadesc = QLabel(
            f"(Python {platform.python_version()}, "
            f"PyQt {PyQtImport.PYQT_VERSION_STR})<hr><br>" + 
            AdvMetadata.aboutadvynia)
        advyniadesc.setTextFormat(Qt.TextFormat.RichText)
        advyniadesc.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction)
        advyniadesc.setWordWrap(True)

        licensebutton = QPushButton("License Info")
        licensebutton.clicked.connect(QDialogLicenseInfo(self).exec)
        confirmbutton = QPushButton("OK")
        confirmbutton.clicked.connect(self.accept)
        confirmbutton.setDefault(True)

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)

        layoutMain.addRow()
        layoutMain[-1].addWidget(advyniaicon)
        layoutMain[-1].addWidget(advynianame)
        layoutMain[-1].addStretch()

        layoutMain.addWidget(advyniadesc)

        layoutMain.addRow()
        layoutMain[-1].addStretch()
        layoutMain[-1].addWidget(licensebutton)
        layoutMain[-1].addWidget(confirmbutton)

    def open(self):
        self.setFocus()
        super().open()

class QDialogLicenseInfo(QDialogBase):
    "Dialog for displaying GPL license notes."

    gpltext = '''
This program is free software: you can redistribute it and/or modify 
it under the terms of the GNU General Public License as published by 
the Free Software Foundation, either version 3 of the License, or 
(at your option) any later version. 
<br><br>
This program is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
GNU General Public License for more details. 
<br><br>
You should have received a copy of the GNU General Public License along with 
this program.  If not, see 
<a href="https://www.gnu.org/licenses/">https://www.gnu.org/licenses/</a>'''

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("GNU General Public License")

        # init widgets
        label = QLabel(self.gpltext)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction)
        label.setWordWrap(True)

        # init layout
        layoutMain = QVHBoxLayout()
        self.setLayout(layoutMain)
        layoutMain.addWidget(label)
        layoutMain.addAcceptRow(self, rejectbutton=False)
