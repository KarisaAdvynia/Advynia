"""Classes and functions for general game data processing, not associated
with any particular console."""

# standard library imports
import copy, math

# Misc classes

class ListData(list):
    "List subclass to assign arbitrary atributes."
    pass

# General import/export functions

def importdata(filepath, offset=0, length=None):
    """Import bytes from a file. By default this reads the entire file.
    Optionally can specify a starting offset and number of bytes to read."""
    with open(filepath, "rb") as f:
        f.seek(offset)
        data = f.read(length)
    return data

def exportdatatofile(filepath, data):
    "Export bytes to a new file."
    with open(filepath, "wb") as f:
        f.write(data)

class Open:
    """Wrapper for Python's open() function. Used as a base class for
    accessing binary files with specialized pointers and read/write functions."""
    def __init__(self, filepath, mode="rb"):
        if "b" not in mode:
            raise ValueError("This class cannot open a file in text mode.")
        self.fileobj = open(filepath, mode)
    def __enter__(self):
        return self
    def __exit__(self, *_):
        self.fileobj.close()

    def __getattr__(self, name):
        # redirect non-overridden attributes to the file object
        return getattr(self.fileobj, name)

    def readint(self, length):
        "Read a little-endian number from the file, with the given byte count."
        return int.from_bytes(self.read(length), "little")

    def writeint(self, num, length):
        "Write a little-endian number to the file, with the given byte count."
        self.fileobj.write(num.to_bytes(length, "little"))

    def erasedata(self, ptr, bytecount):
        "Overwrite data at the given pointer with 00 bytes."
##        print("Erasing", hex(ptr), "to", hex(ptr+bytecount))
        self.seek(ptr)
        self.write(bytes(bytecount))  # fill with 00 bytes

# Multi-console

def findfreespace(filepath, start=0, end=None, minlength=0x80, width=1):
    """Search for blocks of at least minlength consecutive 00 bytes in a
    consecutive region of a file. Returns a list of [start, length] pairs.
    If a word width is provided, the block addresses and lengths are aligned to
    multiples of the width."""

    emptyword = bytes(width)
    if not end:
        end = os.path.getsize(filepath)
    if start % width != 0:
        # round up start of region, if misaligned
        start = math.ceil(start/width)*width

    output = []
    with open(filepath, "rb") as f:
        f.seek(start)
        while f.tell() < end:
            word = f.read(width)
            if not word:  # end of file
                break
            if word == emptyword:
                output.append([f.tell() - width, 0])
                while word == emptyword:
                    output[-1][1] += width
                    word = f.read(width)
                    if f.tell() > end:
                        break
                if output[-1][1] < minlength:
                    del output[-1]
    return output

