
#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      frame.py
 - $Author :      Christian Fernandez

PULSAR Project:
===============
 - Copyright (C) 2006-2008 J.P. Amoureux, C. Fernandez
 - JPA - Unite de Catalyse et Chimie du Solide, Lille, France.
 - CF  - Laboratoire Catalyse et Spectrochimie, Caen, France.

LICENSE:
========
 This program is free software; you can redistribute it and/or modify it under
 the terms of the GNU General Public License (GPL) as published by the Free
 Software Foundation; either version 2 of the License, or (at your option)
 any later version.

 This program is distributed in the hope that it will be useful, but WITHOUT ANY
 WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
 PARTICULAR PURPOSE.  See the GNU General Public License for more details.

 To read the license please visit U{http://www.gnu.org/copyleft/gpl.html}

PURPOSE OF THIS FILE:
=====================

 Set main Frame

"""

__docformat__="epytext"

import wx
from definitions import *
import common as cm
from parentframe import ParentFrame
from project import Project
import wx.aui as Aui
from book import AuiBook
from process import Process
import wx.lib.pubsub as pubsub

#===========================
class AUIFrame(ParentFrame):
#===========================
    """
    Main Aui Frame
    """

#------------------------------------------------------------------------------
    def __init__(self,
                 parent=None,
                 Id=wx.NewId(),
                 title="",
                 config=None,
                 style=wx.DEFAULT_FRAME_STYLE|
                       wx.SIMPLE_BORDER|
                       wx.CLIP_CHILDREN|
                       wx.FULL_REPAINT_ON_RESIZE):
#------------------------------------------------------------------------------
        ParentFrame.__init__(self, parent,title,config)

        # Avoid graphic updating during initial loading
        #----------------------------------------------
        self.Freeze()

        # Tell the Aui frame manager to manage this frame
        #------------------------------------------------
        self._mgr = Aui.AuiManager()
        self._mgr.SetManagedWindow(self)

        # Get and set the pyPulsar Icon
        #------------------------------
        self.SetIcon(cm.GetpyPulsarIcon())

        #---------------------------------#
        # Add the toolbars to the manager #
        #---------------------------------#

        self.ToolFile = ["FILE_NEWPRJ","FILE_SAVE","sep",
        "FILE_ADDDATASET","FILE_REMOVEDATASET","sep",
        "FILE_PRINT"]

        self.ToolEdit = ["EDIT_SAVEPAGE","EDIT_IMPORT","EDIT_EXPORT","sep",
        "EDIT_UNDO","EDIT_REDO","sep",
        "EDIT_CUT","EDIT_COPY","EDIT_PASTE","EDIT_DELETE","EDIT_SELECTALL",
        "EDIT_CLEARALL","sep",
        "EDIT_COMMENT","EDIT_UNCOMMENT","sep","EDIT_SEARCH"]

        self.ToolCommand = ["COMMAND_COMPUTE","COMMAND_STOP","COMMAND_FIT"]

        self.ToolSpectrum = ["SPECTRUM_OPTIONS","SPECTRUM_EXPORT","sep",
        "radio","SPECTRUM_FREEZE", "SPECTRUM_ZOOM", "SPECTRUM_PAN", "sep",
        "EDIT_UNDO","EDIT_REDO","SPECTRUM_RESET","sep","SPECTRUM_BROADENING"]

        self.toolbarFile=cm.CreateToolbarFromMenu(self, self.ToolFile)
        self._mgr.AddPane(self.toolbarFile, Aui.AuiPaneInfo().
                          Name("File").Caption("File").
                          ToolbarPane().Top().Show().
                          LeftDockable(False).RightDockable(False))

        self.toolbarCommand=cm.CreateToolbarFromMenu(self, self.ToolCommand)
        self._mgr.AddPane(self.toolbarCommand, Aui.AuiPaneInfo().
                          Name("Command").Caption("Command").
                          ToolbarPane().Top().Show().
                          LeftDockable(False).RightDockable(False))


        #---------------#
        # Add the panes #
        #---------------#

        # Console (contains Process logs)
        #--------------------------------
        self.Console=AuiBook(self,
                             size=wx.Size(-1, 150),
                             style= wx.NO_BORDER|
                                    Aui.AUI_NB_LEFT)

        self.Process=Process(self.Console)
        self.Logger = self.Process.logger

        self.il=cm.imglist()
        img=self.il.consoleidx

        self.Console.AddPage(self.Process.edit, "Console")

        self.Console.SetPageBitmap(0,self.il.GetBitmap(img))
        self._mgr.AddPane(self.Console, Aui.AuiPaneInfo().
                          Name("Console").CaptionVisible(False).
                          PaneBorder(False).Show().Bottom()
                          .CloseButton(True).
                          MaximizeButton(True).MinimizeButton(True))

        self.Logger.setup()

        # Project
        #-------------------------------------

        self.Project= None
        self._loadLastproject()  # Last Project loading if any

        # contains the project Tree
        self._mgr.AddPane(self.Project.Tree, Aui.AuiPaneInfo().
                          Name("Project").Caption("Project").Show().
                          PaneBorder(False).Left().CloseButton(True).
                          MaximizeButton(True))

        # and the project Book (contains main displays: plot, script, etc...)
        self._mgr.AddPane(self.Project.Book, Aui.AuiPaneInfo().
                          Name("Book").CaptionVisible(True).Show().
                          PaneBorder(True).Center().CloseButton(True).
                          MaximizeButton(True).MinimizeButton(True))

        # Define frame events
        #--------------------
        self.Bind(wx.EVT_SIZE, self._onSize)
        self.Bind(wx.EVT_CLOSE, self._onClose)

        # Set the flag for update
        #------------------------
        self.UpdateDone = False

        # Update the manager and Restore graphic updating
        #------------------------------------------------
        self.Thaw()
        self._mgr.Update()
        self.Show()

#------------------------------------------------------------------------------
    def _onClose(self, _event):
#------------------------------------------------------------------------------
        # write frame config
        self.CONFIG["SizeX"], self.CONFIG["SizeY"] = self.GetSize()
        self.CONFIG["PosX"],self.CONFIG["PosY"] = self.GetPosition()
        self.CONFIG["LogLevel"] = self.Process.logger.GetLogLevel()

        if self.Project:
            self.Project.closeProject()
        self._mgr.UnInit()
        del self._mgr
        self.Project.isLocked = True #prevent update before closing
        self.Destroy()

#------------------------------------------------------------------------------
    def _onSize(self, event):
#------------------------------------------------------------------------------
        if hasattr(self,"_mgr"):
            self._mgr.Update()

#===============================================================================
# Project
# only one project at one time for the pyPulsar Application
# with many possible dataset of different type (sim, exp,...
#===============================================================================

    #-------------------------
    def _loadLastproject(self):
    #-------------------------
        # Initial values of some parameters
        #----------------------------------
        self.last_project = str(self.CONFIG["LastProject"])
##        last = cm.getWorkspacePath('.lastproject')
##        try:
##            code=cm.MakeCode(last)
##            exec(code)
##        except:
##            DEBUG("Can't find last project!")
##            pass


        #load the last project if any
        if self.last_project is not None:
            self.Project=Project(self, self.last_project)
        else:
            DEBUG(" no last project ")
            self.Project=Project(self)

        pubsub.Publisher().sendMessage("UPDATE")

#======#
# TEST #
#======#
#-------------
def runTest():
#-------------
    parent=AUIFrame(None, pos=wx.Point(0, 0), size=wx.Size(800, 500))
    parent.Show()
    return parent

#----------------------------------------------------------------------

#-------------------------
if __name__ == '__main__':
#-------------------------
    import run
    import sys
    import os
    run.main([os.path.basename(sys.argv[0])])
