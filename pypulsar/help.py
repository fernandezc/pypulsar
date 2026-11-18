#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      help.py
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
 Help Classes
"""

__docformat__="epytext"


import wx
import wx.html as wxhtml
if wx.Platform == '__WXMSW__':
    import wx.lib.iewin as iewin  #ActiveX IEtml

#==============================
class HelpAbout(wx.Dialog):
#==============================
    """
    An about box that uses an HTML window
    """

    #--------------------------
    def __init__(self, parent):
    #--------------------------
        """
        Create an instance of pyPulsarAbout
        """
        wx.Dialog.__init__(self, parent, -1, 'About pyPulsar',
                          size=(600, 400))

        html = wxhtml.HtmlWindow(self, -1)
        html.LoadPage("README.html")
        button = wx.Button(self, wx.ID_OK, "Ok")

        # constraints for the html window
        lc = wx.LayoutConstraints()
        lc.top.SameAs(self, wx.Top, 5)
        lc.left.SameAs(self, wx.Left, 5)
        lc.bottom.SameAs(button, wx.Top, 5)
        lc.right.SameAs(self, wx.Right, 5)
        html.SetConstraints(lc)

        # constraints for the button
        lc = wx.LayoutConstraints()
        lc.bottom.SameAs(self, wx.Bottom, 5)
        lc.centreX.SameAs(self, wx.CentreX)
        lc.width.AsIs()
        lc.height.AsIs()
        button.SetConstraints(lc)

        self.SetAutoLayout(True)
        self.Layout()
        self.CentreOnParent(wx.BOTH)

#============================
class HelpDoc(wx.Dialog):
#============================
    """
    An about box
    """

    #--------------------------
    def __init__(self, parent):
    #--------------------------
        """
        Create an instance of pyPulsarDoc
        (because it uses IEHtmlWindow, it works only for Microsoft windows)
        """
        wx.Dialog.__init__(self, parent, -1, 'Loading ONLINE documentation...be patient',
                          size=(999, 640))

        self.html = iewin.IEHtmlWindow(self, -1) #, style = wx.NO_FULL_REPAINT_ON_RESIZE)
        self.html.LoadUrl("http://www-lcs.ensicaen.fr/pyPulsar/index.php/Documentation")

        self.Bind(iewin.EVT_DocumentComplete, self.OnDocumentComplete, self.html)

        # constraints for the html window
        lc = wx.LayoutConstraints()
        lc.top.SameAs(self, wx.Top, 5)
        lc.left.SameAs(self, wx.Left, 5)
        lc.bottom.SameAs(self, wx.Bottom, 5)
        lc.right.SameAs(self, wx.Right, 5)
        self.html.SetConstraints(lc)

        self.SetAutoLayout(True)
        self.Layout()
        self.CentreOnParent(wx.BOTH)

    #-----------------------------------
    def OnDocumentComplete(self, event):
    #-----------------------------------
        """
        Event OnDocumentComplete :Set the dialog title
        """
        if event.URL!="about:blank":
          self.SetTitle("ONLINE Documentation:"+event.URL)


