# ################################
#  pyPulsar project (version 0.2)
# ################################

"""
Script: CP-contact
Version: 0.2
Author: C. Fernandez
Purpose of this script: DEMO
            - Cross polarization sequence between a pair of nuclei
              Contact times variation
"""

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
sim1.set_npts("1 K")
sim1.set_accuracy(4)

# Pulse sequence
#---------------
#sim1.reset_spectra()                #reset spectra to zero

for p15 in arange(50,1000,50):
    sim1.clearspectrum(True)
    for stp in [0,180]:
        # spin temperature inversion phase: stp
        sim1.set_pulse(2.5,powerI=100*kHz,phaseI=0+stp) #90° Y pulse in channel I
        sim1.set_pulse(p15,powerS=100*kHz,phaseS=90,powerI=100*kHz,phaseI=90)    #simultaneous X pulses (Contact)
        sim1.set_rcph(stp) #the receiver has to follow the phase 'stp'

        # Run simulations
        #----------------
        sim1.execute_pulsar()
        sim1.clearspectrum(False)       #keep the spectra in memory
    sim1.store_spectrum(data=p15,label="Contact time")

#Write spectra
sim1.write_spectra()