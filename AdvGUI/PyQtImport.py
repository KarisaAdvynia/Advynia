"Handles the PyQt import, so that it can be easily updated if needed."

# Qt imports
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

# ensure only global-safe Qt classes/functions are imported with import *

import string
_afterQchars = string.digits + string.ascii_uppercase
def isQtglobal(name):
    """Check if a name is distinctly Qt enough to be safe for the global
    namespace. Used when importing.

    Qt classes/functions should start with Q/q respectively, followed by a
    capital letter. "Qt" is also a valid Qt name."""
    if ((name.startswith(("Q", "q")) and name[1] in _afterQchars)
            or name == "Qt"):
        return True

__all__ = [name for name in tuple(globals()) if isQtglobal(name)]
