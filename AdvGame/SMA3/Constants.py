"""SMA3 Constants

Non-pointer constants."""

maxlevel = 0x47
maxsublevel = 0xF5
maxsublevelscreenexit = 0xFF

maxscreen = 0x7F
maxtileX = 0xFF
maxtileY = 0x7F

levelnumrighthalf = ("1", "2", "3", "4", "5", "6", "7", "8",
                    "Secret", "Extra", "Bonus", "Controls")

headersettings = [
    "Background Color",
    "Layer 1 Tileset",
    "Layer 1 Palette",
    "Layer 2 Image",
    "Layer 2 Palette",
    "Layer 3 Image",
    "Layer 3 Palette",
    "Sprite Tileset", 
    "Sprite Palette", 
    "Layer Effects?", 
    "Graphics Animation",
    "Palette Animation",
    "Layer 2/3 Scroll?",
    "Header Music",
    """Item Memory Index/
Middle Ring ID""",
    ]

headermaxvalues = [0x1F, 0x0F, 0x1F, 0x1F, 0x3F, 0x2F, 0x3F, 0x95,
                   0x0F, 0x0F, 0x12, 0x14, 0x1F, 0x0F, 3]
# header defaults: "None" value if one exists, else 0
headerdefaults = [0, 0, 0, 0x1B, 0, 0, 0, 0,
                  0, 0, 4, 0, 0, 0, 0]

# header subset for palettes
headerpalettes = (2, 4, 6, 0, 8, 0xB)
# header subset for graphics
headergraphics = (1, 3, 5, 7, 0xA)

