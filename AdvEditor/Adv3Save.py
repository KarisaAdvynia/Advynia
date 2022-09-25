"""Advynia SMA3 Saving
Saving/exporting-related functions that rely on other parts of Advynia,
as opposed to AdvGame, which does not rely on Advynia globals or Qt."""

# standard library imports
import os, traceback

# import from other files
import AdvMetadata
import AdvEditor
from AdvEditor import (AdvFile, AdvRecovery, AdvSettings, AdvWindow,
                       Adv3Attr, Adv3Visual)
from AdvGame import GBA, SMA3
from AdvGUI.GeneralQt import QSimpleDialog

# General save functions

def savewrapper(func, *args, **kwargs):
    """Wrapper for functions that modify the ROM. Handles restoring the ROM if
    an exception occurs.
    Also includes the unmodified ROM warning, and writing/updating Advynia
    metadata."""

    if not AdvEditor.ROM.exists(): return

    # display warning if the ROM is unmodified
    if not _firstsavewarning(): return

    # back up the ROM
    AdvRecovery.backupROM()

    # save Advynia metadata
    if Adv3Attr.savedversion is None or\
            Adv3Attr.savedversion < AdvMetadata.version:
        _saveAdvyniaMetadata()

    try:
        # run save function, and return its return value(s)
        return func(*args, **kwargs)
    except ROMFreespaceError:
        AdvRecovery.restoreROM()
    except Exception:
        AdvRecovery.restoreROM()
        text = ("An error occurred when saving. Your ROM has not been modified."
                "\n\n" + traceback.format_exc())
        traceback.print_exc()
        QSimpleDialog(AdvWindow.editor, title="Error",
                      text=text).exec()

def saveDataToROM(data, ptrstodata,
                  freespacestart=0x400000, freespaceend=0x2000000):
    """Wrapper for GBA.savedatatofreespace, for Advynia saving.

    Save variable-length data to the currently loaded ROM, and update the
    data's pointer(s). If insufficient space, expand the ROM size by 1 MiB
    at a time."""

    while True:
        newptr = GBA.savedatatofreespace(Adv3Attr.filepath, data, ptrstodata)
        if newptr:
            return newptr
        newsize = expandROM(0x100000)
        if newsize is None:
            raise ROMFreespaceError

class ROMFreespaceError(Exception):
    "Unique exception identifier, to be caught first in savewrapper."
    pass

def _firstsavewarning():
    "Display a warning if the ROM is unmodified."
    if AdvSettings.warn_save_first and Adv3Attr.savedversion is None:
        from AdvGUI.Dialogs import QDialogSaveValidation
        cancelflag = QDialogSaveValidation(AdvWindow.editor).exec()
        if cancelflag:
            return False
        # set version to 0.0.0 to prevent warning multiple times
        Adv3Attr.savedversion = AdvMetadata.ProgramVersion((0, 0, 0))
    return True

def _saveAdvyniaMetadata():
    "Save Advynia metadata to the last 0x20 bytes of the vanilla ROM size."
    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        f.seek(0x083FFFE0)
        metadata = bytearray(b"Advynia3")
        for num in AdvMetadata.version[0:3]:
            metadata += num.to_bytes(2, "little")
        f.write(metadata)
    Adv3Attr.savedversion = AdvMetadata.ProgramVersion(AdvMetadata.version[0:3])

def expandROM(bytecount):
    "Append a number of 00 bytes to the end of the ROM."

    size = os.path.getsize(Adv3Attr.filepath)
    if size >= 0x2000000:
        QSimpleDialog(AdvWindow.editor, title="Error",
            text="File is already at the GBA max ROM size, 32 MiB. "
                 "Data was not saved."
                      ).exec()
        return
    newsize = size + bytecount
    if newsize > 0x2000000:
        bytecount = 0x2000000 - size
        newsize = 0x2000000

    with open(Adv3Attr.filepath, "ab") as f:
        f.write(bytes(bytecount))  # fill with 00 bytes

    if not newsize % 0x100000:
        # integer MiB
        sizestr = str(newsize // 0x100000)
    else:
        # float MiB
        sizestr = format(newsize / 0x100000, ".2f")
    QSimpleDialog(AdvWindow.editor, title="Notice", text="".join(
        ("ROM expanded to ", sizestr, " MiB."))
                 ).exec()
    return newsize

# Sublevel save functions

def saveSublevelToROM(sublevel, sublevelID):
    "Save a sublevel to the ROM, with the specified ID."

    def _save():
        with GBA.Open(Adv3Attr.filepath, "r+b") as f:
            # erase old sublevel data
            oldsublevel = SMA3.Sublevel.importbyID(
                Adv3Attr.filepath, sublevelID)
            f.erasedata(*oldsublevel.datablocks["main"])
            f.erasedata(*oldsublevel.datablocks["sprite"])

            # save new sublevel data
            maindata = sublevel.exportmaindata()
            spritedata = sublevel.exportspritedata()

            mainptr2 = f.readptr(SMA3.Pointers.sublevelmainptrs) + 4*sublevelID
            spriteptr2 = f.readptr(SMA3.Pointers.sublevelspriteptrs) +\
                         4*sublevelID

        mainptr1 = saveDataToROM(maindata, mainptr2)
        spriteptr1 = saveDataToROM(spritedata, spriteptr2)

        # save extended sublevel data from patches
        savesublevelpatchattr(sublevel, sublevelID)

        return mainptr1, spriteptr1

    output = savewrapper(_save)
    if output is None:
        # saving failed
        return
    mainptr1, spriteptr1 = output

    # copy sublevel to recovery folder
    AdvRecovery.exportsublevel()

    # update sublevel's data blocks
    sublevel.datablocks = SMA3.Sublevel.importbyID(
        Adv3Attr.filepath, sublevelID).datablocks

    # update window title and status bar
    AdvWindow.editor.updatewindowtitle()
    actiontext = ("Saved sublevel {sublevelID}: main data at {mainptr}, "
        "sprite data at {spriteptr}.")
    AdvWindow.statusbar.setActionText(actiontext.format(
        sublevelID=format(sublevelID, "02X"),
        mainptr=format(mainptr1, "08X"),
        spriteptr=format(spriteptr1, "08X")))

    return True

def savesublevelpatchattr(sublevel, sublevelID):
    "Save additional sublevel data from Advynia's patches."

    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        if Adv3Attr.musicoverride:
            if sublevel.header[0xD] < 0xE or sublevel.music is None:
                musicID = 0xFF
            else:
                musicID = sublevel.music
            musicbyte = musicID.to_bytes(1, "little")
            f.seek(SMA3.PointersAdv.musicoverride + sublevelID)
            f.write(musicbyte)

        if Adv3Attr.sublevelstripes:
            newgfxptrs = GBA.PointerTable(endmarker=False)
            for stripeID in sublevel.stripeIDs:
                newgfxptrs.append(SMA3.Pointers.levelgfxstripesbyID[stripeID])

            stripeIDtableptr = f.readptr(SMA3.Pointers.levelgfxstripeIDs)
            stripegfxtableptr = f.readptr(SMA3.Pointers.levelgfxstripe)

            f.seek(stripeIDtableptr + 6*sublevelID)
            f.write(sublevel.stripeIDs)
            f.seek(stripegfxtableptr + 0x18*sublevelID)
            f.write(bytes(newgfxptrs))

        if Adv3Attr.world6flag:
            tilesetbyte = (sublevel.header[1] >> 4).to_bytes(1, "little")
            f.seek(SMA3.PointersAdv.L1tilesethighdigit + sublevelID)
            f.write(tilesetbyte)
