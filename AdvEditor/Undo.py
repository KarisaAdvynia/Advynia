# standard library imports
import copy

# import from other files
from AdvEditor import AdvSettings, AdvWindow, Adv3Attr, Adv3Sublevel

class UndoHistory(list):
    "Base class for tracking undo history."
    def __init__(self, initialstate=None):
        super().__init__()
        self.index = None
        self.chain = 0
        self.mergeID = None
        self.lastsave = None
        if initialstate is not None:
            self.reset(initialstate)

    @property
    def state(self):
        if self.index is not None:
            return self[self.index]
    @property
    def data(self):
        if self.index is not None:
            return self.state.data
    @property
    def lastaction(self):
        "The name of the next action to undo, if any."
        return self[self.index].action
    @property
    def nextaction(self):
        "The name of the next action to redo, if any."
        if self.index != len(self)-1:
            return self[self.index + 1].action
        else:
            return ""

    def reset(self, initialstate):
        "Re-init the list with a single initial state."
        self.clear()
        self.append(UndoState(initialstate))
        self.index = 0
        self.chain = 0
        self.mergeID = None
        self._statechange()

    def addstate(self, data, action, mergeID=None, **kwargs):
        """Add a new undo state after the current index, replacing any states
        that may exist after the current index."""
        state = UndoState(data, action, **kwargs)
        if mergeID is not None and self.mergeID == mergeID:
            # merge into existing state
            self[self.index:] = [state]
        else:
            # add new state
            self[self.index+1:] = [state]
            if len(self) > AdvSettings.undo_max + 1:
                # delete oldest to cap number of undos to undo_max
                del self[0]
                self[0].action = ""
            else:
                self.index += 1
            self.mergeID = mergeID
        self.chain = 0
        self._statechange()

    def undo(self):
        "Step backward and return the new current state."
        if self.index > 0:
            updateset = self.state.updateset  # set of old state
            self.index -= 1
            self.chain = min(-1, self.chain - 1)
            self.mergeID = None
            self._statechange()
            return self.data, updateset

    def redo(self):
        "Step forward and return the new current state."
        if self.index + 1 < len(self):
            self.index += 1
            updateset = self.state.updateset  # set of new state
            self.chain = max(1, self.chain + 1)
            self.mergeID = None
            self._statechange()
            return self.data, updateset

    def updatelastsave(self):
        "Set the last saved state to be the current state."
        self.lastsave = self.state
        self._statechange()

    def issaved(self):
        "Return whether the current state is the last saved state."
        return self.state is self.lastsave

    def _statechange(self):
        """Can be subclassed for actions that need to occur whenever the
        current or last saved state changes."""
        pass
##        # print state
##        text = [str(self.index), "/", str(len(self)-1), " ",
##                str(self[self.index])]
##        if self.mergeID:
##            text += [" <mergeID: ", self.mergeID, ">"]
##        print("".join(text))

class UndoState:
    "A single state in undo history."
    def __init__(self, data, action="", updateset=frozenset()):
        self.data = copy.deepcopy(data)
        self.action = action
        self.updateset = updateset

    def __repr__(self):
        if self.action:
            return "".join((
                "<UndoState: ", self.action,
                (", " + str(self.updateset)) if self.updateset is not None
                                             else "",
                ">"
                ))
        else:
            return "<UndoState>"

class SublevelUndoHistory(UndoHistory):
    """Tracks undo history of the current sublevel, and processes the effects
    of undo/redo."""
    def addaction(self, action, *, mergeID=None,
                  updateset=frozenset(), reload=False):
        """Add the current sublevel as an undo state, given the action name.
        Optionally reload an updateset immediately."""
        self.addstate(Adv3Attr.sublevel, action, mergeID,
                      updateset=updateset)
        if reload and updateset:
            AdvWindow.editor.reload(updateset)
        self.updateeditoractions()

    def reset(self, initialstate):
        super().reset(initialstate)
        self.updateeditoractions()

    def undo(self):
        action = self.lastaction
        if not action: return
        self.loadstateineditor(*super().undo())
        self.updateeditoractions()
        self.setActionText("Undo", action)

    def redo(self):
        action = self.nextaction
        if not action: return
        self.loadstateineditor(*super().redo())
        self.updateeditoractions()
        self.setActionText("Redo", action)

    def setActionText(self, name, action):
        AdvWindow.statusbar.setActionText("{name}{num}: {action}".format(
            name=name,
            action=action,
            num="" if abs(self.chain) == 1 else " ({})".format(abs(self.chain))
            ))

    def updateeditoractions(self):
        actions = AdvWindow.editor.actions
        actions["Undo"].setEnabled(bool(self.lastaction))
        actions["Undo"].setText("Undo " + self.lastaction)
        actions["Redo"].setEnabled(bool(self.nextaction))
        actions["Redo"].setText("Redo " + self.nextaction)

    def loadstateineditor(self, sublevel, updateset):
        if updateset and "Header" in updateset:
            # update set corresponds to specific header values
            toupdate = Adv3Sublevel.cmpheader(sublevel.header)
            if toupdate:
                AdvWindow.editor.setHeader(toupdate)
        Adv3Attr.sublevel = copy.deepcopy(sublevel)
        AdvWindow.selection.clear()
        if updateset:
            AdvWindow.editor.reload(updateset)
        else:
            # sublevel editing usually affects these
            AdvWindow.editor.reload({"Objects", "Sprites"})

    def _statechange(self):
        # disable saving if current state is last saved state
        AdvWindow.editor.actions["Save Sublevel"].setDisabled(self.issaved())
