"Functions for loading SMA3 entrances."

# import from other files
from AdvEditor import Adv3Attr
from AdvGame import GBA, SMA3

def loadentrances():
    return SMA3.importlevelentrances(
        Adv3Attr.filepath, maxmidpoints=Adv3Attr.maxmidpoints,
        midwaylen = 6 if Adv3Attr.midway6byte else 4)

def loadglobalentrdata(main=None, midway=None):
    if main is None or midway is None:
        main, midway = loadentrances()

    output = [[] for _ in range(SMA3.Constants.maxsublevelID + 1)]
    for levelID, (mainentr, midwayentrs) in enumerate(zip(main, midway)):
        levelstr = SMA3.levelnumber(levelID, short=True)
        if mainentr:
            output[mainentr.sublevelID].append((f"Main {levelstr}", mainentr))
        for i, entr in enumerate(midwayentrs):
            if entr:
                output[entr.sublevelID].append(
                    [f"Midway {levelstr}-{i:X}", entr])

    Adv3Attr.sublevelentr["level"] = output

def loadglobalscreenexitdata():
    output = [[] for _ in range(SMA3.Constants.maxsublevelID + 1)]
    with GBA.Open(Adv3Attr.filepath, "rb") as f:
        # read entire sublevel main pointer table
        f.seek(f.readptr(SMA3.Pointers.sublevelmainptrs))
        mainptrs = [f.readint(4) for _ in range(SMA3.Constants.maxsublevelID + 1)]

        # import screen exit destinations by sublevel
        for sublevelID, ptr in enumerate(mainptrs):
            sublevel = SMA3.Sublevel()
            f.seek(ptr)
            sublevel.importmaindata(f)
            for key, entr in sublevel.exits.items():
                destsublevelID = entr.sublevelID
                sublevelstr = f"{sublevelID:02X}"
                if destsublevelID > SMA3.Constants.maxsublevelID:
                    # Bandit minigame
                    destsublevelID = entr.anim
                    sublevelstr += f"({entr.sublevelID:02X})"
                    if destsublevelID > SMA3.Constants.maxsublevelID:
                        # nested minigame
                        destsublevelID = 0
                        sublevelstr += f"({entr.anim:02X})"
                output[destsublevelID].append(
                    [f"from {sublevelstr} {key:02X}", entr])

    Adv3Attr.sublevelentr["screenexits"] = output
