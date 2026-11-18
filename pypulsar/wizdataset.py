#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      wizdataset.py
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

 This file implement a class "WizdatasetNew" to open or create new dataset

"""

__docformat__="epytext"

import wx
import wx.xrc as xrc
import os
import sys
import string
from definitions import *
from pypulsar_xrc import xrcdataset_Page_1, xrcdataset_Page_2
from wx.wizard import Wizard, PyWizardPage, \
                      EVT_WIZARD_PAGE_CHANGED, EVT_WIZARD_PAGE_CHANGING, \
                      EVT_WIZARD_CANCEL, EVT_WIZARD_FINISHED
import common as cm
import experimental
import plot
from spectres import Spectres, Spectre

#===============================
class DatasetPage(PyWizardPage):
#===============================
    #--------------------------
    def __init__(self, parent):
    #--------------------------
        PyWizardPage.__init__(self, parent)
        self.next = self.prev = None

        self.panel=xrcdataset_Page_1(self)
        self.panel.ID_EXPERIMENTALPREVIEW = xrc.XRCCTRL(self.panel,
                                                       "ID_EXPERIMENTALPREVIEW")
        self.panel.ID_EXPERIMENTALPREVIEW = xrc.XRCCTRL(self.panel,
                                                       "ID_EXPERIMENTALPREVIEW")
        self.panel.ID_EXPERIMENTALLABEL1 = xrc.XRCCTRL(self.panel,
                                                        "ID_EXPERIMENTALLABEL1")
        self.panel.ID_EXPERIMENTALLABEL2 = xrc.XRCCTRL(self.panel,
                                                        "ID_EXPERIMENTALLABEL2")
        self.panel.ID_EXPERIMENTALLABEL3 = xrc.XRCCTRL(self.panel,
                                                        "ID_EXPERIMENTALLABEL3")

        panelsizer = wx.BoxSizer(wx.VERTICAL)
        panelsizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(panelsizer)

        self.plot = plot.Plot(self.panel.ID_EXPERIMENTALPREVIEW,axe=False)
        plotsizer = wx.BoxSizer(wx.VERTICAL)
        plotsizer.Add(self.plot, 1, wx.EXPAND)
        self.panel.ID_EXPERIMENTALPREVIEW.SetSizer(plotsizer)
        self.plot.ShowAxisY=False
        self.plot.ShowTitle=False
        self.updatebackground=None

        # Init values
        self.panel.ID_DATASETNAME.SetValue("~untitled")
        self.panel.ID_DATASETTYPE.SetValue(False)
        self.panel.ID_PREVIEW.SetValue(False)
        self.panel.ID_DATASETDESCRIPTION.SetValue("")
        self.panel.ID_EXPERIMENTALFORMAT.SetSelection(0)
        self.panel.ID_EXPERIMENTALTYPE.SetSelection(0)
        self.panel.ID_EXPERIMENTALDIR.SetValue(self.readLastExpDir())
        self.panel.ID_EXPERIMENTALNAME.SetValue("")
        self.typeselected=0

        # Init List
        self.Tree= self.panel.ID_EXPERIMENTALFILELIST

        il = wx.ImageList(16,15)
        img1=wx.Bitmap(os.path.join(cm.GetMainPath(), 'images','icons',
                                              'spec1D.gif'), wx.BITMAP_TYPE_GIF)
        img2=wx.Bitmap(os.path.join(cm.GetMainPath(), 'images','icons',
                                              'spec2D.gif'), wx.BITMAP_TYPE_GIF)
        img3=wx.Bitmap(os.path.join(cm.GetMainPath(), 'images', 'icons',
                                                 'dir.gif'), wx.BITMAP_TYPE_GIF)
        img3o=wx.Bitmap(os.path.join(cm.GetMainPath(), 'images', 'icons',
                                           'diropened.gif'), wx.BITMAP_TYPE_GIF)
        img4=wx.Bitmap(os.path.join(cm.GetMainPath(), 'images', 'icons',
                                             'warning.gif'), wx.BITMAP_TYPE_GIF)

        self.spec1Didx = il.Add(bitmap=img1, mask=wx.NullBitmap)
        self.spec2Didx = il.Add(bitmap=img2, mask=wx.NullBitmap)
        self.diridx = il.Add(bitmap=img3, mask=wx.NullBitmap)
        self.diropenedidx = il.Add(bitmap=img3o, mask=wx.NullBitmap)
        self.warningidx = il.Add(bitmap=img4, mask=wx.NullBitmap)
        self.Tree.AssignImageList(il)

        #events
        self.Bind(wx.EVT_RADIOBOX, self.formatSelect,self.panel.ID_EXPERIMENTALFORMAT)
        self.Bind(wx.EVT_RADIOBOX, self.typeSelect,self.panel.ID_EXPERIMENTALTYPE)
        self.Bind(wx.EVT_CHECKBOX, self.datasetTypeSelect,self.panel.ID_DATASETTYPE)
        self.Bind(wx.EVT_CHECKBOX, self.onPreview,self.panel.ID_PREVIEW)
        self.Bind(wx.EVT_BUTTON, self.onBrowse,self.panel.ID_BROWSE)
        self.Bind(wx.EVT_BUTTON, self.updateDir,self.panel.ID_REFRESH)
        self.Bind(wx.EVT_TEXT, self.updateDir,self.panel.ID_EXPERIMENTALDIR)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onSelChanged)

        self.datasetTypeSelect()

        #full experimental path
        self.fullpath=None

    #-----------------------------
    def datasetTypeSelect(self,evt=None):
    #-----------------------------
        state=(self.panel.ID_DATASETTYPE.GetValue()==1)
        preview=(self.panel.ID_PREVIEW.GetValue()==1)
        self.panel.ID_EXPERIMENTALFORMAT.Enable(state)
        self.panel.ID_EXPERIMENTALTYPE.Enable(state)
        self.panel.ID_BROWSE.Enable(state)
        self.panel.ID_REFRESH.Enable(state)
        self.panel.ID_EXPERIMENTALFILELIST.Enable(state)
        self.panel.ID_EXPERIMENTALPREVIEW.Enable(preview)
        self.panel.ID_EXPERIMENTALDIR.Enable(state)
        self.panel.ID_EXPERIMENTALNAME.Enable(state)
        self.panel.ID_EXPERIMENTALLABEL1.Enable(state)
        self.panel.ID_EXPERIMENTALLABEL2.Enable(state)
        self.panel.ID_EXPERIMENTALLABEL3.Enable(state)
        self.panel.ID_PREVIEW.Enable(state)
        if state: self.updateDir()

    #-------------------------
    def updateDir(self,evt=None):
    #-------------------------
        rootdir=self.panel.ID_EXPERIMENTALDIR.GetValue()
        rootdirfilename=cm.GetPath(rootdir,"filename")

        if rootdirfilename=="":
            rootdirfilename=os.sep

        self.Tree.DeleteAllItems()
        # set the invisible root node
        try:
            self.root = self.Tree.AddRoot(rootdirfilename)
            self.specWalk(rootdir,self.root)
        except:
            cm.LOG_WARNING(rootdirfilename,"doesn't exist!")


    #---------------------------------
    def specWalk(self,rootdir,parent):
    #---------------------------------
        img={"1r":self.spec1Didx,"2rr":self.spec2Didx}
        folder={}
        sl=['1r','2rr']
        if self.typeselected>0:
            sl=sl[self.typeselected-1]

        self.dlgprogress = wx.ProgressDialog("Refreshing the spectra list",
                       "...wait...",
                       maximum = 200,
                       parent=self)
        count=1

        for root, dirs, files in os.walk(rootdir):

            if ".svn" in dirs:
                dirs.remove(".svn")

            if  (('1r' in files) or
                ('1i' in files) or
                ('2rr' in files) or
                ('2ri' in files) or
                ('2ir' in files) or
                ('2ii' in files)):

                for name in files:
                    if name in sl:
                        s=fullpath=os.path.join(root, name) # fullpath
                        q=self.calculatePathElements(s)
                        #Set a node for the exeriment folder
                        #q[1] contains the name of the experiment
                        #q[2] contains the number of the experiment
                        #q[4] contains the processing number
                        try:
                            if not folder.has_key(q[0]+"_"):
                                folder[q[0]+"_"] = self.Tree.AppendItem(parent,
                                                                           q[0])
                                self.Tree.SetItemImage(folder[q[0]+"_"],
                                            self.diridx, wx.TreeItemIcon_Normal)
                                self.Tree.SetItemImage(folder[q[0]+"_"],
                                    self.diropenedidx, wx.TreeItemIcon_Expanded)
                                self.Tree.SetPyData(folder[q[0]+"_"], ("",""))
                        except:
                            return

                        if not folder.has_key(q[0]+q[1]):
                            folder[q[0]+q[1]] = self.Tree.AppendItem(
                                                          folder[q[0]+"_"],q[1])
                            self.Tree.SetItemImage(folder[q[0]+q[1]],
                                            self.diridx, wx.TreeItemIcon_Normal)
                            self.Tree.SetItemImage(folder[q[0]+q[1]],
                                    self.diropenedidx, wx.TreeItemIcon_Expanded)
                            self.Tree.EnsureVisible(folder[q[0]+q[1]])
                            self.Tree.SetPyData(folder[q[0]+q[1]], ("",""))
                        text=q[1]+"-"+q[2]+"-"+q[4]
                        child = self.Tree.AppendItem(folder[q[0]+q[1]], text)
                        self.Tree.SetItemImage(child, img[name],
                                                         wx.TreeItemIcon_Normal)
                        #Get the associated title if any
                        title=os.path.join(cm.GetPath(fullpath,"path"),"title")
                        description=""
                        if os.path.exists(title):
                            f=open(title)
                            lines=f.readlines()
                            f.close()
                            for line in lines:
                                description+=str(line)
                        self.Tree.SetPyData(child, (fullpath,description))

                        count += 1
                        if count>200:count=1
                        self.dlgprogress.Update(count)

        #remove the progress dialog
        self.dlgprogress.Destroy()

    #--------------------------------------------
    def calculatePathElements(self,s):
    #--------------------------------------------
        q= s.split(os.sep)         # split path component
        # For bruker file the directory structure must be
        if 'pdata' in q:
            i=q.index('pdata')
            q=q[i-3:]
            return q
        else:
            return None
    #-----------------------------
    def readLastExpDir(self):
    #-----------------------------
        f=None
        try:
            lastexpdir=os.path.join(cm.GetMainPath(),'workspace','.lastexpdir')
            f=open(lastexpdir,'rb')
            filedir= os.path.normpath(f.readline())
            f.close()
        except:
            if f:
                f.close()
            filedir=''
        return filedir

    #----------------------
    def onBrowse(self,evt):
    #----------------------
        filedir = self.readLastExpDir()
        result = cm.directory(parent=self,path=filedir)
                 #(directory=filedir,wildcard=wildcard)
        if result.path:
            self.panel.ID_EXPERIMENTALDIR.SetValue(result.path)
            newexpdir=os.path.join(cm.GetMainPath(),'workspace','.lastexpdir')
            f=open(newexpdir,"wb")
            f.write(result.path)
            f.close()
        cancel = False
        return cancel

    #--------------------------
    def formatSelect(self,evt):
    #--------------------------
        strg=evt.GetString()
        if strg=="Varian":
            cm.messageDialog ( None,'Not yet implemented','Sorry',
                            style = wx.ICON_EXCLAMATION|wx.OK )
            self.panel.ID_EXPERIMENTALFORMAT.SetSelection(0)
            self.panel.ID_EXPERIMENTALFORMAT.ShowItem(1,False)

    #--------------------------
    def typeSelect(self,evt):
    #--------------------------
        self.typeselected=evt.GetSelection()
        self.updateDir()

    #--------------------------------
    def onSelChanged(self, evt=None):
    #--------------------------------
        self.plot.clear()
        try:
            item=self.Tree.GetSelection()
            kind=None
            kind=self.Tree.GetItemImage(item,wx.TreeItemIcon_Normal)
        except:
            # case where preview is selected but no selected item in the tree
            self.plot.hasPlot = False
            return

        if kind is not None and kind<=1: #1D or 2D spectrum
            name=self.Tree.GetItemText(item)
            fullpath=self.Tree.GetPyData(item)[0]
            reducepath=fullpath.split(self.panel.ID_EXPERIMENTALDIR.GetValue())[1]
            self.panel.ID_EXPERIMENTALNAME.SetValue(reducepath)
            self.panel.ID_DATASETNAME.SetValue(name)
            description=self.Tree.GetPyData(item)[1]
            self.panel.ID_DATASETDESCRIPTION.SetValue(description)

            for key in self.plot.keys():
                del self.plot[key]

            if self.panel.ID_PREVIEW.IsChecked():
                data = self.readExperimental()
                specexp = Spectre(data["spectra"][0])
                self.plot["experimental"]=specexp
                self.plot.hasPlot = True
                self.plot.drawSpectra()

    #------------------------
    def onPreview(self, evt):
    #------------------------
        if not self.panel.ID_PREVIEW.IsChecked():
            self.plot.hasPlot = False
        else:
            self.onSelChanged()
            self.plot.hasPlot = True

    #--------------------------
    def readExperimental(self):
    #--------------------------
        """
        Read experimental spectra and parameters
        and convert them to the pypulsar format
        """
##        if self.plot.has_key("experimental"):
##            del self.plot["experimental"]
        data=None
        state=(self.panel.ID_DATASETTYPE.GetValue()==1)
        if not state: return None
        dir=self.panel.ID_EXPERIMENTALDIR.GetValue()
        name=self.panel.ID_EXPERIMENTALNAME.GetValue()
        experimentalpath=dir+name
        data = experimental.readExperimental(experimentalpath)
        if data:
            return data
        else:
            cm.LOG_WARNING("Experimental data not read!")
            return None

    #-----------------------
    def SetNext(self, next):
    #-----------------------
        self.next = next

    #-----------------------
    def SetPrev(self, prev):
    #-----------------------
        self.prev = prev

    #-----------------
    def GetNext(self):
    #-----------------
        return self.next

    #-----------------
    def GetPrev(self):
    #-----------------
        return self.prev

#==============================
class ScriptPage(PyWizardPage):
#==============================
    #--------------------------
    def __init__(self, parent):
    #--------------------------
        PyWizardPage.__init__(self, parent)
        self.next = self.prev = None
        self.parent = parent

        self.panel=xrcdataset_Page_2(self)

        self.panel.ID_SCRIPTMODELLABEL = xrc.XRCCTRL(self.panel,
                                                       "ID_SCRIPTMODELLABEL")
        self.panel.ID_SCRIPTNAMELABEL = xrc.XRCCTRL(self.panel,
                                                       "ID_SCRIPTNAMELABEL")

        panelsizer = wx.BoxSizer(wx.VERTICAL)
        panelsizer.Add(self.panel, 1, wx.EXPAND|wx.ALL)
        self.SetSizer(panelsizer)
        self.SetAutoLayout(True)
        #panelsizer.Fit(parent)

        self.datasettype=parent.datasettype

        self.panel.ID_FROMSCRIPT.SetValue(True)
        self.panel.ID_SCRIPTNAME.SetValue("Default")
        self.panel.ID_SCRIPTMODELLIST.ClearAll()

        self.panel.ID_SCRIPTASSISTANT.Show(False)   #XXX: Script assistant

        self.Bind(wx.EVT_CHECKBOX, self.onFromScript,self.panel.ID_FROMSCRIPT)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected, self.panel.ID_SCRIPTMODELLIST)

        self.list= self.panel.ID_SCRIPTMODELLIST
        il = wx.ImageList(16,15)
        img1=wx.Bitmap(os.path.join(cm.GetMainPath(), 'images','icons',
                                              'script.gif'), wx.BITMAP_TYPE_GIF)
        self.scriptidx = il.Add(bitmap=img1, mask=wx.NullBitmap)
        self.list.AssignImageList(il,wx.IMAGE_LIST_SMALL)


        self.onFromScript()

#------------------------------------------------------------------------------
    def readScript(self):
#------------------------------------------------------------------------------
        path=os.path.join(cm.GetMainPath(),'workspace','models')
        filename=os.path.join(path,self.panel.ID_SCRIPTNAME.GetValue()+".tpl")
        if os.path.exists(filename):
            f = file(filename, 'rb')
            try:
                text=f.read()
                text=text.replace('\r\n', '\n')
                text=text.replace('\r', '\n')
                #this is necessary for the exec command
            finally:
                f.close()
        else:
            text="#No script loaded"
        return text

#------------------------------------------------------------------------------
    def readReport(self):
#------------------------------------------------------------------------------
        path=os.path.join(cm.GetMainPath(),'workspace','models')
        filename=os.path.join(path,self.panel.ID_SCRIPTNAME.GetValue()+".rtf")
        text=""
        if os.path.exists(filename):
            f = file(filename, 'rb')
            try:
                text=f.read()
            finally:
                f.close()
        if text:
            text = cm.rtccontent(text)
        else:
            text = self.parent.datasetdescription

        return text

    #--------------------------------
    def onItemSelected(self, event):
    #--------------------------------
        file=self.list.GetItemText(event.m_itemIndex)
        self.panel.ID_SCRIPTNAME.SetValue(file)

    #----------------------------
    def onFromScript(self, evt=None):
    #----------------------------
        state=(self.panel.ID_FROMSCRIPT.GetValue()==1)
        self.panel.ID_SCRIPTMODELLIST.Enable(state)
        self.panel.ID_SCRIPTMODELLABEL.Enable(state)
        self.panel.ID_SCRIPTNAME.Enable(state)
        self.panel.ID_SCRIPTNAMELABEL.Enable(state)
        if state:
            self.updateScriptList()
        else:
            self.list.ClearAll()

    #----------------------------
    def updateScriptList(self, evt=None):
    #----------------------------
        self.list.ClearAll()
        modelsdir = os.path.join(cm.GetMainPath(), 'workspace','models')
        ls = os.listdir(modelsdir)
        self.list.InsertColumn(0, "Models")
        for file in ls:
            name=cm.GetPath(file,"filebase")
            if string.strip(name)!="":
                index = self.list.InsertImageStringItem(sys.maxint, name,
                                                                 self.scriptidx)
        self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)

    #-----------------------
    def SetNext(self, next):
    #-----------------------
        self.next = next

    #-----------------------
    def SetPrev(self, prev):
    #-----------------------
        self.prev = prev

    #-----------------
    def GetNext(self):
    #-----------------
        """If the checkbox is set then return the next page's next page"""
        return self.next

    #-----------------
    def GetPrev(self):
    #-----------------
