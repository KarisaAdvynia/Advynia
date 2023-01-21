"""Advynia Recovery
Creates and manages the Advynia/recovery folder."""

# standard library imports
import os, shutil

# import from other files
import AdvMetadata, AdvEditor.Export, AdvFile
from AdvEditor import Adv3Attr, Adv3Sublevel

def _recoverydir(currentROMdir=True):
    """Return the recovery directory, if currentROMdir=False, or a
    subdirectory named after the current ROM, if currentROMdir=True.
    If the directory doesn't exist, create it."""
    dirs = [AdvMetadata.appdir, "recovery"]
    if currentROMdir:
        dirs.append(os.path.splitext(Adv3Attr.filename)[0])
    dirpath = os.path.join(*dirs)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath

def backupROM():
    "Copy the current ROM to the recovery folder."
    shutil.copy2(
        Adv3Attr.filepath,
        os.path.join(_recoverydir(), Adv3Attr.filename))

def restoreROM():
    """Restore the current ROM from the recovery folder. Should be called
    if an exception is encountered during saving."""
    recoverypath = os.path.join(_recoverydir(), Adv3Attr.filename)
    if os.path.exists(recoverypath):
        shutil.copy2(
            os.path.join(_recoverydir(), Adv3Attr.filename),
            Adv3Attr.filepath)

def _recoveryexport(a3l):
    a3l.exporttofile(os.path.join(
        _recoverydir(), a3l.defaultfilename(Adv3Attr.filename)))

def exportsublevel():
    "Export the current sublevel to the recovery folder."
    _recoveryexport(AdvEditor.Export.sublevel_to_a3l())

def exportentrances(*entrances):
    "Export the specified level entrances to the recovery folder."
    _recoveryexport(AdvFile.A3LFileData.fromentrances(*entrances))

def exportmessages(messages):
    "Export the specified messages to the recovery folder."
    _recoveryexport(AdvFile.A3LFileData.fromtextdata(messages))
