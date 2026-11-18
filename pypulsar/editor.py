#!/usr/bin/env python
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
import wxaddons.sized_controls as sc
import wx.richtext as rt
import common as cm
import cStringIO

#===============================================================================
class Editor(rt.RichTextCtrl):
#===============================================================================
    """
    subclass of RichTextControl to add some methods
    """
#-------------------------------------------------------------------------------
    def __init__(self,
                 parent,
                 id = wx.ID_ANY,
                 value = wx.EmptyString,
                 pos = wx.DefaultPosition,
                 size = wx.DefaultSize,
                 style = wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER|
                         wx.WANTS_CHARS|wx.TE_MULTILINE):
#-------------------------------------------------------------------------------
        try:  #TODO: find why there is sometimes an error 'RecursionGuards' here!
            rt.RichTextCtrl.__init__(self, parent, id, value, pos, size, style)
            self.normal = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL);
            self.SetFont(self.normal)
            self.parent= parent
            self.haveFocus = False
            self.EditEnabled = True
            self.SearchEnabled = True
        except:
            pass


#===============================================================================
class EditorPage(sc.SizedPanel):
#===============================================================================
    """
    subclass of RichTextControl to add some methods
    """
#------------------------------------------------------------------------------
    def __init__(self,
                 parent,
                 id = wx.ID_ANY,
                 value = wx.EmptyString,
                 pos = wx.DefaultPosition,
                 size = wx.DefaultSize,
                 style = wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER|wx.WANTS_CHARS
                 |wx.TE_MULTILINE):
#------------------------------------------------------------------------------
        sc.SizedPanel.__init__(self,parent,id)
        self.SetSizerType("vertical")
        self.editor=Editor(self,id,value,pos,size,style)
        self.editor.SetSizerProps(expand=True,proportion=1,border=
                   (["left", "right","top","bottom"], 0))
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.Bind(wx.EVT_SET_FOCUS, self.onSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.onKillFocus)
        self.Bind(wx.EVT_KEY_DOWN, self.onSetChildFocus)

        self.parent = parent

        self.isError = False

#-------------------------------------------------------------------------------
# Property isModified
#-------------------------------------------------------------------------------
    def _getModify(self):
#-------------------------------------------------------------------------------
        """
        Get modify status of the project
        """
        return self.editor.IsModified()

    isModified = property(fget = _getModify)

#-------------------------------------------------------------------------------
# Property Content
#-------------------------------------------------------------------------------
    def _getContent(self):
#------------------------------------------------------------------------------
        handler = rt.RichTextXMLHandler()
        handler.SetFlags(rt.RICHTEXT_HANDLER_INCLUDE_STYLESHEET)
        stream = cStringIO.StringIO()
        handler.SaveStream(self.editor.GetBuffer(), stream)
        return stream.getvalue()

#------------------------------------------------------------------------------
    def _setContent(self, content):
#------------------------------------------------------------------------------
        stream = cStringIO.StringIO(content)
        handler = rt.RichTextXMLHandler()
        handler.LoadStream(self.editor.GetBuffer(), stream)

    Content = property(fget = _getContent,
                       fset = _setContent,
                       doc ="Script content")

#------------------------------------------------------------------------------
    def save(self):
#------------------------------------------------------------------------------
        self.parent.save()

#------------------------------------------------------------------------------
    def setSavePoint(self):
#------------------------------------------------------------------------------
        self.editor.DiscardEdits()

#------------------------------------------------------------------------------
    def onSetFocus(self, evt):
#------------------------------------------------------------------------------
        self.editor.haveFocus = True
        #evt.Skip()

#------------------------------------------------------------------------------
    def onSetChildFocus(self, evt):
#------------------------------------------------------------------------------
        self.editor.haveFocus = True
        evt.Skip()

#------------------------------------------------------------------------------
    def onKillFocus(self, evt):
#------------------------------------------------------------------------------
        #self.SetWindowStyle(wx.NO_BORDER)
        self.editor.haveFocus = False
        evt.Skip()

#------------------------------------------------------------------------------
    def write(self,message):
#------------------------------------------------------------------------------
        self.editor.AppendText(message)


#===============================================================================
#  TEST
#===============================================================================
#-------------------------------------------------------------------------------
def runTest():
#-------------------------------------------------------------------------------
    import parentframe
    parent=parentframe.ParentFrame(None, title="Editor")
    editor=Editor(parent)
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
