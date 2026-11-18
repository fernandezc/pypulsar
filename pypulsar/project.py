# !/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
 ==========
 - Name  :   project.py
 - Author :   Christian Fernandez

PULSAR Project:
 ===============
 - Copyright (C) 2006-2008 J.P. Amoureux, C. Fernandez
 - JPA - Unite de Catalyse et Chimie du Solide, Lille, France.
 - CF - Laboratoire Catalyse et Spectrochimie, Caen, France.

LICENSE:
 ========
 This program is free software; you can redistribute it and/or modify it under
 the terms of the GNU General Public License (GPL) as published by the Free
 Software Foundation; either version 2 of the License, or (at your option)
 any later version.

 This program is distributed in the hope that it will be useful, but WITHOUT ANY
 WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
 PARTICULAR PURPOSE. See the GNU General Public License for more details.

 To read the license please visit U{http://www.gnu.org/copyleft/gpl.html}

PURPOSE OF THIS FILE:
 =====================

Pypulsar project classes.

"""
#TODO: when a dataset treeitem is renamed, rename all associated book pages
#TODO: disallow naming several dataset with the same name

__docformat__ = "epytext"

from xml.dom import minidom
import wx
import os
import types
import common as cm
from common import LOG_DEBUG as DEBUG
from definitions import *
from xmldocument import XmlDocument
from plot import PlotPage, MultiPlotPage
from script import ScriptEditorPage
from editor import EditorPage
from wizdataset import WizDatasetNew
from wizproject import WizProjectNew
import wx.aui as Aui
from book import AuiBook
import wx.lib.pubsub as pubsub
from numpy import arange, array, size, shape

TEXT_NODE = minidom.Node.TEXT_NODE

#===============================================================================
class ProjectTree(wx.TreeCtrl):
#===============================================================================
    """
    Tree control to display the project
    """

#-------------------------------------------------------------------------------
    def __init__(self, parent):
#-------------------------------------------------------------------------------
        """
        Init a new Project Instance
        """
        DEBUG(info = True)
        wx.TreeCtrl.__init__(
                   self,
                   parent, -1,
                   wx.Point(0, 0),
                   wx.Size(160, 250),
                   wx.TR_DEFAULT_STYLE| wx.TR_EDIT_LABELS | wx.NO_BORDER)

        # Reference to parent objects
        #----------------------------

        self.parent = parent

        # project
        self.Project = parent.Project

        self.Book = None

        # Private attributes
        #--------------------
        self.__modify = False

        # Other attributes
        #-----------------
        self.il = cm.imglist()
        self.root = None
        self.lastselection = None

        # Tree project events
        #--------------------
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.rename)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSING, self.onItemCollapsing)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onItemChanged)
        self.Bind(wx.EVT_TREE_DELETE_ITEM, self._onItemDeleted)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.onBeginEdit)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.onEndEdit)
        #self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.contextmenu)

        pubsub.Publisher().subscribe(self._itemDelete, "NODE DELETED")

#-------------------------------------------------------------------------------
# Property isLocked
#-------------------------------------------------------------------------------
    def _getLock(self):
#-------------------------------------------------------------------------------
        return self.Project.isLocked

#-------------------------------------------------------------------------------
    def _setLock(self, value):
#-------------------------------------------------------------------------------
        self.Project.isLocked = value

    isLocked = property(
                        fget = _getLock,
                        fset = _setLock,
                        doc = "modify lock status of the tree")

#-------------------------------------------------------------------------------
# Property isLoading
#-------------------------------------------------------------------------------
    def _getLoading(self):
#-------------------------------------------------------------------------------
        return self.Project.isLoading

    isLoading = property(
                        fget = _getLoading,
                        doc = "Get load status of the tree")

#------------------------------------------------------------------------------
    def canRename(self):
#------------------------------------------------------------------------------
        DEBUG(info = True)
        return True

#-------------------------------------------------------------------------------
    def rename(self, event = None):
#-------------------------------------------------------------------------------
        """
        Rename the selected item
        """
        DEBUG(info = True)
        self.EditLabel(self.GetSelection())

#-------------------------------------------------------------------------------
    def _itemDelete(self, message):
#-------------------------------------------------------------------------------
        """
        called when NODE DELETED message is sent
        """
        DEBUG(info = True)
        self.isLocked = True # prevent parsing!
        root = self.GetRootItem()
        self.SelectItem(root) # the item to be deleted cannot be selected
        node = message.data
        nodeId = node.getAttribute("Id")
        treeItemId = self.findTreeItemFromId(nodeId)
        self.Delete(treeItemId)
        self.isLocked = False # allow parsing again if needed!

#-------------------------------------------------------------------------------
    def _onItemDeleted(self, event):
#-------------------------------------------------------------------------------
        """
        Called before the deletion of ean item
        allow deletion of the corresponding book page if necessary
        """
        DEBUG(info = True)
        itemId = event.GetItem()
        datas = self.GetPyData(itemId)
        if datas[1]:
            Id = int(datas[1].getAttribute("Id"))
            pubsub.Publisher().sendMessage("ITEM DELETED", Id)

#------------------------------------------------------------------------------
    def findTreeItemFromId(self, wid = None, parent = None):
#------------------------------------------------------------------------------
        """
        Find a tree Item and the associated DOM node
        from a book page selection (id)
        return the TreeItem or False if it was not found
        """
        DEBUG(info = True)
        if wid is None:
            return False

        if parent is None:
            parent = self.GetRootItem()

        datas = self.GetPyData(parent)
        Id = datas[0]
        if int(Id) == int(wid):
            return parent # Found !

        #find first child
        child, cookie = self.GetFirstChild(parent)
        while (child.IsOk()):
            found = self.findTreeItemFromId(wid, child)
            if found:
                return found
            # find next child
            child, cookie = self.GetNextChild(parent, cookie)

        return False # not found

#-------------------------------------------------------------------------------
    def itemRename(self, itemId):
#-------------------------------------------------------------------------------
        """
        rename node versus the modified item text
        """
        DEBUG(info = True)
        text = self.GetItemText(itemId)
        if self.storetext == self.GetItemText(self.GetSelection()):
            return

        datas = self.GetPyData(itemId)
        if datas[1]:
            #rename Tree item
            datas[1].setAttribute("Name", text)
            Id = int(datas[1].getAttribute("Id"))
            i = self.Book.pageFromItem(Id)
            if i>-1:
                self.Book.SetPageText(i, datas[1].getAttribute("Parent")+
                                     " "+datas[1].getAttribute("Name"))

            #Rename child's
            for node in datas[1].childNodes:
                if node.nodeType == minidom.Node.ELEMENT_NODE:
                    node.setAttribute("Parent", text)

                    #Rename Book page
                    Id = int(node.getAttribute("Id"))
                    i = self.Book.pageFromItem(Id)
                    if i != -1:   #page opened
                        self.Book.SetPageText(i, node.getAttribute("Parent")+
                                         " "+node.getAttribute("Name"))

            self.isModified = True

#-------------------------------------------------------------------------------
    def onItemChanged(self, event = None):
#-------------------------------------------------------------------------------
        """
        Tree item selection modified
        -Select the corresponding pages
        """
        DEBUG(info = True)
        item = self.GetSelection()
        self.Project.Dataset = self.Project.SelectedNode
        if item != self.lastselection:
            self.lastselection = item
        event.Skip()
        if not self.isLocked:
            pubsub.Publisher().sendMessage("UPDATE")

#-------------------------------------------------------------------------------
    def onItemCollapsing(self, event = None):
#-------------------------------------------------------------------------------
        """
        The tree will be always expanded
        """
        #event.Veto()
        pass

#------------------------------------------------------------------------------
    def onBeginEdit(self, event = None):
#------------------------------------------------------------------------------
        #check if it is the project name
        DEBUG(info = True)
        if not self.canRename():
            event.Veto()
        self.storetext = self.GetItemText(self.GetSelection())

#-------------------------------------------------------------------------------
    def onEndEdit(self, event):
#-------------------------------------------------------------------------------
        DEBUG(info = True)
        itemId = self.GetSelection()
        wx.CallAfter(self.itemRename, itemId)
        event.Skip()

#-------------------------------------------------------------------------------
    def parse(self, node, parent = None):
#-------------------------------------------------------------------------------
        """
        Main dispatcher for the parse method
        """
        DEBUG(info = True)
#        self.isLocked = True # prevent update during parsing
        if parent is None:
            parent = self.root = self.setTreeRoot(node)
        parseMethod = getattr(self, "parse%s" % node.__class__.__name__)
        parseMethod(node, parent)
        self.Expand(self.root)
#        self.isLocked = False # allow update during parsing
        self.SelectItem(self.root)

#-------------------------------------------------------------------------------
    def parseDocument(self, node, _parent):
#-------------------------------------------------------------------------------
        """
        parse_Document is only ever called once,
        since there is only one Document node in an XML document,
        and only one Document object in the parsed XML representation.
        """
        DEBUG(info = True)
        if not self.isLoading:
            # if is loading, get the node Id
            Id = node.attributes["Id"].value
        else:
            # else, we set the node Id using a generated id
            Id = wx.NewId()
            node.setAttribute("Id", str(Id))

        # Set the data for the root node
        self.SetPyData(self.root, [Id, node]) #XXX:, None])

        # do parsing recursively
        self.parse(node.documentElement, self.root)

#-------------------------------------------------------------------------------
    def parseText(self, node, parent):
#-------------------------------------------------------------------------------
        """
        parse_Text is called on nodes that represent bits of text.
        This contains data to be displayed
        """
        DEBUG(info = True)
        text = node.data
        datas = self.GetItemPyData(parent)
        #XXX: datas[2] = str(text)
        self.SetPyData(parent, datas)

#-------------------------------------------------------------------------------
    def parseElement(self, node, parent):
#-------------------------------------------------------------------------------
        """
        Parse element node and associate a tree item
        """
        DEBUG(info = True)
        if node.tagName == "Project" :
            # Project node
            project_item = [item for item in node.childNodes]
            for item in project_item:
                # do parsing recursively
                self.parse(item, parent)
        else:
            # Dataset or Dataset child node
            name = node.attributes["Name"].value
            kind = node.attributes["Kind"].value
            if not self.isLoading:
                # if is loading, get the node Id
                Id = node.attributes["Id"].value
            else:
                # else, we set the node Id using a generated id
                # I don't remember why it is so ! TODO: Check this
                Id = wx.NewId()
                node.setAttribute("Id", str(Id))

            # associate a tree item to the element
            item = self.AppendItem(parent, name)

            #set images attributes
            il = cm.imglist()
            img = getattr(il, "%sidx"%prjkinds[int(kind)].lower())
            self.SetItemImage(item, img, wx.TreeItemIcon_Normal)

            # initilize data contained by this item
            self.SetPyData(item, [Id, node]) #XXX:, ""])

            #parse dataset elements (recursively)
            #source_item = [i for i in node.childNodes]
            for i in node.childNodes: #source_item:
                self.parse(i, item)

            # If an experimental spectrum or graph data are present
            # the dataset allows fitting

            #TODO: work on fit
            if int(kind) in [3, 4, 5]:
                self.isFittable = True

#------------------------------------------------------------------------------
    def setTreeItemImage(self, item = None):
#------------------------------------------------------------------------------
        """
        Walk along all tree item and set the image
        """
        DEBUG(info = True)
        self.il = cm.imglist()

        if item is None:
            item = self.GetRootItem()

        datas = self.GetPyData(item)
        Id = int(datas[0])
        node = datas[1]

        kind = int(node.attributes["Kind"].value)
        imgold = self.GetItemImage(item)

        pageN = int(self.Book.pageFromItem(Id))

        if pageN == -1:
            img = getattr(self.il, "%sidx"%(prjkinds[kind].lower()))
            self.SetItemImage(item, img, wx.TreeItemIcon_Normal)

        elif pageN>-1:
            win = self.Book.GetPage(pageN)
            if win.isModified:
                img = getattr(self.il,
                   "%s_modifiedidx"%(prjkinds[kind].lower()))
            else:
                img = getattr(self.il,
                "%sidx"%(prjkinds[kind].lower()))

        if imgold != img:
            self.SetItemImage(item, img, wx.TreeItemIcon_Normal)
            if pageN > -1:
                self.Book.SetPageBitmap(pageN, self.il.GetBitmap(img))

        if item == self.GetRootItem():
            if self.Project.isModified:
                # the project is modified, change also the icon
                img = getattr(self.il, "project_modifiedidx")
            else:
                img = getattr(self.il, "projectidx")
            self.SetItemImage(item, img, wx.TreeItemIcon_Normal)
            if pageN > -1 and self.Book.GetPage(pageN).isModified:
                self.Book.SetPageBitmap(pageN, self.il.GetBitmap(img))

        #find first child
        child, cookie = self.GetFirstChild(item)
        while (child.IsOk()):
            self.setTreeItemImage(child)
            # find next child
            child, cookie = self.GetNextChild(item, cookie)

#-------------------------------------------------------------------------------
    def setTreeRoot(self, node):
#-------------------------------------------------------------------------------
        DEBUG(info = True)
        Id = wx.NewId()
        self.il = cm.imglist()
        self.AssignImageList(self.il)

        # Clear tree
        #-----------
        self.DeleteAllItems()
        self.Refresh()

        # Get name of the project
        #------------------------
        name = node.attributes["Name"].value

        # Create the root tree element
        #-----------------------------
        root = self.AddRoot(name)
        self.SetItemImage(root, self.il.rootidx, wx.TreeItemIcon_Normal)

        # Update some attribute
        #----------------------
        node.setAttribute("Id", str(Id))
        node.setAttribute("Kind", str(PYP_PROJECT))

        # Set the data associated with the tree element
        #----------------------------------------------
        self.SetPyData(root, [Id, node, None])

        return root

#-------------------------------------------------------------------------------
    def update(self, node = None, parent = None):
#-------------------------------------------------------------------------------
        DEBUG(info = True)

        # Associated book
        #-----------------
        if hasattr(self.Project, "Book"):
            self.Book = self.Project.Book

        if node is None:
            datas = self.GetPyData(self.root)
            node = datas[1]
        else:
            # Avoid parsing if another operation on tree item is currently done
            # e.g., delete item!
            if not self.isLocked:
                self.parse(node, parent)

        # update images
        if self.Project.isModified:
            self.setTreeItemImage()

        # get the current selected node
        if self.Project is None:
            return

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

    isModified = property(fget = _getModify, fset = _setModify,
                          doc = "Set /Get modify status")

#===============================================================================
class ProjectBook(AuiBook):
#===============================================================================

#-------------------------------------------------------------------------------
    def __init__(self, parent):
#-------------------------------------------------------------------------------
        DEBUG(info = True)
        AuiBook.__init__(self, parent,
                         style= wx.NO_BORDER|
                         Aui.AUI_NB_DEFAULT_STYLE|
                         Aui.AUI_NB_WINDOWLIST_BUTTON)

        self.Bind(Aui.EVT_AUINOTEBOOK_PAGE_CHANGED,
                                                 self.onBookPageChanged)
        self.Bind(Aui.EVT_AUINOTEBOOK_PAGE_CLOSE,
                                                  self.onBookPageClosed)

        pubsub.Publisher().subscribe(self._pageDelete, "ITEM DELETED")

        # project
        self.Project = self.parent.Project

        # Associated Tree
        #-----------------
        self.Tree = None
        if hasattr(parent.Project, "Tree"):
            self.Tree = parent.Project.Tree

        # Private attributes
        #--------------------
        self.__modify = False

#-------------------------------------------------------------------------------
    def _pageDelete(self, message):
#-------------------------------------------------------------------------------
        """
        called when PAGE DELETED event is sent
        """
        DEBUG(info = True)
        Id = message.data
        pageId = self.pageFromItem(Id)
        # The page exist, delete it.
        #---------------------------
        if pageId > -1:
            page = self.GetPage(pageId)
            #page.Content=None  # to delete associated content
            self.DeletePage(pageId)

#-------------------------------------------------------------------------------
    def getPageIfExists(self, Id):
#-------------------------------------------------------------------------------
        """
        check existence and return page selection number
        """
        DEBUG(info = True)
        pageId= self.pageFromItem(Id)
        if pageId > -1:
            win = self.GetPage(pageId)
            winId = win.GetId()
            page = self.GetPage(self.GetSelection())
            if page != win :
                win.SetFocus()
            treeitem = self.Tree.findTreeItemFromId(winId)
            if treeitem  != self.Tree.GetSelection():
                self.Tree.SelectItem(treeitem)
        return pageId

#-------------------------------------------------------------------------------
    def pageFromItem(self, Id):
#-------------------------------------------------------------------------------
        """
        check existence and return page selection number
        """
        DEBUG(info = True)
        for pageId in range(self.GetPageCount()):
            win = self.GetPage(pageId)
            winId = win.GetId()
            if int(winId) == int(Id):
                return pageId
        return -1

#------------------------------------------------------------------------------
    def deleteAllPages(self):
#------------------------------------------------------------------------------
        DEBUG(info = True)
        for pageId in range(self.GetPageCount()):
            self.DeletePage(pageId)
            self.isModified = True

#------------------------------------------------------------------------------
    def onBookPageChanged(self, event):
#------------------------------------------------------------------------------
        """
        Action to perform when a page is selected
        """
        DEBUG(info = True)
        # Get the window corresponding to the page selection
        page = self.GetPage(self.GetSelection())
        #page.SetFocus()
        pageId = page.GetId()

        # Find the treeitem to the book page
        treeitem = self.Tree.findTreeItemFromId(pageId)

        # Select it - the change in the project properties will be done there
        if treeitem  and treeitem != self.Tree.GetSelection():
            self.Tree.SelectItem(treeitem)

        event.Skip()

#------------------------------------------------------------------------------
    def onBookPageClosed(self, event):
#------------------------------------------------------------------------------
        """
        Action to perform when a page is closed
        """
        DEBUG(info = True)
        # Get the window
        page = self.GetPage(self.GetSelection())

        # is page modified?
        if page.isModified:
            choice = cm.messageDialog(self,
                "Would you like to save this page changes before closing?",
                          "Closing...", wx.YES_NO|wx.YES_DEFAULT)
            if choice.positive:
                self.save(page)
            else:
                confirm = cm.messageDialog(self,
                    "Are you sure you want to close without saving "+\
                    "and loose the page changes?", "Closing...",
                    wx.YES_NO|wx.YES_DEFAULT)
                if not confirm.positive:
                    event.Veto()
                    return
                page.setSavePoint()

        event.Skip()

#-------------------------------------------------------------------------------
    def save(self, page=None):
#-------------------------------------------------------------------------------
        """
        save the new content of a page in the node
        """
        DEBUG(info = True)
        if page is None:
            page = self.GetPage(self.GetSelection())
        pageId = page.GetId()
        treeitem = self.Tree.findTreeItemFromId(pageId)
        datas = self.Tree.GetPyData(treeitem)
        node = datas[1]
        newcontent=str(page.Content).encode('base64_codec')
        self.Project.updateTextnode(node, newcontent)

        page.setSavePoint()  #discard edits

#-------------------------------------------------------------------------------
    def update(self):
#-------------------------------------------------------------------------------
        DEBUG(info = True)
        if self.Project is None:
            return

        node = self.Project.SelectedNode
        self.openPage(node)

#        self.Project._mgr.Update()

#-------------------------------------------------------------------------------
    def openPage(self, node = None):
#-------------------------------------------------------------------------------
        DEBUG(info = True)
        if node is None:
            return

        Id = int(node.attributes["Id"].value)

        # Now show or create the book page corresponding to the same node
        #-----------------------------------------------------------------

        # Check if the page is already displayed (checking the Id)
        pageN=self.getPageIfExists(Id)
        if pageN > -1:
            # if the page already exist
            self.Project.SelectedNode = node
            page = self.GetPage(pageN)
            return page


        # The page doesn't exist, so we create it

        if int(node.getAttribute("Kind")) in [PYP_SCRIPT, PYP_PARAMETERS, PYP_FIT]:
            # Display SCRIPT, PARAMETERS
            page = ScriptEditorPage(self, id = Id )

        elif int(node.getAttribute("Kind")) in PYP_ALLSPECTRA:
            # Display SPECTRUM
            page = PlotPage(self, id = Id)

        elif int(node.getAttribute("Kind")) in PYP_SPECTRACONTAINER:
            # Display multiple SPECTRA
            page = MultiPlotPage(self, id = Id )

        else:
            # Display an simple Editor
            page = EditorPage(self, id = Id )

        kind = node.getAttribute("Kind")
        self.il = cm.imglist()
        img = getattr(self.il, "%sidx"%(prjkinds[int(kind)].lower()))
        self.AddPage(page,
                  node.getAttribute("Parent") + " " + node.getAttribute("Name"),
                          select = True,
                          bitmap = self.il.GetBitmap(img))

        self.isModified = True

        # Set the content of this page
        #------------------------------
        content = self.getNodeContent(node)

        if content is not None:
            page.Content = content
            # Set the save point (to start handling changes from this point)
            page.setSavePoint()

        # inform Project of the possible change
        if node != self.Project.SelectedNode:
            self.Project.SelectedNode = node

        return page

#-------------------------------------------------------------------------------
    def getNodeContent(self, node):
#-------------------------------------------------------------------------------
        """
        retrieve content from node
        """
        DEBUG(info = True)
        # if single spectrum
        #--------------------
        for childnode in node.childNodes:
            if childnode.nodeType == minidom.Node.TEXT_NODE:
                return childnode.data.decode('base64_codec')

        # else container of spectra
        #  if we are here this means that there is no TEXT_NODE
        #  this is the case for PYP_SPECTRA or PYP_SPECTRACONTAINER
        #------------------------------------------------------------
        content = {}
        for childnode in node.childNodes:

            # if child are individual components
            #------------------------------------
            if childnode.nodeType == minidom.Node.ELEMENT_NODE and \
                          int(childnode.getAttribute("Kind")) in PYP_ALLSPECTRA:
                for childnodetext in childnode.childNodes:
                    if childnodetext.nodeType == minidom.Node.TEXT_NODE:
                        content[childnode.getAttribute("Name")] = \
                        childnodetext.data.decode('base64_codec')

            # else child are another container
            #----------------------------------
            for subchildnode in childnode.childNodes:
                if subchildnode.nodeType == minidom.Node.ELEMENT_NODE and \
                       int(subchildnode.getAttribute("Kind")) in PYP_ALLSPECTRA:
                    for subchildnodetext in subchildnode.childNodes:
                        if subchildnodetext.nodeType == minidom.Node.TEXT_NODE:
                            content[subchildnode.getAttribute("Name")] = \
                            subchildnodetext.data.decode('base64_codec')

        return content

#-------------------------------------------------------------------------------
# Property isModified
#-------------------------------------------------------------------------------
    def _getModify(self):
#-------------------------------------------------------------------------------
        """
        Get modify status of the project
        """
        self.__modify = False
        for i in range(self.GetPageCount()):
            self.__modify = self.__modify or self.GetPage(i).isModified
        return self.__modify

#-------------------------------------------------------------------------------
    def _setModify(self, value):
#-------------------------------------------------------------------------------
        """
        Set modify status of the project
        """
        self.__modify = value

    isModified = property(fget = _getModify, fset = _setModify)

#-------------------------------------------------------------------------------
# Property isError
#-------------------------------------------------------------------------------
    def _getError(self):
#-------------------------------------------------------------------------------
        """
        Get modify status of the project
        """
        self.__error = False
        for i in range(self.GetPageCount()):
            self.__error = self.__error or self.GetPage(i).isError
        return self.__error

    isError = property(fget = _getError, doc = "isError (Read only property)")

#-------------------------------------------------------------------------------
# Property isLocked
#-------------------------------------------------------------------------------
    def _getLock(self):
#-------------------------------------------------------------------------------
        return self.Project.isLocked

#-------------------------------------------------------------------------------
    def _setLock(self, value):
#-------------------------------------------------------------------------------
        self.Project.isLocked = value

    isLocked = property(
                        fget = _getLock,
                        fset = _setLock,
                        doc = "modify lock status of the book")

#===============================================================================
class Project(object):
#===============================================================================
    """
    Tree control to display the project
    """

#-------------------------------------------------------------------------------
    def __init__(self, parent, name = None):
#-------------------------------------------------------------------------------
        """
        Init a new Project Instance
        """
        DEBUG(info = True)

        self.parent = parent

        self._mgr = None
        if hasattr(parent, "_mgr"):
            self._mgr = parent._mgr

        # Other private attributes
        #----------------------
        self.doc = None
        self.xmldoc = None
        self.isFittable = False

        # private attributes (properties of the project)
        #----------------------
        self.__containdataset = False  # contains some dataset?
        self.__dataset = None          # current dataset
        self.__selectednode = None
        self.__modify = False
        self.__spectra = None
        self.__spectrum = None
        self.__experiment = None
        self.__parameters = None
        self.__script = None
        self.__locked = False

        # Load a project or create one default
        #-------------------------------------
        self.loadProject(name)
        self.isModified = False

        # Create the interface elements
        #------------------------------
        self.Tree = ProjectTree(parent)
        self.Book = ProjectBook(parent)

        # Create a Tree from the XML data
        #--------------------------------
        self.isLoading = True
        if self.xmldoc is not None:
            self.Tree.update(self.xmldoc.documentElement)
        self.isLoading = False

#------------------------------------------------------------------------------
    def closeProject(self):
#------------------------------------------------------------------------------
        """
        Closing a project
        """
        DEBUG(info = True)
##        lastprj = cm.getWorkspacePath('.lastproject')
##        # write last opened filename
##        if self.parent.hasProject:
##            f = open(lastprj, "wb")
##            last_project = self.doc.getBase()
##            f.writelines("last_project ="+
##                                        repr(cm.getWorkspacePath(last_project)))
##            f.close()

        # save config
        if self.parent.hasProject:
            self.parent.CONFIG["LastProject"]=self.doc.getBase()

        # save the project data
        self.saveProject()

#-------------------------------------------------------------------------------
    def loadProject(self, filename = None, description = None):
#-------------------------------------------------------------------------------
        """
        open an instance of class XMLProject to manage the project elements
        @param filename: name of the project to load (default: None)
        @param description: description of the project (default: None)
        @type filename: string
        @type description: string
        """
        DEBUG(info = True)

        if cm.getWorkspacePath(filename) is not None:
            filename=cm.getWorkspacePath(filename)+".ppp"
        else:
            filename="~untitled.ppp"

        self.doc = doc = XmlDocument(filename, description)
        self.xmldoc = xmldoc = doc.loadXML()
        self.parent.Project=self

        # Project is just loaded
        #-----------------------
        self.isModified = False

#-------------------------------------------------------------------------------
    def newProject(self):
#-------------------------------------------------------------------------------
        DEBUG(info = True)
        wizard = WizProjectNew(self.parent)
        cancel = wizard.cancel

        # If wizard was cancelled, then return immediatelly
        if cancel:
            return False

        # Read the returned info
        self.isLoading = True
        project_info = wizard.Project_info
        if project_info.has_key("path"):
            self.loadProject(project_info["path"],
                     description = project_info["description"])
        # Display the current id node
        top = self.xmldoc.documentElement
        self.Tree.isLocked = True # prevent update during parsing
        self.Tree.parse(top, None)
        self.Tree.isLocked = False
        self.Tree.ExpandAll()
        self.isLoading = False
        self.isModified = False

#-------------------------------------------------------------------------------
    def saveProject(self, saveas = None, xml = None):
#-------------------------------------------------------------------------------
        """
        Save project
        """
        DEBUG(info = True)

        if saveas:
            # Save project to a new filename
            filedir = ''
            if self.doc.getDirpath():
                filedir = self.doc.getDirpath()

            result = cm.saveSingle(directory = filedir)
            if result.path:
                self.doc.setPath(result.path)
            else:
                return

            #Search all open pages in the book
            for pageId in range(self.Book.GetPageCount()):

                #get the editor window
                page = self.Book.GetPage(pageId)
                self.Book.save(page)

            # Change Label of the root item
            self.Tree.SetItemText(self.Tree.RootItem, self.doc.getBase())
            datas = self.Tree.GetPyData(self.Tree.RootItem)

            if datas[1]:
                #rename Tree item
                datas[1].setAttribute("Name", self.doc.getBase())

            top = self.xmldoc.documentElement
            self.Tree.isLocked = True # prevent update during parsing
            self.Tree.parse(top, None)
            self.Tree.isLocked = False

            self.Tree.ExpandAll()

        else:

            #Search all open pages in the book
            for pageId in range(self.Book.GetPageCount()):

                #get the editor window
                page = self.Book.GetPage(pageId)
                self.Book.save(page)

        if xml is None:
            self.xmldoc.toxml()
            self.doc.saveXML(self.xmldoc.toxml())
        else:
            self.doc.saveXML(xml)

        # Set modify status of the project
        self.isModified = False
        self.Tree.isModified = False
        self.Book.isModified = False

        #actualize icons
        self.Tree.setTreeItemImage()

        # Eventually clear errors
        # TODO: call a method ClearError here (to write)

        if self.parent.Process is not None:
            self.parent.Process.Success = True

#------------------------------------------------------------------------------
    def updateProject(self):
#------------------------------------------------------------------------------
        """
        Update project
        """
        DEBUG(info = True)

        if self.isLocked: return

        if self._mgr is not None:
            pane = self._mgr.GetPane("Book")
            pane.Caption("[Project: "+self.doc.getName()+"]")
        self.Tree.update()
        self.Book.update()

#-------------------------------------------------------------------------------
    def updateTextnode(self, parentnode, newcontent):
#-------------------------------------------------------------------------------
        """
        replace text node by the new content
        """
        DEBUG(info = True)
        nodes = parentnode.childNodes
        for node in nodes:
            if node.nodeType == TEXT_NODE:
                textNode = self.xmldoc.createTextNode(newcontent)
                parentnode.appendChild(textNode)
                parentnode.replaceChild(textNode, node)
                return

#-------------------------------------------------------------------------------
# Dataset methods
# and definition of the Dataset Property
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
    def addDataset(self):
#-------------------------------------------------------------------------------
        DEBUG(info = True)
        wizard = WizDatasetNew(self.parent)
        cancel = wizard.cancel

        # If wizard was cancelled, then return immediatelly
        if cancel:
            return False

        datasetname = wizard.datasetname
        datasetdescription = wizard.datasetdescription
        scriptname = wizard.scriptname
        scriptdata = wizard.scriptdata
        reportdata = wizard.reportdata

        # Add a new node to the project xml tree
        top = self.xmldoc.documentElement
        Id = wx.NewId()
        ds = self.xmldoc.createElement(prjkinds[PYP_DATASET])
        top.appendChild(ds)
        ds.setAttribute("Id", str(Id))
        ds.setAttribute("Name", datasetname)
        ds.setAttribute("Kind", str(PYP_DATASET))
        ds.setAttribute("Property", datasetdescription)
        text = reportdata.encode('base64_codec')
        textNode = self.xmldoc.createTextNode(text)
        ds.appendChild(textNode)

        # Add fit commands
        Id = wx.NewId()
        e = self.xmldoc.createElement(prjkinds[PYP_PARAMETERS])
        ds.appendChild(e)
        e.setAttribute("Id", str(Id))
        e.setAttribute("Name", "Fit commands")
        e.setAttribute("Parent", datasetname)
        e.setAttribute("Kind", str(PYP_FIT))
        e.setAttribute("Property", "")
        text = fitcommands.encode('base64_codec')
        textNode = self.xmldoc.createTextNode(text)
        e.appendChild(textNode)

        # Add Script...
        Id = wx.NewId()
        e = self.xmldoc.createElement(prjkinds[PYP_SCRIPT])
        ds.appendChild(e)
        e.setAttribute("Id", str(Id))
        e.setAttribute("Name", "Script")
        e.setAttribute("Parent", datasetname)
        e.setAttribute("Kind", str(PYP_SCRIPT))
        e.setAttribute("Property", scriptname)
        text = scriptdata.encode('base64_codec')
        textNode = self.xmldoc.createTextNode(text)
        e.appendChild(textNode)
        e_script = e

        ### Add Experimental parameters...
        if wizard.experimentaldata:

            # Add spectra container
            Id = wx.NewId()
            e = self.xmldoc.createElement(prjkinds[PYP_SPECTRA])
            ds.appendChild(e)
            e.setAttribute("Id", str(Id))
            e.setAttribute("Name", "Spectra")
            e.setAttribute("Parent", datasetname)
            e.setAttribute("Kind", str(PYP_SPECTRA))
            e.setAttribute("Property", "")
            e_spectra = e

            experimentaldata = wizard.experimentaldata
            Id = wx.NewId()
            e = self.xmldoc.createElement(prjkinds[PYP_PARAMETERS])
            e_script.appendChild(e)
            e.setAttribute("Id", str(Id))
            e.setAttribute("Name", "Experimental parameters")
            e.setAttribute("Parent", datasetname)
            e.setAttribute("Kind", str(PYP_PARAMETERS))
            e.setAttribute("Property", str(experimentaldata["kind"]))
            text = experimentaldata["parameters"].encode('base64_codec')
            textNode = self.xmldoc.createTextNode(text)
            e.appendChild(textNode)

            # Add Experimental spectrum...
            Id = wx.NewId()
            typ = PYP_SPECTRUM1D
            if experimentaldata["kind"] == '2D': typ = PYP_SPECTRUM2D
            e = self.xmldoc.createElement(prjkinds[typ])
            e_spectra.appendChild(e)
            e.setAttribute("Id", str(Id))
            e.setAttribute("Name", "Experimental spectrum")
            e.setAttribute("Parent", datasetname)
            e.setAttribute("Kind", str(typ))
            e.setAttribute("Property", str(experimentaldata["kind"]))
            text = repr(experimentaldata["spectra"][0]).encode('base64_codec')
            textNode = self.xmldoc.createTextNode(text)
            e.appendChild(textNode)

        # parse xml node to recreate tree items

        self.Tree.isLocked = True # prevent update during parsing
        self.Tree.parse(top, None)
        self.Tree.isLocked = False
        self.isModified = True


#-------------------------------------------------------------------------------
    def _setDataset(self, node = None):
#-------------------------------------------------------------------------------
        """
        set the current dataset
        """
        if node is None:
            # no selection
            self.__dataset = None
        else:
            # make the selected dataset the current one
            kind = kind_of_node(node)
            if kind == PYP_PROJECT:
                self.__dataset = None
            elif kind == PYP_DATASET:
                self.__dataset = node
            else:
                #recursice call
                self._setDataset(node.parentNode)

#-------------------------------------------------------------------------------
    def _getDataset(self):
#-------------------------------------------------------------------------------
        """
        get the current dataset from attribute __dataset in the current project.
        @return: dataset node
        """
        if self.__dataset is None: #try to get the current dataset
            node = self.SelectedNode
            self._setDataset(node)

        return self.__dataset

#-------------------------------------------------------------------------------
    def _delDataset(self):
#-------------------------------------------------------------------------------
        DEBUG(info = True)
        if not self.canDelDataset():
            return False

        dataset = self.__dataset

        # Confirmation?
        name = dataset.getAttribute("Name")
        result = cm.messageDialog ( title = "Confirm?",
        message = "We are about to delete ["+ name + \
                  "] dataset. Are you sure" +
                  "\nThis operation will irreversibly delete all corresponding data",
                  style = wx.OK|wx.CANCEL|wx.CENTRE|wx.ICON_QUESTION)

        if not result.positive:
            cm.LOG_WARNING("Operation cancelled: Dataset '"+ \
                                                      name+"' was not deleted!")
            return

        # Avoid update
        #---------------
        self.isLocked = True

        # Send the info for book and tree item deletion
        # before actually removing this node
        #----------------------------------------------
        pubsub.Publisher().sendMessage("NODE DELETED", dataset)

        # Now delete the xml node item
        #-------------------------
        parentNode = dataset.parentNode
        parentNode.removeChild(dataset)
        self.__dataset = None

        self.isLocked = False

        # Update the node graph
        #-----------------------
        top = self.xmldoc.documentElement
        self.Tree.isLocked = True # prevent update during parsing
        self.Tree.parse(top, None)
        self.Tree.isLocked = False

        self.isModified = True

    Dataset = property(fget = _getDataset,
                       fset = _setDataset,
                       fdel = _delDataset,
                       doc = "Dataset set/get/del property.")

#-------------------------------------------------------------------------------
    def delAlldataset(self):
#-------------------------------------------------------------------------------
        """Remove all datasets"""
        #Delete the xml node item
        DEBUG(info = True)
        parentNode = self.xmldoc.documentElement
        nodes = parentNode.childNodes
        for node in nodes:
            if kind_of_node(node) == PYP_DATASET:
                self.SelectedNode = node
                self.Dataset = node
#                del self.__dataset
                # because del induce a new parsing
                #we need to call this method recursively delAlldataset
                self._delDataset()
                self.isModified = True

#-------------------------------------------------------------------------------
    def canDelDataset(self):
#-------------------------------------------------------------------------------
        node = self.SelectedNode
        self.Dataset = node
        if self.__dataset is not None:
            return True
        return False

#-------------------------------------------------------------------------------
    def containDataset(self):
#-------------------------------------------------------------------------------
        """Check if the project contains datasets."""
        DEBUG(info = True)
        top = self.xmldoc.documentElement
        self.__containdataset = False
        if top.childNodes:
            self.__containdataset = True
        return self.__containdataset

#-------------------------------------------------------------------------------
    def removeCalculatedSpectrum(self):
#-------------------------------------------------------------------------------
        """
        Remove a calculated spectrum...
        """
        DEBUG(info = True)
        if self.CurrentSpectrum is None:
            return


        # Avoid update
        #---------------
        self.isLocked = True
        # Store the current dataset reference
        #------------------------------------
        stkDataset = self.Dataset

        # Delete the xml node item
        #--------------------------

        parentNode = self.CurrentSpectrum.parentNode
        parentNode.removeChild(self.CurrentSpectrum)

        # Update the node graph
        #-----------------------
        top = self.xmldoc.documentElement
        self.Tree.isLocked = True # prevent update during parsing
        self.Tree.parse(top, None)
        self.Tree.isLocked = False

        # Restore the dataset reference
        #------------------------------
        self.Dataset = stkDataset

        self.isLocked = False
        self.isModified = True

#-------------------------------------------------------------------------------
    def addCalculatedSpectrum(self,calculateddata = None):
#-------------------------------------------------------------------------------
        """
        Add a calculated spectrum...
        This should happen when compute is selected
        """
        DEBUG(info = True)

        self.isLocked = True

        dataset = self.Dataset
        datasetname = dataset.getAttribute("Name")

        # Is there a spectra container?
        #-------------------------------
        spectra = self.CurrentSpectra
        if spectra is None:
            # Add spectra container
            Id = wx.NewId()
            spectra = self.xmldoc.createElement(prjkinds[PYP_SPECTRA])
            dataset.appendChild(spectra)
            spectra.setAttribute("Id", str(Id))
            spectra.setAttribute("Name", "Spectra")
            spectra.setAttribute("Parent", datasetname)
            spectra.setAttribute("Kind", str(PYP_SPECTRA))
            spectra.setAttribute("Property", "")

        # Create a new calculated spectra
        #---------------------------------
        nspec = calculateddata["nspec"]

        if int(calculateddata["kind"]) in L_2DS:
            typ = PYP_CALCULATED2D
        else:
            typ = PYP_CALCULATED1D

        if nspec > 1:
            # There is several components
            # Add a calculated spectra container
            #------------------------------------
            Id = wx.NewId()
            calcspectra = self.xmldoc.createElement(prjkinds[PYP_CALCSPECTRA])
            spectra.appendChild(calcspectra)
            calcspectra.setAttribute("Id", str(Id))
            calcspectra.setAttribute("Name", "Calculated Spectra")
            calcspectra.setAttribute("Parent", datasetname)
            calcspectra.setAttribute("Kind", str(PYP_CALCSPECTRA))
            calcspectra.setAttribute("Property", str(calculateddata["kind"]))

        for k in range(nspec):
            Id = wx.NewId()
            spectrum = self.xmldoc.createElement(prjkinds[typ])
            spectrumname = "Calculated"
            if nspec > 1:
                calcspectra.appendChild(spectrum)
                spectrumname = spectrumname + "::" +str(k)
                # TODO: use label and variables
            else:
                spectra.appendChild(spectrum)
            spectrum.setAttribute("Id", str(Id))
            spectrum.setAttribute("Name", spectrumname)
            spectrum.setAttribute("Parent", datasetname)
            spectrum.setAttribute("Kind", str(typ))
            spectrum.setAttribute("Property", str(calculateddata["kind"]))
            text = calculateddata["spectra"][k].encode('base64_codec')
            textNode = self.xmldoc.createTextNode(text)
            spectrum.appendChild(textNode)

        self.isModified = True
        self.isNewPlot = True
        self.isLocked = False

        # Display the current id node
        DEBUG("parse")
        self.Tree.isLocked = True # prevent update during parsing
        self.Tree.parse(self.xmldoc.documentElement, None)
        self.Tree.isLocked = False
        DEBUG("end parse")
        self.SelectedNode = dataset
        self.SelectedNode = self.CurrentSpectra

#-------------------------------------------------------------------------------
# Selected Node property
#-------------------------------------------------------------------------------
    def _getSelectedNode(self):
#-------------------------------------------------------------------------------
        if self.Tree.GetSelection() is None:
            return None
        try:
            datas = self.Tree.GetPyData(self.Tree.GetSelection())
            self.__selectednode = datas[1]
        except:
            self.__selectednode= None
        return self.__selectednode

#-------------------------------------------------------------------------------
    def _setSelectedNode(self, node):
#-------------------------------------------------------------------------------
        if node is None: return

        self.__selectednode = node
        Id = int(node.attributes["Id"].value)
        # get the tree item associated with this node
        treeitem = self.Tree.findTreeItemFromId(Id)
        # Select it

        if treeitem and  treeitem != self.Tree.GetSelection():
            self.Tree.SelectItem(treeitem)

    SelectedNode=property(fget = _getSelectedNode,
                          fset = _setSelectedNode,
                          doc = "Current Selected Node property")

#-------------------------------------------------------------------------------
# Property isModified
#-------------------------------------------------------------------------------
    def _getModify(self):
#-------------------------------------------------------------------------------
        self.__modify = self.__modify or \
                        self.Tree.isModified or self.Book.isModified
        return self.__modify

#-------------------------------------------------------------------------------
    def _setModify(self, value):
#-------------------------------------------------------------------------------
        self.__modify = value

    isModified = property(
                        fget = _getModify,
                        fset = _setModify,
                        doc = "modify status of the project")

#-------------------------------------------------------------------------------
# Property isLocked
#-------------------------------------------------------------------------------
    def _getLock(self):
#-------------------------------------------------------------------------------
       return self.__locked

#-------------------------------------------------------------------------------
    def _setLock(self, value):
#-------------------------------------------------------------------------------
        self.__locked = value

    isLocked = property(
                        fget = _getLock,
                        fset = _setLock,
                        doc = "modify lock status of the project")

#-------------------------------------------------------------------------------
# Property CurrentParameters (experimental)
#-------------------------------------------------------------------------------
    def _getExperimentalParameters(self):
#-------------------------------------------------------------------------------
        # get the current script and then the experimental parameter child
        script = self.CurrentScript
        self.__parameters = None
        if script is not None:
            for childnode in script.childNodes:
                if hasattr(childnode, "getAttribute") \
                      and int(childnode.getAttribute("Kind")) == PYP_PARAMETERS:
                    self.__parameters = childnode
        return self.__parameters

    CurrentParameters = property(fget = _getExperimentalParameters,
                                      doc = "Experimental parameters")

#-------------------------------------------------------------------------------
# Property CurrentScript
#-------------------------------------------------------------------------------
    def _getScript(self):
#-------------------------------------------------------------------------------
        # get the current dataset
        dataset = self.Dataset
        self.__script = None
        if dataset is not None:
            # get the current script
            for childnode in dataset.childNodes:
                if hasattr(childnode, "getAttribute") \
                      and int(childnode.getAttribute("Kind")) == PYP_SCRIPT:
                    self.__script = childnode

        return self.__script

    CurrentScript = property(fget = _getScript,
                             doc = "Get CurrentScript page (ReadOnly) ")

#-------------------------------------------------------------------------------
# Property CurrentCommands
#-------------------------------------------------------------------------------
    def _getCommands(self):
#-------------------------------------------------------------------------------
        # get the current dataset
        dataset = self.Dataset
        self.__commands = None
        if dataset is not None:
            # get the current script
            for childnode in dataset.childNodes:
                if hasattr(childnode, "getAttribute") \
                      and int(childnode.getAttribute("Kind")) == PYP_FIT:
                    self.__commands = childnode

        return self.__commands

    CurrentCommands = property(fget = _getCommands,
                             doc = "Get Currentcommands node")

#-------------------------------------------------------------------------------
# Property CurrentSpectra
#-------------------------------------------------------------------------------
    def _getSpectra(self):
#-------------------------------------------------------------------------------
        # get the current dataset
        dataset = self.Dataset
        self.__spectra = None
        if dataset is not None:
            # get the current spectrum
            for childnode in dataset.childNodes:
                if hasattr(childnode, "getAttribute") \
                      and int(childnode.getAttribute("Kind"))==PYP_SPECTRA:
                    self.__spectra = childnode
        return self.__spectra

    CurrentSpectra = property(fget = _getSpectra,
                             doc = "Get CurrentSpectra node")

#-------------------------------------------------------------------------------
# Property CurrentSpectrum
#-------------------------------------------------------------------------------
    def _getSpectrum(self):
#-------------------------------------------------------------------------------
        # get the current dataset
        spectra = self.CurrentSpectra
        self.__spectrum = None
        if spectra is not None:
            # get the current spectrum
            for childnode in spectra.childNodes:
                if hasattr(childnode, "getAttribute") \
                      and int(childnode.getAttribute("Kind")) in PYP_CALCULATED:
                    self.__spectrum = childnode
        return self.__spectrum

    CurrentSpectrum = property(fget = _getSpectrum,
                             doc = "Get CurrentSpectrum node (ReadOnly) ")

#-------------------------------------------------------------------------------
# Property CurrentExperiment (experimental)
#-------------------------------------------------------------------------------
    def _getExperimentalSpectrum(self):
#-------------------------------------------------------------------------------
        spectra = self.CurrentSpectra
        self.__experiment = None
        if spectra is not None:
            for childnode in spectra.childNodes:
                if hasattr(childnode, "getAttribute") \
                      and int(childnode.getAttribute("Kind")) in PYP_EXPERIMENTAL:
                    self.__experiment = childnode

        return self.__experiment

    CurrentExperiment = property(fget = _getExperimentalSpectrum,
                                      doc = "Experimental spectrum")

#-------------------------------------------------------------------------------
# Property isError
#-------------------------------------------------------------------------------
    def _getError(self):
#-------------------------------------------------------------------------------
        """
        Error if there is an error in the open book pages
        """
        return self.Book.isError

    isError = property(fget = _getError, doc = "isError (Read only property)")


# ################
# module functions
# ################

#-------------------------------------------------------------------------------
def kind_of_node(node):
#-------------------------------------------------------------------------------
    """ Determine node kind """
    if node.nodeType == TEXT_NODE:
        return -1  # no kind
    else:
        kind = node.getAttribute("Kind")
        return int(kind)


