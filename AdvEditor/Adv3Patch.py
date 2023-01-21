"""Advynia SMA3 Patching
Handles detecting and applying Advynia's assembly patches."""

# standard library imports
from collections.abc import Iterable
import itertools

# import from other files
import AdvEditor.Export, AdvEditor.ROM
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr, Adv3Save, Adv3Visual
from AdvEditor.PatchData import patches, patchhexdata
from AdvGame import GBA, SMA3

def applypatch(patchkey: str, warndialog=True):
    "Apply an Advynia patch, given the patch key."

    if getattr(Adv3Attr, patchkey) is not False:
        # don't apply patch twice, or if undetected
        return False
    name, desc = patches[patchkey]

    if (warndialog and AdvSettings.warn_patch_all and
            getattr(AdvSettings, "warn_patch_" + patchkey)):
        # load warning dialog, unless it was disabled for this function call,
        #  this patch, or all patches
        from AdvGUI.Dialogs import QDialogPatchValidation
        if not QDialogPatchValidation(patchkey, name, desc).exec():
            return False

    # apply patch, by passing patch function to save wrapper
    applied = Adv3Save.savewrapper(globals()["apply" + patchkey])
    if not applied:
        return False

    # update editor patch flag and layouts
    setattr(Adv3Attr, patchkey, True)
    AdvWindow.editor.updatepatchlayouts()
    AdvWindow.statusbar.setActionText("Applied patch: " + name)

    return True

def applymultiplepatches(patchlist: Iterable[str]):
    "Apply several Advynia patches, without displaying the warning dialog."
    for patchkey in patchlist:
        applypatch(patchkey, warndialog=False)

def _writehexdata(patchkey):
    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        for ptr, hexdata in patchhexdata[patchkey]:
            f.seek(ptr)
            f.write(hexdata)

def detectpatches():
    """Detect which Advynia patches have been applied to the current ROM,
    and set their flags accordingly."""
    with GBA.Open(Adv3Attr.filepath, "rb") as f:
        # huffmantolz77
        Adv3Attr.huffmantolz77 = detectpatches_bytes4(f, 0x081116CA,
            bytes.fromhex("1D F0 FD FF"), bytes.fromhex("1D F0 FF FF"))

        # midway6byte
        Adv3Attr.midway6byte = detectpatches_bytes4(f, 0x08002ED4,
            bytes.fromhex("80 00 09 68"), bytes.fromhex("44 00 80 00"))

        # musicoverride
        f.seek(0x0802C2D6)
        word = f.readint(4)
        if word == 0x68134A22:  # vanilla bytes
            Adv3Attr.musicoverride = False
        elif word & 0b11111000_00000000_11111000_00000000 ==\
                    0b11111000_00000000_11110000_00000000:  # detect bl opcode
            Adv3Attr.musicoverride = True
        else:
            Adv3Attr.musicoverride = None

        # object65
        f.seek(0x081C19D8 + 0x65)
        Adv3Attr.object65 = bool(f.read(1)[0])

        # sublevelstripes
        Adv3Attr.sublevelstripes = detectpatches_bytes4(f, 0x080137A0,
            0x299E.to_bytes(4, "little"), 0x2AAC.to_bytes(4, "little"))

        # world6flag
        Adv3Attr.world6flag = detectpatches_bytes4(f, 0x08013484,
            bytes.fromhex("0D 49 40 18"), bytes.fromhex("0E 48 00 88"))

def detectpatches_bytes4(f, ptr, vanillabytes, patchedbytes):
    f.seek(ptr)
    bytes4 = f.read(4)
    if bytes4 == vanillabytes:
        return False
    elif bytes4 == patchedbytes:
        return True

def detectpatches_sublevel(sublevel):
    """Detect which patches are required to import the given sublevel, if
    not already applied."""
    newpatches = []
    if not Adv3Attr.world6flag and sublevel.header[1] >= 0x10:
        newpatches.append("world6flag")
    if not Adv3Attr.musicoverride and sublevel.music:
        newpatches.append("musicoverride")
    if not Adv3Attr.sublevelstripes and sublevel.stripeIDs:
        with GBA.Open(Adv3Attr.filepath) as f:
            expectedstripes = SMA3.loadstripeIDs(f, sublevel.header[7])
        if sublevel.stripeIDs != expectedstripes:
            newpatches.append("sublevelstripes")
    if not Adv3Attr.object65 and sublevel.obj65_7byte:
        newpatches.append("object65")
    return newpatches

def detectpatches_midway(midways):
    """Detect whether the 6-byte midway entrance patch is required to import
    the given midway entrances, if not already applied."""
    if Adv3Attr.midway6byte:
        return False
    for level in midways:
        for entr in level:
            if entr[4] != 0 or entr[5] != 0:
                return True
    return False