headernames = {
    1:(
        "Cave + background walls",
        "Grass + background walls",
        "Submarine",
        "2.5D + Hookbill blocks",
        "Snow",
        "Jungle",
        "Castle (striped)",
        "Meadow + background walls",
        "Cave + mushrooms/ice/lava",
        "Grass + Forest",
        "Castle (wooden)",
        "Sewer",
        "Flower",
        "Meadow + clouds/bridges",
        "Castle (stone)",
        "Meadow + line-guides",
        "",
        "W6 Wasteland",
        "", "", "", "", "", "", "", "", "", "", "", "", "", "",
        ),
    3:(
        "Cave waterfalls/lavafalls",
        "Tree trunks and bushes",
        "Submarine BG",
        "2.5D lava room (L1=3)",
        "Mountains, trees, hills",
        "Distant fog-shrouded evergreens",
        "Castle wall with torches",
        "Vertical-sided hills",
        "Forest with flowering canopy",
        "(same as 10)",
        "Trees and waterfalls",
        "Grassy platforms (A=02/0B)",
        "Forest with straight canopy",
        "Starry sky with moon",
        "Spiral-decorated platforms",
        "Volcanoes (A=02/0B)",
        "Mountains with forest in front",
        "(glitch)",
        "Sea with clouds",
        "Cave with crystals",
        "Building interior with windows",
        "Snowcapped mountains",
        "Layer 2 boss graphics",
        "(glitch)",
        "Jungle interior with windows",
        "Castle ramparts",
        "Snowcapped cloudy mountains",
        "None",
        "Smiley hills",
        "Rounded mountains (A=02/0B)",
        "Evergreen forest",
        "Baby Bowser's room",
        ),
    5:(
        "None",
        "Submarine water (A=01)",
        "(Layer 3 sprites TBD)",
        "(glitch)",
        "Smiley clouds (A=03/11)",
        "(Layer 3 sprites TBD)",
        "(Layer 3 sprites TBD)",
        "(Layer 3 sprites TBD)",
        "(Layer 3 sprites TBD)",
        "",
        "FG hides land BG walls (L1=?)",
        "",
        "Diagonal light beams",
        "Tall clouds?",
        "",
        "",
        "",
        "Pre-Hookbill mist",
        "Starry sky",
        "Interactive wavy water (A=05)",
        "",
        "Foreground crystals",
        "Shark Chomp (sprite 154)",
        "",
        "Castle ramparts (A=06)",
        "Snowing foreground (A=09)",
        "Clouds/Goonies (A=0A)",
        "Bushes/flowers (butterfly A=0B)",
        "Dark room + Yoshi light circle",
        "",
        "",
        "",
        "Bushes/clouds (A=0F)",
        "Froggy interior",
        "",
        "Sunset (A=0F)",
        "Moon/stars with auras",
        "",
        "Bigger Boo/Milde explosion",
        "",
        "Light snow?",
        "Large clouds (variant)",
        "Large moon",
        "Large clouds (variant)",
        "Foreground mist",
        "(same as 2C)",
        "Large clouds (variant)",
        "",
        ),
    7:(
        "Stripes 20 21 2A 2B 5E 29", 
        "Stripes 20 21 5E 1C 31 29", 
        "Stripes 1F 2C 36 40 51 29", 
        "Stripes 2E 5E 37 1A 1A 1F", 
        "Stripes 55 5E 5F 1F 1A 29", 
        "Stripes 53 40 51 1A 1A 29", 
        "Stripes 36 2A 2B 3C 2D 71", 
        "Stripes 4A 36 1C 71 31 59", 
        "Stripes 6A 1A 1A 1A 1A 1A", 
        "Stripes 50 71 2F 31 49 29", 
        "Stripes 55 57 5D 71 1C 2F", 
        "Stripes 55 71 3C 57 4A 1C", 
        "Stripes 3C 3F 1F 71 1A 1A", 
        "Stripes 25 71 1C 1A 1A 1A", 
        "Stripes 2E 1A 1A 1A 1A 1F", 
        "Stripes 36 57 38 1C 5C 29", 
        "Stripes 3A 3B 31 55 71 29", 
        "Stripes 60 61 1C 22 23 25", 
        "Stripes 1C 25 42 43 4F 29", 
        "Stripes 5A 5B 5C 25 6A 29", 
        "Stripes 1F 37 39 42 43 1A", 
        "Stripes 27 35 4E 3D 1A 30", 
        "Stripes 4E 1C 51 46 71 29", 
        "Stripes 22 23 45 60 1A 30", 
        "Stripes 42 43 38 39 1C 59", 
        "Stripes 60 1D 71 4E 1C 30", 
        "Stripes 60 1D 40 46 4E 30", 
        "Stripes 55 1D 60 4E 51 1A", 
        "Stripes 36 63 1F 5C 1A 29", 
        "Stripes 39 1D 35 1B 63 30", 
        "Stripes 71 1A 51 5F 60 30", 
        "Stripes 2A 63 1A 1A 1A 1A", 
        "Stripes 27 3E 1A 3D 1A 1A", 
        "Stripes 25 2B 47 64 36 1F", 
        "Stripes 51 61 48 65 1C 60", 
        "Stripes 48 1C 65 28 60 71", 
        "Stripes 1C 45 1F 71 6A 29", 
        "Stripes 4D 6A 48 1F 1A 29", 
        "Stripes 28 60 38 4E 36 51", 
        "Stripes 1A 1A 2D 1A 1A 1A", 
        "Stripes 45 35 54 64 1F 1C", 
        "Stripes 54 58 35 3D 71 64", 
        "Stripes 35 41 1F 64 5C 1C", 
        "Stripes 32 33 34 41 4C 54", 
        "Stripes 64 1E 41 1F 1C 29", 
        "Stripes 55 1E 28 60 71 5C", 
        "Stripes 64 4C 41 40 68 29", 
        "Stripes 2F 5C 5D 1C 1A 1A", 
        "Stripes 27 65 49 AA 1C 1F", 
        "Stripes 61 48 71 1C 55 6A", 
        "Stripes 71 3C 60 3F 49 AA", 
        "Stripes 53 1A 1C 55 31 59", 
        "Stripes 42 43 55 1F 41 1A", 
        "Stripes 2A 2B 29 71 1C 5D", 
        "Stripes 55 1F 27 2A 1A 29", 
        "Stripes 4F 2B 47 52 60 51", 
        "Stripes 2B 47 38 71 60 51", 
        "Stripes 40 29 31 4E 1C 59", 
        "Stripes 1C 1A 1A 4E 1A 1A", 
        "Stripes 2B 47 26 52 56 29", 
        "Stripes 2B 47 26 52 31 29", 
        "Stripes 2B 47 1F 29 31 51", 
        "Stripes 2B 47 2F 1E 71 29", 
        "Stripes 29 1A 1A 53 1B 1F", 
        "Stripes 31 40 1F 1A 1A 1A", 
        "Stripes 41 35 39 71 1F 29", 
        "Stripes 2B 47 24 49 1A 1F", 
        "Stripes 1F 5C 49 4E 5D 47", 
        "Stripes 3A 3B 1C 1A 1A 29", 
        "Stripes 1F 1A 38 1A 1A 1A", 
        "Stripes 2B 47 37 54 71 29", 
        "Stripes 3F 3C 66 1C 47 60", 
        "Stripes 31 35 71 54 55 1F", 
        "Stripes 2E 1F 49 24 5E 29", 
        "Stripes 58 54 5E 1F 48 29", 
        "Stripes 60 65 30 71 1A 1A", 
        "Stripes 5E 29 71 26 49 4B", 
        "Stripes 55 2F 58 64 2C 59", 
        "Stripes 5E 24 1C 29 49 4B", 
        "Stripes 27 25 38 49 2A 29", 
        "Stripes 1F 36 4E 1A 1A 1A", 
        "Stripes 4D 1F 55 28 60 71", 
        "Stripes 2E 71 1C 1A 1A 1A", 
        "Stripes 35 39 41 25 64 29", 
        "Stripes 64 25 36 41 1A 29", 
        "Stripes 4E 44 1A 3D 48 29", 
        "Stripes 5D 1E 36 3D 25 48", 
        "Stripes 42 43 44 6A 1A 1A", 
        "Stripes 64 45 1A 1A 1F 29", 
        "Stripes 2A 2B 38 6A 6C 5E", 
        "Stripes 55 31 1A 1A 1A 1F", 
        "Stripes 35 3E 1C 3D 2B 47", 
        "Stripes 2A 2B 5E 63 1A 1A", 
        "Stripes 24 1A 1A 1A 1A 1A", 
        "Stripes 1A 36 31 29 66 59", 
        "Stripes 40 3A 3B 37 36 1A", 
        "Stripes 2F 70 61 6A 1A 1F", 
        "Stripes 6B 6C 1A 6A 47 1F", 
        "Stripes 57 5C 5D 24 1C 29", 
        "Stripes 1B 71 29 1C 1F 5D", 
        "Stripes 55 5C 5F 45 71 37", 
        "Stripes 6F 6D 6E 29 6A 1A", 
        "Stripes 55 6A A9 1A 1A 1F", 
        "Stripes 62 3C 4E 53 71 44", 
        "Stripes 68 6A 1A 1A 1A 1A", 
        "Stripes 1A 1E 52 1F 71 29", 
        "Stripes 5D 44 4C 56 1A 1A", 
        "Stripes 1C 29 44 2A 71 4E", 
        "Stripes 45 71 1C 58 1A 1A", 
        "Stripes 55 25 71 1F 29 1C", 
        "Stripes 5D 37 71 29 1C 1A", 
        "Stripes 45 6A 1F 1A 1A 1A", 
        "Stripes 1F 64 41 53 3E 1C", 
        "Stripes 53 71 5D 1C 1A 1A", 
        "Stripes 36 1C 38 28 60 29", 
        "Stripes 2B 47 20 21 1C 71", 
        "Stripes 20 21 2F 1C 5D 47", 
        "Stripes 27 35 41 54 64 68", 
        "Stripes 1C 71 2C 2D 1A 1A", 
        "Stripes 6A 6C 63 1A 1A 1A", 
        "Stripes 22 23 45 60 1A 30", 
        "Stripes 67 3C 55 1A 1A 29", 
        "Stripes 54 71 41 4C 64 37", 
        "Stripes AD AE AF B0 67 6A", 
        "Stripes 55 47 57 49 1C 29", 
        "Stripes 27 2B 47 1C 25 29", 
        "Stripes 27 71 1C 31 1A 1A", 
        "Stripes 1C 45 1F 71 46 29", 
        "Stripes 20 21 1C 71 36 1C", 
        "Stripes 20 21 4C 51 71 29", 
        "Stripes 55 47 51 4E 1C 1C", 
        "Stripes 51 31 38 2A 46 1C", 
        "Stripes 47 1D 29 59 1C 1D", 
        "Stripes 35 68 1F 29 1C 1C", 
        "Stripes 35 3E 1A 3D 1A 1A", 
        "Stripes 2E 1C 1C 71 1C 1C", 
        "Stripes 1A 1E 1A 1A 1A 29", 
        "Stripes 2B 47 1C 1A 31 1A", 
        "Stripes 2B 47 37 71 1C 1C", 
        "Stripes 2B 47 1A 52 31 1C", 
        "Stripes 2B 47 1C 1A 31 1A", 
        "Stripes 27 5D 1C 4E 71 29", 
        "Stripes 27 51 45 4E 71 29", 
        "Stripes 27 5E 37 2E 1C 29", 
        "Stripes 59 31 26 56 35 29", 
        "Stripes 66 45 30 51 31 1C", 
        "Stripes 27 57 38 4E 1C 1C", 
        "Stripes 3A 3B 1C 71 1C 1C", 
        "Stripes 1F 64 38 5C 1C 1C", 
        "Stripes 20 21 5E 1C 6A 6C",
        ),
    0x9:(
        "None",
        "None?",
        "None?",
        "None?",
        "None?",
        "None?",
        "???",
        "None?",
        "None?",
        "Raphael's moon",
        "Kamek block room",
        "None?",
        "None?",
        "Froggy interior",
        "None?",
        "None?",
        ),
    0xA:(
        "None (clear animated region)",
        "Water for L3=01",
        "Clouds for L2=0B/0F/1D",
        "Smiley clouds for L3=04",
        "None (do nothing)",
        "Water waves for L3=13",
        "Torches for L3=18/?",
        "Lava for object 47",
        "Water for object DC",
        "Foreground snow for L3=19",
        "Goonies for L3=1A",
        "Butterfly for L3=1B + 02's clouds",
        "Water for object 35",
        "Animations 06+07",
        "Animations 06+0C",
        "Clouds for L3=20/23",
        "(glitch)",
        "Animations 03+0C",
        "2.5D lava for object FE",
        ),
    0xB:(
        "None",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        ),
    }

