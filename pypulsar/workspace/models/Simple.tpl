# ################################
#  pyPulsar project (version 0.2)
# ################################

"""
Script: Simple
Version: 0.2
Author: C. Fernandez
Purpose of this script: DEMO - A very basic quadrupolar spectra simulation
"""

# start a new simulation
#-----------------------
sim1=Simulation()
sim1.set_protonfrequency ("800 MHz")

# Set observation channel
#------------------------
sim1.set_channel("14N")

# Nucleus definition
#--------------------
Na=Nucleus("14N")
Na.set_quadrupole(cq="0.2 mhz", eta=0.3)
Na.set_chemicalshift(iso="1 ppm")
Na.set_lb("10 Hz")
sim1.add_nucleus(Na)

# simulation setting
#-------------------
sim1.set_spinningspeed("10 kHz")
sim1.set_sw("1 MHz")
sim1.set_accuracy(12)

# Pulse sequence
#---------------
sim1.set_idealpulse()

# Run simulations
#----------------
sim1.select_nucleus()  # or sim1.select_observed()
sim1.set_nsb(AUTO)
sim1.execute_pulsar()
sim1.store_spectrum()

# save spectrum
#----------------
sim1.save_spectra()
