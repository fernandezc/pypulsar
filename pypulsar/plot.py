#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------

__docformat__="epytext"

"""
FILE INFO:
==========
 - $Name   :      plot.py
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

 Class for the pyPulsar Graphics

"""
import warnings
warnings.filterwarnings("ignore", "Module (.*) was already imported (.*)")

import wx
import matplotlib
matplotlib.use('WXagg')
from matplotlib.backends.backend_wxagg import FigureManager
from matplotlib.figure import Figure
from pylab import setp
import definitions as df
import common as cm
import types
import math
import string
import os, sys
from spectres import Spectres, Spectre
import wx.lib.pubsub as pubsub
import wxaddons.sized_controls as sc
import  wx.lib.scrolledpanel as scrolled
import processing as pg
from figcanvas import FigCanvas

#===============================================================================
class ConfigPlotPanel(scrolled.ScrolledPanel):
#===============================================================================
    """
    Plotting Configuration panel
    """
#-------------------------------------------------------------------------------
    def __init__(self, parent, id=-1, size=wx.DefaultSize, config=df.CFG):
#-------------------------------------------------------------------------------

        scrolled.ScrolledPanel.__init__(self, parent, size=size,
                                            style=wx.BORDER)

        self.SetMinSize(self.GetSize())

        pane = sc.SizedPanel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        pane.SetSizerType("form")

        keys=['Mode',
        'Show_X_Axis','X_Axis_Units','Show_X_Label','X_Offset',
        'Show_Y_Axis','Y_Axis_Units','Show_Y_Label','Y_Offset',
        'Show_Title','Title',
        'Show_Grid',
        'Show_Calculated',
        'Show_Difference',
        'Show_Baseline',
        'Sum_Components',
        'Show_Components',
        'Selected_Components',
        'Show_Legend'
        ]
        stext=(110,12)
        sctrl=(-1,20)

        # init controls from the default CFG dictionary
        # TODO: this is fast doesn't give a nice display. Change this!
        #-------------------------------------------------------------
        for key in keys:

            value=config[key]

            if key=="Mode":
                sampleList=["Standard","Series","Stacked","Intensities",
                            "Contours","Map"]
                wx.StaticText(pane, -1, key, size=stext)
                setattr(self,key, wx.ComboBox(pane, -1, str(value),
                        choices=sampleList, style= wx.CB_DROPDOWN, size=sctrl))
                getattr(self,key).SetSizerProps(expand=True,border=
                   (["top"], 2))

            elif key in ["X_Axis_Units", "Y_Axis_Units"]:
                sampleList=["Intensity","Hz","ppm","time","points"]
                wx.StaticText(pane, -1, key, size=stext)
                setattr(self,key, wx.ComboBox(pane, -1, str(value),
                        choices=sampleList, style= wx.CB_DROPDOWN, size=sctrl))
                getattr(self,key).SetSizerProps(expand=True,border=
                   (["top"], 2))

            elif key=="Selected_Components":
                sampleList=["All"]
                wx.StaticText(pane, -1, key, size=stext)
                setattr(self,key, wx.ComboBox(pane, -1,str(value),
                        choices=sampleList, style= wx.CB_DROPDOWN, size=sctrl))
                getattr(self,key).SetSelection(0)
                getattr(self,key).SetSizerProps(expand=True,border=
                   (["top"], 2))

            elif type(value) in [types.BooleanType]:
                wx.StaticText(pane, -1, key, size=stext)
                setattr(self,key, wx.CheckBox(pane, -1, " ", size=sctrl))
                getattr(self,key).SetSizerProps(expand=True,border=
                   (["top"], 2))
                getattr(self,key).SetValue(value)

            else:
                wx.StaticText(pane, -1, key, size=stext)
                setattr(self,key, wx.TextCtrl(pane, -1, str(value), size=sctrl))
                getattr(self,key).SetSizerProps(expand=True,border=
                   (["top"], 2))

        pane.Fit()

        vbox.Add(pane, 1, wx.EXPAND,5)
        self.SetSizer(vbox)
        self.SetupScrolling()
        self.Fit()

#===============================================================================
class ConfigPlotDialog(sc.SizedDialog):
#===============================================================================
    """
    Plotting configuration dialog
    """
