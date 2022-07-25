"""
Advynia File Processing

A_L data format:
Header:
00-07: ASCII validation string "Advynia_",
       where the final character matches the middle character of the extension
       e.g. "Advynia3" for .a3l files
08-0D: 2 bytes per version component
0E-0F: reserved, not currently read
8 bytes per data key: 1-byte key, 3-byte length, 4-byte offset
1 byte: FF, for end of header

A3L data keys:
01: Sublevel main data
04: Sublevel sprite data
05: Sublevel stripes
06: Sublevel tileset high byte
0D: Sublevel music ID
0F: Sublevel ID
?10: Level ID, if single level
?11: Main entrance(s)
?12: Midway entrances (always treated as 6-byte)
?13: Offsets to main entrances, if multiple levels
?14: Offsets to midway entrances, if multiple levels
65: object65 patch flag
95: SNES flag
"""

# standard library imports
import io, os

# import from other files
from AdvGame import SMA3

# globals
import AdvMetadata

# General file format functions

class AdvyniaFileData(dict):
    """Represents data corresponding to an Advynia export file.
    Keys should be 8-bit integers; values should be byte sequences."""
    def __init__(self, *args, version=None, gamecode=None):
        super().__init__(*args)
        self.version = version
        if version is None:
            self.version = AdvMetadata.version[0:3]
        if gamecode is not None:
            self.gamecode = gamecode

    @property
    def gamecode(self):
        return self._gamecode
    @gamecode.setter
    def gamecode(self, value):
        if isinstance(value, bytes):
            self._gamecode = value
        else:
            self._gamecode = bytes(str(value), encoding="ASCII")
        if len(self._gamecode) > 1:
            raise ValueError("Provided gamecode must be exactly one byte.")

    def __bytes__(self):
        "Convert data to exportable bytes."
        # fixed first 0x10 bytes of header
        header = bytearray(b"Advynia")
        header += self.gamecode
        for num in self.version:
            header += num.to_bytes(2, byteorder="little")
        header += bytes(2)  # 2 reserved bytes

        # account for remainder of variable-length header in the base offset
        offset = len(header) + len(self)*8 + 1

        body = bytearray()
        for key, data in self.items():
            # 1-byte key, 3-byte length, 4-byte offset
            header.append(key)
            header += len(data).to_bytes(3, byteorder="little")
            if len(data) <= 4:  # include data directly in header
                header += data
                header += bytes(4 - len(data))
            elif len(data) >= 0x1000000:
                # shouldn't happen, but a length this large would break the
                #  format
                raise ValueError
            else:
                header += offset.to_bytes(4, byteorder="little")
                body += data
                offset += len(data)

        header.append(0xFF)  # end of header marker

        return bytes(header + body)

    def exporttofile(self, filepath):
        "Create an Advynia export file from the current data."
        with open(filepath, "wb") as f:
            f.write(bytes(self))

    @classmethod
    def importfromfile(cls, filepath):
        "Create a new instance with the data from an Advynia export file."
        extension = os.path.splitext(filepath)[1]
        if len(extension) != 4 or extension[1].lower() != "a" or\
                extension[3].lower() != "l":
            raise ValueError(" ".join((
                "Extension", extension, "is not recognized.")))

        with open(filepath, "rb") as f:
            rawdata = f.read()

        # check validation bytes
        if rawdata[0:7] != b"Advynia" or rawdata[7] != ord(extension[2]):
            raise ValueError("".join((
                "Not a valid ", extension, ' file: validation bytes "',
                str(rawdata[0:8], encoding="UTF-8"), '" failed verification.')))

        versionlist = []
        for i in range(8, 0xE, 2):
            versionlist.append(
                int.from_bytes(rawdata[i:i+2], byteorder="little"))
        version = AdvMetadata.ProgramVersion(versionlist)

        data = cls(version=version)
        if not data.gamecode:
            data.gamecode = extension[2]

        ptrs = {}
        for headeroffset in range(0x10, len(rawdata), 8):
            key = rawdata[headeroffset]
            if key == 0xFF:
                break
            length = int.from_bytes(
                rawdata[headeroffset+1:headeroffset+4], byteorder="little")
            if length <= 4:  # next up to 4 bytes are data, not offset
                dataoffset = headeroffset+4
            else:
                dataoffset = int.from_bytes(
                    rawdata[headeroffset+4:headeroffset+8], byteorder="little")

            data[key] = rawdata[dataoffset:dataoffset+length]

        return data

    @classmethod
    def exportsublevel(cls, outputfilepath, sublevel):
        """Export a sublevel to a file. Relies on a subclass exporttofile
        method; this should not be called on AdvyniaFileData itself."""
        outputdata = cls.fromsublevel(sublevel)
        outputdata.exporttofile(outputfilepath)

    def __repr__(self):
        keystr = ", ".join(hex(key) for key in self)
        maintext = ["".join(("keys: (", keystr, ")"))]
        if self.version is not None:
            maintext += ["version: " + str(self.version)]
        if self.gamecode is not None:
            maintext += ["gamecode: " + str(self.gamecode)]
        return "".join((
            "<", self.__class__.__name__, ": ",
            ", ".join(maintext), ">"))

