try:
    from pylab import *
except:
    pass
import pickle
import optimize
from numpy import array
import common as cm
import functions as fc
import definitions as df
from UserDict import UserDict
import processing as pg
from forpulsar import parameters
import re
global FitStep

#-------------------------------------------------------------------------------
def isRunning(flag=False):
#-------------------------------------------------------------------------------
    if flag:
        parameters.keepgoing=1
    else:
        return (parameters.keepgoing==1)

#===============================================================================
class FitParameters(UserDict):
#===============================================================================
    """
    Allow passing dynamic parameters to the fit function
    """
    count = 0
#-------------------------------------------------------------------------------
    def __init__(self):
#-------------------------------------------------------------------------------
        UserDict.__init__(self)
        self.index ={}
        self.lob = {}
        self.upb = {}
        self.fixed = {}
        self.keys = []

#-------------------------------------------------------------------------------
    def __setitem__(self, key, value):
#-------------------------------------------------------------------------------
        self.isError = False
        if isinstance(key,int):
            index = key
            if index >= len(self.keys):
                # this item index doesn't exist
                raise KeyError
            key = self.keys[index]
        else:
            if not self.data.has_key(key):
                #create key
                self.keys.append(key)
            #else update

        if isinstance(value,tuple) or isinstance(value,list):
            self.data[key] = fc.evaluate(value[0])
            self.lob[key] = None
            self.upb[key] = None
            try:
                if len(value)>2:
                    self.lob[key] = fc.evaluate(value[1])
                    self.upb[key] = fc.evaluate(value[2])
                    self.isError = self._getError(key)
            except:
                pass
            self.fixed[key] = False
            if isinstance(value[-1],bool):
                self.fixed[key] = value[-1]
        else:
            self.data[key] = fc.evaluate(value)
            self.lob[key] = None
            self.upb[key] = None
            self.fixed[key] = False

#-------------------------------------------------------------------------------
    def __getitem__(self, key):
#-------------------------------------------------------------------------------
        if isinstance(key,int):
            l = self.keys
            return self.data[l[key]]
        else :
            return self.data[key]

#-------------------------------------------------------------------------------
    def iteritems(self):
#-------------------------------------------------------------------------------
        return self.data.iteritems()

#-------------------------------------------------------------------------------
    def _getError(self, key):
#-------------------------------------------------------------------------------
        if self.lob[key] is None or self.upb[key] is None:
            return False
        elif self.data[key] < self.lob[key] or self.data[key] > self.upb[key]:
            return True

#===============================================================================
class FitSteps(UserDict):
#===============================================================================
    """
    Define wich parameters are used in a step of the fit
    """
    count = 0
#-------------------------------------------------------------------------------
    def __init__(self, fitpar):
#-------------------------------------------------------------------------------
        UserDict.__init__(self)
        self.fixed = {}
        self.parameters = fitpar.keys

#-------------------------------------------------------------------------------
    def __setitem__(self, step, value):
#-------------------------------------------------------------------------------
        self.data[step]=self.parameters
        self.fixed[step]={}

        # we start with all parameters fixed
        for k in self.parameters:
            self.fixed[step][k] = True

        if not value:
            value='allfixed'

        if isinstance(value,tuple) or isinstance(value,list):
            value = "|".join(value)

        if isinstance(value,str):
            if value[0]!="^": '^('+value
            if value[-1]!="$": value+")$"

            p=re.compile(value)
            for k in self.parameters:
                m = p.search(k)
                if m: self.fixed[step][k] = False
        else:
            cm.LOG_ERROR("FitStep["+str(step)+"]: Can't reconize this input!")

#-------------------------------------------------------------------------------
    def __getitem__(self, step):
#-------------------------------------------------------------------------------
        return self.fixed[step]

#-------------------------------------------------------------------------------
def executefit(calculated, experiment, fitplotter,
                plist, FitStep = None, method = df.SIMPLEX, errfunc = None,
                xtol=0.0001, ftol=0.0001, maxiter=None, maxfun=None,
                fitintensity = True, fitbaseline = True, baselineorder = 1):
