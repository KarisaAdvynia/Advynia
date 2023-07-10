"Functions for loading and evaluating the current sublevel."

# standard library imports
import copy, traceback
from collections import defaultdict

# import from other files
import AdvMetadata, AdvEditor
from AdvEditor import (AdvSettings, AdvWindow,
                       Adv3Attr, Adv3Save, Adv3Patch, Adv3Visual)
from AdvGame import GBA, SMA3
from AdvGUI.Dialogs import (QSimpleDialog, QDialogLoadValidation,
                            QDialogUnsavedWarning)
from AdvGUI import QtAdvFunc

dialogtext = {
    "screencount": (
        "The current sublevel uses {screens} screens. "
        "If a sublevel uses more than {maxscreens} screens, it "
        "will freeze the game on the loading screen!\n"
        "If this sublevel loads in-game, please report this-- "
        "there may be an error with how Advynia simulates object "
        "screen memory allocation."
        ),
    "spritecount": (
        "The current sublevel contains {sprites} sprites. "
        "If a sublevel contains more than {maxsprites} sprites, "
        "excess sprites may always respawn, or never spawn at all."
        ),
    "objF0F3check": (
        "The current sublevel contains {count} (decimal) of objects F0-F3. "
        "If more than {maxcount} are in a single sublevel, the excess objects "
        "will no longer move vertically."
        ),
    "itemmemory": (
        "Items in the same column detected on screen {screen} at x={x}.\n"
        "If one item is collected, any others may vanish!"
        ),
    }

def loadsublevel(sublevel):
    "Load a sublevel from an SMA3.Sublevel object."

    if AdvMetadata.printtime: timer = QtAdvFunc.timerstart()  # debug

    # if SublevelFromSNES, copy to base class to ensure correct methods
    if isinstance(sublevel, SMA3.SublevelFromSNES):
        sublevel = copy.deepcopy(sublevel)
        sublevel.__class__ = SMA3.Sublevel

    try:
        Adv3Attr.sublevel = sublevel
        if not sublevel.fromfile:
            Adv3Patch.loadsublevelpatchattr(sublevel)
        if not sublevel.stripeIDs:
            Adv3Visual.updatestripesfromsublevel()
        Adv3Visual.loadpalette(sublevel)
        Adv3Visual.loadgraphics(sublevel)

        AdvWindow.editor.reload({"All"})

    except Exception as err:
        text = ("Error loading sublevel.\n"
            "This sublevel appears to be corrupt. If you're getting this "
            "error from normal Advynia usage, please report this as a bug. "
            "Uploading your hack as a patch is recommended to help debug "
            "the error."
            "\n\n" + traceback.format_exc())
        traceback.print_exc()
        QSimpleDialog(AdvWindow.editor, text=text).exec()
        return

    # reset undo history, reinit with new sublevel as first state
    AdvWindow.undohistory.reset(sublevel)
    if not sublevel.fromfile:
        AdvWindow.undohistory.updatelastsave()

    # window title and status bar
    if sublevel.ID is not None:
        if sublevel.datablocks:
            AdvWindow.statusbar.setActionText(
                f"Loaded sublevel {sublevel.ID:02X}: main data from "
                f"{sublevel.datablocks['main'][0]:08X}, "
                f"sprite data from {sublevel.datablocks['sprite'][0]:08X}.")
    AdvWindow.editor.updatewindowtitle()
    AdvWindow.statusbar.updateByteText()

    if AdvMetadata.printtime: print("Total sublevel load:",
        QtAdvFunc.timerend(timer), "ms")  # debug

    if AdvSettings.warn_sublevel_intro and sublevel.ID == 0x38:
        QSimpleDialog(AdvWindow.editor, text="Sublevel 38 is used by the intro "
            "cutscene. The header is unused, and "
            "editing this may result in unexpected in-game behavior.",
            title="Warning", dontshow="warn_sublevel_intro").exec()
    if AdvSettings.warn_sublevel_raphael and sublevel.header[9] == 9:
        QSimpleDialog(AdvWindow.editor, text="This is the Raphael arena. "
            "Editing this may result in unexpected in-game behavior.",
            title="Warning", dontshow="warn_sublevel_raphael").exec()
    return True