def loadsublevelpatchattr(sublevel):
    with GBA.Open(Adv3Attr.filepath, "rb") as f:
        if Adv3Attr.musicoverride:
            f.seek(SMA3.PointersAdv.musicoverride + sublevel.ID)
            sublevel.music = f.read(1)[0]
            if sublevel.music == 0xFF:
                sublevel.music = None

        sublevel.importspritetileset(f, Adv3Attr.sublevelstripes)

        if Adv3Attr.world6flag:
            f.seek(SMA3.PointersAdv.L1tilesethighdigit + sublevel.ID)
            highdigit = f.read(1)[0]
            sublevel.header[1] += highdigit << 4

def _movevanillasublevel(sublevelID):
    """Move a sublevel, only if its data is still in the vanilla sublevel
    region, to use the vanilla region for patch freespace."""
    sublevel = SMA3.Sublevel.importbyID(Adv3Attr.filepath, sublevelID)
    move = False
    for block in sublevel.datablocks.values():
        if 0x081C1D54 <= block[0] < 0x081EEE8C:
            break
    else:
        return True
    with GBA.Open(Adv3Attr.filepath, "rb") as f:
        sublevel.importspritetileset(f, Adv3Attr.sublevelstripes)
    saved = Adv3Save.savesubleveltoROM(sublevel, sublevelID)
    return saved

# specific patch code

def applyhuffmantolz77():
    _writehexdata("huffmantolz77")

    # reinsert all Huffman compressed data blocks as LZ77
    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        toinsert = []
        for ptrref in itertools.chain(
                SMA3.Pointers.Huffman_graphics.values(),
                SMA3.Pointers.Huffman_tilemaps.values()):
            # import data and convert to LZ77
            ptr = f.readptr(ptrref)
            data = f.read_decompress(ptr)
            toinsert.append((GBA.compressLZ77(data), ptrref))

            # erase old data
            oldlength = f.tell() - ptr
            f.seek(ptr)
            f.write(bytes(oldlength))

    # insert compressed data
    AdvEditor.Export._insertcompresseddata(toinsert)

    return True

def applymidway6byte():
    _writehexdata("midway6byte")
    return True

def applymusicoverride():
    if not _movevanillasublevel(0):
        return False
    _writehexdata("musicoverride")
    return True

def applyobject65():
    if not _movevanillasublevel(0):
        return False
    _writehexdata("object65")
    return True

def applysublevelstripes():
    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        # extract old stripe ID table
        oldstripeIDs = []
        f.seek(SMA3.Pointers.levelgfxstripeIDs)
        stripeIDtableptr = f.readint(4)
        f.seek(stripeIDtableptr)

        for i in range(SMA3.Constants.headermaxvalues[7] + 1):
            oldstripeIDs.append(f.read(6))

        # extract old sprite tileset header settings
        f.seek(SMA3.Pointers.sublevelmainptrs)
        mainptrtable = f.readint(4)
        f.seek(mainptrtable)
        sublevelmainptrs = []
        for i in range(SMA3.Constants.maxsublevel + 1):
            sublevelmainptrs.append(f.readint(4))

        sublevelh7 = []
        temp = SMA3.Sublevel()
        for ptr in sublevelmainptrs:
            f.seek(ptr)
            temp.extractheader(f.read(10), temp.headerbitcounts)
            sublevelh7.append(temp.header[7])

        # calculate new sprite tilesets, indexed by sublevel
        newstripeIDs = bytearray()
        newgfxptrs = GBA.PointerTable()

        for oldtileset in sublevelh7:
            stripeIDs = oldstripeIDs[oldtileset]
            newstripeIDs += stripeIDs
            for stripeID in stripeIDs:
                newgfxptrs.append(SMA3.Pointers.levelgfxstripesbyID[stripeID])

        # apply patch (just one hex-edit)
        f.seek(0x080137A0)
        f.writeint(0x2AAC, 4)

        # remap graphics pointer table to freespace
        # erase vanilla table
        f.readseek(SMA3.Pointers.levelgfxstripe)
        f.write(bytes(0xE10))

        # save new stripe ID table
        f.seek(stripeIDtableptr)
        f.write(newstripeIDs)

    # save new graphics pointer table
    Adv3Save.savedatatoROM(bytes(newgfxptrs), SMA3.Pointers.levelgfxstripe)

    # ensure currently loaded sublevel includes stripes
    Adv3Attr.sublevel.stripeIDs = Adv3Visual.spritegraphics.stripeIDs[:]

    return True

def applyworld6flag():
    for sublevelID in (0x00, 0x3A):
        if not _movevanillasublevel(sublevelID):
            return False

    _writehexdata("world6flag")

    # init table, and set flags for vanilla 6-1/6-6 sublevels
    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        base = SMA3.PointersAdv.L1tilesethighdigit
        f.seek(base)
        f.write(bytes(0x100))
        for offset in (0x2D, 0x32, 0x64, 0x69, 0x90, 0x95, 0xB5):
            f.seek(base + offset)
            f.write(b"\x01")

    return True
