"""
A_L file format:
A binary file representation of a Python mapping, restricted to 8-bit keys and
byte sequence values. The extension's middle character can vary, and defines the
purpose of each key.

Header:
00-07: ASCII validation string "Advynia_",
       where the final character matches the middle character of the extension
       e.g. "Advynia3" for .a3l files
08-0D: 2 bytes per version component
0E-0F: reserved, not currently read
8 bytes per data key: 1-byte key (00-FE), 3-byte length, 4-byte offset
1 byte: FF, for end of header

All numbers are little-endian.
All offset tables (currently A3L 13, 14, 22-2A evens) are 3 bytes each, where
FFFFFF represents None.
"""

# standard library imports
import io, os

# import from other files
import AdvMetadata

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

    _ext = None

    @property
    def gamecode(self):
        return self._gamecode
    @gamecode.setter
    def gamecode(self, value):
        if isinstance(value, bytes):
            gamecode = value
        else:
            gamecode = bytes(str(value), encoding="ASCII")
        if len(gamecode) > 1:
            raise ValueError("Provided gamecode must be exactly one byte.")
        self._gamecode = gamecode

    @property
    def ext(self):
        "Auto-calculate file extension, if not defined by the subclass."
        if self._ext is None:
            self._ext = ".a" + str(self.gamecode, encoding="ASCII") + "l"
        return self._ext

    @classmethod
    def defaultfilename(cls, sourcefilepath, prefix, ID=None):
        """Generate a default file name, such as 'sma3-Sublevel12.a3l'."""
        output = [os.path.splitext(os.path.basename(sourcefilepath))[0],
                  "-", prefix]
        if ID is not None:
            output.append(f"{ID:02X}")
        output.append(cls().ext)
        return "".join(output)

    def __bytes__(self):
        "Convert data to exportable bytes."
        # fixed first 0x10 bytes of header
        header = bytearray(b"Advynia")
        header += self.gamecode
        for num in self.version:
            header += num.to_bytes(2, "little")
        header += bytes(2)  # 2 reserved bytes

        # account for remainder of variable-length header in the base offset
        offset = len(header) + len(self)*8 + 1

        body = bytearray()
        for key, data in sorted(self.items()):
            # 1-byte key (00-FE), 3-byte length, 4-byte offset
            if not 0 <= key <= 0xFE:
                raise ValueError
            header.append(key)
            header += len(data).to_bytes(3, "little")
            if len(data) <= 4:  # include data directly in header
                header += data
                header += bytes(4 - len(data))
            elif len(data) >= 0x1000000:
                # shouldn't happen, but a length this large would break the
                #  format
                raise ValueError
            else:
                header += offset.to_bytes(4, "little")
                body += data
                offset += len(data)

        header.append(0xFF)  # end of header marker

        return bytes(header + body)

    def exporttofile(self, filepath):
        "Create an Advynia export file from the current data."
        open(filepath, "wb").write(bytes(self))

    @classmethod
    def importfromfile(cls, filepath):
        "Create a new instance with the data from an Advynia export file."
        extension = os.path.splitext(filepath)[1].lower()
        if extension != cls().ext:
            raise ValueError("Unrecognized file extension: " + extension)

        rawdata = open(filepath, "rb").read()

        # check validation bytes
        if rawdata[0:7] != b"Advynia" or rawdata[7] != ord(extension[2]):
            raise ValueError(f"Not a valid {extension} file: validation bytes "
                f"{repr(rawdata[0:8])} failed verification.")

        versionlist = []
        for i in range(8, 0xE, 2):
            versionlist.append(int.from_bytes(rawdata[i:i+2], "little"))
        version = AdvMetadata.ProgramVersion(versionlist)

        data = cls(version=version)
        if not data.gamecode:
            data.gamecode = extension[2]

        for headeroffset in range(0x10, len(rawdata), 8):
            key = rawdata[headeroffset]
            if key == 0xFF:
                break
            length = int.from_bytes(
                rawdata[headeroffset+1:headeroffset+4], "little")
            if length <= 4:  # next up to 4 bytes are data, not offset
                dataoffset = headeroffset + 4
            else:
                dataoffset = int.from_bytes(
                    rawdata[headeroffset+4:headeroffset+8], "little")

            data[key] = rawdata[dataoffset:dataoffset+length]
            actuallength = len(data[key])
            if actuallength != length:  # end of file
                raise ValueError(
                    f"Failed to parse {extension} file: "
                    f"reached end of file when importing key 0x{key:02X} data. "
                    f"(Expected length: 0x{length:X}, "
                    f"actual length: 0x{actuallength:X})"
                    )

        return data

    def __repr__(self):
        keystr = ", ".join(hex(key) for key in self)
        maintext = [f"keys: ({keystr})"]
        if self.version is not None:
            maintext += [f"version: {self.version}"]
        if self.gamecode is not None:
            maintext += [f"gamecode: {self.gamecode}"]
        return "".join((
            "<", self.__class__.__name__, ": ",
            ", ".join(maintext), ">"))

# function used in importing

def importinttable(bytedata, intwidth):
    output = []
    buffer = io.BytesIO(bytedata)
    nonevalue = 2 ** (intwidth*8) - 1
    while rawnum := buffer.read(intwidth):
        num = int.from_bytes(rawnum, "little")
        if num != nonevalue:
            output.append(num)
        else:
            output.append(None)
    return output
