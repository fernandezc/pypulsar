#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      plotcolors.py
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


import wx

#------------------------
def FromwxColourToHex(color):
#------------------------
    rgb=wx.SystemSettings.GetColour(color)
    h=hex(256*256*rgb.Red() +256*rgb.Green() + rgb.Blue())
    return str(h).replace('0x', '#')

#---------------------
def BackGroundColor():
#---------------------
    return FromwxColourToHex(wx.SYS_COLOUR_BTNFACE)

##wx.SYS_COLOUR_SCROLLBAR  The scrollbar grey area.
##wx.SYS_COLOUR_BACKGROUND  The desktop colour.
##wx.SYS_COLOUR_ACTIVECAPTION  Active window caption.
##wx.SYS_COLOUR_INACTIVECAPTION  Inactive window caption.
##wx.SYS_COLOUR_MENU  Menu background.
##wx.SYS_COLOUR_WINDOW  Window background.
##wx.SYS_COLOUR_WINDOWFRAME  Window frame.
##wx.SYS_COLOUR_MENUTEXT  Menu text.
##wx.SYS_COLOUR_WINDOWTEXT  Text in windows.
##wx.SYS_COLOUR_CAPTIONTEXT  Text in caption, size box and scrollbar arrow box.
##wx.SYS_COLOUR_ACTIVEBORDER  Active window border.
##wx.SYS_COLOUR_INACTIVEBORDER  Inactive window border.
##wx.SYS_COLOUR_APPWORKSPACE  Background colour MDI applications.
##wx.SYS_COLOUR_HIGHLIGHT  Item(s) selected in a control.
##wx.SYS_COLOUR_HIGHLIGHTTEXT  Text of item(s) selected in a control.
##wx.SYS_COLOUR_BTNFACE  Face shading on push buttons.
##wx.SYS_COLOUR_BTNSHADOW  Edge shading on push buttons.
##wx.SYS_COLOUR_GRAYTEXT  Greyed (disabled) text.
##wx.SYS_COLOUR_BTNTEXT  Text on push buttons.
##wx.SYS_COLOUR_INACTIVECAPTIONTEXT  Colour of text in active captions.
##wx.SYS_COLOUR_BTNHIGHLIGHT  Highlight colour for buttons (same as ,wx.SYS_COLOUR_3DHILIGHT).
##wx.SYS_COLOUR_3DDKSHADOW  Dark shadow for three-dimensional display elements.
##wx.SYS_COLOUR_3DLIGHT  Light colour for three-dimensional display elements.
##wx.SYS_COLOUR_INFOTEXT  Text colour for tooltip controls.
##wx.SYS_COLOUR_INFOBK  Background colour for tooltip controls.
##wx.SYS_COLOUR_DESKTOP  Same as wx.SYS_COLOUR_BACKGROUND.
##wx.SYS_COLOUR_3DFACE  Same as wx.SYS_COLOUR_BTNFACE.
##wx.SYS_COLOUR_3DSHADOW  Same as wx.SYS_COLOUR_BTNSHADOW.
##wx.SYS_COLOUR_3DHIGHLIGHT  Same as wx.SYS_COLOUR_BTNHIGHLIGHT.
##wx.SYS_COLOUR_3DHILIGHT  Same as wx.SYS_COLOUR_BTNHIGHLIGHT.
##wx.SYS_COLOUR_BTNHILIGHT  Same as wx.SYS_COLOUR_BTNHIGHLIGHT.
