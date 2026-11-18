#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      regularsearch.py
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

Search utility
Inspired from http://wiki.wxpython.org/Using_Python_Regular_Expressions_with_StyledTextCtrl
"""

__docformat__="epytext"


import wx
import wx.xrc as xrc
import re
from pypulsar_xrc import xrcSearchDlg
from common import LOG_DEBUG

# The following functions are general purpose functions for regular
# expression manipulation of the contents of StyledTextCtrls using python
# regular expression syntax.
#
# They are independent of the SearchPanel gui and can be cut out and put into
# their own module or included in a utility module if desired.
#
# All changes made by these functions can be undone by the STC's undo/redo
# commands.
#
# In all the following, parameter sFind should be a regular expression object
# or of type unicode.  The sReplace parameters are expected to be of type
# unicode.  Where a unicode object is expected, on object of type string will do
# as long as it only contains ascii characters.
#

#-------------------------------------------------------------------------------
def _norm(sFind, pos, endpos, ed):
#-------------------------------------------------------------------------------

    """
    Return (text, pos, endpos) where text is a string containing the
    text from pos to endpos in ed after real values have been substituted
    for default values in these variables.

    If sFind is not of type str or unicode it is assumed to be a
    regular expression object otherwise it is compiled into a regular
    expression object.


    """
    endtext = ed.GetTextLength()

    if pos is None:
        _startSel, endSel = ed.GetSelection()
        pos = endSel

    if endpos is None:
        endpos = endtext

    if pos > endpos:
        pos, endpos = endpos, pos

    text = ed.GetTextRange(pos, endpos)

    if isinstance(sFind, (str, unicode)):
        sFind = re.compile(sFind,re.M)

    if pos == endpos:
        return '', sFind, 0, 0

    return text, sFind, pos, endpos


#-------------------------------------------------------------------------------
def Search(sFind, pos, endpos, ed):
#-------------------------------------------------------------------------------
    """
    Search for re sFind from integer pos to integer endpos in STC ed.

    sFind can be a str, unicode or regular expression object. If type
    str then it must only contain ascii data.

    Returns a tuple (match, start, end), where match is an re match
    object, start and end are positions of the found text in the
    target STC.

    """
    text, rFind, pos, endpos = _norm(sFind, pos, endpos, ed)
    m = None
    if len(text):
        m = rFind.search(text)
    if not m:
        return None, 0, 0
    uStart = pos + len(text[:m.start(0)].encode('utf8'))
    uLen = len(m.group(0).encode('utf8'))
    return m, uStart, uStart + uLen


#-------------------------------------------------------------------------------
def SearchList(sFind, pos, endpos, ed):
#-------------------------------------------------------------------------------
    """
    Search the region of STC between pos and endpos for re sFind and
    return a list of tuples representing each find.

    sFind can be a str, unicode or regular expression object. If type
    str then it must only contain ascii data.

    The returned tuples are in the form (match, start, end) where match
    is an re match object and start and end are the start and end of the
    matched region in the target STC.

    """
    text, rFind, pos, endpos = _norm(sFind, pos, endpos, ed)

    ptr = 0
    oldend = 0

    lst=[]
    if len(text) == 0:
        return lst
    for m in rFind.finditer(text):
        start, _end = m.span(0)
        ofs=len(text[oldend:start].encode('utf8'))
        newstart=ptr+ofs
        uLen=len(m.group(0).encode('utf8'))
        ptr = newstart+uLen
        oldend = start + len(m.group(0))
        lst.append((m, pos + newstart, pos + ptr))

    return lst


#-------------------------------------------------------------------------------
def ReplaceList(sReplace, lst, ed):
#-------------------------------------------------------------------------------
    """
    Takes a list of tuples as produced by SearchList and replaces the
    the region specified by the tuple with unicode string sReplace after
    re transformations.

    The list of regions must be ordered from the start of the document
    to the end with no overlapping regions. The regions are replaced
    in reverse order, (because once text is inserted all pointers following
    the insertion point will be invalid!)

    All the changes made to the STC by this method can be undone or
    redone with a single undo/redo operation on the STC.

    """
    lst = list(lst)
    lst.reverse()
    ed.BeginUndoAction()
    for m, start, end in lst:
        ed.SetTargetStart(start)
        ed.SetTargetEnd(end)
        ed.ReplaceTarget(m.expand(sReplace))
    ed.EndUndoAction()


#-------------------------------------------------------------------------------
def ReverseSearch(sFind, pos, endpos, ed):
#-------------------------------------------------------------------------------
    """
    Find all matches of re sFind in the STC (ed) region specified by
    pos and endpos and return a tuple (match, pos, endpos) for the
    LAST match.

    """
    lst = SearchList(sFind, pos, endpos, ed)
    if len(lst)<1:
        return None, 0, 0
    return lst[-1]


#-------------------------------------------------------------------------------
def ReplaceAll(sFind, sReplace, startpos, endpos, ed):
#-------------------------------------------------------------------------------
    """
    Replace all occurences of re sFind between startpos and endpos
    with re replacement expression sReplace after normal re transformations.

    """
    lst = SearchList(sFind, startpos, endpos, ed)
    ReplaceList( sReplace, lst, ed)


#-------------------------------------------------------------------------------
def SearchReplace(sFind, sReplace, pos, endpos, ed):
#-------------------------------------------------------------------------------
    """
    Search the text in an STC between integer pos and integer endpos
    for re sFind and replace the matched text with sReplace after
    re transformation.

    Returns tuple (reMatchOject, start, end) where start and end represent
    positions of the replaced text in the STC ed.

    """
    m, uStart, uEnd = Search(sFind, pos, endpos, ed)

    ed.SetTargetStart(uStart)
    ed.SetTargetEnd(uEnd)
    ed.ReplaceTarget(m.expand(sReplace))

    return m, uStart, uEnd

#
#  End of independant functions for external use
#

#===============================================================================
class SearchDialog(xrcSearchDlg):
#===============================================================================
    """
    Class to privide a way to interactivly apply Python Regular Expressions
    to an STC in such a way that other data in the control is disturbed
    as little as possible and changes can be done and undone using
    normal STC commands.

    In addition to interactive controls, methods are supplied that can
    be used by external scripts.

    """

    FROMTOP = 0
    FORWARD = 1
    BACKWARD = 2
    WRAP = 3
    INSELECTION = 4


#-------------------------------------------------------------------------------
    def __init__(self, parent):
#-------------------------------------------------------------------------------
        """
        Default constructor. Sets up the gui componets of the panel.

        lastMatchObject:
            A place to store the match object returned from a python re
            search.

        """
        xrcSearchDlg.__init__(self, parent)
        self.ID_FOUND = xrc.XRCCTRL(self, "ID_FOUND")

        self.lastMatchObject = None
        self.FindText =  self.ID_SEARCH_STRING
        self.ReplaceText =  self.ID_REPLACE_STRING
        self.directionRadioBox = self.ID_DIRECTION
        self.ed=parent
        self.FindText.SetValue(self.ed.GetSelectedText())
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Bind(wx.EVT_IDLE,self.OnIdle)
        self.Bind(wx.EVT_BUTTON,self.OnButton)

        self.sFind=""

    def OnClose(self,_event):
        self.Destroy()

    def OnIdle(self,_event):
        lastsFind=self.sFind
        self.direction = self.GetDirection()
        self.sFind = self.GetFindStr()
        self.sReplace = self.GetReplaceStr()

        self.canReplace=False
        self.canSearch=False
        if self.sFind!="":
            self.canSearch=True
        if lastsFind != self.sFind:
           self.lastMatchObject=None
           self.ID_FOUND.SetForegroundColour("#8000FF")
           self.ID_FOUND.SetLabel("INFO: You can use regular expressions\n in your search string!")
        if self.lastMatchObject and self.canSearch:
            self.canReplace=True

        self.ID_SEARCH_BUTTON.Enable(self.canSearch)
        self.ID_REPLACE_BUTTON.Enable(self.canReplace)
        self.ID_REPLACESEARCH_BUTTON.Enable(self.canReplace)
        self.ID_REPLACEALL_BUTTON.Enable(self.canReplace)


#-------------------------------------------------------------------------------
    def OnButton(self, event):
#-------------------------------------------------------------------------------
        """
        Callback function for MessageButtons.

        Initialize some variables from the gui then call a method
        to perform the operation requested by the user.
        """
        self.ed.SetFocus()
        self.ID_FOUND.SetForegroundColour("#000000")

        if event.GetId()==self.ID_SEARCH_BUTTON.GetId(): self.OnSearch()
        if event.GetId()==self.ID_REPLACE_BUTTON.GetId(): self.OnReplace()
        if event.GetId()==self.ID_REPLACESEARCH_BUTTON.GetId(): self.OnReplaceAndSearch()
        if event.GetId()==self.ID_REPLACEALL_BUTTON.GetId(): self.OnReplaceAll()

#-------------------------------------------------------------------------------
    def Alert(self,message):
#-------------------------------------------------------------------------------
        self.ID_FOUND.SetForegroundColour("#EE0000")
        self.ID_FOUND.SetLabel(message)

#-------------------------------------------------------------------------------
    def GetDirection(self):
#-------------------------------------------------------------------------------
        """
        Get the 'search direction' value from the gui component.

        """
        return self.directionRadioBox.GetSelection()


#-------------------------------------------------------------------------------
    def SetDirection(self, i):
#-------------------------------------------------------------------------------
        """
        Set value for 'search direction' gui component.

        """
        self.directionRadioBox.SetSelection(i)


#-------------------------------------------------------------------------------
    def GetFindStr(self):
#-------------------------------------------------------------------------------
        """
        Get the search string from the 'find' text box and escape
        all unicode chars, then uncescape escaped unicode chars.

        This allows a mixture of unicode charachters and escaped
        unicode charachters of the form \u00A3 to be entered in the
        imput box.

        """
        s = self.FindText.GetValue().encode('raw_unicode_escape')
        s = s.decode('raw_unicode_escape')
        return s


#-------------------------------------------------------------------------------
    def GetReplaceStr(self):
#-------------------------------------------------------------------------------
        """
        Get the replace string from the 'replace' text box and convert
        it to python internal representation.

        Unicode escapes of the form \u00A3 can be used.

        """
        s = self.ReplaceText.GetValue().encode('raw_unicode_escape')
        s = s.decode('raw_unicode_escape')
        return s


#-------------------------------------------------------------------------------
    def GetSearchRegion(self):
#-------------------------------------------------------------------------------
        """
        Returns the (start, end) of the region, in the target editor,
        to be searched.  Result depends on the state of the gui controls.

        A value of None is returned for end to  indicate that search
        should go to the end of the text in the control.

        If the search direction is FORWARD or WRAP, the search region will
        begin after any current selection or at the current cursor position
        if there is no selection.

        """
        startSel, endSel = self.ed.GetSelection()

        if self.direction == self.INSELECTION:
            return startSel, endSel

        if self.direction == self.FORWARD or self.direction == self.WRAP:

            if startSel != endSel:
                startSel = endSel

            return startSel, None

        if self.direction == self.BACKWARD:
            return 0, startSel

        if self.direction == self.FROMTOP:
                return 0, None


#-------------------------------------------------------------------------------
    def OnSearch(self):
#-------------------------------------------------------------------------------
        """
        Method invoked by 'Search' button in gui. Searches forward from
        the current position or, if text is selected, from just after the
        end of the selected text.

        """
        try:
            rFind = re.compile(self.sFind, re.M)
        except:
            self.Alert('Error in regular expression.')
            return False

        self.lastMatchObject=None

        startSel, endSel = self.GetSearchRegion()

        if self.direction == self.BACKWARD:
            m, uStart, uEnd = ReverseSearch(rFind, startSel, endSel, ed=self.ed)
            if not m:
                self.Alert('No match found')
                return

        else:

            if self.direction == self.FROMTOP:
                self.SetDirection(self.FORWARD)

            m, uStart, uEnd = Search(rFind, startSel, endSel, ed=self.ed)
            if not m:
                self.Alert('No match found')
                if not self.direction == self.WRAP:
                    return False
                #text = self.ed.GetTextRange(0,startSel)
                pos, endpos = 0, startSel
                m, uStart, uEnd = Search(rFind, pos, endpos, ed=self.ed)
                if not m:
                    self.Alert('No match found after wrapping')
                    return

        self.lastMatchObject=m
        self.ed.centerPosInView(uStart)
        self.ed.SetSelection(uStart, uEnd)


#-------------------------------------------------------------------------------
    def OnReplace(self):
#-------------------------------------------------------------------------------
        """
        Method invoked by 'Replace' button in gui.

        Replaces the text found by a previous press of the search buton
        with the contents of the sReplace text box after re substitutions.

        """
        startSel, endSel = self.ed.GetSelection()
        if startSel == endSel:
            self.Alert('Can\'t replace text -non selected')
            return
        m = self.lastMatchObject
        if m is None:
            self.Alert('Can\'t replace text!\nDo a search first')
            return
        selectedText=self.ed.GetSelectedText()
        matchedText = m.group(0)
        if matchedText != selectedText:
            self.lastMatchObject = None
            self.Alert('Can\'t replace text.\nSelected text does not match last found text ')
            return
        newText = m.expand(self.sReplace)
        self.ed.ReplaceSelection(newText)
        self.lastMatchObject = None


#-------------------------------------------------------------------------------
    def OnReplaceAndSearch(self):
#-------------------------------------------------------------------------------
        """
        Method invoked by 'Replace & Search' button in gui.

        Equivelent of pressing the Search button followed by
        pressing the Replace button.

        """
        self.OnReplace()
        self.OnSearch()


#-------------------------------------------------------------------------------
    def OnReplaceAll(self):
#-------------------------------------------------------------------------------
        """
        Method invoked by 'Replace All' button in gui.

        Replaces all text matched by sFind with sReplace after re
        substitutions.  Operates on the entire text or on the selected
        text if the 'in selection' option is set.

        """
        lst = self.OnList(log=False)
        ReplaceList(self.sReplace, lst, ed=self.ed)
        self.Alert('Made %s replacements'%len(lst))


#-------------------------------------------------------------------------------
    def OnCount(self):
#-------------------------------------------------------------------------------
        """
        Method invoked by 'Count' button in gui.

        Counts the number of matches for sFind in the entire text, or in
        the selected text if the 'in selection' option is set.

        """
        _startSel=self.GetSearchRegion()
        count = len(self.OnList(log=False))
        self.Alert('Found search string %s times.'%count)


#-------------------------------------------------------------------------------
    def OnList(self, log=True):
#-------------------------------------------------------------------------------
        """
        Method invoked by 'List' button in gui.

        Creates a list of matches and prints a list of line numbers
        and found strings. The search is done either on the entire text
        or on the selected text if the 'in selection' option is active.

        """
        try:
            rFind = re.compile(self.sFind, re.M)
        except:
            self.Alert('Error in regular expression.')
            return []

        dir = self.GetDirection()
        if dir == self.INSELECTION:
            startSel, endSel = self.GetSearchRegion()
        else:
            startSel, endSel = 0, None

        lst = SearchList(rFind, startSel, endSel, ed=self.ed)

        if log:
            for _m, uStart, uEnd in lst:
                LOG_INFO( '%s: %r'%(self.ed.LineFromPosition(uStart),
                        self.ed.GetTextRange(uStart,uEnd)))

            self.Alert('List Search found %s matches.\n\nResults were printed on the console.'%len(lst))

        return lst

#-------------------------------------------------------------------------------
    def OnUnknownSignal(self):
#-------------------------------------------------------------------------------
        pass
