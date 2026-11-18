#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#-------------------------------------------------------------------------------
"""
FILE INFO:
==========
 - $Name   :      experimental.py
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

 View and actions on experimental spectra

"""
#-------------------------------------------------------------------------------

__docformat__="epytext"

from definitions import *
import common as cm
from plot import Plot
from numpy import array, fliplr, flipud
from scipy.io.fopen import fopen #FIXME: deprecation warning : use npfile
import os
import re
import string

#===============================================================================
class Experimental:
#===============================================================================
    """
    Class Experimental spectra
    """
#-------------------------------------------------------------------------------
    def __init__(self):
#-------------------------------------------------------------------------------
        """
        Initialisation function
        """
        self.data={}
        self.par=None

#-------------------------------------------------------------------------------
    def Load(self, filename=None, origin="BRUKER"):
#-------------------------------------------------------------------------------
        """
        Generic Function Load
        Open experimental file in buffer.
        """
        if filename is None: return False
        LoadMethod = getattr(self, "Load%s" % origin)
        LoadMethod(filename)
        return self.data

#-------------------------------------------------------------------------------
    def LoadBRUKER(self, filename=None):
#-------------------------------------------------------------------------------
        """
        Open experimental BRUKER file.
        """

        if not filename: return False

        DEBUG("Loading bruker file...."+str(filename))

        if not os.path.exists(filename):
            return False

        [filepath, filebase, _fileext]=cm.GetPath(filename)
        if filebase=="fid":
            #we are loading a FID
            [path, expno, procno]=self.GetBRUKERPath(filepath, filetype="acqu")
            if not self.LoadBRUKERpar(path, expno, procno, kind=EXP_FID):
                return False
            if not self.LoadBRUKERfile(path, expno, procno, kind=EXP_FID):
                return False

        elif filebase=="1r" or filebase=="1i":
            #we have to loading a 1D file
            [path, expno, procno]=self.GetBRUKERPath(filepath, filetype="proc")
            if not self.LoadBRUKERpar(path, expno, procno, kind=EXP_1D):
                return False
            if not self.LoadBRUKERfile(path, expno, procno, kind=EXP_1D):
                return False

        if filebase=="ser":
            #we are loading a SER 2D file
            [path, expno, procno]=self.GetBRUKERPath(filepath, filetype="acqu")
            if not self.LoadBRUKERpar(path, expno, procno, kind=EXP_SER):
                return False
            if not self.LoadBRUKERfile(path, expno, procno, kind=EXP_SER):
                return False

        elif filebase=="2rr" or filebase=="2ri" or filebase=="2ir" \
                                                            or filebase=="2ii" :
            #we have to loading a 2D file
            [path, expno, procno]=self.GetBRUKERPath(filepath, filetype="proc")
            if not self.LoadBRUKERpar(path, expno, procno, kind=EXP_2D):
                return False
            if not self.LoadBRUKERfile(path, expno, procno, kind=EXP_2D):
                return False

        return True

#-------------------------------------------------------------------------------
    def GetBRUKERPath(self, filepath=None, filetype="proc"):
#-------------------------------------------------------------------------------
        """
        Open experimental BRUKER parameter files.
        """
        if filetype=="acqu":
            #determine only the expno (procno=1 by default)
            [path, expno, _nothing]=cm.GetPath(filepath)
            procno="1"
        else:
            #determine expno and procno
            [datapath, procno, _nothing]=cm.GetPath(filepath)
            [exppath, _datadir, _nothing]=cm.GetPath(datapath)
            [path, expno, _nothing]=cm.GetPath(exppath)
        return [path, expno, procno]

#-------------------------------------------------------------------------------
    def LoadBRUKERpar(self, path, expno, procno, kind=EXP_1D):
#-------------------------------------------------------------------------------
        """
        Open experimental BRUKER parameter files.
        and display it in the parameter notebook tab.
        """
