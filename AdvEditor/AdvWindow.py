"""Advynia Editor
Major editor widgets/attributes that need global references."""

editor = None
sublevelscene = None
selection = None
sidebar = None
statusbar = None

from .Undo import SublevelUndoHistory
undohistory = SublevelUndoHistory()
