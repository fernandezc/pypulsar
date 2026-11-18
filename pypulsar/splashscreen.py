#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      splashscreen.py
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
"""

__docformat__="epytext"

import wx.xrc as xrc
from pypulsar_xrc import xrcSplashDlg, xrcCheckDlg
from wx import EVT_BUTTON
import urllib
import string
import time
from build.version import __PROJECT_VERSION__,__PROJECT_REVISION__, \
                          __PROJECT_SVNREVISION__,__PROJECT_REVISION_DATE__

VERSION = __PROJECT_VERSION__
REVISION = __PROJECT_REVISION__
SVN = __PROJECT_SVNREVISION__
DATE = __PROJECT_REVISION_DATE__

#====================================
class SplashScreen(xrcSplashDlg):
#====================================
    #--------------------------
    def __init__(self):
    #--------------------------
        # Initialize the splashscreen
        xrcSplashDlg.__init__(self, None)
        #  Static elements are not generated with XRCED, unfortunatly
        self._TEXT = xrc.XRCCTRL(self, "_TEXT")
        self._VERSION = xrc.XRCCTRL(self, "_VERSION")
        self._COPYRIGHT = xrc.XRCCTRL(self, "_COPYRIGHT")
        self._BITMAP = xrc.XRCCTRL(self, "_BITMAP")

        self._VERSION.SetLabel("version: "+VERSION+"."+REVISION+" (svn-"+SVN+")")
        self._VERSION.Show(True)
        self._BITMAP.Show(True)
        self._TEXT.Show(True)
        self._COPYRIGHT.Show(True)
        self.Show(True)
        self.Layout()

    #------------------------
    def setText(self, value):
    #------------------------
        self._TEXT.SetLabel(value)

    #---------------------
    def SplashClose(self):#, frame):
    #---------------------
        self.Destroy()

#====================================
class CheckVersionScreen(xrcCheckDlg):
#====================================
    #--------------------------
    def __init__(self,splash,statusbar):
    #--------------------------
        # Initialize the splashscreen
        xrcCheckDlg.__init__(self, None)

        #  Static elements are not generated with XRCED, unfortunatly
        self._TEXT = xrc.XRCCTRL(self, "_TEXT")
        self._VERSION = xrc.XRCCTRL(self, "_VERSION")
        self._COPYRIGHT = xrc.XRCCTRL(self, "_COPYRIGHT")
        self._BITMAP = xrc.XRCCTRL(self, "_BITMAP")

        self.statusbar=statusbar
        self.splash=splash
##        try:
        f=urllib.urlopen("http://www-lcs.ensicaen.fr/pyPulsar/version/index.html")
        line = f.readline().split(".")
        newversion = string.strip(str(line[0])+'.'+str(line[1]))
        newrevision = string.strip(str(line[2]))
        if (newrevision != SVN):
            self.Bind(EVT_BUTTON, self.OnOk, self._OKBUTTON)
            self._TEXT.Show()
            self._INFO.Show()
            self._OKBUTTON.Show()
            # Update the Version Number
            self._VERSION.SetLabel("version: "+VERSION+"."+REVISION+
                                                           " (svn-"+SVN+")")
            self._TEXT.SetLabel("A new update is available:  "
                                               +newversion+"."+newrevision)
            self._INFO.SetValue(string.join(f.readlines(), " "))
            self.Layout()
            self.Refresh()
            self.Raise()
            self.Show()
            self.statusbar.SetStatusText("Found a new program update!",0)
        else:
            self.Destroy()
            self.statusbar.SetStatusText("",0)
##    except:
##            self.Destroy()
##            self.statusbar.SetStatusText("",0)

    #------------------------
    def setText(self, value):
    #------------------------
        self._TEXT.SetLabel(value)

    #---------------------
    def OnOk(self, event):
    #---------------------
        self.statusbar.SetStatusText("",0)
        try:
            self.splash.Destroy()
        except:
            pass #in case the splash window is already self destroyed
        self.Destroy()