# flags for whether each layer 2/3 ID is a background/foreground image (display)
#  or another purpose (don't display)
layer23enable = {
    2:(
        1, 1, 1, 1, 1, 1, 1, 1,  # 00-07
        1, 1, 1, 1, 1, 1, 1, 1,  # 08-0F
        1, 1, 1, 1, 1, 1, 0, 1,  # 10-17
        1, 1, 1, 1, 1, 1, 1, 1,  # 18-1F
        ),
    3:(
        1, 1, 0, -1, 1, 0, 0, 0,  # 00-07
        0, -1, 0, 0, 1, 1, 1, 1,  # 08-0F
        1, -1, 1, 1, 1, 1, 0, -1,  # 10-17
        1, -1, -1, 1, 0, -1, -1, 0,  # 18-1F
        1, 1, 1, 1, 1, 1, 0, 1,  # 20-27
        1, 1, -1, 1, 1, 1, 1, 1,  # 28-2F
        ),
    }

entranceanim = (
    "None / X door closing",
    "On skis",
    "Pipe, rightward",
    "Pipe, leftward",
    "Pipe, downward",
    "Pipe, upward",
    "Screen edge, rightward",
    "Screen edge, leftward",
    "Screen edge, downward",
    "Launch upward",
    "Raphael's moon"
    )

