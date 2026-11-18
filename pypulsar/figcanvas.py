#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      figcanvas.py
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

"""

__docformat__="epytext"


from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
import wx
import string
import wx.lib.pubsub as pubsub

#======================================================
class FigCanvas(FigureCanvasWxAgg, NavigationToolbar2):
#======================================================
    """
    subclass Figure canvas
    """
    #--------------------------------------
    def __init__(self, parent, id, figure):
    #--------------------------------------
        FigureCanvasWxAgg.__init__(self, parent, id, figure)


        NavigationToolbar2.__init__(self, self)   #TODO: Rewrite this in a better way.
                                                  #I use this to get function
                                                  #defined in this class
                                                  # but I will not display the toolbar
                                                  # this way
        self.can_backward=False
        self.can_forward=False
        self.haveFocus = False
        self.EditEnabled = True
        self.SearchEnabled = False
        self.iszooming=False
        self.ispanning=False
        self._idle=True
        self.currentx=None
        self.currenty=None
        self.cursor=wx.CURSOR_CROSS
        self.mpl_connect('draw_event',  self.OnSetFocus)
        self.mpl_connect('button_release_event', self._release)
        self.mpl_connect('button_press_event', self._press)
        self.mpl_connect('motion_notify_event', self._motion)
        self.SetFocus()

        self._modify = False

    #--------------------
    def _init_toolbar(self):
    #--------------------
        #just bypass the creation of the toolbar this as we do not want this toolbar now
        pass

    #-------------------------
    def OnSetFocus(self, _evt):
    #-------------------------
        self.haveFocus = True

    #--------------------------
    def getContent(self):
    #--------------------------
        """
        Not Implemented
        """
        pass

    #--------------------
    def set_history_buttons(self):
    #--------------------
        if self._views._elements:
            can_backward = (self._views._pos > 0)
            can_forward = (self._views._pos < len(self._views._elements) - 1)
        else:
            can_backward=can_forward=False
        self.can_backward=can_backward
        self.can_forward=can_forward

    #--------------------
    def doReset(self):
    #--------------------
        self.home()

    #--------------------
    def home(self, *_args):
    #--------------------
        'restore the original view'
        self._views.home()
        self._positions.home()
        self._update_view()
        self._views._elements=[]
        self.set_history_buttons()
        self._update_view()

    #--------------------
    def CanUndo(self):
    #--------------------
        return self.can_backward

    #--------------------
    def CanRedo(self):
    #--------------------
        return self.can_forward

    #--------------------
    def Undo(self):
    #--------------------
        self.back()

    #--------------------
    def Redo(self):
    #--------------------
        self.forward()

    #--------------------
    def CanZoom(self):
    #--------------------
        return not (self.iszooming)

    #--------------------
    def CanPan(self):
    #--------------------
        return not (self.ispanning)

    #--------------------
    def doZoom(self, *_args):
    #--------------------
        if self.ispanning:
            self.pan(self)
            self.ispanning=False
        self.zoom(self)
        self.iszooming=not self.iszooming

    #--------------------
    def _press(self, evt):
    #--------------------
        if self.ispanning and evt.button==1: self.cursor=wx.CURSOR_HAND
        elif self.ispanning and evt.button==3: self.cursor=wx.CURSOR_SIZING
        elif self.iszooming and evt.button==1: self.cursor=wx.CURSOR_MAGNIFIER
        elif self.iszooming and evt.button==3: self.cursor=wx.CURSOR_SIZING
        #TODO: Make a custom cursor for minimizing
        else: self.SetCursor(wx.StockCursor(self.cursor))

    #--------------------
    def _release(self, _evt):
    #--------------------
        if hasattr(self,"lastrect"): del self.lastrect
        self.cursor=wx.CURSOR_ARROW
        self.SetCursor(wx.StockCursor(self.cursor))

    #--------------------
    def doPan(self, *_args):
    #--------------------
        if self.iszooming:
            self.zoom(self)
            self.iszooming=False
        self.pan(self)
        self.ispanning=not self.ispanning

    #--------------------
    def doFreeze(self):
    #--------------------
        if self.ispanning:
            self.pan(self)
            self.ispanning=False
        if self.iszooming:
            self.zoom(self)
            self.iszooming=False

    #--------------------
    def draw_rubberband(self, _evt, x0, y0, x1, y1):
    #--------------------
        'adapted from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/189744'
        canvas = self
        dc =wx.ClientDC(canvas)
        dc.SetLogicalFunction(wx.XOR)
        wbrush =wx.Brush(wx.Colour(255,255,255), wx.TRANSPARENT)
        wpen =wx.Pen(wx.Colour(0, 250, 255), 1, wx.DOT)
        dc.SetBrush(wbrush)
        dc.SetPen(wpen)
        dc.ResetBoundingBox()
        dc.BeginDrawing()
        height = self.figure.bbox.height
        y1 = height - y1
        y0 = height - y0
        if y1<y0: y0, y1 = y1, y0
        if x1<y0: x0, x1 = x1, x0
        w = x1 - x0
        h = y1 - y0
        rect = int(x0), int(y0), int(w), int(h)
        try: lastrect = self.lastrect
        except AttributeError: pass
        else: dc.DrawRectangle(*lastrect)  #erase last
        self.lastrect = rect
        dc.DrawRectangle(*rect)
        dc.EndDrawing()

    #--------------------
    def dynamic_update(self):
    #--------------------
        d = self._idle
        self._idle = False
        if d:
            self.canvas.draw()
            self._idle = True

    #--------------------------------
    def _motion(self, event):
    #--------------------------------
        """
        When mouse move, return coordinates in current units
        """
        # display the mouse position in the current units
        #-------------------------------------------------
        if event.inaxes:
            if event.button is None:
                if self.ispanning: self.cursor=wx.CURSOR_HAND
                elif self.iszooming: self.cursor=wx.CURSOR_MAGNIFIER
                else: self.cursor=wx.CURSOR_CROSS
            self.SetCursor(wx.StockCursor(self.cursor))
            self.currentx, self.currenty = event.xdata, event.ydata
        else:
            self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
            self.currentx, self.currenty = None, None

        # Send info
        #-----------
        pubsub.Publisher().sendMessage("MOTION")

#-------------------------------------------------------------------------------
    def getPosString(self):
#-------------------------------------------------------------------------------
        x = self.currentx
        if x is not None:
            sx = string.strip("%10.3f"%x)
        else:
            sx = "-"
        y = self.currenty
        if x is not None:
            sy = string.strip("%10.3f"%y)
        else:
            sy ="-"
        return (sx + " : "+ sy)

#-------------------------------------------------------------------------------
    def clearAll(self):
#-------------------------------------------------------------------------------
    #TODO: Implement Plot.clearAll()
        pass

    #-----------------------
    def setPlot(self, plot):
    #-----------------------
    #TODO: Implement Plot.setPlot()
        pass

#-------------------------------------------------------------------------------
# Property isModified
#-------------------------------------------------------------------------------
    def _getModify(self):
#-------------------------------------------------------------------------------
        """
        Get modify status of the project
        """
        #TODO: implement self.plot.GetModify()
        return self.__modify

#-------------------------------------------------------------------------------
    def _setModify(self, value):
#-------------------------------------------------------------------------------
        """
        Set modify status of the project
        """
        self.__modify = value

    isModified = property(fget = _getModify, fset = _setModify)



#StockCursor.value__ Field
#StockCursor.wxCURSOR_ARROW Field
#StockCursor.wxCURSOR_ARROWWAIT Field
#StockCursor.wxCURSOR_BLANK Field
#StockCursor.wxCURSOR_BULLSEYE Field
#StockCursor.wxCURSOR_CHAR Field
#StockCursor.wxCURSOR_CROSS Field
#StockCursor.wxCURSOR_HAND Field
#StockCursor.wxCURSOR_IBEAM Field
#StockCursor.wxCURSOR_LEFT_BUTTON Field
#StockCursor.wxCURSOR_MAGNIFIER Field
#StockCursor.wxCURSOR_MAX Field
#StockCursor.wxCURSOR_MIDDLE_BUTTON Field
#StockCursor.wxCURSOR_NONE Field
#StockCursor.wxCURSOR_NO_ENTRY Field
#StockCursor.wxCURSOR_PAINT_BRUSH Field
#StockCursor.wxCURSOR_PENCIL Field
#StockCursor.wxCURSOR_POINT_LEFT Field
#StockCursor.wxCURSOR_POINT_RIGHT Field
#StockCursor.wxCURSOR_QUESTION_ARROW Field
#StockCursor.wxCURSOR_RIGHT_ARROW Field
#StockCursor.wxCURSOR_RIGHT_BUTTON Field
#StockCursor.wxCURSOR_SIZENESW Field
#StockCursor.wxCURSOR_SIZENS Field
#StockCursor.wxCURSOR_SIZENWSE Field
#StockCursor.wxCURSOR_SIZEWE Field
#StockCursor.wxCURSOR_SIZING Field
#StockCursor.wxCURSOR_SPRAYCAN Field
#StockCursor.wxCURSOR_WAIT Field
#StockCursor.wxCURSOR_WATCH Field