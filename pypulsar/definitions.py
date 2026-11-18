#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      definitions.py
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

 global data to share between modules

"""
#-------------------------------------------------------------------------------

__docformat__="epytext"


#TODO: Revise this
prjkinds=[]
PYP_PROJECT=0; prjkinds.append("Project")
PYP_DATASET=1; prjkinds.append("Dataset")
PYP_SCRIPT=2; prjkinds.append("Script")
PYP_SPECTRUM1D=3; prjkinds.append("Spectrum1D")
PYP_SPECTRUM2D=4; prjkinds.append("Spectrum2D")
PYP_SPECTRUM3D=5; prjkinds.append("Spectrum2D")
PYP_GRAPH=6; prjkinds.append("Graph")
PYP_TEXT=7; prjkinds.append("Text")
PYP_PARAMETERS=8; prjkinds.append("Parameters")
PYP_IMAGE=9; prjkinds.append("Image")
PYP_ANY=10; prjkinds.append("Any")
PYP_CALCULATED1D=11; prjkinds.append("Calculated1D")
PYP_CALCULATED2D=12; prjkinds.append("Calculated2D")
PYP_CALCULATED3D=13; prjkinds.append("Calculated3D")
PYP_PROPERTY=14; prjkinds.append("Property")
PYP_SPECTRA=15; prjkinds.append("Spectra")
PYP_CALCSPECTRA=16; prjkinds.append("CalcSpectra") #FIXME: Change image
PYP_FIT=17; prjkinds.append("Fit") #FIXME: Change image

#collections
PYP_ALLSPECTRA=[3,4,5,6,11,12,13]
PYP_SPECTRACONTAINER = [15,16]
PYP_EXPERIMENTAL=[3,4,5]
PYP_CALCULATED=[11,12,13,16]
PYP_PYTHONEDITOR=[0,1,2,8]

# data kinds
EXP_FID=0
EXP_1D=1
EXP_SER=2
EXP_SER3D=3
EXP_2D=4
EXP_3D=5
EXP_DATA=6  #for arbitrary list of experimental data
CALC_1D=7
CALC_2D=8
CALC_3D=9
CALC_DATA=10  #for arbitrary list of calculated data
GRAPH_1D=11
GRAPH_2D=12
GRAPH_3D=13

# lists
L_DATAS=(EXP_DATA,CALC_DATA)
L_GRAPHS=(GRAPH_1D,GRAPH_2D,GRAPH_3D)
L_CALCS=(CALC_1D, CALC_2D, CALC_3D)
L_EXPS=(EXP_FID,EXP_SER,EXP_SER3D, EXP_1D,EXP_2D,EXP_3D)
L_1DS=(EXP_FID,EXP_1D,CALC_1D,GRAPH_1D)
L_2DS=(EXP_SER,EXP_2D,CALC_2D,GRAPH_2D)
L_3DS=(EXP_SER3D,EXP_3D,CALC_3D,GRAPH_3D)
L_FIDS=(EXP_FID,EXP_SER,EXP_SER3D)
L_SPECS=(CALC_1D,CALC_2D,CALC_3D,EXP_1D,EXP_2D,EXP_3D)

#kinds of dimensions
DIM_TIME = 100
DIM_FREQ = 200

#log levels
ERRORLEVEL=NOLOGLEVEL=1
WARNINGLEVEL=2
MESSAGELEVEL=3
STATUSLEVEL=INFOLEVEL=4
VERBOSELEVEL=5
DEBUGLEVEL=6
LEVELS = {"1":"Error",
           "2":"Warning",
           "3":"Message",
           "4":"Status",
           "5":"Verbose",
           "6":"Debug"}

# Constant and units
#-------------------
#logicals
TRUE = true = YES = Yes = yes = Y = y = True
FALSE = false = NO = No = no = N = n = False

#units
HZ = Hz = hz = 1.0
KHZ = kHz = khz = 1.0e3
MHZ = MHz = mhz = 1.0e6
USEC = usec = 1.0
MSEC = msec = 1.0e3
SEC = sec = 1.0e6
TESLA = Tesla = tesla = 1
ANGSTROM = ANGS = angs = angstrom = 1
NM = nm = 10   #nanometer (relative to angstrom)
K = k = 1024   #kpoint
PPM = None

#miscellaneous
MAS = mas = 54.735610
STATIC = static = 0
from math import pi
GAMMA_H = gamma_H = 26.7510e7/(2.0*pi)
AUTO = auto = -999
FULL = full = -998
ALL = all = 0
CENTRAL = Central = central = 1
SATELLITE = Satellite = satellite = 2

CFG={
'Mode':'Standard',
'Show_X_Axis':True,
'X_Axis_Units':'Hz',
'Show_Y_Axis':False,
'Y_Axis_Units':'Intensity',
'Show_X_Label':True,
'X_Axis_label':'',
'Show_Y_Label':True,
'Y_Axis_label':'',
'Show_Title':True,
'Title':'',
'Show_Grid':False,
'Show_Calculated':True,
'Show_Difference':True,
'Show_Baseline': True,
'Show_Legend': True,
'Sum_Components':True,
'Show_Components':True,
'Selected_Components':['All'],
'X_Offset':0.,
'Y_Offset':10.,
}

linecolor=['g','c','m','y']
linestyle=['--',':','-.']

fitcommands= \
"""
##****************************************************************************
## OPTIMIZATION COMMANDS
##****************************************************************************
## Syntax:
## FitParameter["<name>"] = <value>{, <lower_bound>}{, <upper_bound>}{, FIXED}
## Note that values between {} are optionals
##****************************************************************************

