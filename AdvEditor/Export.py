"Functions for importing/exporting data using external files."

# standard library imports
import itertools, os, traceback

# import from other files
import AdvMetadata, AdvEditor, AdvFile
from AdvEditor import (AdvSettings, AdvWindow,
                       Adv3Attr, Adv3Patch, Adv3Save, Adv3Sublevel, Adv3Visual)
from AdvEditor.Format import pluralize
from AdvGame import AdvGame, GBA, SMA3
from AdvGUI.Dialogs import (QFileDialog, QSimpleDialog, QDialogFileError,
    QDialogLoadValidation, QDialogImportPatch, QDialogSMA3ImportMultiple,
    QDialogImportGraphics)

# General

def loadwrapper(func, filepath, *args, _errordialog=True, **kwargs):
    "Wrapper for loading a file. Handles various error messages."

    try:
        return func(filepath, *args, **kwargs)
    except Exception as err:
        if not _errordialog: return
        # check for specific errors
        if isinstance(err, FileNotFoundError):
            text = "File not found."
        elif isinstance(err, PermissionError):
            text = "Insufficient permissions to access file."
        # check if error includes a string
        elif hasattr(err, "strerror"):
            text = err.strerror
        elif isinstance(err.args[0], str):
            text = err.args[0]
        # default to traceback
        else:
            text = traceback.format_exc()

        traceback.print_exc()
        QDialogFileError(AdvWindow.editor, filepath, text=text).exec()

def importwrapper(func, filepath, *args, **kwargs):
    """Wrapper for importing an Advynia-format file. In addition to checking
    for general load errors, this also checks if the file was created on a
    higher version."""

    data = loadwrapper(func, filepath, *args, **kwargs)
    if not data: return
    if data.version > AdvMetadata.version:
        if "_errordialog" in kwargs and kwargs["_errordialog"] is False:
            # dialogs are bypassed: don't offer to load anyway
            return
        if not QDialogLoadValidation(
            AdvWindow.editor, savedversion=data.version,
            filetypestr="file", override=True).exec():
            return
    return data

def importprocesswrapper(func, filepath, *args, **kwargs):
    try:
        return func(filepath, *args, **kwargs)
    except Exception:
        QDialogFileError(AdvWindow.editor, filepath, text="".join((
            "Error parsing " + os.path.splitext(filepath)[1] + " data. "
            "File may be corrupted, or may include data not implemented in "
            "this Advynia version."
            ))).exec()

# A3L: single import/export

def importA3L_action():
    """Load an A3L or SNES YI Level Tool file, then open the level entrance or
    message dialog if applicable."""

    filepath, _ = QFileDialog.getOpenFileName(
        AdvWindow.editor, caption="Import A3L File",
        directory=os.path.dirname(Adv3Attr.filepath),
        filter=";;".join((
            "All supported files (*.a3l *.ylt *.yet)",
            AdvFile.A3LFileData.longext,
            "SNES YI Level Tool file (*.ylt *.yet)",
            )))
    if not filepath:
        return
    ext = os.path.splitext(filepath)[1]

    warnSNES = False

    match ext:
        case ".a3l":
            a3l = importwrapper(AdvFile.A3LFileData.importfromfile, filepath)
            if not a3l: return
            importprocesswrapper(_processgeneralA3L, filepath, a3l)

        case ".ylt":
            sublevel = loadwrapper(AdvFile.YILevelTool.import_ylt, filepath)
            if not sublevel: return
            _importsublevel(sublevel, filepath, warnSNES=True)

        case ".yet":
            _importentrances(filepath)

        case _:
            QSimpleDialog(AdvWindow.editor, title="Error", wordwrap=False,
                          text="".join((
                "Importing from file extension ", ext, " is not supported."
                ))).exec()

def _processgeneralA3L(filepath, a3l):
    datatype = a3l.datatype()

    if datatype == "Sublevel":
        sublevel = a3l.tosublevel()
        # check for patches that aren't applied to current ROM
        newpatches = Adv3Patch.detectpatches_sublevel(sublevel)
        if newpatches:
            warn = False
            if AdvSettings.warn_patch_all:
                for patchkey in newpatches:
                    # warn if any specific patch warning is enabled
                    if getattr(AdvSettings, "warn_patch_" + patchkey):
                        print("warn_patch_" + patchkey)
                        warn = True
            if warn:
                # load warning dialog
                if not QDialogImportPatch(newpatches, sublevel).exec():
                    return
            else:
                Adv3Patch.applymultiplepatches(newpatches)
        _importsublevel(sublevel, filepath, warnSNES=(0x95 in a3l))
    elif datatype.startswith("Entrances"):
        _importentrances(filepath)
    elif datatype == "Text":
        _importmessages(filepath)
    else:
        raise ValueError

