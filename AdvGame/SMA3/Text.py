"""SMA3 Text
Classes for SMA3 text strings and commands."""

# standard library imports
import io, string

# import from other files
from AdvGame import AdvGame, GBA, SNES
from AdvGame.SMA3 import Constants, Pointers, PointersSNES

class TextCommand:
    "A single command from SMA3 text data."
    def __init__(self, charID=0xFF, params=None, repcount=1):
        self.charID = charID
        if params is None:
            self.params = bytearray()
        else:
            self.params = params
        self.repcount = repcount

    def __eq__(self, other):
        if type(other) is not type(self):
            return False
        for attr in ("charID", "params", "repcount"):
            if not getattr(self, attr) == getattr(other, attr):
                return False
        return True

    def __str__(self):
        output = ["@{", ",".join(format(i, "02X") for i in self.params)]
        if self.repcount > 1:
            output += "#", format(self.repcount, "X")
        output.append("}")
        return "".join(output)

    def __bytes__(self):
        output = bytearray()
        output.append(self.charID)
        output += self.params
        return bytes(output) * self.repcount

class Text(list):
    "Representation of an SMA3 text string, including characters and commands."
    def __init__(self, iterable=None):
        if iterable is not None:
            try:
                list.__init__(self, iterable)
            except TypeError:
                # allow init to a single char ID or command
                list.__init__(self, (iterable,))
        self.datablock = None
        self.valid = True

    # class attributes, can be redefined in subclasses

    maxchar = 0xFE   # maximum character byte that's not a command
    endofdata = b"\xFF\xFF"  # end of data byte marker
    width = 0x80     # width of displayed message in pixels
    height = 0x40    # height of displayed message in pixels

    # converting to string/bytes

    def __str__(self):
        output = []
        # convert each char/command to text
        for char in self:
            if isinstance(char, TextCommand):
                # if string is not empty, add newline before certain commands
                if output and self.isnewline(char):
                    output.append("\n")
                output.append(str(char))
            elif Constants.sma3char[char] is None:
                output += "\\{", format(char, "02X"), "}"
            else:
                output.append(Constants.sma3char[char])
        return "".join(output)

    def __repr__(self):
        # overwrite default list with printable string
        return "".join((
            "<SMA3.", type(self).__name__, ": '", self.shortstr(), "'>"))

    def shortstr(self):
        """Convert to a 1-line abbreviated string, suitable for including in
        displayed lists. Unlike __str__, this is not lossless."""
        output = []
        for char in self:
            if isinstance(char, TextCommand):
                if self.isnewline(char):
                    if output:
                        output.append(" ")
                elif not self._shortignore(char):
                    output.append("@")
            elif Constants.sma3char[char] is None:
                output.append("\\")
            elif len(Constants.sma3char[char]) > 1:
                output.append(Constants.sma3char[char][2])
            else:
                output.append(Constants.sma3char[char])
        return "".join(output)

    def isnewline(self, command):
        "Can be overridden to determine which commands act as a newline."
        return False

    def _shortignore(self, command):
        """Can be overridden to determine which commands should be ignored, not
        displayed '@', in self.shortstr."""
        return False

    def __bytes__(self):
        output = bytearray()
        # convert each char/command to bytes
        for i in self:
            if isinstance(i, TextCommand):
                output += bytes(i)
            else:
                output.append(i)

        output += self.endofdata
        return bytes(output)

    # properties

    @classmethod
    def ptrref(cls):
        return Pointers.text[cls.texttype]

    def charcount(self):
        "Return the number of non-command characters in the message."
        output = 0
        for char in self:
            if isinstance(char, int):
                output += 1
        return output

    def linecount(self):
        "Return the number of lines (defined by subclasses) in the message."
        output = 1
        for char in self[1:]:
            if isinstance(char, TextCommand) and self.isnewline(char):
                output += 1
        return output

    def bytecount(self):
        "Return the number of bytes in the message."
        return len(bytes(self))

    def size(self):
        """Return the pixel width/height of the message. Width and height
        can be overridden by subclasses."""
        return self.width, self.height

    # import methods

    @classmethod
    def importtext(cls, f, addr=0):
        """Import text data from a file object.
        Can only be called from subclasses that define self.charsfrombytes,
        a generator that yields text characters/commands."""
        output = cls()
        try:
            f.seek(addr)
        except (ValueError, TypeError):  # invalid pointer
            return output

        output.extend(output.charsfrombytes(f))
        if isinstance(f, AdvGame.Open):
            # if importing from a file, record the data block
            output.datablock = (addr, f.tell() - addr)
        return output

    @classmethod
    def importall(cls, filepath):
        """Import all text of this class's type from a ROM file.
        Returns a SharedPointerList.
        Can only be called from subclasses that define cls.charsfrombytes."""
        ptrref = cls.ptrref()
        ptrtable = GBA.PointerTable.importtable(
            filepath, ptrref, ptrref.vdest, cls.vlen, maxlen=0x1000)
        with GBA.Open(filepath, "rb") as fileobj:
            return AdvGame.SharedPointerList(
                ptrtable, lambda ptr : cls.importtext(fileobj, ptr))

    @classmethod
    def importallfromSNES(cls, filepath):
        """Import all text of this class's type from an SNES YI ROM file.
        In addition to the cls.importall restrictions, this only works with text
        types where SNES/GBA use the same format."""
        with SNES.Open(filepath, "rb") as f:
            ptr = PointersSNES.text[cls.texttype]
            bankhigh = ptr & 0xFF0000
            f.seek(ptr)
            ptrtable = []
            for levelID in range(cls.vlen):
                rawptr = f.readint(2)
                if rawptr:
                    ptrtable.append(bankhigh | rawptr)
                else:
                    ptrtable.append(None)
            return AdvGame.SharedPointerList(
                ptrtable, lambda ptr : cls.importtext(f, ptr))

    @classmethod
    def importallfrombytes(cls, bytedata, offsets):
        buffer = io.BytesIO(bytedata)
        return AdvGame.SharedPointerList(
            offsets, lambda offset : cls.importtext(buffer, offset))

    def updatefromstr(self, textstr, includenewlines=False):
        """Update the current text data using the contents of a string,
        as produced by __str__.
        includenewlines: parse newlines as commands. Only valid in subclasses
        that define self._commandfromnewline."""
        self.clear()
        self.datablock = None
        self.valid = True
        if includenewlines:
            # start of first line commands, if any
            self += self._newlineseq(0)
            linenum = 1
        with io.StringIO(textstr) as buffer:
            while char := buffer.read(1):
                currentpos = buffer.tell()
                try:
                    if char == "\n" and includenewlines:
                        # new line commands
                        self += self._newlineseq(linenum)
                        linenum += 1
                    elif char in string.whitespace and char != " ":
                        # don't process newlines/tabs
                        continue
                    elif char == "@":
                        # command with hex values
                        command = self._commandfromstr(buffer)
                        if not self.validatecommand(command):
                            raise ValueError
                        self.append(command)
                    elif char == "\\":
                        # special char keyword or hex code
                        charID = self._specialcharfromstr(buffer)
                        if charID > self.maxchar:
                            raise ValueError
                        self.append(charID)
                    else:
                        self.append(Constants.sma3char_lookup[char])
                except (KeyError, ValueError) as err:
                    # replace invalid character with space, and revert position
                    buffer.seek(currentpos)
                    self.append(0xD0)
                    self.valid = False
                    continue
        if includenewlines:
            # end of final line commands, if any
            self += self._newlineseq(linenum, finalline=True)
        return self

    @staticmethod
    def _specialcharfromstr(buffer):
        """Process a special character string in the format \{text}, after
        detecting the initial '\'."""
        nextchar = buffer.read(1)
        if nextchar != "{":
            raise ValueError

        textstr = "\{"
        for _ in range(Constants.sma3char_maxlen - 2):
            textstr += buffer.read(1)
            try:
                # return character, if a match found
                return Constants.sma3char_lookup[textstr]
            except KeyError:
                # if length 5, check for a hex code, else pass
                if len(textstr) == 5 and textstr[4] == "}":
                    return int(textstr[2:4], base=16)
        else:
            raise ValueError

    @staticmethod
    def _commandfromstr(buffer):
        """Process a command in the format @{hex[,hex][#rep]}, after detecting
        the initial '@'."""
        nextchar = buffer.read(1)
        if nextchar != "{":
            raise ValueError

        command = TextCommand()
        while True:
            # process hex bytes
            command.params.append(int(buffer.read(2), base=16))
            nextchar = buffer.read(1)
            if nextchar != ",":
                break
        if nextchar == "#":
            repstr = ""
            while repchar := buffer.read(1):
                if repchar not in string.hexdigits:
                    break
                repstr += repchar
            command.repcount = int(repstr, base=16)
            nextchar = repchar
        if nextchar != "}":
            raise ValueError
        return command

    def validatecommand(self, command):
        """Can be overridden to define whether an arbitrary TextCommand is valid
        for this message type."""
        # default: early end of data command would lead to data leaks
        if bytes(command).startswith(self.endofdata):
            return False
        return True