##        try:

        #Open the acqu
        acqufile = open(os.path.join(path, expno, "acqus"), "rb")
        procfile = open(os.path.join(path, expno, "pdata", procno,
                                                             "procs"), "rb")
        acqu = self.readBRUKERJCAMPDXfile(acqufile)
        proc = self.readBRUKERJCAMPDXfile(procfile)

        if kind==EXP_2D:
            acqu2file = open(os.path.join(path, expno, "acqu2s"), "rb")
            proc2file = open(os.path.join(path, expno, "pdata", procno,
                                                            "proc2s"), "rb")
            acqu2 = self.readBRUKERJCAMPDXfile(acqu2file)
            proc2 = self.readBRUKERJCAMPDXfile(proc2file)

        #Create a script (that can be used by the Pulsar process)
        text='#ACQUS and PROCS parameters\n'
        for k, v in self.sortedDict(acqu, proc):
            text+=k+" = "+str(v)+"\n"

        if kind==EXP_2D:
            text+='\n\n#ACQUS and PROCS parameters for F1 dimension\n'
            for k, v in self.sortedDict(acqu2, proc2):
                text+=k+"_1 = "+str(v)+"\n"

        self.par=text
        self.data["parameters"]=self.par

        return True

##        except:
##            self.par=None
##            return False

#-------------------------------------------------------------------------------
    def LoadBRUKERfile(self, path, expno, procno, kind=EXP_1D):
#-------------------------------------------------------------------------------
        """
        Open experimental BRUKER spec or fid file.
        and display it in the parameter plot tab.
        """

        #interpret parameters by executing the par file
        if self.par is None: return
        code=compile(self.par, '<script>', 'exec')
        #-----------------------------------------
        BYTORDA =  0
        BYTORDP =  0
        NC_proc =  0
        NS =  0
        NUC1 = 'off'
        NUCLEUS = 'off'
        SF =  0.0
        SFO1 =  0
        SI =  0
        SW_h =  0.0
        TD =  0
        XDIM =  0
        SF_1 =  0.0
        SFO1_1 =  0.0
        SI_1 =  0
        SW_h_1 =  0.0
        TD_1 =  0
        XDIM_1 =  0

        exec(code)

        #get necessary parameters for dimension F2
        self.xdim2 = xdim2 = XDIM
        self.td2 = td2 = TD
        self.si2 = si2 = SI
        self.sw2 = sw2 = SW_h
        self.sf2 = sf2 = SF
        self.sfo12 = sfo12 = SFO1
        self.sr2 = sr2 = (sf2-sfo12)*10**6

        if kind==EXP_SER or kind==EXP_2D:
            #get necessary parameters for dimension F1
            self.xdim1 = xdim1 = XDIM_1
            self.td1 = td1 = TD_1
            self.si1 = si1 = SI_1
            self.sw1 = sw1 = SW_h_1
            self.sf1 = sf1 = SF_1
            self.sfo11 = sfo11 = SFO1_1
            self.sr1 = sr1 = (sf1-sfo11)*10**6
        else:
            #set default values
            self.xdim1 = xdim1 = 1
            self.td1 = td1 = 1
            self.si1 = si1 = 1
            self.sw1 = sw1 = 0.0
            self.sf1 = sf1 = 0.0
            self.sfo11 = sfo11 = 0.0
            self.sr1 = sr1 = 0.0

        #Get the nuclei
        nucleus = NUCLEUS
        if nucleus == "off":
            nucleus = NUC1

        #Scale factor depending on the number of scans and nc_proc
        mult=1. # 2.**NC_proc / NS

        # open file
        if kind==EXP_FID:
            fid = fopen(os.path.join(path, expno, "fid"), permission='r',
                                                 format=self.setEndian(BYTORDA))
            self.td1=td1=1

        elif kind==EXP_1D:
            f1r = fopen(os.path.join(path, expno, "pdata", procno, "1r"),
                                 permission='r', format=self.setEndian(BYTORDP))
            f1i = fopen(os.path.join(path, expno, "pdata", procno, "1i"),
                                 permission='r', format=self.setEndian(BYTORDP))
            self.si1 = si1 = 1

        if kind==EXP_SER:
            fid = fopen(os.path.join(path, expno, "ser"), permission='r',
                                                 format=self.setEndian(BYTORDA))
            self.td1 = td1 = TD_1
            if fid.size()/float(td2*4)<td1:
                                   self.td1 = td1 = int(fid.size()/float(td2*4))

        elif kind==EXP_2D:
            f2rr = fopen(os.path.join(path, expno, "pdata", procno, "2rr"),
                                 permission='r', format=self.setEndian(BYTORDP))
            f2ri = fopen(os.path.join(path, expno, "pdata", procno, "2ri"),
                                 permission='r', format=self.setEndian(BYTORDP))
            f2ir = fopen(os.path.join(path, expno, "pdata", procno, "2ir"),
                                 permission='r', format=self.setEndian(BYTORDP))
            f2ii = fopen(os.path.join(path, expno, "pdata", procno, "2ii"),
                                 permission='r', format=self.setEndian(BYTORDP))
            self.si1 = si1 = SI_1
            self.xdim1 = xdim1 = XDIM_1

        if kind==EXP_FID:
            Z=[]
            re = map(float, fid.fread(td2, 'l'))
            for i in range(td2/2):
                Z.append(complex(re[i]*mult, re[i+1]*mult))
            n2=td2/2
            n1=1

        if kind==EXP_SER:
            Z=[[] for i in range(td1)]
            for j in range(td1):
                re = map(float, fid.fread(td2, 'l'))
                for i in range(td2/2):
                    Z[j].append(complex(re[i]*mult, re[i+1]*mult))
            n2=td2/2
            n1=td1

        if kind==EXP_1D:
            Z=[]
            f1=si1/xdim1
            f2=si2/xdim2
            re = map(float, f1r.fread(si2, 'l'))
            im = map(float, f1i.fread(si2, 'l'))
            for i in range(si2):
                Z.append(complex(re[i]*mult, im[i]*mult))
            Z = array(Z[::-1])  #reverse      #TODO: Rewrite everything using numpy array, should be better
            n2=si2
            n1=1

        if kind==EXP_2D:
            Z=[[] for i in range(si1)]
            f1=si1/xdim1
            f2=si2/xdim2
            for o in range(f1):
                for _p in range(f2):
                    for j in range(xdim1):
                        rr = map(float, f2rr.fread(xdim2, 'l'))
                        ri = map(float, f2ri.fread(xdim2, 'l'))
                        _ir = map(float, f2ir.fread(xdim2, 'l'))
                        _ii = map(float, f2ii.fread(xdim2, 'l'))
                        for i in range(xdim2):
                            Z[j+o*xdim1].append(complex(rr[i]*mult, ri[i]*mult))
                                                          #TODO: check ri or ir?
            Z=fliplr(flipud(Z)) #reversed
            n2=si2
            n1=si1

        # Prepare CFG (configuration of plot)
        #-------------------------------------
        cfg=CFG
        cfg['kind'] = kind
        if kind in [EXP_FID,EXP_SER]:
            cfg['dim_2'] = DIM_TIME
            cfg['dim_1'] = None
            if kind == EXP_SER:
                cfg['dim_1'] = DIM_TIME
        else:
            cfg['dim_2'] = DIM_FREQ
            cfg['dim_1'] = None
            if kind == EXP_2D:
                cfg['dim_1'] = DIM_FREQ

        cfg['dim_0'] = None

        # Prepare the data header
        #------------------------
        data={}
        header=[]

        header.append((cfg))            #CFG
        header.append((sfo12*1.0e6, sfo11*1.0e6, None))
        header.append((sw2, sw1, None))
        header.append((sr2, sr1, None))
        header.append((td2, td1, 1))
        header.append((si2, si1, 1))
        header.append((0., 0., 1.0))    #lb, gb, conc
        header.append(("", ""))         #Label, Variable

        # We will need later to store Z as a string,
        # but array can not be transformed in string (!?)
        # we need to change them to list
        spec=Z.tolist()
        self.data["spectra"] = [[header, spec]]
        self.data["kind"] = kind

        return True