def _importsublevel(sublevel, filepath, warnSNES):
    "Load an imported sublevel. Called by importA3L_action."

    Adv3Sublevel.loadsublevel(sublevel)

    AdvWindow.statusbar.setActionText("".join((
        "Imported sublevel ", format(Adv3Attr.sublevel.ID, "02X"),
        " from ", filepath)))

    if warnSNES and AdvSettings.warn_import_SNES:
        text = (
            "This sublevel was created on the SNES version. The "
            "entrance camera bytes will need to be set manually, and "
            "level design may need to be tweaked for the GBA screen "
            "size.")
        if (Adv3Attr.sublevelstripes and
            os.path.splitext(filepath)[1].lower() == ".ylt"):
            text += (
                "<br><br>Additionally, the original sprite tileset is unknown. "
                "The .a3l format includes the sprite tileset, but .ylt "
                "does not.")
        QSimpleDialog(AdvWindow.editor, title="Warning",
                      dontshow="warn_import_SNES",
                      text=text).exec()

def _importentrances(filepath):
    "Import entrances for one or more levels. Called by importA3L_action."
    AdvWindow.entranceeditor.open()
    AdvWindow.entranceeditor.importentrances(filepath)

def _importmessages(filepath):
    "Import messages. Called by importA3L_action."
    AdvWindow.texteditor.open()
    AdvWindow.texteditor.importmessages(filepath)

def exportsublevel_action():
    """Called from the main window's export sublevel action. Prompts the user
    for an export filepath, then exports the current sublevel if valid."""

    a3l = sublevel_to_a3l()

    # generate default filepath
    defaultpath = os.path.join(
        os.path.dirname(Adv3Attr.filepath),
        a3l.defaultfilename(Adv3Attr.filename))

    # get filepath from user
    filepath, _ = QFileDialog.getSaveFileName(
        AdvWindow.editor, caption="Export Sublevel",
        filter=AdvFile.A3LFileData.longext, directory=defaultpath)

    # export data
    if filepath:
        a3l.exporttofile(filepath)
        AdvWindow.statusbar.setActionText("Exported sublevel to " + filepath)

def export_ylt():
    """Same as exportsublevel_action, but to the SNES YI Level Tool format.
    Does not export any GBA-specific data-- intended only for GBA-SNES
    porting."""

    # generate default filepath
    defaultpath = os.path.join(
        os.path.dirname(Adv3Attr.filepath),
        "level_" + format(Adv3Attr.sublevel.ID, "02X") + ".ylt")

    # get filepath from user
    filepath, _ = QFileDialog.getSaveFileName(
        AdvWindow.editor, caption="Export Sublevel to SNES",
        filter="SNES YI Level Tool File (*.ylt)", directory=defaultpath)

    # export data
    if filepath:
        AdvFile.YILevelTool.export_ylt(Adv3Attr.sublevel, filepath)
        AdvWindow.statusbar.setActionText(
            "Exported sublevel (GBA to SNES) to " + filepath)

def export_yet():
    """Export level entrances to the SNES YI level tool format. Due to the
    restrictions, only a maximum entrance count is supported."""

    # import entrances, capping midpoints to 4
    mainentr, midwayentr = SMA3.importlevelentrances(
        Adv3Attr.filepath, maxmidpoints=4,
        midwaylen = 6 if Adv3Attr.midway6byte else 4)

    # remove Secret level entrances
    for secretID in range(8, 0x48, 0xC):
        for seq in mainentr, midwayentr:
            extraID = secretID + 1
            seq[secretID], seq[extraID] = seq[extraID], []

    # test for maximum entrance count
    errorlines = []
    maincount = sum(bool(entr) for entr in mainentr)
    if maincount > 56:
        errorlines.append("".join((
            "This ROM contains ", str(maincount), " (decimal) main entrances. "
            "The .ylt format only supports 56.")))
    midwaycount = sum(len(level) for level in midwayentr)        
    if midwaycount > 122:
        errorlines.append("".join((
            "This ROM contains ", str(midwaycount), " (decimal) midway entrances. "
            "The .ylt format only supports 122.")))

    if errorlines:
        errorlines.insert(0, "After removing Secret level entrances:")
        QSimpleDialog(AdvWindow.editor, title="Error", wordwrap=True,
                      text="\n".join(errorlines)).exec()
        return

    # generate default filepath
    defaultpath = os.path.join(
        os.path.dirname(Adv3Attr.filepath), "entrances.yet")

    # get filepath from user
    filepath, _ = QFileDialog.getSaveFileName(
        AdvWindow.editor, caption="Export Entrances to SNES",
        filter="SNES YI Level Tool entrances (*.yet)", directory=defaultpath)

    # export data
    if filepath:
        AdvFile.YILevelTool.export_yet(mainentr, midwayentr, filepath)
        AdvWindow.statusbar.setActionText(
            "Exported entrances (GBA to SNES) to " + filepath)

