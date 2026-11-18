#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      plotprinter.py
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

 Plot Printer class

"""

__docformat__="epytext"


from wx.html import HtmlEasyPrinting

#===============================
class PlotPrinter(HtmlEasyPrinting):
#===============================
    """
        Class Printer : to print Figure and Script...
    """
    #------------------------
    def __init__(self,frame):
        HtmlEasyPrinting.__init__(self)
        self.frame=frame

    #--------------------------------
    def PrintFig(self,plot,doc_name):
        gpsd=self.GetPageSetupData()
        (pw,ph)=gpsd.GetPaperSize()
        inch=25.4
        pw=pw/inch
        ph=ph/inch #in inch
        (wi,hi)=plot.fig.get_size_inches()
        #search which dimension should be taken as reference
        dpi=plot.fig.get_dpi()
        (w,h)=(dpi*wi,dpi*hi)
        if (hi*pw/wi) > pw:
            hs=dpi*ph
            ws=hs*w/h
        else:
            ws=dpi*pw
            hs=ws*h/w
        plot.canvas.print_figure("fig_tmp.png",300)
        self.SetHeader("<b>"+doc_name+"</b><hr>")
        self.PrintText("<img src='fig_tmp.png' width='"+str(ws)+"' height='"+str(hs)+"'>")
        self.SetFooter("<hr>")
