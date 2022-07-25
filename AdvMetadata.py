appname = "Advynia"
version = (0, 2, 0)
printtime = False

aboutadvynia = '''
An editor for Yoshi's Island: Super Mario Advance 3, developed by Karisa. 
Work in progress.
<br><br>
For more information, join the Discord: 
<a href="https://discord.gg/mS5EcyRb8W">https://discord.gg/mS5EcyRb8W</a>
'''

export3ext = "Advynia SMA3 Export (*.a3l)"

import os

appdir = os.path.dirname(__file__)
datadir = os.path.join(appdir, "AdvData")
def datapath(*relpath):
    "Generate an absolute path to Advynia's graphics folder."
    return os.path.join(datadir, *relpath)

################################################################################

class ProgramVersion(tuple):
    def __new__(cls, seq=()):
        part = [0, 0, 0, ""]
        part[:min(len(seq), 4)] = seq[:4]
        return super().__new__(cls, part)

    def __str__(self):
        "Convert the version to a string."
        output = [str(self[0]), ".", str(self[1])]
        if self[2] or self[3]: output += ".", str(self[2])
        if self[3]: output += "-", self[3]
        return "".join(output)

    def __lt__(self, other):
        for i in range(3):
            if self[i] < other[i]:
                return True
            elif self[i] > other[i]:
                return False
        return False  # equal

    def __le__(self, other):
        for i in range(3):
            if self[i] < other[i]:
                return True
            elif self[i] > other[i]:
                return False
        return True  # equal; text component is ignored

version = ProgramVersion(version)
appnamefull = " ".join((appname, str(version)))