def loadsublevelID(sublevelID):
    "Load a sublevel from the ROM."
    if not AdvEditor.ROM.exists(): return
    return loadsublevel(SMA3.Sublevel.importbyID(Adv3Attr.filepath, sublevelID))

def savesublevel_action():
    """Called from the main window's save sublevel action, and when confirming
    Save As. Handles other checks before saving."""

    # check for screen count
    if AdvSettings.warn_save_screencount:
        screencount = AdvWindow.sublevelscene.layer1.tilemap.screencount()
        if screencount > SMA3.Constants.maxlayer1screens:
            QSimpleDialog(
                AdvWindow.editor, title="Warning",
                dontshow="warn_save_screencount",
                text=dialogtext["screencount"].format(
                    screens=f"{screencount:02X}",
                    maxscreens=f"{SMA3.Constants.maxlayer1screens:02X}")
                ).exec()

    # check for sprite count
    if AdvSettings.warn_save_spritecount:
        spritecount = len(Adv3Attr.sublevel.sprites)
        if spritecount > SMA3.Constants.maxspritecount:
            QSimpleDialog(
                AdvWindow.editor, title="Warning",
                dontshow="warn_save_spritecount",
                text=dialogtext["spritecount"].format(
                    sprites=f"{spritecount:02X}",
                    maxsprites=f"{SMA3.Constants.maxspritecount:02X}")
                ).exec()

    # check for vertical shift object overflow
    if AdvSettings.warn_save_objF0F3:
        objF0F3check()

    # check for item memory errors
    if AdvSettings.warn_save_itemmemory:
        itemmemorycheck(dialog_on_pass=False)

    # save
    success = Adv3Save.savesubleveltoROM(Adv3Attr.sublevel, Adv3Attr.sublevel.ID)
    if success:
        AdvWindow.undohistory.updatelastsave()
    return success

def savecheck():
    if AdvSettings.warn_unsaved and not AdvWindow.undohistory.issaved():
        result = QDialogUnsavedWarning(AdvWindow.editor).exec()
        # 1=Save, 2=Don't Save, 0=Cancel
        if result == 0:
            return False
        if result == 1:
            if not savesublevel_action():
                return False
    return True

def cmpheader(newheader):
    """Given a header that may differ from the current sublevel's header,
    return a mapping containing the header values to update."""
    toupdate = {}
    for i, (new, old) in enumerate(zip(
            newheader, Adv3Attr.sublevel.header, strict=True)):
        if new != old:
            toupdate[i] = new
    return toupdate

def countitems():
    redcoins = 0
    flowers = 0
    for row in AdvWindow.sublevelscene.layer1.tilemap:
        for tileID in row:
            if tileID in (0x6001, 0xA400, 0x10E16) or tileID>>8 == 0xA3:
                # red coin tile or in poundable post
                redcoins += 1
    for spr in Adv3Attr.sublevel.sprites:
        match spr.ID:
            case 0x065 | 0x022 | 0x068 | 0x05B:
                # stationary sprite, flashing egg, flashing egg block,
                #  Bandit with red coin
                redcoins += 1
            case 0x0FA | 0x110 | 0x0B8:
                # flower, tileset-specific flower, ? cloud with flower
                flowers += 1
            case 0x12C:
                if not spr.x&1:
                    # Fly Guy with red coin, back and forth
                    redcoins += 1
            case 0x08D:
                if spr.parity() == 1:
                    # Fly Guy with red coin, timed
                    redcoins += 1
            case 0x067:
                if spr.parity() == 2:
                    # Chomp Rock ? cloud with flower
                    flowers += 1
            case 0x161:
                # reward for killing all enemies
                if spr.parity() == 0:
                    redcoins += 1
                elif spr.parity() == 2:
                    flowers += 1

    text = "Red coins: {redcoins}<br>Flowers: {flowers}"
    QSimpleDialog(AdvWindow.editor, title="Count Items", wordwrap=False,
        text=text.format(redcoins=redcoins, flowers=flowers)).exec()