class LevelName(Text):
    "Subclass to handle level name text."

    texttype = "Level name"
    vlen = 0x48
    maxchar = 0xFC
    endofdata = b"\xFD"

    def charsfrombytes(self, f):
        while True:
            charID = f.read(1)[0]
            match charID:
                case 0xFE:   # next 2 bytes are part of command
                    yield TextCommand(charID, f.read(2))
                case 0xFF:
                    yield TextCommand(charID, f.read(1))
                case 0xFD:   # end of data
                    return
                case _:
                    yield charID

    def isnewline(self, command):
        return command.charID == 0xFE

    def validatecommand(self, command):
        # validating and charID both depend on length
        # so charID is updated here, to avoid hardcoding in Text.updatefromstr
        match len(command.params):
            case 2:
                command.charID = 0xFE
                return True
            case 1:
                command.charID == 0xFF
                return True
            case _:
                return False

    @classmethod
    def importallfromSNES(cls, filepath):
        # swap Extra/Secret level names
        levelnames = super().importallfromSNES(filepath)
        from AdvGame.SMA3 import Level
        Level.swapExtraSecret(levelnames)
        return levelnames

class StandardMessage(Text):
    "Subclass to handle standard message text."

    texttype = "Standard message"
    vlen = 0x12C

    @property
    def height(self):
        h = 0x40
        for char in self:
            if isinstance(char, TextCommand):
                commandID = char.params[0]
                if 0x11 <= commandID <= 0x14:
                    h += (commandID & 0xF) * char.repcount
        return h

    def charsfrombytes(self, f):
        while True:
            charID = f.read(1)[0]
            if charID == 0xFF:
                params = f.read(1)  # command ID
                if params[0] == 0xFF:   # end of data
                    return
                elif params[0] == 0x60:
                    # command 60 includes 7 additional bytes
                    params += f.read(7)
                    yield TextCommand(charID, params)
                elif self and isinstance(self[-1], TextCommand) and\
                        self[-1].params[0] == params[0]:
                    # previous character exists and is the same command
                    self[-1].repcount += 1
                else:
                    yield TextCommand(charID, params)
            else:
                yield charID

    def isnewline(self, command):
        return command.params[0] in (0x05, 0x06, 0x07, 0x08, 0x0E)

    def _shortignore(self, command):
        return command.params[0] in (0x0A, 0x0F, 0x11, 0x12, 0x13, 0x14)

    def validatecommand(self, command):
        match command.params[0]:
            case 0xFF:  # end of data command
                return False
            case 0x60:  # large image
                return len(command.params) == 8
            case _:
                return len(command.params) == 1

    # Simplified string methods

    def simplifiedstr(self):
        """Variant of __str__ that excludes common newline/pause=related
        commands, if they occur in the vanilla command pattern."""
        if not self.issimplified():
            # fall back to normal __str__
            return str(self)
        output = []
        # convert each char/command to text
        for char in self:
            if isinstance(char, TextCommand):
                # if string is not empty, add newline before certain commands
                if self.isnewline(char) and char.params[0] != 0x05:
                    output.append("\n")
                    continue
                elif char.params[0] in (0x05, 0x0A, 0x0F, 0x12):
                    continue
                else:
                    output.append(str(char))
            elif Constants.sma3char[char] is None:
                output += "\\{", format(char, "02X"), "}"
            else:
                output.append(Constants.sma3char[char])
        return "".join(output)

    def issimplified(self):
        "Check if a message uses the vanilla command format."
        # check for end command (sequence), and exclude it from in iterable
        if not self or self[-1] != TextCommand(params=b"\x0F"):
            # simplified-compatible messages must end with command 0F
            return False
        linecount = self.linecount()
        if linecount > 4:
            if self[-2] != TextCommand(params=b"\x12", repcount=8):
                # if multi-page, there's a group of command 12s before 0F
                return False
            if linecount % 4 == 1:
                # if exactly 1 line more than a page, there's also 0A
                if self[-3] != TextCommand(params=b"\x0A"):
                    return False
                end = -3
            else:
                end = -2
        else:
            end = -1
        chariter = iter(self[:end])
        matchlineiter = self._simplifiedlinegen()

        try:
            if not self._checkcommandseq(next(chariter), chariter, matchlineiter):
                return False
            for char in chariter:
                if isinstance(char, TextCommand) and (
                        self.isnewline(char) or self._shortignore(char)):
                    # start checking for new command sequence
                    if not self._checkcommandseq(char, chariter, matchlineiter):
                        return False
        except StopIteration:
            pass
        return True

    _simplifiedlines = [
        (0x05,), (0x06,), (0x07,), (0x08,), (0x0E,), (0x0A, 0x12, 0x0E),
        (0x12, 0x0E), (0x12, 0x0E), (0x12, 0x0E)]
    _command12_8 = TextCommand(params=b"\x12", repcount=8)

    def _simplifiedlinegen(self):
        yield from self._simplifiedlines
        while True:
            yield from self._simplifiedlines[-4:]

    def _checkcommandseq(self, firstchar, chariter, matchlineiter):
        matchline = next(matchlineiter)
        char = firstchar
        for i, commandID in enumerate(matchline):
            if i > 0:
                # first char was already retrieved from iterator
                char = next(chariter)
            if (not isinstance(char, TextCommand) or
                    char.params[0] != commandID):
                return False
            if commandID == 0x12 and char.repcount != 8:
                # simplified messages have command 12 in groups of 8
                return False
        return True

    def _newlineseq(self, linenum, finalline=False):
        """Return text commands corresponding to a newline, in a simplified
        string."""
        output = []
        if linenum > 8:
            # loop every 4th line
            linenum = 5 + (linenum - 1) % 4
        commands_to_add = list(self._simplifiedlines[linenum])
        if finalline:
            commands_to_add[-1] = 0x0F
        for commandID in commands_to_add:
            repcount = 1
            if commandID == 0x12:
                repcount = 8
            output.append(
                TextCommand(params=bytes([commandID]), repcount=repcount))
        return output

