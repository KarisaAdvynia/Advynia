"""Metadata TSV Parser
Imports Advynia's object/sprite metadata from TSV files."""

# standard library imports
import ast, copy, math

# import from other files
import AdvMetadata
from AdvGame import SMA3
from AdvGame.SpriteTilemapTextParser import processrawtilemap

class Metadata:
    def __repr__(self):
        output = ["<", self.__class__.__name__, ": {"]
        for key in dir(self):
            if key.startswith("_"):
                continue
            output += [repr(key), ":", repr(getattr(self, key)), ", "]
        output[-1] = "}>"
        return "".join(output)

class ObjectMetadata(Metadata):
    _objdata = ("ID", "extID", "x", "y", "adjwidth", "adjheight")
    _tilesets = [format(i, "X") for i in range(0x10)] + ["11"]
    _resizing = ("wmin", "wmax", "wstep", "hmin", "hmax", "hstep")
    _strkeys = ("name", "tooltipbase", "graphicstype")
    _numkeys = ("enabled",
                "itemmemory", "rng", "overlap", "layer0",
                "nointeract", "solid", "slope", "destroy", "danger", "warp",
                "t_anim")

    def __init__(self):
        for key in self._strkeys:
            self.__setattr__(key, "")
        for key in self._numkeys:
            self.__setattr__(key, None)
        self.preview = {"ID":0, "extID":None,
                        "x":3, "y":3, "adjwidth":3, "adjheight":3}
        self.tilesets = set()
        self.resizing = {"wmin":1, "wmax":0x80, "wstep":1,
                         "hmin":1, "hmax":0x80, "hstep":1,
                         "horiz":0, "vert":0}

class SpriteMetadata(Metadata):
    _sprdata = ("ID", "extID", "x", "y")
    _strkeys = ("name", "tooltipbase", "tilemap", "graphicstype")
    _numkeys = ("enabled", "parity",
                "itemmemory", "rng", "overlap",
                "nointeract", "enemy", "item", "standable", "warp")

    def __init__(self):
        for key in self._strkeys:
            self.__setattr__(key, "")
        for key in self._numkeys:
            self.__setattr__(key, None)
        self.preview = {"ID":0, "extID":None, "x":4, "y":4}

class ObjectMetadataMapping(dict):
    "Subclass of dict, with fallback for objects with arbitrary extID."
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return dict.__getitem__(self, (key[0], None))

class SpriteMetadataMapping(dict):
    "Subclass of dict, with fallback for undefined sprite parity values."
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            paritybits = dict.__getitem__(self, (key[0], None)).parity
            if paritybits:
                newkey = (key[0], key[1] & paritybits)
                if newkey in self:
                    return dict.__getitem__(self, newkey)
            return dict.__getitem__(self, (key[0], None))

def _importmetadata(file):
    """Convert metadata from the spreadsheet .tsv export to a list of dicts,
    with first row as keys."""
    with open(file, mode="r", encoding="UTF-8") as f:
        keys = f.readline().rstrip("\n").split(sep="\t")
        lines = []
        while True:
            line = f.readline().rstrip("\n").split(sep="\t")
            if line == [""]:
                break
            lines.append({})
            for i, key in enumerate(keys):
                lines[-1][key] = line[i]
    return lines

