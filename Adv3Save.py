# standard library imports
import os

# import from other files
from AdvGame.SMA3 import *

# globals
import AdvMetadata, AdvSettings, Adv3Attr, Adv3Visual

def saveDataToROM(data, ptrstodata,
                  freespacestart=0x400000, freespaceend=0x2000000):
    """Wrapper for GBA.savedatatofreespace, for Advynia saving.

    Save variable-length data to the currently loaded ROM, and update the
    data's pointer(s). If insufficient space, expand the ROM size by 1 MiB
    at a time."""

    updateversion()

    while True:
        newptr = GBA.savedatatofreespace(Adv3Attr.filepath, data, ptrstodata)
        if newptr:
            return newptr
        newsize = expandROM(0x100000)
        if not newsize:
            return

def saveAdvyniaMetadata():
    "Save Advynia metadata to the last 0x20 bytes of the vanilla ROM size."
    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        f.seek(0x083FFFE0)
        metadata = bytearray(b"Advynia3")
        for num in AdvMetadata.version[0:3]:
            metadata += num.to_bytes(2, byteorder="little")
        f.write(metadata)
    Adv3Attr.savedversion = AdvMetadata.ProgramVersion(AdvMetadata.version[0:3])

def updateversion():
    """Wrapper for saveAdvyniaMetadata that runs only if the version needs
    updating."""
    if Adv3Attr.savedversion is None or\
            Adv3Attr.savedversion < AdvMetadata.version:
        saveAdvyniaMetadata()

def firstsavewarning():
    if Adv3Attr.savedversion is None:
        from AdvGUI.Dialogs import QDialogSaveValidation
        cancelflag = QDialogSaveValidation(AdvSettings.editor).exec()
        if cancelflag:
            return False
        # set version to 0.0.0 to prevent warning multiple times
        Adv3Attr.savedversion = AdvMetadata.ProgramVersion((0, 0, 0))
    return True

def expandROM(bytecount):
    "Append a number of 00 bytes to the end of the ROM."

    from AdvGUI import QSimpleDialog

    size = os.path.getsize(Adv3Attr.filepath)
    if size >= 0x2000000:
        QSimpleDialog(AdvSettings.editor, title="Error",
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

    if newsize / 0x100000 == newsize // 0x100000:  # integer MiB
        sizestr = str(newsize // 0x100000)
    else:
        sizestr = format(newsize / 0x100000, ".2f")  # float MiB
    QSimpleDialog(AdvSettings.editor, title="Notice", text="".join(
        ("ROM expanded to ", sizestr, " MiB."))
                 ).exec()
    return newsize

def savesublevelpatchattr(sublevel, sublevelID):
    if Adv3Attr.musicoverride:
        saveMusicOverride(sublevel, sublevelID)
    if Adv3Attr.sublevelstripes:
        saveStripeData(sublevel, sublevelID)
    if Adv3Attr.world6flag:
        saveL1TilesetHighDigit(sublevel, sublevelID)

def saveStripeData(sublevel, sublevelID):
    "For use with the Sublevel Sprite Tilesets patch."
    newgfxptrs = GBA.PointerTable(endmarker=False)
    for stripeID in sublevel.stripeIDs:
        newgfxptrs.append(Pointers.levelgfxstripesbyID[stripeID])

    stripeIDtableptr = GBA.readptr(Adv3Attr.filepath, Pointers.levelgfxstripeIDs)
    stripegfxtableptr = GBA.readptr(Adv3Attr.filepath, Pointers.levelgfxstripe)
    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        f.seek(stripeIDtableptr + 6*sublevelID)
        f.write(sublevel.stripeIDs)
        f.seek(stripegfxtableptr + 0x18*sublevelID)
        f.write(bytes(newgfxptrs))

def saveMusicOverride(sublevel, sublevelID):
    "For use with the Music Override patch."
    if sublevel.header[0xD] < 0xE or sublevel.music is None:
        musicID = 0xFF
    else:
        musicID = sublevel.music
    musicbyte = musicID.to_bytes(1, byteorder="little")
    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        f.seek(Pointers.Adv.musicoverride + sublevelID)
        f.write(musicbyte)

def saveL1TilesetHighDigit(sublevel, sublevelID):
    "For use with the World 6 Tileset Flag patch."
    tilesetbyte = (sublevel.header[1] >> 4).to_bytes(1, byteorder="little")
    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        f.seek(Pointers.Adv.L1tilesethighdigit + sublevelID)
        f.write(tilesetbyte)

