import wx
import wx.lib.pubsub as pubsub
from UserDict import UserDict
from definitions import *
import common as cm
import string
from processing import *
from numpy import array, zeros
import psyco

#===============================================================================
class Spectres(UserDict, object):
#===============================================================================
    count = 0
#-------------------------------------------------------------------------------
    def __init__(self, parent):
#-------------------------------------------------------------------------------
        UserDict.__init__(self)
        object.__init__(self)
        self.parent = parent
        self.Maxi = self.Mini = 0.0
        self.__config = CFG
        self.Shape = 1
        self.count = 0
        self.__adding = True
        self.__class__.count += 1

    def __del__(self):
        self.data = {}

#-------------------------------------------------------------------------------
    def iteritems(self):
#-------------------------------------------------------------------------------
        return self.data.iteritems()

#-------------------------------------------------------------------------------
    def __setitem__(self, key, item):
#-------------------------------------------------------------------------------
        """override the setitem method"""
        self.__adding = True
        self.data[key] = item
        self.count += 1
        # set some attributes
        item["color"] = linecolor[(self.count-1)%4]
        item["style"] = linestyle[(self.count-1)%3]

        if self.count == 1:
            self.Shape = item.Shape
            self.Config = item.Config
        else:
            # Update Config versus the config of the first spectra
            if self.Shape != item.Shape:
                raise ValueError(self.Shape)
            item.Config = self.Config

        self.Maxi = max(self.Maxi, item.findMaximum())
        self.Mini = min(self.Mini, item.findMinimum())

        # When a new spectrum is added we should redraw the corresponding plot
        pubsub.Publisher().sendMessage("SPECTRE ADDED", self.parent)
        self.__adding = False

#-------------------------------------------------------------------------------
    def __delitem__(self, key):
#-------------------------------------------------------------------------------
        """override the delitem method"""
        # When a new spectrum is deleted we should redraw the corresponding plot
        pubsub.Publisher().sendMessage("SPECTRE DELETED", self.parent)

        # remove the 'spectre' from the collection
        del self.data[key]

        # remove the reference to the 'spectre' instance
        del key
        self.count -= 1

#-------------------------------------------------------------------------------
# Properties
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
    def _getX(self):
#-------------------------------------------------------------------------------
        item = self.data.values()[0]
        return item.getXScale()

#-------------------------------------------------------------------------------
    def _getY(self):
#-------------------------------------------------------------------------------
        item = self.data.values()[0]
        return item.getYScale()

#-------------------------------------------------------------------------------
    def _getZ(self):
#-------------------------------------------------------------------------------
        item = self.data.values()[0]
        return item.getZScale()

#-------------------------------------------------------------------------------
    def _getSum(self):
#-------------------------------------------------------------------------------
        item = self.data.values()[0]
        sumspec = zeros((item.getNpts(dim=2))) #TODO: Check for 2D
        for spectre in self.data.values():
            spec = array(spectre["spec"])

            if spectre.has_key("kind") and spectre["kind"] in L_CALCS:
                sumspec += spec
        return sumspec

#-------------------------------------------------------------------------------
    def _getDiff(self):
#-------------------------------------------------------------------------------
        item = self.data.values()[0]
        calculation = zeros((item.getNpts(dim=2))) #TODO: Check for 2D
        for spectre in self.data.values():
            spec = array(spectre["spec"])
            if spectre.has_key("kind") and spectre["kind"] in L_CALCS:
                calculation += spec.real
            elif spectre.has_key("kind") and spectre["kind"] in L_EXPS:
                experiment = spec # -(spec[0]+spec[-1])/2.
                experiment = experiment.real

        # in this case, we will fit the intensity and the baseline
        intensity, baseline = fitBaseline(calculation, experiment,order=1)

        calculation = intensity*calculation + baseline

        diffspec = experiment - calculation
        return (diffspec, calculation, baseline, intensity)

    X = property(fget = _getX)
    Y = property(fget = _getY)
    Z = property(fget = _getZ)
    SumSpec = property(fget = _getSum)
    DiffSpec = property(fget = _getDiff)

#-------------------------------------------------------------------------------
    def _getConfig(self):
#-------------------------------------------------------------------------------
        return self.__config

#-------------------------------------------------------------------------------
    def _setConfig(self, config):
#-------------------------------------------------------------------------------
        if self.__config != config:
            self.__config = config
            for item in self.data.values():
                item.Config = self.__config

            if not self.__adding:
                pubsub.Publisher().sendMessage("CONFIG MODIFIED",self.parent)

    Config = property(fget = _getConfig, fset = _setConfig)

#===============================================================================
class Spectre(UserDict, object):
#===============================================================================

    #count = 0  # will help to count the number of spectrum to handle in each plot

#-------------------------------------------------------------------------------
    def __init__(self, data):
