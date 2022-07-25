# import from other files
from AdvGame.SMA3 import *

# globals
import AdvSettings, Adv3Attr, Adv3Save

patches = {  # ID:(name, text)
    "midway6byte":("6-byte Midway Entrances",
        """Allows manually specifying the camera bytes in each midway entrance.
The bytes can still be left as 00 to save/load them with the checkpoint, as
in vanilla."""),
    "musicoverride":("Music Override",
        """Allows customizing the music ID and enabling/disabling pause menu
items in every sublevel."""),
    "object65":("Object 65: Arbitrary Single Tile",
        """Adds a rectangular custom object that can be any single 16x16 
tile ID."""),
    "sublevelstripes":("Sublevel Sprite Tilesets",
        """Allows customizing the 6 stripes for every sublevel.<br>
Each sublevel's stripes will default to its current sprite tileset header
setting. The header setting will no longer be used afterward."""),
    "world6flag":("World 6 Tileset Flag",
        """Allows access to the world 6 tileset (tileset 11) in any world, and to
tileset 1 in world 6. Tilesets 10,12-1F also become selectable, but are clones of
tilesets 0,2-F."""),
    }

patchdata = {
    "midway6byte":(
        (0x08002ED4, bytes.fromhex("""
            44 00 80 00 00 19 09 68 09 18 45 48
0A 88 02 80 4A 88 42 80 8A 88 00 2A 01 D0 82 80
09 E0 43 4A 11 78 01 71 11 79 41 71 03 E0 00 00
00 00 00 00 00 00""")),  # patch hex code
        ),
    "musicoverride":(
        (0x0802C2D6, bytes.fromhex("95 F1 28 FE")),  # jump
        (0x081C1F2A, bytes.fromhex("""09 4A 10 78 0E 21
88 42 02 D2 07 4A 13 68 70 47 88 43 06 4A 10 70
06 4A 12 88 06 4B 98 5C 6A F7 34 FA 70 BD 00 00
B6 4B 00 03 40 72 00 03 B8 48 00 03 B8 4C 00 03
00 20 1C 08""")),  # patch hex code
        (Pointers.Adv.musicoverride, b"\xFF"*0x100),  # music ID table
        ),
    "object65":(
        (0x0816828C + 0x65*4, 0x081C1FC1.to_bytes(4, "little")),  # init pointer
        (0x08168AAC + 0x65*4, 0x081C1FDF.to_bytes(4, "little")),  # main pointer
        (0x081C19D8 + 0x65, b"\x06"),  # signal flag
        (0x081C1FC0, bytes.fromhex("""
30 B5 C3 8E 09 4C 24 68 E5 5C 01 33 E4 5C 01 33
C3 86 24 02 2C 43 44 87 58 F6 4A F8 30 BD 42 8F
4A 30 00 88 02 49 09 68 0A 52 70 47 14 4D 00 03
10 70 00 03""")),  # patch hex code
        ),
    "world6flag":(
        (0x08013480, bytes.fromhex("""
0E 48 01 88 0E 48 00 88 0E 4A 12 5C 12 01 11 43
C8 00 89 00 41 18 0C 48 0D 18 28 68 00 68 0B 49
1C F1 14 F9 68 68 00 68 09 49 1C F1 0F F9 A8 68
00 68 08 49 1C F1 0A F9 16 E0 00 00 9E 4B 00 03
B8 4C 00 03 54 23 1C 08 44 5C 16 08 00 20 00 06
00 30 00 06 00 00 00 06 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00""")),  # patch hex code
        (0x08013510, bytes.fromhex("4F E0")),  # skip vanilla world 6 tileset checks
        (0x08013882, bytes.fromhex("1D E0")),  # skip vanilla world 6 palette checks
        ),
    }

def patchinit(patchID, warndialog):
    if getattr(Adv3Attr, patchID) is not False:
        # don't apply patch twice, or if undetected
        return False
    name, desc = patches[patchID]

    if warndialog:
        # load warning dialog
        from AdvGUI.Dialogs import QDialogPatchValidation
        if not QDialogPatchValidation(*patches[patchID]).exec():
            return False
    if not Adv3Save.firstsavewarning():
        return False

    # update editor patch flag and layouts
    Adv3Save.updateversion()
    setattr(Adv3Attr, patchID, True)
    AdvSettings.editor.updatepatchlayouts()
    AdvSettings.editor.statusbar.setActionText("Applied patch: " + name)
    return True

def detectpatches():
    "Detect which Advynia patches have been applied to the current ROM."
    with GBA.Open(Adv3Attr.filepath, "rb") as f:
        # midway6byte
        f.seek(0x08002ED4)
        bytes4 = f.read(4)
        if bytes4 == bytes.fromhex("80 00 09 68"):
            Adv3Attr.midway6byte = False
        elif bytes4 == bytes.fromhex("44 00 80 00"):
            Adv3Attr.midway6byte = True
        else:
            Adv3Attr.midway6byte = None

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
        f.seek(0x080137A0)
        word = f.readint(4)
        if word == 0x299E:
            Adv3Attr.sublevelstripes = False
        elif word == 0x2AAC:
            Adv3Attr.sublevelstripes = True
        else:
            Adv3Attr.sublevelstripes = None

        # world6flag
        f.seek(0x08013484)
        bytes4 = f.read(4)
        if bytes4 == bytes.fromhex("0D 49 40 18"):
            Adv3Attr.world6flag = False
        elif bytes4 == bytes.fromhex("0E 48 00 88"):
            Adv3Attr.world6flag = True
        else:
            Adv3Attr.world6flag = None

