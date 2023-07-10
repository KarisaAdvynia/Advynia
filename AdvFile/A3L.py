"""
A3L data keys:
01: Sublevel main data
04: Sublevel sprite data
05: Sublevel stripes
06: Sublevel tileset high byte
07: Sublevel layer 2/3 Y offsets
0D: Sublevel music ID
0F: Sublevel ID
10: Level ID, if single level
11: Main entrance(s)
12: Midway entrances (always 6-byte)
13: Main entrance offsets, if multiple levels
14: Midway entrance offsets, if multiple levels
21: Text: Level names
22: Text: Level name offsets
23: Text: Standard messages
24: Text: Standard message offsets
25: Text: File select
26: Text: File select offsets
27: Text: Story intro
28: Text: Story intro offsets
29: Text: Credits
2A: Text: Credits offsets
2B: Text: Ending message
65: Sublevel object65 patch flag
95: SNES flag
"""

# standard library imports
import io, itertools

# import from other files
from AdvFile.FileBase import AdvyniaFileData, importinttable
from AdvGame import SMA3

class A3LFileData(AdvyniaFileData):
    """Subclass representing the A3L file format. Handles converting to/from
    SMA3 data formats."""

    gamecode = b"3"
    ext = ".a3l"
    longext = "Advynia SMA3 Export (*.a3l)"

    def __init__(self, *args, version=None):
        super().__init__(*args, version=version)

    def datatype(self):
        if 1 in self and 4 in self:  # sublevel main/sprite data
            return "Sublevel"
        if 0x11 in self and 0x12 in self:
            if 0x13 in self and 0x14 in self:  # entrance level offsets
                return "Entrances: All Levels"
            if 0x10 in self:  # entrance level ID
                return "Entrances: Single Level"
        for key in range (0x21, 0x2C, 2):
            if key in self and (key == 0x2B or (key + 1) in self):
                return "Text"
        return ""

    def defaultfilename(self, sourcefilepath):
        ID = None
        match self.datatype():
            case "Sublevel":
                prefix = "Sublevel"
                try:
                    ID = self[0xF][0]
                except KeyError:
                    pass
            case "Entrances: Single Level":
                prefix = "LevelEntr"
                ID = self[0x10][0]
            case "Entrances: All Levels":
                prefix = "LevelEntrAll"
            case "Text":
                prefix = "Messages"
            case _:
                prefix = "Unknown"
        return super().defaultfilename(sourcefilepath, prefix, ID)

    @classmethod
    def fromsublevel(cls, sublevel, stripeIDs=None):
        "Create an A3LFileData instance representing an SMA3.Sublevel."

        data = cls()

        # process main data
        data[1] = sublevel.exportmaindata()
        data[4] = sublevel.exportspritedata()
        if sublevel.ID is not None:
            data[0xF] = sublevel.ID.to_bytes(1, "little")
        if sublevel.layerYoffsets:
            data[7] = (sublevel.layerYoffsets[2].to_bytes(2, "little") +
                       sublevel.layerYoffsets[3].to_bytes(2, "little"))

        # process patch data
        if stripeIDs is not None:
            data[5] = stripeIDs
        elif sublevel.stripeIDs:
            data[5] = sublevel.stripeIDs
        if sublevel.header[1] >= 0x10:
            data[6] = (sublevel.header[1] >> 4).to_bytes(1, "little")
        if sublevel.music is not None:
            data[0xD] = sublevel.music.to_bytes(1, "little")

        # write object 65 flag only if object 65 is actually used
        if sublevel.obj65_7byte:
            for obj in sublevel.objects:
                if obj.ID == 0x65:
                    data[0x65] = b"\1"
                    break

        # write SNES flag if applicable
        try:
            if sublevel.fromSNES:
                data[0x95] = b"\1"
        except AttributeError: pass

        return data

    def tosublevel(self):
        """Create an SMA3.Sublevel instance using current data. Should be called
        only if tnis instance represents a sublevel."""

        if self.datatype() != "Sublevel":
            raise ValueError("A3L file keys do not represent an SMA3 sublevel.")

        # initialize sublevel
        sublevel = SMA3.Sublevel()
        sublevel.fromfile = True
        if 0x65 in self: sublevel.obj65_7byte = self[0x65][0]

        # import base data
        sublevel.importmaindata(io.BytesIO(self[1]))
        sublevel.importspritedata(io.BytesIO(self[4]))
        if 0xF in self: sublevel.ID = self[0xF][0]
        if 7 in self:
            sublevel.layerYoffsets[2] = int.from_bytes(self[7][0:2], "little")
            sublevel.layerYoffsets[3] = int.from_bytes(self[7][2:4], "little")

        # import patch data
        if 5 in self: sublevel.stripeIDs = bytearray(self[5])
        if 6 in self: sublevel.header[1] |= self[6][0] << 4
        if 0xD in self: sublevel.music = self[0xD][0]

        return sublevel

    @classmethod
    def fromentrances(cls, mainentrances, midwayentrances, levelID=None):
        """Create an A3LFileData instance representing SMA3 level entrances,
        for one or all levels."""

        data = cls()
        if levelID is not None:
            # single level's entrances
            data[0x10] = levelID.to_bytes(1, "little")
            data[0x11] = mainentrances
            data[0x12] = b"".join(midwayentrances)
        else:
            # all level entrances
            data[0x11], mainoffsets = mainentrances.tobytearray()
            data[0x12], midwayoffsets = midwayentrances.tobytearray(midwaylen=6)
            for key, offsets in ((0x13, mainoffsets), (0x14, midwayoffsets)):
                array = bytearray()
                for num in offsets:
                    if num is not None:
                        array += num.to_bytes(3, "little")
                    else:
                        array += b"\xFF"*3
                data[key] = array
        return data

    def toentrances(self):
        """Create instances of SMA3.MainEntrances and SMA3.MidwayEntrances using
        current data. Should be called only if this instance represents
        entrances."""

        if self.datatype() == "Entrances: Single Level":
            levelID = int.from_bytes(self[0x10], "little")
            mainentrance = SMA3.Entrance(self[0x11])
            midwayraw = self[0x12]
            midwayentrances = []
            for i in range(0, len(midwayraw), 6):
                midwayentrances.append(SMA3.Entrance(midwayraw[i:i+6]))

            return levelID, mainentrance, midwayentrances

        if self.datatype() == "Entrances: All Levels":
            output = []
            for key, cls in ((0x11, SMA3.MainEntrances),
                             (0x12, SMA3.MidwayEntrances)):
                bytedata = self[key]
                offsets = importinttable(self[key+2], 3)
                output.append(cls.importfrombytes(bytedata, offsets))
            return output

        else:
            raise ValueError(
                "A3L file keys do not represent SMA3 level entrances.")

    @classmethod
    def fromtextdata(cls, messagemap):
        """Create an A3LFileData instance representing SMA3 text data, given
        a mapping from texttype strings to sequences of messages."""

        data = cls()
        for texttype, messages in messagemap.items():
            key = 0x21 + list(SMA3.textclasses).index(texttype) * 2
            if texttype == "Ending":
                # single ending message
                data[key] = bytes(messages[0])
            else:
                # list of messages: convert to byte data and offset table
                data[key], offsets = messages.tobytearray(
                    nullptr=(texttype=="Story intro"))
                for offset in offsets:
                    array = bytearray()
                    for num in offsets:
                        if num is not None:
                            array += num.to_bytes(3, "little")
                        else:
                            array += b"\xFF"*3
                data[key+1] = array
        return data

    def totextdata(self):
        if self.datatype() != "Text":
            raise ValueError("A3L file keys do not represent SMA3 text data.")

        output = {}
        for (texttype, cls), key in zip(SMA3.textclasses.items(),
                                        itertools.count(0x21, 2)):
            if key in self:
                if texttype == "Ending":
                    # single ending message
                    buffer = io.BytesIO(self[key])
                    output[texttype] = [cls.importtext(buffer)]
                else:
                    try:
                        offsets = importinttable(self[key+1], 3)
                        output[texttype] = cls.importallfrombytes(
                            self[key], offsets)
                    except KeyError:
                        # offsets key is missing
                        pass
        return output
