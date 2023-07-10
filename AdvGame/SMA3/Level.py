"""SMA3 Level
Classes and functions for SMA3 levels and sublevels."""

# standard library imports
import itertools

##if __name__ == "__main__":
##    # allow testing as if it's from the Advynia main directory
##    import os, sys
##    os.chdir("../..")
##    sys.path.append(".")

# import from other files
import AdvGame
from AdvGame import GBA, SNES
from AdvGame.SMA3 import Pointers, PointersSNES, Constants

# Misc info

def levelnumber(levelID, short=False):
    "Generate a printable level number (e.g. 2-3, 5-Secret) from a level ID."
    if levelID == 0xB:   # Intro level is hardcoded to 0B
        if short:
            return "Intro"
        else:
            return "Intro level"
    else:
        worldnum = levelID // 0xC + 1
        cursorpos = levelID % 0xC
        output = f"{worldnum}-{Constants.levelnumrighthalf[cursorpos]}"
        if short:
            # use only first letter of words
            output = output[0:3]
        return output

def screentocoords(screen):
    "Convert a screen number to the tile x,y of the screen's top-left corner."
    return (screen & 0xF) << 4, screen & 0xF0

def coordstoscreen(x, y):
    "Calculate the screen number given a tile x,y."
    return (y & 0xF0) | (x >> 4)

# SMA3 sublevel data classes

class Sublevel:
    """Representation of a sublevel's data. Includes header, objects, sprites,
    and screen exits, and functions for import/export."""
    def __init__(self, *, obj65_7byte=False):
        # initialize a null sublevel
        self.ID = None
        self.header = [0]*0xF
        self.objects = []
        self.exits = {}
        self.sprites = []
        self.layerYoffsets = self.layerYoffsets_defaults.copy()

        self.datablocks = {}

        self.fromfile = False

        # Advynia patches
        self.stripeIDs = None
        self.music = None
        self.obj65_7byte = obj65_7byte

    layerYoffsets_defaults = {2: 0x034E, 3: 0x015E}
    headerbitcounts = (5,4,5,5,6,6,6,8,5,5,6,5,5,4,2)

    def __getattr__(self, name):
        if name == "objlengthprop":
            # if object length properties aren't provided, use these defaults
##            print("Warning: using hardcoded object length properties!")
            self.objlengthprop = [
                None,2,1,1,2,2,2,2,2,2,1,1,1,0,1,1,
                   2,2,2,0,2,0,2,2,2,2,0,1,1,0,0,2,
                   2,2,1,1,2,1,1,2,2,2,2,1,1,1,1,1,
                   1,1,2,2,0,2,1,0,2,2,2,2,1,0,1,1,
                   1,0,1,1,2,2,2,2,2,1,1,1,1,1,2,2,
                   1,0,2,0,2,2,2,0,2,2,2,2,2,2,2,2,
                   2,2,2,0,0,0,2,2,2,2,0,2,2,1,2,1,
                   0,0,0,1,1,1,1,1,2,0,2,2,0,0,0,2,
                   0,0,2,0,0,2,2,2,2,2,2,2,0,1,0,2,
                   2,1,1,1,2,2,2,2,2,1,1,1,1,2,0,0,
                   2,2,2,2,2,1,0,2,2,1,1,1,0,0,1,0,
                   2,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,
                   0,0,0,0,0,1,0,0,1,0,2,2,2,2,0,0,
                   0,1,0,2,1,1,0,0,0,0,2,2,2,2,1,0,
                   1,2,1,2,2,2,2,2,2,2,2,2,2,2,2,2,
                   2,2,2,2,1,2,2,0,0,0,0,0,0,0,2]
            if self.obj65_7byte:
                self.objlengthprop[0x65] = 2
            return self.objlengthprop
        raise AttributeError(" ".join((repr(self.__class__.__name__),
            "object has no attribute", repr(name))))

    def bytesize(self):
        """Calculate the total byte size of this sublevel: the sum of the byte
        lengths of this sublevel's main and sprite data."""
