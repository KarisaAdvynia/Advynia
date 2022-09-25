"""GBA General
Classes and functions for reading/writing/processing GBA ROM data, not
associated with a specific game."""

# standard library imports
from operator import itemgetter

# import from other files
from . import AdvGame

class Open(AdvGame.Open):
    "Wrapper for Python's open() function, for reading/writing GBA ROM images."
    def seek(self, ptr):
        "Seek to a GBA ROM pointer."
        if not 0x08000000 <= ptr < 0x0A000000:
            raise ValueError("Address " + format(ptr, "08X") +
                             " is not a valid GBA ROM pointer.")
        self.fileobj.seek(ptr & 0x01FFFFFF)

    def tell(self):
        "Return the curent position as a GBA pointer."
        return self.fileobj.tell() | 0x08000000

    def readptr(self, ptr, index=0):
        """Seek to the given pointer, offset with a pointer table index if
        provided, then read a GBA pointer from the ROM."""
        if ptr % 4 != 0:
            print("Warning: Pointer " + format(ptr, "08X") +
                  " is not a multiple of 4. It may be misaligned.")
        self.seek(ptr + index*4)
        return self.readint(4)

    def readmultiptr(self, ptr, num=2):
        """Load a nested pointer-to-pointer. Seek position ends after reading
        the last pointer."""
        for i in range(num):
            ptr = self.readptr(ptr)
        return ptr

    def readseek(self, ptr=None):
        "Read a pointer at the current or specified position, then seek to it."
        if not ptr:
            ptr = f.tell()
        self.seek(self.readptr(ptr))

    def read_decompress(self, ptr=None):
        """Decompress and extract data stored in GBA-specific compression
        formats, at the current or specified position.
        Supports GBA's LZ77 and Huffman formats."""

        if ptr is not None:
            self.seek(ptr)
        startaddr = self.tell()
        if startaddr & 3:
            print("Warning: Pointer " + format(startaddr, "08X") +
                  " is not a multiple of 4. It may be misaligned.")

        # process compression header
        compresstype = self.read(1)[0]
        length = self.readint(3)
        if compresstype == 0x10:  # LZ77
            output = _decompressLZ77(self.fileobj, length)
        elif compresstype & 0xF0 == 0x20:  # Huffman
            bitlength = compresstype & 0xF
            if bitlength != 8:
                raise NotImplementedError("".join((
                    "Only Huffman data with bit length 8 is currently "
                    "supported. Data at ", format(startaddr, "08X"),
                    " has bit length ", str(bitlength), "."
                    )))
            output = _decompressHuffman(self.fileobj, length, bitlength)
        else:
            raise ValueError("".join((
                "Data at ", format(startaddr, "08X"),
                " is not valid GBA LZ77/Huffman data. "
                "Only LZ77/Huffman formats are supported."
                )))

        endaddr = self.tell()
        if endaddr & 3:
            self.read(4 - (endaddr & 3))  # force GBA alignment

        # cleanup
        if len(output) != length:
            print("Warning: Final length of " + hex(len(output)) +
                  " does not match declared length of " + hex(length) + ".")
        return output

def _decompressLZ77(f, length):
    "Called by GBA.Open.read_decompress, to handle LZ77-format data."

    output = bytearray()

    while len(output) < length:
        flags = f.read(1)[0]

        # process compression flags highest to lowest
        for bitindex in range(8):
            bit = flags & 0x80>>bitindex
            if bit:   # use 16-bit parameter to copy previous data
                block = f.read(2)
                copylength = (block[0] >> 4) + 3
                offset = block[1] + ((block[0]&0xF)<<8) + 1
                for i in range(copylength):
                    output.append(output[-offset])
            else:   # uncompressed byte
                output += f.read(1)
            if len(output) >= length:
                break

    return output

def _decompressHuffman(f, length, bitlength):
    """Called by GBA.Open.read_decompress, to handle Huffman-format data.
    Currently only supports bitlength 8."""

    # construct tree decoder, mapping bit tuples to uncompressed bytes
    treeraw = bytearray(f.read(1))  # tree length byte
    treeraw += f.read(treeraw[0]*2 + 1)
    treemap = {}
    _followHuffnode(treeraw, treemap, offset=1)
##    print([("".join(str(i) for i in bits), "%02X"%byte)
##           for bits, byte in treemap.items()])

    # decompress data
    output = bytearray()

    bitkey = []
    while len(output) < length:
        bitstream = int.from_bytes(f.read(4), "little")
        for bitoffset in reversed(range(32)):
            bitkey.append((bitstream >> bitoffset) & 1)
            try:
                output.append(treemap[tuple(bitkey)])
                if len(output) >= length:
                    break
                bitkey.clear()
            except KeyError:
                # keep appending bits until a valid key is found
                pass

    return output

