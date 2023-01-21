"""Advynia SMA3 Saving
Saving/exporting-related functions that rely on other parts of Advynia,
as opposed to AdvGame, which does not rely on Advynia globals or Qt."""

# standard library imports
import os, traceback

# import from other files
import AdvMetadata, AdvEditor.Number, AdvEditor.ROM, AdvEditor.Recovery, AdvFile
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr, Adv3Patch, Adv3Visual
from AdvGame import AdvGame, GBA, SMA3
from AdvGUI.GeneralQt import QSimpleDialog

savewrapperactive = False
queuedalert = None

# General save functions

def savewrapper(func, *args, **kwargs):
    """Wrapper for functions that modify the ROM. Handles restoring the ROM if
    an exception occurs.
    Also includes the unmodified ROM warning, and writing/updating Advynia
    metadata."""

    global savewrapperactive, queuedalert

    # if save wrapper is already active, don't nest try clauses
    if savewrapperactive:
        return func(*args, **kwargs)
    savewrapperactive = True

    try:
        if not AdvEditor.ROM.exists(): return

        # display warning if the ROM is unmodified
        if not _firstsavewarning(): return

        # back up the ROM
        AdvEditor.Recovery.backupROM()

        # save Advynia metadata
        if Adv3Attr.savedversion is None or\
                Adv3Attr.savedversion < AdvMetadata.version:
            _saveAdvyniaMetadata()

        try:
            # run save function, and return its return value(s)
            output = func(*args, **kwargs)
            if queuedalert:
                queuedalert.exec()
            return output
        except ROMFreespaceError:
            AdvEditor.Recovery.restoreROM()
            QSimpleDialog(AdvWindow.editor, title="Error", wordwrap=False,
                text="File is already at the GBA max ROM size, 32 MiB.\n"
                     "Data was not saved."
                          ).exec()
        except Exception:
            AdvEditor.Recovery.restoreROM()
            text = ("An error occurred when saving. Your ROM has not been "
                    "modified.\n\n" + traceback.format_exc())
            traceback.print_exc()
            QSimpleDialog(AdvWindow.editor, title="Error",
                          text=text).exec()
    finally:
        queuedalert = None
        savewrapperactive = False

def savedatatoROM(data, ptrref,
                  freespacestart=0x08400000, freespaceend=0x0A000000):
    """Wrapper for GBA.savedatatofreespace, for Advynia saving.

    Save variable-length data to the currently loaded ROM, and update the
    data's pointer(s). If insufficient space and the ROM size doesn't include
    the entire interval, expand the ROM size by up to 1 MiB at a time."""

    while True:
        newptr = GBA.savedatatofreespace(
            Adv3Attr.filepath, data, ptrref, freespacestart, freespaceend)
        if newptr:
            return newptr

        # expand ROM if allowed
        size = os.path.getsize(Adv3Attr.filepath)
        maxsize = freespaceend - 0x08000000
        if size < maxsize:
            expandROM(min(0x100000, maxsize - size))
        else:
            raise ROMFreespaceError

class ROMFreespaceError(Exception):
    "Unique exception identifier, to be caught first in savewrapper."
    pass

def _firstsavewarning():
    "Display a warning if the ROM is unmodified."
    if AdvSettings.warn_save_first and Adv3Attr.savedversion is None:
        from AdvGUI.Dialogs import QDialogSaveValidation
        if not QDialogSaveValidation(AdvWindow.editor).exec():
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
        raise ROMFreespaceError
    newsize = size + bytecount
    if newsize > 0x2000000:
        bytecount = 0x2000000 - size
        newsize = 0x2000000

    with open(Adv3Attr.filepath, "ab") as f:
        f.write(bytes(bytecount))  # fill with 00 bytes

    if AdvSettings.warn_save_expandROM:
        global queuedalert
        queuedalert = QSimpleDialog(
            AdvWindow.editor, title="Notice", wordwrap=False,
            text="".join(("ROM expanded to ",
                          AdvEditor.Number.megabytetext(newsize), " MiB.")))
    return newsize

# Sublevel save functions

def savesubleveltoROM(sublevel, sublevelID):
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

        mainptr1 = savedatatoROM(maindata, AdvGame.PtrRef(mainptr2))
        spriteptr1 = savedatatoROM(spritedata, AdvGame.PtrRef(spriteptr2))

        # save extended sublevel data from patches
        savesublevelpatchattr(sublevel, sublevelID)

        return mainptr1, spriteptr1

    output = savewrapper(_save)
    if output is None:
        # saving failed
        return
    mainptr1, spriteptr1 = output

    # copy sublevel to recovery folder
    if AdvSettings.recovery_autoexport:
        AdvEditor.Recovery.exportsublevel()

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

        if Adv3Attr.sublevelstripes and sublevel.stripeIDs:
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

# Other data save functions

