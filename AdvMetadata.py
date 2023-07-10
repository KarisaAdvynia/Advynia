appname = "Advynia"
version = (0, 5, 0)
printtime = False

aboutadvynia = '''
An editor for Yoshi's Island: Super Mario Advance 3, developed by Karisa. 
Work in progress.
<br><br>
For more information, join the Discord: 
<a href="https://discord.gg/mS5EcyRb8W">https://discord.gg/mS5EcyRb8W</a>
'''

# pixelwidths of AdvData/advpixelfont.bin
fontwidths = [
    0,0,0,0,0,0,0,0, 0,5,0,0,0,0,0,0,  ## unprintable
    0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,  ## unprintable
    2,3,4,6,5,5,5,3, 4,4,4,4,3,4,3,5,  #  !"#$%&'()*+,-./
    5,5,5,5,5,5,5,5, 5,5,3,3,4,4,4,5,  # 0123456789:;<=>?
    6,5,5,5,5,5,5,6, 5,5,5,5,5,7,6,5,  # @ABCDEFGHIJKLMNO
    5,5,5,5,5,5,5,7, 5,5,5,4,5,4,4,5,  # PQRSTUVWXYZ[\]^_
    3,5,5,5,5,5,5,5, 5,3,5,5,3,7,5,5,  # `abcdefghijklmno
    5,5,5,5,5,5,5,7, 5,5,5,5,5,3,5,0]  # pqrstuvwxyz{|}~
fontheight = 9

# calculate app directory

import os
from pathlib import Path

_path = Path(__file__)
for _i, _part in enumerate(_path.parts):
    if _part.endswith(".app"):
        # if this is a Mac app, use first directory outside the .app
        appdir = _Path(*_path.parts[0:_i]).as_posix()
        break
else:
    # use directory of the executable
    appdir = _path.parent.as_posix()

datadir = os.path.join(appdir, "AdvData")
def datapath(*relpath):
    "Generate an absolute path to Advynia's data folder."
    return os.path.join(datadir, *relpath)

################################################################################

class ProgramVersion(tuple):
    def __new__(cls, seq=()):
        part = [0, 0, 0, ""]
        part[:min(len(seq), 4)] = seq[:4]
        return super().__new__(cls, part)

    def __bool__(self):
        return self != (0, 0, 0, "")

    def __str__(self):
        output = f"{self[0]}.{self[1]}"
        if self[2] or self[3]:
            output += f".{self[2]}"
        if self[3]:
            output += f"-{self[3]}"
        return output

    # ignore text components when comparing
    def __lt__(self, other):
        return self[0:3] < other[0:3]
    def __gt__(self, other):
        return self[0:3] > other[0:3]
    def __le__(self, other):
        return self[0:3] <= other[0:3]
    def __ge__(self, other):
        return self[0:3] >= other[0:3]

version = ProgramVersion(version)
appnamefull = f"{appname} {version}"
