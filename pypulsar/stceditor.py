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
import wxaddons.sized_controls as sc
import wx.stc as stc
import wx.richtext as rt
import keyword
import string
import re
import wx.lib.pubsub as pubsub

if 'wxMSW' in wx.PlatformInfo:
    FACES = { 'times'     : 'Times New Roman',
              'mono'      : 'Courier New',
              'helv'      : 'Arial',
              'lucida'    : 'Lucida Console',
              'other'     : 'Comic Sans MS',
              'size'      : 9,
              'lnsize'    : 8,
              'backcol'   : '#FFFFFF',
              'calltipbg' : '#FFFFB8',
              'calltipfg' : '#404040',
            }

elif 'wxGTK' in wx.PlatformInfo and 'gtk2' in wx.PlatformInfo:
    FACES = { 'times'     : 'Serif',
              'mono'      : 'Monospace',
              'helv'      : 'Sans',
              'other'     : 'new century schoolbook',
              'size'      : 10,
              'lnsize'    : 9,
              'backcol'   : '#FFFFFF',
              'calltipbg' : '#FFFFB8',
              'calltipfg' : '#404040',
            }

elif 'wxMac' in wx.PlatformInfo:
    FACES = { 'times'     : 'Lucida Grande',
              'mono'      : 'Courier New',
              'helv'      : 'Geneva',
              'other'     : 'new century schoolbook',
              'size'      : 13,
              'lnsize'    : 10,
              'backcol'   : '#FFFFFF',
              'calltipbg' : '#FFFFB8',
              'calltipfg' : '#404040',
            }

else: # GTK1, etc.
    FACES = { 'times'     : 'Times',
              'mono'      : 'Courier',
              'helv'      : 'Helvetica',
              'other'     : 'new century schoolbook',
              'size'      : 12,
              'lnsize'    : 10,
              'backcol'   : '#FFFFFF',
              'calltipbg' : '#FFFFB8',
              'calltipfg' : '#404040',
            }

#===============================================================================
class StcEditor(stc.StyledTextCtrl):
#===============================================================================
    """
    Editor based on StyledTextCtrl.
    """
    #TODO: change display according to the "kind" parameter
#-------------------------------------------------------------------------------
    def __init__(self, parent, language="python", kwlist=(),
                 id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.CLIP_CHILDREN|wx.SIMPLE_BORDER):
#-------------------------------------------------------------------------------
        """
        Create Editor instance.
        """
        stc.StyledTextCtrl.__init__(self, parent, id, pos, size, style)

        self.language=language
        self.externalkwlist=kwlist

        self._config()

        # Local events
        stc.EVT_STC_UPDATEUI(self, id, self.onUpdateUI)

        self.Bind(stc.EVT_STC_MARGINCLICK, self.onMarginClick)
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.onKeyUp)
        self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
        self.Bind(wx.EVT_SET_FOCUS, self.onSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.onKillFocus)

        self.message=None
        self.errorline=0

        self.EmptyUndoBuffer()

        # To be used with menus in top frame
        self.haveFocus = False
        self.EditEnabled = True
        self.searchEnabled = True

#-------------------------------------------------------------------------------
    def onSetFocus(self, evt):
#-------------------------------------------------------------------------------
        self.haveFocus = True
        evt.Skip()

#-------------------------------------------------------------------------------
    def onKillFocus(self, evt):
#-------------------------------------------------------------------------------
        self.haveFocus = False
        evt.Skip()

#-------------------------------------------------------------------------------
    def _config(self):
