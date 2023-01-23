appname = "Advynia"
version = (0, 4, 1)
printtime = False

aboutadvynia = '''
An editor for Yoshi's Island: Super Mario Advance 3, developed by Karisa. 
Work in progress.
<br><br>
For more information, join the Discord: 
<a href="https://discord.gg/mS5EcyRb8W">https://discord.gg/mS5EcyRb8W</a>
'''

import os

appdir = os.path.dirname(__file__)
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
        output = [str(self[0]), ".", str(self[1])]
        if self[2] or self[3]:
            output += ".", str(self[2])
        if self[3]:
            output += "-", self[3]
        return "".join(output)

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
appnamefull = " ".join((appname, str(version)))
