# ################################
#  pyPulsar project (version 0.2)
# ################################

"""
Script: popt
Version: 0.2
Author: C. Fernandez
"""

#------------------------------------------------------------------------------
# Purpose of this script:
#   Performing a variation of one parameter
#------------------------------------------------------------------------------

# start a new simulation
#-----------------------
observed="23Na"
sim1=Simulation()
                                 # This open a new simulation instance with
                                 # the default proton frequency set to 400 Mhz
                                 # (but we can also pass another proton frequency
                                 # e.g., sim1=Simulation("600 MHz")'
sim1.set_channel(observed)         # define the observed nucleus (required)

# Nucleus definition
#--------------------
Na1=Nucleus(observed)                # create a new nucleus instance
Na1.set_quadrupole(cq="2.5 mhz")   # default cq=0,eta=0,alpha=0,beta=0,gamma=0
Na1.set_chemicalshift(iso="5 ppm")  # iso (always given in ppm)
                                   # default iso=0,csa=0,eta=0,alpha=0,beta=0,gamma=0
Na1.set_lb("100 Hz")               # broadening (lorentzian)
Na1.set_gb(0)                      # gaussian (optional)
Na1.set_concentration(1.)          # optioanl (default=1.)
sim1.add_nucleus(Na1)              # add the Nucleus defined as Na in the simulation

# simulation setting
#-------------------
## Optional statements (to overset the default values)
sim1.set_spinningspeed("10 kHz")# default STATIC for non spinning sample
sim1.set_spinningangle(MAS)     # default MAS
sim1.set_qfactor(100)           # Probe quality factor (default 0.001)
sim1.set_npts("1 K")            # default 4096 or 4*K
sim1.set_sw("20 kHz")           # default 10000.
sim1.set_accuracy(4)            # default 8
sim1.set_rfstep(5)              # default 5

## required statement
sim1.select_nucleus()           # this statement is necessary
                                # to validate the nucleus list
                                # the two following statements must always appear after 'select_nucleus'
sim1.set_nsb(AUTO)              # default 0 (AUTO means automatic calculation of nsb)
sim1.set_detect(ALL)            # default ALL (other values: CENTRAL, SATELLITE)

# Run simulation (variation of the pulse length
#----------------------------------------------
p1_list= arange(.5,10,.5)       # (start,end,step)
for p1 in p1_list:              # start a loop on p1
    #Pulse sequence (one pulse): length is the pulse length, here variable
    sim1.set_pulse(p1,powerS="100 kHz",offsetS=0,phaseS=0)
    # start execution of this simulation
    sim1.execute_pulsar()
    sim1.store_spectrum(data=p1,label="pulse length")
                                # storing the result in the buffer
                                # for display with some identifier

#Write spectra
sim1.save_spectra()