class FileSelectText(Text):
    "Subclass to handle file select text."

    texttype = "File select"
    vlen = 0xC
    width = 0x98
    height = 0x10

    def charsfrombytes(self, f):
        while True:
            charID = f.read(1)[0]
            if charID == 0xFF:
                params = f.read(2)
                if params[0] == 0xFF:   # end of data
                    return
                yield TextCommand(charID, params)
            else:
                yield charID

    def _shortignore(self, _):
        return True

    def validatecommand(self, command):
        return len(command.params) == 2 and command.params[0] != 0xFF

class StoryText(Text):
    "Base class for story intro/credits text."

    width = 0xF0

    def charsfrombytes(self, f):
        while True:
            charID = f.read(1)[0]
            if charID == 0xFF:
                params = f.read(1)
                if params[0] == 0xFF:   # end of data
                    return
                elif (self.texttype != "Story intro" or
                      params[0] not in (0x04, 0x31)):
                    params += f.read(1)
                yield TextCommand(charID, params)
            else:
                yield charID

    def isnewline(self, command):
        return command.params[0] == 0x02

    def _shortignore(self, command):
        return 2 <= command.params[0] <= 3

class StoryIntroText(StoryText):
    "Subclass to handle story intro text."

    texttype = "Story intro"
    vlen = 0x2A
    height = 0x40

    def validatecommand(self, command):
        if command.params[0] in (0x04, 0x31):
            return len(command.params) == 1
        else:
            return len(command.params) == 2 and command.params[0] != 0xFF

