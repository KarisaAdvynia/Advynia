# standard library imports
import math, os

if __name__ == "__main__":
    # allow testing as if it's from the Advynia main directory
    import os, sys
    os.chdir("../..")
    sys.path.append(".")

# import from other files
from AdvGame import General, GBA, SNES, GameGraphics
from AdvGame.SMA3 import Pointers, Constants


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

        # retrieve object lengths
        if not objlengthprop:
            objlengthraw, _ = GBA.importdata(
                filepath, GBA.readptr(filepath, Pointers.objlengthprop),
                length=0xFF)
            # only lowest 2 bits of table are used for length properties
            sublevel.objlengthprop = [byte&3 for byte in objlengthraw]
            if objlengthraw[0x65] & 0x3C:
                sublevel.obj65_7byte = True

        with GBA.Open(filepath) as f:
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
        while True:
            objectID = f.read(1)[0]
            if objectID == 0xFF:  # end of data
                break
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
                obj.width = int.from_bytes(
                    f.read(1), byteorder="little", signed=True)
            if self.objlengthprop[objectID] != 0:
                # if property 1 or 2, there's a signed height byte
                obj.height = int.from_bytes(
                    f.read(1), byteorder="little", signed=True)
            if obj.ID in (0x64, 0x65):
                if self.obj65_7byte and obj.ID == 0x65:
                    obj.extID = int.from_bytes(f.read(2), byteorder="little")
                    obj.extIDbytes = 2
                else:
                    obj.ID == 0x63
            self.objects.append(obj)

    def importexitdata(self, f, entrlength=6):
        "Import a sublevel's screen exit data from a file object."
        while True:
            screenindex = f.read(1)[0]
            if screenindex == 0xFF:
                break
            self.exits[screenindex] = Entrance(f.read(entrlength))

    def importspritedata(self, f):
        "Import a sublevel's sprite data from a file object."
        while True:
            sprite32bit = int.from_bytes(f.read(4), byteorder="little")
            if sprite32bit == 0xFFFFFFFF:
                break            

            spr = Sprite()
            spr.ID = sprite32bit & 0x1FF
            spr.y = (sprite32bit >> 9) & 0x7F
            spr.x = (sprite32bit >> 16) & 0xFF
            spr.param = sprite32bit >> 24

            self.sprites.append(spr)

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
    "Subclassed for importing SNES-format data."

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

    def importspritetileset(self, f):
        spritetileset = self.header[7]
        f.seek(0x00B039 + spritetileset*6)
        self.stripeIDs = bytearray(f.read(6))

    def importmaindata(self, f):
        headerraw = f.read(10)
        self.extractheader(headerraw, self.headerbitcountsSNES)
        self.importobjectdata(f)
        self.importexitdata(f, entrlength=4)
        return f.tell()

    def importspritedata(self, f):
        while True:
            sprite16bit = int.from_bytes(f.read(2), byteorder="little")
            if sprite16bit == 0xFFFF:
                break            

            spr = Sprite()
            spr.ID = sprite16bit & 0x1FF
            if 0x1BA <= spr.ID <= 0x1F4:  # adjust command sprite IDs
                spr.ID += 0xA
            spr.y = (sprite16bit >> 9) & 0x7F
            spr.x = f.read(1)[0]

            self.sprites.append(spr)

        return f.tell()

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
        self.tiles = set()
        self.alltiles = set()

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

    def _adjlength(self, length):
        """Convert an object's internal width/height to its displayed
        equivalent, to calculate the adjwidth/adjheight attributes.

        Displayed lengths are +1 if nonnegative, -1 if negative. Dimensions that
        don't exist are assumed 1, their default in-game value."""
        if length is None:
            return 1
        if length >= 0:
            return length + 1
        return length - 1

    def _unadjlength(self, length):
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

    def restorebackup(self):
        try:
            self.x = self.backup_x
            self.y = self.backup_y
            self.width = self.backup_width
            self.height = self.backup_height
            self.tiles = self.backup_tiles
            self.alltiles = self.backup_alltiles
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
            output += self.extID.to_bytes(self.extIDbytes, byteorder="little")
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