def sublevel_to_a3l():
    "Convert the current sublevel to an export file."
    a3l = AdvFile.A3LFileData.fromsublevel(Adv3Attr.sublevel)
    if not Adv3Attr.sublevelstripes:
        # include stripe data even if the patch isn't applied
        a3l[5] = Adv3Visual.spritegraphics.stripeIDs
    return a3l

# A3L: import/export all

def importmultiple():
    "Import all A3L files in a directory, and save their data to the ROM."

    if not AdvEditor.ROM.exists(): return

    importdir = QFileDialog.getExistingDirectory(
        AdvWindow.editor, caption="Select Import Folder",
        directory=os.path.dirname(Adv3Attr.filepath))
    if not importdir: return

    # import .a3l files
    processedfiles = 0
    newsublevels = {}
    newentrances = {}
    allentrances = None
    newmessages = {}
    newpatches = set()
    duplicates = set()
    failedfiles = []
    for filename in os.listdir(importdir):
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".a3l":
            a3l = importwrapper(
                AdvFile.A3LFileData.importfromfile,
                os.path.join(importdir, filename), _errordialog=False)
            if not a3l:
                failedfiles.append(filename)
                continue
            try:
                match a3l.datatype():
                    case "Sublevel":
                        sublevel = a3l.tosublevel()
                        if sublevel.ID in newsublevels:
                            duplicates.add("Sublevel " +
                                           format(sublevel.ID, "02X"))
                        newsublevels[sublevel.ID] = sublevel
                        newpatches.update(Adv3Patch.detectpatches_sublevel(
                            sublevel))
                    case "Entrances: Single Level":
                        levelID, main, midways = a3l.toentrances()
                        if allentrances or levelID in newentrances:
                            duplicates.add("Level entrance " +
                                           format(levelID, "02X"))
                        newentrances[levelID] = (main, midways)
                        if Adv3Patch.detectpatches_midway([midways]):
                            newpatches.add("midway6byte")
                    case "Entrances: All Levels":
                        if allentrances:
                            duplicates.add("All level entrances")
                        elif newentrances:
                            duplicates.update(
                                "Level entrance " + format(levelID, "02X")
                                for levelID in newentrances)
                        allentrances = a3l.toentrances()
                        if Adv3Patch.detectpatches_midway(allentrances[1]):
                            newpatches.add("midway6byte")
                    case "Text":
                        messagestoadd = a3l.totextdata()
                        for key in messagestoadd:
                            if key in newmessages:
                                duplicates.add("Messages: " + key)
                        newmessages.update(messagestoadd)
                    case _:
                        raise ValueError
            except Exception:
                failedfiles.append(filename)
                continue

            processedfiles += 1

    # display dialog with list of data to be imported, and patches to be applied
    text = ["Processed ", pluralize(processedfiles, ".a3l file"), " from ",
            importdir, "\n\n"]
    if newsublevels or newentrances or allentrances or newmessages:
        text += ["About to import and save to ROM:\n"]
        if newsublevels:
            text += ["   Sublevels ",
                     AdvGame.collectionstr(newsublevels, "02X"),
                     "\n"]
        if allentrances:
            text.append("   All level entrances\n")
        elif newentrances:
            text += ["   Level entrances for levels ",
                     AdvGame.collectionstr(newentrances, "02X"),
                     "\n"]
        if newmessages:
            text += ["   Messages: ", ", ".join(newmessages), "\n"]

        if newpatches:
            text += ["\nPatches to apply:\n"]
            text += ("  " + AdvEditor.PatchData.patches[key][0] + "\n"
                     for key in sorted(newpatches))

        if duplicates:
            text += ["\nDuplicate data detected! "
                     "Only the last file name (in alphabetical order) will be "
                     "imported.\n   ",
                     ", ".join(sorted(duplicates)),
                     "\n"]
    else:
        text += ["No valid importable files detected in directory."]
        QSimpleDialog(AdvWindow.editor, title="Import Multiple A3Ls",
                      text="".join(text), wordwrap=True).exec()
        return

    if failedfiles:
        text += ["\nFailed to process:\n   ",
                 "\n   ".join(failedfiles),
                 "\nAttempting to import a file individually may provide a "
                 "more specific error."
                 "\n\n"]

    # open dialog, which handles saving data
    datatosave = (newsublevels, newentrances, allentrances, newmessages,
                  newpatches)
    if not QDialogSMA3ImportMultiple(
        AdvWindow.editor, "".join(text).strip(), datatosave).exec():
        return

    # if the current sublevel was replaced, reload it
    if Adv3Attr.sublevel.ID in newsublevels:
        Adv3Sublevel.loadsublevelID(Adv3Attr.sublevel.ID)

    AdvWindow.statusbar.setActionText("".join((
        "Imported ", pluralize(processedfiles, ".a3l file"), " from ",
        importdir)))

