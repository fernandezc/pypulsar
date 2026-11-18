#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      process.py
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
 External process handling
"""

__docformat__="epytext"


#FIXME: There is a bug during successive calculation on different dataset. Clear history???

import wx
import sys
import common as cm
from common import LOG_DEBUG as DEBUG
from functions import *
from editor import Editor
import traceback
import threading, Queue
from wx.lib.newevent import NewEvent
import pickle
from error import *
from xml.dom import minidom
from processing import baseline
import wx.lib.pubsub as pubsub
import plot
from spectres import Spectre
import string

ID_BEGIN=wx.NewId()
wxWorkerDone, EVT_WORKER_DONE= NewEvent()

#===============================================================================
class Worker(threading.Thread):
#===============================================================================
    requestID = 0
#-------------------------------------------------------------------------------
    def __init__(self, parent, requestQ, resultQ, **kwds):
#-------------------------------------------------------------------------------
        threading.Thread.__init__(self, name="Simulation", **kwds)
        self.parent=parent
        self.setDaemon(True)
        self.requestQ = requestQ
        self.resultQ = resultQ
        self.start()

#-------------------------------------------------------------------------------
    def beginProcess(self, callable, *args, **kwds):
#-------------------------------------------------------------------------------
        Worker.requestID +=1
        cm.LOG_INFO("Started script evaluation... process ID:"+
                                                         str(Worker.requestID))
        print "Started script evaluation... process ID:",str(Worker.requestID)
        self.requestQ.put((Worker.requestID, callable, args, kwds))
        return Worker.requestID

#-------------------------------------------------------------------------------
    def run(self):
#-------------------------------------------------------------------------------
        self.running=True
        while self.running:
            requestID, callable, args, kwds = self.requestQ.get()
##            try:
            self.resultQ.put((requestID, callable(*args, **kwds)))
            evt = wxWorkerDone()
            wx.PostEvent(self.parent.edit, evt)
##            except:
##                print "Exception (most likely raised during interpreter shutdown)"

#===============================================================================
class Process(): #Editor):
#===============================================================================
    """
    Class Pulsar process:
                         Compile, Run script and show result in a console window
    """
#-------------------------------------------------------------------------------
    def __init__(self, parent):
#-------------------------------------------------------------------------------
        """
        """
        #TODO: add a toolbar
        self.edit=Editor(parent, style = wx.TE_MULTILINE|wx.TE_READONLY)
        # define some usefull attributes
        self.parent = parent
        self.frame = parent.parent
        self._mgr = parent.parent._mgr

        # Define the log
        self.logger=cm.pyLog(self)

        wx.Log_SetActiveTarget(self.logger)

        # Thread process
        self.requestQ = Queue.Queue()
        self.resultQ = Queue.Queue()
        self.worker = Worker(self, self.requestQ, self.resultQ)


        # private attributes for properties
        self.__issuccess=True
        self.__isrunning=False
        self.__iserror=False
        self.__progress= self.parent.progress

        # define some flags
        self.edit.SearchEnabled=False  # not necessary to search in this window

        # Bind events
        self.edit.Bind(wx.EVT_TIMER, self.onTimer)
        self.edit.Bind(EVT_WORKER_DONE, self.onWorkerDone)

        # define a timer and start it
        self.timer = wx.Timer(self.edit, -1)

        self.reset_pulsar = reset #from forpulsar

#------------------------------------------------------------------------------
    def canRun(self):
#------------------------------------------------------------------------------
        """
        Determine if a script can be executed
        """
        self.Project= self.parent.parent.Project
        if self.Project is None:
            return False

        if not self.isRunning and not self.isError \
                              and self.Project.Dataset \
                              and not self.Project.isError \
                              and not self.Project.isModified:
            return True
        else:
            return False

#-------------------------------------------------------------------------------
    def showprogress(self):
#-------------------------------------------------------------------------------
        self.__progress.Show()
        if hasattr(self,"__timer"):
            self.__timer.Start(100)
        self.__progress.Pulse()

#-------------------------------------------------------------------------------
    def hideprogress(self):
#-------------------------------------------------------------------------------
        self.__progress.Hide()
        if hasattr(self,"__timer"):
            self.__timer.Stop()

#-------------------------------------------------------------------------------
    def compute(self, fitting = False, fitplotter= None, experiment = None):
#-------------------------------------------------------------------------------
        self.showprogress()

        self.reset_pulsar()

        self.scriptpage = scriptpage = self.script
        self.expparampage = expparampage = self.expparam
        self.commandspage = commandspage = self.commands
        parameters.keepgoing = True
        l=locals()

        try:
            ceditor = None
            if commandspage is not None:
                commandsContent="ceditor='COMMAND'\n"+ \
                                    commandspage.Content+ \
                                    "\nceditor=None\n"
            if expparampage is not None:
                expparamContent="ceditor='EXPPAR'\n"+ \
                                    expparampage.Content+ \
                                    "\nceditor=None\n"
            scriptContent="ceditor='SCRIPT'\n"+ \
                                    scriptpage.Content+ \
                                    "\nceditor=None\n"
            indent = ""
            # first check commands parameters
            #--------------------------------
            header = ["from functions import *"]
            header +=["TOLERANCE=1.e-4"]
            header +=["MAX_ITERATIONS=None"]
            header +=["MAX_CALLS=None"]
            header +=["FIXED=True"]
            header +=["METHOD=0"]
            header +=["FIT_INTENSITY=True"]
            header +=["FIT_BASELINE=True"]
            header +=["BASELINE_ORDER=1"]
            header +=["global FitParameter"]
            header +=["FitParameter = FitParameters()"]
            header +=["global FitStep"]
            header +=["FitStep = FitSteps(FitParameter)"]
            header +=["if experiment is not None:"]
            header +=["\tphcursor=abs(experiment).argmax()"]
            header +=["else:"]
            header +=["\tphcursor=0"]

            if commandspage is not None:
                len_header=1
                header += commandsContent.splitlines()
                _script=""
                for i in header:
                    _script+=i+"\n"
                code=compile(_script, '<script>', 'exec')
                exec(code)

                # Check is fitting is possible
                #-----------------------------
                if experiment is None and fitting:
                    raise UserError, "no data to fit!"

            # now check experimental parameters
            #---------------------------
            if expparampage is not None:
                len_header=len(header)
                expparamlist = header + expparamContent.splitlines()
                _script = ""
                for i in expparamlist:
                    _script += i + "\n"
                code=compile(_script, '<script>', 'exec')
                exec(code)

            # finally check and execute the complete script
            #-----------------------------------------------
            _script = ""
            if commandspage is not None and fitting:
                # we need to create the function f
                #----------------------------------
                header += ["\n\ndef calculated(phcursor=phcursor,"+\
                            "fitting=True):"]
                header += ["\n\ttry:"]
                indent = "\t\t"  # indent
            len_header=len(header)
            for i in header:
                _script += i + "\n"
            if expparampage is not None:
                expparamlist = expparamContent.splitlines()
                len_header = len_header + len(expparamlist)
                for i in expparamlist:
                    _script += indent + i + "\n"
            scriptlist = scriptContent.splitlines()
            simstr = "sim1"
            psim = re.compile('(\S+)=Simulation\((.*)\)')
            pcursor = re.compile('set_phases\((.*)\)')
            for i in scriptlist:
                # search the Simulation() class instance
                m = psim.search(i)
                if m:
                    simstr = m.group(1)
                    arg = string.strip(m.group(2))+","
                    if arg==",": arg=""
                    i= simstr+"=Simulation("+arg+"fitting=fitting)"
                m = pcursor.search(i)
                if m:
                    phases = m.group(1)
                    i= simstr+".set_phases("+phases+",phcursor=phcursor)"
                _script += indent + i + "\n"

            # add the fitting command
            # (given that data is an array with the data to fit)
            #---------------------------------------------------
            if commandspage is not None and fitting:
                _script += "\n\texcept AbortWarning:\n\t\tpass"
                _script += "\n\n\tif locals().has_key('"+simstr+"'):"
                _script += "\n\n\t\treturn "+simstr+".calculatedSpectra, "
                _script += simstr+".Data"
                _script += "\n\n\telse: return None"
                cmds="""
