from numpy import pi, exp, size, arange, zeros, log, ceil
from scipy.fftpack import fft,ifft
from scipy import optimize
from common import P2F

#-------------------------------------------------------------------------------
def round_to_power_of_2(val):
#-------------------------------------------------------------------------------
    """Round to power of two function
    """
    if val>0.0:
        return int(pow(2,ceil(log(val)/log(2))))
    else:
        return 1

#-------------------------------------------------------------------------------
def broadening(spec, sw, **kwargs):
#-------------------------------------------------------------------------------
    """
    Make 1D line broadenings
    do some zero filling in order to avoid truncation
    """

    # 1D spectrum broadening
    lb = 0.
    gb = 0.
    if kwargs.has_key("lb"):
        lb = float(kwargs["lb"])
    if kwargs.has_key("gb"):
        gb = float(kwargs["gb"])

    # Store npts
    oldnpts = size(spec)
    npts=round_to_power_of_2(max(2**17,oldnpts))
                # try this zerofilling
                # this value should be adapted to the line broadening
                # -> this is what is done in the following
    power = int(ceil(log(npts)/log(2)))

    #make a first passage to determine the better size of the spectrum
    newsw=sw*float(npts)/float(oldnpts)
    pin=-pi/newsw
    delt=1.133/newsw/2.
    for i in range(0,power):
        siz=float(2**i)
        widthh=lb+siz*gb*gb*delt
        m=exp(pin*siz*widthh)
        if m<0.005 and siz>=oldnpts/2: break

    #ok, now we have a size adjusted
    npts=int(siz*2)
    newsw=sw*float(siz*2)/float(oldnpts)
    b1=[0.0 for i in range(npts/2)] #init b
    pin=-pi/newsw
    delt=1.133/newsw/2.
    for i in range(npts/2):
        widthh=lb+i*gb*gb*delt
        m=exp(pin*i*widthh)
        b1[i]=m

    #make this list symmetric
    b2=[]
    l1=b1
    b2.extend(l1)
    l1.reverse()
    b2.extend(l1)

    fid=[]

    # TODO: This is for dimension 2 only.
    fid = fft(spec, npts)
    for i in range(npts):
        fid[i]=fid[i]*b2[i]
    sp= ifft(fid,npts)

    # here we have the broadened spectra
    maxi = max(abs(sp))
    sp = sp / abs(maxi)
    return sp

#-------------------------------------------------------------------------------
def baseline(spec, **kwargs):
#-------------------------------------------------------------------------------
    """
    Correct baseline based on the first and last points of the spectrum
    #TODO: improve this using more sophisticated procedure (spline)
    @return: spec (corrected spectrum)
    """
    if kwargs.has_key("mode"):
        if kwargs["mode"]=="True":
            #automatic baseline
            y1=spec[0]
            y2=spec[-1]
            n = len(spec)
            a = (y2 - y1)/(n-1)
            b = y1
            for i in range(n):
                spec[i] = spec[i]-a*i-b
    return spec

#-------------------------------------------------------------------------------
def fitBaseline(calc, expe, fitintensity=True, fitbaseline=True, order=1):
#-------------------------------------------------------------------------------
    """
    fit a baseline : assuming it is of order 'order': 0-constant, 1-linear, etc
    calculation is made on (expe - (intensity*calc+base1*i+base0))
    @return: intensity (scalar)
    @return: baseline (array)
    """

    npts = size(expe)
    v=arange(npts)
    intensity = max(expe)/max(calc)
    base = (expe[0]+expe[-1])/2.

    # Internal fit function
    #-----------------------
    def fitfunc(p, x, order, fitintensity=True,
                                              intensity=None, fitbaseline=True):

        if fitintensity == True:
            y = p[0]*x
        else:
            y = intensity*x
        if fitbaseline == True:
            for i in range(order):
                y += p[i+1]*v**i
        return y

    # Internal Error function
    #-------------------------
    def errfunc(p, x, y, order, fitintensity=True,
                                              intensity=None, fitbaseline=True):
        return fitfunc(p, x, order, fitintensity, intensity, fitbaseline) - y

    # Initial guess for the parameters
    #----------------------------------
    if fitintensity == True and fitbaseline == True:
        p0 = zeros(2+order)
        p0[0] = intensity
        p0[1]= base
    elif fitbaseline == True:
        p0 = zeros(1+order)
        p0[0]= base
    elif fitintensity == True:
        p0 = zeros(1)
        p0[0]= intensity

    # performs leastsquare optimization
    #-----------------------------------
    if fitintensity == True or fitbaseline == True:
        p,success = optimize.leastsq(errfunc, p0[:],
               args = (calc, expe, order, fitintensity, intensity, fitbaseline))
    else:
        pass #will return results based on first guess only

    # create the baseline array
    #---------------------------
    if fitintensity == True and fitbaseline == True:
        intensity = p[0]
        baseline = zeros(npts)
        for i in range(order):
            baseline += p[i+1]*v**i
    elif fitbaseline == True:
        baseline = zeros(npts)
        for i in range(order):
            baseline += p[i]*v**i
    elif fitintensity == True:
        p0 = zeros(1)
        p0[0]= intensity
        baseline = zeros(npts)
        baseline += base
    else:
        baseline = zeros(npts)
        baseline += base

    # return results
    #---------------
    return intensity, baseline

#-------------------------------------------------------------------------------
def apply_phase(spc,npts,sw,sr,ph0,ph1,phcursor=0):
#-------------------------------------------------------------------------------
    """
    spc is 1D spectrum
    x scaled axis in Hz
    ph0, ph1 phases in degrees
    """

    if ph0==0 and ph1==0:
        return spc
    (a,b)=P2F(npts, sw, sr)
    point = arange(npts)
    scalex = a*point+b
    scursor=scalex[phcursor]
    sph0=ph0-scursor*ph1/sw
    sph1=ph1/sw

    return spc*exp(1j*(sph0+sph1*scalex)*pi/180.)

#------
# tests
#------
if __name__ == '__main__':
#-------------------------
    calc = array([1,2,3,4,5,4,3,1])
    v = arange(8)
    c0, c1, c2 = 5., 7., -1.
    expe = calc*c0 + v*c1 + c2
    print c0,c1,c2
    intensity, baseline= fitBaseline(calc, expe, 0)

    import matplotlib
    matplotlib.use('WXagg')
    import pylab as pl
    pl.plot(expe)
    pl.plot(baseline)
    pl.plot(intensity*calc+baseline)
    pl.show()