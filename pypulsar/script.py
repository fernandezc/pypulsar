#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      script.py
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

Script classes
"""

__docformat__="epytext"

import wx
import common as cm
import wxaddons.sized_controls as sc
import stceditor as st
import traceback
import sys
import string
import wx.lib.pubsub as pubsub

#===============================================================================
class ScriptEditorPage(sc.SizedPanel):
#===============================================================================
    """
    Script Editor Page
    """
#-------------------------------------------------------------------------------
    def __init__(self,
                 parent,
                 id=-1,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.SIMPLE_BORDER):
#-------------------------------------------------------------------------------

        # The editor can be inserted in a frame or in a notebook.
        # thus we need to determine what is the upper parent frame
        #---------------------------------------------------------
        sc.SizedPanel.__init__(self,parent,id)
        self.SetSizerType("vertical")

        # Get ParentFrame
        #----------------
        frame = cm.GetParentFrame(parent)

        # Create Toolbar
        #---------------
        self.tb = wx.ToolBar(self, -1,
                                style = wx.TB_FLAT|wx.TB_NODIVIDER,size=(-1,21))
        cm.MakeToolBar(self.tb, frame, frame.ToolEdit)
        self.tb.Realize()

        # Create Script Editor
        #---------------------
        self.editor=ScriptEditor(self,id,pos,size,style=wx.BORDER_SUNKEN)

        # place the editor and the toolbar in a sizer
        #---------------------------------------------
        self.tb.SetSizerProps(expand=False,proportion=0,border=
                   (["bottom"], 0))
        self.editor.SetSizerProps(expand=True,proportion=1,border=
                   (["left", "right","top","bottom"], 1))
        self.Fit()
        self.SetMinSize(self.GetSize())

        # define class attributes for future references
        #----------------------------------------------
        self.parent= parent
        self.frame=frame
        self.Project=frame.Project
        self.Process=frame.Process
        self.progress=frame.progress

        self.editor.line=0
        self.editor.errorline=0
        self.lastmessage=""

        # Private attributes
        self.__isCalculated = False
        self.__isSyntaxError = False
        self.__isRunError = False
        self.__isChecked = False
        self.__storetext = ""

        # Assign handlers for events
        self.Bind(wx.EVT_IDLE, self._onIdle)

#-------------------------------------------------------------------------------
    def setSavePoint(self):
#-------------------------------------------------------------------------------
        self.editor.SetSavePoint()

#-------------------------------------------------------------------------------
    def _onIdle(self, event):
#-------------------------------------------------------------------------------
        if not hasattr(self,"nidle") or self.isSyntaxError:
            self.nidle=0
        if self.nidle==0:
            if self.__storetext != self.Content:
                #cm.LOG_DEBUG("check",self.editor.position)
                self.isChecked = False
                self.isRunError = False
                self.checkSyntax()
                self.__storetext = self.Content
        self.nidle= (self.nidle+1)%500    #To slightly slow down refreshing
        event.Skip(True)

#-------------------------------------------------------------------------------
# Property Content
#-------------------------------------------------------------------------------
    def _setContent(self, content):
#-------------------------------------------------------------------------------
        self.editor.Content=content

#-------------------------------------------------------------------------------
    def _getContent(self):
#-------------------------------------------------------------------------------
        return self.editor.Content

    Content = property(fget = _getContent,
                       fset = _setContent,
                       doc ="Script content")

#-------------------------------------------------------------------------------
# Property isModified
#-------------------------------------------------------------------------------
    def _getModify(self):
#-------------------------------------------------------------------------------
        return self.editor.GetModify()

    isModified = property(fget = _getModify,
                          doc ="Script modified status")

#-------------------------------------------------------------------------------
# Property isCalculated
#-------------------------------------------------------------------------------
    def _getCalculated(self):
#-------------------------------------------------------------------------------
        if self.isModified:
            self.__isCalculated = False

        return self.__isCalculated

#-------------------------------------------------------------------------------
    def _setCalculated(self, value):
#-------------------------------------------------------------------------------
        self.__isCalculated = value

    isCalculated = property(fget = _getCalculated,
                            fset = _setCalculated,
                            doc ="Script calculated status")

#-------------------------------------------------------------------------------
# Property isSyntaxError
#-------------------------------------------------------------------------------
    def _getSyntaxError(self):
#-------------------------------------------------------------------------------
        return self.__isSyntaxError

#-------------------------------------------------------------------------------
    def _setSyntaxError(self, value):
#-------------------------------------------------------------------------------
        self.__isSyntaxError = value

    isSyntaxError = property(fget = _getSyntaxError,
                       fset = _setSyntaxError,
                       doc ="SyntaxError status")

#-------------------------------------------------------------------------------
# Property isRunError
#-------------------------------------------------------------------------------
    def _getRunError(self):
#-------------------------------------------------------------------------------
        return self.__isRunError

#-------------------------------------------------------------------------------
    def _setRunError(self, value):
#-------------------------------------------------------------------------------
        self.__isRunError = value

    isRunError = property(fget = _getRunError,
                       fset = _setRunError,
                       doc ="RunError status")

#-------------------------------------------------------------------------------
# Property isError
#-------------------------------------------------------------------------------
    def _getError(self):
#-------------------------------------------------------------------------------
        return self.__isError|self.__isSyntaxError


    isError = property(fget = _getRunError,
                       doc ="General Error status (read only)")

#-------------------------------------------------------------------------------
# Property Content
#-------------------------------------------------------------------------------
    def _setChecked(self, content):
#-------------------------------------------------------------------------------
        self.__isChecked=content

#-------------------------------------------------------------------------------
    def _getChecked(self):
#-------------------------------------------------------------------------------
        return self.__isChecked

    isChecked = property(fget = _getChecked,
                         fset = _setChecked,
                         doc ="Script content checked?")

#------------------------------------------------------------------------------
    def save(self):
#------------------------------------------------------------------------------
        if self.isError:
            result = cm.messageDialog ( title = "Error",
            message = "There is one (or more) error in this script! \n...not saved!",
                  style = wx.OK|wx.CENTRE|wx.ICON_ERROR)
            return False

        self.parent.save(self)
        return True

#-------------------------------------------------------------------------------
    def checkSyntax(self):
#-------------------------------------------------------------------------------
        """
        Check a script content
        """
        if self.isChecked:
            #already checked
            return

        self.isRunError = False
        self.isSyntaxError = False

        try:
            if self.Content:

                # check unicode error
                lines= self.Content.splitlines()
                line=0
                for linestr in lines:
                    line += 1
                    textencoded = linestr.encode('base64_codec')

                # check syntax error
                compile(self.Content, '<script>', 'exec')

                if self.editor.errorline>0:
                    self.editor.unhighlightline(self.editor.errorline-1)
                    self.editor.errorline=0

                self.Process.clearLog()

                if self.lastmessage:
                    self.Process.clearLog()
                    cm.LOG_INFO("No syntax error")
                    self.lastmessage=""

        except SyntaxError, inst:
            self.isSyntaxError = True
            # Show message
            message = inst.args[0]
            line = inst.args[1][1]
            offset = inst.args[1][2]
            linestr = inst.args[1][3]
            self.editor.errorline = line
            message = "\n"+message+" in line "+str(line)+" or above!:\n"
            if linestr is not None: message += linestr.replace('\n', '')+"\n"
            if offset is not None and offset<80:
                # avoid too long message (case of EOF error)
                message += offset*"." + "^\n"
            self.editor.highlightline(line-1,
                               0, "Line "+str(line)+" or above : "+message)
            if string.strip(message)==string.strip(self.lastmessage):
                return #the same error was already shown (don't show it!)
            #self.Process.clearLog()
            cm.LOG_ERROR(message)
            self.lastmessage=message

        except UnicodeEncodeError, inst:
            self.isSyntaxError = True
            # Show message
            message = "\nInvalid characters located in line "+str(line)
            message += linestr.encode("raw_unicode_escape")
            self.editor.highlightline(line-1, 0)
            self.editor.errorline=line

            if string.strip(message)==string.strip(self.lastmessage):
                return #the same error was already shown (don't show it!)

            self.Process.clearLog()
            cm.LOG_ERROR(message)
            self.lastmessage=message

        except:
            self.isSyntaxError=True
            # Show message
            message="\nUndefined ERROR (report this to the bug tracker):"
            tb=traceback.extract_tb(sys.exc_traceback)
            self.Process.clearLog()
            cm.LOG_ERROR(message,tb)
            self.lastmessage=message


        # set the flag to avoir repeating syntax checking
        # if there is no change in the script since last checking
        self.isChecked = True

        pubsub.Publisher().sendMessage("ERROR",self.isError)


#===============================================================================
class ScriptEditor(st.StcEditor):
#===============================================================================
    """
    Script Editor
    """
#-------------------------------------------------------------------------------
    def __init__(self,
                 parent,
                 id=-1,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.SIMPLE_BORDER):
#-------------------------------------------------------------------------------
        """
        Create Script instance.
        and the associated document
        """
        # Editor
        kwlist=("Simulation",
            "set_protonfrequency",
            "set_channel",
            "add_nucleus",
            "set_spinningspeed",
            "set_sw",
            "set_accuracy",
            "get_numberofnuclei",
            "select_observed",
            "select_nucleus",
            "Nucleus",
            "set_nsb",
            "AUTO",
            "set_spinningangle",
            "set_qfactor",
            "set_relaxation",
            "set_npts",
            "set_rfstep",
            "set_detect",
            "CENTRAL",
            "SATELLITE",
            "set_idealpulse",
            "set_pulse",
            "set_delay",
            "set_quadrupole",
            "set_chemicalshift",
            "set_lb",
            "set_gb",
            "set_concentration",
            "execute_pulsar",
            "range",
            "arange",
            "store_spectrum",
            "sum_spectra",
            "write_spectra",
            "plot_spectra",
            "save_spectra")

        kind="python"


        st.StcEditor.__init__(self, parent, kind, kwlist, id, pos, size, style)

    def __del__(self):
        pass

#===============================================================================
#  TEST
#===============================================================================
#-------------------------------------------------------------------------------
def runTest():
#-------------------------------------------------------------------------------
    from parentframe import ParentFrame
    parent=ParentFrame(None, title="Editor")
    editor=ScriptEditorPage(parent)
    mainSizer=wx.BoxSizer(wx.VERTICAL)
    parent.SetSizer(mainSizer)
    mainSizer.Add(editor, 1, wx.EXPAND)
    parent.Layout()
    parent.SendSizeEvent()
    parent.Show()

#===============================================================================
if __name__ == '__main__':

    import run
    import os.path
    import sys
    run.main([os.path.basename(sys.argv[0])])

#===============================================================================
