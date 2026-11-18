#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      common.py
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
Basic variables, functions or classes used in pyPulsar
"""

__docformat__="epytext"

#-------------------------------------------------------------------------------
import wx
import sys
import re
import types
import string
import math
import cStringIO
import os
import os.path as path
import time

from definitions import *
from forpulsar import parameters
from pypulsar_xrc import xrcInfoDlg

#===============================================================================
#                                   Classes
#===============================================================================

#===============================================================================
class pyLog(wx.PyLog):
#===============================================================================
    """
    Class writing of logs in the specified control
    """

#-------------------------------------------------------------------------------
    def __init__(self, parent):
#-------------------------------------------------------------------------------
        """
        Create a PyLog instance
        """
        wx.PyLog.__init__(self)
        self.target = parent.edit
        self.normal = wx.Font(9, wx.MODERN, wx.NORMAL, wx.NORMAL);
        self.bold = wx.Font(9, wx.MODERN, wx.NORMAL, wx.BOLD);
        self.italic = wx.Font(9, wx.MODERN, wx.ITALIC, wx.NORMAL);
        self.target.SetFont(self.normal)
        self.SetVerbose(True)
        self.modified=False
        self.CONFIG = parent.frame.CONFIG
        self.Process = parent

#-------------------------------------------------------------------------------
    def setup(self):
#-------------------------------------------------------------------------------
        import sys

        if self.CONFIG["LogLevel"]:
            self.SetLogLevel(int(self.CONFIG["LogLevel"]))
        else:
            self.SetLogLevel(INFOLEVEL)

        if self.CONFIG["Debug"]=="True":
            self.SetLogLevel(DEBUGLEVEL)

        if self.GetLogLevel()==DEBUGLEVEL:
            self.target.parent.parent.OPTIONS_LOGDEBUG.Check(True)
        elif self.GetLogLevel()==VERBOSELEVEL:
            self.target.parent.parent.OPTIONS_LOGVERBOSE.Check(True)
        elif self.GetLogLevel()==INFOLEVEL:
            self.target.parent.parent.OPTIONS_LOGINFO.Check(True)
        elif self.GetLogLevel()==WARNINGLEVEL:
            self.target.parent.parent.OPTIONS_LOGWARNING.Check(True)
        elif self.GetLogLevel()==ERRORLEVEL:
            self.target.parent.parent.OPTIONS_LOGERROR.Check(True)

        parameters.loglevel = self.GetLogLevel()
        self.CONFIG["LogLevel"] = self.GetLogLevel()

        wx.LogDebug("In setup, LogLevel was set to '"+
                                            LEVELS[str(self.GetLogLevel())]+"'")

#-------------------------------------------------------------------------------
    def setLogLevel(self, loglevel):
#-------------------------------------------------------------------------------
        self.SetLogLevel(loglevel)
        parameters.loglevel=self.GetLogLevel()
        self.Process.showCurrentLogLine()

#-------------------------------------------------------------------------------
    def DoLogString(self, message, timeStamp=0):
#-------------------------------------------------------------------------------
        if isinstance(message, unicode):
                message= message.encode('latin-1')

        t = time.localtime(timeStamp)
        t = "%d:%d:%d"%t[3:6]
        print t, str(message)

#-------------------------------------------------------------------------------
    def DoLog(self, level=INFOLEVEL, message="", timeStamp=0):
#-------------------------------------------------------------------------------
        """
        Override the DoLogString method
        """
        strtype={"1":"Error: ",
                 "2":"Warning: ",
                 "3":"",    #"Message"
                 "4":"",    #"Status"
                 "5":"#",    #"Verbose"
                 "6":">>>"}

        if isinstance(message, unicode):
                message= message.encode('latin-1')

        if self.GetLogLevel()==DEBUGLEVEL:
            t = time.localtime(timeStamp)
            t = "%d:%d:%d"%t[3:6]
            print t,strtype[str(level)],str(message)

        if not hasattr(self,"target"):
            return
        if not hasattr(self.target,"BeginTextColour"):
            return

##        try:
        if string.strip(repr(message))=="CLEAR":
            self.target.Clear()
            return

        if level<MESSAGELEVEL:
            self.target.BeginBold()
        if level==DEBUGLEVEL:
            self.target.BeginTextColour(wx.Colour(0, 0, 255))
        elif level==WARNINGLEVEL:
            self.target.BeginTextColour(wx.Colour(128, 0, 0))
        elif level==ERRORLEVEL:
            self.target.BeginTextColour(wx.Colour(255, 0, 0))
        else:
            self.target.BeginTextColour(wx.Colour(32,100,100))

        if level == STATUSLEVEL:
            self.target.parent.parent.SetStatusText(str(message),1)
        elif level != DEBUGLEVEL:
            self.target.AppendText(strtype[str(level)]+message+'\n')
            self.modified=True

        self.target.EndTextColour()

        if level<MESSAGELEVEL:
            self.target.EndBold()

##        except:
##            self.Flush()
##            pass

#===============================================================================
class imglist(wx.ImageList):
#===============================================================================
    def __init__(self):
        """
        Set the image list
        """
        wx.ImageList.__init__(self,16, 15)
        #wxImageList(int width, int height, const bool mask = true,
        #int initialCount = 1)
        imgpath=path.join(GetMainPath(),'images', 'icons', 'datatypes')
        imgtype={"gif":wx.BITMAP_TYPE_GIF,"png":wx.BITMAP_TYPE_PNG}
        images=os.listdir(imgpath)
        if ".svn" in images : images.remove(".svn")
        for item in images:
            image=string.split(item,'.')
            idx=wx.Bitmap(path.join(imgpath,item), imgtype[image[1]])
            setattr(self,"%sidx"%image[0],self.Add(idx,mask=wx.NullBitmap))

#===============================================================================
class TextCtrlXRC(wx.TextCtrl):
#===============================================================================
    """
    TextCtrl from XRC
    - with additional properties
    """
#-------------------------------------------------------------------------------
    def __init__(self):
#-------------------------------------------------------------------------------
        p = wx.PreTextCtrl() # the Create step is done by XRC.
        self.PostCreate(p)
        f=self.GetFont()
        f.SetDefaultEncoding(wx.FONTENCODING_ISO8859_1)
        self.SetFont(f)
        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

#-------------------------------------------------------------------------------
    def OnSetFocus(self, evt):
#-------------------------------------------------------------------------------
        self.haveFocus = True
        evt.Skip()

#-------------------------------------------------------------------------------
    def OnKillFocus(self, evt):
#-------------------------------------------------------------------------------
        self.haveFocus = False
        evt.Skip()

#===============================================================================
class TextCtrl(wx.TextCtrl):
#===============================================================================
    """
    Normal TextCtrl
    - with additional properties
    """
#-------------------------------------------------------------------------------
    def __init__(self, parent, id=-1, *args, **kwargs):
#-------------------------------------------------------------------------------
        wx.TextCtrl.__init__(self, parent, id, *args, **kwargs)
        self.parent=parent
        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

#-------------------------------------------------------------------------------
    def OnSetFocus(self, evt):
#-------------------------------------------------------------------------------
        self.haveFocus = True
        evt.Skip()

#-------------------------------------------------------------------------------
    def OnKillFocus(self, evt):
#-------------------------------------------------------------------------------
        self.haveFocus = False
        evt.Skip()

#-------------------------------------------------------------------------------
    def _getContent(self):
#-------------------------------------------------------------------------------
        return self.GetValue().encode('raw_unicode_escape')

#-------------------------------------------------------------------------------
    def _setContent(self, content):
#-------------------------------------------------------------------------------
        self.SetValue(content.decode('raw_unicode_escape'))

    Content = property(fget= _getContent, fset= _setContent)

#===============================================================================
class DialogResults:
#===============================================================================
    """
    DialogResults class.
    """

#-------------------------------------------------------------------------------
    def __init__(self, returned):
#-------------------------------------------------------------------------------
        """
            Create wrapper for results returned by dialog.
        """
        self.returned = returned
        self.positive = returned in (wx.ID_OK, wx.ID_YES)
        self.text = self._asString()

#-------------------------------------------------------------------------------
    def __repr__(self):
#-------------------------------------------------------------------------------
        return str(self.__dict__)

#-------------------------------------------------------------------------------
    def _asString(self):
#-------------------------------------------------------------------------------
        returned = self.returned
        if returned == wx.ID_OK:
            return "Ok"
        elif returned == wx.ID_CANCEL:
            return "Cancel"
        elif returned == wx.ID_YES:
            return "Yes"
        elif returned == wx.ID_NO:
            return "No"

#====================================
class InfoDialog(xrcInfoDlg):
#====================================
    #--------------------------
    def __init__(self, message):
    #--------------------------
        # Initialize the dialog
        xrcInfoDlg.__init__(self, None)
        self.Show()
        self._INFO.ChangeValue(message)


#===============================================================================
#                           Module common functions
#===============================================================================

#-------------------------------------------------------------------------------
def CreateToolbarFromMenu(  parent, tools,
                            pos= wx.DefaultPosition,
                            size = wx.DefaultSize,
                            style= wx.TB_FLAT | wx.TB_NODIVIDER):
#-------------------------------------------------------------------------------

    tb = wx.ToolBar(parent, -1, pos, size, style )
    MakeToolBar(tb, parent, tools)
    tb.Realize()
    return tb

#-------------------------------------------------------------------------------
def GetParentFrame(parent):
#-------------------------------------------------------------------------------
        frame=parent
        while 1:
            p = frame.GetParent()
            if p is not None:
                frame=p
            else:
                break
        return frame

#-------------------------------------------------------------------------------
def MakeToolBar(tb, parent, tools):
#-------------------------------------------------------------------------------
    tb.SetToolBitmapSize(wx.Size(16,16))    #this is in fact the default size

    radio=False

    for strg in tools:

        if  strg =="sep":
            tb.AddSeparator()
            radio = False

        elif strg == "radio":
            radio = True

        elif radio:
            item = getattr(parent, strg)
            radio=True
            Id = item.GetId()
            label = item.GetLabel()
            helps = item.GetHelp()
            if not item.GetBitmap(): continue
            bitmap1 = item.GetBitmap()
            bitmap2 = wx.NullBitmap
             # Create the corresponding Tool
             # (toolId, label, bitmap1, bitmap2,
             #                     shortHelpString, longHelpString, clientData)
            tb.AddRadioLabelTool(Id,
                              label,
                              bitmap1,
                              bitmap2,
                              label,
                              helps)
        else:
            item = getattr(parent, strg)
            #skip if no image ( will be only in the menu)
            if not item.GetBitmap(): continue
            Id = item.GetId()
            label = item.GetLabel()
            helps = item.GetHelp()
            bitmap1 = item.GetBitmap()
            #Create the corresponding Tool
            tb.AddLabelTool(Id,
                            label,
                            bitmap1,
                            shortHelp=label,
                            longHelp=helps)

#-------------------------------------------------------------------------------
def GetpyPulsarIcon():
#-------------------------------------------------------------------------------
    """
    Get the pyPulsar icon from a file
    """
    file=path.join(GetMainPath(), "images", "icons", "smallpypulsarlogo.gif")
    filecontent=open(file, "rb").read()
    stream = cStringIO.StringIO(filecontent)
    bitmap=wx.BitmapFromImage(wx.ImageFromStream(stream))
    icon = wx.EmptyIcon()
    icon.CopyFromBitmap(bitmap)
    return icon

#-------------------------------------------------------------------------------
def GetPath(fullpath=None, option=None):
#-------------------------------------------------------------------------------
    """
    Get the path info
    @param fullpath: File path to analyze
    @param option: Part to return (0-path, 1-filename, 2-basename, 3-extension)
    @type fullpath: String
    @type option: Optional, Integer [0-3]
    @rtype: String
    """

    filepath=None    # full path without filename
    filename=None    # filename with extension
    filebase=None    # filename without extension
    fileext=None     #filexetension
    if fullpath:
        [filepath,filename]=path.split(fullpath)
        [filebase,fileext]=path.splitext(filename)
    else:
        return None

    #handle the case of filename strating with a dot
    if not filebase:
        filebase = fileext
        fileext = ""
    if not option:
        return [filepath, filebase, fileext]
    else:
        if option==0 or option=='filepath' or option=='path':
            return filepath
        elif option==1 or option=='filename' or option=='name':
            return filename
        elif option==2 or option=='filebase' or option=='base':
            return filebase
        elif option==3 or option=='fileext'or option=='ext':
            return fileext
        else:
            raise ValueError, "option not found"

#-------------------------------------------------------------------------------
def GetMainPath():
#-------------------------------------------------------------------------------
    """
    Get the application directory path
    @return: path of the application
    """
    global apppath

    mainpath=path.split(sys.argv[0])[0]
    if mainpath=='':
        mainpath=os.getcwd()
        return mainpath

    #necessary when the main application is runned under pyScripter IDE
    try:
        if apppath: return apppath

    except:
        apppath=mainpath
        return mainpath


#-------------------------------------------------------------------------------
def PathNorm(fullpath=None):
#-------------------------------------------------------------------------------
    """
    Create normalized paths and Escape \\ characters in window paths
    @param fullpath: path to normalize
    @return: new path
    """
    if not fullpath:
        return None
    normpath=path.normpath(fullpath)
    # For path in windows,
    # several functions like os.rename doesn't work
    # if the backslash are not escaped!
    t=string.split(normpath,'\\')
    normpath=string.join(t,'\\\\')
    return normpath

#-------------------------------------------------------------------------------
def GetFilename(fullpath):
#-------------------------------------------------------------------------------
    """
    Get the path info
    @return: filename
    """
    return path.split(fullpath)[1]

#-------------------------------------------------------------------------------
def getWorkspacePath(name):
#-------------------------------------------------------------------------------
    """
    Get the Workspace pathname
    """
    if name is None:
        return
    name = GetPath(name,2)  # get only filename (but this doesnt work if filename start
    # with a dot
    return path.join(GetMainPath(),"workspace",name)

#-------------------------------------------------------------------------------
def rtn(st):
#-------------------------------------------------------------------------------
    """
    Remove trailing \\n in string read by readline()
    """
    st=st.split("\n")[0]
    st=st.split("\r")[0]
    return st

#-------------------------------------------------------------------------------
def P2F(si, sw, sr=0.0):
#-------------------------------------------------------------------------------
    """
    Calculate spectrum scale coefficients
    for point to frequency (Hz)conversions
    @param si: Number of points
    @param sw: Spectral width (Hz)
    @param sr: Spectrum reference (default = 0)
    @return: (a,b) coefficients f= a*p+ b
    @type si: Integer
    @type sw: Float
    @type sr: Float
    @rtype: Float Tuple
    """
    fst = -sw / 2.0 - sr
    wp = float(si-1)
    wf = sw
    a = wf / wp
    b = fst
    return (a, b)

#-------------------------------------------------------------------------------
def F2P(si, sw, sr=0.0):
#-------------------------------------------------------------------------------
    """
    Calculate spectrum scale coefficients
    for frequency (Hz) to point conversions
    @param si: Number of points
    @param sw: Spectral width (Hz)
    @param sr: Spectrum reference (default = 0)
    @return: (a,b) coefficients p= a*f+ b
    @type si: Integer
    @type sw: Float
    @type sr: Float
    @rtype: Float Tuple
    """
    fst = -sw / 2 - sr
    wp = float(si - 1)
    wf = sw
    a = wp / wf
    b = - a * fst
    return (a, b)

#-------------------------------------------------------------------------------
def F2T(sw):
#-------------------------------------------------------------------------------
    """
    Calculate Frequency to Time conversion
    @param sw: Spectral width (Hz)
    @type sw: Float
    @return: dwell time in µs
    @rtype: Float
    """
    try:
        dw=2.e6/sw  #Factor 2 is due to the sampling of a complex point
                    #dwell time in microsec
    except:
        dw=1.
    return dw

#-------------------------------------------------------------------------------
def MakeCode(fullpath=None, script=None, addself=True, compiled=True):
#-------------------------------------------------------------------------------
    """
    Prepare code for exec from a cfg file
    @param fullpath: Name of the file to compile (generaly *.cfg)
    @type fullpath: String
    @rtype: Code
    """

    lines=[]

    # Check if fullpath file exists
    if not path.exists(fullpath):
        fullpath=None

    if not (fullpath is None):   # Read file
        try:
            cfg = open(fullpath, "rb")
            lines=cfg.readlines()
            cfg.close()
        except:
            cfg.close()
            LOG_WARNING(fullpath,"not found",info=True)
            return None

    elif script is not None and lines==[]:   # Read script
        lines=script.splitlines()

    else:
        LOG_DEBUG("MakeCode do not know how to create a code.")
        return None

    # Create code
    text=""
    for line in lines:
        if line.find("=")>0:
            if addself:
                # add "self." if addself flag is true (default)
                text=text+"\nself."+line
        else:
            text=text+"\n"+line
    text = text.replace('\r', '\n')

    # Compile this script and return the result is it is successful
    if compiled:
        try:
            code=compile(text, '<script>', 'exec')
            return code
        except:
            LOG_WARNING("MakeCode","this code cannot be compiled!")
            return False
    else:
        return text

#-------------------------------------------------------------------------------
def messageDialog(parent=None,
                  message='',
                  title='Message box',
                  style=wx.YES_NO|wx.CANCEL|wx.CENTRE|wx.ICON_QUESTION,
                  pos=wx.DefaultPosition):
#-------------------------------------------------------------------------------
    """
    Message dialog wrapper function.
    Shows the dialog, returning one of wxID_OK, wxID_CANCEL, wxID_YES, wxID_NO.

    """
    dialog = wx.MessageDialog(parent, message, title, style, pos)
    result = DialogResults(dialog.ShowModal())
    dialog.Destroy()
    return result

#-------------------------------------------------------------------------------
def fileDialog(parent=None,
               title='Open',
               directory= GetMainPath(),
               filename='',
               wildcard='All Files (*.*)|*.*',
               style=wx.OPEN|wx.MULTIPLE):
#-------------------------------------------------------------------------------
    """
    File dialog wrapper function.
    """
    dialog = wx.FileDialog(parent, title, directory, filename,
                           wildcard, style)
    result = DialogResults(dialog.ShowModal())
    if result.positive:
        result.paths = dialog.GetPaths()
    else:
        result.paths = []
    dialog.Destroy()
    return result

#-------------------------------------------------------------------------------
def openSingle(parent=None,
               title='Open',
               directory=GetMainPath(),
               filename='',
               wildcard='pyPulsar project (*.ppp)|*.ppp',
               style=wx.OPEN):
#-------------------------------------------------------------------------------
    """
    File dialog wrapper function.
    """
    dialog = wx.FileDialog(parent, title, directory, filename,
                           wildcard, style)
    result = DialogResults(dialog.ShowModal())
    if result.positive:
        result.path = dialog.GetPath()
        result.filterindex = dialog.GetFilterIndex()
    else:
        result.path = None
    dialog.Destroy()
    return result

#-------------------------------------------------------------------------------
def saveSingle(parent=None,
               title='Save',
               directory=GetMainPath(),
               filename='',
               wildcard='pyPulsar project (*.ppp)|*.ppp|All text (*.*)|*.*',
               style=wx.SAVE|wx.HIDE_READONLY|wx.OVERWRITE_PROMPT):
#-------------------------------------------------------------------------------
    """
    File dialog wrapper function.
    """
    dialog = wx.FileDialog(parent, title, directory, filename,
                           wildcard, style)
    result = DialogResults(dialog.ShowModal())
    if result.positive:
        result.path = dialog.GetPath()
    else:
        result.path = None
    dialog.Destroy()
    return result

#-------------------------------------------------------------------------------
def directory(parent=None,
              message='Choose a directory',
              path=GetMainPath(),
              style=0,
              pos=wx.DefaultPosition,
              size=wx.DefaultSize):
#-------------------------------------------------------------------------------
    """
    Dir dialog wrapper function.
    """
    dialog = wx.DirDialog(parent, message, path, style, pos, size)
    result = DialogResults(dialog.ShowModal())
    if result.positive:
        result.path = dialog.GetPath()
    else:
        result.path = None
    dialog.Destroy()
    return result

#-------------------------------------------------------------------------------
def WRITE_LOG(level=None,strg=None):
#-------------------------------------------------------------------------------
    """
    Print a message from the FORPULSAR module
    Callback function called by Fortran
    @param level: Level of the debugging message
         "1":"Error",
         "2":"Warning",
         "3":"Message",
         "4":"Status",
         "5":"Verbose",
         "6":"Debug"
    @param strg: message to display
    @type level: int
    @type strg: string
    """
    strtype={"1":"Error",
         "2":"Warning",
         "3":"Message",
         "4":"Status",
         "5":"Verbose",
         "6":"Debug"}
    try:
        LogMethod = getattr(wx, "Log%s" % strtype[str(level)])
        LogMethod(str(strg))
    except:
        pass

#-------------------------------------------------------------------------------
def LOG_STRING(*args):
#-------------------------------------------------------------------------------
    """
    Display a message in the output panel
    @param args: parameter(s) to display
    @type args: Any
    """
    strg=""
    for s in args:
        strg+=str(s)+"\t"
    wx.LogMessage(str(strg))

#-------------------------------------------------------------------------------
def LOG_INFO(*args):
#-------------------------------------------------------------------------------
    """
    (alias of LOG_STRING)
    @param args: parameter(s) to display
    @type args: Any
    """
    strg=""
    for s in args:
        strg+=str(s)+"\t"
    wx.LogMessage(str(strg))

#-------------------------------------------------------------------------------
def LOG_STATUS(*args):
#-------------------------------------------------------------------------------
    """
    Display a message in the status bar
    @param args: parameter(s) to display (any type)
    @type args: Any
    """
    strg=""
    for s in args:
        strg+=str(s)+"\t"
    wx.LogStatus(str(strg))

#-------------------------------------------------------------------------------
def LOG_ERROR(*args, **kwargs):
#-------------------------------------------------------------------------------
    """
    Display an error message in the output panel
    @param args: parameter(s) to display (any type)
    @param kwargs: keyword parameters
    @type args: Any
    @type kwargs: ["info","parent"]

        info=True: display additionnal informations
        parent=True: display class name

    """
    strg=""
    if kwargs.has_key("info"):
        if kwargs["info"]:
            if kwargs.has_key("parent"):
                cls = kwargs["parent"].__class__.__name__
                strg=INFOS(2, cls)+"\t"
            else:
                strg=INFOS(2)+"\t"
    for s in args:
        strg+=str(s)+"\t"

    wx.LogError(str(strg))

#-------------------------------------------------------------------------------
def LOG_WARNING(*args, **kwargs):
#-------------------------------------------------------------------------------
    """
    Display a warning message in the output panel
    @param args: parameter(s) to display (any type)
    @param kwargs: keyword parameters

        info=True: display additionnal informations
        parent=True: display class name
    """
    strg=""
    if kwargs.has_key("info"):
        if kwargs["info"]:
            if kwargs.has_key("parent"):
                cls = kwargs["parent"].__class__.__name__
                strg=INFOS(2, cls)+"\t"
            else:
                strg=INFOS(2)+"\t"
    for s in args:
        strg+=str(s)+"\t"

    wx.LogWarning(str(strg))

#-------------------------------------------------------------------------------
def LOG_DEBUG(*args, **kwargs):
#-------------------------------------------------------------------------------
    """
    Display a debug message in the output panel
    @param args: parameter(s) to display (any type)
    @param kwargs: keyword parameters

        info=True: display additionnal informations
        parent=True: display class name

    """
    strg=""
    if kwargs.has_key("info"):
        if kwargs["info"]:
            if kwargs.has_key("parent"):
                cls = kwargs["parent"].__class__.__name__
                strg=INFOS(2, cls)+"\t"
            else:
                strg=INFOS(2)+"\t"
    for s in args:
        strg+=str(s)+"\t"

    wx.LogDebug(strg)

#-------------------------------------------------------------------------------
def LOG_VERBOSE(*args):
#-------------------------------------------------------------------------------
    """
    Display verbosing message in the output panel
    @param args: parameter(s) to display (any type)
    """
    strg=""
    for s in args:
        strg+=str(s)+"\t"
    wx.LogVerbose(str(strg))


#-------------------------------------------------------------------------------
def INFOS(depth=1,cls=None):
#-------------------------------------------------------------------------------
    """
    Display some information about the calling function and classes
    """
    s=""
    frame=sys._getframe(depth)
    filename=frame.f_code.co_filename
    fun=frame.f_code.co_name
    lineno=frame.f_lineno
    if cls is not None:
        cls="in class:"+cls
    else:
        cls=""
    s+=str(filename)+" -> "+cls+" method:"+str(fun)+ "(line: "+str(lineno)+")"
    return s

#-------------------------------------------------------------------------------
def rtccontent(str):
#-------------------------------------------------------------------------------
    """
    default string for the richtextctrl editor in xml format
    """
    snew = '<?xml version="1.0" encoding="UTF-8"?>'
    snew += '<richtext version="1.0.0.0" xmlns="http://www.wxwidgets.org">'
    snew += '<paragraphlayout textcolor="#000000" fontsize="10" fontstyle="90" '
    snew += 'fontweight="90" fontunderlined="0" fontface="Courier New" '
    snew += 'texteffects="0" texteffectflags="5" alignment="1" '
    snew += 'parspacingafter="10" parspacingbefore="0" linespacing="10">'
    snew += '<paragraph><text>'
    snew += str
    snew += '</text></paragraph></paragraphlayout></richtext>'
    return snew

