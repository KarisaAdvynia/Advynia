"""SMA3 Layer 1 Tilemap: Shared Generators/Classes"""

import itertools

class MultiTileID(int):
    """Used to generate tiles that act like one tile ID for overlap code, but
    display as another tile ID for error purposes."""
    def __new__(cls, mainID, displayID):
        x = int.__new__(cls, mainID)
        x.displayID = displayID
        return x

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__index__():#x}, {self.displayID:#x})"

    def __deepcopy__(self, _):  # without this, deepcopy crashes
        return MultiTileID(self, self.displayID)

    def __eq__(self, other):
        if not isinstance(other, MultiTileID): return False
        return other.displayID == self.displayID

def genseq_bordered(length, first=0, mid=1, last=2):
    """Generate a sequence of a specified length, with distinct first and last
    values, defaulting to a single value in between."""
    yield first
    if length > 1:
        for i in range(length-2):
            yield mid
        yield last

def genseq_bordered_cycle(length, first, midseq, last):
    """Generate a sequence of a specified length, with distinct first and last
    values, cycling between values in between."""
    yield first
    if length > 1:
        miditer = itertools.cycle(midseq)
        for i in range(length-2):
            yield next(miditer)
        yield last

def gen_rectindex(a, b):
    """Generate indexes from 0 to 8, used to determine the corner/edge/center
    tiles of a rectangle with dimensions a,b."""
    if a == 0:
        yield 0
        if b != 0:
            for i in range(b-1):
                yield 3
            yield 6
    else:
        # first edge
        yield 0
        for i in range(a-1):
            yield 1
        yield 2
        if b != 0:
            # central lines
            for i in range(b-1):
                yield 3
                for i in range(a-1):
                    yield 4
                yield 5
            # last edge
            yield 6
            for i in range(a-1):
                yield 7
            yield 8

def gen_rectindex_parity2(a, b):
    """Generate indexes from 0 to 15, used to determine the corner/edge/center
    tiles of a rectangle with dimensions a,b, where edge/center tiles are
    affected by parity in both directions."""
    if a == 0:
        yield from genseq_bordered_cycle(b+1, 0, (4, 8), 12)
    else:
        # first edge
        yield from genseq_bordered_cycle(a+1, 0, (1, 2), 3)
        if b != 0:
            # central lines
            b_offset = 0
            for i in range(b-1):
                yield from genseq_bordered_cycle(a+1,
                    4 + b_offset, (5 + b_offset, 6 + b_offset), 7 + b_offset)
                b_offset ^= 4
            # last edge
            yield from genseq_bordered_cycle(a+1, 12, (13, 14), 15)

def gen_iter_default(iterable, default):
    yield from iterable
    while True:
        yield default