class GameGraphics(list):
    "Imported 8x8 tiles, indexed by tile number."
    def __init__(self, rawdata=None, tilesize=0x20):
        self.tilesize = tilesize

        if not rawdata:
            return
        if len(rawdata) % tilesize != 0:
            raise ValueError("Graphics data length " + hex(len(rawdata)) +\
                  " does not correspond to an integer number of tiles.")
        for i in range(len(rawdata) // tilesize):
            self.append(rawdata[i*tilesize : (i+1)*tilesize])

    def replacegraphics(self, graphics, byteoffset=0):
        if byteoffset % self.tilesize != 0:
            raise ValueError("".join(("Offset ", hex(byteoffset),
                " does not correspond to an integer number of tiles.")))
        startindex = byteoffset // self.tilesize
        endindex = startindex + len(graphics)
        if len(self) < endindex:
            self.extend([None] * (endindex - len(self)))
        self[startindex : startindex+len(graphics)] = graphics

class SharedPointerList(list):
    """Represents a list of imported mutable data, where due to shared pointers
    in the source data, multiple indexes can refer to the same item.
    These linksets (sets of indexes referring to a single item) are tracked,
    to allow for exporting data without duplicating it."""
    def __init__(self, ptrtable, importfunc):
        """Create a new shared pointer list, using the provided pointer table
        and import function.
        importfunc(ptr) should take 1 argument, and return an item to append."""
        self.linksets = []

        ptrmap = {}
        for i, ptr in enumerate(ptrtable):
            try:
                linkset = ptrmap[ptr]
            except KeyError:
                # new item
                self.append(importfunc(ptr))
                ptrmap[ptr] = self.linksets[-1]
            else:
                # duplicate item
                # any linkset element is fine since they all give the same item
                self.append(self[next(iter(linkset))])
                linkset.add(i)
                self.linksets[-1] = linkset

    def tobytearray(self, nullptr=False):
        output = bytearray()
        relptrs = [None]*len(self)
        for i, item in enumerate(self):
            if relptrs[i] is not None:
                # skip if already processed via linked item
                continue
            if nullptr and not item:
                # if null pointers are allowed,
                #  don't process items that are considered False
                continue
            for j in self.linksets[i]:
                # set pointer to start of output data
                relptrs[j] = len(output)
            # add to output data
            output += bytes(item)
        return output, relptrs

    def append(self, item):
        self.linksets.append({len(self)})
        list.append(self, item)

    def islinked(self, index):
        return len(self.linksets[index]) != 1

    def linkitem(self, destindex, sourceindex):
        # remove from existing linkset
        self.linksets[destindex].remove(destindex)

        # add to sourceindex's linkset
        linkset = self.linksets[sourceindex]
        linkset.add(destindex)
        self.linksets[destindex] = linkset

        # change reference to refer to the same item
        self[destindex] = self[sourceindex]

    def unlinkitem(self, index):
        # remove from existing linkset
        self.linksets[index].remove(index)

        # create new linkset
        self.linksets[index] = {index}

        # change reference to refer to a distinct item
        self[index] = copy.deepcopy(self[index])

    def uniqueitems(self):
        """Iterator over items in the list, where linked items are returned
        only once."""
        for i, item in enumerate(self):
            if min(self.linksets[i]) == i:
                yield item

    def linksetstr(self, index, formatstr=""):
        "Return a compact string containing the indexes in a linkset."
        if len(self.linksets[index]) == 1:
            return "None"
        output = []
        prev = None
        chain = False
        for i in sorted(self.linksets[index]):
            if i - 1 == prev:
                chain = True
            else:
                if prev is not None:
                    if chain:
                        output += ["-", format(prev, formatstr)]
                        chain = False
                    output.append(",")
                output.append(format(i, formatstr))
            prev = i
        if chain:
            output += ["-", format(prev, formatstr)]
        return "".join(output)

def color15split(color):
    "Split a 15-bit GBA/GBC/SNES RGB color into components."
    if not 0 <= color < 0x10000:
        raise ValueError("Color {color} is not a valid 16-bit integer.".format(
            color=format(color, "X")))
    return (color & 0b00011111, (color>>5) & 0b00011111, color>>10 & 0b00011111)

def color15merge(red, green, blue):
    "Combine RGB 5-bit components into a 15-bit GBA/GBC/SNES color."
    return blue<<10 | green<<5 | red

def color15interpolate(color1, color2):
    "Interpolate between two colors, rounded down to produce a 15-bit color."
    r1, g1, b1 = color15split(color1)
    r2, g2, b2 = color15split(color2)
    red = (r1+r2)//2
    green = (g1+g2)//2
    blue = (b1+b2)//2
    return color15merge(red, green, blue)

def color15to24(color):
    """Split a 15-bit GBA/GBC/SNES RGB color into components, and pad them to
    24-bit RGB. Returns the components.

    The lowest 3 bits of each 8-bit component are filled with a copy of the
    highest 3 bits of the 5-bit input, to ensure an equal distribution in
    the 0-255 range. Multiplying by 33 (0b100001) is equivalent to creating
    an adjacent copy of the 5-bit input."""
    
    return (i*33//4 for i in color15split(color))