#-------------------------------------------------------------------------------
    def __init__(self, parent, id,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 config=df.CFG):
#-------------------------------------------------------------------------------
        sc.SizedDialog.__init__(self, None, -1, "Plot Configuration Dialog",
                        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                        pos=(30,30), size=(350,500)) #wx.DefaultSize)

        self.SetMinSize(self.GetSize())

        pane = self.GetContentsPane()
        pane.SetSizerType("horizontal")

        # Create an instance of ConfigPlotPanel
        #--------------------------------------
        self.__config = config
        self.configpanel = ConfigPlotPanel(pane, -1, pane.GetSize(), config)
        self.configpanel.SetSizerProps(expand=True, proportion=1)

        # Add dialog buttons
        #-------------------
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))

        # layout
        # a little trick to make sure that you can't resize the dialog to
        # less screen space than the controls need
        self.Fit()
        self.configpanel.SetFocus()

#-------------------------------------------------------------------------------
    def getConfigData(self):
#-------------------------------------------------------------------------------
        """
        Get configuration data
        @return: the configuration dictionnary
        @rtype: dict
        """
        for key,value in self.configpanel.__dict__.iteritems():
            if value.__class__.__name__!= "PySwigObject":
                s=value.GetValue()
                if type(s) is types.UnicodeType:
                    s=str(value.GetValue())
                self.__config[key]=s
        return self.__config

#===============================================================================
class PlotPage(wx.Panel):
#===============================================================================
    """
    Notebook Page of type Plot
    """
#-------------------------------------------------------------------------------
    def __init__(self, parent, id=-1):
#-------------------------------------------------------------------------------
        wx.Panel.__init__(self,parent,id)

        # Get ParentFrame
        #----------------
        frame = cm.GetParentFrame(parent)

        # Create Toolbar
        #---------------
        self.tb = wx.ToolBar(self, id,
                                style = wx.TB_FLAT|wx.TB_NODIVIDER,size=(-1,21))
        cm.MakeToolBar(self.tb, frame, frame.ToolSpectrum)
        self.tb.Realize()

        # Create an editor instance
        #--------------------------
        #self.Freeze()
        self.editor = Plot(self,parent, id)
        self.editor.Hide()
        #self.Thaw()

        # Add these two object to a sizer
        #--------------------------------
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        sizer.Add(self.tb, 0, wx.BOTTOM, 2)
        sizer.Add(self.editor, 1, wx.EXPAND|wx.ALL, 0)
        self.SetAutoLayout(True)
        self.Fit()

        # required
        self.isError = False
        self.editor.Show()

#-------------------------------------------------------------------------------
# Property isModified
#-------------------------------------------------------------------------------
    def _getModify(self):
#-------------------------------------------------------------------------------
        """
        Get modify status of the plot
        """
        return self.editor.isModified

#-------------------------------------------------------------------------------
    def _setModify(self, value):
#-------------------------------------------------------------------------------
        """
        Set modify status of the plot
        """
        self.editor.isModified = value

    isModified = property(fget = _getModify, fset = _setModify)

#-------------------------------------------------------------------------------
# Property Content
#-------------------------------------------------------------------------------
    def _setContent(self, content):
#-------------------------------------------------------------------------------
        self.editor.Content= content
        self.tb.Update()

#-------------------------------------------------------------------------------
    def _getContent(self):
#-------------------------------------------------------------------------------
        return self.editor.Content

    Content = property(fget = _getContent, fset = _setContent,
                       doc ="Get or Set the Plot page content")

#-------------------------------------------------------------------------------
    def setSavePoint(self):
#-------------------------------------------------------------------------------
        """
        Point from where to handle the changes
        Set when the content are saved
        """
        self.isModified = False

#********************
# property PlotLines
#********************
#-------------------------------------------------------------------------------
    def _getPlotLines(self):
#-------------------------------------------------------------------------------
        """
        return the collection of x and y data
        """
        return self.editor.PlotLines

#-------------------------------------------------------------------------------
    def setPlotLines(self,lines):
#-------------------------------------------------------------------------------
        """
        update the x and y data
        """
        self.editor.PlotLines = lines


    PlotLines = property(fget = _getPlotLines, fset = setPlotLines,
                        doc= "Get or set lines in the plot")

    def Annotate(self,value):
        self.editor.Annotate(value)

