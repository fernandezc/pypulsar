#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
"""
pyPULSAR Project:
=================
    - Copyright (C) 2006-2007, Christian Fernandez and Jean-Paul Amoureux
    - JPA: Unite de Catalyse et Chimie du Solide, Lille, France.
    - CF: Laboratoire Catalyse et Spectrochimie, Caen, France.

LICENSE:
========
 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU General Public License (GPL)
 as published by the Free Software Foundation; either version 2
 of the License, or (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 To read the license please visit http://www.gnu.org/copyleft/gpl.html

PURPOSE OF THIS FILE:
=====================
 Main program

"""
__docformat__="epytext"

import wx
import common as cm
from common import LOG_DEBUG as DEBUG

# local
import sys
import frame
import splashscreen
from datetime import timedelta
from time import time
from build.version import versionString
from UserDict import UserDict

##import pytz.zoneinfo.UTC

#======================
class pyPulsarApp(wx.App):
#======================
    """
    pyPulsar main application.
    """

#------------------------------------------------------------------------------
    def __init__(self):
#------------------------------------------------------------------------------
        """
        Create a pyPulsarApp instance
        """
        wx.App.__init__(self, redirect=False)

#------------------------------------------------------------------------------
    def OnInit(self):
#------------------------------------------------------------------------------
        """
        Initialisation event
            - Create the main frame
            - Show the welcome Screen
            - return True if Init is successfull

        @rtype: bool

        """
        #Show the welcome screen and the main frame
        if SPLASH:
            self.splash = splashscreen.SplashScreen()
            self.splash.Show(True)
            wx.FutureCall(4000, self.setFrame, self.splash)
        else:
            self.setFrame()

        return True

#------------------------------------------------------------------------------
    def setFrame(self, splash=None):
#------------------------------------------------------------------------------
        """
        Create the main frame

        @param splash: SplashScreen class instance or None
        @type splash: SplashScreen

        """

        self.frame=frame.AUIFrame(title='pyPULSAR '+versionString,
                                  config = CONFIG)
        if usepsyco:
            psyco.cannotcompile(self.frame.OnUpdate_ui)

        self.frame.Process.logger.setup()

        if splash is not None:
            wx.FutureCall(20000, self.checkVersion)
            wx.FutureCall(3000, splash.Destroy)

#------------------------------------------------------------------------------
    def checkVersion(self):
#------------------------------------------------------------------------------
        """
        Determine whether or not it is usefull to check for new version
        """
        currenttime= float(time())
        if CONFIG["VersionCheck"]:
            print "ok",CONFIG["VersionCheck"]
            prev_check = float(CONFIG["VersionCheck"])
        else:
            CONFIG["VersionCheck"] =  currenttime #store current time
            prev_check=0

        td= timedelta(seconds = currenttime-prev_check)

        # td.days, "days and ", td.seconds, "seconds since last version checking."
        if(td.days > 6):
            #perform a check every week
            self.frame.StatusBar.SetStatusText("Checking for update...", 0)
            self.check = splashscreen.CheckVersionScreen(self.splash,
                                                           self.frame.StatusBar)
            CONFIG["VersionCheck"] =  currenttime #store current time


#===============================================================================
class pyPulsarConfig(UserDict):
#===============================================================================
    """ configuration """
#-------------------------------------------------------------------------------
    def __init__(self):
#-------------------------------------------------------------------------------
        UserDict.__init__(self)
        self.__config = wx.Config("pyPulsar0.2")
        # read registry (Windows) or configuration file (Unix)
        bCont, key, index = self.__config.GetFirstEntry()
        while bCont:
            self.data[key] = self.__config.Read(key)
            bCont, key, index = self.__config.GetNextEntry(index)

#-------------------------------------------------------------------------------
    def iteritems(self):
#-------------------------------------------------------------------------------
        return self.data.iteritems()

#-------------------------------------------------------------------------------
    def __setitem__(self, key, item):
#-------------------------------------------------------------------------------
        self.data[key] = str(item)
        self.__config.Write(key, str(item))

#-------------------------------------------------------------------------------
    def __getitem__(self, key):
#-------------------------------------------------------------------------------
        if self.data.has_key(key):
            return self.data[key]
        else:
            return None

#-------------------------------------------------------------------------------
    def __delitem__(self, key):
#-------------------------------------------------------------------------------
        del self.data[key]
        self.__config.DeleteEntry(key, item)


#------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Main program
    """
    # Configuration
    #---------------
    CONFIG = pyPulsarConfig()

    # Debugging mode
    #----------------
    debug = (((CONFIG["Debug"]=="True")
            |("/DEBUG" in sys.argv))
            &("/NODEBUG" not in sys.argv))

    CONFIG["Debug"]=debug

    # Psyco code optimizer
    #----------------------
    usepsyco =  (((CONFIG["UsePsyco"]=="True")
                |("/NOPSYCO" not in sys.argv))
                & (not debug))
    if usepsyco:
        CONFIG["UsePsyco"]=True
        import psyco
        try:
            psyco.profile(0.3)
        except:
            CONFIG["UsePsyco"]=False
    else:
        CONFIG["UsePsyco"]=False
    usepsyco = (CONFIG["UsePsyco"]=="True")

    SPLASH=True             # Should be set to False
                                   # for removing Splash during developpement
    app = pyPulsarApp()
    app.MainLoop()