#-------------------------------------------------------------------------------
        """
        Configure shell based on user preferences.
        """
        self.SetLexer(stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, ' '.join(keyword.kwlist)+' '+' '.join(self.externalkwlist))

        # Enable folding
        self.SetProperty("fold", "1")
        self.SetProperty("tab.timmy.whinge.level", "1")

        # Set left and right margins
        self.SetMargins(2, 2)

        self.SetMarginType(1, stc.STC_MARGIN_SYMBOL)
        self.SetMarginWidth(1, 15)
        self.SetMarginSensitive(1, True)

        # Set up the numbers in the margin for margin #1
        # Reasonable value for, say, 4-5 digits using a mono font (40 pix)
        self.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(1, 40)

        # Indentation and tab stuff
        self.SetIndent(3)               # Proscribed indent size for wx
        self.SetIndentationGuides(True) # Show indent guides
        self.SetBackSpaceUnIndents(True)# Backspace unindents
        self.SetTabIndents(True)        # Tab key indents
        self.SetTabWidth(3)             # Proscribed tab size for wx
        self.SetUseTabs(False)          # Use spaces rather than tabs, or
                                        # TabTimmy will complain!
        # White space
        self.SetViewWhiteSpace(False)   # Don't view white space

        # EOL: Since we are loading/saving ourselves, and the
        # strings will always have \n's in them, set the STC to
        # edit them that way.
        self.SetEOLMode(stc.STC_EOL_LF)
        self.SetViewEOL(False)

	    # No right-edge mode indicator
        #self.SetEdgeMode(stc.STC_EDGE_LINE)

        # Setup a margin to hold fold markers
        self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 15)

        # and now set up the fold markers
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,
                          stc.STC_MARK_BOXPLUSCONNECTED, "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID,
                          stc.STC_MARK_BOXMINUSCONNECTED, "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL,
                          stc.STC_MARK_TCORNER, "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,
                          stc.STC_MARK_LCORNER, "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,
                          stc.STC_MARK_VLINE, "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDER,
                          stc.STC_MARK_BOXPLUS, "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,
                          stc.STC_MARK_BOXMINUS, "white", "black")

        self.setStyles(FACES)
        self.SetViewWhiteSpace(False)
        self.SetTabWidth(4)
        self.SetUseTabs(False)
        self.SetWrapMode(False)

        try:
            self.SetEndAtLastLine(False)
        except AttributeError:
            pass

#-------------------------------------------------------------------------------
    def setStyles(self, faces):
#-------------------------------------------------------------------------------
        """
        Configure font size, typeface and color for lexer.
        """

        # Default style
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT,
                          "face:%(mono)s,size:%(size)d,back:%(backcol)s" % \
                          faces)

        self.StyleClearAll()

        # Built in styles
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER,
                          "back:#C0C0C0,face:%(mono)s,size:%(lnsize)d" % faces)
        self.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR,
                          "face:%(mono)s" % faces)
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT,
                          "fore:#0000FF,back:#FFFF88")
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD,
                          "fore:#FF0000,back:#FFFF88")

#        self.StyleSetSpec(STC_ERR_PYTHON,
#                          "fore:#FF00F0,back:#FFFF88")

        # Python styles
        self.StyleSetSpec(stc.STC_P_DEFAULT,
                          "face:%(mono)s" % faces)
        self.StyleSetSpec(stc.STC_P_COMMENTLINE,
                          "fore:#007F00,face:%(mono)s" % faces)
        self.StyleSetSpec(stc.STC_P_NUMBER,
                          "")
        self.StyleSetSpec(stc.STC_P_STRING,
                          "fore:#7F007F,face:%(mono)s" % faces)
        self.StyleSetSpec(stc.STC_P_CHARACTER,
                          "fore:#7F007F,face:%(mono)s" % faces)
        self.StyleSetSpec(stc.STC_P_WORD,
                          "fore:#00007F,bold")
        self.StyleSetSpec(stc.STC_P_TRIPLE,
                          "fore:#7F0000")
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE,
                          "fore:#000033,back:#FFFFE8")
        self.StyleSetSpec(stc.STC_P_CLASSNAME,
                          "fore:#0000FF,bold")
        self.StyleSetSpec(stc.STC_P_DEFNAME,
                          "fore:#007F7F,bold")
        self.StyleSetSpec(stc.STC_P_OPERATOR,
                          "")
        self.StyleSetSpec(stc.STC_P_IDENTIFIER,
                          "")
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK,
                          "fore:#7F7F7F")
        self.StyleSetSpec(stc.STC_P_STRINGEOL,
                "fore:#000000,face:%(mono)s,back:#E0C0E0,eolfilled" % faces)

       # Caret color
        self.SetCaretForeground("BLUE")
        # Selection background
        self.SetSelBackground(1, '#66CCFF')

        self.SetSelBackground(True,
                    wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT))
        self.SetSelForeground(True,
                    wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))

        # Line numbers in margin
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER,
                          'fore:#000000,back:#99A9C2')
        # Highlighted brace
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT,
                          'fore:#00009D,back:#FFFF00')
        # Unmatched brace
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD,
                          'fore:#00009D,back:#FF0000')
        # Indentation guide
        self.StyleSetSpec(stc.STC_STYLE_INDENTGUIDE, "fore:#CDCDCD")

        # Python styles
        self.StyleSetSpec(stc.STC_P_DEFAULT, 'fore:#000000')
        # Comments
        self.StyleSetSpec(stc.STC_P_COMMENTLINE, 'fore:#00B000,back:#FFFFFF')
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, 'fore:#008000,back:#F0FFF0')
        # Numbers
        self.StyleSetSpec(stc.STC_P_NUMBER, 'fore:#008080')
        # Strings and characters
        self.StyleSetSpec(stc.STC_P_STRING, 'fore:#800080')
        self.StyleSetSpec(stc.STC_P_CHARACTER, 'fore:#800080')
        # Keywords
        self.StyleSetSpec(stc.STC_P_WORD, 'fore:#000080,bold')
        # Triple quotes
        self.StyleSetSpec(stc.STC_P_TRIPLE, 'fore:#800080,back:#FFFFEA')
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, 'fore:#800080,back:#FFFFEA')
        # Class names
        self.StyleSetSpec(stc.STC_P_CLASSNAME, 'fore:#0000FF,bold')
        # Function names
        self.StyleSetSpec(stc.STC_P_DEFNAME, 'fore:#008080,bold')
        # Operators
        self.StyleSetSpec(stc.STC_P_OPERATOR, 'fore:#800000,bold')
        # Identifiers. I leave this as not bold because everything seems
        # to be an identifier if it doesn't match the above criterae
        self.StyleSetSpec(stc.STC_P_IDENTIFIER, 'fore:#000000')

