#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      wizproject.py
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

 This file implement a class "WizProjectNew" to open or create new project

"""

__docformat__="epytext"


from common import *
from pypulsar_xrc import *
from wx.wizard import Wizard, WizardPageSimple

#===================
class WizProjectNew:
#===================

#-------------------------------------------------------------------------------
    def __init__(self, parent=None):
#-------------------------------------------------------------------------------

        # Create  and open the Wizard Dialog New
        img=wx.Bitmap(os.path.join(GetMainPath(), 'images','icons','wizardlogo.gif'),wx.BITMAP_TYPE_GIF)
        wizard = Wizard ( parent, -1, 'Create/Open new project', bitmap=img )

        # Create two pages for this wizard
        wizardPage1 = WizardPageSimple ( wizard )
        wizardPage2 = WizardPageSimple ( wizard )

        #fill the first page
        self.newpanel1=xrcproject_WizardPage_1(wizardPage1)
        panelsizer = wx.BoxSizer(wx.VERTICAL)
        panelsizer.Add(self.newpanel1, 1, wx.EXPAND)
        wizardPage1.SetSizer(panelsizer)

        #fill the second page
        self.newpanel2=xrcproject_WizardPage_2(wizardPage2)
        panelsizer = wx.BoxSizer(wx.VERTICAL)
        panelsizer.Add(self.newpanel2, 1, wx.EXPAND)
        wizardPage2.SetSizer(panelsizer)

        # set default values
        self.newpanel1.wizprojectname.SetValue("~untitled")
        self.newpanel1.wizUseDefaultLocation.SetValue(True)
        self.newpanel1.wizprojectpath.SetValue(os.path.join(GetMainPath(), 'workspace'))
        self.newpanel2.wizprojectdescription.SetValue("type a description here")

        # Link the pages together
        wx.wizard.WizardPageSimple_Chain( wizardPage1, wizardPage2 )
        wizard.FitToPage(wizardPage1)

        self.newpanel1.Bind(wx.EVT_CHECKBOX, self.OnUseDefaultLocation, self.newpanel1.wizUseDefaultLocation)
        self.newpanel1.Bind(wx.EVT_BUTTON, self.OnBrowseDirectory, self.newpanel1.wizprojectpathBrowse)
        self.newpanel1.Bind(wx.EVT_TEXT, self.OnUpdateProjectlist, self.newpanel1.wizprojectpath)
        self.newpanel1.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.newpanel1.wizprojectlist)

        #Window close button pushed
        wizard.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING,self.OnWizardPageChange)

        # image for list
        self.il=imglist()
        self.newpanel1.wizprojectlist.AssignImageList(self.il, wx.IMAGE_LIST_SMALL)

        self.OnUseDefaultLocation()
        self.OnUpdateProjectlist()

        # Run the wizard and display a message if it was completed successfully
        self.Project_info={}
        if (wizard.RunWizard(wizardPage1) and
            self.newpanel1.wizprojectname.GetValue()!="~untitled"):
           project_file=os.path.join(self.newpanel1.wizprojectpath.GetValue(),
                                    self.newpanel1.wizprojectname.GetValue())

           #set the values of project dict that will be read from the mainframe
           self.Project_info= {
                "path":project_file+".ppp",
                "description":
                    rtccontent(self.newpanel2.wizprojectdescription.GetValue())}
           self.cancel=False
        else:
           self.cancel=True
           messageDialog ( None,
                           'No project was created!',
                           'Cancelled',
                           style = wx.ICON_EXCLAMATION|wx.OK )

        # Destroy the wizard
        wizard.Destroy()

    #--------------------------------
    def OnItemSelected(self, event):
    #--------------------------------
        name=self.newpanel1.wizprojectlist.GetItemText(event.m_itemIndex)
        self.newpanel1.wizprojectname.SetValue(name)
        self._Description_=""
        self.newpanel2.wizprojectdescription.SetValue(self._Description_)

    #----------------------------------
    def OnWizardPageChange(self,event):
    #----------------------------------
        if self.newpanel1.wizprojectname.GetValue()=="~untitled":
            event.Veto()
            messageDialog ( None, 'The project name "~untitled" is invalid. You must define a valid name (without extension)!', 'Warning',
                                        style = wx.ICON_EXCLAMATION|wx.OK )

    #----------------------------------------------
    def OnUseDefaultLocation(self, event=None):
    #----------------------------------------------
        chkstate=self.newpanel1.wizUseDefaultLocation.GetValue()
        self.newpanel1.wizprojectpath.Enable(not chkstate)
        self.newpanel1.wizprojectpathBrowse.Enable(not chkstate)
        if chkstate:
            self.newpanel1.wizprojectpath.SetValue(os.path.join(GetMainPath(), 'workspace'))

    #---------------------------
    def OnBrowseDirectory(self,event=None):
    #---------------------------
        result = directory(parent=self.newpanel1, message='Choose a workspace directory',
                  path=os.path.join(GetMainPath(), 'workspace'))

        if result.path:
            if os.path.exists(result.path):
               self.newpanel1.wizprojectpath.SetValue(result.path)

    #---------------------------
    def OnUpdateProjectlist(self, event=None):
    #---------------------------
        list= self.newpanel1.wizprojectlist
        list.ClearAll()

        info = wx.ListItem()
        info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
        info.m_image = -1
        info.m_format = 0
        info.m_text = "Project"
        list.InsertColumnInfo(0, info)

        info.m_format = wx.LIST_FORMAT_RIGHT
        info.m_text = "Description"
        list.InsertColumnInfo(1, info)

        ws = self.newpanel1.wizprojectpath.GetValue()
        listdir=os.listdir(ws)
        for item in listdir:
            pitem=os.path.splitext(item)
            if pitem[1]==".ppp":
                    self._Description_=""
                    #TODO : extract description from file
                    index = list.InsertImageStringItem(sys.maxint, pitem[0],
                                                       self.il.projectidx)
                    strg = str(self._Description_)
                    if len(strg)>40: strg=strg[0:39]+"..."
                    list.SetStringItem(index, 1, strg)
        list.SetColumnWidth(1, wx.LIST_AUTOSIZE)