# SMA3 level entrances

def importmainentrances(filepath, maxlevelID=0x47):
    entrptrs = GBA.PointerTable.importtable(
        filepath, Pointers.entrancemainptrs[0],
        vstart=Pointers.entrancemainptrsvanilla, vlen=0x46)
    mainentrances = General.ListData()
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
                elif ptr+6 > datablock[0]+datablock[1]:
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
    midwayentrances = General.ListData()
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
    return (
        importmainentrances(filepath, maxlevelID),
        importmidwayentrances(filepath, maxlevelID, maxmidpoints, midwaylen))

# SMA3 text

def importmessage(filepath, ID_or_ptr):
    """Import text data, parsing multi-byte commands according to SMA3's most
    common command format."""
    ## need to split story intro/credits from this!
    ##  commands 01-03 only include 1 additional byte for story intro/credits

    # Manual override from pointer
    if ID_or_ptr >= 0x08000000:
        ptr = ID_or_ptr
    else:
        msgptrtable = GBA.readptr(filepath, Pointers.messageptrs)
        ptr = GBA.readptr(filepath, msgptrtable, index=ID_or_ptr)

    if not ptr:
        return None

    with open(filepath, "rb") as f:
        startoffset = GBA.addrtofile(ptr)
        f.seek(startoffset)

        output = []
        while True:
            nextbyte = f.read(1)
            charID = nextbyte[0]   # integer
            command = None
            if charID == 0xFF:   # next byte is command ID
                command = f.read(1)
                if command[0] == 0xFF:   # end of data
                    break
                elif command[0] == 0x60:
                    # command 60 includes 7 additional bytes
                    command += f.read(7)
                elif 1 <= command[0] <= 3:
                    # commands 01-03 include 1 additional byte
                    command += f.read(1)
                elif output:
                # if command is not 60, check if duplicate of previous command
                    try:   # is previous entry a command?
                        output[-1][1][0]
                    except TypeError:
                        pass
                    else:
                        if output[-1][1][0] == command[0]:
                            output[-1][2] += 1  # increment duplicate count
                            continue

            output.append([charID, command, 0])

    return output

def importlevelname(filepath, levelID):
    """Import text data, using the level name command set."""
    nameptrtable = GBA.readptr(filepath, Pointers.levelnameptrs)
    ptr = GBA.readptr(filepath, nameptrtable, index=levelID)

    if not ptr:
        return None

    with open(filepath, "rb") as f:
        startoffset = GBA.addrtofile(ptr)
        f.seek(startoffset)

        output = []
        while True:
            nextbyte = f.read(1)
            charID = nextbyte[0]   # integer
            command = None
            if charID == 0xFE:   # next 2 bytes are part of command
                command = f.read(2)
            if charID == 0xFD:   # end of data
                break
            output.append([charID, command, 0])

    return output

def importfileselecttext(filepath, ptr):
    """Import text data, using the file select command set."""
    with open(filepath, "rb") as f:
        startoffset = GBA.addrtofile(ptr)
        f.seek(startoffset)

        output = []
        while True:
            nextbyte = f.read(1)
            charID = nextbyte[0]   # integer
            command = None
            if charID == 0xFF:   # next 2 bytes are part of command
                command = f.read(2)
                if command[0] == 0xFF:   # end of data
                    break
            output.append([charID, command, 0])

    return output