#        prev=self.prev
#        if prev and self.datasettype!=1:
#            prev = prev.GetPrev()
        return self.prev

#====================================
class CreateWizard(wx.wizard.Wizard):
#====================================
    """
    Add pages to this wizard object to make it useful.
    """
    #--------------------------------------
    def __init__(self, parent, title, img):
    #--------------------------------------
        Wizard.__init__(self, parent, -1, title, img)
        self.pages = []
        # Lets catch the events
        self.Bind(EVT_WIZARD_PAGE_CHANGED, self.onPageChanged)
        self.Bind(EVT_WIZARD_PAGE_CHANGING, self.onPageChanging)
        self.Bind(EVT_WIZARD_CANCEL, self.onCancel)
        self.Bind(EVT_WIZARD_FINISHED, self.onFinished)
        self.cancel=False
        self.datasettype=0

    #------------------------
    def add_page(self, page):
    #------------------------
        """
        Add a wizard page to the list.
        """
        if self.pages:
            previous_page = self.pages[-1]
            page.SetPrev(previous_page)
            previous_page.SetNext(page)
        self.pages.append(page)
        self.SetAutoLayout(True)

    #-------------
    def run(self):
    #-------------
        self.RunWizard(self.pages[0])
        self.currentpage=self.pages[0]

    # Now define some event handler functions from the demo

    #------------------------------
    def onPageChanged(self, evt):
    #------------------------------
        pass

    #-------------------------------
    def onPageChanging(self, evt):
    #-------------------------------
        """
        Executed before the page changes, so we might veto it.
        """
        page = evt.GetPage()
        if (page is self.pages[0]):
            #Check that the name is valid
            if page.panel.ID_DATASETNAME.GetValue()=="":
                evt.Veto()
                cm.messageDialog ( None,
                                'Sorry, you must define a valid name, '+\
                                'before going to the next page!',
                                'Warning',
                                style = wx.ICON_EXCLAMATION|wx.OK )

    #------------------------
    def onCancel(self, evt):
    #------------------------
        self.datasetname=None
        self.cancel=True

    #--------------------------
    def onFinished(self, evt):
    #--------------------------
        """
        Finish button has been pressed.  Exit.
        """
        self.datasetname=self.pages[0].panel.ID_DATASETNAME.GetValue()
        self.datasetdescription=\
             cm.rtccontent(self.pages[0].panel.ID_DATASETDESCRIPTION.GetValue())
        dir=self.pages[0].panel.ID_EXPERIMENTALDIR.GetValue()
        name=self.pages[0].panel.ID_EXPERIMENTALNAME.GetValue()
        self.experimentalpath=os.path.join(dir,name)
        self.experimentaldata=self.pages[0].readExperimental()
        self.scriptname=self.pages[1].panel.ID_SCRIPTNAME.GetValue()
        self.scriptdata=self.pages[1].readScript()
        self.reportdata=self.pages[1].readReport()