#-------------------------------------------------------------------------------
    def setEndian(self, bytord):
#-------------------------------------------------------------------------------
        """
        Select little or big-endian according BYTORD parameters

        XWIN-NMR runs on computers with different byte order,
        for example SGI workstations are big endian
        and Intel PCs are little endian.
        @param bytord: Byte order value read from acqu or proc file
        """
        if bytord==0:return 'l'
        else: return 'b'

#-------------------------------------------------------------------------------
    def sortedDict(self, adict, bdict=None):
#-------------------------------------------------------------------------------
        """
        A function to sort a dictionary
        """
        if bdict:
            for k, v in bdict.iteritems():
                adict[k]=v
        keys = adict.keys()
        keys.sort()
        return [(key, adict[key]) for key in keys]

#-------------------------------------------------------------------------------
    def readBRUKERJCAMPDXfile(self, file=None):
#-------------------------------------------------------------------------------
        """
        read a bruker JCAMP-DX parameter file
        """
        #read the compplete file
        try:
            lines=file.readlines()
            nlines=len(lines)
        except:
            return False

        #create a new dictionary
        par={}
        #comment={}
        #regular expression searches
        #TODO: Can be probably written more efficiently
        pegal=re.compile(r"=")
        pdollar=re.compile(r"\$")
        pdot=re.compile(r"(\(\d+\.\.\d+\))(.*)")
        pnum=re.compile('\d+')
        pst=re.compile(r"^<(.*)>$")
        i=0
        while i<nlines:
            #only look for ##$ or ## parameters
            line=cm.rtn(lines[i])
            if pegal.search(line):
                #this is a parameter : split the key and values
                [k, v]=cm.rtn(lines[i]).split('=')
                m=pdollar.search(k)
                if m:
                    key=k[3:]  # key is in the form ##$xx
                else:
                    # or ##xx  (this is a comment)
                    i+=1
                    continue

                if self.isExcluded(key):
                    #go to next line
                    i+=1
                    continue

                #detect strings <>
                st=pst.search(v.strip())
                if st:
                    v="'"+st.group(1)+"'"
                #read the arrays
                pd = pdot.search(v)
                if pd:
                    # we must read the array of numbers in the rest of the line
                    # or the next line
                    limit=pnum.findall(pd.group(1))
                    # read the rest of the line
                    v=[]
                    if pd.group(2) :
                        vadd=map(float, pnum.findall(pd.group(2)))
                        for l in vadd:
                            v.append(l)
                    while len(v)<int(limit[1])+1:
                        #there is a second line
                        #merge the rest of the list
                        i+=1
                        vadd=map(float, pnum.findall(lines[i]))
                        for l in vadd:
                            v.append(l)

                #Detect boolean (no and yes)
                if isinstance(v, str):
                    if string.find(v, 'no')!=-1:v = False
                    elif string.find(v, 'yes')!=-1:v = True

                par[key]=v

            i+=1
        return par