def loadsublevelpatchattr(sublevel):
    with GBA.Open(Adv3Attr.filepath, "rb") as f:
        if Adv3Attr.musicoverride:
            f.seek(Pointers.Adv.musicoverride + sublevel.ID)
            sublevel.music = f.read(1)[0]
            if sublevel.music == 0xFF:
                sublevel.music = None

        if Adv3Attr.world6flag:
            f.seek(Pointers.Adv.L1tilesethighdigit + sublevel.ID)
            highdigit = f.read(1)[0]
            sublevel.header[1] += highdigit << 4

        if Adv3Attr.sublevelstripes:
            f.seek(f.readptr(Pointers.levelgfxstripeIDs) + 6*sublevel.ID)
            sublevel.stripeIDs = bytearray(f.read(6))

def applymultiplepatches(patchlist):
    for patch in patchlist:
        # call the corresponding apply function
        globals()["apply" + patch](warndialog=False)

def applymidway6byte(warndialog=True):
    if not patchinit("midway6byte", warndialog):
        return False

    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        for ptr, hexdata in patchdata["midway6byte"]:
            f.seek(ptr)
            f.write(hexdata)

    return True

def applymusicoverride(warndialog=True):
    if not patchinit("musicoverride", warndialog):
        return False

    # move sublevel 00 if it's still vanilla, to free space for patching
    sublevel00 = SMA3.Sublevel.importbyID(Adv3Attr.filepath, 0)
    if sublevel00.datablocks["main"][0] == 0x081C1F29:
        AdvSettings.editor.saveSublevelToROM(sublevel00, 0)

    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        for ptr, hexdata in patchdata["musicoverride"]:
            f.seek(ptr)
            f.write(hexdata)

    return True

def applyobject65(warndialog=True):
    if not patchinit("object65", warndialog):
        return False

    # move sublevel 00 if it's still vanilla, to free space for patching
    sublevel00 = SMA3.Sublevel.importbyID(Adv3Attr.filepath, 0)
    if sublevel00.datablocks["main"][0] == 0x081C1F29:
        AdvSettings.editor.saveSublevelToROM(sublevel00, 0)

    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        for ptr, hexdata in patchdata["object65"]:
            f.seek(ptr)
            f.write(hexdata)

    return True

def applysublevelstripes(warndialog=True):
    if not patchinit("sublevelstripes", warndialog):
        return False

    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        # extract old stripe ID table
        oldstripeIDs = []
        f.seek(Pointers.levelgfxstripeIDs)
        stripeIDtableptr = f.readint(4)
        f.seek(stripeIDtableptr)

        for i in range(Constants.headermaxvalues[7] + 1):
            oldstripeIDs.append(f.read(6))

        # extract old sprite tileset header settings
        f.seek(Pointers.sublevelmainptrs)
        mainptrtable = f.readint(4)
        f.seek(mainptrtable)
        sublevelmainptrs = []
        for i in range(Constants.maxsublevel + 1):
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
                newgfxptrs.append(Pointers.levelgfxstripesbyID[stripeID])

        # apply patch (just one hex-edit)
        f.seek(0x080137A0)
        f.write(0x2AAC.to_bytes(4, byteorder="little"))

        # remap graphics pointer table to freespace
        # erase vanilla table
        f.readseek(Pointers.levelgfxstripe)
        f.write(bytes(0xE10))

        # save new stripe ID table
        f.seek(stripeIDtableptr)
        f.write(newstripeIDs)

    # save new graphics pointer table
    Adv3Save.saveDataToROM(bytes(newgfxptrs), Pointers.levelgfxstripe)

    # ensure currently loaded sublevel includes stripes
    import Adv3Visual
    Adv3Attr.sublevel.stripeIDs = Adv3Visual.spritegraphics.stripeIDs[:]

    return True

def applyworld6flag(warndialog=True):
    if not patchinit("world6flag", warndialog):
        return False

    # move sublevels 00/3C if they're still vanilla, to free space for patching
    sublevel00 = SMA3.Sublevel.importbyID(Adv3Attr.filepath, 0)
    if sublevel00.datablocks["sprite"][0] == 0x081C2354:
        AdvSettings.editor.saveSublevelToROM(sublevel00, 0)
    sublevel3A = SMA3.Sublevel.importbyID(Adv3Attr.filepath, 0x3A)
    if sublevel3A.datablocks["sprite"][0] == 0x081C2434:
        AdvSettings.editor.saveSublevelToROM(sublevel3A, 0x3A)

    with GBA.Open(Adv3Attr.filepath, "r+b") as f:
        for ptr, hexdata in patchdata["world6flag"]:
            f.seek(ptr)
            f.write(hexdata)

        # init table, and set flags for vanilla 6-1/6-6 sublevels
        base = Pointers.Adv.L1tilesethighdigit
        f.seek(base)
        f.write(bytes(0x100))
        for offset in (0x2D, 0x32, 0x64, 0x69, 0x90, 0x95, 0xB5):
            f.seek(base + offset)
            f.write(b"\x01")

    return True