banditminigames = (
    "Throwing Balloons (4)",
    "Throwing Balloons (5)",
    "Throwing Balloons (6)",
    "",
    "Gather Coins",
    "Popping Balloons (+10)",
    "Popping Balloons (+20)",
    "",
    "",
    "Seed Spitting Contest",
    )

stripes = (
    (0x1A, "Hookbill BG/null stripe"),
    (0x1B, "Chomps, BG Shy Guy, Raphael (1/2)"),
    (0x1C, "Red arrows, Raphael (2/2)"),
    (0x1D, "Zeus Guy"),
    (0x1E, "Melon Bug, Harry Hedgehog"),
    (0x1F, "Egg Plant, Barney Bubble"),
    (0x20, "Falling stone block (1/2)"),
    (0x21, "Falling stone block (2/2)"),
    (0x22, "Boo Blah (1/2)"),
    (0x23, "Boo Blah (2/2)"),
    (0x24, "Heading Pokey"),
    (0x25, "Nipper Plant, Gusty (long horizontal)"),
    (0x26, "Spike (enemy), Goomba"),
    (0x27, "Huffin Puffin, Stretch Shy Guy"),
    (0x28, "Little Mouser"),
    (0x29, "Milde, Piranha Plant, Tap-Tap"),
    (0x2A, "Goonie, rotation block"),
    (0x2B, "Wings for Paratroopa/Goonie"),
    (0x2C, "Gusty (vertical back and forth)"),
    (0x2D, "Gusty (horizontal back and forth)"),
    (0x2E, "Ski Lift, Train Shy Guy"),
    (0x2F, "Eggo-Dil, giant egg"),
    (0x30, "Blindfold Boo, Pyro Guy"),
    (0x31, "Bullet Bill, rotating doors 1-2"),
    (0x32, "Lunge Fish (1/3)"),
    (0x33, "Lunge Fish (2/3)"),
    (0x34, "Lunge Fish (3/3)"),
    (0x35, "Spear Guy (shielded), Clawdaddy"),
    (0x36, "Blow Hard, Spiked Fun Guy"),
    (0x37, "Stilt Guy"),
    (0x38, "Baseball Boys"),
    (0x39, "Spear Guy (dancing)"),
    (0x3A, "Poochy (1/2)"),
    (0x3B, "Poochy (2/2)"),
    (0x3C, "Boo Guy (working)"),
    (0x3D, "Boo Guy (relay)"),
    (0x3E, "Submarine enemies"),
    (0x3F, "Boo Guy (raising a spiked ball)"),
    (0x40, "Snifit, rotating doors 3-4"),
    (0x41, "Georgette Jelly"),
    (0x42, "Large ghosts (1/2)"),
    (0x43, "Large ghosts (2/2)"),
    (0x44, "Flower pot"),
    (0x45, "Slime Drop, Salvo, Piro Dangle"),
    (0x46, "Spooky Shy Guy, Grim Leecher"),
    (0x47, "Koopa"),
    (0x48, "Boo (1x1), buoyant post, keyhole cork"),
    (0x49, "Lakitu"),
    (0x4A, "Kaboomba"),
    (0x4B, "Thunder Lakitu"),
    (0x4C, "Buoyant grassy platform, Donut Lift"),
    (0x4D, "Tap-Tap the Red Nose/Golden"),
    (0x4E, "Bandit, spiked weight for ? gear"),
    (0x4F, "Raven (wall-following), Aqua Lakitu"),
    (0x50, "Fat Guy"),
    (0x51, "Lava Drop"),
    (0x52, "Fuzzy"),
    (0x53, "Nep-Enut?, Shark Chomp?"),
    (0x54, "Cheep-Cheep"),
    (0x55, "Lantern Ghost, Sluggy, Fang"),
    (0x56, "Flutter"),
    (0x57, "Arrow clouds"),
    (0x58, "Spray Fish"),
    (0x59, "Grunt, Mace Guy"),
    (0x5A, "Naval Piranha vines (1/2)"),
    (0x5B, "Naval Piranha vines (2/2)"),
    (0x5C, "Vine from winged cloud"),
    (0x5D, "Petal Guy, Crazee Dayzee"),
    (0x5E, "Bumpty, bird decoration"),
    (0x5F, "Falling icicle"),
    (0x60, "Boo Guy, Little Mouser (skull mask)"),
    (0x61, "Boo (2x2)"),
    (0x62, "Blargg"),
    (0x63, "Skeleton Goonie"),
    (0x64, "Monkey"),
    (0x65, "Firebar, Boo Balloon, pumpable balloon"),
    (0x66, "Hot Lips"),
    (0x67, "Kamek (standing, geometric magic)"),
    (0x68, "Frog Pirate"),
    (0x69, "(unused monkey)"),
    (0x6A, "Kamek (flying/talking)"),
    (0x6B, "Hookbill? (1/2)"),
    (0x6C, "Hookbill? (2/2), background Kamek"),
    (0x6D, "2x2 Milde (1/2)"),
    (0x6E, "2x2 Milde (2/2)"),
    (0x6F, "4x4 Milde"),
    (0x70, "Prince Froggy battle"),
    (0x71, "Special Flower, tileset-specific"),
    (0xA9, "Sluggy the Unshaven?"),
    (0xAA, "Fishing Lakitu's rod"),
    (0xAB, "Intro Yoshis (1/2)"),
    (0xAC, "Intro Yoshis (2/2)"),
    (0xAD, "Baby Bowser (1/4)"),
    (0xAE, "Baby Bowser (2/4)"),
    (0xAF, "Baby Bowser (3/4)"),
    (0xB0, "Baby Bowser (4/4)"),
    )

