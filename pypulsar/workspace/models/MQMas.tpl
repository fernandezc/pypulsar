# ################################
#  pyPulsar project (version 0.2)
# ################################

"""
Script: MQMAS
Version: 0.2
Author: C. Fernandez
"""

#------------------------------------------------------------------------------
# Purpose of this script:
#   Performing a variation of one parameter and selecting coherence
#   MQMAS optimization exemple
#------------------------------------------------------------------------------

# start a new simulation
#-----------------------
observed="23Na"
sim1=Simulation()
sim1.set_channel(observed)

# Nucleus definition
#--------------------
Na1=Nucleus(observed)
Na1.set_quadrupole(cq="1.5 mhz")
Na1.set_lb("100 Hz")
sim1.add_nucleus(Na1)

# simulation setting
#-------------------
sim1.set_spinningspeed(STATIC)
sim1.set_spinningangle(MAS)
sim1.set_npts("1 K")
sim1.set_sw("20 kHz")
sim1.set_accuracy(5)
sim1.set_rfstep(5)

## required statement
sim1.select_observed()           # this statement is necessary
                                # to validate the nucleus list
                                # the two following statements must always appear after 'select_nucleus'
sim1.set_nsb(0)                 # default 0 (AUTO means automatic calculation of nsb)
sim1.set_detect(CENTRAL)        # calculate only CENTRAL transitions

# Run simulation (variation of the p2 length
#----------------------------------------------
#
plist= arange(.5,10,.5)        # (start,end,step)
for p1 in plist:              # start a loop on p1

    sim1.set_pulse(p1,powerS="100 kHz",selectS=+3)      #first strong rf pulse
    sim1.set_pulse(2.7,powerS="100 kHz")                #second rf pulse
    sim1.execute_pulsar()
    sim1.store_spectrum(data=p1,label="p1 length")

    sim1.set_pulse(p1,powerS="100 kHz",selectS= -3)     #first strong rf pulse
    sim1.set_pulse(2.7,powerS="100 kHz")                #second rf pulse
    sim1.execute_pulsar()
    sim1.store_spectrum(data=p1,label="p1 length")

#Write spectra
#-------------
sim1.write_spectra()

