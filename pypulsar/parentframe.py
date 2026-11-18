#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name  :   parentframe.py
 - $Author :   Christian Fernandez

PULSAR Project:
===============
 - Copyright (C) 2006-2008 J.P. Amoureux, C. Fernandez
 - JPA - Unite de Catalyse et Chimie du Solide, Lille, France.
 - CF - Laboratoire Catalyse et Spectrochimie, Caen, France.

LICENSE:
========
 This program is free software; you can redistribute it and/or modify it under
 the terms of the GNU General Public License (GPL) as published by the Free
 Software Foundation; either version 2 of the License, or (at your option)
 any later version.

 This program is distributed in the hope that it will be useful, but WITHOUT ANY
 WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
 PARTICULAR PURPOSE. See the GNU General Public License for more details.

 To read the license please visit U{http://www.gnu.org/copyleft/gpl.html}

PURPOSE OF THIS FILE:
=====================
 parent Frame

"""

__docformat__ = "epytext"


from definitions import *
from common import *
from common import LOG_DEBUG as DEBUG
from pypulsar_xrc import xrcParentFrame
import enhancedstatusbar as ESB
import wx.lib.buttons as button
from printer import Printer, Plotter
from help import HelpDoc, HelpAbout
import regularsearch as Search
import types
import wx.lib.pubsub as pubsub

# ================================
class ParentFrame(xrcParentFrame):
# ================================
    """
    Basic parent frame class
    """
#------------------------------------------------------------------------------
    def __init__(self, parent=None, title='Untitled',CONFIG=None):
#------------------------------------------------------------------------------
        """
        Initialisation of the frame with status and menu bars
        """
        xrcParentFrame.__init__(self, parent)

        self.CONFIG=CONFIG
        self.SetTitle(title)

        #------------------------------
        # Min size for the frame itself
        #------------------------------
        self.SetMinSize(wx.DefaultSize)

        # Size of the window
        #--------------------
        if CONFIG["SizeX"] and CONFIG["SizeY"] \
        and CONFIG["PosX"] and CONFIG["PosY"]:
            x = int(float(CONFIG["SizeX"]))
            y = int(float(CONFIG["SizeY"]))
            x0 = int(float(CONFIG["PosX"]))
            y0 = int(float(CONFIG["PosY"]))
        else:
            proportion=.75
            x=wx.SystemSettings_GetMetric(wx.SYS_SCREEN_X)*proportion
            y=wx.SystemSettings_GetMetric(wx.SYS_SCREEN_Y)*proportion
            x0 = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_X)/2. - x/2.
            y0 = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_Y)/2. - y/2.
        CONFIG["SizeX"] = x
        CONFIG["SizeY"] = y
        CONFIG["PosX"] = x0
        CONFIG["PosY"] = y0
        self.SetSize((x,y))
        self.SetPosition((x0,y0))

        #-------------------------------
        # Create and init the Status Bar
        #-------------------------------
        self.sb = ESB.EnhancedStatusBar(self, style = wx.ST_SIZEGRIP)
        self.makeStatusBar()
        self.SetStatusBar(self.sb)
        self.setStatusText(default = True)

        #------------------------
        # Default initializations
        #------------------------
        self.printer = Printer(self)
        self.plotter = Plotter(self)
        # There is no project and no process by default
        self.Project = None
        self.Process = None
        self.Console = None
        self.SearchEnabled=False

        self.win = None
        self.winbook = None
        self.__modify = False
        self.__updatedone = False
        self.__savewin = None
        self.currentwin = None
        self.__stopui = False
        self.__iserror = False

        # events
        #---------------------
        self.Bind(wx.EVT_IDLE, self._onIdle)
        self.Bind(wx.EVT_MOUSE_EVENTS, self._stopUpdateUI)
        pubsub.Publisher().subscribe(self._forceUpdateFrame, "UPDATE")
        pubsub.Publisher().subscribe(self._updatePos, "MOTION")
        pubsub.Publisher().subscribe(self._setHasError, "ERROR")

#------------------------------------------------------------------------------
    def _onIdle(self, event):
#------------------------------------------------------------------------------
        if not self.updateDone:
            self._updateFrame()
        event.Skip()

#-------------------------------------------------------------------------------
# Property updateDone
#-------------------------------------------------------------------------------
    def _getUpdateFlag(self):
#-------------------------------------------------------------------------------
        """
        Get update status of the project
        """
        return self.__updatedone

#-------------------------------------------------------------------------------
    def _setUpdateFlag(self, value):
#-------------------------------------------------------------------------------
        """
        Set update status of the project
        """
        self.__updatedone = value

    updateDone = property(fget = _getUpdateFlag, fset = _setUpdateFlag)

#-------------------------------------------------------------------------------
    def _forceUpdateFrame(self, data=None):
#-------------------------------------------------------------------------------
        self._updateFrame()

#-------------------------------------------------------------------------------
# Property hasProject
#-------------------------------------------------------------------------------
    def _getHasProject(self):
#-------------------------------------------------------------------------------
        """
        is project existing?
        """
        if self.Project:
            return True
        else:
            return False

    hasProject = property(fget = _getHasProject)

#-------------------------------------------------------------------------------
# Property hasError
#-------------------------------------------------------------------------------
    def _setHasError(self, value):
#-------------------------------------------------------------------------------
        """
        set by event ERROR
        """
        self.__iserror = value.data
        self._forceUpdateFrame()

#-------------------------------------------------------------------------------
    def _getHasError(self):
#-------------------------------------------------------------------------------
        """
        is there any errors?
        """
        return self.__iserror

    hasError = property(fget = _getHasError)

#-------------------------------------------------------------------------------
    def _updateFrame(self):
#-------------------------------------------------------------------------------
        """
        Update and Set update flag
        """
        self.__updatedone = True

        # Update statusbar
        self._updateStatus()
        # Update title
        self._updateTitle()
        # Update project
        self._updateProject()
        # Update Console
        self._updateConsole()

#-------------------------------------------------------------------------------
    def _updateConsole(self):
#-------------------------------------------------------------------------------
        """
        Update Console image
        """
        txt = ""
        if self.hasError:
            txt = "_error"
        self.il = imglist()
        img = getattr(self.il, "console%sidx"%txt)
        if hasattr(self, "Console"):
            self.Console.SetPageBitmap(0, self.il.GetBitmap(img))

#-------------------------------------------------------------------------------
    def _updateStatus(self, message = None):
#-------------------------------------------------------------------------------
        """
        Update current statusbar information.
        """
        win = wx.Window_FindFocus()
        if hasattr(win, "getOvertype"):
            self.currentwin = win

        # Update the statusbar main text
        self.setStatusText("pyPulsar- A solid state NMR simulation program")

        # update the position display in statusbar
        if hasattr(win, "getPosString") \
           and win.getPosString() != self.getStatusText(4):
            self.setStatusText(win.getPosString(), 4)

        # overtype button display in the statusbar
        self.overtype.Show(hasattr(win, "getOvertype"))
        if hasattr(win, "getOvertype") \
              and win.getOvertype() != self.overtype.GetLabel():
            self.overtype.SetLabel(win.getOvertype())
            self.Refresh()

#-------------------------------------------------------------------------------
    def _updatePos(self, message = None):
#-------------------------------------------------------------------------------
        """
        Update current statusbar information with current position.
        """
        win = wx.Window_FindFocus()
        if hasattr(win, "getOvertype"):
            self.currentwin = win

        # update the position display in statusbar
        if hasattr(win, "getPosString") \
                                and win.getPosString() != self.getStatusText(4):
            self.setStatusText(win.getPosString(), 4)

#-------------------------------------------------------------------------------
    def _updateProject(self):
#-------------------------------------------------------------------------------
        if self.Project:
            self.Project.updateProject()

#-------------------------------------------------------------------------------
    def _updateTitle(self):
#-------------------------------------------------------------------------------
        """
        Update current title information.
        """
        title = self.GetTitle()
        if self.Project and self.Project.isModified:
            if title.startswith('* '):
                pass
            else:
                self.SetTitle('* ' + title)
        else:
            if title.startswith('* '):
                self.SetTitle(title[2:])

#===============================================================================
# Status bar
#===============================================================================

#-------------------------------------------------------------------------------
    def makeStatusBar(self):
#-------------------------------------------------------------------------------
        self.sb.SetFieldsCount(5)
        self.sb.SetStatusWidths([-2, -2, -1, 60, 120])
        self.progress = wx.Gauge(self.sb, -1, size = wx.Size(200, 20),
                                 style=wx.GA_SMOOTH)
        self.overtype = button.GenButton(self.sb, -1, 'Overtype',
                        style = wx.BORDER_NONE|wx.TRANSPARENT)
        self.progress.Hide()
        self.overtype.Hide()

        self.sb.AddWidget(self.progress, ESB.ESB_EXACT_FIT,
                              ESB.ESB_EXACT_FIT, pos = 2)
        self.sb.AddWidget(self.overtype, ESB.ESB_EXACT_FIT,
                              ESB.ESB_EXACT_FIT, pos = 3)

        # Bind event to the overtype button
        self.Bind(wx.EVT_BUTTON, self.onToggleOvertype, self.overtype)

#-------------------------------------------------------------------------------
    def getStatusText(self, number):
#-------------------------------------------------------------------------------
        return self.sb.GetStatusText(number)

#-------------------------------------------------------------------------------
    def setStatusText(self, args = "", number = 0, default = False):
#-------------------------------------------------------------------------------
        """
        Override setStatusText
        virtual void setStatusText( tuple or text args, int number = 0,
                                boolean default = False)

        Sets the status bar text and redraws the status bar.

        @param text: The text for the status field or a tuple of fields.
        @keyword number: The status field (starting from zero).
        @keyword default: if True set default fields

        """
        self.default = ["pyPulsar- A solid state NMR simulation program",
                "",
                "",
                "",
                ""]

        if type(args) is str and not default:
            self.sb.SetStatusText(args, number)
        else:
            if default:
                # Status Bar default
                status = self.default
            else:
                status = args
            for i in range(5):
                self.sb.SetStatusText(str(status[i]), i)

#-------------------------------------------------------------------------------
    def onToggleOvertype(self, _event):
#-------------------------------------------------------------------------------
        self.currentwin.ToggleOvertype()


#===============================================================================
# Menus and Toolbar updates
#===============================================================================

    def _stopUpdateUI(self, event):
        self.__stopui = event.ButtonDown()
        #event.Skip()

#-------------------------------------------------------------------------------
    def OnUpdate_ui(self, event):
#-------------------------------------------------------------------------------
        """
        Update menu items based on current status and context.
        """
        if self.__stopui :
            return

        if event:
            aid = event.GetId()
            #print aid
            event.Enable(False)
        else:
            return

        win = wx.Window_FindFocus()
        if win is None :
            return

        winbook = None
        if hasattr(self.Project, "Book"):
            if self.Project.Book.GetPageCount()>0:
                winbook = self.Project.Book.GetPage(
                                       self.Project.Book.GetSelection())
        if win != self.win or winbook != self.winbook:
            self.win = win
            self.winbook = winbook

##        if aid == self.GetId():
##            event.Enable(True)

        # File-----------------------------------
        if aid == self.FILE_NEWPRJ.GetId()\
          and hasattr(self, "hasProject")\
          and hasattr(self.Project, "newProject"):
            event.Enable(True)

        elif aid == self.FILE_ADDDATASET.GetId() \
          and hasattr(self, "hasProject"):
            event.Enable(self.hasProject)

        elif aid == self.FILE_REMOVEDATASET.GetId() \
          and hasattr(self, "hasProject") \
          and hasattr(self.Project, "canDelDataset"):
            event.Enable(self.Project.canDelDataset())

        elif aid == self.FILE_REMOVEALLDATASET.GetId() \
          and hasattr(self, "hasProject") \
          and hasattr(self.Project, "containDataset") \
          and self.Project.containDataset():
            event.Enable(True)

        elif aid == self.FILE_SAVE.GetId() \
          and self.hasProject \
          and hasattr(self.Project, "saveProject"):
            event.Enable(self.Project.isModified)

        elif aid == self.FILE_SAVEAS.GetId() \
          and self.hasProject \
          and hasattr(self.Project, "saveProject"):
            event.Enable(True)

        elif aid == self.FILE_REVERT.GetId() \
               and hasattr(self, "Project")\
          and hasattr(self.Project, "revert"):
            event.Enable(self.Project.isModified
                   and self.Project.canUndo() )

        elif aid == self.FILE_RENAME.GetId()\
               and self.hasProject \
               and hasattr(self.Project.Tree, "canRename")\
               and hasattr(self.Project.Tree, "rename"):
            event.Enable(self.Project.Tree.canRename())

        elif aid == self.FILE_PRINT.GetId() \
              and hasattr(win, "print"):
            event.Enable(win.Content != "" or win.Content is not None)

        elif aid == self.EXIT.GetId() :
            event.Enable(True)


        # Edit---------------------------------------
        elif aid == self.EDIT_SAVEPAGE.GetId() \
            and winbook is not None \
            and hasattr(winbook, "save"):
            event.Enable(winbook.isModified)

        elif aid == self.EDIT_CLEARALL.GetId() \
                    and hasattr(win, "Content") \
                    and hasattr(win, "clearAll"):
            event.Enable(win.Content != "" or win.Content is not None)

        elif aid == self.EDIT_SELECTALL.GetId()  \
                    and hasattr(win, "Content") \
              and hasattr(win, "selectAll"):
            event.Enable(win.Content != "" or win.Content is not None)

        elif aid == self.EDIT_UNDO.GetId() \
              and hasattr(win, "Undo"):
            event.Enable(win.CanUndo())

        elif aid == self.EDIT_REDO.GetId() \
              and hasattr(win, "Redo"):
            event.Enable(win.CanRedo())

        elif aid == self.EDIT_CUT.GetId() \
              and hasattr(win, "canCut"):
            event.Enable(win.canCut())

        elif aid == self.EDIT_COPY.GetId() \
              and hasattr(win, "canCopy"):
            event.Enable(win.canCopy())

        elif aid == self.EDIT_PASTE.GetId() \
              and hasattr(win, "canPaste"):
            event.Enable(win.canPaste())

        elif aid == self.EDIT_DELETE.GetId() \
              and hasattr(win, "canCut"):
            event.Enable(win.canCut())

        elif aid == self.EDIT_COMMENT.GetId()  \
                    and hasattr(win, "Content") \
              and hasattr(win, "canComment"):
            event.Enable((win.Content != "" or win.Content is not None) \
                   and win.canComment())

        elif aid == self.EDIT_UNCOMMENT.GetId()  \
                    and hasattr(win, "Content") \
            and hasattr(win, "canUncomment"):
            event.Enable((win.Content != "" or win.Content is not None)
                   and win.canUncomment())

        elif aid == self.EDIT_SEARCH.GetId()  \
                    and hasattr(win, "Content") \
              and hasattr(win, "searchEnabled"):
            event.Enable(win.searchEnabled and win.Content is not None \
                                                              and win.haveFocus)

        # Plot-------------------------------------------
        elif aid == self.SPECTRUM_RESET.GetId() and hasattr(win, "doReset"):
            event.Enable(win.CanRedo() or win.CanUndo())

        elif aid == self.SPECTRUM_ZOOM.GetId() and hasattr(win, "CanZoom"):
            event.Enable(win.CanZoom())

        elif aid == self.SPECTRUM_PAN.GetId() \
          and hasattr(win, "CanPan"):
            event.Enable(win.CanPan())

        elif aid == self.SPECTRUM_FREEZE.GetId() \
          and hasattr(win, "CanPan"):
            event.Enable(not win.CanPan() or not win.CanZoom())

        elif aid == self.SPECTRUM_UNDO.GetId() \
          and hasattr(win, "CanUndo"):
            event.Enable(win.CanUndo())

        elif aid == self.SPECTRUM_REDO.GetId() \
          and hasattr(win, "CanRedo"):
            event.Enable(win.CanRedo())

        elif aid == self.SPECTRUM_OPTIONS.GetId():
            #win is here figCanvas -> we need the parent : Plot
            if hasattr(win.GetParent(), "doPlotConfig"):
                event.Enable(True)

        elif aid == self.SPECTRUM_EXPORT.GetId():
            if hasattr(win.GetParent(), "hasPlot"):
                event.Enable(win.GetParent().hasPlot)

        elif aid == self.SPECTRUM_BROADENING.GetId():
            if hasattr(win.GetParent(), "hasPlot"):
                event.Enable(win.GetParent().hasPlot)

        # Commands----------------------------------
        elif aid == self.COMMAND_COMPUTE.GetId() \
                             and hasattr(self.Process, "canRun"):
            self.toolbarCommand.Show()
            self._mgr.Update()
            event.Enable(self.Process.canRun())

        elif aid == self.COMMAND_STOP.GetId() \
                                         and hasattr(self.Process, "isRunning"):
            event.Enable(self.Process.isRunning)

        elif aid == self.COMMAND_FIT.GetId() \
                                            and hasattr(self.Process, "canRun"):
            event.Enable(self.Process.canRun())   # and self.Project.isFittable)
##          and hasattr(winbook, "canRun"):
##            event.Enable(winbook.canRun() and self.Project.isFittable)

        # Logs -------------------------------------
        elif aid == self.OPTIONS_LOGERROR.GetId():
            event.Enable(True)
##            e = self.OPTIONS_LOGERROR
##            if e.IsChecked():
##                self.loglevel = ERRORLEVEL

        elif aid == self.OPTIONS_LOGWARNING.GetId():
            event.Enable(True)
##            e = self.OPTIONS_LOGWARNING
##            if e.IsChecked():
##                self.loglevel = WARNINGLEVEL

        elif aid == self.OPTIONS_LOGINFO.GetId():
            event.Enable(True)
##            e = self.OPTIONS_LOGINFO
##            if e.IsChecked():
##                self.loglevel = INFOLEVEL

        elif aid == self.OPTIONS_LOGVERBOSE.GetId():
            event.Enable(True)
##            e = self.OPTIONS_LOGVERBOSE
##            if e.IsChecked():
##                self.loglevel = VERBOSELEVEL

        elif aid == self.OPTIONS_LOGDEBUG.GetId():
            event.Enable(False)
##            e = self.OPTIONS_LOGDEBUG
##            if e.IsChecked():
##                self.loglevel = DEBUGLEVEL

        # Help ---------------------------------------
        elif aid == self.HELP_CONTEXT.GetId():
            event.Enable(False) #TODO: implement HELPCONTEXT

        elif aid == self.HELP_DOC.GetId():
            event.Enable(wx.Platform == '__WXMSW__')

        elif aid == self.HELP_ABOUT.GetId():
            event.Enable(True)  # Always enabled

        else:
            pass

#-------------------------------------------------------------------------------
    def OnMenu_FILE_NEWPRJ(self, evt):
#-------------------------------------------------------------------------------
        self.Project.newProject()

#-------------------------------------------------------------------------------
    def OnMenu_FILE_SAVE(self, evt):
#-------------------------------------------------------------------------------
        self.Project.saveProject(saveas = False)

#-------------------------------------------------------------------------------
    def OnMenu_FILE_SAVEAS(self, evt):
#-------------------------------------------------------------------------------
        self.Project.saveProject(saveas = True)

#-------------------------------------------------------------------------------
    def OnMenu_FILE_REVERT(self, evt):
#-------------------------------------------------------------------------------
        self.Project.revert()

#-------------------------------------------------------------------------------
    def OnMenu_FILE_ADDDATASET(self, evt):
#-------------------------------------------------------------------------------
        self.Project.addDataset()

#-------------------------------------------------------------------------------
    def OnMenu_FILE_REMOVEDATASET(self, evt):
#-------------------------------------------------------------------------------
        del self.Project.Dataset

#-------------------------------------------------------------------------------
    def OnMenu_FILE_REMOVEALLDATASET(self, evt):
#-------------------------------------------------------------------------------
        self.Project.delAlldataset()

#-------------------------------------------------------------------------------
    def OnMenu_FILE_RENAME(self, evt):
#-------------------------------------------------------------------------------
        self.Project.Tree.rename()

#-------------------------------------------------------------------------------
    def OnMenu_FILE_IMPORT(self, evt):
#-------------------------------------------------------------------------------
        #TODO: implement Import
        pass

#-------------------------------------------------------------------------------
    def OnMenu_FILE_EXPORT(self, evt):
#-------------------------------------------------------------------------------
        #TODO: implement Export
        pass

#-------------------------------------------------------------------------------
    def OnMenu_FILE_PAGESETUP(self, evt):
#-------------------------------------------------------------------------------
        #TODO: implement PageSetup
        pass

#-------------------------------------------------------------------------------
    def OnMenu_FILE_PRINT(self, evt):
#-------------------------------------------------------------------------------
        #Todo: implement Print
        pass

#-------------------------------------------------------------------------------
    def OnMenu_EXIT(self, evt):
#-------------------------------------------------------------------------------
        if hasattr(self, "_onClose"):
            self._onClose(evt)
        else:
            self.Destroy()

#-------------------------------------------------------------------------------
    def OnMenu_EDIT_SAVEPAGE(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        winbook = self.Project.Book.GetPage(self.Project.Book.GetSelection())
        winbook.save()

#-------------------------------------------------------------------------------
    def OnMenu_EDIT_UNDO(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.Undo()

#-------------------------------------------------------------------------------
    def OnMenu_EDIT_REDO(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.Redo()

#-------------------------------------------------------------------------------
    def OnMenu_EDIT_CUT(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.Cut()

#-------------------------------------------------------------------------------
    def OnMenu_EDIT_COPY(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.Copy()

#-------------------------------------------------------------------------------
    def OnMenu_EDIT_PASTE(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.Paste()

#-------------------------------------------------------------------------------
    def OnMenu_EDIT_DELETE(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.Clear()

#-------------------------------------------------------------------------------
    def OnMenu_EDIT_SELECTALL(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.SelectAll()

#-------------------------------------------------------------------------------
    def OnMenu_EDIT_CLEARALL(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.ClearAll()

#-------------------------------------------------------------------------------
    def OnMenu_EDIT_COMMENT(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        s = win.GetSelectionStart()
        e = win.GetSelectionEnd()
        linestart = win.LineFromPosition(s)
        lineend = win.LineFromPosition(e)
        for line in range(linestart, lineend+1):
            win.GotoLine(line)
            start = win.selectLineAtCursor()[0]
            win.InsertText(start, "#")

#-------------------------------------------------------------------------------
    def OnMenu_EDIT_UNCOMMENT(self, evt):
#-------------------------------------------------------------------------------
        searchstring = {}
        searchstring["python"] = "^\s*#+"

        win = wx.Window_FindFocus()
        s = win.GetSelectionStart()
        e = win.GetSelectionEnd()
        linestart = win.LineFromPosition(s)
        lineend = win.LineFromPosition(e)
        for line in range(linestart, lineend+1):
            win.GotoLine(line)
            start, end = win.selectLineAtCursor()
            sFind = searchstring["python"]
            rFind = re.compile(sFind)
            m, uStart, uEnd = Search.Search(rFind, start, end, ed = win)
            if m:
                win.SetSelection(uStart, uEnd)
                text = win.GetSelectedText()
                win.ReplaceSelection(text[0:len(text)-1])
        win.Refresh()

#-------------------------------------------------------------------------------
    def OnMenu_EDIT_SEARCH(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        self.dialogsearch = Search.SearchDialog(win)
        self.dialogsearch.Show()

#-------------------------------------------------------------------------------
    def OnMenu_COMMAND_COMPUTE(self, evt):
#-------------------------------------------------------------------------------
        self.Process.runScript()

#-------------------------------------------------------------------------------
    def OnMenu_COMMAND_STOP(self, evt):
#-------------------------------------------------------------------------------
        self.Process.stopScript()

#-------------------------------------------------------------------------------
    def OnMenu_COMMAND_FIT(self, evt):
#-------------------------------------------------------------------------------
        self.Process.runScript(fitting = True)

#-------------------------------------------------------------------------------
    def OnMenu_SPECTRUM_ZOOM(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.doZoom()

#-------------------------------------------------------------------------------
    def OnMenu_SPECTRUM_PAN(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.doPan()

#-------------------------------------------------------------------------------
    def OnMenu_SPECTRUM_UNDO(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.Undo()

#-------------------------------------------------------------------------------
    def OnMenu_SPECTRUM_REDO(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.Redo()

#-------------------------------------------------------------------------------
    def OnMenu_SPECTRUM_FREEZE(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.doFreeze()

#-------------------------------------------------------------------------------
    def OnMenu_SPECTRUM_OPTIONS(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.GetParent().doPlotConfig()

#-------------------------------------------------------------------------------
    def OnMenu_SPECTRUM_EXPORT(self,evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.GetParent().doExport()

#-------------------------------------------------------------------------------
    def OnMenu_SPECTRUM_BROADENING(sef,evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.GetParent().doBroadening()

#-------------------------------------------------------------------------------
    def OnMenu_SPECTRUM_RESET(self, evt):
#-------------------------------------------------------------------------------
        win = wx.Window_FindFocus()
        win.doReset()

#-------------------------------------------------------------------------------
    def OnMenu_OPTIONS_LOGERROR(self, evt):
#-------------------------------------------------------------------------------
        LOG_WARNING("Log level has been set to 'ERROR'")
        self.Logger.setLogLevel(ERRORLEVEL)

#-------------------------------------------------------------------------------
    def OnMenu_OPTIONS_LOGWARNING(self, evt):
#-------------------------------------------------------------------------------
        LOG_WARNING("Log level has been set to 'WARNING'")
        self.Logger.setLogLevel(WARNINGLEVEL)

#-------------------------------------------------------------------------------
    def OnMenu_OPTIONS_LOGINFO(self, evt):
#-------------------------------------------------------------------------------
        LOG_WARNING("Log level has been set to 'INFORMATION'")
        self.Logger.setLogLevel(INFOLEVEL)

#-------------------------------------------------------------------------------
    def OnMenu_OPTIONS_LOGVERBOSE(self, evt):
#-------------------------------------------------------------------------------
        LOG_WARNING("Log level has been set to 'VERBOSE'")
        self.Logger.setLogLevel(VERBOSELEVEL)

#-------------------------------------------------------------------------------
    def OnMenu_OPTIONS_LOGDEBUG(self, evt):
#-------------------------------------------------------------------------------
        LOG_WARNING("Log level has been set to 'DEBUG'")
        self.Logger.setLogLevel(DEBUGLEVEL)

#-------------------------------------------------------------------------------
    def OnMenu_HELP_ABOUT(self, event):
#-------------------------------------------------------------------------------
        """
        Show the About dialog box (modal)
        """
        dlg = HelpAbout(self)
        dlg.ShowModal()
        dlg.Destroy()

#-------------------------------------------------------------------------------
    def OnMenu_HELP_DOC(self, event):
#-------------------------------------------------------------------------------
        """
        Show the online doc pages (not modal)
        """
        dlg = HelpDoc(self)
        dlg.Show(True)

#-------------------------------------------------------------------------------
    def OnMenu_HELP_CONTEXT(self, event):
#-------------------------------------------------------------------------------
        """
        Show the context help pages
        """
        pass #TODO implement HelpContext


# ====== #
# TEST #
# ====== #
#-------------------------------------------------------------------------------
def runTest():
#-------------------------------------------------------------------------------
    top = wx.Frame(None, -1)
    ParentFrame(top, size = wx.Size(800, 500))
    top.Show()
    return top


#-------------------------------------------------------------------------------
if __name__ == '__main__':
#-------------------------------------------------------------------------------
    import run
    import os, sys
    run.main([os.path.basename(sys.argv[0])])