headermusicIDs = (
    (0x0F, 0), (0x10, 0), (0x13, 0), (0x17, 1),
    (0x12, 0), (0x14, 1), (0x0F, 0), (0x14, 1),
    (0x14, 1), (0x17, 1), (0x11, 0), (0x1F, 0),
    (0x17, 1), (0x17, 0), (-1, 0), (-1, 1),
    )

music = (
    "Story intro",
    "SMA3 title",
    "Choose a game",
    "YI title (W1-W5)",
    "YI title (W6/postgame)",
    "Intro cutscene",
    "Intro level",
    "Level select (W1)",
    "Level select (W2)",
    "Level select (W3)",
    "Level select (W4)",
    "Level select (W5)",
    "Level select (W6)",
    "Level select (postgame)",
    "Level intro drums",
    "Land level",
    "Jungle level",
    "Sky level",
    "Cave level",
    "Castle level",
    "Kamek encounter",
    "Kamek enlarge",
    "x-4 boss",
    "Pre-boss",
    "x-8 boss",
    "x-8 victory",
    "Bowser battle",
    "Bowser battle victory",
    "Kamek exits/ending",
    "Credits",
    "Credits end",
    "Bonus/Super Star",
    "Goal/x-4 victory",
    "Course clear",
    "Goal minigame",
    "Death (Yoshi died)",
    "Death (Toadies)",
    "Game over",
    "100% cutscene, part 1",
    "100% cutscene, part 2",
    )