\nceditor='SCRIPTCOMPLEMENT'\n
# Fit commands
#-------------
issuccess, data_fitted, data_spec = executefit(
    calculated, experiment,
    fitplotter, FitParameter,
    FitStep,
    method= METHOD,
    errfunc = ERRFUNC,
    xtol = TOLERANCE,
    ftol = TOLERANCE,
    maxiter = MAX_ITERATIONS,
    maxfun = MAX_CALLS,
    fitintensity = FIT_INTENSITY ,
    fitbaseline = FIT_BASELINE,
    baselineorder = BASELINE_ORDER)

"""
                _script += cmds
            else:
                _script += "\ndata_spec="+simstr+".Data"

            DEBUG(_script)
            issuccess = 0
            data_fitted = {}
            code=compile(_script, '<script>', 'exec')
            DEBUG("start execution...")
            exec code
            DEBUG("end execution...")
            return issuccess, data_fitted, data_spec

        # Errors
        #--------
        except SyntaxError, inst:
            #atttributes inst ->(message, (filename, lineno, offset, line))
            #for easier access to the details.
            editor, len_header = self.set_editor(ceditor, _script)
            message=inst.args[0]
            lineno=inst.args[1][1]-len_header
            offset=inst.args[1][2]
            line=inst.args[1][3]
            cm.LOG_ERROR("")
            cm.LOG_ERROR("SYNTAX, line", lineno, message)
            self.highlightline(editor,lineno,offset)

        except AttributeError, (message,):
            if l.has_key("_script"):
                editor, len_header = self.set_editor(ceditor, _script)
            tb=traceback.extract_tb(sys.exc_traceback)
            if parameters.loglevel == DEBUGLEVEL or fitting: print tb
            lineno=tb[1][1]-len_header
            cm.LOG_ERROR("ATTRIBUTE error, in line", lineno, message)
            self.highlightline(editor,lineno)

        except NameError, (message,):
            editor, len_header = self.set_editor(ceditor, _script)
            tb=traceback.extract_tb(sys.exc_traceback)
            if parameters.loglevel == DEBUGLEVEL or fitting: print tb
            lineno=tb[1][1]-len_header
            cm.LOG_ERROR("NAME error, line", lineno, message)
            self.highlightline(editor,lineno)

        except TypeError, (message,):
            editor, len_header = self.set_editor(ceditor, _script)
##                try:
            tb=traceback.extract_tb(sys.exc_traceback)
            if parameters.loglevel == DEBUGLEVEL or fitting: print tb
            lineno=tb[1][1]-len_header
            cm.LOG_ERROR("TYPE error, in line", lineno, message)
            self.highlightline(editor,lineno)
##                except:
##                    pass

        except IndexError, (message,):
            editor, len_header = self.set_editor(ceditor, _script)
            tb=traceback.extract_tb(sys.exc_traceback)
            if parameters.loglevel == DEBUGLEVEL or fitting: print tb
            lineno=tb[1][1]-len_header
            cm.LOG_ERROR("INDEX error, in line", lineno, message)
            self.highlightline(editor,lineno)

        except RuntimeError, (message,):
            print "most likely raised during shutdown"
            sys.exit()

        except IOError, (message,):
            editor, len_header = self.set_editor(ceditor, _script)
            tb=traceback.extract_tb(sys.exc_traceback)
            if parameters.loglevel == DEBUGLEVEL or fitting: print tb
            lineno=tb[1][1]-len_header
            cm.LOG_ERROR("I/O error, in line", lineno, message)
            self.highlightline(editor,lineno)

        except ValueError, message:
            editor, len_header = self.set_editor(ceditor, _script)
            tb=traceback.extract_tb(sys.exc_traceback)
            if parameters.loglevel == DEBUGLEVEL or fitting: print tb
            lineno=tb[1][1]-len_header
            cm.LOG_ERROR("VALUE error, in line", lineno, message)
            self.highlightline(editor,lineno)

        except MemoryError, message:
            editor, len_header = self.set_editor(ceditor, _script)
            tb=traceback.extract_tb(sys.exc_traceback)
            if parameters.loglevel == DEBUGLEVEL or fitting: print tb
            lineno=tb[1][1]-len_header
            cm.LOG_ERROR("VALUE error, in line", lineno, message)
            self.highlightline(editor,lineno)

        except KeyError, (message,):
            editor, len_header = self.set_editor(ceditor, _script)
            tb=traceback.extract_tb(sys.exc_traceback)
            if parameters.loglevel == DEBUGLEVEL or fitting: print tb
            editor, lineno = self.lookfor(_script, message)
            cm.LOG_ERROR("KEY error in line ", lineno,
                                            " key not found:'"+ message+"'")
            self.highlightline(editor,lineno)
            raise KeyError, (message,)

        except UserError, message:
            editor, len_header = self.set_editor(ceditor, _script)
            tb=traceback.extract_tb(sys.exc_traceback)
            if parameters.loglevel == DEBUGLEVEL or fitting: print tb
            lineno=tb[1][1]-len_header
            cm.LOG_ERROR("KEY error, in line",  lineno, message)
            self.highlightline(editor,lineno)

        except AbortWarning, message:
            editor, len_header = self.set_editor(ceditor, _script)
            tb=traceback.extract_tb(sys.exc_traceback)
            if parameters.loglevel == DEBUGLEVEL or fitting: print tb
            lineno=tb[1][1]-len_header
            cm.LOG_WARNING("Execution interrupted:",message)

        except:
            editor, len_header = self.set_editor(ceditor, _script)
            tb=traceback.extract_tb(sys.exc_traceback)
            if parameters.loglevel == DEBUGLEVEL or fitting: print tb
            lineno=tb[1][1]-len_header
            message=tb
            cm.LOG_ERROR(  "\n\tUNHANDLED error, in line", lineno,
                        "\n\t", message,
                        "\n\t(please report this problem to the developpers)")
            self.highlightline(editor,lineno)

        self.editor = editor
        pubsub.Publisher().sendMessage("UPDATE")

        return -1, None, None

    def lookfor(self,script,strg):

        i = 1
        l = script.splitlines()
        ceditor=None
        for item in l:
            if string.strip(item)=="":
                i += 1
                continue

#            print "strg",strg,"ceditor",ceditor
            if item.find("COMMAND") != -1: ceditor='COMMAND'
            if item.find("SCRIPT") != -1: ceditor='SCRIPT'
            if item.find("SCRIPTCOMPLEMENT") != -1: ceditor='SCRIPT'
            if item.find("EXPPAR") != -1: ceditor='EXPPAR'
            if item.find(strg) != -1 and ceditor is not None:
                editor, lh = self.set_editor(ceditor,script)
                return editor, i - lh
            i += 1

#-------------------------------------------------------------------------------
    def set_editor(self, ceditor, script):
#-------------------------------------------------------------------------------
        try:
            editor = self.scriptpage.editor
        except:
            return None, 0

        if ceditor is None: return None,0

        lineno = -1
        if ceditor=='COMMAND':
            editor = self.commandspage.editor
        elif ceditor=='EXPPAR':
            editor = self.expparampage.editor
        else:
            editor = self.scriptpage.editor

        if editor is not None:
            editor.runError = False
            l = script.splitlines()
            nl=[]
            for i in l:
                nl.append(string.strip(i))
            lineno = nl.index("ceditor='"+ceditor+"'")+1
            if ceditor=='SCRIPTCOMPLEMENT':
                # we must try another way to find the error
                lineno == 0
        return editor, lineno

#-------------------------------------------------------------------------------
    def highlightline(self, editor, lineno, offset=0):
#-------------------------------------------------------------------------------
        self.hideprogress()

        if editor is None or lineno==-1:
            return
        try:
            editor.highlightline(lineno-1,offset)
            editor.ScrollToLine(max(0,lineno-10))
            editor.isRunError=True
            editor.errorline=lineno
        except:
            pass

#-------------------------------------------------------------------------------
    def runScript(self, fitting = False):
#-------------------------------------------------------------------------------
        """
        Prepare the simulation, run it and show the resulting spectrum
        @param name: name of the script to execute
        @param checkonly: True is the calculation is bypassed (Syntax checking only)
        @return: True if the calculation was successful
        """
        self.perspective_default = self._mgr.SavePerspective()

        # Clear the log window
        #----------------------
        self.clearLog()

        # In principle canRun should be True here
        #----------------------------------------
        if not self.canRun():
            return

        # Set Computing and Error flags
        #------------------------------
        self.runError=False

        # we remove the page containing the calculated spectra
        # will be recreated after the calculation
        #-----------------------------------------------------
        self.Project.Book.Freeze()
        self.Project.removeCalculatedSpectrum()

        # Get current script nodes
        #-------------------------
        self.dataset = self.Project.Dataset
        self.scriptnode = scriptnode = self.Project.CurrentScript
        self.expparamnode = expparamnode = self.Project.CurrentParameters
        self.commandsnode = commandsnode = self.Project.CurrentCommands

        # Open the corresponding pages (if not already)
        # Create a reference to these pages
        #----------------------------------------------
        self.expparam = self.Project.Book.openPage(expparamnode)
        self.script = self.Project.Book.openPage(scriptnode)
        self.commands = self.Project.Book.openPage(commandsnode)

        # default editor:
        self.editor= self.script.editor

        # get the experimental data
        #--------------------------
        experiment = None
        self.fitplotter = None

        experimentnode = self.Project.CurrentExperiment
        if experimentnode is not None:
            # get the experiment
            self.experimental = self.Project.Book.openPage(experimentnode)
            #get the full 'Spectre' instance
            data = self.experimental.Content
            experimentspec = Spectre(data)
            ex = experimentspec["spec"]
            #eliminate possible baseline offset
            experiment = ex-(ex[0]+ex[-1])/2.

        if fitting:
##            experimentnode = self.Project.CurrentExperiment
##            # get the page containing the experiment to fit
##            # TODO: if we want to fit an experiment of course: make a check
##            self.experimental = self.Project.Book.openPage(experimentnode)
##
##            #get the full 'Spectre' instance
##            data = self.experimental.Content
##            experimentspec = Spectre(data)

            #create a new plot window fot the fit
            self.fitplotter = plot.PlotPage(self.parent)
            self.pl = pl = self.fitplotter.editor
            self.plotpageidx = self.parent.AddPage(self.fitplotter, "view fit")
            self.parent.SetSelection(self.plotpageidx)

            # show only the console book
            self._mgr.GetPane("Project").Hide()
            self._mgr.GetPane("Book").Hide()
            self._mgr.GetPane("Console").Show().Center()
            self._mgr.Update()

            # update this plot window with the experimental spectra
            pl["Experimental"]=experimentspec
            pl.hasPlot = True
            pl.drawSpectra()

            #get the traces itself for the fit
            xdata, ydata = self.fitplotter.PlotLines["Experimental"]

##            #eliminate possible baseline offset
##            experiment = ydata-(ydata[0]+ydata[-1])/2.

            lines = self.fitplotter.PlotLines


        # Make the current script selected
        #---------------------------------
        self.Project.SelectedNode = scriptnode

        # # Remove the previous temporary data
        #-------------------------------------
        try:
            os.remove(getWorkspacePath("scratch.tmp"))
        except:
            pass

        self.Project.Book.Thaw()
        # start the script
        #-----------------
        parameters.keepgoing = True

        self.__issuccess = True
        self.__isrunning = True
        self.__isfitting = fitting

        self.worker.beginProcess(self.compute, fitting,
                                                    self.fitplotter, experiment)
        self.clearLog()

#-------------------------------------------------------------------------------
    def stopScript(self):
#-------------------------------------------------------------------------------
        parameters.keepgoing = False

#-------------------------------------------------------------------------------
    def onWorkerDone(self, event):
#-------------------------------------------------------------------------------
        issuccess, data_returned, data_spec = self.resultQ.get()[1]
        #0 if success
        if issuccess in [-1,3]:
            self.__issuccess = False
        else:
            self.__issuccess = True
        self.__isrunning = False
        self.hideprogress()

        # Update the command page window
        #-------------------------------
        if self.__isfitting and self.__issuccess:
            text = self.commands.Content
            textdisp =''
            keys=data_returned.keys()
            keys.sort()
            for key in keys:
                param = re.compile('^(FitParameter\[.*'+key+
                          '.*\]\s*=\s*)([-+]?\w+[.]?\w*)(,?.*)$',
                                                               re.MULTILINE)
                m = param.search(text)
                if m:
                    textdisp += param.sub(r'\g<1>'+str(data_returned[key])+
                                          r'\g<3>\n',m.group(0))
                    text = param.sub(r'\g<1>'+str(data_returned[key])+
                                                              r'\g<3>',text)

            choice = cm.messageDialog(self.parent,
                "Would you like to update the fit parameters"+
                " in the command page with these results?\n"+textdisp,
                          "Update fit parameters...", wx.YES_NO|wx.YES_DEFAULT)
            if choice.positive:
                self.commands.Content = text
                self.commands.save()

        # Plot the spectra if it is successful
        #-------------------------------------
        if self.__issuccess:
            # Create the page Calculated
            #---------------------------
            cm.LOG_STATUS("Plotting...")
            infodialog = cm.InfoDialog("Please, wait... "+\
                                        "this process may take several seconds")
            self.Project.addCalculatedSpectrum(data_spec)
            self.Project.saveProject()
            pubsub.Publisher().sendMessage("ERROR",False)
            cm.LOG_STATUS("")
            infodialog.Destroy()

        else:
            # There is some errors. Try to display this information
            #------------------------------------------------------
            if self.editor is not None:
                if self.editor.GetParent() == self.script:
                    self.Project.SelectedNode = self.scriptnode
                if self.editor.GetParent() == self.expparam:
                    self.Project.SelectedNode = self.expparamnode
                if self.editor.GetParent() == self.commands:
                    self.Project.SelectedNode = self.commandsnode

            pubsub.Publisher().sendMessage("ERROR",True)

        self._mgr.LoadPerspective(self.perspective_default)
        if hasattr(self,"plotpageidx"):
            self.parent.DeletePage(self.plotpageidx)

#-------------------------------------------------------------------------------
    def onTimer(self, event):
#-------------------------------------------------------------------------------
        self.__progress.Pulse()
        if self.logger.modified:
            self.showCurrentLogLine()

#-------------------------------------------------------------------------------
    def hasError(self):
#-------------------------------------------------------------------------------
        return not self.__issuccess or self.runError

#-------------------------------------------------------------------------------
    def clearLog(self):
#-------------------------------------------------------------------------------
        """Clear log"""
        try:
            self.logger.Flush()
            self.edit.Clear()
        except:
            pass #to avoid strange errors: unbalanced wxRecursionGuards (???)

#-------------------------------------------------------------------------------
    def showCurrentLogLine(self):
#-------------------------------------------------------------------------------
        try:
            pos=self.edit.GetLastPosition()
            self.edit.ShowPosition(pos)
            self.logger.modified=False
        except:
            pass
            #to avoid strange errors: unbalanced wxRecursionGuards (???)

#-------------------------------------------------------------------------------
# property isRunning
#-------------------------------------------------------------------------------
    def _setRunning(self, value):
#-------------------------------------------------------------------------------
        self.__isrunning = value

#-------------------------------------------------------------------------------
    def _getRunning(self):
#-------------------------------------------------------------------------------
        return self.__isrunning

    isRunning = property(fget = _getRunning, fset = _setRunning)

#-------------------------------------------------------------------------------
# property runError
#-------------------------------------------------------------------------------
    def _setError(self, value):
#-------------------------------------------------------------------------------
        self.__iserror = value

#-------------------------------------------------------------------------------
    def _getError(self):
#-------------------------------------------------------------------------------
        return self.__iserror

    isError = property(fget = _getError, fset = _setError)


#======#
# TEST #
#======#

#-------------------------------------------------------------------------------
def runTest():
#-------------------------------------------------------------------------------
    import parentframe
    parent=parentframe.ParentFrame(None, title="Process")
    process=Process(parent)
    mainSizer=wx.BoxSizer(wx.VERTICAL)
    parent.SetSizer(mainSizer)
    mainSizer.Add(process, 1, wx.EXPAND)
    parent.Layout()
    parent.SendSizeEvent()
    parent.Show()

    #------------------
    f=open("popt.tpl")
    script = f.read()
    f.close()
    process.RunScript(script)

#-------------------------
if __name__ == '__main__':
#-------------------------
    import run
    run.main([os.path.basename(sys.argv[0])])