#===============================================================================
class MultiPlotPage(PlotPage):
#===============================================================================
    """
    To allow special treatment of multiplot display
    (not really used up to now)
    """
#-------------------------------------------------------------------------------
    def __init__(self, parent, id=-1):
#-------------------------------------------------------------------------------
        PlotPage.__init__(self,parent,id)

#-------------------------------------------------------------------------------
# Property Content
#-------------------------------------------------------------------------------
    def _setContent(self, content):
#-------------------------------------------------------------------------------
        self.editor.Content= content

#-------------------------------------------------------------------------------
    def _getContent(self):
#-------------------------------------------------------------------------------
        return self.editor.Content

    Content = property(fget = _getContent, fset = _setContent,
                       doc ="Get or Set the MultiPlot page content")


#===============================================================================
class Plot(wx.Panel,Spectres):
#===============================================================================
    """
    Plot panel
    act also as a dictionary of spectra
    """
#-------------------------------------------------------------------------------
    def __init__(self, parent=None, fullpath=None, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.NO_BORDER,
                 axe = True, kind = None):
#-------------------------------------------------------------------------------
        wx.Panel.__init__( self, parent, id , pos, size, style)
        Spectres.__init__( self, parent = self)

        # Set the ID of this plot
        #------------------------
        self.id = id

        # Get parent
        # it may be the project Auibook or a frame (wizdataset)
        #------------------------------------------------------
        try:
            self.__parent=parent.GetParent().GetParent()  # refer to AuiBook
        except AttributeError:
            self.__parent = parent

        # say if axes must be displayed
        # No axe in the wizdataset
        #------------------------------
        self.__isAxe=axe

        # Set the colors
        #---------------
        self.__bgcolor="#EEEEDE"  #TODO: add this to the configuration panel
        self.SetBackgroundColour(self.__bgcolor)

        # Create a Figure
        #----------------
        self.__dpi=75
        self.__fig = Figure((20,20),dpi=self.__dpi, frameon = True)
        self.__canvas = FigCanvas(self, id, self.__fig)
        self.__fig.set_facecolor(self.__bgcolor)
        self.__fig.set_edgecolor(self.__bgcolor)

        # Size this objects
        #------------------
        plotSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(plotSizer)
        plotSizer.Add(self.__canvas, 1, wx.EXPAND,5)
        self.SetAutoLayout(True)

        # Prepare figure
        #---------------
        self.__fig.clear()
        (w,h)=self.__fig.get_size_inches()
        dpi=self.__fig.get_dpi()
        self.__fig.set_dpi(self.__dpi)
        self.__fig.set_size_inches((w*dpi/self.__dpi,h*dpi/self.__dpi),forward=True)

        # Create a figure manager to manage things
        #-----------------------------------------
        self.__figmgr = FigureManager(self.__canvas, 1, self)
        self.Fit()

        # some additionnal setup
        #-----------------------------------------
        if hasattr(self.__parent, "progress"):
            self.__progress=self.__parent.progress
        else:
            self.__progress=None

        if hasattr(self.__parent, "Project"):
            self.__project=self.__parent.Project
        else:
            self.__project=None

        # set a timer (used later)
        #-------------------------
        self.__timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self._onTimer)

        # privates attributes
        #---------------------
        self.__plotdata = None
        self.__modify = False
        self.__isplot = False
        self.__content = None
        self.__kind = kind #argument of Plot
        self.__isAdding = False

        # Subscribe to spectres events
        #------------------------------
        pubsub.Publisher().subscribe(self._onSpectreChanged, "SPECTRE DELETED")
        pubsub.Publisher().subscribe(self._onSpectreChanged, "SPECTRE ADDED")
        pubsub.Publisher().subscribe(self._onSpectreChanged, "CONFIG MODIFIED")

    def __del__(self):
        Spectres.__del__(self)

#-------------------------------------------------------------------------------
    def _onSpectreChanged(self, event):