def exportallYIdata(sourcefilepath, outputdir, console="GBA"):
    "Export all A3L-compatible data from a GBA or SNES YI ROM."

    match console:
        case "GBA":
            Sublevel = SMA3.Sublevel
            sublevelrange = range(0xF6)
            texttypes = SMA3.textclasses
            textimportmethod = "importall"
        case "SNES":
            Sublevel = SMA3.SublevelFromSNES
            sublevelrange = range(0xDE)
            texttypes = dict(
                pair for pair in SMA3.textclasses.items()
                if pair[0] in ("Level name", "Standard message", "Ending"))
            textimportmethod = "importallfromSNES"
        case _:
            raise ValueError("Input 'console' must be either 'GBA' or 'SNES'.")

    if not os.path.exists(outputdir):
        os.mkdir(outputdir)

    # export sublevels
    for sublevelID in sublevelrange:
        try:
            sublevel = Sublevel.importbyID(sourcefilepath, sublevelID)
            if console == "GBA":
                Adv3Patch.loadsublevelpatchattr(sublevel)
            a3l = AdvFile.A3LFileData.fromsublevel(sublevel)
            exportpath = os.path.join(outputdir,
                a3l.defaultfilename(sourcefilepath))
            a3l.exporttofile(exportpath)
        except ValueError:
            pass

    # export entrances
    try:
        if console == "GBA":
            entrances = SMA3.importlevelentrances(
                sourcefilepath, maxmidpoints=Adv3Attr.maxmidpoints,
                midwaylen = 6 if Adv3Attr.midway6byte else 4)
        elif console == "SNES":
            entrances = (SMA3.MainEntrances.importfromSNES(sourcefilepath),
                         SMA3.MidwayEntrances.importfromSNES(sourcefilepath))
        a3l = AdvFile.A3LFileData.fromentrances(*entrances)
        if console == "SNES": a3l[0x95] = b"\1"
        a3l.exporttofile(os.path.join(outputdir,
            a3l.defaultfilename(sourcefilepath)))
    except ValueError:
        pass

    # export text
    try:
        exportmessages = {}
        for texttype, cls in texttypes.items():
            exportmessages[texttype] = getattr(cls, textimportmethod)(
                sourcefilepath)
        a3l = AdvFile.A3LFileData.fromtextdata(exportmessages)
        if console == "SNES": a3l[0x95] = b"\1"
        a3l.exporttofile(os.path.join(outputdir,
            a3l.defaultfilename(sourcefilepath)))
    except ValueError:
        pass

def exportall_action():
    _exportallwarning()

    outputdir = QFileDialog.getExistingDirectory(
        AdvWindow.editor, caption="Select Export Folder",
        directory=os.path.dirname(Adv3Attr.filepath))
    if not outputdir: return

    exportallYIdata(Adv3Attr.filepath, outputdir, console="GBA")
    AdvWindow.statusbar.setActionText(
        "Exported sublevels, entrances, and messages to " + outputdir)

def exportSNESdata_action():
    _exportallwarning()

    filepath, _ = QFileDialog.getOpenFileName(
        AdvWindow.editor, caption="Open SNES ROM",
        directory=os.path.dirname(Adv3Attr.filepath),
        filter="SNES ROM Image (*.sfc *.smc)")
    if not filepath: return

    outputdir = QFileDialog.getExistingDirectory(
        AdvWindow.editor, caption="Select Export Folder",
        directory=os.path.dirname(filepath))
    if not outputdir: return

    exportallYIdata(filepath, outputdir, console="SNES")
    AdvWindow.statusbar.setActionText(
        "Extracted sublevels, entrances, and messages from " +
        os.path.basename(filepath))

