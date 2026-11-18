# ################################
#  pyPulsar project (version 0.2)
# ################################

"""
Script: Experimental Bruker file simulation
Version: 0.2
Author: C. Fernandez
"""


#------------------------------------------------------------------------------
# Purpose of this script:
# Calculate a spectrum corresponding to an experimental dataset
# Use data read from the experimental file
#------------------------------------------------------------------------------

# Read in the parameter file
#---------------------------
_freq = BF2*MHz    
_nucleus = NUC1
_sw = SW_h
_sr = (SF-SFO1)*10**6  #from Bruker doc
_npts = SI

# start a new simulation
#-----------------------
sim1=Simulation(_freq)

# Set observation channel
#------------------------
sim1.set_channel(_nucleus)
sim1.set_sr(_sr)

# Nucleus definition
#--------------------
N1=Nucleus(_nucleus)
N1.set_chemicalshift(iso=FitParameter["iso1"])
N1.set_lb(FitParameter["lb1"])
N1.set_gb(FitParameter["gb1"])
conc1 = 1.-FitParameter["conc2"]-FitParameter["conc3"]
N1.set_concentration(conc1)
sim1.add_nucleus(N1)

###and more if needed... 
N2=Nucleus(_nucleus)
N2.set_chemicalshift(iso=FitParameter["iso2"])
N2.set_lb(FitParameter["lb2"])
N1.set_gb(FitParameter["gb2"])
N2.set_concentration(FitParameter["conc2"])
sim1.add_nucleus(N2)

N3=Nucleus(_nucleus)
N3.set_chemicalshift(iso=FitParameter["iso3"])
N3.set_lb(FitParameter["lb3"])
N1.set_gb(FitParameter["gb3"])
N3.set_concentration(FitParameter["conc3"])
sim1.add_nucleus(N3)

# simulation setting
#-------------------
sim1.set_spinningspeed("10 kHz")
sim1.set_sw(_sw)
sim1.set_npts(_npts)

# Run simulations
#----------------
n=sim1.get_numberofnuclei(_nucleus)
for index in range (n):

    sim1.select_observed(index) # only one observed nucleus is calculated at once

    sim1.set_nsb(AUTO)          #WARNING: when AUTO, the program needs to know
                                # the nucleus parameters to calculate the number
                                # of spinning sidebands:
                                # This line must then appears after the
                                # 'select_observed' commands
    # Pulse sequence
    #---------------
    sim1.set_idealpulse()       #WARNING: when there is a loop
                                # with a 'execute_pulsar()' command inside,
                                # the pulse sequence is erased at the
                                # beginning of the loop.
                                # Thus pulse sequence must be always defined
                                # inside the loop

    sim1.execute_pulsar()       # EXECUTION OF PULSAR
                                # Then automatically apply 'reset_pulse()'

    sim1.store_spectrum()       # Store the spectrum in a collection of spectra

sim1.sum_spectra()              # Sum the spectra present in the colection
sim1.save_spectra()             # write spectra on the disk