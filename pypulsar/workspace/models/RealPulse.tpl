# ################################
#  pyPulsar project (version 0.2)
# ################################

"""
Script: RealPulse
Version: 0.2
Author: C. Fernandez
"""

#------------------------------------------------------------------------------
# Purpose of this script:
#   Use of real pulse
#------------------------------------------------------------------------------

# start a new simulation
#-----------------------
sim1=Simulation()

# Set observation channel
#------------------------
sim1.set_channel("27Al")

# Nucleus definition
#--------------------
al=Nucleus("27Al")
al.set_quadrupole(cq="2.5 mhz", eta=0.3)
al.set_chemicalshift(iso="2 ppm")
al.set_lb("100 Hz")
sim1.add_nucleus(al)

# simulation setting
#-------------------
sim1.set_spinningspeed("5 kHz")
sim1.set_sw("20 kHz")

# Pulse sequence
#---------------
sim1.set_pulse(0.5*usec,powerS=100*kHz)

# Run simulations
#----------------
sim1.select_nucleus()
sim1.set_detect(CENTRAL)
sim1.set_nsb(AUTO)
sim1.execute_pulsar()
sim1.store_spectrum()

#Write spectra
sim1.write_spectra()