#-------------------------------------------------------------------------------
        UserDict.__init__(self)
        object.__init__(self)
        __metaclass__ = psyco.compacttype
        # Extract header and spec from the data, format [header,spec]
        #-------------------------------------------------------------
        self.__header = self.__saveheader = data[0]
        self.__spec = self.__savespec = array(data[1],"Complex64")

        # Extract all parameters
        #------------------------
        self.__config = self.__header[0]
        self.__dim2 = self.__config['dim_2']
        self.__dim1 = self.__config['dim_1']
        self.__dim0 = self.__config['dim_0']

        self.__vl2, self.__vl1, self.__vl0 = self.__header[1]
        self.__sw2, self.__sw1, self.__sw0 = self.__header[2]
        self.__sr2, self.__sr1, self.__sr0 = self.__header[3]
        self.__td2, self.__td1, self.__td0 = self.__header[4]
        self.__si2, self.__si1, self.__si0 = self.__header[5]
        self.__lb , self.__gb, self.__concentration = self.__header[6]
        self.__label, self.__variable = self.__header[7]

        # Initialisation
        #----------------
        self.__n2 = self.__si2
        self.__n1 = self.__si1
        self.__n0 = self.__si0
        if self.__dim2 == DIM_TIME:
            self.__n2 = self.__td2
        if self.__dim1 == DIM_TIME:
            self.__n1 = self.__td1
        if self.__dim0 == DIM_TIME:
            self.__n0=self.__td0

        if self.__n1 < 2 : self.__shape = 1
        elif self.__n0 < 2 : self.__shape = 2
        else: self.__shape = 3


        # correct the concentration
        # and perform the initial broadening
        #--------------------------
        s =  self.addBroadening(self.__savespec,
                                                  lb = self.__lb, gb =self.__gb)

        for i in range(self.__n2):
            self.__spec[i] = s[i] * self.__concentration

        # add the key "spec" and "kind"
        #-------------------------------
        self["spec"] = self.__spec
        self["kind"] = self.__config['kind']

        label = str(self.__label) + " " + str(self.__variable)

        self["label"] = label

#-------------------------------------------------------------------------------
    def __del__(self):
#-------------------------------------------------------------------------------
        self.data={}
        self.__spec = self.__savespec = None
        self.__header = self.__saveheader = None

#-------------------------------------------------------------------------------
# Properties
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
    def _getShape(self):
#-------------------------------------------------------------------------------
        return self.__shape

#-------------------------------------------------------------------------------
    def _getConfig(self):
#-------------------------------------------------------------------------------
        return self.__config

#-------------------------------------------------------------------------------
    def _setConfig(self, config):
#-------------------------------------------------------------------------------
        self.__config = config

    Config = property(fget = _getConfig, fset = _setConfig)
    Shape = property(fget = _getShape)

#-------------------------------------------------------------------------------
# Methods
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
    def setNpts(self,npts,dim=2):
#-------------------------------------------------------------------------------
        if dim == 2:
            self.__n2 = npts
        elif self.__shape == 2 and dim == 1:
            self.__n1 = npts
        elif self.__shape == 3 and dim == 0:
            self.__n0 = npts
        else:
            cm.LOG_ERROR("incoherent values - npts:",npts,
                                            " dim:", dim, " kind:", self.__shape)

            raise ValueError

        #TODO: Ajust sw accordingly

#-------------------------------------------------------------------------------
    def getNpts(self,dim=2):
#-------------------------------------------------------------------------------
        if dim == 2:
            return self.__n2
        elif self.__shape == 2 and dim == 1:
            return self.__n1
        elif self.__shape == 3 and dim == 0:
            return self.__n0
        else:
            cm.LOG_ERROR("incoherent values - dim:", dim, " kind:", self.__shape)
            raise ValueError

#-------------------------------------------------------------------------------
    def setSw(self,sw,dim=2):
#-------------------------------------------------------------------------------
        if dim == 2:
            self.__sw2 = sw
        elif self.__shape == 2 and dim == 1:
            self.__sw1 = sw
        elif self.__shape == 1 and dim == 0:
            self.__sw0 = sw
        else:
            cm.LOG_ERROR("incoherent values - sw:",sw,
                                            " dim:", dim, " kind:", self.__shape)
            raise ValueError

        #TODO: Ajust npts accordingly

#-------------------------------------------------------------------------------
    def getSw(self,dim=2):
#-------------------------------------------------------------------------------
        if dim == 2:
            return self.__sw2
        elif self.__shape == 2 and dim == 1:
            return self.__sw1
        elif self.__shape == 1 and dim == 0:
            return self.__sw0
        else:
            cm.LOG_ERROR("incoherent values - dim:", dim, " kind:", self.__shape)
            raise ValueError

#-------------------------------------------------------------------------------
    def setVl(self,vl,dim=2):
#-------------------------------------------------------------------------------
        if dim == 2:
            self.__vl2 = vl
        elif self.__shape == 2 and dim == 1:
            self.__vl1 = vl
        elif self.__shape == 1 and dim == 0:
            self.__vl0 = vl
        else:
            cm.LOG_ERROR("incoherent values - vl:",vl,
                                            " dim:", dim, " kind:", self.__shape)
            raise ValueError

#-------------------------------------------------------------------------------
    def getVl(self,dim=2):
