"""SMA3 Level
Classes and functions for SMA3 levels and sublevels."""

# standard library imports
import os

##if __name__ == "__main__":
##    # allow testing as if it's from the Advynia main directory
##    import os, sys
##    os.chdir("../..")
##    sys.path.append(".")

# import from other files
from AdvGame import AdvGame, GBA, SNES
from AdvGame.SMA3 import Pointers, Constants

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
        output = "".join((
            str(worldnum), "-", Constants.levelnumrighthalf[cursorpos]))
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
    def __init__(self, obj65_7byte=False):
        # initialize a null sublevel
        self.ID = None
        self.header = [0]*0xF
        self.objects = []
        self.exits = {}
        self.sprites = []

        self.datablocks = {}

        self.fromfile = False

        # Advynia patches
        self.stripeIDs = None
        self.music = None
        self.obj65_7byte = obj65_7byte

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

    @property
    def size(self):
        return len(self.exportmaindata()), (len(self.sprites)+1)*4

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
        while (screenindex := f.read(1)[0]) != 0xFF:
            self.exits[screenindex] = Entrance(f.read(entrlength))

    def importspritedata(self, f):
        "Import a sublevel's sprite data from a file object."
        while (sprite32bit := int.from_bytes(f.read(4), "little")) !=\
               0xFFFFFFFF:
            spr = Sprite(
                ID = sprite32bit & 0x1FF,
                y = (sprite32bit >> 9) & 0x7F,
                x = (sprite32bit >> 16) & 0xFF,
                param = sprite32bit >> 24
                )
            self.sprites.append(spr)

    def importspritetileset(self, f, sublevelstripes=False):
        spritetileset = self.ID if sublevelstripes else self.header[7]
        f.seek(f.readptr(Pointers.levelgfxstripeIDs) + spritetileset*6)
        self.stripeIDs = bytearray(f.read(6))

    def exportmaindata(self):
        "Export a sublevel's main data (header, objects, exits) to a bytearray."
        output = bytearray()

        # process header values
        bitoffset = 0
        newbyte = 0
        for i, bitcount in enumerate(self.headerbitcounts):
            for j in reversed(range(bitcount)):
                # read from highest to lowest bit
                bit = self.header[i]>>j & 1
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
            f.seek(0x01B08F)
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

class Object:
    """An object from a sublevel's main data.

    For manual construction: use keywords adjwidth and adjheight to set adjusted
    width/height. Adjusted width of -1 is impossible, and will produce
    an actual width of 0 (adjusted width 1)."""
    def __init__(self, **kwargs):
        self.ID = 0
        self.x = 0
        self.y = 0
        self.extID = None
        self.extIDbytes = 1
        self.width = None
        self.height = None

        self.tiles = frozenset()
        self.alltiles = frozenset()
        self.lasttile = (None, None)

        # if kwargs, construct an object manually
        for key, value in kwargs.items():
            self.__setattr__(key, value)

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

    def restorebackup(self):
        try:
            self.x = self.backup_x
            self.y = self.backup_y
            self.width = self.backup_width
            self.height = self.backup_height
        except AttributeError:
            pass

    def __bytes__(self):
        "Convert an object back to its in-game byte sequence."
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
        text = [format(self.ID, "02X")]
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
        text = [self.idstr(),
                " x", format(self.x, "02X"),
                " y", format(self.y, "02X")]
        if self.width is not None:
            text += [" w", format(self.adjwidth, "+03X")]
        if self.height is not None:
            text += [" h", format(self.adjheight, "+03X")]
        return "".join(text)
    def __repr__(self):
        return "<SMA3.Object: " + self.__str__() + ">"

class Sprite:
    "A sprite from a sublevel's sprite data."
    def __init__(self, **kwargs):
        self.ID = 0
        self.x = 0
        self.y = 0
        self.param = 0

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
        "Convert a sprite back to its in-game byte sequence."
        output = (self.ID&0xFF, self.y<<1 | self.ID>>8, self.x, self.param)
        return bytes(output)

    def idstr(self):
        return format(self.ID, "03X")

    def __str__(self):
        text = [self.idstr()]
        if self.param:
            text += ["(", format(self.param, "02X"), ")"]
        text += [" x", format(self.x, "02X"),
                 " y", format(self.y, "02X")]
        return "".join(text)
    def __repr__(self):
        return "<SMA3.Sprite: " + self.__str__() + ">"

class Entrance(bytearray):
    """SMA3-format entrance.
    Compatible with level entrances, midway entrances, and screen exits."""

    attr = ("sublevel", "x", "y", "anim", "byte4", "byte5")

    def __init__(self, byteinput=None):
        self += b"\x00"*6
        if byteinput is not None:
            if len(byteinput) > 6:
                print("Warning: Entrance length is limited to 6 bytes. "
                      "Input ", byteinput, " has length ", len(byteinput), ".",
                      sep="")
                byteinput = byteinput[:6]
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
        return " ".join(format(i, "02X") for i in self)
    def __repr__(self):
        return "<SMA3.Entrance: " + self.__str__() + ">"


# SMA3 level entrances

def importmainentrances(filepath, maxlevelID=0x47):
    entrptrs = GBA.PointerTable.importtable(
        filepath, Pointers.entrancemainptrs[0],
        vstart=Pointers.entrancemainptrsvanilla, vlen=0x46)
    mainentrances = AdvGame.ListData()
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

def importmidwayentrances(filepath, maxlevelID=0x47, maxmidpoints=4,
                          midwaylen=4):
    """Import midway entrances, auto-splitting by level based on the distance
    between pointers."""
    # import midway entrance pointers
    midwayptrs = GBA.PointerTable.importtable(
        filepath, Pointers.entrancemidwayptrs,
        vstart=Pointers.entrancemidwayptrsvanilla, vlen=0x46)
    midwayentrances = AdvGame.ListData()
    midwayentrances.ptrs = midwayptrs
    datablock = None
    for levelID in range(maxlevelID+1):
        midwayentrances.append([])

    # sort pointers
    midwayptrset = set(midwayptrs)
    midwayptrset.discard(0)  # remove 0, the vanilla filler pointer, if present
    midwayptrset.add(0xFFFFFFFF)
    sortedptrs = sorted(midwayptrset)

    with GBA.Open(filepath, "rb") as f:
        # use sorted pointers to import midway entrances, without duplicating
        for i, ptr in enumerate(sortedptrs):
            if ptr == 0xFFFFFFFF:
                break
            levelID = midwayptrs.index(ptr)

            try:
                f.seek(ptr)
                midwaycount = min(
                    (sortedptrs[i+1] - ptr)//midwaylen, maxmidpoints)
                for j in range(midwaycount):
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

def importlevelentrances(filepath, maxlevelID=0x47, maxmidpoints=4,
        midwaylen=4):
    "Convenience function to import both main and midway entrances."
    return (importmainentrances(filepath, maxlevelID),
        importmidwayentrances(filepath, maxlevelID, maxmidpoints, midwaylen))