def _importobjmetadata(file):
    "Import and process the objects' metadata."
    rawlines = _importmetadata(file)

    output = ObjectMetadataMapping()
    for rawline in rawlines:
        objID = ast.literal_eval(rawline["ID"])
        extID = ast.literal_eval(rawline["extID"])
        output[(objID, extID)] = ObjectMetadata()
        metadata = output[(objID, extID)]

        for key in ObjectMetadata._objdata:
            if rawline[key]:
                metadata.preview[key] = ast.literal_eval(rawline[key])
        for key in ObjectMetadata._tilesets:
            if rawline[key]:
                metadata.tilesets.add(int(key, base=16))
        for key in ObjectMetadata._resizing:
            if rawline[key]:
                metadata.resizing[key] = ast.literal_eval(rawline[key])
        for key in ObjectMetadata._numkeys:
            if rawline[key]:
                setattr(metadata, key, ast.literal_eval(rawline[key]))
            elif key == "enabled":
                pass
            else:
                setattr(metadata, key, 0)
        for key in ObjectMetadata._strkeys:
            setattr(metadata, key, rawline[key])

        # Construct graphics type string, if not already present
        if metadata.enabled and not metadata.graphicstype:
            text = []
            if len(metadata.tilesets) == 0x11:
                text.append("Global")
            elif metadata.tilesets:
                text.append("L1=")
                text.append(" ".join(
                    format(i, "X") for i in sorted(metadata.tilesets)))
            if metadata.t_anim:
                if text: text.append(" + ")
                text += "A=", format(metadata.t_anim, "02X")
            metadata.graphicstype = "".join(text)
        # account for special graphics types
        elif metadata.graphicstype == "train":
            metadata.graphicstype = "L2=05 06 07 0D 0E 18"

        # Construct full tooltip

        tooltipname = metadata.name
        if not metadata.name:
            tooltipname = "<i>Unimplemented</i>"

        # abbreviate the word "background" only in the short name
        tooltipstart = "Object {objID}: " + tooltipname.format(
            bg="background", Bg="Background")
        metadata.name = metadata.name.format(bg="BG", Bg="BG")

        # make first line nonbreaking
        tooltip = [nonbreakingstr(tooltipstart)]

        if metadata.tooltipbase:
            tooltip.append(metadata.tooltipbase)

        if metadata.resizing["wmin"] == metadata.resizing["wmax"]:
            tooltip.append("".join(
                ("<i>Only width=", format(metadata.resizing["wmin"], "02X"),
                 " supported</i>")))
        elif metadata.resizing["wmax"] <= 1:
            tooltip.append("<i>Only negative widths supported</i>")
        if metadata.resizing["hmin"] == metadata.resizing["hmax"]:
            tooltip.append("".join(
                ("<i>Only height=", format(metadata.resizing["hmin"], "02X"),
                 " supported</i>")))
        elif metadata.resizing["hmax"] <= 1:
            tooltip.append("<i>Only negative heights supported</i>")
        if metadata.itemmemory:
            tooltip.append("<i>Affected by item memory</i>")
        if metadata.rng:
            tooltip.append("<i>Affected by RNG</i>")
        metadata.tooltiplong = "<br>".join(tooltip)

        # Determine valid resize directions

        resizing = metadata.resizing

        if resizing["wstep"] != 0 and resizing["wmin"] != resizing["wmax"]:
            if resizing["wmax"] > 1:
                resizing["horiz"] |= 1  # enable right
            if resizing["wmin"] < 1:
                resizing["horiz"] |= 2  # enable left
        if resizing["hstep"] != 0 and resizing["hmin"] != resizing["hmax"]:
            if resizing["hmax"] > 1:
                resizing["vert"] |= 1  # enable down
            if resizing["hmin"] < 1:
                resizing["vert"] |= 2  # enable up

        # change resize min/max from adjusted to unadjusted
        if resizing["horiz"]:
            resizing["wmin"] = SMA3.Object._unadjlength(resizing["wmin"])
            resizing["wmax"] = SMA3.Object._unadjlength(resizing["wmax"])
        if resizing["vert"]:
            resizing["hmin"] = SMA3.Object._unadjlength(resizing["hmin"])
            resizing["hmax"] = SMA3.Object._unadjlength(resizing["hmax"])

    return output

