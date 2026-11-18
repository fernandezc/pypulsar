#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      specselect.py
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


from common import *
import wx.gizmos as gizmos

def create(parent):
    return DlgSpecSelect(parent)

[wxID_DLGSPECSELECT, wxID_DLGSPECSELECTAPPLY, wxID_DLGSPECSELECTCLOSE,
 wxID_DLGSPECSELECTRESET, wxID_DLGSPECSELECTSELECTION,
] = [wx.NewId() for _init_ctrls in range(5)]

class DlgSpecSelect(wx.Dialog):
    def _init_coll_Selection_Columns(self, parent):
        # generated method, don't edit

        parent.AddColumn(text='selected')
        parent.AddColumn(text='Informations')
        parent.AddColumn(text='Color')

    def _init_ctrls(self, prnt):
        # generated method, don't edit
        wx.Dialog.__init__(self, id=wxID_DLGSPECSELECT, name='DlgSpecSelect',
              parent=prnt, pos=wx.Point(817, 170), size=wx.Size(287, 490),
              style=wx.DEFAULT_DIALOG_STYLE, title='Spectra selections')
        self.SetClientSize(wx.Size(279, 456))
        self.SetIcon(wx.Icon(os.path.join(GetMainPath(),'images','pypulsar.ico'),
              wx.BITMAP_TYPE_ICO))
        self.SetToolTipString('Spectra selection dialog')

        self.Selection = gizmos.TreeListCtrl(id=wxID_DLGSPECSELECTSELECTION,
              name='Selection', parent=self, pos=wx.Point(8, 8),
              size=wx.Size(264, 416), style=wx.TR_HAS_BUTTONS)
        self.Selection.SetToolTipString('Spectrum selection list')
        self.Selection.SetMainColumn(2)
        self.Selection.SetLabel('Select spectra')
        self._init_coll_Selection_Columns(self.Selection)

        self.Close = wx.Button(id=wxID_DLGSPECSELECTCLOSE, label='Close',
              name='Close', parent=self, pos=wx.Point(200, 432),
              size=wx.Size(75, 23), style=0)

        self.Apply = wx.Button(id=wxID_DLGSPECSELECTAPPLY, label='Apply',
              name='Apply', parent=self, pos=wx.Point(120, 432),
              size=wx.Size(75, 23), style=0)

        self.REset = wx.Button(id=wxID_DLGSPECSELECTRESET,
              label='Reset default', name='REset', parent=self, pos=wx.Point(40,
              432), size=wx.Size(75, 23), style=0)

    def __init__(self, parent):
        self._init_ctrls(parent)