#-------------------------------------------------------------------------------
    def isExcluded(self, key):
#-------------------------------------------------------------------------------
        """
        Define a list of keys that are not necessary for the BRUKER spectra
        and check if the key passed in parameter is in this list
         - TODO: Make this list selectable by the user
        @param key: key to be checked
        """
        excludedKey=[
            "AMP",
            "AUNM",
            "AUTOPOS",
            "BF3",
            "BF4",
            "BF5",
            "BF6",
            "BF7",
            "BF8",
            "CFDGTYP",
            "CFRGTYP",
            "CHEMSTR",
            "CPDPRG",
            "CPDPRG1",
            "CPDPRG2",
            "CPDPRG3",
            "CPDPRG4",
            "CPDPRG5",
            "CPDPRG6",
            "CPDPRG7",
            "CPDPRG8",
            "CPDPRGB",
            "CPDPRGT",
            "DATE",
            "DBL",
            "DBP",
            "DBP07",
            "DBPNAM0",
            "DBPNAM1",
            "DBPNAM2",
            "DBPNAM3",
            "DBPNAM4",
            "DBPNAM5",
            "DBPNAM6",
            "DBPNAM7",
            "DBPOAL",
            "DBPOFFS",
            "DECBNUC",
            "DECNUC",
            "DECSTAT",
            "DL",
            "DP",
            "DP07",
            "DPNAME0",
            "DPNAME1",
            "DPNAME2",
            "DPNAME3",
            "DPNAME4",
            "DPNAME5",
            "DPNAME6",
            "DPNAME7",
            "DPOAL",
            "DPOFFS",
            "DQDMODE",
            "DR",
            "DS",
            "DSLIST",
            "DSPFIRM",
            "DSPFVS",
            "DTYPA",
            "EXP",
            "F1LIST",
            "F2LIST",
            "F3LIST",
            "FCUCHAN",
            "FL1",
            "FL2",
            "FL3",
            "FL4",
            "FOV",
            "FQ3LIST",
            "FQ4LIST",
            "FQ5LIST",
            "FQ6LIST",
            "FQ7LIST",
            "FQ8LIST",
            "FS",
            "FTLPGN",
            "FnMODE",
            "GP031",
            "GPNAM0",
            "GPNAM1",
            "GPNAM10",
            "GPNAM11",
            "GPNAM12",
            "GPNAM13",
            "GPNAM14",
            "GPNAM15",
            "GPNAM16",
            "GPNAM17",
            "GPNAM18",
            "GPNAM19",
            "GPNAM2",
            "GPNAM20",
            "GPNAM21",
            "GPNAM22",
            "GPNAM23",
            "GPNAM24",
            "GPNAM25",
            "GPNAM26",
            "GPNAM27",
            "GPNAM28",
            "GPNAM29",
            "GPNAM3",
            "GPNAM30",
            "GPNAM31",
            "GPNAM4",
            "GPNAM5",
            "GPNAM6",
            "GPNAM7",
            "GPNAM8",
            "GPNAM9",
            "GPX",
            "GPY",
            "GPZ",
            "GRDPROG",
            "HDDUTY",
            "HDRATE",
            "HGAIN",
            "HL1",
            "HL2",
            "HL3",
            "HL4",
            "HOLDER",
            "HPMOD",
            "HPPRGN",
            "INSTRUM",
            "L",
            "LFILTER",
            "LGAIN",
            "LOCKED",
            "LOCKFLD",
            "LOCKGN",
            "LOCKPOW",
            "LOCKPPM",
            "LOCNUC",
            "LOCPHAS",
            "LOCSHFT",
            "LTIME",
            "MASRLST",
            "NBL",
            "NC",
            "NUC3",
            "NUC4",
            "NUC5",
            "NUC6",
            "NUC7",
            "NUC8",
            "O3",
            "O4",
            "O5",
            "O6",
            "O7",
            "O8",
            "OBSCHAN",
            "OVERFLW",
            "PAPS",
            "PCPD",
            "PHCOR",
            "PHP",
            "PH_ref",
            "POWMOD",
            "PR",
            "PRECHAN",
            "PRGAIN",
            "PROBHD",
            "PROSOL",
            "PW",
            "QNP",
            "RD",
            "RECCHAN",
            "RECPH",
            "RG",
            "ROUTWD1",
            "ROUTWD2",
            "RPUUSED",
            "RSEL",
            "S",
            "SEOUT",
            "SFO3",
            "SFO4",
            "SFO5",
            "SFO6",
            "SFO7",
            "SFO8",
            "SOLVENT",
            "SP",
            "SP07",
            "SPECTR",
            "SPNAM0",
            "SPNAM1",
            "SPNAM10",
            "SPNAM11",
            "SPNAM12",
            "SPNAM13",
            "SPNAM14",
            "SPNAM15",
            "SPNAM16",
            "SPNAM17",
            "SPNAM18",
            "SPNAM19",
            "SPNAM2",
            "SPNAM20",
            "SPNAM21",
            "SPNAM22",
            "SPNAM23",
            "SPNAM24",
            "SPNAM25",
            "SPNAM26",
            "SPNAM27",
            "SPNAM28",
            "SPNAM29",
            "SPNAM3",
            "SPNAM30",
            "SPNAM31",
            "SPNAM4",
            "SPNAM5",
            "SPNAM6",
            "SPNAM7",
            "SPNAM8",
            "SPNAM9",
            "SPOAL",
            "SPOFFS",
            "SUBNAM0",
            "SUBNAM1",
            "SUBNAM2",
            "SUBNAM3",
            "SUBNAM4",
            "SUBNAM5",
            "SUBNAM6",
            "SUBNAM7",
            "SUBNAM8",
            "SUBNAM9",
            "SWIBOX",
            "TD0",
            "TE",
            "TE2",
            "TE3",
            "TEG",
            "TL",
            "TP",
            "TP07",
            "TPNAME0",
            "TPNAME1",
            "TPNAME2",
            "TPNAME3",
            "TPNAME4",
            "TPNAME5",
            "TPNAME6",
            "TPNAME7",
            "TPOAL",
            "TPOFFS",
            "TUNHIN",
            "TUNHOUT",
            "TUNXOUT",
            "USERA1",
            "USERA2",
            "USERA3",
            "USERA4",
            "USERA5",
            "V9",
            "VALIST",
            "VCLIST",
            "VD",
            "VDLIST",
            "VPLIST",
            "VTLIST",
            "WBST",
            "WBSW",
            "XGAIN",
            "XL",
            "YL",
            "YMAX_a",
            "YMIN_a",
            "ZGOPTNS",
            "ZL1",
            "ZL2",
            "ZL3",
            "ZL4",
            #PROCS parameters
            "ABSF1",
            "ABSF2",
            "ABSG",
            "ABSL",
            "ALPHA",
            "AQORDER",
            "ASSFAC",
            "ASSFACI",
            "ASSFACX",
            "ASSWID",
            "AUNMP",
            "AZFE",
            "AZFW",
            "BCFW",
            "BC_mod",
            "COROFFS",
            "CY",
            "DATMOD",
            "DC",
            "DFILT",
            "DTYPP",
            "FCOR",
            "FTSIZE",
            "FT_mod",
            "GAMMA",
            "INTBC",
            "INTSCL",
            "ISEN",
            "LEV0",
            "LPBIN",
            "MAXI",
            "MC2",
            "MEAN",
            "ME_mod",
            "MI",
            "NCOEF",
            "NLEV",
            "NOISF1",
            "NOISF2",
            "NSP",
            "NTH_PI",
            "NZP",
            "OFFSET",
            "PC",
            "PKNL",
            "PPARMOD",
            "PSCAL",
            "PSIGN",
            "RO",
            "SIGF1",
            "SIGF2",
            "SINO",
            "SIOLD",
            "SREGLST",
            "SSB",
            "SYMM",
            "S_DEV",
            "TI",
            "TILT",
            "TM1",
            "TM2",
            "TOPLEV",
            "USERP1",
            "USERP2",
            "USERP3",
            "USERP4",
            "USERP5",
            "WDW",
            "AQSEQ",
            "AQ_mod",
            "BYTORDA",
            "BYTORDP",
            "CNST",
            "DE",
            "DECIM",
            "DIGMOD",
            "DIGTYP",
            "F1P",
            "F2P",
            "FQ1LIST",
            "FQ2LIST",
            "FW",
            "GB",
            "IN",
            "INP",
            "LB",
            "NTH_PF",
            "NUCLEI",
            "NUCLEUS",
            "PHC0",
            "PHC1",
            "PH_mod",
            "QS",
            "QSB",
            "REVERSE",
            "SW_p",
            "T1D",
            "TDeff",
            "TDoff",
            "WS",
            "YMAX_p",
            "YMIN_p",
            ]
        if key in excludedKey: return True

