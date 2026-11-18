# ################################
#  pyPulsar project (version 0.2)
# ################################

"""
Script: CP-HartmanHahn
Version: 0.2
Author: C. Fernandez
"""

#------------------------------------------------------------------------------
# Purpose:
#   Cross polarization sequence between a pair of nuclei
#   Hartman-Hahn Matching
#------------------------------------------------------------------------------

# start a new simulation
#-----------------------
sim1=Simulation()

# Set observation channel
#------------------------
sim1.set_channel("13C","1H")      #define both channels

# Nucleus definition
#--------------------
#nucleus with index 0
C=Nucleus("13C")
C.set_lb("100 Hz")
sim1.add_nucleus(C)

# and the proton (with all default parameters)
#---------------------------------------------
H=Nucleus("1H")
sim1.add_nucleus(H)

#select observed
#---------------
sim1.select_observed(C)

#select coupled
#---------------
sim1.select_coupled(H)
sim1.set_dipole(1, dip="5000 Hz")

# simulation setting
#-------------------
sim1.set_spinningspeed(STATIC)
sim1.set_sw("10 kHz")
sim1.set_detect(CENTRAL)
sim1.set_npts(128)
sim1.set_accuracy(4)

p15=250*usec
for plS in arange(50,151,1):
    sim1.clearspectrum(True)
    for ph in [0,180]:

        # Pulse sequence
        #---------------
        # spin temperature inversion phase: ph
        sim1.set_pulse(2.5,powerI=100*kHz,phaseI=ph) #90° Y pulse in channel I (plus 'stp' a phase for spin temperature inversion)
        sim1.set_pulse(p15,powerS=plS*kHz,phaseS=90,powerI=100*kHz,phaseI=90)    #simultaneous X pulses (Contact)
        sim1.set_rcph(ph) #the receiver has to follow the phase 'stp'

        # Run simulations
        #----------------
        sim1.execute_pulsar()
        sim1.clearspectrum(False)       #keep the spectra in memory
    sim1.store_spectrum(data=plS,label="rf(kHz)")

#Write spectra
sim1.write_spectra()