#===================
class WizDatasetNew:
#===================
    #-------------------------------
    def __init__(self, parent=None):
    #-------------------------------
        # Create  and open the Wizard Dialog New
        img=wx.Bitmap(os.path.join(cm.GetMainPath(), 'images',
                                   'icons','wizardlogo.gif'),wx.BITMAP_TYPE_GIF)
        self.wizard= wizard = CreateWizard ( parent,
                                                'Create/Open new dataset', img )
        self.cancel= False

        # Create trhee pages for this wizard
        Page1 = DatasetPage(wizard)
        Page2 = ScriptPage(wizard)

        wizard.FitToPage(Page1)
        # and add them to the wizard
        wizard.add_page(Page1)
        wizard.add_page(Page2)

        wizard.run()

        if wizard.cancel :
            self.cancel=wizard.cancel
            self.datasetname=None
            cm.LOG_WARNING("Operation Cancelled!")
        else:
            self.datasetname=self.wizard.datasetname
            self.datasetdescription=self.wizard.datasetdescription
            self.experimentalpath=self.wizard.experimentalpath
            self.experimentaldata=self.wizard.experimentaldata
            self.scriptname=self.wizard.scriptname
            self.scriptdata=self.wizard.scriptdata
            self.reportdata=self.wizard.reportdata