##        return len(self.exportmaindata()) + (len(self.sprites)+1)*4
        return (0x10 + sum(len(bytes(obj)) for obj in self.objects) +
                7*len(self.exits) + 4*len(self.sprites))

    # import methods

    @classmethod
    def importbyID(cls, filepath, sublevelID, objlengthprop=None):
        "Import a specified sublevel's main and sprite data from the game."
        sublevel = cls()
        sublevel.ID = sublevelID

        with GBA.Open(filepath) as f:
            # retrieve object lengths
            if not objlengthprop:
                f.readseek(Pointers.objlengthprop)
                objlengthraw = f.read(0xFF)
                # only lowest 2 bits of table are used for length properties
                sublevel.objlengthprop = [byte&3 for byte in objlengthraw]
                if objlengthraw[0x65] & 0x3C:
                    sublevel.obj65_7byte = True

            # load main/sprite data
            mainptrtable = f.readptr(Pointers.sublevelmainptrs)
            mainptr = f.readptr(mainptrtable, index=sublevelID)

            spriteptrtable = f.readptr(Pointers.sublevelspriteptrs)
            spriteptr = f.readptr(spriteptrtable, index=sublevelID)

            f.seek(mainptr)
            sublevel.importmaindata(f)
            sublevel.datablocks["main"] = [mainptr, f.tell() - mainptr]

            f.seek(spriteptr)
            sublevel.importspritedata(f)
            sublevel.datablocks["sprite"] = [spriteptr, f.tell() - spriteptr]

            # load sublevel-indexed layer Y offsets
            f.seek(f.readptr(Pointers.sublevellayerY) + 4*sublevelID)
            sublevel.layerYoffsets[2] = f.readint(2)
            sublevel.layerYoffsets[3] = f.readint(2)

        return sublevel

    def importmaindata(self, f):
        """Import a sublevel's main data (header, objects, exits) from a file
        object."""
        headerraw = f.read(10)
        self.extractheader(headerraw, self.headerbitcounts)
        self.importobjectdata(f)
        self.importexitdata(f)

    def extractheader(self, headerraw, headerbitcounts):
        "Extract a sublevel header's bitwise values from the raw bytes object."
        self.header = []
        bitoffset = 0
        for bitcount in headerbitcounts:
            newbyte = 0
            for i in range(bitcount):
                # read from highest to lowest bit
                bit = (headerraw[bitoffset//8] >> (7 - bitoffset%8)) & 1
                newbyte = newbyte<<1 | bit
                bitoffset += 1
            self.header.append(newbyte)

    def importobjectdata(self, f):
        "Import a sublevel's object data from a file object."
        self.objects = []
        while (objectID := f.read(1)[0]) != 0xFF:
            objscreen = f.read(1)[0]
            objcoord = f.read(1)[0]

            obj = Object(ID=objectID)
            # untangle x/y high and low digits
            obj.x = ((objscreen & 0xF) << 4) | (objcoord & 0xF)
            obj.y = (objscreen & 0xF0) | (objcoord >> 4)
            if obj.ID == 0:
                # if object 00, there's an extended object ID byte
                obj.extID = f.read(1)[0]
                self.objects.append(obj)
                continue   # object 00 has no length bytes
            if self.objlengthprop[objectID] != 1:
                # if property 0 or 2, there's a signed width byte
                obj.width = int.from_bytes(f.read(1), "little", signed=True)
            if self.objlengthprop[objectID] != 0:
                # if property 1 or 2, there's a signed height byte
                obj.height = int.from_bytes(f.read(1), "little", signed=True)
            if obj.ID in (0x64, 0x65):
                if self.obj65_7byte and obj.ID == 0x65:
                    obj.extID = int.from_bytes(f.read(2), "little")
                    obj.extIDbytes = 2
                else:
                    obj.ID == 0x63
            self.objects.append(obj)

    def importexitdata(self, f, entrlength=6):
        "Import a sublevel's screen exit data from a file object."
        self.exits = {}
        while (screenindex := f.read(1)[0]) != 0xFF:
            self.exits[screenindex] = Entrance(f.read(entrlength))

    def importspritedata(self, f):
        "Import a sublevel's sprite data from a file object."
        self.sprites = []
        while (rawbytes := f.read(4)) != b"\xff\xff\xff\xff":
            if not rawbytes:
                # prevent infinite loop
                raise ValueError("Reached end of byte stream when importing "
                                 "sprite data.")
            sprite32bit = int.from_bytes(rawbytes, "little")
            spr = Sprite(
                ID = sprite32bit & 0x1FF,
                y = (sprite32bit >> 9) & 0x7F,
                x = (sprite32bit >> 16) & 0xFF,
                extID = sprite32bit >> 24
                )
            self.sprites.append(spr)

    def importspritetileset(self, f, sublevelstripes=False):
        spritetileset = self.ID if sublevelstripes else self.header[7]
        self.stripeIDs = loadstripeIDs(f, spritetileset)

    # export methods

    def exportmaindata(self):
        "Export a sublevel's main data (header, objects, exits) to a bytearray."
        output = bytearray()

        # process header values
        output += self._headertobytes(self.header, self.headerbitcounts)

        # process objects
        for obj in self.objects:
            output += bytes(obj)
        output.append(0xFF)

        # process screen exits
        for screenindex, entrance in self.exits.items():
            output.append(screenindex)
            output += entrance
        output.append(0xFF)

        return output

    @staticmethod
    def _headertobytes(header, headerbitcounts):
        output = bytearray()
        bitoffset = 0
        newbyte = 0
        for i, bitcount in enumerate(headerbitcounts):
            for j in reversed(range(bitcount)):
                # read from highest to lowest bit
                bit = header[i]>>j & 1
                newbyte = newbyte<<1 | bit
                bitoffset += 1
                if bitoffset == 8:
                    output.append(newbyte)
                    bitoffset = 0
                    newbyte = 0
        if bitoffset:
            # finish incomplete final byte
            newbyte <<= (8-bitoffset)
            output.append(newbyte)
        return output

    def exportspritedata(self):
        "Export a sublevel's sprite data to a bytearray."
        output = bytearray()

        for spr in self.sprites:
            output += bytes(spr)
        output += b"\xFF"*4

        return output

class SublevelFromSNES(Sublevel):
    "Subclass for importing SNES-format data."

    fromSNES = True
    headerbitcountsSNES = (5,4,5,5,6,6,6,7,4,5,6,5,5,4,2)
    objlengthprop = (
        None,2,1,1,2,2,2,2,2,2,1,1,1,0,1,1,
           2,2,2,0,2,0,2,2,2,2,0,1,1,0,0,2,
           2,2,1,1,2,1,1,2,2,2,2,1,1,1,1,1,
           1,1,2,2,0,2,1,0,2,2,2,2,1,0,1,1,
           1,0,1,1,2,2,2,2,2,1,1,1,1,1,2,2,
           1,0,2,0,2,2,2,0,2,2,2,2,2,2,2,2,
           2,2,2,0,0,0,2,2,2,2,0,2,2,1,2,1,
           0,0,0,1,1,1,1,1,2,0,2,2,0,0,0,2,
           0,0,2,0,0,2,2,2,2,2,2,2,0,1,0,2,
           2,1,1,1,2,2,2,2,2,1,1,1,1,2,0,0,
           2,2,2,2,2,1,0,2,2,1,1,1,0,0,1,0,
           2,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,
           0,0,0,0,0,1,0,0,1,0,2,2,2,2,0,0,
           0,1,0,2,1,1,0,0,0,0,2,2,2,2,1,0,
           1,2,1,2,2,2,2,2,2,2,2,2,2,2,2,2,
           2,2,2,2,1,2,2,0,0,0,0,0,0,0,2)

    @classmethod
    def importbyID(cls, filepath, sublevelID):
        "Import a specified sublevel's main and sprite data from an SNES ROM."
        sublevel = cls()
        sublevel.ID = sublevelID

        with SNES.Open(filepath, "rb") as f:
            f.seek(PointersSNES.sublevelptrs)
            ptrtable = f.readint(3)
            f.seek(ptrtable + 6*sublevelID)
            mainptr = f.readint(3)
            spriteptr = f.readint(3)

            f.seek(mainptr)
            sublevel.importmaindata(f)
            f.seek(spriteptr)
            sublevel.importspritedata(f)

            sublevel.importspritetileset(f)

        return sublevel

    def importmaindata(self, f):
        headerraw = f.read(10)
        self.extractheader(headerraw, self.headerbitcountsSNES)
        self.importobjectdata(f)
        self.importexitdata(f, entrlength=4)
        for entr in self.exits.values():
            # fix Bandit minigame sublevel IDs
            if 0xDE <= entr.sublevelID <= 0xE7:
                entr.sublevelID += 0x18
                if 0xDE <= entr.anim <= 0xE7:
                    entr.anim += 0x18

    def importspritedata(self, f):
        while (sprite16bit := int.from_bytes(f.read(2), "little")) != 0xFFFF:
            spr = Sprite()
            spr.ID = sprite16bit & 0x1FF
            if 0x1BA <= spr.ID <= 0x1F4:  # adjust command sprite IDs
                spr.ID += 0xA
            spr.y = (sprite16bit >> 9) & 0x7F
            spr.x = f.read(1)[0]
            self.sprites.append(spr)

    def importspritetileset(self, f):
        spritetileset = self.header[7]
        f.seek(0x00B039 + spritetileset*6)
        self.stripeIDs = bytearray(f.read(6))

def loadstripeIDs(f, spritetileset):
    f.seek(f.readptr(Pointers.levelgfxstripeIDs) + spritetileset*6)
    return bytearray(f.read(6))

class Object:
    """An object from a sublevel's main data.

    For manual construction: use keywords adjwidth and adjheight to set adjusted
    width/height. Adjusted width of -1 is impossible, and will produce
    an actual width of 0 (adjusted width 1)."""
    def __init__(self, **kwargs):
        # object attributes
        self.ID = 0
        self.x = 0
        self.y = 0
        self.extID = None
        self.extIDbytes = 1
        self.width = None
        self.height = None

        # used by L1Tilemap
        self.tiles = frozenset()
        self.alltiles = frozenset()
        self.lasttile = (None, None)
        self.error = None

        # if kwargs, construct an object manually
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def adjwidth(self): return self._adjlength(self.width)
    @property
    def adjheight(self): return self._adjlength(self.height)

    @adjwidth.setter
    def adjwidth(self, value): self.width = self._unadjlength(value)
    @adjheight.setter
    def adjheight(self, value): self.height = self._unadjlength(value)

    @staticmethod
    def _adjlength(length):
        """Convert an object's internal width/height to its displayed
        equivalent, to calculate the adjwidth/adjheight attributes.

        Displayed lengths are +1 if nonnegative, -1 if negative. Dimensions that
        don't exist are assumed 1, their default in-game value."""
        if length is None:
            return 1
        if length >= 0:
            return length + 1
        return length - 1

    @staticmethod
    def _unadjlength(length):
        """Convert an object's displayed width/height to its internal
        equivalent. Adjusted length -1 (impossible in-game) is treated as 1.
        Adjusted length 0 is treated as the parameter does not exist."""
        if not length:
            return None
        if length > 0:
            return length - 1
        return length + 1

    def backup(self):
        self.backup_x = self.x
        self.backup_y = self.y
        self.backup_width = self.width
        self.backup_height = self.height
        self.backup_tiles = self.tiles
        self.backup_alltiles = self.alltiles
        self.backup_lasttile = self.lasttile

    def restorebackup(self):
        try:
            self.x = self.backup_x
            self.y = self.backup_y
            self.width = self.backup_width
            self.height = self.backup_height
            self.tiles = self.backup_tiles
            self.alltiles = self.backup_alltiles
            self.lasttile = self.backup_lasttile
        except AttributeError:
            pass

    def __bytes__(self):
        # Convert an object back to its in-game byte sequence
        output = [self.ID,
                  self.y & 0xF0 | self.x >> 4,
                  (self.y & 0xF) << 4 | self.x & 0xF]
        if self.width is not None:
            output.append(self.width % 0x100)
        if self.height is not None:
            output.append(self.height % 0x100)
        if self.extID is not None:
            output += self.extID.to_bytes(self.extIDbytes, "little")
        return bytes(output)

    def idstr(self, extprefix=""):
        text = [f"{self.ID:02X}"]
        if self.extID is not None:
            if self.ID == 0 and extprefix:
                text = [extprefix]
            # nonbreaking character exists only because Qt line-breaks on
            #  periods for an unknown reason
            text.append(".\u2060")
            # 02X for 1-byte extension, 04X for 2-byte extension
            text.append(format(self.extID,
                               "0" + str(self.extIDbytes * 2) + "X"))
        return "".join(text)

    def __str__(self):
        text = [self.idstr(), f" x{self.x:02X} y{self.y:02X}"]
        if self.width is not None:
            text.append(f" w{self.adjwidth:+03X}")
        if self.height is not None:
            text.append(f" h{self.adjheight:+03X}")
        return "".join(text)
    def __repr__(self):
        return "<SMA3.Object: " + self.__str__() + ">"

class Sprite:
    "A sprite from a sublevel's sprite data."
    def __init__(self, **kwargs):
        self.ID = 0
        self.x = 0
        self.y = 0
        self.extID = 0

        # if kwargs, construct a sprite manually
        for key, value in kwargs.items():
            self.__setattr__(key, value)

    def parity(self):
        return (self.y&1)<<1 | self.x&1

    def backup(self):
        self.backup_x = self.x
        self.backup_y = self.y

    def restorebackup(self):
        try:
            self.x = self.backup_x
            self.y = self.backup_y
        except AttributeError:
            pass

    def __bytes__(self):
        # convert a sprite back to its in-game byte sequence
        output = [self.ID&0xFF, self.y<<1 | self.ID>>8, self.x, 0]
        if self.extID:
            output[3] = self.extID
        return bytes(output)

    def idstr(self):
        text = f"{self.ID:03X}"
        if self.extID:
            text += f"({self.extID:02X})"
        return text

    def __str__(self):
        return self.idstr() + f" x{self.x:02X} y{self.y:02X}"
    def __repr__(self):
        return "<SMA3.Sprite: " + self.__str__() + ">"

class Entrance(bytearray):
    """SMA3-format entrance.
    Compatible with level entrances, midway entrances, and screen exits."""

    attr = ("sublevelID", "x", "y", "anim", "byte4", "byte5")

    def __init__(self, byteinput=None):
        self += b"\x00"*6
        if byteinput is not None:
            if len(byteinput) > 6:
                byteinput = byteinput[0:6]
            self[:len(byteinput)] = byteinput

    def __getattr__(self, name):
        if name in Entrance.attr:
            return self[Entrance.attr.index(name)]
        raise AttributeError(" ".join((repr(self.__class__.__name__),
            "object has no attribute", repr(name))))

    def __setattr__(self, name, value):
        if name in Entrance.attr:
            self[Entrance.attr.index(name)] = value
        else:
            bytearray.__setattr__(self, name, value)

    def __bool__(self):
        # return false if all bytes are 0
        return self != Entrance()

    def __str__(self):
        return " ".join(f"{i:02X}" for i in self)
    def __repr__(self):
        return "<SMA3.Entrance: " + self.__str__() + ">"

    @property
    def destscreen(self):
        return coordstoscreen(*self[1:3])

# SMA3 level entrances

class MainEntrances(list):
    "List of all levels' main entrances."

    ptrref = Pointers.entrancemainptrs

    @classmethod
    def importfromROM(cls, filepath, maxlevelID=0x47):
        "Create a new instance using main entrances from the ROM."

        entrptrs = GBA.PointerTable.importtable(
            filepath, cls.ptrref, vstart=cls.ptrref.vdest, vlen=0x46)
        mainentrances = cls()
        mainentrances.ptrs = entrptrs
        datablock = None

        with GBA.Open(filepath, "rb") as f:
            for levelID in range(maxlevelID+1):
                try:
                    # import entrance
                    ptr = entrptrs[levelID]
                    f.seek(ptr)
                    mainentrances.append(Entrance(f.read(6)))

                    # expand datablock if needed
                    if not datablock:
                        datablock = [ptr, 6]
                    elif ptr < datablock[0]:
                        datablock[1] += datablock[0] - ptr
                        datablock[0] = ptr
                    elif ptr+6 > datablock[0] + datablock[1]:
                        datablock[1] = ptr+6 - datablock[0]
                except (ValueError, IndexError):
                    # pointer isn't valid, or index higher than vanilla table
                    mainentrances.append(Entrance())

            # account for Advynia-added end-of-data marker
            f.seek(sum(datablock))
            if f.read(4) == b"\xFF\xFF\xFF\xFF":
                datablock[1] += 4

        mainentrances.datablock = datablock
        return mainentrances

    @classmethod
    def importfromSNES(cls, filepath):
        with SNES.Open(filepath, "rb") as f:
            # read offsets to table
            offsets = []
            f.seek(PointersSNES.entrancemainoffsets)
            f.seek(f.readint(3))
            for levelID in range(Constants.maxlevelID+1):
                offsets.append(f.readint(2))

            f.seek(PointersSNES.entrancemaintable)
            entrtable = f.readint(3)

            mainentrances = cls()
            for offset in offsets:
                if offset % 4:  # misaligned offset -> probably not valid
                    mainentrances.append(Entrance())
                else:
                    try:
                        f.seek(entrtable + offset)
                        mainentrances.append(Entrance(f.read(4)))
                    except ValueError:
                        mainentrances.append(Entrance())

        swapExtraSecret(mainentrances)

        return mainentrances

    @classmethod
    def importfrombytes(cls, bytedata, offsets, entrancelen=6):
        """Create a new instance from byte data, given a sequence of offsets to
        each entrance."""

        mainentrances = cls()
        for offset in offsets:
            if offset is not None:
                mainentrances.append(Entrance(
                    bytedata[offset : offset + entrancelen]))
            else:
                 mainentrances.append(Entrance())

        # ensure all level IDs are included, if offset table was shorter
        while len(mainentrances) < Constants.maxlevelID + 1:
            mainentrances.append(Entrance())

        return mainentrances

    def tobytearray(self, *, entrancelen=6, endmarker=True):
        """Convert to a byte sequence. Also return the offsets necessary to
        generate level-indexed pointers."""

        bytedata = bytearray()
        offsets = []
        for entr in self:
            if entr:
                offsets.append(len(bytedata))
                bytedata += entr[0:entrancelen]
            else:
                offsets.append(None)
        if endmarker:
            bytedata += b"\xFF\xFF\xFF\xFF"

        return bytedata, offsets

class MidwayEntrances(list):
    "List containing a list of midway entrances per level."

    ptrref = Pointers.entrancemidwayptrs

    @classmethod
    def importfromROM(cls, filepath, maxlevelID=0x47, maxmidpoints=4,
                      midwaylen=4):
        """Create a new instance using midway entrances from the ROM,
        auto-splitting by level based on the distance between pointers."""

        # import midway entrance pointers
        midwayptrs = GBA.PointerTable.importtable(
            filepath, cls.ptrref, vstart=cls.ptrref.vdest, vlen=0x46)
        midwayentrances = cls()
        midwayentrances.midwaylen = midwaylen
        midwayentrances.ptrs = midwayptrs
        datablock = None
        for levelID in range(maxlevelID+1):
            midwayentrances.append([])

        # sort pointers
        # also remove 0 (vanilla filler pointer) if present, and add 0xFFFFFFFF
        sortedptrs = sorted((set(midwayptrs) | {0xFFFFFFFF}) - {0})

        with GBA.Open(filepath, "rb") as f:
            # use sortedptrs to import midway entrances, without duplicating
            for ptr, nextptr in itertools.pairwise(sortedptrs):
                levelID = midwayptrs.index(ptr)

                try:
                    f.seek(ptr)
                    midwaycount = min((nextptr - ptr) // midwaylen, maxmidpoints)
                    for i in range(midwaycount):
                        entr = Entrance(f.read(midwaylen))
                        if entr[0:4] == b"\xFF\xFF\xFF\xFF":
                            break
                        midwayentrances[levelID].append(entr)

                    # expand datablock if needed
                    if not datablock:
                        datablock = [ptr, 0]
                    if ptr < datablock[0]:
                        datablock[1] += datablock[0] - ptr
                        datablock[0] = ptr
                    elif f.tell() > datablock[0] + datablock[1]:
                        datablock[1] = f.tell() - datablock[0]

                except (ValueError, IndexError):
                    pass

            # account for Advynia-added end-of-data marker
            f.seek(sum(datablock))
            if f.read(4) == b"\xFF\xFF\xFF\xFF":
                datablock[1] += 4

        midwayentrances.datablock = datablock
        return midwayentrances

    @classmethod
    def importfromSNES(cls, filepath, *, force4=True):
        with SNES.Open(filepath, "rb") as f:
            f.seek(PointersSNES.entrancemidwaybank)
            bank = f.readint(1)

            # determine table location and max offset
            f.seek(PointersSNES.entrancemidwaytable)
            entrtable = bank << 0x10 | f.readint(2)
            maxoffset = ((bank+1) << 0x10) - entrtable

            # read offsets to table
            offsets = []
            f.seek(PointersSNES.entrancemidwayoffsets)
            f.seek(bank << 0x10 | f.readint(2))
            for levelID in range(Constants.maxlevelID+1):
                num = f.readint(2)
                if num % 4 or num >= maxoffset:
                    offsets.append(None)
                else:
                    offsets.append(num)

            midwayentrances = cls()
            for levelID in range(Constants.maxlevelID+1):
                midwayentrances.append([])

            # read entrances
            if force4:
                # read 4 midway entrances for every level
                for levelID, offset in enumerate(offsets):
                    if offset is not None:
                        f.seek(entrtable + offset)
                        for i in range(4):
                            midwayentrances[levelID].append(Entrance(f.read(4)))
            else:
                # use sorted offsets to avoid duplicating
                sortedoffsets = sorted((set(offsets) | {maxoffset}) - {None})
                for offset, nextoffset in itertools.pairwise(sortedoffsets):
                    try:
                        levelID = offsets.index(offset)
                        f.seek(entrtable + offset)
                        midwaycount = min((nextoffset - offset) // 4, 4)
                        for i in range(midwaycount):
                            midwayentrances[levelID].append(Entrance(f.read(4)))
                    except ValueError:
                        pass

        swapExtraSecret(midwayentrances)

        return midwayentrances

    @classmethod
    def importfrombytes(cls, bytedata, offsets, midwaylen=6):
        """Create a new instance from byte data, given a sequence of offsets to
        each level's midway entrances."""

        midwayentrances = cls()
        for _ in offsets:
            midwayentrances.append([])

        # iterate over pairs of consecutive offsets; the last offset uses
        #  len(bytedata) as its end
        sortedoffsets = sorted((set(offsets) | {len(bytedata)}) - {None})
        for offset, nextoffset in itertools.pairwise(sortedoffsets):
            levelID = offsets.index(offset)
            for i in range(offset, nextoffset, midwaylen):
                entr = Entrance(bytedata[i:i+midwaylen])
                if entr[0:4] == b"\xFF\xFF\xFF\xFF":
                    # don't import end-of-data marker, if it exists
                    break
                midwayentrances[levelID].append(entr)

        # ensure all level IDs are included, if offset table was shorter
        while len(midwayentrances) < Constants.maxlevelID + 1:
            midwayentrances.append([])

        return midwayentrances

    def tobytearray(self, *, midwaylen=None, endmarker=True):
        """Convert to a byte sequence. Also return the offsets necessary to
        generate level-indexed pointers.
        Optionally can override self.midwaylen."""

        if midwaylen is None:
            midwaylen = self.midwaylen

        bytedata = bytearray()
        offsets = []
        for level in self:
            if level:
                offsets.append(len(bytedata))
                for entr in level:
                    bytedata += entr[0:midwaylen]
            else:
                offsets.append(None)
        if endmarker:
            bytedata += b"\xFF\xFF\xFF\xFF"

        return bytedata, offsets

def importlevelentrances(filepath, maxlevelID=0x47, maxmidpoints=4,
        midwaylen=4):
    "Convenience function to import both main and midway entrances."
    return (MainEntrances.importfromROM(filepath, maxlevelID),
            MidwayEntrances.importfromROM(
                filepath, maxlevelID, maxmidpoints, midwaylen))

def swapExtraSecret(seq):
    """Swap indexes corresponding to Extra/Secret levels.
    For use in porting SNES/GBA level-indexed data."""
    for secretID in range(8, 0x48, 0xC):
        extraID = secretID + 1
        seq[secretID], seq[extraID] = seq[extraID], seq[secretID]

def import_tile16interact(filepath, length=0xA9):
    "Import the 16x16 tile interaction values/flags for each high byte."
    output = []
    with GBA.Open(filepath, "rb") as f:
        f.readseek(Pointers.tile16interact)
        for _ in range(length):
            output.append(f.read(3))
            f.read(1)  # discard every 4th byte
    return output

def tile16interactstr(tileID, interactmap, numprefix=False, sep="\n"):
    highbyte = tileID >> 8
    flags, extra, slope = interactmap[highbyte]
    proplist = []
    if flags & 0x10: proplist.append("lava")
    if flags & 0x08: proplist.append("liquid")
    if flags & 0x04: proplist.append(f"slope (type {slope:02X})")
    if flags & 0x02: proplist.append("solid")
    if flags & 0x01: proplist.append("semisolid")
    if flags & 0x20: proplist.append("?[20]")
    if not proplist: proplist.append("non-solid")
    propjoined = ", ".join(proplist)
    propjoined = str.capitalize(propjoined[0]) + propjoined[1:]

    text = []
    # flag interaction text
    if numprefix: text.append(f"{flags:02X}: ")
    text.append(f"{propjoined}{sep}")

    # extra interaction text
    specialstr = Constants.tile16interact_special_highbyte.get(highbyte,
              Constants.tile16interact_special_full.get(tileID))
    if specialstr is not None:
        if numprefix: text.append("Special: ")
        text.append(specialstr)
    else:
        if numprefix: text.append(f"{extra:02X}: ")
        text.append(Constants.tile16interact_extra.get(extra, "???"))

    return "".join(text)
