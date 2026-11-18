# ################################
#  pyPulsar project (version 0.2)
# ################################

"""
Script: hahnecho
Version: 0.2
Author: C. Fernandez
"""

#--------------------------------------
# Purpose of this script:
#   Effect Hahn echo with T2 relaxation
#--------------------------------------

# start a new simulation
#-----------------------
sim1=Simulation()

# Set observation channel
#------------------------
sim1.set_channel("27Al")

# Nucleus definition
#--------------------
#nucleus 13C with index 0
Al=Nucleus("27Al")
Al.set_quadrupole(cq="2.5 mhz", eta=0.3)
Al.set_lb("100 Hz")
Al.set_relaxation(1*msec)
sim1.add_nucleus(Al)

#select observed
#---------------
sim1.select_observed(Al)

# simulation setting
#-------------------
vr= 10*kHz
sim1.set_spinningspeed(vr)
sim1.set_sw("10 kHz")
sim1.set_detect(CENTRAL)
sim1.set_npts("1 K")
sim1.set_accuracy(5)

# Pulse sequence
#---------------
power=10 * kHz
p90=25./3. * usec
p180=50./3. * usec
ntaur_list=arange(1,20,5)    #number of Rotor period
taur=1.0e6/vr                #Rotor period in usec

for ntaur in ntaur_list:
    sim1.set_pulse(p90,powerS=power,selectS=+1)    #first 90 rf pulse
    sim1.set_delay(ntaur*taur-p90/2.-p180/2.)      #Tau1 is rotor synchonised
    sim1.set_pulse(p180,powerS=power,phaseS=90.)   #second 180 rf pulse
    sim1.set_delay(ntaur*taur-p180/2.)             #Tau2 is rotor synchonised

    # Run simulations
    #----------------
    sim1.execute_pulsar()

# For each increment store the results
    sim1.store_spectrum(data=ntaur,label="number of rotor period")

#Write spectra
sim1.write_spectra()