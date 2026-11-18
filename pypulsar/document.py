#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      document.py
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
 <purpose>
"""
#------------------------------------------------------------------

__docformat__="epytext"


import os

#=============================
class Document:
#=============================
    """
    Document class implementation

    Local variables:

    self.__path :  full path of the document (see getPath)
    self.__root: path of the parent directory of the current document dir
    self.__dirpath: long path of the directory containing the document
    self.__dir: directory name
    self.__name:  filename with extension
    self.__base: filename without extension
    self.__ext: extension

    """
    #---------------------------------
    def __init__(self, fullpath=None):
    #---------------------------------
        """
        Create a Document instance.
        @param fullpath: fullpath of the document
        """
        self.__name = None        # filename with extension
        self.__base = None        # filename without extension
        self.__ext = None         # file extension

        self.__path = None        # full path to the document
        self.__dirpath = None     # full path to the container directory (dataset)
        self.__root = None        # full path to the upper level container directory (project)

        self.__property = "<Property/>"

        # Set this initial variable from arg fullpath
        if fullpath is None: return
        self._SetPathElements(fullpath)

        # check link to the document on the disk or create it if necessary
        self._Open()

    #---------------------
    def getProperty(self):
    #---------------------
        """
        Get Property string of the document
        @rtype: String
        @return: Property string (by default: '<Property/>')
        """
        return self.__property

    #---------------------
    def getName(self):
    #---------------------
        """
        Get Name of the document (filename with extension)
        @rtype: String
        @return: Name of the document
        """
        return self.__name

    #-----------------
    def getBase(self):
    #-----------------
        """
        Get base Name of the document (filename without extension)
        @rtype: String
        @return: Base Name of the document
        """
        return self.__base

    #----------------
    def getExt(self):
    #----------------
        """
        Get Extension of the document
        @rtype: String
        @return: Extension of the document
        """
        return self.__ext

    #-----------------
    def getPath(self):
    #-----------------
        """
        Get path of the document
        @rtype: String
        @return: path of the document
        """
        return self.__path

    #------------------------
    def setPath(self, fullpath):
    #------------------------
        """
        Method to set the path of the document from fullpath
        Also try to open the document
        @param fullpath:fullpath of the document
        @type: String
        """
        self._SetPathElements(fullpath)
        self._Open()

    def getDirpath(self):
        """
        Get directory name
        @rtype: String
        @return: directory name of the document
        """
        return self.__dirpath

    def getRoot(self):
        """
        Get root directory path
        @rtype: String
        @return: root directory path of the document
        """
        return self.__root

    def getInfo(self):
        """
        Get info
        @rtype: String
        @return: info text
        """
        return self.__info

    def setInfo(self, value):
        """
        Method to set info
        @param value: dictionary of info to set
        @type: dict
        """
        self.__info = value

    def delInfo(self):
        """
        delete info disctionnary
        """
        self.__info= {}

    def getDir(self):
        """
        Get directory name
        @rtype: String
        @return: name of the directory containing the document
        """
        return self.__dir

    #---------------------------
    def _SetPathElements(self, fullpath):
    #---------------------------
        """
        Private method: get path elements from fullpath
        and set the path and file names variable
        @param fullpath: full path
        """
        if fullpath is None: return

        self.__path = os.path.realpath(fullpath)
        self.__dirpath, self.__name = os.path.split(self.__path)
        self.__base, self.__ext = os.path.splitext(self.__name)
        self.__root, self.__dir = os.path.split(self.__dirpath)

    #-------------------------------
    def _Open(self):
    #-------------------------------
        """
        Private method
        Link to the document or Create physically a new document
        """
        #Create a default file if this file doen't exist
        if self.__path and not os.path.exists(self.__path):
            return self._CreateDefaultDocument()

    #---------------------
    def _CreateDefaultDocument(self):
    #---------------------
        """
        Private method
        Write a default document
        @return: True if success
        """
        try:
            f = file(self.__path, 'wb')
            f.write('<?xml version="1.0" encoding="utf-8"?><Project Name="'+self.__base+'"/>')
            f.close()
            return True
        except:
            if 'f' in locals():   #Test if variable exist
                f.close()
            return False

    #--------------
    def read(self):
    #--------------
        """
        Return contents of file.
        @return: Text that was read from file or None
        @rtype: String (or none)
        """
        if self.__path and os.path.exists(self.__path):
            f = file(self.__path, 'rb')
            try:
                return f.read()
            finally:
                f.close()
        else:
            return None

    #-----------------
    def CanUndo(self):
    #-----------------
        """
        Return undo status of the document
        @return: True if it can be undone
        @rtype: bool
        """
        if self.__path and os.path.exists(self.__path+".tmp"):
            return True
        else:
            return False

    #--------------
    def revert(self):
    #--------------
        """
        Return contents of file.
        @return: Text that was read from file or None
        """
        if self.__path and os.path.exists(self.__path+".tmp"):
            f = file(self.__path+".tmp", 'rb')
            try:
                return f.read()
            finally:
                f.close()
        else:
            self.read()

    #---------------------
    def write(self, text):
    #---------------------
        """
        Write text to file.
        @param text: Text to write
        @return: True if success
        """
        returned=False
        try:
            f = file(self.__path, 'wb')
            tmp= file(self.__path+".tmp", 'wb')
            f.write(text)
            f.close()
            returned=True
        except:
            if f:
                f.close()
        try:
            tmp= file(self.__path+".tmp", 'wb')
            tmp.write(text)
            tmp.close()
        except:
            if f:
                f.close()
        return returned

    #----------------------
    def openDocument(self):
    #----------------------
        """
        open document
        @return: file instance f
        @rtype: file
        """
        return open(self.__path)

    #--------------------------
    def closeDocument(self, f):
    #--------------------------
        """
        Close document
        @param f: file instance
        """
        f.close()

###-------------------------
##if __name__ == '__main__':
###-------------------------
##    """
##    test of this class
##    """
##    doc=Document("../workspace/essai.pulse")
##    print doc.read()
##    print doc.getName()
##    print "------"
##    print "ext "+doc.getExt()
##    print "base "+doc.getBase()
##    print "dir "+doc.getDir()
##    print "root "+doc.getRoot()
##    print "path "+doc.getPath()
