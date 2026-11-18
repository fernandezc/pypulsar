#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      run.py
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

TEST CONTROLS (inspired by run.py in wx demo)
"""

__docformat__="epytext"


import wx
import wx.lib.mixins.inspection as inspection
import sys, os

# stuff for debugging
wx.LogDebug("wx.version:"+repr(wx.version()))
wx.LogDebug("pid:"+repr(os.getpid()))

assertMode = wx.PYAPP_ASSERT_DIALOG
#assertMode = wx.PYAPP_ASSERT_EXCEPTION

#----------------------------------------------------------------------------
class RunApp(wx.App, inspection.InspectionMixin):

    def __init__(self, name, module):
        self.name = name
        self.module = module
        wx.App.__init__(self, redirect=False)

    def OnInit(self):
        wx.Log_SetActiveTarget(wx.LogStderr())
        wx.Log_SetVerbose(True)

        #wx.Log_SetTraceMask(wx.TraceMessages)
        self.SetAssertMode(assertMode)
        self.Init()  # InspectionMixin
        self.module.runTest()

        return True

#----------------------------------------------------------------------------
def main(argv):

    if len(argv) < 1:
        print "Please specify a module name on the command-line"
        raise SystemExit

    wx.LogDebug("Current running module:"+repr(argv[0]))

    name, ext  = os.path.splitext(argv[0])
    module = __import__(name)

    app = RunApp(name, module)
    app.MainLoop()

if __name__ == "__main__":
    main(sys.argv)