msgnewlines = (0x05, 0x06, 0x07, 0x08, 0x0E)
def printabletext(textdata):
    """Convert imported SMA3 text data to a printable/editable string."""
    if not textdata:
        return ""

    textstr = ""

    processcommand = 0
    commandID = 0xFF
    texttype = "Message"
    if textdata[0][0] == 0xFE:
        texttype = "Level name"
        commandID = 0xFE
    elif textdata[0][0] == 0xFF:
        if textdata[0][1][0] == 0x01:
            texttype = "Credits"
        elif textdata[0][1][0] == 0x02:
            texttype = "Story intro"

    for entry in textdata:
        entryID = entry[0]
        arg = entry[1]
        repcount = entry[2]
        
        if entryID == commandID:
            commandstr = "@{"
            for i, byte in enumerate(arg):
                commandstr += format(byte, "02X")
                if i == len(arg)-1:
                    # insert repcount after final byte of command, if it exists
                    if repcount:
                        commandstr += "#" + str(repcount+1)
                    commandstr += "}"
                else:
                    commandstr += ","
            if textstr:
                # if string is not empty,
                # add newline before commands that function as a newline
                if texttype == "Level name" or\
                   (texttype == "Message" and (arg[0] in msgnewlines)) or\
                   (texttype == "Credits" and arg[0] == 0x01) or\
                   (texttype == "Story intro" and arg[0] == 0x02):
                    textstr += "\n"
                
            textstr += commandstr
            
        elif Constants.sma3char[entryID]:  # if byte has a decoding
            textstr += Constants.sma3char[entryID]
        else:    # if byte does not have a decoding, use backslash hex code
            textstr += "\\{" + format(entryID, "02X") + "}"
            
    return textstr

# SMA3 Graphics

class LayerVRAM(GameGraphics):
    """Simulated GBA VRAM, of the layer tiles loaded during a standard SMA3
    sublevel. Used to display game graphics in the GUI. Includes functions to
    load specific tilesets."""
    def __init__(self, filepath, layer1ID=None, layer2ID=None, layer3ID=None,
                 animID=None):
        super().__init__(tilesize=0x20)

        self.tilemap = {}
        self.animated = GameGraphics()
        self.layer1ID = None
        self.layer2ID = None
        self.layer3ID = None
        self.animID = None

        # load global graphics
        for ptr, offset, size in Pointers.levelgfxlayerglobal:
            self.replacegraphics(GameGraphics(GBA.importdata(
                filepath, GBA.readptr(filepath, ptr), size)[0]), offset)

        # load global animated graphics, first frame
        for ptr, offset, size in Pointers.levelgfxanimglobal:
            self.replacegraphics(GameGraphics(GBA.importdata(
                filepath, ptr, size)[0]), offset)

        if layer1ID is not None:
            self.loadL1graphics(filepath, layer1ID)
        if layer2ID is not None:
            self.loadL2graphics(filepath, layer2ID)
        if layer3ID is not None:
            self.loadL3graphics(filepath, layer3ID)
        if animID is not None:
            self.loadanimgraphics(filepath, animID)

    def loadL1graphics(self, filepath, tilesetID):
        self.layer1ID = tilesetID
        tableptr = Pointers.levelgfxL1 + tilesetID*0xC
        if tilesetID > 0xF:  # higher values are treated as W6 alternate tilesets
            tableptr = Pointers.levelgfxL1W6 + (tilesetID-0x10)*0xC
        self._loadgraphicsloop(filepath, tableptr, (0x2000, 0x3000, 0))

        if self.animID in (0x7, 0xD):
            # animation 7 uses different graphics in tileset A
            self.loadanimgraphics(filepath, 7)

    def loadL2graphics(self, filepath, imageID):
        self.layer2ID = imageID
        tableptr = Pointers.levelgfxL2 + imageID*8
        self._loadgraphicsloop(filepath, tableptr, (0x5000, 0x6000))
        self.tilemap[2] = self.loadL23image(filepath, 2, imageID)

    def loadL3graphics(self, filepath, imageID):
        self.layer3ID = imageID
        tableptr = Pointers.levelgfxL3 + imageID*8
        self._loadgraphicsloop(filepath, tableptr, (0x7000, 0x8000))
        self.tilemap[3] = self.loadL23image(filepath, 3, imageID)

    def loadanimgraphics(self, filepath, animID):
        self.animID = animID

        # overwrite old animation with blank graphics
        self.animated.clear()

        animgfxptrs = []
        if animID in Pointers.levelgfxAnimIDs:
            animgfxptrs += Pointers.levelgfxAnimIDs[animID]

        if animID == 0x06:
##            if self.layereffectsID == 0xA:
##                animgfxptrs += Pointers.levelgfxAnimIDs[(0x06,0x0A)]
            # else, animation 06 uses the same graphics as 05
            animgfxptrs += Pointers.levelgfxAnimIDs[0x5]
        if animID == 0x0B:  # animation 0B loads both 02 and 0A
            animgfxptrs += Pointers.levelgfxAnimIDs[0x2]
            animgfxptrs += Pointers.levelgfxAnimIDs[0xA]
        elif animID == 0x0D:  # animation 0D loads both 05 and 07
            animgfxptrs += Pointers.levelgfxAnimIDs[0x5]
            animgfxptrs += Pointers.levelgfxAnimIDs[0x7]
        elif animID == 0x0E:  # animation 0E loads both 05 and 0C
            animgfxptrs += Pointers.levelgfxAnimIDs[0x5]
            animgfxptrs += Pointers.levelgfxAnimIDs[0xC]
        elif animID == 0x11:  # animation 11 loads both 03 and 0C
            animgfxptrs += Pointers.levelgfxAnimIDs[0x3]
            animgfxptrs += Pointers.levelgfxAnimIDs[0xC]

        if animID in (0x07, 0x0D) and self.layer1ID == 0xA:
            # animation 07 uses different graphics in tileset A
            animgfxptrs[-4:] = Pointers.levelgfxAnimIDs[(0x07,0x0A)]

        if animgfxptrs:
            for ptr, offset, size in animgfxptrs:
                self.animated.replacegraphics(GameGraphics(GBA.importdata(
                    filepath, ptr, size)[0]), offset)
        elif animID == 0:  # overwrite animated region with blank tiles
            self.animated.replacegraphics(GameGraphics(bytes(0x800)), 0x4000)
        elif animID == 0x09:  # compressed animation
            graphics = GameGraphics(GBA.decompress(
                filepath, GBA.readptr(filepath, Pointers.levelgfxAnim09))[0])
            # not entirely documented; these offsets are estimates
            self.animated.replacegraphics(graphics[0x170:0x178], 0x8C00)
            self.animated.replacegraphics(graphics[0x178:0x180], 0x8E00)
        elif animID == 0x12:  # compressed animation
            graphics = GameGraphics(GBA.decompress(
                filepath, GBA.readptr(filepath, Pointers.levelgfxAnim12))[0])
            self.animated.replacegraphics(graphics[0:0x80], 0)
            self.animated.replacegraphics(graphics[0x80:0x90], 0x3E00)

    def _loadgraphicsloop(self, filepath, tableptr, offsets):
        for offset in offsets:
            graphicsptr = GBA.readmultiptr(filepath, tableptr, 2)
            self.replacegraphics(GameGraphics(GBA.importdata(
                filepath, graphicsptr, -1)[0]), offset)
            tableptr += 4

    def loadL23image(self, filepath, layer, imageID):
        """Import the tilemap for a layer 2 or 3 image."""
        ptr = GBA.readptr(filepath, Pointers.leveltilemapL23[layer], imageID)
        tilemapraw, _ = GBA.decompress(filepath, ptr)
        tilemap = []
        if len(tilemapraw) % 2 != 0:
            raise ValueError("Tilemap data length " + hex(len(rawdata)) +\
                  " does not correspond to an integer number of tiles.")
        for i in range(len(tilemapraw)//2):
            tilemap.append(
                int.from_bytes(tilemapraw[2*i:2*i+2], byteorder="little"))
        return tilemap

class SpriteVRAM(GameGraphics):
    def __init__(self, filepath, spritetileset=None, stripeIDs=None):
        super().__init__(tilesize=0x20)

        self.stripeIDs = bytearray(6)
        self.stripes = {}

        # load global graphics
        for ptr, offset, size in Pointers.levelgfxspriteglobal:
            self.replacegraphics(GameGraphics(GBA.importdata(
                filepath, GBA.readptr(filepath, ptr), size)[0]), offset)

        if stripeIDs is not None:
            for i, stripeID in enumerate(stripeIDs):
                self.loadstripe(filepath, i, stripeID)
        elif spritetileset is not None:
            self.loadstripes(filepath, spritetileset)

    def loadstripes(self, filepath, spritetileset):
        with GBA.Open(filepath, "rb") as f:
            idptr = f.readptr(Pointers.levelgfxstripeIDs) + spritetileset*6
            graphicsptrs = f.readptr(Pointers.levelgfxstripe) +\
                           spritetileset*0x18

            stripeptrs = []
            f.seek(idptr)
            self.stripeIDs[:] = f.read(6)
            for i in range(6):
                stripeptrs.append(f.readmultiptr(graphicsptrs + 4*i, 2))

        self.stripes.clear()
        for stripeID, graphicsptr in zip(self.stripeIDs, stripeptrs):
            self.stripes[stripeID] = GameGraphics(GBA.importdata(
                filepath, graphicsptr, -1)[0])

    def loadstripe(self, filepath, index, stripeID):
        oldID = self.stripeIDs[index]
        if oldID and self.stripeIDs.count(oldID) == 1:
            # delete graphics only if there's exactly one instance of the old ID
            del self.stripes[oldID]

        self.stripeIDs[index] = stripeID
        ptr = Pointers.levelgfxstripesbyID[stripeID]
        graphicsptr = GBA.readptr(filepath, ptr)
        self.stripes[stripeID] = GameGraphics(GBA.importdata(
                filepath, graphicsptr, -1)[0])

def loadstripeIDs(filepath, spritetileset):
    with GBA.Open(filepath, "rb") as f:
        f.seek(f.readptr(Pointers.levelgfxstripeIDs) + spritetileset*6)
        return f.read(6)

class LevelPalette(list):
    """Simulated palette during a standard SMA3 sublevel, in 15-bit color
    format. Includes main 0x200-byte palette and 0x18-byte background gradient."""
    def __init__(self, filepath, layer1ID=None, layer2ID=None, layer3ID=None,
                 layer3image=None, BGpalID=None, spritepalID=None, yoshipalID=0,
                 showredcoins=True):
        self.showredcoins = showredcoins
        self.extend([0]*0x200)
        self.BGgradient = [0]*0x18
        self.colortype = ["Unknown"]*0x200

        self.layer1ID = None
        self.layer2ID = None
        self.layer3ID = None
        self.layer3image = None
        self.BGpalID = None

        with GBA.Open(filepath, mode="rb") as f:
            # load global layer 1 colors (fixed color table index of 0x98)
            f.seek(Pointers.colortable + 0x98)
            for paletterow in (1, 2, 3):
                for i in range(1, 0xC):
                    colorID = paletterow<<4 | i
                    self[colorID] = f.readint(2)
                    self.colortype[colorID] = "Layer 1 Global"

            # load global sprite colors
            f.readseek(Pointers.levelpal100)
            for colorID in range(0x100, 0x150):
                self[colorID] = int.from_bytes(f.read(2), byteorder="little")
                self.colortype[colorID] = "Sprite Global"
            f.readseek(Pointers.levelpal180)
            for colorID in range(0x180, 0x1F8):
                self[colorID] = int.from_bytes(f.read(2), byteorder="little")
                self.colortype[colorID] = "Sprite Global"
            f.readseek(Pointers.levelpal1F8)
            for colorID in range(0x1F8, 0x200):
                self[colorID] = int.from_bytes(f.read(2), byteorder="little")
                self.colortype[colorID] = "Message Global"

            self._setuninitialized(0x80, 0xD0)
            self.colortype[0xD0:0xE0] = ["Unused SNES leftover/Yoshi Palette"]*0x10
            self.colortype[0xE0:0xF0] = ["Unused SNES leftover/Sprite Palette"]*0x10

        if BGpalID is not None:
            self.loadBGpalette(filepath, BGpalID)
        if layer1ID is not None:
            self.loadL1palette(filepath, layer1ID)
        if layer2ID is not None:
            self.loadL2palette(filepath, layer2ID)
        if layer3ID is not None:
            self.loadL3palette(filepath, layer3ID)
        if layer3image is not None:
            self.loadL3imagepal(filepath, layer3image)
        if spritepalID is not None:
            self.loadspritepalette(filepath, spritepalID)
        self.loadyoshipalette(filepath, yoshipalID)

        self.colortype[0xF0:0x100] = ["Red Coin Palette"]*0x10

        # label transparent colors
        for colorID in range(0x10, 0x200, 0x10):
            self.colortype[colorID] = "Transparent"

    def loadBGpalette(self, filepath, paletteID):
        self.BGpalID = paletteID
        with GBA.Open(filepath, mode="rb") as f:
            colorindex = paletteID*2
            f.seek(Pointers.colortable + colorindex)
            self[0] = f.readint(2)
            self.colortype[0] = "Background Color " + format(paletteID, "02X")

            for colorID in range(0x80, 0xA0, 4):
                # account for layer 3 image region copying background color
                if self.colortype[colorID].startswith("Background Color"):
                    self[colorID] = self[0]
                    self.colortype[colorID] = self.colortype[0]

            if paletteID >= 0x10:
                f.seek(f.readptr(Pointers.levelBGgradient) + paletteID*4)
                colorindex = f.readint(2)
                f.seek(Pointers.colortable + colorindex)
                for i in range(0x18):
                    self.BGgradient[i] = f.readint(2)
            else:
                self.BGgradient = [self[0]]*0x18

    def loadL1palette(self, filepath, paletteID):
        self.layer1ID = paletteID
        with GBA.Open(filepath, mode="rb") as f:
            f.seek(f.readptr(Pointers.levelpalL1) + paletteID*2)
            colorindex = f.readint(2)
            f.seek(Pointers.colortable + colorindex)
            # layer 1 palettes load to 2 distinct rectangular regions
            for paletteIDrange, colorIDrange in (((4, 5), range(1, 0x10)),
                                                 ((1, 2, 3), range(0xC, 0x10))):
                for paletterow in paletteIDrange:
                    for i in colorIDrange:
                        colorID = paletterow<<4 | i
                        self[colorID] = f.readint(2)
                        self.colortype[colorID] = "Layer 1 Palette " +\
                                                  format(paletteID, "X")

        # red coin palette is a copy of palette 1 or 2
        self.setRedCoinPalette()

    def setRedCoinPalette(self, newvalue=None):
        if newvalue is not None:
            self.showredcoins = newvalue
        if self.showredcoins:
            self[0xF0:0x100] = self[0x10:0x20]
        else:
            self[0xF0:0x100] = self[0x20:0x30]

    def loadL2palette(self, filepath, paletteID):
        self.layer2ID = paletteID
        with GBA.Open(filepath, mode="rb") as f:
            f.seek(f.readptr(Pointers.levelpalL2) + paletteID*2)
            colorindex = f.readint(2)
            f.seek(Pointers.colortable + colorindex)
            for paletterow in (6, 7):
                for i in range(1, 0x10):
                    colorID = paletterow<<4 | i
                    self[colorID] = f.readint(2)
                    self.colortype[colorID] = "Layer 2 Palette " +\
                                              format(paletteID, "02X")

    def loadL3palette(self, filepath, paletteID):
        self.layer3ID = paletteID
        with GBA.Open(filepath, mode="rb") as f:
            f.seek(f.readptr(Pointers.levelpalL3) + paletteID*2)
            colorindex = f.readint(2)
            f.seek(Pointers.colortable + colorindex)
            for colorID in range(1, 0x10):
                self[colorID] = f.readint(2)
                self.colortype[colorID] = "Layer 3 Palette " +\
                                          format(paletteID, "02X")

    L3images = (0x0D, 0x18, 0x23, 0x20, 0x13, 0x2A, 0x0C, 0x05)
    def loadL3imagepal(self, filepath, imageID):
        self.layer3image = imageID
        try:
            index = self.L3images.index(imageID)
        except ValueError:
            stop = 0x80
        else:
            stop = 0x90
            if imageID == 0x18:
                stop = 0xA0

            with GBA.Open(filepath, mode="rb") as f:
                ptr = f.readptr(f.readptr(Pointers.levelpalL3image) + index*4)
                colortype = "Layer 3 Image " + format(imageID, "02X")

                if imageID == 0x23 and self.layer3ID == 0x1C:
                    # game hardcodes a different palette for this combo
                    ptr += 0x20
                    colortype = "Layer 3 Image 23 + Palette 1C"

                f.seek(ptr)
                for colorID in range(0x80, stop):
                    if colorID & 3:
                        self[colorID] = f.readint(2)
                        self.colortype[colorID] = colortype
                    else:
                        f.read(2)  # discard next 2 bytes
                        if colorID & 0xF:
                            self[colorID] = self[0]  # copy background color
                            self.colortype[colorID] = self.colortype[0]

        self._setuninitialized(stop, 0xA0)


    def loadspritepalette(self, filepath, paletteID):
        with GBA.Open(filepath, mode="rb") as f:
            ptr = f.readptr(f.readptr(Pointers.levelpalsprite), paletteID)
            f.seek(ptr)
            for colorID in range(0x160, 0x180):
                self[colorID] = f.readint(2)
                if colorID & 0xF:
                    self.colortype[colorID] = "Sprite Palette " +\
                                              format(paletteID, "X")

    def loadyoshipalette(self, filepath, paletteID):
        with GBA.Open(filepath, mode="rb") as f:
            f.seek(Pointers.levelpalyoshi + 0x20*paletteID)
            for colorID in range(0x150, 0x160):
                self[colorID] = f.readint(2)
                if colorID & 0xF:
                    self.colortype[colorID] = "Yoshi Palette " +\
                                              format(paletteID, "X")

    def _setuninitialized(self, start, stop):
        for colorID in range(start, stop):
            if colorID & 0xF != 0:
                self[colorID] = 0x7C1F  # magenta to signal uninitialized
        self.colortype[start:stop] = ["Uninitialized"] * (stop-start)

    def row(self, paletteID):
        """Returns one 0x10-color palette, for use in coloring 8x8 tiles."""
        return self[paletteID*0x10 : (paletteID+1)*0x10]

def importL1_8x8tilemaps(filepath):
    """Import the 8x8 tilemap for each layer 1 16x16 tile ID."""
    with GBA.Open(filepath, mode="rb") as f:
        ptrs = []
        f.seek(Pointers.tilemapL1_8x8)
        for i in range(0xA9):
            ptrs.append(f.readint(4))
        ptrs.append(Pointers.tilemapL1_8x8)
        # last entry of vanilla tilemap table ends with the pointer table itself

        output = {}
        for highbyte in range(0xA9):
            f.seek(ptrs[highbyte])
            # read until next pointer, or 0x100 table entries (in case of edited
            #  pointer), whichever comes first
            tile16count = min((ptrs[highbyte+1]-ptrs[highbyte]) // 8, 0x100)

            tile16 = highbyte << 8
            for i in range(tile16count):
                tilemap = []
                for j in range(4):
                    tilemap.append(f.readint(2))
                output[tile16] = tilemap
                tile16 += 1

    return output

def exporttextgraphics(sourcefilepath, exportfilepath, texttype="main"):
    """Export SMA3's variable-width font graphics to a pixel graphics file.

    The export format expands each character's graphics from 8x12 to 8x16,
    and arranges them vertically as viewed in YY-CHR, so that they're reasonably
    editable. The variable width is indicated with an underline."""

    charlength = Pointers.textgraphics[texttype]["length"]
    with open(sourcefilepath, "rb") as f:
        f.seek(GBA.addrtofile(Pointers.textgraphics[texttype]["graphics"]))
        textgraphicsraw = f.read(charlength*0xC)
        f.seek(GBA.addrtofile(Pointers.textgraphics[texttype]["widths"]))
        widths = f.read(charlength)

    bitlines = (0b00000000, 0b10000000, 0b11000000, 0b11100000, 0b11110000,
                0b11111000, 0b11111100, 0b11111110, 0b11111111)

    with open(exportfilepath, "wb") as f:
        # Fill with empty space. Should be 0x1000, but it won't display
        #  in YYCHR without at least 0x2000
        f.write(b"\x00" * 0x2000)
        for charID in range(charlength):
            # first 8 8px rows
            f.seek(charID // 0x10 * 0x100 + charID % 0x10 * 8)
            f.write(textgraphicsraw[charID*12 : charID*12 + 8])

            # remaining 4 8px rows
            f.seek(charID // 0x10 * 0x100 + 0x80 + charID % 0x10 * 8)
            f.write(textgraphicsraw[charID*12 + 8 : charID*12 + 12])

            # use padding area to represent width
            f.seek(charID // 0x10 * 0x100 + 0x85 + charID % 0x10 * 8)
            try:
                widthline = bytes((bitlines[widths[charID]],))
            except IndexError:
                widthline = bytes((bitlines[0],))
            widthline += b"\x80"  # hook to mark left edge of line
            f.write(widthline)

def exportgraphics(sourcefilepath):
    """Export all currently known SMA3 graphics and compressed tilemaps.

    Also generate two directories, <fileroot>-Graphics and <fileroot>-Tilemaps,
    to hold the exports if they don't already exist."""

    # generate a filename-safe prefix for the export directories
    sourcefilename = os.path.basename(sourcefilepath)
    sourcefileroot = os.path.splitext(sourcefilename)[0]

    outputdir = os.path.dirname(sourcefilepath)
    outputroot = os.path.join(outputdir, sourcefileroot)

    folders = {}
    for name in ("Graphics", "Tilemaps"):
        folders[name] = outputroot + "-" + name
        if not os.path.exists(folders[name]):
            os.mkdir(folders[name])
    
    for addr, destfile in Pointers.LZ77_graphics:
        data, _ = GBA.decompress(sourcefilepath, addr)
        General.exportdatatofile(folders["Graphics"] + "/" + destfile, data)

    for addr, destfile in Pointers.LZ77_tilemaps:
        data, _ = GBA.decompress(sourcefilepath, addr)
        General.exportdatatofile(folders["Tilemaps"] + "/" + destfile, data)

    for addr, destfile, length in Pointers.uncompressed_graphics:
        data, _ = GBA.importdata(sourcefilepath, addr, length)
        General.exportdatatofile(folders["Graphics"] + "/" + destfile, data)

    exporttextgraphics(sourcefilepath,
                       folders["Graphics"] + "/" + "Font_082F63CC_main.bin",
                       texttype="main")
    exporttextgraphics(sourcefilepath,
                       folders["Graphics"] + "/" + "Font_0816D509_credits.bin",
                       texttype="credits")

########

if __name__ == "__main__":
    pass
