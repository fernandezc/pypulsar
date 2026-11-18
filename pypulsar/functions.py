#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      functions.py
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
 This file contains some of the routines used by pulsar
 for the input of the starting parameters
"""

__docformat__="epytext"

#-------------------------------------------------------------------------------
# External Imports:
#------------------
from fit import * # before other call because of fft module
from numpy import arange, array, size, shape
from scipy.fftpack import ifft, fft
import pickle

# pyPulsar Imports:      #TODO: try to reduce the * import
#------------------
from definitions import *
import wx
import types
import string
import math
import re
import common as cm
from common import LOG_DEBUG as DEBUG
from forpulsar import *
from periodictable import *
from error import *
from processing import broadening, apply_phase

# list of parameters (used in the forpulsar fortran routine that need a
# new calculation of the spectra if they are changed
#(in the fit process for instance)

parcalc = \
"""spectrometerfield
protonfrequency
spinningangle
spinningspeed
qfactor
nucleus
chemicalshift
indirect
dipole
quadrupole
t2
accuracy
rfstep
nsb
npts
sw
sr
ncycles
nall
pulseangle
pulse
delay
coher
ctp
nboucle
ifasing
nphase
level
qu1
qu2
iref
rcph
"""
#TODO: VERIFY that all thiese parameters are needed

#===============================================================================
class Saving:
#===============================================================================
    """
    A container class (for saving parameters between different calculations)
    """
    pass

#===============================================================================
class Simulation(object):
#===============================================================================
    """
    A class to handle the parameters relative to a single pyPulsar simulation
    """
    count = 0
    saved = Saving()
    aborting = False

#-------------------------------------------------------------------------------
    def __init__(self, protonfrequency = "400 MHz", fitting=False):
#-------------------------------------------------------------------------------
        """
        Class Simulation constructor
        - additionally set default parameters for the simulation
        @param protonfrequency: Proton Larmor Frequency
        """
        # Reset most of the already allocated parameters
        #it is mandatory to reset forpulsar when doing a new simulation
        #that means to zero some arrays that can have different size in
        #different simulation

        self.__class__.count += 1
        self.saved = self.__class__.saved
        self.reset_pulsar()
        self.reset_pulse()
        self.reset_nucleus()
        self.reset_spectra()

        self.current_spectrum = []
        self.collection_spectra = []
        self.collection_variable = []
        self.collection_label= []

        # Initialise some basic parameters for the simulation
        self.set_protonfrequency(protonfrequency)
        self.spinningspeed=0.
        self.spinningangle=MAS
        self.qfactor=0.001
        self.accuracy=8
        self.rfstep=5
        self.npts=4*K
        self.sw=10*kHz
        self.sr=0.0
        self.aliasing=no
        self.nsb=0
        self.nall=0
        self.phc1=0.
        self.phc0=0.
        self.phcursor=0.
        self.flag_sum=False

        # and the fit
        self.__isfitting = fitting
        self.__calculatedspectra=None
        self.__data = None

        # Validate all new parameters
        # the most important here is the protonfrequency
        self.validate()

        # Initialise a "void" sample
        self.sample=Sample()

        # initialise a "void" pulse sequence
        self.sequence=PulseSequence()
        self.S_channel=None
        self.I_channel=None

    #----------------------
    def reset_pulsar(self):
    #----------------------
        """
        Deallocate most of the important arrays in the FORPULSAR module
        """
        if check_abort(): return
        DEBUG("SIMULATION.RESET PULSAR")
        #Call the FORPULSAR reset function
        reset()

    #-----------------------
    def reset_spectra(self):
    #-----------------------
        """
        Delete all spectra in a collection to zero (initialisation)
        """
        if check_abort(): return
        DEBUG("SIMULATION.RESET SPECTRA")
        self.collection_spectra = []
        self.list_lb=[]
        self.list_gb=[]
        self.list_concentration=[]
        self.list_name=[]

        # also set the parameter zerospectrum to True : Erasing spectra
        parameters.zerospectrum=True

    #-----------------------
    def reset_pulse(self):
    #-----------------------
        """
        Deallocate pulse arrays (initialisation)
        """
        if check_abort(): return
        DEBUG("SIMULATION.RESET_PULSE")
        parameters.pulse = []
        parameters.delay = []
        parameters.coher = []
        parameters.ctp = []
        self.ctpall = []
        self.ctptemp = []
        parameters.rcph = 0.0

    #-----------------------
    def reset_nucleus(self):
    #-----------------------
        """
        Deallocate the parameter arrays concerning the nuclei
        """
        if check_abort(): return
        DEBUG("SIMULATION.RESET NUCLEUS")
        parameters.nucleus=[]

    #-------------------------------------------------------
    def execute_pulsar(self, kind="Spectrum", TEST=False):
    #-------------------------------------------------------
        """
        Run the simulation using the forPulsar module
        @param kind: type of calculation ("Spectrum" or "Intensity")
        @type kind: INFO
        @param TEST: For test and developpement - Bypass the Fortran calculation
        @type TEST: Boolean
        @return: Success flag
        @rtype: Boolean
        """

        if check_abort(): return

        DEBUG("SIMULATION.EXECUTE PULSAR")

        # Validation of the parameters
        self.validate()

        # This instruction is very important because the array
        # in fortran 'diagonalize' function are not automatically deallocated
        diagonalize.dealloc()

        # No nucleus?
        if not self.sample.nuclei:
            raise UserError, "There is no nuclei defined! ABORTING calculation..."

        # Settings in case of spinning sideband aliasing
        if self.aliasing:
            cm.LOG_VERBOSE("ALIASING=YES")
            self.set_nsb("FULL")
            parameters.nsb = self.nsb
            parameters.sw = self.spinningspeed*float(self.nsb*2)
            parameters.npts = int(self.npts*(parameters.sw/self.sw))

        # Set the coherence transfer pathways
        parameters.ctp=self.ctpall

        # Display the current parameters if needed
        self.display()

        # Check if we need to calculate the spectrum
        # or just the intensity (density matrix)
        if string.lower(kind)=="intensity":
            parameters.spectrum_compute=False

        # Abort if Simulation was cancelled
        if check_abort(): return

        # If it is not a TEST, execute the simulation (call the 'compute'
        # fortran subroutine)
##        clear_exception()
        if not TEST and not check_abort():

            DEBUG("Entering Fortran Compute Subroutine")

            index = len(self.collection_spectra)
            if self.changed(index):
                #compute
                #print "compute"
                done = compute(cm.WRITE_LOG)
                #save the current parameters
                self.saveParameters(index)
            else:
                #recal an already calculated spectrum
                parameters.spec = self.saved.spec[index]
                done = True

            DEBUG("End Fortran Compute Subroutine")
            if not done:
                cm.LOG_ERROR("Compute routine returned unsuccessfull!")
                abort()
                return

        # Reset pulse
        self.reset_pulse()

#------------------------------------------------------------------------------
    def saveParameters(self,index):
#------------------------------------------------------------------------------
        """
        save parameters that need a recalculation of the spectrum if they are changed
        """
        # read the parameters that need recalculation if changed
        keys = parcalc.splitlines()

        #initialization
        if not hasattr(self.saved,"spec"):
#            print index, "INIT"
            self.saved.spec = []
            for k in keys:
                setattr(self.saved,k,[])

        #update
        if len(self.saved.spec)>index:
            self.saved.spec[index]=parameters.spec.copy()
            for k in keys:
#                print "update index", index, k, getattr(parameters,k)
                if getattr(parameters,k) is not None:
                    getattr(self.saved,k)[index]= getattr(parameters,k).copy()

        #append
        else:
            self.saved.spec.append(parameters.spec.copy())
            for k in keys:
#                print "append index", index, k, getattr(parameters,k)
                if getattr(parameters,k) is not None:
                    getattr(self.saved,k).append(getattr(parameters,k).copy())

#------------------------------------------------------------------------------
    def changed(self, index):
#------------------------------------------------------------------------------
        """
        Check if the spectrum parameters have changed
        """
##        print "TEST changed", index, parameters.chemicalshift[0][1]
        if not hasattr(self.saved,"spec"):
##            print "\nindex: ", index, "Changed True\n"
            return True

        if len(self.saved.spec) <= index:
##            print "\nindex: ", index, "Changed True\n"
            return True

        # read the parameters that need recalculation if changed
        keys = parcalc.splitlines()

        for k in keys:
##            print k
            if  getattr(parameters,k) is None:
##                print "index: ", index,  "Changed ", k, "False"
                pass
            else:
                if (getattr(self.saved,k)[index] == getattr(parameters,k)).all():
##                    print "index: ", index,  "Changed ", k, "False"
                    pass
                else:
#                    print "\nindex: ", index, "Changed ", k, "True\n"
                    return True
        return False # no change found

#------------------------------------------------------------------------------
    def display(self):
#------------------------------------------------------------------------------
        if check_abort():
            return
        DEBUG("DISPLAY")

        cm.LOG_VERBOSE("SPECTROMETER:")
        cm.LOG_VERBOSE("-------------")
        cm.LOG_VERBOSE( \
          "\tSpectrometer field: %10.3f Tesla"%parameters.spectrometerfield)
        cm.LOG_VERBOSE( \
          "\tProton frequency: %10.3f MHz"%(parameters.protonfrequency/mhz))

        cm.LOG_VERBOSE("PROBEHEAD:")
        cm.LOG_VERBOSE("----------")
        cm.LOG_VERBOSE( \
         "\tspinning speed: %10.3f kHz"%(parameters.spinningspeed/khz))
        cm.LOG_VERBOSE("\tspinning angle: %10.3f deg."%parameters.spinningangle)
        cm.LOG_VERBOSE("\tquality factor: %10.3f "%parameters.qfactor)

        cm.LOG_VERBOSE("SIMULATION parameters:")
        cm.LOG_VERBOSE("----------------------")
        cm.LOG_VERBOSE("\tnumber of points: " + str(parameters.npts))
        cm.LOG_VERBOSE("\tspectral width: " + str(parameters.sw/khz)+" kHz")
        cm.LOG_VERBOSE( \
                 "\tnumber of spinning sidebands: " + str(parameters.nsb*2))
        cm.LOG_VERBOSE( \
               "\tpowder integration accuracy: " + str(parameters.accuracy))
        cm.LOG_VERBOSE("\trf integration step: " + str(parameters.rfstep))
        if (parameters.nall == 0): strg = "-- detect all transitions"
        if (parameters.nall == 1):
            strg = "-- detect central transition only"
        if (parameters.nall == 2):
            strg = "-- detect satellite transitions only"
        cm. LOG_VERBOSE("\tDetection: "+ strg)

        cm.LOG_VERBOSE("OTHER INFORMATIONS:")
        cm.LOG_VERBOSE("-------------------")
        cm.LOG_VERBOSE( \
                "\tAliasing of the spinning sidebands: "+str(self.aliasing))
        cm.LOG_VERBOSE( "\tSR: "+str(self.sr))

        cm.LOG_VERBOSE("PULSE SEQUENCE:")
        cm.LOG_VERBOSE("---------------")

        if (not parameters.idealpulse):
            siz=len(parameters.pulse)
            for i in range(siz):
                strg="Pulse"+" P"+str(int(parameters.pulse[i, 0]))+" "
                strg= strg + "["
                strg= strg + str(parameters.pulse[i, 1])+" usec"
                if parameters.pulse[i, 2]!=0 :
                    strg= strg + "("+str(parameters.pulse[i, 2]/khz) \
                               + " kHz," \
                               +str(parameters.pulse[i, 3])+" Hz," \
                               +str(parameters.pulse[i, 4])+"):S"
                if parameters.pulse[i, 5]!=0 :
                    strg= strg + "("+str(parameters.pulse[i, 5]/khz) \
                               +" kHz," \
                               +str(parameters.pulse[i, 6])+" Hz," \
                               +str(parameters.pulse[i, 7])+"):I"
                strg= strg + "]"
                cm.LOG_VERBOSE(strg)
                if (parameters.delay[i, 1]>0):
                    strg= "Delay "+"D"+str(int(parameters.delay[i, 0]))
                    strg= strg + "[ "+str(parameters.delay[i, 1])+" usec ] "
                    if (parameters.delay[i, 2]==1):
                        strg=strg + "-- without decoupling"
                    else:
                        strg=strg +"-- with decoupling"
                    cm.LOG_VERBOSE(strg)

            self.print_pathways()

        else:
            strg= "Ideal pulse (dirac)"
            cm.LOG_VERBOSE(strg)

    #------------------
    def validate(self):
    #------------------
        """
        set parameters in the fortran module
        """
        if check_abort():
            return

        DEBUG("VALIDATE SIMULATION")

        parameters.spectrometerfield = self.field
        parameters.protonfrequency = self.protonfrequency
        parameters.spinningangle = self.spinningangle
        parameters.spinningspeed = self.spinningspeed
        parameters.qfactor = self.qfactor
        parameters.rfstep = self.rfstep
        parameters.npts = self.npts
        parameters.nsb = self.nsb
        parameters.accuracy = self.accuracy
        parameters.sw = self.sw
        parameters.sr = self.sr
        parameters.nall = self.nall

    #--------------------------
    def set_field(self, field):
    #--------------------------
        """
        Change the spectrometer field
        and calculate the corresponding proton frequency
        """
        if check_abort():
            return

        DEBUG("SET_FIELD")
        try:
            self.field = abs(evaluate(field))
        except:
            self.field=0
        if self.field == 0 :
            cm.LOG_VERBOSE("'set_field': reset to default 9.395*tesla\n")
            self.field = 9.395*tesla
        self.protonfrequency = self.field*gamma_H
        parameters.spectrometerfield = self.field
        parameters.protonfrequency = self.protonfrequency

    #----------------------------------------
    def set_frequency(self, protonfrequency):
    #----------------------------------------
        """ similar to set_protonfrequency
            kept for backward compatibility """
        if check_abort():
            return

        self.set_protonfrequency(protonfrequency)

    #----------------------------------------
    def set_protonfrequency(self, protonfrequency):
    #----------------------------------------
        """
        Change the proton frequency
        and calculate the corresponding spectrometer field
        """
        if check_abort():
            return

        DEBUG("SET_PROTONFREQUENCY")
        try:
            self.protonfrequency = abs(evaluate(protonfrequency))
        except:
            cm.LOG_VERBOSE("'set_protonfrequency': reset to default 400*mhz\n")
            self.protonfrequency = 400*mhz
        self.field = self.protonfrequency/gamma_H
        parameters.spectrometerfield = self.field
        parameters.protonfrequency = self.protonfrequency

    #------------------------------------------
    def set_spinningspeed(self, spinningspeed):
    #------------------------------------------
        """
        Change the spinning speed
        """
        if check_abort():
            return

        DEBUG("SET_SPINNINGSPEED")
        self.spinningspeed = abs(evaluate(spinningspeed))
        if self.spinningspeed<1*hz and self.nsb > 0:
            cm.LOG_VERBOSE( \
                     "the spinning speed being 0, nsb has also been set to 0\n")
            self.nsb = 0

    #------------------------------------------
    def set_spinningangle(self, spinningangle):
    #------------------------------------------
        """
        Change the spinning angle
        """
        if check_abort():
            return

        DEBUG("SET_SPINNINGANGLE")
        self.spinningangle = abs(evaluate(spinningangle))

    #----------------------
    def set_nsb(self, nsb):
    #----------------------
        """
        Change the number of spinning sideband - can be AUTO
        """
        if check_abort():
            return

        DEBUG("SET_NSB")
        self.nsb = evaluate(nsb)
        if self.nsb == -999 and self.spinningspeed > 0.1:
            # calculate number of spinning sidebands for satellite transition
            try:
                s = parameters.nucleus[0, 1]
                wQ=3.*parameters.quadrupole[0, 1]/(2.*s*(2*s-1))
                width=min(self.sw*1.1, wQ*(2*s-1.)*1.25)
                self.nsb = int(width/self.spinningspeed/2.)
            except:
                raise ValueError, "The 'AUTO' flag in 'set_nsb' can be used only " \
                    +"after a nucleus S has been defined" \
                    +"\n\t (Additionnaly, the sw (using set_sw) and " \
                    +"the spinningspeed (using set_spinningspeed) must " \
                    +"\n\t  also be defined prior to this calculation)\n"
                return

        elif self.nsb == -998 and self.spinningspeed > 0.1:
            # calculate the maximum number of spinning sidebands
            #for satellite transition
            try:
                s = parameters.nucleus[0, 1]
                wQ=3.*parameters.quadrupole[0, 1]/(2.*s*(2*s-1))
                width=wQ*(2*s-1.)*1.25
                self.nsb = int(width/self.spinningspeed/2.)
            except:
                cm.LOG_WARNING("error with 'FULL' calculation")
        else:
            if self.spinningspeed<0.1:
                self.nsb = 0
            else:
                self.nsb = evaluate(nsb)

        self.nsb=abs(self.nsb)

    #------------------------
    def set_npts(self, npts):
    #------------------------
        """
        Change the number of points
        """
        if check_abort():
            return

        DEBUG("SET_NPTS")
        self.npts = abs(evaluate(npts))
        self.npts = int(2**round(math.log(self.npts+1)/math.log(2)))
        self.npts = max(min(self.npts, parameters.nptsmax), 128)

    #---------------------------------
    def set_sw(self, sw, aliasing=no):
    #---------------------------------
        """
        Change the spectral width
        """
        if check_abort():
            return

        DEBUG("SET_SW")
        self.sw = abs(abs(evaluate(sw)))
        self.sw = max(self.sw, 100*Hz)
        self.aliasing=evaluate(aliasing)

    #---------------------------------
    def set_sr(self, sr):
    #---------------------------------
        """
        Change the spectral width
        """
        if check_abort():
            return

        DEBUG("SET_SR")
        self.sr = evaluate(sr)

    #--------------------------------
    def set_accuracy(self, accuracy):
    #--------------------------------
        """
        Change the accuracy
        """
        if check_abort():
            return

        DEBUG("SET_ACCURACY")
        self.accuracy = abs(evaluate(accuracy))
        self.accuracy = max(min(self.accuracy, parameters.accuracymax), 1)

    #----------------------------
    def set_rfstep(self, rfstep):
    #----------------------------
        """
        Change the rf integration step
        """
        if check_abort():
            return

        DEBUG("SET_RFSTEP")
        self.rfstep = abs(evaluate(rfstep))
        self.rfstep = max(self.rfstep, .1)

    #----------------------------
    def set_detect(self, detect):
    #----------------------------
        """
        Set detection parameters
        args:
            detect choice: "all", "central", "satellite"
        """
        if check_abort():
            return

        DEBUG("SET_DETECT")
        self.nall = max(min(evaluate(detect), 2), 0)
        try:
            spins = parameters.nucleus[0, 1]
            if spins<1 : self.nall = 0
        except:
            raise UserError, "'set_detect' can be used only after \
                  a nucleus S has been defined\n"
            return

    #------------------------------
    def set_qfactor(self, qfactor):
    #------------------------------
        """
        Change the probe quality factor
        """
        if check_abort():
            return

        DEBUG("SET_QFACTOR")
        self.qfactor = max(evaluate(qfactor), 0.0001)



#------------------------------------------------------------------------------
    def store_spectrum(self, variable=None, label=None):
#------------------------------------------------------------------------------
        """
        Store a spectrum in the collection
        @param variable: numeric or INFO
        @param label: INFO
        """

        if check_abort():
            return

        DEBUG("STORE_SPECTRUM")

        spec = array(parameters.spec)

        if len(spec)==0: #nothing to add
            raise UserError, "No spectrum to store!"
            return

        # phasing (return also phcursor to maintain it to an unique value
        #in the course of the simulation
        spec  = apply_phase(spec,self.npts,self.sw,self.sr,
                            self.phc0,self.phc1,self.phcursor)

        if type(variable) is not types.NoneType:
            if not (isinstance(variable, int) \
                    or isinstance(variable, long) \
                    or isinstance(variable, float)) :
                variable=str(variable)
            self.collection_variable.append(variable)      #identifier
            DEBUG("Stored variable: "+ str(variable))
        else:
            variable='undefined'

        if type(label) is types.StringType:
            self.collection_label=label
            DEBUG("Stored label: "+label)
        else:
            self.collection_label="variable"

        self.collection_spectra.append(spec)
        self.current_spectrum = array(spec)
        self.list_lb.append(self.lb)
        self.list_gb.append(self.gb)
        self.list_concentration.append(self.concentration)
        self.list_name.append(self.name)

        cm.LOG_VERBOSE("A spectrum has been added to the collection of spectra (" \
            + str(len(self.collection_spectra))+")")
        cm.LOG_VERBOSE(" "+self.collection_label+" : "+str(variable))

    #----------------------------
    def integrate_spectrum(self):
        """
        Spectrum integration
        """
        if check_abort():
            return

        DEBUG("INTEGRATE_SPECTRUM")
        spec = array(parameters.spec)

        if len(spec)==0:
            raise UserError, "No spectrum to integrate!"

        sum=0
        for i in range(len(spec)):
            sum += spec[i].imag

        return sum

    #------------------------------------------------------------
    def get_densitymatrix(self, row=0, col=0, coherence=-1, channel="S"):
        """
        get density matrix elements
        (rows and columns are numbered from 1 to n)
        """
        if check_abort():
            return

        ros = array(parameters.ros)
        roi = array(parameters.roi)
        ns=len(ros)
        ni=len(roi)
        if ns==0:
            raise UserError, "No density matrix!"
            return

        if (row!=0 and col!=0):
            if channel=="S":
                return ros[row-1][col-1]
            else:
                return roi[row-1][col-1]
        if (coherence!=0):
            if channel=="S":
                for row in range(-ns, ns, 1):
                    if (row+coherence) in range(ns) and row in range(ns):
                        return ros[row][row+coherence]
            else:
                for (row) in range(-ni, ni, 1):
                    if (row+coherence) in range(ni) and row in range(ni):
                        return roi[row][row+coherence]

    #-----------------------------------
    def clearspectrum(self, clear=True):
    #-----------------------------------
        """
        Keep or clear the current spectrum buffer
        """
        if check_abort():
            return

        DEBUG("CLEARSPECTRUM "+str(clear))
        parameters.zerospectrum=clear

    #----------------------------------
    def sum_spectra(self, do_sum=True):
    #----------------------------------
        """
        Set a flag for future summation of spectra
        """
        if check_abort():
            return

        DEBUG("SUM_SPECTRA "+str(do_sum))
        self.flag_sum=do_sum

    #-----------------------
    def write_spectra(self):
    #-----------------------
        """
        write spectra into a file
        """
        if check_abort():
            return

        #for back compatibility with version 0.1 of pyPulsar
        self.save_spectra()

    #-----------------------
    def save_spectra(self):
    #-----------------------
        """
            save spectra for future handling
        """
        if check_abort():
            return

        DEBUG("SAVE_SPECTRA ")

        kind= CALC_1D # by default #TODO: add other possililities

        n2 = self.npts
        sw2 = self.sw
        vl2 = parameters.nucleus[0, 2]
        sr2 = self.sr

        self.nspec = nspec = len(self.collection_spectra)

        if kind == CALC_1D:
            sw1 = 0
            vl1 = 0
            sr1 = 0
            n1  = 1

        flag_sum=self.flag_sum
        lb2=self.list_lb #list
        gb2=self.list_gb #list
        conc2=self.list_concentration
        name=self.list_name

        label=[]
        variables=[]
        if len(self.collection_variable)==nspec:
            label=self.collection_label
            variables=self.collection_variable #list

        # Prepare CFG (configuration of plot)
        #-------------------------------------
        cfg=CFG
        cfg['kind'] = kind
        cfg['dim_2'] = DIM_FREQ
        cfg['dim_1'] = None        # TODO: case of 2D
        cfg['dim_0'] = None
        cfg['Sum_Components']=flag_sum

        # Prepare the data header
        #------------------------
        header = []
        for k in range(nspec):
            headerk = []
            headerk.append((cfg))                           #CFG
            headerk.append((vl2, vl1, None))
            headerk.append((sw2, sw1, None))
            headerk.append((sr2, sr1, None))
            headerk.append((n2, n1, 1))
            headerk.append((n2, n1, 1))
            headerk.append((lb2[k], gb2[k], conc2[k]))       # lb, gb, conc
            if label and variables:
                headerk.append((label, variables[k]))         # Label, Variable
            else:
                headerk.append((name[k],""))
            header.append(headerk)

        # Prepare spectra
        #-----------------
        newZ = []
        for k in range(nspec):
            newItem=[]
            spec=self.collection_spectra[k]

            #case of an aliasing
            if self.aliasing:
                i=0
                specs=[]
                np=parameters.npts
                for j in range(n2):
                    sp=0.
                    for i in range(np/n2):
                        sp=sp+spec[j+i*n2]
                    specs.append(sp)
                spec=[0]*n2
                spec[1:n2/2-1]=specs[n2/2:n2-1]
                spec[n2/2:n-1]=specs[1:n2/2-1]

            # Make a correction of the spec
            # by creating actual Abs and Disp component
            fid=[]
            newn=2**17
            ##try:

            ##print spec
            fid = fft(array(spec, 'D'), newn, -1, 1)
            for i in range(newn/2, newn):
                fid[i]=complex(0., 0.)  #dissymetrisation
            temp= ifft(fid, newn, -1, 1)
            for i in range(n2):
                spec[i]=temp[i] #restore spectrum to its correct size

            ##except:
            ##    raise UserError, "fft problems"

            for i in range(len(spec)):
                newItem.append(complex(spec[i].imag, spec[i].real))

            newZ.append(newItem)

        # create the data directory
        #--------------------------
        data={}
        data["kind"] = kind
        data["nspec"] = nspec
        data["spectra"]=[]
        for k in range(nspec):
            data["spectra"].append(repr([header[k], newZ[k]]))

#        print str(data)[0:1000]
        # This is for fit information
        #----------------------------
        self.__calculatedspectra = (newZ, n2, nspec, sw2,
                          self.list_lb, self.list_gb, self.list_concentration)
        self.__data=data

        # This need to be transmitted to the main program
        # but I don't know how to make a callback to the calling program.
        # use a temporary file instead
        # TODO: see if there is a better way
        #----------------------------------------------------------------
        try:
            os.remove(getWorkspacePath("scratch.tmp"))
        except:
            pass

        #if not self.fitting:
##        DEBUG(cm.getWorkspacePath("scratch.tmp"))
##        f = open(cm.getWorkspacePath("scratch.tmp"), "wb")
##        pickle.dump(data,f)
##        f.close()

        cm.LOG_VERBOSE("Saving of spectra data done.")

        self.reset_spectra()


######################################
## NUCLEUS AND SELECTION OF NUCLEUS ##
######################################

    #-----------------------------------
    def add_nucleus(self, nucleus=None):
    #-----------------------------------
        """
        add a nucleus to the current simulation
        """
        if check_abort():  return

        DEBUG("ADD NUCLEUS")
        # check if Nucleus was defined
        if nucleus is None:
            raise ValueError, "an Nucleus instance argument is required"

        # check if Nucleus is an instance of class Nucleus
        if type(nucleus) is not types.InstanceType:
            raise TypeError, "Argument of add_nucleus must be a Nucleus class instance \
                 \n        e.g. use N=Nucleus(isotope) to define a Nucleus instance 'N' "

        # check if ABORT in class nucleus was not set
        if check_abort(): return

        # we add this nucleus to the sample
        self.sample.add_nucleus(nucleus)

    #-----------------------------
    def set_channel(self, *channel):
    #------------------------------
        """
        define the channels
        """
        if check_abort():   return

        DEBUG("SET_CHANNEL : "+repr(channel))

        # Check if the channels correspond to existing isotope
        try:
            for isotope in channel:
                #read from peiodictable
                done = isotopes[isotope]
        except KeyError:
            message = isotope+ \
                      " was not found in the nucleus list, "+ \
                      "Check its name and/or the its number"
            raise KeyError, message

        # the channel correspond to a Nucleus selection
        try:
            self.S_channel=channel[0]
            if len(channel)>1:
                self.I_channel=channel[1]
                DEBUG("SET_CHANNEL : "+channel[1])
        except:
            raise UserError, "'set_channel' problem"

    #-----------------------------------------------------
    def select_observed(self, nucleus=None):
    #-----------------------------------------------------
        """
        Exactly equivalent to select_nucleus()
        [this is the new form - more clear I think)
        """
        if check_abort():  return

        self.select_nucleus(nucleus)

    #-----------------------------------------------------
    def select_coupled(self, nucleus=None):
    #-----------------------------------------------------
        """
            Selection of the coupled nuclei
            arg:
            nucleus : an instance of the nucleus class
        """
        if check_abort():  return

        DEBUG("  ")
        DEBUG("SELECT_COUPLED ")
        DEBUG("Number of different nuclei :"+str(len(self.sample.nuclei)))

        # because we do not take into account homonuclear couplings,
        # this number must be greater than 2 to continue
        # Stop process if there is not enough nucleus
        if len(self.sample.nuclei)<2:
            raise UserError, "No nucleus that can be coupled (HETERONUCLEAR) to "  \
                 + self.S_channel + \
                 " have been found! define them before calling set_coupled"

        # First we have to handle a possible error arising
        # when no observed channels have been defined
        if not self.S_channel: self.S_channel=self.sample.observed
        DEBUG("Observed channel :"+self.S_channel)


        # The command 'set_I_nucleus' was given without arguments:
        # This is not allowed
        if (nucleus is None or type(nucleus) is not types.InstanceType):
            raise UserError, "No argument in set_coupled or the argument " \
            +"is not a nucleus instance  : this is required "

        # Ok, if we are here, the command was entered
        # with a Nucleus instance specification

        #check if the S nucleus was already defined
        if len(parameters.nucleus)<1:
            raise UserError, "The definition of the S nucleus must be set before using " \
                +"select_coupled: \ndefine the observed S Nucleus, " \
                +"using select_observed (or select_nucleus)"
            return

        #Now validate the nucleus
        index=nucleus.index
        coupled=nucleus.isotope
        DEBUG("Selection of "+coupled+" index " \
                +str(index+1))
        if coupled == self.S_channel:
            raise UserError, "The selected coupled nucleus can not be on the " \
            +self.S_channel+" channel (only heteronuclear coupling allowed)"
        else:
            #ok, it is an observed nuclei
            DEBUG("OK, it can be coupled to the current S nucleus")
            #Validation
            abundance=None #### TODO: This has to be discussed with Jean-Paul
            self.sample.validate(coupled, index, 0.0, abundance)

    #-----------------------------------------------------
    def select_nucleus(self, nucleus=None):
    #-----------------------------------------------------
        """
        define the observed nucleus used for the calculation (use only
          its index)
        arg:
            nucleus : an instance of the nucleus class
                      (by default it is the S_channel but it may be interesting
                      to have a nucleus close in frequency like 51V
                      when studying 23Na or an integer representing the index
                      of an observed nuclei (index start at 1)
        warning:
            Only one observed nucleus can be choosen at at given time
            for calculation: it must be the first in the parameter.nucleus array
            in Fortran (this behavior must be probably modified in the future,
            because it is slightly rigid! #TODO: change this behavior
        """

        if check_abort():
            return

        delta=0.
        abundance=None

        DEBUG("  ")
        DEBUG("SELECT_NUCLEUS ")
        DEBUG("Number of defined and different nuclei :" \
            +str(len(self.sample.nuclei)))

        #Stop process if there is no nucleus
        if len(self.sample.nuclei)==0:
            parameters.exception=1000 #Missing instruction
            parameters.exception_text=array(string.ljust( \
            "No nucleus found! define them before calling select_nucleus", 255))
            abort()
            return

        # First we have to handle a possible error arising
        # when no observed channels have been defined
        if not self.S_channel: self.S_channel=self.sample.observed

        DEBUG("  Observed channel :"+self.S_channel)

        # The command 'set_nucleus' was given without arguments:
        # Validation for instance of a single observed nucleus
        if (nucleus is None):
            index=0
            observed=self.S_channel
            cm.LOG_VERBOSE("No argument in set_nucleus : the first nucleus in '" \
            +self.S_channel+"' list will be considered ")

        # Ok, if we are here, the command was entered with an index
        # or a Nucleus instance specification
        if type(nucleus) is types.IntType:
            # we specified an index  : in this case it can be only for observed
            # nuclei
            index=nucleus-1  #internal index start at 0
            observed=self.S_channel
            DEBUG("Selection of "+observed+" with index "\
                    +str(index+1)+" in the list of observed nuclei")
            if self.get_numberofnuclei(self.S_channel)==0:
                raise UserError, "No observed nuclei defined!"
            if index >= self.get_numberofnuclei(self.S_channel):
                raise UserError, "This nucleus index does not exist (maximum is "+ \
                            str(self.get_numberofnuclei(self.S_channel)) \
                            + " in the channel: "+ self.S_channel+\
                            "\n. Check the nucleus definition list!" + \
                            "\n(Note: Index in nucleus lists start at 1: " \
                            +"first nucleus entered has index 1, " \
                            +"the second has index 2, and so on...)"

        if type(nucleus) is types.InstanceType:
            # we specified a nucleus instance
            index=nucleus.index
            observed=nucleus.isotope
            DEBUG("Selection of "+observed+" index " \
                                                                  +str(index+1))
            if observed == self.S_channel:
                #ok, it is an observed nuclei
                DEBUG("OK, the selected nucleus can be observed")

            else:
                if observed == self.I_channel:
                        # well, it is a I nuclei, but this has no sense because
                        # it cannot be observed
                    raise UserError, "Cannot observe nucleus "+observed+ \
                                " on the actual observed channel: " \
                                +self.S_channel+ \
                                ". You may want to change the observed " \
                                +"channel using set_channel"
                else:
                    # there is no I channel
                    # check if this nucleus is close enougth to S_channel
                    # to be observed (even partly).
                    DEBUG( \
                       "\tAbs. Larmor frequency of the this nucleus : " \
                       +str(abs(nucleus.nucleus["larmor"])))
                    DEBUG( "\tFrequency of the observed " \
                       +self.S_channel+" channel : " \
                       +str(isotopes[self.S_channel]["larmor"]))
                    delta = abs(nucleus.nucleus["larmor"]) \
                       - abs(isotopes[self.S_channel]["larmor"])
                    DEBUG("\tDifference : "+str(delta)+ " MHz")
                    if delta>5:
                        raise UserError, "This frequency difference seems too" \
     +" large for taking into account this nucleus. It will not be calculated!"
                        return
                    #ok we takes this delta into account
                    delta=delta*mhz
                    abundance=isotopes[nucleus.isotope]["abundance"]
                    #TODO: change to take into account possible enrichment

        DEBUG("Observed nuclei index :"+str(index))
        DEBUG("Observed nucleus isotope:"+observed)

        #Validation
        self.sample.validate(observed, index, delta, abundance, observed=True)

        #Read the lb, gb and concentration from the current nucleus
        self.lb=self.sample.nuclei[observed][index].lb
        self.gb=self.sample.nuclei[observed][index].gb
        self.concentration=self.sample.nuclei[observed][index].concentration

        if hasattr(self.sample.nuclei[observed][index],"name"):
            self.name = self.sample.nuclei[observed][index].name
        else:
            self.name = str(index+1)

    #-------------------------------------------------------------
    def get_numberofnuclei(self, isotope):
    #-------------------------------------------------------------
        """
        Get the number of nuclei of a given type
        parameters
        * isotope: required isotope name
        Usage
            ...
            get_numberofnuclei("27Al")   # determine the number of 27Al nuclei
            ...
        """
        if check_abort():
            return

        if isotope in self.sample.nuclei:  #has_key!
            nb= len(self.sample.nuclei[isotope])
            #DEBUG("Number of nuclei:"+str(nb))
            return nb
        else: return 0


#===============================================================================
#    #-------------------------------------------------------------
#    XXX: def import_sample(self,file=None,*only):
#    #-------------------------------------------------------------
#        """
#            import the a file with sample definition
#            (TO WORK ON IT... There is too many limitations!)
#        """
#        if check_abort():
#            return
#
#        if file is None:
#            cm.LOG_WARNING("File name to load was not given in the arguments")
#            return
#
#        try:
#            f = open(PathNorm("workspace/"+file),"r")
#        except:
#            raise_exception("When opening file: '"+file+"'")
#            self.ABORT=True
#            return
#
#        try:
#            lines=f.readlines()
#        except:
#            raise_exception("When reading file: '"+file+"'")
#            self.ABORT=True
#            return
#
#        try:
#            for line in lines:
#                exec(line)
#        except:
#            raise_exception("When executing line: '"+line+"' in file: '" \
#              +file+"'")
#            self.ABORT=True
#            return
#
# ##        print len(self.sample.nuclei)
# ##        print self.sample.nuclei
#
#        f.close()
#===============================================================================

######################
## DIPOLAR COUPLING ##
######################

    # indirect j coupling ------------------------------------------------------
    def set_indirect(self, index=None, j = 0, delta = 0, eta = 0, alpha = 0,
                     beta = 0, gamma = 0):
    #---------------------------------------------------------------------------
        """
        Set the indirect J coupling between a pair of nucleus
        @param index: index of the coupled nucleus
        @param j: J coupling value
        @param delta: anisotropy of J
        @param alpha, beta, gamma: euler angles with respect
               to the molecular frame
        """
        #FIXME: Complete and check set_indirect function: probably not working
        second=None

        if check_abort():
            return

        DEBUG("SET INDIRECT")
        #Some nuclei need to be defined first, this is a fatal error
        if parameters.nucleus is None:
            raise UserError, "No observed and coupled nucleus" \
                          +" were defined yet. Cannot set dipolar coupling'!\n"

        else:
            # At least one coupled nucleus need to be defined,
            # this is a fatal error
            if len(parameters.nucleus)==1:
                raise UserError, "There is no defined coupled nucleus: " \
                         +"use set_coupled to define them!\n"

            # If the index is not specified select index=1
            if index is None:
                cm.LOG_VERBOSE("the index of the coupled nucleus is not given" \
            +" in set_indirect!")
                index=1
                cm.LOG_VERBOSE("\tthe first coupled nucleus" \
                     +" (index=1) in the list of coupled nuclei will be used.")

            #if the selected index does not exit : This is a fatal error.
            if index>len(parameters.nucleus) or index<1:
                raise UserError, "This index "+ index  \
                     +" does not correspond to an existing coupled nucleus!\n"

        try:
            j=evaluate(j)
            delta = evaluate(delta)
            eta = evaluate(eta)
            alpha=evaluate(alpha)
            beta=evaluate(beta)
            gamma=evaluate(gamma)

        except:
            raise UserError, "Something is wrong in the definition " \
                                         +"of the scalar coupling parameters!"

        if j==0:
            cm.LOG_VERBOSE("Scalar J coupling is found to be zero!")

        if parameters.indirect==None:
            DEBUG("indirect J coupling:")
            ar=[[1, 1+index, j, delta, eta, alpha, beta, gamma]]
        else:
            size=len(parameters.indirect)
            ar=[[0, 0, 0, 0, 0, 0, 0] for i in range(size+1)]
            #copy of the previous elements
            i=0
            while i < size :
                ar[i]=[int(parameters.indirect[i, 0]),
                       int(parameters.indirect[i, 1]),
                       parameters.indirect[i, 2],
                       parameters.indirect[i, 3],
                       parameters.indirect[i, 4],
                       parameters.indirect[i, 5],
                       parameters.indirect[i, 6],
                       parameters.indirect[i, 7]]
                       #copy of the previous elements
                i=i+1
            ar[size]=[1, 1+index, j, delta, eta, alpha, beta, gamma]
        parameters.indirect=ar
        #allocate or reallocate and initialize
        size=len(parameters.indirect)
        i=size-1
        DEBUG("\tIndirect J coupling ("+str(index)+"): " \
                       + str(parameters.indirect[i, 2])+" Hz")
#FIXME: Second is not defined!!!
        if parameters.indirect[i, 3]!=0 :
            DEBUG("\tdelta J ("+str(index)+","+str(second)+"): "
                   + str(parameters.indirect[i, 3])+" Hz")
        if parameters.indirect[i, 3]!=0 :
            DEBUG("\teta J ("+str(index)+","+str(second)+"): "
                   + str(parameters.indirect[i, 4]))
        if parameters.indirect[i, 3]!=0 :
            DEBUG("\teuler J ("+str(index)+","+str(second)+"): ["
                   + str(parameters.indirect[i, 5])+","
                   + str(parameters.indirect[i, 6])+","
                   + str(parameters.indirect[i, 7])+"]")

    # direct dipolar coupling -----------------------------------------
    def set_dipole(self, index=None, dip=0, distance=0, alpha=0, beta=0,
                   gamma=0):
    #------------------------------------------------------------------
        """
        Set the direct dipole coupling between a pair of nucleus
        @param index: index in the coupled nucleus list
                      (defined previously by set_coupled)
        @param dip: dipolar coupling value
        @param distance: distance between nucleus in angstrom
                      (will be used only if dip=0)
        @param alpha, beta, gamma: euler angles
                                   with respect to the molecular frame
        @return: info on Dipolar coupling and the related distance
        """
        if check_abort():
            return dip

        DEBUG("SET_DIPOLE")

        #Some nuclei need to be defined first, this is a fatal error
        if parameters.nucleus is None:
            raise UserError, "No observed and coupled nucleus \
                   were defined yet. Cannot set dipolar coupling'!\n"

        else:
            # At least one coupled nucleus need to be defined,
            # this is a fatal error
            if len(parameters.nucleus)==1:
                raise UserError, "There is no defined coupled nucleus: \
                          use set_coupled to define them!\n"

            # If the index is not specified select index=1
            if index is None:
                cm.LOG_VERBOSE( \
                 "the index of the coupled nucleus is not given in set_dipole!")
                index=1
                DEBUG( \
                 "\tthe first coupled nucleus (index=1) " \
                 +"in the list of coupled nuclei will be used.")

            # if the selected index does not exit : This is a fatal error.
            if index>len(parameters.nucleus) or index<1:
                message= "This index "+ index \
                      +" does not correspond to an existing coupled nucleus!\n"
                raise UserError, message
        #ok, now we are here, without index error.
        try:
            dip=evaluate(dip)
            distance=evaluate(distance)
            if (distance!=0) and (dip==0) :
                dip=dipole_from_distance(distance, parameters.nucleus[0, 2],
                        parameters.nucleus[index, 2])
            #print dip,distance
            alpha=evaluate(alpha)
            beta=evaluate(beta)
            gamma=evaluate(gamma)
        except:
            raise UserError, "Something is wrong in the definition of \
                      the dipolar coupling parameters!"

        if dip==0:
            cm.LOG_VERBOSE( \
          "Dipolar coupling is found to be zero (dip=0 or distance too large)!")

        if parameters.dipole==None:
            DEBUG("dipolar coupling:")
            ar=[[1, 1+index, dip, distance, alpha, beta, gamma]]
        else:
            size=len(parameters.dipole)
            ar=[[0, 0, 0, 0, 0, 0, 0] for i in range(size+1)]
            #copy of the previous elements
            i=0
            while i < size :
                ar[i]=[int(parameters.dipole[i, 0]),
                       int(parameters.dipole[i, 1]),
                       parameters.dipole[i, 2],
                       parameters.dipole[i, 3],
                       parameters.dipole[i, 4],
                       parameters.dipole[i, 5],
                       parameters.dipole[i, 6]]
                i=i+1
            ar[size]=[1, 1+index, dip, distance, alpha, beta, gamma]
        parameters.dipole=ar
        # allocate or reallocate and initialize

        size=len(parameters.dipole)
        i=size-1
        DEBUG("\tdipolar coupling ("+str(index)+"): "
             + str(parameters.dipole[i, 2])+" Hz")
        DEBUG("\tpolar angles [alpha,beta] ("+str(index)+"): ["
             + str(parameters.dipole[i, 4])+","
             + str(parameters.dipole[i, 5])+","
             + str(parameters.dipole[i, 6])+"]")
        return dip

###########################
## PULSES and COHERENCES ##
###########################

    #------------------------
    def set_idealpulse(self):
    #------------------------
        """
        The pulse is considered as an ideal pulse
        """
        if check_abort():
            return

        DEBUG("SET_IDEAL")
        self.sequence.idealpulse()

    #---------------------------------------------------------------------------
    def set_pulse(self, length=0, powerS=0, offsetS=0, phaseS=0,
                                powerI=0, offsetI=0, phaseI=0,
                                selectS=999, selectI=999):
    #---------------------------------------------------------------------------
        """
         SYNTAX:set_pulse(self,length=0,powerS=0,offsetS=0,phaseS=0,selectS=999,
                                        powerI=0,offsetI=0,phaseI=0,selectI=999)
         'Set pulse parameters'
         optional args:
            length - pulse duration (default is 0)
            powerS, powerI - rf power respectively on spin S (1) and I (2)
            offsetS, offsetI - offset respectively on spin S and I
            phaseS, phaseI - pulse phase instruction resp. on S and I
            selectS, selectI - selected coherence on S and I
                              (only for S for the moment)
        """
        if check_abort():
            return

        if selectI!=999:
            cm.LOG_WARNING("Coherence selection on I spin not implemented!")

        DEBUG("SET_PULSE")
        #print "\nsetpulse"
        #print length,powerS,offsetS,phaseS,powerI,offsetI,phaseI
        #print selectS
        isSetPulse=self.sequence.pulse(length, powerS, offsetS, phaseS, powerI,
                    offsetI, phaseI)
        #print "isSetPulse",isSetPulse
        if isSetPulse:
            #Create or update CTP(coherence transfer pathways)
            np=len(parameters.pulse)
            #print "np", np
            if np==0:
                raise UserError, "Error in set_pulse (actual number of pulse=0)"
            if np==1:
                #set the first element of one ctp to 0
                self.ctpall.append([0])

            #now we treat the command argument: selectS
            if type(selectS) is types.ListType \
                   or type(selectS) is types.TupleType:
                arrayselectS=array(selectS)
            else:
                arrayselectS=array([selectS])
            length=len(arrayselectS)
            #print "array",arrayselectS, length
            if length==0:
                raise UserError, "Error in selectS: Null array!"

            if length>len(self.ctpall):
                #in this case the number of ctp's is increased
                # (duplicate the last one)
                for i in range(len(self.ctpall)-length):
                    self.ctpall.append(self.ctpall[len(self.ctpall)-1])

            if length<len(self.ctpall):
                #in this case there is less ctp
                #extend the selectS list to the number of required ctp.
                cm.LOG_WARNING("For pulse "+str(np)
                           +" the coherence selection list was two short." \
                            "It has been automatically extended")
                for i in range(len(self.ctpall)-length):
                    arrayselectS.append(arrayselectS[length-1])

            for i in range(length):
                #now we add the selection
                self.ctpall[i].append(arrayselectS[i])

            #print "\npulse:",np, "ctp",self.ctpall


    #-------------------------------------------
    def set_delay(self, length=0, decouple=false):
    #-------------------------------------------
        """
         SYNTAX : set_delay(length,decouple)
         'Set delay parameters'
         args:
            length - delay duration
            decouple - decoupling flag (default=false)
        """
        if check_abort():
            return

        DEBUG("SET_DELAY")
        self.sequence.delay(length, decouple)

    #-------------------------------------------
    def set_rcph(self, phase=0):
    #-------------------------------------------
        """
         'Set receiver phase'
         arg:
         - phase, default 0
        """
        if check_abort():
            return

        DEBUG("SET_RCPH")
        if phase==0: return # nothing to do
        parameters.rcph=phase # transmit to the fortran program

#-------------------------------------------------------------------------------
    def set_phases(self, phc0=0, phc1=0, phcursor=0):
#-------------------------------------------------------------------------------
        """
         'Set receiver phase'
         arg:
         - phase, default 0
        """
        if check_abort():
            return

        DEBUG("SET_PHASE")
        self.phc0=phc0
        self.phc1=phc1
        self.phcursor=phcursor

    # set ctp------------------
    def set_pathway(self, *list):
    #--------------------------
        """ create one CTP(s) from a list of value """

        if check_abort():
            return

        self.ctpall=[]
        self.noparametersulses=len(parameters.pulse)

        DEBUG("ADDING A COHERENCE TRANSFER PATHWAY:")
        DEBUG("------------------------------------")
        #sometimes a list  is passed as a single argument
        if type(list[0]) is types.ListType or type(list[0]) is types.TupleType:
            pathway=list[0]
        else:
            pathway=list

        #print "pathway",len(pathway),pathway

        if len(pathway)!= self.noparametersulses+1:
            raise UserError, "The length of the submitted list of coherence is not correct. \
            \n       It must be the number of pulse"

        if pathway[0]!=0 or pathway[len(pathway)-1]!=-1:
            raise UserError, "List must start with 0 end ending with -1"

        self.ctpall.append(pathway)

    # add ctp------------------
    def add_pathway(self, *list):
    #--------------------------
        """ create one CTP(s) from a list of value """

        if check_abort():
            return

        self.noparametersulses=len(parameters.pulse)

        DEBUG("ADDING A COHERENCE TRANSFER PATHWAY:")
        DEBUG("------------------------------------")
        #sometimes a list  is passed as a single argument
        if type(list[0]) is types.ListType or type(list[0]) is types.TupleType:
            pathway=list[0]
        else:
            pathway=list

        DEBUG("pathway", len(pathway), pathway)

        if len(pathway)!= self.noparametersulses+1:
            raise UserError, "The length of the submitted list of coherence is not correct. \
                          \n       It must be the (number of pulse)"
            return

        if pathway[0]!=0 or pathway[len(pathway)-1]!=-1:
            raise UserError, "List must start with 0 end ending with -1"

        self.ctpall.append(pathway)

    #------------------------
    def print_pathways(self):
    #------------------------
        """ print selected coherence transfers pathways """
        if check_abort():
            return
        i=1
        self.ctpall.sort()
        #create a dictionnary (to reference easily the various coherence)
        self.ctpdict={}
        for c in self.ctpall:
            self.ctpdict[i]=c
            strg = str(int(i)) + ":  {"
            for j in range(size(self.ctpall, 1)-1):
                item=c[j]
                if abs(item)<=999:
                    strg= strg + str(int(item)).rjust(3)+" ->"
                else:
                    strg= strg + "("+str(int(item-10000)).rjust(3)+","
                    +str(-int(item-10000)).ljust(3)+") ->"
            strg=strg + " -1 }"
            cm.LOG_VERBOSE(strg)
            i=i+1

    #------------------------
    def check_pathways(self):
    #------------------------
        """ check coherence transfers pathways """
        if check_abort():
            return

        DEBUG("LIST OF POSSIBLE COHERENCE TRANSFER PATHWAYS (CTP):")

        self.noparametersulses=len(parameters.pulse)

        if (self.noparametersulses==1):
            cm.LOG_WARNING("single pulse, no CTP selection possible")
            return

        self.ns=2*parameters.nucleus[0, 1]  #maximum order
        pend=0
        ctp=range(self.noparametersulses+1)
        self.ctpall=[]
        self.searchp(1, pend, ctp)

        if len(self.ctpall)==0 :
            message= "No valid coherence transfer has been found:"\
                       +"\n\t  Check your coherence transfer settings!"\
                       +"\n\t   e.g., sum("\
                       +chr(127)+"p) "\
                       +"must be -1 for the observed spin S and 0 for spin I"
            raise UserError,message

        # store the result
        nctp=size(self.ctpall, 0)
        self.ctpall.sort()
        if nctp!=pow(2*self.ns+1, self.noparametersulses-1):
            DEBUG("number of CTPs: " + nctp)
            self.print_ctp()
            parameters.ctp=self.ctpall
        else:
            DEBUG(" all allowed")
            #TODO: check some other situation where it is not needed to
            #      make the calculation of all CTPs


    # compress coherence transfers----------------------------------------------
    def compress_ctp(self):
    #---------------------------------------------------------------------------
        #global noparametersulses, ns, ctpall
        if check_abort():
            return

        DEBUG("REDUCING NUMBER OF CTP :")

        l=len(self.ctpall)
        if l==0 :
            raise UserError, "No valid coherence transfer has been found"

        # look for pathway where two symmetrical coherences are found
        for c1 in self.ctpall:
            # print "check ",c1
            for c2 in self.ctpall:
                if c2!=c1:
                    # print "compare with ",c2
                    for i in range(1, size(self.ctpall, 1)-1):
                        # look each items except the first one (always 0)
                        # and the last (-1).
                        store=c2
                        store[i]=-store[i]
                        if store==c1:
                            #this two pathway are identical except
                            #for one element which is symetric
                            #we can reduce it to only one (we add 10000 to says
                            #that two symetric element
                            #must be retained)
                            self.ctpall.remove(c2)
                            self.ctpall.remove(c1)
                            store[i]=abs(store[i])+10000
                            self.ctpall.append(store)
                            #DEBUG( store )
                        break
        if len(self.ctpall)== l :
            DEBUG("No reduction possible.")
        else:
            parameters.ctp=self.ctpall
            self.print_ctp()

    # searchp-------------------------------------------------------------------
    def searchp(self, nc, pend, ctpi):
    #---------------------------------------------------------------------------
        """
        recursive function
        used by check_ctp
        """
        #global noparametersulses, ns, ctpall
        if check_abort():
            return

        ctpi[nc-1]=pend
        if nc==(self.noparametersulses+1):
            if pend==-1 and nc==(self.noparametersulses+1):
                c=[]
                for i in ctpi:
                    c.append(i)
                self.ctpall.append(c)
            return
        else:
            dp=parameters.coher[nc-1, 1]
            nbphases=parameters.coher[nc-1, 2]
            if dp==999 :   #all jumps allowed
                dp=1
                nbphases=1
            for n in range(-int(3*self.ns), int(3*self.ns)):
                p=pend+dp+nbphases*n
                if p<=self.ns and p>=-self.ns :
                    self.searchp(nc+1, p, ctpi)

    # remove_ctp----------------------------------------------------------------
    def remove_ctp(self, index):
    #---------------------------------------------------------------------------
        """ remove_ctp : to remove one or more ctp in the list
            arg: index is a scalar
                 or a list in the format (index1, index2...)"""
        if check_abort():
            return

        #global ctpdict, ctpall
        DEBUG("REMOVING CTP"+str(index))
        # here the dictionnary is useful
        #(because we cannot know easily the order of the list element)
        try:
            for i in index:
                del self.ctpdict[i]
        except:
            try:
                del self.ctpdict[index]  #if list is a single number
            except:
                raise UserError, "in 'remove_ctp' command"

        self.ctpall=self.ctpdict.values()
        parameters.ctp=self.ctpall
        self.print_ctp()

##    #-----------------------------------------
##    XXX: def select_coherence(self,dp=999,nbphases=1):
##    #-----------------------------------------
##        """
##         SYNTAX : select_coherence(self,dp=999,nbphases=1)
##         'select coherence transfer and mode of selection'
##         args:
##            dp - coherence transfer jump (999 : no selection)
##            nbphases - number of phases (1 by default : no phase cycling)
##        """
##        if check_abort():
##            return
##
##        DEBUG("SELECT_COHERENCE")
##        self.sequence.coherence(dp,nbphases)

#-------------------------------------------------------------------------------
# Property isFitting
#-------------------------------------------------------------------------------
    def _setFitting(self,value):
        self.__isfitting = value
    def _getFitting(self):
        return self.__isfitting
    isFitting = property(fset= _setFitting, fget= _getFitting)

#-------------------------------------------------------------------------------
# Property calculatedSpectra
#-------------------------------------------------------------------------------
    def _getcalculatedSpectra(self):
        calc = self.__calculatedspectra
        if calc is not None:
            data, npts, nspec, sw, lbs, gbs, concs = calc
        else:
            return None
        # set in save_spectra
        specsum = zeros_like(data[0])
        for k in range(nspec):
            spec = array(data[k],"Complex64")
            lb = lbs[k]
            gb = gbs[k]
            conc = concs[k]
            s = broadening(spec, sw, lb = lb, gb = gb)
            for i in range(npts):
                specsum[i] = specsum[i] + s[i] * conc
        # return the summed spectra and the parameters
        return specsum
    calculatedSpectra = property(fget= _getcalculatedSpectra)

#-------------------------------------------------------------------------------
# Property Data
#-------------------------------------------------------------------------------
    def _getData(self):
        return self.__data
    Data = property(fget= _getData)

#==============================================================================
class Sample:
#==============================================================================
    """
    A class to handle the parameters relative to a set of nucleus for one sample
      * A sample contain list of nuclei
      * A list of nuclei corresponds to one type of nuclei (key: ex. 27Al, etc)
                  and may contains several nucleus (instances of class nucleus).
      (for the moment this class stay private)
    """
    #------------------
    def __init__(self):
    #------------------
        """
        initialize the class sample with a zero number of nucleus
        """
        DEBUG("INIT Sample")
        self.nuclei = {}        #initialize to no nucleus
        self.observed = None
            #no observed nucleus defined
            #(by default it will be the first one that will be defined)

    #---------------------------------
    def add_nucleus(self, newnucleus):
    #---------------------------------
        """
            add a nucleus (instance of class nucleus) to the sample
            args:
            - newnucleus: a nucleus instance
        """
        # the name of the isotope become the key
        key=newnucleus.isotope

        DEBUG("ADD NUCLEUS " + key + " to Sample")

        # if there is no nuclei already defined and in case we need to know
        # what was the first nuclei entered in this dictionary
        if not self.nuclei: self.observed=key

        # if this key does not exist yet,
        # create a new list a nuclei for this key
        if not self.nuclei.has_key(key): self.nuclei[key] = []

        # add the nucleus to the list corresponding to this key
        # (we have also to give it some index: useful for select_nucleus)
        newnucleus.index=len(self.nuclei[key])
        self.nuclei[key].append(newnucleus)

    #-------------------------------------------------------------------
    def validate(self, key, index=0, delta=0, abundance=1, observed=False):
    #-------------------------------------------------------------------
        """
            Validation of one nucleus
            args:
            - key: the isotope INFO
            - index: the index of the nucleus in the list
                      corresponding to the key
            - delta: to handle different nucleus with close larmor frequency
            - abundance: The abundance of course
                         with respect to the natural abundance
            - observed (Boolean): Say if the nucleus is observed or not
        """
        DEBUG("VALIDATE a nucleus in the sample")

        # if there is not nuclei, return
        if not self.nuclei: return

        # if such key does not exist, return
        if not self.nuclei.has_key(key): return

        #extract the nucleus instance with the key and the index indicated
        nucleus=self.nuclei[key][index]
        nucleus.validate(delta, abundance, observed)

#===============================================================================
#    #----------------------
#    def validate_all(self):
#    #----------------------
#        """
#            Validation of all nuclei in the sample
#            (XXX: I don't know if this can be useful)
#        """
#        DEBUG("VALIDATE ALL Nuclei in the sample")
#
#        # if there is some nuclei in the sample, validate all in sequence
#        if self.nuclei:
#            nuclei=[]
#            for key,nuclei in self.nuclei.items():
#                for nucleus in nuclei:
#                    nucleus.validate()
#===============================================================================

#==============================================================================
class Nucleus:
#==============================================================================
    """
    A class to define the nucleus parameters
    """


    #---------------------------------
    def __init__(self, isotope = "1H"):
    #---------------------------------
        """
            set default parameters
            arg:
            - isotope = '1H'
        """
        DEBUG("INIT Nucleus "+isotope)
        self.isotope = isotope
        self.nucleus=None

        try:
            #read from peiodictable
            self.nucleus = isotopes[isotope]
        except KeyError:
            message = isotope+ \
                      " was not found in the nucleus list, "+ \
                      "Check its name and/or the its number"
            raise KeyError, message

            #extract the known parameters
##            self.spin = self.nucleus["spin"]
##            self.larmor = abs(self.nucleus["larmor"])
##            self.name = self.nucleus["name"]
##            self.quadmoment = self.nucleus["quadrupole"]
##            self.abundance = self.nucleus["abundance"]
##            self.relative = self.nucleus["relative"]
##            self.absolute = self.nucleus["absolute"]

            #init some initial values for user parameters
        self.set_chemicalshift(init_only=True)
        self.set_quadrupole()
        self.set_relaxation()
        self.lb=0.01
        self.gb=0.
        self.concentration=1.

##        if hasattr(self,"isppm"):
##            del self.isppm

        #except:
        # raise_exception("Something is wrong with the INIT Nucleus procedure!")

    #--------------------------------------------------------
    def validate(self, delta=0, abundance=None, observed=False):
    #--------------------------------------------------------
        """
            Validate parameters in the fortran module
            args:
            - delta: Shift in Larmor frequency
            - abundance: Natural abundance=1
            - observed: to say if the nucleus is observed (True) or not (False)
        """
        DEBUG("VALIDATE Nucleus")

         #No nucleus to validate?
        if not self.nucleus:
            raise UserError, "problem: No nucleus to validate!"

        spin = self.nucleus["spin"]
        larmor = abs(self.nucleus["larmor"])
        name = self.nucleus["name"]
#        quadmoment = self.nucleus["quadrupole"]
        if abundance is None: abundance = self.nucleus["abundance"]
#        relative = self.nucleus["relative"]
#        absolute = self.nucleus["absolute"]

        if parameters.nucleus == None:
            # if the 'parameters.nucleus' doesn't exist
            # create the temporary 'ar' array with a  single line
            # this becomes the observed nuclei
            #----------------------------------------------------
            self.index = 1
            ar = [[self.index,
                     spin, larmor*parameters.protonfrequency/100., abundance]]
                            #conversion made to actual larmor frequency
            # allocate and initialize the 'parameters.nucleus' array
            # with the 'ar' array
            parameters.nucleus = ar
        else:
            # the 'parameters.nucleus' array exist already
            if observed:
                #in this case, our nucleus must be on line 0 with index 1!
                self.index=1
                parameters.nucleus[0] = [self.index, spin,
                     larmor*parameters.protonfrequency/100., abundance]
            else:
                # then copy the existing 'parameters.nucleus'
                # array into the temporary 'ar' array
                #---------------------------------------------------------------
                nofnuclei  =  len(parameters.nucleus)
                ar = [[0, 0, 0, 0] for i in range(nofnuclei+1)]
                i = 0
                while i < nofnuclei :
                    ar[i] = [i+1, parameters.nucleus[i, 1],
                             parameters.nucleus[i, 2],
                             parameters.nucleus[i, 3]]
                             #copy of the previous elements
                    i = i+1
                # and add a new line
                #-------------------
                self.index = nofnuclei+1
                ar[nofnuclei] = [self.index, spin,
                              larmor*parameters.protonfrequency/100., abundance]
                                #conversion made to actual larmor frequency

                # allocate or reallocate and initialize the 'parameters.nucleus'
                # array with the 'ar' array
                #---------------------------------------------------------------
                parameters.nucleus = ar

        nofnuclei  =  len(parameters.nucleus)

        # chemical shift
        #---------------
        # conversion ppm to hz (depends on the larmor frequency)
        # add the shift due to eventual difference with the radio frequency
        if hasattr(self,"isppm") and self.isppm:
            DEBUG("Is PPM?",self.isppm)
            ppm = parameters.nucleus[self.index-1, 2]/mhz
        else:
            DEBUG("Is PPM?",False)
            ppm = 1.0 #Hz unit by default
        iso = self.iso*ppm + delta
        csa = self.csa*ppm
        DEBUG(iso, csa," in Hz")

        if parameters.chemicalshift == None:
            # if the 'parameters.chemicalshift' array doen't exist, create it
            # with one line
            # (which in principe correspond to index 1
            # as this function is called immediately
            # after the creation of the each nuclei)
            ar = [[self.index, iso, csa, self.etacsa, self.alphacsa,
                   self.betacsa, self.gammacsa]]
        else:
            # the size of the 'parameters.shift' has to be the same
            # as the size of 'parameters.nucleus'
            # copy of the previous elements
            ar = [[0, 0, 0, 0, 0, 0, 0] for i in range(nofnuclei)]
            i = 0
            size = len(parameters.chemicalshift)
            while i < size :
                ar[i] = [int(parameters.chemicalshift[i, 0]),
                         parameters.chemicalshift[i, 1],
                         parameters.chemicalshift[i, 2],
                         parameters.chemicalshift[i, 3],
                         parameters.chemicalshift[i, 4],
                         parameters.chemicalshift[i, 5],
                         parameters.chemicalshift[i, 6]]
                i = i+1
            # replace the line of the given index with the new one
            ar[self.index-1] = [self.index, iso, csa, self.etacsa,
                                self.alphacsa, self.betacsa, self.gammacsa]
        parameters.chemicalshift = ar
        #allocate or reallocate and initialize

        if parameters.quadrupole==None:
            # if the 'parameters.quadrupole' array doesn't exist,
            #create it with one line
            # (which in principe correspond to index 1)
            ar = [[self.index, self.cq, self.etaq, self.alphaq, self.betaq,
                 self.gammaq]]
        else:
            #copy of the previous elements
            ar = [[0, 0, 0, 0, 0, 0] for i in range(nofnuclei)]
            i = 0
            size = len(parameters.quadrupole)
            while i < size :
                ar[i] = [int(parameters.quadrupole[i, 0]),
                         parameters.quadrupole[i, 1],
                         parameters.quadrupole[i, 2],
                         parameters.quadrupole[i, 3],
                         parameters.quadrupole[i, 4],
                         parameters.quadrupole[i, 5]]
                i = i+1
            ar[self.index-1] = [self.index, self.cq, self.etaq, self.alphaq,
                  self.betaq, self.gammaq]
        parameters.quadrupole = ar
            #allocate or reallocate and initialize
        # T2
        if parameters.t2 == None:
            # if the 'parameters.t2' array doen't exist, create it with one line
            # (which in principe correspond to index 1)
            ar = [[self.index, self.t2]]
        else:
            # copy of the previous elements
            size = len(parameters.t2)
            ar = [[0, 0] for i in range(nofnuclei)]
            i = 0
            while i < size :
                ar[i] = [int(parameters.t2[i, 0]), parameters.t2[i, 1]]
                i = i+1
            # replace the line of the given index with the new one
            ar[self.index-1] = [self.index, self.t2]
            # the numbering start at zero (this is why I use index-1)
        parameters.t2 = ar
        #allocate or reallocate and initialize


        #Display the current parameters
        #------------------------------
        cm.LOG_VERBOSE("NUCLEUS: "+name)
        cm.LOG_VERBOSE("------------")
        if self.index == 1 :
            cm.LOG_VERBOSE("\t-This is the observed nucleus")
        if self.index == 2 :
            cm.LOG_VERBOSE("\t-This is the excited but non observed nucleus I" \
                        +" \n\t-only ONE excited nucleus in this version-")
        if self.index > 2 :
            cm.LOG_VERBOSE("\t-additionnal NON-excited nucleus")
        if self.index > 1 :
            cm.LOG_VERBOSE( \
        "\t  (For information, the index of this nucleus will be "
                 +str(self.index-1)+" for future reference)")
        i = self.index-1
        spin=parameters.nucleus[i, 1]
        if (spin*2 == int(spin)*2):
            cm.LOG_VERBOSE("\tspin: " + str(int(spin)))
        else:
            cm.LOG_VERBOSE("\tspin: " + str(int(spin*2))+"/2")
        cm.LOG_VERBOSE("\tlarmor frequency: "
          + str(parameters.nucleus[i, 2]/mhz)+" MHz")
        if self.index<3:
            cm.LOG_VERBOSE("\tisotropic shift: "
            + str(parameters.chemicalshift[i, 1]) + " Hz")
            if parameters.chemicalshift[i, 2]!=0 :
                cm.LOG_VERBOSE("\tcsa anisotropy: "
                + str(parameters.chemicalshift[i, 2])+" Hz")
            if parameters.chemicalshift[i, 2]!=0 :
                cm.LOG_VERBOSE("\teta csa: "
                 + str(parameters.chemicalshift[i, 3]))
            if parameters.chemicalshift[i, 2]!=0 :
                cm.LOG_VERBOSE("\teuler csa [alpha,beta,gamma]: ["
                + str(parameters.chemicalshift[i, 4])+","
                +str(parameters.chemicalshift[i, 5])+","
                +str(parameters.chemicalshift[i, 6])+"]")
            if parameters.quadrupole[i, 1]!=0 :
                cm.LOG_VERBOSE("\tQuadrupolar coupling : "
                + str(parameters.quadrupole[i, 1]/mhz)+" MHz")
            if parameters.quadrupole[i, 1]!=0 :
                cm.LOG_VERBOSE("\teta Quadrupole: "
                + str(parameters.chemicalshift[i, 2]))
            if parameters.quadrupole[i, 1]!=0 :
                cm.LOG_VERBOSE("\teuler Quadrupole [alpha,beta,gamma]: ["
                + str(parameters.quadrupole[i, 3])+ \
                             ","+str(parameters.quadrupole[i, 4])
                             +","+str(parameters.quadrupole[i, 5])+"]")
            cm.LOG_VERBOSE("\tT2 relaxation: "
                  +str(parameters.t2[i, 1]/sec)+" sec")
            cm.LOG_VERBOSE("\tLB: "+str(self.lb)+" Hz")
            cm.LOG_VERBOSE("\tGB: "+str(self.gb)+" Hz")
            cm.LOG_VERBOSE("\tconcentration: "+str(self.concentration))

    # --------------------------------------------------------------------------
    def set_chemicalshift(self, iso=0, csa = 0, eta = 0, alpha = 0,
                                beta = 0, gamma = 0, init_only=False):
    #---------------------------------------------------------------------------
        """
            Set the chemical shift of a given nucleus
            args:
            - index - index of the nucleus (defined previously by set_nucleus)
            - iso - isotropic chemical shift
            - csa - chemical shift anisotropy
            - eta - assymetry of the csa
            - alpha, beta, gamma - euler angles describing the orientation
                                 with respect to the molecular frame
        """
        DEBUG("Nucleus SET CHEMICAL SHIFT")
        if not init_only:
            DEBUG("iso to evaluate: ",iso)
            self.iso, isppm = evaluate(iso,set_isppm=True)
            self.csa, isppm2 = evaluate(csa,set_isppm=True)

            #check the isppm flag
            DEBUG(self.iso, isppm)
            DEBUG(self.csa, isppm2)

            if not hasattr(self,"isppm"): #first definition of isppm
                self.isppm = isppm
                DEBUG("first time self.isppm:",self.isppm)
            else:
                DEBUG("now self.isppm is set to ",self.isppm)
                if self.csa > 0.0 and isppm2!=self.isppm:
                    #unit for iso and csa are different
                    raise TypeError, "Sorry but units (Hz or ppm) for ISO and CSA"
        else:
            self.iso=0.0
            self.csa=0.0

        self.etacsa=evaluate(eta)
        self.alphacsa=evaluate(alpha)
        self.betacsa=evaluate(beta)
        self.gammacsa=evaluate(gamma)

    # set_relaxation---------------------
    def set_relaxation(self, t2 = 1.0e+30):
    #------------------------------------
        """
            Set the T2 of a given nucleus
            args:
            - index : index of the nucleus (defined previously by set_nucleus)
            - t2 : T2 relaxation time
        """
        DEBUG("Nucleus SET RELAXATION")
        self.t2 = evaluate(t2)

    # set_quadrupole ----------------------------------------------------
    def set_quadrupole(self, cq = 0, eta = 0, alpha = 0, beta = 0, gamma = 0):
    #--------------------------------------------------------------------
        """
            Set the quadrupolar parameters of a given nucleus
            args:
            - index - index of the nucleus (defined previously by set_nucleus)
            - cq - quadrupolar coupling constant in Hz
            - eta - assymetry of the quadrupolar interaction tensor
            - alpha, beta, gamma - euler angles describing the orientation
                                 with respect to the molecular frame
        """
        DEBUG("Nucleus SET QUADRUPOLE")
        if not self.nucleus:
            return

        self.cq = evaluate(cq)
        self.etaq = evaluate(eta)
        self.alphaq = evaluate(alpha)
        self.betaq = evaluate(beta)
        self.gammaq = evaluate(gamma)
        if self.nucleus["spin"]<1:
            #if the spin is non quadrupolar
            self.cq = 0.0
            self.etaq = 0.0
            self.alphaq = 0.0
            self.betaq = 0.0
            self.gammaq = 0.0

    # set_lb-------------------
    def set_lb(self, lb = 0.01):
    #--------------------------
        """
            Set the LB of a given nucleus
            args:
            -lb - broadening (lorenzian)
        """
        DEBUG("Nucleus SET LB")
        self.lb = evaluate(lb)

    # set_gb------------------
    def set_gb(self, gb = 0.0):
    #-------------------------
        """
            Set the GB of a given nucleus
            args:
            - gb - broadening (gaussian)
        """
        DEBUG("Nucleus SET GB")
        self.gb = evaluate(gb)

    # set_concentration-------
    def set_concentration(self, concentration = 1.0):
    #-------------------------
        """
        Set the CONCENTRATION of a given nucleus
        """
        DEBUG("Nucleus SET CONCENTRATION")
        self.concentration = evaluate(concentration)

#===================
class PulseSequence:
    """
    A class to handle the pulse sequence definition
    """

    #------------------
    def __init__(self):
    #------------------
        DEBUG("Pulse INIT")
        pass

    #--------------------
    def idealpulse(self):
    #--------------------
        DEBUG("Pulse IDEALPULSE")
        parameters.idealpulse= True
        self.addpulse()
        return True

    #------------------------
    def pulse(self, length=0, powerS=0, offsetS=0, phaseS=0,
                            powerI=0, offsetI=0, phaseI=0):
    #------------------------
        DEBUG("pulse PULSE")
        parameters.idealpulse= False
        return self.addpulse(length, powerS, offsetS, phaseS, powerI,
                             offsetI, phaseI)

    # --------------------------------------------------------------------------
    def addpulse(self, length=0, powerS=0, offsetS=0, phaseS=0, powerI=0,
                 offsetI=0, phaseI=0):
    #---------------------------------------------------------------------------
        DEBUG("pulse ADDPULSE")

        length=evaluate(length)
        powerS=evaluate(powerS)
        powerI=evaluate(powerI)
        offsetS=evaluate(offsetS)
        offsetI=evaluate(offsetI)
        phaseS=evaluate(phaseS)
        phaseI=evaluate(phaseI)

        if (abs(powerS)+abs(powerI))< 0.1 and parameters.pulse:
            #in this case there is no power (no pulse)... set a delay instead!
            #but only if a pulse already exist (important for ideal pulse)
            self.delay(length)
            return False  # Return isSetPulse=False

        if parameters.pulse==None:
            index=1
            ar=[[index, length, powerS, offsetS, phaseS, powerI,
                 offsetI, phaseI]]

        else:

            size=len(parameters.pulse)
            ar=[[0, 0, 0, 0, 0, 0, 0, 0] for i in range(size+1)]
            i=0
            while i < size :
                ar[i]=[int(parameters.pulse[i, 0]), parameters.pulse[i, 1],
                       parameters.pulse[i, 2], parameters.pulse[i, 3],
                       parameters.pulse[i, 4], parameters.pulse[i, 5],
                       parameters.pulse[i, 6], parameters.pulse[i, 7]]
                #copy of the previous elements
                i=i+1
            index=size+1
            ar[size]=[index, length, powerS, offsetS, phaseS, powerI,
                  offsetI, phaseI]
        parameters.pulse=ar
        # allocate or reallocate and initialize

        # put automatically a delay=0 and select_coherence()
        # -> no selection by default
        self.delay(length=0)

        #return isSetPulse
        return True

    # -----------------------------------------------
    def delay(self, length=0, decoupling=false):
    #------------------------------------------------
        DEBUG("pulse DELAY")

        if parameters.pulse==None:
            cm.LOG_WARNING("A sequence cannot start with a delay"
               +" (no effect). It is ignored")
            return
        # the index will be that of the preceeding pulse
        noparametersulses=len(parameters.pulse)

        length=evaluate(length)
        nodecouple=1
        if decoupling : nodecouple=0

        if parameters.delay==None:
            ar=[[1, length, nodecouple]]
        else:
            ar=[[0, 0, 0] for i in range(noparametersulses)]
            #copy of the previous elements
            i=0
            size=len(parameters.delay)
            while i < size :
                ar[i]=[int(parameters.delay[i, 0]), parameters.delay[i, 1],
                     parameters.delay[i, 2]]
                i=i+1
            if ar[noparametersulses-1][1]==0:
                ar[noparametersulses-1]=[noparametersulses, length, nodecouple]
#                updated=''
            else:
                ar[noparametersulses-1][1]=ar[noparametersulses-1][1]+length
#                updated="updated "

        parameters.delay=ar  #allocate or reallocate and initialize

##    # coherence ----------------------------
##    def coherence(self,dp=999,nbphases=1):
##    #---------------------------------------
##        DEBUG("pulse COHERENCE")
##        dp=evaluate(dp)
##        nbphases=evaluate(nbphases)
##        if parameters.pulse==None:
##            cm.LOG_WARNING(
##"WARNING: A sequence cannot start with a coherence selection (no effect).
##It is ignored")
##            return
##        if dp==999:
##            nbphases==1    #no selection at all in this case
##        # the index will be that of the preceeding pulse
##        noparametersulses=len(parameters.pulse)
##        if parameters.coher==None:
##            ar=[[1,dp,nbphases]]
##        else:cm.LOG_STRIN
##            ar=[[0,0,0,0] for i in range(noparametersulses)]
##            #copy of the previous elements
##            i=0
##            size=len(parameters.coher)
##            while i < size :
##                ar[i]=[int(parameters.coher[i,0]), parameters.coher[i,1],
## parameters.coher[i,2]]
##                i=i+1
##            ar[noparametersulses-1]=[noparametersulses,dp,nbphases]
##        parameters.coher=ar          # allocate or reallocate and initialize
##        if dp!=999:
##            if (self.verbose) : pass #cm.LOG_VERBOSE("coherence selection :
## Number of phases N="+str(nbphases)+", Required "+chr(127)+"p="+str(dp))
##        if nbphases==1:
##            if (self.verbose) : pass #cm.LOG_VERBOSE("no coherence selection")

#######################
##  MODULE FUNCTIONS ##
#######################

#-----------------------------------------------------------------
def dipole_from_distance(distance, f1, f2, field=None):
#-----------------------------------------------------------------
    """
    Compute dipolar coupling from distances
    @param distance : distances between nucleus 1 and 2(Angtroms)
    @type distance: Float
    @param f1: larmor frequency of nuclei 1 (MHz)
    @type f1: Float
    @param f2: larmor frequency of nuclei 2 (MHz)
    @type f2: Float
    @param field: optional spectrometer field (Tesla).
                  Default is the current field.
    @type field: Float
    @return: Dipolar coupling in Hz
    @rtype: Float
    """

    if not field:
        field = parameters.spectrometerfield

    h = 6.6260693e-34
    mu0 = 4*math.pi*1.0e-7
    f1 = f1/field
    f2 = f2/field
    c=abs(f1*f2*mu0*h/4.0/math.pi)

    try:
        dipolar = c/(distance*1.0e-10)**3
    except:
        raise UserError, "calculation of dipolar coupling not possible: check parameters!"

    DEBUG("Dipolar coupling=%10.3f Hz"%dipolar)
    DEBUG("\t[Distance=%10.3f Angstrom,"%distance)
    DEBUG("\t Spectrometer field=%10.3f Tesla]"%field)

    return dipolar

#----------------------------------------------------------------
def distance_from_dipole(dipolar, f1, f2, field=None):
#----------------------------------------------------------------
    """
    Compute distance from dipolar coupling
    @param dipolar : dipolar coupling between nucleus 1 and 2(Hz)
    @type dipolar: Float
    @param f1: larmor frequency of nuclei 1 (MHz)
    @type f1: Float
    @param f2: larmor frequency of nuclei 2 (MHz)
    @type f2: Float
    @param field: optional spectrometer field (Tesla).
                  Default is the current field
    @type field: Float
    @return: Distance in Angstrom
    @rtype: Float
    """

    if not field:
        field = parameters.spectrometerfield

    h = 6.6260693e-34
    mu0 = 4*math.pi*1.0e-7
    f1 = f1/field
    f2 = f2/field
    p=1.0/3.0
    c=abs(f1*f2*mu0*h/4.0/math.pi)

    try:
        distance=1.0e10*((c/dipolar)**p)
    except:
        raise UserError, "calculation of distance not possible: check parameters!"
        return False

    DEBUG("Distance=%10.3f Angstrom"%distance)
    DEBUG("\t[Dipolar coupling=%10.3f Hz"%dipolar)
    DEBUG("\t Spectrometer field=%10.3f Tesla]"%field)

    return distance

#----------------------------------
def evaluate(strg, set_isppm=False):
#----------------------------------
    """
    Allow the evaluation of strings containing units
    @param strg: string  containing units to evaluate, e.g., '10 kHz'
    @type strg: string
    @param isppm: Flag to specify that ppm is required
    @type isppm: Boolean
    @return: Value of the string, or False, if there is an error
    @rtype: Float or Boolean

    @todo: implement ppm units!
    """

    res = False
    isppm = False

    if type(strg) is types.StringType:

        strg=string.upper(strg)

        p = re.compile('\s+')
        m = p.split(string.strip(strg))

        try:
            res = eval(m[0])
        except NameError:
            message="Cannot evaluate '"+strg+"' >> "+m[0]+" is not defined"
            raise NameError,message
        except SyntaxError:
            message="Syntax error in '"+strg+"'"
            raise SyntaxError,message

        #read unit
        if len(m) > 1:

            if string.strip(m[1]) == "PPM":
            #ppm will be evaluated later: set flag isppm to True
                isppm=True
                m[1]="HZ"
            try:
                res=res*eval(m[1])
            except NameError:
                message= "Cannot evaluate '"+strg+"' >> "
                +m[1]+" is not defined"
                raise UserError,message
            except SyntaxError:
                message="Syntax error in '"+strg+"'"
                raise UserError,message
    else:

        # not a string (probably a scalar that can be return as it is)
        res = strg

    if not set_isppm:
        return res
    else:
        return res, isppm

#-----------------
def showmatrix(d):
#-----------------
    """
    Display a matrix
    @param d: matrix to display
    """
    nr = len(d)
    nc = len(d[0])
    ii = 0
    strg='\n'
    while ii < nr:
        jj = 0
        while jj < nc:
            strg=strg + ("%10.3f+%10.3f.j "%(d[ii, jj].real, d[ii, jj].imag))
            jj = jj + 1
        strg=strg+"\n"
        ii = ii + 1
    cm.LOG_INFO(strg)

#----------------------
def nowhitespace(strg):
#----------------------
    """
    Remove whitespace in a string
    @param strg: Input string
    @return: string without whitespace
    """
    strg=list(str(strg))
    ch=''
    for x in strg:
        ch=ch+string.strip(str(x))
    return string.strip(str(ch))

#-----------------------------
def interval(start, end, inc=1):
#-----------------------------
    """
    Create a list corresponding from an interval
    @param start: starting values
    @param end: ending values
    @param inc: increment values
    @return: list of values in the interval
    """
    result=[]
    i=start
    while i<=end:
        result.append(i)
        i=i+inc
    return result

#--------------------
def write(something):
#--------------------
    """
    simple command to write on the log window
    @param something: INFO or value to write
    """
    if type(something) is not types.StringType:
        cm.LOG_INFO(str(something))
    else:
        cm.LOG_INFO(something)


###-------------
### EXCEPTIONS
###-------------
###-----------------------------------
##def raise_exception(text):
###-----------------------------------
##    """
##    Generate an exception
##    """
##    import traceback
##    parameters.keepgoing=False
##    parameters.exception=1
##    parameters.exception_text=array(string.ljust(text, 80))
##
###-----------------------------------
##def clear_exception():
###-----------------------------------
##    """
##    Clear generated exception
##    """
##    parameters.exception=-1
##
#-----------------------------------
def check_abort():
#-----------------------------------
    # Abort if Simulation was cancelled
    if not parameters.keepgoing:
        raise AbortWarning

#-----------------------------------
def abort():
#-----------------------------------
    # Abort if Simulation was cancelled
    parameters.keepgoing = False
    raise AbortWarning

#*******************************************************************************
#-TEST--------------------
if __name__ == "__main__":
#-------------------------
##    dipole_from_distance(1.1, 400000000.0, 400000000.0, field=9.36)
##    distance_from_dipole(91.0e3, 400000000.0, 400000000.0, field=9.36)
##    #the following should generate an error
##    distance_from_dipole(0, 400000000.0, 400000000.0, field=9.36)
##    print evaluate("1. ppm",False)

    pass