#-------------------------------------------------------------------------------
    """
    main routine for fit
    """
    cm.LOG_INFO("Starting fit...")

    # Set loglevel to INFOLEVEL maximum
    #-----------------------------------
    loglevel=fc.parameters.loglevel
    if loglevel > df.INFOLEVEL:
        fc.parameters.loglevel = df.INFOLEVEL

    # Experiment data
    #-----------------
    experiment = experiment.real
    ampl = abs(max(experiment)-min(experiment))
    npts = size(experiment)

    #-------------------------------------------------
    def chi2(params, keys=None, fitplotter=None):
    #-------------------------------------------------
    # return sum((y - x)**2)
        txt = ""
        for i in range(len(params)):
            key=keys[i]
            plist[key]=params[i], \
                     plist.lob[key],plist.upb[key]

            txt += " * "+key+": "+str(plist[key])+"\n"
            if plist.isError:
                return 1.e+300

        # result is the calculated spectrum
        result = calculated()

        if result is None: return 1.e+300

        if result[0] is None: return 1.e+300

        calculation = result[0].real

        intensity, baseline = pg.fitBaseline(calculation, experiment,
                fitintensity, fitbaseline, order = baselineorder)

        calculation = intensity*calculation+baseline

        chi2 = errfunc(experiment,calculation)

        fitplotter.PlotLines={"Experimental":experiment,
                 "Calculated":calculation,
                 "Difference":experiment-calculation,
                 "Baseline":baseline}

        return chi2

    # set the initial parameter list
    #-------------------------------
    #TODO: allow reading saved parameters in saved.tmp
    stepcount = 0

    # Performs different step in optimisation
    #-----------------------------------------
    while stepcount < len(FitStep):
        p=[]
        keys=[]
        if len(FitStep)==0:
            # There is no fit steps
            cm.LOG_STATUS("Optimization running")
            for key in plist.keys:
                if not plist.fixed[key]:
                    p.append(plist[key])
                    keys.append(key)
        else:
            # There is at least one step
            # Use this information
            stepcount += 1
            cm.LOG_STATUS("Optimization step ",stepcount)
            fixed = FitStep[stepcount]
            for key in plist.keys:
                if not fixed[key] and not plist.fixed[key]:
                    p.append(plist[key])
                    keys.append(key)

        res = optimize.minimize(method,chi2, p, args=(keys, fitplotter),
                            xtol=xtol, ftol=ftol,
                            maxiter=maxiter, maxfun=maxfun, callback=saveTemp)

        # restore previous log level
        #----------------------------
        fc.parameters.loglevel=loglevel
        cm.LOG_INFO("\n\n***********************")
        cm.LOG_INFO("Optimization terminated")
        cm.LOG_INFO("***********************\n")
        cm.LOG_INFO("Minimum ErrorFunc value:",res[1])
        cm.LOG_INFO("Number of Iterations:",res[2])
        if isRunning():
            cm.LOG_INFO("Function evaluations: %d" % res[3])
        if method!=df.SIMPLEX:
            cm.LOG_INFO("Gradient evaluations: %d" % res[5])
        cm.LOG_INFO("\nBest results:\n")

        data_returned={}
        for i in range(len(p)):
            key=keys[i]
            if plist.lob[key] is None:
                plist[key]=res[0][i], plist.fixed[key]
            else:
                plist[key]=res[0][i], plist.lob[key],plist.upb[key],plist.fixed[key]
            data_returned[key]=res[0][i]

        for i in range(len(plist)):
            key = plist.keys[i]
            message = "FitParameter['"+key+"'] = "
            message += str(plist[key])
            if plist.lob[key] is not None:
                message += ", "+ str(plist.lob[key])+", "
                message += str(plist.upb[key])
            if plist.fixed[key]:
                message += ", FIXED"
            cm.LOG_INFO(message)
        cm.LOG_INFO("--------")

        flag = 0
        warnflag = res[4]

        if not isRunning():
            cm.LOG_WARNING("Optimization stopped by peer!")
            flag = 3+res[3]
            break # stop optimization steps here

        if warnflag == 1 and method==df.SIMPLEX:
            cm.LOG_WARNING("Maximum number of function evaluations"+ \
                            " has been exceeded")
            flag=1
        if warnflag == 2  and method==df.SIMPLEX:
            cm.LOG_WARNING("Maximum number of iterations has been exceeded")
            flag=2

        if warnflag == 2 and method!=df.SIMPLEX:
            cm.LOG_WARNING("Desired error not necessarily achieved"+ \
                            " due to precision loss")

        if warnflag == 1 and method!=df.SIMPLEX:
            cm.LOG_WARNING("Maximum number of iterations has been exceeded")


    # Do last call with the minimized parameters
    #-------------------------------------------
    isRunning(True)
    try:
        result = calculated()
        if result is not None:
            data_spec = result[1]
    except:
        data_spec = None

    return flag, data_returned, data_spec

#-------------------------------------------------------------------------------
def saveTemp(info, x, args, iterations=None, fcalls=None, fsim=None, fgrad=None):
#-------------------------------------------------------------------------------
    """ temporary save after each iterations """
    keys = args[0]
    fitplotter = args[1]
    txt = info+":\n\n"
    txt += "Iterations: "+str(iterations)+", "
    txt += "Function calls: "+str(fcalls)+"\n"
    if fgrad is not None:
        txt += "Gradient evaluations: "+str(fgrad)+"\n"
    txt += "\nBest Fmin value: "+str(fsim)+"\n\n"
    txt += "\nCurrent parameters for the best optimization: \n"
    if keys is not None:
        for i in range(len(x)):
            key=keys[i]
            txt += " * "+key+": "+str(x[i])+"\n"

    fitplotter.Annotate(txt)

    f = open(cm.getWorkspacePath("saved.tmp"), "wb")
    pickle.dump(x,f)
    f.close()


#-TEST--------------------
if __name__ == "__main__":
#-------------------------

    F=FitSteps(['conc1','lb1','conc2','phc1'])