#-------------------------------------------------------------------------------
def readExperimental(fullpath, origin="BRUKER"):
#-------------------------------------------------------------------------------
    """
    Read experimental data main function
    e.g. called by wizdataset
    """
    c=Experimental()
    data = c.Load(fullpath, origin)
    return data

###===============================================================================
### TEST
###===============================================================================
##
###------------------------------------------------
##def makePlot(plot, spc, title="Untitled"):
##    """
##    Make the plot
##    @param spc: Format of spc=(kind,header,Z)
##    """
##    #set some parameters
##    plot.flag_sum=False
##    plot.flag_sum_only=False
##    plot.specshowed=[0]
##    plot.title=title
##
##    #do the plot
##    header=spc[0]
##
##    #header=[sfo12*1.0e6,sfo11*1.0e6,sw2,sw1,sr2,sr1,td2,td1,si2,si1]
##    plot.vl2=header[0]
##    plot.vl1=header[1]
##    plot.sw2=header[2]
##    plot.sw1=header[3]
##    plot.sr2=header[4]
##    plot.sr1=header[5]
##    plot.td2=header[6]
##    plot.td1=header[7]
##    plot.si2=header[8]
##    plot.si1=header[9]
##    plot.kind=header[10]
##    #nb of points
##    if plot.kind==EXP_FID or plot.kind==EXP_SER:
##        plot.n2=plot.td2/2
##        plot.n1=plot.td1
##    if plot.kind==EXP_1D or plot.kind==EXP_2D:
##        plot.n2=plot.si2
##        plot.n1=plot.si1
##    plot.spec=spc[1]
##    plot.mode="Standard"
##    plot.ydata = []
##    plot.plot_data()
##    plot.Layout()
##
###-------------
##def runTest():
###-------------
##    import parentframe
##
##
##    parent=parentframe.ParentFrame(None, title="plot")
##    win = Plot(parent,"")
##    parent.Show()
##
##    exp=Experimental()
##    data=exp.Load("D:/EclipseWorkspaces/archives/bruker_spectres/RbNO3/10/pdata/1/1r")
###    dataencoded=repr(data)
###    spc=None
###    code=compile("spc="+dataencoded, '<script>', 'exec')
###    exec(code)
##    dataencoded=repr(data["spectrum"])
##    spc=None
##    code=compile("spc="+dataencoded, '<script>', 'exec')
###    exec(code)
###    code=compile("spc="+spc, '<script>', 'exec')
##    exec(code)
##
###   makePlot(win, data["spectrum"], data["parameters"],data["kind"])
##    makePlot(win, spc)
##
##    return win
##
##if __name__ == '__main__':
##    import sys, os
##    import run
##    run.main([os.path.basename(sys.argv[0])])



