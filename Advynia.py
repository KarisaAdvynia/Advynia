"""Advynia
Application file. Run this to launch Advynia.
Requires Python 3.10 or later.
Also requires PyQt6 installed; see AdvGUI.PyQtImport"""

# standard library imports
import sys

# import from other files
import AdvMetadata, AdvEditor.ROM
from AdvEditor import AdvSettings, Adv3Attr
from AdvGUI.PyQtImport import QApplication
from AdvGUI.Dialogs import QDialogAbout
from AdvGUI.MainWindow import QSMA3Editor

# Windows-specific: give unique taskbar icon
try:
    from ctypes import windll
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        AdvMetadata.appnamefull)
except ImportError:
    pass

# Run editor

if __name__ == "__main__":
    # print exceptions to console
    def _excepthook(cls, value, traceback):
        sys.__excepthook__(cls, value, traceback)
    sys.excepthook = _excepthook

    app = QApplication(sys.argv)

    # Mac-specific: don't use default Mac style
    if app.style().name() == "macos":
        app.setStyle("Fusion")

    # check if config is absent or from an older version
    try:
        newversion = AdvMetadata.version > AdvSettings.editor_lastversion
    except TypeError:
        newversion = True
    if newversion:
        if not AdvMetadata.ProgramVersion(AdvSettings.editor_lastversion):
            QDialogAbout().exec()
        AdvSettings.editor_lastversion = AdvMetadata.version[0:3]

    editor = QSMA3Editor()

    # load the most recent ROM, if enabled and possible
    if AdvSettings.ROM_autoload and AdvSettings.ROM_recent:
        AdvEditor.ROM.loadROM(AdvSettings.ROM_recent[0])

    # prompt for ROM on open
    while not Adv3Attr.filepath:
        confirm = AdvEditor.ROM.opendialog()
        if not confirm:
            ## open startup dialog?
            sys.exit()

    editor.show()

    sys.exit(app.exec())