def _exportallwarning():
    "Shared warning for exporting all data to A3Ls, from GBA or SNES."
    if AdvSettings.warn_export_all:
        QSimpleDialog(AdvWindow.editor, title="Export All Data", wordwrap=True,
            dontshow="warn_export_all",
            text="This will create a large number of files, including one per "
                 "sublevel. An empty folder is recommended.").exec()

# Graphics import/export

_graphicsdirs = {
    "graphics": AdvSettings.dir_graphicssuffix,
    "tilemaps": AdvSettings.dir_tilemapssuffix}
_ptrdata = {
    "graphics": SMA3.Pointers.LZ77_graphics,
    "tilemaps": SMA3.Pointers.LZ77_tilemaps}
_ptrdata_Huffman = {
    "graphics": SMA3.Pointers.Huffman_graphics,
    "tilemaps": SMA3.Pointers.Huffman_tilemaps}

def exportgraphics(filepath, exportdir=None):
    """Export all currently known SMA3 graphics and compressed tilemaps.

    Also generate two directories in exportdir, {basename}{dir_graphicssuffix}
    and {basename}{dir_tilemapssuffix}, to hold the exports if they don't
    already exist."""

    # generate a filename-safe prefix for the export directories
    sourcefileroot = os.path.splitext(os.path.basename(filepath))[0]

    if not exportdir:
        exportdir = os.path.dirname(filepath)
    outputroot = os.path.join(exportdir, sourcefileroot)

    folders = {}
    for key, suffix in _graphicsdirs.items():
        folders[key] = outputroot + suffix
        if not os.path.exists(folders[key]):
            os.mkdir(folders[key])

    with GBA.Open(filepath, "rb") as f:
        # compressed graphics
        for exporttype, ptrrefs in _ptrdata.items():
            for destfile, ptrref in ptrrefs.items():
                f.readseek(ptrref)
                data = f.read_decompress()
                AdvGame.exportdatatofile(
                    os.path.join(folders[exporttype], destfile), data)

        # uncompressed graphics
        for destfile, ptr, length in SMA3.Pointers.uncompressed_graphics:
            f.seek(ptr)
            data = f.read(length)
            AdvGame.exportdatatofile(
                os.path.join(folders["graphics"], destfile), data)

        # 1bpp custom format graphics
        for key, textattr in SMA3.Pointers.textgraphics.items():
            SMA3.exporttextgraphics(
                f, os.path.join(folders["graphics"], textattr.exportfile), key)
        SMA3.exportmessageimages(
            f, os.path.join(folders["graphics"],
                            SMA3.Pointers.messageimages_export))

    AdvWindow.statusbar.setActionText(
        "Exported all graphics and compressed tilemaps.")

def exportgraphics_action():
    try:
        exportgraphics(Adv3Attr.filepath)
    except Exception:
        text = ("Exporting was aborted due to an error.\n\n" +
                traceback.format_exc())
        traceback.print_exc()
        QSimpleDialog(AdvWindow.editor, title="Error",
                      text=text).exec()