def _followHuffnode(treeraw, treemap, offset, bits=(), dataflag=False):
    """Recursive function to follow the left and right nodes of the Huffman
    tree, and map bit sequences to decoded bytes."""
    try:
        node = treeraw[offset]
    except IndexError:
        # tree table overflowed: defining None ensures invalid key lookup
        #  will terminate with an exception, not an infinite loop
        treemap[bits] = None
        return

    if dataflag:
        # endpoint: map bit sequence (path to reach this node) to byte
        treemap[bits] = node
        return

    nextoffset = (offset//2 + (node&0x3F) + 1) * 2
    _followHuffnode(treeraw, treemap, nextoffset, bits+(0,), node&0x80)
    _followHuffnode(treeraw, treemap, nextoffset+1, bits+(1,), node&0x40)


def addrtofile(addr):
    "Convert a GBA ROM pointer to a file offset, both expressed in integers."
    if not 0x08000000 <= addr < 0x0A000000:
        raise ValueError("Address " + format(addr, "08X") +
                         " is not a valid GBA ROM pointer.")
    return addr & 0x01FFFFFF

def addrfromfile(addr):
    "Convert a file offset to a GBA ROM pointer, both expressed in integers."
    if addr >= 0x02000000:
        raise ValueError("Offset " + format(addr, "08X") +
                         " is larger than the maximum GBA ROM size, 32 MiB.")
    return addr | 0x08000000

def readinternalname(filepath):
    "Extract the GBA internal name."
    with open(filepath, "rb") as f:
        f.seek(0xA0)
        title = str(f.read(0xC).rstrip(b"\x00"), encoding="ASCII")
        ID = str(f.read(4).rstrip(b"\x00"), encoding="ASCII")
    return title, ID

def setinternalname(filepath, newbytes):
    "Change the GBA internal name, and update the internal header checksum."
    if len(newbytes) > 16:
        raise ValueError("Internal name is limited to 16 bytes.")
    with open(filepath, "r+b") as f:
        f.seek(0xA0)
        f.write(newbytes)
    testchecksum(filepath, fix=True)

def testchecksum(filepath, fix=False):
    "Test and potentially fix the GBA internal header checksum."
    with open(filepath, "r+b") as f:
        f.seek(0xA0)
        rawbytes = f.read(0x1D)
        checksum = f.read(1)[0]

        result = (-sum(rawbytes) - 0x19) & 0xFF

        if not fix:
            return result == checksum
        if fix and result != checksum:
            f.seek(0xBD)
            f.write(result.to_bytes(1, "little"))

def readptr(filepath, addr, index=0):
    "Wrapper for GBA.Open.readptr, to read a pointer from a specified file."
    with Open(filepath) as f:
        return f.readptr(addr, index)

def readmultiptr(filepath, addr, num=2):
    """Wrapper for GBA.Open.readmultiptr, to read a nested GBA
    pointer-to-pointer from a specified file."""
    with Open(filepath) as f:
        return f.readmultiptr(addr, num)

def decompress(filepath, addr=0):
    """Wrapper for GBA.Open.decompress, to open and decompress data from a
    specified file."""

    if addr >= 0x08000000:
        # addr is a GBA ROM pointer
        if addr % 4 != 0:
            print("Warning: Pointer " + format(addr, "08X") +
                  " is not a multiple of 4. It may be misaligned.")
    else:
        # load as if addr is a GBA ROM pointer
        addr = addrfromfile(addr)

    with Open(filepath, "rb") as f:
        f.seek(addr)
        return f.read_decompress()

def compressLZ77(data):
    "Compress data to GBA's LZ77 compression format. Returns a bytearray."

    length = len(data)
    if length > 0x40000:
        raise ValueError("Data size " + hex(length) +\
                         " is too large for a GBA's RAM to process.")

    output = bytearray()
    output.append(0x10)  # LZ77 compression type
    output += length.to_bytes(3, "little")

    index = 0
    while index < length:
        # process 8 bytes or copy commands at a time, to store in a flags byte
        flags = 0
        newbytes = bytearray()
        for bitindex in range(8):
            flags <<= 1   # prepare flag byte for next compression flag
            start = max(0, index-0x1000)
            for copylength in range(0x12, 2, -1):
                if index+copylength > len(data):
                    # slice is interrupted by end of data
                    continue
                # search earlier data for progressively shorter subsequences
                pos = data.find(data[index:index+copylength],
                                start, index+copylength-1)
                if pos >= 0:  # matching subsequence found
                    # generate 16-bit parameter to copy previous data
                    offset = index - pos - 1
                    newbytes.append(offset>>8 | (copylength-3)<<4)
                    newbytes.append(offset & 0xFF)

                    index += copylength
                    flags |= 1  # set compression flag
                    break
            else:  # uncompressed byte
                newbytes.append(data[index])
                index += 1

            if index >= length:  # no bytes remaining to compress
                # finish off left-shifting the flags before breaking loop
                flags <<= (7-bitindex)
                break
        output.append(flags)
        output += newbytes

    # ensure output length is word-aligned
    while len(output) % 4 != 0:
        output.append(0)

    return output

def importdata(filepath, addr, length):
    """Import data from a GBA address, compressed or uncompressed.
    Returns data, and address of end of data.
    Set length to -1 if compressed."""

    if length == -1:
        return decompress(filepath, addr)
    else:
        offset = addrtofile(addr)
        return AdvGame.importdata(filepath, offset, length)

def savedatatofreespace(filepath, data, ptrstodata,
        freespacestart=0x400000, freespaceend=0x2000000):
    """Save variable-length data to a GBA ROM, in the provided freespace region,
    and update the data's pointer(s).
    Returns the new pointer, or None if insufficient space in the region."""

    if ptrstodata:
        try:
            ptrstodata[0]
        except TypeError:
            # convert single pointer to sequence of pointers
            ptrstodata = (ptrstodata,)
    else:
        ptrstodata = ()

    freespace = AdvGame.findfreespace(
        filepath, freespacestart, freespaceend, minlength=max(len(data), 0x10),
        width=4)
    if not freespace:
        return

    # save at smallest free location
    newptr = addrfromfile(min(freespace, key=itemgetter(1))[0])
    with Open(filepath, "r+b") as f:
        f.seek(newptr)
        f.write(data)
        for ptr in ptrstodata:
            f.seek(ptr)
            f.writeint(newptr, 4)
    return newptr

def overwritedata(filepath, data, ptr, expectedlen=None):
    if expectedlen is not None and len(data) != expectedlen:
        raise ValueError("".join((
            "Data to be overwritten at ", format(ptr, "08X"),
            " did not match expected length ", hex(expectedlen), "."
            )))
    with Open(filepath, "r+b") as f:
        f.seek(ptr)
        f.write(data)

def erasedata(filepath, ptr, bytecount):
    "Wrapper for GBA.Open.erasedata, to overwrite data with 00 bytes."
    with Open(filepath, "r+b") as f:
        f.erasedata(ptr, bytecount)

def splittilemap(tileprop):
    "Split a GBA tilemap 16-bit tile into its bitwise properties."
    tileID_8 = tileprop & 0x3FF
    paletterow = tileprop >> 12
    xflip = tileprop & 0x400
    yflip = tileprop & 0x800
    return tileID_8, paletterow, xflip, yflip

class PointerTable(list):
    "List subclass representing a GBA pointer table."
    def __init__(self, *args, endmarker=True):
        list.__init__(self, *args)
        self.datablock = None
        self.endmarker = endmarker

    @classmethod
    def importtable(cls, filepath, ptrtotable, vstart=None, vlen=None,
                    maxlen=0x100):
        """Import a GBA pointer table.
        Read until encountering an end-of-data marker FFFFFFFF, or to maxlen.
        If a vanilla start and length (in pointer count, not bytes) are
        specified, don't look for an end-of-data marker."""
        with Open(filepath, "rb") as f:
            f.seek(ptrtotable)
            tablestart = f.readint(4)

            output = cls()
            f.seek(tablestart)

            if tablestart == vstart:
                # read vanilla table; don't look for end-of-data marker
                output.endmarker = False
                for i in range(vlen):
                    ptr = f.readint(4)
                    if ptr == 1:
                        # interpret 00000001 as a null pointer
                        output.append(0)
                    else:
                        output.append(ptr)
            else:
                for i in range(maxlen+1):
                    # add 1 to maxlen to account for end of data
                    ptr = f.readint(4)
                    if ptr == 0xFFFFFFFF:
                        # FFFFFFFF signals end of data
                        break
                    elif ptr == 1:
                        # interpret 00000001 as a null pointer
                        output.append(0)
                    else:
                        output.append(ptr)
            end = f.tell()

        output.datablock = [tablestart, end-tablestart]
        return output

    def tobytearray(self, nullptr=0):
        output = bytearray()
        for ptr in self:
            if not ptr:
                ptr = nullptr
            output += ptr.to_bytes(4, "little")
        if self.endmarker:
            output += b"\xFF\xFF\xFF\xFF"
        return output

    def __bytes__(self):
        return bytes(self.tobytearray())