FitParameter['conc1'] = 1., FIXED
FitParameter['conc2'] = 0.296272971734, 0.0, 1.0
FitParameter['conc3'] = 0.661335491612, 0.0, 1.0
FitParameter['lb1'] = 0.1, 0.0, 2000.0, FIXED
FitParameter['lb2'] = 0.1, 0.0, 2000.0, FIXED
FitParameter['lb3'] = 0.1, 0.0, 2000.0, FIXED
FitParameter['gb1'] = 450.069747961, 0.0, 2000.0
FitParameter['gb2'] = 1404.55008506, 0.0, 2000.0
FitParameter['gb3'] = 854.162310001, 0.0, 2000.0
FitParameter['iso1'] = 17190.2235925, 17000.0, 17300.0
FitParameter['iso2'] = 4443.26604439, 4300.0, 4600.0
FitParameter['iso3'] = 1417.94940305, 1300.0, 1500.0
FitParameter['phc0'] = -0.855347567484
FitParameter['phc1'] = 20.1917620791

## Other fit parameters (important: must appears before Fit sequence!)
##
FIT_INTENSITY = False
FIT_BASELINE = True
BASELINE_ORDER = 0

## Fit sequence
## ***************************************************************************
## syntax: (use regular expressions)
##
## FitStep[1]='name1','name2'  --> fit only two parameters: 'name1' and 'name2'
## we can also use 'name1|name2'
## FitStep[2]='.*1'--> fit only parameters whose name ends with '1'
## FitStep[3]='c.*'--> fit only parameters whose name starts with'c'
## FitStep[4]='[^ph].*1'--> fit only parameters whose name ends with '1'
##                          and do not start with 'ph'
## FitStep[5]=ALL_PARAMETERS or ='.*' --> Fit all parameters
## Note: if the  FIXED keyword is used in FitParameter definition,
## it will always remain fixed whatever the FitStep declaration

FitStep[1]='conc2','conc3'
FitStep[2]='phc1','phc0'
FitStep[3]='[^phc1].*1'
FitStep[4]='.*2'
FitStep[5]='.*3'
FitStep[5]='gb.*','conc.*[^1]','iso.*'
FitStep[6]='.*' #ALL_PARAMETERS

## Method of optimization
## **************************************************************************
## methods can be :
##  - SIMPLEX: Simplex algorithm of Nelder and Mead
##  - BFGS: Quasi-Newton method of Broyden, Fletcher, Goldfarb and Shanno
##  - CG: Nonlinear conjugate gradient algorithm of Polak and Ribiere
METHOD = BFGS
TOLERANCE=1.e-4
MAX_ITERATIONS=5000

## error function to minimize
## **************************************************************************
def ERRFUNC(experiment,calculated):
    chi2 = sqrt(sum((experiment-calculated)**2)/size(experiment))
    chi2 = chi2*100./max(experiment)
    return chi2
"""

SIMPLEX = 10001
BFGS = 10002
CG = 10003

ALL_PARAMETERS = '.*'
