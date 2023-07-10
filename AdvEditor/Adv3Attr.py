"""Advynia SMA3 Attributes
Contains global attributes of the currently loaded ROM/sublevel."""

# import from other files
from AdvGame import SMA3
from AdvEditor import PatchData

# initialize attributes
filepath = ""
filename = ""
savedversion = None
tilemapL1_8x8 = None
tilemapL0flags = None
tile16interact = None
sublevel = SMA3.Sublevel()
sublevelentr = {}

# initialize patch flags
for key in PatchData.patches:
    globals()[key] = False

maxmidpoints = 4