def saveentrances(mainentrances, midwayentrances, *, oldmidwaylen=None):
    "Save level entrances to ROM."

    # import old entrances, to retrieve data blocks
    if oldmidwaylen is None:
        oldmidwaylen = 6 if Adv3Attr.midway6byte else 4
    oldmain, oldmidway = SMA3.importlevelentrances(
        Adv3Attr.filepath, maxmidpoints=Adv3Attr.maxmidpoints,
        midwaylen=oldmidwaylen)

    # determine 4 or 6-byte midways, for SMA3.MidwayEntrances.tobytearray
    if Adv3Attr.midway6byte:
        midwaylen = 6
    elif Adv3Patch.detectpatches_midway(midwayentrances):
        applied = Adv3Patch.applypatch("midway6byte")
        if not applied: return
        midwaylen = 6
    else:
        midwaylen = 4
    midwayentrances.midwaylen = midwaylen

    startptrs = []
    for entrances, oldentrances in ((mainentrances, oldmain),
                                    (midwayentrances, oldmidway)):
        # generate bytearrays
        data, offsets = entrances.tobytearray()

        # calculate number of pointers to save
        oldlen = len(oldentrances.ptrs)
        newlen = len(offsets)
        if len(offsets) > oldlen:
            for ptr in reversed(offsets[oldlen:]):
                if ptr != None:
                    break
                newlen -= 1
        offsets = offsets[0:newlen]

        # write entrances to ROM, without auto-updating pointers
        GBA.erasedata(Adv3Attr.filepath, *oldentrances.datablock)
        startptr = savedatatoROM(data, None)
        startptrs.append(startptr)

        # calculate pointers
        ptrs = GBA.PointerTable()
        for offset in offsets:
            if offset is None:
                ptrs.append(1)
            else:
                ptrs.append(startptr + offset)

        # save entrance pointer table
        if newlen != oldlen:
            ptrs.endmarker = True
            GBA.erasedata(Adv3Attr.filepath, *oldentrances.ptrs.datablock)
            newtableptr = savedatatoROM(
                ptrs.tobytearray(nullptr=1), entrances.ptrref)
        else:
            ptrs.endmarker = False
            GBA.overwritedata(
                Adv3Attr.filepath, bytes(ptrs),
                GBA.readptr(Adv3Attr.filepath, entrances.ptrref))

    # copy entrances to recovery folder
    if AdvSettings.recovery_autoexport:
        AdvEditor.Recovery.exportentrances(mainentrances, midwayentrances)

    # update status bar
    statustext = ("Saved main entrances to {mainptr}, "
                  "midway entrances to {midwayptr}.")
    AdvWindow.statusbar.setActionText(statustext.format(
        mainptr=format(startptrs[0], "08X"),
        midwayptr=format(startptrs[1], "08X")))

    return True

def savemessages(messages, texttypestosave=None):
    """Save messages to ROM. If an iterable of text types is provided, save
    only those types."""
    if texttypestosave is None:
        texttypestosave = messages.keys()

    newptrs = []
    for texttype in texttypestosave:
        if texttype != "Ending":
            newblockptr = _savetablemessages(messages[texttype], texttype)
        else:
            message = messages["Ending"][0]

            # erase old ending message
            GBA.erasedata(Adv3Attr.filepath, *type(message).importall(
                Adv3Attr.filepath)[0].datablock)

            # save ending message and update pointer
            newblockptr = savedatatoROM(bytes(message), message.ptrref())
        newptrs.append((texttype, newblockptr))

    # copy messages to recovery folder
    if AdvSettings.recovery_autoexport:
        AdvEditor.Recovery.exportmessages(messages)

    # update status bar
    statustext = ["Saved messages: "]
    for texttype, ptr in newptrs:
        if texttype in ("Level name", "Standard message"):
            texttype += "s"
        statustext += [texttype.lower(), " at ", format(ptr, "08X"), ", "]
    statustext[-1] = "."
    AdvWindow.statusbar.setActionText("".join(statustext))

    return True

def _savetablemessages(messages, texttype):
    array, relptrs = messages.tobytearray(nullptr=(texttype=="Story intro"))

    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        # erase old messages
        for message in type(messages[0]).importall(
                Adv3Attr.filepath).uniqueitems():
            if message.datablock:
                f.erasedata(*message.datablock)

        # save new message data block, without auto-updating pointers
        newblockptr = savedatatoROM(array, None)

        # overwrite pointer table
        ptrs = GBA.PointerTable(
            ((ptr + newblockptr if ptr is not None else 0)
             for ptr in relptrs),
            endmarker=False)
        if texttype == "Credits":
            # update hardcoded pointers for last 3 messages,
            #  and remove them from table
            creditsendptrs = ptrs[-3:]
            del ptrs[-3:]
            for ptrtotext, newptr in zip(
                    SMA3.Pointers.text["Credits final"], creditsendptrs,
                    strict=True):
                f.seek(ptrtotext)
                f.writeint(newptr, 4)
        f.readseek(messages[0].ptrref())
        f.write(bytes(ptrs))
    return newblockptr