#-------------------------------------------------------------------------------
        """
        Spectre Changed Event
        @param event: event.topic and event.data (not used)
        """
        # avoid event not related to this plot
        #-------------------------------------
        if not hasattr(self,"id") or (self.id != event.data.id): return
        # check attribute in order to avoid error in case of object deletion
        #-------------------------------------------------------------------
        if hasattr(self,"__timer"): self.__timer.Start(10)
        if not self.__isAdding:
            if hasattr(self,"drawSpectra"): self.drawSpectra()
        if hasattr(self,"__timer"): self.__timer.Stop()

#-------------------------------------------------------------------------------
# Property hasPlot
#-------------------------------------------------------------------------------
    def _setHasPlot(self,state=False):
#-------------------------------------------------------------------------------
        self.__isplot = state
        if self.__isplot:
            self.Show()
        else:
            self.Hide()

#-------------------------------------------------------------------------------
    def _getHasPlot(self):
#-------------------------------------------------------------------------------
        if self.__isplot:
            self.Show()
        else:
            self.Hide()

        return self.__isplot

    hasPlot = property(fget = _getHasPlot, fset = _setHasPlot, doc= "Set or Get the HasPlot flag. Show or hide spectra accordingly")

#-------------------------------------------------------------------------------
# Property isModified
#-------------------------------------------------------------------------------
    def _getModify(self):
#-------------------------------------------------------------------------------
        return self.__modify

#-------------------------------------------------------------------------------
    def _setModify(self, value):
#-------------------------------------------------------------------------------
        self.__modify = value

    isModified = property(fget = _getModify, fset = _setModify)

#-------------------------------------------------------------------------------
# Property Content
#-------------------------------------------------------------------------------
    def _getContent(self):
#-------------------------------------------------------------------------------
        return self.__content

#-------------------------------------------------------------------------------
    def _setContent(self, content):
#-------------------------------------------------------------------------------
        # Clear previous content
        #-----------------------
        self.clear()
        self.showprogress()
        if type(content) is types.DictType:
            # This is a set of spectra (also displayed in the subnodes)
            #----------------------------------------------------------
            self.__content={}
            count = len(content.keys())
            for k,v in content.iteritems():

                # avoid redrawing before end of adding plots
                if self.count < count -1:
                    self.__isAdding = True
                else:
                    self.__isAdding = False
                code=compile("content_item="+v, '<script>', 'exec')
                exec code
                self.__content[k]= content_item

                # Add the spectra to the collection
                #----------------------------------
                specs = Spectre(self.__content[k])
                if specs["kind"] in df.L_EXPS:
                    label = "Experimental"
                else:
                    label = str(specs["label"])
                self[label]=specs

        elif type(content) is types.StringType:
            # This is a single spectra
            #-------------------------
            code=compile("content="+content, '<script>', 'exec')
            exec code
            self.__content = content

            # Add the spectrum to the collection
            #-----------------------------------
            specs = Spectre(self.__content)
            if specs["kind"] in df.L_EXPS:
                label = "Experimental"
            else:
                label = str(specs["label"])
            self[label]=specs

        else:
            # Unknown content
            #----------------
            cm.LOG_WARNING("plot content of unknown type")
            self.__content = None

        try:
            self.hideprogress()
        except:
            pass

    Content = property(fget = _getContent, fset = _setContent)

#-------------------------------------------------------------------------------
    def showprogress(self):
#-------------------------------------------------------------------------------
#        self.Freeze()   #prevent redrawing
#        self.__project.Tree.Freeze()
        self.__progress.Show()
        if hasattr(self,"__timer"):
            self.__timer.Start(10)
        self.__progress.Pulse()

#-------------------------------------------------------------------------------
    def hideprogress(self):
#-------------------------------------------------------------------------------
        self.__progress.Hide()
        if hasattr(self,"__timer"):
            self.__timer.Stop()
#        self.Thaw()   #prevent redrawing
#        self.__project.Tree.Thaw()

#-------------------------------------------------------------------------------
# Public methods
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
    def clear(self):
#-------------------------------------------------------------------------------
        """
        Clear spect
        """
        self._plotArea()

#-------------------------------------------------------------------------------
    def doPlotConfig(self):
#-------------------------------------------------------------------------------
        """
        Open the plot configuration dialog
        """
        config=self.Config
        dlg=ConfigPlotDialog(self,-1,pos=(0,0),config=config.copy())
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            newconfig = dlg.getConfigData()
            if newconfig!=config:
                self.Config=newconfig
                self.isModified = True
        else:
            pass

        dlg.Destroy()