class A3LFileData(AdvyniaFileData):
    """Subclass representing the A3L file format. Handles converting to/from
    SMA3 data formats."""

    gamecode = b"3"

    def __init__(self, *args, version=None):
        super().__init__(*args, version=version)

    @classmethod
    def fromsublevel(cls, sublevel, stripeIDs=None):
        "Create an A3LFileData instance representing an SMA3.Sublevel."
        data = cls()

        # process main data
        data[1] = sublevel.exportmaindata()
        data[4] = sublevel.exportspritedata()
        if sublevel.ID is not None:
            data[0xF] = sublevel.ID.to_bytes(1, byteorder="little")

        # process patch data
        if stripeIDs is not None:
            data[5] = stripeIDs
        elif sublevel.stripeIDs:
            data[5] = sublevel.stripeIDs
        if sublevel.header[1] >= 0x10:
            data[6] = (sublevel.header[1] >> 4).to_bytes(1, byteorder="little")
        if sublevel.music is not None:
            data[0xD] = sublevel.music.to_bytes(1, byteorder="little")

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
        "Create an SMA3.Sublevel instance using current data."

        # initialize sublevel
        sublevel = SMA3.Sublevel()
        sublevel.fromfile = True
        if 0x65 in self: sublevel.obj65_7byte = self[0x65][0]

        # import base data
        sublevel.importmaindata(io.BytesIO(self[1]))
        sublevel.importspritedata(io.BytesIO(self[4]))
        if 0xF in self: sublevel.ID = self[0xF][0]

        # import patch data
        if 5 in self: sublevel.stripeIDs = bytearray(self[5])
        if 6 in self: sublevel.header[1] |= self[6][0] << 4
        if 0xD in self: sublevel.music = self[0xD][0]

        return sublevel

# specialized exports

def exportallYIsublevels(sourcefilepath, outputdir, console="GBA"):
    if console == "GBA":
        from AdvGame.SMA3 import Sublevel
        sublevelrange = range(0xF6)
    elif console == "SNES":
        from AdvGame.SMA3 import SublevelFromSNES as Sublevel
        sublevelrange = range(0xDE)
    else:
        raise ValueError("Input 'console' must be either 'GBA' or 'SNES'.")

    if outputdir[-1] != "/":
        outputdir += "/"
    if not os.path.exists(outputdir):
        os.mkdir(outputdir)

    for sublevelID in sublevelrange:
        try:
            sublevel = Sublevel.importbyID(sourcefilepath, sublevelID)
            exportpath = (
                outputdir,
                os.path.splitext(os.path.basename(sourcefilepath))[0], "-",
                "Sublevel", format(sublevelID, "02X"), ".a3l")
            A3LFileData.exportsublevel("".join(exportpath), sublevel)
        except ValueError:
            pass

########

if __name__ == "__main__":
    pass