#-------------------------------------------------------------------------------
    def onUpdateUI(self, _event):
#-------------------------------------------------------------------------------
        """
        Check for matching braces.
        """
        # If the auto-complete window is up let it do its thing.
        if self.AutoCompActive() or self.CallTipActive():
            return
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.GetCurrentPos()
        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1)

        # Check before.
        if charBefore and chr(charBefore) in '[]{}()' \
        and styleBefore == stc.STC_P_OPERATOR:
            braceAtCaret = caretPos - 1

        # Check after.
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos)
            if charAfter and chr(charAfter) in '[]{}()' \
            and styleAfter == stc.STC_P_OPERATOR:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1  and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)

#-------------------------------------------------------------------------------
    def onMarginClick(self, evt):
#-------------------------------------------------------------------------------
        # fold and unfold as needed
        if evt.GetMargin() == 1:
            if self.message:
                end = self.GetLineEndPosition(self.errorline)
                self.CallTipShow(end, self.message)

        if evt.GetMargin() == 2:

            if self.message:
                #syntax error somewhere

                return

            if evt.GetShift() and evt.GetControl():
                self.FoldAll()
            else:
                lineClicked = self.LineFromPosition(evt.GetPosition())

                if self.GetFoldLevel(lineClicked) & stc.STC_FOLDLEVELHEADERFLAG:
                    if evt.GetShift():
                        self.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 1)
                    elif evt.GetControl():
                        if self.GetFoldExpanded(lineClicked):
                            self.SetFoldExpanded(lineClicked, False)
                            self.Expand(lineClicked, False, True, 0)
                        else:
                            self.SetFoldExpanded(lineClicked, True)
                            self.Expand(lineClicked, True, True, 100)
                    else:
                        self.ToggleFold(lineClicked)

#-------------------------------------------------------------------------------
    def foldAll(self):
#-------------------------------------------------------------------------------
        lineCount = self.GetLineCount()
        expanding = True

        # find out if we are folding or unfolding
        for lineNum in range(lineCount):
            if self.GetFoldLevel(lineNum) & stc.STC_FOLDLEVELHEADERFLAG:
                expanding = not self.GetFoldExpanded(lineNum)
                break

        lineNum = 0

        while lineNum < lineCount:
            level = self.GetFoldLevel(lineNum)
            if level & stc.STC_FOLDLEVELHEADERFLAG and \
               (level & stc.STC_FOLDLEVELNUMBERMASK) == stc.STC_FOLDLEVELBASE:

                if expanding:
                    self.SetFoldExpanded(lineNum, True)
                    lineNum = self.Expand(lineNum, True)
                    lineNum = lineNum - 1
                else:
                    lastChild = self.GetLastChild(lineNum, -1)
                    self.SetFoldExpanded(lineNum, False)

                    if lastChild > lineNum:
                        self.HideLines(lineNum+1, lastChild)

            lineNum = lineNum + 1

#-------------------------------------------------------------------------------
    def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
