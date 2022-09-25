"""Advynia SMA3 Patch Data
Constants for Adv3Patch."""

from AdvGame.SMA3 import PointersAdv

patches = {  # key:(name, text)
    "midway6byte":("6-byte Midway Entrances",
        """Allows manually specifying the camera bytes in each midway entrance.
The bytes can still be left as 00 to save/load them with the checkpoint, as
in vanilla."""),
    "musicoverride":("Music Override",
        """Allows customizing the music ID and enabling/disabling pause menu
items in every sublevel."""),
    "object65":("Object 65: Arbitrary Single Tile",
        """Adds a rectangular custom object that can be any single 16x16 
tile ID."""),
    "sublevelstripes":("Sublevel Sprite Tilesets",
        """Allows customizing the 6 stripes for every sublevel.<br>
Each sublevel's stripes will default to its current sprite tileset header
setting. The header setting will no longer be used afterward."""),
    "world6flag":("World 6 Tileset Flag",
        """Allows access to the world 6 tileset (tileset 11) in any world, and to
tileset 1 in world 6. Tilesets 10,12-1F also become selectable, but are clones of
tilesets 0,2-F."""),
    }

patchhexdata = {
    "midway6byte":(
        (0x08002ED4, bytes.fromhex("""
            44 00 80 00 00 19 09 68 09 18 45 48
0A 88 02 80 4A 88 42 80 8A 88 00 2A 01 D0 82 80
09 E0 43 4A 11 78 01 71 11 79 41 71 03 E0 00 00
00 00 00 00 00 00""")),  # patch hex code
        ),
    "musicoverride":(
        (0x0802C2D6, bytes.fromhex("95 F1 28 FE")),  # jump
        (0x081C1F2A, bytes.fromhex("""09 4A 10 78 0E 21
88 42 02 D2 07 4A 13 68 70 47 88 43 06 4A 10 70
06 4A 12 88 06 4B 98 5C 6A F7 34 FA 70 BD 00 00
B6 4B 00 03 40 72 00 03 B8 48 00 03 B8 4C 00 03
00 20 1C 08""")),  # patch hex code
        (PointersAdv.musicoverride, b"\xFF"*0x100),  # music ID table
        ),
    "object65":(
        (0x0816828C + 0x65*4, 0x081C1FC1.to_bytes(4, "little")),  # init pointer
        (0x08168AAC + 0x65*4, 0x081C1FDF.to_bytes(4, "little")),  # main pointer
        (0x081C19D8 + 0x65, b"\x06"),  # signal flag
        (0x081C1FC0, bytes.fromhex("""
30 B5 C3 8E 09 4C 24 68 E5 5C 01 33 E4 5C 01 33
C3 86 24 02 2C 43 44 87 58 F6 4A F8 30 BD 42 8F
4A 30 00 88 02 49 09 68 0A 52 70 47 14 4D 00 03
10 70 00 03""")),  # patch hex code
        ),
    "world6flag":(
        (0x08013480, bytes.fromhex("""
0E 48 01 88 0E 48 00 88 0E 4A 12 5C 12 01 11 43
C8 00 89 00 41 18 0C 48 0D 18 28 68 00 68 0B 49
1C F1 14 F9 68 68 00 68 09 49 1C F1 0F F9 A8 68
00 68 08 49 1C F1 0A F9 16 E0 00 00 9E 4B 00 03
B8 4C 00 03 54 23 1C 08 44 5C 16 08 00 20 00 06
00 30 00 06 00 00 00 06 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00""")),  # patch hex code
        (0x08013510, bytes.fromhex("4F E0")),  # skip vanilla world 6 tileset checks
        (0x08013882, bytes.fromhex("1D E0")),  # skip vanilla world 6 palette checks
        ),
    }
