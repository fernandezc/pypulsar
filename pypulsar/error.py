#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      error.py
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

 User Errors Class

"""
#-------------------------------------------------------------------------------

__docformat__="epytext"

#===============================================================================
class Error(Exception):
#===============================================================================
    """
    Base class for exceptions in this module.
    """
    pass

#===============================================================================
class AbortWarning(Error):
#===============================================================================
    """
    Exception raised by a user interuption.

    Attributes:
        - expression -- input expression in which the error occurred
        - message -- explanation of the error
    """

    def __init__(self):
        self.message = "Script execution interrupted (by user)."

#===============================================================================
class UserError(Error):
#===============================================================================
    """
    Attributes:
        - message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message