def _importsprmetadata(file):
    "Import and process the sprites' metadata."
    rawlines = _importmetadata(file)

    output = SpriteMetadataMapping()
    for rawline in rawlines:
        sprID = ast.literal_eval(rawline["ID"])
        extID = ast.literal_eval(rawline["extID"])
        if extID is not None and ((sprID, None) in output):
            metadata = copy.deepcopy(output[(sprID, None)])
        else:
            metadata = SpriteMetadata()
        output[(sprID, extID)] = metadata

        for key in SpriteMetadata._sprdata:
            if rawline[key]:
                metadata.preview[key] = ast.literal_eval(rawline[key])
        for key in SpriteMetadata._numkeys:
            if rawline[key]:
                setattr(metadata, key, ast.literal_eval(rawline[key]))
            elif extID is not None or key == "enabled":
                pass
            else:
                setattr(metadata, key, 0)
        for key in SpriteMetadata._strkeys:
            if rawline[key]:
                setattr(metadata, key, rawline[key])

    for key, metadata in output.items():
        sprID, extID = key

        tilemap, stripes, dynamic = processrawtilemap(metadata.tilemap)

        if tilemap:
            metadata.tilemap = tilemap

            # Calculate sprite pixmap offset/size
            xmin = []
            ymin = []
            xmax = []
            ymax = []
            for attr in tilemap:
                if attr.angle or attr.scaleX != 1 or attr.scaleY != 1:
                    # account for rotate/scale in min/max
                    newwidth, newheight = rotaterectbox(
                        attr.width, attr.height, attr.angle)
                    newwidth *= attr.scaleX
                    newheight *= attr.scaleY
                    widthoffset = (newwidth - attr.width) / 2
                    heightoffset = (newheight - attr.height) / 2
                    xmin.append(round(attr.x - widthoffset))
                    ymin.append(round(attr.y - heightoffset))
                    xmax.append(round(attr.x + attr.width + widthoffset))
                    ymax.append(round(attr.y + attr.height + heightoffset))
                else:
                    xmin.append(attr.x)
                    ymin.append(attr.y)
                    xmax.append(attr.x + attr.width)
                    ymax.append(attr.y + attr.height)
            metadata.offset = (min(xmin), min(ymin))
            metadata.pixmapsize = (max(xmax) - metadata.offset[0],
                                   max(ymax) - metadata.offset[1])

            # Construct graphics type string, if not already present
            if not metadata.graphicstype:
                text = []
                if stripes:
                    text.append("Stripe ")
                    text.append("+".join(format(stripe, "02X")
                                for stripe in sorted(stripes)))
                if dynamic:
                    if text: text.append(" + ")
                    text.append("Dynamic")

                if text:
                    metadata.graphicstype = "".join(text)
                else:
                    metadata.graphicstype = "Global"
        else:
            metadata.tilemap = []

        # Construct full tooltip

        tooltipname = metadata.name
        if extID is not None and extID < 4:
            # use base name for parity sprites
            tooltipname = output[sprID, None].name
        if not tooltipname:
            tooltipname = "<i>Unimplemented</i>"

        tooltipstart = "".join((
            "Sprite ", format(sprID, "03X"), ": ", tooltipname))

        # make first line nonbreaking
        tooltip = [nonbreakingstr(tooltipstart)]

        if metadata.tooltipbase:
            tooltip.append(metadata.tooltipbase)

        # add parity
        if extID is not None and extID < 4:
            if metadata.parity == 3:
                line = ["<i>Affected by YX parity:"]
                for i in range(4):
                    line.append(" ")
                    if i == extID: line.append("<b>")
                    text = output[sprID, i].name
                    if not text: text = "???"
                    line += ["[", format(i, "02b"), "]:", nonbreakingstr(text)]
                    if i == extID: line.append("</b>")
                line.append("</i>")
                tooltip.append("".join(line))
            elif metadata.parity in (1, 2):
                if metadata.parity == 1:
                    line = ["<i>Affected by X parity:"]
                else:
                    line = ["<i>Affected by Y parity:"]
                for i in (0, metadata.parity):
                    line.append(" ")
                    if i == extID: line.append("<b>")
                    text = output[sprID, i].name
                    if not text: text = "???"
                    line += ["[", str(i//metadata.parity), "]:",
                             nonbreakingstr(text)]
                    if i == extID: line.append("</b>")
                line.append("</i>")
                tooltip.append("".join(line))

        if metadata.itemmemory:
            tooltip.append("<i>Affected by item memory</i>")
        if metadata.rng:
            tooltip.append("<i>Affected by RNG</i>")

        metadata.tooltiplong = "<br>".join(tooltip)

    return output

def nonbreakingstr(text):
    "Replace spaces/hyphens in a string with their nonbreaking equivalents."
    text = list(text)
    for i, char in enumerate(text):
        match char:
            case " ":
                text[i] = "\u00A0"  # nonbreaking space
            case "-":
                text[i] = "\u2011"  # nonbreaking hyphen
            case "." | ":" | "/":
                # nonbreaking character since for an unknown reason,
                #  Qt line-breaks on these characters
                text[i] += "\u2060"
    return "".join(text)

def rotaterectbox(width, height, degrees):
    "Return the bounding box of a rotated rectangle."
    angle = math.radians(degrees)
    return (abs(math.cos(angle)*width) + abs(math.sin(angle)*height),
            abs(math.sin(angle)*width) + abs(math.cos(angle)*height))

ObjectMetadata = _importobjmetadata(
    AdvMetadata.datapath("tsv", "SMA3ObjectMetadata.tsv"))
SpriteMetadata = _importsprmetadata(
    AdvMetadata.datapath("tsv", "SMA3SpriteMetadata.tsv"))

########

if __name__ == "__main__":
    tilemapcount = 0
    totalsprites = 512
    enabledcount = [0]*5
    paritycount = [0]*4
    for i in range(totalsprites):
        metadata = SpriteMetadata[(i, None)]
        enabled = metadata.enabled
        if enabled is None:
            enabled = 4
        enabledcount[enabled] += 1
        if enabled == 3:
            paritycount[metadata.parity] += 1

        for parity in range(metadata.parity + 1):
            if SpriteMetadata[(i, parity)].tilemap:
                tilemapcount += 1
                break
        else:
            if enabled < 3:
                totalsprites -= 1

    print("".join((
        "Sprite tilemaps implemented: ", str(tilemapcount),
        "/", str(totalsprites))))
    print("Sprites disabled:{0}, glitch:{1}, non-recommended:{2}, "
          "recommended:{3}, None:{4}".format(*enabledcount))
    print("Parity:  None:{0}, X:{1}, Y:{2}, XY:{3}".format(*paritycount))
##    print(ObjectMetadata[(0xFD, 0)])
##    print(ObjectMetadata[(0, 0x82)])
##    print(SpriteMetadata[(0x1E, None)])