def objF0F3check():
    count = 0
    for obj in Adv3Attr.sublevel.objects:
        if 0xF0 <= obj.ID <= 0xF3:
            count += 1
    if count > SMA3.Constants.maxobjF0F3:
        QSimpleDialog(
            AdvWindow.editor, title="Warning", dontshow="warn_save_objF0F3",
            text=dialogtext["objF0F3check"].format(
                count=count, maxcount=SMA3.Constants.maxobjF0F3)
            ).exec()

def itemmemorycheck(*, dialog_on_pass=True):
    # check for sprite conflicts, and track any item memory sprites
    sprcolstatus = defaultdict(int)
    for spr in Adv3Attr.sublevel.sprites:
        itemattr = SMA3.SpriteMetadata[spr].itemmemory
        if spr.ID == 0x0B6:  # ring of 8 coins
            # activate X positions of the 2 possible coin rings, low priority
            sprkey = (SMA3.coordstoscreen(spr.x, spr.y), spr.x)
            tocheck = set()
            for offsetX, offsetY in (
                (-2, -1), (-2, +1), (+2, -1), (+2, +1),  #\ centered
                (-1, -2), (-1, +2), (+1, -2), (+1, +2),  #/
                (-1, -1), (-1, +1), (+3, -1), (+3, +1),  #\ 1 tile right
                (-0, -2), (-0, +2), (+2, -2), (+2, +2),  #/
                ):
                x = spr.x + offsetX
                y = spr.y + offsetY
                if not (0 <= x < SMA3.Constants.maxtileX and
                        0 <= y < SMA3.Constants.maxtileY):
                    continue
                screen = SMA3.coordstoscreen(x, y)
                key = (screen, x)
                if key != sprkey:  # prevent sprite from conflicting with itself
                    tocheck.add((screen, x))
            for key in tocheck:
                if sprcolstatus[key] >= 2:
                    _itemmemoryerror(*key)
                    return
                sprcolstatus[key] = 1  # surrounding coins are low priority
            itemattr = 2  # 0B6 itself is high priority

        if itemattr:
            # sprite uses item memory
            screen = SMA3.coordstoscreen(spr.x, spr.y)
            if itemattr + sprcolstatus[(screen, spr.x)] >= 3:
                _itemmemoryerror(screen, spr.x)
                return
            sprcolstatus[(screen, spr.x)] = itemattr

    # check for tile conflicts
    tilemap = AdvWindow.sublevelscene.layer1.tilemap
    for screen in range(SMA3.Constants.maxscreen + 1):
        startX, startY = SMA3.screentocoords(screen)
        for x in range(startX, startX+0x10):
            if not _itemmemorycolcheck(
                    tilemap, x, startY, sprcolstatus[(screen, x)]):
                _itemmemoryerror(screen, x)
                return

    if dialog_on_pass:
        QSimpleDialog(
            AdvWindow.editor, title="Item Memory Check", wordwrap=False,
            text="No item memory errors detected.").exec()

def _itemmemorycolcheck(tilemap, x, startY, colstatus=0):
    for y in range(startY, startY+0x10):
        tileID = tilemap[y][x]
        if tileID in (0x6001, 0x10E16) or tileID>>8 == 0xA3:
            # red coin tile or in poundable post: high priority
            if colstatus:
                return False
            colstatus = 2
        elif tileID in (0x6000, 0x7400, 0xA400):
            # normal coins only conflict with high-priority items
            # green red coins aren't objects, so they're also low priority
            if colstatus >= 2:
                return False
            colstatus = 1
    return True

def _itemmemoryerror(screen, x):
    QSimpleDialog(
        AdvWindow.editor, title="Item Memory Check", wordwrap=False,
        text=dialogtext["itemmemory"].format(
            screen=f"{screen:02X}", x=f"{x:02X}")
        ).exec()