#-------------------------------------------------------------------------------
        if dim == 2:
            return self.__vl2
        elif self.__shape == 2 and dim == 1:
            return self.__vl1
        elif self.__shape == 1 and dim == 0:
            return self.__vl0
        else:
            cm.LOG_ERROR("incoherent values - dim:", dim, " kind:", self.__shape)
            raise ValueError

#-------------------------------------------------------------------------------
    def setSr(self,sr,dim=2):
#-------------------------------------------------------------------------------
        if dim == 2:
            self.__sr2 = sr
        elif self.__shape == 2 and dim == 1:
            self.__sr1 = sr
        elif self.__shape == 1 and dim == 0:
            self.__sr0 = sr
        else:
            cm.LOG_ERROR("incoherent values - sr:",sr,
                                            " dim:", dim, " kind:", self.__shape)

            raise ValueError

#-------------------------------------------------------------------------------
    def getSr(self,dim=2):
#-------------------------------------------------------------------------------
        if dim == 2:
            return self.__sr2
        elif self.__shape == 2 and dim == 1:
            return self.__sr1
        elif self.__shape == 1 and dim == 0:
            return self.__sr0
        else:
            cm.LOG_ERROR("incoherent values - dim:", dim, " kind:", self.__shape)
            raise ValueError

#-------------------------------------------------------------------------------
    def findMaximum(self):
#-------------------------------------------------------------------------------
        """ find maximum """
        maxi=0
        mxi=max(map(abs,self.__spec))
        maxi=max(mxi,maxi)
        return maxi

#-------------------------------------------------------------------------------
    def findMinimum(self):
#-------------------------------------------------------------------------------
        """ find minimum """
        mini=0
        mni=min(self.__spec)
        mini=min(mni,mini)
        return mini

#-------------------------------------------------------------------------------
    def addBroadening(self, spec, **kwargs):
#-------------------------------------------------------------------------------
        """
            Make line broadenings
            do some zero filling in order to avoid truncation
        """

        if self.__shape > 1:
            raise NotImplementedError

        # 1D spectrum broadening
        sw = self.getSw(2)
        return broadening(spec, sw, **kwargs)

#-------------------------------------------------------------------------------
    def getXScale(self):
#-------------------------------------------------------------------------------
        dim = 2
        dw=cm.F2T(self.getSw(dim))
        (a,b)=cm.P2F(self.getNpts(dim), self.getSw(dim), self.getSr(dim))
        scale = []
        label = ""

        unit = string.lower(self.Config['X_Axis_Units'])

        if unit == "hz":
            label = "Frequency (Hz)"
            for point in range(self.getNpts(dim)):
                scale.append(a*point+b)

        if unit == "ppm":
            label = "Chemical Shift (ppm)"
            for point in range(self.getNpts(dim)):
                scale.append((a*point+b)*10.0**6/abs(self.getVl(dim)))

        if  unit == "point":
            label = "Points"
            scale = range(self.getNpts(dim))

        if  unit == "time":
            label = "Time (ms)"
            for point in range(self.getNpts(dim)):
                scale.append(dw*point/1000.)

        return (scale, label)

#-------------------------------------------------------------------------------
    def getYScale(self):
#-------------------------------------------------------------------------------
        dim = 1
        dw=cm.F2T(self.getSw(dim))
        (a,b)=cm.P2F(self.getNpts(dim), self.getSw(dim), self.getSr(dim))
        scale = []
        unit = string.lower(self.Config['Y_Axis_Units'])
        if unit=="hz":
            label = "Frequency (Hz)"
            for point in range(self.getNpts(dim)):
                scale.append(a*point+b)

        if unit=="ppm":
            label = "Chemical Shift (ppm)"
            for point in range(self.getNpts(dim)):
                scale.append((a*point+b)*10.0**6/abs(self.getVl(dim)))

        if unit=="point":
            label = "Points"
            scale = range(self.getNpts(dim))

        if unit=="time":
            label = "Time (ms)"
            for point in range(self.getNpts(dim)):
                scale.append(dw*point/1000.)

        return (scale, label)

#-------------------------------------------------------------------------------
    def getZScale(self):
#-------------------------------------------------------------------------------
        dim = 0
        dw=cm.F2T(self.getSw(dim))
        (a,b)=cm.P2F(self.getNpts(dim), self.getSw(dim), self.getSr(dim))
        scale = []

        if unit=="hz":
            label = "Frequency (Hz)"
            for point in range(self.getNpts(dim)):
                scale.append(a*point+b)

        unit = string.lower(self.Config['Z_Axis_Units'])

        if unit=="ppm":
            label = "Chemical Shift (ppm)"
            for point in range(self.getNpts(dim)):
                scale.append((a*point+b)*10.0**6/abs(self.getVl(dim)))

        if unit=="point":
            label = "Points"
            scale = range(self.getNpts(dim))

        if unit=="time":
            label = "Time (ms)"
            for point in range(self.getNpts(dim)):
                scale.append(dw*point/1000.)

        return (scale, label)