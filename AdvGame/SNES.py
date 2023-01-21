"""SNES General
Classes and functions for reading SNES ROMs."""

# standard library imports
import os

# import from other files
from . import AdvGame

class Open(AdvGame.Open):
    "Wrapper for Python's open() function, for reading SNES ROM images."
    def __init__(self, filepath, *args, **kwargs):
        super().__init__(filepath, *args, **kwargs)
        # account for the presence or absence of the SMC header
        self.SMCheader = hasSMCheader(filepath)

    def seek(self, ptr):
        """Seek to a 24-bit SNES ROM pointer. Only the SuperFX ROM mapping is
        supported."""
        bank = (ptr // 0x10000) & 0x7F
        addr16 = ptr & 0xFFFF

        if bank < 0x40 and addr16 >= 0x8000:  # LoROM region
            fileaddr = (bank - 1) * 0x8000 + addr16
        elif 0x40 <= bank < 0x60:  # HiROM region
            fileaddr = (bank & 0x3F) * 0x10000 + addr16
        else:
            raise ValueError("Address " + format(ptr, "06X") +
                             " is not a valid SNES SuperFX ROM pointer.")
        if self.SMCheader:
            fileaddr += 0x200
        self.fileobj.seek(fileaddr)

def hasSMCheader(filepath):
    sizemod = os.path.getsize(filepath) % 0x8000
    if sizemod == 0:
        return False
    if sizemod == 0x200:
        return True
    raise ValueError("Could not load file:\n" + filepath +
        "\nFile does not have an integer number of ROM banks. Could not detect "
        "whether it's a headered ROM.")