#-------------------------------------------------------------------------------
        lastChild = self.GetLastChild(line, level)
        line = line + 1

        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.ShowLines(line, line)
                else:
                    self.HideLines(line, line)
            else:
                if doExpand:
                    self.ShowLines(line, line)

            if level == -1:
                level = self.GetFoldLevel(line)

            if level & stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.SetFoldExpanded(line, True)
                    else:
                        self.SetFoldExpanded(line, False)

                    line = self.Expand(line, doExpand, force, visLevels-1)

                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self.Expand(line, True, force, visLevels-1)
                    else:
                        line = self.Expand(line, False, force, visLevels-1)
            else:
                line = line + 1

        return line

#-------------------------------------------------------------------------------
    def onLeftUp(self, event):
#-------------------------------------------------------------------------------
        line=self.GetCurrentLine()
        if line!=self.errorline and self.message:
            end = self.GetLineEndPosition(self.errorline)
##            self.CallTipShow(end, self.message)
##        elif self.CallTipActive():
##            self.CallTipCancel()
        event.Skip(True)
        pubsub.Publisher().sendMessage("MOTION")

#-------------------------------------------------------------------------------
    def onKeyUp(self, event):
#-------------------------------------------------------------------------------
        pubsub.Publisher().sendMessage("MOTION")

#-------------------------------------------------------------------------------
    def onKeyDown(self, event):
#-------------------------------------------------------------------------------
        line=self.GetCurrentLine()
        if line!=self.errorline and self.message:
            end = self.GetLineEndPosition(self.errorline)
##            self.CallTipShow(end, self.message)
##        elif self.CallTipActive():
##            self.CallTipCancel()
        event.Skip(True)

#        if key == 32 and event.ControlDown():
#            pos = self.GetCurrentPos()
#
#            # Tips
#            if event.ShiftDown():
#                self.CallTipSetBackground("yellow")
#                self.CallTipShow(pos, 'lots of of text: blah, blah, blah\n\n'
#                                 'show some suff, maybe parameters..\n\n'
#                                 'fubar(param1, param2)')
#            # Code completion
#            else:
#                #lst = []
#                #for x in range(50000):
#                #    lst.append('%05d' % x)
#                #st = " ".join(lst)
#                #self.AutoCompShow(0, st)
#
#                kw = keyword.kwlist[:]
#                kw.append("zzzzzz?2")
#                kw.append("aaaaa?2")
#                kw.append("__init__?3")
#                kw.append("zzaaaaa?2")
#                kw.append("zzbaaaa?2")
#                kw.append("this_is_a_longer_value")
#                #kw.append("this_is_a_much_much_much_much_much_much_much_longer_value")
#
#                kw.sort()  # Python sorts are case sensitive
#                self.AutoCompSetIgnoreCase(False)  # so this needs to match
#
#                # Images are specified with a appended "?type"
#                for i in range(len(kw)):
#                    if kw[i] in keyword.kwlist:
#                        kw[i] = kw[i] + "?1"
#
#                self.AutoCompShow(0, " ".join(kw))
#        else:
#            event.Skip()

#-------------------------------------------------------------------------------
    def canCopy(self):
#-------------------------------------------------------------------------------
        """
        Return True if text is selected and can be copied.
        """
        return self.GetSelectionStart() != self.GetSelectionEnd()

#-------------------------------------------------------------------------------
    def canCut(self):
#-------------------------------------------------------------------------------
        """
        Return True if text is selected and can be cut.
        """
        return self.canCopy() and self.canEdit()

#-------------------------------------------------------------------------------
    def canEdit(self):
#-------------------------------------------------------------------------------
        """
        Return True if editing should succeed.
        """
        return not self.GetReadOnly()

#-------------------------------------------------------------------------------
    def canPaste(self):
#-------------------------------------------------------------------------------
        """
        Return True if pasting should succeed.
        """
        return self.canEdit() # and stc.StyledTextCtrl.CanPaste(self)

#-------------------------------------------------------------------------------
    def centerPosInView(self, pos):
#-------------------------------------------------------------------------------
        """
        Given a position in the control, center the line that
        contins that position in the view.

        """
        line = self.LineFromPosition(pos)
        self.centerLineInView(line)
        self.GotoLine(line)
        self.GotoPos(pos)

#-------------------------------------------------------------------------------
    def centerLineInView(self, line):
#-------------------------------------------------------------------------------
        """
        Given a line in the control, center that line
        in the view.

        """
        nlines = self.LinesOnScreen()
        first=self.GetFirstVisibleLine()
        target = first + nlines/2
        self.LineScroll(0, line - target)

#-------------------------------------------------------------------------------
    def highlightline(self, line, offset=0, message=''):
