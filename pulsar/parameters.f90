!$parameters.f90
!
!author = Jean-Paul Amoureux <jean-paul.amoureux@univ-lille1.fr>
!contributors = C. Fernandez <christian.fernandez@ensicaen.fr>
!
!PULSAR Project:
!
! Copyright (C) 2006-2007 Jean-Paul Amoureux, Christian Fernandez
! JPA - Unite de Catalyse et Chimie du Solide, Lille, France.
! CF  - Laboratoire Catalyse et Spectrochimie, Caen, France.
!
!LICENSE:
!
! This program is free software; you can redistribute it and/or
! modify it under the terms of the GNU General Public License (GPL)
! as published by the Free Software Foundation; either version 2
! of the License, or (at your option) any later version.
! This program is distributed in the hope that it will be useful,
! but WITHOUT ANY WARRANTY; without even the implied warranty of
! MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
! GNU General Public License for more details.
! To read the license please visit http://www.gnu.org/copyleft/gpl.html
!
!PURPOSE OF THIS FILE:
!
!  Module for Pulsar
!
! MODULES:
!   parameters
!
! SUBROUTINES:
!   reset_parameters
!_______________________________________________________________________

module parameters
!----------------
  implicit none

                                                 ! info debugging
                                                 !---------------
  integer*8 :: exception=-1
  character(LEN=256) :: exception_text=" "

  integer*8 :: ERROR,WARNING,INFO,STATUS,VERBOSE,DEBUG
  parameter (ERROR=1)
  parameter (WARNING=2)
  parameter (INFO=3)
  parameter (STATUS=4)
  parameter (VERBOSE=5)
  parameter (DEBUG=6)
  integer*8 :: loglevel=INFO


                                                 !---------------------------------------------------------
                                                 ! very important: to be used in conjunction with python,
                                                 ! all static variables must be initialized...
                                                 ! for an unknown reason,
                                                 ! if the variable are not initialized or initialised to zero,
                                                 ! the passing of values between python and fortran doesn't work
                                                 ! (at least on my window system: to check on linux)
                                                 !---------------------------------------------------------

                                                 ! useful constants
                                                 ! ----------------
  real*8 :: pi
  real*8 :: sq6
  real*8 :: eps
  real*8 :: twopi
  real*8 :: twopim6
  character(len=2)  :: crlf=char(13)//char(10)
  character(len=2)  :: tab=char(09)
  character(len=32) :: underline
  parameter (underline="----------------------------------------------")

  parameter (pi=3.1415926535897932384626433832795d0)
  parameter (sq6=2.4494897427831780981972840747059d0)
  parameter (eps=1.0d-30)
  parameter (twopi=6.283185307179586476925286766559d0)
  parameter (twopim6=0.000006283185307179586476925286766559d0)


  character (len=32768) :: message
  character (len=255)  :: message_fmt


                                                 !limits for array allocations
                                                 !----------------------------
  integer*8 :: nptsmax=16384
  integer*8 :: accuracymax=16

                                                 !spectrometer
                                                 !------------
  real*8 :: spectrometerfield=2.3d0              !spectrometer field
  real*8 :: protonfrequency=100.d0               !proton frequency

                                                 !probehead
                                                 !---------
  real*8 :: spinningangle=eps                    !spinner  angle / bo
  real*8 :: spinningspeed=eps                    !spinner frequency
  real*8 :: qfactor=0.001                        !probe quality q-factor (f.w.h.m=wo/q_factor)

                                                 !spin_system
                                                 !-----------
  real*8, allocatable :: nucleus(:,:)            !nucleus 'x_n'
  real*8, allocatable :: chemicalshift(:,:)      !iso, csa, eta, euler angles
  real*8, allocatable :: indirect(:,:)           !i, j, jcoupling  (note: jcoupling is a reserved keyword in f2py cannot be used here)
  real*8, allocatable :: dipole(:,:)             !i, j, dipole, euler angles
  real*8, allocatable :: quadrupole(:,:)         !quadrupolar constant, eta and euler angle
  real*8, allocatable :: t2(:,:)                 !t2 homogeneous relaxation time

                                                 !simulation_parameters
                                                 !---------------------
  integer*8 :: accuracy=1                        !accuracy on euler angles (1-16)
  real*8    :: rfstep=5.d0                        !rf integration step
  integer*8 :: nsb=10                            !number of sidebands
  integer*8 :: npts=512                          !spectrum points number
  real*8    :: sw=10000.d0                       !total spectral width
  real*8    :: sr=eps
  integer*8 :: ncycles=1                         !number of period (pulse+delay) in the sequence
  integer*8 :: nall=999                          !undefined=999, all transitions :0, central: 1, satellite: 2
                                                 !pulses
                                                 !------
  real*8, allocatable :: pulseangle(:)           !pulse angle
  real*8, allocatable :: pulse(:,:)              !pulse definition
  real*8, allocatable :: delay(:,:)              !delay definition
  real*8, allocatable :: coher(:,:)              !phase selection and coherence jump
  real*8, allocatable :: ctp(:,:)                !pathways selection list

                                                 !final simulation arrays
                                                 !-----------------------
  complex*8, allocatable :: spec(:)              !spectrum
  complex*8, allocatable :: ros(:,:)             !density matrix for the spin s
  complex*8, allocatable :: roi(:,:)             !density matrix for the spin i

                                                 !phases  (to be supressed later)
                                                 !------
  integer*8 :: nboucle=-1                        !index of the pulse where a ctp merging occurs
  integer*8 :: ifasing=1                         !flag to say if a phase cycling is used or not (by default phase cycling is used)

  integer*8, allocatable :: nphase(:)            !number of phase for each pulse  (2pi/nphase phase cycling)
  integer*8, allocatable :: level(:)             !selected coherence level after each pulse (during a phase cycling)
  integer*8, allocatable :: qu1(:,:)             !selected coherence in a direct selection in the density matrix
  integer*8, allocatable :: qu2(:,:)             !a second coherence with may be also retained
  integer*8, allocatable :: iref(:)

  logical*8 :: idealpulse=.true.
  logical*8 :: zerospectrum=.true.                         ! the spectrum memo
  real*8 :: rcph = 0.0d0                                ! receiver phase

  logical*8 :: keepgoing=.true.
  logical*8 :: spectrum_compute=.true.  
  
  
