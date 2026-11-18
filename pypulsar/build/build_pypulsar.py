#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
"""
pyPULSAR Project:
=================
    - Copyright (C) 2006-2007, Christian Fernandez and Jean-Paul Amoureux
    - JPA: Unite de Catalyse et Chimie du Solide, Lille, France.
    - CF: Laboratoire Catalyse et Spectrochimie, Caen, France.

LICENSE:
========
 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU General Public License (GPL)
 as published by the Free Software Foundation; either version 2
 of the License, or (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 To read the license please visit http://www.gnu.org/copyleft/gpl.html

PURPOSE OF THIS FILE:
=====================
 Provide building command facility
 to make a new release
 Syntax   build_pypulsar.py [debug]
            debug = 1 for console output
 works for Windows only
"""

__docformat__="epytext"

#Go to Top directory
import os
from os.path import normpath
import sys
import subprocess
import string, re

#define DIRs
SRCDIR=normpath("P:/pyPulsar/trunk/pypulsar")
os.chdir(SRCDIR)
PYINSTALLER=normpath(SRCDIR+"/../pyinstaller")
BUILDDIR=normpath(SRCDIR+"/build")
DESTDIR=normpath(BUILDDIR+"/dist")
ADDTODIST=normpath(BUILDDIR+'/add_to_dist')
SVNDIR=normpath(SRCDIR+"/.svn")


print PYINSTALLER
print SRCDIR
print BUILDDIR
print ADDTODIST
print DESTDIR

#SVN update of the working directory
retcode = subprocess.call("svn update")
retcode = subprocess.call("svn info")
#COMMENT: todo later - use module svn to perform these commands but I didn't find a documentation

print "Update version number"
debug = False
version= "0.2.alpha1"
initialsvnrevision = 383 # revision number for the first 0.2 version release

if len(sys.argv)>1:
    debug= sys.argv[1]
    print "debug",debug
    print int(debug)==1

f=open(normpath(SVNDIR+"/entries"),"rb")
lines=f.readlines()
print lines[0:10]

#increment the version number because a commit will be done at the end of this build
svn=str( int(string.strip(lines[3]))+1)
date=string.strip(lines[9][0:10])+" "+string.strip(lines[9][12:19])
revision = str(int(svn)-initialsvnrevision)
versionstring = version+"."+revision+"-"+svn
f.close()

print "Building pyPulsar-%s"%(versionstring)
retcode = subprocess.call(normpath("C:/Program Files/Windows NT/Accessoires/wordpad.exe")+" "+normpath(BUILDDIR+"/NEWS.rtf"))

f=open(normpath(BUILDDIR+"/version.py"),"wb")
lines=[]
lines.append("__PROJECT_VERSION__ = '"+version+"'\n")
lines.append("__PROJECT_REVISION__ = '"+revision+"'\n")
lines.append("__PROJECT_SVNREVISION__ = '"+svn+"'\n")
lines.append("__PROJECT_REVISION_DATE__='"+date+"'\n")
lines.append("versionString='"+versionstring+"'\n")
print "version.py"
print lines
f.writelines(lines)
f.close()

#update version number
f=open(normpath(BUILDDIR+"/pypulsar.spec"),"rb")
lines=f.readlines()
f.close()

#update pypulsar.spec file
f=open(normpath(BUILDDIR+"/pypulsar.spec"),"wb")
lines[0]="#Don't modify the following lines ******************************\n"
lines[1]="__version__='"+versionstring+"'\n"
lines[2]="__console__="+str(int(debug)==1)+"\n"
lines[3]="#Don't modify the above lines ************************************\n"
f.writelines(lines)
f.close()

#notes
# to make it working i have modified the matplotlib/numerix/__init__.py
#around line 172 (because they generate errors
# la = linear_algebra
# ra = random_array

#build everything
print "build distribution files"
BUILD=normpath(PYINSTALLER+"/build.py")
retcode = subprocess.call("python -O "+normpath(BUILD)+" "+normpath(BUILDDIR+"/pypulsar.spec"))
if retcode!=0:
    print "error "+str(retcode)+", Build Stopped."
    raise SystemExit

print "copy additional files"
print "xcopy  "+normpath(ADDTODIST+"/*.*")+"  "+DESTDIR+" /S/D/Y"
retcode = subprocess.call("xcopy  "+normpath(ADDTODIST+"/*.*")+"  "+DESTDIR+" /S/D/Y")
if retcode!=0:
    raise SystemExit
print "xcopy  "+SRCDIR+"workspace\\*.pul  "+DESTDIR+"workspace\\ /S/D/Y"
retcode = subprocess.call("xcopy  "+SRCDIR+"workspace\\*.pul  "+DESTDIR+"workspace\\ /S/D/Y")
if retcode!=0:
    raise SystemExit
print "xcopy  "+SRCDIR+"workspace\\*.cfg  "+DESTDIR+"workspace\\ /S/D/Y"
retcode = subprocess.call("xcopy  "+SRCDIR+"workspace\\*.cfg  "+DESTDIR+"workspace\\ /S/D/Y")
if retcode!=0:
    raise SystemExit

#make the setup file
print "build setup"
f=open(BUILDDIR+"pyPulsar.iss","rb")
lines=f.readlines()
f.close()
f=open(BUILDDIR+"pyPulsar.iss","wb")
lines[4]='#define MyAppVerName "pyPulsar-'+version+'.'+revision+'"\n'
lines[32]='VersionInfoVersion='+version+'.'+revision+'\n'
f.writelines(lines)
f.close()
retcode = subprocess.call("C:\\Program Files\\Inno Setup 5\\Compil32.exe /cc "+BUILDDIR+"pyPulsar.iss")
if retcode!=0: raise SystemExit

exit()
###Make a commit
##print "Committing"
##rep=raw_input("Should I commit last changes to SVN repository (y/n)?")
##if string.lower(str(rep)[0])=="y":
##    cmd='svn commit --message "Last commit before release '+version+'.'+revision+'"'
##    print cmd
##    retcode = subprocess.call(cmd)
##else:
##    retcode=1
##
##if retcode!=0:
##    print " no commit was done!"
##    raise SystemExit
##
###Make a tag
##print "Tagging"
##rep=raw_input("Should I make a new release tag in SVN repository (y/n)?")
##if string.lower(str(rep)[0])=="y":
##    cmd='svn copy https://pypulsar.svn.sourceforge.net/svnroot/pypulsar/trunk '+ \
##                   ' https://pypulsar.svn.sourceforge.net/svnroot/pypulsar/tags/pyPulsar-'+version+'.'+revision+ \
##                   ' --message "Tagging of release '+version+'.'+revision+'"'
##
##    print cmd
##    retcode = subprocess.call(cmd)
##    if retcode!=0:
##        print "no tagging done"
##        raise SystemExit
##