sma3char = (
    "à", "â", "ç", "è", "é", "ê", "î", "ô", #00-07
    "ù", "û", "/", "œ", None, None, None, None, #08-0F
    "ä", "ö", "ü", "ß", "Ä", "Ö", "Ü", None, #10-17
    "\{buttonRcrop0}", "\{buttonRcrop1}", "\{buttonA0}", "\{buttonA1}",
    "\{buttonB0}", "\{buttonB1}", "\{buttonLcrop0}", "\{buttonLcrop1}", #18-1F
    "\{select0}", "\{select1}", "\{select2}", "\{buttonL0}",
    "\{buttonL1}", "\{buttonL2}", ":", ";", #20-27
    "\{buttonR0}", "\{buttonR1}", "\{buttonR2}", "'",
    "\{upoutline}", "\{left}", "\{right}", "\{up}", #28-2F
    "\{down}", "\{start0}", "\{start1}", "\{start2}",
    "\{upcloud0}", "\{upcloud1}", "=", ",", #30-37
    "\{e_}", "\{i_}", "\{t_}", "\{r_}", "\{h_}", "\{f_}", "\{n_}", ".", #38-3F
    "À", "Â", "Ç", "È", "É", "Ê", "Î", "Ô", #40-47
    "Ú", "Ù", "Ï", "ï", "Ë", "Û", "Á", "Í", #48-4F
    "Ñ", "Ó", "Ì", "Ò", "ë", "ò", "á", "í", #50-57
    "ñ", "ó", "ì", "º", "ª", "¡", "¿", "ú", #58-5F
    None, None, None, None, None, None, None, None, #60-67
    None, None, None, None, None, None, None, None, #68-6F
    None, None, None, None, None, None, None, None, #70-77
    None, None, None, None, None, None, None, None, #78-7F
    None, None, None, None, None, None, None, None, #80-87
    None, None, None, None, None, None, None, None, #88-8F
    None, None, None, None, None, None, None, None, #90-97
    None, None, None, None, None, None, None, None, #98-9F
    "0", "1", "2", "3", "4", "5", "6", "7", #A0-A7
    "8", "9", "A", "B", "C", "D", "E", "F", #A8-AF
    "G", "H", "I", "J", "K", "L", "M", "N", #B0-B7
    "O", "P", "Q", "R", "S", "T", "U", "V", #B8-BF
    "W", "X", "Y", "Z", "『", "』", "?", "!", #C0-C7
    "、", "-", "\{dpad0}", "\{dpad1}", "\{···}", "。", "~", "\{, }", #C8-CF
    " ", "“", "”", "·", "►", "\{yoshi0}", "\{yoshi1}", "×", #D0-D7
    "a", "b", "c", "d", "e", "f", "g", "h", #D8-DF
    "i", "j", "k", "l", "m", "n", "o", "p", #E0-E7
    "q", "r", "s", "t", "u", "v", "w", "x", #E8-EF
    "y", "z", "◄", "\{. }",
    "\{?cloud0}", "\{?cloud1}", "\{star0}", "\{star1}", #F0-F7
    "\{!switch0}", "\{!switch1}", "\{downoutline}", "\{heartL0}",
    "\{heartL1}", "\{heartR0}", "\{heartR1}", None, #F8-FF
    )