end module parameters

!-------------------------------------------------
subroutine reset_parameters()
!-------------------------------------------------
! Initialisation of the main parameters and arrays
!-------------------------------------------------
  use parameters

  message=''
  message_fmt=''
  nptsmax=16384
  accuracymax=16
  spectrometerfield=2.3d0
  protonfrequency=100.0d0
  spinningangle=0.0d0
  spinningspeed=0.0d0
  qfactor=0.001
  if (allocated(nucleus)) deallocate(nucleus)
  if (allocated(chemicalshift)) deallocate (chemicalshift)
  if (allocated(indirect)) deallocate (indirect)
  if (allocated(dipole)) deallocate (dipole)
  if (allocated(quadrupole)) deallocate (quadrupole)
  if (allocated(t2)) deallocate (t2)
  accuracy=1
  rfstep=5.0
  nsb=0.0D0
  npts=512
  sw=10000.0
  sr=0.0
  ncycles=1
  nall=0
  if (allocated (pulseangle)) deallocate(pulseangle)
  if (allocated (pulse)) deallocate(pulse)
  if (allocated (delay)) deallocate(delay)
  if (allocated (coher)) deallocate(coher)
  if (allocated (ctp)) deallocate(ctp)
  if (allocated (spec)) deallocate (spec)
  if (allocated (ros)) deallocate (ros)
  if (allocated (roi)) deallocate (roi)
  nboucle=-1
  ifasing=1
  if (allocated (nphase)) deallocate (nphase)
  if (allocated (level)) deallocate (level)
  if (allocated (qu1)) deallocate (qu1)
  if (allocated (qu2)) deallocate (qu2)
  if (allocated (iref)) deallocate (iref)
  idealpulse=.true.

end subroutine reset_parameters