#-------------------------------------------------------------------------------
        #reset everything first
        self.MarkerDeleteAll(0)
        self.StartStyling(0, stc.STC_INDICS_MASK)
        self.SetStyling(self.GetLength(), 0)
        self.SetLexer(stc.STC_LEX_PYTHON)
        self.CallTipCancel()
        self.Refresh()

        start = self.PositionFromLine(line)
        end = self.GetLineEndPosition(line)
        self.IndicatorSetStyle(0, stc.STC_INDIC_SQUIGGLE)
        self.IndicatorSetForeground(0, wx.RED)
        self.MarkerDefine(0, stc.STC_MARK_SHORTARROW, "#CC0000", "RED")
        self.SetLexer(stc.STC_LEX_NULL)
        self.StartStyling(start+offset, stc.STC_INDICS_MASK)
        self.SetStyling(end-start-offset, stc.STC_INDIC0_MASK)
        self.MarkerAdd(line, 0)
        self.Refresh()

        #set global variables
        self.message=message
        self.errorline=line

#-------------------------------------------------------------------------------
    def unhighlightline(self, line):
#-------------------------------------------------------------------------------
        start = self.PositionFromLine(line)
        end = self.GetLineEndPosition(line)
        self.StartStyling(start, stc.STC_INDICS_MASK)
        self.SetStyling(end-start, 0)
        self.SetLexer(stc.STC_LEX_PYTHON)
        self.MarkerDeleteAll(0)
        self.CallTipCancel()
        self.Refresh()

        #reset global variables
        self.message=None
        self.errorline=0

#-------------------------------------------------------------------------------
    def getPosString(self):
#-------------------------------------------------------------------------------
        """
        Return position
        """
        pos = self.GetCurrentPos()
        line = self.LineFromPosition(pos) + 1
        col = self.GetColumn(pos)
        stringpos = "L "+str(line)+" : C "+str(col)
        return stringpos

#-------------------------------------------------------------------------------
    def getLineAtCursor(self):
#-------------------------------------------------------------------------------
        """
        Return position
        """
        pos = self.GetCurrentPos()
        line = self.LineFromPosition(pos) + 1
        return line

#-------------------------------------------------------------------------------
    def selectLineAtCursor(self):
#-------------------------------------------------------------------------------
        """
        select a line at position
        """
        pos = self.GetCurrentPos()
        line = self.LineFromPosition(pos)
        self.GotoLine(line)
        start = self.GetCurrentPos()
        end=self.GetLineEndPosition(line)
        self.SetSelection(start,end)
        return (start,end)

        #SetTargetStart and SetTargetEnd.
#        self.SetSearchFlags(stc.STC_FIND_REGEXP)


#-------------------------------------------------------------------------------
# Property Content
#-------------------------------------------------------------------------------
    def _getContent(self):
#-------------------------------------------------------------------------------
        """
        Return contents of script text window.
        """
        content=string.strip(self.GetText())
        if content!='':
            return content
        else:
            return "# No script"

#-------------------------------------------------------------------------------
    def _setContent(self, content):
#-------------------------------------------------------------------------------
        self.SetText(content)

    Content = property(fget = _getContent,
                       fset = _setContent,
                       doc ="Editor content")


#-------------------------------------------------------------------------------
    def ToggleOvertype(self):
#-------------------------------------------------------------------------------
        over=self.GetOvertype()
        self.SetOvertype(not over)
        self.SetFocus()

#-------------------------------------------------------------------------------
    def getOvertype(self):
#-------------------------------------------------------------------------------
        """
        Return Overtype string.
        """
        if self.GetOvertype():
            mode = "Overtype"
        else:
            mode = "Insert"
        return mode

#-------------------------------------------------------------------------------
    def canComment(self):
#-------------------------------------------------------------------------------
        return True

#-------------------------------------------------------------------------------
    def canUncomment(self):
#-------------------------------------------------------------------------------
        searchstring={}
        searchstring["python"]="^\s*#"

        #check if the selection can be uncommented
        s=self.GetSelectionStart()
        e=self.GetSelectionEnd()
        linestart = self.LineFromPosition(s)
        lineend = self.LineFromPosition(e)
        text=""
        for line in range(linestart, lineend+1):
            text+=self.GetLine(line)+"\n"

        #look for comments
        sFind=searchstring[self.language]
        rFind = re.compile(sFind, re.MULTILINE)
        m = rFind.search(text)
        if m:
            return True
        else:
            return False