#-------------------------------------------------------------------------------
    def doBroadening(self):
#-------------------------------------------------------------------------------
        pass

#-------------------------------------------------------------------------------
    def doExport(self):
#-------------------------------------------------------------------------------
        """
        Save figure image to file
        """
        file_choices = "PNG (*.png)|*.png|" \
                       "PS (*.ps)|*.ps|" \
                       "EPS (*.eps)|*.eps|" \
                       "BMP (*.bmp)|*.bmp"

        dirname = self.__project.doc.getDirpath()
        basename = self.__project.doc.getBase()
        dlg = wx.FileDialog(self,
                            message='Export Plot Figure as...',
                            defaultDir = dirname,
                            defaultFile=basename+'.png',
                            wildcard=file_choices, style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.__canvas.print_figure(path,dpi=300)
            if (path.find(dirname) ==  0):
                path = path[len(dirname)+1:]

#-------------------------------------------------------------------------------
    def drawSpectra(self):
#-------------------------------------------------------------------------------
        """
        Plot a spectrum on the current figure
        """

        self.clear()

        # Config
        #-------
        shape = self.Shape
        size = self.count
        config = self.Config

        xoffset = float(config['X_Offset'])
        yoffset = float(config['Y_Offset'])
        if size == 1:
            offset = 0.
        else:
            offset = yoffset*self.Maxi/100.
        calcoffset = 0.

        xscale,xlabel = self.X

        lines = {}
        hasExperimental = False


        # experimental spectra present?
        #------------------------------
        for key, spectre in self.iteritems():
            kind = spectre["kind"]
            if kind in df.L_EXPS:
                hasExperimental = True
                spec = spectre["spec"]
                lines["Experimental"], = \
                self.__plotdata.plot(   xscale,
                                        spec,
                                        'k',
                                        label="Experimental")

        intensity = 1.
        if config['Show_Difference'] and size > 1 and hasExperimental:
            diffspec, sumspec, baseline, intensity = self.DiffSpec
        else:
            sumspec = self.SumSpec

        # Plot sum?
        #----------
        if config['Sum_Components'] and size > 1:
            lines["Calculated"], = \
                self.__plotdata.plot(   xscale,
                                        sumspec - calcoffset,
                                        'b',
                                        label="Calculated Sum")

        if config['Show_Difference'] and size > 1 and hasExperimental:

            lines["Difference"], = \
                self.__plotdata.plot(   xscale,
                                       diffspec - (size+1)*offset  - calcoffset,
                                        'r',
                                        label="Difference")

            if config['Show_Baseline']:
                lines["Baseline"], = \
                    self.__plotdata.plot(   xscale,
                                            baseline - calcoffset,
                                            'g',
                                            label="Baseline")

        # Iterate on all spectra
        #-----------------------
        index = 0
        expindex = 0

        for key, spectre in self.iteritems():

            kind = spectre["kind"]
            if kind in df.L_EXPS : continue

            spec = spectre["spec"]
            color = spectre["color"]
            style = spectre["style"]

            if size > 1:
                color = color+style
                label = str(key)
                index +=1
            else:
                color = 'b'
                label = "Calculated"
                index = 0

            # Mode?
            #------
            Mode=config['Mode']

            # Mode Standard 1D
            #------------------
##            config['Show_Y_Axis']=True
            if Mode=="Standard" and shape == 1:

                if config['Show_Components'] or size == 1:

                    shift = - offset*(index+1) - calcoffset
                    newspec = spec*intensity + shift

                    lines[label], = \
                        self.__plotdata.plot(   xscale,
                                                newspec,
                                                color,
                                                label = label)#[-1]


        # x axis
        self.__plotdata.set_xlim(xscale[len(xscale)-1],xscale[0])
        self.__plotdata.set_xlabel(xlabel)

        # y axis
        maxylim = self.Maxi*1.1
        minylim = self.Mini - (size+2)*offset
        self.__plotdata.set_ylim(minylim,maxylim)
        ylabel='Intensity (a.u.)'
        self.__plotdata.set_ylabel(ylabel)

        # apply some additional properties to the plot
        #---------------------------------------------
        #TODO: adjust dimension with respect to the pixel size of the graph
        if not self.__isAxe:
            # case of previewing experimental spectra
            self.__fig.subplots_adjust(left=0.0, bottom=0.0,
                                                         right=1.0, top=1.0)
            self.__plotdata.set_yticks([])
            self.__plotdata.set_yticklabels([])
            self.__plotdata.set_xticks([])
            self.__plotdata.set_xticklabels([])

        elif config['Show_Y_Axis']:
            self.__fig.subplots_adjust(left=0.10, bottom=0.10,
                                                       right=.995, top=.9)#95)
        else:
            self.__fig.subplots_adjust(left=.005, bottom=0.10,
                                                       right=.995, top=.995)
            self.__plotdata.set_yticks([])
            self.__plotdata.set_yticklabels([])

        # Title, grid and so on
        #----------------------
        if config['Show_Title']:
                                self.__plotdata.set_title(config['Title'])

        self.__plotdata.grid(config['Show_Grid'])

        if len(lines) > 1 and config['Show_Legend']:
            # create the ordered legend
            tlines = []
            tlabels = []
            self.__tkeys = tkeys = lines.keys()
            tkeys.sort()
            for k in tkeys:
                tlines.append(lines[k])
                tlabels.append(lines[k].get_label())
            self.__legend = self.__plotdata.legend(tlines,tlabels, numpoints=2)
            self.setLegendProperties()

        #update everything
        #-----------------
        self.__canvas.draw()

        # Set isModified and HasPlot flags
        #---------------------------------
        self.isModified = True
        self.hasPlot = True

        self.__lines = lines
        #self.setSelectLineProperties(4) ## TODO:use during line selection

#-------------------------------------------------------------------------------
    def setLegendProperties(self):
#-------------------------------------------------------------------------------
        leg = self.__plotdata.get_legend()
        ltext  = leg.get_texts()  # all the text.Text instance in the legend
        llines = leg.get_lines()  # all the lines.Line2D instance in the legend
        frame  = leg.get_frame()  # the patch.Rectangle instance surrounding the legend
        # see text.Text, lines.Line2D, and patches.Rectangle for more info on
        # the settable properties of lines, text, and rectangles
        setp(ltext, fontsize='smaller')    # the legend text fontsize
        setp(llines, linewidth=1)      # the legend linewidth
        frame.set_facecolor('0.98')      # set the frame face color to light gray
        leg.draw_frame(False)           # don't draw the legend frame

#-------------------------------------------------------------------------------
    def setSelectLineProperties(self,selected):
#-------------------------------------------------------------------------------
        leg = self.__plotdata.get_legend()
        llines = leg.get_lines()  # all the lines.Line2D instance in the legend
        setp(llines, linewidth=1)      # the legend linewidth
        setp(llines[selected], linewidth=1.5)      # the legend linewidth
        setp(self.__lines[self.__tkeys[selected]], linewidth=1.5)

#-------------------------------------------------------------------------------
    def GetToolBar(self):
#-------------------------------------------------------------------------------
        """
        called by Matplotlib
        """
        return None

#-------------------------------------------------------------------------------
    def _plotArea(self):
#-------------------------------------------------------------------------------
        """
        Prepare the plot areawhere to draw
        """
        self.__fig.clear()
        (w,h)=self.__fig.get_size_inches()
        dpi=self.__fig.get_dpi()
        self.__fig.set_dpi(self.__dpi)
        self.__fig.set_size_inches((w*dpi/self.__dpi,h*dpi/self.__dpi),forward=True)

        # Create the subplot area where to draw spectra
        self.__plotdata = self.__fig.add_subplot(111)
        self.hasPlot = False

#-------------------------------------------------------------------------------
    def _onTimer(self, event):
#-------------------------------------------------------------------------------
        self.__progress.Pulse()

#-------------------------------------------------------------------------------
    def _sumSpectra(self, spec, n, n1):
#-------------------------------------------------------------------------------
        #sum of the spectra
        p=[]
        for i in range (n):
            sum=complex(0.,0.)
            for j in range(n1):
                sum=sum+spec[j][i]
            p.append(sum)
        return p

#-------------------------------------------------------------------------------
    def _getPlotdata(self):
#-------------------------------------------------------------------------------
        """
        needed for external calls
        """
        return (self.__plotdata, self.__canvas)
    PlotData = property(fget = _getPlotdata)

#********************
# property PlotLines
#********************
#-------------------------------------------------------------------------------
    def _getPlotLines(self):
#-------------------------------------------------------------------------------
        """
        return the collection of x and y data
        """
        lines = {}
        for k,v in self.__lines.iteritems():
            lines[k]=(v.get_xdata(),v.get_ydata())
        return lines

#-------------------------------------------------------------------------------
    def _setPlotLines(self,lines):
#-------------------------------------------------------------------------------
        """
        update the x and y data
        """
        for k,v in lines.iteritems():
            if isinstance(v,tuple) or isinstance(v,list):
                self.__lines[k].set_xdata(v[0])
                self.__lines[k].set_ydata(v[1])
            else:
#                print "max "+k+": ",max(v)
                if self.__lines.has_key(k):
                    self.__lines[k].set_ydata(v)
                else:
                    xdata = self.__lines["Experimental"].get_xdata()
                    self.__lines[k], =self.__plotdata.plot(xdata, v,label = k)
                    self.__plotdata.set_xlim(xdata[-1],xdata[0])
                    self.__plotdata.legend()
        self.__canvas.draw()

    PlotLines = property(fget = _getPlotLines, fset = _setPlotLines,
                        doc= "Get or set lines in the plot")

#-------------------------------------------------------------------------------
    def Annotate(self,value,position=(10, -10)):
#-------------------------------------------------------------------------------
        # use negative points or pixels to specify from right, top -10, 10
        # is 10 points to the left of the right side of the axes and 10
        # points above the bottom

            if hasattr(self,"annote"):
                self.annote.set_text(value)
            else:
                self.annote = self.__plotdata.annotate(value, xy=position,
                xycoords='axes points',
                horizontalalignment='left', verticalalignment='top',
                fontsize=10)
            self.__canvas.draw()


##    TO WORK (modification marked #CF in matplotlib/cbook.py)
##             to avoid error when resizing a window
##    class maxdict(dict):
##    """
##    A dictionary with a maximum size; this doesn't override all the
##    relevant methods to contrain size, just setitem, so use with
##    caution
##    """
##    def __init__(self, maxsize):
##        dict.__init__(self)
##        self.maxsize = maxsize
##        self._killkeys = []
##    def __setitem__(self, k, v):
##        try: #CF
##            if len(self)>=self.maxsize:
##                del self[self._killkeys[0]]
##                del self._killkeys[0]
##            dict.__setitem__(self, k, v)
##            self._killkeys.append(k)
##        except:  #CF
##            pass #CF


#******************************************************************************#
# TEST
#******************************************************************************#

#-------------------------------------------------------------------------------
def runTest():
#-------------------------------------------------------------------------------
    import parentframe
    import experimental

    parent=parentframe.ParentFrame(None, title="Plot")
    parent.ToolSpectrum = ["SPECTRUM_OPTIONS","SPECTRUM_EXPORT","sep",
        "radio","SPECTRUM_FREEZE", "SPECTRUM_ZOOM", "SPECTRUM_PAN", "sep",
        "SPECTRUM_RESET","sep","SPECTRUM_BROADENING"]

    plot=PlotPage(parent)
    mainSizer=wx.BoxSizer(wx.VERTICAL)
    parent.SetSizer(mainSizer)
    mainSizer.Add(plot, 1, wx.EXPAND)
    parent.Layout()
    parent.SendSizeEvent()
    parent.Show()

    experimentalpath="P:/Catbis28/alanine/12/pdata/1/1r"
    data = experimental.readExperimental(experimentalpath)
    if data:
        # define a new spectrum
        spec = Spectre(data["spectrum"])
        plot.editor[1]=spec
    experimentalpath="P:/Catbis28/alanine/13/pdata/1/1r"
    data = experimental.readExperimental(experimentalpath)
    if data:
        # define a second spectrum
        spec = Spectre(data["spectrum"])
        plot.editor[2]=spec

if __name__ == '__main__':
#-------------------------
    import run
    #run.main([os.path.basename(sys.argv[0])])
