"Functions for validating and loading ROMs."

# standard library imports
import os, zlib

# import from other files
from AdvEditor import AdvSettings, Adv3Sublevel
from AdvGUI.Dialogs import *
from AdvGUI.GeneralQt import *

oldglobals = frozenset(globals())

def exists():
    "Check if the ROM file is still in the expected location."
    if not os.path.exists(Adv3Attr.filepath):
        QSimpleDialog(AdvWindow.editor, title="Error",
            text="Could not access ROM file:\n" + Adv3Attr.filepath).exec()
        return False
    return True

def opendialog():
    if Adv3Attr.filepath:
        if not Adv3Sublevel.savecheck():
            return
        directory = os.path.dirname(Adv3Attr.filepath)
    else:
        directory = AdvMetadata.appdir

    filepath, _ = QFileDialog.getOpenFileName(
        AdvWindow.editor, caption="Open ROM", directory=directory,
        filter="GBA ROM Image (*.gba)")
    if filepath:
        loadROM(filepath)
        return filepath

def loadROM(filepath):
    """Validate the given filepath as a ROM image of SMA3 (U), and if
    successful, load the ROM."""

    if not os.path.exists(filepath):
        QSimpleDialog(AdvWindow.editor, title="Error", text="".join(
            ("Could not load file:\n", filepath, 
             "\nFile not found."))
                      ).exec()
        return False

    size = os.path.getsize(filepath)

    if size < 0x400000:
        QDialogROMValidation(AdvWindow.editor, size=size, override=False).exec()
        return False

    savedmetadata = GBA.importdata(filepath, 0x083FFFE0, 0x20)
    if savedmetadata == bytes(0x20):
        Adv3Attr.savedversion = None
    else:
        # metadata region is not blank: validate
        if savedmetadata[0:8] != b"Advynia3":
            QSimpleDialog(AdvWindow.editor, title="Error", text="".join(
                ("Could not load file:\n", filepath, 
                 "\nFile does not appear to be a valid SMA3 (U) ROM image."))
                          ).exec()
            return False
        versionlist = []
        for i in range(8, 0xE, 2):
            versionlist.append(int.from_bytes(savedmetadata[i:i+2], "little"))
        Adv3Attr.savedversion = AdvMetadata.ProgramVersion(versionlist)

        # check for higher version
        if Adv3Attr.savedversion > AdvMetadata.version:
            cancelflag = QDialogROMValidation(
                AdvWindow.editor, size=size, savedversion=Adv3Attr.savedversion).exec()
            if cancelflag:
                return False

        _loadROMvalidated(filepath)
        return True

    # if no Advynia metadata, try to validate as clean ROM
    if size == 0x400000:
        with open(filepath, "rb") as f:
            crc32 = zlib.crc32(f.read())
        if crc32 != SMA3.Constants.crc32:
            # incorrect checksum
            internalID = GBA.importdata(filepath, 0x080000AC, 4)
            internalID = str(internalID, encoding="ASCII")
            if internalID == "A3AJ" or internalID == "A3AP":
                # If it's another region of SMA3, Advynia may successfully
                # load a sublevel then crash on graphics load, so they need
                # to be filtered manually.
                QSimpleDialog(AdvWindow.editor, title="Error", text="".join(
                    ("Could not load file:\n", filepath, 
                     "\nFile appears to be a ROM image of SMA3 ",
                     {"A3AJ":"(J)", "A3AP":"(E)"}[internalID],
                     ". Advynia only supports the (U) version.",
                     ))).exec()
                return False
            else:
                cancelflag = QDialogROMValidation(
                    AdvWindow.editor, crc32=crc32).exec()
                if cancelflag:
                    return False
    else:
        # size > 0x400000: incorrect file size
        cancelflag = QDialogROMValidation(AdvWindow.editor, size=size).exec()
        if cancelflag:
            return False

    try:
        # Try to load a sublevel. If the ROM isn't SMA3, this will usually
        # produce an invalid pointer, but might result in other errors.
        sublevel = SMA3.Sublevel.importbyID(filepath, 0)
        sublevel = SMA3.Sublevel.importbyID(filepath, 1)
    except Exception:
        internalname = str(
            GBA.readinternalname(filepath)[0:0xC], encoding="ASCII")
        if internalname == "SUPER MARIOC":
            QSimpleDialog(AdvWindow.editor, title="Error", text="".join(
                ("Could not load file:\n", filepath, 
                 "\nFile appears to be SMA3 (U), but SMA3 sublevel data "
                 "was not found or could not be parsed."))
                         ).exec()
        else:
            QSimpleDialog(AdvWindow.editor, title="Error", text="".join(
                ("Could not load file:\n", filepath, 
                 "\nFile does not appear to be a valid SMA3 (U) ROM image."))
                         ).exec()
        return False
    else:
        # Validation successful, so load the ROM
        _loadROMvalidated(filepath)
        return True

def _loadROMvalidated(filepath):
    Adv3Attr.filepath = filepath
    Adv3Attr.filename = os.path.basename(filepath)
    AdvSettings._ROM_recent_add(filepath)
    AdvWindow.editor.updaterecentROMmenu()
    Adv3Attr.tilemapL1_8x8 = SMA3.importL1_8x8tilemaps(Adv3Attr.filepath)
    Adv3Patch.detectpatches()
    AdvWindow.editor.updatepatchlayouts()
    if Adv3Attr.sublevel.ID:
        Adv3Sublevel.loadsublevelID(Adv3Attr.sublevel.ID)
    else:
        Adv3Sublevel.loadsublevelID(0)
    AdvWindow.statusbar.setActionText("Opened ROM: " + filepath)

# import only newly defined functions using import *
__all__ = [name for name in (frozenset(globals()) - oldglobals)
           if name[0] != "_"]
