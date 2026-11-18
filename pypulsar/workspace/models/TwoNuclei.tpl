# ################################
#  pyPulsar project (version 0.2)
# ################################

"""
Script: TwoNuclei
Version: 0.2
Author: C. Fernandez
"""

#------------------------------------------------------------------------------
# Purpose of this script:
#   A sum of several spectra
#------------------------------------------------------------------------------

# start a new simulation
#-----------------------
sim1=Simulation()

# Set observation channel
#------------------------
sim1.set_channel("23Na")

# Nucleus definition
#--------------------
Na1=Nucleus("23Na")
Na1.set_quadrupole(cq="1.5 mhz", eta=0.3)
Na1.set_chemicalshift(iso="2 ppm")
Na1.set_lb("100 Hz")
Na1.set_concentration(0.75)
sim1.add_nucleus(Na1)

Na2=Nucleus("23Na")
Na2.set_quadrupole(cq="3.0 mhz", eta=1)
Na2.set_chemicalshift(iso="-20 ppm")
Na2.set_lb("100 Hz")
Na2.set_concentration(1.0)
sim1.add_nucleus(Na2)

# simulation setting
#-------------------
sim1.set_spinningspeed("5 kHz")
sim1.set_sw("30 kHz")

# Run simulations
#----------------
n=sim1.get_numberofnuclei("23Na")
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
sim1.save_spectra()            # write spectra on the disk

