"""Advynia SMA3 Attributes
Contains global attributes of the currently loaded ROM/sublevel."""

# import from other files
from AdvGame import SMA3

# initialize attributes
filepath = ""
filename = ""
savedversion = None
tilemapL1_8x8 = None
sublevel = SMA3.Sublevel()

# initialize patch flags
midway6byte = False
musicoverride = False
object65 = False
sublevelstripes = False
world6flag = False