def importgraphics(filepath):
    """Scan the ROM's folder for previously exported subfolders with compressed
    data, and if any files were modified, import them."""

    pathstart = os.path.splitext(filepath)[0]
    exporttypes = []
    if AdvSettings.import_includegraphics: exporttypes.append("graphics")
    if AdvSettings.import_includetilemaps: exporttypes.append("tilemaps")

    toinsert = []
    tooverwrite = []
    toerase = []
    dirwarnings = []
    sizewarnings = []
    sizeerrors = []

    if not Adv3Attr.huffmantolz77:
        # test if Huffman files need conversion
        if _testhuffman(GBA.Open(filepath, "rb"), pathstart, exporttypes):
            if not Adv3Patch.applypatch("huffmantolz77"):
                return False

    with GBA.Open(filepath, "rb") as f:
        # process compressed data
        for exporttype in exporttypes:
            exportdir = pathstart + _graphicsdirs[exporttype]
            if not os.path.exists(exportdir):
                dirwarnings.append((exporttype, exportdir))
                continue

            for filename, ptrref in _ptrdata[exporttype].items():
                exportpath = os.path.join(exportdir, filename)
                if os.path.exists(exportpath):
                    newdata = open(exportpath, "rb").read()
                    olddataptr = f.readptr(ptrref)
                    olddata = f.read_decompress(olddataptr)
                    if newdata != olddata:
                        # update data only if different
                        compresseddata = GBA.compressLZ77(newdata)
                        toinsert.append((compresseddata, ptrref))
                        toerase.append((olddataptr, f.tell() - olddataptr))

                        newlength = len(newdata)
                        oldlength = len(olddata)
                        if newlength != oldlength:
                            sizewarnings.append((filename, newlength, oldlength))

        exportdir = pathstart + _graphicsdirs["graphics"]
        if "graphics" in exporttypes and os.path.exists(exportdir):
            # process uncompressed graphics
            for filename, ptr, length in SMA3.Pointers.uncompressed_graphics:
                exportpath = os.path.join(exportdir, filename)
                if os.path.exists(exportpath):
                    newdata = open(exportpath, "rb").read()
                    if len(newdata) != length:
                        sizeerrors.append((filename, len(newdata), length))
                    else:
                        tooverwrite.append((newdata, ptr))

            # process text character graphics
            for key, textattr in SMA3.Pointers.textgraphics.items():
                exportpath = os.path.join(exportdir, textattr.exportfile)
                if os.path.exists(exportpath):
                    tooverwrite.append(
                        (SMA3.importtextgraphics(exportpath, key),
                         textattr.graphicsptr))

            # process text image graphics
            exportpath = os.path.join(exportdir,
                                      SMA3.Pointers.messageimages_export)
            if os.path.exists(exportpath):
                ptr = f.readptr(SMA3.Pointers.messageimages)
                tooverwrite.append(
                    (SMA3.importmessageimages(exportpath), ptr))

    nodata = False if (toinsert or tooverwrite) else True

    if dirwarnings or sizewarnings or sizeerrors or nodata:
        allowoverride = True
        if nodata or sizeerrors:
            allowoverride = False
        if not QDialogImportGraphics(AdvWindow.editor, allowoverride,
                dirwarnings, exporttypes, sizewarnings, sizeerrors, nodata
                                     ).exec():
            return False

    with GBA.Open(filepath, "r+b") as f:
        # erase old compressed data
        for ptr, length in toerase:
##            print("Erasing:", hex(length), "bytes from", format(ptr, "08X"))
            f.seek(ptr)
            f.write(bytes(length))

        # overwrite uncompressed/text graphics
        for newdata, ptr in tooverwrite:
            f.seek(ptr)
            f.write(newdata)

    _insertcompresseddata(toinsert)

    for seq in dirwarnings:
        exporttypes.remove(seq[0])
    AdvWindow.statusbar.setActionText("".join((
        "Inserted ",
        " and ".join(exporttypes),
        " from export folders.")))

    return True

def _insertcompresseddata(toinsert):
    """Insert compressed graphics to freespace, prioritizing the vanilla
    compressed region if possible."""

    # loop across data to insert:
    #  find freespace, write new data, update pointers in ptrref
    for compresseddata, ptrref in toinsert:
        newptr = None
        if AdvSettings.import_graphicstovanillaregion:
            # try to save in the corresponding vanilla region first, if enabled
            try:
                for start, end in SMA3.Pointers.vanillacompressedregions:
                    if start <= ptrref.vdest < end:
##                        print("Trying region", format(start, "08X"), format(end, "08X"))
                        newptr = Adv3Save.savedatatoROM(
                            compresseddata, ptrref, start, end)
                        break
            except Adv3Save.ROMFreespaceError:
                pass
        if newptr is None:
            # save to freespace
            newptr = Adv3Save.savedatatoROM(compresseddata, ptrref)
##        print("Saved", hex(len(compresseddata)), "bytes to", format(newptr, "08X"))

def _testhuffman(f, pathstart, exporttypes):
    """Test if the Huffman to LZ77 patch needs to be applied, before inserting
    compressed data."""

    for exporttype in exporttypes:
        exportdir = pathstart + _graphicsdirs[exporttype]
        for filename, ptrref in _ptrdata_Huffman[exporttype].items():
            exportpath = os.path.join(exportdir, filename)
            if os.path.exists(exportpath):
                newdata = open(exportpath, "rb").read()
                olddataptr = f.readptr(ptrref)
                olddata = f.read_decompress(olddataptr)
                if newdata != olddata:
                    return True
    return False

def importgraphics_action():
    Adv3Save.savewrapper(importgraphics, Adv3Attr.filepath)
    AdvWindow.editor.reload({"All Graphics"})