class CreditsText(StoryText):
    "Subclass to handle credits text."

    texttype = "Credits"
    vlen = 0x24
    height = 0x20

    def validatecommand(self, command):
        return len(command.params) == 2 and command.params[0] != 0xFF

    @classmethod
    def importall(cls, filepath):
        "Subclassed to include hardcoded pointers for last 3 credits messages."
        ptrref = cls.ptrref()
        ptrtable = GBA.PointerTable.importtable(
            filepath, ptrref, ptrref.vdest, cls.vlen, maxlen=0x1000)
        with GBA.Open(filepath, "rb") as fileobj:
            output = AdvGame.SharedPointerList(
                ptrtable, lambda ptr : cls.importtext(fileobj, ptr))
            for ptr in Pointers.text["Credits final"]:
                # hardcoded pointers
                newtext = cls.importtext(fileobj, fileobj.readptr(ptr))
                output.append(newtext)
        return output

class EndingText(Text):
    "Subclass to handle the unique post-Bowser ending message."

    texttype = "Ending"
    width = 0xC8

    @property
    def height(self):
        h = 0x10
        for char in self:
            if isinstance(char, TextCommand) and char.params[0] in (0x09, 0x0A):
                h += 0x10
        return min(h, 0x100)

    def charsfrombytes(self, f):
        while True:
            charID = f.read(1)[0]
            if charID == 0xFF:
                params = f.read(1)
                if params[0] == 0xFF:  # end of data
                    return
                yield TextCommand(charID, params)
            else:
                yield charID

    def isnewline(self, command):
        return command.params[0] in (0x09, 0x0A)

    @classmethod
    def importall(cls, filepath):
        """Return the message as a 1-element list, for consistent processing
        with other text types."""
        with GBA.Open(filepath, "rb") as fileobj:
            ptr = fileobj.readptr(Pointers.text[cls.texttype])
            return [cls.importtext(fileobj, ptr)]

    @classmethod
    def importallfromSNES(cls, filepath):
        with SNES.Open(filepath, "rb") as f:
            ptrref = PointersSNES.text[cls.texttype]
            f.seek(ptrref)
            ptr = ptrref & 0xFF0000 | f.readint(2)
            return [cls.importtext(f, ptr)]

    def validatecommand(self, command):
        return len(command.params) == 1 and command.params[0] != 0xFF

textclasses = {
    "Level name": LevelName,
    "Standard message": StandardMessage,
    "File select": FileSelectText,
    "Story intro": StoryIntroText,
    "Credits": CreditsText,
    "Ending": EndingText,
    }

def importalltext(filepath):
    """Wrapper function to import all messages for all text types into a
    single dict."""
    messages = {}
    for key, cls in textclasses.items():
        messages[key] = cls.importall(filepath)
    return messages

if __name__ == "__main__":
##    msgs = StandardMessage.importallfromSNES("../../../../2/YI hacks/yi.sfc")
    msgs = LevelName.importallfromSNES("../../../../2/YI hacks/NEW!SMW2YI 2012-12-31.smc")
    for ID, msg in enumerate(msgs):
        print(format(ID, "02X"), repr(msg))
